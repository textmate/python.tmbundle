#!/usr/bin/env python

import os
import sys
import pydoc
import time
from urllib2 import urlopen, URLError

PORT=9877
URL='http://localhost:%d/' % PORT
UID='pydoc_server_%d' % PORT

def browse_and_exit():
    print "browsing pydocs at %s ..." % URL
    sys.exit(os.system('open %s' % URL))

def is_serving():
    try:
        urlopen(URL)
        # server is up
        return True
    except URLError:
        return False

def start_serv():
    
    # Redirect standard file descriptors.
    out_log = file('/tmp/%s.log' % UID, 'a+')
    err_log = file('/tmp/%s_error.log' % UID, 'a+', 0)
    dev_null = file('/dev/null', 'r')
    sys.stdout.flush()
    sys.stderr.flush()
    
    os.dup2(out_log.fileno(), sys.stdout.fileno())
    os.dup2(err_log.fileno(), sys.stderr.fileno())
    os.dup2(dev_null.fileno(), sys.stdin.fileno())
    
    # hmm, I guess the completer callback won't help me while forking
    pydoc.serve(PORT)

def wait_for_server():
    timeout, interval, elapsed = 10,1,0
    while not is_serving():
        time.sleep(interval)
        elapsed = elapsed + interval
        if elapsed >= timeout:
            raise RuntimeError('timed out waiting for server!')
    browse_and_exit()

def main():
    if is_serving():
        browse_and_exit()
    
    # the magical two forks, lifted from:
    # http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/66012
    try:
        pid = os.fork()
        if pid > 0:
            print "waiting for server to start on port %d ..." % PORT
            wait_for_server()
            sys.exit(0)
    except OSError, e: 
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)
    
    os.chdir('/')
    os.setsid()
    os.umask(0)
    
    try:
        pid = os.fork()
        if pid > 0:
            # this is the server's pid
            # write a pid file ?
            sys.exit(0)
    except OSError, e: 
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror) 
        sys.exit(1)
    
    start_serv()

if __name__ == '__main__':
    main()