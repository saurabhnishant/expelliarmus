import os
import sys
import time

import shutil
from threading import Thread

from Decomposer import Decomposer
from GuestFSHelper import GuestFSHelper
from VMISimilarity import SimilarityCalculator
from Reassembler import Reassembler
from RepositoryDatabase import RepositoryDatabase
from StaticInfo import StaticInfo
from VMIDescription import VMIDescriptor
from Evaluation import SimilarityToAllEvaluation, DecompositionEvaluation, \
    ReassemblingEvaluation


class Expelliarmus:
    def __init__(self, vmiFolder=None):
        if vmiFolder is not None:
            StaticInfo.relPathLocalVMIFolder = vmiFolder
        self.checkFolderExistence()

    def checkFolderExistence(self):
        if not os.path.isdir(StaticInfo.relPathGuestRepoConfigs):
            sys.exit("ERROR: folder for repository configuration files not found (looking for %s)" % StaticInfo.relPathGuestRepoConfigs)
        if not os.path.isdir(StaticInfo.relPathLocalRepository):
            os.mkdir(StaticInfo.relPathLocalRepository)
        if not os.path.isdir(StaticInfo.relPathLocalRepositoryPackages):
            os.mkdir(StaticInfo.relPathLocalRepositoryPackages)
        if not os.path.isdir(StaticInfo.relPathLocalRepositoryBaseImages):
            os.mkdir(StaticInfo.relPathLocalRepositoryBaseImages)
        if not os.path.isdir(StaticInfo.relPathLocalRepositoryUserFolders):
            os.mkdir(StaticInfo.relPathLocalRepositoryUserFolders)
        if not os.path.isdir(StaticInfo.relPathLocalVMIFolder):
            os.mkdir(StaticInfo.relPathLocalVMIFolder)

    def printVMIs(self):
        with RepositoryDatabase() as repoManager:
            print "\nVMIs in repository:\n"
            print "{:22s} {:10s} {:10s} {:10s} {:11s} {:13s}".format("Name", "Distro", "Version", "Arch", "PkgManager",
                                                                     "Main-Services")
            print "-----------------------------------------------------------------------------------------------------------"
            vmiDataList = sorted(repoManager.getDataForAllVMIs(), key=lambda vmiData: vmiData[0].lower())
            for vmiData in vmiDataList:
                name = (vmiData[0][:19] + '..') if len(vmiData[0]) > 21 else vmiData[0]
                distribution = (vmiData[1][:7] + '..') if len(vmiData[1]) > 9 else vmiData[1]
                distVersion = (vmiData[2][:7] + '..') if len(vmiData[2]) > 9 else vmiData[2]
                arch = (vmiData[3][:7] + '..') if len(vmiData[3]) > 9 else vmiData[3]
                pkgManager = (vmiData[4][:8] + '..') if len(vmiData[4]) > 10 else vmiData[4]
                mainServices = vmiData[7]
                print "{:22s} {:10s} {:10s} {:10s} {:11s} {:s}".format(name, distribution, distVersion, arch,
                                                                       pkgManager, mainServices)
            print "-----------------------------------------------------------------------------------------------------------"
            print "Overall VMIs in repository: " + str(len(vmiDataList)) + "\n"

    def printPackages(self):
        with RepositoryDatabase() as repoManager:
            print "\nPackages in repository:\n"
            print "{:30s} {:20s} {:10s} {:10s}".format("Name", "Version", "Arch", "Distribution")
            print "---------------------------------------------------------------------------"
            packageDataList = sorted(repoManager.getAllPackages(), key=lambda pkgData: (pkgData[3], pkgData[0].lower()))
            for packageData in packageDataList:
                name = (packageData[0][:27] + '..') if len(packageData[0]) > 29 else packageData[0]
                version = (packageData[1][:17] + '..') if len(packageData[1]) > 19 else packageData[1]
                arch = (packageData[2][:7] + '..') if len(packageData[2]) > 9 else packageData[2]
                distro = (packageData[3][:7] + '..') if len(packageData[3]) > 9 else packageData[3]
                print "{:30s} {:20s} {:10s} {:10s}".format(name, version, arch, distro)
            print "---------------------------------------------------------------------------"
            print "Overall Packages in repository: " + str(len(packageDataList)) + "\n"

    def printBaseImages(self):
        with RepositoryDatabase() as repoManager:
            print "\nBase images in repository:\n"
            print "{:12s} {:10s} {:10s} {:10s}".format("Distribution", "Version", "Arch", "PkgManager")
            print "---------------------------------------------"
            baseDataList = sorted(repoManager.getAllBaseImages(), key=lambda baseData: baseData[0].lower())
            for baseData in baseDataList:
                distro = (baseData[0][:9] + '..') if len(baseData[0]) > 11 else baseData[0]
                version = (baseData[1][:7] + '..') if len(baseData[1]) > 9 else baseData[1]
                arch = (baseData[2][:7] + '..') if len(baseData[2]) > 9 else baseData[2]
                pkgManager = (baseData[3][:7] + '..') if len(baseData[3]) > 9 else baseData[3]
                print "{:12s} {:10s} {:10s} {:10s}".format(distro, version, arch, pkgManager)
            print "---------------------------------------------"
            print "Overall base images in repository: " + str(len(baseDataList)) + "\n"

    def inspectVMIsInFolder(self, pathToDir):
        if not os.path.isdir(pathToDir):
            print "Error while inspecting VMIs. \"%s\" is not a directory." % pathToDir
            return
        vmiPaths = self.getVmiPaths(pathToDir)
        numVMIs = len(vmiPaths)
        numMetaFiles = 0
        vmiFileNamesWithMeta = []
        vmiPathsWithoutMeta = []
        for pathToVMI in vmiPaths:
            possibleMetaFile = pathToVMI.rsplit(".", 1)[0] + ".meta"
            if os.path.isfile(possibleMetaFile):
                numMetaFiles = numMetaFiles + 1
                vmiFileNamesWithMeta.append(pathToVMI.split("/")[-1])
            else:
                vmiPathsWithoutMeta.append(pathToVMI)
        print "Inspecting VMIs in folder %s" % pathToDir
        print "\tFound VMIs: %i" % numVMIs
        print "\tExisting meta files for these VMIs: %i" % numMetaFiles

        # if meta files existing, ask if they should be replaced
        replaceMetaFiles = None
        vmiPathsToInspect = None
        if numMetaFiles > 0:
            userInput = raw_input("\tThere already exist meta files for the following VMIs. Replace all, yes or [no]? \n\t" + ", ".join(vmiFileNamesWithMeta) + "\n\t")
            if userInput == "yes" or userInput == "y":
                replaceMetaFiles = True
                vmiPathsToInspect = vmiPaths
            else:
                print "\tMeta files will not be overridden."
                replaceMetaFiles = False
                vmiPathsToInspect = vmiPathsWithoutMeta
        else:
            vmiPathsToInspect = vmiPaths

        if len(vmiPathsToInspect) > 0:
            count = 1
            for pathToVMI in vmiPathsToInspect:
                print "VMI %i/%i" % (count,len(vmiPathsToInspect))
                self.inspectVMI(pathToVMI,replaceMetaFiles=replaceMetaFiles)
                count = count +1
        else:
            print "No VMIs to inspect."

    def inspectVMI(self, pathToVMI, replaceMetaFiles=None):
        extension = pathToVMI.split(".")[-1]
        pathToMeta = pathToVMI.rsplit(".", 1)[0] + ".meta"

        print "Inspecting VMI \"%s\"" % pathToVMI

        # check if file exists
        if not os.path.isfile(pathToVMI):
            print "\tError while analyzing VMI. File \"%s\" does not exist." % pathToVMI
            return
        # check if valid format
        if not extension in StaticInfo.validVMIFormats:
            print "\tError while analyzing VMI. File extension \"%s\" is not supported." % extension
            print "\tSupported extensions: " + ",".join(StaticInfo.validVMIFormats)
            return

        # check if meta file already exists
        if os.path.isfile(pathToMeta):
            if replaceMetaFiles is None:
                userInput = raw_input("\tThere already exists a meta data file for the VMI \"%s\". Replace, yes or [no]? \n\t")
                if not (userInput == "yes" or userInput == "y"):
                    print "\tInput not recognized, Meta file will not be replaced."
                else:
                    print "\tExisting meta file will be replaced"
                    self.createMetaFileForVMI(pathToVMI, pathToMeta)
            elif replaceMetaFiles == True:
                print "\tExisting meta file will be replaced"
                self.createMetaFileForVMI(pathToVMI, pathToMeta)
            else:
                print "\tMeta file already exists for VMI."
        else:
            self.createMetaFileForVMI(pathToVMI,pathToMeta)

    def createMetaFileForVMI(self, pathToVMI, pathToMetafile):
        print "\tCreating Handler for \"%s\"" % pathToVMI
        guest, root = GuestFSHelper.getHandle(pathToVMI, rootRequired=True)
        print "\tCreating VMIDescriptor"
        vmi = VMIDescriptor(pathToVMI, "test", [], guest, root)
        GuestFSHelper.shutdownHandle(guest)
        correctMS = False
        while not correctMS:
            userInputMS = raw_input("\tEnter Main Services in format \"MS1,MS2,...\"\n\t")
            vmi.mainServices = userInputMS.split(",")
            print "\tUserinput: " + str(vmi.mainServices)

            # Check if these main services exist
            error = False
            for pkgName in vmi.mainServices:
                if not vmi.checkIfNodeExists(pkgName):
                    error = True
                    print "\t\tMain Service \"" + pkgName + "\" does not exist"
                    similar = vmi.getListOfNodesContaining(pkgName)
                    if len(similar) > 0:
                        print "\t\tDid you mean one of the following?\n\t\t" + ",".join(similar)
                    else:
                        print "\t\t\tNo similar packages found."
            if not error:
                print "\t\tProvided Main Services exist in VMI."
                uInput = raw_input("\t\tCorrect, yes or no?\n\t\t")
                if uInput == "y" or uInput == "yes":
                    correctMS = True

        # add meta file for vmi
        sumInstallSize = vmi.getPkgsInstallSize()
        with open(pathToMetafile, "w+") as metaData:
            vmiFileName = pathToVMI.rsplit("/",1)[-1]
            metaData.write(vmiFileName + ";" +
                           str(sumInstallSize) + ";" +
                           ",".join(vmi.mainServices))
        print "\tFinished Inspection of VMI \"%s\". Meta file written to \"%s\"" % (pathToVMI, pathToMetafile)

    def decomposeVMIsInFolder(self, pathToDir):
        if not os.path.isdir(pathToDir):
            print "Error while decomposing VMIs. \"%s\" is not a directory." % pathToDir
            return
        vmiPaths = self.getVmiPaths(pathToDir)
        numVMIs = len(vmiPaths)
        numVMIsWithMetaFiles = 0
        vmiPathsWithMeta = []
        vmiFilenamesWithoutMeta = []
        for pathToVMI in vmiPaths:
            possibleMetaFile = pathToVMI.rsplit(".", 1)[0] + ".meta"
            if os.path.isfile(possibleMetaFile):
                numVMIsWithMetaFiles = numVMIsWithMetaFiles + 1
                vmiPathsWithMeta.append(pathToVMI)
            else:
                vmiFilenamesWithoutMeta.append(pathToVMI.split("/")[-1])
        print "Decomposing VMIs in folder %s" % pathToDir
        print "\tFound VMIs: %i" % numVMIs
        print "\tExisting meta files for these VMIs: %i" % numVMIsWithMetaFiles

        # if meta files missing, ask to continue
        if numVMIsWithMetaFiles == 0:
            print "Error: Meta files required for decomposition."
            vmiPathsToDecompose = []
        elif numVMIs != numVMIsWithMetaFiles:
            userInput = raw_input("\tThere are missing meta files for the following VMIs. Continue with the remaining %i VMIs, yes or [no]? \n\t%s\n\t" % (numVMIsWithMetaFiles,", ".join(vmiFilenamesWithoutMeta)))
            if userInput == "yes" or userInput == "y":
                vmiPathsToDecompose = vmiPathsWithMeta
            else:
                print "\tAborting Decomposition of VMIs."
                vmiPathsToDecompose = []
        else:
            vmiPathsToDecompose = vmiPaths

        if len(vmiPathsToDecompose) > 0:
            count = 1
            for pathToVMI in vmiPathsToDecompose:
                print "VMI %i/%i" % (count,len(vmiPathsToDecompose))
                self.decomposeVMI(pathToVMI)
                count = count +1
        else:
            pass

    def decomposeVMI(self, pathToVMI):
        vmiFileName = pathToVMI.split("/")[-1]
        extension = pathToVMI.split(".")[-1]
        pathToMeta = pathToVMI.rsplit(".", 1)[0] + ".meta"
        # check if VMI exists
        if not os.path.isfile(pathToVMI):
            print "\tError while decomposing VMI. File \"%s\" does not exist." % pathToVMI
            return
        # check if valid format
        if not extension in StaticInfo.validVMIFormats:
            print "\tError while decomposing VMI. File extension \"%s\" is not supported." % extension
            print "\tSupported extensions: " + ",".join(StaticInfo.validVMIFormats)
            return
        # check if meta file exists
        if not os.path.isfile(pathToMeta):
            print "\tError while decomposing VMI. Meta File \"%s\" does not exist." % pathToMeta
            return

        # obtain main services from meta data file
        vmiMetaData = open(pathToMeta).read().split("\n")[0].split(";")
        mainServices = vmiMetaData[2].split(",")

        # decompose and clean up
        Decomposer.decompose(pathToVMI, vmiFileName, mainServices)
        os.remove(pathToMeta)

    def reassembleAllVMIs(self):
        vmisInFolder = self.getVmiPaths(StaticInfo.relPathLocalVMIFolder)
        if len(vmisInFolder) > 0:
            validInput = False
            while not validInput:
                userInput = raw_input(
                    "There are VMIs stored in folder \"%s\". These might conflict with VMIs that are about to be reassembled.\n"
                    "Clear This folder, yes or no?" % (StaticInfo.relPathLocalVMIFolder)
                )
                if userInput == "yes" or userInput == "y":
                    shutil.rmtree(StaticInfo.relPathLocalVMIFolder)
                    os.mkdir(StaticInfo.relPathLocalVMIFolder)
                    validInput = True
                elif userInput == "no" or userInput == "n":
                    validInput = True
                else:
                    print "Input \"%s\" not recognized."

        vmiNames = []
        with RepositoryDatabase() as repo:
            vmiNames = repo.getAllVmiNames()

        numVMIs = len(vmiNames)
        vmiPaths = []
        if numVMIs > 0:
            print "Reassembling %i VMIs\n"
            count = 1
            for vmiName in vmiNames:
                print "VMI %i/%i" % (count, numVMIs)
                vmiPaths.append(self.reassembleVMI(vmiName))
                count = count + 1
            print "\nVMIs reassembled: %i" % numVMIs
            print "Reassembled VMIs stored at:%s" % "\n\t".join(vmiPaths)
        else:
            print "No VMIs to reassemble"

    def reassembleVMI(self, vmiName):
        return Reassembler.reassemble(vmiName)

    def evaluateSimBetweenAll(self, pathToDir):
        evalLogPath = os.path.join (StaticInfo.relPathLocalEvaluation,"evaluation_simToAll_MS.csv")
        sortedVmiData = self.getSortedVmiData(pathToDir)
        sortedVmiFileNames = list (x[1] for x in sortedVmiData)
        evalSimToMaster = SimilarityToAllEvaluation(evalLogPath, sortedVmiFileNames)
        evalSimToMaster.similarities = SimilarityCalculator.computeSimilarityManyToMany(sortedVmiData, onlyOnMainServices=True)
        evalSimToMaster.saveEvaluation()

    def evaluateDecomposition(self, pathToSource, repetitions, resetBeforeEachDecomposition):
        for i in range(1, repetitions + 1):
            print "============================================"
            print "          Evaluating decomposition          "

            if not resetBeforeEachDecomposition:
                print "       exploiting semantic redundancy       "
            else:
                print "     not exploiting semantic redundancy     "

            print "              Iteration %i/%i" % (i, repetitions)
            print "============================================\n"

            self.resetRepo()
            print "Copy VMIs from \"%s\" to \"%s\":\n" % (pathToSource, StaticInfo.relPathLocalVMIFolder)
            if os.path.isdir(StaticInfo.relPathLocalVMIFolder):
                shutil.rmtree(StaticInfo.relPathLocalVMIFolder)

            origSize = self.getDirSize(pathToSource)
            t = Thread(target=shutil.copytree, args=[pathToSource, StaticInfo.relPathLocalVMIFolder])
            t.setDaemon(True)
            t.start()
            while t.isAlive():
                time.sleep(2)
                sys.stdout.write("\r\tProgress: %.1f%%" % (float(self.getDirSize(StaticInfo.relPathLocalVMIFolder)) / origSize * 100))
                sys.stdout.flush()
            sys.stdout.write("\r\tProgress: 100.0%")
            sys.stdout.flush()
            print ""
            self.checkFolderExistence()

            if not resetBeforeEachDecomposition:
                evalLogFileName = StaticInfo.relPathLocalEvaluation + "/decomposition_" + str(i) + ".csv"
            else:
                evalLogFileName = StaticInfo.relPathLocalEvaluation + "/decomposition_noRedundancy" + str(i) + ".csv"
            self.evaluateDecompositionOnce(StaticInfo.relPathLocalVMIFolder, evalLogFileName, resetBeforeEachDecomposition)
        print "\n\nEvaluation completed, results saved in \"%s\"." % StaticInfo.relPathLocalEvaluation

    def evaluateDecompositionOnce(self, pathToDir, evalLogFileName, resetBeforeEachDecomposition):
        evalDecomp = DecompositionEvaluation(evalLogFileName)

        sortedVmiData = self.getSortedVmiData(pathToDir)
        i = 0
        for (pathToVMI, vmiFileName, mainServices) in sortedVmiData:
            if resetBeforeEachDecomposition:
                self.resetRepo()
            i = i + 1
            print ""
            print "        VMI %i/%i" % (i, len(sortedVmiData))
            print "============================="
            evalDecomp.vmiFilename = vmiFileName
            evalDecomp.vmiMainServices = mainServices
            evalDecomp.addVmiOrigSize(os.path.getsize(pathToVMI))

            startTime = time.time()
            Decomposer.decompose(pathToVMI, vmiFileName, mainServices, evalDecomp=evalDecomp)
            decompTime = time.time() - startTime

            repoStorageSize = self.getDirSize(StaticInfo.relPathLocalRepository)

            evalDecomp.sumRepoStorageSize = repoStorageSize
            evalDecomp.dbSize = os.path.getsize(StaticInfo.relPathLocalRepositoryDatabase)
            evalDecomp.timeDecompAll = decompTime
            evalDecomp.newLine()

            # remove meta data file
            pathToMetaData = pathToVMI.rsplit(".", 1)[0] + ".meta"
            os.remove(pathToMetaData)
        evalDecomp.saveEvaluation()

    def evaluateReassembly(self, repetitions):
        for i in range(1, repetitions + 1):
            print "============================================"
            print "           Evaluating reassembly            "
            print "              Iteration %i/%i" % (i, repetitions)
            print "============================================\n"
            if os.path.isdir(StaticInfo.relPathLocalVMIFolder):
                shutil.rmtree(StaticInfo.relPathLocalVMIFolder)
            os.mkdir(StaticInfo.relPathLocalVMIFolder)
            self.evaluateReassemblyOnce(StaticInfo.relPathLocalEvaluation + "/reassembly_" + str(i) + ".csv")

    def evaluateReassemblyOnce(self, evalLogFileName):
        evalReassembly = ReassemblingEvaluation(evalLogFileName)
        with RepositoryDatabase() as repoManager:
            vmiNameList = repoManager.getAllVmiNames()

        # filter out snapshots
        # vmiNameList = [x for x in vmiNameList if "Snapshot" not in x]

        i = 0
        for vmiName in vmiNameList:
            i = i + 1
            print ""
            print "        VMI %i/%i" % (i, len(vmiNameList))
            print "============================="
            shutil.rmtree(StaticInfo.relPathLocalVMIFolder)
            os.mkdir(StaticInfo.relPathLocalVMIFolder)
            startTime = time.time()
            pathToNewVMI = Reassembler.reassemble(vmiName, evalReassembly=evalReassembly)
            reassemblingTime = time.time() - startTime

            evalReassembly.reassemblingTime = reassemblingTime
            evalReassembly.vmiSize = os.path.getsize(pathToNewVMI)
            evalReassembly.newLine()
        evalReassembly.saveEvaluation()



    def verifySourceFolder(self, pathToDir):
        if not os.path.isdir(pathToDir):
            print "Error: \"%s\" is not a directory." % pathToDir
            return False
        print "Verifying source folder \"%s\":" % pathToDir
        vmiPaths = self.getVmiPaths(pathToDir)
        metaPaths = []
        numVMIs = len(vmiPaths)
        numVMIsWithMetaFiles = 0
        vmiFilenamesWithoutMeta = []

        # Check if meta file exists for every valid VMI
        for pathToVMI in vmiPaths:
            possibleMetaFile = pathToVMI.rsplit(".", 1)[0] + ".meta"
            if os.path.isfile(possibleMetaFile):
                numVMIsWithMetaFiles = numVMIsWithMetaFiles + 1
                metaPaths.append(possibleMetaFile)
            else:
                vmiFilenamesWithoutMeta.append(pathToVMI.split("/")[-1])
        if numVMIs != numVMIsWithMetaFiles:
            print "\tThe following VMIs are missing meta files:\n\t" + ",".join(vmiFilenamesWithoutMeta)
            return False

        # Check if only valid files in folder
        extraFiles = []
        for filename in os.listdir(pathToDir):
            # check if extension supported
            pathToFile = os.path.join(pathToDir,filename)
            if (pathToFile not in vmiPaths) and (pathToFile not in metaPaths):
                extraFiles.append(pathToFile.rsplit("/",1)[1])
        if len(extraFiles) > 0:
            print "\tThe following files are either meta files not corresponding to any VMI or other files not supported by this program."
            print "\tPlease remove these manually."
            print "\t\t" + ",".join(extraFiles)
            return False

        print "\tVerification finished successfully."
        return True

    def resetRepo(self, verbose=False):
        if verbose:
            print "Resetting Repository."
        # Remove old repository
        if os.path.exists(StaticInfo.relPathLocalRepository):
            shutil.rmtree(StaticInfo.relPathLocalRepository)
        # Create Folder Structure
        self.checkFolderExistence()
        # import basic files
        shutil.copytree(StaticInfo.relPathInitPackages, StaticInfo.relPathLocalRepositoryPackagesBasic)
        # Init database
        with RepositoryDatabase() as repo:
            pass

    def getVmiPaths(self, pathToDir):
        """
        :param pathToDir:
        :return: list of VMI paths with supported file extensions in folder specified by path (e.g. [pathToDir/vmiName.qcow2]
        """
        vmiPaths = list()
        for filename in os.listdir(pathToDir):
            # check if extension supported
            extension = filename.rsplit(".", 1)[1]
            if extension in StaticInfo.validVMIFormats:
                vmiPaths.append(os.path.join(pathToDir,filename))
        sortedVmiPaths = sorted(vmiPaths, key=lambda fileName: fileName.lower())
        return sortedVmiPaths

    def getSortedVmiData(self, pathToDir):
        """
            .meta file has to exist for each VMI to be recognized! run verifySourceFolder before!
            :return:
            :return: [(pathToVMI, vmiFilename, [MS1,MS2])]
        """
        vmiPaths = self.getVmiPaths(pathToDir)
        # list of vmi data
        # [(vmiPath, vmiFileName, pkgSize, [main services])]
        vmiData = list()
        for pathToVMI in vmiPaths:
            pathToMetaData = pathToVMI.rsplit(".",1)[0] + ".meta"
            with open(pathToMetaData, "r") as metaDataFile:
                metaData = metaDataFile.read().replace("\n", "").split(";")
                vmiFileName = metaData[0]
                pkgsSize = metaData[1]
                mainservices = metaData[2]
                vmiData.append((pathToVMI,vmiFileName, pkgsSize, mainservices))

        # sort list by 1. pkgSize 2. filename
        # and remove pkgSize
        # [(vmiPath, vmiFileName, [main services])]
        sortedVmiData = list(
            (x[0], x[1], x[3].split(",")) for x in sorted(vmiData, key=lambda vmiData: (vmiData[2], vmiData[1])))
        return sortedVmiData

    def getDirSize(self, start_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(start_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size




    def evaluateDecompositionOnceOLD(self, evalLogFileName):
        evalDecomp = DecompositionEvaluation(evalLogFileName)

        sortedVmiFileNames = self.getSortedListOfAllVMIs()
        i = 0
        for vmiFileName in sortedVmiFileNames:
            i = i + 1
            print "============================="
            print "        VMI %i/%i" % (i,len(sortedVmiFileNames))
            print "============================="

            vmiPath = StaticInfo.relPathLocalVMIFolder + "/" + vmiFileName
            vmiMetaDataPath = StaticInfo.relPathLocalVMIFolder + "/" + vmiFileName.rsplit(".", 1)[0] + ".meta"
            vmiMetaData = open(vmiMetaDataPath).read().split("\n")[0].split(";")
            mainServices = vmiMetaData[2].split(",")

            evalDecomp.vmiFilename = vmiFileName
            evalDecomp.vmiMainServices = mainServices
            evalDecomp.addVmiOrigSize(os.path.getsize(vmiPath))

            startTime = time.time()
            Decomposer.decompose(vmiPath, vmiFileName, mainServices, evalDecomp=evalDecomp)
            decompTime = time.time() - startTime

            repoStorageSize = self.getDirSize(StaticInfo.relPathLocalRepositoryBaseImages) + \
                              self.getDirSize(StaticInfo.relPathLocalRepositoryUserFolders) + \
                              self.getDirSize(StaticInfo.relPathLocalRepositoryPackages)

            evalDecomp.sumRepoStorageSize = repoStorageSize
            evalDecomp.dbSize = os.path.getsize(StaticInfo.relPathLocalRepositoryDatabase)
            evalDecomp.timeDecompAll = decompTime
            evalDecomp.newLine()
            os.remove(vmiMetaDataPath)
        evalDecomp.saveEvaluation()

    def evaluateDecompositionOLD(self, distribution, numberOfEvaluations):
        vmiBackupFolder = "VMI_Backups/" + distribution

        for i in range(1,numberOfEvaluations+1):
            self.resetRepo()
            print "Copy VMIs from \"%s\" to \"%s\":\n" % (vmiBackupFolder, StaticInfo.relPathLocalVMIFolder)
            shutil.rmtree(StaticInfo.relPathLocalVMIFolder)

            origSize = self.getDirSize(vmiBackupFolder)
            t = Thread(target=shutil.copytree, args=[vmiBackupFolder, StaticInfo.relPathLocalVMIFolder])
            t.start()
            while t.isAlive():
                time.sleep(2)
                sys.stdout.write("\r\tProgress: %.1f%%" % (float(self.getDirSize(StaticInfo.relPathLocalVMIFolder)) / origSize * 100))
                sys.stdout.flush()
            print ""
            self.checkFolderExistence()
            self.evaluateDecompositionOnceOLD("Evaluation/" + distribution + "_evaluation_decomp_" + str(i) + ".csv")
            raw_input("Continue?")

    def evaluateDecompositionNoRedundancyOnce(self, evalLogFileName):
        evalDecomp = DecompositionEvaluation(evalLogFileName)

        sortedVmiFileNames = self.getSortedListOfAllVMIs()
        i = 0
        for vmiFileName in sortedVmiFileNames:
            self.resetRepo()
            self.checkFolderExistence()

            i = i + 1
            print "============================="
            print "        VMI %i/%i" % (i,len(sortedVmiFileNames))
            print "============================="

            vmiPath = StaticInfo.relPathLocalVMIFolder + "/" + vmiFileName
            vmiMetaDataPath = StaticInfo.relPathLocalVMIFolder + "/" + vmiFileName.rsplit(".", 1)[0] + ".meta"
            vmiMetaData = open(vmiMetaDataPath).read().split("\n")[0].split(";")
            mainServices = vmiMetaData[2].split(",")

            evalDecomp.vmiFilename = vmiFileName
            evalDecomp.vmiMainServices = mainServices
            evalDecomp.addVmiOrigSize(os.path.getsize(vmiPath))

            startTime = time.time()
            Decomposer.decompose(vmiPath, vmiFileName, mainServices, evalDecomp=evalDecomp)
            decompTime = time.time() - startTime

            repoStorageSize = self.getDirSize(StaticInfo.relPathLocalRepositoryBaseImages) + \
                              self.getDirSize(StaticInfo.relPathLocalRepositoryUserFolders) + \
                              self.getDirSize(StaticInfo.relPathLocalRepositoryPackages)

            evalDecomp.sumRepoStorageSize = repoStorageSize
            evalDecomp.dbSize = os.path.getsize(StaticInfo.relPathLocalRepositoryDatabase)
            evalDecomp.timeDecompAll = decompTime
            evalDecomp.newLine()
            os.remove(vmiMetaDataPath)
        evalDecomp.saveEvaluation()

    def evaluateDecompositionNoRedundancy(self, distribution, numberOfEvaluations):
        vmiBackupFolder = "VMI_Backups/" + distribution
        for i in range(1,numberOfEvaluations+1):
            print "Copy VMIs from \"%s\" to \"%s\":\n" % (vmiBackupFolder, StaticInfo.relPathLocalVMIFolder)
            shutil.rmtree(StaticInfo.relPathLocalVMIFolder)

            origSize = self.getDirSize(vmiBackupFolder)
            t = Thread(target=shutil.copytree, args=[vmiBackupFolder, StaticInfo.relPathLocalVMIFolder])
            t.start()
            while t.isAlive():
                time.sleep(2)
                sys.stdout.write("\r\tProgress: %.1f%%" % (
                float(self.getDirSize(StaticInfo.relPathLocalVMIFolder)) / origSize * 100))
                sys.stdout.flush()
            print ""

            self.checkFolderExistence()
            self.evaluateDecompositionNoRedundancyOnce("Evaluation/" + distribution + "_evaluation_decomp_noRedundancy_" + str(i) + ".csv")

    def evaluateReassemblingOnceOLD(self, evalLogFileName):
        evalReassembly = ReassemblingEvaluation(evalLogFileName)
        with RepositoryDatabase() as repoManager:
            vmiNameList = repoManager.getAllVmiNames()

        vmiNameListNoSnapshots = [x for x in vmiNameList if "Snapshot" not in x]

        i = 0
        for vmiName in vmiNameListNoSnapshots:
            i = i + 1
            print "============================="
            print "        VMI %i/%i" % (i, len(vmiNameListNoSnapshots))
            print "============================="
            shutil.rmtree(StaticInfo.relPathLocalVMIFolder)
            os.mkdir(StaticInfo.relPathLocalVMIFolder)
            startTime = time.time()
            pathToNewVMI = Reassembler.reassemble(vmiName, evalReassembly=evalReassembly)
            reassemblingTime = time.time() - startTime

            evalReassembly.reassemblingTime = reassemblingTime
            evalReassembly.vmiSize = os.path.getsize(pathToNewVMI)
            evalReassembly.newLine()
        evalReassembly.saveEvaluation()

    def evaluateReassemblingOLD(self, distribution, numberOfEvaluations):
        for i in range(1, numberOfEvaluations + 1):
            shutil.rmtree(StaticInfo.relPathLocalVMIFolder)
            os.mkdir(StaticInfo.relPathLocalVMIFolder)
            self.evaluateReassemblingOnce("Evaluation/" + distribution + "_evaluation_reassembly_" + str(i) + ".csv")

    def getSortedListOfAllVMIs(self):
        """
        .meta file has to exist for each VMI to be recognized!
        :return:
        """
        vmiList = list()
        for filename in os.listdir(StaticInfo.relPathLocalVMIFolder):
            if filename.endswith(".meta"):
                filePath = StaticInfo.relPathLocalVMIFolder + "/" + filename
                with open(filePath, "r") as metaDataFile:
                    metaData = metaDataFile.read().split(";")
                    vmiFileName = metaData[0]
                    pkgsSize = metaData[1]
                    if os.path.isfile(StaticInfo.relPathLocalVMIFolder + "/" + vmiFileName):
                        vmiList.append((vmiFileName,pkgsSize))
                    else:
                        print "Warning, meta file found for VMI \"%s\" but VMI not found. Meta file removed." % vmiFileName
                        os.remove(filePath)
        sortedVMIs = list( x[0] for x in sorted(vmiList, key=lambda vmiData: (int(vmiData[1]),vmiData[0])))
        return sortedVMIs

    def getSortedListOfAllVMIsAndMS(self):
        """
        .meta file has to exist for each VMI to be recognized!
        :return:
        :return: [(vmiFilename,[MS1,MS2])]
        """
        vmiTriples = list()
        for filename in os.listdir(StaticInfo.relPathLocalVMIFolder):
            if filename.endswith(".meta"):
                filePath = StaticInfo.relPathLocalVMIFolder + "/" + filename
                with open(filePath, "r") as metaDataFile:
                    metaData = metaDataFile.read().replace("\n","").split(";")
                    vmiFileName = metaData[0]
                    pkgsSize = metaData[1]
                    mainservices = metaData[2]
                    vmiTriples.append((vmiFileName,pkgsSize,mainservices))
        #sortedVMIs = sorted(vmiTriples, key=lambda vmiData: (vmiData[1],vmiData[0]))
        sortedVMIs = list( (x[0],x[2].split(",")) for x in sorted(vmiTriples, key=lambda vmiData: (vmiData[1],vmiData[0])))
        return sortedVMIs