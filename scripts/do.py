#!/usr/bin/env python
# django version 1.5
import sys
import re
import os

pat = r'(?P<indent>\s+)(?P<code>execute_from_command_line.+)$'
patch = '''from django.conf import settings
settings.INSTALLED_APPS = settings.INSTALLED_APPS + ('djado',)'''

if len(sys.argv) > 1 and os.path.basename(sys.argv[1]) == 'manage.py':
    print "Createing a do.py...."
    dst = os.path.join(os.path.dirname(os.path.abspath(sys.argv[1])),
                       'do.py')
    with open(dst, "w") as out, open(sys.argv[1]) as src:
        for i in src.readlines():
            m = re.search(pat, i)
            m = m and m.groupdict()
            if m:
                for p in patch.split('\n'):
                    out.write(m['indent'])
                    out.write(p)
                    out.write("\n")
            out.write(i)
