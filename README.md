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

## Installations instructions for Mac Users

NB: when you are instructed to type in a command, do not type the '$' symbol; it just indicates the start of the prompt.

NB: most of these commands will produce significant text output. You can safely ignore it unless it explicitly is marked as an 'error'.

### Install XCode

XCode is a free application that contains of all the tools you need to compile most software on Mac OS X. You can get it from the Mac App Store) or you can start the download from the Terminal. To do the latter, launch the application 'Terminal.app', then type the following at the prompt, then hit return:

    $ xcode-select --install
Note that this is a large download and will take a while. Start it now! An alternative option that is somewhat smaller is Command Line Tools for Xcode.

### Install HTK (Hidden Markov ToolKit)

HTK is the "backend" that powers the aligner. It is available only as uncompiled code. First, go to the HTK website and register. Then click on 'Download' on the left panel, and then click on 'HTK source code (tar+gzip archive)' under 'Linux/Unix downloads'.

Once this is downloaded, you may have to unpack the "tarball". Launch the application 'Terminal.app' (if you haven't already), and then navigate to your downloads directory (cd ~/Downloads will probably work). Then unpack the tarball like so:

    $ tar -xvzf HTK-3.4.1.tar.gz

Some browsers automatically unpack compressed files that they download. If you get an error when you execute the above command, try the following instead:

    $ tar -xvf HTK-3.4.1.tar

Once you extract the application, navigate into the resulting directory:

    $ cd htk

Once this is complete, the next step is to compile HTK. Execute the following commands inside the htk directory:

    $ make clean
    $ export CPPFLAGS=-UPHNALG
    $ ./configure --disable-hlmtools --disable-hslab
    $ make -j4 all
    $ sudo make -j4 install

(This will take a few minutes.)

At the last step, you may be asked to provide your system password; do so and then hit return. Note that your password will not echo (i.e., no '*' will be produced when you type).

### Install Homebrew

Homebrew is a command-line application for installing software on your Macintosh. It is the easiest way to get the remaining dependencies to run the aligner. To install Homebrew, launch the application 'Terminal.app' (if you haven't already) and type the following:

    $ ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"

and then follow along with the instructions that are displayed in the terminal window. Once again, you may need to enter your system password, and once again, your password will not echo.

### Install Python 3

Homebrew makes it easy to install the newest version of Python programming language that powers the aligner. To install it, launch the application 'Terminal.app' (if you haven't already) and type the following:

    $ brew install python3

(This will take a few minutes.)

### Install SoX

SoX is the "Swiss Army knife of sound processing programs", and can be used to do fast batch of your audio files (though it is possible to run the aligner without using SoX). Once again, Homebrew makes it easy to install SoX. Launch the application 'Terminal.app' (if you haven't already) and type the following:

    $ brew install sox

(This may take a few minutes.)

### Install the actual aligner

Prosodylab-Aligner lives on GitHub, a repository for open-source software. You may want to create an account there, and perhaps install 'GitHub.app', which makes it easier to interact with GitHub. But for the purposes of installing the aligner, all you need is the git command-line tool, which is part of Xcode (and so should already be installed). Launch the application 'Terminal.app' (if you haven't already) and type the following:

    $ git clone http://github.com/prosodylab/Prosodylab-Aligner

Finally, you need to install a few additional dependencies for Python. Enter the following commands to take care of this:

    $ cd Prosodylab-Aligner 
    $ pip3 install -r requirements.txt

At this point, you can test your installation by running:

    $ python3 -m aligner --help

which should print out some information about how to use the aligner.

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





