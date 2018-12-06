from abc import ABCMeta, abstractmethod
import networkx as nx
import os
from StaticInfo import StaticInfo
from VMIGraph import VMIGraph


class BaseImageDescriptor():
    __metaclass__ = ABCMeta
    def __init__(self, pathToVMI):
        self.pathToVMI = pathToVMI
        self.distribution = None
        self.distributionVersion = None
        self.architecture = None
        self.pkgManager = None
        self.graph = None  # type: nx.MultiDiGraph
        self.graphFileName = None


    def initializeNew(self, guest, root, verbose=False):
        #print "Creating new Descriptor for \"%s\"" % self.pathToVMI
        self.distribution = guest.inspect_get_distro(root)
        self.distributionVersion = str(guest.inspect_get_major_version(root)) + \
                                   "_" + \
                                   str(guest.inspect_get_minor_version(root))
        self.architecture = guest.inspect_get_arch(root)
        self.pkgManager = guest.inspect_get_package_management(root)
        self.graph = VMIGraph.createGraph(guest, self.pkgManager, verbose=verbose)

    def initializeFromRepo(self, distribution, distributionVersion, architecture, pkgManager, graphFileName):
        self.distribution = distribution
        self.distributionVersion = distributionVersion
        self.architecture = architecture
        self.pkgManager = pkgManager
        self.graphFileName = graphFileName
        self.graph = nx.read_gpickle(graphFileName)

    def saveGraph(self):
        if self.graphFileName is None:
            self.graphFileName = "_".join(self.pathToVMI.rsplit(".",1)) + ".pkl"
        if os.path.isfile(self.graphFileName):
            os.remove(self.graphFileName)
        nx.write_gpickle(self.graph, self.graphFileName)

    def getVMIMasterDescriptor(self):
        master = VMIMasterDescriptor(self.pathToVMI)
        master.createNew(self.distribution, self.distributionVersion,
                         self.architecture, self.pkgManager, self.graph, [])
        return master

    def getNodeData(self):
        assert (self.graph != None)
        return dict((pkgName, pkgInfo) for (pkgName, pkgInfo) in self.graph.nodes(data=True))

    def getNumberOfPackages(self):
        return len(self.graph)

    def getPkgsInstallSize(self):
        size = 0
        for pkg, pkgInfo in self.graph.nodes(data=True):
            size = size + int(pkgInfo[StaticInfo.dictKeyInstallSize])
        return size

    def getSubGraphFromRoots(self, rootNodeList):
        nodeList = list()
        for name in rootNodeList:
            nodeList = nodeList + list(nx.bfs_tree(self.graph, name))
        return nx.MultiDiGraph(self.graph.subgraph(nodeList))

    def getSubGraphFromRootsOLD(self, rootNodeList):
        nodeList = list()
        for name in rootNodeList:
            nodeList.append(nx.bfs_tree(self.graph, name))
        return nx.MultiDiGraph(self.graph.subgraph(nodeList))

    def getNodeDataFromSubTree(self, rootNode):
        nodeList = nx.bfs_tree(self.graph, rootNode)
        NodeDataDict = dict((pkgName, pkgInfo) for (pkgName, pkgInfo) in self.graph.subgraph(nodeList).nodes(data=True))
        return NodeDataDict

    def getNodeDataFromSubTrees(self, rootNodeList):
        result = dict()
        for name in rootNodeList:
            nodeList = nx.bfs_tree(self.graph, name)
            result.update(dict((pkgName, pkgInfo) for (pkgName, pkgInfo) in self.graph.subgraph(nodeList).nodes(data=True)))
        return result

    def checkIfNodeExists(self, nodeName):
        return nodeName in self.graph

    def getListOfNodesContaining (self, name):
        ret = list()
        for node in self.graph.nodes():
            if name in node:
                ret.append(node)
        return ret

    def checkCompatibilityForPackages(self, packageDict, verbose=False):
        """
        :param dict() packageDict:
                in the form of dict{pkgName, pkgInfo} with pkgInfo = dict{version:?, Arch:?,...}
        :return:
        """
        graphNodeData = self.getNodeData()
        if packageDict is None:
            return True
        for pkg2Name,pkg2Data in packageDict.iteritems():
            if pkg2Name in graphNodeData:
                # pkg2 is in graph, version and architecture has to match, otherwise return False:
                pkg1Data = graphNodeData[pkg2Name]
                if not (
                        # Version has to be the same
                        pkg1Data[StaticInfo.dictKeyVersion] == pkg2Data[StaticInfo.dictKeyVersion]
                        # Architecture has to be the same, or at least on has to say all
                        and (
                            pkg1Data[StaticInfo.dictKeyArchitecture] == pkg2Data[StaticInfo.dictKeyArchitecture]
                            or pkg1Data[StaticInfo.dictKeyArchitecture] == "all"
                            or pkg2Data[StaticInfo.dictKeyArchitecture] == "all"
                        )
                ):
                    if verbose:
                        print "Failed Compatibility Check"
                        print "failed on package:"
                        print "\t" + pkg2Name
                        print "\t" + pkg1Data[StaticInfo.dictKeyVersion] + " vs " + pkg2Data[StaticInfo.dictKeyVersion]
                        print "\t" + pkg1Data[StaticInfo.dictKeyArchitecture] + " vs " + pkg2Data[StaticInfo.dictKeyArchitecture]
                    return False
        return True


class VMIDescriptor(BaseImageDescriptor):
    def __init__(self, pathToVMI, vmiName, mainServices, guest, root, verbose=False):
        super(VMIDescriptor, self).__init__(pathToVMI)
        self.vmiName = vmiName
        self.mainServices = mainServices
        self.initializeNew(guest, root, verbose=verbose)

    def getMainServicesDepList(self):
        return [
            (
                mainService,
                self.getNodeDataFromSubTree(mainService)
            )
            for mainService in self.mainServices
        ]

    def getNodeDataFromMainServicesSubtrees(self):
        return self.getNodeDataFromSubTrees(self.mainServices)

    def getSubGraphForMainServices(self):
        return self.getSubGraphFromRoots(self.mainServices)

    def getBaseImageDescriptor(self, guest, root):
        base = BaseImageDescriptor(self.pathToVMI)
        base.initializeNew(guest, root)
        return base

class VMIMasterDescriptor(BaseImageDescriptor):
    def __init__(self, pathToVMI):
        super(VMIMasterDescriptor, self).__init__(pathToVMI)
        self.mainServices = None

    def createNew(self, distribution, distributionVersion, architecture, pkgManager, graph, mainServices):
        self.distribution = distribution
        self.distributionVersion = distributionVersion
        self.architecture = architecture
        self.pkgManager = pkgManager
        self.graph = nx.MultiDiGraph(graph)
        self.mainServices = set(mainServices)
        self.graphFileName = None

    def initializeMasterFromRepo(self, distribution, distributionVersion, architecture, pkgManager, graphFileName, mainServices):
        self.distribution = distribution
        self.distributionVersion = distributionVersion
        self.architecture = architecture
        self.pkgManager = pkgManager
        self.graphFileName = graphFileName
        self.graph = nx.read_gpickle(graphFileName)
        self.mainServices = set(mainServices)

    def saveGraph(self):
        if self.graphFileName is None:
            self.graphFileName = "_".join(self.pathToVMI.rsplit(".",1)) + "_MASTER.pkl"
        if os.path.isfile(self.graphFileName):
            os.remove(self.graphFileName)
        nx.write_gpickle(self.graph, self.graphFileName)

    def getSubGraphForMainServices(self):
        return self.getSubGraphFromRoots(self.mainServices)

    def getNodeDataFromMainServicesSubtrees(self):
        return self.getNodeDataFromSubTrees(self.mainServices)

    def addSubGraph(self, mainServices, newGraph):
        # Check compatibility
        newPkgDict = dict((pkgName, pkgInfo) for (pkgName, pkgInfo) in newGraph.nodes(data=True))
        if not self.checkCompatibilityForPackages(newPkgDict):
            print "ERROR in Mastergraph: trying to add packages that are not compatible to mastergraph!"
            return False

        self.graph = nx.compose(newGraph, self.graph)
        self.mainServices = self.mainServices.union(set(mainServices))