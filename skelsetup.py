#!/usr/bin/env python

from __future__ import print_function
import argparse
import os
import sys
import shutil

def create_bmk(template_root, app_id):
    bmk_path = os.path.join(template_root, "bmks", app_id)
    src_path = os.path.join(template_root, "bmks", 'template')

    assert src_path != bmk_path, 'ERROR: Do not support app_id `template`'

    try:
        os.mkdir(bmk_path)
    except:
        print('ERROR: Unable to create directory `%s`' % (bmk_path,), file=sys.stderr)
        sys.exit(1)
    
    files = ['app.mk', 'Makefile', 'template_support.cu']

    for f in files:
        print("Copying '%s' -> '%s'" % (os.path.join(src_path, f),
                                        os.path.join(bmk_path, f)),
                                        file=sys.stderr)

        shutil.copy(os.path.join(src_path, f),
                    os.path.join(bmk_path, f))


    os.rename(os.path.join(bmk_path, 'template_support.cu'),
              os.path.join(bmk_path, '{0}_support.cu'.format(app_id)))

    
    with open(os.path.join(bmk_path, 'app.mk'), "w") as f:
        f.write("""BMKNAME={appid}
SRCPY={appid}.py
SUPPORT={appid}_support.cu
""".format(appid = app_id))


def setup_okay(template_root):
    links = [os.path.join(template_root, "rt"),
             os.path.join(template_root, "skelapp")]

    for l in links:
        if not os.path.exists(l):            
            return False
    
    return True

def setup(ggc_root, template_root):
    links = [(os.path.join(template_root, "rt"),
              os.path.join(ggc_root, "rt")),
             (os.path.join(template_root, "skelapp"),
              os.path.join(ggc_root, "skelapp"))]

    for l, p in links:
        if not os.path.lexists(l):
            print("Creating '%s' -> '%s'" % (l, p), file=sys.stderr)
            os.symlink(p, l)
        else:
            # link exists
            pp = os.readlink(l)

            if pp != p:
                print("Removing '%s' -> '%s'" % (l, pp), file=sys.stderr)
                os.unlink(l)
                print("Creating '%s' -> '%s', originally pointing to '%s'" % (l, p, pp), file=sys.stderr)
                os.symlink(p, l)
            else:
                print("Link '%s' exists" % (l,), file=sys.stderr)

            if not os.path.exists(p):
                print("WARNING: Path '%s' does not exist!" % (p,))

    with open(os.path.join(template_root, "bmks", "local.mk"), "w") as f:
        f.write("# automatically created by skelsetup.py, do not change\n")
        f.write("GGCDIR={0}\n".format(ggc_root))
                
    return True

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Create and initialize a skelapp-based IrGL program")
    
    # subparsers
    sp = p.add_subparsers(dest="cmd")
    setup_cmd = sp.add_parser("setup", help="Setup template directory")
    setup_cmd.add_argument("ggc_root", help="Path to GGC root directory")

    # subparsers
    create_cmd = sp.add_parser("create", help="Create new application from template")
    create_cmd.add_argument("app_id", help="Application ID of new IrGL skelapp-based program (valid filename, no spaces)")

    args = p.parse_args()

    template_root = os.path.dirname(__file__)

    okay = setup_okay(template_root)

    if args.cmd == 'setup':
        if not os.path.exists(args.ggc_root):
            print('ERROR: `%s` does not exist' % (args.ggc_root,))
            sys.exit(1)

        setup(args.ggc_root, template_root)
        
    elif args.cmd == 'create':
        if not okay:
            print('ERROR: Template is not setup. Please run `%s setup /path/to/ggc` to setup template' % (sys.argv[0]))
            sys.exit(1)

        create_bmk(template_root, args.app_id)
