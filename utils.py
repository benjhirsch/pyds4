import os
import re

#functions i need to reuse across different scripts that aren't directly related to PDS4

def flist(path, ext='', excl=[]):
    '''returns all files in path that end with ext and are not in list excl'''
    fl = []
    for root, _, file in os.walk(path):
        fl.extend([os.path.normpath(os.path.join(root, fn)) for fn in file if fn.endswith(ext) and all([re.search(e, fn) is None for e in excl])])
    return fl

def make80(input_string, line_limit=80):
    '''returns a list of lines no longer than 80 characters'''
    para_split = input_string.split('\n')
    lines = ['']
    for para in para_split:
        for word in para.split():
            next_word = '%s %s' % (lines[-1], word)
            if len(next_word) <= line_limit:
                lines[-1] = next_word.strip()
            else:
                lines.append(word.strip())
        lines.append('')
    return lines
