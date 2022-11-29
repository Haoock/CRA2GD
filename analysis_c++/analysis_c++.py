from util.neo4j_client import Neo4j_Client_Driver
from util.nebula_process import NebulaClientDriver
from file_analysis import *
import time


# generate graph to neo4j
def generate_neo4j_graph(all_file_obj):
    neo4j_driver = Neo4j_Client_Driver()
    print("Connecting to neo4j!")
    neo4j_driver.connect()
    print("Connect succeed, start to generate graph.")
    time_start = time.time()
    for k, v in all_file_obj.items():
        node_id = neo4j_driver.create_node(name=k, full_path=v.file_full_path, is_user_file=v.is_user_file)
        v.node_id = node_id
    time_end = time.time()
    print("time cost:", time_end - time_start, 's')
    print("Start to generate edges.")
    for k, v in all_file_obj.items():
        for include_file in v.include_name:
            neo4j_driver.create_edge(v.node_id, all_file_obj[include_file].node_id)
    neo4j_driver.close()
    time_end2 = time.time()
    print("time cost:", time_end2 - time_end, 's')


def process_file_vertex_data(vid, file_name):
    return "'{}':('{}'), ".format(vid, file_name)


def process_package_vertex_data(vid, pkg_name):
    return "'{}':('{}'), ".format(vid, pkg_name)


def process_library_vertex_data(vid, lib_name):
    return "'{}':('{}');".format(vid, lib_name)


def process_edge_data(src_vid, dst_vid, e_type):
    return "'{}'->'{}':('{}'), ".format(src_vid, dst_vid, e_type)


def create_include_relationship(nebula_driver, all_file_obj, l_len):
    all_files = []
    for k, v in all_file_obj.items():
        all_files.append(process_file_vertex_data(k, os.path.basename(k)))
        if len(all_files) == l_len:
            all_files[-1] = all_files[-1][:-2] + ";"
            nebula_driver.create_vertex("File", ''.join(all_files))
            all_files.clear()
    if len(all_files) != 0:
        all_files[-1] = all_files[-1][:-2] + ";"
        nebula_driver.create_vertex("File", ''.join(all_files))

    # create edges
    edge_lst = []
    for k, v in all_file_obj.items():
        for include_file in v.include_name:
            edge_lst.append(process_edge_data(k, include_file, "Include"))
            if len(edge_lst) == l_len:
                edge_lst[-1] = edge_lst[-1][:-2] + ";"
                nebula_driver.create_edge(''.join(edge_lst))
                edge_lst.clear()
    if len(edge_lst) != 0:
        edge_lst[-1] = edge_lst[-1][:-2] + ";"
        nebula_driver.create_edge(''.join(edge_lst))


def create_contains_relationship(nebula_driver, all_file_obj, lib_name, source_root, linux_true, l_len):
    all_package_obj = {lib_name: list()}
    for k, v in all_file_obj.items():
        while not k == os.path.dirname(k):
            sub_file_or_pkg = k
            k = os.path.dirname(k)
            if k == "":
                if v.is_user_file:
                    k = lib_name
                else:
                    break
            if v.is_user_file:
                if k not in all_package_obj.keys():
                    all_package_obj[k] = list()
                    all_package_obj[k].append(sub_file_or_pkg)
                else:
                    all_package_obj[k].append(sub_file_or_pkg)
                    break
    # create package and Library
    if not linux_true:
        source_root = change_win_path_to_linux(source_root)
    nebula_driver.create_vertex("Library", process_library_vertex_data(lib_name, lib_name[3:]))
    all_packages = []
    for k, v in all_package_obj.items():
        if k != lib_name:
            all_packages.append(process_package_vertex_data(k, os.path.basename(k)))
        if len(all_packages) == l_len:
            all_packages[-1] = all_packages[-1][:-2] + ";"
            nebula_driver.create_vertex("Package", ''.join(all_packages))
            all_packages.clear()
    if len(all_packages) != 0:
        all_packages[-1] = all_packages[-1][:-2] + ";"
        nebula_driver.create_vertex("Package", ''.join(all_packages))

    # create edges
    edge_lst = []
    for k, v in all_package_obj.items():
        for pkg_or_file in v:
            edge_lst.append(process_edge_data(k, pkg_or_file, "Contain"))
            if len(edge_lst) == l_len:
                edge_lst[-1] = edge_lst[-1][:-2] + ";"
                nebula_driver.create_edge(''.join(edge_lst))
                edge_lst.clear()
    if len(edge_lst) != 0:
        edge_lst[-1] = edge_lst[-1][:-2] + ";"
        nebula_driver.create_edge(''.join(edge_lst))


def generate_nebula_graph(all_file_obj, lib_name, source_root, nebula_driver, linux_true, l_len):
    print("Create include nodes and relationship")
    create_include_relationship(nebula_driver, all_file_obj, l_len)
    print("Include finish")
    print("Create contain nodes and relationship")
    create_contains_relationship(nebula_driver, all_file_obj, lib_name, source_root, linux_true, l_len)
    print("Contain finish")


def file_analysis(lan, source_root, lib_name, search_library_lst, include_dir_lst, exclude_dir_lst, linux_true,
                  nebula_space_name, l_len, visit_all_type, include_type):
    dependency_lib_files = set()
    lib_name = lan + "_" + "#" + lib_name
    time_start = time.time()
    nebula_driver = NebulaClientDriver(space_name=nebula_space_name)
    nebula_driver.connect()
    file_infos = []
    print("Start visiting all files")
    if visit_all_type == 1:
        file_infos = visit_all_files(source_root, linux_true, exclude_dir_lst)
    elif visit_all_type == 2:
        file_infos = visit_all_files2(source_root, linux_true, exclude_dir_lst)
    else:
        print("please enter the va_type!")
        exit(1)
    print("Visited all files")
    include_dir_files = []
    if include_type == 1:
        include_dir_files = visit_include_dir(include_dir_lst, source_root, linux_true)
    elif include_type == 2:
        include_dir_files = visit_include_dir2(include_dir_lst, source_root, linux_true)
    else:
        print("please enter the include_type!")
        exit(1)
    print("Visited all include files")
    print("Start analysing files")
    all_file_dic_obj = {}  # key:lib_name + file's name，value:FileInfo
    for file_info in file_infos:
        file_info.sys_include_files, file_info.rel_include_files = read_file_content(file_info.file_full_path,
                                                                                     linux_true)
        file_full_path_temp = file_info.file_full_path
        if not linux_true:
            source_root = change_lin_path_to_win(source_root)
            file_full_path_temp = change_lin_path_to_win(file_full_path_temp)
        path_temp = os.path.relpath(file_full_path_temp, source_root)
        if not linux_true:
            path_temp = change_win_path_to_linux(path_temp)
        path_temp = add_library_name(lib_name, path_temp)
        all_file_dic_obj[path_temp] = file_info

    # for k, v in include_dir_files.items():
    #     print(k)
    #     print(v)

    print("analysing rel_include and sys_include!")
    for file_info in file_infos:
        # print(file_info.file_full_path)
        analysis_rel_include_content(file_info, all_file_dic_obj, source_root, linux_true, lib_name)
        analysis_sys_include_content(lan, file_info, all_file_dic_obj, source_root, include_dir_files, search_library_lst,
                                     linux_true, nebula_driver, lib_name, dependency_lib_files)
    time_end = time.time()
    print("time cost:", time_end - time_start, 's')
    print("Finish analysing, start generate graph!")

    print(dependency_lib_files)
    # for k, v in all_file_dic_obj.items():
    #     print(k)
    #     print(v.sys_include_files)
    #     print(v.rel_include_files)
    #     print(v.include_name)

    # # generate_neo4j_graph(all_file_dic_obj)
    generate_nebula_graph(all_file_dic_obj, lib_name, source_root, nebula_driver, linux_true, l_len)
    nebula_driver.close()
    time_end2 = time.time()
    print("total time cost：", time_end2 - time_start, 's')


if __name__ == "__main__":

    # small boost
    # source_root = "F:\\lhh\\py_test\\boost2"
    # include_search_dir_lst = []
    # library_name = "boost"
    source_root_dir = ""
    library_name = ""
    dependency_libraries = []  # （vid）
    include_dirs = []
    exclude_dirs = []
    v_a_type = 1
    i_type = 1


    # neo4j config
    host = "bolt://localhost:7687"
    user = "neo4j"
    psw = "1234"
    linux = False  # linux True, windows False

    # nebular config
    nubula_host = "123.60.77.114"
    nebula_port = 9669
    nebula_user_name = "root"
    nebula_password = "nubula"
    nebula_space = "AllProjects"
    lst_len = 150
    language = "C"

    print("1: glibc---C标准库")
    print("2: linux---linux源代码库")
    print("3: C++Std---C++标准库")
    print("4: boost---boost源码库")
    print("5: libpqxx---libpqxx源码库")
    print("6: cryptopp---cryptopp源代码库")
    print("7: inja---inja源代码库")
    print("8: bserv---bserv源代码库")
    print("9: ASL---ASL源代码库")
    num = int(input("Please enter the project number which you want to choose(from 1 to 9):"))
    if num == 1:
        # c standard
        source_root_dir = "F:\\lhh\\py_test\\glibc"
        library_name = "glibc"
        dependency_libraries = []
        include_dirs = ["include"]
        exclude_dirs = []
    elif num == 2:
        # linux
        source_root_dir = "F:\\lhh\\py_test\\linux-master"
        library_name = "LINUX"
        dependency_libraries = ["glibc/include"]
        include_dirs = ["include", "arch/x86/include"]
        exclude_dirs = []
    elif num == 3:
        # C++ standard library，ues visit_all_files2
        source_root_dir = "F:\\lhh\\py_test\\llvm-project\\libcxx"
        library_name = "C++Std"
        dependency_libraries = ["LINUX/include"]  # （vid）
        include_dirs = ["include", "src/include"]
        exclude_dirs = ["test"]
        v_a_type = 2
        i_type = 2
    elif num == 4:
        # boost
        source_root_dir = "F:\\lhh\\py_test\\boost"
        library_name = "boost"
        dependency_libraries = ["C++Std/include"]
        include_dirs = []
        exclude_dirs = ["doc", "stage", "status", "more"]
    elif num == 5:
        # libpqxx, use visit_all_files2 and visit_include_dir2
        source_root_dir = "F:\\lhh\\py_test\\libpqxx"
        library_name = "libpqxx"
        dependency_libraries = ["C++Std/include"]
        include_dirs = ["include"]
        exclude_dirs = ["tools", "config-tests"]
    elif num == 6:
        # cryptopp ,use visit_all_files
        source_root_dir = "F:\\lhh\\py_test\\cryptopp"
        library_name = "cryptopp"
        dependency_libraries = ["C++Std/include"]
        include_dirs = []
        exclude_dirs = ["TestPrograms"]
    elif num == 7:
        #inja, use visit_all_files
        source_root_dir = "F:\\lhh\\py_test\\inja"
        library_name = "inja"
        dependency_libraries = ["C++Std/include"]
        include_dirs = ["include", "third_party/include"]
        exclude_dirs = ["single_include"]
    elif num == 8:
        # bserv, use visit_all_files
        source_root_dir = "F:\\lhh\\py_test\\bserv"
        library_name = "bserv"
        dependency_libraries = ["C++Std/include", "boost", "libpqxx/include", "inja/include", "#"]
        include_dirs = ["bserv/include"]
        exclude_dirs = ["dependencies"]
    elif num == 9:
        # ASL, use visit_all_files
        source_root_dir = "F:\\lhh\\py_test\\ASL"
        library_name = "ASL"
        dependency_libraries = ["C++Std/include", "boost"]
        include_dirs = ["adobe"]
        exclude_dirs = ["documentation", "tools"]
    file_analysis(language, source_root_dir, library_name, dependency_libraries, include_dirs, exclude_dirs, linux,
                  nebula_space, lst_len, v_a_type, i_type)
