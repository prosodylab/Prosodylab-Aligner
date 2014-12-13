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
Corpus utilities
"""


import os
import logging

from re import match
from glob import glob
from tempfile import mkdtemp
from subprocess import check_call

from .wavfile import WavFile
from .prondict import PronDict
from .utilities import opts2cfg, mkdir_p, MISSING, OOV, SIL, SP, TEMP


# regexp for inspecting phones
VALID_PHONE = r"^[^\d\s]\S*$"


def splitname(fullname):
    """
    Split a filename into directory, basename, and extension
    """
    (dirname, filename) = os.path.split(fullname)
    (basename, ext) = os.path.splitext(filename)
    return (dirname, basename, ext)


class Corpus(object):

    """
    Class representing directory of training data; once constructed, it
    is ready for training or aligning.
    """

    def __init__(self, dirname, opts):
        # temporary directories for stashing the data
        tmpdir = os.environ["TMPDIR"] if "TMPDIR" in os.environ else None
        self.tmpdir = mkdtemp(dir=tmpdir)
        self.auddir = os.path.join(self.tmpdir, "audio")
        mkdir_p(self.auddir)
        self.labdir = os.path.join(self.tmpdir, "label")
        mkdir_p(self.labdir)
        # samplerate
        self.samplerate = opts["samplerate"]
        # phoneset
        self.phoneset = frozenset(opts["phoneset"])
        for phone in self.phoneset:
            if not match(VALID_PHONE, phone):
                logging.error("Phone '{}': not /{}/.".format(phone,
                                                      VALID_PHONE))
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
        # prepare the data for processing
        (audiofiles, labelfiles) = self._lists(dirname)
        self.audiofiles = audiofiles
        self._prepare_label(labelfiles)
        self._prepare_audio(audiofiles)
        self._extract_features()

    def _lists(self, dirname):
        """
        Create lists of .wav and .lab files, detecting missing pairs.
        """
        audiofiles = glob(os.path.join(dirname, "*.wav"))
        labelfiles = glob(os.path.join(dirname, "*.lab"))
        if not audiofiles:
            logging.error("No .wav files in '{}'.".format(dirname))
            exit(1)
        elif not labelfiles:
            logging.error("No .lab files in '{}'.".format(dirname))
            exit(1)
        audiobasenames = frozenset(splitname(audiofile)[1] for
                                   audiofile in audiofiles)
        labelbasenames = frozenset(splitname(labelfile)[1] for
                                   labelfile in labelfiles)
        missing = []
        missing.extend(basename + ".wav" for basename in
                       labelbasenames - audiobasenames)
        missing.extend(basename + ".lab" for basename in
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
                (_, filename) = os.path.split(labelfile)
                phon_labfile = os.path.join(self.auddir, filename)
                word_labfile = os.path.join(self.labdir, filename)
                # header for each file in the .mlf
                print('"{}"'.format(word_labfile), file=word_mlf)
                # read in words from original .lab file
                with open(labelfile, "r") as orig_handle:
                    words = orig_handle.readline().split()
                found_words.update(words)
                # write out new wordlab
                with open(word_labfile, "w") as word_handle:
                    print("\n".join(words), file=word_handle)
                # get pronunciation and check for in-dictionary-hood
                phons = []
                for word in words:
                    try:
                        phons.extend(self.thedict[word][0])
                    except (KeyError, IndexError):
                        pass
                # write out new phonelab
                with open(phon_labfile, "w") as phon_handle:
                    print("\n".join(phons), file=phon_handle)
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
                (_, filename) = os.path.split(audiofile)
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

    def _extract_features(self):
        """
        Compute audio features
        """
        check_call(["HCopy", "-C", self.HCopy_cfg, "-S", self.audio_scp])
