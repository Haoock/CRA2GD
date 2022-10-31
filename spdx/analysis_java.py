import os
import re

from spdx.analysis_c import change_lin_path_to_win, change_win_path_to_linux
from spdx.neo4j_client import Neo4j_Client_Driver


class java_file:
    def __init__(self, name, full_path) -> None:
        self.file_name = name

        self.file_full_path = full_path

        self.import_name = []

        self.static_import_name = []

        self.actual_import = []

        self.third_party_dep = []

        self.actual_static_import = []

        self.package_name = ""

        self.same_package_files = []

        self.node_id = None

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
                file = java_file(filename, p)
                files.append(file)
    return files


def visit_import_dir(import_search_dir, source_root, linux_true):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    import_dict = {}
    for search_dir in import_search_dir:
        if not linux_true:
            search_dir = change_lin_path_to_win(search_dir)
        search_dir_full = os.path.join(source_root_temp, search_dir)
        dir_set = set()
        for(currentDir, _, filenames) in os.walk(search_dir_full):
            for filename in filenames:
                file_type = filename.split(".")[-1]
                if file_type == 'java':
                    p = os.path.join(currentDir, filename)
                    temp_path = os.path.relpath(p, search_dir_full)
                    if not linux_true:
                        temp_path = change_win_path_to_linux(temp_path)
                    dir_set.add(temp_path)
        if not linux_true:
            search_dir = change_win_path_to_linux(search_dir)
        import_dict[search_dir] = dir_set
    return  import_dict


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

def analysis_import_content(java_file, file_dict, source_root, linux_true, third_party):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    for content in java_file.import_name:
        full_path_temp = java_file.file_full_path
        path = content.replace(".", "/")
        path = '/' + path + ".java"
        if not linux_true:
            full_path_temp = change_lin_path_to_win(full_path_temp)
            path = change_lin_path_to_win(path)
        idx = full_path_temp.find("/com/")
        full_path_temp = full_path_temp[:idx]
        full_name = full_path_temp + path
        dic_full_name = os.path.relpath(full_name, source_root)
        if change_win_path_to_linux(dic_full_name) in file_dict.keys():
            java_file.actual_import.append(change_win_path_to_linux(dic_full_name))
        else:
            third_party.add(content)
            java_file.third_party_dep.append(content)

    for content in java_file.static_import_name:
        full_path_temp = java_file.file_full_path
        path = content.replace(".", "/")
        path = '/' + path + ".java"
        if not linux_true:
            full_path_temp = change_lin_path_to_win(full_path_temp)
            path = change_lin_path_to_win(path)
        idx = full_path_temp.find("/com/")
        full_path_temp = full_path_temp[:idx]
        full_name = full_path_temp + path
        dic_full_name = os.path.relpath(full_name, source_root)
        if change_win_path_to_linux(dic_full_name) in file_dict.keys():
            java_file.actual_static_import.append(change_win_path_to_linux(dic_full_name))
        else:
            third_party.add(content)
            java_file.third_party_dep.append(content)


def analysis_same_package(java_file, source_root, linux_true):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    if java_file.package_name == "":
        return
    else:
        dirname = java_file.file_full_path
        package_dir = os.path.dirname(dirname)
        for currentDir, _, filenames in os.walk(package_dir):
            for filename in filenames:
                file_type = filename.split(".")[-1]
                if file_type == "java":
                    p = os.path.join(currentDir, filename)
                    dic_full_name = os.path.relpath(p, source_root)
                    java_file.same_package_files.append(dic_full_name)


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


def file_analysis(source_root, import_search_lst, host, user, psw, linux_true):
    file_infos = visit_all_files(source_root, linux_true)
    print("java文件均已访问")
    import_dir = visit_import_dir(import_search_lst, source_root, linux_true)
    print("所有引用文件已访问")

    file_dits = {}
    for file_info in file_infos:
        file_full_path_temp = file_info.file_full_path
        file_info.import_name, file_info.package_name, \
        file_info.static_import_name = read_java_file(file_full_path_temp, linux_true)
        if not linux_true:
            source_root = change_lin_path_to_win(source_root)
            file_full_path_temp = change_lin_path_to_win(file_full_path_temp)
        path_temp = os.path.relpath(file_full_path_temp, source_root)
        if not linux_true:
            path_temp = change_win_path_to_linux(path_temp)
        file_dits[path_temp] = file_info

    print("分析引用关系。。。")
    third_party = set()
    for file_info in file_infos:
        analysis_import_content(file_info, file_dits, source_root, linux_true, third_party)
        analysis_same_package(file_info, source_root, linux_true)

    print("正在生成图。。。")
    get_neo4j_graph(file_dits, third_party, host, user, psw)

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

if __name__ == "__main__":

    source_root = "/Users/dzf/Downloads/intellij-community-master"
    import_search_lst = ["import"]

    host = "bolt://localhost:7687"
    user = "neo4j"
    psw = "dudu990911"
    linux_true = True
    file_analysis(source_root, import_search_lst, host, user, psw, linux_true)