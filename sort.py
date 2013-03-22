#!/usr/bin/env python
# 
# Kyle Gorman <gormanky@ohsu.edu>
# 
# The UNIX sort utility does not always do the right thing in HTK's mind,
# but this one does, so check it out, y'all.

import fileinput


if __name__ == '__main__':
    # accumulate
    lines = list(set(l.rstrip() for l in fileinput.input()))
    # sort
    lines.sort()
    # dump out
    for line in lines:
        print line
