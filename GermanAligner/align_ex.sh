#!/bin/bash
# align_ex.sh: do a single alignment
# Kyle Gorman <gormanky@ohsu.edu>

# fail if any non-zero return codes
set -e

# check args
if [ $# -lt 2 ]; then
    echo "USAGE: ./align_ex.sh [align.py_args...] WAV LAB"
    exit 1
fi

# arguments logic
ARGS=("$@")
WAV=${ARGS[$#-2]}
LAB=${ARGS[$#-1]}
unset ARGS[$#]
unset ARGS[$#]

# check for existence of data
if ! ( [ -e "$WAV" ] ); then
    echo "WAV file '$WAV' not found."
    exit 1
fi

if ! ( [ -e "$LAB" ] ); then
    echo "LAB file '$LAB' not found."
    exit 1
fi

# make a temp directory to keep outcomes in
TMP=$(mktemp -d -t $(basename $0))
echo "$TMP"

# copy it to the tmp folder
cp "$WAV" "$LAB" "$TMP"

# perform alignment
python align.py ${ARGS[@]:0:$#-2} "$TMP"

# name of output file
TextGrid=$(basename "$WAV" ); 
TextGrid=${TextGrid%.*}.TextGrid
# move it
mv "$TMP"/"$TextGrid" .
echo "Output in '$TextGrid'."
