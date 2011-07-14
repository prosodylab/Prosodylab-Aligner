#!/usr/bin/env python
# A script for fixing typos, etc. in .lab files
# Kyle Gorman <kgorman@ling.upenn.edu>

from os import path
from sys import argv
from glob import glob

def error():
    print """
    fixlab.py: a script for fixing typos in .lab files

    USAGE: ./fixlab.py TYPO CORRECTION FOLDER

    TYPO and CORRECTION will be treated as strings. FOLDER is a path where the 
    .lab files can be found. If TYPO or CORRECTION contains whitespace, delimit
    them with a single (right) quote (e.g., the <'> character)
    """
    exit(1)

if __name__ == '__main__':

    if len(argv) != 4:
        error()

    # parse args
    typo = argv[1] 
    correction = argv[2]

    # make corrections
    for file in glob(path.join(argv[3], '*.lab')):
        words = open(file, 'r').readline().split()
        typoed = False
        for i in xrange(len(words)):
            if words[i] == typo:
                words[i] = correction
                typoed = True
        if typoed: # needs a correction
            open(file, 'w').write(' '.join(words))
