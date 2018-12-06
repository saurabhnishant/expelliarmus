import sys
import os
import shutil
import time

from GuestFSHelper import GuestFSHelper
from RepositoryDatabase import RepositoryDatabase
from StaticInfo import StaticInfo
from VMIManipulation import VMIManipulator
from VMIDescription import BaseImageDescriptor


class Reassembler:

    @staticmethod
    def reassemble(vmiName, evalReassembly=None):
        # TODO: reset image
        print "\n=== Reassemble VMI \"" + vmiName + "\""

        with RepositoryDatabase() as repoManager:
            if not repoManager.vmiExists(vmiName):
                sys.exit("Error: Cannot reassemble VMI \"%s\". No VMI with that name exists in the database!" % vmiName)
            baseImage = None # type: BaseImageDescriptor
            userDirPath, baseImage, mainServices, packageInfoDict = repoManager.getVMIData(vmiName)

        if userDirPath is None \
                or baseImage is None\
                or mainServices is None\
                or packageInfoDict is None:
            sys.exit("Error while reassembling VMI \"%s\". Insufficient Data in database" % vmiName)

        if not os.path.isfile(baseImage.pathToVMI):
            sys.exit("Error while reassembling: Base Image \"%s\" does not exist" % baseImage.pathToVMI)
        if not os.path.isfile(userDirPath):
            sys.exit("Error while reassembling: Compressed User Directory \"%s\" does not exist" % userDirPath)


        format = baseImage.pathToVMI.split(".")[-1]
        if vmiName.endswith(".qcow2") or vmiName.endswith(".img"):
            pathToVMI = StaticInfo.relPathLocalVMIFolder + "/" + vmiName.rsplit(".",1)[0] + "." + format
        else:
            pathToVMI = StaticInfo.relPathLocalVMIFolder + "/" + vmiName + "." + format

        if os.path.isfile(pathToVMI):
            sys.exit("Error while reassembling VMI \"%s\". \"%s\" already exists. Was it reassembled before?" % (vmiName, pathToVMI))


        print "Copy of Base Image is being created..."
        startTime = time.time()
        shutil.copy(baseImage.pathToVMI, pathToVMI)
        copyTime = time.time() - startTime

        # Reset Image
        startTime = time.time()
        VMIManipulator.resetImage(pathToVMI)
        resetTime = time.time() - startTime

        # Create handler
        startTime = time.time()
        print ('Creating GuestFS Handle...')
        (guest, root) = GuestFSHelper.getHandle(pathToVMI, rootRequired=True)
        handlerCreationTime = time.time() - startTime

        manipulator = VMIManipulator.getVMIManipulator(pathToVMI, vmiName, guest, root)
        selinux = manipulator.checkSELinux()


        # Import Home
        manipulator.importHomeDir(userDirPath)

        # Import Packages
        startTime = time.time()
        errorString = Reassembler.importPackages(manipulator, baseImage, mainServices, packageInfoDict, evalReassembly=evalReassembly)
        importTime = time.time() - startTime

        GuestFSHelper.shutdownHandle(guest)

        # Relabel SELinux filesystem
        if selinux:
            VMIManipulator.relabelSELinux(pathToVMI)

        if errorString is None:
            print "\nReassembling finished."
            print "\tVMI saved in \"%s\"" % pathToVMI
        else:
            logFileName = pathToVMI.rsplit(".",1)[0] + "_ERROR.log"
            with open(logFileName, "w+") as log:
                log.write(errorString)
            print "\nReassembling finished."
            print "\tIMPORTANT: Importing packages exited with errors."
            print "\t           It is assumed that the errors were due to missing user interaction but that the services work anyway."
            print "\t           Inspecting the log is advised!"
            print "\t           Log saved in: \"%s\"" % logFileName
            print "\t           VMI saved in: \"%s\"" % pathToVMI

        if evalReassembly is not None:
            evalReassembly.vmiFilename = pathToVMI.rsplit("/",1)[-1]
            evalReassembly.vmiMainServices = mainServices
            evalReassembly.pathToBase = baseImage.pathToVMI.rsplit("/",1)[-1]
            evalReassembly.baseImageSize = os.path.getsize(baseImage.pathToVMI)
            evalReassembly.copyTime = copyTime
            evalReassembly.resetTime = resetTime
            evalReassembly.importTime = importTime
            evalReassembly.handlerCreationTime = handlerCreationTime
            if errorString is not None:
                evalReassembly.info = "\"/dev/pts\" error while reassembling, check manually."

        return pathToVMI


    @staticmethod
    def importPackages(manipulator, baseImage, mainServices, packageInfoDict, evalReassembly=None):

        allPkgsNum = len(packageInfoDict)
        allPkgsSize = 0
        reqPkgsSize = 0

        # Filter which packages already exist in VMI
        vmiPackageDict = baseImage.getNodeData()
        reqPackagesFileNames = list()

        for pkgName,pkgInfo in packageInfoDict.iteritems():
            if not (
                    pkgName in vmiPackageDict and
                    vmiPackageDict[pkgName][StaticInfo.dictKeyVersion] == pkgInfo[StaticInfo.dictKeyVersion] and
                    vmiPackageDict[pkgName][StaticInfo.dictKeyArchitecture] == pkgInfo[StaticInfo.dictKeyArchitecture]
                ):
                reqPackagesFileNames.append(pkgInfo[StaticInfo.dictKeyFilePath])
                reqPkgsSize = reqPkgsSize + int(pkgInfo[StaticInfo.dictKeyInstallSize])
            allPkgsSize = allPkgsSize + int(pkgInfo[StaticInfo.dictKeyInstallSize])

        reqPkgNum = len(reqPackagesFileNames)
        print "Package Import:\n\t" \
              "Main Service(s):\t\t\t%s\n\t" \
              "Package(s) required:\t\t%i\n\t" \
              "Already existing in VMI:\t%i\n\t" \
              "Package(s) to be imported:\t%i" \
              % (",".join(mainServices), allPkgsNum, allPkgsNum - reqPkgNum, reqPkgNum)

        errorString = manipulator.importPackages(mainServices, reqPackagesFileNames)

        if evalReassembly is not None:

            evalReassembly.reqPkgsNum = allPkgsNum
            evalReassembly.impPkgsNum = reqPkgNum
            evalReassembly.reqPkgsSize = allPkgsSize
            evalReassembly.impPkgsSize = reqPkgsSize

        return errorString