#!/bin/sh
# Example that does a single alignment
# Kyle Gorman <kgorman@ling.upenn.edu>

# check args
if [ $# != 2 ]; then
    echo "USAGE: ./align_ex.sh WAVFILE LABFILE";
    exit;
fi

# make a temp directory to keep outcomes in
mkdir -p .dat;

# copy it to the tmp folder
cp $1 $2 .dat;

# perform alignment
./align.py .dat/;

# name of output file
TextGrid=$(basename $1);
TextGrid=${TextGrid%.*}.TextGrid;

# report
if [ $TextGrid != ".TextGrid" ]; then 
    mv .dat/$TextGrid .;
    echo "Output is in $TextGrid";
else # blank
    echo "Alignment failed";
fi
