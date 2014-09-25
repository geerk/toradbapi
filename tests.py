from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from future.builtins import super
from datetime import date

from tornado.ioloop import IOLoop
from tornado.testing import AsyncTestCase, gen_test
import tornado.platform.twisted
import mysql.connector

tornado.platform.twisted.install()

from toradbapi import ConnectionPool


class ConnectionPoolTestCase(AsyncTestCase):
    DB_CONFIG = {
        'user': 'root', 'password': '', 'host': '127.0.0.1', 'port': 3306}
    DB_NAME = 'test_toradbapi'
    DB_DRIVER = 'mysql.connector'

    def get_new_ioloop(self):
        # use singleton ioloop and reactor across all tests
        return IOLoop.instance()

    def setUp(self):
        super().setUp()
        # create test database and test table
        self.cnx = mysql.connector.connect(**self.DB_CONFIG)
        self.cursor = self.cnx.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS `person` ('
                            '    `name` varchar(255) NOT NULL,'
                            '    `dob` date DEFAULT NULL,'
                            '    UNIQUE KEY (`name`))')
        # create connection pool
        self.pool = ConnectionPool(
            self.DB_DRIVER, database=self.DB_NAME, **self.DB_CONFIG)

    def tearDown(self):
        self.cursor.execute('DROP TABLE `person`')
        self.cursor.close()
        self.cnx.close()
        self.pool.close()
        super().tearDown()

    @gen_test
    def test_run_query_empty(self):
        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(result, [])

    @gen_test
    def test_insert_select(self):
        yield self.pool.run_operation(
            'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
            ('testname', date(1000, 10, 10)))
        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(result, [('testname', date(1000, 10, 10))])

    @gen_test
    def test_transaction_error(self):
        def _interaction(txn):
            txn.execute(
                'INSERT INTO `person` (`dob`) VALUES (%s)')
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname', date(1000, 10, 10)))
        try:
            yield self.pool.run_interaction(_interaction)
        except mysql.connector.errors.ProgrammingError:
            pass
        else:
            self.fail()

        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(result, [])

    @gen_test
    def test_transaction_rollback(self):
        def _interaction(txn):
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname', date(1000, 10, 10)))
            txn.execute('SELECT * FROM `person`')
            self.assertEqual(txn.fetchall(), [('testname', date(1000, 10, 10))])
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname', date(1000, 10, 10)))
        try:
            yield self.pool.run_interaction(_interaction)
        except mysql.connector.errors.DatabaseError:
            pass
        else:
            self.fail()

        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(result, [])

    @gen_test
    def test_transaction_success(self):
        def _interaction(txn):
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname0', date(1000, 10, 10)))
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname1', date(1111, 11, 11)))

        yield self.pool.run_interaction(_interaction)

        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(result, [
            ('testname0', date(1000, 10, 10)),
            ('testname1', date(1111, 11, 11))])
