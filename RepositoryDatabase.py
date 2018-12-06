import os
import sys
import shutil
import sqlite3
from collections import defaultdict

from StaticInfo import StaticInfo
from VMIDescription import BaseImageDescriptor, VMIMasterDescriptor

class RepositoryDatabase:
    def __init__(self,forceNew=False):
        self.dbFile = StaticInfo.relPathLocalRepositoryDatabase
        self.forceNew = forceNew
        self.db = None
        self.cursor = None

    def __enter__(self):
        if self.forceNew:
            if os.path.exists(self.dbFile):
                os.remove(self.dbFile)
            self.db = sqlite3.connect(self.dbFile)
            self.cursor = self.db.cursor()
            self.initDB()
        elif os.path.exists(self.dbFile):
            self.db = sqlite3.connect(self.dbFile)
            self.cursor = self.db.cursor()
        else:
            self.db = sqlite3.connect(self.dbFile)
            self.cursor = self.db.cursor()
            self.initDB()
        return self

    def __exit__(self, *args):
        self.db.close()

    def initDB(self):
        self.cursor.execute('''
            CREATE TABLE PackageRepository(
              pkgID         INTEGER PRIMARY KEY AUTOINCREMENT,
              name          TEXT    NOT NULL,
              version       TEXT    NOT NULL,
              architecture  TEXT    NOT NULL,
              distribution  TEXT    NOT NULL,
              installsize   INTEGER NOT NULL,
              filename      TEXT    NOT NULL)
        ''')
        self.cursor.execute('''
            CREATE TABLE PackageDependencies(
              depID         INTEGER PRIMARY KEY AUTOINCREMENT,
              vmiID         INTEGER NOT NULL,
              pkgID         INTEGER NOT NULL,
              deppkgID      INTEGER NOT NULL,
              FOREIGN KEY(vmiID)    REFERENCES vmiRepository(vmiID),
              FOREIGN KEY(pkgID)    REFERENCES PackageRepository(pkgID),
              FOREIGN KEY(deppkgID) REFERENCES PackageRepository(pkgID));
        ''')
        self.cursor.execute('''
            CREATE TABLE vmiRepository(
                vmiID         INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL,
                userDirPath   TEXT    NOT NULL,
                baseImageID   TEXT    NOT NULL,
                FOREIGN KEY(baseImageID) REFERENCES baseImageRepository(baseID));
        ''')
        self.cursor.execute('''
            CREATE TABLE baseImageRepository(
                baseID         INTEGER PRIMARY KEY AUTOINCREMENT,
                distribution  TEXT    NOT NULL,
                version       TEXT    NOT NULL,
                architecture  TEXT    NOT NULL,
                pkgManager    TEXT    NOT NULL,
                filename      TEXT    NOT NULL,
                graphPath     TEXT    NOT NULL,
                masterGraphPath TEXT  NOT NULL);
                ''')
        self.db.commit()
        self.addPackageDict(StaticInfo.basicPackagesDictFedora, "fedora")

    def initRepo(self):
        if os.path.exists(StaticInfo.relPathLocalRepository):
            shutil.rmtree(StaticInfo.relPathLocalRepository)
        os.mkdir(StaticInfo.relPathLocalRepositoryPackages)
        os.mkdir(StaticInfo.relPathLocalRepositoryBaseImages)
        os.mkdir(StaticInfo.relPathLocalRepositoryUserFolders)

    def getNumberOfVMIs(self):
        self.cursor.execute('''
              SELECT count(*) FROM vmiRepository
            ''',
            ()
        )
        result = self.cursor.fetchall()
        return str(result[0][0])

    def getNumberOfBaseImages(self):
        self.cursor.execute('''
              SELECT count(*) FROM baseImageRepository
            ''',
            ()
        )
        result = self.cursor.fetchall()
        return str(result[0][0])

    def getNumberOfPackages(self):
        self.cursor.execute('''
              SELECT count(*) FROM PackageRepository
            ''',
            ()
        )
        result = self.cursor.fetchall()
        return str(result[0][0])

    def packageExists(self, name, version, arch, distribution):
        """
        Checks if specific Package exists in database
        :param name:
        :param version:
        :param distribution:
        :return:
            if package does not exist,
                False
            if package does exists or multiple rows (then Error message),
                True
        """
        self.cursor.execute('''
            SELECT filename FROM PackageRepository
            WHERE name=?
            AND version=?
            AND architecture=?
            AND distribution=?''',
            (name,version,arch,distribution)
        )
        result = self.cursor.fetchall()
        if len(result) == 0:
            return False
        elif len(result) == 1:
            return True
        else:
            print "ERROR in Repository: multiple lines in table PackageRepository\n" \
                  "Search for name=%s, version=%s, architecture=%s, distribution=%s\n" \
                  "Result:" % (name, version, arch, distribution)
            for row in result:
                print "\t" + row[0]
            return True

    def getPackageID(self, pkgName, version, arch, distribution):
        """
        Returns filename of package if exists, otherwise None
        :param pkgName:
        :param version:
        :param distribution:
        :return:
            ID      , if package exists
            None    , otherwise
        """
        self.cursor.execute('''
                SELECT pkgID FROM PackageRepository
                WHERE name=?
                AND version=?
                AND architecture=?
                AND distribution=?
            ''',
            (pkgName, version, arch, distribution)
        )
        result = self.cursor.fetchall()
        if len(result) == 0:
            return None
        elif len(result) == 1:
            return result[0][0]
        else:
            print("ERROR in database: multiple packages with same name, version and distribution exist:\n" \
                "\tSearch for name=" + pkgName + ", version=" + version + ", architecture="+arch+"distribution=" + distribution + " results in:\n" \
                "\t" + str(result) + "\n" \
                "\tsolve manually!")
            return result[0][0]

    def getPackageFileNameFromID(self,pkgID):
        self.cursor.execute('''
            SELECT filename FROM PackageRepository
            WHERE pkgID=?''',
            (pkgID,)
        )
        result = self.cursor.fetchall()
        if len(result) == 0:
            return None
        else:
            return result[0][0]

    def getPackageFileName(self, pkgName, version, arch, distribution):
        """
        Returns filename of package if exists, otherwise None
        :param pkgName:
        :param version:
        :param distribution:
        :return:
            filename    , if package exists
            None        , otherwise
        """
        self.cursor.execute('''
            SELECT filename FROM PackageRepository
            WHERE name=?
            AND version=?
            AND architecture=?
            AND distribution=?''',
            (pkgName, version, arch, distribution)
        )
        result = self.cursor.fetchall()
        if len(result) == 0:
            return None
        elif len(result) == 1:
            return result[0][0]
        else:
            print("ERROR in database: multiple packages with same name, version and distribution exist:\n" \
                "\tSearch for name=" + pkgName + ", version=" + version + ", architecture="+arch+", distribution=" + distribution + " results in:\n" \
                "\t" + str(result) + "\n" \
                "\tsolve manually!")
            return result[0][0]

    def addPackageDict(self, packageInfoDict, distribution):
        packageInfoList = [(
            pkgInfo[StaticInfo.dictKeyName],
            pkgInfo[StaticInfo.dictKeyVersion],
            pkgInfo[StaticInfo.dictKeyArchitecture],
            distribution,
            pkgInfo[StaticInfo.dictKeyInstallSize],
            pkgInfo[StaticInfo.dictKeyFilePath]
        ) for pkg,pkgInfo in packageInfoDict.iteritems()]
        self.cursor.executemany('''
                      INSERT INTO PackageRepository(name, version, architecture, distribution, installsize, filename)
                      VALUES(?,?,?,?,?,?)
                  ''', packageInfoList)
        self.db.commit()

    def getBaseImageId(self, filename):
        self.cursor.execute('''
            SELECT baseID FROM baseImageRepository
            WHERE filename=?''',
            (filename,)
        )
        result = self.cursor.fetchall()
        if len(result) > 1:
            print("ERROR in database: multiple base Images with same filename exist:\n" 
                  "\t" + str(result) + "\n\tsolve manually!")
            return result[0][0]
        elif len(result) == 1:
            return result[0][0]
        else:
            return None

    def addBaseImage(self, baseImage, masterGraphPath):
        # Insert new Base Image
        self.cursor.execute('''
                        INSERT INTO baseImageRepository (distribution, version,architecture, pkgManager,filename, graphPath, masterGraphPath)
                        VALUES (?,?,?,?,?,?,?)''',
                            (baseImage.distribution,
                             baseImage.distributionVersion,
                             baseImage.architecture,
                             baseImage.pkgManager,
                             baseImage.pathToVMI,
                             baseImage.graphFileName,
                             masterGraphPath))
        self.db.commit()
        # Return id
        return self.getBaseImageId(baseImage.pathToVMI)

    def removeBaseImage(self, baseID):
        self.cursor.execute('''
            DELETE 
            FROM baseImageRepository
            WHERE baseID = ? 
            ''', (baseID,)
        )
        self.db.commit()

    def getVmiID(self,vmiName):
        self.cursor.execute('''
            SELECT vmiID FROM vmiRepository
            WHERE name=?''',
            (vmiName,)
        )
        result = self.cursor.fetchall()
        if len(result) > 1:
            print("ERROR in database: multiple VMIs with same name exist:\n" \
                     "\t"+str(result)+"\n\tsolve manually!")
            return result[0][0]
        elif len(result) == 1:
            return result[0][0]
        else:
            return None

    def getVmiUserDirPath(self,vmiName):
        self.cursor.execute('''
            SELECT userDirPath FROM vmiRepository
            WHERE name=?''',
            (vmiName,)
        )
        result = self.cursor.fetchall()
        if len(result) > 1:
            print("ERROR in database: multiple VMIs with same name exist:\n" \
                     "\t"+str(result)+"\n\tsolve manually!")
            return result[0][0]
        elif len(result) == 1:
            return result[0][0]
        else:
            return None

    def vmiExists(self, vmiName):
        if self.getVmiID(vmiName) != None:
            return True
        else:
            return False

    def getBaseImageInfoForVmiID(self, vmiID):
        self.cursor.execute('''
                SELECT distribution,version,architecture,pkgManager,filename,graphPath
                FROM baseImageRepository
                WHERE baseID=(
                    SELECT baseImageID
                    FROM vmiRepository
                    WHERE vmiID = ?)
            ''',
            (vmiID,)
        )
        result = self.cursor.fetchall()
        if len(result) == 1:
            return [str(x) for x in result[0]]
        else:
            return list()

    def getBaseImageIDsWith(self, distribution, version, architecture, pkgManager):
        self.cursor.execute('''
                    SELECT baseID
                    FROM baseImageRepository
                    WHERE distribution = ?
                        AND version = ?
                        AND architecture= ?
                        AND pkgManager = ?
                    ''',
                    (distribution, version, architecture, pkgManager)
                    )
        result = self.cursor.fetchall()
        if len(result) > 0:
            baseImageIdList = list( int(row[0]) for row in result )
            return baseImageIdList
        else:
            return list()

    def getBaseImagesWith(self, distribution, version, architecture, pkgManager):
        self.cursor.execute('''
                    SELECT baseID, filename,graphPath
                    FROM baseImageRepository
                    WHERE distribution = ?
                        AND version = ?
                        AND architecture= ?
                        AND pkgManager = ?
                    ''',
                    (distribution, version, architecture, pkgManager)
                    )
        result = self.cursor.fetchall()
        if len(result) > 0:
            baseImageList = list()
            for row in result:
                info = [str(col) for col in row] # -> returns [baseID, imageFilename, graphFileName]
                baseImage = BaseImageDescriptor(info[1])
                baseImage.initializeFromRepo(distribution, version, architecture, pkgManager, info[2])
                baseImageList.append(baseImage)
            return baseImageList
        else:
            return (None,None)

    def getBaseImageFromID(self, baseID):
        self.cursor.execute('''
                    SELECT distribution,version,architecture,pkgManager,filename,graphPath
                    FROM baseImageRepository
                    WHERE baseID = ?
                    ''',
                    (baseID,)
                    )
        result = self.cursor.fetchall()
        if len(result) == 1:
            info = [str(col) for col in result[0]] # -> returns [distribution,version,architecture,pkgManager,filename,graphPath]
            baseImage = BaseImageDescriptor(info[4])
            baseImage.initializeFromRepo(info[0], info[1], info[2], info[3], info[5])
            return baseImage
        else:
            return None

    def getVMIMasterDescriptorFromBaseID(self, baseID):
        self.cursor.execute('''
                            SELECT distribution,version,architecture,pkgManager,filename,masterGraphPath
                            FROM baseImageRepository
                            WHERE baseID = ?
                            ''',
                            (baseID,)
                            )
        result = self.cursor.fetchall()
        if len(result) == 1:
            info = [str(col) for col in
                    result[0]]  # -> returns [distribution,version,architecture,pkgManager,filename,masterGraphPath]
            master = VMIMasterDescriptor(info[4])
            master.initializeMasterFromRepo(info[0], info[1], info[2], info[3], info[5], self.getMainServicesForBaseImage(baseID))
            return master
        else:
            return None

    def getVMIMasterDescriptors(self):
        self.cursor.execute('''
                SELECT baseID
                FROM baseImageRepository
                '''
        )
        result = self.cursor.fetchall()
        baseIDs = [ int(row[0]) for row in result]
        masterDescriptors = list()
        for baseID in baseIDs:
            tmp = self.getVMIMasterDescriptorFromBaseID(baseID)
            if tmp is not None:
                masterDescriptors.append(tmp)
        return masterDescriptors

    def getNumberOfBaseImagesWith(self,distribution,version,architecture,pkgManager):
        self.cursor.execute('''
            SELECT count(baseID)
            FROM baseImageRepository
            WHERE distribution = ?
                AND version = ?
                AND architecture= ?
                AND pkgManager = ?
            ''',
            (distribution,version,architecture,pkgManager)
        )
        result = self.cursor.fetchall()
        if len(result) == 1:
            return result[0][0]
        else:
            return None

    def getBaseImagesWithCompatiblePackages(self, distribution, version, architecture, pkgManager):
        """
        :param distribution:
        :param version:
        :param architecture:
        :param pkgManager:
        :return: baseImagesAndCompatiblePackages:
                    in the form:    dict(base1: MSPackages, base2:...)
                    MSPackages:     dict(MS1:MS1Info,dep1:dep1Info...)
                    xInfo:          dict(name:"curl",version:"1.1",...)
        """
        baseImageIDs = self.getBaseImageIDsWith(distribution, version, architecture, pkgManager)
        baseImagesAndCompatiblePackages = dict()
        for baseID in baseImageIDs:
            baseImage = self.getBaseImageFromID(baseID)
            baseImagesAndCompatiblePackages[baseImage] = self.getCompPkgDictForBaseImageID(baseID)
        return baseImagesAndCompatiblePackages

    def getMainServicesForBaseImage(self,baseID):
        self.cursor.execute('''
                    SELECT name
                    FROM PackageRepository
                    WHERE pkgID IN(
                        SELECT DISTINCT pkgID
                        FROM PackageDependencies
                        WHERE vmiID IN (
                            SELECT vmiID
                            FROM vmiRepository
                            WHERE baseImageID = ?
                        )
                    )''',
                            (baseID,)
                            )
        result = self.cursor.fetchall()
        if len(result) == 1:
            return [str(row[0]) for row in result]
        else:
            return []

    def replaceAndRemoveBaseImages(self, newBaseImage, baseImagesToReplace):
        newBaseID = self.getBaseImageId(newBaseImage.pathToVMI)
        if newBaseID == None:
            sys.exit("ERROR in Database: Trying to replace base images with new base image that is not found in database")

        # update VMIs to use new Base image and remove old ones
        for oldBase in baseImagesToReplace:
            oldBaseID = self.getBaseImageId(oldBase.pathToVMI)

            # remove base image and graph files
            if os.path.isfile(oldBase.pathToVMI):
                os.remove(oldBase.pathToVMI)
            if oldBase.graphFileName is not None and os.path.isfile(oldBase.graphFileName):
                os.remove(oldBase.graphFileName)

            if oldBaseID is not None:
                masterGraphFileName = self.getVMIMasterDescriptorFromBaseID(oldBaseID).graphFileName
                if os.path.isfile(masterGraphFileName):
                    os.remove(masterGraphFileName)

                # update VMIs to use new base image and remove old base image
                self.updateVMIs(oldBaseID,newBaseID)
                self.removeBaseImage(oldBaseID)

    def addVMI(self, vmiName, localPathToUserDir, baseImageID):
        """
        tries to add new VMI and returns vmiID. if VMI already exists its vmiID is returned
        :param vmiName:
        :param baseImageID:
        """
        # check if VMI exists
        self.cursor.execute('''
            SELECT vmiID FROM vmiRepository
            WHERE name=?''',
            (vmiName,)
        )
        result = self.cursor.fetchall()
        if len(result) > 1:
            sys.exit("ERROR in database: multiple VMIs with same name exist:\n"
                     "\t"+str(result)+"\n\tsolve manually!")
        elif len(result) == 1:
            sys.exit("ERROR in database: adding already existing VMI:\n"
                  "\t" + str(result) + "\n\tsolve manually!")
        else:
            # Insert new VMI
            self.cursor.execute('''
                INSERT INTO vmiRepository (name,userDirPath,baseImageID)
                VALUES (?,?,?)
            ''', (vmiName, localPathToUserDir, baseImageID))
            self.db.commit()
            # Return id
            return self.getVmiID(vmiName)

    def updateVMIs(self, oldBaseID, newBaseID):
        self.cursor.execute('''
            UPDATE vmiRepository
            SET baseImageID = ?
            WHERE baseImageID = ?
            ''',
            (newBaseID, oldBaseID))
        self.db.commit()

    def addMainServicesDepListForVMI(self, vmiID, distribution, mainServicesDepList):
        """
        :param vmiID:
        :param distribution:
        :param mainServicesDepList:
                # in the form of [(root,dict{nodeName:dict{nodeAttributes}})]
                # Note: root is mainservice and part of the dict
        :return:
        """
        # transform input data into list readable by database connector
        depList = []
        # format: [(vmiID,pkgID,deppkgName, deppkgVersion, deppkgArch, deppkgDistribution)]
        for mainServiceName,pkgDict in mainServicesDepList:
            mainServiceID = self.getPackageID(mainServiceName,
                                              pkgDict[mainServiceName][StaticInfo.dictKeyVersion],
                                              pkgDict[mainServiceName][StaticInfo.dictKeyArchitecture],
                                              distribution)
            assert(mainServiceID != None)
            for depName,depInfo in pkgDict.iteritems():
                if depName != mainServiceName:
                    depList.append((
                        vmiID,
                        mainServiceID,
                        depName,
                        depInfo[StaticInfo.dictKeyVersion],
                        depInfo[StaticInfo.dictKeyArchitecture],
                        distribution
                    ))
        self.cursor.executemany('''
                INSERT INTO PackageDependencies (vmiID,pkgID, deppkgID)
                VALUES (?, ?, (SELECT pkgID FROM PackageRepository
                                WHERE name=?
                                AND version=?
                                AND architecture=?
                                AND distribution=?))
            ''', (depList))
        self.db.commit()

    def getMainServicesForVmiID(self, vmiID):
        self.cursor.execute('''
            SELECT name
            FROM PackageRepository
            WHERE pkgID IN (
                SELECT DISTINCT pkgID
                FROM PackageDependencies
                WHERE vmiID=?
            )''',
            (vmiID,)
        )
        result = self.cursor.fetchall()
        if len(result) >= 1:
            return [str(x[0]) for x in result]
        else:
            return None

    def getMainServiceIDForVmiID(self, vmiID, pkgName):
        self.cursor.execute('''
            SELECT pkgID
            FROM PackageRepository
            WHERE name = ?
            AND pkgID IN (
                SELECT DISTINCT pkgID
                FROM PackageDependencies
                WHERE vmiID=?
            )''',
            (pkgName, vmiID)
        )
        result = self.cursor.fetchall()
        if len(result) == 1:
            return str(result[0][0])
        else:
            return None

    def getCompPkgDictForBaseImageID(self, baseID):
        """
        :param baseID:
        :return: compatiblePackages:
                    in the form:    dict(MS1:MS1Info,dep1:dep1Info...)
                    xInfo:          dict(name:"curl",version:"1.1",...)
        """
        self.cursor.execute('''
            SELECT name,version,architecture,filename
            FROM PackageRepository
            WHERE pkgID IN (
                SELECT DISTINCT deppkgID
                FROM PackageDependencies
                WHERE vmiID IN (
                    SELECT vmiID
                    FROM vmiRepository
                    WHERE baseImageID = ?
                )
            )
            OR pkgID IN(
                SELECT DISTINCT pkgID
                FROM PackageDependencies
                WHERE vmiID IN (
                    SELECT vmiID
                    FROM vmiRepository
                    WHERE baseImageID = ?
                )
            )''',
            (baseID,baseID)
        )
        result = self.cursor.fetchall()
        if len(result) >= 1:
            return dict(
                (
                    str(row[0]),
                    {
                        StaticInfo.dictKeyName: str(row[0]),
                        StaticInfo.dictKeyVersion: str(row[1]),
                        StaticInfo.dictKeyArchitecture: str(row[2])
                    }

                ) for row in result )
        else:
            return None

    def getDepPkgInfoSetForVMI(self, vmiID):
        self.cursor.execute('''
            SELECT name,version,architecture,filename
            FROM PackageRepository
            WHERE pkgID IN (
                SELECT DISTINCT deppkgID
                FROM PackageDependencies
                WHERE vmiID=?
            )
            OR pkgID IN(
                SELECT DISTINCT pkgID
                FROM PackageDependencies
                WHERE vmiID=?
            )''',
            (vmiID,vmiID)
        )
        result = self.cursor.fetchall()
        if len(result) >= 1:
            return {(str(x[0]), str(x[1]), str(x[2]), str(x[3])) for x in result}
        else:
            return None

    def getDepPkgInfoDictForVMI(self, vmiID):
        """
        :param vmiID:
        :return: dict with package information required to install main services on specific VMI
                 in the form of dict(pkg:pkgInfo)
                       pkgInfo: dict(name:"pkg", version:"1.1", architecture:"amd64", installsize:10, filePath:local/ubuntu/pkg1.deb)
        """
        self.cursor.execute('''
            SELECT name,version,architecture,installsize,filename
            FROM PackageRepository
            WHERE pkgID IN (
                SELECT DISTINCT deppkgID
                FROM PackageDependencies
                WHERE vmiID=?
            )
            OR pkgID IN(
                SELECT DISTINCT pkgID
                FROM PackageDependencies
                WHERE vmiID=?
            )''',
            (vmiID,vmiID)
        )
        result = self.cursor.fetchall()
        if len(result) >= 1:
            pkgInfoDict = defaultdict(dict)
            for row in result:
                pkgInfoDict[row[0]] = {
                    StaticInfo.dictKeyName: str(row[0]),
                    StaticInfo.dictKeyVersion: str(row[1]),
                    StaticInfo.dictKeyArchitecture: str(row[2]),
                    StaticInfo.dictKeyInstallSize: str(row[3]),
                    StaticInfo.dictKeyFilePath: str(row[4])
                }
            return pkgInfoDict
        else:
            return None

    def getDepPkgInfoDictForVmiOneMS(self, vmiID, mainService):
        """
        :param vmiID:
        :param mainService
        :return: dict with package information required to install one specific main services on specific VMI
                 in the form of dict(pkg:pkgInfo)
                       pkgInfo: dict(name:"pkg", version:"1.1", architecture:"amd64", installsize:10, filePath:local/ubuntu/pkg1.deb)
        """
        mainServiceID = self.getMainServiceIDForVmiID(vmiID, mainService)

        self.cursor.execute('''
            SELECT name,version,architecture,installsize,filename
            FROM PackageRepository
            WHERE pkgID IN (
                SELECT DISTINCT deppkgID
                FROM PackageDependencies
                WHERE vmiID = ?
                AND pkgID = ?
            )
            OR pkgID = ?
            ''',
            (vmiID,mainServiceID,mainServiceID)
        )
        result = self.cursor.fetchall()
        if len(result) >= 1:
            pkgInfoDict = defaultdict(dict)
            for row in result:
                pkgInfoDict[row[0]] = {
                    StaticInfo.dictKeyName: str(row[0]),
                    StaticInfo.dictKeyVersion: str(row[1]),
                    StaticInfo.dictKeyArchitecture: str(row[2]),
                    StaticInfo.dictKeyInstallSize: str(row[3]),
                    StaticInfo.dictKeyFilePath: str(row[4])
                }
            return pkgInfoDict
        else:
            return None

    def getVMIData(self, vmiName):
        """

        :param vmiName:
        :return: triple (pathToBaseImage, mainServices, packageList)
        :rtype (pathToUserDir,BaseImageDescriptor,list(),dict())
        """
        vmiID = self.getVmiID(vmiName)
        if vmiID == None:
            return None


        userDirPath = self.getVmiUserDirPath(vmiName)
        baseImageInfo = self.getBaseImageInfoForVmiID(vmiID)
        baseImage = BaseImageDescriptor(baseImageInfo[4])
        baseImage.initializeFromRepo(baseImageInfo[0], baseImageInfo[1], baseImageInfo[2], baseImageInfo[3], baseImageInfo[5])

        return (
            userDirPath,
            baseImage,
            self.getMainServicesForVmiID(vmiID),
            self.getDepPkgInfoDictForVMI(vmiID)
        )

    def getDataForAllVMIs(self):
        vmiDataList = list()
        self.cursor.execute('''
            SELECT vmiID, name
            FROM vmiRepository
            '''
        )
        result = self.cursor.fetchall()
        vmiIdsAndNames = list((int(row[0]), str(row[1])) for row in result)
        for (vmiID, vmiName) in vmiIdsAndNames:
            # list(MS1, MS2)
            vmiMSList = self.getMainServicesForVmiID(vmiID)
            # list(distribution,version,architecture,pkgManager,filename,graphPath)
            vmiBaseInfo = self.getBaseImageInfoForVmiID(vmiID)
            # remove full path for filename and graph so that only filenames remain
            vmiBaseInfo[4] = vmiBaseInfo[4].split("/")[-1]
            vmiBaseInfo[5] = vmiBaseInfo[5].split("/")[-1]
            vmiData = list(vmiBaseInfo)
            vmiData.insert(0,vmiName)
            vmiData.append(", ".join(vmiMSList))
            vmiDataList.append(vmiData)
        return vmiDataList

    def getAllPackages(self):
        self.cursor.execute('''
            SELECT name,version,architecture, distribution
            FROM PackageRepository
            '''
        )
        result = self.cursor.fetchall()
        return list((str(row[0]), str(row[1]), str(row[2]), str(row[3])) for row in result)

    def getAllBaseImages(self):
        self.cursor.execute('''
            SELECT distribution,version,architecture,pkgManager
            FROM baseImageRepository
            '''
        )
        result = self.cursor.fetchall()
        return list((str(row[0]), str(row[1]), str(row[2]), str(row[3])) for row in result)

    def getAllVmiNames(self):
        """
        :return: vmiNames ordered the way they were added
        """
        vmiDataList = list()
        self.cursor.execute('''
            SELECT name
            FROM vmiRepository
            ORDER BY vmiID ASC
            '''
        )
        result = self.cursor.fetchall()
        vmiNames = list( str(row[0]) for row in result)

        return vmiNames

    def getVmiMetaInfo(self, vmiID):
        self.cursor.execute('''
                    SELECT distribution, version, architecture, pkgManager
                    FROM baseImageRepository
                    WHERE baseID = (
                      SELECT baseImageID
                      FROM vmiRepository
                      WHERE vmiID = ?
                    )''',
                    (vmiID,)
                    )
        result = self.cursor.fetchall()
        if len(result) == 0:
            sys.exit("ERROR in database: cannot find distribution for VMI with ID \"%s\""
                     % vmiID)
        else:
            return (str(result[0][0]),
                    str(result[0][1]),
                    str(result[0][2]),
                    str(result[0][3])
                    )
