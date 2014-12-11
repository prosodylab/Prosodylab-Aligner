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
# Requires Python 3.4 or better
#
# See README.md for usage information and a tutorial.
#
# This project was funded by:
#
# FQRSC Nouvelle Chercheur NP-132516
# SSHRC Digging into Data Challenge Grant 869-2009-0004
# SSHRC Canada Research Chair 218503


from numpy import asarray
from scipy.io import wavfile
from scipy.signal import resample


class WavFile(object):

    """
    Mono-mixed wav file
    """

    def __init__(self, signal, Fs):
        self.signal = asarray(signal)
        self.Fs = Fs

    @classmethod
    def from_file(cls, filename):
        (Fs, signal) = wavfile.read(filename)
        if signal.ndim > 1:
            raise ValueError("Expected mono audio," +
                             " but '{}'".format(filename) +
                             " has {} channels.".format(signal.ndim))
        return cls(signal, Fs)

    def __repr__(self):
        return "{}(signal={!r}, Fs={!r})".format(self.__class__.__name__,
                                                 self.signal, self.Fs)

    def __len__(self):
        return len(self.signal)

    def write(self, filename):
        wavfile.write(filename, self.Fs, self.signal)

    def _resample(self, Fs_out):
        ratio = Fs_out / self.Fs
        resampled_signal = resample(self.signal, ratio * len(self))
        return resampled_signal

    def resample(self, Fs_out):
        return WavFile(self._resample(Fs_out), Fs_out)

    def resample_bang(self, Fs_out):
        self.signal = self._resample(Fs_out)
        self.Fs = Fs_out
