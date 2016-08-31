#!/usr/bin/python

import sys, argparse, multiprocessing, threading, time, signal, os, math
import config_hodor, prep_hodor, out_hodor

def main():
  # Parsing command line arguments
  helpmsg = "Welcome to the Hodor fuzzer!"
  parser = argparse.ArgumentParser(description=helpmsg)
  # Arguments listed in order of precedence, where applicable
  parser.add_argument("-s", "--stdin",
    help="Read fuzz seed from STDIN.",
    action="store_true")

  parser.add_argument('-t', '--textmode',
    nargs='?',
    const=sys.stdin,
    type=argparse.FileType('r'),
    help="Textmode, file required containing fuzz seed if not using stdin")

  parser.add_argument('-b', '--binmode',
    nargs='?',
    const=sys.stdin,
    type=argparse.FileType('rb'),
    help="Binarymode, file required containing fuzz seed if not using stdin")

  parser.add_argument("-f", "--fullmutate",
    help="Mutate entire input, ignore any delimiters",
    action="store_true")

  args = parser.parse_args()
  if not args.binmode and not args.textmode:
    print "Must select either binarymode or textmode"
    parser.print_help()
    sys.exit()
  build_logpaths()
  # Walk the args, call correct module 
  indata = ""
  if args.stdin:
    while 1:
      try:
        line = sys.stdin.readline()
      except KeyboardInterrupt:
        break
      if not line:
        break
      indata += line
    handler = prep_hodor.parse_text if args.textmode else prep_hodor.parse_bin 
  elif args.textmode and indata == "":
    indata = args.textmode.read()
    args.textmode.close()
    handler = prep_hodor.parse_text
  elif args.binmode and indata == "":
    if indata == "":
      indata = args.binmode.read()
      args.binmode.close()
      handler = prep_hodor.parse_bin
  plock = multiprocessing.Lock() 
  global pjobs
  pjobs = []
  signal.signal(signal.SIGINT, clean_kill)
  for i in xrange(config_hodor.procs): # We aren't going to use threads for qpq, just processes
    if 'qpq' in config_hodor.mutator: 
      if args.binmode:
        print "qpq mode not compatible with binmode" # Need to add binmode compat someday..
        sys.exit()
      p = multiprocessing.Process(name=str(i), target=prep_hodor.qpq_text, args=(indata, args.fullmutate, plock, False)) # Set tlock to false
    else:
      p = multiprocessing.Process(name=str(i), target=thread_helper, args=(indata, args.fullmutate, plock, handler))
    pjobs.append(p)
    p.start()
  [p.join() for p in pjobs]
  return

# Chop up threads for each process
def thread_helper(indata, fullmutate, plock, handler):
  tlock = threading.Lock()
  tjobs = [] 
  # Dispatch threads
  for i in xrange(config_hodor.threads):
    t = threading.Thread(name=str(i), target=exec_loop, args=(indata, fullmutate, plock, tlock, handler))
    tjobs.append(t)
    t.start()    
  [t.join() for t in tjobs]

def exec_loop(indata, fullmutate, plock, tlock, handler):
  threadrem = 0
  if int(multiprocessing.current_process().name)+1 == config_hodor.procs and int(threading.current_thread().name)+1 == config_hodor.threads:
    threadrem = config_hodor.iterations % (config_hodor.procs * config_hodor.threads)
  iterations = (config_hodor.iterations/config_hodor.procs)/config_hodor.threads + threadrem
  threading.current_thread().name = str(int(threading.current_thread().name)*iterations)
  for i in xrange(iterations):
    if config_hodor.execdelay != 0: time.sleep(config_hodor.execdelay)
    handler(indata, fullmutate, plock, tlock)
    threading.current_thread().name = str(int(threading.current_thread().name)+1)

def build_logpaths():
  for handler in config_hodor.output_handler.itervalues():
    if "log" in handler and "path" in handler["log"]:
      if not os.path.exists(handler["log"]["path"]): os.makedirs(handler["log"]["path"])
    if handler == config_hodor.process: 
      if not os.path.isfile(handler["log"]["path"] + "crashlog.txt"):
        out_hodor.loghelper(handler["log"]["path"] + "crashlog.txt", "Crash Log\n", "w")
      if config_hodor.process["log"]["proc_out"]:
        if not os.path.exists(handler["log"]["path"]+"proc_out/"): os.makedirs(handler["log"]["path"]+"proc_out/")


def clean_kill(signal, frame):
  for p in pjobs:
    os.kill(p.pid, 9)
  sys.exit(0)


if __name__ == '__main__':
  main()

