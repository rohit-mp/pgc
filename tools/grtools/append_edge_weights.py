#!/usr/bin/env python

import grf
import sys
import argparse
import array
import gractions

def get_edge_weights(nedges, weight = 1):
    a = gractions.get_array_of_size('I', nedges)
    
    for i in range(nedges):
        a[i] = weight

    return a

p = argparse.ArgumentParser(description="Append/Overwrite edge weights to an existing graph file")

p.add_argument("graph", metavar="FILE", help="Graph file")
p.add_argument("-w", dest="weight", type=int, help="Weight to add", default=1)
p.add_argument("-f", dest="force", action="store_true", help="Overwrite existing edge weight data")
p.add_argument("--hdr", dest="hdr_only", action="store_true", help="Update header only", default=False)

args = p.parse_args()

gr = grf.GRGraph()
#gr.read(args.graph)

hdr = gr.read_hdr(args.graph)

if hdr.sizeEdgeTy > 0 and not args.force:
    print >>sys.stderr, "ERROR: Graph already has edge data! Use -f to overwrite."
    sys.exit(1)

print >>sys.stderr, "Edge data offset: %d" % (hdr.edgeDataOffset,)

f = open(args.graph, "r+")
gr.write_hdr(f, grf.GRHeader(version=1, sizeEdgeTy=4, numNodes = hdr.numNodes, numEdges = hdr.numEdges, edgeDataOffset=hdr.edgeDataOffset))

if not args.hdr_only:
    f.seek(hdr.edgeDataOffset, 0)
    a = get_edge_weights(hdr.numEdges, args.weight)
    a.tofile(f)

f.close()
