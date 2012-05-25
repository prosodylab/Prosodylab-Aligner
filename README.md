# Prosodylab-Aligner, v. 0.8

Scripts for alignment of laboratory speech production data

* Kyle Gorman <kgorman@ling.upenn.edu> 
* Michael Wagner <chael@mcgill.ca>

## Funding

* FQRSC Nouvelle Chercheur NP-132516
* SSHRC Canada Research Chair 218503
* SSHRC Digging into Data Challenge Grant 869-2009-0004

## License

See included "LICENSE" 

## Usage

    ./align.py [options] data_to_be_aligned/ 

    Option              Function

    -a                  Perform speaker adaptation,
                        w/ or w/o prior training
    -d dictionary       specify a dictionary file     [default: dictionary.txt]
    -h                  display this message
    -m                  list files containing 
                        out-of-dictionary words
    -n n                number of training iterations [default: 4]
                        for each step of training      
    -p                  Guess unseen words with base
                        projection (CMU English only)
    -s samplerate (Hz)  Samplerate for models         [default: 8000]
                        (NB: available only with -t)
    -t training_data/   Perform model training
    -u                  Support for UTF-8 and UTF-16 
                        label files

## Installing

The scripts require a version of Python 2 no earlier than 2.5, a BASH-compatible shell in /bin/sh, and curl. All these will be installed on recent Macintosh computers as well as most computers running Linux. The scripts included here assume that HTK and SoX are installed on your system. While these scripts can also be made to work on Windows computers, it is non-trivial and not described here.

### Installing SoX

SoX: Source for SoX, which is under the GNU General Public License, can be found at the following URL:

    http://sourceforge.net/projects/sox/files/

#### Linux

On Linux or similar POSIX-based systems, SoX can be obtained from the distribution-specific package manager (`apt-get`, `yum`, etc.), or can be compiled from source without too much difficulty. 

#### Mac OS X

On Mac OS X it may be obtained from Fink or DarwinPorts, though compiling by hand may be somewhat difficult. Fortunately, the SoX maintainers provide compiled binaries for Mac OS X. You can simply download these binaries from the above URL (click on the link after the text "Looking for the latest version?"). The zip file can be expanded by double-clicking on it. The resulting files must be placed in your `$PATH`. A simple way to do this is to navigate to the resulting directory, and issue the following command:

    $ sudo mv rec play sox soxi /usr/local/bin

This will prompt for your password; type it in (it will not "echo", as `***`), and hit Enter when you're done. 

#### Checking installation

You can confirm that SoX is installed by issuing the following command in any directory:

    $ sox --version
    sox: SoX v14.3.2

Note that your version may be different: `align.py` has been tested for this version, but it should work for both somewhat older versions as well as for the foreseeable future.

### Installing HTK

Source for HTK can be obtained at the following URL:

    $ http://htk.eng.cam.ac.uk/download.shtml

Note that you will have to make an account and agree to their restricted distribution license. Once you obtain the "tarball", the following command (adjusting for version number) should unpack it:

    $ tar -fvxz htk-3.4.1.tar.gz

Once you extract the application, navigate into the resulting directory:

    $ cd htk

#### 64-bit x86 Linux 

Edit the file `configure`, making the following changes:

* On line 5507, replace "-m32" with "-s" (make 64-bit stripped binaries instead of 32-bit unstripped binaries)
* On line 6788, replace "-O2" with "-O3" (make fully optimmized binaries)

This will produce smaller, faster binaries than otherwise. Then run the following commands

    $ ./configure --disable-hslab --disable-hlmtools
    ...
    $ make all
    ...
    $ sudo make install
    ...

#### Mac OS X

By default, no C compiler is installed on Mac OS X. There are a few quick ways to get one. You can get a full set of compilers by downloading [Xcode](http://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12) from the Mac App Store. This package is really quite gigantic (a concern for those users who have capped bandwidth), and may take days(!) to download. An excellent alternative is to download the new [Command Line Tools for Xcode](http://developer.apple.com/downloads) package on the Mac App Store, which is much smaller. You will need a free registration to download either package.

Once that's taken care of, execute the following commands in the "htk/" directory you just navigated to:

    $ ./configure --disable-hslab --disable-hlmtools
    ...
    $ make all
    ...
    $ sudo make install
    ...

#### Checking installation

You can confirm that HTK is installed by issuing the following command in any directory:

    $ HCopy -V
    HTK Version Information
    Module     Version    Who    Date      : CVS Info
    HCopy      3.4.1      CUED   12/03/09  : $Id: HCopy.c,v 1.1.1.1 2006/10/11 09:54:59 jal58 Exp $
    ...

## Tutorial

### Obtaining a dictionary

First, obtain an appropriate pronunciation dictionary. Since many of the intended users are American English speakers, I've provided a script (`get_dict.sh`) which will download the CMU pronunciation dictionary automatically.

    ./get_dict.sh

Other dictionaries can be found online, or written in the CMU format for specific tasks. If you're working with RP speakers, CELEX might be a good one.

### Aligning one pair

Imagine you simply want to align multiple audio files with their associated label files, in the following format:

    file data/myexp_1_1_1.*
    data/myexp_1_1_1.lab: ASCII text
    data/myexp_1_1_1.wav: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 22050 Hz

    cat data/myexp_1_1_1.lab
    BARACK OBAMA WAS TALKING ABOUT HOW THERE'S A MISUNDERSTANDING THAT ONE MINORITY GROUP CAN'T GET ALONG WITH ANOTHER SUCH AS AFRICAN AMERICANS AND LATINOS AND HE'S SAID THAT HE HIMSELF HAS SEEN IT HAPPEN THAT THEY CAN AND HE'S BEEN INVOLVED WITH GROUPS OF OTHER MINORITIES

In the case that you only want to align one .wav/.lab pair, perhaps to test out the system, the script `align_ex.sh` is provided, and can be used like the following:

    `./align_ex.sh data/myexp_1_1_1.wav data/myexp_1_1_1.lab`
    ...

Assuming alignment is successful, this script will copy the resulting TextGrid file (called `myexp_1_1_1.TextGrid`) to the current directory for your inspection.

### Aligning multiple pairs

If you'd like to align multiple .wav/.lab file pairs, and they're all in a single directory, aligning them is as simple as:

    $ ./align.py data/
    ...

This will compute the best alignments, and then place then in Praat TextGrids in the data/ directory. 

### Likely errors

Several errors can occur at this stage. 

#### Unpaired data

First, if a .lab file in data/ is not paired with a .wav file in the same directory, or vis versa, then align.py will quit and report the unpaired data to unpaired.txt. You can read this file to figure out what files are missing, or use it to delete present, but unpaired, files. The following will delete unpaired files, after they are found by align.py and written to unpaired.txt.

    $ rm `xargs -d '\n' < unpaired`

#### Out of dictionary words

Secondly, a word in your .lab files may be missing from the dictionary. Such words are written to outofdict.txt. You can transcribe these in outofdict.txt using a text editor, then mix them back in like so:

    $ ./sort.py dictionary.txt outofdict.txt > tmp; 
    $ mv tmp dictionary.txt

If you call align.py with the argument -m, each word in outofdict.txt is paired with a list of .lab files where it occurs. This may be useful for fixing typos in the .lab files. 

#### SoX not installed

Also, if SoX is not installed, but it needed because the audio is in a different format than the provided models (which are mono and sampled at 8000 Hz), an error will be raised.

#### align.py not executable ("Permission denied")

Lastly, the file `align.py` may not be marked as executable on your system, in which case you'll get an error like the following:

    $ ./align.py data/ 
    -bash: ./align.py: Permission denied

On Linux or Mac OS X, the following command should do the trick:

    $ chmod +x ./align.py

Then, run `align.py` like above.  

#### Out of space error

The `align.py` script makes prodigious use of "temporary" disk space. On Linux (in particular), it is possible that this space is limited by the OS, and `align.py` will fail with number of cascading errors referring to disc space. A simple way to fix this is to use a temporary directory located somewhere else. If the environmental variable `$TMPDIR` is defined and it points to a writeable directory, `align.py` will use it.

    $ mkdir ~/tmpdir
    $ export TMPDIR=~/tmpdir

### Training your own models

The `align.py` script also allows you to train your own models, where the folder for training is specified by a directory after the `-t` flag

    $ ./align.py -t test_data/ data/
    ...

This requires a lot of data to work well, and further takes a long time when there is a lot of data. It is also possible to train on your test data, and in fact it is something we do quite often at the lab. That looks like:

    $ ./align.py -t data/ data/
    ...

When `-t` is specified, a few other command-line options to `align.py    become available. The `-s` flag specifies samplerate for the models used, and if SoX is installed, both training and testing data will be resampled to this rate, if they do not match it. For instance, to use 44010 Hz models, you could say:

    $ ./align.py -s 44010 -t data data
    ...

Note that the slash character </> is not obligatory in specifying directories: align.py assumes these are directory names, possibly including wildcards, and expands the wildcards if possible.

    $ ./align.py -d MY_DICTIONARY.txt -t data data
    ...

Lastly, the `-n` flag may be used to specify the number of training iterations per "round": align.py performs three rounds of training, each of which take approximately the same time, so the effect of increasing this value by one is approximately 3-fold. By default, `-n` is 4 (so 12 iterations of training in all), but the following command would set it at 5 (or 15 rounds of training):

    $ ./align.py -n 4 -t data data
    ...

Other options are documented above.

## Importing the module

Users who are familiar with Python are encouraged to import `align.py` as a Python module if it makes sense for their application. 
