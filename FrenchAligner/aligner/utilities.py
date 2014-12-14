"""
Global variables and helpers for forced alignment
"""

import os
import yaml
import logging

# global variables

SP = "SP"
SIL = "sil"
TEMP = "temp"

ALIGNED = "aligned.mlf"
CONFIG = "config.yaml"
DICT = "dict"
HMMDEFS = "hmmdefs"
MACROS = "macros"
MISSING = "missing.txt"
PROTO = "proto"
OOV = "OOV.txt"
SCORES = "scores.txt"
VFLOORS = "vFloors"

# samplerates which appear to be HTK-compatible (all divisors of 1e7)
SAMPLERATES = [4000, 8000, 10000, 12500, 15625, 16000, 20000, 25000,
               31250, 40000, 50000, 62500, 78125, 80000, 100000, 125000,
               156250, 200000]


# helpers

def opts2cfg(filename, opts):
    """
    Convert dictionary of key-value pairs to an HTK config file
    """
    with open(filename, "w") as sink:
        for (setting, value) in opts.items():
            print("{!s} = {!s}".format(setting, value), file=sink)


def mkdir_p(dirname):
    """
    Create a directory, recursively if necessary, and suceed
    silently if it already exists
    """
    os.makedirs(dirname, exist_ok=True)


def splitname(fullname):
    """
    Split a filename into directory, basename, and extension
    """
    (dirname, filename) = os.path.split(fullname)
    (basename, ext) = os.path.splitext(filename)
    return (dirname, basename, ext)


def resolve_opts(args):
    with open(args.configuration, "r") as source:
        opts = yaml.load(source)
    # command line only
    if not args.dictionary:
        logging.error("Dictionary not specified.")
        exit(1)
    opts["dictionary"] = args.dictionary
    if not args.epochs:
        logging.error("Epochs not specified.")
        exit(1)
    opts["epochs"] = args.epochs
    # could be either, and the command line takes precedent.
    try:
        sr = args.samplerate if args.samplerate else opts["samplerate"]
    except KeyError:
        logging.error("Samplerate not specified.")
        exit(1)
    if sr not in SAMPLERATES:
        i = bisect(SAMPLERATES, sr)
        if i == 0:
            pass
        elif i == len(SAMPLERATES):
            i = -1
        elif SAMPLERATES[i] - sr > sr - SAMPLERATES[i - 1]:
            i = i - 1
        # else keep `i` as is
        sr = SAMPLERATES[i]
        logging.warning("Using {} Hz as samplerate".format(sr))
    opts["samplerate"] = sr
    return opts
