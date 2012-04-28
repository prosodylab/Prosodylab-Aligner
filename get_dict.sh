#!/bin/sh
## grabs English stress-free dictionary from CMU
## Kyle Gorman <kgorman@ling.upenn.edu>

## instead, use the following line (uncomment it) to get a stress dictionary
curl -s https://cmusphinx.svn.sourceforge.net/svnroot/cmusphinx/trunk/cmudict/cmudict.0.7a | grep "^[A-Z]" | grep -v '^SIL' | sed -e 's/([0-9][0-9]*)//' | sed -e 's/\ \ */\ /g' | sed -e "s/^\'/\\\'/" > dictionary.txt
