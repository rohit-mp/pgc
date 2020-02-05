import time
import struct
import sys
import array
from collections import namedtuple

CHATTY = True
USE_ARRAY = True   # only on little-endian machines!

GRHeader = namedtuple('GRHeader', ['version', 'sizeEdgeTy', 'numNodes', 'numEdges', 'edgeDataOffset'])

class GRGraphReader(object):
    def _read_array_from_file_2(self, ty, n, f):
        """Read N items of type ty (struct.Struct) into a array"""

        # could've used array except it doesn't support 64-bit types until 3.3
        st = time.clock()
        sz = ty.size
        out = []
        for i in range(n):
            d = f.read(sz)
            out.append(ty.unpack(d)[0])

        end = time.clock()
        print("total", end - st)

        return out

    # only handles very simple types
    def _primitive_type(self, pt):
        bsa = ''
        repeat = 1
        ty = pt[-1]
        
        if len(pt) >= 3:
            bsa = pt[0]
            repeat = int(pt[1:-1])
        elif len(pt) == 2:
            bsa = pt[0]
            if bsa not in ('@', '=', '<', '>', '!'):
                repeat = int(bsa)
            else:
                repeat = 1

        return (bsa, repeat, ty)

    def _read_array_from_file(self, ty, n, f):
        """Read N items of type ty (struct.Struct) into a array"""
        per_round = 128

        oldty = self._primitive_type(ty.format)
        nty = struct.Struct("%s%d%s" % (oldty[0], oldty[1] * per_round, oldty[2]))

        #st = time.clock()
        sz = ty.size * per_round

        assert nty.size == sz

        out = []
        for i in range(n/per_round):
            d = f.read(sz)
            out += list(nty.unpack(d))

        for i in range(n % per_round):
            d = f.read(ty.size)
            out += list(ty.unpack(d))

        #end = time.clock()
        #print "total", end - st

        return out

    def _write_array_to_file(self, ty, array, f):
        """Write N items of type ty (struct.Struct) into a array"""
        per_round = 128

        oldty = self._primitive_type(ty.format)
        nty = struct.Struct("%s%d%s" % (oldty[0], oldty[1] * per_round, oldty[2]))

        #st = time.clock()
        sz = ty.size * per_round

        assert nty.size == sz
        
        # module array doesn't support quads...
        n = len(array)
        out = []
        for i in range(n/per_round):
            s = nty.pack(*array[i*per_round:(i+1)*per_round])
            f.write(s)
            
        off = (n/per_round) * per_round
        for i in range(n % per_round):
            s = ty.pack(array[off+i])
            f.write(s)

    def from_csr(self, cg):
        self.num_nodes = cg.num_nodes
        self.num_edges = cg.num_edges
        self.offsets = cg.offsets
        self.edges = cg.dst
        self.edge_data = cg.wt

    def from_arrays(self, offsets, dst, edgewts = None, move = False):
        self.num_nodes = len(offsets) - 1
        self.num_edges = len(dst)

        if move:
            assert isinstance(offsets, array.array) and offsets.typecode == 'I'
            assert isinstance(dst, array.array) and offsets.typecode == 'I'
            
            self.offsets = offsets
            self.edges = dst
            
        else:
            self.offsets = array.array('I', offsets)
            self.edges = array.array('I', dst)

        if edgewts:            
            if move:
                assert isinstance(edgewts, array.array) and edgewts.typecode == 'I'
                self.edge_data = edgewts
            else:
                self.edge_data = array.array('I', edgewts)

    def to_coo(self):
        for n in range(self.num_nodes):
            for e in range(self.offsets[n], self.offsets[n+1]):
                yield (n, self.edges[e], self.edge_data[e])

    def _read_hdr(self, g):
        fmt = '<4Q'
        sz = struct.calcsize(fmt)
        header = g.read(sz)
        version, sizeEdgeTy, numNodes, numEdges = struct.unpack(fmt, header)

        edgeDataOffset = sz + numNodes * 8 + numEdges * 4 + (numEdges % 2) * 4

        return GRHeader(version, sizeEdgeTy, numNodes, numEdges, edgeDataOffset)

    def read_hdr(self, f):
        g = open(f, "r")
        hdr = self._read_hdr(g)
        g.close()
        return hdr

    def read(self, f):
        g = open(f, "r")
        t_st = time.clock()
 	# uint64_t* fptr = (uint64_t*)m;
  	# __attribute__((unused)) uint64_t version = le64toh(*fptr++);
  	# assert(version == 1);
  	# uint64_t sizeEdgeTy = le64toh(*fptr++);
  	# uint64_t numNodes = le64toh(*fptr++);
  	# uint64_t numEdges = le64toh(*fptr++);
        self.hdr = self._read_hdr(g)
        version, sizeEdgeTy, numNodes, numEdges, _ = self.hdr
        assert(version == 1)
  
        if CHATTY: print >>sys.stderr, "reading %s: %d nodes, %d edges" % (f, numNodes, numEdges)

        self.num_nodes = numNodes
        self.num_edges = numEdges

        self.offsets = array.array('L', [0])
        if USE_ARRAY and self.offsets.itemsize == 8:
            self.offsets.fromfile(g, numNodes)
        else:
            self.offsets = self._read_array_from_file(struct.Struct('<Q'), numNodes, g)
            self.offsets.insert(0, 0)

  	# uint64_t *outIdx = fptr;
  	# fptr += numNodes;

        if USE_ARRAY:
            self.edges = array.array('I')
            if self.edges.itemsize != 4:
                self.edges = array.array('L')

            assert self.edges.itemsize == 4
            self.edges.fromfile(g, numEdges)            
        else:
            self.edges = self._read_array_from_file(struct.Struct('<L'), numEdges, g)

        # if (numEdges % 2) fptr32 += 1;
        if numEdges % 2:
            g.read(struct.Struct('<L').size)

        assert sizeEdgeTy == 4 or sizeEdgeTy == 0, "Edge size of %d not supported" % (sizeEdgeTy,)

        if sizeEdgeTy == 4:
            assert self.hdr.edgeDataOffset == g.tell()
            if USE_ARRAY:
                self.edge_data = array.array('I')
                if self.edge_data.itemsize != 4:
                    self.edge_data = array.array('L')
                    
                assert self.edge_data.itemsize == 4
                self.edge_data.fromfile(g, numEdges)
            else:
                self.edge_data = self._read_array_from_file(struct.Struct('I'), numEdges, g)            
        
        g.close()
        t_end = time.clock()

        if CHATTY: print >>sys.stderr, "reading done.", t_end - t_st

    def write_hdr(self, f, hdr):
        f.seek(0)
        fmt = '<4Q'
        s = struct.pack(fmt, hdr.version, hdr.sizeEdgeTy, hdr.numNodes, hdr.numEdges)
        f.write(s)
        
    def write(self, f):
        g = open(f, "w")

        if hasattr(self, 'edge_data'):
            edsize = 4
        else:
            edsize = 0

        self.write_hdr(g, GRHeader(version=1, sizeEdgeTy=edsize, numNodes = self.num_nodes, numEdges = self.num_edges,
                                   edgeDataOffset=0))
    
        self._write_array_to_file(struct.Struct('<Q'), self.offsets[1:], g)

        if USE_ARRAY:
            self.edges.tofile(g)
        else:
            self._write_array_to_file(struct.Struct('<L'), self.edges, g)

        if self.num_edges % 2:
            g.seek(struct.Struct('<L').size, 1)

        if USE_ARRAY:
            if hasattr(self, 'edge_data'):
                self.edge_data.tofile(g)
        else:
            self._write_array_to_file(struct.Struct('I'), self.edge_data, g)

        g.close()
        

GRGraph = GRGraphReader

if __name__ == "__main__":
    import sys

    inp = sys.argv[1]
    if len(sys.argv) == 3:
        out = sys.argv[2]
    else:
        out = None

    g = GRGraphReader()
    g.read(inp)

    if g.num_edges < 10:
        for e in g.to_coo():
            print e
    
    if out:
        g.write(out)

