from file_process import *


def add_library_name(lib_name, name):
    return lib_name + "/" + name


def analysis_name(string_name):
    res_lst = string_name.split(".")
    if len(res_lst) == 2:
        return True
    else:
        return False


# analysis "" 's content
def analysis_rel_include_content(file_obj, all_file_dic_obj, source_root, linux_true, lib_name):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    for content in file_obj.rel_include_files:
        full_path_temp = file_obj.file_full_path
        if not linux_true:
            full_path_temp = change_lin_path_to_win(full_path_temp)
            content = change_lin_path_to_win(content)
        # windows forbidden
        if content.startswith("aux"):
            continue
        full_name = os.path.join(os.path.dirname(full_path_temp), content)
        full_name = os.path.abspath(full_name)
        if analysis_name(full_name):
            dic_full_name = os.path.relpath(full_name, source_root)
            p_temp = add_library_name(lib_name, change_win_path_to_linux(dic_full_name))
            if p_temp in all_file_dic_obj.keys():
                file_obj.include_name.add(p_temp)
            else:  # not exist then add in sys_include_files
                file_obj.sys_include_files.append(change_win_path_to_linux(content))
        else:  # not include .xxx，but use ""   not common
            file_obj.sys_include_files.append(change_win_path_to_linux(content))


# include_search_dir_lst: all rel path
def search_include_file(content, source_root, include_dir_files, linux_true):
    if not linux_true:
        source_root = change_lin_path_to_win(source_root)
    for search_path, files in include_dir_files.items():
        if not linux_true:
            search_path = change_win_path_to_linux(search_path)
            content = change_win_path_to_linux(content)
        files_set = files
        if content in files_set:
            if not linux_true:
                search_path = change_lin_path_to_win(search_path)
                content = change_lin_path_to_win(content)
            res = os.path.relpath(os.path.join(source_root, search_path, content), source_root)
            return True, change_win_path_to_linux(res)
    return False, ""


def search_library_file(lan, file, search_library_lst, nebula_driver, dependency_lib_files):
    for library in search_library_lst:
        if library == "#":
            file_name = lan + "_" + library + file
        else:
            library_name = lan + "_" + "#" + library
            file_name = add_library_name(library_name, file)  # file's vid
        if file_name in dependency_lib_files:
            return True, file_name
        else:
            res_len = nebula_driver.find_node(file_name)
            if res_len:
                dependency_lib_files.add(file_name)
                return True, file_name
    return False, ""


# analysis #include<> content ，also include #include"" 's content
def analysis_sys_include_content(lan, file_obj, all_file_dic_obj, source_root, include_dir_files, search_library_lst,
                                 linux_true, nebula_driver, lib_name, dependency_lib_files):
    for content in file_obj.sys_include_files:
        content_temp = add_library_name(lib_name, content)
        if content_temp in all_file_dic_obj.keys():
            file_obj.include_name.add(content_temp)
        else:
            # 1、find in include_dir_files，2、find in dependency files，3、then add new file
            if len(include_dir_files) != 0:
                res, res_content = search_include_file(content, source_root, include_dir_files, linux_true)
                if res:
                    file_obj.include_name.add(add_library_name(lib_name, res_content))
                    continue
            if len(search_library_lst) != 0:
                res2, res_content2 = search_library_file(lan, content, search_library_lst, nebula_driver, dependency_lib_files)
                if res2:
                    file_obj.include_name.add(res_content2)
                    continue
            file = FileInfo(content, "", False)
            f_temp = add_library_name(lib_name, content)
            all_file_dic_obj[f_temp] = file
            file_obj.include_name.add(f_temp)
