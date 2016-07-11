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
Aligner utilities
"""

import os
import logging

from re import match
from tempfile import mkdtemp
from shutil import copyfile, rmtree
from subprocess import check_call, Popen, CalledProcessError, PIPE

from .utilities import opts2cfg, mkdir_p, \
                       HMMDEFS, MACROS, PROTO, SP, SIL, TEMP, VFLOORS


# regexp for parsing the HVite trace
HVITE_SCORE = r".+==  \[\d+ frames\] (-\d+\.\d+)"
# in case you"re curious, the rest of the trace string is:
#     /\[Ac=-\d+\.\d+ LM=0.0\] \(Act=\d+\.\d+\)/


class Aligner(object):

    """
    Class representing an aligner, including HMM definitions and 
    configuration options
    """

    def __init__(self, opts):
        # make temporary directories to stash everything
        hmmdir = os.environ["TMPDIR"] if "TMPDIR" in os.environ else None
        self.hmmdir = mkdtemp(dir=hmmdir)
        # config options
        self.HCompV_opts = opts["HCompV"]
        self.HERest_cfg = os.path.join(self.hmmdir, "HERest.cfg")
        opts2cfg(self.HERest_cfg, opts["HERest"])
        self.HVite_opts = opts["HVite"]
        self.pruning = [str(i) for i in opts["pruning"]]
        # initialize directories
        self.epochs = 0
        self.curdir = os.path.join(self.hmmdir, str(self.epochs).zfill(3))
        mkdir_p(self.curdir)
        self.epochs += 1
        self.nxtdir = os.path.join(self.hmmdir, str(self.epochs).zfill(3))
        mkdir_p(self.nxtdir)

    def _nxtdir(self):
        """
        Get the next HMM directory
        """
        self.curdir = self.nxtdir
        self.epochs += 1
        self.nxtdir = os.path.join(self.hmmdir, str(self.epochs).zfill(3))
        mkdir_p(self.nxtdir)

    def flatstart(self, corpus):
        self.epochs = 1
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
        check_call(["HCompV", "-m",
                              "-f", str(self.HCompV_opts["F"]),
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
                print("".join(vfloors.readlines()).rstrip(), file=macros)
        # make `hmmdefs`
        with open(os.path.join(self.curdir, HMMDEFS), "w") as hmmdefs:
            with open(os.path.join(self.curdir, PROTO), "r") as proto:
                protolines = proto.readlines()[4:]
            with open(corpus.phons, "r") as phons:
                for phone in phons:
                    print('~h "{}"'.format(phone.rstrip()), file=hmmdefs)
                    print("".join(protolines).rstrip(), file=hmmdefs)

    def train(self, corpus, epochs):
        """
        Perform one or more rounds of estimation
        """
        for _ in range(epochs):
            logging.debug("Training iteration {}.".format(self.epochs))
            check_call(["HERest", "-C", self.HERest_cfg,
                        "-S", corpus.feature_scp,
                        "-I", corpus.phon_mlf,
                        "-M", self.nxtdir,
                        "-H", os.path.join(self.curdir, MACROS),
                        "-H", os.path.join(self.curdir, HMMDEFS),
                        "-t"] + self.pruning + [corpus.phons])
            self._nxtdir()

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
TI silst {{{1}.state[3],{0}.state[2]}}
""".format(SP, SIL), file=hed)
        check_call(["HHEd", "-H", os.path.join(self.curdir, MACROS),
                            "-H", os.path.join(self.curdir, HMMDEFS),
                            "-M", self.nxtdir,
                            temp, corpus.phons])
        temp = os.path.join(self.hmmdir, TEMP)
        with open(temp, "w") as led:
            print("""EX
IS {0} {0}
""".format(SIL), file=led)
        check_call(["HLEd", "-l", corpus.auddir,
                            "-d", corpus.taskdict,
                            "-i", corpus.phon_mlf,
                            temp, corpus.word_mlf])
        logging.debug("(Skipping an iteration number).")
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
                             "-I", corpus.word_mlf,] +
                             #FIXME(kg) do we want this?
                             #"-s", str(self.HVite_opts["SFAC"]), 
                             #"-t"] + self.pruning +
                   [corpus.taskdict, corpus.phons], stdout=PIPE)

    def realign(self, corpus):
        """
        Align and then overwrite `corpus.word_mlf` with the result
        """
        temp = os.path.join(self.hmmdir, TEMP)
        self.align(corpus, temp)
        copyfile(temp, corpus.word_mlf)

    def align_and_score(self, corpus, mlf, scores):
        """
        The same as `self.align`, but also generates a text file `score`
        with -log likelihood confidence scores for each audio file
        """
        proc = Popen(["HVite", "-a", "-m",
                               "-T", "1",
                               "-o", "SM",
                               "-y", "lab",
                               "-b", SIL,
                               "-i", mlf,
                               "-L", corpus.labdir,
                               "-C", self.HERest_cfg,
                               "-S", corpus.feature_scp,
                               "-H", os.path.join(self.curdir, MACROS),
                               "-H", os.path.join(self.curdir, HMMDEFS),
                               "-I", corpus.word_mlf,] +
                               #FIXME(kg) do we want this?
                               #"-s", str(self.HVite_opts["SFAC"]),
                               #"-t"] + self.pruning +
                     [corpus.taskdict, corpus.phons],
                     stdout=PIPE)
        with open(scores, "w") as sink:
            i = 0
            for line in proc.stdout:
                m = match(HVITE_SCORE, line.decode("UTF-8"))
                if m:
                    print('"{!s}",{!s}'.format(corpus.audiofiles[i],
                                               m.group(1)), file=sink)
                    i += 1
        # Popen equivalent to check_call...
        retcode = proc.wait()
        if retcode != 0:
            raise CalledProcessError(retcode, proc.args)

    def HTKbook_training_regime(self, corpus, epochs, flatstart=True):
        if flatstart:
            logging.info("Flat start training.")
            self.flatstart(corpus)
        self.train(corpus, epochs)
        logging.info("Modeling silence.")
        self.small_pause(corpus)
        logging.info("Additional training.")
        self.train(corpus, epochs)
        logging.info("Realigning.")
        self.realign(corpus)
        logging.info("Final training.")
        self.train(corpus, epochs)

    def __del__(self):
        rmtree(self.hmmdir)
