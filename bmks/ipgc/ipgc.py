# -*- mode: python -*-

from gg.ast import *
from gg.lib.graph import Graph
from gg.lib.wl import Worklist
from gg.ast.params import GraphParam

import cgen

G = Graph("graph")
WL = Worklist()

ast = Module([
    CBlock([
        "typedef int edge_data_type",
        "typedef int node_data_type"
    ]),

    Kernel("ipgc_init", [G.param(), ("int *", "max_degree")], [
        ForAll("node", G.nodes(), [
            CBlock([
                "graph.node_data[node] = 0",
                "atomicMax(max_degree, graph.getOutDegree(node))" 
            ]),
            WL.push("node")
        ])
    ]), #initializing all nodes to color 0        

    Kernel("assignColors", [G.param(), ("bool *", "forbidden"), ("int *", "max_degree")], [
        ForAll("wlnode", WL.items(), [
            CDecl([
                ("int", "node", ""),
                ("bool", "pop", ""),
                ("int", "color", "=0")
            ]),
            WL.pop("pop", "wlnode", "node"), 
            ForAll("edge", G.edges("node"), [
                CDecl([("index_type", "dst", "=graph.getAbsDestination(edge)")]),
                CBlock(["forbidden[max_degree[0] * node + graph.node_data[dst]] = true"]),
            ]),
            While("forbidden[max_degree[0] * node + color]==true", [
                CBlock(["color++"]),
            ]),
            #R: do we need a sync_threads here to make sure forbidden of all nodes is calculated before updating any node?
            CBlock(["graph.node_data[node] = color"]),
            WL.push("node")
        ])
    ]), #assigning new colors to all conflicting nodes

    Kernel("detectConflicts", [G.param()], [
        ForAll("wlnode", WL.items(), [
            CDecl([
                ("int", "node", ""),
                ("bool", "pop", "")
            ]),
            WL.pop("pop", "wlnode", "node"),
            ForAll("edge", G.edges("node"), [
                CDecl([("index_type", "dst", "=graph.getAbsDestination(edge)")]), 
                If("graph.node_data[dst] == graph.node_data[node] && dst < node", [
                    WL.push("node")
                ])
            ])
        ])
    ]), #detecting conflicting nodes

    Kernel("gg_main", [GraphParam('hg', True), GraphParam('gg', True)], [
        CDecl([("Shared<int>", "max_degree", "(1)")]),
        Pipe([
            Invoke("ipgc_init", ["gg", "max_degree.zero_gpu()"]),
            CDecl([("Shared<bool>", "forbidden", "(gg.nnodes * (max_degree.cpu_rd_ptr())[0]+1)")]),
            Pipe([ 
                Invoke("assignColors", ["gg", "forbidden.zero_gpu()", "max_degree.gpu_rd_ptr()"]),
                Invoke("detectConflicts", ["gg"]),
            ]),
        ], once=True, wlinit=WLInit("100*gg.nnodes", [])) #this might be a reason why it's not working.. but then ipgc_bit is working.. so idk
        #wlinit=WLInit("2*gg.nedges", []))
    ])
])
