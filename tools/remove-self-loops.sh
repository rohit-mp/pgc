for graph in binary_files/*.gr
do
	echo $graph
	grtools/grtool.py $graph modify --drop-loops $graph
	echo
done

