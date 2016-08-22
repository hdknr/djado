# -*- coding: utf-8 -*-
from __future__ import print_function

from django import template
from django.utils.safestring import mark_safe
import djclick as click


def echo(text, fg="green", **kwargs):
    click.secho(render(text, **kwargs), fg=fg)


def echo_by(template, fg="green", **kwargs):
    click.secho(render_by(template, **kwargs), fg=fg)


def render(src, **ctx):
    return mark_safe(
        template.Template(src).render(template.Context(ctx)))


def render_by(template_name, **ctx):
    return mark_safe(
        template.loader.get_template(
            template_name).render(template.Context(ctx)))
