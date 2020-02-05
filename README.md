# Parallel Graph Coloring on GPU
This repo contains source code for our paper "A Hybrid Graph 
Coloring Algorithm for GPUs" ([link](https://arxiv.org/abs/1912.01478)). 
We have re-implemented Iterative Parallel Graph Coloring (IPGC) and 
Edge Based Graph Coloring based on [this](https://ieeexplore.ieee.org/document/7516086) 
previous work. 

For IPGC, we have an optimized version of the algorithm that performs 
36% faster than the previous work on average. A key optimization for 
our algorithm was to heuristically choose between two modes of graph 
traversal.

## Installation

Obtain ggc from [here](https://www.cs.rochester.edu/~sree/ggc/).

Run `./skelsetup.py setup $GGC` to setup the template directory,
 where `$GGC` is the root directory containing the ggc IrGL compiler.

This will create softlinks to `$GGC/rt` and `$GGC/skelapp` in the
template directory and also setup variables in `bmks/local.mk` to
point to `$GGC`.

Also, the python packages `cgen` and `toposort` are required.

## Compilation

The implementations of the benchmarks can be found in seperate 
folders in the `bmks` directory. (Assume `cc` is a benchmark for 
the rest of the section).

Run `make` in the `cc` directory. If everything went well, you should
have see generated code in `../gensrc/cc`, with the following files:

  1. A `kernel.cu` file (the compiled `cc.py`)
  2. A `support.cu` file (a soft-linked `cc_support.cu`)
  3. A `Makefile` to compile this using CUDA

Run `make` in this directory to get `test_nontex`, a binary that can be
 run.  

__Note:__ IrGL optimizations provide better results. Running make in `bmks/ipgc_bit` with additional flags provides the best results:
```bash
make GGCFLAGS="--opt np --npf 8 --opt parcomb --opt oitergb"
```

## Setup benchmark configuration

`bmk2cfg` contains the benchmark configuration for `bmk2` benchmark
tool.

`bmk2cfg/irgl.inputdb` contains the graphs used for benchmarking. 
Change the basepath in line 2 to the path of the directory in your 
system which contains the graphs.

In the `basepath`, the `.gr` format graphs are assumed to be in 
`binary_files` directory, the `.mtx` format graphs are assumed to 
be in `mtx_files` directory and kokkos graphs in `kokkos_binaries`.

## Obtaining input graphs

`tools` folder has the scripts to obtain the input graphs in the paper
and converting them to the format expected by `ggc`.
