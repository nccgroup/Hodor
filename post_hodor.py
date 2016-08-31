#!/usr/bin/python

"""
This module handles the processing of mutated output
Do final modifications to data then send to an output mode
"""

import sys, zlib, inspect
import config_hodor, out_hodor

# Select the correct post-fuzz handler, then fire to output
def handler(mutated_out, plock, tlock):
  funclist = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
  funcdict = {x[0]: x[1] for x in funclist}
  for handler in config_hodor.post_handler:
    funcdict[handler](mutated_out, plock, tlock)
  out_hodor.out(mutated_out, plock, tlock)

# Generates checksum and allows specification of offset
# if no offset given, will default to append checksum at the end
def add_CRC32(mutated_out, plock, tlock):
  # Check config entries are valid:
  if config_hodor.CRC32["input_fields"] and config_hodor.CRC32["sum_location"]:
    for fields in config_hodor.CRC32["input_fields"]:
      if (config_hodor.CRC32["input_fields"][0] > fields[0] and config_hodor.CRC32['sum_location'][0] <= fields[1]):
        print "Invalid CRC32['sum_location']: " + hex(config_hodor.CRC32['sum_location'][0]) + " Cannot overwrite CRC32['input_fields']: " + hex(fields[0]) + " " + hex(fields[1])
        exit(1)
  # Creating checksum
  # if input specified, create list of pieces
  if config_hodor.CRC32['input_fields']:
    sum_pieces = []
    for fields in config_hodor.CRC32['input_fields']:
      sum_pieces.append(mutated_out[fields[0]:fields[1]])
    # Only one piece:
    if len(config_hodor.CRC32['input_fields']) == 1:
      checksum = zlib.crc32(str(sum_pieces[0])) & 0xffffffff
    # Multiple pieces:
    elif len(config_hodor.CRC32['input_fields']) > 1:
      for i in sum_pieces:
          checksum = zlib.crc32(str(i),0) if i == sum_pieces[0] else (zlib.crc32(str(i), checksum) & 0xffffffff)
  else: # Sum all data
    checksum = zlib.crc32(str(mutated_out)) & 0xffffffff
  checksum = '%x' % checksum
  checksum = checksum.zfill(8) #Fixes leading 0 problem
  checksum = bytearray(checksum)
  # Determine where to put checksum
  if "bin" in config_hodor.CRC32['type']:
    if config_hodor.CRC32['sum_location']:
      mutated_out[config_hodor.CRC32['sum_location'][0]:(config_hodor.CRC32['sum_location'][0] + 8)] = checksum.decode("hex")
    else:
      mutated_out += checksum.decode("hex")
  elif "text" in config_hodor.CRC32['type']:
    if config_hodor.CRC32['sum_location']:
      mutated_out[config_hodor.CRC32['sum_location']:(config_hodor.CRC32['sum_location'] + 8)] = checksum
    else:
      mutated_out += checksum
  else:
    print "CRC32['type'] not specified in config_hodor.py"
    exit(1)
  return mutated_out

