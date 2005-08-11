#!/usr/bin/env python 
# encoding: latin-1

# copyright (c) Domenico Carbotta, 2005
# this script is released under the GNU General Public License


__version__ = (0, 0, 1)


import os
import sys
import re


def wrap(text, width):
    '''
        A word-wrap function that preserves existing line breaks
        and most spaces in the text. Expects that existing line
        breaks are posix newlines (\n).
        Written by Mike Brown for the ASPN Python Cookbook
    '''
    text = ' '.join(text.split('\n'))
    return reduce(lambda line, word, width=width: '%s%s%s' %
            (line,
                ' \n'[(len(line)-line.rfind('\n')-1
                     + len(word.split('\n',1)[0]
                          ) >= width)],
            word), text.split(' '))


def wrap_and_indent(text, width):
    text = wrap(text, width-4)
    rv = ''
    for line in text.split('\n'):
        rv += '    ' + line + '\n'
    return rv[:-1]


def tmate_current_word():
    line = os.environ['TM_CURRENT_LINE']
    column = int(os.environ['TM_COLUMN_NUMBER'])
    cursor = '\x07'
    
    line = line[:column] + cursor + line[column:]
    
    split_chars = re.compile(r' \: | \s | \( | \) | \[ | \] | \' | \" ',
            re.VERBOSE)
    current_word = [word.replace(cursor, '') for word in split_chars.split(line)
            if cursor in word][0]
    
    return current_word.strip('.,')

def get_doc(current_word):
    docstrings = []
    
    # try to look for a module
    try:
        env = {}
        exec 'import %s' % current_word.split('.')[0] in env
    except (SyntaxError, ImportError):
        pass
    else:
        completions = [current_word.split('.')[0]]
        for piece in current_word.split('.')[1:]:
            completions.append(completions[-1] + '.' + piece)
        for completion in completions:
            try:
                docstring = eval('%s.__doc__' % completion, env)
                if docstring is not None:
                    docstrings.append((completion, docstring))
            except (AttributeError, NameError):
                pass
        
    # try to look for a method in a builtin type
    slot_name = current_word.split('.')[-1]
    if not slot_name.startswith('__'):
        type_names = [__builtins__, str, list, tuple, set, unicode, int, long,
                float, complex]
        for builtin_type in type_names:
            if hasattr(builtin_type, slot_name):
                if builtin_type is not __builtins__:
                    completion = builtin_type.__name__ + '.' + slot_name
                else:
                    completion = slot_name
                docstring = getattr(builtin_type, slot_name).__doc__
                if docstring is not None:
                    docstrings.append((completion, docstring))
    if docstrings == []:
        docstrings.append((current_word,"No Help"))
    
    return docstrings


for name, doc in get_doc(tmate_current_word()):
    print name
    print wrap_and_indent(doc.split('\n\n')[0], 50)
    print 
