# coding: utf-8
"""
tmhooks.py for PyMate.

This file monkey-patches sys.excepthook to intercept any unhandled
exceptions, format the exception in fancy html, and write them to
a file handle (for instance, sys.stderr).

Also, sys.stdout and sys.stder are wrapped in a utf-8 codec writer.

"""

import sys, os

# remove TM_BUNDLE_SUPPORT from the path.
if os.environ['TM_BUNDLE_SUPPORT'] in sys.path:
  sys.path.remove(os.environ['TM_BUNDLE_SUPPORT'])

# now import local sitecustomize
try:
  import sitecustomize
  if sys.version_info[0] >= 3:
    from imp import reload
  reload(sitecustomize)
except ImportError: pass

import codecs

from os import environ, path, fdopen, popen
from traceback import extract_tb
from cgi import escape

try:
    from urllib import quote
    # add utf-8 support to stdout/stderr
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout);
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr);
except:
    from urllib.parse import quote
    


def tm_excepthook(e_type, e, tb):    
    """ 
    sys.excepthook(type, value, traceback)
    This function prints out a given traceback and exception to sys.stderr.

    When an exception is raised and uncaught, the interpreter calls sys.excepthook with three arguments, 
    the exception class, exception instance, and a traceback object. In an interactive session this happens 
    just before control is returned to the prompt; in a Python program this happens just before the program
    exits. The handling of such top-level exceptions can be customized by assigning another three-argument 
    function to sys.excepthook.
    """
    
    # get the file descriptor.
    error_fd = int(str(environ['TM_ERROR_FD']))
    io = fdopen(error_fd, 'wb', 0)
    
    def ioWrite(s):
        # if isinstance(message, unicode):
        io.write(bytes(s, 'UTF-8'))
        
    ioWrite("<div id='exception_report' class='framed'>\n")
    
    if isinstance(e_type, str):
        ioWrite("<p id='exception'><strong>String Exception:</strong> %s</p>\n" % escape(e_type))
    elif e_type is SyntaxError:
        # if this is a SyntaxError, then tb == None
        filename, line_number, offset, text = e.filename, e.lineno, e.offset, e.text
        url, display_name = '', 'untitled'
        if not offset: offset = 0
        ioWrite("<pre>%s\n%s</pre>\n" % (escape(e.text).rstrip(), "&nbsp;" * (offset-1) + "↑"))
        ioWrite("<blockquote><table border='0' cellspacing='0' cellpadding='0'>\n")
        if filename and path.exists(filename):
            url = "&url=file://%s" % quote(filename)
            display_name = path.basename(filename)
        if filename == '<string>': # exception in exec'd string.
            display_name = 'exec'
        ioWrite("<tr><td><a class='near' href='txmt://open?line=%i&column=%i%s'>" %
                                                    (line_number, offset, url))
        ioWrite("line %i, column %i" % (line_number, offset))
        ioWrite("</a></td>\n<td>&nbsp;in <strong>%s</strong></td></tr>\n" %
                                            (escape(display_name)))
        ioWrite("</table></blockquote></div>")
    else:
        message = ""
        if e.args:
            # For some reason the loop below works, but using either of the lines below
            # doesn't
            # message = ", ".join([str(arg) for arg in e.args])
            # message = ", ".join([unicode(arg) for arg in e.args])
            message = repr(e.args[0])
            if len(e.args) > 1:
                for arg in e.args[1:]:
                    message += ", %s" % repr(arg)
            ioWrite("<p id='exception'><strong>%s:</strong> %s</p>\n" %
                                    (e_type.__name__, escape(message)))
                                    
    if tb: # now we write out the stack trace if we have a traceback
        ioWrite("<blockquote><table border='0' cellspacing='0' cellpadding='0'>\n")
        for trace in extract_tb(tb):
            filename, line_number, function_name, text = trace
            url, display_name = '', 'untitled'
            if filename and path.exists(filename):
                url = "&url=file://%s" % quote(path.abspath(filename))
                display_name = path.basename(filename)
            ioWrite("<tr><td><a class='near' href='txmt://open?line=%i%s'>" %
                                                            (line_number, url))
            if filename == '<string>': # exception in exec'd string.
                display_name = 'exec'
            if function_name and function_name != "?":
                if function_name == '<module>':
                    ioWrite("<em>module body</em>")
                else:
                    ioWrite("function %s" % escape(function_name))
            else:
                ioWrite('<em>at file root</em>')
            ioWrite("</a> in <strong>%s</strong> at line %i</td></tr>\n" %
                                                (escape(display_name).encode("utf-8"), line_number))
            ioWrite("<tr><td><pre class=\"snippet\">%s</pre></tr></td>" % text)
        ioWrite("</table></blockquote></div>")
    if e_type is UnicodeDecodeError:
        ioWrite("<p id='warning'><strong>Warning:</strong> It seems that you are trying to print a plain string containing unicode characters.\
            In many contexts, setting the script encoding to UTF-8 and using plain strings with non-ASCII will work,\
            but it is fragile. See also <a href='http://macromates.com/ticket/show?ticket_id=502C2FDD'>this ticket.</a><p />\
            <p id='warning'>You can fix this by changing the string to a unicode string using the 'u' prefix (e.g. u\"foobar\").</p>")
    io.flush()

sys.excepthook = tm_excepthook
