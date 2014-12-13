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



from re import match
from glob import glob
from bisect import bisect
from shutil import copyfile
from tempfile import mkdtemp
from collections import defaultdict
from argparse import ArgumentParser
from subprocess import check_call, Popen, CalledProcessError, PIPE


# local modules
from textgrid import MLF
from archive import Archive
from wavfile import WavFile
from prondict import PronDict


# global vars

LOGGING_FMT = "%(module)s: %(message)s"

SP = "sp"
SIL = "sil"

TEMP = "temp"
DICT = "dict"
PROTO = "proto"
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


## helpers

def get_opts(filename):
    with open(filename, "r") as source:
            return yaml.load(source)

def resolve_opts(args):
    opts = get_opts(args.configuration)
    opts["dictionary"] = args.dictionary if args.dictionary \
                                         else opts["dictionary"]
    samplerate = args.samplerate if args.samplerate else opts["samplerate"]
    if samplerate not in SAMPLERATES:
        i = bisect(SAMPLERATES, samplerate)
        if i == 0:
            pass
        elif i == len(SAMPLERATES):
            i = -1
        elif SAMPLERATES[i] - samplerate > samplerate - SAMPLERATES[i - 1]:
            i = i - 1
        # else keep `i` as is
        samplerate = SAMPLERATES[i]
        logging.warning("Using {} Hz as samplerate".format(samplerate))
    opts["samplerate"] = samplerate
    opts["epochs"] = args.epochs if args.epochs else opts["epochs"]
    return opts


def opts2cfg(filename, opts):
    with open(filename, "w") as sink:
        for (setting, value) in opts.items():
            print("{} = {}".format(setting, value), file=sink)


def splitname(fullname):
    """
    Split a filename into directory, basename, and extension
    """
    (dirname, filename) = os.path.split(fullname)
    (basename, ext) = os.path.splitext(filename)
    return (dirname, basename, ext)



class Corpus(object):

    """
    Representation of a directory of training data
    """

    def __init__(self, dirname, opts):
        # temporary directories for stashing the data
        tmpdir = os.environ["TMPDIR"] if "TMPDIR" in os.environ else None
        self.tmpdir = mkdtemp(dir=tmpdir)
        self.auddir = os.path.join(self.tmpdir, "audio")
        os.mkdir(self.auddir)
        self.labdir = os.path.join(self.tmpdir, "label")
        os.mkdir(self.labdir)
        # samplerate
        self.samplerate = opts["samplerate"]
        # phoneset
        self.phoneset = frozenset(opts["phoneset"])
        for phone in self.phoneset:
            if not match(VALID_PHONE, phone):
                logging.error("Phone '{}': not /{}/.".format(ph,
                                               VALID_PHONE.pattern))
                exit(1)
        # dictionary
        self.dictionary = opts["dictionary"]
        self.thedict = PronDict(self.dictionary, self.phoneset)
        #self.thedict[SIL] = [SIL]
        self.taskdict = os.path.join(self.tmpdir, "taskdict")
        # word and phone lists
        self.phons = os.path.join(self.tmpdir, "phons")
        self.words = os.path.join(self.tmpdir, "words")
        # MLF
        self.pron_mlf = os.path.join(self.tmpdir, "pron.mlf")
        self.word_mlf = os.path.join(self.tmpdir, "words.mlf")
        self.phon_mlf = os.path.join(self.tmpdir, "phones.mlf")
        # feature extraction configuration
        self.HCopy_cfg = os.path.join(self.tmpdir, "HCopy.cfg")
        opts2cfg(self.HCopy_cfg, opts["HCopy"])
        self.audio_scp = os.path.join(self.tmpdir, "audio.scp")
        self.feature_scp = os.path.join(self.tmpdir, "feature.scp")
        # actually prepare the data
        (audiofiles, labelfiles) = self._lists(dirname)
        # most errors occur during the former, so we're doing it first
        self._prepare_label(labelfiles)
        self._prepare_audio(audiofiles)
        self._HCopy()

    def _lists(self, dirname):
        """
        Create lists of .wav and .lab files, detecting missing pairs.
        """
        audiofiles = glob(os.path.join(dirname, "*.wav"))
        labelfiles = glob(os.path.join(dirname, "*.lab"))
        if not audiofiles:
            logging.error("No .wav files in directory '{}'.".format(dirname))
            exit(1)
        elif not labelfiles:
            logging.error("No .lab files in directory '{}'.".format(dirname))
            exit(1)
        audiobasenames = frozenset(splitname(audiofile)[1] for
                                  audiofile in audiofiles)
        labelbasenames = frozenset(splitname(labelfile)[1] for
                                  labelfile in labelfiles)
        missing = []
        missing.extend(basename + ".wav" for basenames in
                       labelbasenames - audiobasenames)
        missing.extend(basename + ".lab" for basenames in
                       audiobasenames - labelbasenames)
        if missing:
            with open(MISSING, "w") as sink:
                for filename in missing:
                    print(os.path.join(dirname, filename), file=sink)
            logging.error("Missing data files: see '{}'.".format(MISSING))
            exit(1)
        return (audiofiles, labelfiles)

    def _prepare_label(self, labelfiles):
        """
        Check label files against dictionary, and construct new .lab
        and .mlf files
        """
        found_words = set()
        with open(self.word_mlf, "w") as word_mlf:
            print("#!MLF!#", file=word_mlf)
            for labelfile in labelfiles:
                (dirname, filename) = os.path.split(labelfile)
                word_labfile = os.path.join(self.labdir, filename)
                phon_labfile = os.path.join(self.auddir, filename)
                # header for each file in the .mlf
                print('"{}"'.format(word_labfile), file=word_mlf)
                # read in words from original .lab file
                with open(labelfile, "r") as orig_handle:
                    words = orig_handle.readline().split()
                found_words.update(words)
                # write out new wordlab
                with open(word_labfile, "w") as word_handle:
                    print(" ".join(words), file=word_handle)
                # get pronunciation and check for in-dictionary-hood
                phons = []
                for word in words:
                    try:
                        phons.extend(self.thedict[word][0])
                    except KeyError as error:
                        pass
                # write out new phonelab
                with open(phon_labfile, "w") as phon_handle:
                    print(" ".join(phons), file=phon_handle)
                # append to word_mlf
                print("\n".join(words), file=word_mlf)
                print(".", file=word_mlf)
        # report and die if OOV words are found
        if self.thedict.oov:
            with open(OOV, "w") as oov:
                print("\n".join(sorted(self.thedict.oov)), file=oov)
            logging.error("OOV word(s): see '{}'.".format(OOV))
            exit(1)
        # make words
        with open(self.words, "w") as words:
            print("\n".join(found_words), file=words)
        # create temp file to abuse
        temp = os.path.join(self.tmpdir, TEMP)
        # run HDMan
        with open(temp, "w") as ded:
            print("AS {0}\nMP {1} {1} {0}".format(SP, SIL), file=ded)
        check_call(["HDMan", "-m",
                             "-g", temp,
                             "-w", self.words,
                             "-n", self.phons,
                             self.taskdict,
                             self.dictionary])
        # add SIL to phone list
        with open(self.phons, "a") as phons:
            print(SIL, file=phons)
        # add SIL to taskdict
        with open(self.taskdict, "a") as taskdict:
            print("{0} {0}".format(SIL), file=taskdict)
        # run HLEd
        with open(temp, "w") as led:
            print("""EX
IS {0} {0}
DE {1}
""".format(SIL, SP), file=led)
        check_call(["HLEd", "-l", self.labdir,
                            "-d", self.taskdict,
                            "-i", self.phon_mlf,
                            temp, self.word_mlf])

    def _prepare_audio(self, audiofiles):
        """
        Check audio files, downsampling if necessary, creating .scp file
        """
        with open(self.audio_scp, "w") as audio_scp, \
             open(self.feature_scp, "w") as feature_scp:
            for audiofile in audiofiles:
                (head, filename) = os.path.split(audiofile)
                (basename, _) = os.path.splitext(filename)
                featurefile = os.path.join(self.auddir, basename + ".mfc")
                w = WavFile.from_file(audiofile)
                if w.Fs != self.samplerate:
                    new_wav = os.path.join(self.auddir, filename)
                    logging.warning("Resampling '{}'.".format(audiofile))
                    w.resample_bang(self.samplerate)
                    w.write(new_wav)
                print('"{}" "{}"'.format(audiofile, featurefile),
                      file=audio_scp)
                print('"{}"'.format(featurefile), file=feature_scp)

    def _HCopy(self):
        """
        Compute audio features
        """
        check_call(["HCopy", "-C", self.HCopy_cfg, "-S", self.audio_scp])


class Aligner(object):

    def __init__(self, opts):
        # make temporary directories to stash everything
        hmmdir = os.environ["TMPDIR"] if "TMPDIR" in os.environ else None
        self.hmmdir = mkdtemp(dir=hmmdir)
        self.HCompV_opts = opts["HCompV"]
        self.HERest_cfg = os.path.join(self.hmmdir, "HERest.cfg")
        opts2cfg(self.HERest_cfg, opts["HERest"])
        self.HVite_opts = opts["HVite"]
        # define pruning list
        self.pruning = [str(i) for i in opts["pruning"]]

    def _nxtdir(self):
        """
        Get the next HMM directory
        """
        self.curdir = self.nxtdir
        self.epochs += 1
        self.nxtdir = os.path.join(self.hmmdir, str(self.epochs).zfill(3))
        os.mkdir(self.nxtdir)

    def flatstart(self, corpus):
        # create initial HMM directories
        self.epochs = 0
        self.curdir = os.path.join(self.hmmdir, str(self.epochs).zfill(3))
        os.mkdir(self.curdir)
        self.epochs += 1
        self.nxtdir = os.path.join(self.hmmdir, str(self.epochs).zfill(3))
        os.mkdir(self.nxtdir)
        # ...and now we can rely on `self._nxtdir`
        # make `proto`
        self.proto = os.path.join(self.hmmdir, PROTO)
        with open(self.proto, "w") as proto:
            # FIXME this is highly specific to the default acoustic 
            # features, but figuring out the number of means and variances
            # needed from the HCopy configuration file is not trivial.
            means = " ".join(["0.0" for _ in range(39)])
            varg = " ".join(["1.0" for _ in range(39)])
            print("""~o <VECSIZE> 39 <MFCC_D_A_0>
~h "proto"
<BEGINHMM>
<NUMSTATES> 5""", file=proto)
            for i in range(2, 5):
                print("<STATE> {}".format(i), file=proto)
                print("<MEAN> 39", file=proto)
                print(means, file=proto)
                print("<VARIANCE> 39", file=proto)
                print(varg, file=proto)
            print("""<TRANSP> 5
 0.0 1.0 0.0 0.0 0.0
 0.0 0.6 0.4 0.0 0.0
 0.0 0.0 0.6 0.4 0.0
 0.0 0.0 0.0 0.7 0.3
 0.0 0.0 0.0 0.0 0.0
<ENDHMM>""", file=proto)
        # make `vFloors`
        check_call(["HCompV", "-f", str(self.HCompV_opts["F"]),
                              "-C", self.HERest_cfg,
                              "-S", corpus.feature_scp,
                              "-M", self.curdir, self.proto])
        # make `macros`
        # get first three lines from local proto
        with open(os.path.join(self.curdir, MACROS), "a") as macros:
            with open(os.path.join(self.curdir,
                      os.path.split(self.proto)[1]), "r") as proto:
                for _ in range(3):
                    print(proto.readline().strip(), file=macros)
            # get remaining lines from `vFloors`
            with open(os.path.join(self.curdir, VFLOORS), "r") as vfloors:
                print("\n".join(vfloors.readlines()), file=macros)
        # make `hmmdefs`
        with open(os.path.join(self.curdir, HMMDEFS), "w") as hmmdefs:
            with open(self.proto, "r") as proto:
                protolines = proto.readlines()[2:]
            with open(corpus.phons, "r") as phons:
                for phone in phons:
                    print('~h "{}"'.format(phone.rstrip()), file=hmmdefs)
                    print("\n".join(protolines), file=hmmdefs)

    def train(self, corpus, epochs):
        """
        Perform one or more rounds of estimation
        """
        for _ in range(epochs):
            logging.info("iteration.")
            check_call(["HERest", "-C", self.HERest_cfg,
                                  "-S", corpus.feature_scp,
                                  "-I", corpus.phon_mlf,
                                  "-M", self.nxtdir,
                                  "-H", os.path.join(self.curdir, MACROS),
                                  "-H", os.path.join(self.curdir, HMMDEFS),
                                  "-t"] + self.pruning +
                       [corpus.phons], stdout=PIPE)
            self._nxtdir()

    def HTKbook_training_regime(self, corpus, epochs):
        logging.info("Flat start training.")
        self.flatstart(corpus)
        self.train(corpus, epochs)
        logging.info("Modeling silence.")
        self.small_pause(corpus)
        logging.info("Additional training.")
        self.train(corpus, epochs)
        logging.info("Realigning.")
        self.align(corpus, corpus.phon_mlf)
        logging.info("Final training.")
        aligner.train(corpus, epochs)

    def small_pause(self, corpus):
        """
        Add in a tied-state small pause model
        """
        # make new hmmdef 
        saved = ['~h "{}"'.format(SP)]
        # opened both for reading and writing
        with open(os.path.join(self.curdir, HMMDEFS), "r+") as hmmdefs:
            # find SIL
            for line in hmmdefs:
                if line.startswith('~h "{}"'.format(SIL)):
                    break
            saved.extend(["<BEGINHMM>",
                          "<NUMSTATES> 3",
                          "<STATE> 2"])
            # pass until we get to SIL's middle state
            for line in hmmdefs:
                if line.startswith("<STATE> 3"):
                    break
            # grab SIL's middle state
            for line in hmmdefs:
                if line.startswith("<STATE> 4"):
                    break
                saved.append(line.rstrip())
            # add in the TRANSP matrix
            saved.extend(["<TRANSP> 3", 
                          " 0.0 1.0 0.0", 
                          " 0.0 0.9 0.1",
                          " 0.0 0.0 0.0", 
                          "<ENDHMM>"])
            # write all the lines to the end of `hmmdefs`
            hmmdefs.seek(0, os.SEEK_END)
            hmmdefs.write("\n".join(saved))
        # tie states together
        temp = os.path.join(self.hmmdir, TEMP)
        with open(temp, "w") as hed:
            print("""AT 2 4 0.2 {{{1}.transP}}
AT 4 2 0.2 {{{1}.transP}}
AT 1 3 0.3 {{{0}.transP}}
TI silst {{{1}.state[3],{0}.state[2]}}""".format(SP, SIL), file=hed)
        check_call(["HHEd", "-H", os.path.join(self.curdir, MACROS),
                            "-H", os.path.join(self.curdir, HMMDEFS),
                            "-M", self.nxtdir, 
                            temp, corpus.phons])
        temp = os.path.join(self.hmmdir, TEMP)
        with open(temp, "w") as led:
            print("""EX
IS {0} {0}
""".format(SIL), file=led)
        check_call(["HLEd", "-l", corpus.labdir,
                            "-d", corpus.taskdict,
                            "-i", corpus.phon_mlf,
                            temp, corpus.word_mlf])
        self._nxtdir()

    def align(self, corpus, mlf):
        check_call(["HVite", "-a", "-m",
                             "-o", "SM",
                             "-y", "lab",
                             "-b", SIL,
                             "-i", mlf,
                             "-L", corpus.labdir,
                             "-C", self.HERest_cfg,
                             "-S", corpus.feature_scp,
                             "-H", os.path.join(self.curdir, MACROS),
                             "-H", os.path.join(self.curdir, HMMDEFS),
                             "-I", corpus.word_mlf,
                             "-s", str(self.HVite_opts["SFAC"]),
                             "-t"] + self.pruning +
                             [corpus.taskdict, corpus.phons])

    def align_and_score(self, corpus, mlf):
        """
        The same as `self.align`, but also generates a text file with
        -log likelihood confidence scores for each audio file
        """
        proc = Popen(["HVite", "-a", "-m",
                               "-T", "1",
                               "-o", "SM",
                               "-y", "lab",
                               "-b", SIL,
                               "-i", mlf,
                               "-L", corpus.labdir,
                               "-C", self.HERest_cfg,
                               "-S", corpus.run_scp,
                               "-H", os.path.join(self.curdir, MACROS),
                               "-H", os.path.join(self.curdir, HMMDEFS),
                               "-I", corpus.word_mlf,
                               "-s", str(self.HVite_opts["SFAC"]),
                               "-t"] + self.pruning + \
                               [corpus.taskdict, corpus.phons], 
                                                   stdout=PIPE)
        with open(score, "w") as sink:
            i = 0
            for line in proc.stdout:
                m = match(HVITE_SCORE, line)
                if m:
                    print("{}\t{}".format(corpus.wavlist[i], m.group(1)),
                          file=sink)
                    i += 1
        # Popen equivalent to check_call...
        retcode = proc.wait()
        if retcode != 0:
            raise CalledProcessError(retcode, proc.args)


if __name__ == "__main__":
    # parse arguments
    argparser = ArgumentParser(prog="align.py",
                               description="Prosodylab-Aligner")
    argparser.add_argument("-c", "--configuration", default=CONFIG,
                           help="Configuration file to use")
    argparser.add_argument("-d", "--dictionary", default=DICT,
                           help="dictionary file to use (default: {})".format(DICT))
    argparser.add_argument("-s", "--samplerate", type=int,
                           default=SAMPLERATE,
                           help="analysis samplerate in Hz (default: {})".format(SAMPLERATE))
    argparser.add_argument("-E", "--epochs", type=int, default=EPOCHS,
                           help="# of epochs of training per round (default: {})".format(EPOCHS))
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
        aligner = Aligner.from_archive(args.read)
    elif args.train:
        logging.info("Preparing corpus '{}'.".format(args.train))
        opts = resolve_opts(args)
        corpus = Corpus(args.train, opts)
        logging.info("Preparing aligner.")
        aligner = Aligner(opts)
        logging.info("Training aligner on corpus '{}'.".format(args.train))
        aligner.HTKbook_training_regime(corpus, opts["epochs"])
    # else unreachable

    exit("output not working yet; bye")
    """
    ## output: pick one
    if args.align:
        mlf = aligner.align_and_score()
        logging.info("Making TextGrids.")
        if MLF(mlf).write(args.align) < 1:
            logging.error("No paths found!")
            exit(1)
    elif args.write:
        raise NotImplementedError
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
