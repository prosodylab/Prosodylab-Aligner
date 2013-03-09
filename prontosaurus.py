#!/usr/bin/env python
# prontosaurus.py, v 0.5
# by Kyle Gorman <kgorman@ling.upenn.edu>
#
# Prontosaurus predicts the pronunciations of unseen words based on their 
# regular (-s, -ed, -ing) inflectional variants. It currently uses the CMU
# pronunciation dictionary ARPABET phone set and the doctests are designed for 
# the version "cmudict.0.7a".
#
# This software owes an obvious debt to the original Porter stemmer:
#
# Porter, M. 1980. An algorithm for suffix stripping. Program 14(3): 130-137. 
#
# I hope that a later version will also include base inference.
#
# The primary application of Prontosaurus is for automated alignment and 
# speech recognition, and it is an integral part of Prosodylab-Aligner:
#
# http://prosodylab.org/tools/aligner/
#
# More sophisticated grapheme-to-phoneme converters exist (e.g., Sequitur). 
# The advantage of such tools is that they have higher recall and can be
# quickly extended to languages other than English; the disadvantage is that 
# they surely have lower precision: I doubt Prontosaurus makes any erroneous
# projections.

from sys import stderr
from collections import defaultdict

## container for affixes
class Affix(object):
    """
    Container for functions associated with individual affixes:

    identify(orth): return True if orth could be affixed with said affix
    affix(pron):    return affixed version of pron
    strip(orth):    return Iterable of inferred bases
    """

    def __init__(self, identify, affix, strip):
        self.identify  = identify
        self.affix     = affix
        self.strip     = strip


## orthographic identification functions

_id_z   = lambda x: len(x) > 3 and x[-1] == 'S'
_id_d   = lambda x: len(x) > 3 and x[-1] == 'D'
_id_ing = lambda x: len(x) > 4 and x[-3:] == 'ING'


## pronunciation affixation functions
_voiceless_obstruents = ('P', 'T', 'K', 'CH', 'F', 'TH', 'S', 'SH')


def _affix_z(pron):
    if pron[-1] in ('S', 'SH', 'Z', 'ZH'):
        return pron + ['IH0', 'Z']
    elif pron[-1] in _voiceless_obstruents:
        return pron + ['S']
    else:
        return pron + ['Z']


def _affix_d(pron):
    if pron[-1] in ('T', 'D', 'CH', 'JH'):
        return pron + ['IH0', 'D']
    elif pron[-1] in _voiceless_obstruents:
        return pron + ['T']
    else:
        return pron + ['D']


_affix_ing = lambda x: x + ['IH0', 'NG']

## orthographic stripping functions, returning iterables


def _strip_z(orth):
    queries = []
    if orth[-3:-1] == 'IE': # e.g., "severity"/"severities"
        queries.append(orth[:-3] + 'Y')
    elif orth[-2] == "'": # e.g., "bathroom's"
        return [orth[:-2]] # only reasonable one
    queries.append(orth[:-1])
    return queries


def _strip_d(orth):
    queries = []
    if orth[-2] == 'E': # e.g., "point"/"pointed"
        if orth[-3] == orth[-4]: # e.g., "dog"/"dogged"
            queries.append(orth[:-3])
        queries.append(orth[:-2])
    queries.append(orth[:-1])
    return queries


def _strip_ing(orth):
    queries = []
    if orth[-4] == orth[-5]: # e.g., "dog"/"dogging"
        queries.append(orth[:-4] + 'E')
        queries.append(orth[:-4])
    queries.append(orth[:-3] + 'E')
    queries.append(orth[:-3])
    return queries


## populate affix list
RegularAffixes = [Affix(_id_z,   _affix_z,    _strip_z),
                  Affix(_id_d,   _affix_d,    _strip_d),
                  Affix(_id_ing, _affix_ing,  _strip_ing)]


class PronDict(object):
    """
    A wrapper for a normal pronunciation dictionary in the CMU dictionary 
    ARPABET style
    """
    def __init__(self, f, affixes=None):
        # affix argument is ignored for compatibility with subclass
        sink = f if hasattr(f, 'read') else open(f, 'r')
        self.d = defaultdict(list)
        for line in sink:
            if line[0] != ';': # comment
                (word, pron) = line.rstrip().split(None, 1)
                pron = pron.split()
                self.d[word].append(pron)
        sink.close()
        self.ood = set()

    def __contains__(self, key):
        return key in self.d and self.d[key] != []

    def __getitem__(self, key):
        getlist = self.d[key]
        if getlist or key:
            return getlist
        else:
            self.ood.add(key)
            raise(KeyError(key))

    def __str__(self):
        return 'PronDict({0})'.format(self.d)

    def __setitem__(self, key, value):
        self.d[key].append(value)


class BaseProjPronDict(PronDict):
    """
    A variant of the original PronDict that can project new inflectional
    variants from known bases

    ## load
    >>> pd = BaseProjPronDict('dictionary.txt', RegularAffixes)

    ## projection from observed bases (-Z, -S, -IH0 Z, -D, -T, -IH0 D, -IH0 NG)
    >>> print ' '.join(pd['STYLINGS'][0])   # observed: 'STYLING'
    S T AY1 L IH0 NG Z
    >>> print ' '.join(pd['ABROGATES'][0])  # observed: 'ABROGATE'
    AE1 B R AH0 G EY2 T S
    >>> print ' '.join(pd['CONDENSES'][0])  # observed: 'CONDENSE'
    K AH0 N D EH1 N S IH0 Z
    >>> print ' '.join(pd['SEVERITIES'][0]) # observed: 'SEVERITY'
    S IH0 V EH1 R IH0 T IY0 Z
    >>> print ' '.join(pd['COLLAGED'][0])   # observed: 'COLLAGE'
    K AH0 L AA1 ZH D
    >>> print ' '.join(pd['POGGED'][0])     # * observed: 'POG'
    P AA1 G D
    >>> print ' '.join(pd['ABSCESSED'][0])  # observed: 'ABSCESS'
    AE1 B S EH2 S T
    >>> print ' '.join(pd['EXCRETED'][0])   # observed: 'EXCRETE'
    IH0 K S K R IY1 T IH0 D
    >>> print ' '.join(pd['EXCRETING'][0])  # observed: 'EXCRETE'
    IH0 K S K R IY1 T IH0 NG
    >>> print ' '.join(pd['EXCRETING'][0])  # check to see if it takes
    IH0 K S K R IY1 T IH0 NG

    ## these tests don't work yet as base inference is not yet implemented
    ## direct base inference
    #>>> print ' '.join(pd['UNFLAG'].pop())     # * observed: 'UNFLAGGING' 
    #AH0 N F L AE1 G
    #>>> print ' '.join(pd['INFLECT'].pop())    # observed: 'INFLECTED'
    #IH0 N F L EH1 K T

    ## indirect base inference
    #>>> print pd['INFLECTING'] # observed: 'INFLECTED'
    #IH0 N F L EH1 K T IH0 NG
    """

    def __init__(self, f, affixes):
        self.affixes = affixes
        # collect known pronunciations
        self.d = defaultdict(list)
        sink = f if hasattr(f, 'read') else open(f, 'r')
        for line in sink:
            if line[0] != ';':
                (word, pron) = line.rstrip().split(None, 1)
                pron = pron.split()
                self.d[word].append(pron)
        sink.close()
        # store unknown and projected pronunciations
        self.ood = set()
        self.projected = defaultdict(list)

    def project(self, key):
        """
        Try to find a new pronunciation
        """
        # try to infer inflected form from known base
        for affix in self.affixes:
            if affix.identify(key):
                for query in affix.strip(key):
                    if query in self.d:
                        addto = self.projected[key]
                        for base_pron in self.d[query]:
                            projected = affix.affix(base_pron)
                            addto.append(projected)
                            proj_string = ' '.join(projected)
                            print >> stderr, 'Prontosaurus:',
                            print >> stderr, '{0} -> {1}'.format(key,
                                                             proj_string)
                        return True
                break # FIXME only one affix can ever match...remove otherwise
        # bomb out
        self.ood.add(key)
        return False

    def __contains__(self, key):
        if key in self.ood:
            return False
        elif key in self.d or key in self.projected:
            return True
        else:
            if self.project(key):
                return True
            else:
                return False

    def __getitem__(self, key):
        if key in self.ood:
            raise(ValueError)
        elif key in self.d:
            return self.d[key]
        elif key in self.projected:
            return self.projected[key]
        else:
            if self.project(key):
                return self.projected[key]
            else:
                raise(KeyError(key))

    def __str__(self):
        return 'BaseProjPronDict({0})'.format(self.d)


# just run tests 
if __name__ == '__main__':
    import doctest
    doctest.testmod()
