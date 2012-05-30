#!/usr/bin/python -B
# 
# Copyright (c) 2011 Kyle Gorman, Michael Wagner
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
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# 
# align.py: text/speech alignment for speech production experiments
# Kyle Gorman <kgorman@ling.upenn.edu>, Michael Wagner <chael@mcgill.ca>
# 
# Requires Python 2.5-2.7; not compatible with earlier versions or Python 3.
# 
# See README.md for usage information and a tutorial.
# 
# This project was funded by: 
# 
# FQRSC Nouvelle Chercheur NP-132516
# SSHRC Digging into Data Challenge Grant 869-2009-0004
# SSHRC Canada Research Chair 218503

from __future__ import with_statement        # compatible with python 2.5 and later

import os
import re
import wave

from glob import glob      
from bisect import bisect
from shutil import rmtree
from tempfile import mkdtemp
from sys import argv, stderr, exit
from collections import defaultdict
from getopt import getopt, GetoptError
from subprocess import call, Popen, PIPE

# should be in the current directory
from textgrid import MLF
# http://github.com/kylebgorman/textgrid.py/
from prontosaurus import PronDict, BaseProjPronDict, RegularAffixes
# http://github.com/kylebgorman/prontosaurus/

### GLOBAL VARS
# You can change these if you know HTK well

sp        = 'sp'
sil       = 'sil'
temp      = 'temp'
macro     = 'macros'
hmmdf     = 'hmmdefs'
vFloors   = 'vFloors'
unpaired  = 'unpaired.txt'
outofdict = 'outofdict.txt'

# string constants for call()
f       = str(0.01)
pruning = [str(i) for i in (250.0, 150.0, 2000.0)]

# hidden, but useful files
align_mlf  = '.ALIGN.mlf'
scores_txt = '.SCORES.txt'

# regexp for parsing the HVite trace
HVite_score = re.compile('.+==  \[\d+ frames\] (-\d+\.\d+)')
# the rest of the string is: '\[Ac=-\d+\.\d+ LM=0.0\] \(Act=\d+\.\d+\)'

# divisors of 1e7, truncated on either end, to help pick out good samplerates
SRs = [4000, 8000, 10000, 12500, 15625, 16000, 20000, 25000, 31250, 40000, 
       50000, 62500, 78125, 80000, 100000, 125000, 156250, 200000]

### GENERIC FUNCTIONS

def error(msg, *args):
    """
    Raises an error in msg, using printf-like args, then exits
    """
    stderr.write("""
align.py: Forced alignment with HTK and SoX
Kyle Gorman <kgorman@ling.upenn.edu> and Michael Wagner <chael@mcgill.ca>

USAGE: ./align.py [OPTIONS] data_to_be_aligned/

Option              Function

-a                  Perform speaker adaptation,
                    w/ or w/o prior training
-d dictionary       specify a dictionary file       [default: dictionary.txt]
-h                  Display this message
-m                  List files containing 
                    out-of-dictionary words
-n n                Number of training iterations   [default: 4]
                    for each step of training
-p                  Guess unseen words with base
                    projection (CMU English only)
-s samplerate (Hz)  Samplerate for models           [default: 8000]
                    (NB: available only with -t)
-t training_data/   Perform model training
-u                  Support for UTF-8 and UTF-16
                    label files

""")
    exit('Error: ' + msg.format(*args))

def resolve(path):
    """
    Returns path string with user/tilde and environmental variables converted
    """
    return os.path.expandvars(os.path.expanduser(path))


### CLASSES

class Aligner(object):
    """
    Basic class for performing alignment, using Montreal English lab speech 
    models shipped with this package and stored in the directory MOD/.  
    """

    def __init__(self, ts_dir, tr_dir, dictionary, sr, ood_mode, use_baseproj):
        ## class variables
        self.sr = sr
        self.has_sox = self._has_sox()
        # get a temporary directory to stash everything
        arg = os.environ['TMPDIR'] if 'TMPDIR' in os.environ else None
        self.tmp_dir = mkdtemp(dir=arg)
        # make subdirectories
        self.aud_dir = os.path.join(self.tmp_dir, 'DAT') # AUD dir
        os.mkdir(self.aud_dir)
        self.lab_dir = os.path.join(self.tmp_dir, 'LAB') # LAB dir
        os.mkdir(self.lab_dir)
        self.hmm_dir = os.path.join(self.tmp_dir, 'HMM') # HMM dir
        os.mkdir(self.hmm_dir)
        ## dictionary reps
        self.dictionary = dictionary     # string where dict can be found
        if use_baseproj:
            self.the_dict = BaseProjPronDict(dictionary, RegularAffixes)
        else:
            self.the_dict = PronDict(dictionary)
        self.the_dict['sil'] = 'sil'
        # lists
        self.words = os.path.join(self.tmp_dir, 'words')
        self.phons = os.path.join(self.tmp_dir, 'phones')
        # HMMs
        self.proto = os.path.join(self.tmp_dir, 'proto')
        # task dictionary
        self.taskdict = os.path.join(self.tmp_dir, 'taskdict')
        # SCP files
        self.copy_scp = os.path.join(self.tmp_dir, 'copy.scp')
        self.test_scp = os.path.join(self.tmp_dir, 'test.scp')
        self.train_scp = os.path.join(self.tmp_dir, 'train.scp') # empty often
        # CFG
        self.cfg = os.path.join(self.tmp_dir, 'cfg')
        # MLFs
        self.pron_mlf = os.path.join(self.tmp_dir, 'pron.mlf')
        self.word_mlf = os.path.join(self.tmp_dir, 'words.mlf')
        self.phon_mlf = os.path.join(self.tmp_dir, 'phones.mlf')
        # other options
        self.ood_mode = ood_mode
        # initializing
        self._subclass_specific_init(ts_dir, tr_dir)

    def _subclass_specific_init(self, ts_dir, tr_dir):
        """
        Performs subclass-specific initialization operations
        """
        ## perform checks on data
        self._check(ts_dir)
        ## make audio copies
        self._HCopy()
        ## where trained models can be found...
        self.cur_dir = tr_dir
    
    def _has_sox(self):
        """
        Check if sox is in the user's PATH
        """
        for path in os.environ['PATH'].split(os.pathsep):
            fpath = os.path.join(path, 'sox')
            if os.path.exists(fpath) and os.access(fpath, os.X_OK):
                return True
        return False

    def _check(self, ts_dir):
        """
        Performs checks on .wav and .lab files in the folder indicated by 
        ts_dir. If any problem arises, an error results.
        """
        ## check for missing, unpaired data
        (self.wav_list, lab_list) = self._lists(ts_dir)
        ## check dictionary
        self._check_dct(lab_list)
        ## check audio
        self._check_aud(self.wav_list)

    def _lists(self, path):
        """
        Checks that the .wav and .lab files are all paired. An error is raised
        if they are not, and the unpaired data are written to the file pointed 
        to by the string unpaired. Returns the tupel (wav_list, lab_list)
        """
        # glob together the list of source data
        wav_list = glob(os.path.join(os.path.realpath(path), '*.wav'))
        lab_list = glob(os.path.join(os.path.realpath(path), '*.lab'))
        if len(wav_list) < 1: # broken
            error('Directory {0} has no .wav files', path)
        else:
            unpaired_list = []
            for lab in lab_list:
                wav = os.path.splitext(lab)[0] + '.wav' # expected...
                if not os.path.exists(wav):
                    unpaired_list.append(wav)
            for wav in wav_list:
                lab = os.path.splitext(wav)[0] + '.lab' # expected...
                if not os.path.exists(lab):
                    unpaired_list.append(lab)
            if unpaired_list:
                sink = open(unpaired, 'w')
                for path in unpaired_list:
                    sink.write('{0}\n'.format(path))
                error('Missing .wav or .lab files; see {0}', unpaired)
        return (wav_list, lab_list)

    def _check_dct(self, lab_list):
        """
        Checks the label files to confirm that all words are found in the 
        dictionary, while building new .lab and .mlf files silently

        TODO: add checks that the phones are also valid
        """
        found_words = set()
        with open(self.word_mlf, 'w') as word_mlf:
            ood = defaultdict(list)
            print >> word_mlf, '#!MLF!#'
            for lab in lab_list:
                lab_name = os.path.split(lab)[1]
                # new lab file at the phone level, in self.aud_dir
                phon_lab = open(os.path.join(self.aud_dir, lab_name), 'w')
                # new lab file at the word level, in self.lab_dir
                word_lab = open(os.path.join(self.lab_dir, lab_name), 'w')
                # .mlf headers
                print >> word_mlf, '"{0}"'.format(word_lab.name)
                # sil
                print >> phon_lab, sil
                # look up words
                for word in open(lab, 'r').readline().rstrip().split():
                    if word in self.the_dict:
                        found_words.add(word)
                        print >> phon_lab, '\n'.join(self.the_dict[word][0])
                        word_lab.write('{0} '.format(word))
                        print >> word_mlf, word
                    else:
                        ood[word].append(lab)
                print >> phon_lab, sil
                print >> word_mlf, '.'
                phon_lab.close()
                word_lab.close()
        ## now complain if any found
        if ood:
            with open(outofdict, 'w') as sink:
                if self.ood_mode:
                    for (word, flist) in ood.iteritems():
                        print >> sink, '{0}\t{1}'.format(word, ' '.join(flist))
                else:
                    for word in ood:
                        print >> sink, word
            error('Out of dictionary word(s), see {0}', outofdict)
        ## make word
        open(self.words, 'w').write('\n'.join(found_words))
        ## run HDMan
        ded = os.path.join(self.tmp_dir, temp)
        open(ded, 'w').write("""AS {0}\nMP {1} {1} {0}""".format(sp, sil))
        call(['HDMan', '-m', '-g', ded, '-w', self.words, '-n', self.phons, 
                                              self.taskdict, self.dictionary])
        # add sil
        print >> open(self.phons, 'a'), '{0}'.format(sil)
        ## add sil and projected words to self.taskdict
        with open(self.taskdict, 'a') as sink:
            print >> sink, '{0} {1}'.format(sil, sil)
            if hasattr(self.the_dict, 'projected'):
                for (key, pronlist) in self.the_dict.projected.iteritems():
                    for pron in pronlist:
                        print >> sink, '{0} {1}'.format(key, 
                                       ' '.join(pron + ['sp']))
        ## run HLEd
        led = os.path.join(self.tmp_dir, temp)
        open(led, 'w').write('EX\nIS {1} {1}\nDE {0}\n'.format(sp, sil))
        call(['HLEd', '-l', self.lab_dir, '-d', self.taskdict, '-i', 
                                            self.phon_mlf, led, self.word_mlf])

    def _check_aud(self, wav_list, training=False):
        """
        Check audio files, mixing down to mono and the correct sample rate if
        necessary. copy_scp and the training or testing SCP files are written.
        """
        copy_scp = open(self.copy_scp, 'a')
        check_scp = open(self.train_scp if training else self.test_scp, 'w')
        i = 0
        if self.has_sox:
            for wav in wav_list:
                head = os.path.splitext(os.path.split(wav)[1])[0]
                mfc = os.path.join(self.aud_dir, head + '.mfc')
                w = wave.open(wav, 'r')
                pids = [] # pids
                if (w.getframerate() != self.sr) or (w.getnchannels() > 1):
                    new_wav = os.path.join(self.aud_dir, head + '.wav')
                    pids.append(Popen(['sox', '-G', wav, '-b', '16', new_wav,                                         'remix', '-', 'rate', str(self.sr), 
                                       'dither', '-s'], stderr=PIPE))
                    wav = new_wav
                for pid in pids: # "join"
                    pid.wait()
                copy_scp.write('{0} {1}\n'.format(wav, mfc))
                check_scp.write('{0}\n'.format(mfc))
                w.close()
        else:
            for wav in wav_list:
                head = os.path.splitext(wav)[0]
                mfc = os.path.join(self.aud_dir, head + '.mfc')
                w = wave.open(wav, 'r')
                if (w.getframerate() != self.sr) or (w.getnchannels() != 1):
                    error('File {0} requires resampling but Sox not found', w)
                copy_scp.write('{0} {1}\n'.format(wav, mfc))
                check_scp.write('{0}\n'.format(mfc))
                w.close()
        copy_scp.close()
        check_scp.close()

    def _HCopy(self):
        """
        Compute MFCCs
        """
        # write a CFG for extracting MFCCs
        open(self.cfg, 'w').write("""SOURCEKIND = WAVEFORM
SOURCEFORMAT = WAVE
TARGETRATE = 100000.0
TARGETKIND = MFCC_D_A_0
WINDOWSIZE = 250000.0
PREEMCOEF = 0.97
USEHAMMING = T
ENORMALIZE = T
CEPLIFTER = 22
NUMCHANS = 20
NUMCEPS = 12""")
        call(['HCopy', '-C', self.cfg, '-S', self.copy_scp])
        # write a CFG for what we just built
        open(self.cfg, 'w').write("""TARGETRATE = 100000.0
TARGETKIND = MFCC_D_A_0
WINDOWSIZE = 250000.0
PREEMCOEF = 0.97
USEHAMMING = T
ENORMALIZE = T
CEPLIFTER = 22
NUMCHANS = 20
NUMCEPS = 12""")

    def align(self, mlf):
        """
        Align using the models in self.cur_dir and MLF to path
        """
        call(['HVite', '-a', '-m', '-y', 'lab', '-o', 'SM', '-b', sil, 
                       '-i', mlf, '-L', self.lab_dir, 
                       '-C', self.cfg, '-S', self.test_scp,
                       '-H', os.path.join(self.cur_dir, macro),
                       '-H', os.path.join(self.cur_dir, hmmdf),
                       '-I', self.word_mlf, '-t'] + pruning + 
                       [self.taskdict, self.phons])

    def align_and_score(self, mlf, score):
        """
        The same as self.align(mlf), but also with a file including scores
        """
        i = 0
        sink = open(score, 'w')
        for line in Popen(['HVite', '-T', '1', '-a', '-m', '-y', 'lab', 
                       '-o', 'SM', '-b', sil, '-i', mlf, '-L', self.lab_dir,
                       '-C', self.cfg, '-S', self.test_scp,
                       '-H', os.path.join(self.cur_dir, macro),
                       '-H', os.path.join(self.cur_dir, hmmdf),
                       '-I', self.word_mlf, '-t'] + pruning + 
                       [self.taskdict, self.phons], stdout=PIPE).stdout:
            mch = HVite_score.match(line) # check for score line
            if mch:
                sink.write('{0}\t{1}\n'.format(self.wav_list[i], mch.group(1)))
                i += 1
        sink.close()

    def __del__(self):
        """
        Destroys the temp directory on the way out
        """
        rmtree(self.tmp_dir)


class TrainAligner(Aligner):
    """
    This inherits the align() and data prep methods from Align, but also
    supports train(), small_pause(), and realign() for building your own
    models
    """
        
    def _subclass_specific_init(self, ts_dir, tr_dir):
        """
        Performs subclass-specific initialization operations
        """
        ## perform checks on data
        self._check(ts_dir, tr_dir)
        ## run HCopy
        self._HCopy()
        ## create the next HMM directory
        self.n = 0
        self.cur_dir = os.path.join(self.hmm_dir, str(self.n).zfill(3))
        # make the first directory
        os.mkdir(self.cur_dir)
        # increment
        self.n =+ 1
        # compute the path for the new one
        self.nxt_dir = os.path.join(self.hmm_dir, str(self.n).zfill(3))
        # make the new directory
        os.mkdir(self.nxt_dir) # from now on, can just call self._nxt_dir()
        ## make proto
        sink = open(self.proto, 'w')
        means = ' '.join(['0.0' for i in xrange(39)])
        varg  = ' '.join(['1.0' for i in xrange(39)])
        sink.write("""~o <VECSIZE> 39 <MFCC_D_A_0>
~h "proto"
<BEGINHMM>
<NUMSTATES> 5
""")
        for i in xrange(2, 5):
            sink.write('<STATE> {0}\n<MEAN> 39\n{1}\n'.format(i, means))
            sink.write('<VARIANCE> 39\n{0}\n'.format(varg))
        sink.write("""<TRANSP> 5
 0.0 1.0 0.0 0.0 0.0
 0.0 0.6 0.4 0.0 0.0
 0.0 0.0 0.6 0.4 0.0
 0.0 0.0 0.0 0.7 0.3
 0.0 0.0 0.0 0.0 0.0
<ENDHMM>\n""")
        sink.close()
        ## make vFloors
        call(['HCompV', '-f', str(f), '-C', self.cfg, '-S', self.train_scp,
                                      '-M', self.cur_dir, self.proto])
        ## make local macro 
        # get first three lines from local proto
        sink = open(os.path.join(self.cur_dir, macro), 'a')
        source = open(os.path.join(self.cur_dir, 
                      os.path.split(self.proto)[1]), 'r')
        for i in xrange(3):
            sink.write(source.readline())
        source.close()
        # get remaining lines from vFloors
        sink.writelines(open(os.path.join(self.cur_dir, 
                                          vFloors), 'r').readlines())
        sink.close()
        ## make hmmdefs
        sink = open(os.path.join(self.cur_dir, hmmdf), 'w')
        for phone in open(self.phons, 'r'):
            source = open(self.proto, 'r') 
            # ignore
            source.readline() 
            source.readline() 
            # the header
            sink.write('~h "{0}"\n'.format(phone.rstrip()))
            # the rest
            sink.writelines(source.readlines())
            source.close()
        sink.close()

    def _check(self, ts_dir, tr_dir):
        """
        Performs checks on .wav and .lab files in the folders indicated by 
        dir1 and dir2, combining them to eliminate any redundant computations.
        """
        if ts_dir == tr_dir: # if training on testing
            (self.wav_list, lab_list) = self._lists(ts_dir)
            ## check and make dictionary
            self._check_dct(lab_list)
            ## inspect audio
            self._check_aud(self.wav_list)
            ## IMPORTANT
            self.train_scp = self.test_scp
        else: # otherwise
            (self.wav_list, ts_lab_list) = self._lists(ts_dir)
            (tr_wav_list, tr_lab_list) = self._lists(tr_dir)
            ## check and make dictionary
            self._check_dct(ts_lab_list + tr_lab_list)
            ## inspect test audio
            self._check_aud(self.wav_list)
            ## inspect training audio
            self._check_aud(tr_wav_list, True)

    def _nxt_dir(self):
        """
        Get the next HMM directory
        """
        # pass on the previously new one to the old one
        self.cur_dir = self.nxt_dir
        # increment
        self.n += 1
        # compute the path for the new one
        self.nxt_dir = os.path.join(self.hmm_dir, str(self.n).zfill(3))
        # make the new directory
        os.mkdir(self.nxt_dir)
            
    def train(self, niter):
        """
        Perform one or more rounds of estimation
        """        
        for i in xrange(niter):
            call(['HERest', '-C', self.cfg, '-S', self.train_scp,
                                  '-I', self.phon_mlf, '-M', self.nxt_dir, 
                                       '-H', os.path.join(self.cur_dir, macro),
                                       '-H', os.path.join(self.cur_dir, hmmdf),
                                            '-t'] + pruning + [self.phons], 
                                                    stdout=PIPE)
            self._nxt_dir()

    def small_pause(self):
        """
        Add in a tied-state small pause model
        """
        ## make a new hmmdf
        source = open(os.path.join(self.cur_dir, hmmdf), 'r+')
        saved = ['~h "{0}"\n'.format(sp)] # keep track of lines to append later
        # pass until we find "sil"
        for line in source: 
            if line == '~h "{0}"\n'.format(sil): 
                break
        # header for "sil"
        saved.append('<BEGINHMM>\n<NUMSTATES> 3\n<STATE> 2\n')
        # pass until we get to "sil"'s middle state
        for line in source: 
            if line == '<STATE> 3\n':
                break
        # grab "sil"'s middle state
        for line in source:
            if line == '<STATE> 4\n':
                break
            saved.append(line)
        # add in the TRANSP matrix (from VoxForge tutorial, not HTK book...)
        saved.append('<TRANSP> 3\n')
        saved.append(' 0.0 1.0 0.0\n 0.0 0.9 0.1\n 0.0 0.0 0.0\n<ENDHMM>')
        # go to the end of the file
        source.seek(0, os.SEEK_END)
        # append all the lines to the end of the file
        source.writelines(saved)
        source.close()
        ## tie the states together
        hed = os.path.join(self.tmp_dir, temp)
        open(hed, 'w').write("""AT 2 4 0.2 {{{1}.transP}}
AT 4 2 0.2 {{{1}.transP}} 
AT 1 3 0.3 {{{0}.transP}}
TI silst {{{1}.state[3],{0}.state[2]}}
""".format(sp, sil))
        call(['HHEd', '-H', os.path.join(self.cur_dir, macro), '-H',
                            os.path.join(self.cur_dir, hmmdf), '-M', 
                                         self.nxt_dir, hed, self.phons])
        #FIXME this seems to not be necessary, but I'm not sure why.
        """
        # run HLEd
        sink = open(temp, 'w')
        sink.write('EX\nIS {0} {0}\n'.format(sil))
        sink.close()
        call(['HLEd', '-A', '-l', self.aud_dir, '-d', self.taskdict, '-i', self.phon_mlf, temp, self.word_mlf])
        """
        self._nxt_dir() # increments dirs


### MAIN
if __name__ == '__main__':

    ## parse arguments
    # complain if no test directory specification
    try:
        (opts, args) = getopt(argv[1:], 'd:n:s:t:aAmhpu')
        # default opts values
        dictionary = 'dictionary.txt' # -d
        sr = 8000
        tr_dir = None
        ood_mode = False
        n_per_round = 4 # -n
        use_baseproj = False # -p
        use_unicode = False # -u
        speaker_dependent = False # -T
        require_training = False # to keep track of if -n, -s used
        # go through args
        for (opt, val) in opts:
            if opt == '-d': # dictionary  
                dictionary = val
                if not os.access(dictionary, os.R_OK):
                    error('-d path {0} not found', dictionary)
            elif opt == '-m': # ood_mode
                ood_mode = True
            elif opt == '-n':
                try:
                    n_per_round = int(val)
                    require_training = True
                    if not (0 < n_per_round):
                        raise ValueError
                except ValueError:
                    error('-n value must be > 0')
            elif opt == '-p':
                use_baseproj = True
            elif opt == '-s':
                try:
                    sr = int(val)
                    require_training = True
                    if not sr > 0:
                        raise ValueError
                except ValueError:
                    error('-s value must be > 0')
                # check for sane samplerate
                if sr not in SRs:
                    i = bisect(SRs, sr)
                    if i == 0: sr = SRs[0]
                    elif i == len(SRs): sr = SRs[-1]
                    elif SRs[i] - sr > sr - SRs[i - 1]: sr = SRs[i - 1]
                    else: sr = SRs[i]
                    stderr.write('Nearest viable SR is {0} Hz\n'.format(sr))
            elif opt == '-t':
                tr_dir = resolve(val)
                if not os.access(tr_dir, os.F_OK):
                    error('-t path {0} cannot be read', tr_dir)
            elif opt == '-h':
                error('-h requests usage message')
            elif opt == '-a':
                speaker_adaptation = True
                raise NotImplementedError('Not yet implemented.') #FIXME
            elif opt == '-u':
                use_unicode = True
                raise NotImplementedError('Not yet implemented') #FIXME
            else:
                raise GetoptError
    except GetoptError, err:
        error(str(err))
    if len(args) == 0: error('No test directory specified')
    ts_dir = resolve(args.pop())

    ## do the model
    path_to_mlf = os.path.join(ts_dir, align_mlf)
    if tr_dir: 
        print 'Initializing...'
        aligner = TrainAligner(ts_dir, tr_dir, dictionary, sr, ood_mode, 
                                                               use_baseproj)
        print 'Training...'
        aligner.train(n_per_round) # start training
        print 'Modeling silence...'
        aligner.small_pause()      # fix small pauses
        print 'More training...'
        aligner.train(n_per_round) # more training
        print 'Realigning...'
        aligner.align(aligner.phon_mlf) # get best pronuciation of homonyms
        print 'More training...'
        aligner.train(n_per_round) # more training
        print 'Final aligning...'
        aligner.align_and_score(path_to_mlf, os.path.join(ts_dir, scores_txt))
        print 'Making TextGrids...'
        MLF(path_to_mlf).write(ts_dir)
        print 'Alignment complete.'
    else:
        if require_training:
            error('-n, -s only available in training (-t) mode')
        print 'Initializing...'
        aligner = Aligner(ts_dir, 'MOD', dictionary, sr, ood_mode,
                                                         use_baseproj)
        print 'Aligning...'
        aligner.align_and_score(path_to_mlf, os.path.join(ts_dir, scores_txt))
        print 'Making TextGrids...'
        MLF(path_to_mlf).write(ts_dir)
        print 'Alignment complete.'
