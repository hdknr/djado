# -*- coding: utf-8 -*-

from pycommand import djcommand
from django.db.models import Model, get_models, get_app, get_apps
from django.db import connection, connections
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_unicode
# from django.utils import functional
import json
import os
import re
import inspect

_format = dict(
    line='{module}.{object_name} {db_table}',
    sphinx='''
.. _{module}.{object_name}:

{object_name}
{sep}

.. autoclass:: {module}.{object_name}
    :members:

''',
)


class SqlCommand(djcommand.SubCommand):

    class JsonEncoder(DjangoJSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                obj = list(obj)
            elif callable(obj):
                return str(obj)
            elif type(obj).__name__ == '__proxy__':
                return force_unicode(obj)

            return super(SqlCommand.JsonEncoder, self).default(obj)

    def to_json(self, obj):
        return json.dumps(
            self.fields, indent=2, ensure_ascii=False,
            cls=self.JsonEncoder)

    def models(self):
        return get_models()

    def model_fullname(self, model):
        return "{0}.{1}".format(
            model.__module__, model.__name__)

    def exec_sql(self, user, password, sql, fetchall=False):
        import MySQLdb
        con = MySQLdb.connect(
            user=user,
            passwd=password
        )
        cursor = con.cursor()
        cursor.execute(sql)
        return cursor.fetchall() if fetchall else cursor

    def mysqldump(self, USER=None, PASSWORD=None, NAME=None,
                  options=None, *args, **kwargs):
        options = options or []
        return "mysqldump {0} -u {1} --password={2} {3}".format(
            " ".join(options),
            USER, PASSWORD, NAME)

    def mysqldump_data(self, USER=None, PASSWORD=None, NAME=None,
                       options=None, **kwargs):
        options = options or (
            "--skip-extended-insert",  # line by line
            "-c",                      # full column name
            "-t",                      # no DDL
        )
        return self.mysqldump(USER, PASSWORD, NAME, options, **kwargs)

    def print_dict(self, dict_data, heading=''):
        import json

        print heading,
        print json.dumps(dict_data, ensure_ascii=False, indent=4)


class Command(djcommand.Command):

    class ResetAutoIncrement(djcommand.SubCommand):
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

    class ListModel(djcommand.SubCommand):
        name = "list_model"
        description = "List Model"
        args = [
            (('app_labels',), dict(nargs='+', help="app_label")),
            (('--format', '-f',),
             dict(default='line', help="format=[line|sphinx]")),
        ]

        def run(self, params, **options):

            for app_label in params.app_labels:
                for model in get_models(get_app(app_label)):
                    data = {
                        "app_label": app_label,
                        "module": model.__module__,
                        "object_name": model._meta.object_name,
                        "sep": '-' * len(model._meta.object_name),
                        "db_table": model._meta.db_table,
                    }
                    print _format[params.format].format(**data)

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

    class DumpData(SqlCommand):
        name = "dumpsdata"
        description = "Dump Database Data"
        args = [
            (('tables',), dict(nargs='*', help="Database Tables")),
            (('--database', '-d'),
             dict(default="default", help="database to created")),
            (('--dryrun', '-r'),
             dict(action='store_true', help="dry run(rehearsal)")),
        ]

        def run(self, params, **options):
            from django.conf import settings
            p = settings.DATABASES[params.database]
            if p['ENGINE'] == 'django.db.backends.mysql':
                cmd = self.mysqldump_data(**p) + " " + " ".join(params.tables)
                print cmd
                params.dryrun or os.system(cmd)
                return

    class ModelDoc(SqlCommand):
        name = "model_doc"
        description = "Create Model Documentation for Sphinx"
        args = [
            (('apps',), dict(nargs='+', help="Applications")),
            (('--subdocs', '-s', ),
             dict(action='store_true', help="Include each models document")),
        ]

        def header(self, text, level=0):
            c = ['=', '=', '-', '^', '~', '#', ]
            if level == 0:
                print len(text) * 2 * c[level]
            # print "@@@@", type(text)
            print type(text) == str and text or text.encode('utf8')
            print len(text) * 2 * c[level]
            print

            if level == 0:
                print ".. contents::"
                print "    :local:"
                print

        def ref(self, name):
            print ".. _{0}:\n".format(name)

        def autoclass(self, name):
            print ".. autoclass:: {0}".format(name)
            print "    :members:".encode('utf8')
            print

        def models_for_app(self, app):

            def is_modelclass(c):
                if inspect.isclass(c) and issubclass(c, Model):
                    return app.__name__ == c.__module__
                return False

            res = [m[1] for m in inspect.getmembers(app, is_modelclass,)]
            return res

        def field_choices(self, field):
            choices = getattr(field, 'choices', ())
            if not choices:
                return

            indent = "          "
            print
            print indent, ".. list-table::\n"
            for val, title in choices:
                print indent, "    *    -", val
                print indent, "         -", title.encode('utf8')
                print indent, ""

        def field_table(self, model):
            con = connections['default']      # TODO
            print ""
            print ".. list-table::\n"
            for field in model._meta.fields:
                print "    *    -", field.name
                print "         -", field.verbose_name.encode('utf8')
                print "         -", field.db_type(con)
                print "         -", field.help_text.encode('utf8')
                self.field_choices(field)
                print ""

        def run_for_app(self, app, subdocs=False):
            title = (app.__doc__ or "Model").split('\n')[0]
            self.header(title, 0)

            # for m in get_models(app):
            for m in self.models_for_app(app):
                fullname = self.model_fullname(m)
                self.ref(fullname)
                desc = m._meta.verbose_name     #
                title = u"{0}:{1}".format(
                    m.__name__, desc,
                )
                self.header(title, 1)
                self.autoclass(fullname)

                self.field_table(m)
                if subdocs:
                    print ".. include:: {0}.rst".format(fullname)
                    print

        def run(self, params, **options):
            params.apps = [a + ".models" for a in params.apps]
            apps = get_apps()
            for app in apps:
                if params.apps and app.__name__ not in params.apps:
                    continue
                self.run_for_app(app, params.subdocs)

    class ListField(SqlCommand):
        name = "list_field"
        description = "Search Model Field"
        args = [
            (('apps',), dict(nargs='*', help="Applications")),
            (('--pattern', '-p'), dict(default='', help="Fieldname Pattern")),
        ]

        def run_for_app(self, app, pattern=None):
            for m in get_models(app):
                for f in m._meta.fields:
                    if pattern and not pattern.search(f.name):
                        continue
                    models = self.fields.get(f.name, list())
                    val = (self.model_fullname(m),) + f.deconstruct()[3:]
                    models.append(val)
                    self.fields[f.name] = models

        def run(self, params, **options):
            pattern = params.pattern and re.compile(params.pattern)
            self.fields = {}
            params.apps = [a + ".models" for a in params.apps]
            apps = get_apps()
            for app in apps:
                if params.apps and app.__name__ not in params.apps:
                    continue
                self.run_for_app(app, pattern)

            print self.to_json(self.fields).encode('utf8')
