**NB**: This README is currently out of date: the main branch is changing rapidly and will continue to do so until the end of December 2014; at this point, we will bring the README back up to date. Click [here](https://github.com/kylebgorman/Prosodylab-Aligner/archive/2204ee08a14ab91007155a09423da1d81d4be420.zip) to download the stable version of the aligner, which is described in the README below.

# Prosodylab-Aligner, v. 1.0

Scripts for alignment of laboratory speech production data

* Kyle Gorman <gormanky@ohsu.edu>
* Michael Wagner <chael@mcgill.ca>

## Funding

* FQRSC Nouvelle Chercheur NP-132516
* SSHRC Canada Research Chair 218503
* SSHRC Digging Into Data Challenge Grant 869-2009-0004

## License

See included "LICENSE" 

## Citation

Please you use this tool; we would appreciate if you cited the following paper:

Gorman, Kyle, Jonathan Howell and Michael Wagner. 2011. Prosodylab-Aligner: A Tool for Forced Alignment of Laboratory Speech. Canadian Acoustics. 39.3. 192–193.

## Usage

    USAGE: ./align.py [OPTIONS] data_to_be_aligned/

    Option              Function
    
    -c config_file      Specify a configuration file to use     [default: en.yaml]

    -d dictionary       Specify a dictionary file               
                        (NB: available only with -t (See Input Group))

    -h                  Display this message

    -s samplerate (Hz)  Samplerate for models                   [default: SAMPLERATE]
                        (NB: available only with -t)

    -e                  Number of epochs in training per round  [default: EPOCHS]
                        (NB: available only with -t (See Input Group))

    -v                  Verbose output

    -V                  More verbose output

    Input Group:        Only one of the following arguments may be selected

    -r                  Read in serialized acoustic model

    -t training_data/   Perform model training 

    Output Group:       Only one of the following arguments may be selected

    -a                  Directory of data to be aligned

    -w                  Location to write serialized model

## FAQ

### What is forced alignment?

Forced alignment can be thought of as the process of finding the times at which individual sounds and words appear in an audio recording under the constraint that words in the recording follow the same order as they appear in the transcript. This is accomplished much in the same way as traditional speech recognition, but the problem is somewhat easier given the constraints on the "language model" imposed by the transcript.

### What is forced alignment good for?

The primary use of forced alignment is to eliminate the need for human annotation of time-boundaries for acoustic events of interest. Perhaps you are interested in sound change: forced alignment can be used to locate individual vowels in a sociolinguistic interview for formant measurement. Perhaps you are interested in laboratoy speech production: forced alignment can be used to locate the target word for pitch measurement.

### Can I use Prosodylab-Aligner for languages other than English?

Yes! If you have a few hours of high quality speech and associated word-level transcripts, Prosodylab-Aligner can induce a new acoustic model, then compute the best alignments for said data according to the acoustic model.

### What are the limitations of forced alignment?

Forced alignment works well for audio from speakers of similar dialects with little background noise. Aligning data with considerable dialect variation, or to speech embedded in noise or music, is currently state of the art.

### How can I improve alignment quality?

You can train your own acoustic models, using as much training data as possible, or try to reduce the noise in your test data before aligning.

### How does Prosodylab-Aligner differ from HTK?

The [Hidden Markov Model Toolkit](http://htk.eng.cam.ac.uk) (HTK) is a set of programs for speech recognition and forced alignment. The [HTK book](http://htk.eng.cam.ac.uk/docs/docs.shtml) describes how to train acoustic models and perform forced alignment. However, the procedure is rather complex and the error messages are cryptic. Prosodylab-Aligner essentially automates the HTK forced alignment workflow.

### How does Prosodylab-Aligner differ from the Penn Forced Aligner?

The [Penn Forced Aligner](http://www.ling.upenn.edu/phonetics/p2fa/) (P2FA) provides forced alignment for American English using an acoustic model derived from audio of US Supreme Court oral arguments. Prosodylab-Aligner has a number of additional capabilities, most importantly acoustic model training, and it is possible in theory to use Prosodylab-Aligner to simulate P2FA.

## Installing

The scripts require a version of Python no earlier than 3.3, a BASH-compatible shell located in `/bin/sh`, and `curl`. All these will be installed on recent Macintosh computers as well as most computers running Linux. The scripts included here also assume that HTK is installed on your system. While these scripts can also be made to work on Windows computers, it is non-trivial and not described here.


### Installing HTK

You will need first to download [HTK's source code](http://htk.eng.cam.ac.uk/download.shtml).

Note that you will have to make an account and agree to their restricted distribution license. Once you obtain the "tarball", the following command (adjusting for version number) should unpack it:

    $ tar -fvxz htk-3.4.1.tar.gz

Note that if your browser automatically attempts to unpack compressed files upon download, you may get the following error:

    tar: Must specify one of -c, -r, -t, -u, -x

In this case, use the command (again adjusting for version number):

    $ tar -xf htk-3.4.1.tar.gz

Once you extract the application, navigate into the resulting directory:

    $ cd htk

#### 64-bit x86 Linux 

Run the following commands:

    $ ./configure --disable-hslab --disable-hlmtools
    ...
    $ make all
    ...
    $ sudo make install
    ...

#### Mac OS X

By default, no C compiler is installed on Mac OS X. There are a few quick ways to get one. You can get a full set of compilers by downloading [Xcode](http://itunes.apple.com/us/app/xcode/id497799835?ls=1&mt=12) from the Mac App Store. This package is really quite large and may take days(!) to download. A good alternative is to download the new [Command Line Tools for Xcode](http://developer.apple.com/downloads) package on the Mac App Store, which is much smaller. You will need a free registration to download either package.

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

First, obtain an appropriate pronunciation dictionary. Currently, the aligner comes with a file "dictionary.txt" intended for use with American English. Some dictionaries we have created are available at the [`prosodylab.dictionaries` repository](https://github.com/prosodylab/prosodylab.dictionaries). Other dictionaries can be found online, or written for specific tasks. If you're working with RP speakers, [CELEX](http://catalog.ldc.upenn.edu/LDC96L14) might be a good choice. For languages with regular, transparent orthographies, you may want to create a simple rule-based grapheme-to-phoneme system as a series of ordered rules.

### Aligning files

Imagine you simply want to align multiple audio files with their associated label files, in the following format:

    file data/myexp_1_1_1.*
    data/myexp_1_1_1.lab: ASCII text
    data/myexp_1_1_1.wav: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 22050 Hz

    cat data/myexp_1_1_1.lab
    BARACK OBAMA WAS TALKING ABOUT HOW THERE'S A MISUNDERSTANDING THAT ONE MINORITY GROUP CAN'T GET ALONG WITH ANOTHER SUCH AS AFRICAN AMERICANS AND LATINOS AND HE'S SAID THAT HE HIMSELF HAS SEEN IT HAPPEN THAT THEY CAN AND HE'S BEEN INVOLVED WITH GROUPS OF OTHER MINORITIES

If you'd like to align multiple .wav/.lab file pairs, and they're all in a single directory, aligning them is as simple as:

    $ python3 -m aligner -r lang-mod.zip -a data/ -d dictionary 
    ...

This will compute the best alignments, and then place then in Praat TextGrids in the data/ directory. 

* `-r fra-mod.zip` indicates the source of the acoustic model and settings to be used
* `-a fra` indicates the source of data to be aligned.

### Likely errors

Several errors can occur at this stage. 

#### Unpaired data

First, if a .lab file in data/ is not paired with a .wav file in the same directory, or vis versa, then align.py will quit and report the unpaired data to unpaired.txt. You can read this file to figure out what files are missing, or use it to delete present, but unpaired, files. The following will delete unpaired files, after they are found by align.py and written to unpaired.txt.

    $ rm `xargs -d '\n' < unpaired`

#### Out of dictionary words

Secondly, a word in your .lab files may be missing from the dictionary. Such words are written to OOV.txt. You can transcribe these in outofdict.txt using a text editor, then mix them back in like so:

    $ ./sort.py lang.dict OOV.txt > tmp; 
    $ mv tmp lang.dict.txt

If you are transcribing new words using the CMU phone set, see [this page](http://www.csee.ogi.edu/~gormanky/papers/codes/) for IPA equivalents.


#### align.py not executable ("Permission denied")

Lastly, the file `aligner.py` may not be marked as executable on your system, in which case you'll get an error like the following:

    $ ./aligner.py data/ 
    -bash: ./align.py: Permission denied

On Linux or Mac OS X, the following command should do the trick:

    $ chmod +x ./aligner.py

Then, run `aligner.py` like above.

#### Out of space errors

The Aligner package makes prodigious use of "temporary" disk space. On Linux (in particular), it is possible that this space is limited by the OS, and the aligner will fail with number of cascading errors referring to disc space. A simple way to fix this is to use a temporary directory located somewhere else. If the environmental variable `$TMPDIR` is defined and it points to a writeable directory, `align.py` will use it.

    $ mkdir ~/tmpdir
    $ export TMPDIR=~/tmpdir

### Training your own models

The Aligner package also allows you to train your own models, 

    $ python3 -m aligner -V -c fr.yaml -d fr.dict -e 10 -t lang -w lang-mod.zip
    ...


* `-V` stands for “full verbosity"
* `-c fra.yaml` points to the configuration file to use. this also contains information about the phone set we’re using (Lexique) and will be used to “save the state” of the aligner for later
* `-d fra.dict` indicates that I’m using a dictionary file called fra.dict: this is just Lexique with our tweaks
* `-e 10` indicates ten “epochs” of training for each round of training the system does (there are 3 rounds, usually)
* `-t fr` indicates the source of the training data, a directory called `fra/`
* `-w fr-model.zip` indicates that the resulting acoustic model and settings will be written to a file of the same name

Please note: THIS REQUIRES A LOT OF DATA to work well, and further takes a long time when there is a lot of data. 

When `-t` is specified, a few other command-line options to `align.py` become available. The `-s` flag specifies samplerate for the models used, both training and testing data will be resampled to this rate, if they do not match it. For instance, to use 44010 Hz models, you could say:


Lastly, the `-e` flag may be used to specify the number of training iterations per "round": align.py performs three rounds of training, each of which take approximately the same time, so the effect of increasing this value by one is approximately 3-fold. By default, `-E` is 4 (so 12 iterations of training in all), but the following command would set it at 5 (or 15 rounds of training):

    $ ./align.py -e 5 -t data data
    ...

Other options are documented above.

