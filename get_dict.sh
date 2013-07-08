#!/bin/sh
# get_dict.sh: grabs English stress-free dictionary from CMU
# Kyle Gorman <gormanky@ohsu.edu>

## use the following line to get a stress dictionary
curl -s http://svn.code.sf.net/p/cmusphinx/code/trunk/cmudict/cmudict.0.7a | grep "^[A-Z]" | grep -v '^SIL  ' | sed -e 's/([0-9][0-9]*)//' | sed -e 's/\ \ */\ /g' | sed -e "s/^\'/\\\'/" | sed -e "s/ARABIA AH R EY1 B IY0 AH0/ARABIA AH0 R EY1 B IY0 AH0/" > dictionary.txt
