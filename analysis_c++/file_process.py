import os
import re
from object_class import FileInfo


def change_win_path_to_linux(win_path):
    return '/'.join(win_path.split('\\'))


def change_lin_path_to_win(lin_path):
    return '\\'.join(lin_path.split('/'))


# read every .c .C .cc .cxx .c++ .cpp .h .hpp .hxx file
def visit_all_files(source_root, linux_true, exclude_dir_lst):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    files_unique_info = []
    for (currentDir, _, filenames) in os.walk(source_root_temp):
        relpath = os.path.relpath(currentDir, source_root)
        if not linux_true:
            dir_name = relpath.split("\\")[0]
        else:
            dir_name = relpath.split("/")[0]
        if dir_name in exclude_dir_lst:
            continue
        for filename in filenames:
            file_suffix = filename.split(".")[-1]
            if file_suffix == 'c' or file_suffix == 'C' or file_suffix == 'cc' or file_suffix == 'cxx' or file_suffix == 'c++' or file_suffix == 'cpp' or file_suffix == 'h' or file_suffix == 'hpp' or file_suffix == 'hxx':
                p = os.path.join(currentDir, filename)
                if not linux_true:
                    p = change_win_path_to_linux(p)
                    filename = change_win_path_to_linux(filename)
                file = FileInfo(filename, p, True)
                files_unique_info.append(file)
    return files_unique_info


def contains_include_in_file(p, linux_true):
    if not linux_true:
        p = change_lin_path_to_win(p)
    sys_files_name = []
    rel_files_name = []
    f = open(p, 'r', encoding='ISO-8859-1')
    line = f.readline()
    while line:
        line = line.strip()
        res_lst1 = re.compile('#\s*include\s*["](.*?)["]').findall(line)
        res_lst2 = re.compile('#\s*include\s*[<](.*?)[>]').findall(line)
        if len(res_lst1) != 0 or len(res_lst2) != 0:
            return True
        line = f.readline()
    f.close()
    return False


# if one file contains #include, view as a source file
def visit_all_files2(source_root, linux_true, exclude_dir_lst):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    files_unique_info = []
    for (currentDir, _, filenames) in os.walk(source_root_temp):
        relpath = os.path.relpath(currentDir, source_root)
        if not linux_true:
            dir_name = relpath.split("\\")[0]
        else:
            dir_name = relpath.split("/")[0]
        if dir_name in exclude_dir_lst:
            continue
        for filename in filenames:
            p = os.path.join(currentDir, filename)
            if contains_include_in_file(p, linux_true):
                if not linux_true:
                    p = change_win_path_to_linux(p)
                    filename = change_win_path_to_linux(filename)
                file = FileInfo(filename, p, True)
                files_unique_info.append(file)
    return files_unique_info


def visit_include_dir(include_dir_lst, source_root, linux_true):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    include_dirs_dict = {}
    for search_dir in include_dir_lst:
        if not linux_true:
            search_dir = change_lin_path_to_win(search_dir)
        search_dir_full_name = os.path.join(source_root_temp, search_dir)
        dir_set = set()
        for (currentDir, _, filenames) in os.walk(search_dir_full_name):

            for filename in filenames:
                file_suffix = filename.split(".")[-1]
                if file_suffix == 'c' or file_suffix == 'C' or file_suffix == 'cc' or file_suffix == 'cxx' or file_suffix == 'c++' or file_suffix == 'cpp' or file_suffix == 'h' or file_suffix == 'hpp' or file_suffix == 'hxx':
                    p = os.path.join(currentDir, filename)
                    temp_path = os.path.relpath(p, search_dir_full_name)
                    if not linux_true:
                        temp_path = change_win_path_to_linux(temp_path)
                    dir_set.add(temp_path)
        if not linux_true:
            search_dir = change_win_path_to_linux(search_dir)
        include_dirs_dict[search_dir] = dir_set
    return include_dirs_dict


# if one file contains #include, view as a source file
def visit_include_dir2(include_dir_lst, source_root, linux_true):
    source_root_temp = source_root
    if not linux_true:
        source_root_temp = change_lin_path_to_win(source_root_temp)
    include_dirs_dict = {}
    for search_dir in include_dir_lst:
        if not linux_true:
            search_dir = change_lin_path_to_win(search_dir)
        search_dir_full_name = os.path.join(source_root_temp, search_dir)
        dir_set = set()
        for (currentDir, _, filenames) in os.walk(search_dir_full_name):
            for filename in filenames:
                p = os.path.join(currentDir, filename)
                if contains_include_in_file(p, linux_true):
                    temp_path = os.path.relpath(p, search_dir_full_name)
                    if not linux_true:
                        temp_path = change_win_path_to_linux(temp_path)
                    dir_set.add(temp_path)
        if not linux_true:
            search_dir = change_win_path_to_linux(search_dir)
        include_dirs_dict[search_dir] = dir_set
    return include_dirs_dict


def read_file_content(file_path, linux_true, num_lines=200):
    """

    Args:
        file_path: file's full_path
        linux_true: linux is true
        num_lines: not contain #include lines > num_lines then finish reading

    Returns: sys_files_name(list), rel_files_name(list)

    """
    if not linux_true:
        file_path = change_lin_path_to_win(file_path)
    sys_files_name = []
    rel_files_name = []
    not_include_line_num = 0
    f = open(file_path, 'r', encoding='ISO-8859-1')
    line = f.readline()
    while line:
        if not_include_line_num > num_lines:
            break
        line = line.strip()
        res_lst1 = re.compile('#\s*include\s*["](.*?)["]').findall(line)
        res_lst2 = re.compile('#\s*include\s*[<](.*?)[>]').findall(line)
        if len(res_lst1) != 0 or len(res_lst2) != 0:
            not_include_line_num = 0
            if len(res_lst1) == 1:
                rel_files_name.append(res_lst1[0])
            elif len(res_lst2) == 1:
                sys_files_name.append(res_lst2[0])
            else:
                print("include部分分析错误！！！")
        elif len(line) != 0:
            not_include_line_num += 1
        line = f.readline()
    f.close()
    return sys_files_name, rel_files_name
