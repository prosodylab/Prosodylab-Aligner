#!/usr/bin/env python

from sys import argv
from glob import glob

def error():
    print """
    sort.py: a script for sorting dictionaries in the HTK-appropriate format

    USAGE: ./sort.py dictionary1 [... dictionary2]

    """
    exit(1)

if __name__ == '__main__':

    if len(argv) < 2:
        error()

    # accumulate
    lines = []
    for path in argv[1:]:
        for line in open(path, 'r'):
            lines.append(line.rstrip())
    # sort
    lines.sort()
    # dump out
    for line in lines:
        print line
