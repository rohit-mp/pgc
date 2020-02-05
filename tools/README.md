# Scripts to obtain input graphs

The README contains instructions to obtain the input graphs in the 
paper and convert it into appropriate graph format. The name of input 
graphs are in `graphs.txt` (which can be modified to obtain other
graphs)

All the below instrcutions are in the form of script in `get-graphs.sh`.

## Instructions

1. Look in grtools/README.md for python requirements necessary.

2. In `grtools`, run
```bash
$ python setup.py install --user
```

3. Download all graphs in `.mtx` format (Takes up about 5GB space)
```bash
$ ./download-graphs.sh
```

4. Convert all graphs to `.gr`
```bash
$ ./tmd.sh
```
This will quite a bit of time. The converted graphs will take upto 
15GB of space.

After this step, you may remove the downloaded graphs.

5. Remove self loops from converted graphs
```bash
$ ./remove-self-loops.sh
```

The required graphs will be in `binary_files` folder.
