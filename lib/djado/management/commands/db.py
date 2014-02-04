# -*- coding: utf-8 -*-

from . import GenericCommand


class Command(GenericCommand):
    option_list = GenericCommand.option_list + ()

    def command_reset_autoincrement(self, *args, **options):
        from django.db.models import get_models
        from django.db import connection

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
