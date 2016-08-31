#!/usr/bin/python

"""
This is the Hodor module that will prep the files for fuzzing.
Handles delimited text files as well as binary files with formatting info.
Delimiters can be specified by config file and are $$ by default.
"""
import re, string, time
import config_hodor, mutator_hodor, post_hodor

# Takes in text blob, pulls strings delimited by text_delimeter (or not), sends to mutator
# Sends bytearray of mutated output to post_hodor.handler() for further processing
# tlock is set to false by things that aren't utilizing threading. plock is always used
def parse_text(filetext, ignore_tokens, plock, tlock):
  if ignore_tokens:
    filetext = [filetext] # mutate expects a list
    mutated_text = mutator_hodor.mutate(filetext)[0]
  else:
    delim = config_hodor.text_delimiter
    regexp = "%s([\s\S]*?)%s" % (delim, delim)
    tokens = re.findall(regexp, filetext)
    toklocs = [m.start() for m in re.finditer(regexp, filetext)]
    mutated_tokens = mutator_hodor.mutate(tokens)
    # Replace original input with mutated output
    for idx, val in enumerate(tokens):
      filetext = filetext[:2+toklocs[idx]] + mutated_tokens[idx] + filetext[toklocs[idx]+2+len(mutated_tokens[idx]):]
    mutated_text = bytearray(string.replace(filetext, delim, ""))
  post_hodor.handler(mutated_text, plock, tlock)
  return

# Takes in a binary blob, pulls fields specified in bin_fields (or not), sends to mutator
# Sends bytearray of mutated output to post_hodor.handler() for further processing
def parse_bin(filebytes, ignore_fields, plock, tlock):
  if ignore_fields:
    filebytes = [filebytes]
    mutated_bytes = mutator_hodor.mutate(filebytes)[0]
  else:
    tokens = []
    for fields in config_hodor.bin_fields:
      tokens.append(filebytes[fields[0]:fields[1]])
    mutated_tokens = mutator_hodor.mutate(tokens)
    mutated_bytes = bytearray(filebytes)
    for idx, val in enumerate(config_hodor.bin_fields):
      mutated_bytes[val[0]:val[1]] = mutated_tokens[idx]
    mutated_bytes = bytearray(mutated_bytes)
  post_hodor.handler(mutated_bytes, plock, tlock)
  return

# qpq mode requires some different stuff
def qpq_text(filetext, ignore_tokens, plock, tlock):
  if ignore_tokens:
    filetext = [filetext] # mutate expects a list
    mutated_text = mutator_hodor.qpq(filetext)
    mutated_text = bytearray(mutated_text[0][0])
    post_hodor.handler(mutated_text, plock, tlock)
  else:
    delim = config_hodor.text_delimiter
    regexp = delim + "([\s\S]*?)" + delim
    tokens = re.findall(regexp, filetext)
    toklocs = [m.start() for m in re.finditer(regexp, filetext)]
    mutated_tokens = mutator_hodor.qpq(tokens)
    # Replace original input with mutated output
    # qpq returns a list of lists of new tokens for each delimmed token
    for idx, val in enumerate(tokens):
      for newtok in mutated_tokens[idx]:
        mutated_text = filetext[:2+toklocs[idx]] + newtok + filetext[toklocs[idx]+2+len(val):]
        mutated_text = bytearray(string.replace(mutated_text, delim, ""))
        if config_hodor.execdelay != 0: time.sleep(config_hodor.execdelay)
        post_hodor.handler(mutated_text, plock, tlock)
  return

