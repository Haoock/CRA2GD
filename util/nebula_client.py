from nebula3.Config import Config
from nebula3.gclient.net import ConnectionPool
def nebula_client():
    config = Config()
    config.max_connection_pool_size = 10

    connection_pool = ConnectionPool()
    assert connection_pool.init([('123.60.77.114', 9669)], config)
    client = connection_pool.get_session('root', 'nebula')
    return config, client