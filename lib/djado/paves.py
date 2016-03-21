from paver.easy import (
    task, cmdopts, sh, consume_args
)
import os
import sys


def path(name):
    return os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        name
    )


def manage_py(args, do=False, settings_class="app.settings"):
    #: manage.py
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", settings_class)
    from django.core.management import execute_from_command_line
    if do:
        from django.conf import settings
        settings.INSTALLED_APPS = settings.INSTALLED_APPS + [
            'djado',
            'django_extensions', ]
    execute_from_command_line(args)


@task
@cmdopts([
    ('port=', 'p', 'TCP PORT'),
])
def runserver(options):
    ''' Run Django Web Application '''
    listen = "0.0.0.0:{}".format(
        options.get('port', '8000'))
    args = ['manage.py', 'runserver', listen]
    manage_py(args)


@task
@consume_args
def do(args):
    ''' Run manage.py with additional functions '''
    args.insert(0, 'manage.py')
    manage_py(args, do=True)
