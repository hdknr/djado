#!/usr/bin/env python
from __future__ import print_function
# django version 1.5
import click


PAVES = '''# -*- coding: utf-8 -*-
from paver.easy import (
    task, cmdopts, sh, consume_args
)
from djado.paves import runserver, do
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
'''


def _P(text, fg="green", **kwargs):
    click.secho(text, fg=fg)


@click.group(invoke_without_command=True)
@click.pass_context
def main(ctx):
    pass


@main.command()
@click.pass_context
def init(ctx):
    _P("providing pavement.py")
    with open('pavement.py', 'w') as pave:
        pave.write(PAVES)


if __name__ == '__main__':
    main()
