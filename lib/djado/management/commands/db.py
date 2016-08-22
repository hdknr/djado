# -*- coding: utf-8 -*-
from __future__ import print_function

from django.apps import apps
from django.db import connection
# from django.utils import functional
from djado.utils import echo, echo_by
import djclick as click
import os
import re
from .sql import SqlCommand


_format = dict(
    line='{{module}}.{{object_name}} {{db_table}}',
    sphinx='''
.. _{{module}}.{{object_name}}:

{{object_name}}
{{sep}}

.. autoclass:: {{module}}.{{object_name}}
    :members:

''',
)


sqlcommand = SqlCommand()


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    pass


@main.command()
@click.pass_context
def reset_autoincrement(ctx):
    '''Reset MySQL autoincrement value. '''
    queries = []
    for model in apps.get_models():
        try:
            max_id = model.objects.latest('id').id + 1
        except:
            max_id = 1

        sql = 'ALTER TABLE %s AUTO_INCREMENT = %d'
        queries.append(sql % (model._meta.db_table, max_id))

        cursor = connection.cursor()
        map(lambda query: cursor.execute(query), queries)


@main.command()
@click.argument('app_labels', nargs=-1)
@click.option('--format', '-f', default='sphinx', help="format=[line|sphinx]")
@click.pass_context
def list_model(ctx, app_labels, format):
    '''List Models'''
    echo('{{ a }} {{ f }}', a=app_labels, f=format)
    from django.apps import apps

    for app_label in app_labels:
        conf = apps.get_app_config(app_label)
        for model in conf.get_models():
            data = {
                "app_label": app_label,
                "module": model.__module__,
                "object_name": model._meta.object_name,
                "sep": '-' * len(model._meta.object_name),
                "db_table": model._meta.db_table,
            }
            echo(_format[format], **data)


@main.command()
@click.option('--user', '-u', default=os.environ.get("DBROOT_USER"))
@click.option('--password', '-p', default=os.environ.get("DBROOT_PASSWD"))
@click.option('--database', '-d', default="default")
@click.pass_context
def createdb(ctx, user, password, database):
    MYSQL_CREATEDB = """
    CREATE DATABASE %(NAME)s
    DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;
    GRANT ALL on %(NAME)s.*
    to '%(USER)s'@'%(SOURCE)s'
    identified by '%(PASSWORD)s' WITH GRANT OPTION;
    """

    from django.conf import settings
    sqlcommand.print_dict(settings.DATABASES, "@@@ Your database settings :")

    if settings.DATABASES[database]['ENGINE'] \
            is 'django.db.backends.sqlite3':

        print("@@@ Not required to create database, just do syncdb.")
        return

    cursor = sqlcommand.exec_sql(user, password, "show databases")

    p = settings.DATABASES[database]
    p['SOURCE'] = p.get('HOST', 'localhost')

    if (p['NAME'],) in cursor.fetchall():
        print("database %(NAME)s exists" % p)
        return
    else:
        query = MYSQL_CREATEDB % p
        print("executing:\n", query)
        cursor.execute(query)
        for r in cursor.fetchall():
            print(r)


@main.command()
@click.option('--user', '-u', default=os.environ.get("DBROOT_USER"))
@click.option('--password', '-p', default=os.environ.get("DBROOT_PASSWD"))
@click.option('--database', '-d', default="default")
@click.pass_context
def dropdb(ctx, user, password, database):
    ''' Drop Database '''

    from django.conf import settings
    p = settings.DATABASES[database]

    sqlcommand.print_dict(p, "@@@ Your database settings :")
    if p['ENGINE'] == 'django.db.backends.sqlite3':
        print("@@@ Not required to create database, just do syncdb.")
        return

    i = raw_input("Are you ready to delete %(NAME)s ?=[y/n]" % p)
    if i != 'y':
        return

    print(sqlcommand.exec_sql(
        user, password, "drop database %(NAME)s" % p,
        fetchall=True,
    ))


@main.command()
@click.option('--user', '-u', default=os.environ.get("DBROOT_USER"))
@click.option('--password', '-p', default=os.environ.get("DBROOT_PASSWD"))
@click.option('--database', '-d', default="default")
@click.option('--dryrun', '-r', is_flag=True, default=False)
@click.pass_context
def dumpdb(ctx, user, password, database, dryrun):
    '''Dump Database'''

    MYSQLDUMP = "mysqldump -c --skip-extended-insert"
    MYSQLPARAM_F = " -u %(USER)s --password=%(PASSWORD)s %(NAME)s"

    from django.conf import settings
    p = settings.DATABASES[database]

    if p['ENGINE'] == 'django.db.backends.mysql':
        cmd = MYSQLDUMP + MYSQLPARAM_F % p
        print(cmd)
        dryrun or os.system(cmd)
        return


@main.command()
@click.option('--user', '-u', default=os.environ.get("DBROOT_USER"))
@click.option('--password', '-p', default=os.environ.get("DBROOT_PASSWD"))
@click.option('--database', '-d', default="default")
@click.option('--dryrun', '-r', is_flag=True, default=False)
@click.pass_context
def dumpschema(ctx, user, password, database, dryrun):
    '''Dump Database Schema '''
    MYSQLDUMP = "mysqldump --no-data"
    MYSQLPARAM_F = " -u %(USER)s --password=%(PASSWORD)s %(NAME)s"

    from django.conf import settings
    p = settings.DATABASES[database]

    if p['ENGINE'] == 'django.db.backends.mysql':
        cmd = MYSQLDUMP + MYSQLPARAM_F % p
        print(cmd)
        dryrun or os.system(cmd)
        return


@main.command()
@click.argument('tables', nargs=-1)
@click.option('--user', '-u', default=os.environ.get("dbroot_user"))
@click.option('--password', '-p', default=os.environ.get("dbroot_passwd"))
@click.option('--database', '-d', default="default")
@click.option('--dryrun', '-r', is_flag=True, default=False)
@click.pass_context
def dumpdata(ctx, tables, user, password, database, dryrun):
    '''Dump Database Data'''

    from django.conf import settings
    p = settings.DATABASES[database]
    if p['ENGINE'] == 'django.db.backends.mysql':
        cmd = sqlcommand.mysqldump_data(**p) + " " + " ".join(tables)
        print(cmd)
        dryrun or os.system(cmd)
        return


@main.command()
@click.option('--user', '-u', default=os.environ.get("dbroot_user"))
@click.option('--password', '-p', default=os.environ.get("dbroot_passwd"))
@click.option('--database', '-d', default="default")
@click.option('--dryrun', '-r', is_flag=True, default=False)
@click.pass_context
def db_grant_all(ctx, user, password, database, dryrun):
    ''' Add DB Admin Privilege '''
    MYSQL_GRANT_ALL = """
    GRANT ALL on *.* to '%(USER)s'@'%(SOURCE)s' WITH GRANT OPTION;
    """

    from django.conf import settings
    sqlcommand.print_dict(settings.DATABASES, "@@@ Your database settings :")

    if settings.DATABASES[database]['ENGINE'] \
            is 'django.db.backends.sqlite3':

        print("@@@ Not required to create database, just do syncdb.")
        return

    p = settings.DATABASES[database]
    p['SOURCE'] = p.get('HOST', 'localhost')

    cursor = sqlcommand.exec_sql(user, password, MYSQL_GRANT_ALL % p)

    for r in cursor.fetchall():
        print(r)


@main.command()
@click.argument('apps', nargs=-1)
@click.option('--subdocs', '-s', is_flag=True, default=False)
@click.pass_context
def model_doc(ctx, apps, subdocs):
    '''Sphinx Model Documentation'''
    for app_label in apps:
        sqlcommand.generate_doc(app_label, subdocs)


@main.command()
@click.argument('apps', nargs=-1)
@click.option('--pattern', '-p')
@click.pass_context
def list_field(ctx, apps, pattern):
    '''Search Model Field'''

    def run_for_app(app, pattern, fields):
        for name, m in apps.get_app_config(app).models:
            for f in m._meta.fields:
                if pattern and not pattern.search(f.name):
                    continue
                models = fields.get(f.name, list())
                val = (sqlcommand.model_fullname(m),) + f.deconstruct()[3:]
                models.append(val)
                fields[f.name] = models

    pattern = pattern and re.compile(pattern)
    fields = {}
    for app in apps:
        run_for_app(app, pattern, fields)

    print(sqlcommand.to_json(fields).encode('utf8'))


@main.command()
@click.option('--database', '-d', default="default")
@click.pass_context
def createdb_script(ctx, database):
    from django.conf import settings
    db = settings.DATABASES[database]
    echo_by('djado/{ENGINE}/createdb_script.sql'.format(**db), db=db)
