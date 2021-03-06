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
    CBlock([cgen.Define("MAXFORBID", "32")]),

    Kernel("ipgc_init", [G.param()], [
        ForAll("node", G.nodes(), [
            CBlock(["graph.node_data[node] = 0"]),
            WL.push("node")
        ])
    ]), #initializing all nodes to color 0        

    Kernel("assignColors", [G.param()], [
        ForAll("node", G.nodes(), [
            CDecl([
                ("int", "FORBIDDEN", ""),
                ("int", "offset", "=0"),
                ("bool", "colored", "=false")
            ]),
            If("graph.node_data[node] == 0", [
                While("colored == false", [
                    CBlock(["FORBIDDEN = 0"]),
                    For("edge", G.edges("node"), [
                        CDecl([
                            ("index_type", "dst", "=graph.getAbsDestination(edge)"),
                            ("int", "color", "=graph.node_data[dst]")
                        ]), 
                        If("color >= offset && color < offset + MAXFORBID", [
                            CBlock(["FORBIDDEN |= (1<<(color-offset))"])
                            #should be atomic OR if forall
                        ])
                    ]),
                    If("~FORBIDDEN", [
                        CBlock([
                            "graph.node_data[node] = offset + __ffs(~FORBIDDEN) - 1",
                            "colored = true"
                        ])
                    ]),
                    CBlock(["offset += MAXFORBID"]),
                ])
            ])
        ])
    ]),

    Kernel("assignColors_wl", [G.param()], [
        ForAll("wlnode", WL.items(), [
            CDecl([
                ("int", "node", ""),
                ("bool", "pop", ""),
                ("int", "color", "=0")
            ]),
            WL.pop("pop", "wlnode", "node"), 
            CDecl([
                ("int", "FORBIDDEN", ""),
                ("int", "offset", "=0"),
                ("bool", "colored", "=false")
            ]),
            While("colored == false", [
                CBlock(["FORBIDDEN = 0"]),
                For("edge", G.edges("node"), [
                    #can be ForAll?
                    CDecl([
                        ("index_type", "dst", "=graph.getAbsDestination(edge)"),
                        ("int", "color", "=graph.node_data[dst]")
                    ]), 
                    If("color >= offset && color < offset + MAXFORBID", [
                        CBlock(["FORBIDDEN |= (1<<(color-offset))"])
                        #should be atomic OR if forall
                    ])
                ]),
                If("~FORBIDDEN", [
                    CBlock([
                        "graph.node_data[node] = offset + __ffs(~FORBIDDEN) - 1",
                        "colored = true"
                    ])
                ]),
                CBlock(["offset += MAXFORBID"]),
            ]),
        ])
    ]), #assigning new colors to all conflicting nodes

    Kernel("detectConflicts", [G.param()], [
        ForAll("node", G.nodes(), [
            CDecl(('bool', 'pop', '')),
            CBlock(["pop = node < graph.nnodes"], parse=False),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CDecl([("index_type", "dst", "=graph.getAbsDestination(edge)")]), 
                If("graph.node_data[dst] == graph.node_data[node] && dst < node", [
                    WL.push("node"),
                    CBlock(["graph.node_data[node] = 0"]),
                ])
            ]))
        ])
    ]), #detecting conflicting nodes

    Kernel("detectConflicts_wl", [G.param()], [
        ForAll("wlnode", WL.items(), [
            CDecl([
                ("int", "node", ""),
                ("bool", "pop", "")
            ]),
            WL.pop("pop", "wlnode", "node"),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CDecl([("index_type", "dst", "=graph.getAbsDestination(edge)")]), 
                If("graph.node_data[dst] == graph.node_data[node] && dst < node", [
                    WL.push("node"),
                    CBlock(["graph.node_data[node] = 0"]),
                ])
            ]))
        ])
    ]), #detecting conflicting nodes

    Kernel("removeDups_wl", [("int *", "dup_checker")], [
        ForAll("wlnode", WL.items(), [
            CDecl([
                ("int", "node", ""),
                ("bool", "pop", "")
            ]),
            WL.pop("pop", "wlnode", "node"),
            CBlock("dup_checker[node] = wlnode"),
        ]),
        GlobalBarrier().sync(),
        ForAll("wlnode2", WL.items(), [
            CDecl([
                ("int", "node", ""),
                ("bool", "pop", "")
            ]),
            WL.pop("pop", "wlnode2", "node"),
            If("dup_checker[node] == wlnode2", [
                WL.push("node"),
            ]),
        ]),
    ]),

    Kernel("gg_main", [GraphParam('hg', True), GraphParam('gg', True)], [
        CDecl([
            ("Shared<int>", "dup_checker", "(gg.nnodes)"),
            ("int", "flag", "=1"),
        ]),
        GlobalBarrier().setup("removeDups_wl"),
        # ClosureHint(Pipe([
        Pipe([
            Invoke("ipgc_init", ["gg"]),
            While("flag", [
                Invoke("assignColors", ["gg"]),
                Invoke("detectConflicts", ["gg"]),
                If("pipe.in_wl().nitems() <= 0.5 * gg.nedges", [
                    CBlock([
                        "flag = 0",
                    ]),
                ]),
            ]),
            ClosureHint(Pipe([ 
                Invoke("removeDups_wl", ["dup_checker.gpu_wr_ptr()"]),
                Invoke("assignColors_wl", ["gg"]),
                Invoke("detectConflicts_wl", ["gg"]),
            ])),
        # ], once=True, wlinit=WLInit("gg.nedges", []))),
        ], once=True, wlinit=WLInit("gg.nedges", [])),
    ])
])

