#!/bin/sh
# Example that does a single alignment
# Kyle Gorman <kgorman@ling.upenn.edu>

# check args
if [ $# != 2 ]; then
    echo "USAGE: ./align_ex.sh WAVFILE LABFILE"; 
    exit 1;
fi

# check for existence of 1 and 2
if ! ( [ -e $1 ] && [ -e $1 ] ); then
    echo "File not found."; 
    exit 1;
fi

# make a temp directory to keep outcomes in
mkdir -p .dat;

# copy it to the tmp folder
cp $1 $2 .dat;

# perform alignment
./align.py .dat/;

if [ $? != 1 ]; then
    # name of output file
    TextGrid=$(basename $1 ); TextGrid=${TextGrid%.*}.TextGrid;
    # move it
    mv .dat/$TextGrid .; 
    echo "Output is in $TextGrid.";
    rm -r .dat;
else
    echo "Alignment failed."
    exit 1;
fi
