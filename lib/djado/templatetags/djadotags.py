# -*- coding: utf-8 -*-
from django import template
register = template.Library()


@register.filter
def tup(src, arg):
    if isinstance(src, tuple):
        return src + (arg, )
    return (src, arg, )


@register.filter
def db_type(field, connection):
    return field.db_type(connection)


HEADER = ['=', '=', '-', '^', '~', '#', ]


@register.simple_tag
def header_label(text, level=0):
    text = u"{}".format(text)
    level = level and int(level) or 0
    line = len(text) * 2 * HEADER[level]
    return "\n".join([
        line if level == 0 else '',
        text,
        line])


@register.filter
def app_model_opts(app):
    return [m._meta for m in app.get_models()]
