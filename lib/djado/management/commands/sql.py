# -*- coding: utf-8 -*-
from __future__ import print_function

from django.db.models import Model
from django.apps import apps
from django.db import connections, DEFAULT_DB_ALIAS
from django.core.serializers.json import DjangoJSONEncoder
from django.utils.encoding import force_text
import json
import inspect
from djado.utils import echo_by


class SqlCommand(object):

    class JsonEncoder(DjangoJSONEncoder):
        def default(self, obj):
            if isinstance(obj, set):
                obj = list(obj)
            elif callable(obj):
                return str(obj)
            elif type(obj).__name__ == '__proxy__':
                return force_text(obj)

            return super(SqlCommand.JsonEncoder, self).default(obj)

    def connection(self, name=DEFAULT_DB_ALIAS):
        return connections[name]

    def dump_command(self, name=DEFAULT_DB_ALIAS):
        conn = self.connection(name or DEFAULT_DB_ALIAS)
        cmd = conn.client.executable_name
        d = {
            'psql': 'pg_dump -h {HOST} -U {USER} {NAME}',
            'mysql': "mysqldump -h {HOST} -u {USER} --password={PASSWORD} {NAME}",      # NOQA
        }
        return d[cmd].format(**conn.settings_dict)

    def to_json(self, obj):
        return json.dumps(
            self.fields, indent=2, ensure_ascii=False,
            cls=self.JsonEncoder)

    def models(self):
        return apps.get_models()

    def model_fullname(self, model):
        return "{0}.{1}".format(
            model.__module__, model.__name__)

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

        print(heading)
        print(json.dumps(dict_data, ensure_ascii=False, indent=4))

    def models_for_app(self, app):

        def is_modelclass(c):
            if inspect.isclass(c) and issubclass(c, Model):
                return app.__name__ == c.__module__
            return False

        res = [m[1] for m in inspect.getmembers(app, is_modelclass,)]
        return res

    def generate_doc(self, app_label, subdocs=False):
        from django.apps import apps
        con = connections['default']      # TODO
        app = apps.get_app_config(app_label)
        echo_by(
            'djado/db/models.rst',
            app=app, connection=con, subdoc=subdocs)

    def exec_sql(self, user, password, sql, fetchall=False):
        import MySQLdb
        con = MySQLdb.connect(
            user=user, passwd=password)
        cursor = con.cursor()
        cursor.execute(sql)
        return cursor.fetchall() if fetchall else cursor
