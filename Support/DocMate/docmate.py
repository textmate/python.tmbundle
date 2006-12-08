import re
from os import environ as env
from os import path
from os import mkdir
import cPickle

prefdir = path.join(env["HOME"], "Library/Preferences/com.macromates.textmate.python")
if not path.exists(prefdir):
    mkdir(prefdir)
hitcount_path = path.join(prefdir, 'hitcount')

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

def doc(word):
    try:
        f = open(path.join(env["TM_BUNDLE_SUPPORT"], 'DocMate/lib.index'))
        words = cPickle.load(f)
    finally:
        f.close()
    if path.exists(path.join(hitcount_path)):
        try:
            f = open(hitcount_path, 'r')
            hit_count = cPickle.load(f)
        finally:
            f.close()
    else:
        hit_count = {}
    paths = []
    matching_keys = [key for key in words if re.compile(r"\b(%s)\b" % word).search(key)]
    for key in matching_keys:
        for desc, url in words[key]:
            count = hit_count.get(url, 0)
            paths.append((count, desc, url))
    paths.sort()
    paths.reverse()
    paths = [(d,u) for c, d, u in paths]
    return paths
