#*- mode: python -*-
 
from gg.ast import *
from gg.lib.graph import Graph
from gg.lib.wl import Worklist
from gg.ast.params import GraphParam

import cgen

G = Graph("graph")
WL = Worklist() # EdgeList

ast = Module([
    CBlock([
        "typedef int edge_data_type",
        "typedef int node_data_type"
    ]),

    Kernel("ebgc_init", [G.param(), ("int *", "edge_src"), ("int *", "VForbidden"), ("int *", "CS"), ("int *", "TVForbidden")], [
        ForAll("node", G.nodes(), [
            CBlock([
                "graph.node_data[node] = 0",# 0 represents not colored
                "VForbidden[node] = 0",
                "TVForbidden[node] = 0",
                "CS[node] = 0"
            ]),
            CDecl(('bool', 'pop', '')),
            CBlock(["pop = node < graph.nnodes"], parse=False),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CBlock([("edge_src[edge] = node")]), 
            ]))
        ])
    ]), #initializing all nodes to color 0 (not colored), pushing edges to edgelist and setting edge_src

    Kernel("assignColors", [G.param(), ("int *", "CS"), ("int *", "VForbidden"), ("int *", "TVForbidden")], [
        ForAll("node", G.nodes(), [
            CDecl([("int", "AllForbid", "=0")]),
            If("graph.node_data[node] < 0", [
                CBlock(["graph.node_data[node] = -graph.node_data[node]"]),      
            ]),
            If("graph.node_data[node] == 0", [
                CBlock(["AllForbid = VForbidden[node] | TVForbidden[node]"]),
                If("AllForbid != 0x7fffffff", [ # 31 colors
                    CBlock(["graph.node_data[node] = 1<<(__ffs(~AllForbid)-1)"]),
                ]),
                If("AllForbid == 0x7fffffff && VForbidden[node] == 0x7fffffff", [ 
                    CBlock([
                        "CS[node] = CS[node] + 1",
                        "VForbidden[node] = 0",
                        "TVForbidden[node] = 0"
                    ])
                ]),
            ]),
        ]),
    ]), #assigning new colors to all conflicting nodes

    Kernel("detectConflicts", [G.param(), ("int *", "edge_src"), ("int *", "CS")], [
        ForAll("node", G.nodes(), [
            CDecl(('bool', 'pop', '')),
            CBlock(["pop = node < graph.nnodes"], parse=False),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CDecl([
                    ('int', 'u', '= edge_src[edge]'),
                    ('int', 'v', '= graph.getAbsDestination(edge)')
                ]),
                If("CS[u] == CS[v] && graph.node_data[u] == graph.node_data[v] && u < v", [
                    CBlock(["graph.node_data[v] = 0"]), # uncolor node v
                    # WL.push("edge"),
                ]),
            ])),
        ]),
    ]), #detecting conflicting nodes


    Kernel("createNewEdgeList", [G.param(), ("int *", "edge_src"), ("int *", "CS"), ("int *", "VForbidden")], [
        ForAll("node", G.nodes(), [
            CDecl(('bool', 'pop', '')),
            CBlock(["pop = node < graph.nnodes"], parse=False),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CDecl([
                    ('int', 'u', '= edge_src[edge]'),
                    ('int', 'v', '= graph.getAbsDestination(edge)')
                ]),
                #S: Point 2 in opt 3 doesn't make sense to me
                #R: makes sense, u is colored and v is not, meaning they were conflicting and v was uncolored and finalized the color of u. So the next time v is colored, VForbidden will prevent it from getting the same color as u.
                If("graph.node_data[u] == 0 || graph.node_data[v] == 0", [ # Case 1 edges don't enter
                    If("graph.node_data[u] > 0", [
                        If("CS[u] > CS[v]", [ # Case 3 edges don't enter
                            WL.push("edge"),
                        ]), 
                        If("CS[u] == CS[v]", [
                            If("(VForbidden[v] & graph.node_data[u]) == 0", [ # Case 2 edges nodes don't enter
                                WL.push("edge"),   
                            ])   
                        ])
                    ]), 
                    If("graph.node_data[v] > 0", [
                        If("CS[v] > CS[u]", [
                            WL.push("edge"),
                        ]),
                        If("CS[u] == CS[v]", [
                            If("(VForbidden[u] & graph.node_data[v]) == 0", [
                                WL.push("edge"),
                            ])
                        ])

                    ]),
                    If("graph.node_data[u] == 0 && graph.node_data[v] == 0", [ # If both are uncolored, push!
                        WL.push("edge")   
                    ])
                ]),
            ])),
        ]) 
    ]), # Selectively remove unnecessary edges

    Kernel("forbidColors", [G.param(), ("int *", "edge_src"), ("int *", "VForbidden"), ("int *", "CS")], [
        ForAll("node", G.nodes(), [
            CDecl(('bool', 'pop', '')),
            CBlock(["pop = node < graph.nnodes"], parse=False),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CDecl([
                    ('int', 'u', '= edge_src[edge]'),
                    ('int', 'v', '= graph.getAbsDestination(edge)')
                ]),
                If("CS[u] == CS[v]", [
                    If("graph.node_data[u] == 0 && graph.node_data[v] != 0", [
                        CBlock([("atomicOr(&VForbidden[u], graph.node_data[v])")]) 
                    ]),
                    If("graph.node_data[u] != 0 && graph.node_data[v] == 0", [
                            CBlock([("atomicOr(&VForbidden[v], graph.node_data[u])")])  
                    ])
                ]),
            ]))
        ])
    ]), # forbid colors for conflicting nodes

    Kernel("preproceesTentative", [G.param(), ("int *", "TVForbidden")], [
        ForAll("node", G.nodes(), [
            CBlock(["TVForbidden[node] = 0"]),
        ])   
    ]),

    Kernel("tentativeColor", [G.param(), ("int *", "edge_src"), ("int *", "VForbidden"), ("int *", "CS"), ("int *", "TVForbidden")], [
        ForAll("node", G.nodes(), [
            CDecl(('bool', 'pop', '')),
            CBlock(["pop = node < graph.nnodes"], parse=False),
            ClosureHint(ForAll("edge", G.edges("node"), [
                CDecl([
                    ('int', 'u', '= edge_src[edge]'),
                    ('int', 'v', '= graph.getAbsDestination(edge)'),
                    ('int', 'AllForbid', ''),
                ]),
                If("CS[u] == CS[v]", [
                    If("graph.node_data[u] == 0 && graph.node_data[v] == 0 && u < v", [
                        CBlock(["AllForbid = VForbidden[v] | TVForbidden[v]"]),
                        If("AllForbid != 0x7fffffff", [
                            CBlock([
                                "graph.node_data[v] = -(1<<(__ffs(~AllForbid)-1))",
                                "atomicOr(&TVForbidden[u], -graph.node_data[v])"
                            ])
                        ])
                    ]),
                    If("graph.node_data[u] < 0 && graph.node_data[v] == 0", [
                        CBlock(["atomicOr(&TVForbidden[v], -graph.node_data[u])"])
                    ]),
                    If("graph.node_data[u] == 0 && graph.node_data[v] < 0", [
                        CBlock(["atomicOr(&TVForbidden[u], -graph.node_data[v])"])
                    ]),
                    If("graph.node_data[u] < 0 && graph.node_data[v] < 0 && graph.node_data[u] == graph.node_data[v] && v < u", [
                        CBlock(["AllForbid = VForbidden[v] | TVForbidden[v]"]),
                        If("AllForbid != 0x7fffffff", [
                            CBlock([
                                "graph.node_data[v] = -(1<<(__ffs(~AllForbid)-1))",
                                "atomicOr(&TVForbidden[u], -graph.node_data[v])"
                            ])
                        ])
                    ])
                ]),
            ]))
        ]),
    ]), #tentatively color conflicting nodes (for less number of iterations)











    
    Kernel("assignColors_wl", [G.param(), ("int *", "CS"), ("int *", "VForbidden"), ("int *", "TVForbidden")], [
        ForAll("node", G.nodes(), [
            CDecl([("int", "AllForbid", "=0")]),
            If("graph.node_data[node] < 0", [
                CBlock(["graph.node_data[node] = -graph.node_data[node]"]),      
            ]),
            If("graph.node_data[node] == 0", [
                CBlock(["AllForbid = VForbidden[node] | TVForbidden[node]"]),
                If("AllForbid != 0x7fffffff", [ # 31 colors
                    CBlock(["graph.node_data[node] = 1<<(__ffs(~AllForbid)-1)"]),
                ]),
                If("AllForbid == 0x7fffffff && VForbidden[node] == 0x7fffffff", [ 
                    CBlock([
                        "CS[node] = CS[node] + 1",
                        "VForbidden[node] = 0",
                        "TVForbidden[node] = 0"
                    ])
                ]),
            ]),
        ]),
    ]), #assigning new colors to all conflicting nodes

    Kernel("detectConflicts_wl", [G.param(), ("int *", "edge_src"), ("int *", "CS")], [
        ForAll("wledge", WL.items(), [
            CDecl([
                ("int", "edge", ""),
                ("bool", "pop", ""),
                ("int", "color", "=0")
            ]),
            WL.pop("pop", "wledge", "edge"),
            CDecl([
                ('int', 'u', '= edge_src[edge]'),
                ('int', 'v', '= graph.getAbsDestination(edge)')
            ]),
            If("CS[u] == CS[v] && graph.node_data[u] == graph.node_data[v] && u < v", [
                CBlock(["graph.node_data[v] = 0"]), # uncolor node v
            ]),
        ]),
    ]), #detecting conflicting nodes

    Kernel("createNewEdgeList_wl", [G.param(), ("int *", "edge_src"), ("int *", "CS"), ("int *", "VForbidden")], [
        ForAll("wledge", WL.items(), [
            CDecl([
                ("int", "edge", ""),
                ("bool", "pop", "")
            ]),
            WL.pop("pop", "wledge", "edge"),
            CDecl([
                ('int', 'u', '= edge_src[edge]'),
                ('int', 'v', '= graph.getAbsDestination(edge)')
            ]),
            #S: Point 2 in opt 3 doesn't make sense to me
            #R: makes sense, u is colored and v is not, meaning they were conflicting and v was uncolored and finalized the color of u. So the next time v is colored, VForbidden will prevent it from getting the same color as u.
            If("graph.node_data[u] == 0 || graph.node_data[v] == 0", [ # Case 1 edges don't enter
                If("graph.node_data[u] > 0", [
                    If("CS[u] > CS[v]", [ # Case 3 edges don't enter
                        WL.push("edge"),
                    ]), 
                    If("CS[u] == CS[v]", [
                        If("(VForbidden[v] & graph.node_data[u]) == 0", [ # Case 2 edges nodes don't enter
                            WL.push("edge"),   
                        ])   
                    ])
                ]), 
                If("graph.node_data[v] > 0", [
                    If("CS[v] > CS[u]", [
                        WL.push("edge"),
                    ]),
                    If("CS[u] == CS[v]", [
                        If("(VForbidden[u] & graph.node_data[v]) == 0", [
                            WL.push("edge"),
                        ])
                    ])

                ]),
                If("graph.node_data[u] == 0 && graph.node_data[v] == 0", [ # If both are uncolored, push!
                    WL.push("edge")   
                ])
            ]),
        ]) 
    ]), # Selectively remove unnecessary edges

    Kernel("forbidColors_wl", [G.param(), ("int *", "edge_src"), ("int *", "VForbidden"), ("int *", "CS")], [
        ForAll("wledge", WL.items(), [
            CDecl([
                ("int", "edge", ""),
                ("bool", "pop", "")
            ]),
            WL.pop("pop", "wledge", "edge"),
            CDecl([
                ('int', 'u', '= edge_src[edge]'),
                ('int', 'v', '= graph.getAbsDestination(edge)')
            ]),
            If("CS[u] == CS[v]", [
                If("graph.node_data[u] == 0 && graph.node_data[v] != 0", [
                    CBlock([("atomicOr(&VForbidden[u], graph.node_data[v])")]) 
                ]),
                If("graph.node_data[u] != 0 && graph.node_data[v] == 0", [
                        CBlock([("atomicOr(&VForbidden[v], graph.node_data[u])")])  
                ])
            ]),
        ])
    ]), # forbid colors for conflicting nodes

    Kernel("preproceesTentative_wl", [G.param(), ("int *", "TVForbidden")], [
        ForAll("node", G.nodes(), [
            CBlock(["TVForbidden[node] = 0"]),
        ])   
    ]),

    Kernel("tentativeColor_wl", [G.param(), ("int *", "edge_src"), ("int *", "VForbidden"), ("int *", "CS"), ("int *", "TVForbidden")], [
        ForAll("wledge", WL.items(), [
            CDecl([
                ("int", "edge", ""),
                ("bool", "pop", ""),
                ("int", "AllForbid", "")
            ]),
            WL.pop("pop", "wledge", "edge"),
            CDecl([
                ('int', 'u', '= edge_src[edge]'),
                ('int', 'v', '= graph.getAbsDestination(edge)')
            ]),
            If("CS[u] == CS[v]", [
                If("graph.node_data[u] == 0 && graph.node_data[v] == 0 && u < v", [
                    CBlock(["AllForbid = VForbidden[v] | TVForbidden[v]"]),
                    If("AllForbid != 0x7fffffff", [
                        CBlock([
                            "graph.node_data[v] = -(1<<(__ffs(~AllForbid)-1))",
                            "atomicOr(&TVForbidden[u], -graph.node_data[v])"
                        ])
                    ])
                ]),
                If("graph.node_data[u] < 0 && graph.node_data[v] == 0", [
                    CBlock(["atomicOr(&TVForbidden[v], -graph.node_data[u])"])
                ]),
                If("graph.node_data[u] == 0 && graph.node_data[v] < 0", [
                    CBlock(["atomicOr(&TVForbidden[u], -graph.node_data[v])"])
                ]),
                If("graph.node_data[u] < 0 && graph.node_data[v] < 0 && graph.node_data[u] == graph.node_data[v] && v < u", [
                    CBlock(["AllForbid = VForbidden[v] | TVForbidden[v]"]),
                    If("AllForbid != 0x7fffffff", [
                        CBlock([
                            "graph.node_data[v] = -(1<<(__ffs(~AllForbid)-1))",
                            "atomicOr(&TVForbidden[u], -graph.node_data[v])"
                        ])
                    ])
                ])
            ]),
        ]),
    ]), #tentatively color conflicting nodes (for less number of iterations)

    Kernel("convert_color", [G.param(), ("int *", "CS")], [
        ForAll("node", G.nodes(), [
            CBlock(["graph.node_data[node] = 31 * CS[node] + __ffs(graph.node_data[node]) - 1"])        
        ])      
    ]), # Convert bit representation of color to decimal

    Kernel("gg_main", [GraphParam('hg', True), GraphParam('gg', True)], [
        CDecl([
            ("Shared<int>", "edge_src", "(gg.nedges)"),
            ("Shared<int>", "VForbidden", "(gg.nnodes)"),
            ("Shared<int>", "CS", "(gg.nnodes)"),
            ("Shared<int>", "TVForbidden", "(gg.nnodes)"),
            ("int", "flag", "=true"),
        ]),
        Pipe([
            Invoke("ebgc_init", ["gg", "edge_src.gpu_wr_ptr()", "VForbidden.gpu_wr_ptr()", "CS.gpu_wr_ptr()", "TVForbidden.gpu_wr_ptr()"]),
            While("flag", [
                Invoke("assignColors", ["gg", "CS.gpu_wr_ptr()", "VForbidden.gpu_wr_ptr()", "TVForbidden.gpu_wr_ptr()"]),
                Invoke("detectConflicts", ["gg", "edge_src.gpu_rd_ptr()", "CS.gpu_rd_ptr()"]),
                Invoke("createNewEdgeList", ["gg", "edge_src.gpu_rd_ptr()", "CS.gpu_rd_ptr()", "VForbidden.gpu_rd_ptr()"]),
                Invoke("forbidColors", ["gg", "edge_src.gpu_rd_ptr()", "VForbidden.gpu_wr_ptr()", "CS.gpu_rd_ptr()"]),
                Invoke("preproceesTentative", ["gg", "TVForbidden.gpu_wr_ptr()"]),
                Invoke("tentativeColor", ["gg", "edge_src.gpu_rd_ptr()", "VForbidden.gpu_wr_ptr()", "CS.gpu_rd_ptr()", "TVForbidden.gpu_wr_ptr()"]),
                If("pipe.in_wl().nitems() <= 0.5 * gg.nedges", [
                    CBlock([
                        "flag = false",
                    ]),
                ]),
            ]),
            
            ClosureHint(Pipe([
                Invoke("assignColors_wl", ["gg", "CS.gpu_wr_ptr()", "VForbidden.gpu_wr_ptr()", "TVForbidden.gpu_wr_ptr()"]),
                Invoke("detectConflicts_wl", ["gg", "edge_src.gpu_rd_ptr()", "CS.gpu_rd_ptr()"]),
                Invoke("createNewEdgeList_wl", ["gg", "edge_src.gpu_rd_ptr()", "CS.gpu_rd_ptr()", "VForbidden.gpu_rd_ptr()"]),
                Invoke("forbidColors_wl", ["gg", "edge_src.gpu_rd_ptr()", "VForbidden.gpu_wr_ptr()", "CS.gpu_rd_ptr()"]),
                Invoke("preproceesTentative_wl", ["gg", "TVForbidden.gpu_wr_ptr()"]),
                Invoke("tentativeColor_wl", ["gg", "edge_src.gpu_rd_ptr()", "VForbidden.gpu_wr_ptr()", "CS.gpu_rd_ptr()", "TVForbidden.gpu_wr_ptr()"]),
            ]) ),
            Invoke("convert_color", ["gg", "CS.gpu_rd_ptr()"]) #S: Here or outside pipe?
        ], once=True, wlinit=WLInit("gg.nedges", []) ),
    ]),
])


