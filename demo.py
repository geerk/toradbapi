from __future__ import (absolute_import, division,
                        print_function, unicode_literals)

import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import tornado.gen
import tornado.platform.twisted
import mysql.connector

tornado.platform.twisted.install()

import toradbapi


DB_NAME = 'test_toradbapi'
DB_HOST = '127.0.0.1'
DB_PORT = 3306
DB_USER = 'root'
DB_PASSWORD = ''


class MainHandler(tornado.web.RequestHandler):

    def initialize(self, db):
        self.db = db

    @tornado.gen.coroutine
    def get(self):
        people = yield self.db.run_query('SELECT `name` FROM `person`')
        self.finish('<html><head><title>Demo toradbapi</title></head>'
                    '<body><h3>Type new name:</h3>'
                    '<form method="post"><input name="name" type="text"/>'
                    '<input type="submit" value="Submit"/></form>'
                    '<h3>Already inserted names:</h3>'
                    '<ul>%s</ul></body></html>' % ''.join(
                        '<li>%s</li>' % name for name in people))

    @tornado.gen.coroutine
    def post(self):
        name = self.get_argument('name')
        try:
            yield self.db.run_operation(
                # always use escaping functionality to avoid sql-injection
                'INSERT INTO `person` (`name`) VALUES (%s)',
                (name,))
        except mysql.connector.errors.DatabaseError as e:
            self.finish('<html><head><title>Demo toradbapi</title></head>'
                        '<body><h3>Error inserting new name: %s</h3>'
                        '<br/><a href="/">Main page</a></body></html>' % e)
        else:
            self.redirect('/')


def setup_database():
    # just to ensure that database and table exist
    cnx = mysql.connector.connect(
        user=DB_USER, passwd=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
    cursor = cnx.cursor()
    try:
        cursor.execute('CREATE DATABASE `%s` CHARACTER SET utf8' % DB_NAME)
    except mysql.connector.errors.DatabaseError:
        # do nothing if database exists
        pass
    cursor.execute('USE `%s`' % DB_NAME)
    cursor.execute('CREATE TABLE IF NOT EXISTS `person` ('
                   '    `name` varchar(255) NOT NULL,'
                   '    `dob` date DEFAULT NULL'
                   '    UNIQUE KEY (`name`))')
    cursor.close()
    cnx.close()


def main():
    setup_database()
    tornado.options.parse_command_line()
    pool = toradbapi.ConnectionPool(
        'mysql.connector', database=DB_NAME, user=DB_USER, port=DB_PORT,
        password=DB_PASSWORD, host=DB_HOST)
    application = tornado.web.Application([(r'/', MainHandler, {'db': pool})])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(8888, '127.0.0.1')
    try:
        tornado.ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        pass
    finally:
        pool.close()
        tornado.ioloop.IOLoop.instance().stop()


if __name__ == '__main__':
    main()
