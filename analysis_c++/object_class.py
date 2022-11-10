class FileInfo:
    def __init__(self, name, full_path, is_user_file, sys_files=None, rel_files=None) -> None:
        if rel_files is None:
            rel_files = []
        if sys_files is None:
            sys_files = []
        self.file_name = name

        self.file_full_path = full_path  # linux type path

        self.is_user_file = is_user_file  # user_file or sys_file

        self.sys_include_files = sys_files  # #include<>

        self.rel_include_files = rel_files  # #include""

        self.include_name = set()  # all_file_dic_obj's key

        self.node_id = None  # id in neo4j database
