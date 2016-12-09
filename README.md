# Prosodylab-Aligner, v. 1.1

Scripts for alignment of laboratory speech production data

* Kyle Gorman <gormanky@ohsu.edu>
* Michael Wagner <chael@mcgill.ca>

## Funding

* FQRSC Nouvelle Chercheur NP-132516
* SSHRC Canada Research Chair 218503
* SSHRC Digging Into Data Challenge Grant 869-2009-0004

## License

	The MIT License
	
	Copyright (c) 2011-2016 Kyle Gorman and Michael Wagner

    Permission is hereby granted, free of charge, to any person
    obtaining a copy of this software and associated documentation
    files (the “Software”), to deal in the Software without
    restriction, including without limitation the rights to use,
    copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following
    conditions:

    The above copyright notice and this permission notice shall be
    included in all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND,
    EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
    OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
    NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
    HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
    WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
    OTHER DEALINGS IN THE SOFTWARE.

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

The primary use of forced alignment is to eliminate the need for human annotation of time-boundaries for acoustic events of interest. Perhaps you are interested in sound change: forced alignment can be used to locate individual vowels in a sociolinguistic interview for formant measurement. Perhaps you are interested in laboratory speech production: forced alignment can be used to locate the target word for pitch measurement.

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

    $ export CPPFLAGS=-UPHNALG
    $ ./configure --disable-hlmtools --disable-hslab
    $ make clean    # necessary if you're not starting from scratch
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

## Installation for Linux users

The instructions are the same as for Mac users, with the exception that there is no direct analogue to XCode. Instead, you will probably need to use your distribution's package manager to install a C compiler; on Ubuntu, for instance, the relevant package is called `libc-dev`.

## Installation for Windows 10 (Ubuntu on Windows)

This method requires Windows 10 64-bit with the Anniversary edition update (Ubuntu on Windows is not available in 32 bit installations). If you are running Windows 10 but have not yet had the update rolled out to you, you can force the update by visiting https://www.microsoft.com/en-us/software-download/windows10 and selecting the corresponding option.

### Installing Ubuntu on Windows

Go to Windows Settings > Update & Security > For developers. Make sure Developer mode is on (in my instance it required a reboot). Push the start button and type "Turn Windows features on" and select the option in the menu. Check the option for Windows Subsystem for Linux (beta), and again reboot if you are told to do so. Afterward, find "bash" under the Start Menu (I normally just mash the Windows key and type bash). When starting, the system will ask if you want to install Ubuntu from the Windows Store. Do so and wait for it to finish. You will need to set up a username and password. The password will have to be entered several times during this process.

### Setting up folders

One quirk about the Ubuntu on Windows system is that it doesn't seem to like you monkeying around with files inside its root file system. After installation you will see the prompt indicate your current folder is /mnt/c, which is indeed your C: drive. You will probably want to set up a folder inside there to transfer files into and out of Ubuntu. In my case I used

    mkdir Voice

In this folder I could drop files from Windows Explorer, and then later transfer them into Ubuntu's home folder.

Now we will set up a folder in your home directory. This will bring you to your home folder, and I made a folder in here as well

    cd ~
	mkdir Voice
	cd Voice
	
### Get the HTK

The Hidden Markov Toolkit cannot be distributed by anyone other than Cambridge, so visit http://htk.eng.cam.ac.uk/download.shtml and set up an account. Download the latest stable version of HTK (not the newest beta). This was 3.4.1 at the time of this writing. Move the file from your downloads folder to your c:\Voice folder, and then copy it into your Linux directory

    cp /mnt/c/Voice/* ~/Voice
	
### Step 4: Compile the HTK

Unpack the HTK and go to it using

    tar -xvzf HTK-3.4.1.tar.gz
    cd htk

This will create a HTK folder inside your ~/Voice folder. We now need to compile the HTK. First, execute

    export CPPFLAGS=-UPHNALG
    ./configure --disable-hlmtools --disable-hslab

You now need to modify the configure file. I used vim

    vim configure

We want to change the line that says -m32 to say -m64 instead, which will compile the HTK for 64 bit architectures. To find the line type forward slash followed by m32. This should jump down to the correct line. Press a to enter editing mode and modify the text. Hit escape to exit editing mode, then type colon, x, and enter to get out of VIM and save the file.

We also need the cross-architecture c++ libraries, so

    sudo apt-get install g++-multilib

You should be prompted for a password, so type it in (or paste it in by right clicking the window bar and select Edit > Paste). 

    make clean
    make -j4 all
    sudo make -j4 install

The HTK should now compile and install (the second command will take awhile).

### Getting the other dependencies

The base Ubuntu comes with Python3, but not with pip, so install it now

    sudo apt-get install python3-pip

We need to install Python numerical packages SciPy and NumPy. This will be done automatically later, but they depend on the BLAS and ATLAS projects, which can't be installed automatically (for whatever reason) under Ubuntu. You need to install these packages separately:

    sudo apt-get install libblas-dev liblapack-dev libatlas-base-dev gfortran

To install SOX audio tools, we first grab Ruby, then install LinuxBrew

    sudo apt-get install ruby
    ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Linuxbrew/install/master/install)" PATH="$HOME/.linuxbrew/bin:$PATH"

Note that the second command is all one line. To use LinuxBrew, and for a step further on, we need to modify our path variable (the folders the shell will search when we ask it to start a program). Navigate to the root of your home directory and get a file listing

    cd ~
    ls -a

You should see a file called .bash_profile. Whether or not you do, we'll edit this file (if it doesn't exist, VIM will create it)

    vim .bash_profile

Enter the following lines, substituting "Voice" for whatever folder you set up for your installation. Press a and enter

    export PATH="$HOME/.linuxbrew/bin:$PATH"
    export PATH="$HOME/Voice/htk/HTKTools:$PATH"

Again, to save and quit, hit escape, colon, x, enter. To make sure this worked, type

    cat .bash_profile

You should see the lines you entered print to the screen. If all is well, execute this now by typing

    source ~/.bash_profile

The file will automatically execute every time you start bash, so you only need to do this once.

Now to install SOX, we just type

    brew install sox

### Getting Prosody-Align and its Python dependencies

Install git from the package manager, go into your voice directory, and then grab the Prosodylab-Aligner project

    cd Voice
    sudo apt-get install git
    git clone https://github.com/prosodylab/Prosodylab-Aligner

You should have a folder called Prosodylab-Aligner. Enter this folder

    cd Prosodylab-Aligner

(Note that after typing the first two or so letters you can type press tab to autocomplete). Now for the part that's the biggest pain, installing the Python numerical packages.

    sudo pip3 install -r requirements.txt

This will install NumPy and SciPy, along with a couple of other packages. Using these instructions, you should not encounter any errors. Note that these are massive packages and people have difficulty installing them all the time (as I certainly did). If you encounter errors, you will find numerous helpful posts on getting them working under Ubuntu by Googling.

### Testing

While in the Prosodylab-Aligner folder, you can test your installation

    python3 -m aligner --help

This should return text about how to use aligner. To process files, you can add them to your C:\Voice folder along with their corresponding LAB file (a text file with a transcript of the WAV file with no punctuation in all uppercase)

    python3 -m aligner -a /mnt/c/Voice/

As long as all the words are in the dictionary, and as long as the WAV file is something normal, this should generate a TextGrid. If the words are not in the dictionary, you will get an OOV error, which generates an OOV.txt file. *Resist the temptation* to edit this from a Windows text editor like Notepad++. I found that doing that kills the permissions and in some cases made the file invisible to Ubuntu. Instead, either use VIM to enter the phonemes after the word, or transfer the file out to your C:\ folder, edit that in Notepad++, and then transfer it back.

    ./sort.py lang.dict OOV.txt > tmp; 
    mv tmp lang.dict


## Tutorial

### Obtaining a dictionary

The aligner comes with an (American) English dictionary file `eng.dict`. Some additional dictionaries we have created are available at [`prosodylab.dictionaries` repository](https://github.com/prosodylab/prosodylab.dictionaries). Other dictionaries can be found online, or written for specific tasks. If you're working with RP speakers, [CELEX](http://catalog.ldc.upenn.edu/LDC96L14) might be a good choice. For languages with highly regular, transparent orthographies (e.g., Spanish or Tagalog), you may want to create a simple rule-based grapheme-to-phoneme system using a cascade of ordered rules.

### Aligning files

Imagine you simply want to align multiple audio files with their associated label files, in the following format:

    file data/myexp_1_1_1.*
    data/myexp_1_1_1.lab: ASCII text
    data/myexp_1_1_1.wav: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 22050 Hz

    cat data/myexp_1_1_1.lab
    BARACK OBAMA WAS TALKING ABOUT HOW THERE'S A MISUNDERSTANDING THAT ONE MINORITY GROUP CAN'T GET ALONG WITH ANOTHER SUCH AS AFRICAN AMERICANS AND LATINOS AND HE'S SAID THAT HE HIMSELF HAS SEEN IT HAPPEN THAT THEY CAN AND HE'S BEEN INVOLVED WITH GROUPS OF OTHER MINORITIES

If you'd like to align multiple .wav/.lab file pairs, and they're all in a single directory `data/`, aligning them is as simple as:

    $ python3 -m aligner -r lang-mod.zip -a data/ -d lang.dict 
    ...

This will compute the best alignments, and then place the Praat TextGrids in the `data/` directory. 

The `-r` flag indicates the source of the acoustic model and settings to be used. In the example, `lang-mod.zip` represents the zip directory containing the acoustic model to be used.

`-a data/` indicates the directory containing the data to be aligned.

`-d lang.dict` points to the dictionary to be used in aligning the data.

### Likely errors

#### Out of dictionary words

Secondly, a word in your .lab files may be missing from the dictionary. Such words are written to `OOV.txt`. You can transcribe these using a text editor, then mix them back in like so:

    $ ./sort.py lang.dict OOV.txt > tmp; 
    $ mv tmp lang.dict

If you are transcribing new words using the CMU phone set, see [this page](http://cslu.ohsu.edu/~gormanky/papers/codes/) for IPA equivalents.

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

    $ ./resample.sh -s 16000 -r data/ -w newDirectory/ 

The `-s` flag specifies the desired sample rate (Hz). 16000 Hz is the default for the aligner, and therefore recommended as a sample rate. Alternatively, a different sample rate can be specified for `resample.sh` and aligner module.

The `-r` flag points to the directory containing the files to be resampled. 

The `-w` flag indicates the name of a directory where the new, resampled files should be written. 
