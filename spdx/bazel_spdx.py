import os
import hashlib
import re
from datetime import datetime


class BuilderDocumentConfig:
    def __init__(self):
        super(BuilderDocumentConfig, self).__init__()

        # configs for packages: package root dir => BuilderPackageConfig
        # self.packageConfigs = {}

        # self.mainPackages = []


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

        # package's subPackages list(string object)
        self.subPackages = []

        # package's source files
        self.srcs = []


class BuilderPackage:
    def __init__(self, pkgCfg):
        super(BuilderPackage, self).__init__()

        self.config = pkgCfg

        self.name = pkgCfg.packageName
        self.spdxID = pkgCfg.spdxID
        # unique_pkg_id
        self.uniquePkgId = os.path.join(pkgCfg.scandir, pkgCfg.packageName[:-8])  # # 以完整路径名+package名称的形式
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

class BuilderDocument:
    def __init__(self, docCfg):
        super(BuilderDocument, self).__init__()
        ##### Document info

        # name of document
        self.documentName = ""

        # namespace for this document
        self.documentNamespace = ""

        # corresponding document configuration
        self.config = docCfg

        # packages in this document: package root dir => BuilderPackage
        self.packages = {}

        # all files timeSeen
        self.timesSeen = {}

        # external document refs that this document uses
        # list of tuples of external doc refs, in format:
        #    [("DocumentRef-<docID>", "<namespaceURI>", "<hashAlg>", "<hashValue>"), ...]
        self.extRefs = []


# First need to scan all files within src_root_dir

def getSPDXIDSafeCharacter(c):
    """
    Converts a character to an SPDX-ID-safe character.
    Arguments:
        - c: character to test
    Returns: c if it is SPDX-ID-safe (letter, number, '-' or '.');
             '-' otherwise
    """
    if c.isalpha() or c.isdigit() or c == "-" or c == ".":
        return c
    return "-"


def convert_to_spdxId_safe(filenameOnly):
    """
    Converts a filename to only SPDX-ID-safe characters.
    Note that a separate check (such as in getUniqueID, below) will need
    to be used to confirm that this is still a unique identifier, after
    conversion.
    Arguments:
        - filenameOnly: filename only (directories omitted) seeking ID.
    Returns: filename with all non-safe characters replaced with dashes.
    """
    return "".join([getSPDXIDSafeCharacter(c) for c in filenameOnly])


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


def analysis_file_names_str(file_names_str):
    file_names_lst = file_names_str.split(",")
    new_file_name_lst = []
    for i in range(len(file_names_lst)):
        file_names_lst[i] = file_names_lst[i].strip()
        if file_names_lst[i] == '':
            continue
        file_names_lst[i] = file_names_lst[i].lstrip('"')
        file_names_lst[i] = file_names_lst[i].rstrip('"')
        file_names_lst[i] = file_names_lst[i].lstrip("'")
        file_names_lst[i] = file_names_lst[i].rstrip("'")
        new_file_name_lst.append(file_names_lst[i])
    return new_file_name_lst


def analysis_main_build_pkg(path, src_root_dir):
    """
    only analysis main_build_file
    param path: the build file's path(full path)
    :return: main build file's BuilderPackageConfig
    """
    main_build_pkg_cfg = BuilderPackageConfig()
    file_str = read_build_file(path)
    # first to find cc_binary（cc_binary is only in main build file）
    cc_binary_lst = re.compile('cc_binary\s*[(](.*?)[)]').findall(file_str)
    sub_package_lst = []
    if len(cc_binary_lst) != 0:
        cc_binary_str = cc_binary_lst[0]
        pkg_name = re.compile('\s*name\s*=\s*\\"(.*?)\\"').findall(cc_binary_str)  # list type
        if pkg_name != 0:
            main_build_pkg_cfg.packageName = pkg_name[0] + " sources"
            main_build_pkg_cfg.spdxID = "SPDXRef-" + pkg_name[0]
        else:
            print("Warning: main_pkg_name does not exist!")
        main_build_pkg_cfg.isMainPackage = True
        main_build_pkg_cfg.doSHA256 = True
        main_build_pkg_cfg.scandir = os.path.split(path)[0]
        src_file_names_lst = re.compile('srcs\s*=\s*[\[](.*?)[]]').findall(cc_binary_str)
        src_file_names_str = ""
        if len(src_file_names_lst) != 0:
            src_file_names_str = src_file_names_lst[0]
        else:
            print("Info: main_file's srcs does not exist!")
        src_file_names_lst = analysis_file_names_str(src_file_names_str)
        hdr_file_names_str = re.compile('hdrs\s*=\s*[\[](.*?)[]]').findall(cc_binary_str)
        if len(hdr_file_names_str) != 0:
            hdr_file_names_str = hdr_file_names_str[0]
            hdr_file_names_lst = analysis_file_names_str(hdr_file_names_str)
            src_file_names_lst.extend(hdr_file_names_lst)
        main_build_pkg_cfg.srcs = src_file_names_lst

        # analysis subPackages
        sub_pkg_name_list = re.compile('deps\s*=\s*[\[](.*?)[]]').findall(cc_binary_str)
        if len(sub_pkg_name_list) != 0:
            sub_package_str = sub_pkg_name_list[0]
            sub_pkg_name_list = analysis_file_names_str(sub_package_str)

        new_sub_pkg_name_list = []
        for pkg_name in sub_pkg_name_list:
            if pkg_name[:2] == "//":  # if pkg_name starts with "//"
                pkg_name = pkg_name[2:]
                sp_lst = pkg_name.split(":")
                new_sub_pkg_name_list.append(os.path.join(src_root_dir, sp_lst[0], sp_lst[1]))
            elif pkg_name[:1] == ":":
                pkg_name = pkg_name[1:]
                new_sub_pkg_name_list.append(os.path.join(main_build_pkg_cfg.scandir, pkg_name))
        main_build_pkg_cfg.subPackages = new_sub_pkg_name_list
        print(main_build_pkg_cfg.spdxID + "'s subPackage list is:")
        print(new_sub_pkg_name_list)

    return main_build_pkg_cfg


def analysis_normal_build_pkg(pkg_path, src_root_dir):
    """
        :param path: the build file's path(full path)
        :return: normal file's BuilderPackageConfig(mainly cc_library library)
    """

    # pkg_path = os.path.join(pkg_path, "BUILD")
    file_str = read_build_file(pkg_path)
    print(file_str)
    # pkg_names = re.compile('cc_library\s*\\(\s*name\s*=\s*\\"(.*?)\\"').findall(file_str)  # list type
    pkg_lsts = re.compile('cc_library\s*[(](.*?)[)]').findall(file_str)
    # 同一个build文件中会包含多个pkg（每一个cc_library都是一个pkg）
    pkg_cfgs = []
    for pkg_str in pkg_lsts:
        print(pkg_str)
        pkg_cfg = BuilderPackageConfig()
        pkg_name_lst = re.compile('\s*name\s*=\s*\\"(.*?)\\"').findall(pkg_str)  # list type
        if len(pkg_name_lst) != 0:
            pkg_cfg.packageName = pkg_name_lst[0] + " sources"
            pkg_cfg.spdxID = "SPDXRef-" + pkg_name_lst[0]
        else:
            print("Warning: pkg_name does not exists!")

        pkg_cfg.doSHA256 = True
        pkg_cfg.scandir = os.path.split(pkg_path)[0]
        src_file_names_lst = re.compile('srcs\s*=\s*[\[](.*?)[]]').findall(pkg_str)
        src_file_names_str = ""
        if len(src_file_names_lst) != 0:
            src_file_names_str = src_file_names_lst[0]
        else:
            print("Info: sub_file's srcs does not exist!")
        src_file_names_lst = analysis_file_names_str(src_file_names_str)
        hdr_file_names_str = re.compile('hdrs\s*=\s*[\[](.*?)[]]').findall(pkg_str)
        if len(hdr_file_names_str) != 0:
            hdr_file_names_str = hdr_file_names_str[0]
            hdr_file_names_lst = analysis_file_names_str(hdr_file_names_str)
            src_file_names_lst.extend(hdr_file_names_lst)
        print(src_file_names_lst)
        pkg_cfg.srcs = src_file_names_lst

        # analysis subPackages
        sub_pkg_name_list = re.compile('deps\s*=\s*[\[](.*?)[]]').findall(pkg_str)
        if len(sub_pkg_name_list) != 0:
            sub_package_str = sub_pkg_name_list[0]
            sub_pkg_name_list = analysis_file_names_str(sub_package_str)
        new_sub_pkg_name_list = []
        for pkg_name in sub_pkg_name_list:
            if pkg_name[:2] == "//":  # if pkg_name starts with "//"
                pkg_name = pkg_name[2:]
                sp_lst = pkg_name.split(":")
                new_sub_pkg_name_list.append(os.path.join(src_root_dir, sp_lst[0], sp_lst[1]))
            elif pkg_name[:1] == ":":
                pkg_name = pkg_name[1:]
                new_sub_pkg_name_list.append(os.path.join(pkg_cfg.scandir, pkg_name))
        pkg_cfg.subPackages = new_sub_pkg_name_list
        print(pkg_cfg.spdxID + "'s subPackage list is:")
        print(new_sub_pkg_name_list)
        pkg_cfgs.append(pkg_cfg)
    return pkg_cfgs


def analysis_file_by_scan(src_root_dir, doc, excludes=None):
    """
        Gathers a list of all paths for all files within src_root_dir or its children.
        Arguments:
            - src_root_dir: root directory of files being collected(suppose that we have "workspace" file in this dir)
            - excludes: array of excluded directory names
        Returns: array of paths
    """
    if excludes is None:
        excludes = []
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
    main_build_cfgs = []

    # analysis all build files that contain binary library.
    for bf_path in build_file_paths:
        build_pkg_cfg = analysis_main_build_pkg(bf_path, src_root_dir)  # we only analysis main build file(cc_binary)
        if build_pkg_cfg.isMainPackage:
            main_build_cfgs.append(build_pkg_cfg)

    # add all main_build_pkgs and add them to doc
    for main_build_cfg in main_build_cfgs:
        main_build_pkg = BuilderPackage(main_build_cfg)
        doc.packages[main_build_pkg.uniquePkgId] = main_build_pkg
        # doc.config.mainPackages.append(main_build_pkg)

    # analysis all sub_pkgs and add them to doc
    all_normal_pkg_cfg = []
    for bf_path in build_file_paths:
        normal_pkgs = analysis_normal_build_pkg(bf_path, src_root_dir)  # we only analysis sub build file(cc_library)
        all_normal_pkg_cfg.extend(normal_pkgs)

    # add all sub_pkgs and add them to doc
    for normal_pkg_cfg in all_normal_pkg_cfg:
        normal_build_pkg = BuilderPackage(normal_pkg_cfg)
        doc.packages[normal_build_pkg.uniquePkgId] = normal_build_pkg


    # #
    # # # we then analysis sub_pkgs
    # for pkg_name in sub_pkg_name_list:
    #     if pkg_name[:2] == "//":  # if pkg_name starts with "//"
    #         # 以固定的格式进行分割
    #         pkg_name = pkg_name[2:]
    #         sp_lst = pkg_name.split(":")
    #         sub_pkg_objs = analysis_normal_build_file(os.path.join(src_root_dir, sp_lst[0]), sp_lst[1])
    #         main_build_cfg.subPackages.extend(sub_pkg_objs)
    #     elif pkg_name[:1] == ":":
    #         pkg_name = pkg_name[1:]
    #         sub_pkg_objs = analysis_normal_build_file(main_build_cfg.scandir, pkg_name)
    #         main_build_cfg.subPackages.extend(sub_pkg_objs)
    #
    # return main_build_cfg


def getUniqueID(filenameOnly, timesSeen):
    """
    Find an SPDX ID that is unique among others seen so far.
    Arguments:
        - filenameOnly: filename only (directories omitted) seeking ID.
        - timesSeen: dict of all filename-only to number of times seen.
    Returns: unique SPDX ID; updates timesSeen to include it.
    """

    converted = convert_to_spdxId_safe(filenameOnly)
    spdxID = f"SPDXRef-File-{converted}"

    # determine whether spdxID is unique so far, or not
    filenameTimesSeen = timesSeen.get(converted, 0) + 1
    if filenameTimesSeen > 1:
        # we'll append the # of times seen to the end
        spdxID += f"-{filenameTimesSeen}"
    else:
        # first time seeing this filename
        # edge case: if the filename itself ends in "-{number}", then we
        # need to add a "-1" to it, so that we don't end up overlapping
        # with an appended number from a similarly-named file.
        p = re.compile("-\d+$")
        if p.search(converted):
            spdxID += "-1"

    timesSeen[converted] = filenameTimesSeen
    return spdxID


def splitExpression(expression):
    """
    Parse a license expression into its constituent identifiers.
    Arguments:
        - expression: SPDX license expression
    Returns: array of split identifiers
    """
    # remove parens and plus sign
    e2 = re.sub(r'\(|\)|\+', "", expression, flags=re.IGNORECASE)

    # remove word operators, ignoring case, leaving a blank space
    e3 = re.sub(r' AND | OR | WITH ', " ", e2, flags=re.IGNORECASE)

    # and split on space
    e4 = e3.split(" ")

    return sorted(e4)


def getHashes(filePath):
    """
    Scan for and return hashes.
    Arguments:
        - filePath: path to file to scan.
    Returns: tuple of (SHA1, SHA256, MD5) hashes for filePath.
    """
    hSHA1 = hashlib.sha1()
    hSHA256 = hashlib.sha256()
    hMD5 = hashlib.md5()

    with open(filePath, 'rb') as f:
        buf = f.read()
        hSHA1.update(buf)
        hSHA256.update(buf)
        hMD5.update(buf)

    return hSHA1.hexdigest(), hSHA256.hexdigest(), hMD5.hexdigest()


def parseLineForExpression(line):
    """Return parsed SPDX expression if tag found in line, or None otherwise."""
    p = line.partition("SPDX-License-Identifier:")
    if p[2] == "":
        return None
    # strip away trailing comment marks and whitespace, if any
    expression = p[2].strip()
    expression = expression.rstrip("/*")
    expression = expression.strip()
    return expression


def getExpressionData(filePath, numLines):
    """
    Scans the specified file for the first SPDX-License-Identifier:
    tag in the file.
    Arguments:
        - filePath: path to file to scan.
        - numLines: number of lines to scan for an expression before
                    giving up. If 0, will scan the entire file.
    Returns: parsed expression if found; None if not found.
    """
    with open(filePath, "r") as f:
        try:
            lineno = 0
            for line in f:
                lineno += 1
                if numLines > 0 and lineno > numLines:
                    break
                expression = parseLineForExpression(line)
                if expression is not None:
                    return expression
        except UnicodeDecodeError:
            # invalid UTF-8 content
            return None

    # if we get here, we didn't find an expression
    return None


def makeFileData(filePath, pkgCfg, timesSeen):
    """
    Scan for expression, get hashes, and fill in data.
    Arguments:
        - filePath: path to file to scan.
        - pkgCfg: BuilderPackageConfig for this scan.
        - timesSeen: dict of all filename-only (converted to SPDX-ID-safe)
                     to number of times seen.
    Returns: BuilderFile
    """
    bf = BuilderFile()
    bf.name = os.path.join(".", os.path.relpath(filePath, pkgCfg.scandir))

    filenameOnly = os.path.basename(filePath)
    bf.spdxID = getUniqueID(filenameOnly, timesSeen)

    (sha1, sha256, md5) = getHashes(filePath)
    bf.sha1 = sha1
    if pkgCfg.doSHA256:
        bf.sha256 = sha256
    if pkgCfg.doMD5:
        bf.md5 = md5

    expression = getExpressionData(filePath, pkgCfg.numLinesScanned)
    if expression != None:
        bf.licenseConcluded = expression
        bf.licenseInfoInFile = splitExpression(expression)

    return bf


def getPackageLicenses(bfs):
    """
    Extract lists of all concluded and infoInFile licenses seen.
    Arguments:
        - bfs: array of BuilderFiles
    Returns: tuple(sorted list of concluded license exprs,
                   sorted list of infoInFile ID's)
    """
    licsConcluded = set()
    licsFromFiles = set()
    for bf in bfs:
        licsConcluded.add(bf.licenseConcluded)
        for licInfo in bf.licenseInfoInFile:
            licsFromFiles.add(licInfo)
    return (sorted(list(licsConcluded)), sorted(list(licsFromFiles)))


def normalizeExpression(licsConcluded):
    """
    Combine array of license expressions into one AND'd expression,
    adding parens where needed.
    Arguments:
        - licsConcluded: array of license expressions
    Returns: string with single AND'd expression.
    """
    # return appropriate for simple cases
    if len(licsConcluded) == 0:
        return "NOASSERTION"
    if len(licsConcluded) == 1:
        return licsConcluded[0]

    # more than one, so we'll need to combine them
    # iff an expression has spaces, it needs parens
    revised = []
    for lic in licsConcluded:
        if lic == "NONE" or lic == "NOASSERTION":
            continue
        if " " in lic:
            revised.append(f"({lic})")
        else:
            revised.append(lic)
    return " AND ".join(revised)


def calculateVerificationCode(bfs):
    """
    Calculate the SPDX Package Verification Code for all files in the package.
    Arguments:
        - bfs: array of BuilderFiles
    Returns: verification code as string
    """
    hashes = []
    for bf in bfs:
        hashes.append(bf.sha1)
    hashes.sort()
    filelist = "".join(hashes)

    hSHA1 = hashlib.sha1()
    hSHA1.update(filelist.encode('utf-8'))
    return hSHA1.hexdigest()


def make_all_pkg_files(all_pkgs, timesSeen):
    for k, pkg in all_pkgs.items():
        # for every package we first need to scan all source files
        bfs = []
        for file_name in pkg.config.srcs:
            p = os.path.join(pkg.config.scandir, file_name)
            bf = makeFileData(p, pkg.config, timesSeen)
            bfs.append(bf)
        (licsConcluded, licsFromFiles) = getPackageLicenses(bfs)

        if pkg.config.shouldConcludeLicense:
            pkg.licenseConcluded = normalizeExpression(licsConcluded)
        pkg.licenseInfoFromFiles = licsFromFiles
        pkg.files = bfs
        pkg.verificationCode = calculateVerificationCode(bfs)
    # return pkg


def find_contains_of_main_pkg(f, pkg):
    print(type(pkg))
    # main_pkg: BuilderPackage object
    for src in pkg.files:
        if os.path.split(src.name)[1] == "build" or os.path.split(src.name)[1] == "BUILD":
            f.write(f"Relationship: {src.spdxID} DEPENDENCY_MANIFEST_OF {pkg.spdxID}")
        else:
            f.write(f"Relationship: {pkg.spdxID} CONTAINS {src.spdxID}")
        f.write(f"\n")
    if len(pkg.config.subPackages) != 0:
        for sub_pkg in pkg.config.subPackages:
            f.write(f"Relationship: {sub_pkg.spdxID} DEPENDS_ON {pkg.spdxID}")
            f.write(f"\n")
        for sub_pkg in pkg.config.subPackages:
            f.write(f"Relationship: {pkg.spdxID} DEPENDENCY_OF {sub_pkg.spdxID}")
            f.write(f"\n")



def find_contains_of_sub_pkg(f, sub_pkgs):
    for sub_pkg in sub_pkgs:
        find_contains_of_main_pkg(f, sub_pkg)


def writeSourceRelationShip(f, main_pkg):
    # first we need to find CONTAINS and CONTAINED_BY relationship
    find_contains_of_main_pkg(f, main_pkg)
    find_contains_of_sub_pkg(f, main_pkg.subPackages)

    # if len(main_pkg.srcs) != 0:

    # then we need to find DEPENDS_ON and DEPENDENCY_OF relationship
    # then DEPENDENCY_MANIFEST_OF


def writePackages(f, pkgs):
    # write subPackage sections
    for k, pkg in pkgs.items():
        print(pkg.name)
        f.write(f"""##### Package: {pkg.name}

PackageName: {pkg.name}
SPDXID: {pkg.spdxID}
PackageDownloadLocation: {pkg.downloadLocation}
FilesAnalyzed: true
PackageVerificationCode: {pkg.verificationCode}
PackageLicenseConcluded: {pkg.licenseConcluded}
""")
        for licFromFiles in pkg.licenseInfoFromFiles:
            f.write(f"PackageLicenseInfoFromFiles: {licFromFiles}\n")
        f.write(f"""PackageLicenseDeclared: {pkg.licenseDeclared}
PackageCopyrightText: NOASSERTION

Relationship: SPDXRef-DOCUMENT DESCRIBES {pkg.spdxID}

""")

        # write file sections
        for bf in pkg.files:
            f.write(f"""FileName: {bf.name}
SPDXID: {bf.spdxID}
FileChecksum: SHA1: {bf.sha1}
""")
            if bf.sha256 != "":
                f.write(f"FileChecksum: SHA256: {bf.sha256}\n")
            if bf.md5 != "":
                f.write(f"FileChecksum: MD5: {bf.md5}\n")
            f.write(f"LicenseConcluded: {bf.licenseConcluded}\n")
            if len(bf.licenseInfoInFile) == 0:
                f.write(f"LicenseInfoInFile: NONE\n")
            else:
                for licInfoInFile in bf.licenseInfoInFile:
                    f.write(f"LicenseInfoInFile: {licInfoInFile}\n")
            f.write(f"FileCopyrightText: {bf.copyrightText}\n\n")


def outputSPDX(doc, spdxPath):
    """
    Write SPDX doc, package and files content to disk.
    Arguments:
        - doc: BuilderDocument
        - spdxPath: path to write SPDX content
    Returns: True on success, False on error.
    """
    try:
        with open(spdxPath, 'w') as f:
            # write document creation info section
            f.write(f"""SPDXVersion: SPDX-2.2
DataLicense: CC0-1.0
SPDXID: SPDXRef-DOCUMENT
DocumentName: {doc.documentName}
DocumentNamespace: {doc.documentNamespace}
Creator: Tool: bazel-spdx
Created: {datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")}
""")
            # write any external document references
            for extRef in doc.extRefs:
                f.write(f"ExternalDocumentRef: {extRef[0]} {extRef[1]} {extRef[2]}:{extRef[3]}\n")
            f.write(f"\n")

            # write mainPackage sections
            writePackages(f, doc.packages)
            # write subPackage sections
            # writePackages(f, doc.mainPackage.subPackages)
            writeSourceRelationShip(f, doc.mainPackage)
            return True

    except OSError as e:
        print(f"Error: Unable to write to {spdxPath}: {str(e)}")
        return False


def make_bazel_spdx(doc, spdx_output_dir):
    """
    MAIN FUNCTION
    Parse Cmake data and scan source / build directories, and create a
    corresponding SPDX tag-value document.
    Arguments:
        - srcRootDirs: mapping of package SPDX ID (without "SPDXRef-") =>
                       sources root dir
        - spdxOutputDir: output directory where SPDX documents will be written
        - spdxNamespacePrefix: prefix for SPDX Document Namespace (will have
            "sources" and "build" appended); see Document Creation Info
            section in SPDX spec for more information
    Returns: True on success, False on failure; note that failure may still
             produce one or more partial SPDX documents
    """
    # create SPDX file for sources
    srcSpdxPath = os.path.join(spdx_output_dir, "sources.spdx")


    make_all_pkg_files(doc.packages, doc.timesSeen)

    # for sub_pkg_cfg in main_pkg.config.subPackages:
    #     sub_pkg = BuilderPackage(sub_pkg_cfg)
    #     sub_pkg = make_pkg_files(sub_pkg)
    #     main_pkg.subPackages.append(sub_pkg)
    #
    # srcDocCfg.mainPackage = main_pkg
    #
    srcDoc = outputSPDX(doc, srcSpdxPath)
    #
    # if srcDoc:
    #     print(f"Saved sources SPDX to {srcSpdxPath}")
    # else:
    #     print(f"Couldn't generate sources SPDX file")
    #     return False

    # # get hash of sources SPDX file, to use for build doc's extRef
    # hSHA256 = hashlib.sha256()
    # with open(srcSpdxPath, 'rb') as f:
    #     buf = f.read()
    #     hSHA256.update(buf)
    # srcSHA256 = hSHA256.hexdigest()
    #
    # # create SPDX file for build
    # buildSpdxPath = os.path.join(spdx_output_dir, "build.spdx")
    # buildDocCfg = BuilderDocumentConfig()
    # buildDocCfg.documentName = "build"
    # buildDocCfg.documentNamespace = os.path.join(spdx_namespace_prefix, "build")
    #
    # buildPkgCfg = BuilderPackageConfig()
    # buildPkgCfg.packageName = "build"
    # buildPkgCfg.spdxID = "SPDXRef-build"
    # buildPkgCfg.doSHA256 = True
    # buildPkgCfg.scandir = cm.paths_build
    # buildDocCfg.packageConfigs[cm.paths_build] = buildPkgCfg
    #
    # # add external document ref to sources SPDX file
    # buildDocCfg.extRefs = [("DocumentRef-sources", srcDocCfg.documentNamespace, "SHA256", srcSHA256)]
    #
    # # exclude CMake file-based API responses -- presume only used for this
    # # SPDX generation scan, not for actual build artifact
    # buildExcludeDir = os.path.join(cm.paths_build, ".cmake", "api")
    # buildPkgCfg.excludeDirs.append(buildExcludeDir)
    #
    # buildDoc = makeSPDX(buildDocCfg, buildSpdxPath)
    # if buildDoc:
    #     print(f"Saved build SPDX to {buildSpdxPath}")
    # else:
    #     print(f"Couldn't generate build SPDX file")
    #     return False

    return True


def make_spdx_from_build_file(workSpace_dir, spdx_output_dir, spdx_namespace):
    # start to create BuilderDocumentConfig
    doc_cfg = BuilderDocumentConfig()

    doc = BuilderDocument(doc_cfg)
    doc.documentName = "sources"
    doc.documentNamespace = os.path.join(spdx_namespace, "sources")
    analysis_file_by_scan(workSpace_dir, doc)  #
    return make_bazel_spdx(doc, spdx_output_dir)


if __name__ == "__main__":
    # scan_dir = r"E:\myProjects\test4"
    scan_dir = r"E:\bazel\test5_c"
    # spdx_path = r"E:\myProjects"
    spdx_path = r"E:\bazel"
    spdxPrefix = "https://huawei.com/haoock/"
    make_spdx_from_build_file(scan_dir, spdx_path, spdxPrefix)
    # srcRootDirs = {}
    # pkgID = convertToSPDXIDSafe("")
    # srcRootDirs[pkgID] = scan_dir
    # res = makeFinalSpdx(srcRootDirs, spdx_path, spdxPrefix)
    # print(res)
