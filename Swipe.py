#!/usr/bin/env python
""" Copyright (c) 2009-2011 Kyle Gorman

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
 Statistical functions based on stats.py by Gary Strangman
 Modifications kindly contributed by Josef Fruehwald

 This program is to be distributed with the C implementation of SWIPE', 
 available at the following URL:

    http://ling.upenn.edu/~kgorman/c/swipe/ """

from math import sqrt
from bisect import bisect
from subprocess import Popen, PIPE

def ss(x):
    """ compute the sum of all squared values in x """
    s = 0.
    for i in x:
        s += i * i
    return s


def mean(x):
    """ compute x's mean """
    return float(sum(x)) / len(x)
    

def var(x):
    """ compute x's variance """
    my_mean = mean(x)
    s = 0.
    for i in x:
        s += (i - my_mean) ** 2
    return s / len(x) - 1


def regress(x, y):
    """ compute the slope, intercept, and R^2 for y ~ x """
    n = float(len(x))
    if n == 0:
        raise ValueError, 'empty vector(s)'
    if n != len(y):
        raise ValueError, 'x and y must be the same length'
    x_sum = sum(x)
    y_sum = sum(y)
    r = 0 # being built up iteratively
    for (i, j) in zip(x, y):
        r += i * j
    r *= n 
    r -= (x_sum * y_sum)
    q = n * ss(x) - (x_sum ** 2)
    slope = r / q
    r /= sqrt(q * (n * ss(y) - (y_sum ** 2))) # now it's done!
    return slope, y_sum / n - slope * x_sum / n, r ** 2


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
        assert not P.stderr.readline(), 'Err: %s' % P.stderr.readlines()[-1]
        self.time = []
        self.pitch = []
        for line in P.stdout: # Data is a list of (time, pitch) pairs
            (t, p) = line.split()
            self.time.append(float(t))
            self.pitch.append(float(p))


    def __str__(self):
        return '<Swipe pitch track with %d points>' % len(self.time)


    def __len__(self):
        return len(self.time)


    def __iter__(self):
        return iter(zip(self.time, self.pitch))


    def __getitem__(self, time):
        """ Takes a time argument and gives the nearest sample """
        if self.time[0] <= 0.:
            raise ValueError, 'Time less than 0'
        i = bisect(self.time, time)
        if self.time[i] - time > time - self.time[i - 1]:
            return self.pitch[i - 1]
        else:
            return self.pitch[i]


    def time_bisect(self, tmin=None, tmax=None):
        """ not really a user class, but a helper function """
        if not tmin:
            if not tmax:
                raise ValueError, 'At least one of tmin, tmax must be defined'
            else:
                return (0, bisect(self.time, tmax))
        elif not tmax:
            return (bisect(self.time, tmin), len(self.time))
        else:
            return (bisect(self.time, tmin), bisect(self.time, tmax))


    def slice(self, tmin=None, tmax=None):
        """ slice out samples outside of times [tmin, tmax], operating inline """
        if tmin or tmax:
            (i, j) = self.time_bisect(tmin, tmax)
            self.time = self.time[i:j]
            self.pitch = self.pitch[i:j]
        else:
            raise ValueError, 'At least one of tmin, tmax must be defined'


    def mean(self, tmin=None, tmax=None):
        """ Returns pitch mean """
        if tmin or tmax:
            (i, j) = self.time_bisect(tmin, tmax)
            return mean(self.pitch[i:j])
        else:
            return mean(self.pitch)


    def var(self, tmin=None, tmax=None):
        """ Returns pitch variance """
        if tmin or tmax:
            (i, j) = self.time_bisect(tmin, tmax)
            return var(self.pitch[i:j])
        else:
            return var(self.pitch)


    def sd(self, tmin=None, tmax=None):
        """ Returns pitch standard deviation """
        return sqrt(self.var(tmin, tmax))


    def regress(self, tmin=None, tmax=None):
        """ Returns the linear regression slope, intercept, and R^2. I wouldn't
        advise using this on raw pitch, but rather the Mel frequency option in
        swipe: e.g., call Swipe(yourfilename, min, max, mel=True). The reason for
        this is that Mel frequency is log-proportional to pitch in Hertz, and I find
        that log-pitch is much closer to satisfying the normality assumption """
        if tmin or tmax:
            (i, j) = self.time_bisect(tmin, tmax)
            return regress(self.time[i:j], self.pitch[i:j])
        else:
            return regress(self.time, self.pitch)


# just some testing code
if __name__ == '__main__':
    from Swipe import Swipe
    pitch = Swipe('test.wav', 75, 500, mel=True) # you must provide a "test.wav"
    print pitch
    print pitch[.6] # pitch nearest to 600 ms
    print pitch.sd()
    print pitch.mean(.2, 5)
    print pitch.regress(.2, 5) # regression on sliced interval
