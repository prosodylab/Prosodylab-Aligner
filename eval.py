#!/usr/bin/env python -O
# eval.py: instrinsic evaluation for forced alignment using Praat TextGrids
# Kyle Gorman <gormanky@ohsu.edu>

from __future__ import division

from textgrid import TextGridFromFile

from sys import argv, stderr
from collections import namedtuple
from getopt import getopt, GetoptError


USAGE = """USAGE: {} [-s 20] [-t phones] TGrid1 TGrid2""".format(__file__)

CLOSE_ENOUGH = 20
TIER_NAME = "phones"

boundary = namedtuple("boundary", ["transition", "time"])


def boundaries(textgrid, tier_name):
    """
    Extract a single tier named `tier_name` from the TextGrid object 
    `textgrid`, and then convert that IntervalTier to boundaries
    """
    tiers = textgrid.getList(tier_name)
    if not tiers:
        exit('TextGrid has no "{}" tier.'.format(tier_name))
    if len(tiers) > 1:
        exit('TextGrid has many "{}" tiers.'.format(tier_name))
    tier = tiers[0]
    boundaries = []
    for (interval1, interval2) in zip(tier, tier[1:]):
        boundaries.append(boundary('"{}"+"{}"'.format(interval1.mark,
                                                      interval2.mark),
                                                      interval1.maxTime))
    return boundaries


def is_close_enough(tx, ty, close_enough):
    """
    Return True iff `tx` and `ty` are within `close_enough` of each other
    """
    return abs(tx - ty) < close_enough


if __name__ == "__main__":
    # check args
    tier_name = TIER_NAME
    close_enough = CLOSE_ENOUGH / 1000
    (opts, args) = getopt(argv[1:], 's:t:')
    if len(args) != 2:
        print >> stderr, USAGE
        exit("Not enough TextGrids provided")
    try:
        for (opt, val) in opts:
            if opt == '-s':
                close_enough = int(val) / 1000
            elif opt == '-t':
                tier_name = val
            else:
                raise GetoptError
    except (TypeError, GetoptError) as err:
        print >> stderr, USAGE
        exit(str(err))
    # get boundaries
    first = boundaries(TextGridFromFile(args[0]), tier_name)
    secnd = boundaries(TextGridFromFile(args[1]), tier_name)
    # count
    if len(first) != len(secnd):
        exit("Tiers lengths do not match.")
    concordant = 0
    discordant = 0
    for (boundary1, boundary2) in zip(first, secnd):
        if boundary1.transition != boundary2.transition:
            exit("Tier labels do not match.")
        if is_close_enough(boundary1.time, boundary2.time, close_enough):
            concordant += 1
        else:
            discordant += 1
    # print out
    agreement = concordant / (concordant + discordant)
    print '{} "close enough" boundaries, {} incorrect boundaries'.format(
                                         concordant, discordant)
    print 'Agreement: {:.4f}'.format(agreement)
