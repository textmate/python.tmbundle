# encoding: utf-8

# PyMate, a Python output beautifier for TextMate.
# Copyright (c) Domenico Carbotta, 2005.
# With enhancements and precious input by Brad Miller, Jeroen van der Ham.
# Wrap function by Mike Brown from the ASPN Python Cookbook.
# This script is released under the GNU General Public License.

# Note to contributors: please stick to lines of 80 characters or less :) DC


__version__ = 106


import sys
import os
import threading
import MacOS
import textwrap
import codecs
import commands
import unittest

import pymate_output as pmout
import tmproj


html_substitutions = [('&', '&amp;'), ('<', '&lt;'), ('>', '&gt;'),
    ('\t', ' '*4), ('\n', '<br>')]


def get_file_encoding(filename):
    filename = filename.replace('"', '\"')
    try:
        support_dir = os.environ['TM_BUNDLE_SUPPORT']
    except KeyError:
        support_dir = '.'
    encoding = os.popen('perl "%s/getpyencoding.pl" "%s"' %
            (support_dir, filename)).read().strip()
    try:
        if encoding == '':
            encoding = os.environ['TM_PYMATE_DEFAULT_ENCODING']
        codecs.lookup(encoding)
    except (KeyError, LookupError):
        encoding = 'utf-8'
    return encoding


def raw_input_replacement(prompt=''):
    '''
        A replacement for raw_input() which displays a graphical input dialog.
    '''
    sys.__stdout__.flush()

    cmd = ('CocoaDialog inputbox --title Input --informative-text "' +
            prompt.replace('"', '\\"') +
            '" --button1 OK --button2 Cancel --button3 EOF')
    res = os.popen(cmd)
    status = res.readline()
    if int(status) == 2:
       raise IOError('User dismissed the input dialog box.')
    elif int(status) == 3:
        raise EOFError('User pressed the EOF button.')
    rv = res.read()[:-1]
    res.close()
    return rv


def input_replacement(prompt=''):
    '''
        A replacement for input() which displays a graphical input dialog.
    '''
    # XXX doesn't work -- cannot find a way to gain access to the current
    # environment of the script
    if prompt != '':
        prompt += '\n'
    prompt += 'For total compatibility use eval(raw_input()) '
    prompt += 'instead of input().'
    rv = raw_input_replacement(textwrap.fill(prompt, 60))
    return eval(rv, globals(), locals())


def disabled_input_replacement(prompt=''):
    '''
        Signals that the current version of PyMate cannot replace input().
    '''
    raise EOFError, ('When running under PyMate input() is disabled. ' +
            'Use eval(raw_input()) instead.')


class SafeStream:
    
    close_what = None
    output = u''
    TheLock = threading.Lock()
    last = None
    
    def __init__(self, before, after, encoding):
        self.before = str(before)
        self.after = str(after)
        self.encoding = encoding
        
        try:
            limit = int(os.environ['TM_PYMATE_LINE_WIDTH'])
            if limit < 50 and limit != 0:
                self.limit = 50
            else:
                self.limit = limit
        except (KeyError, ValueError):
            self.limit = 80
    
    def wrap(self, text):
            '''
            A word-wrap function that preserves existing line breaks
            and most spaces in the text. Expects that existing line
            breaks are posix newlines (\n).
            '''
            return reduce(lambda line, word, width=self.limit: '%s%s%s' %
                          (line,
                           ' \n'[(len(line)-line.rfind('\n')-1
                                 + len(word.split('\n',1)[0]
                                      ) >= width)],
                           word),
                          text.split(' ')
                         )
    
    def write(self, string):
        try:
            SafeStream.TheLock.acquire()
        
            if SafeStream.last not in (self, None):
                 sys.__stdout__.write('<hr>')
            
            SafeStream.last = self
            
            string = self.wrap(string)
            
            for sub_from, sub_to in html_substitutions:
                string = string.replace(sub_from, sub_to)
            
            string = string.decode(self.encoding)
            
            sys.__stdout__.write(self.before + string + self.after)
        
        finally:
            SafeStream.TheLock.release()


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
    
    if sys.version_info[3] == 'final':
        py_version = 'Python %d.%d.%d' % sys.version_info[:3]
    else:
        py_version = 'Python %d.%d.%d %s %d' % sys.version_info
    py_version += ' &#8212; PyMate r%d' % __version__
    
    script_name_short = os.path.basename(script_name)
    print pmout.preface % (py_version, script_name_short)
    
    # the environment in which the script will run
    script_env = {}
        
    # the script should run in the __main__ namespace
    script_env['__name__'] = '__main__'
    # We set the filename to the filename of the script:
    script_env['__file__'] = script_name_short
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
    sys.path[0] = os.path.dirname(script_name)
        
    # we clean traces of our presence from sys.argv[]
    sys.argv.pop(0)
    
    # let's cd the scripts' directory
    os.chdir(os.path.dirname(script_name))
        
    # let's get the the default output encoding used by the script.
    encoding = get_file_encoding(script_name)
    
    # we sanitize stdout and stderr, replacing them with two instances of
    # our 'html-safe' streams
    sys.stdout = SafeStream('', '', encoding)
    sys.stderr = SafeStream('<span class="stderr">', '</span>', encoding)
    
    try:
        
        # run python run!
        exec script in script_env
        
    except:
        # we don't want html sanitization on our own output!
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        print
        
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
        if hasattr(e_obj, 'args'):
            e_args = ': ' + ', '.join(map(str, e_obj.args))
        else:
            e_args = '.'

        # if the exception was SystemExit, it's a normal condition        
        if e_class is SystemExit:
            print '<strong>Script terminated raising SystemExit%s</strong>' \
                    % e_args
            print pmout.normal_end
            return

        # when we get a syntax error in a regular script,
        # the traceback is not interesting but we want to format
        # differently the exception parameters            
        if e_class is SyntaxError and tb_len == 0:
            e_args = (' in <a href="txmt://open?url=file://%s&line=%d">' +
                    '%s</a> at line %d')
            
            if e_obj.filename in (None, '<string>'):
                filename = '/tmp/Unknown location'
                short_filename = '<em>unknown location</em>'
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
        
        # try to build a TMProj object representing the current project
        # defaulting to None
        try:
            current_project = tmproj.TMProj()
        except tmproj.Error:
            current_project = None
            script_dir = os.path.dirname(script_name)
        
        while tb is not None:

            # extract the file name from the current traceback
            filename = tb.tb_frame.f_code.co_filename
            short_filename = os.path.basename(filename)
                            
            # extract the function name from the current traceback
            func_name = tb.tb_frame.f_code.co_name
            if func_name == '?':
                func_name = '<em>module body</em>'            
            
            lineno = tb.tb_lineno
            
            if not os.path.exists(filename):
                print pmout.tbitem_binary % locals()
            
            else:         
                # as suggested by Jeroen: mark files which don't belong to the
                # current project.
            
                if current_project is None:
                    # the script is being run from a "standalone" window (i.e.
                    # there's no open project).
                    # if the script doesn't reside in the same directory,
                    # a  or a parent directory of the script being run
                    # it's "far"
                    file_dir = os.path.dirname(filename)
                    is_near = (script_dir == file_dir or
                            script_dir.startswith(file_dir) or
                            file_dir.startswith(script_dir))
                else:
                    # there's an open project. see tmproj module for info.
                    is_near = filename in current_project
            
                if is_near:
                    template = pmout.tbitem_near
                else:
                    template = pmout.tbitem_far
            
                print template % locals()
            
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


class pymateTests(unittest.TestCase):
        
    def testUseCmdShiftR(self):
        print >> sys.__stdout__, ('In order to run Unit Tests, ' +
                'use &#x2325;&#x2318;&#x21E7;R instead.')


if __name__ == '__main__':
    
    if len(sys.argv) < 2:
        print 'PyMate is designed for use under TextMate.'
    else:
        main(sys.argv[1])
