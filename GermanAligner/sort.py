#!/usr/bin/env python3
# Kyle Gorman <gormanky@ohsu.edu>
# The UNIX `sort` utility does not always sort the dictionary the way that
# HTK expects; this one does


import fileinput


if __name__ == "__main__":
    lines = frozenset(l.rstrip() for l in fileinput.input())  # accumulate
    print("\n".join(sorted(lines)))                           # linearize
