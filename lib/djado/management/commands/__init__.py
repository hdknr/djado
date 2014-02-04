# -*- coding: utf-8 -*-

from django.core.management.base import BaseCommand

from optparse import make_option
import sys


class GenericCommand(BaseCommand):
    args = ''
    help = ''
    model = None

    option_list = BaseCommand.option_list + (
        make_option('--encoding', '-e',
                    action='store',
                    dest='encoding',
                    default='utf-8',
                    help=u'encoding'),
    )
    ''' Command Option '''

    def open_file(self, options):
        fp = sys.stdin if options['file'] == 'stdin' else open(options['file'])
        return fp

    def command_help(self, *args, **options):
        import re
        for i in dir(self):
            m = re.search('^command_(.*)$', i)
            if m is None:
                continue
            print m.group(1)
        print args
        print options

    def handle(self, *args, **options):
        '''  command main '''

        if len(args) < 1:
            return "a sub command must be specfied"
        self.command = args[0]
        getattr(self,
                'command_%s' % self.command,
                GenericCommand.command_help)(*args[1:], **options)
