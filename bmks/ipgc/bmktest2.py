import bmk2
from irglprops import graph_coloring_bmk, PERF_RE, get_gc_checker

class ipgc_wl(graph_coloring_bmk):
	variant = 'ipgc_wl'
        
BINARIES = [ipgc_wl()]
