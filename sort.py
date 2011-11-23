#!/usr/bin/env python
# A script for sorting according to HTK principles
# Kyle Gorman <kgorman@ling.upenn.edu>

from sys import argv


def error():
    print """
    sort.py: a script for sorting dictionaries in the HTK-appropriate format

    USAGE: ./sort.py dictionary1 [... dictionary2]

    """
    exit(1)


if __name__ == '__main__':

    if len(argv) < 1: error()
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
