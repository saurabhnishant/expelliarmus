import cmd
import os
import glob
import shutil
import readline
from Expelliarmus import Expelliarmus
from RepositoryDatabase import RepositoryDatabase
from StaticInfo import StaticInfo

# for correct path completion (https://stackoverflow.com/questions/16826172/filename-tab-completion-in-cmd-cmd-of-python)
readline.set_completer_delims(' \t\n')


def _complete_rel_path(path):
    if not path.startswith("/"):
        if os.path.isdir(path):
            return glob.glob(os.path.join(path, '*'))
        else:
            return glob.glob(path+'*')
    else:
        return None

def _complete_arg_list(text, arglist):
    return [i for i in arglist if i.startswith(text)]

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class MainInterpreter(cmd.Cmd):
    prompt = bcolors.OKBLUE + "(Expelliarmus) " + bcolors.ENDC
    _availableArgsList = ("vmis", "packages", "baseimages")
    _availableArgsReassembly = []
    _availableArgsEvaluateFunctions = ["decomposition1", "decomposition2", "reassembly", "similarity"]
    _availableArgsEvaluateOptions = ["--repetitions=", "--path="]

    def __init__(self):
        cmd.Cmd.__init__(self)
        print StaticInfo.cliLogo
        print StaticInfo.cliIntro
        print "\n\n\n\n"
        print StaticInfo.cliIntroHelp

        self.exp = Expelliarmus()

        with RepositoryDatabase() as repo:
            numVMIs = repo.getNumberOfVMIs()
            numBases = repo.getNumberOfBaseImages()
            numPkgs = repo.getNumberOfPackages()
            self._availableArgsReassembly = repo.getAllVmiNames()
            self._availableArgsReassembly.append("all")

        digits = max(len(numVMIs),len(numBases),len(numPkgs))
        print "State of Repository Storage:\n"
        print "\tVMIs:        {0:>{width}s}".format(numVMIs, width=digits)
        print "\tBase Images: {0:>{width}s}".format(numBases, width=digits)
        print "\tPackages:    {0:>{width}s}".format(numPkgs, width=digits)
        print "\nSupported VMI formats: " + ",".join(StaticInfo.validVMIFormats) + "\n\n\n\n"


    def emptyline(self):
        pass

    def do_help(self, arg):
        if arg:
            cmd.Cmd.do_help(self, arg)
        else:
            print ""
            print "Expelliarmus: " + StaticInfo.cliIntro + "\n"
            print "The following Commands are available. Type \"help name\" to get a summary about the command \"name\" and how to use it."
            print "Any path given by the user to specify files or folders has to be relative to the working directory of this program."
            print ""
            print "\tlist       - show information about VMI components currently stored"
            print "\tinspect    - inspect VMIs and define main services"
            print "\tdecompose  - decompose VMIs"
            print "\treassemble - reassemble VMIs"
            print "\tevaluate   - tool to evaluate this program"
            print "\treset      - reset local repository of VMI components"
            print "\texit       - exit program"
            print ""

    def do_list(self, items):
        if items == "vmis":
            self.exp.printVMIs()
        elif items == "packages":
            self.exp.printPackages()
        elif items == "baseimages":
            self.exp.printBaseImages()
        else:
            print "\"%s\" not recognized. Type \"help list\" for possible components to list" % items

    def complete_list(self, text, line, begidx, endidx):
        return [i for i in self._availableArgsList if i.startswith(text)]

    def help_list(self):
        print "\nUsage: list { vmis | packages | baseimages }"
        print ""
        print "\tShows a complete list of VMIs/Packages/Base images that are currently stored in the repository.\n"

    def do_inspect(self, line):
        if line.startswith("/"):
            print "Error: \"%s\" is not a valid path. Please try again with a path relative to the directory of this program." % line
        elif os.path.isfile(line):
            self.exp.inspectVMI(line)
        elif os.path.isdir(line):
            self.exp.inspectVMIsInFolder(line)
        else:
            print "Error: \"%s\" is not a valid path." % line

    def complete_inspect(self, text, line, begidx, endidx):
        return _complete_rel_path(text)

    def help_inspect(self):
        print "\n" \
              "Usage: inspect path\n\n" \
              "\tInspect the VMI specified by \"path\" or all vmis in folder specified by \"path\".\n" \
              "\tThis process allows the user to specify main services for VMIs.\n" \
              "\tCorresponding .meta files required for decomposition are created in the same folder as the inspected VMI(s).\n" \
              "\t" + StaticInfo.cliHintPath + "\n"

    def do_decompose(self, line):
        if line.startswith("/"):
            print "Error: \"%s\" is not a valid path. Please try again with a path relative to the directory of this program." % line
        elif os.path.isfile(line):
            self.exp.decomposeVMI(line)
            with RepositoryDatabase() as repo:
                self._availableArgsReassembly = repo.getAllVmiNames()
                self._availableArgsReassembly.append("all")
        elif os.path.isdir(line):
            self.exp.decomposeVMIsInFolder(line)
            with RepositoryDatabase() as repo:
                self._availableArgsReassembly = repo.getAllVmiNames()
                self._availableArgsReassembly.append("all")
        else:
            print "Error: \"%s\" is not a valid path." % line

    def help_decompose(self):
        print "\nUsage: decompose path"
        print "\n\tDecompose the VMI specified by \"path\" or all VMIs in folder specified by \"path\"."
        print "\tRequires a .meta file for each VMI to be decomposed. This file can be created with command \"inspect\".\n"

    def complete_decompose(self, text, line, begidx, endidx):
        return _complete_rel_path(text)

    def do_reassemble(self, line):
        if line == "all":
            self.exp.reassembleAllVMIs()
        elif line in self._availableArgsReassembly:
            self.exp.reassembleVMI(line)
        else:
            print "Error: VMI name \"%s\" not recognized." % line

    def help_reassemble(self):
        print "\nUsage: reassemble { name | all }"
        print "\n\tReassemble the VMI specified by \"name\" or \"all\" VMIs stored in the repository."
        print "\tA list of available VMIs can be obtained through \"list vmis\".\n"

    def complete_reassemble(self, text, line, begidx, endidx):
        return [i for i in self._availableArgsReassembly if i.startswith(text)]

    def parseRepetitions(self, text):
        try:
            return int(text.rsplit("=", 1)[1])
        except ValueError as e:
            print "Error: %s is not a valid number" % text.rsplit("=", 1)[1]
            return None

    def do_evaluate(self,line):
        args = line.split()
        repetitions = None
        path = None
        func = None

        # no arguments
        if len(args) == 0:
            print "Error: missing arguments. Please consult \"help evaluate\"."
            return

        # one argument, has to be function
        if len(args) < 2:
            func = args[0]

        # two arguments, first option, second functionality
        elif len(args) == 2:
            if args[0].startswith ("--path="):
                path = args[0][7:]
            elif args[0].startswith ("--repetitions="):
                repetitions = self.parseRepetitions(args[0])
                if not repetitions: return
            else:
                print "Error: With two arguments, first has to be an option. Please consult \"help evaluate\"."
                return
            func = args[1]

        # three arguments, two options, one functionality
        elif len(args) == 3:
            # first option
            if args[0].startswith ("--path="):
                path = args[0][7:]
            elif args[0].startswith ("--repetitions="):
                repetitions = self.parseRepetitions(args[0])
                if not repetitions: return
            else:
                print "Error: With three arguments, first two have to be options. Please consult \"help evaluate\"."
                return
            # second option
            # first was repetitions, second has to be path
            if repetitions and args[1].startswith ("--path="):
                path = args[1][7:]
            # first was path, second has to be repetitions
            elif path and args[1].startswith ("--repetitions="):
                repetitions = self.parseRepetitions(args[1])
                if not repetitions: return
            else:
                print "Error: With three arguments, first two have to be options. Please consult \"help evaluate\"."
                return
            func = args[2]

        else:
            print "Error: to many arguments. Please consult \"help evaluate\"."
            return

        # if path set, verify
        if path:
            # check if path is directory
            if path and not os.path.isdir(path):
                print "Error: \"%s\" is not a directory" % path
                return
            # check if path is relative
            if path.startswith("/"):
                print "Error: \"%s\" is not a valid path. Please try again with a path relative to the directory of this program." % path
                return
            # check if all meta files exist
            if not self.exp.verifySourceFolder(path):
                print "Error: Verification of source folder failed. See explanation above."
                return

        # check if functionality valid
        if not func in self._availableArgsEvaluateFunctions:
            print "Error: Functionality \"%s\" not recognized" % func
            return

        # if repetitions not set, set to default
        if not repetitions:
            repetitions = 5

        # check if evaluation folder exists
        if not os.path.isdir(StaticInfo.relPathLocalEvaluation):
            os.mkdir(StaticInfo.relPathLocalEvaluation)

        # check if evaluation folder is empty
        if len(os.listdir(StaticInfo.relPathLocalEvaluation)) > 0:
            print "Evaluation folder \"%s\" is not empty. Please back up any evaluation files in this folder and remove them." % StaticInfo.relPathLocalEvaluation
            return

        # start evaluation
        print ""
        print "\nEvaluated Functionality:              " + func
        if path:
            print "Folder with Images to evaluate:       " + path
        print "Number of repetitions for evaluation: " + str(repetitions)
        print ""

        if repetitions > 5:
            print "You chose to repeat the evaluation process %i times. Depending on the data set, this might take a long time." % repetitions
            answer = raw_input("\tAre you sure you want to continue, yes or no?")
            if answer == "yes":
                pass
            else:
                return

        if func == "similarity":
            if not path:
                print "Error: no path set. Please consult \"help evaluate\"."
                return
            print "\n"
            self.exp.evaluateSimBetweenAll(path)
        elif func == "decomposition1":
            if not path:
                print "Error: no path set. Please consult \"help evaluate\"."
                return
            print "This evaluation requires the local repository to be reset and the directory \"%s\" to be cleared." % StaticInfo.relPathLocalVMIFolder
            if self.do_reset("") and self.clearVmiFolder():
                print "\n"
                self.exp.evaluateDecomposition(path,repetitions, resetBeforeEachDecomposition=False)
        elif func == "decomposition2":
            if not path:
                print "Error: no path set. Please consult \"help evaluate\"."
                return
            print "This evaluation requires the local repository to be reset and the directory \"%s\" to be cleared." % StaticInfo.relPathLocalVMIFolder
            if self.do_reset("") and self.clearVmiFolder():
                print "\n"
                self.exp.evaluateDecomposition(path, repetitions, resetBeforeEachDecomposition=True)
        elif func == "reassembly":
            print "This evaluation requires the directory \"%s\" to be cleared." % StaticInfo.relPathLocalVMIFolder
            if self.clearVmiFolder():
                print "\n"
                self.exp.evaluateReassembly(repetitions)
        else:
            print "Error: Functionality \"%s\" not recognized" % func

    def help_evaluate(self):
        print "\nUsage: evaluate [options] { decomposition1 | decomposition2 | reassembly | similarity }"
        print "\n\tEvaluates the given functionality and saves results in folder \"Evaluations\"."
        print "\nFunctionalities:"
        print "\tdecomposition1"
        print "\t\tEvaluates the decomposition process exploiting semantic redundancy (i.e. using a local repository)."
        print "\t\tOption \"--path\" has to be set to specify a source folder for VMIs (These will only be copied, not manipulated)."
        print "\n\tdecomposition2"
        print "\t\tEvaluates the decomposition process without exploiting semantic redundancy (i.e. not using a local repository)."
        print "\t\tOption \"--path\" has to be set to specify a source folder for VMIs (These will only be copied, not manipulated)."
        print "\n\treassembly"
        print "\t\tEvaluates the reassembly process using any VMI present in the local repository."
        print "\t\tOption \"--path\" is ignored."
        print "\n\tsimilarity"
        print "\t\tEvaluates the similarity between each VMI in source folder."
        print "\t\tOption \"--path\" has to be set to specify a source folder for VMIs (These will not be manipulated)."
        print "\nOptions:"
        print "\t--repetitions=x"
        print "\t\tSpecify number of repetitions for evaluation (default is 5), not applicable for similarity."
        print "\n\t--path=x"
        print "\t\tSpecify source folder with VMIs for evaluation (ignored for evaluation of reassembly)"
        print "\t\tMeta Files for all VMIs have to exist. Files in this folder are not manipulated."
        print ""

    def complete_evaluate(self, text, line, begidx, endidx):
        strings = line.split(" ")
        # complete first argument (option or function)
        if len(strings) == 2:
            # complete path
            if text.startswith("--path="):
                #return _complete_rel_path(text[7:])
                return  list( "--path=" + x for x in _complete_rel_path(text[7:]))
            # complete option
            elif text.startswith("-"):
                return _complete_arg_list(text, self._availableArgsEvaluateOptions)
            else:
                return _complete_arg_list(text, self._availableArgsEvaluateFunctions)
        # complete second argument (option or function)
        elif len(strings) == 3:
            # option
            if text.startswith("-"):
                # complete path
                if text.startswith("--path="):
                    return list("--path=" + x for x in _complete_rel_path(text[7:]))
                # complete option
                else:
                    return _complete_arg_list(text, self._availableArgsEvaluateOptions)
            # function
            else:
                return _complete_arg_list(text, self._availableArgsEvaluateFunctions)
        # complete third argument (function)
        elif len(strings) == 4:
            return _complete_arg_list(text, self._availableArgsEvaluateFunctions)
        else:
            return None

    def do_evaluateOLD(self,line):
        args = line.split()
        if len(args) < 2:
            print "Error: Command evaluate requires at least two arguments."
            return
        elif len(args) == 2:
            repetitions = 5
            func = args[0]
            path = args[1]
        elif len(args) == 3:
            if args[0].startswith("--repetitions="):
                try:
                    repetitions = int(args[0].rsplit("=",1)[1])
                except ValueError as e:
                    print "Error: %s is not a valid number" % args[0].rsplit("=",1)[1]
                    return
                except IndexError as e:
                    print "Error: expected \"--repetitions=x\", received \"%s\" instead." % args[0]
                    return
            else:
                print "Error: with three arguments, first has to be a valid option. \"%s\" was not recognized" % args[0]
                return
            func = args[1]
            path = args[2]
        else:
            print "Error: to many arguments"
            return

        # check if path is directory
        if not os.path.isdir(path):
            print "Error: \"%s\" is not a directory" % path
            return
        # check if path is relative
        if path.startswith("/"):
            print "Error: \"%s\" is not a valid path. Please try again with a path relative to the directory of this program." % path
            return

        # check if all meta files exist
        if not self.exp.verifySourceFolder(path):
            print "Error: Verification of source folder failed. See explanation above."
            return

        # check if evaluation folder exists
        if not os.path.isdir(StaticInfo.relPathLocalEvaluation):
            os.mkdir(StaticInfo.relPathLocalEvaluation)

        # check if evaluation folder is empty
        if len(os.listdir(StaticInfo.relPathLocalEvaluation)) > 0:
            print "Evaluation folder \"%s\" is not empty. Please back up any evaluation files in this folder and remove them." % StaticInfo.relPathLocalEvaluation
            return

        # start evaluation
        print "Evaluation"
        print "\tEvaluated Functionality:              " + func
        print "\tFolder with Images to evaluate:       " + path
        print "\tNumber of repetitions for evaluation: " + str(repetitions)

        if func == "similarity":
            print "\n"
            self.exp.evaluateSimBetweenAll(path)
        elif func == "decomposition1":
            print "This evaluation requires the local repository to be reset and the directory \"%s\" to be cleared." % StaticInfo.relPathLocalVMIFolder
            if self.do_reset("") and self.clearVmiFolder():
                print "\n"
                self.exp.evaluateDecomposition(path,repetitions, resetBeforeEachDecomposition=False)
        elif func == "decomposition2":
            print "This evaluation requires the local repository to be reset and the directory \"%s\" to be cleared." % StaticInfo.relPathLocalVMIFolder
            if self.do_reset("") and self.clearVmiFolder():
                print "\n"
                self.exp.evaluateDecomposition(path, repetitions, resetBeforeEachDecomposition=True)
        elif func == "reassembly":
            print "not implemented yet."
        else:
            print "Error: Functionality \"%s\" not recognized" % func

    def complete_evaluateOLD(self, text, line, begidx, endidx):
        strings = line.split(" ")
        # complete first argument (option or function)
        if len(strings) == 2:
            if text.startswith("-"):
                return _complete_arg_list(text, self._availableArgsEvaluateOptions)
            elif text != "":
                return _complete_arg_list(text, self._availableArgsEvaluateFunctions)
            else:
                return None
        # complete second argument (function or path)
        elif len(strings) == 3:
            # first argument was option, next has to be function
            if strings[1].startswith("-"):
                return _complete_arg_list(text, self._availableArgsEvaluateFunctions)
            # first argument was function, next has to be path
            else:
                return _complete_rel_path(text)
        # complete third argument
        elif len(strings) == 4:
            # second argument was function, next is path
            if strings[2] in self._availableArgsEvaluateFunctions:
                return _complete_rel_path(text)
            # second argument was path, no further args required
            else:
                return None
        else:
            return None

    def do_reset(self, line):
        """
        Reset the repository: Removes all base images, packages, user data and meta data.
        """
        print "Attention: This operation will reset the whole repository -> Baseimages, packages, user data and meta data will be removed!"
        answer = raw_input("\tAre you sure you want to continue, yes or no?")
        if answer == "yes":
            print "\tResetting repository..."
            self.exp.resetRepo()
            print "\tRepository reset."
            return True
        else:
            return False

    def clearVmiFolder(self):
        print "Attention: This operation will clear the directory \"%s\"!" % StaticInfo.relPathLocalVMIFolder
        answer = raw_input("\tAre you sure you want to continue, yes or no?")
        if answer == "yes":
            if os.path.isdir(StaticInfo.relPathLocalVMIFolder):
                shutil.rmtree(StaticInfo.relPathLocalVMIFolder)
            os.mkdir(StaticInfo.relPathLocalVMIFolder)
            print "\tDirectory cleared."
            return True
        else:
            return False

    def do_exit(self, line):
        """
        Exit the program
        """
        return True