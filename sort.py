#!/usr/bin/env python -O
#
# Kyle Gorman <gormanky@ohsu.edu>
#
# The UNIX sort utility does not always do the right thing, as far as HTK
# is concerned; this one does.

import fileinput


if __name__ == '__main__':
    lines = set(l.rstrip() for l in fileinput.input())  # accumulate
    print '\n'.join(sorted(lines))                      # linearize
