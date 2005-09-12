#!/usr/bin/env python
# encoding: utf-8

# copyright (c) Domenico Carbotta, 2005
# wrap function shamelessly taken from the ASPN Python Cookbook
# this script is released under the GNU General Public License


__version__ = (0, 0, 2)


import os
import sys
import re


html_header = '''
    <style type="text/css">
    body {
    	font-family: "Lucida Grande";
    	font-size: 10pt;
    	background-color: rgb(170, 200, 255);
    	margin: 0;
    	height: 100%%;
    }
    pre {
        font-family: "Lucida Grande";
    }
    dl {
        background-color: rgb(230, 240, 255);
    	border-style: dotted;
    	border-width: 1px 0;
    	border-color: #666;
    	margin: 5px 0;
    	padding: 10px
    }
    dt {
        margin: 0; padding: 0;
    }
    h3 {
        margin: 0; padding: 0;
        font: 16pt "Lucida Grande";
    }
    dd {
        margin: 0 0 0 40px;
        font: 9pt "Monaco";
    }
    </style>'''


def wrap(text, width):
    '''
        A word-wrap function. Expects that existing line breaks are posix
        newlines (\n).
        Written by Mike Brown for the ASPN Python Cookbook.
        Modified by Domenico Carbotta for this script in order to discard all
        original whitespace replacing it with spaces only.
    '''
    ##text = ' '.join(text.split())
    text = text.replace('\t', '    ')
    return reduce(lambda line, word, width=width: '%s%s%s' %
            (line,
                ' \n'[(len(line)-line.rfind('\n')-1
                     + len(word.split('\n',1)[0]
                          ) >= width)],
            word), text.split(' '))


def wrap_and_indent(text, width):
    text = wrap(text, width - 4)
    rv = ''
    for line in text.split('\n'):
        rv += '    ' + line + '\n'
    return rv[:-1]


def textmate_word():
    line = os.environ['TM_CURRENT_LINE']
    column = int(os.environ['TM_COLUMN_NUMBER'])
    cursor = '\x07'

    if line[column-2]  in '([':
        column = column - 1
    
    line = line[:column - 1] + cursor + line[column - 1:]
    
    split_chars = re.compile(r' \: | \s | \( | \) | \[ | \] | \' | \" ',
            re.VERBOSE)
    word = [word.replace(cursor, '') for word in split_chars.split(line)
            if cursor in word][0]
    
    return word.strip('.,')


def get_docstrings(word):
    docstrings = []
    
    # try to look for a module
    try:
        module_name = word.split('.')[0]
        m = __import__(module_name, {}, {}, [])
    except (ValueError, ImportError):
        pass
    else:
        if m.__doc__ != '' and m.__doc__ is not None:
            docstrings.append((module_name, m.__doc__))
        completions = word.split('.')[1:]
        compl_name = ''
        for completion in completions:
            if compl_name == '':
                compl_name += completion
            else:
                compl_name += '.' + completion
            if hasattr(m, compl_name):
                f = getattr(m, compl_name)
                if type(f) in (str, list, tuple, unicode, int, long, float,
                        complex):
                    docstrings.append((module_name + '.' + compl_name, str(f)))
                    break
                elif f.__doc__ != '' and f.__doc__ is not None:
                    if module_name + '.' + compl_name == word:
                        # we have a perfect match. no need to look at anything
                        # else
                        return [(word, f.__doc__)]
                    docstrings.append((module_name + '.' + compl_name,
                        f.__doc__))
            else:
                break
        
    # try to look for a method in a builtin type
    slot_name = word.split('.')[-1]    
    type_names = ['__builtins__', 'str', 'list', 'tuple', 'set', 'frozenset', 'unicode', 'int',
            'long', 'float', 'complex', 'type']
    
    for type_name in type_names:
        # be nice to older Python 2.3.5 (OS X default)
        try:
            builtin_type = globals()[type_name]
        except KeyError:
            builtin_type = None
            
        if hasattr(builtin_type, slot_name):
            if builtin_type is not __builtins__:
                completion = builtin_type.__name__ + '.' + slot_name
            else:
                completion = slot_name
            f = getattr(builtin_type, slot_name)
            if type(f) in (str, list, tuple, unicode, int, long, float,
                    complex):
                docstrings.append((completion, str(f)))
            else:
                docstring = getattr(builtin_type, slot_name).__doc__
                if docstring != '' and docstring is not None:
                    docstrings.append((completion, docstring))
        
    return docstrings


def main(word, extended):
    docstrings = get_docstrings(word)

    limit = 400
    overflow = False

    if len(docstrings) == 0:
        print 'No matches found.'
    else:
        if extended: print html_header
        if extended: print '<body><pre>',
        first = True
        
        for name, doc in docstrings:
            if not extended:
                if not first:
                    print '----'
                else:
                    first = False
            
            if extended: print '<dl><dt><h3>',
            print name,
            if extended: print '</h3></dt>'

            if extended: print '<dd>',           
            print
            if not extended and len(doc) > limit:
                overflow = True
                doc = doc[:limit-3] + '...'
            print wrap(doc, 80), ##.split('\n\n')[0], 50)
            if extended: print '</dd></dl>',

    if overflow:
        print
        print '----'
        print 'Press \xe2\x8c\x98\xe2\x87\xa7H to read more'

    if extended: print '</pre>'


def test(extended):
    tests = 'dir print blabla blabla.split os.dir os.path os.walk email.pizza'.split()
    for test_word in tests:
        print test_word
        print '---'
        main(test_word, extended)
        print


if __name__ == '__main__':
    if '--test' in sys.argv:
        test('--extended' in sys.argv)
    else:
        main(textmate_word(), '--extended' in sys.argv)