import sys
import re
import parser

pat = r"^\s*execute_from_command_line"
manage_py = "".join([i for i in open(sys.argv[1]).readlines()
                     if not re.search(pat, i)])

eval(parser.suite(manage_py).compile())

del sys.argv[0]
from django.conf import settings
settings.INSTALLED_APPS = settings.INSTALLED_APPS + ('djado,')
execute_from_command_line(sys.argv)
