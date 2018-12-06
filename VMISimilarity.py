import sys
from collections import defaultdict

from StaticInfo import StaticInfo
from GuestFSHelper import GuestFSHelper
from VMIDescription import VMIDescriptor

class SimilarityCalculator:
    @staticmethod
    def checkMainServicesExistence(vmiDescriptor1,mainServices):
        for pkgName in mainServices:
            if not vmiDescriptor1.checkIfNodeExists(pkgName):
                sys.exit("Error: Main Service \"" + pkgName + "\" does not exist in " + vmiDescriptor1.pathToVMI)

    @staticmethod
    def checkCompatibility(vmiDescriptor1, vmiDescriptor2):
        if vmiDescriptor1.distribution != vmiDescriptor2.distribution:
            print "Mapping: Check Compatibility failed: distributions differ! (%s vs. %s)" % (
                vmiDescriptor1.distribution, vmiDescriptor2.distribution)
            return False
        if vmiDescriptor1.distributionVersion != vmiDescriptor2.distributionVersion:
            print "Mapping: Check Compatibility failed: distribution versions differ! (%s vs. %s)" % (
                vmiDescriptor1.distributionVersion, vmiDescriptor2.distributionVersion)
            return False
        if vmiDescriptor1.architecture != vmiDescriptor2.architecture:
            print "Mapping: Check Compatibility failed: architectures differ! (%s vs. %s)" % (
                vmiDescriptor1.distributionVersion, vmiDescriptor2.distributionVersion)
            return False
        return True

    @staticmethod
    def computeSimilarityBetweenVMIDescriptorsSimple(vmi1, vmi2, onlyOnMainServices):
        """
        :param VMIDescriptor vmi1:
        :param VMIDescriptor vmi2:
        :param Boolean onlyOnMainServices:
        :return:
        """

        def max(x, y):
            if x > y:
                return x
            else:
                return y

        g1NodesDict = vmi1.getNodeData()
        g2NodesDict = vmi2.getNodeData()
        numG1Nodes = len(g1NodesDict)
        numG2Nodes = len(g2NodesDict)

        # similarity =
        #                 |matching Nodes in nodesToCheck|
        #               / |nodesToCheck|

        if onlyOnMainServices:
            # nodesToCheck: union(mainServices1,mainServices2)
            nodesToCheck = set(vmi1.getNodeDataFromMainServicesSubtrees().keys()) \
                .union(
                set(vmi2.getNodeDataFromMainServicesSubtrees().keys()))
            numAllNodes = len(nodesToCheck)

            # prefilter nodesToCheck by name occurring in both graphs
            nodesToCheck = nodesToCheck.intersection(set(g1NodesDict.keys()))
            nodesToCheck = nodesToCheck.intersection(set(g2NodesDict.keys()))
        else:
            # nodesToCheck: union(g1,g2)
            numAllNodes = len(set(g1NodesDict.keys()).union(set(g2NodesDict.keys())))
            # prefilter nodesToCheck by name occurring in both graphs
            nodesToCheck = set(g1NodesDict.keys()).intersection(set(g2NodesDict.keys()))

        numMatches = 0

        # Check similarity for all (prefiltered) packages
        for pkgName in nodesToCheck:
            pkg1Data = g1NodesDict[pkgName]
            pkg2Data = g2NodesDict[pkgName]
            if (
                    # Version has to be the same
                            pkg1Data[StaticInfo.dictKeyVersion] == pkg2Data[StaticInfo.dictKeyVersion]
                    # Architecture has to be the same, or at least on has to say all
                    and (
                            pkg1Data[StaticInfo.dictKeyArchitecture] == pkg2Data[StaticInfo.dictKeyArchitecture]
                            or pkg1Data[StaticInfo.dictKeyArchitecture] == "all"
                            or pkg2Data[StaticInfo.dictKeyArchitecture] == "all"
                    )
            ):
                numMatches = numMatches + 1

        similarity = float(numMatches) / float(numAllNodes)
        if onlyOnMainServices:
            print "\nComparison of two VMIs (Only on main services!):\n" \
                  "\tVMI 1: %i packages\n" \
                  "\tVMI 2: %i packages\n" \
                  "\t\t %i main service related packages match in name, version and architecture\n" \
                  "\t\t %i compared packages in total (union of main services from both VMIs)\n" \
                  "\t\t similarity = %i/%i = %.3f" \
                  % (numG1Nodes, numG2Nodes, numMatches, numAllNodes, numMatches, numAllNodes, similarity)
        else:
            print "\nComparison of two VMIs:\n" \
                  "\tVMI 1: %i packages\n" \
                  "\tVMI 2: %i packages\n" \
                  "\t\t %i packages match in name, version and architecture\n" \
                  "\t\t similarity = %i/%i = %.3f" \
                  % (numG1Nodes, numG2Nodes, numMatches, numMatches, numAllNodes, similarity)
        return similarity

    @staticmethod
    def computeWeightedSimilarityBetweenVMIDescriptors(vmi1, vmi2, onlyOnMainServices, verbose=True):
        """
        :param VMIDescriptor vmi1:
        :param VMIDescriptor vmi2:
        :param Boolean onlyOnMainServices:
        :return:
        """
        def max(x, y):
            """
            :param Float x:
            :param Float y:
            :return:
            """
            x = float(x)
            y = float(y)
            if x > y:
                return x
            else:
                return y

        g1NodesDict = vmi1.getNodeData()
        g2NodesDict = vmi2.getNodeData()
        numG1Nodes = len(g1NodesDict)
        numG2Nodes = len(g2NodesDict)

        # similarity =
        #                 |(weight * 1) for each matching Node in nodesToCheck|
        #               / |(weight * 1) for each node in nodesToCheck|
        # in variables:
        #                 sumNormSizeMatches
        #               / sumNormSizeAll

        if onlyOnMainServices:
            # nodesToCheck: union(g1-mainServices1,g2-mainServices2)
            nodesToCheck = set(vmi1.getNodeDataFromMainServicesSubtrees().keys())\
                           .union(
                           set(vmi2.getNodeDataFromMainServicesSubtrees().keys()))
        else:
            # nodesToCheck: union(G1,G2)
            nodesToCheck = set(g1NodesDict.keys()).union(set(g2NodesDict.keys()))

        numAllNodes = len(nodesToCheck)

        # determine maximum install size for normalized sizes as weights
        maxInstallSize = 0
        for pkg in nodesToCheck:
            if pkg in g1NodesDict:
                maxInstallSize = max(maxInstallSize, int(g1NodesDict[pkg][StaticInfo.dictKeyInstallSize]))
            if pkg in g2NodesDict:
                maxInstallSize = max(maxInstallSize, int(g2NodesDict[pkg][StaticInfo.dictKeyInstallSize]))

        # calculate sumNormSizeAll as sum of normalized sizes (weights)
        sumNormSizeAll = 0.0
        for pkg in nodesToCheck:
            if pkg in g1NodesDict and pkg in g2NodesDict:
                sumNormSizeAll = sumNormSizeAll +\
                                 max(g1NodesDict[pkg][StaticInfo.dictKeyInstallSize],
                                     g2NodesDict[pkg][StaticInfo.dictKeyInstallSize])/maxInstallSize
            elif pkg in g1NodesDict:
                sumNormSizeAll = sumNormSizeAll + \
                                 float(g1NodesDict[pkg][StaticInfo.dictKeyInstallSize]) / maxInstallSize
            elif pkg in g2NodesDict:
                sumNormSizeAll = sumNormSizeAll + \
                                 float(g2NodesDict[pkg][StaticInfo.dictKeyInstallSize]) / maxInstallSize

        # prefilter nodesToCheck by name occurring in both graphs
        nodesToCheck = nodesToCheck.intersection(set(g1NodesDict.keys()))
        nodesToCheck = nodesToCheck.intersection(set(g2NodesDict.keys()))

        numMatches = 0
        sumNormSizeMatches = 0.0

        # Check similarity for all (prefiltered) packages
        for pkgName in nodesToCheck:
            pkg1Data = g1NodesDict[pkgName]
            pkg2Data = g2NodesDict[pkgName]
            if (
                    # Version has to be the same
                    pkg1Data[StaticInfo.dictKeyVersion] == pkg2Data[StaticInfo.dictKeyVersion]
                    # Architecture has to be the same, or at least one has to say all
                    and (
                            pkg1Data[StaticInfo.dictKeyArchitecture] == pkg2Data[StaticInfo.dictKeyArchitecture]
                            or pkg1Data[StaticInfo.dictKeyArchitecture] == "all"
                            or pkg2Data[StaticInfo.dictKeyArchitecture] == "all"
                    )
            ):
                numMatches = numMatches + 1
                sumNormSizeMatches = sumNormSizeMatches\
                                     + max(pkg1Data[StaticInfo.dictKeyInstallSize],
                                           pkg2Data[StaticInfo.dictKeyInstallSize])/maxInstallSize

        similarity = float(sumNormSizeMatches) / float(sumNormSizeAll)

        if verbose:
            if onlyOnMainServices:
                print "\nWeighted Comparison of two VMIs (Only on main services!):\n" \
                      "\tGraph 1: %i packages\n" \
                      "\tGraph 2: %i packages\n" \
                      "\t\t %i main service related packages match in name, version and architecture\n" \
                      "\t\t %i compared packages in total (union of main services from both VMIs)\n" \
                      "\t\t similarity = %.3f/%.3f = %.3f" \
                      % (numG1Nodes, numG2Nodes, numMatches, numAllNodes, sumNormSizeMatches, sumNormSizeAll, similarity)
            else:
                print "\nWeighted Comparison of two VMIs:\n" \
                      "\tVMI 1: %i packages\n" \
                      "\tVMI 2: %i packages\n" \
                      "\t\t %i packages match in name, version and architecture\n" \
                      "\t\t similarity = %i/%i = %.3f" \
                      % (numG1Nodes, numG2Nodes, numMatches, sumNormSizeMatches, numAllNodes, similarity)
        return similarity

    @staticmethod
    def computeSimilarityOneToOne(pathToVMI1, mainServices1, pathToVMI2, mainServices2, onlyOnMainServices):

        # Create Descriptors/Graphs for each VMI
        print "\n=== Creating Descriptor for VMI \"%s\"" % (pathToVMI1)
        (guest, root) = GuestFSHelper.getHandle(pathToVMI1, rootRequired=True)
        vmi1 = VMIDescriptor(pathToVMI1, "internal_vmi1", mainServices1, guest, root)
        GuestFSHelper.shutdownHandle(guest)

        print "\n=== Creating Descriptor for VMI \"%s\"" % (pathToVMI2)
        (guest, root) = GuestFSHelper.getHandle(pathToVMI2, rootRequired=True)
        vmi2 = VMIDescriptor(pathToVMI2, "internal_vmi2", mainServices2, guest, root)
        GuestFSHelper.shutdownHandle(guest)

        # Check if Main Services exist
        SimilarityCalculator.checkMainServicesExistence(vmi1, mainServices1)
        SimilarityCalculator.checkMainServicesExistence(vmi2, mainServices2)

        # Compute Similarity
        graphSimilarity = SimilarityCalculator.computeWeightedSimilarityBetweenVMIDescriptors(vmi1, vmi2, onlyOnMainServices)
        return graphSimilarity

    @staticmethod
    def computeSimilarityManyToMany(vmiData, onlyOnMainServices):
        if onlyOnMainServices:
            print "=====Calculating similarities with respect to main services between each of %i VMIs" % len(vmiData)
        else:
            print "=====Calculating similarities between each of %i VMIs" % len(vmiData)

        sortedVMIDescriptorList = list()
        count = 0
        for (pathToVMI, vmiFileName, mainServices) in vmiData:
            count = count + 1
            print "Creating Descriptor for vmi \"%s\" (%i/%i)..." % (vmiFileName, count, len(vmiData))
            (guest, root) = GuestFSHelper.getHandle(pathToVMI, rootRequired=True)
            vmi = VMIDescriptor(pathToVMI, vmiFileName, mainServices, guest, root)
            GuestFSHelper.shutdownHandle(guest)
            sortedVMIDescriptorList.append(vmi)

        similarities = defaultdict(dict)
        for vmi1 in sortedVMIDescriptorList:
            print "Similarities for VMI \"%s\":" % vmi1.vmiName
            for vmi2 in sortedVMIDescriptorList:
                if vmi1.pathToVMI == vmi2.pathToVMI:
                    similarities[vmi1.vmiName][vmi2.vmiName] = None
                else:
                    # Check if Main Services exist
                    SimilarityCalculator.checkMainServicesExistence(vmi1, vmi1.mainServices)
                    SimilarityCalculator.checkMainServicesExistence(vmi2, vmi2.mainServices)

                    sim = SimilarityCalculator.computeWeightedSimilarityBetweenVMIDescriptors(vmi1, vmi2,
                                                                                              onlyOnMainServices,
                                                                                              verbose=False)
                    similarities[vmi1.vmiName][vmi2.vmiName] = sim
                    print "\t%0.2f similarity to VMI \"%s\"" % (sim, vmi2.vmiName)
        return similarities

    @staticmethod
    def computeSimilarityManyToManyOLD(vmisAndMS, onlyOnMainServices):
        if onlyOnMainServices:
            print "=====Calculating similarities with respect to main services between each of %i VMIs" % len(vmisAndMS)
        else:
            print "=====Calculating similarities between each of %i VMIs" % len(vmisAndMS)

        sortedVMIDescriptorList = list()
        i = 0
        for (vmiFileName,mainServices) in vmisAndMS:
            i = i + 1
            print "Creating Descriptor for vmi \"%s\" (%i/%i)..." % (vmiFileName, i, len(vmisAndMS))
            pathToVMI = StaticInfo.relPathLocalVMIFolder + "/" + vmiFileName
            (guest, root) = GuestFSHelper.getHandle(pathToVMI, rootRequired=True)
            vmi = VMIDescriptor(pathToVMI, vmiFileName, mainServices, guest, root)
            GuestFSHelper.shutdownHandle(guest)
            sortedVMIDescriptorList.append(vmi)

        similarities = defaultdict(dict)
        for vmi1 in sortedVMIDescriptorList:
            print "Similarities for VMI \"%s\":" % vmi1.vmiName
            for vmi2 in sortedVMIDescriptorList:
                if vmi1.pathToVMI == vmi2.pathToVMI:
                    similarities[vmi1.vmiName][vmi2.vmiName] = None
                else:
                    # Check if Main Services exist
                    SimilarityCalculator.checkMainServicesExistence(vmi1, vmi1.mainServices)
                    SimilarityCalculator.checkMainServicesExistence(vmi2, vmi2.mainServices)

                    sim = SimilarityCalculator.computeWeightedSimilarityBetweenVMIDescriptors(vmi1, vmi2,
                                                                                              onlyOnMainServices, verbose=False)
                    similarities[vmi1.vmiName][vmi2.vmiName] = sim
                    print "\t%0.2f similarity to VMI \"%s\"" % (sim,vmi2.vmiName)
        return similarities



























