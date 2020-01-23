import bmk2
from irglprops import graph_coloring_bmk, PERF_RE, get_gc_checker

class ipgc_bit(graph_coloring_bmk):
	variant = 'ipgc_bit'
        
BINARIES = [ipgc_bit()]
