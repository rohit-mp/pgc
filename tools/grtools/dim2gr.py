#!/usr/bin/python
# -*- coding: utf-8 -*-

import grf
import sys
import array
import random
import argparse
import gractions

# nodes_size = 768*1048576
# max_edges_size = 2048*1048576

if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Convert a graph from DIMACS to GR')
    #p.add_argument('input', help='Input DIMACS')
    p.add_argument("output", help="Output file")

    args = p.parse_args()

    num_nodes = None
    num_edges = None
    edges = []
    for l in sys.stdin:
        if l[0] == 'p':
            ls = l.strip().split()
            if ls[1] == 'edge':
                assert num_nodes is None

                num_nodes = int(ls[2])
                num_edges = int(ls[3])
            else:
                raise NotImplementedError
        elif l[0] == 'e':
            ls = l.strip().split()
            edges.append((int(ls[1]) - 1, int(ls[2]) - 1))
        else:
            pass

    edges = sorted(edges)

    print 'num_nodes', num_nodes
    print 'num_edges', num_edges

    assert num_edges == len(edges)

    print 'creating %d nodes' % (num_nodes, )
    out = gractions.get_array_of_size('I', num_nodes, True)

    for e in edges:
        out[e[0]] += 1

    print 'creating edges'
    edges_dst = gractions.get_array_of_size('I', num_edges, True)

    for i in xrange(num_edges):
        edges_dst[i] = edges[i][1]

    print 'creating row offset array'
    s = 0
    for (i, j) in enumerate(out):
        out[i] = s
        s += j

    out.append(s)

    # TODO: edge weights

    print 'creating CSR graph'
    g = grf.GRGraph()
    g.from_arrays(out, edges_dst, move=True)
    print 'num_nodes', g.num_nodes
    print 'num_edges', g.num_edges

    print 'writing to file %s' % (args.output, )
    g.write(args.output)

