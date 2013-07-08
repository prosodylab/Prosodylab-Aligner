#!/usr/bin/env python
#
# Kyle Gorman <gormanky@ohsu.edu>
#
# The UNIX sort utility does not always do the right thing in HTK's mind,
# but this one does.

import fileinput


if __name__ == '__main__':
    lines = list(set(l.rstrip() for l in fileinput.input()))  # accumulate
    lines.sort()       # sort
    print '\n'.join(lines)
