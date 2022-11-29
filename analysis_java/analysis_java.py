import os
import time
import uuid

from util.tools import change_lin_path_to_win, change_win_path_to_linux
from util.nebula_process import NebulaClientDriver
from util.neo4j_client import Neo4j_Client_Driver


class java_file:
    def __init__(self, name, full_path, node_id) -> None:
        self.file_name = name

        self.file_full_path = full_path

        self.import_name = []

        self.static_import_name = []

        self.actual_import = []

        self.third_party_dep = []

        self.actual_static_import = []

        self.package_name = ""

        self.same_package_files = []

        self.node_id = node_id


class Component:
    def __init__(self, id, name) -> None:
        self.id = id
        self.name = name


class App:
    def __init__(self, id, name) -> None:
        self.id = id
        self.name = name


class Package:
    def __init__(self, id, name, path) -> None:
        self.id = id
        self.name = name
        self.pac_path = path


class Library:
    def __init__(self, id, name) -> None:
        self.id = id
        self.name = name
#
# class third_party_node:
#     def __init__(self, name) -> None:
#         self.name = name
#
#         self.node_id = None


def visit_all_files(source_root, linux_true):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    files = []
    for (currentDir, _, filenames) in os.walk(source_root_temp):
        for filename in filenames:
            file_type = filename.split(".")[-1]
            if file_type == 'java':
                p = os.path.join(currentDir, filename)
                if not linux_true:
                    p = change_win_path_to_linux(p)
                    filename = change_win_path_to_linux(filename)
                file = java_file(filename, p, uuid.uuid1().int>>64)
                files.append(file)
    return files


def read_java_file(file_path, linux_true):
    if not linux_true:
        file_path = change_lin_path_to_win(file_path)
    import_file_name = []
    static_import_lst = []
    package_name = ""
    no_import_line = 0
    f = open(file_path, 'r', encoding='ISO-8859-1')
    line = f.readline()

    while line:
        if no_import_line > 20:
            break
        line = line.strip()
        if line.startswith("import"):
            line = line.replace("import", "").strip()
            if line.startswith("static"):
                fname = line.replace("static", "").replace(";", "").strip();
                if not fname.endswith("*"):
                    static_import_lst.append(fname.strip())
            else:
                fname = line.replace(";", "")
                if not fname.endswith("*"):
                    import_file_name.append(fname.strip())
            no_import_line = 0
        elif line.startswith("package"):
            pname = line.replace(" ", "").replace("package", "").replace(";", "")
            package_name += pname
            no_import_line = 0
        # elif line.startswith("import static"):
        #     fname = line.replace("import static", "").strip().replace(";", "")
        elif line.startswith("public"):
            break
        else:
            no_import_line += 1
        line = f.readline()
    f.close()
    return import_file_name, package_name, static_import_lst

# import_file_name, package_name,  slst= read_java_file('/Users/dzf/Downloads/intellij-community-master/json/src/com/intellij/json/codeinsight/JsonCompletionContributor.java', linux_true=True)
# print(package_name)
# for item in import_file_name:
#     print(item)
# for item in slst:
#     print(item)
def getMaxCommonSubstr(s1, s2):

    len_s1 = len(s1)
    len_s2 = len(s2)

    record = [[0 for i in range(len_s2 + 1)] for j in range(len_s1 + 1)]

    maxNum = 0  # 最长匹配长度
    p = 0  # 字符串匹配的终止下标

    for i in range(len_s1):
        for j in range(len_s2):
            if s1[i] == s2[j]:
                # 相同则累加
                record[i + 1][j + 1] = record[i][j] + 1

                if record[i + 1][j + 1] > maxNum:
                    maxNum = record[i + 1][j + 1]
                    p = i

    return  p + 1 - maxNum


def analysis_import_content(java_file, file_dict, source_root, linux_true, third_party, app_name):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    for content in java_file.import_name:
        path = content.replace(".", "/")
        path = '/' + path + ".java"
        file_relpath = os.path.relpath(java_file.file_full_path, source_root)
        final_path = app_name + '/' + file_relpath[:getMaxCommonSubstr(file_relpath, path)]+path
        if change_win_path_to_linux(final_path) in file_dict.keys():
            java_file.actual_import.append(change_win_path_to_linux(final_path))
        else:
            third_party.add(content)
            java_file.third_party_dep.append(content)

    for content in java_file.static_import_name:
        path = content.replace(".", "/")
        path = '/' + path + ".java"
        file_relpath = os.path.relpath(java_file.file_full_path, source_root)
        final_path = app_name + '/' + file_relpath[:getMaxCommonSubstr(file_relpath, path)] + path
        if change_win_path_to_linux(final_path) in file_dict.keys():
            java_file.actual_import.append(change_win_path_to_linux(final_path))
        else:
            third_party.add(content)
            java_file.third_party_dep.append(content)


# def analysis_same_package(java_file, source_root, linux_true):
#     if not linux_true:
#         source_root = change_lin_path_to_win(source_root)
#     if java_file.package_name == "":
#         return
#     else:
#         dirname = java_file.file_full_path
#         package_dir = os.path.dirname(dirname)
#         for currentDir, _, filenames in os.walk(package_dir):
#             for filename in filenames:
#                 file_type = filename.split(".")[-1]
#                 if file_type == "java":
#                     p = os.path.join(currentDir, filename)
#                     dic_full_name = os.path.relpath(p, source_root)
#                     java_file.same_package_files.append(dic_full_name)


def search_import_file(content, import_search_lst, source_root, import_dir, linux_true):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    if len(import_search_lst) == 0:
        return False, ""
    for search_path in import_search_lst:
        if not linux_true:
            search_path = change_lin_path_to_win(search_path)
            content = change_lin_path_to_win(content)
        file_set = import_dir[search_path]
        if content in file_set:
            if not linux_true:
                search_path = change_lin_path_to_win(search_path)
                content = change_lin_path_to_win(content)
            res = os.path.relpath(os.path.join(source_root, search_path, content), source_root)
            return True, change_win_path_to_linux(res)
        else:
            return False, ""


def file_analysis(source_root, host, user, psw, linux_true, neo):
    time_start = time.time()
    app_name = source_root[source_root.rfind("/")+1:]
    components = set()
    packages = set()

    file_infos = visit_all_files(source_root, linux_true)
    print(app_name + "中java文件均已访问")
    print("正在创建文件索引")
    file_dits = {}
    for file_info in file_infos:
        file_full_path_temp = file_info.file_full_path
        idx = os.path.relpath(file_full_path_temp, source_root).rfind('/')
        package_temp = os.path.relpath(file_full_path_temp, source_root)[:idx]
        idx = package_temp.find('/')
        component_temp = package_temp[:idx]
        packages.add(package_temp)
        components.add(component_temp)
        file_info.import_name, file_info.package_name, \
        file_info.static_import_name = read_java_file(file_full_path_temp, linux_true)
        if not linux_true:
            source_root = change_lin_path_to_win(source_root)
            file_full_path_temp = change_lin_path_to_win(file_full_path_temp)
        path_temp = app_name + '/' + os.path.relpath(file_full_path_temp, source_root)
        if not linux_true:
            path_temp = change_win_path_to_linux(path_temp)
        file_dits[path_temp] = file_info

    print("分析" + app_name + "引用关系。。。")
    third_party = set()
    for file_info in file_infos:
        analysis_import_content(file_info, file_dits, source_root, linux_true, third_party, app_name)
        # analysis_same_package(file_info, source_root, linux_true)

    time_mid = time.time()
    print("分析引用关系用时：", time_mid - time_start, 's')
    print("正在生成图。。。")
    if not neo:
        get_nebula_graph(file_dits, app_name, components, packages, third_party, nebula_space_name)
    else:
        get_neo4j_graph(file_dits, third_party, host, user, psw)

    time_end = time.time()
    print("生成图用时：", time_end - time_mid, 's')


def create_contains_relationship(nebula_driver, app_name, components, packages, file_dicts):
    nebula_driver.create_java_vertex("App", '"{}":("{}")'.format(app_name, app_name))
    for component in components:
        nebula_driver.create_java_vertex("Component", '"{}":("{}")'.format(component, component))
        nebula_driver.create_java_relationship("contained_by", '"{}"->"{}":()'.format(component, app_name))
    for package in packages:
        package_name = package.replace('/', '.')
        nebula_driver.create_java_vertex("Package", '"{}":("{}", "{}")'.format(package, package_name, package))
        temp_component = package[:package.find('/')]
        nebula_driver.create_java_relationship("contained_by", '"{}"->"{}":()'.format(package, temp_component))
    for k, v in file_dicts.items():
        nebula_driver.create_java_vertex("File", '"{}":("{}", "{}")'.format(k, v.file_name, v.file_full_path))
        idx = os.path.relpath(v.file_full_path, source_root).rfind('/')
        package_temp = os.path.relpath(v.file_full_path, source_root)[:idx]
        nebula_driver.create_java_relationship("contained_by", '"{}"->"{}":()'.format(k, package_temp))


def create_contains_relationship_tuned(nebula_driver, app_name, components, packages, file_dicts):
    nebula_driver.create_java_vertex("App", '"{}":("{}")'.format(app_name, app_name))
    component_lst = []
    for component in components:
        s = '"{}":("{}"),'.format(app_name + '/' + component, component)
        component_lst.append(s)
        if len(component_lst) == 300:
            component_lst[-1] = component_lst[-1][:-1] + ';'
            nebula_driver.create_java_vertex("Component", ''.join(component_lst))
            component_lst.clear()

    if len(component_lst) != 0:
        component_lst[-1] = component_lst[-1][:-1] + ';'
        nebula_driver.create_java_vertex("Component", ''.join(component_lst))

    pac_lst = []
    for pac in packages:
        pac_name = pac.replace('/', '.')
        s = '"{}":("{}", "{}"),'.format(app_name + '/' + pac, pac_name, pac)
        pac_lst.append(s)
        if len(pac_lst) == 300:
            pac_lst[-1] = pac_lst[-1][:-1] + ';'
            nebula_driver.create_java_vertex("Package", ''.join(pac_lst))
            pac_lst.clear()
    if len(pac_lst) != 0:
        pac_lst[-1] = pac_lst[-1][:-1] + ';'
        nebula_driver.create_java_vertex("Package", ''.join(pac_lst))

    all_files = []
    for k, v in file_dicts.items():
        s = '"{}":("{}", "{}"),'.format(k, v.file_name, v.file_full_path)
        all_files.append(s)
        if len(all_files) == 300:
            all_files[-1] = all_files[-1][:-1] + ';'
            nebula_driver.create_java_vertex("File", ''.join(all_files))
            all_files.clear()
    if len(all_files) != 0:
        all_files[-1] = all_files[-1][:-1] + ';'
        nebula_driver.create_java_vertex("File", ''.join(all_files))

    edge_lst = []
    for c in components:
        sc = '"{}"->"{}":(),'.format(app_name + '/' + c, app_name)
        edge_lst.append(sc)
        if len(edge_lst) == 300:
            edge_lst[-1] = edge_lst[-1][:-1] + ';'
            nebula_driver.create_java_relationship("contained_by", ''.join(edge_lst))
            edge_lst.clear()
    if len(edge_lst) != 0:
        edge_lst[-1] = edge_lst[-1][:-1] + ';'
        nebula_driver.create_java_relationship("contained_by", ''.join(edge_lst))
        edge_lst.clear()

    for p in packages:
        temp_com = p[:p.find('/')]
        sp = '"{}"->"{}":(),'.format(app_name + '/' + p, app_name + '/' + temp_com)
        edge_lst.append(sp)
        if len(edge_lst) == 300:
            edge_lst[-1] = edge_lst[-1][:-1] + ';'
            nebula_driver.create_java_relationship("contained_by", ''.join(edge_lst))
            edge_lst.clear()
    if len(edge_lst) != 0:
        edge_lst[-1] = edge_lst[-1][:-1] + ';'
        nebula_driver.create_java_relationship("contained_by", ''.join(edge_lst))
        edge_lst.clear()

    for k, v in file_dicts.items():
        idx = os.path.relpath(v.file_full_path, source_root).rfind('/')
        package_temp = os.path.relpath(v.file_full_path, source_root)[:idx]
        s = '"{}"->"{}":(),'.format(k, app_name + '/' + package_temp)
        edge_lst.append(s)
        if len(edge_lst) == 300:
            edge_lst[-1] = edge_lst[-1][:-1] + ';'
            nebula_driver.create_java_relationship("contained_by", ''.join(edge_lst))
            edge_lst.clear()
    if len(edge_lst) != 0:
        edge_lst[-1] = edge_lst[-1][:-1] + ';'
        nebula_driver.create_java_relationship("contained_by", ''.join(edge_lst))
        edge_lst.clear()


def create_import_relationship(nebula_driver, file_dicts, third_party):
    for content in third_party:
        nebula_driver.create_java_vertex("Library", '"{}":("{}")'.format(content, content))

    for k,v in file_dicts.items():
        for actual in v.actual_import:
            nebula_driver.create_java_relationship("import_file", '"{}"->"{}":()'.format(k, actual))

    cmds = []
    for k,v in file_dicts.items():
        for third_p in v.third_party_dep:
            cmd = '"{}"->"{}":()'.format(k, third_p)
            cmds.append(cmd)
    for c in cmds:
        nebula_driver.create_java_relationship("import_library", c)


def create_import_relationship_tuned(nebula_driver, file_dicts, third_party):
    libraries = []
    for content in third_party:
        s = '"{}":("{}"),'.format(content, content)
        libraries.append(s)
        if len(libraries) == 300:
            libraries[-1] = libraries[-1][:-1] + ';'
            nebula_driver.create_java_vertex("Library", ''.join(libraries))
            libraries.clear()
    if len(libraries) != 0:
        libraries[-1] = libraries[-1][:-1] + ';'
        nebula_driver.create_java_vertex("Library", ''.join(libraries))

    a_edge_lst = []
    t_edge_lst = []
    for k, v in file_dicts.items():
        for actual in v.actual_import:
            sa = '"{}"->"{}":(),'.format(k, actual)
            a_edge_lst.append(sa)
            if len(a_edge_lst) == 300:
                a_edge_lst[-1] = a_edge_lst[-1][:-1] + ';'
                nebula_driver.create_java_relationship("import_file", ''.join(a_edge_lst))
                a_edge_lst.clear()
        for third_p in v.third_party_dep:
            st = '"{}"->"{}":(),'.format(k, third_p)
            t_edge_lst.append(st)
            if len(t_edge_lst) == 300:
                t_edge_lst[-1] = t_edge_lst[-1][:-1] + ';'
                nebula_driver.create_java_relationship("import_library", ''.join(t_edge_lst))
                t_edge_lst.clear()
    if len(a_edge_lst) != 0:
        a_edge_lst[-1] = a_edge_lst[-1][:-1] + ';'
        nebula_driver.create_java_relationship("import_file", ''.join(a_edge_lst))
    if len(t_edge_lst) != 0:
        t_edge_lst[-1] = t_edge_lst[-1][:-1] + ';'
        nebula_driver.create_java_relationship("import_library", ''.join(t_edge_lst))

#
# def create_import_library_relationship(nebula_driver, file_dicts):
#     cmds = []
#     for k,v in file_dicts.items():
#         for third_p in v.third_party_dep:
#             cmd = '"{}"->"{}":()'.format(k, third_p)
#             cmds.append(cmd)
#     for c in cmds:
#         nebula_driver.create_java_relationship("import_library", c)


def get_nebula_graph(file_dicts, app_name, components, packages, third_party, nebula_space_name):
    nebula_driver = NebulaClientDriver(space_name=nebula_space_name)
    nebula_driver.connect()
    print("成功连接nebula,开始生成节点")
    print("开始生成Contains节点关系")
    create_contains_relationship_tuned(nebula_driver, app_name, components, packages, file_dicts)
    print("成功生成Contains关系")
    print("开始生成Import关系")
    create_import_relationship_tuned(nebula_driver, file_dicts, third_party)
    print("成功生成Import关系")
    nebula_driver.close()


# def get_import_library(file_dicts, nebula_space_name):
#     nebula_driver = NebulaClientDriver(space_name=nebula_space_name)
#     nebula_driver.connect()
#     create_import_library_relationship(nebula_driver, file_dicts)
#     nebula_driver.close()

def get_neo4j_graph(file_dict, third_party, host, userName, password):
    neo4jDriver = Neo4j_Client_Driver()
    neo4jDriver.connect(host=host, user=userName, password=password)

    #创建文件节点
    for k, v in file_dict.items():
        node_id = neo4jDriver.create_import_node(name=k, full_path=v.file_full_path)
        v.node_id = node_id

    #创建外部依赖节点
    for content in third_party:
        node_id = neo4jDriver.create_third_party_node(name=content)


    #根据外部引用创建边
    for k,v in file_dict.items():
        for third_p in v.third_party_dep:
            neo4jDriver.create_third_party_edge(v.node_id, third_p)

    #根据import创建边
    for k,v in file_dict.items():
        for actual in v.actual_import:
            neo4jDriver.create_import_edge(v.node_id, file_dict[actual].node_id)

    #根据相同包创建边
    for k,v in file_dict.items():
        for file in v.same_package_files:
            if file in file_dict.keys():
                neo4jDriver.create_same_package_edge(v.node_id, file_dict[file].node_id)


    neo4jDriver.close()


# def get_nebula_graph(file_dict, third_party):
#     config, client = nebula_client()
#     client.execute(
#         'CREATE SPACE IF NOT EXISTS javaFileAnalysis(PARTITION_NUM=20, vid_type=FIXED_STRING(200));'
#         'USE javaFileAnalysis;'
#         'CREATE TAG IF NOT EXISTS FileNode(filename string, fileFullPath string);'
#         'CREATE TAG IF NOT EXISTS ThirdParty(name string);'
#         'CREATE EDGE IF NOT EXISTS Relationship(typeName string);'
#     )
#     for k,v in file_dict.items():
#         cmd = 'INSERT VERTEX IF NOT EXISTS FileNode(filename, fileFullPath) VALUES "{}":("{}","{}")'.format(
#             k, k, v.file_full_path
#         )
#         client.execute(cmd)
#
#     for content in third_party:
#         cmd = 'INSERT VERTEX IF NOT EXISTS ThirdParty(name) VALUES "{}":("{}")'.format(
#             content, content
#         )
#         client.execute(cmd)
#
#     for k,v in file_dict.items():
#         for actual in v.actual_import:
#             cmd = 'INSERT EDGE IF NOT EXISTS Relationship(typeName) VALUES "{}"->"{}":("{}")'.format(
#                 k, file_dict[actual].file_name, "import"
#             )
#             client.execute(cmd)
#
#     for k,v in file_dict.items():
#         for third_party in v.third_party_dep:
#             cmd = 'INSERT EDGE IF NOT EXISTS Relationship(typeName) VALUES "{}"->"{}":("{}")'.format(
#                 k, third_party, "third_party"
#             )
#             client.execute(cmd)



if __name__ == "__main__":

    source_roots = []

    f = open('apps.txt')
    line = f.readline()
    while line:
        source_roots.append(line.replace('\n', ''))
        line = f.readline()
    f.close()

    host = "bolt://localhost:7687"
    user = "neo4j"
    psw = "dudu990911"
    linux_true = True
    nebula_host = "123.60.77.114"
    nebula_port = 9669
    nebula_user_name = "root"
    nebula_password = "nebula"
    nebula_space_name = "java_test1"

    for source_root in source_roots:
        file_analysis(source_root, host, user, psw, linux_true, neo=False)