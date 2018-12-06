import guestfs
import re
import sys
from abc import ABCMeta, abstractmethod

import networkx as nx
import os
from enum import IntEnum

from StaticInfo import StaticInfo


class VMIGraph:
    __metaclass__ = ABCMeta
    GNodeAttrName = "name"
    GNodeAttrVersion = "version"
    GNodeAttrArchitecture = "architecture"
    GNodeAttrEssential = "essential"
    GNodeAttrInstallSize = "size"
    GNodeAttrFilePath = "path"
    GEdgeAttrConstraint = "constraint"
    GEdgeAttrOperator = "operator"
    GEdgeAttrVersion = "version"

    @staticmethod
    def createGraph(guest, pkgManagement, verbose=False):
        if pkgManagement == "apt":
            return VMIGraph.createGraphAPT(guest, verbose=verbose)
        elif pkgManagement == "dnf":
            return VMIGraph.createGraphDNF(guest, verbose=verbose)
        else:
            sys.exit("ERROR in VMIGraph: trying to create Graph for VMI with unsupported package manager \"%s\"" % pkgManagement)

    @staticmethod
    def createGraphAPT(guest, verbose=False):
        # Enum more understandable list access
        class Q(IntEnum):
            Name        = 0
            Version     = 1
            Arch        = 2
            Essential   = 3
            InstallSize = 4
            Depends     = 5
            PreDepends  = 6

        # Regular Expressions for pattern matching Package's info
        patternPkgName = r"([^(): ]*)"
        patternArch = r"(?:: *([^(): ]*))?"
        patternVersionConstraint = r"(?:\( *([^()]*) *\))?"
        depMatcher = re.compile(r"^ *" + patternPkgName + " *" + patternArch + " *" + patternVersionConstraint + " *$")

        # Init Graph
        graph = nx.MultiDiGraph()

        # Obtain Package Data from guest
        # install size is in kbytes
        pkgsInfoString = guest.sh(
            "dpkg-query --show --showformat='${Package};${Version};${Architecture};${Essential};${Installed-Size};${Depends};${Pre-Depends}\\n'")[:-1]
        # returns lines of form "curl;1.1;amd64;no;dep1, dep2,...;dep3, dep4,..."

        # List of node names and attributes
        pkgsInfo = []   # in the form of [(pkg,{name:"pkg", version:"1.1", architecture:"amd64", essential:False, installsize:10})]
        pkgHelperDict = dict()
        for line in pkgsInfoString.split("\n"):
            lineData = line.split(";")
            essentialPkg = True if lineData[Q.Essential] == "yes" else False
            pkgsInfo.append((lineData[Q.Name],
                             {
                                 StaticInfo.dictKeyName: lineData[Q.Name],
                                 StaticInfo.dictKeyVersion: lineData[Q.Version],
                                 StaticInfo.dictKeyArchitecture: lineData[Q.Arch],
                                 StaticInfo.dictKeyEssential: essentialPkg,
                                 StaticInfo.dictKeyInstallSize: int(lineData[Q.InstallSize])*1000,
                                 StaticInfo.dictKeyFilePath: None
                            }))
            pkgHelperDict[lineData[Q.Name]] = {StaticInfo.dictKeyName: lineData[Q.Name],
                                               StaticInfo.dictKeyVersion: lineData[Q.Version],
                                               StaticInfo.dictKeyArchitecture: lineData[Q.Arch],
                                               StaticInfo.dictKeyEssential: essentialPkg,
                                               StaticInfo.dictKeyInstallSize: int(lineData[Q.InstallSize])*1000,
                                               StaticInfo.dictKeyFilePath: None}

        # List of edge data (fromNode, toNode and attributes)
        depList = []  # in the form of [(pkg,deppkg,{constraint:True, operator:">=", version:"1.6"})]
        for line in pkgsInfoString.split("\n"):
            lineData = line.split(";")
            deps = [dep for dep in (lineData[Q.Depends] + "," + lineData[Q.PreDepends]).split(",") if dep != ""]
            for dep in deps:
                #print lineData[Q.Name] + ": \"" + dep + "\""
                for depPossibility in dep.split("|"):
                    #print "\"" + depPossibility + "\""
                    matchResult = depMatcher.match(depPossibility)
                    if not matchResult:
                        sys.exit("ERROR: Could not match Dependency line: \"" + lineData[Q.Name] + "\" -> \"" + depPossibility + "\"")
                    if matchResult:
                        depPkgName = matchResult.group(1)
                        depPkgArch = matchResult.group(2)
                        depPkgVersConstraint = matchResult.group(3)
                        Zinstalled = depPkgName in pkgHelperDict
                        #if Zinstalled:
                        #    ZarchSpecified = depPkgArch == None
                        #    ZarchAny       = depPkgArch == "any"
                        #    ZArchAllAllowed= pkgHelperDict[depPkgName]["architecture"] == "all"
                        if depPkgName in pkgHelperDict and (depPkgArch == None or depPkgArch == "any" or pkgHelperDict[depPkgName][StaticInfo.dictKeyArchitecture] == "all"):
                            constraint = False
                            operator = ""
                            version = ""
                            if depPkgVersConstraint != None:
                                versConstraintTuple = depPkgVersConstraint.split(" ")
                                if len(versConstraintTuple) != 2:
                                    sys.exit("Error could not read Version constraint tuple: \"" + str(versConstraintTuple) + "\"")
                                constraint = True
                                operator = versConstraintTuple[0]
                                version = versConstraintTuple[1]
                            depList.append((lineData[Q.Name],depPkgName,
                                            {
                                                StaticInfo.dictKeyConstraint:constraint,
                                                StaticInfo.dictKeyOperator:operator,
                                                StaticInfo.dictKeyVersion:version}))
                            break # innermost for loop: possible packages that satisfy dependency, first is taken here

        # Fill Graph with nodes and edges
        graph.add_nodes_from(pkgsInfo)
        graph.add_edges_from(depList)
        return graph

    @staticmethod
    def createGraphDNF(guest, verbose=False):
        # Enum more understandable list access
        class Q(IntEnum):
            Name = 0
            Version = 1
            Arch = 2
            InstallSize = 3

        ignoreSet = {"filesystem"}
        ignoredPackages = set()

        # Regular Expressions for pattern matching Package's info
        patternLevel = r"\(level [0-9]*\)"
        patternPkgName = r"([^ ]*)"
        depMatcher = re.compile(r"^" + patternLevel + " " + patternPkgName + " -> " + patternPkgName + " *$")

        # Init Graph
        graph = nx.MultiDiGraph()

        # tag size specifies installsize in bytes
        # see http://ftp.rpm.org/max-rpm/ch-queryformat-tags.html
        # Obtain Package Data from guest
        pkgsInfoString = guest.sh(
            "rpm --query --all --queryformat "
            "'%{NAME};%{VERSION};%{ARCH};%{SIZE}\n'")[:-1]
        # returns lines of form "curl;1.1;amd64;10"

        # List of node names and attributes
        pkgsInfo = []  # in the form of [(pkg,{name:"pkg", version:"1.1", architecture:"amd64", essential:False, installsize:10})]
                       # essential not present in dnf
        pkgHelperDict = dict()
        for line in pkgsInfoString.split("\n"):
            lineData = line.split(";")
            if lineData[Q.Name] in ignoreSet:
                ignoredPackages.add(lineData[Q.Name])
            else:
                pkgsInfo.append((lineData[Q.Name],
                                 {
                                     StaticInfo.dictKeyName: lineData[Q.Name],
                                     StaticInfo.dictKeyVersion: lineData[Q.Version],
                                     StaticInfo.dictKeyArchitecture: lineData[Q.Arch],
                                     StaticInfo.dictKeyEssential: False,
                                     StaticInfo.dictKeyInstallSize: lineData[Q.InstallSize],
                                     StaticInfo.dictKeyFilePath: None
                                 }))
                pkgHelperDict[lineData[Q.Name]] = {StaticInfo.dictKeyName: lineData[Q.Name],
                                                   StaticInfo.dictKeyVersion: lineData[Q.Version],
                                                   StaticInfo.dictKeyArchitecture: lineData[Q.Arch],
                                                   StaticInfo.dictKeyEssential: False,
                                                   StaticInfo.dictKeyInstallSize: lineData[Q.InstallSize],
                                                   StaticInfo.dictKeyFilePath: None}

        graph.add_nodes_from(pkgsInfo)


        # Obtain Package Dependencies from guest
        vmiPathDepInfo = "/var/tempDependencies.txt"

        try:
            guest.sh("rpmdep -level --all > %s" % vmiPathDepInfo)
        except RuntimeError as e:
            if "WARNING (name2pac) can not find who provides " in e.message:
                pass
            else:
                sys.exit("ERROR while fetching dependency information from guest:\n" + e.message)

        guest.download(vmiPathDepInfo, StaticInfo.relPathLocalRepositoryTempDepInfo)
        guest.rm_rf(vmiPathDepInfo)

        pkgsDepString = open(StaticInfo.relPathLocalRepositoryTempDepInfo, "r").read()
        os.remove(StaticInfo.relPathLocalRepositoryTempDepInfo)

        # List of edge data (fromNode, toNode and attributes)
        depList = []  # in the form of [(pkg,deppkg,{constraint:True, operator:">=", version:"1.6"})]

        for line in pkgsDepString.split("\n"):
            matchResult = depMatcher.match(line)
            if not matchResult:
                #print "ERROR: Could not match Dependency line: \"%s\"" % line
                pass
            if matchResult:
                pkgName = matchResult.group(1)
                depName = matchResult.group(2)
                if ("rpmlib" in pkgName or
                    "rpmlib" in depName or
                    pkgName in ignoreSet or
                    depName in ignoreSet):
                    pass
                elif (pkgName in pkgHelperDict and
                      depName in pkgHelperDict):
                    depList.append((pkgName, depName))
                    depList.append((pkgName, depName,
                                    {
                                        StaticInfo.dictKeyConstraint: False,
                                        StaticInfo.dictKeyOperator: "",
                                        StaticInfo.dictKeyVersion: ""}))

                else:
                    print "Not processed: %s -> %s" % (pkgName, depName)

        graph.add_edges_from(depList)
        if verbose==True and len(ignoredPackages) > 0:
            print "\tThe following packages were ignored while creating the VMI graph:"
            print "\t\t" + ",".join(ignoredPackages)
        return graph