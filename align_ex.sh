#!/bin/bash
# Example that does a single alignment
# Kyle Gorman <gormanky@ohsu.edu>

# check args

if [ $# -lt 2 ]; then
    echo "USAGE: ./align_ex.sh [align.py_args...] WAV LAB"; 
    exit 1;
fi

# arguments logic
ARGS=("$@")
WAV=${ARGS[$#-2]}
LAB=${ARGS[$#-1]}
unset ARGS[$#]
unset ARGS[$#]

# check for existence of data
if ! ( [ -e $WAV ] ); then
    echo "WAV file $WAV not found."; 
    exit 1;
fi

if ! ( [ -e $LAB ] ); then
    echo "LAB file $LAB not found."; 
    exit 1;
fi

# make a temp directory to keep outcomes in
mkdir -p .dat;

# copy it to the tmp folder
cp $WAV $LAB .dat;

# perform alignment
python align.py ${ARGS[@]:0:$#-2} .dat/;

if [ $? != 1 ]; then
    # name of output file
    TextGrid=$(basename $WAV ); TextGrid=${TextGrid%.*}.TextGrid;
    # move it
    mv .dat/$TextGrid .; 
    echo "Output is in $TextGrid.";
    rm -r .dat;
else
    echo "Alignment failed."
    exit 1;
fi
