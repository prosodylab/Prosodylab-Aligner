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

def split_filename(fullname):
    """
    Split a filename into directory, basename, and extension
    """
    (dirname, filename) = os.path.split(fullname)
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
        self._prepare(args.align) # perform checks on data

    def _prepare(self, dirname):
        """
        Performs checks on .wav and .lab files in the folder indicated by
        ts_dir. If any problem arises, an error results.
        """
        (wavfiles, labfiles) = self._lists(dirname)
        self._prepare_lab(labfiles)
        self._prepare_wav(wavfiles)
        self._HCopy()

    def _lists(self, dirname):
        """
        Create lists of .wav and .lab files, detecting missing pairs.
        """
        wavfiles = glob(os.path.join(dirname), "*.wav")
        labfiles = glob(os.path.join(dirname), "*.lab")
        if not wavfiles:
            logging.error("Found no .wav files in directory" +
                          " '{}'.".format(dirname))
            exit(1)
        elif labfiles:
            logging.error("Found no .lab files in directory" +
                          " '{}'.".format(dirname))
            exit(1)
        wavbasenames = frozenset(bname for (_, bname, _) in wavfiles)
        labbasenames = frozenset(bname for (_, bname, _) in labfiles)
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
        return (wavfiles, labfiles)

    def _prepare_lab(self, labfiles):
        """
        Check label files against dictionary, and construct new .lab
        and .mlf files
        """
        found_words = set()
        with open(self.word_mlf, "w") as word_mlf:
            print("#!MLF!#", file=word_mlf)
            for labfile in labfiles:
                (dirname, filename) = os.path.split(labfile)
                word_labfile = os.path.join(self.labdir, filename)
                phon_labfile = os.path.join(self.auddir, filename)
                # header for each file in the .mlf
                print('"{}"'.format(word_labfile), file=word_mlf)
                # read in words from original .lab file
                with open(labfile, "r") as orig_handle:
                    words = [SIL] + lab_handle.readline().split() + [SIL]
                # write out new wordlab
                with open(word_labfile, "w") as word_handle:
                    print(" ".join(words), file=word_handle)
                # get pronunciation and check for in-dictionary-hood
                phons = [SIL]
                for word in words:
                    try:
                        phons.extend(self.thedict[word][0])
                    except KeyError as error:
                        pass
                phons.append(SIL)
                # write out new phonelab
                with open(phon_labfile, "r") as phon_handle:
                    print(" ".join(phons), file=phon_handle)
                # tail of each MLF entry
                print(".", word_mlf)
        # report and die if OOV words are found
        if self.thedict.oov:
            with open(OOV, "w") as oov:
                print("\n".join(sorted(self.thedict.oov)), file=oov)
            logging.error("OOV word(s): see '{}'.".format(OOV))
            exit(1)
        # make words
        with open(self.words, "w") as words:
            print("\n".join(words), file=word)
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
        # add silence to phone list
        with open(self.phons, "a") as phons:
            print(SIL, file=phons)
        # run HLEd
        with open(temp, "w") as led:
            print("EX\nIS {0} {0}\nDE {1}".formt(SIL, SP), file=led)
        check_call(["HLEd", "-l", self.labdir,
                            "-d", self.taskdict,
                            "-i", self.phon_mlf,
                            temp,
                            self.word_mlf])

    def _prepare_wav(self, wavfiles):
        """
        Check audio files, downsampling if necessary, creating `copy.scp`
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

    def align(self, dirname):
        """
        Align using the models in self.cur_dir and MLF to path
        """
        check_call(["HVite", "-a", "-m",
                             "-o", "SM",
                             "-y", "lab",
                             "-b", SIL,
                             "-i", mlf,
                             "-L", self.labdir,
                             "-C", self.HERest_cfg,
                             "-S", self.test_scp,
                             "-H", os.path.join(self.cur_dir, MACROS),
                             "-H", os.path.join(self.cur_dir, HMMDEFS),
                             "-I", self.word_mlf,
                             "-s", str(self.HVite_opts["SFAC"]),
                             "-t"] + self.pruning +
                             [self.taskdict, self.phons])

    def align_and_score(self, dirname):
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
                    print("{}\t{}".format(self.wavlist[i], m.group(1)),
                          file=sink)
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

    def _subclass_specific_init(self, args):
        """
        Performs subclass-specific initialization operations
        """
        if not args.train:
            raise ValueError
        self._prepare(args.train)
        # create the next HMM directory
        self.n = 0
        self.curdir = os.path.join(self.hmmdir, str(self.n).zfill(3))
        # make the first directory
        os.mkdir(self.curdir)
        # increment
        self.n = + 1
        # compute the path for the new one
        self.nxtdir = os.path.join(self.hmmdir, str(self.n).zfill(3))
        # make the new directory
        os.mkdir(self.nxtdir)  # from now on, just call self._nxt_dir()
        # make `proto`
        with open(self.proto, "w") as proto:
            # FIXME this is highly specific to the default acoustic 
            # features, but figuring out the number of means and variances
            # needed from the HCopy configuration file is not trivial.
            means = " ".join(["0.0" for _ in xrange(39)])
            varg = " ".join(["1.0" for _ in xrange(39)])
            print("""~o <VECSIZE> 39 <MFCC_D_A_0>
    ~h "proto"
<BEGINHMM>
<NUMSTATES> 5""", file=proto)
            for i in xrange(2, 5):
                print("<STATE> {}\n<MEAN> 39\n{}".format(i, means), 
                      file=proto)
                print("<VARIANCE> 39\n{}".format(varg), file=proto)
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
                              "-S", self.train_scp,
                              "-M", self.curdir, self.proto])
        # make `macros`
        # get first three lines from local proto
        with open(os.path.join(self.curdir, MACROS), "a") as macros:
            with open(os.path.join(self.curdir, 
                      os.path.split(self.proto)[1]), "r") as proto:
                for _ in xrange(3):
                    print(proto.readline().strip(), file=macros)
            # get remaining lines from `vFloors`
            with open(os.path.join(self.cur_dir, VFLOORS), "r") as vfloors:
                macros.writelines(vfloors.readlines())
        # make `hmmdefs`
        with open(os.path.join(self.cur_dir, HMMDEFS), "w") as hmmdefs:
            with open(self.proto, "r") as proto:
                protolines = proto.readlines()[2:]
            with open(self.phons, "r") as phons:
                for phone in phons:
                    print('~h "{}"'.format(phone.rstrip()), file=hmmdefs)
                    hmmdefs.writelines(protolines)
        # FIXME what to do here to make this work?
        #if args.align and args.train != args.align:
        #    self._prepare(args.align)

    def _nxtdir(self):
        """
        Get the next HMM directory
        """
        self.curdir = self.nxtdir
        self.n += 1
        self.nxtdir = os.path.join(self.hmmdir, str(self.n).zfill(3))
        os.mkdir(self.nxtdir)

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
        # make new hmmdef 
        saved = ['~h "{}"\n'.format(SP)]
        with open(os.path.join(curdir, HMMDEFS), "r+") as hmmdefs:
            # find SIL
            for line in hmmdefs:
                if line.startswith('~h "{}"'.format(SIL)):
                    break
            saved.append("<BEGINHMM>\n<NUMSTATES 3\n<STATE 2\n")
            # pass until we get to SIL's middle state
            for line in hmmdefs:
                if line.startswith("<STATE> 4"):
                    break
            saved.append(line)
            # add in the TRANSP matrix
            saved.extend("<TRANSP> 3", " 0.0 1.0 0.0", " 0.0 0.9 0.1",
                          " 0.0 0.0 0.0", "<ENDHMM>")
            # write all the lines to the end of `hmmdefs`
            hmmdefs.seek(0, os.SEEK_END)
            hmmdefs.writelines(saved)
        # tie states together
        temp = os.path.join(self.tmpdir, TEMP)
        with open(temp, "w") as hed:
            print("""AT 2 4 0.2 {{{1}.transP}}
AT 4 2 0.2 {{{1}.transP}}
AT 1 3 0.3 {{{0}.transP}}
TI silst {{{1}.state[3],{0}.state[2]}}""".format(SP, SIL), file=hed)
        check_call(["HHEd", "-H", os.path.join(self.curdir, MACROS),
                            "-H", os.path.join(self.curdir, HMMDEFS),
                            "-M", self.nxtdir, 
                            temp, self.phons])
        # FIXME abandoned code for running HLEd. I don't quite remember 
        # what this is good for (perhaps inserting initial silence? that's
        # not necessary anymore, as I start the models like that), but 
        # I'm going to keep it around for a while longer - KG, 2014-12-11
        #with open(TEMP, "w") as led:
        #    print("EX\nIS {0} {0}\n".format(SIL), file=led)
        #check_call(["HLEd", "-A", 
        #                    "-l", self.auddir,
        #                    "-d", self.taskdir,
        #                    "-i", self.phon_mlf,
        #                    TEMP, self.word_mlf])
        # /FIXME
        self._nxtdir()


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
