# GGC/CUDA Benchmark Skelapp Template

This repository provides code that lets you create IrGL benchmarks
that use the skelapp graph algorithm infrastructure. The skelapp
infrastructure allows you to parse command line arguments, load graphs
from disk, call the `gg_main` function, time it, as well as write
output from the computation to file. It is the infrastructure used by
all the IrGL benchmarks, though it is not necessary to use this --
merely convenient.


## Installation

Run `./skelsetup.py setup $GGC` to setup the template directory,
 where `$GGC` is the root directory containing the ggc IrGL compiler.

This will create softlinks to `$GGC/rt` and `$GGC/skelapp` in the
template directory and also setup variables in `bmks/local.mk` to
point to `$GGC`.
   
## Create a benchmark directory from the template

Let's suppose the benchmark name is `cc`.

Run `./skelsetup.py create cc` to create a new directory `bmks/cc`.

## Create your code

The default `Makefile` assumes your project structure (for the `cc`
example) will be:

  1. A `cc.py` file containing the IrGL code and the `gg_main` function.
  2. A `cc_support.cu` file that contains auxiliary routines for use with skelapp.

Modify `cc_support.cu` as you see fit.

Add your IrGL code to `cc.py`.

## Compile your code

Run `make` in the `cc` directory. If everything went well, you should
have see generated code in `../gensrc/cc`, with the following files:

  1. A `kernel.cu` file (the compiled `cc.py`)
  2. A `support.cu` file (a soft-linked `cc_support.cu`)
  3. A `Makefile` to compile this using CUDA

Run `make` in this directory to get `test`, a binary that can be run.

## Setup benchmark configuration

`bmk2cfg` contains the benchmark configuration for `bmk2` benchmark
tool.

`bmk2cfg/irgl.inputdb` contains the graphs used for benchmarking. 
Change the basepath in line 2 to the path of the directory in your 
system which contains the graphs.

In the `basepath`, the `.gr` format graphs are assumed to be in 
`binary_files` directory, the `.mtx` format graphs are assumed to 
be in `mtx_files` directory and kokkos graphs in `kokkos_binaries`.