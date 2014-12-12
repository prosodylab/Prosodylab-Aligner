#!/usr/bin/env python
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
#
# align.py: text/speech alignment for speech production experiments
# Kyle Gorman <gormanky@ohsu.edu> and Michael Wagner <chael@mcgill.ca>
#
# Requires Python 2.6-2.7
#
# See README.md for usage information and a tutorial.
#
# This project was funded by:
#
# FQRSC Nouvelle Chercheur NP-132516
# SSHRC Digging into Data Challenge Grant 869-2009-0004
# SSHRC Canada Research Chair 218503

from __future__ import division

# VERSION CHECK
# before we get going, check Python version
from sys import version_info, exit

if version_info[0] != 2 or version_info[1] < 6:
    exit("You need Python 2.6-2.7 to run this script.")

import os
import re
import yaml
import logging

LOGGING_FMT = "%(levelname)s: %(message)s"

from glob import glob
from bisect import bisect
from tempfile import mkdtemp
from collections import defaultdict
from argparse import ArgumentParser
from subprocess import check_call, Popen, CalledProcessError, PIPE

# should be in the current directory
from textgrid import MLF  # http://github.com/kylebgorman/textgrid.py/
from wavfile import WavFile

# GLOBAL VARS
# You can change these if you know HTK well

SP = "sp"
SIL = "sil"
TEMP = "temp"
MACROS = "macros"
HMMDEFS = "hmmdefs"
VFLOORS = "vFloors"

OOV = "OOV.txt"
SCORES = "scores.txt"
MISSING = "missing.txt"

EPOCHS = 4
SAMPLERATE = 16000

# hidden, but useful for debugging
ALIGN_MLF = ".ALIGN.mlf"

# regexp for parsing the HVite trace
HVITE_SCORE = re.compile(".+==  \[\d+ frames\] (-\d+\.\d+)")
# in case you"re curious, the rest of the trace string is:
#     /\[Ac=-\d+\.\d+ LM=0.0\] \(Act=\d+\.\d+\)/

# regexp for inspecting phones
VALID_PHONE = re.compile("^[^\d\s]\S*$")

# list of CMU English phones, which can only be used if you"re not training

CMU_PHONES = set(["AA0", "AA1", "AA2", "AE0", "AE1", "AE2",
                  "AH0", "AH1", "AH2", "AO0", "AO1", "AO2",
                  "AW0", "AW1", "AW2", "AY0", "AY1", "AY2",
                  "EH0", "EH1", "EH2", "ER0", "ER1", "ER2",
                  "EY0", "EY1", "EY2", "IH0", "IH1", "IH2",
                  "IY0", "IY1", "IY2", "OW0", "OW1", "OW2",
                  "OY0", "OY1", "OY2", "UH0", "UH1", "UH2",
                  "UW0", "UW1", "UW2",
                  "B", "CH", "D", "DH", "F", "G", "HH", "JH", "K", "L",
                  "M", "N", "NG", "P", "R", "S", "SH", "T", "TH", "V",
                  "W", "Y", "Z", "ZH"])

# defaults
EPOCHS = 5
SAMPLERATE = 16000
# samplerates which are HTK-compatible (divisors of 1e7)
SAMPLERATES = [4000, 8000, 10000, 12500, 15625, 16000, 20000, 25000,
               31250, 40000, 50000, 62500, 78125, 80000, 100000, 125000,
               156250, 200000]


# CLASSES


class PronDict(object):

    """
    A wrapper for a normal pronunciation dictionary in the CMU style
    """

    @staticmethod
    def pronify(source):
        for (i, line) in enumerate(source, 1):
            if line.startswith(";"):
                continue
            (word, pron) = line.rstrip().split(None, 1)
            yield (i, word, pron.split())

    def __init__(self, f, phoneset):
        # inspect phoneset
        for phone in phoneset:
            if not VALID_PHONE.match(phone):
                logging.error("Disallowed phone '{}' in".format(ph) +
                              " dictionary '{}'".format(source.name) +
                              " (ln. {})".format(i) +
                              ": phones must match /^[a-zA-Z]\S+$/.")
                exit(1)
        # build up dictionary
        source = f if hasattr(f, "read") else open(f, "r")
        self.d = defaultdict(list)
        for (i, word, pron) in PronDict.pronify(source):
            for ph in pron:
                if ph not in phoneset:
                    logging.error("Unknown phone '{}' in".format(ph) +
                                  " dictionary '{}'".format(source.name) +
                                  " (ln. {}).".format(i))
                    exit(1)
            self.d[word].append(pron)
        source.close()
        # for later...
        self.ood = set()

    def __contains__(self, key):
        return key in self.d and self.d[key] != []

    def __getitem__(self, key):
        getlist = self.d[key]
        if getlist or key:
            return getlist
        else:
            self.ood.add(key)
            raise KeyError(key)

    def __repr__(self):
        return "PronDict({})".format(self.d)

    def __setitem__(self, key, value):
        self.d[key].append(value)


class Aligner(object):

    """
    Basic class for performing alignment, using Montreal English lab speech
    models shipped with this package and stored in the directory MOD/.
    """

    def __init__(self, ts_dir, tr_dir, dictionary, phoneset, samplerate,
                 pruning, HCopy_opts, HCompV_opts, HERest_opts,
                 HVite_opts, ood_mode=True):
        # make a temporary directory to stash everything
        arg = os.environ["TMPDIR"] if "TMPDIR" in os.environ else None
        self.tmp_dir = mkdtemp(dir=arg)
        # make subdirectories thereof
        self.aud_dir = os.path.join(self.tmp_dir, "DAT")
        os.mkdir(self.aud_dir)
        self.lab_dir = os.path.join(self.tmp_dir, "LAB")
        os.mkdir(self.lab_dir)
        self.hmm_dir = os.path.join(self.tmp_dir, "HMM")
        os.mkdir(self.hmm_dir)
        # class variables
        self.samplerate = samplerate
        self.pruning = [str(i) for i in pruning]
        # dictionary reps
        self.dictionary = dictionary  # string of dict location
        self.the_dict = PronDict(dictionary, phoneset)
        self.the_dict[SIL] = [SIL]
        # lists
        self.words = os.path.join(self.tmp_dir, "words")
        self.phons = os.path.join(self.tmp_dir, "phones")
        # HMMs
        self.proto = os.path.join(self.tmp_dir, "proto")
        # task dictionary
        self.taskdict = os.path.join(self.tmp_dir, "taskdict")
        # SCP files
        self.copy_scp = os.path.join(self.tmp_dir, "copy.scp")
        self.test_scp = os.path.join(self.tmp_dir, "test.scp")
        self.train_scp = os.path.join(self.tmp_dir, "train.scp")
        # MLFs
        self.pron_mlf = os.path.join(self.tmp_dir, "pron.mlf")
        self.word_mlf = os.path.join(self.tmp_dir, "words.mlf")
        self.phon_mlf = os.path.join(self.tmp_dir, "phones.mlf")
        # config
        self.HCopy_cfg = os.path.join(self.tmp_dir, "HCopy.cfg")
        Aligner.opts2cfg(self.HCopy_cfg, HCopy_opts)
        self.HCompV_opts = HCompV_opts
        self.HERest_cfg = os.path.join(self.tmp_dir, "HERest.cfg")
        Aligner.opts2cfg(self.HERest_cfg, HERest_opts)
        self.HVite_opts = HVite_opts
        self.ood_mode = ood_mode
        # initializing whatever else is needed
        self._subclass_specific_init(ts_dir, tr_dir)

    @staticmethod
    def opts2cfg(filename, opts):
        with open(filename, "w") as sink:
            for (setting, value) in opts.iteritems():
                print >> sink, "{} = {}".format(setting, value)

    def _subclass_specific_init(self, ts_dir, tr_dir):
        """
        Performs subclass-specific initialization operations
        """
        # perform checks on data
        self._check(ts_dir)
        # make audio copies
        self._HCopy()
        # where trained models can be found...
        self.cur_dir = tr_dir

    def _check(self, ts_dir):
        """
        Performs checks on .wav and .lab files in the folder indicated by
        ts_dir. If any problem arises, an error results.
        """
        # check for missing, unpaired data
        (self.wav_list, lab_list) = self._lists(ts_dir)
        # check dictionary
        self._check_dct(lab_list)
        # check audio
        self._check_aud(self.wav_list)

    def _lists(self, path):
        """
        Checks that the .wav and .lab files are all paired. An exception is
        raised if they are not, and the unpaired data are written out.
        If no errors result, the tuple (wav_list, lab_list) is returned.
        """
        # glob together the list of source data
        wav_list = glob(os.path.join(os.path.realpath(path), "*.wav"))
        lab_list = glob(os.path.join(os.path.realpath(path), "*.lab"))
        if len(wav_list) < 1:  # broken
            logging.error("Directory '{}' has no .wav files.".format(path))
            exit(1)
        else:
            missing = []
            for lab in lab_list:
                wav = os.path.splitext(lab)[0] + ".wav"  # expected...
                if not os.path.exists(wav):
                    missing.append(wav)
            for wav in wav_list:
                lab = os.path.splitext(wav)[0] + ".lab"  # expected...
                if not os.path.exists(lab):
                    missing.append(lab)
            if missing:
                with open(MISSING, "w") as sink:
                    for path in missing:
                        print >> sink, path
                    print >> sink, path
                logging.error("Missing data: see '{}'.".format(MISSING))
                exit(1)
        return (wav_list, lab_list)

    def _check_dct(self, lab_list):
        """
        Checks the label files to confirm that all words are found in the
        dictionary, while building new .lab and .mlf files silently

        TODO: add checks that the phones are also valid
        """
        found_words = set()
        with open(self.word_mlf, "w") as word_mlf:
            ood = defaultdict(list)
            print >> word_mlf, "#!MLF!#"
            for lab in lab_list:
                lab_name = os.path.split(lab)[1]
                # new lab file at the phone level, in self.aud_dir
                phon_lab = open(os.path.join(self.aud_dir, lab_name), "w")
                # new lab file at the word level, in self.lab_dir
                word_lab = open(os.path.join(self.lab_dir, lab_name), "w")
                # .mlf headers
                print >> word_mlf, '"{}"'.format(word_lab.name)
                # sil
                print >> phon_lab, SIL
                # look up words
                for word in open(lab, "r").readline().rstrip().split():
                    if word in self.the_dict:
                        found_words.add(word)
                        print >> phon_lab, "\n".join(
                                           self.the_dict[word][0])
                        print >> word_lab, "{} ".format(word)
                        print >> word_mlf, word
                    else:
                        ood[word].append(lab)
                print >> phon_lab, SIL
                print >> word_mlf, "."
                phon_lab.close()
                word_lab.close()
        # now complain if any found
        if ood:
            with open(OOV, "w") as sink:
                if self.ood_mode:
                    for (word, flist) in sorted(ood.iteritems()):
                        print >> sink, "{}\t{}".format(word,
                                                       " ".join(flist))
                else:
                    for word in sorted(ood):
                        print >> sink, word
            logging.error("OOV word(s): see '{}'.".format(OOV))
            exit(1)
        # make word
        print >> open(self.words, "w"), "\n".join(found_words)
        ded = os.path.join(self.tmp_dir, TEMP)
        # make ded
        print >> open(ded, "w"), """AS {0}\nMP {1} {1} {0}""".format(SP,
                                                                     SIL)
        check_call(["HDMan", "-m", "-g", ded, "-w", self.words, "-n",
                    self.phons, self.taskdict, self.dictionary])
        # add sil
        print >> open(self.phons, "a"), SIL
        # add sil and projected words to self.taskdict
        print >> open(self.taskdict, "a"), "{0} {0}".format(SIL)
        # run HLEd
        led = os.path.join(self.tmp_dir, TEMP)
        print >> open(led, "w"), "EX\nIS {0} {0}\nDE {1}".format(SIL, SP)
        check_call(["HLEd", "-l", self.lab_dir, "-d", self.taskdict,
                            "-i", self.phon_mlf, led, self.word_mlf])

    def _check_aud(self, wav_list, train=False):
        """
        Check audio files, mixing down to mono and downsampling if
        necessary. Writes copy_scp and the training or testing SCP files
        """
        copy_scp = open(self.copy_scp, "a")
        check_scp = open(self.train_scp if train else self.test_scp, "w")
        i = 0
        for wav in wav_list:
            head = os.path.splitext(os.path.split(wav)[1])[0]
            mfc = os.path.join(self.aud_dir, head + ".mfc")
            w = WavFile.from_file(wav)
            if w.Fs != self.samplerate:
                new_wav = os.path.join(self.aud_dir, head + ".wav")
                logging.warning("Resampling '{}'.".format(wav))
                w.resample_bang(self.samplerate)
                w.write(new_wav)
            print >> copy_scp, '"{}" "{}"'.format(wav, mfc)
            print >> check_scp, '"{0}"'.format(mfc)
        copy_scp.close()
        check_scp.close()

    def _HCopy(self):
        """
        Compute MFCCs
        """
        check_call(["HCopy", "-C", self.HCopy_cfg,
                             "-S", self.copy_scp])

    def align(self, mlf):
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
                   [self.taskdict,
                    self.phons])

    def align_and_score(self, mlf, score):
        """
        The same as self.align(mlf), but also with a file including scores
        """
        i = 0
        call_list = ["HVite", "-a", "-m",
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
            [self.taskdict,
             self.phons]
        proc = Popen(call_list, stdout=PIPE)
        with open(score, "w") as sink:
            for line in proc.stdout:
                mch = HVITE_SCORE.match(line)  # check for score line
                if mch:
                    print >> sink, "{}\t{}".format(self.wav_list[i],
                                                   mch.group(1))
                    i += 1
        # catch any errors in decoding
        retcode = proc.wait()  # should be exhausted, but just to be sure
        if retcode != 0:
            raise CalledProcessError(retcode, call_list)


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
        # make proto
        sink = open(self.proto, "w")
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
        sink.close()
        # make vFloors
        check_call(["HCompV", "-f", str(self.HCompV_opts["F"]),
                              "-C", self.HERest_cfg,
                              "-S", self.train_scp,
                              "-M", self.cur_dir, self.proto])
        # make local macro
        # get first three lines from local proto
        sink = open(os.path.join(self.cur_dir, MACROS), "a")
        source = open(os.path.join(self.cur_dir,
                                   os.path.split(self.proto)[1]), "r")
        for _ in xrange(3):
            print >> sink, source.readline(),
        source.close()
        # get remaining lines from vFloors
        sink.writelines(open(os.path.join(self.cur_dir,
                                          VFLOORS), "r").readlines())
        sink.close()
        # make hmmdefs
        sink = open(os.path.join(self.cur_dir, HMMDEFS), "w")
        for phone in open(self.phons, "r"):
            source = open(self.proto, "r")
            # ignore
            source.readline()
            source.readline()
            # the header
            print >> sink, '~h "{}"'.format(phone.rstrip())
            # the rest
            sink.writelines(source.readlines())
            source.close()
        sink.close()

    def _check(self, ts_dir, tr_dir):
        """
        Performs checks on .wav and .lab files in the folders indicated by
        dir1 and dir2, eliminating any redundant computations.
        """
        if ts_dir == tr_dir:  # if training on testing
            (self.wav_list, lab_list) = self._lists(ts_dir)
            # check and make dictionary
            self._check_dct(lab_list)
            # inspect audio
            self._check_aud(self.wav_list)
            # IMPORTANT
            self.train_scp = self.test_scp
        else:  # otherwise
            (self.wav_list, ts_lab_list) = self._lists(ts_dir)
            (tr_wav_list, tr_lab_list) = self._lists(tr_dir)
            # check and make dictionary
            self._check_dct(ts_lab_list + tr_lab_list)
            # inspect test audio
            self._check_aud(self.wav_list)
            # inspect training audio
            self._check_aud(tr_wav_list, True)

    def _nxt_dir(self):
        """
        Get the next HMM directory
        """
        # pass on the previously new one to the old one
        self.cur_dir = self.nxt_dir
        # increment
        self.n += 1
        # compute the path for the new one
        self.nxt_dir = os.path.join(self.hmm_dir, str(self.n).zfill(3))
        # make the new directory
        os.mkdir(self.nxt_dir)

    def train(self, niter):
        """
        Perform one or more rounds of estimation
        """
        for _ in xrange(niter):
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

    def small_pause(self):
        """
        Add in a tied-state small pause model
        """
        # make a new hmmdf
        source = open(os.path.join(self.cur_dir, HMMDEFS), "r+")
        saved = ['~h "{}"\n'.format(SP)]  # store lines to append later
        # pass until we find SIL
        for line in source:
            if line.startswith('~h "{}"'.format(SIL)):
                break
        # header for silence
        saved.append("<BEGINHMM>\n<NUMSTATES> 3\n<STATE> 2\n")
        # pass until we get to "SIL""s middle state
        for line in source:
            if line == "<STATE> 3\n":
                break
        # grab "SIL""s middle state
        for line in source:
            if line == "<STATE> 4\n":
                break
            saved.append(line)
        # add in the TRANSP matrix (from VoxForge tutorial)
        saved.append("<TRANSP> 3\n")
        saved.append(" 0.0 1.0 0.0\n 0.0 0.9 0.1\n 0.0 0.0 0.0\n<ENDHMM>")
        # go to the end of the file
        source.seek(0, os.SEEK_END)
        # append all the lines to the end of the file
        source.writelines(saved)
        source.close()
        # tie the states together
        hed = os.path.join(self.tmp_dir, TEMP)
        print >> open(hed, "w"), """AT 2 4 0.2 {{{1}.transP}}
AT 4 2 0.2 {{{1}.transP}}
AT 1 3 0.3 {{{0}.transP}}
TI silst {{{1}.state[3],{0}.state[2]}}
""".format(SP, SIL)
        check_call(["HHEd", "-H", os.path.join(self.cur_dir, MACROS),
                            "-H", os.path.join(self.cur_dir, HMMDEFS),
                            "-M", self.nxt_dir, hed, self.phons])
        # FIXME this seems to not be necessary, but I"m not sure why.
        """
        # run HLEd
        sink = open(temp, "w")
        sink.write("EX\nIS {0} {0}\n".format(sil))
        sink.close()
        call(["HLEd", "-A", "-l", self.aud_dir, "-d", 
              self.taskdict, "-i", self.phon_mlf, temp, self.word_mlf])
        """
        self._nxt_dir()  # increments dirs


if __name__ == "__main__":
    # parse arguments
    argparser = ArgumentParser(prog="align.py",
                               description="Prosodylab-Aligner")
    argparser.add_argument("-c", "--configuration", default="en.yaml",
                           help="Configuration file to use")
    argparser.add_argument("-d", "--dictionary",
                           help="dictionary file to use")
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
        logging.basicConfig(format=LOGGING_FMT)
    # parse configuration file and overwrite opts with args
    try:
        source = open(args.configuration, "r")
        opts = yaml.load(source)
    except (IOError, yaml.YAMLError) as err:
        logging.error("Error reading config file '{}' ({}).".format(
                      args.configuration, err))
        exit(1)
    # can just read this from opts: it has to already be there
    phoneset = frozenset(opts["phoneset"])
    # `dictionary` will be the full path, and `opts["dictionary"]` just
    # the truncated name, since we'll copy it into the archive later
    dictionary = os.path.abspath(args.dictionary if args.dictionary
                                 else opts["dictionary"])
    (_, opts["dictionary"]) = os.path.split(dictionary)
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
    # do the model
    if args.read or args.write:
        raise NotImplementedError
    if args.align:
        args.align = os.path.abspath(args.align)
    path_to_mlf = os.path.join(args.align, ALIGN_MLF)
    if args.train:
        args.train = os.path.abspath(args.train)
        logging.info("Initializing.")
        aligner = TrainAligner(args.align, args.train, dictionary,
                               phoneset, opts["samplerate"],
                               opts["PRUNING"],
                               opts["HCopy"],
                               opts["HCompV"],
                               opts["HERest"],
                               opts["HVite"])
        logging.info("Training.")
        aligner.train(opts["epochs"])
        logging.info("Modeling silence.")
        aligner.small_pause()
        logging.info("Additional training.")
        aligner.train(opts["epochs"])
        logging.info("Realigning.")
        aligner.align(aligner.phon_mlf)
        logging.info("Final training.")
        aligner.train(opts["epochs"])
    else:
        raise NotImplementedError
    aligner.align_and_score(path_to_mlf, os.path.join(args.align,
                                                      SCORES))
    logging.info("Making TextGrids.")
    if MLF(path_to_mlf).write(args.align) < 1:
        logging.error("No paths found!")
        exit(1)
