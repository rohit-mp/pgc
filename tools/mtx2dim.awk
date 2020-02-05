BEGIN {read_dim=0; sym = 2} # sym : 1 = unsym, 2 = sym

/^%%MatrixMarket/ {
    if($5 == "symmetric") sym = 2;
}

/^[0-9]/ {
    if(read_dim == 0) {
        read_dim = 1; 
        print "p edge " $1, $3*sym
    } 
    else {
        print "e", $1, $2
        if(sym == 2) {
            print "e", $2, $1
        }
    }
}

