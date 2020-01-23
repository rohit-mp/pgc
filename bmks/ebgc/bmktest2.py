import bmk2
from irglprops import graph_coloring_bmk, PERF_RE, get_gc_checker

class ebgc(graph_coloring_bmk):
	variant = 'ebgc'
        
BINARIES = [ebgc()]
