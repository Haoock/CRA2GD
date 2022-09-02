import os
import hashlib
import re
from datetime import datetime


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

        # package's subPackages list(BuilderPackageConfig object)
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


def read_build_file(path):
    """
    :param path: the build file's path(full path)
    :return: build file's content as string
    """
    f = open(path)
    line = f.readline()
    file_str = ""
    while line:
        file_str += line.strip()
        if line.strip() != "":
            file_str += " "
        line = f.readline()
    f.close()
    return file_str


def analysis_main_build_file(path):
    """
    :param path: the build file's path(full path)
    :return: main build file's BuilderPackageConfig
    """
    main_build_pkg_cfg = BuilderPackageConfig()
    file_str = read_build_file(path)
    print(file_str)
    # first to find cc_binary（cc_binary is only in main build file）
    pkg_name = re.compile('cc_binary\s*\\(\s*name\s*=\s*\\"(.*?)\\"').findall(file_str)  # list type
    sub_package_lst = []
    if len(pkg_name) != 0:
        main_build_pkg_cfg.isMainPackage = True
        main_build_pkg_cfg.packageName = pkg_name[0]

        # then analysis all cc_library
        # cc_libs = re.compile('cc_library\s*\\(\s*name\s*=\s*"(.*?)",').findall(file_str)
        # print(cc_libs)
        # print(len(cc_libs))
        src_file_names_str = re.compile('cc_binary\s*\\(.+srcs\s*=\s*\\[\s*"(.*?)"\s*,?\s*\\]').findall(file_str)[0]
        src_file_names_lst = src_file_names_str.split(",")
        for i in range(len(src_file_names_lst)):
            if src_file_names_lst[i] == '':
                continue
            src_file_names_lst[i] = src_file_names_lst[i].lstrip('"')
            src_file_names_lst[i] = src_file_names_lst[i].rstrip('"')
            src_file_names_lst[i] = src_file_names_lst[i].lstrip("'")
            src_file_names_lst[i] = src_file_names_lst[i].rstrip("'")
        main_build_pkg_cfg.srcs = src_file_names_lst
        print(src_file_names_lst)

        # analysis subPackages
        sub_package_str = re.compile('cc_binary\s*\\(.+deps\s*=\s*\\[\s*"(.*?)"\s*,?\s*\\]').findall(file_str)[0]
        print(sub_package_str)
        sub_package_lst = sub_package_str.split(",")
        for i in range(len(sub_package_lst)):
            if sub_package_lst[i] == '':
                continue
            sub_package_lst[i] = sub_package_lst[i].lstrip('"')
            sub_package_lst[i] = sub_package_lst[i].rstrip('"')
            sub_package_lst[i] = sub_package_lst[i].lstrip("'")
            sub_package_lst[i] = sub_package_lst[i].rstrip("'")
        print(sub_package_lst)
    return main_build_pkg_cfg,  sub_package_lst


def analysis_normal_build_file(pkg_path, pak_name):
    """
        :param path: the build file's path(full path)
        :return: normal file's BuilderPackageConfig(mainly cc_library library)
    """
    pkg_cfg = BuilderPackageConfig()
    pkg_path = os.path.join(pkg_path, "build")
    print(pkg_path)
    file_str = read_build_file(pkg_path)
    print(file_str)


def analysis_file_by_scan(src_root_dir, excludes):
    """
        Gathers a list of all paths for all files within src_root_dir or its children.
        Arguments:
            - src_root_dir: root directory of files being collected(suppose that we have "workspace" file in this dir)
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
    main_build_cfg = BuilderPackageConfig()
    sub_pkg_name_list = []
    for bf_path in build_file_paths:
        build_pkg_cfg, lst = analysis_main_build_file(bf_path)
        if build_pkg_cfg.isMainPackage:
            main_build_cfg = build_pkg_cfg
            sub_pkg_name_list = lst
    for pkg_name in sub_pkg_name_list:
        if pkg_name[:2] == "//":  # if pkg_name starts with "//"
            # 以固定的格式进行分割
            pkg_name = pkg_name[2:]
            sp_lst = pkg_name.split(":")
            analysis_normal_build_file(os.path.join(src_root_dir, sp_lst[0]), sp_lst[1])


def make_document():
    """
        Every document has a list of packages.
        We view a build file as a package.

    :return:
    """
    files = analysis_file_by_scan(scan_dir, excludes)


if __name__ == "__main__":
    # scan_dir = r"E:\myProjects\test4"
    scan_dir = r"C:\Users\haock\Desktop\temp\test4"
    # spdx_path = r"E:\myProjects"
    spdx_path = r"C:\Users\haock\Desktop\temp"
    spdxPrefix = "https://huawei.com/haoock/"
    excludes = []
    files = analysis_file_by_scan(scan_dir, excludes)
    # srcRootDirs = {}
    # pkgID = convertToSPDXIDSafe("")
    # srcRootDirs[pkgID] = scan_dir
    # res = makeFinalSpdx(srcRootDirs, spdx_path, spdxPrefix)
    # print(res)
