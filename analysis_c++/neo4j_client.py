from select import select
from neo4j import GraphDatabase


class Neo4j_Client_Driver:
    def __init__(self):
        self.driver = None

    def connect(self, host="bolt://localhost:7687", user="neo4j", password="1234", encrypted=False):
        try:
            neo4j_host = host
            neo4j_user = user
            neo4j_passport = password
            neo4j_encrypted = encrypted
            self.driver = GraphDatabase.driver(neo4j_host, auth=(neo4j_user, neo4j_passport), encrypted=neo4j_encrypted)
        except Exception:
            print("Neo4j connect failed")

    def clear_db(self):
        with self.driver.session() as session:
            return session.run("match (n) detach delete n;")

    # 创建用户自定义的文件节点
    def __create_user_file_node(self, tx, name, full_path):
        result = tx.run("CREATE (n:UserFile {file_name: $name, full_path: $full_path}) return id(n) as node_id",
                        name=name, full_path=full_path)
        record = result.single()
        return record["node_id"]

    def __create_sys_file_node(self, tx, name, full_path):
        result = tx.run("CREATE (n:SysFile {file_name: $name, full_path: $full_path}) return id(n) as node_id",
                        name=name, full_path=full_path)
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
        tx.run("match(a) where id(a) = $id1 match(b) where id(b) = $id2 create (a) -[:include]->(b);", id1=id1, id2=id2)

    def create_edge(self, id1, id2):
        with self.driver.session() as session:
            session.execute_write(self.__create_include_relationship, id1, id2)

    def __run_cypher(self, tx, cypher):
        result = tx.run(cypher)  # StatementResult obj
        lst = []
        # print(type(result))
        for record in result:  # Record obj
            # print(record)
            # print(record.keys())
            # print(record.get('n'))
            lst.append(record)
        return lst

    def close(self):
        self.driver.close()

    def run(self, cypher):
        """
        find results in match
        Args:
            cypher: cypher phrases

        Returns:
            StatementResult and Record
        """
        with self.driver.session() as session:
            # return session.run(cypher)
            return session.execute_read(self.__run_cypher, cypher)


if __name__ == "__main__":
    neo4j_obj = Neo4j_Client_Driver()
    neo4j_obj.connect("bolt://localhost:7687", "neo4j", "1234")
    neo4j_obj.clear_db()
    # node_id1 = neo4j_obj.create_node("bserv.hpp", "bser/main/test", True)
    # node_id2 = neo4j_obj.create_node("bserv.cpp", "bser/main/test", True)
    # neo4j_obj.create_edge(node_id1, node_id2)

    lst = neo4j_obj.run("match (n) return n;")
    print(lst)