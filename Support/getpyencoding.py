#!/usr/bin/env python

import re

while True:
    try:
        m = re.search('#.*?coding[:=]\s*([-\w.]+)', raw_input())
    except EOFError:
        raise SystemExit
    if m is not None:
        print m.groups(1)[0]
        raise SystemExit