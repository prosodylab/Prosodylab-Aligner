#!/usr/bin/env python
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
 Modifications and SD and mean functions kindly contributed by Josef Fruehwald

 This program is to be distributed with the C implementation of SWIPE', 
 available at the following URL:

    http://ling.upenn.edu/~kgorman/c/swipe/ """

from bisect import bisect
from subprocess import Popen, PIPE
from stats import llinregress, mean, stdev


class Swipe:
    """ Wrapper class for SWIPE' pitch extractions """

    def __init__(self, file, pMin=100.0, pMax=600.0, s=0.3, t=0.01, mel=False, 
                                                                bin = 'swipe'):
        if mel:
            P = Popen('%s -i %s -r %f:%f -s %f -t %f -nm' % (bin, file, pMin, 
                                       pMax, s, t), shell=True,
                                           stdin=PIPE, stdout=PIPE, stderr=PIPE)
        else:
            P = Popen('%s -i %s -r %f:%f -s %f -t %f -n' % (bin, file, pMin, 
                                       pMax, s, t), shell=True,
                                           stdin=PIPE, stdout=PIPE, stderr=PIPE)
        (fin, fot, fer) = (P.stdin, P.stdout, P.stderr)
        assert not fer.readline(), 'Err: %s' % fer.readlines()[-1]
        self.data = []
        for line in fot: # Data is represented as list of (time, pitch) pairs
            (t, p) = line.split()
            self.data.append((float(t), float(p)))


    def __str__(self):
        return '<Swipe pitch track with %d points>' % len(self.data)


    def __len__(self):
        return len(self.data)


    def __iter__(self):
        return iter(self.data)


    def __getitem__(self, time):
        """ Takes a time argument and gives the nearest sample """
        assert self.data[0][0] <= time, 'Err: time < %f' % self.data[0][0]
        assert self.data[-1][0] >= time, 'Err: time > %f' % self.data[-1][0]
        index = bisect([t for (t, p) in self.data], time)
        if self.data[index][0] - time > time - self.data[index - 1][0]:
            return self.data[index - 1][1]
        else:
            return self.data[index][1]


    def slice(self, tmin, tmax):
        """ return only samples within the range [tmin, tmax] """
        i = bisect([t for (t, p) in self.data], tmin)
        j = bisect([t for (t, p) in self.data], tmax)
        return self.data[i:j]


    def bounds(self):
        """ Returns first and last time sample """
        return (self.data[0][0], self.data[-1][0]) 


    def regress(self):
        """ Returns the linear regression slope, intercept, and r^2 """
        ptch = [p for (t, p) in self.data]
        time = [t for (t, p) in self.data]
        (slope, intercept, r, t, err) = llinregress(ptch, time)
        return (slope, intercept, pow(r, 2))


    def mean(self, tmin=0, tmax=0):
        """ Returns mean pitch """
        if tmax == 0:
            ptch = [p for (t, p) in self.data]
        else:
            ptch = [p for (t, p) in self.slice(tmin, tmax)]
        return mean(ptch)

    
    def sd(self, tmin=0, tmax=0):
        """ Returns pitch standard deviation """
        if tmax == 0:
            ptch = [p for (t,p) in self.data]
        else:
            ptch = [p for (t, p) in self.slice(tmin, tmax)]
        return stdev(ptch)


# just some testing code
if __name__ == '__main__':
    from Swipe import Swipe
    (start, stop) = (.2, .6) # a region of interest
    pitch = Swipe('test.wav', 75, 500) # of course, you must provide "test.wav"
    pAt1 = pitch[.6] # get the pitch nearest to 600 ms
    (slope, intercept, r2) = pitch.regress() # regression on sliced interval
    print pAt1, slope, r2
