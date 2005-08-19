# encoding: latin-1

# copyright (c) Domenico Carbotta, 2005
# with enhancements and precious input by Brad Miller and Jeroen van der Ham
# wrap function shamelessly taken from the ASPN Python Cookbook
# this script is released under the GNU General Public License


__all__ = ['TMProj', 'Error']


import re
import os


dir_re = re.compile('''
    <key>sourceDirectory</key>
    \s*
    <string>(.*?)</string>
''', re.VERBOSE)

file_re = re.compile('''
    <key>filename</key>
    \s*
    <string>(.*?)</string>
''', re.VERBOSE)


def join(*pieces):
    '''
        Joins and normalizes path elements.
    '''
    return os.path.normpath(os.path.join(*pieces))


class Error (Exception):
    pass


class TMProj:
    '''
        Represents a TextMate project. Use the "in" operator to test for
        inclusion (e.g. '/scripts/file.py' in TMProj())
    '''
    
    def __init__(self, project_filepath=None):
        '''
            Creates a TMProj object from the contents of the specified file.
            If no project_name argument is specified, it defaults to the
            contents of the TM_PROJECT_FILEPATH environment variable if present.
        '''
        if project_filepath is None:
            if 'TM_PROJECT_FILEPATH' in os.environ:
                project_filepath = os.environ['TM_PROJECT_FILEPATH']
            else:
                raise Error('No active project')
        
        project = open(project_filepath).read()
        project_dir = os.path.dirname(project_filepath)
        
        directories = []
        for m in dir_re.finditer(project):
            directories.append(join(project_dir, m.group(1)) + '/')
        
        files = []
        for m in file_re.finditer(project):
            files.append(join(project_dir, m.group(1)))
        
        # we filter out non-existent files and directories
        # and transform everything to lower-case since OS X is case insensitive
        self.directories = map(str.lower, filter(os.path.exists, directories))
        self.files = map(str.lower, filter(os.path.exists, files))
        
    def __contains__(self, other):
        assert isinstance(other, basestring)
        
        # normalize the path and bring it to lowercase
        filename = os.path.normpath(other).lower()
        
        if filename in self.files:
            return True
        
        file_dir = os.path.dirname(filename)
        for d in self.directories:
            if file_dir.startswith(d):
                return True
        
        return False
