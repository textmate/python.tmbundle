#!/usr/bin/python
#
# PyCheckMate, a PyChecker output beautifier for TextMate.
# Copyright (c) Jay Soffian, 2005.
# Inspired by Domenico Carbotta's PyMate.
#
# License: Artistic.

__version__ = "$Revision$"

import sys
import os
import re
import select
import traceback
from cgi import escape
from urllib import quote

_pychecker_url = "http://pychecker.sourceforge.net/"

# pattern to match pychecker output
_pattern = re.compile(r"^(.*?\.pyc?):(\d+):\s+(.*)$")

# careful editing these, they are format strings
_txmt_url_line = r"txmt://open?url=file://%s&line=%s"
_txmt_url_linecol = r"txmt://open?url=file://%s&line=%s&col=%s"
_html_header = r"""<html>
<head>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
<title>PyCheckMate %s</title>
<style type="text/css">
<!--

body {
  background-color: #D8E2F1;
  margin: 0;
}

div#body {
  border-style: dotted;
  border-width: 1px 0;
  border-color: #666;
  margin: 10px 0;
  padding: 10px;
  background-color: #C9D9F0;
}

div#output{
  padding: 0;
  margin: 0;
  font-family: Monaco;
  font-size: 8pt;
}

strong.title { font-size: 11pt; }
span.stderr { color: red; }
p {margin: 0; padding: 2px 0; }

-->
</style>
</head>
<body>
<div id="body">
<p><strong class="title">%s</strong></p><br>
<div id="output">
"""

_html_footer = """</div>
</div>
</body>
</html>
"""

class Error(Exception): pass

class MyPopen:
    """Modifed version of standard popen2.Popen class that does what I need.
    
    Runs command with stdin redirected from /dev/null and monitors its stdout
    and stderr. Each time poll() is called a tuple of (stdout, stderr) is
    returned where stdout and stderr are lists of zero or more lines of output
    from the command. status() should be called before calling poll() and if
    it returns other than -1 then the child has terminated and poll() will
    return no additional output. At that point drain() should be called to
    return the last bit of output.
    
    As a simplication, readlines() can be called until (stdout, stderr) both
    return zero lines.
    """
    
    try:
        MAXFD = os.sysconf('SC_OPEN_MAX')
    except (AttributeError, ValueError):
        MAXFD = 256
    
    def __init__(self, cmd):
        stdout_r, stdout_w = os.pipe()
        stderr_r, stderr_w = os.pipe()
        self._status = -1
        self._pid = os.fork()
        if self._pid == 0:
            # child
            devnull = open("/dev/null")
            os.dup2(devnull.fileno(), 0)
            os.dup2(stdout_w, 1)
            os.dup2(stderr_w, 2)
            devnull.close()
            self._run_child(cmd)
        else:
            # parent
            os.close(stdout_w)
            os.close(stderr_w)
            self._stdout = stdout_r
            self._stderr = stderr_r
            self._poll = select.poll()
            self._poll.register(self._stdout)
            self._poll.register(self._stderr)
            self._stdout_buf = ""
            self._stderr_buf = ""

    def _run_child(self, cmd):
        if isinstance(cmd, basestring):
            cmd = ['/bin/sh', '-c', cmd]
        for i in range(3, self.MAXFD):
            try:
                os.close(i)
            except OSError:
                pass
        try:
            os.execvp(cmd[0], cmd)
        finally:
            os._exit(1)
    
    def status(self):
        """Returns exit status of child or -1 if still running."""
        if self._status < 0:
            try:
                pid, this_status = os.waitpid(self._pid, os.WNOHANG)
                if pid == self._pid:
                    self._status = this_status
            except os.error:
                pass
        return self._status
    
    def poll(self, timeout=None):
        """Returns (stdout, stderr) from child."""
        stdout_buf = ""
        stderr_buf = ""
        for fd, event in self._poll.poll(timeout):
            if not (event & select.POLLIN):
                continue
            if fd == self._stdout:
                stdout_buf = self._stdout_buf + os.read(self._stdout, 4096)
            elif fd == self._stderr:
                stderr_buf = self._stderr_buf + os.read(self._stderr, 4096)
            else:
                raise Error("Implementation Error")
        self._stdout_buf = ""
        self._stderr_buf = ""
        stdout_lines = stdout_buf.splitlines()
        stderr_lines = stderr_buf.splitlines()
        if stdout_lines and not stdout_buf.endswith("\n"):
            self._stdout_buf = stdout_lines.pop()
        if stderr_lines and not stderr_buf.endswith("\n"):
            self._stderr_buf = stderr_lines.pop()
        return (stdout_lines, stderr_lines)
    
    def drain(self):
        stdout, stderr = [], []
        while 1:
            data = os.read(self._stdout, 4096)
            if not data: break
            stdout.append(data)
        while 1:
            data = os.read(self._stderr, 4096)
            if not data: break
            stderr.append(data)
        stdout = ''.join(stdout).splitlines()
        stderr = ''.join(stderr).splitlines()
        return (stdout, stderr)
    
    def readlines(self):
        if self.status() == -1:
            return self.poll()
        else:
            return self.drain()
    
    def close(self):
        os.close(self._stdout)
        os.close(self._stderr)

def check_syntax(script_path):
    f = open(script_path, 'r')
    source = ''.join(f.readlines()+["\n"])
    f.close()
    try:
        print "Syntax Errors...<br><br>"
        compile(source, script_path, "exec")
        print "None<br>"
    except SyntaxError, e:
        href = _txmt_url_linecol % (quote(script_path), e.lineno, e.offset)
        print '<a href="%s">%s:%s</a> %s' % (
            href, 
            escape(os.path.basename(script_path)), e.lineno, 
            e.msg)
    except:
        for line in apply(traceback.format_exception, sys.exc_info()):
            stripped = line.lstrip()
            pad = "&nbsp;" * (len(line) - len(stripped))
            line = escape(stripped.rstrip())
            print '<span class="stderr">%s%s</span><br>' % (pad, line)

def pychecker_version(pychecker_bin):
    try:
        import pychecker.Config
        return pychecker.Config._VERSION
    except (ImportError, AttributeError):
        pass
    # that didn't work, let's try it the hard way
    p = os.popen("%s -V 2>/dev/null" % pychecker_bin)
    version = p.readline().strip()
    p.close()
    return version

def run_pychecker(pychecker_bin, script_path):
    basepath = os.getenv("TM_PROJECT_DIRECTORY")
    p = MyPopen([pychecker_bin, script_path])
    while 1:
        stdout, stderr = p.readlines()
        if not stdout and not stderr:
            break
        for line in stdout:
            line = line.rstrip()
            match = _pattern.search(line)
            if match:
                filename, lineno, msg = match.groups()
                href = _txmt_url_line % (quote(os.path.abspath(filename)), 
                                         lineno)
                if basepath is not None and filename.startswith(basepath):
                    filename = filename[len(basepath)+1:]
                # naive linewrapping, but it seems to work well-enough
                if len(filename) + len(msg) > 80:
                    add_br = "<br>&nbsp;&nbsp;"
                else:
                    add_br = " "
                line = '<a href="%s">%s:%s</a>%s%s' % (
                       href, escape(filename), lineno, add_br,
                       escape(msg))
            else:
                line = escape(line)
            print "%s<br>" % line
        for line in stderr:
            # strip whitespace off front and replace with &nbsp; so that
            # we can allow the browser to wrap long lines but we don't lose
            # leading indentation otherwise.
            stripped = line.lstrip()
            pad = "&nbsp;" * (len(line) - len(stripped))
            line = escape(stripped.rstrip())
            print '<span class="stderr">%s%s</span><br>' % (pad, line)
    p.close()

def main(script_path):
    pychecker_bin = os.getenv("TM_PYCHECKER", "pychecker")
    pychecker_ver = pychecker_version(pychecker_bin)
    my_revision = __version__.split()[1]
    if not pychecker_ver:        
        version_string = "PyCheckMate r%s &ndash; PyChecker %s" % (
            my_revision, "not installed")
    else:
        version_string = "PyCheckMate r%s &ndash; PyChecker %s" % (
            my_revision, pychecker_ver)
    
    basepath = os.getenv("TM_PROJECT_DIRECTORY")
    if basepath:
        project_dir = os.path.basename(basepath)
        script_name = os.path.basename(script_path)
        title = "%s &mdash; %s" % (escape(script_name), escape(project_dir))
    else:
        title = escape(script_path)

    print _html_header % (title, version_string)
    if pychecker_ver:        
        run_pychecker(pychecker_bin, script_path)
    else:
        print \
            "<p>Please install " \
            "<a href=\"javascript:TextMate.system('open %s', null)\">" \
            "PyChecker</a> for more extensive code checking.</p><br>" \
            % _pychecker_url
        check_syntax(script_path)
    print _html_footer
    return 0

if __name__ == "__main__":
    if len(sys.argv) == 2:
        sys.exit(main(sys.argv[1]))
    else:
        print "pycheckermate.py <file.py>"
        sys.exit(1)
