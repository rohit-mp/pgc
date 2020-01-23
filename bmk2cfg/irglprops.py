import bmk2
import os

PERF_RE = "^Total time: (?P<time_ns>.*) ns$"
PERF_DISCOUNTED_RE = r"^Total time \(discounted\): (?P<time_ns>.*) ns$"

class irgl_bmk(bmk2.Binary):
    def __init__(self):
        self.props = irgl_bmk_props(self.bmk, self.variant)
        
    def get_id(self):
        return "%s/%s" % (self.bmk, self.variant)

    def apply_config(self, config):
        self.config = config

class irgl_bmk_props(bmk2.Properties):
    def __init__(self, bmk, variant):
        self.bmk = bmk
        self.variant = variant

class graph_coloring_bmk(irgl_bmk):
	bmk = 'graphcoloring'
	variant = None

	def filter_inputs(self, inputs):
	    return filter(lambda x: x.props.format == 'bin/galois' and 'symmetric' in x.props.flags, inputs)

	def get_run_spec(self, bmkinput):
	    x = bmk2.RunSpec(self, bmkinput)
	    x.set_binary(self.props._cwd, 'test_nontex')
	    x.set_arg(bmkinput.props.file, bmk2.AT_INPUT_FILE)
	    x.set_arg('-o')
	    x.set_arg('@output', bmk2.AT_TEMPORARY_OUTPUT)
            
	    x.set_checker(bmk2.ExternalChecker(get_gc_checker(bmkinput.props.file, path = self.props._cwd)))
	    x.set_perf(bmk2.PerfRE(PERF_RE))
	    return x

        
def get_gc_checker(inputfile, output='@output',
                   oflag = bmk2.AT_TEMPORARY_INPUT, path = None):
    ec = bmk2.BasicRunSpec()

    #TODO: fix the name of the binary to be non-generic
    binary = "test_nontex"

    if path is not None:
        for x in [os.path.join('..', 'color_checker')]:
            puc = os.path.join(path, x)
            if os.path.exists(os.path.join(puc, binary)):
                ec.set_binary(puc, binary, in_path = False)
                break
        else:
            # NOTE: different binary name!
            ec.set_binary("", "color_checker", in_path = True)
            
    ec.set_arg(inputfile, bmk2.AT_INPUT_FILE)
    ec.set_arg(output, oflag)

    return ec
