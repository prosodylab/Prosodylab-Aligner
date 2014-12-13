# Copyright (c) 2011-2014 Kyle Gorman and Michael Wagner
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""
Command-line driver for the module
"""

import os
import yaml
import logging

from bisect import bisect
from shutil import copyfile

from .corpus import Corpus
from .aligner import Aligner
from .archive import Archive
from .textgrid import MLF
from .utilities import splitname, \
                       ALIGNED, CONFIG, DICT, HMMDEFS, MACROS, SCORES

from argparse import ArgumentParser

# global vars

LOGGING_FMT = "%(message)s"


# samplerates which appear to be HTK-compatible (all divisors of 1e7)
SAMPLERATES = [4000, 8000, 10000, 12500, 15625, 16000, 20000, 25000,
               31250, 40000, 50000, 62500, 78125, 80000, 100000, 125000,
               156250, 200000]


# helpers

def get_opts(filename):
    with open(filename, "r") as source:
        return yaml.load(source)


def resolve_opts(args):
    opts = get_opts(args.configuration)
    opts["dictionary"] = args.dictionary if args.dictionary \
        else opts["dictionary"]
    sr = args.samplerate if args.samplerate else opts["samplerate"]
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
    opts["epochs"] = args.epochs if args.epochs else opts["epochs"]
    return opts


# parse arguments
argparser = ArgumentParser(prog="align.py",
                           description="Prosodylab-Aligner")
argparser.add_argument("-c", "--configuration",
                       help="config file")
argparser.add_argument("-d", "--dictionary",
                       help="dictionary file")
argparser.add_argument("-s", "--samplerate", type=int,
                       help="analysis samplerate (in Hz)")
argparser.add_argument("-E", "--epochs", type=int,
                       help="# of epochs of training per round")
input_group = argparser.add_mutually_exclusive_group(required=True)
input_group.add_argument("-r", "--read",
                         help="read in serialized acoustic model")
input_group.add_argument("-t", "--train",
                         help="directory of data to train on")
output_group = argparser.add_mutually_exclusive_group(required=True)
output_group.add_argument("-a", "--align",
                          help="directory of data to align")
output_group.add_argument("-w", "--write",
                          help="location to write serialized model")
verbosity_group = argparser.add_mutually_exclusive_group()
verbosity_group.add_argument("-v", "--verbose", action="store_true",
                             help="Verbose output")
verbosity_group.add_argument("-V", "--extra-verbose", action="store_true",
                             help="Even more verbose output")
args = argparser.parse_args()

# set up logging
loglevel = logging.WARNING
if args.extra_verbose:
    loglevel = logging.DEBUG
elif args.verbose:
    loglevel = logging.INFO
logging.basicConfig(format=LOGGING_FMT, level=loglevel)

# input: pick one
if args.read:
    logging.info("Reading aligner from '{}'.".format(args.read))
    raise NotImplementedError
elif args.train:
    logging.info("Preparing corpus '{}'.".format(args.train))
    opts = resolve_opts(args)
    corpus = Corpus(args.train, opts)
    logging.info("Preparing aligner.")
    aligner = Aligner(opts)
    logging.info("Training aligner on corpus '{}'.".format(args.train))
    aligner.HTKbook_training_regime(corpus, opts["epochs"])
# else unreachable

# output: pick one
if args.align:
    # check to make sure we're not aligning on the training data
    if os.path.realpath(args.train) != os.path.realpath(args.align):
        logging.info("Preparing corpus '{}'.".format(args.align))
        corpus = Corpus(args.align, opts)
    logging.info("Aligning corpus '{}'.".format(args.align))
    aligner.align_and_score(corpus, ALIGNED, SCORES)
    logging.info("Writing likelihood scores to '{}'.".format(SCORES))
    logging.info("Writing TextGrids.")
    size = MLF(ALIGNED).write(args.align)
    if not size:
        logging.error("No paths found!")
        exit(1)
    logging.debug("Wrote {} TextGrids.".format(size))
elif args.write:
    logging.info("Writing out aligner..".format(args.write))
    # create and populate archive
    (_, basename, _) = splitname(args.write)
    archive = Archive.empty(basename)
    archive.add(os.path.join(aligner.curdir, HMMDEFS))
    archive.add(os.path.join(aligner.curdir, MACROS))
    archive.add(opts["dictionary"], DICT)
    # adjust opts to reflect that last one
    opts["dictionary"] = DICT
    # write opts to config file inside archive
    with open(os.path.join(archive.dirname, CONFIG), "w") as sink:
        yaml.dump(opts, sink)
    archive_path = os.path.relpath(archive.dump(args.write))
    logging.info("Wrote aligner to '{}'.".format(archive_path))
# else unreachable
logging.info("Success!")
