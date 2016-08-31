# Hodor Fuzzer :

We want to design a general-use fuzzer that can be configured to use known-good
input and delimiters in order to fuzz specific locations. Somewhere between a
totally dumb fuzzer and something a little smarter, with significantly less effort
than with implementation of a proper smart fuzzer. Hodor.

We've had a few projects where a tool like this would have been useful. It's not
uncommon to have some sort of case where we have known good input and want to
modify it. If we know a bit about the file/protocol/etc spec, this could be
used to easily do slightly smarter fuzzing.

The design is intended to be portable so that one can just drop the files onto
any box with python 2.7 and get cracking.

Joel St. John, Braden Hollembaek, and Frank Arana


**NOTE: POKE AROUND THE CONFIG FILE BEFORE RUNNING**  

Examples of usage:  
>`python hodor.py -t testfiles/test.txt` Mutate delimited text from test.txt  
`python hodor.py -t testfiles/test.txt -f ` Mutate all text from test.txt    
`python -c "print 'A' * 50" | python hodor.py -t -f` Pipe in input from another program, mutate all input  
`python hodor.py -b testfiles/bintest.png > diff.png` Mutate binary file at ranges specified in config_hodor.bin_fields (not compatible with qpq mode)  
Show where the files differ [address] [file1 hex] [file2 hex]:  
`cmp -l bintest.png diff.png | gawk '{printf "%08X %02X %02X\n", $1, strtonum(0$2), strtonum(0$3)}'`

### WISH LIST:
* Make bflipper better
* Add more mutators and ability to use multiple types simultaneously
* Add features to qpq mode
	- Binary mode
	- Named-delimiters that allow for swap of same thing in all tokens of same name
	- Swap multiple tokens at once
* Add more token handling features

---


# Hodor Manual
A general-use fuzzer that can be configured to use known-good input and delimiters in order to fuzz specific locations.

Somewhere in between a dumb fuzzer and a proper smart fuzzer. Hodor.

## Table of Contents
* <a href="#filetypes">Filetypes</a>  
* <a href="#mutationmethods">Mutation Methods</a>  
* <a href="#postmutation">Post Mutation Handler</a>  
* <a href="#outputmutations">Outputting Mutations</a>  
* <a href="#performance">Performance</a>  

<a name="filetypes"></a>
## Filetypes

The first question is what kind of file are you mutating? Choosing a filetype is done at the command line.
(i.e. `python hodor.py -b binfile` or `python hodor.py -t file.txt`)

### Full mutation:
If you want to mutate the entire file sparing nothing, use the `-f` option. (i.e. `python hodor.py -t file.txt -f`)

### Mutating file segments:
#### Binary Files  
 Use `bin_fields` to choose which bytes to mutate in the binary.  

Example:  
If `bin_fields = [(0x3,0x7)]`  
First 16 bytes of the original file:  
`0000000: 8950 4e47 0d0a 1a0a 0000 000d 4948 4452  .PNG........IHDR`  
A few mutations:  
`0000000: 8950 4e55 0d0a 1a0a 0000 000d 4948 4452  .PNU........IHDR`  
`0000000: 8950 4e46 0d0a 1a0a 0000 000d 4948 4452  .PNF........IHDR`  
`0000000: 8950 4e47 0d0a 330a 0000 000d 4948 4452  .PNG..3.....IHDR`  
`0000000: 8950 4e47 0dd9 1a0a 0000 000d 4948 4452  .PNG........IHDR`  

**Note:** In Python's slicing, 0x3 does not get modified and is the byte before selection while 0x7 is the last byte to be mutated. A mathematical representation of this interval is (0x3, 0x7]

#### For text files
Use `text_delimiter` to decide which parts of your text will be mutated.  

Example:  
If `text_delimiter = "@@"`   
Original file:  `In @@West Philadelphia@@ born and raised `  
Mutated output:  `In We_t Ih��a]Ih��al
hi| born and raised`

<a name="mutationmethods"></a>
## Mutation Methods

Hodor has several mutation methods implemented for use.

### Millerfuzz
The classic dumb fuzz algorithm by Charlie Miller. Millerfuzz mutation uses `FuzzFactor` to determine how minute the fuzzing will be. The higher the value in `FuzzFactor`, the more minute the mutation.

### Quid Pro Quo (QPQ)
Quid Pro Quo is currently only partially implemented.  

Swap out tokens from the seed file with specific tokens of your choosing. If you specify more than one file, they will be aligned with each token from input in same order. If more than one file, you need to have same number of files as tokens for it to function correctly.

For example, if you specify two files and have two tokens, the first token will be iteratively replaced by things from the first file, and the second token will be iteratively replaced with items from the second file. Only one change is made per output.

Example:  
`qpq = {"file" : ["qpqfiles/qpqtest.txt", "qpqfiles/qpqtest2.txt"], 
"swapmode" : "oneatatime"}`

### TotesRand
Replace the token with totally randomly output generated from Python's random.randrange()

### BFlipper
Flip a determined amount of bits. Set `flipmode` to the number of bits to flip at once. If there are more iterations than bits, flipmode will increase automatically. BFlipper is deterministic.

<a name="postmutation"></a>
## Post Mutation Handler

### CRC32 Fixup
Hodor can compute and add a CRC32 checksum to the newly-mutated token. The CRC32 module has a few fields to configure:

#### Type
Can either be set for binary or text files.  
Options:   `"type" : "bin"` or `"type" : "text"`

#### Input_fields
Works very similarly to `bin_fields` from the binary mutation section. All of the segments listed will be used to calculate the checksum. If `input_fields : None`, then the entire mutation will be used for computation and automatically append the sum to the end of the file.

Example:  
`input_fields : [(0x12, 0x15), (0x4f, 0x5a)]` will compute the checksum for all segments *in the order listed*.

**Note:** Remember, Python slices use the interval (x,y]

#### Sum_location
This designates where where to begin overwriting the location specified to insert the checksum. If set to `None` the sum will be appended to the end of the mutation.

**Note:** `sum_location` cannot be a value that intercepts with any interval from `input_fields`, and `sum_location` will go unchecked if `input_fields` is set to `None`   

Example:  
`sum_location : [(0x0)]` will start overwriting the at the beginning of the file.

<a name="outputmutations"></a>
## Outputting Mutations
What to do with the mutations. Logging is done differently per module.  

### Stdout
Print mutations directly to stdout. No other logging is done.

### Network  
Send mutation to network, indicate target and where to log results, 'file' will write unique files to specified directory.

#### Connection

The target host and port are set in `network`.

Example:  
`network = {"remotehostport" : ("localhost", 1234)`

Specify connection type by setting `ssl` to `True` or `False`.

#### Logging

Two options are available for logging. Using `file` allows to set a directory to write output to, and `stdout` will print to standard out.
 
Example:  

`"log" : {"file" : "results/" }`

### Disk 
Write mutations as separate files into directory specified in `disk`

Example:
`disk = results/` will create the directory `results` in the current working directory, and store mutations within.

### Process
Automatically send mutation to specified process. Hodor will log if the program crashes, or if the maximum wait time is reached. Either way the process is terminated and then the next iteration will begin.

#### Name
The name of the executable to run. 
 
Example: `"name" : "readelf"`

#### Arguments  
Use `arguments` to add any arguments needed to run the executable listed in `name`.  

Example: `"arguments" : "-h"` will run `readelf -h`.   

If the mutation needs to be a command-line argument, set `"file_arg" : True`. If set to `False` the mutation will be send to the process as stdin.

If the mutation needs a particular file extension use `extension` to designate it.

Example: `"extension" : ".mp3"`

Combining all the examples listed in this section, Hodor will execute `readelf -h mutation.mp3`

#### Wait Time  
How long to wait before terminating an iteration of process if it does not crash.
  
Example:  
Setting `"timeout" : 5` `"steps" : .3` Will check every .3 seconds to see if the process has crashed, and terminate at the final wait time of five seconds.

#### Logging in process
Handles how and what is stored through every iteration. These are located within the `log` portion of the process configuration.  

##### What is always stored
Some logs are automatically generated without configuration. A file `crashlog.txt` will be created containing every crash that occurs in the `path` directory specified.

##### How crashes are logged  
All files generated by logging will be located in `path`.  
Example:  
`"path" : "results/"` will create the directory `results` in the current working directory, and store log files within.  

##### Logging Options
Aside from `crashlog.txt`, setting `"mutations" : True` means every crash will have the offending mutation saved to a directory named after the terminating signal.  

Similarly, `"proc_out" : True` will record the stdout and stderr of *every* process to a text file. Including processes that do not crash.

<a name="performance"></a>
## Performance
### Execution Delays
Delays each mutation iteration. Useful for not flooding a network target. Values are measured in seconds.

Example:  
`execdelay = .1` will delay every iteration by one-tenth of a second. 

### Processes
The amount of parallel iterations running at one time. It is recommended to only have one process per CPU core. Defined as `proc`.

### Threads
Number of threads per-process to be used to handle the iterations. Useful for optimizing against I/O bound fuzzing.

### Iterations
This is number of total iterations, and will be divided among procs and threads. Any number not divisible by procs*threads will just get the remainder dumped onto the last thread.


---

That's it. Go find bugs!
