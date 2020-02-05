# grtools

grtools is a suite of programs for dealing with graph data stored
using the Galois `.gr` (v1) binary graph format.

## Pre-requisites

  - Cython 
  - Setuptools

## Installation

In the directory containing the source, run: 

  python setup.py install --user

Or:
	
  python setup.py develop --user

## Libraries

### grtools/grf.py

This contains a class for reading/writing .grf files.

Originally from the OM project.

### grtools/gractions.py

This contains Cython tools for manipulating CSR data in memory.

Originally from the OM project.


## Utilities

All utilities support the `-h` help option.

### crgr.py

Create a graph of a particular (memory) size.

### dim2gr.py

Convert a dimacs9 format graph (i.e. text file) to the Galois .gr format.

NOTE: This file has been changed to aid in mtx to dimacs to gr 
conversion.

### grtool.py

Various tools for Galois GR graph formats.
