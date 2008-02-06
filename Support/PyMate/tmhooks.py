# coding: utf-8
"""
tmhooks.py for PyMate.

This file monkey-patches sys.excepthook to intercept any unhandled
exceptions, format the exception in fancy html, and write them to
a file handle (for instance, sys.stderr).

We also monkey-patch the input and raw_input functions to provide
a tm_dialog.

"""

import re
import sys
import inspect
import codecs
import locale

from os import environ, path, fdopen, popen
from traceback import extract_tb
from cgi import escape
from urllib import quote

import plistlib
from_python = plistlib.writePlistToString
to_python = plistlib.readPlistFromString

# add utf-8 support to stdout/stderr
sys.stdout = codecs.getwriter('utf-8')(sys.stdout);
sys.stderr = codecs.getwriter('utf-8')(sys.stderr);

def e_sh(s):
    return re.sub(r"(?=[^a-zA-Z0-9_.\/\-\x7F-\xFF\n])", r'\\', s).replace("\n", "'\n'")

def tm_raw_input(prompt=""):
    dialog = path.join(environ["TM_SUPPORT_PATH"], 'bin/tm_dialog')
    nib = path.join(environ["TM_BUNDLE_SUPPORT"], "PyMate/TextInput.nib")
    cmd = 'bash -c "%s -mp %s %s"' % \
        (e_sh(dialog),
         e_sh(from_python({"prompt": prompt})),
         e_sh(nib))
    io = popen(cmd)
    plist = io.read()
    io.close()
    plist = to_python(plist)
    if plist['returnCode'] == 1:
        raise KeyboardInterrupt
    if "inputText" in plist:
        return plist["inputText"]
    else:
        return ""
    
def tm_input(prompt=""):
    try:
        frame = inspect.getouterframes(inspect.currentframe())[1][0]
        result = eval(tm_raw_input(prompt), frame.f_globals, frame.f_locals)
    finally:
        del frame
    return result
    
__builtins__['raw_input'] = tm_raw_input
__builtins__['input'] = tm_input

def tm_excepthook(e_type, e, tb):
    """
    Catch unhandled exceptions, and write the traceback in pretty HTML
    to the file descriptor given by $TM_ERROR_FD.
    """
    # get the file descriptor.
    error_fd = int(str(environ['TM_ERROR_FD']))
    io = fdopen(error_fd, 'wb', 0)
    io.write("<div id='exception_report' class='framed'>\n")
    if isinstance(e_type, str):
        io.write("<p id='exception'><strong>String Exception:</strong> %s</p>\n" % escape(e_type))
    else:
        message = ""
        if e.args and e_type is not SyntaxError:
            message = ", ".join([unicode(arg) for arg in e.args])
        else:
            message = unicode(e.args[0])
        io.write("<p id='exception'><strong>%s:</strong> %s</p>\n" %
                                (e_type.__name__, escape(message).encode("utf-8")))
    if e_type is SyntaxError:
        # if this is a SyntaxError, then tb == None
        filename, line_number, offset, text = e.filename, e.lineno, e.offset, e.text
        url, display_name = '', 'untitled'
        io.write("<pre>%s\n%s</pre>\n" % (escape(e.text).rstrip(), "&nbsp;" * (offset-1) + "↑"))
        io.write("<blockquote><table border='0' cellspacing='0' cellpadding='0'>\n")
        if filename and path.exists(filename):
            url = "&url=file://%s" % quote(filename)
            display_name = path.basename(filename)
        if filename == '<string>': # exception in exec'd string.
            display_name = 'exec'
        io.write("<tr><td><a class='near' href='txmt://open?line=%i&column=%i%s'>" %
                                                    (line_number, offset, url))
        io.write("line %i, column %i" % (line_number, offset))
        io.write("</a></td>\n<td>&nbsp;in <strong>%s</strong></td></tr>\n" %
                                            (escape(display_name)))
        io.write("</table></blockquote></div>")
    if tb: # now we write out the stack trace if we have a traceback
        io.write("<blockquote><table border='0' cellspacing='0' cellpadding='0'>\n")
        for trace in extract_tb(tb)[1:]: # skip the first one, to avoid showing pymate's execfile call.
            filename, line_number, function_name, text = trace
            url, display_name = '', 'untitled'
            if filename and path.exists(filename):
                url = "&url=file://%s" % quote(path.abspath(filename))
                display_name = path.basename(filename)
            io.write("<tr><td><a class='near' href='txmt://open?line=%i%s'>" %
                                                            (line_number, url))
            if filename == '<string>': # exception in exec'd string.
                display_name = 'exec'
            if function_name and function_name != "?":
                if function_name == '<module>':
                    io.write("<em>module body</em>")
                else:
                    io.write("function %s" % escape(function_name))
            else:
                io.write('<em>at file root</em>')
            io.write("</a> in <strong>%s</strong> at line %i</td></tr>\n" %
                                                (escape(display_name).encode("utf-8"), line_number))
            io.write("<tr><td><pre class=\"snippet\">%s</pre></tr></td>" % text)
        io.write("</table></blockquote></div>")
    io.flush()

sys.excepthook = tm_excepthook
