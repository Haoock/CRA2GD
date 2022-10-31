
from select import select
from neo4j import GraphDatabase


class Neo4j_Client_Driver:
    def __init__(self):
        self.driver = None

    def connect(self, host, user, password, encrypted = False):
        try:
            neo4j_host = host
            neo4j_user = user
            neo4j_passport = password
            neo4j_encrypted = encrypted
            self.driver = GraphDatabase.driver(neo4j_host, auth=(neo4j_user, neo4j_passport), encrypted=neo4j_encrypted)
        except Exception:
            print("Neo4j连接失败")

    def clear_db(self):
        with self.driver.session() as session:
            return session.run("match (n) detach delete n;")

    # 创建用户自定义的文件节点
    def __create_user_file_node(self, tx, name, full_path):
        result = tx.run("CREATE (n:UserFile {file_name: $name, full_path: $full_path}) return id(n) as node_id", name=name, full_path=full_path)
        record = result.single()
        return record["node_id"]

    # 创建系统文件
    def __create_sys_file_node(self, tx, name, full_path):
        result = tx.run("CREATE (n:SysFile {file_name: $name, full_path: $full_path}) return id(n) as node_id", name=name, full_path=full_path)
        record = result.single()
        return record["node_id"]


    def create_node(self, name, full_path, is_user_file):
        with self.driver.session() as session:
            if is_user_file:
                node_id = session.execute_write(self.__create_user_file_node, name, full_path)
            else:
                node_id = session.execute_write(self.__create_sys_file_node, name, full_path)
        return node_id

    def __create_include_relationship(self, tx, id1, id2):
        tx.run("match(a) where id(a) = $id1 match(b) where id(b) = $id2 create (a) -[:include]->(b);", id1 = id1, id2 = id2)


    def __create_import_relationship(self, tx, id1, id2):
        tx.run("match(a) where id(a) = $id1 match(b) where id(b) = $id2 create (a) -[:import]->(b);", id1 = id1, id2 = id2)


    def __create_third_party_relationship(self, tx, id1, name):
        tx.run("match(a:JavaFile),(b:ThirdParty) where id(a) = $id1 and b.name = $name create (a) -[:import_third_party]->(b);", id1 = id1, name=name)


    def __create_same_package_relationship(self, tx, id1, id2):
        tx.run("match(a) where id(a) = $id1 match(b) where id(b) = $id2 create (a) -[:same_package]->(b);", id1 = id1, id2 = id2)


    def create_import_edge(self, id1, id2):
        with self.driver.session() as session:
            session.write_transaction(self.__create_import_relationship, id1, id2)


    def create_third_party_edge(self, id1, name):
        with self.driver.session() as session:
            session.write_transaction(self.__create_third_party_relationship, id1, name)


    def create_same_package_edge(self, id1, id2):
        with self.driver.session() as session:
            session.write_transaction(self.__create_same_package_relationship, id1, id2)


    def create_edge(self, id1, id2):
        with self.driver.session() as session:
            session.execute_write(self.__create_include_relationship, id1, id2)

    def __run_cypher(self, tx, cypher):
        result = tx.run(cypher) # 这是一个StatementResult对象
        lst = []
        # print(type(result))
        for record in result:  # 实际上它是由Record对象组成的集合
            # print(record)  # 这是每一条结果
            # print(record.keys())  # 返回record中所有可以使用的关键字
            # print(record.get('n'))  # 使用关键字来获取record中的值
            lst.append(record)
        return lst

    def close(self):
        self.driver.close()

    def __create_import_node(self, tx, name, full_path):
        result = tx.run("CREATE (n:JavaFile {file_name: $name, full_path: $full_path}) return id(n) as node_id", name=name, full_path=full_path)
        record = result.single()
        return record["node_id"]

    def __create_third_party_node(self, tx, name):
        result = tx.run("CREATE (n:ThirdParty {name: $name}) return id(n) as node_id", name=name)
        record = result.single()
        return record["node_id"]

    def create_import_node(self, name, full_path):
        with self.driver.session() as session:
            node_id = session.write_transaction(self.__create_import_node, name, full_path)
        return node_id

    def create_third_party_node(self, name):
        with self.driver.session() as session:
            node_id = session.write_transaction(self.__create_third_party_node, name)
        return node_id


        

    def run(self, cypher):
        """
        专门用于Match查询语句的执行
        Args:
            cypher: cypher语句

        Returns:
            返回StatementResult和Record
        """
        with self.driver.session() as session:
            # return session.run(cypher)
            return session.read_transaction(self.__run_cypher, cypher)

if __name__ == "__main__":
    neo4j_obj = Neo4j_Client_Driver()
    neo4j_obj.connect("bolt://localhost:7687", "neo4j", "dudu990911")
    # neo4j_obj.clear_db()
    # node_id1 = neo4j_obj.create_node("bserv.hpp", "bser/main/test", True)
    # node_id2 = neo4j_obj.create_node("bserv.cpp", "bser/main/test", True)
    # neo4j_obj.create_edge(node_id1, node_id2)
    
    neo4j_obj.run("match (a)-[r:same_package]->(b) DELETE r")