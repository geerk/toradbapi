from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
from datetime import date

from tornado.ioloop import IOLoop
from tornado.testing import AsyncTestCase, gen_test
from tornado.test.util import unittest
import tornado.platform.twisted
import mysql.connector
import pymysql

try:
    import MySQLdb
except ImportError:
    MySQLdb = None

tornado.platform.twisted.install()

from toradbapi import ConnectionPool


class MySQLConnectorConnectionPoolTestCase(AsyncTestCase):
    DB_CONFIG = dict(
        user='root', passwd='', host='127.0.0.1', port=3306,
        db='test_toradbapi')
    DB_DRIVER = 'mysql.connector'
    DATABASE_ERROR = mysql.connector.errors.DatabaseError
    PROGRAMMING_ERROR = mysql.connector.errors.ProgrammingError

    def get_new_ioloop(self):
        # use singleton ioloop and reactor across all tests
        return IOLoop.instance()

    def setUp(self):
        super(MySQLConnectorConnectionPoolTestCase, self).setUp()
        # create test database and test table
        self.cnx = mysql.connector.connect(**self.DB_CONFIG)
        self.cursor = self.cnx.cursor()
        self.cursor.execute('CREATE TABLE IF NOT EXISTS `person` ('
                            '    `name` varchar(255) NOT NULL,'
                            '    `dob` date DEFAULT NULL,'
                            '    UNIQUE KEY (`name`))')
        # create connection pool
        self.pool = ConnectionPool(self.DB_DRIVER, **self.DB_CONFIG)

    def tearDown(self):
        self.cursor.execute('DROP TABLE `person`')
        self.cursor.close()
        self.cnx.close()
        self.pool.close()
        super(MySQLConnectorConnectionPoolTestCase, self).tearDown()

    @gen_test
    def test_run_query_empty(self):
        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(list(result), [])

    @gen_test
    def test_insert_select(self):
        yield self.pool.run_operation(
            'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
            ('testname', date(1000, 10, 10)))
        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(list(result), [('testname', date(1000, 10, 10))])

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
        except self.PROGRAMMING_ERROR:
            pass
        else:
            self.fail()

        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(list(result), [])

    @gen_test
    def test_transaction_rollback(self):
        def _interaction(txn):
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname', date(1000, 10, 10)))
            txn.execute('SELECT * FROM `person`')
            self.assertEqual(list(txn.fetchall()),
                             [('testname', date(1000, 10, 10))])
            txn.execute(
                'INSERT INTO `person` (`name`, `dob`) VALUES (%s, %s)',
                ('testname', date(1000, 10, 10)))
        try:
            yield self.pool.run_interaction(_interaction)
        except self.DATABASE_ERROR:
            pass
        else:
            self.fail()

        result = yield self.pool.run_query('SELECT * FROM `person`')
        self.assertEqual(list(result), [])

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
        self.assertEqual(list(result), [
            ('testname0', date(1000, 10, 10)),
            ('testname1', date(1111, 11, 11))])


@unittest.skipIf(MySQLdb is None, 'MySQLdb is not available')
class MySQLdbConnectionPoolTestCase(MySQLConnectorConnectionPoolTestCase):
    DB_DRIVER = 'MySQLdb'

    @classmethod
    def setUpClass(cls):
        cls.DATABASE_ERROR = MySQLdb.DatabaseError
        cls.PROGRAMMING_ERROR = MySQLdb.ProgrammingError


class PyMySQLConnectionPoolTestCase(MySQLConnectorConnectionPoolTestCase):
    DB_DRIVER = 'pymysql'
    DATABASE_ERROR = pymysql.DatabaseError
    PROGRAMMING_ERROR = pymysql.ProgrammingError
