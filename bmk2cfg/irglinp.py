import os
import re

FT = {".gr": "bin/galois", ".dimacs" : "text/dimacs", ".mtx" : "text/mmarket",
      ".bin": "bin/custom", ".ele": "text/mesh", ".edges.txt": "text/edges",
      ".edges": "text/edges+mst",
      ".totem": "bin/totem"}


FMT_RE = re.compile("^(.*)(%s)$" % ("|".join(["(%s)" % (k.replace(".", r"\.")) for k in FT])))

def serialize_input(i):
    if 'flags' in i and isinstance(i['flags'], set):
        i['flags'] = ",".join(i['flags'])

def unserialize_input(i, basepath):
    x = i['flags'].strip()
    if len(x):
        i['flags'] = set(x.split(","))
    else:
        i['flags'] = set()

    # TODO?
    for x in ('bfs_output', 'sssp_output', 'pr_output'):
        if x in i:
            i[x] = os.path.join(basepath, i[x])

    return i

def describe_input(d, f, relpath):
    rdot = f.rfind(".")
    if rdot == -1: return None

    match = FMT_RE.match(f)
    if not match:
        return None

    name = match.group(1)
    fmt = match.group(2)

    out = {}
    out['format'] = FT[fmt]
    out["flags"] = set()
          
    ext = name.split(".")
    ext.reverse()

    ext_n = []
    for p in ext[:-1]:
        if p == "sym":
            out['flags'].add("symmetric")
        elif p == "tri":
            out["flags"].add("triangle")

        ext_n.append(p)
        
    ext_n.append(ext[-1])

    if 'format' == 'bin' and 'triangles' not in out['flags']:
        del out['format']

    if 'format' in out:
        out['flags'] = ",".join(out['flags'])
        out['name'] = ".".join(reversed(ext_n))
        return out
