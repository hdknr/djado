#!/usr/bin/env python
from __future__ import print_function
# django version 1.5
import sys
import re
import os
import argparse
from pycommand import command


PAVES = '''# -*- coding: utf-8 -*-
from paver.easy import (
    task, cmdopts, sh, consume_args
)
from djado.paves import runserver, do
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
'''


class DoCommand(command.Command):
    class InitCommand(command.SubCommand):
        name = "init"
        description = "create pavement.py"
        args = []

        def run(self, params, **options):
            print("providing pavement.py")
            with open('pavement.py', 'w') as pave:
                pave.write(PAVES)

if __name__ == '__main__':
    DoCommand().run()
