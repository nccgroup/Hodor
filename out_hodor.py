#!/usr/bin/python

"""
This module handles the exit of mutated output
Send it across the network, print to STDOUT, dump into local bin, whatever.
"""

import sys, inspect, signal, threading, multiprocessing, os, ssl, socket
import traceback, time, subprocess, select
import config_hodor

sub_pid = []

# Select the correct output handler
def out(mutated_out, plock, tlock):
  funclist = inspect.getmembers(sys.modules[__name__], inspect.isfunction)
  funcdict = {x[0]: x[1] for x in funclist}
  for handler in config_hodor.output_handler:
    funcdict[handler](mutated_out, plock, tlock) 

def stdout(output, plock, tlock):
  plock.acquire()
  if tlock: tlock.acquire()
  sys.stdout.write(output) # Just dump to stdout for now
  if tlock: tlock.release()
  plock.release()

# Send output over the network per config_hodor.network config options
def network(mutated_out, plock, tlock):
  try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if config_hodor.network["ssl"]: s = ssl.wrap_socket(s, cert_reqs=ssl.CERT_NONE) # Not checking certs for fuzzing..
    s.connect(config_hodor.network["remotehostport"])
    s.send(mutated_out)
    s.setblocking(0)
    retdata = ""
    ready = select.select([s], [], [], 10) # Ten second max timeout, may want to alter if target is limping
    if ready[0]:
      retdata = s.recv(4096) 
  except socket.error as (errno, sockerr):
    sys.stderr.write("SOCKET ERROR({0}): {1}\n".format(errno, sockerr))
    s.close()
    return
  s.close()
  # Handle logging
  if "path" in config_hodor.network["log"]:
    logfile = config_hodor.network["log"]["path"]
    uid = "%s-%s-%s" % (multiprocessing.current_process().pid, threading.current_thread().name, time.clock())
    infile = "%s%s.sent" % (logfile,uid)
    outfile = "%s%s.recv" % (logfile,uid)
    loghelper(infile, mutated_out, 'wb')
    loghelper(outfile, retdata, 'wb')
  if "stdout" in config_hodor.network["log"]:
    dump = "\nSENT:\n%s\nRECEIVED:\n%s" % (mutated_out,retdata)
    stdout(dump, plock, tlock)
  # else we log nothing
  
def disk(output, plock, tlock):
  uid = "%s-%s-%s" % (multiprocessing.current_process().pid, threading.current_thread().name, time.clock())
  filename = "%s/%s" % (config_hodor.disk["log"]["path"], uid)
  loghelper(filename, output, 'wb')    

def process(mutated_out, plock, tlock):
  if "name" not in config_hodor.process:
    print "Missing process name (Process is enabled.)"
    exit(9001)
  name = config_hodor.process["name"]
  args = "" if "arguments" not in config_hodor.process else config_hodor.process["arguments"]
  try:
    logpath = config_hodor.process["log"]["path"]
    if tlock: tlock.acquire()
    mutationsig = "%s-%s-%s" % (multiprocessing.current_process().pid, threading.current_thread().name, time.clock())
    if config_hodor.process["log"]["proc_out"]:
      proc_out = open(logpath+"proc_out/"+mutationsig+".proc_out", 'w')
      file_out = proc_out
    else: file_out = subprocess.PIPE
    if "file_arg" in config_hodor.process:
      tempfilename = "tempfile%s%s" % (mutationsig,config_hodor.process["extension"])
      fullpath = "%s/%s" % (logpath, tempfilename)
      loghelper(fullpath, mutated_out, "w")
      execution = "exec %s %s %s/%s" % (name,args,logpath,tempfilename)
      p = subprocess.Popen(execution, shell=True, stdout=file_out, stdin=subprocess.PIPE, stderr=file_out)
      pout = str(p.returncode)
    else:
      execution = "%s %s" % (name, args)
      p = subprocess.Popen(execution, shell=True, stdout=file_out, stdin=subprocess.PIPE, stderr=file_out)
      p.stdin.write(mutated_out)
      p.stdin.close()
      pout = str(p.returncode)
    sub_pid.append(p.pid)
    timeout = config_hodor.process["timeout"]
    steps = config_hodor.process["steps"]
    timer = 0
    exit_status = None
    while(timer < timeout and exit_status==None):
      time.sleep(steps)
      exit_status = p.poll()
      timer += steps
    if exit_status:  # Not the best way to do this, doing your own instrumentation might be better
      # Crashed process
      signame = signal_name(128 - (exit_status % 128)) # Crude method to get signal code
      entry = "%s Exit status: %s\n" % (mutationsig,signame)
      crash_filename = "%scrashlog.txt" % (logpath)
      loghelper(crash_filename, entry, 'a')
      if config_hodor.process["log"]["mutations"]:
        signal_path = "%s%s" % (logpath,signame)
        try:
          if not os.path.exists(signal_path): os.makedirs(signal_path)
        except e:
          pass
        mutated_filename = "%s/%s%s" % (signal_path, mutationsig, config_hodor.process["extension"])
        loghelper(mutated_filename, mutated_out, "w")
    elif exit_status == None:
      try: # Kill running process
        p.kill()
        p.communicate()
      except OSError, errno:
        pass
    # Delete this file
    if not os.path.isfile(fullpath): 
      exit(9100) # Something happened to our tempfile?
    else: 
      os.remove(fullpath)
    if tlock: tlock.release()
    sub_pid.remove(p.pid)
  except Exception, e:
    print "Exception caught:\n"
    pout = traceback.print_exc()
    if tlock: tlock.release()
    exit(9001)
  finally:
    if config_hodor.process["log"]["proc_out"]: proc_out.close()
  
def loghelper(filename, data, mode):
  f = open(filename, mode)
  f.write(data)
  f.close()

def signal_name(num):
  signames = []
  for key in signal.__dict__.keys():
      if key.startswith("SIG") and getattr(signal, key) == num:
        signames.append (key)
  if len(signames) == 1:
    return signames[0]
  else:
    return str(num)
