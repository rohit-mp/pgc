import bmk2
from irglprops import irgl_bmk, PERF_RE, get_gc_checker

class kokkos_graph_coloring_bmk(irgl_bmk):
	bmk = 'graphcoloring'
	variant = 'kokkos'
        alg = None
        
        def __init__(self, alg, *args, **kwargs):
            super(kokkos_graph_coloring_bmk, self).__init__(*args, **kwargs)
            self.alg = alg
            self.variant = self.variant + "+" + self.alg
        
	def filter_inputs(self, inputs):
	    return filter(lambda x: x.props.format == 'bin/custom'
                          #and 'symmetric' in x.props.flags
                          , inputs)

        def filter_inputs_for_checker(self, inputs):
            return filter(lambda x: x.props.format == 'bin/galois' and 'symmetric' in x.props.flags, inputs)

	def get_run_spec(self, bmkinput):
	    x = bmk2.RunSpec(self, bmkinput)
	    x.set_binary(self.props._cwd, 'KokkosGraph_color.exe')
            x.set_arg('--amtx')
	    x.set_arg(bmkinput.props.file, bmk2.AT_INPUT_FILE)

            x.set_arg('--algorithm')
	    x.set_arg(self.alg)

            x.set_arg('--cuda')

            x.set_arg('--repeat')
            x.set_arg('1')

	    x.set_arg('-o')
	    x.set_arg('@output', bmk2.AT_TEMPORARY_OUTPUT)

            chkinput = bmkinput.get_alt_format('bin/galois')
	    x.set_checker(bmk2.ExternalChecker(get_gc_checker(chkinput.props.file, path = self.props._cwd)))
            #x.set_checker(bmk2.PassChecker())
	    x.set_perf(bmk2.PerfRE(PERF_RE))
	    return x


# Maybe also check on CPU?
BINARIES = [kokkos_graph_coloring_bmk('COLORING_DEFAULT'), kokkos_graph_coloring_bmk('COLORING_VB'), kokkos_graph_coloring_bmk('COLORING_VBBIT'), 
            kokkos_graph_coloring_bmk('COLORING_EB'), kokkos_graph_coloring_bmk('COLORING_VBD'), kokkos_graph_coloring_bmk('COLORING_VBDBIT')]
