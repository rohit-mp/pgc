The README contains instrcutions to obtain the input graphs in the 
paper and convert it into appropriate graph format.

All the below instrcutions are in the form of script in `get-graphs.sh`.

1. Untar `grtools.tar.gz`
```bash
$ tar -xzf grtools.tar.gz
```

`grtools` folder should is created.

2. Look in `GRTOOLS.md` for python requirements necessary.

3. In `grtools`, run
```bash
$ python setup.py install --user
```

4. Move `dim2gr1.py` into `grtools` folder.
```bash
$ mv dim2gr1.py grtools/
```

5. Download all graphs in `.mtx` format (Takes up about 5GB space)
```bash
$ ./download-graphs.sh
```

6. Convert all graphs to `.gr`
```bash
$ ./tmd.sh
```
This will quite a bit of time. The converted graphs will take upto 
15GB of space.

After this step, you may remove the downloaded graphs.

7. Remove self loops from converted graphs
```bash
$ ./rem_self_loops.sh
```

The required graphs will be in `binary_files` folder.
