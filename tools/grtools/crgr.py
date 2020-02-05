#!/usr/bin/env python


import grf
import sys
import array
import random
import argparse
import gractions

#nodes_size = 768*1048576
#max_edges_size = 2048*1048576

p = argparse.ArgumentParser(description="Create a graph spanning a size of memory")
p.add_argument("row_offset_size", help="Row offset size in bytes", type=int)
p.add_argument("edge_dst_size", help="Edge destination size in bytes", type=int)
p.add_argument("output", help="Output file")

args = p.parse_args()

nodes_size = args.row_offset_size
max_edges_size = args.edge_dst_size

num_nodes = nodes_size / 4 - 1 
max_edges_per_node = (max_edges_size / 4) / num_nodes

print "num_nodes", num_nodes
print "max_edges", num_nodes * max_edges_per_node

print "creating %d nodes" % (num_nodes,)
out = gractions.get_array_of_size('I', num_nodes)
for i in xrange(num_nodes):
    out[i] = random.randint(0, max_edges_per_node)

print "creating edges"
total_edges = sum(out)
edges_dst = gractions.get_array_of_size('I', total_edges)
for i in xrange(total_edges):
    edges_dst[i] = random.randint(0, num_nodes - 1)

print "creating row offset array"
s = 0
for i, j in enumerate(out):
    out[i] = s
    s += j
out.append(s)

assert len(out) * 4 <= nodes_size
assert len(edges_dst) * 4 <= max_edges_size

print "creating CSR graph"
g = grf.GRGraph()
g.from_arrays(out, edges_dst, move=True)
print "num_nodes", g.num_nodes
print "num_edges", g.num_edges

print "writing to file %s" % (args.output,)
g.write(args.output)
