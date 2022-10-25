from distutils.errors import LibError
from lib2to3.pgen2 import driver
import os
from posixpath import abspath
import re
from datetime import datetime
from traceback import format_exception_only
from turtle import fd, right
from neo4j_client import Neo4j_Client_Driver
import re
import time




# 主要目的是将数据存储到neo4j中或者存储到Nebular数据库中

# 文件的完整信息，也是图数据库中一个节点各种属性信息
class file_info:
    def __init__(self, name, full_path, is_user_file, sys_files = [], rel_files = []) -> None:
        self.file_name = name  # 文件名称

        self.file_full_path = full_path  # 文件所在的完整路径，存储的时候一律使用linux路径来存

        self.is_user_file = is_user_file  # 是否是用户自定义文件，用于区分是用户自定义还是系统文件

        self.sys_include_files = sys_files  # #include<>包含着的

        self.rel_include_files = rel_files  # #include""包含着的

        self.include_name = []  # 最后形成的总的需要连接的名称列表（图数据库中的引用关系边）

        self.node_id = None # 在图数据库中的节点id


def change_win_path_to_linux(win_path):
    return '/'.join(win_path.split('\\'))

def change_lin_path_to_win(lin_path):
    return '\\'.join(lin_path.split('/'))

# 完全遍历一遍项目的所有文件夹，然后分别读取每一个.c .C .cc .cxx .c++ .cpp .h .hpp .hxx文件
def visit_all_files(source_root, linux_true):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    files_unique_info = []
    for (currentDir, _, filenames) in os.walk(source_root_temp):
        for filename in filenames:
            file_suffix = filename.split(".")[-1]
            if file_suffix == 'c' or file_suffix == 'C' or file_suffix == 'cc' or file_suffix =='cxx' or file_suffix == 'c++' or file_suffix == 'cpp' or file_suffix == 'h' or file_suffix == 'hpp' or file_suffix == 'hxx':
                p = os.path.join(currentDir, filename)
                if not linux_true:
                    p = change_win_path_to_linux(p)
                    filename = change_win_path_to_linux(filename)
                file = file_info(filename, p, True)
                files_unique_info.append(file)
    return files_unique_info
            
# 用空间换时间，减少时间复杂度，也就是说提前读取该文件夹下的所有文件,返回字典：
def visit_include_dir(include_search_dir_lst,source_root,linux_true):
    source_root_temp = source_root
    if not linux_true: # 如果是win
        source_root_temp = change_lin_path_to_win(source_root_temp)
    include_dirs_dict = {}
    for search_dir in include_search_dir_lst:
        if not linux_true: # 如果是win
            search_dir = change_lin_path_to_win(search_dir)
        search_dir_fullName = os.path.join(source_root_temp, search_dir)
        dir_set = set()
        for (currentDir, _, filenames) in os.walk(search_dir_fullName):
            for filename in filenames:
                file_suffix = filename.split(".")[-1]
                if file_suffix == 'c' or file_suffix == 'C' or file_suffix == 'cc' or file_suffix =='cxx' or file_suffix == 'c++' or file_suffix == 'cpp' or file_suffix == 'h' or file_suffix == 'hpp' or file_suffix == 'hxx':
                    p = os.path.join(currentDir, filename)
                    temp_path = os.path.relpath(p, search_dir_fullName)
                    if not linux_true:
                        temp_path = change_win_path_to_linux(temp_path)
                    dir_set.add(temp_path)
        if not linux_true:
            search_dir = change_win_path_to_linux(search_dir)
        include_dirs_dict[search_dir] = dir_set
    return include_dirs_dict

# 读取文件内容。优化的内容：此处设置如果读取20行内容都不包含#inlcude关键字，那么就结束这个文件的读取。
def read_file_content(file_path, linux_true):
    if not linux_true:
        file_path = change_lin_path_to_win(file_path)
    sys_files_name = []
    rel_files_name = []
    not_include_line_num = 0
    f = open(file_path, 'r', encoding='ISO-8859-1')
    line = f.readline()
    while line:
        if not_include_line_num > 20 :
            break
        line = line.strip()
        res_lst1 = re.compile('#\s*include\s*["](.*?)["]').findall(line)
        res_lst2 = re.compile('#\s*include\s*[<](.*?)[>]').findall(line)
        if len(res_lst1) != 0 or len(res_lst2) != 0:
            not_include_line_num = 0
            if(len(res_lst1) == 1):
                rel_files_name.append(res_lst1[0])
            elif len(res_lst2) == 1:
                sys_files_name.append(res_lst2[0])
            else:
                print("分析错误：include部分！！！")
        elif len(line) != 0 :
            not_include_line_num += 1
        line = f.readline()
    f.close()
    return sys_files_name, rel_files_name


def analysis_name(string_name):
    res_lst = string_name.split(".")
    # 说明这是一个.内容，那么一般直接完整去匹配，如果不是一个.内容，那么就不再加任何后缀内容
    if len(res_lst) == 2:
        return True
    else:
        return False


# 分析使用双引号#inlcude内容，如果不存在，那么还要添加到尖括号的列表中去
def analysis_rel_include_content(file_obj, all_file_dic_obj, source_root, linux_true):
    # linux_true为false的情况下应该全部转换成windows路径进行处理
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    for content in file_obj.rel_include_files:
        full_path_temp = file_obj.file_full_path 
        if not linux_true:
            full_path_temp = change_lin_path_to_win(full_path_temp)
            content = change_lin_path_to_win(content)
        # 含有后缀名的内容
        full_name = os.path.join(os.path.dirname(full_path_temp), content)
        full_name = os.path.abspath(full_name)
        if analysis_name(full_name):
            #寻找是否存在这个文件
            dic_full_name = os.path.relpath(full_name, source_root) # 在dic中的full name，需要判断是否存在
            if change_win_path_to_linux(dic_full_name) in all_file_dic_obj.keys():
                file_obj.include_name.append(change_win_path_to_linux(dic_full_name))
            else: # 如果不存在，都给他加到sys的寻找路径中去
                file_obj.sys_include_files.append(change_win_path_to_linux(content))
        else:
            file_obj.sys_include_files.append(change_win_path_to_linux(content))

# include_search_dir_lst中的路径名称都是相对于source_root的
def search_include_file(content, include_search_dir_lst, source_root, include_dir_files,linux_true):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    if len(include_search_dir_lst) == 0:
        return False, ""
    for search_path in include_search_dir_lst:
        if not linux_true:
            search_path = change_win_path_to_linux(search_path)
            content = change_win_path_to_linux(content)
        # 读取这个路径下的所有文件，查看是否存在与这个content同名的文件
        files_set = include_dir_files[search_path]
        if content in files_set: # 如果存在，那么则进行返回
            if not linux_true:
                search_path = change_lin_path_to_win(search_path)
                content = change_lin_path_to_win(content)
            res = os.path.relpath(os.path.join(source_root, search_path, content),source_root)
            return True, change_win_path_to_linux(res)
        else:
            return False, ""
            

# 分析使用尖括号#include内容，这边同时包含了双引号#include内容
def analysis_sys_include_content(file_obj, all_file_dic_obj, include_search_dir_lst, source_root, include_dir_files, linux_true):
    for content in file_obj.sys_include_files:
        # 到尖括号的内容，一定不存在#include"../.."这种相对路径的引用，因此不需要考虑这种相对路径的情况
        if analysis_name(content): # 如果有后缀，那么去搜索路径中进行搜索
            # print(content)
            if content not in all_file_dic_obj.keys(): # 如果不存在，那么就去include_search_dir_list中去搜索，如果搜索不到再进行生成
                res, res_content = search_include_file(content, include_search_dir_lst, source_root, include_dir_files, linux_true)
                if res:
                    file_obj.include_name.append(res_content)
                else:
                    file = file_info(content, "", False)
                    all_file_dic_obj[content] = file
                    file_obj.include_name.append(content)
        else: #如果没有后缀，如#include<iostream>一定会生成一个新的节点
            if content not in all_file_dic_obj.keys():
                file = file_info(content, "", False)
                all_file_dic_obj[content] = file
            file_obj.include_name.append(content)
            

# 生成图像存入neo4j中
def generate_neo4j_graph(all_file_obj, host, userName, password):
    neo4jDriver = Neo4j_Client_Driver()
    neo4jDriver.connect(host=host, user=userName, password=password)
    # 创建所有的文件节点
    for k,v in all_file_obj.items():
        node_id = neo4jDriver.create_node(name=k, full_path=v.file_full_path, is_user_file=v.is_user_file)
        v.node_id = node_id
    # 创建节点之间的边
    for k,v in all_file_obj.items():
        for include_file in v.include_name:
            neo4jDriver.create_edge(v.node_id, all_file_obj[include_file].node_id)
    neo4jDriver.close()


    
    

def file_analysis(source_root, include_search_dir_lst, host, user, psw, linux_true):
    file_infos = visit_all_files(source_root, linux_true)
    print("访问所有的文件完成！！！")
    include_dir_files = visit_include_dir(include_search_dir_lst, source_root, linux_true)
    print("访问所有的引用文件完成！！！")

    all_file_dic_obj = {} # 以文件相对source_root的路径名作为这个文件的唯一标识，也就是作为这个字典的key，其value是file_info对象
    for file_info in file_infos:
        file_info.sys_include_files, file_info.rel_include_files = read_file_content(file_info.file_full_path, linux_true)
        file_full_path_temp = file_info.file_full_path
        if not linux_true:
            source_root = change_lin_path_to_win(source_root)
            file_full_path_temp = change_lin_path_to_win(file_full_path_temp)
        path_temp = os.path.relpath(file_full_path_temp,source_root)
        if not linux_true:
            path_temp = change_win_path_to_linux(path_temp)
        all_file_dic_obj[path_temp] = file_info
    
    print("正在分析引用关系")
    for file_info in file_infos:
        analysis_rel_include_content(file_info, all_file_dic_obj, source_root, linux_true)
        analysis_sys_include_content(file_info, all_file_dic_obj, include_search_dir_lst, source_root, include_dir_files,linux_true)
    print("分析引用关系完整，开始生成点和边，存入图数据库中！")
    # for k,v in all_file_dic_obj.items():
    #     print(k)
    #     print(v.sys_include_files)
    #     print(v.rel_include_files)
    
    generate_neo4j_graph(all_file_dic_obj, host, user, psw)
    


if __name__ == "__main__":
    # bserv测试
    # source_root  = "F:\\lhh\\bserv\\bserv-main\\bserv"
    # include_search_dir_lst = ["include"]

    # libpqxx测试
    source_root  = "F:\\lhh\\py_test\\libpqxx"
    include_search_dir_lst = ["include"]
    
    # source_root = "F:\\lhh\\py_test\\boost" # 推荐全部传linux路径
    # include_search_dir_lst = []


    host = "bolt://localhost:7687"
    user = "neo4j"
    psw = "1234"
    linux_true = False  # 根据它来判断是lin还是win,如果是linux则是True，否则必须是False
    file_analysis(source_root, include_search_dir_lst, host, user, psw, linux_true)
    