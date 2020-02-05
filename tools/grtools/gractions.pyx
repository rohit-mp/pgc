# -*- mode: python -*-
from cpython cimport array
from cpython cimport bool
from collections import namedtuple

cdef extern from "limits.h":
    unsigned UINT_MAX

drop_return = namedtuple('drop_return', ['dropped', 'offsets', 'edges', 'edge_data'])

def get_degrees(g):
    """Given a graph, get the degrees of the nodes in the graph"""

    out = array.array('I')
    array.resize(out, g.num_nodes)

    cdef unsigned i
    cdef unsigned [:] outw = out
    cdef unsigned long [:] off = g.offsets
    cdef unsigned wli
    cdef unsigned [:] wlr
    cdef unsigned mindegree = UINT_MAX
    cdef unsigned maxdegree = 0

    for i in range(g.num_nodes):
        outw[i] = off[i+1] - off[i]

        assert off[i] < (g.num_edges + 1)

        if outw[i] > maxdegree: maxdegree = outw[i]
        if outw[i] < mindegree: mindegree = outw[i]
        
    return (out, mindegree, maxdegree)


def get_degree_freq(unsigned [:] deg, unsigned maxdeg):
    """Given a list of (unsigned) degrees, return a degree distribution"""
            
    out = array.array('I')
    array.resize(out, maxdeg+1)  # overkill?, zero-init?
    array.zero(out)

    cdef unsigned i

    for i in range(len(deg)):
        out[deg[i]] += 1

    return [(k, v) for k, v in enumerate(out) if v != 0]

def count_loops_and_multi_edges(g):
    """Given a graph, return a count of self-loops and multiple edges"""
            
    cdef unsigned n
    cdef unsigned e
    cdef unsigned long [:] off = g.offsets
    cdef unsigned int [:] dsts = g.edges
    cdef unsigned rs, re
    cdef unsigned loops = 0
    cdef unsigned multi_edges = 0

    for n in range(g.num_nodes):
        rs = off[n]
        re = off[n+1]

        assert rs < (g.num_edges + 1)
        assert re < (g.num_edges + 1)
        assert rs <= re

        d = set()

        for e in range(rs, re):
            if dsts[e] == n:
                loops += 1

            if dsts[e] in d:
                multi_edges += 1
            else:
                d.add(dsts[e])
            
    return (loops, multi_edges)

def drop_edges(g, bool drop_loops = False, bool drop_multi_edges = False):
    """Given a graph, drop self-loops and multiple edges"""

    out_offsets = array.array(g.offsets.typecode)
    array.resize(out_offsets, g.num_nodes + 1)

    out_edges = array.array(g.edges.typecode)
    array.resize(out_edges, g.num_edges)
            
    cdef unsigned n
    cdef unsigned e
    cdef unsigned long [:] off = g.offsets
    cdef unsigned int [:] dsts = g.edges
    cdef unsigned rs, re
    cdef unsigned loops = 0
    cdef unsigned multi_edges = 0
    cdef unsigned edge_ptr = 0
    cdef unsigned prev_node_start = 0
    cdef bool has_edge_data = hasattr(g, 'edge_data')
    cdef unsigned int [:] edge_data
    cdef unsigned int [:] out_edge_data_p

    if has_edge_data:
        edge_data = g.edge_data
        out_edge_data = array.array(g.edge_data.typecode)
        array.resize(out_edge_data, g.num_edges)
        out_edge_data_p = out_edge_data

    for n in range(g.num_nodes):
        rs = off[n]
        re = off[n+1]

        assert rs < (g.num_edges + 1)
        assert re < (g.num_edges + 1)

        d = set()
        for e in range(rs, re):
            if drop_loops and dsts[e] == n:
                loops += 1
                continue

            if drop_multi_edges:
                if dsts[e] in d:
                    multi_edges += 1
                    continue

                d.add(dsts[e])
            
            out_edges[edge_ptr] = dsts[e]
            if has_edge_data:
                out_edge_data_p[edge_ptr] = edge_data[e]

            edge_ptr += 1

        out_offsets[n] = prev_node_start
        prev_node_start = edge_ptr


    cdef unsigned int new_edges = edge_ptr

    assert new_edges == g.num_edges - (loops + multi_edges)

    out_offsets[g.num_nodes] = new_edges
    array.resize(out_edges, new_edges)
    
    if has_edge_data:
        array.resize(out_edge_data, new_edges)
    
    if has_edge_data:
        return drop_return(loops + multi_edges, out_offsets, out_edges, out_edge_data)
    else:
        return drop_return(loops + multi_edges, out_offsets, out_edges, None)

def get_array_of_size(typecode, unsigned int N, zero = False):
    out = array.array(typecode)
    array.resize(out, N)
    if zero:
        array.zero(out)

    return out


