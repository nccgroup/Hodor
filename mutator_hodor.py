#!/usr/bin/python

"""
This file contains all of the mutators for fuzzing.
Pass in your data, watch it get mangled.
"""
import sys, math, random, multiprocessing, threading, inspect
import config_hodor

# Takes in a list of tokens to be mutated
# Select mutator based on config_hodor.py
def mutate(tokens):
  funclist = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
  funcdict = {x[0]: x[1] for x in funclist} 
  for mutator in config_hodor.mutator:
    tokens = funcdict[mutator](tokens)
  return tokens

# Pass it a list of fields, will return a list of fuzzed fields
# Based on the Charlie Miller 5 line fuzzer
def millerfuzz(tokens):
  # The higher the fuzz factor, the more minute the fuzzing
  FuzzFactor = config_hodor.mutator['millerfuzz']['FuzzFactor']
  mutated_tokens = []
  for item in tokens:
    buf = bytearray(item) if isinstance(item, str) else item
    numwrites = random.randrange(math.ceil((float(len(buf)) / FuzzFactor))) + 1
    for j in range(numwrites):
      rbyte = random.randrange(256)
      rn = random.randrange(len(buf))
      buf[rn] = "%c"%(rbyte)
    mutated_tokens.append(buf)
  return mutated_tokens

# Just replace the tokens with totally random stuff
def totesrand(tokens):
  mutated_tokens = []
  for item in tokens:
    buf = bytearray(item) if isinstance(item, str) else item
    for j in range(len(buf)):
      rbyte = random.randrange(256)
      buf[j] = "%c"%(rbyte)
    mutated_tokens.append(buf)
  return mutated_tokens

# Bitflipper, flips bits. Roughish implementation 
def bflipper(tokens):
  mutated_tokens = []
  procnum = int(multiprocessing.current_process().name)
  threadnum = int(threading.current_thread().name)
  mystart = procnum*max((config_hodor.iterations/config_hodor.procs), 8)
  # Figure out how to spread threads in a sensible manner
  for item in tokens:
    buf = bytearray(item) if isinstance(item, str) else item
    if len(buf) == 0:
      mutated_tokens.append(buf) # Nothing to do
      continue
    # This is supposed to deal with iterations > buflen in a sane way
    # Should just loop through and flip more bits at once
    myflip = config_hodor.mutator["bflipper"]["flipmode"] + (mystart+threadnum)/(len(buf)*8) 
    flipme = (threadnum/8)+(mystart/8)
    if flipme >= len(buf):
      flipme = flipme % len(buf)
    for j in range(myflip):
      buf[flipme] ^= (1 << ((threadnum+j)%8)) # Minor bug here, will do one extra xor on myflip>1
    mutated_tokens.append(buf)
  return mutated_tokens

# Quid pro quo, swap out old tokens for user specified tokens
def qpq(tokens):
  procnum = int(multiprocessing.current_process().name)
  mutated_tokens = []
  for token in tokens:
    mutated_tokens.append([])
  # Go through all files specified in config
  for filenum, files in enumerate(config_hodor.mutator['qpq']['file']):
    qpqfile = open(files, 'r')
    # Chop qpqfile into sections for each process to handle
    num_lines = sum(1 for line in qpqfile)
    qpqfile.seek(0)
    mylines = num_lines/config_hodor.procs
    mystart = procnum*mylines
    myend = (procnum+1)*mylines
    # Slow and inefficient way to get to next offset, must be a better way 
    for i in range(mystart):
      qpqfile.readline()
    if procnum+1 != config_hodor.procs:
      for i in range(mystart, myend):
        newtok = qpqfile.readline().rstrip()
        if len(config_hodor.mutator['qpq']['file']) == 1:  # if there is only one file, replace all tokens with same thing
          for idx, val in enumerate(mutated_tokens):
            mutated_tokens[idx].append(newtok)
        else:                                              # else, each token is aligned with one file
          mutated_tokens[filenum].append(newtok)
    else:
      for line in qpqfile:
        newtok = line.rstrip()
        if len(config_hodor.mutator['qpq']['file']) == 1:  # if there is only one file, replace all tokens with same thing
          for idx, val in enumerate(mutated_tokens):
            mutated_tokens[idx].append(newtok)
        else:                                              # else, each token is aligned with one file
          mutated_tokens[filenum].append(newtok)
    qpqfile.close()
  return mutated_tokens

