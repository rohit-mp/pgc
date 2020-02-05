#!/usr/bin/env python

import grf
import sys
import argparse
import gractions
import array

def execute_info(rdr, graph):
    nfo = rdr.read_hdr(graph)

    print "file: %s" % (graph,)
    print "version: %d" % (nfo.version)
    print "sizeEdgeTy: %d" % (nfo.sizeEdgeTy)
    print "nodes: %d" % (nfo.numNodes)
    print "edges: %d" % (nfo.numEdges)

def execute_stats(rdr, graph):
    rdr.read(graph)
    nfo = rdr.hdr

    degrees, mindeg, maxdeg = gractions.get_degrees(rdr)
    freq_dist = gractions.get_degree_freq(degrees, maxdeg)
    loops, multi_edges = gractions.count_loops_and_multi_edges(rdr)

    print "file: %s" % (graph,)
    print "version: %d" % (nfo.version)
    print "sizeEdgeTy: %d" % (nfo.sizeEdgeTy)
    print "nodes: %d" % (nfo.numNodes)
    print "edges: %d" % (nfo.numEdges)

    print "max_degree: %d" % (maxdeg)
    print "min_degree: %d" % (mindeg)

    fd = dict(freq_dist)
    print fd

    print "zero-degree nodes: %d (%0.2f%%)" % (fd.get(0, 0), 100.0 * fd.get(0, 0) / nfo.numNodes)
    print "self-loops: %d (%0.2f%%)" % (loops, 100.0 * loops / nfo.numEdges)
    print "multi_edges: %d (%0.2f%%)" % (multi_edges, 100.0 * multi_edges / nfo.numEdges)

    #print "degree distribution:"
    #for d, f in freq_dist:
    #    print "\t %5d: %5d" % (d, f)


def execute_dump(rdr, graph, output):
    rdr.read(graph)

    f = open(output, "w")

    print >>f, "%d %d" % (rdr.num_nodes, rdr.num_edges)

    for n in range(rdr.num_nodes):
        for e in range(rdr.offsets[n], rdr.offsets[n+1]):
            if hasattr(rdr, 'edge_data'):
                print >>f, "%d %d %d" % (n+1, rdr.edges[e]+1, rdr.edge_data[e])
            else:
                print >>f, "%d %d" % (n+1, rdr.edges[e]+1)

    f.close()

p = argparse.ArgumentParser(description="Tools for manipulating Galois GR files")

p.add_argument("graph", metavar="FILE", help="Graph file")
sub = p.add_subparsers(dest="cmd")

ip = sub.add_parser("info")
sp = sub.add_parser("stats")
mp = sub.add_parser("modify")
dp = sub.add_parser("dump")
mp.add_argument("output", metavar="FILE", help="Output file")
mp.add_argument("--drop-loops", action="store_true", help="Drop self-loops")
mp.add_argument("--drop-multi-edges", action="store_true", help="Drop multiple edges to same destination")
mp.add_argument("--add-edge-weight", choices=['0', '1'], help="Add edge weights")
dp.add_argument("output", metavar="FILE", help="Output file")

args = p.parse_args()

gr = grf.GRGraph()

if args.cmd == "info":
    execute_info(gr, args.graph)
elif args.cmd == "stats":
    execute_stats(gr, args.graph)
elif args.cmd == "dump":
    execute_dump(gr, args.graph, args.output)
elif args.cmd == "modify":
    execute_info(gr, args.graph)
    gr.read(args.graph)

    if args.add_edge_weight is not None:
        if hasattr(gr, 'edge_data'):
            print "ERROR: Cannot add edge data if already present"
            sys.exit(1)

    if args.drop_loops or args.drop_multi_edges:
        out = gractions.drop_edges(gr, drop_loops=args.drop_loops, drop_multi_edges=args.drop_multi_edges)
        print "Dropped %d edges (%0.2f%%)" % (out.dropped, 100.0 * out.dropped / gr.num_edges)

        o = grf.GRGraph()
        o.num_nodes = gr.num_nodes
        o.num_edges = len(out.edges)

        o.offsets = out.offsets
        o.edges = out.edges

        if out.edge_data is not None:
            o.edge_data = out.edge_data
            
        gr = o

    if args.add_edge_weight is not None:
        gr.edge_data = array.array('I', [int(args.add_edge_weight)]*gr.num_edges)

    print "Saving to", args.output, "(%d, %d)" % (gr.num_nodes,gr.num_edges)
    gr.write(args.output)

    


    
