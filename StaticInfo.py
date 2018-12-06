

class StaticInfo:
    # paths
    # path to libguestfs build
    absPathLibguestfs = "/home/csat2890/Downloads/libguestfs-1.36.7"
    absPathLibguestfsRun = None

    # List of supported VMI formats/extensions
    validVMIFormats = ["qcow2"]

    # local repository folders
    relPathLocalRepository = "localRepository"
    relPathLocalRepositoryPackages = relPathLocalRepository + "/packages"
    relPathLocalRepositoryPackagesBasic = relPathLocalRepository + "/packages/basic"
    relPathLocalRepositoryBaseImages = relPathLocalRepository + "/BaseImages"
    relPathLocalRepositoryUserFolders = relPathLocalRepository + "/UserFolders"
    relPathLocalRepositoryDatabase = relPathLocalRepository + "/db_repo_metadata.sqlite"

    relPathLocalRepositoryTempDepInfo = "localRepository/tempDependencies.txt"

    # basic files and folders that need to be present
    relPathInitPackages = "files/basic"
    relPathGuestRepoConfigs = "files/VMIRepoConfigFiles"
    relPathGuestRepoConfigUbuntu = relPathGuestRepoConfigs + "/DEB_temprepository.list"
    relPathGuestRepoConfigFedora = relPathGuestRepoConfigs + "/RPM_temprepository.repo"

    relPathLocalVMIFolder = "VMIs"

    relPathLocalEvaluation = "Evaluations"

    relPathDocker = "Docker"
    relPathDockerCreation = relPathDocker + "/Creation"
    relPathDockerHomeFolders = relPathDocker + "/Homefolders"
    relPathDockerRepoScannerUbuntu = relPathDocker + "/RepoScannerUbuntu"
    relPathDockerTempRepo = relPathDocker + "/tempRepository"

    # Dict keys
    dictKeyName = "name"
    dictKeyVersion = "version"
    dictKeyArchitecture = "architecture"
    dictKeyEssential = "essential"
    dictKeyInstallSize = "size"
    dictKeyFilePath = "path"
    dictKeyConstraint = "constraint"
    dictKeyOperator = "operator"

    # basic packages that cannot be repackaged
    basicPackagesDictFedora = {
        "filesystem": {
            dictKeyName: "filesystem",
            dictKeyVersion: "3.2",
            dictKeyArchitecture: "x86_64",
            dictKeyInstallSize: "0",
            dictKeyFilePath: relPathLocalRepositoryPackages + "/basic/fedora/filesystem-3.2-40.fc26.x86_64.rpm"
        },
        "jemalloc": {
            dictKeyName: "jemalloc",
            dictKeyVersion: "4.5.0",
            dictKeyArchitecture: "x86_64",
            dictKeyInstallSize: "666211",
            dictKeyFilePath: relPathLocalRepositoryPackages + "/basic/fedora/jemalloc-4.5.0-1.fc26.x86_64.rpm"
        }
    }

    # CLI Texts
    cliLogo = "\n" \
              "   ______                 _ _ _                                \n" \
              "  |  ____|               | | (_)                               \n" \
              "  | |__  __  ___ __   ___| | |_  __ _ _ __ _ __ ___  _   _ ___ \n" \
              "  |  __| \ \/ / '_ \ / _ \ | | |/ _` | '__| '_ ` _ \| | | / __|\n" \
              "  | |____ >  <| |_) |  __/ | | | (_| | |  | | | | | | |_| \__ \\\n" \
              "  |______/_/\_\ .__/ \___|_|_|_|\__,_|_|  |_| |_| |_|\__,_|___/\n" \
              "              | |                                              \n" \
              "              |_|                                              \n"

    cliIntro = "Functional Decomposition and Reassembly of Virtual Machine Images"
    cliIntroHelp = "Type \"help\" to see a list of available commands.\n" \
                   "Type \"help name\" to get a summary about the command \"name\" and how to use it.\n" \
                   "Any path given by the user to specify files or folders has to be relative to the working directory of this program.\n\n"
    cliHintPath = "The specified path has to be relative to the working directory of this program."