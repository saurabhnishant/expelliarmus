from abc import ABCMeta, abstractmethod
from collections import defaultdict

import sys


class Evaluation:
    __metaclass__ = ABCMeta
    def __init__(self, evaluationLogPath):
        self.evaluationLogPath = evaluationLogPath
        self.lines = []

    def saveEvaluation(self):
        output = "\n".join(self.lines)
        open(self.evaluationLogPath, "w+").write(output)

    @abstractmethod
    def newLine(self): pass

class SimilarityToAllEvaluation(Evaluation):
    def __init__(self, evaluationLogPath, sortedVmiFileNames):
        super(SimilarityToAllEvaluation, self).__init__(evaluationLogPath)
        self.sortedVmiFileNames = sortedVmiFileNames
        # First line in output
        self.lines.append(";" + ";".join(self.sortedVmiFileNames))
        self.similarities = defaultdict(dict)

    def newLine(self):pass

    def saveEvaluation(self):
        for vmi1FileName in self.sortedVmiFileNames:
            line = vmi1FileName
            for vmi2FileName in self.sortedVmiFileNames:
                line = line + ";" + str(self.similarities[vmi1FileName][vmi2FileName])
            self.lines.append(line)
        super(SimilarityToAllEvaluation, self).saveEvaluation()

class DecompositionEvaluation(Evaluation):
    def __init__(self, evaluationLogPath):
        super(DecompositionEvaluation, self).__init__(evaluationLogPath)
        # First line in output
        self.lines.append("vmiFilename;vmi main services;"
                          "sumOrigStorageSize[bytes];RepoStorageSize[bytes];dbSize[bytes];"
                          "timeDecomp[s];timeHandlerCreation[s];timeExport[s];"
                          "reqPkgsNum;expPkgsNum;"
                          "reqPkgsSize[bytes];expPkgsSize[bytes];"
                          "baseImageInfo;"
                          "highest similarity;base with highest similarity;numPkgs in master;comparisons;time to calc sim")
        self.vmiFilename = None
        self.vmiMainServices = None
        self.sumRepoStorageSize = None
        self.dbSize = None
        self.timeDecompAll = None
        self.timeHandlerCreation = None
        self.timeExport = None
        self.reqPkgsNum = None
        self.expPkgsNum = None
        self.reqPkgsSize = None
        self.expPkgsSize = None
        self.baseImageInfo = None

        # Info about calculation of similarity to master
        self.comparisons = 0
        self.simToMaster = None
        self.masterPathToImage = None
        self.masterNumPkgs = None
        self.timeSimToMasterCalc = None

        # no reset, current VMI size is added
        self.sumOrigStorageSize = 0

    def resetAttributes(self):
        self.vmiFilename = None
        self.vmiMainServices = None
        self.sumRepoStorageSize = None
        self.dbSize = None
        self.timeDecompAll = None
        self.timeHandlerCreation = None
        self.timeExport = None
        self.reqPkgsSize = None
        self.expPkgsSize = None
        self.baseImageInfo = None

        self.comparisons = 0
        self.simToMaster = None
        self.masterPathToImage = None
        self.masterNumPkgs = None
        self.timeSimToMasterCalc = None

    def addVmiOrigSize(self, vmiOrigSize):
        self.sumOrigStorageSize = self.sumOrigStorageSize + vmiOrigSize

    def setSimilarity(self, simAndMasterList):
        self.comparisons = len(simAndMasterList)
        for (similarity,master) in simAndMasterList:
            if self.simToMaster is None or similarity > self.simToMaster:
                self.simToMaster = similarity
                self.masterPathToImage = master.pathToVMI
                self.masterNumPkgs = master.getNumberOfPackages()

    def newLine(self):
        self.lines.append(self.vmiFilename + ";" +
                          ",".join(self.vmiMainServices) + ";" +
                          str(self.sumOrigStorageSize) + ";" +
                          str(self.sumRepoStorageSize) + ";" +
                          str(self.dbSize) + ";" +
                          str(self.timeDecompAll) + ";" +
                          str(self.timeHandlerCreation) + ";" +
                          str(self.timeExport) + ";" +
                          str(self.reqPkgsNum) + ";" +
                          str(self.expPkgsNum) + ";" +
                          str(self.reqPkgsSize) + ";" +
                          str(self.expPkgsSize) + ";" +
                          self.baseImageInfo + ";" +
                          str(self.simToMaster) + ";" +
                          str(self.masterPathToImage) + ";" +
                          str(self.masterNumPkgs) + ";" +
                          str(self.comparisons) + ";" +
                          str(self.timeSimToMasterCalc))
        self.resetAttributes()

class ReassemblingEvaluation(Evaluation):
    def __init__(self, evaluationLogPath):
        super(ReassemblingEvaluation, self).__init__(evaluationLogPath)
        # First line in output
        self.lines.append("vmiFilename;used base image;base image size [bytes];"
                          "vmi main services;vmi size [bytes];"
                          "reassembling time [s];copy time [s];reset time [s];import time [s];handler creation time [s];"
                          "number of required packages;number of imported packages;"
                          "required PkgsSize[bytes];imported PkgsSize[bytes];"
                          "reassembling info")
        self.vmiFilename = None
        self.vmiMainServices = None
        self.vmiSize = None
        self.pathToBase = None
        self.baseImageSize = None
        self.reassemblingTime = None
        self.copyTime = None
        self.resetTime = None
        self.importTime = None
        self.handlerCreationTime = None
        self.reqPkgsNum = None
        self.expPkgsNum = None
        self.reqPkgsSize = None
        self.impPkgsSize = None
        self.info = None

    def resetAttributes(self):
        self.vmiFilename = None
        self.vmiMainServices = None
        self.vmiSize = None
        self.pathToBase = None
        self.baseImageSize = None
        self.reassemblingTime = None
        self.copyTime = None
        self.resetTime = None
        self.importTime = None
        self.handlerCreationTime = None
        self.reqPkgsNum = None
        self.expPkgsNum = None
        self.reqPkgsSize = None
        self.impPkgsSize = None
        self.info = None

    def newLine(self):
        self.lines.append(self.vmiFilename + ";" +
                          self.pathToBase + ";" +
                          str(self.baseImageSize) + ";" +
                          ",".join(self.vmiMainServices) + ";" +
                          str(self.vmiSize) + ";" +
                          str(self.reassemblingTime) + ";" +
                          str(self.copyTime) + ";" +
                          str(self.resetTime) + ";" +
                          str(self.importTime) + ";" +
                          str(self.handlerCreationTime) + ";" +
                          str(self.reqPkgsNum) + ";" +
                          str(self.impPkgsNum) + ";" +
                          str(self.reqPkgsSize) + ";" +
                          str(self.impPkgsSize) + ";" +
                          str(self.info))
        self.resetAttributes()













