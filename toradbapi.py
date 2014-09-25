from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

from twisted.enterprise.adbapi import ConnectionPool as TxConnectionPool
from tornado.concurrent import TracebackFuture


class ConnectionPool(object):
    """
    Wrapper for twisted.enterprise.adbapi.ConnectionPool to use with tornado.
    """

    def __init__(self, *args, **kwargs):
        self._pool = TxConnectionPool(*args, **kwargs)

    def run_query(self, *args, **kwargs):
        return self._defer_to_future(self._pool.runQuery(*args, **kwargs))

    def run_operation(self, *args, **kwargs):
        return self._defer_to_future(self._pool.runOperation(*args, **kwargs))

    def run_interaction(self, *args, **kwargs):
        return self._defer_to_future(self._pool.runInteraction(*args, **kwargs))

    def close(self):
        self._pool.close()

    @staticmethod
    def _defer_to_future(defer):
        future = TracebackFuture()
        defer.addCallbacks(
            future.set_result,
            lambda failure: future.set_exc_info(
                (failure.type, failure.value, failure.tb)))
        return future
