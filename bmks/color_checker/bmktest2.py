import bmk2
from irglprops import irgl_bmk, PERF_RE

class color_checker(irgl_bmk):
	bmk = 'graphcoloring'
	variant = 'color-checker'

	def filter_inputs(self, inputs):
                #TODO: add symmetric
                return filter(lambda x: x.props.format == 'bin/galois', inputs)
		#return filter(lambda x: x.props.format == 'bin/galois' and 'symmetric' in x.props.flags, inputs)

	def get_run_spec(self, bmkinput):
		x = bmk2.RunSpec(self, bmkinput)
		x.set_binary(self.props._cwd, 'test')
		x.set_arg(bmkinput.props.file, bmk2.AT_INPUT_FILE)
		x.set_checker(bmk2.REChecker('^valid_coloring: yes$'))
		x.set_perf(bmk2.PerfRE(PERF_RE))
		return x

#mis-checker sample.sym,sample.sym,sample.sym
BINARIES = [color_checker()]
