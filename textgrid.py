#!/usr/bin/env python
# 
# Copyright (c) 2011 Kyle Gorman, Max Bane, Morgan Sonderegger
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 
# textgrid.py
# Classes for Praat TextGrid data structures, and HTK .mlf files
# 
# Max Bane <bane@uchicago.edu>
# Kyle Gorman <kgorman@ling.upenn.edu>
# Morgan Sonderegger <morgan@cs.uchicago.edu>

"""
This module is designed for manipulation of Praat TextGrid, PointTier, and
IntervalTier files in Python. A class interface is also provided for the .mlf
files created by HTK (with HVite -o SM), and can be easily used to generate 
TextGrid files:

#>>> from textgrid import MLF
#>>> MLF('your_mlf_file.mlf').write('your_output_dir')

This reads the MLF file in 'your_mlf_file.mlf', and writes TextGrids into
the directory 'your_output_dir/'. 
"""

import re
import os.path

from bisect import bisect_left

class Point(object):
    """ 
    Represents a point in time with an associated textual mark, as stored in a
    PointInterval.

    # Point/Point comparison
    >>> foo = Point(3.0, 'foo')
    >>> bar = Point(4.0, 'bar')
    >>> foo < bar
    True
    >>> foo == Point(3.0, 'baz')
    True
    >>> bar > foo
    True

    # Point/Value comparison
    >>> foo < 4.0
    True
    >>> foo == 3.0
    True
    >>> foo > 5.0
    False

    # Point/Interval comparison
    >>> baz = Interval(3.0, 5.0, 'baz')
    >>> foo < baz
    True
    >>> foo == baz
    False
    >>> bar == baz 
    True
    """

    def __init__(self, time, mark):
        self.time = time
        self.mark = mark
    

    def __repr__(self):
        return 'Point(%r, %r)' % (self.time, self.mark)


    def __cmp__(self, other):
        """
        In addition to the obvious semantics, Point/Interval comparison is 0 
        iff the point is inside the interval (non-inclusively), if you need
        inclusive membership, use Interval.__contains__
        """
        if isinstance(other, Point):
            return cmp(self.time, other.time)
        elif isinstance(other, Interval):
            return cmp(self.time, other.minTime) + \
                   cmp(self.time, other.maxTime)
        else: # hopefully numerical
            return cmp(self.time, other)


class Interval(object):
    """ 
    Represents an interval of time, with an associated textual mark, as stored
    in an IntervalTier.

    >>> foo = Point(3.0, 'foo')
    >>> bar = Point(4.0, 'bar')
    >>> baz = Interval(3.0, 5.0, 'baz')
    >>> foo in baz
    True
    >>> 3.0 in baz
    True
    >>> bar in baz
    True
    >>> 4.0 in baz
    True
    """

    def __init__(self, minTime, maxTime, mark):
        self.minTime = minTime
        self.maxTime = maxTime
        self.mark = mark
    

    def __repr__(self):
        return 'Interval(%r, %r, %r)' % (self.minTime, self.maxTime, self.mark)


    def duration(self):
        """ 
        Returns the duration of the interval in seconds.
        """
        return self.maxTime - self.minTime


    def __cmp__(self, other):
        if isinstance(other, Interval):
            if self.overlaps(other):
                raise ValueError, '%r and %r overlap' % (self, other)
            # given that the two intervals do not overlap:
            return cmp(self.minTime, other.minTime)
        elif isinstance(other, Point):
            return cmp(self.minTime, other.time) + \
                   cmp(self.maxTime, other.time)
        else: 
            return cmp(self.minTime, other) + cmp(self.maxTime, other)


    def __eq__(self, other):
        """
        This might seem superfluous but not that a ValueError will be raised
        if you compare two intervals to each other...not anymore though
        """
        if isinstance(other, Interval):
            if self.minTime == other.minTime:
                if self.maxTime == other.maxTime:
                    return True
        elif isinstance(other, Point):
            return self.minTime < other.time < self.maxTime
        else:
            return False


    def overlaps(self, other):
        """
        Tests whether self overlaps with the given interval. Symmetric.
        How elegant: http://www.rgrjr.com/emacs/overlap.html
        """
        return other.minTime < self.maxTime and self.minTime < other.maxTime


    def __contains__(self, other):
        """
        Tests whether the given time point is contained in this interval, either
        a numeric type or a Point object.
        """
        if isinstance(other, Point):
            return self.minTime <= other.time <= self.maxTime
        else:
            return self.minTime <= other <= self.maxTime


    def bounds(self):
        return (self.minTime, self.maxTime)
    


class PointTier(object):
    """ 
    Represents Praat PointTiers (also called TextTiers) as list of Points
    (e.g., for point in pointtier). A PointTier is used much like a Python
    set in that it has add/remove methods, not append/extend methods.

    >>> foo = PointTier('foo')
    >>> foo.add(4.0, 'bar')
    >>> foo.add(2.0, 'baz')
    >>> foo
    PointTier('foo', [Point(2.0, 'baz'), Point(4.0, 'bar')])
    >>> foo.remove(4.0, 'bar')
    >>> foo.add(6.0, 'bar')
    >>> foo
    PointTier('foo', [Point(2.0, 'baz'), Point(6.0, 'bar')])
    """ 

    def __init__(self, name=None):
        self.minTime = 0.
        self.maxTime = 0.
        self.points = []
        self.name = name


    def __str__(self):
        return '<PointTier %r with %d points>' % (self.name, len(self))


    def __repr__(self):
        return 'PointTier(%r, %r)' % (self.name, self.points)


    def __iter__(self):
        return iter(self.points)
    

    def __len__(self):
        return len(self.points)
    

    def __getitem__(self, i):
        return self.points[i]


    def _fixBoundaries(self):
        if self.points:
            self.minTime = self.points[0].time
            self.maxTime = self.points[-1].time


    def __min__(self):
        return self.minTime


    def __max__(self):
        return self.maxTime


    def add(self, time, mark):
        """ 
        constructs a Point and adds it to the PointTier, maintaining order
        """
        self.addPoint(Point(time, mark))


    def addPoint(self, point):
        i = bisect_left(self.points, point)
        if i != len(self.points) and self.points[i] == point:
            raise ValueError, '%r already at this time' % self.points[i]
        self.points.insert(i, point)
        self._fixBoundaries()


    def remove(self, time, mark):
        """
        removes a constructed Point i from the PointTier
        """
        self.removePoint(Point(time, mark))


    def removePoint(self, point):
        self.points.remove(point)
        self._fixBoundaries()


    def read(self, f):
        """
        Read the Points contained in the Praat-formated PointTier/TextTier file 
        and append those tiers. f may be a file object to read from, or a 
        string naming a path for reading
        """
        source = f if isinstance(f, file) else open(f, 'r')
        source.readline() # header junk 
        source.readline()
        source.readline()
        source.readline() # min
        source.readline() # max
        for i in xrange(int(source.readline().rstrip().split()[3])):
            source.readline().rstrip() # header
            itim = float(source.readline().rstrip().split()[2])
            imrk = source.readline().rstrip().split()[2].replace('"', '') 
            self.points.append(Point(imrk, itim))
        self._fixBoundaries()


    def write(self, f):
        """
        Write the current state into a Praat-format PointTier/TextTier file. f
        may be a file object to write to, or a string naming a path for writing
        """
        sink = f if isinstance(f, file) else open(f, 'w')
        sink.write('File type = "ooTextFile"\n')
        sink.write('Object class = "TextTier"\n\n')
        sink.write('xmin = %f\n' % min(self))
        sink.write('xmax = %f\n' % max(self))
        sink.write('points: size = %d\n' % len(self))
        for (i, point) in enumerate(self.points):
            sink.write('points [%d]:\n' % i + 1)
            sink.write('\ttime = %f\n' % point.time)
            sink.write('\mark = "%s"\n' % point.mark)
        sink.close()


    def bounds(self):
        return self.minTime, self.maxTime


class PointTierFromFile(PointTier):
    """
    The same as a PointTier, but initialized from a text file
    """

    def __init__(self, f, name=None):
        self.minTime = 0.
        self.maxTime = 0.
        self.points = []
        self.name = name
        self.read(f)
        


class IntervalTier(object):
    """ 
    Represents Praat IntervalTiers as list of sequence types of Intervals 
    (e.g., for interval in intervaltier). An IntervalTier is used much like a 
    Python set in that it has add/remove methods, not append/extend methods.

    >>> foo = IntervalTier('foo')
    >>> foo.add(0.0, 2.0, 'bar')
    >>> foo.add(2.0, 2.5, 'baz')
    >>> foo
    IntervalTier('foo', [Interval(0.0, 2.0, 'bar'), Interval(2.0, 2.5, 'baz')])
    >>> foo.remove(0.0, 2.0, 'bar')
    >>> foo
    IntervalTier('foo', [Interval(2.0, 2.5, 'baz')])
    >>> foo.add(0.0, 1.0, 'bar')
    >>> foo
    IntervalTier('foo', [Interval(0.0, 1.0, 'bar'), Interval(2.0, 2.5, 'baz')])
    >>> foo.add(1.0, 3.0, 'baz')
    Traceback (most recent call last):
        ...
    ValueError: Interval(2.0, 2.5, 'baz') and Interval(1.0, 3.0, 'baz') overlap
    >>> foo.intervalContaining(2.25)
    Interval(2.0, 2.5, 'baz')
    """

    def __init__(self, name=None):
        self.minTime = 0.
        self.maxTime = 0.
        self.intervals = []
        self.name = name


    def __str__(self):
        return '<IntervalTier %r with %d points>' % (self.name, len(self))


    def __repr__(self):
        return 'IntervalTier(%r, %r)' % (self.name, self.intervals)


    def __iter__(self):
        return iter(self.intervals)


    def __len__(self):
        return len(self.intervals)


    def __getitem__(self, i):
        return self.intervals[i]


    def _fixBoundaries(self):
        if self.intervals:
            self.minTime = self.intervals[0].minTime
            self.maxTime = self.intervals[-1].maxTime


    def __min__(self):
        return self.minTime


    def __max__(self):
        return self.maxTime


    def add(self, minTime, maxTime, mark):
        self.addInterval(Interval(minTime, maxTime, mark))


    def addInterval(self, interval):
        i = bisect_left(self.intervals, interval)
        if i != len(self.intervals) and self.intervals[i] == interval:
            raise ValueError, '%r already at this span' % self.intervals[i]
        self.intervals.insert(i, interval)
        self._fixBoundaries()


    def remove(self, minTime, maxTime, mark):
        self.removeInterval(Interval(minTime, maxTime, mark))


    def removeInterval(self, interval):
        self.intervals.remove(interval)
        self._fixBoundaries()


    def intervalContaining(self, time):
        """
        Returns the interval containing the given time point, or None if the
        time point is outside the bounds of this tier. The argument can be a
        numeric type, or a Point object.
        """
        i = bisect_left(self.intervals, time) 
        if i != len(self.intervals):
            if self.intervals[i].minTime < time < self.intervals[i].maxTime: 
                return self.intervals[i]


    def read(self, f):
        """
        Read the tiers contained in the Praat-format IntervalTier file named by
        the given string, and append those tiers to self. f may be a file
        object to read from, or a string naming the path to open for reading
        """
        source = f if isinstance(f, file) else open(f, 'r')
        source.readline() # header junk 
        source.readline()
        source.readline()
        source.readline() # min
        source.readline() # max
        for i in xrange(int(source.readline().rstrip().split()[3])):
            source.readline().rstrip() # header
            imin = float(source.readline().rstrip().split()[2]) 
            imax = float(source.readline().rstrip().split()[2])
            imrk = source.readline().rstrip().split()[2].replace('"', '') # txt
            self.intervals.append(Interval(imin, imax, imrk))
        source.close()
        self._fixBoundaries()


    def write(self, f):
        """
        Write the current state into a Praat-format IntervalTier file. f may be
        a file object to write to, or a string naming a path for writing
        """
        sink = f if isinstance(f, file) else open(f, 'w')
        sink.write('File type = "ooTextFile"\n')
        sink.write('Object class = "IntervalTier"\n\n')
        sink.write('xmin = %f\n' % self.minTime)
        sink.write('xmax = %f\n' % self.maxTime)
        sink.write('intervals: size = %d\n' % len(self))
        for (i, interval) in enumerate(self.intervals):
            sink.write('intervals [%d]:\n' % (i + 1))
            sink.write('\txmin = %f\n' % interval.minTime)
            sink.write('\txmax = %f\n' % interval.maxTime)
            sink.write('\ttext = "%s"\n' % interval.mark)
        sink.close()


    def bounds(self):
        return self.minTime, self.maxTime


class IntervalTierFromFile(IntervalTier):
    """
    The same as a IntervalTier, but initialized from a text file
    """

    def __init__(self, f, name=None):
        self.minTime = 0.
        self.maxTime = 0.
        self.intervals = []
        self.name = name
        self.read(f)


class TextGrid(object):
    """ 
    Represents Praat TextGrids as list of sequence types of tiers (e.g., for
    tier in textgrid), and as map from names to tiers (e.g.,
    textgrid['tierName']). Whereas the *Tier classes that make up a TextGrid
    impose a strict ordering on Points/Intervals, a TextGrid instance is 
    given order by the user. Like a true Python list, there are append/extend
    methods for a TextGrid.

    >>> foo = TextGrid('foo')
    >>> bar = PointTier('bar')
    >>> bar.add(1.0, 'spam')
    >>> bar.add(2.75, 'eggs')
    >>> baz = IntervalTier('baz')
    >>> baz.add(0.0, 2.5, 'spam')
    >>> baz.add(2.5, 3.5, 'eggs')
    >>> foo.extend([bar, baz])
    >>> foo.append(bar) # now there are two copies of bar in the TextGrid
    >>> foo.minTime
    0.0
    >>> foo.maxTime
    3.5
    >>> foo.getFirst('bar')
    PointTier('bar', [Point(1.0, 'spam'), Point(2.75, 'eggs')])
    >>> foo.getList('bar')[1]
    PointTier('bar', [Point(1.0, 'spam'), Point(2.75, 'eggs')])
    >>> foo.getNames()
    ['bar', 'baz', 'bar']
    """

    def __init__(self, name=None):
        """
        Construct a TextGrid instance with the given (optional) name (which is
        only relevant for MLF stuff). If file is given, it is a string naming
        the location of a Praat-format TextGrid file from which to populate this
        instance.
        """
        self.minTime = 0.
        self.maxTime = 0.
        self.tiers = []
        self.name = name


    def __str__(self):
        return '<TextGrid %r with %d Tiers>' % (self.name, len(self))


    def __repr__(self):
        return 'TextGrid(%r, %r)' % (self.name, self.tiers)


    def __iter__(self):
        return iter(self.tiers)


    def __len__(self):
        return len(self.tiers)


    def __getitem__(self, i):
        """ 
        Return the ith tier
        """
        return self.tiers[i]


    def getFirst(self, tierName):
        """
        Return the first tier with the given name.
        """
        for t in self.tiers:
            if t.name == tierName:
                return t


    def getList(self, tierName):
        """
        Return a list of all tiers with the given name.
        """
        tiers = []
        for t in self.tiers:
            if t.name == tierName:
                tiers.append(t)
        return tiers


    def getNames(self):
        """
        return a list of the names of the intervals contained in this TextGrid
        """
        return [tier.name for tier in self.tiers]


    def _fixBoundaries(self):
        if self.tiers:
            self.minTime = min([tier.minTime for tier in self.tiers])
            self.maxTime = max([tier.maxTime for tier in self.tiers])


    def __min__(self):
        return self.minTime


    def __max__(self):
        return self.maxTime


    def append(self, tier):
        self.tiers.append(tier)
        self._fixBoundaries()


    def extend(self, tiers):
        self.tiers.extend(tiers)
        self._fixBoundaries()


    def pop(self, i=None):
        """
        Remove and return tier at index i (default last). Raise IndexError if
        TextGrid is empty or index is out of range.
        """
        if i:
            r = self.tiers.pop(i)
        else:
            r = self.tiers.pop()
        self._fixBoundaries()
        return r


    @staticmethod
    def _getMark(text):
        a = re.search('(\S+) (=) (".*")', text.readline().rstrip())
        return a.groups()[2][1:-1]


    def read(self, f):
        """ 
        Read the tiers contained in a Praat-format TextGrid file. f may be a
        file object to read from, or a string naming the path for reading
        """
        source = f if isinstance(f, file) else open(f, 'r')
        for i in xrange(6):
            source.readline() # header junk
        m = int(source.readline().rstrip().split()[2]) # will be self.n soon
        source.readline()
        for i in xrange(m): # loop over grids
            source.readline()
            if source.readline().rstrip().split()[2] == '"IntervalTier"': 
                inam = source.readline().rstrip().split(' = ')[1].strip('"')
                imin = float(source.readline().rstrip().split()[2])
                imax = float(source.readline().rstrip().split()[2])
                itie = IntervalTier(inam)
                for j in xrange(int(source.readline().rstrip().split()[3])):
                    source.readline().rstrip().split() # header junk
                    jmin = float(source.readline().rstrip().split()[2])
                    jmax = float(source.readline().rstrip().split()[2])
                    jmrk = self._getMark(source)
                    itie.addInterval(Interval(jmin, jmax, jmrk))
                self.append(itie) 
            else: # pointTier
                inam = source.readline().rstrip().split(' = ')[1].strip('"')
                imin = float(source.readline().rstrip().split()[2])
                imax = float(source.readline().rstrip().split()[2])
                itie = PointTier(inam)
                n = int(source.readline().rstrip().split()[3])
                for j in xrange(n):
                    source.readline().rstrip() # header junk
                    jtim = float( source.readline().rstrip().split()[2])
                    jmrk = source.readline().rstrip().split()[2][1:-1]
                    itie.addPoint(Point(jtim, jmrk))
                self.append(itie)
        source.close()


    def write(self, f):
        """
        Write the current state into a Praat-format TextGrid file. f may be a
        file object to write to, or a string naming a path to open for writing.
        """
        sink = f if isinstance(f, file) else open(f, 'w')
        sink.write('File type = "ooTextFile"\n')
        sink.write('Object class = "TextGrid"\n\n')
        sink.write('xmin = %f\n' % self.minTime)
        sink.write('xmax = %f\n' % self.maxTime)
        sink.write('tiers? <exists>\n')
        sink.write('size = %d\n' % len(self))
        sink.write('item []:\n')
        for (i, tier) in enumerate(self.tiers):
            sink.write('\titem [%d]:\n' % (i + 1))
            if tier.__class__ == IntervalTier: 
                sink.write('\t\tclass = "IntervalTier"\n')
                sink.write('\t\tname = "%s"\n' % tier.name)
                sink.write('\t\txmin = %f\n' % tier.minTime)
                sink.write('\t\txmax = %f\n' % tier.maxTime)
                sink.write('\t\tintervals: size = %d\n' % len(tier))
                for (j, interval) in enumerate(tier):
                    sink.write('\t\t\tintervals [%d]:\n' % (j + 1))
                    sink.write('\t\t\t\txmin = %f\n' % interval.minTime)
                    sink.write('\t\t\t\txmax = %f\n' % interval.maxTime)
                    sink.write('\t\t\t\ttext = "%s"\n' % interval.mark)
            else: # PointTier
                sink.write('\t\tclass = "TextTier"\n')
                sink.write('\t\tname = "%s"\n' % tier.name)
                sink.write('\t\txmin = %f\n' % min(tier))
                sink.write('\t\txmax = %f\n' % max(tier))
                sink.write('\t\tpoints: size = %d\n' % len(tier))
                for (k, point) in enumerate(tier):
                    sink.write('\t\t\tpoints [%d]:\n' % k + 1)
                    sink.write('\t\t\t\ttime = %f\n' % point.time)
                    sink.write('\t\t\t\tmark = "%s"\n' % point.mark)
        sink.close()


class TextGridFromFile(TextGrid):
    """
    The same as a TextGrid, but initialized from a text file
    """

    def __init__(self, f, name=None):
        self.minTime = 0.
        self.maxTime = 0.
        self.tiers = []
        self.name = name
        self.read(f)


class MLF(object):
    """
    Read in a HTK .mlf file generated with HVite -o SM and turn it into a list 
    of TextGrids. The resulting class can be iterated over to give one TextGrid
    at a time, or the write(prefix='') class method can be used to write all 
    the resulting TextGrids into separate files. 

    Unlike other classes, this is always initialized from a text file.
    """

    def __init__(self, f, samplerate=10e6):
        self.grids = []
        self.read(f, samplerate)


    def __iter__(self):
        return iter(self.grids)


    def __str__(self):
        return '<MLF with %d TextGrids>' % len(self)


    def __repr__(self):
        return "MLF(%r)" % self.grids


    def __len__(self):
        return len(self.grids)


    def __getitem__(self, i):
        """ 
        Return the ith TextGrid
        """
        return self.grids[i]


    def read(self, f, samplerate):
        source = f if isinstance(f, file) else open(f, 'r')
        samplerate = float(samplerate)
        source.readline() # header
        while 1: # loop over text
            name = re.match('\"(.*)\"', source.readline().rstrip())
            if name:
                name = name.groups()[0]
                grid = TextGrid(name)
                phon = IntervalTier(name='phones')
                word = IntervalTier(name='words')
                wmrk = ''
                wsrt = 0.
                wend = 0.
                while 1: # loop over the lines in each grid
                    line = source.readline().rstrip().split()
                    if len(line) == 4: # word on this baby
                        pmin = round(float(line[0]) / samplerate, 5)
                        pmax = round(float(line[1]) / samplerate, 5)
                        phon.add(pmin, pmax, line[2])
                        if wmrk:
                            word.add(wsrt, wend, wmrk)
                        wmrk = line[3]
                        wsrt = pmin
                        wend = pmax
                    elif len(line) == 3: # just phone
                        pmin = round(float(line[0]) / samplerate, 5)
                        pmax = round(float(line[1]) / samplerate, 5)
                        phon.add(pmin, pmax, line[2])
                        wend = pmax
                    else: # it's a period
                        word.add(wsrt, wend, wmrk)
                        self.grids.append(grid)
                        break
                grid.append(phon)
                grid.append(word)
            else:
                source.close()
                break


    def write(self, prefix=''):
        """ 
        Write the current state into Praat-formatted TextGrids. The filenames
        that the output is stored in are taken from the HTK label files. If 
        a string argument is given, then the any prefix in the name of the 
        label file (e.g., "mfc/myLabFile.lab"), it is truncated and files are 
        written to the directory given by the prefix. An IOError will result
        if the folder does not exist. 
        """
        for grid in self.grids:
            (junk, tail) = os.path.split(grid.name)
            (root, junk) = os.path.splitext(tail)
            grid.write(open(os.path.join(prefix, root + '.TextGrid'), 'w'))


if __name__ == '__main__':
    import doctest
    doctest.testmod()
