# encoding: latin-1

# copyright (c) Domenico Carbotta, 2005
# this script is released under the GNU General Public License
# EasyDialog support added by Brad Miller
#

import sys
import os
import pymate_output as pmout

from EasyDialogs import AskString


def tkInput(s):
    root = Tk()
    Button(root, text="Hello!").pack()
    root.update()
    d = MyDialog(root)
    root.wait_window(d.top)
    return d.val

def doInput(s):
    try:
        r = AskString(s)
    except:
        sys.__stdout__.write('<strong>Need to use pythonw to get input through dialog</strong>')
        return None
    try:
        r1 = eval(r)
    except:
        r1 = r
    return r1

def doRawInput(s):
    try:
        r = AskString(s)
    except:
        sys.__stdout__.write('<strong>Need to use pythonw to get input through dialog</strong>')
        return None
    return r

    
subs = [('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;')]


def sanitize(string, limit=0):
    '''
        Substitutes HTML entities for &, < and > (thus assuring us that no
        output from the script is interpreted as HTML tags or entities) and
        wraps output lines to the specified number of characters (0 means
        don't wrap).
    '''
    
    assert limit == 0 or limit >= 20
    
    for sub_from, sub_to in subs:
        string = string.replace(sub_from, sub_to)
    
    if limit != 0 and len(string) > limit:
        string_pieces = string.split(' ')
        string = ''
        line_width = 0
        for piece in string_pieces:
            l = len(piece)
            if l > limit:
                string += '\n' + piece + '\n'
                line_width = 0
            elif line_width + l <= limit:
                string += ' ' + piece
                line_width = line_width + l
            else:
                string += '\n' + piece
                line_width = 0
    
    return string


class SanitizedStream:
    
    def __init__(self, before='', after='', limit=0):
        self.before = str(before)
        self.after = str(after)
        self.limit = limit
    
    def write(self, string):
        sys.__stdout__.write(self.before)
        sys.__stdout__.write(sanitize(string, self.limit))
        sys.__stdout__.write(self.after)


def main(script_name):
    
    try:
        script = open(script_name)
    except IOError, msg:
        print '<title>PyMate</title>'
        print '<strong>IOError:</strong>', msg
        return
    
    py_version = 'PyMate running on Python %d.%d.%d %s' % sys.version_info[:-1]
    script_name_short = os.path.basename(script_name)
    print pmout.preface % (py_version, script_name_short)
    
    # script should act like it's running in the __main__ namespace;
    # we signal our presence by setting the __pymate variable to True
    script_env = {'__name__': '__main__', '__pymate': True, 'input':doInput, 'raw_input':doRawInput}
    
    # script should be able to load modules from its directory
    # we overwrite our path since we won't load any other modules
    # and we don't want script to look for modules from our directory!
    sys.path[0] = os.path.dirname(script_name)
    
    # we sanitize stdout and stderr, replacing them with two instances of
    # our 'html-safe' streams
    sys.stdout = SanitizedStream(limit=80)
    sys.stderr = SanitizedStream('<em>', '</em>', limit=80)
    
    try:
        
        # run python run!
        exec script in script_env
        
    except:
        # we don't want html sanitization on our own output!
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        # retrieving exception data...
        e_class, e_obj, tb = sys.exc_info()
        
        # undecorated exception name
        e_name = str(e_class).split('.')[-1]
        
        # exception arguments
        if len(e_obj.args) != 0:
            e_args = ': ' + ', '.join(map(str, e_obj.args))
        else:
            e_args = '.'
        # if the exception was SystemExit, it's a normal condition
        if e_class is SystemExit:
            print
            print '<strong>Script terminated raising SystemExit%s</strong>' \
                    % e_args
            print pmout.normal_end
            return
        
        if e_class is SyntaxError:
            print pmout.syntax_preface % (e_name,e_args)
            print pmout.syntax_item % (e_obj.filename, e_obj.lineno,os.path.basename(e_obj.filename),e_obj.lineno,e_obj.text)
            print pmout.syntax_end
            return
        
        print pmout.exception_preface % (e_name, e_args)
        
        # we discard the first traceback element, since it refers to us
        tb = tb.tb_next
        
        while (tb is not None):
            # extract info from the current traceback object
            function_name = tb.tb_frame.f_code.co_name
            if function_name == '?':
                function_name = '<em>module body</em>'
            filename = tb.tb_frame.f_code.co_filename
            short_filename = os.path.basename(filename)
            lineno = tb.tb_lineno
            
            print pmout.traceback_item % (filename, lineno, function_name,
                    lineno, short_filename)
            
            # advance to the next traceback object
            tb = tb.tb_next
        
        print pmout.exception_end
    
    else:
        # we don't want html sanitization on our own output!
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        print
        print '<strong>Script terminated with success.</strong>'
        print pmout.normal_end


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'PyMate should be only used under TextMate.'
        raise SystemExit, 0
    main(sys.argv[1])