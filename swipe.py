""" Copyright (c) 2009 Kyle Gorman

 Permission is hereby granted, free of charge, to any person obtaining a copy
 of this software and associated documentation files (the "Software"), to deal
 in the Software without restriction, including without limitation the rights
 to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 copies of the Software, and to permit persons to whom the Software is
 furnished to do so, subject to the following conditions:

 The above copyright notice and this permission notice shall be included in
 all copies or substantial portions of the Software.

 THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
 THE SOFTWARE.

 SWIPE' wrapper
 Kyle Gorman <kgorman@ling.upenn.edu>

 This program is to be distributed with the C implementation of SWIPE', 
 available at the following URL:

    http://ling.upenn.edu/~kgorman/c/swipe/ """

from os import popen3
from bisect import bisect
from stats import llinregress

class swipe:
    """ Wrapper class for SWIPE' pitch extractions """

    def __init__(self, file, pMin = 100.0, pMax = 600.0, s = 0.3, t = 0.01, 
                                                mel = False, bin = 'swipe'):
        fin = ''
        fot = ''
        fer = ''
        if mel:
            (fin, fot, fer) = popen3('%s -i %s -r %f:%f -s %f -t %f -nm' % 
                                                (bin, file, pMin, pMax, s, t))
        else:
            (fin, fot, fer) = popen3('%s -i %s -r %f:%f -s %f -t %f -n' % 
                                                (bin, file, pMin, pMax, s, t))
        assert not fer.readline(), 'Err: %s' % fer.readlines()[-1]
        self.__data = []
        for line in fot: # Data is represented as list of (time, pitch) pairs
            (t, p) = line.split()
            self.__data.append((float(t), float(p)))


    def __str__(self):
        return '<swipe pitch extraction with %d points>' % len(self.__data)


    def __len__(self):
        return len(self.__data)


    def __iter__(self):
        return iter(self.__data)


    def __getitem__(self, time):
        """ Takes a time argument and gives the nearest sample """
        assert self.__data[0][0] <= time, 'Err: time < %f' % self.__data[0][0]
        assert self.__data[-1][0] >= time, 'Err: time > %f' % self.__data[-1][0]
        index = bisect([t for (t, p) in self.__data], time)
        if self.__data[index][0] - time > time - self.__data[index - 1][0]:
            return self.__data[index - 1][1]
        else:
            return self.__data[index][1]


    def slice(self, tmin, tmax):
        """ Inline, chop out samples outside the range [tmin, tmax] """
        i = bisect([t for (t, p) in self.__data], tmin)
        j = bisect([t for (t, p) in self.__data], tmax)
        self.__data = self.__data[i:j]


    def bounds(self):
        """ Returns first and last time sample """
        return (self.__data[0][0], self.__data[-1][0]) 


    def regress(self):
        """ Returns the linear regression slope, intercept, and r^2 """
        voiced = [(t, p) for (t, p) in self.__data if p > 0.0]
        ptch = [p for (t, p) in voiced]
        time = [t for (t, p) in voiced]
        (slope, intercept, r, t, err) = llinregress(ptch, time)
        return (slope, intercept, pow(r, 2))
