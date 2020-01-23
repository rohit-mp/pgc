from gg.ast import *
from gg.lib.graph import Graph
from gg.lib.wl import Worklist

G = Graph("graph")
WL = Worklist()

ast = Module([
        CDecl([("extern int", "N_NODES", ""),
               ("extern int*", "COLORS", ""),
               ("extern int", "CHROMATIC_NUMBER", "")]),
        CBlock([cgen.Define("NOT_VALID", "0"),
                cgen.Define("VALID", "1"),
                ]),
        Kernel("check_coloring", [G.param(), ("int *", "colors"), ("int *", "chromatic_number")], 
               [
                ForAll("node", G.nodes(), 
                       [
                           CBlock([("graph.node_data[node] = VALID")]),
                           ForAll("edge", G.edges("node"),
                               [
                                   CDecl([("int", "dst", "=graph.getAbsDestination(edge)")]),
                                    If("colors[node] == colors[dst]", 
                                        [
                                            CBlock([("graph.node_data[node] = NOT_VALID")]),    
                                        ]),
                               ]),
                           CBlock(["atomicMax(chromatic_number, colors[node])"]),
                        ]),
                ]
               ),
        Kernel("gg_main", [('CSRGraphTy&', 'hg'), ('CSRGraphTy&', 'gg')],
               [
                   CDecl([("Shared<int>", "colors", "(hg.nnodes)"),
                           ("Shared<int>", "chromatic_number", "(1)")]),
                   CFor(CDecl(("int", "i", "= 0")), "i < N_NODES", "i++", 
                       [CBlock([("colors.cpu_wr_ptr()[i] = COLORS[i]")])]),
                   Invoke("check_coloring", ["gg", "colors.gpu_rd_ptr()", "chromatic_number.zero_gpu()"]),
                   CBlock([("CHROMATIC_NUMBER = chromatic_number.cpu_rd_ptr()[0]")]),
        ])
])
