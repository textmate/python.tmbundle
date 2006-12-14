#!/usr/bin/env python2.3
# -*- coding: UTF-8 -*-
import re
import sys
from os import system, path, mkdir, environ as env
import cPickle
import urllib2
import inspect
from urlparse import urljoin as _urljoin
import time

# make sure Support/lib is on the path
support_lib = path.join(env["TM_SUPPORT_PATH"], "lib")
if support_lib not in sys.path:
    sys.path.insert(0, support_lib)

import tm_helpers

if "TM_PYTHONDOCS" in env:
    PYTHONDOCS = env["TM_PYTHONDOCS"]
else:
    PYTHONDOCS = "http://docs.python.org"

TIMEOUT = 5 * 60
_PYDOC_PORT = 7400
_PYDOC_URL = "http://localhost:%i/"

prefdir = path.join(env["HOME"], "Library/Preferences/com.macromates.textmate.python")
if not path.exists(prefdir):
    mkdir(prefdir)
hitcount_path = path.join(prefdir, 'docmate_url_hitcount')

def urljoin(base, *fragments):
    for f in fragments:
        base = _urljoin(base, f, allow_fragments=True)
    return base

def accessible(url):
    """ True if the url is accessible. """
    try:
        urllib2.urlopen(url)
        return True
    except urllib2.URLError:
        return False

def load_hitcounts():
    hit_count = {}
    if path.exists(hitcount_path):
        f = None
        try:
            f = open(hitcount_path, 'r')
            hit_count = cPickle.load(f)
        finally:
            if f: f.close()
    return hit_count

def increment_hitcount(url):
    if path.exists(hitcount_path):
        try:
            f = open(hitcount_path, 'r')
            hit_count = cPickle.load(f)
        finally:
            f.close()
    else:
        hit_count = {}
    try:
        f = open(hitcount_path, 'w')
        if not url in hit_count:
            hit_count[url] = 0
        hit_count[url] += 1
        cPickle.dump(hit_count, f)
    finally:
        f.close()

def pydoc_url():
    """ Return a URL to pydoc for the python returned by tm_helpers.env_python(). """
    python, version = tm_helpers.env_python()
    port = _PYDOC_PORT + version
    url = _PYDOC_URL % port
    return url, port

def launch_pydoc_server():
    server = path.join(env["TM_BUNDLE_SUPPORT"], "DocMate/pydoc_server.py")
    python, version = tm_helpers.env_python()
    url, port = pydoc_url()
    if not accessible(url):
        # launch pydoc.
        system('/usr/bin/nohup %s %s %i %i\
                    1>> /tmp/pydoc.log 2>> /tmp/pydoc.log &' \
                    % (python, tm_helpers.sh_escape(server), port, TIMEOUT))
    return url

def doc(word):
    """ Return a list of (desc, url) pairs for `word`. """
    pairs = []
    if PYTHONDOCS: # and accessible(PYTHONDOCS)
        pairs = library_docs(word)
    #if accessible(PYDOC_URL):
    # sort by hit count.
    if pairs:
        h = load_hitcounts()
        t = []
        for desc, url in pairs:
            t.append((h.get(url, 0), desc, url))
        t.sort()
        t.reverse()
        pairs = [(desc,url) for c, desc, url in t]
    pairs.extend(pydoc(word))
    return pairs

def library_docs(word):
    # build a list of matching library docs
    paths = []
    try:
        f = open(path.join(env["TM_BUNDLE_SUPPORT"], 'DocMate/lib.index'))
        index = cPickle.load(f)
    finally:
        f.close()
    word_re = re.compile(r"\b(%s)\b" % word)
    matching_keys = [key for key in index if word_re.search(key)]
    for key in matching_keys:
        for desc, url in index[key]:
            paths.append((desc, urljoin(PYTHONDOCS, "lib/", url)))
    return paths

def local_docs(word):
    import pydoc
    try:
        obj, name = pydoc.resolve(word)
    except ImportError:
        return None
    desc = pydoc.describe(obj)
    return [(desc, urljoin(pydoc_url()[0], "%s.html" % word))]