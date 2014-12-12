from __future__ import division

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
