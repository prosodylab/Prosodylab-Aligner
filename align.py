#!/usr/bin/env python3
#
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


import os
import yaml
import logging


LOGGING_FMT = "%(module)s: %(message)s"


from re import match
from glob import glob
from bisect import bisect
from shutil import copyfile
from tempfile import mkdtemp
from argparse import ArgumentParser
from subprocess import check_call, Popen, CalledProcessError, PIPE


# local modules
from textgrid import MLF
from archive import Archive
from wavfile import WavFile
from prondict import PronDict


# global vars

SP = "sp"
SIL = "sil"

TEMP = "temp"
DICT = "dict"
MACROS = "macros"
HMMDEFS = "hmmdefs"
VFLOORS = "vFloors"

OOV = "OOV.txt"
ALIGN = "align.mlf"
CONFIG = "config.yaml"
SCORES = "scores.txt"
MISSING = "missing.txt"

EPOCHS = 5
SAMPLERATE = 16000
# samplerates which appear to be HTK-compatible (all divisors of 1e7)
SAMPLERATES = [4000, 8000, 10000, 12500, 15625, 16000, 20000, 25000,
               31250, 40000, 50000, 62500, 78125, 80000, 100000, 125000,
               156250, 200000]

# regexp for inspecting phones
VALID_PHONE = r"^[^\d\s]\S*$"

# regexp for parsing the HVite trace
HVITE_SCORE = r".+==  \[\d+ frames\] (-\d+\.\d+)"
# in case you"re curious, the rest of the trace string is:
#     /\[Ac=-\d+\.\d+ LM=0.0\] \(Act=\d+\.\d+\)/


# CLASSES

def split_filename(path):
    """
    Split a filename into directory, basename, and extension
    """
    (dirname, filename) = os.path.split(path)
    (basename, ext) = os.path.splitext(filename)
    return (dirname, basename, ext)



class Aligner(object):

    """
    Basic class for performing alignment, using Montreal English lab speech
    models shipped with this package and stored in the directory MOD/.
    """

    @classmethod
    def from_archive(cls, filename, args, opts):
        # open archive
        archive = Archive(filename)
        # set dictionary correctly
        opts["dictionary"] = os.path.join(archive.dirname, DICT)
        # create instance
        retval = cls(args, opts)
        # set hmmdir correctly
        retval.hmmdir = archive.dirname
        return retval

    def __init__(self, args, opts):
        # make a temporary directory to stash everything
        tmpdir = os.environ["TMPDIR"] if "TMPDIR" in os.environ else None
        self.tmpdir = mkdtemp(dir=tmpdir)
        # make subdirectories
        self.auddir = os.path.join(self.tmpdir, "AUD")
        os.mkdir(self.auddir)
        self.labdir = os.path.join(self.tmpdir, "LAB")
        os.mkdir(self.labdir)
        self.hmmdir = os.path.join(self.tmpdir, "HMM")
        os.mkdir(self.hmmdir)
        # specific hyperparameters
        self.samplerate = opts["samplerate"]
        self.pruning = [str(i) for i in opts["pruning"]]
        # phoneset
        self.phoneset = frozenset(phoneset)
        for phone in self.phoneset:
            if not match(VALID_PHONE, phone):
                logging.error("Disallowed phone '{}' in".format(ph) +
                              " dictionary '{}'".format(source.name) +
                              " (ln. {})".format(i) +
                              ": phones must match /^[a-zA-Z]\S+$/.")
                exit(1)
        # dictionary
        self.dictionary = opts["dictionary"]
        self.thedict = PronDict(dictionary, self.phoneset)
        self.thedict[SIL] = [SIL]
        # lists
        self.words = os.path.join(self.tmpdir, "words")
        self.phons = os.path.join(self.tmpdir, "phones")
        # HMMs
        self.proto = os.path.join(self.tmpdir, "proto")
        # task dictionary
        self.taskdict = os.path.join(self.tmpdir, "taskdict")
        # SCP files
        self.copy_scp = os.path.join(self.tmpdir, "copy.scp")
        self.test_scp = os.path.join(self.tmpdir, "test.scp")
        self.train_scp = os.path.join(self.tmpdir, "train.scp")
        # MLFs
        self.pron_mlf = os.path.join(self.tmpdir, "pron.mlf")
        self.word_mlf = os.path.join(self.tmpdir, "words.mlf")
        self.phon_mlf = os.path.join(self.tmpdir, "phones.mlf")
        # config
        self.HCopy_cfg = os.path.join(self.tmpdir, "HCopy.cfg")
        Aligner.opts2cfg(self.HCopy_cfg, opts["HCopy"])
        self.HCompV_opts = opts["HCompV"]
        self.HERest_cfg = os.path.join(self.tmpdir, "HERest.cfg")
        Aligner.opts2cfg(self.HERest_cfg, opts["HERest"])
        self.HVite_opts = opts["HVite_opts"]
        # initializing whatever else is needed
        self._subclass_specific_init(args)

    @staticmethod
    def opts2cfg(filename, opts):
        with open(filename, "w") as sink:
            for (setting, value) in opts.items():
                print("{} = {}".format(setting, value), file=sink)

    def _subclass_specific_init(self, args):
        """
        Performs subclass-specific initialization operations
        """
        self._check(args) # perform checks on data
        self._HCopy(args) # extract audio features

    def _check(self, args):
        """
        Performs checks on .wav and .lab files in the folder indicated by
        ts_dir. If any problem arises, an error results.
        """
        # check for missing, unpaired data
        raise NotImplementedError

    def _lists(self, dirname):
        """
        Create lists of .wav and .lab files, detecting missing pairs.
        """
        wavlist = glob(os.path.join(dirname), "*.wav"))
        lablist = glob(os.path.join(dirname), "*.lab"))
        if len(wavlist) < 1:
            logging.error("Found no .wav files in directory" +
                          " '{}'.".format(dirname))
            exit(1)
        elif len(lablist) < 1:
            logging.error("Found no .lab files in directory" +
                          " '{}'.".format(dirname))
            exit(1)
        wavbasenames = frozenset(bname for (_, bname, _) in wavlist)
        labbasenames = frozenset(bname for (_, bname, _) in lablist)
        missing = []
        missing.extend(basename + ".wav" for basenames in
                       labbasenames - wavbasenames)
        missing.extend(basename + ".lab" for basenames in
                       wavbasenames - labbasenames)
        if missing:
            with open(MISSING, "w") as sink:
                for filename in missing:
                    print(os.path.join(dirname, filename), file=sink)
            logging.error("Missing data files: see '{}'.".format(MISSING))
            exit(1)
        return (wavlist, lablist)

    def _check_dct(self, lab_list):
        """
        Checks the label files to confirm that all words are found in the
        dictionary, while building new .lab and .mlf files silently

        TODO: add checks that the phones are also valid
        """
        raise NotImplementedError

    def _prepare_audio(self, wavfiles):
        """
        Check audio files, mixing down to mono and downsampling if
        necessary; also writes copy_scp.
        """
        with open(self.copy_scp, "r") as copy_spc:
            for wavfile in wavfiles:
                (_, tail) = os.path.split(wavfile)
                basename = os.path.splitext(tail)
                mfc = os.path.join(self.auddir, basename + ".mfc")
                w = WavFile.from_file(wav)
                if w.Fs != self.samplerate:
                    new_wave = os.path.join(self.auddir, head + ".wav")
                    logging.warning("Resampling '{}'.".format(wav))
                    w.resample_bang(self.samplerate)
                    w.write(new_wave)
                print('"{}" "{}"'.format(wav, mfc), file=copy_scp)

    def _HCopy(self):
        """
        Compute MFCCs
        """
        check_call(["HCopy", "-C", self.HCopy_cfg, "-S", self.copy_scp])

    def align(self):
        """
        Align using the models in self.cur_dir and MLF to path
        """
        check_call(["HVite", "-a", "-m",
                             "-o", "SM",
                             "-y", "lab",
                             "-b", SIL,
                             "-i", mlf,
                             "-L", self.lab_dir,
                             "-C", self.HERest_cfg,
                             "-S", self.test_scp,
                             "-H", os.path.join(self.cur_dir, MACROS),
                             "-H", os.path.join(self.cur_dir, HMMDEFS),
                             "-I", self.word_mlf,
                             "-s", str(self.HVite_opts["SFAC"]),
                             "-t"] + self.pruning +
                             [self.taskdict, self.phons])

    def align_and_score(self):
        """
        The same as self.align(mlf), but also generates a text file with 
        -log likelihood confidence scores for each audio file
        """
        proc = Popen(["HVite", "-a", "-m",
                               "-T", "1",
                               "-o", "SM",
                               "-y", "lab",
                               "-b", SIL,
                               "-i", mlf,
                               "-L", self.lab_dir,
                               "-C", self.HERest_cfg,
                               "-S", self.test_scp,
                               "-H", os.path.join(self.cur_dir, MACROS),
                               "-H", os.path.join(self.cur_dir, HMMDEFS),
                               "-I", self.word_mlf,
                               "-s", str(self.HVite_opts["SFAC"]),
                               "-t"] + self.pruning + \
                               [self.taskdict, self.phons], stdout=PIPE)
        with open(score, "w") as sink:
            i = 0
            for line in proc.stdout:
                m = match(HVITE_SCORE, line)
                if m:
                    print >> sink, "{}\t{}".format(self.wavlist[i],
                                                   m.group(1))
                    i += 1
        # Popen equivalent to check_call...
        retcode = proc.wait()
        if retcode != 0:
            raise CalledProcessError(retcode, proc.args)


class TrainAligner(Aligner):

    """
    This inherits the align() and data prep methods from Align, but also
    supports train(), small_pause(), and realign() for building your own
    models
    """

    def _subclass_specific_init(self, ts_dir, tr_dir):
        """
        Performs subclass-specific initialization operations
        """
        # perform checks on data
        self._check(ts_dir, tr_dir)
        # run HCopy
        self._HCopy()
        # create the next HMM directory
        self.n = 0
        self.cur_dir = os.path.join(self.hmm_dir, str(self.n).zfill(3))
        # make the first directory
        os.mkdir(self.cur_dir)
        # increment
        self.n = + 1
        # compute the path for the new one
        self.nxt_dir = os.path.join(self.hmm_dir, str(self.n).zfill(3))
        # make the new directory
        os.mkdir(self.nxt_dir)  # from now on, just call self._nxt_dir()
        # make `proto`
        with open(self.proto, "w") as sink:
            # FIXME this is highly specific to the default acoustic 
            # features, but figuring out the number of means and variances
            # needed from the HCopy configuration file is not trivial.
            means = " ".join(["0.0" for _ in xrange(39)])
            varg = " ".join(["1.0" for _ in xrange(39)])
            print >> sink, """~o <VECSIZE> 39 <MFCC_D_A_0>
    ~h "proto"
<BEGINHMM>
<NUMSTATES> 5"""
            for i in xrange(2, 5):
                print >> sink, "<STATE> {}\n<MEAN> 39\n{}".format(i, means)
                print >> sink, "<VARIANCE> 39\n{}".format(varg)
            print >> sink, """<TRANSP> 5
 0.0 1.0 0.0 0.0 0.0
 0.0 0.6 0.4 0.0 0.0
 0.0 0.0 0.6 0.4 0.0
 0.0 0.0 0.0 0.7 0.3
 0.0 0.0 0.0 0.0 0.0
<ENDHMM>"""
        # make `vFloors`
        check_call(["HCompV", "-f", str(self.HCompV_opts["F"]),
                              "-C", self.HERest_cfg,
                              "-S", self.train_scp,
                              "-M", self.cur_dir, self.proto])
        # make `macros`
        # get first three lines from local proto
        with open(os.path.join(self.cur_dir, MACROS), "a") as macros:
            with open(os.path.join(self.cur_dir, 
                      os.path.split(self.proto)[1]), "r") as proto:
                for _ in xrange(3):
                    print >> macros, proto.readline(),
            # get remaining lines from `vFloors`
            with open(os.path.join(self.cur_dir, VFLOORS), "r") as vfloors:
                macros.writelines(vfloors.readlines())
        # make `hmmdefs`
        with open(os.path.join(self.cur_dir, HMMDEFS), "w") as hmmdefs:
            with open(self.proto, "r") as proto:
                protolines = proto.readlines()[2:]
            with open(self.phons, "r") as phons:
                for phone in phons:
                    # the header
                    print >> hmmdefs, '~h "{}"'.format(phone.rstrip())
                    # the rest
                    hmmdefs.writelines(protolines)

    def _check(self, ts_dir, tr_dir):
        """
        Performs checks on .wav and .lab files in the folders indicated by
        dir1 and dir2, eliminating any redundant computations.
        """
        raise NotImplementedError

    def _nxt_dir(self):
        """
        Get the next HMM directory
        """
        raise NotImplementedError

    def train(self, epochs):
        """
        Perform one or more rounds of estimation
        """
        for _ in xrange(epochs):
            check_call(["HERest", "-C", self.HERest_cfg,
                                  "-S", self.train_scp,
                                  "-I", self.phon_mlf,
                                  "-M", self.nxt_dir,
                                  "-H", os.path.join(self.cur_dir, MACROS),
                                  "-H", os.path.join(self.cur_dir,
                                                     HMMDEFS),
                                  "-t"] + self.pruning +
                       [self.phons], stdout=PIPE)
            self._nxt_dir()

    def HTKbook_training_regime(self, epochs):
        self.train(epochs)
        logging.info("Modeling silence.")
        self.small_pause()
        logging.info("Additional training.")
        self.train(epochs)
        logging.info("Realigning.")
        self.align()
        logging.info("Final training.")
        aligner.train(epochs)

    def small_pause(self):
        """
        Add in a tied-state small pause model
        """
        raise NotImplementedError


## helpers


def get_opts(filename):
    try: 
        with open(filename.configuration, "r") as source:
            return yaml.load(source)
    except (IOError, yaml.YAMLError) as error:
        logging.error("Error reading configuration file '{}': {}".format(
                      filename, error))
        exit(1)

def resolve_opts(args, opts):
    opts = get_opts(args.configuration)
    opts["dictionary"] = args.dictionary if args.dictionary \
                                         else opts["dictionary"]
    samplerate = args.samplerate if args.samplerate else opts["samplerate"]
    if samplerate not in SAMPLERATES:
        i = bisect(SAMPLERATES, samplerate)
        if i == 0:
            pass
        elif i == len(SRs):
            i = -1
        elif SAMPLERATES[i] - samplerate > samplerate - SAMPLERATES[i - 1]:
            i = i - 1
        # else keep `i` as is
        samplerate = SAMPLERATES[i]
        logging.warning("Using {} Hz as samplerate".format(samplerate))
    opts["samplerate"] = samplerate
    opts["epochs"] = args.epochs if args.epochs else opts["epochs"]
    return opts


if __name__ == "__main__":
    # parse arguments
    argparser = ArgumentParser(prog="align.py",
                               description="Prosodylab-Aligner")
    argparser.add_argument("-c", "--configuration", default=CONFIG,
                           help="Configuration file to use")
    argparser.add_argument("-d", "--dictionary", default=DICT,
                           help="dictionary file to use" + 
                           " (default: {})".format(DICT))
    argparser.add_argument("-s", "--samplerate", type=int,
                           default=SAMPLERATE,
                           help="analysis samplerate in Hz" +
                           " (default: {})".format(SAMPLERATE))
    argparser.add_argument("-E", "--epochs", type=int, default=EPOCHS,
                           help="# of epochs of training per round " +
                           "(default: {})".format(EPOCHS))
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
    argparser.add_argument("-v", "--verbose", action="store_true",
                           help="Verbose output")
    argparser.add_argument("-V", "--really-verbose", action="store_true",
                           help="Even more verbose output")
    args = argparser.parse_args()

    # set up logging
    if args.really_verbose:
        logging.basicConfig(format=LOGGING_FMT, level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(format=LOGGING_FMT, level=logging.INFO)
    else:
        logging.basicConfig(format=LOGGING_FMT, level=logging.WARNING)

    ## input: pick one
    if args.read:
        logging.info("Initializing aligner from file.")
        aligner = TrainAligner.from_archive(args.read)
    elif args.train:
        logging.info("Training aligner.")
        opts = resolve_opts(args)
        aligner = TrainAligner(args, opts)
        aligner.HTKBook_training_regime(opts["epochs"])
    # else unreachable

    ## output: pick one
    if args.align:
        mlf = aligner.align_and_score()
        logging.info("Making TextGrids.")
        if MLF(mlf).write(args.align) < 1:
            logging.error("No paths found!")
            exit(1)
    elif args.write:
        raise NotImplementedError
        """
        archive = Archive(aligner.hmm_dir)
        # copy dictionary to archive
        copyfile(dictionary, os.path.join(archive.dirname, DICT))
        # FIXME what should I do about the dictionary path?
        # write config file to archive
        filename = os.path.join(archive.dirname, CONFIG)
        try:
            with open(filename, "w") as sink:
                print(yaml.dump(opts, default_flow_style=False), file=sink)
        except (IOError, yaml.YAMLError) as err:
            logging.error("Error writing config file '{}': {}.".format(
                          filename, err))
        # write full archive to disk
        archiveout = archive.dump(args.write)
        logging.info("Serialized model to '{}'.".format(archiveout))
    # else unreachable
        """
