#!/usr/bin/python

"""
Config file for Hodor. Use Python data structures and vars to make things easy.
"""

# Number of seconds between executions per process, in case you don't want to flood a network target
execdelay = 0

# Used to specify tokens in text file that specify region to be fuzzed.
# e.g. "West @@Philadelphia@@ born and raised." Will pass 'Philadelphia' to fuzz module
# If you use a special regex character (. $ ^ { [ ( | ) ] } * + ? \), you may break things
text_delimiter = "@@"

# Binary mutation config options
# Each tuple is a [begin,end] token for mutation from the input
# e.g.[(0x3,0x18),(0x172,0x17D)] will mutate two areas of the binary, 0x3-0x18 and 0x172-0x17D
bin_fields = [(0x3,0x18),(0x172,0x17D)]

# Specify the number of processes to spawn to carry out the operation
procs = 2

threads = 4

# Number of times to fuzz output, will be ignored for qpq (which just parses whole qpqfile).
# This is number of total iterations, and will be divided among procs and threads, anything
# not divisible by procs*threads will just get the remainder dumped onto the last thread
iterations = 12

# The classic dumb fuzz algorithm by Charlie Miller
millerfuzz = {"FuzzFactor" : 100}   # The higher the fuzz factor, the more minute the fuzzing

# Quid pro quo, swap out tokens from the seed file with specific tokens of your choosing
# If you specify more than one file, they will be aligned with each token from input in same order
# 	If more than one file, you need to have same number of files as tokens for it to function correctly
# See qpqfiles/README.txt for a description of pre-built files and available modes/types
qpq = {"file" : ["qpqfiles/qpqtest.txt", "qpqfiles/qpqtest2.txt"],
       "swapmode" : "oneatatime"}

# Replace the token with totally random output
totesrand = {}

# Select the flipmode, aka number of bits to flip at once
# If there are more iterations than bits, flipmode will increase automatically
bflipper = {"flipmode" : 1}

# Uncomment the mutator you want to use, comment out all others
# If you have multiple selected, things will probably screw up, so don't do that
# If you comment them all out, no mutator is called
mutator = {
#"millerfuzz" : millerfuzz
#"qpq" : qpq
#"totesrand" : totesrand
"bflipper" : bflipper
}


# Post handler selection and option specification
# Do fixups before sending the output 

# CRC Fixup Module
# "input_fields" for checksum
# Each tuple is a [begin,end] token for what needs to be checksummed.
# Starting number is exclusive, ending value is inclusive 
# If crc_input_fields = None, will checksum entire mutated data
# "sum_location" = Where to write the checksum
# WARNING: Cannot overlap above input fields.

CRC32 = {
	"type": 
		"bin",
		#"text",
	"input_fields":
		#[(0x12, 0x15), (0x4f, 0x5a)],
		None,
	"sum_location":
		[(0x0)]
		#None
}

post_handler = {
#"add_CRC32" : CRC32
} 


# Output handler selection and option specification
# Available output handlers and their required configuration options

# Dump output to standard out
stdout = {}
# Send to network, indicate target and where to log results, 'file' will write unique files to specified dir
# Comment out both file and stdout for no logging. ssl must be set to True or False depending on need
network = {"remotehostport" : ("localhost", 1234),
"ssl" : False,
"log" : {"path" : "results/"
         #"stdout" : True
        }
}

#Write output to directory
disk = {"log" : {"path" : 'results/'}}

# Uncomment in output_handler to call specified external process
process = { 
"name" : "vlc",
"arguments" : "",
"file_arg" : True, # Use mutated filename as an argument
"extension" : ".out", # extension to use for saved mutations
"timeout" : 5,  # seconds until subprocess is killed
"steps" : .3,    # steps in seconds
"log" : {
  "path" : "results/",
  "mutations" : True, # save mutations that caused a crash?
  "proc_out" : False # save output from process that is being called?
  }
}

# Uncomment the one you want to actually use
output_handler = {
"stdout" : stdout
#"disk" : disk
#"network" : network
#"process" : process
}
