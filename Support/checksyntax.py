#!/usr/bin/python 

import os
import sys
import string
import tokenize

def checkSyntax(filename):
    f = open(filename, 'r')
    source = f.read()
    f.close()
    if '\r' in source:
        source = re.sub(r"\r\n", "\n", source)
    if source and source[-1] != '\n':
        source = source + '\n'

    try:
        # If successful, return the compiled code
        return compile(source, filename, "exec")
    except (SyntaxError, OverflowError), err:
        try:
            msg, (errorfilename, lineno, offset, line) = err
            if not errorfilename:
                err.args = msg, (filename, lineno, offset, line)
                err.filename = filename
            print os.path.basename(errorfilename), "line:", lineno, "col:", offset, msg
        except:
            msg = "*** " + str(err)
        return False


def main():
    checkSyntax(sys.argv[1])


main()