# Prosodylab-Aligner, v. 1.1

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

    USAGE: python3 -m aligner [OPTIONS]

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

### Installing SoX

Installing SoX is not required for using the aligner. It does, however, speed up the process of creating models and aligning data by cutting down on resampling time. 

#### Linux

On Linux or similar POSIX-based systems, SoX can be obtained from the distribution-specific package manager (`apt-get`, `yum`, etc.), or can be compiled from source without too much difficulty.

#### Mac OS X

On Mac OS X it may be obtained via package managers like [http://brew.sh](Homebrew). The SoX maintainers also provide compiled binaries, which can be downloaded from [SourceForge](http://sox.sourceforge.net): click on the link after "Looking for the latest version?". The zip file can be expanded by double-clicking on it. The resulting files must be placed in your `$PATH`. A simple way to do this is to navigate to the resulting directory, and issue the following command:

    $ sudo mv rec play sox soxi /usr/local/bin

This will prompt for your password; type it in (it will not "echo", as `***`), and hit Enter when you're done.

Alternatively, you can install 'homebrew', an application that makes it easier to install other software on your mac. 

#### Installing Homebrew/SoX

Launch 'Terminal.app' and type the prompt:
        $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

    ...and then follow along with the instructions that will be displayed in the Terminal window.

To install SoX useing Homebrew, in the Terminal prompt type: 
    
        $ brew install sox
    
This may take a few minutes.

#### Checking installation

You can confirm that SoX is installed by issuing the following command in any directory:

    $ sox --version
    sox: SoX v14.3.2

Note that your version may be different: the aligner module has been tested for this version, but it should work for both somewhat older versions as well as for the foreseeable future.

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

If you'd like to align multiple .wav/.lab file pairs, and they're all in a single directory data/, aligning them is as simple as:

    $ python3 -m aligner -r lang-mod.zip -a data/ -d lang.dict 
    ...

This will compute the best alignments, and then place the Praat TextGrids in the data/ directory. 

The `-r` flag indicates the source of the acoustic model and settings to be used. In the example, `lang-mod.zip` represents the zip directory containing the acoustic model to be used.

`-a data/` indicates the directory containing the data to be aligned.

### Likely errors

#### Out of dictionary words

Secondly, a word in your .lab files may be missing from the dictionary. Such words are written to OOV.txt. You can transcribe these in outofdict.txt using a text editor, then mix them back in like so:

    $ ./sort.py lang.dict OOV.txt > tmp; 
    $ mv tmp lang.dict.txt

If you are transcribing new words using the CMU phone set, see [this page](http://www.csee.ogi.edu/~gormanky/papers/codes/) for IPA equivalents.

#### Subprocess Process Error

Sometimes there are processing errors that occur. These can often be fixed by enterring the following into Terminal:

    $ make clean
    $ export CPPFLAGS=-UPHNALG
    $ ./configure --disable-hlmtools --disable-hslab
    $ make -j4
    $ sudo make -j4 install 
    
Provide your password, if necessary.

### Training your own models

The aligner module also allows you to train your own models, 

    $ python3 -m aligner -c lang.yaml -d lang.dict -e 10 -t lang/ -w lang-mod.zip
    ...

Please note: THIS REQUIRES A LOT OF DATA to work well, and further takes a long time when there is a lot of data. 

When the `-v` or `-V` flags are specified, output is verbose. `-v` indicates verbose output while `-V` indicates more verbose output.

The `-c` flag points to the configuration file to use. In the example above, this file is `lang.yaml`. This file contains information about the setting preferences and phone set and is used to save the state of the aligner.

The `-d` flag points to the dictionary containing the words to be aligned. 

The `-w` flag indicates that the resulting acoustic model and settings will be written to a file of the name following. In the example, the acoustic model and settings will be written to `lang-mod.zip`.

The `-e` flag is used to specify the number of training iterations per "round": the aligner performs three rounds of training, each of which take approximately the same time, so the effect of increasing this value by one is approximately 3-fold. 

Lastly, the `-t` flag indicates the source of the training data. In the example, this is a directory called `lang/`. When `-t` is specified, a few other command-line options become available. The `-s` flag specifies samplerate for the models used, both training and testing data will be resampled to this rate, if they do not match it. For instance, to use 44010 Hz models, you could say:

    $ python3 -m aligner -c lang.yaml -d lang.dict -e 10 -t lang -w lang-mod.zip -s 44010
    ...

Resampling this way can take a long time, especially with large sets of data. It is therefore recommended that samplerate specifications are made using `resample.sh`. This requires installing SoX (see above installation instructions).

### Resampling Data Files

To be more efficient, it is recommended that `resample.sh` is used to resample data. To do this, enter the following into your Terminal while in the aligner directory: 

    $ bash resample.sh -s 16000 -r data/ -w newDirectory/ 

The `-s` flag specifies the desired sample rate (Hz). 16000 Hz is the default for the aligner, an therefore recommended as a sample rate. Alternatively, a different sample rate can be specified for `resample.sh` and aligner module.

The `-r` flag points to the directory containing the files to be resampled. 

The `-w` flag indicates the name of a directory where the new, resampled files should be written. 





