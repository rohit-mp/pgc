# Should be run in tools directory

tar -xzf grtools.tar.gz
cd grtools
python setup.py install --user                                          
cd ..
mv dim2gr1.py grtools/                                                  

mkdir binary_files
./download-graphs.sh
./tmd.sh
./rem_self_loops.sh
