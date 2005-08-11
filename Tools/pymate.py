# encoding: latin-1

# copyright (c) Domenico Carbotta, 2005
# with enhancements and precious input by Brad Miller and Jeroen van der Ham
# wrap function shamelessly taken from the ASPN Python Cookbook
# this script is released under the GNU General Public License


__version__ = (0, 0, 5)


import sys
import os
import threading
import EasyDialogs
import MacOS
import pymate_output as pmout


subs = [('&', '&amp;'),
        ('<', '&lt;'),
        ('>', '&gt;'),
            # by default, tabs are rendered as 8 spaces
            # I _really_ do like four spaces instead
        ('\t', ' ' * 4)]


def wrap(text, width):
    '''
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        Written by Mike Brown for the ASPN Python Cookbook
    '''
    return reduce(lambda line, word, width=width: '%s%s%s' %
            (line,
                ' \n'[(len(line)-line.rfind('\n')-1
                     + len(word.split('\n',1)[0]
                          ) >= width)],
            word), text.split(' '))


def sanitize(string):
    '''
        Substitutes HTML entities for &, < and > (thus assuring us that no
        output from the script is interpreted as HTML tags or entities).
    '''
    
    for sub_from, sub_to in subs:
        string = string.replace(sub_from, sub_to)
    
    return string


def raw_input_replacement(prompt=''):
    '''
        A replacement for raw_input() which displays a graphical input dialog.
    '''
    try:
        rv = EasyDialogs.AskString(prompt)
    except MacOS.Error:
        # python is not allowed to interact with user.
        # raise EOFError like every noninteractive shell does.
        raise EOFError
    if rv == '\x04':
        # user typed ^D, which by all means is an EOF ;)
        raise EOFError
    else:
        return rv


def input_replacement(prompt=''):
    '''
        A replacement for input() which displays a graphical input dialog.
    '''
    # XXX doesn't work -- cannot find a way to gain access to the current
    # environment of the script
    if prompt != '':
        prompt += '\n\n'
    prompt += 'Please note that in the current version PyMate cannot gain '
    prompt += 'access to the scripts environment; you can only enter '
    prompt += 'expressions involving literals.'
    rv = raw_input_replacement(wrap(prompt, 100))
    return eval(rv, globals(), locals())


def disabled_input_replacement(prompt=''):
    '''
        Signals that the current version of PyMate cannot replace input().
    '''
    raise EOFError, ('When running under PyMate input() is disabled. ' +
            'Use eval(raw_input()) instead.')


class SanitizedStream:
    
    close_what = None
    output = ''
    TheLock = threading.Lock()
    
    def __init__(self, before='', after='', limit=0):
        self.before = str(before)
        self.after = str(after)
        self.limit = limit
    
    def write(self, string):
        SanitizedStream.TheLock.acquire()
        
        if SanitizedStream.close_what is None:
            # it's the first write ever.
            # open our context
            SanitizedStream.output += self.before
            # register our context closing string
            SanitizedStream.close_what = self.after
        
        elif SanitizedStream.close_what != self.after:
            # another context is already open.
            # close previous context by writing what's specified in the
            # other SanitizedStream's after field
            if SanitizedStream.output[-1] != '\n':
                SanitizedStream.output += '\n'
            SanitizedStream.output += SanitizedStream.close_what
            # open our context
            SanitizedStream.output += self.before
            # register our context closing string
            SanitizedStream.close_what = self.after
        
        SanitizedStream.output += sanitize(string)
        
        SanitizedStream.TheLock.release()
    
    # @staticmethod
    def flush(limit=80):
        SanitizedStream.TheLock.acquire()
        
        # close the current context
        if SanitizedStream.close_what is not None:
            SanitizedStream.output += SanitizedStream.close_what
            SanitizedStream.close_what = ''
        
        # split and wrap lines, then print them
        print >> sys.__stdout__, wrap(SanitizedStream.output, limit)
        SanitizedStream.output = ''
        
        SanitizedStream.TheLock.release()
    
    flush = staticmethod(flush)


def main(script_name):
    '''
        Main entry point to the program.
    '''
    
    try:
        script = open(script_name)
    except IOError, msg:
        print '<title>PyMate</title>'
        print '<strong>IOError:</strong>', msg
        return
        
    py_version = 'PyMate %d.%d.%d running on Python %d.%d.%d %s' % (
            __version__ + sys.version_info[:4])
    py_version += '''
<small>Please remember that PyMate is still in an early beta stage...
Send all your bug reports to <a
href="mailto:domenico.carbotta@gmail.com">the author</a> :)</small>
'''
    script_name_short = os.path.basename(script_name)
    print pmout.preface % (py_version, script_name_short)
    
    # the environment in which the script will run
    script_env = {}
        
    # the script should run in the __main__ namespace
    script_env['__name__'] = '__main__'
    # we signal our presence
    script_env['__pymate'] = True
    # override raw_input() and input() in order to display a graphical prompt
    script_env['raw_input'] = raw_input_replacement
    # input() cannot access the script namespace, but it *almost* works
    script_env['input'] = input_replacement
    # in case you don't like it...
    # script_env['input'] = disabled_input_replacement
    
    # script should be able to load modules from its directory
    # we overwrite our path since we won't load any other modules
    # and we don't want script to look for modules from our directory!
    sys.path[0] = os.path.split(script_name)[0]
    
    # we clean traces of our presence from sys.argv[]
    sys.argv.pop(0)
    
    # we sanitize stdout and stderr, replacing them with two instances of
    # our 'html-safe' streams
    sys.stdout = SanitizedStream(limit=80)
    sys.stderr = SanitizedStream('<em>', '</em>', limit=80)
    
    try:
        
        # run python run!
        exec script in script_env
        
    except:
        # flush script's output
        SanitizedStream.flush()
        
        # we don't want html sanitization on our own output!
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        # retrieving exception data...
        e_class, e_obj, tb = sys.exc_info()
        
        # retrieving exception name
        e_name = str(e_class)
        if e_name.startswith('exceptions.'):
            # undecorated exception name
            e_name = e_name.split('.')[-1]
        
        # traceback lenght is useful for checking wheter a SyntaxError
        # occurred in the main file or in an exec statement
        tb_len = 0
        tbx = tb.tb_next
        while (tbx is not None):
            tbx = tbx.tb_next
            tb_len += 1
        del tbx
        
        # exception arguments
        if len(e_obj.args) != 0:
            e_args = ': ' + ', '.join(map(str, e_obj.args))
        else:
            e_args = '.'
        
        if e_class is SystemExit:
            # if the exception was SystemExit, it's a normal condition
            print '<strong>Script terminated raising SystemExit%s</strong>' \
                    % e_args
            print pmout.normal_end
            return
        elif e_class is SyntaxError and tb_len == 0:
            # when we get a syntax error in a regular script,
            # the traceback is not interesting but we want to format
            # differently the exception parameters
            e_args = (' in <a href="txmt://open?url=file://%s&line=%d">' +
                    '%s</a> at line %d')
            
            if e_obj.filename in (None, ''):
                filename = '/tmp/Unknown location'
                short_filename = '<em>an exec statement</em>'
            else:
                filename = e_obj.filename
                short_filename = os.path.basename(e_obj.filename)
                    
            e_args = e_args % (filename, e_obj.lineno,
                    short_filename, e_obj.lineno)
            print pmout.syntax % (e_name, e_args)
            return
        
        print pmout.exception_preface % (e_name, e_args)
        
        # we discard the first traceback element, since it refers to us
        tb = tb.tb_next
        
        while (tb is not None):
            # extract info from the current traceback object
            function_name = tb.tb_frame.f_code.co_name
            if function_name == '?':
                function_name = '<em>module body</em>'
            
            # as required bt Jeroen:
            # mark entries regarding files that are in a subdirectory or a
            # parent directory of the script being run as belonging to class
            # "near" and the others as belonging to class 'far'.
            # we could even open the project file and mess with it.
            
            filename = tb.tb_frame.f_code.co_filename
            short_filename = os.path.basename(filename)
            
            script_dir = os.path.split(os.path.realpath(script_name))[0]
            file_dir = os.path.split(os.path.realpath(filename))[0]
            
            # if the script doesn't reside in the same directory, a subdirectory
            # or a parent directory of the script being run it's "far"
            if (script_dir == file_dir or
                    script_dir in file_dir or
                    file_dir in script_dir):
                link_class = 'near'
            else:
                link_class = 'far'
                function_name += ' \xe2\x8e\x8b' # broken circle with an arrow 
            
            lineno = tb.tb_lineno
            
            print pmout.traceback_item % (link_class, filename, filename,
                    lineno, function_name, short_filename, lineno)
            
            # advance to the next traceback object
            tb = tb.tb_next
        
        print pmout.exception_end
    
    else:
        # flush script's output
        SanitizedStream.flush()
        
        # we don't want html sanitization on our own output!
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        
        print '<strong>Script terminated with success.</strong>'
        print pmout.normal_end


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print 'PyMate should be only used under TextMate.'
    else:
        main(sys.argv[1])
