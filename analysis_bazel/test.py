import re
import os

# def analysis_file_names_str(file_names_str):
#     file_names_lst = file_names_str.split(",")
#     new_file_name_lst = []
#     for i in range(len(file_names_lst)):
#         file_names_lst[i] = file_names_lst[i].strip()
#         if file_names_lst[i] == '':
#             continue
#         file_names_lst[i] = file_names_lst[i].lstrip('"')
#         file_names_lst[i] = file_names_lst[i].rstrip('"')
#         file_names_lst[i] = file_names_lst[i].lstrip("'")
#         file_names_lst[i] = file_names_lst[i].rstrip("'")
#         new_file_name_lst.append(file_names_lst[i])
#     return new_file_name_lst
#
# compile_str = 'cc_binary( name = "pj1", srcs = ["hello-world.cc"], deps = [ ":sandwich", ], ) cc_library( name = "sandwich", srcs = ["sandwich.cc"], hdrs = ["sandwich.h"], deps = [":bread"], ) cc_library( name = "bread", srcs = ["bread.cc"], hdrs = ["bread.h"], deps = [":flour"], ) cc_library( name = "flour", srcs = ["flour.cc"], hdrs = ["flour.h"], ) '
# # srcs\s*=\s*\[[\]\s*"(.*?)"\s*\[]\]
# lst_res = re.compile('cc_library\s*[(](.*?)[)]').findall(compile_str)
# print(lst_res)
# for x in lst_res:
#     print(x)
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
        # self.packageConfigs = {}

        self.mainPackage = None

class BuilderDocument:
    def __init__(self, docCfg):
        super(BuilderDocument, self).__init__()

        # corresponding document configuration
        self.config = docCfg

        # packages in this document: package root dir => BuilderPackage
        self.packages = {}

def analysis_file_by_scan(a, b):
    b.config.documentName = "hahaha"

doc_cfg = BuilderDocumentConfig()
doc_cfg.documentName = "sources"
doc_cfg.documentNamespace = "fdsa"
doc = BuilderDocument(doc_cfg)
analysis_file_by_scan("fdsa", doc)  #
print(doc.config.documentName)



