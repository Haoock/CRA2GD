import os
import hashlib
import re
from datetime import datetime

# 哈哈哈


class BuilderDocumentConfig:
    def __init__(self):
        super(BuilderDocumentConfig, self).__init__()

        ##### Document info

        # name of document
        self.documentName = ""

        # namespace for this document
        self.documentNamespace = ""

        # external document refs that this document uses
        # list of tuples of external doc refs, in format:
        #    [("DocumentRef-<docID>", "<namespaceURI>", "<hashAlg>", "<hashValue>"), ...]
        self.extRefs = []

        # configs for packages: package root dir => BuilderPackageConfig
        self.packageConfigs = {}


class BuilderPackageConfig:
    def __init__(self):
        super(BuilderPackageConfig, self).__init__()

        #####
        ##### Package-specific config info
        #####

        # name of package
        self.packageName = ""

        # SPDX ID for package, must begin with "SPDXRef-"
        self.spdxID = ""

        # download location for package, defaults to "NOASSERTION"
        self.packageDownloadLocation = "NOASSERTION"

        # should conclude package license based on detected licenses,
        # AND'd together?
        self.shouldConcludeLicense = True

        # declared license, defaults to "NOASSERTION"
        self.declaredLicense = "NOASSERTION"

        # copyright text, defaults to "NOASSERTION"
        self.copyrightText = "NOASSERTION"

        # should include SHA256 hashes? (will also include SHA1 regardless)
        self.doSHA256 = False

        # should include MD5 hashes? (will also include MD5 regardless)
        self.doMD5 = False

        # root directory to be scanned
        self.scandir = ""

        # directories whose files should not be included
        self.excludeDirs = [".git/"]

        # directories whose files should be included, but not scanned
        # FIXME not yet enabled
        self.skipScanDirs = []

        # number of lines to scan for SPDX-License-Identifier (0 = all)
        # defaults to 20
        self.numLinesScanned = 20

        # if isMainPackage is True, it means this package has binary rule
        self.isMainPackage = False

        # package's subPackages list
        self.subPackages = []

        # package's source files
        self.srcs = []


class BuilderDocument:
    def __init__(self, docCfg):
        super(BuilderDocument, self).__init__()

        # corresponding document configuration
        self.config = docCfg

        # packages in this document: package root dir => BuilderPackage
        self.packages = {}
        for rootPath, pkgCfg in docCfg.packageConfigs.items():
            self.packages[rootPath] = BuilderPackage(pkgCfg)


class BuilderPackage:
    def __init__(self, pkgCfg):
        super(BuilderPackage, self).__init__()

        self.config = pkgCfg

        self.name = pkgCfg.packageName
        self.spdxID = pkgCfg.spdxID
        self.downloadLocation = pkgCfg.packageDownloadLocation
        self.verificationCode = ""
        self.licenseConcluded = "NOASSERTION"
        self.licenseInfoFromFiles = []
        self.licenseDeclared = pkgCfg.declaredLicense
        self.copyrightText = pkgCfg.copyrightText
        self.files = []


class BuilderFile:
    def __init__(self):
        super(BuilderFile, self).__init__()

        self.name = ""
        self.spdxID = ""
        # FIXME not yet implementing FileType
        self.type = ""
        self.sha1 = ""
        self.sha256 = ""
        self.md5 = ""
        self.licenseConcluded = "NOASSERTION"
        self.licenseInfoInFile = []
        self.copyrightText = "NOASSERTION"


# First need to scan all files within src_root_dir

def should_exclude_file(filename, excludes):
    """
    Determines whether a file is in an excluded directory.
    Arguments:
        - filename: filename being tested
        - excludes: array of excluded directory names
    Returns: True if should exclude, False if not.
    """
    for exc in excludes:
        if exc in filename:
            return True
    return False


def make_all_file_data(filePaths, pkgCfg, timesSeen):
    """
            Scan all files for expressions and hashes, and fill in data.
            Arguments:
                - filePaths: sorted array of paths to files to scan.
                - pkgCfg: BuilderPackageConfig for this scan.
                - timesSeen: dict of all filename-only (converted to SPDX-ID-safe)
                             to number of times seen.
            Returns: array of BuilderFiles
            """
    bfs = []
    for file_path in filePaths:
        # bf = make_file_data(filePath, pkgCfg, timesSeen)
        bf = make_file_data(file_path, pkgCfg, timesSeen)
        bfs.append(bf)

    return bfs


def analysis_build_file(path):
    pkg_cfg = BuilderPackageConfig()
    print(path)
    f = open(path)
    line = f.readline()
    file_str = ""
    while line:
        file_str += line.strip()
        if line.strip() != "":
            file_str += " "
        line = f.readline()
    f.close()
    print(file_str)
    pkg_name = re.compile('cc_library\s*\\(\s*name\s*=\s*\\"(.*?)\\"').findall(file_str)
    pkg_type = "cc_library"
    if len(pkg_name) == 0:
        pkg_cfg.isMainPackage = True
        pkg_name = re.compile('cc_binary\s*\\(\s*name\s*=\s*\\"(.*?)\\"').findall(file_str)  # it's a list
    pkg_cfg.packageName = pkg_name
    print(pkg_name)
    src_file_names = re.compile('cc_library\s*\\(.+srcs\s*=\s*\\["(.*?)"\\]').findall(file_str)
    print(src_file_names)




def analysis_file_by_scan(src_root_dir, excludes):
    """
        Gathers a list of all paths for all files within src_root_dir or its children.
        Arguments:
            - src_root_dir: root directory of files being collected
            - excludes: array of excluded directory names
        Returns: array of paths
    """
    paths = []
    # ignoring second item in tuple, which lists immediate subdirectories
    for (currentDir, _, filenames) in os.walk(src_root_dir):
        for filename in filenames:
            p = os.path.join(currentDir, filename)
            if not should_exclude_file(p, excludes):
                paths.append(p)
    paths.sort()
    # find build file paths
    build_file_paths = []
    for file_path in paths:
        head_tail = os.path.split(file_path)[1]
        if head_tail == "BUILD":
            build_file_paths.append(file_path)
    # analysis build file(package)
    for bf_path in build_file_paths:
        build_pkg_cfg = analysis_build_file(bf_path)


def make_document():
    """
        Every document has a list of packages.
        We view a build file as a package.

    :return:
    """
    files = analysis_file_by_scan(scan_dir, excludes)


if __name__ == "__main__":
    scan_dir = r"E:\myProjects\test4"
    spdx_path = r"E:\myProjects"
    spdxPrefix = "https://huawei.com/haoock/"
    excludes = []
    files = analysis_file_by_scan(scan_dir, excludes)
    # srcRootDirs = {}
    # pkgID = convertToSPDXIDSafe("")
    # srcRootDirs[pkgID] = scan_dir
    # res = makeFinalSpdx(srcRootDirs, spdx_path, spdxPrefix)
    # print(res)
