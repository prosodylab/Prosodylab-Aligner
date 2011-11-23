#!/bin/sh
## grabs English stress-free dictionary from CMU
## Kyle Gorman <kgorman@ling.upenn.edu>

## instead, use the following line (uncomment it) to get a stress dictionary
curl -s https://cmusphinx.svn.sourceforge.net/svnroot/cmusphinx/trunk/cmudict/cmudict.0.7a | grep -v '^[^A-Z]' | sed -e 's/\ \ /\ /g' | sed -e 's/^"/\\"/' | sed -e "s/^\'/\\\'/" | sed -e 's/([0-9][0-9]*)//' > dictionary.txt
