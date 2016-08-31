Quid Pro Quo is partially implemented but still functional for many purposes.


If you specify one qpqfile in config_hodor, tokens from that file will be swapped sequentially with each
delimited token, one change at a time. If you specify multiple qpqfiles, you MUST specify the same number
of qpqfiles as delimited tokens in the input file, or behavior is undefined.

For example, if you specify two files and have two tokens, the first token will be iteratively replaced
by things from the first file, and the second token will be iteratively replaced with items from the
second file. Only one change is made per output.

qpqtest.txt and qpqtest2.txt are brief PoC files for use with test.txt
