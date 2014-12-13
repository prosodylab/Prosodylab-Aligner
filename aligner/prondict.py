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
Pronunciation dictionary utilities
"""


import logging

from collections import defaultdict


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

    def __init__(self, filename, phoneset):
        # build up dictionary
        with open(filename, "r") as source:
            self.d = defaultdict(list)
            for (i, word, pron) in PronDict.pronify(source):
                for ph in pron:
                    if ph not in phoneset:
                        logging.error("Unknown phone '{}' in dictionary '{}' (ln. {}).".format(ph, filename, i))
                        exit(1)
                self.d[word].append(pron)
        # for later...
        self.oov = set()

    def __contains__(self, key):
        return key in self.d and self.d[key] != []

    def __getitem__(self, key):
        getlist = self.d[key]
        if getlist:
            return getlist
        else:
            self.oov.add(key)
            raise KeyError(key)

    def __repr__(self):
        return "PronDict({})".format(self.d)

    def __setitem__(self, key, value):
        self.d[key].append(value)
