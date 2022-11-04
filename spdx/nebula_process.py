import sys
import time
import threading
from nebula3.gclient.net import ConnectionPool
from nebula3.Config import Config
from FormatResp import print_resp


class NebulaClientDriver:
    def __init__(self, host="123.60.77.114", port=9669, user_name="root", password="nubula", space_name="",
                 pool_size=4):
        self.host = host
        self.port = port
        self.user_name = user_name
        self.password = password
        self.space_name = space_name
        self.config = Config()
        self.config.max_connection_pool_size = pool_size
        self.connection_pool = ConnectionPool()

    def connect(self):
        # init connection pool
        assert self.connection_pool.init([(self.host, self.port)], self.config)

    def create_vertex(self, v_type, data):
        try:
            nebula_client = self.connection_pool.get_session(self.user_name, self.password)
            assert nebula_client is not None
            # select space
            nebula_client.execute('USE {}'.format(self.space_name))
            if v_type == "File":
                nebula_client.execute(
                    'INSERT VERTEX {}(file_name, full_path) VALUES '.format(v_type) + data
                )
            elif v_type == "Package":
                nebula_client.execute(
                    'INSERT VERTEX {}() VALUES '.format(v_type) + data
                )
            elif v_type == "Library":
                nebula_client.execute(
                    'INSERT VERTEX {}(full_path) VALUES '.format(v_type) + data
                )

        except Exception as x:
            print(x)
            import traceback

            print(traceback.format_exc())

    def create_edge(self, e_type, data):
        try:
            nebula_client = self.connection_pool.get_session(self.user_name, self.password)
            assert nebula_client is not None
            if e_type == "Include":
                nebula_client.execute('USE {}'.format(self.space_name))
                nebula_client.execute(
                    'INSERT EDGE Include() VALUES ' + data
                )
            elif e_type == "Contain":
                nebula_client.execute('USE {}'.format(self.space_name))
                nebula_client.execute(
                    'INSERT EDGE Contain() VALUES ' + data
                )

        except Exception as x:
            print(x)
            import traceback

            print(traceback.format_exc())

    def close(self):
        # close connect pool
        self.connection_pool.close()


if __name__ == '__main__':
    nebula_obj = NebulaClientDriver(space_name="libpqxx_test")
    nebula_obj.connect()
    # nebula_obj.create_vertex()
    nebula_obj.close()
