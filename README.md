# GGC/CUDA Benchmark Skelapp Template

This repository provides code that lets you create IrGL benchmarks
that use the skelapp graph algorithm infrastructure. The skelapp
infrastructure allows you to parse command line arguments, load graphs
from disk, call the `gg_main` function, time it, as well as write
output from the computation to file. It is the infrastructure used by
all the IrGL benchmarks, though it is not necessary to use this --
merely convenient.

## Installation

Obtain ggc from [here](https://www.cs.rochester.edu/~sree/ggc/).

Run `./skelsetup.py setup $GGC` to setup the template directory,
 where `$GGC` is the root directory containing the ggc IrGL compiler.

This will create softlinks to `$GGC/rt` and `$GGC/skelapp` in the
template directory and also setup variables in `bmks/local.mk` to
point to `$GGC`.

## Compilation

The implementations of the benchmarks can be found in seperate 
folders in the `bmks` directory. (Assume `cc` is a benchmark for 
the rest of the section).

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
