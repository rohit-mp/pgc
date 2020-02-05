# tar.gz to mtx to dim

# matrices files contains list of all matrices to be converted
cat graphs.txt | while read matrix
do
    echo "Converting $matrix to binary format..."
    tar xvOzf "$matrix.tar.gz" "$matrix/$matrix.mtx" | awk -f mtx2dim.awk | grtools/dim2gr.py "binary_files/$matrix.sym.gr" 
    echo
done

