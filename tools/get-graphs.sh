# Should be run in tools directory

cd grtools
python setup.py install --user                                          
cd ..

mkdir binary_files
./download-graphs.sh
./tmd.sh
./remove-self-loops.sh
