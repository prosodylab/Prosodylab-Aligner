#!/usr/bin/env python3
# eval.py: instrinsic evaluation for forced alignment using Praat TextGrids
# Kyle Gorman <gormanky@ohsu.edu>

from __future__ import division

from textgrid import TextGrid

from sys import argv, stderr
from collections import namedtuple
from argparse import ArgumentParser


CLOSE_ENOUGH = 20
TIER_NAME = "phones"


boundary = namedtuple("boundary", ["transition", "time"])


def boundaries(textgrid, tier_name):
    """
    Extract a single tier named `tier_name` from the TextGrid object 
    `textgrid`, and then convert that IntervalTier to a list of boundaries
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
    argparser = ArgumentParser(description="Alignment quality evaluation")
    argparser.add_argument("-f", "--fudge", type=int,
                           help="Fudge factor in milliseconds")
    argparser.add_argument("-t", "--tier",
                           help="Name of tier to use")
    argparser.add_argument("OneGrid")
    argparser.add_argument("TwoGrid")
    args = argparser.parse_args()
    if args.fudge:
        close_enough = args.fudge / 1000
    if args.tier:
        tier_name = args.tier
    # read in
    first = boundaries(TextGrid.fromFile(args.OneGrid), tier_name)
    secnd = boundaries(TextGrid.fromFile(args.TwoGrid), tier_name)
    # count concordant and discordant boundaries
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
    print("{} 'close enough' boundaries.".format(concordant))
    print("{} incorrect boundaries.".format(discordant))
    print("Agreement: {:.4f}".format(agreement))
