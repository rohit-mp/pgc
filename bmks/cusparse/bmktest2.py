import bmk2
from irglprops import graph_coloring_bmk, PERF_RE, get_gc_checker

class cusparse(graph_coloring_bmk):
	variant = 'cusparse'
        
BINARIES = [cusparse()]
