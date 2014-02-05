# -*- coding: utf-8 -*-

from . import GenericCommand

from django.db.models import get_models, get_app
from django.db import connection
from django.db import DEFAULT_DB_ALIAS
from optparse import make_option
import os


class Command(GenericCommand):
    option_list = GenericCommand.option_list + (
        make_option('--database', action='store', dest='database',
                    default=DEFAULT_DB_ALIAS,
                    help='Nominates a database to print the '
                         'SQL for.  Defaults to the "default" database.'),
        make_option('--user', action='store', dest='user',
                    default=None,
                    help='Database user. '
                         'Some comands requires root privillege'),
        make_option('--password', action='store', dest='password',
                    default=None,
                    help="Database user's password. "),
    )

    def command_reset_autoincrement(self, *args, **options):

        queries = []
        for model in get_models():
            try:
                max_id = model.objects.latest('id').id + 1
            except:
                max_id = 1

            sql = 'ALTER TABLE %s AUTO_INCREMENT = %d'
            queries.append(sql % (model._meta.db_table, max_id))

        cursor = connection.cursor()
        map(lambda query: cursor.execute(query), queries)

    def command_list_models(self, app_label=None, *args, **options):
        if not app_label:
            print "db list_models you_app_label"
            return

        for model in get_models(get_app(app_label)):
            print model

    def exec_sql(self, user, password, sql, fetchall=False):
        import MySQLdb
        con = MySQLdb.connect(
            user=user,
            passwd=password
        )
        cursor = con.cursor()
        cursor.execute(sql)
        return cursor.fetchall() if fetchall else cursor

    def print_dict(self, dict_data, heading=''):
        import json

        print heading,
        print json.dumps(dict_data, indent=4)

    def command_createdb(self, *args, **options):
        d = options.get('database', 'default')
        from django.conf import settings
        self.print_dict(settings.DATABASES, "@@@ Your database settings :")
        if settings.DATABASES[d]['ENGINE'] is 'django.db.backends.sqlite3':
            print "@@@ Not required to create database, just do syncdb."
            return

        p = settings.DATABASES[d]
        p['SOURCE'] = p['HOST'] or 'localhost'
        MYSQL_CREATEDB = """
        CREATE DATABASE %(NAME)s
        DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
        GRANT ALL on %(NAME)s.*
        to '%(USER)s'@'%(SOURCE)s'
        identified by '%(PASSWORD)s' WITH GRANT OPTION;
        """

        cursor = self.exec_sql(
            options['user'] or os.environ.get('DBROOT_USER', ''),
            options['password'] or os.environ.get('DBROOT_PASSWD', ''),
            "show databases"
        )

        if (p['NAME'],) in cursor.fetchall():
            print "database %(NAME)s exists" % p
            return
        else:
            query = MYSQL_CREATEDB % p
            print "executing:\n", query
            cursor.execute(query)
            for r in cursor.fetchall():
                print r

    def command_dropdb(self, *args, **options):
        from django.conf import settings
        p = settings.DATABASES[options.get('database', 'default')]
        self.print_dict(p, "@@@ Your database settings :")
        if p['ENGINE'] is 'django.db.backends.sqlite3':
            print "@@@ Not required to create database, just do syncdb."
            return

        i = raw_input("Are you ready to delete %(NAME)s ?=[y/n]" % p)
        if i != 'y':
            return

        print self.exec_sql(
            options['user'] or os.environ.get('DBROOT_USER', ''),
            options['password'] or os.environ.get('DBROOT_PASSWD', ''),
            "drop database %(NAME)s" % p,
            fetchall=True,
        )
