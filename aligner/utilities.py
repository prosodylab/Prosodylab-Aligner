"""
Global variables and helpers for forced alignment
"""

import os

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
