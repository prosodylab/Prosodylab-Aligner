"""
Global variables and helpers for forced alignment
"""

from os import makedirs

# global variables

SP = "SP"
SIL = "sil"
TEMP = "temp"

OOV = "OOV.txt"
SCORES = "scores.txt"
ALIGNED = "aligned.mlf"
MISSING = "missing.txt"


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
    makedirs(dirname, exist_ok=True)
