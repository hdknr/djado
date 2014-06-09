# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand
from pycommand.command import Command as PyCommand, SubCommand
from django.db.models import get_models, get_app
from django.db import connection
#from django.db import DEFAULT_DB_ALIAS
import os

_sphinx_format = '''
.. _%(module)s.%(object_name)s:

%(object_name)s
%(sep)s

.. autoclass:: %(module)s.%(object_name)s
    :members:

'''


class SqlCommand(SubCommand):
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


class Command(BaseCommand, PyCommand):
    managers = ['manage.py', 'do.py']

    def run_from_argv(self, argv):
        return self.run(argv)

    class ResetAutoIncrement(SubCommand):
        name = "reset_autoincrement"
        description = "Reset MySQL autoincrement value."
        args = []

        def run(self, params, **options):
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

    class ListModel(SubCommand):
        name = "list_model"
        description = "List Model"
        args = [
            (('app_labels',), dict(nargv='+', help="app_label")),
            (('--sphinx', '-s'),
             dict(action='store_true', help="sphinx format")),
        ]

        def run(self, params, **options):

            for app_label in params.app_labels:
                for model in get_models(get_app(app_label)):
                    if params.sphinx:
                        print _sphinx_format % {
                            "app_label": app_label,
                            "module": model.__module__,
                            "object_name": model._meta.object_name,
                            "sep": '-' * len(model._meta.object_name),
                        }
                    else:
                        print model

    class CreatDatabase(SqlCommand):
        name = "createdb"
        description = "Create Database"
        args = [
            (('--user', '-u'),
             dict(default=os.environ.get("DBROOT_USER"),
                  help="database user")
            ),
            (('--password', '-p'),
             dict(default=os.environ.get("DBROOT_PASSWD"),
             help="database password")),
            (('--database', '-d'),
             dict(default="default", help="database to created")),
        ]

        MYSQL_CREATEDB = """
        CREATE DATABASE %(NAME)s
        DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
        GRANT ALL on %(NAME)s.*
        to '%(USER)s'@'%(SOURCE)s'
        identified by '%(PASSWORD)s' WITH GRANT OPTION;
        """

        def run(self, params, **options):
            from django.conf import settings
            self.print_dict(settings.DATABASES, "@@@ Your database settings :")

            if settings.DATABASES[params.database]['ENGINE'] \
                    is 'django.db.backends.sqlite3':

                print "@@@ Not required to create database, just do syncdb."
                return

            p = settings.DATABASES[params.database]
            p['SOURCE'] = p.get('HOST', 'localhost')

            cursor = self.exec_sql(
                params.user, params.password,
                "show databases"
            )

            if (p['NAME'],) in cursor.fetchall():
                print "database %(NAME)s exists" % p
                return
            else:
                query = self.MYSQL_CREATEDB % p
                print "executing:\n", query
                cursor.execute(query)
                for r in cursor.fetchall():
                    print r

    class DropDatabase(SqlCommand):
        name = "dropdb"
        description = "Drop Database"
        args = [
            (('--database', '-d'),
             dict(default="default", help="database to created")),
        ]

        def run(self, params, **options):
            from django.conf import settings
            p = settings.DATABASES[params.database]

            self.print_dict(p, "@@@ Your database settings :")
            if p['ENGINE'] == 'django.db.backends.sqlite3':
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

    class DumpDatabase(SqlCommand):
        name = "dumpdb"
        description = "Dump Database"
        args = [
            (('--database', '-d'),
             dict(default="default", help="database to created")),
            (('--dryrun', '-r'),
             dict(action='store_true', help="dry run(rehearsal)")),
        ]
        MYSQLDUMP = "mysqldump -c --skip-extended-insert"
        MYSQLPARAM_F = " -u %(USER)s --password=%(PASSWORD)s %(NAME)s"

        def run(self, params, **options):
            from django.conf import settings
            p = settings.DATABASES[params.database]

            if p['ENGINE'] == 'django.db.backends.mysql':
                cmd = self.MYSQLDUMP + self.MYSQLPARAM_F % p
                print cmd
                params.dryrun or os.system(cmd)
                return

    class DumpSchemea(SqlCommand):
        name = "dumpschema"
        description = "Dump Database Schema"
        args = [
            (('--database', '-d'),
             dict(default="default", help="database to created")),
            (('--dryrun', '-r'),
             dict(action='store_true', help="dry run(rehearsal)")),
        ]
        MYSQLDUMP = "mysqldump --no-data"
        MYSQLPARAM_F = " -u %(USER)s --password=%(PASSWORD)s %(NAME)s"

        def run(self, params, **options):
            from django.conf import settings
            p = settings.DATABASES[params.database]

            if p['ENGINE'] == 'django.db.backends.mysql':
                cmd = self.MYSQLDUMP + self.MYSQLPARAM_F % p
                print cmd
                params.dryrun or os.system(cmd)
                return
