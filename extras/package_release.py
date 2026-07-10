#!/usr/bin/env python3

# This script is for building releases for MVP (MVS/CE Package manager)
# It works by creating an XMI file which contains:
# - Task file(s), JCL/REXX files that will be submitted or executed in
#   numbered order and follow a specific naming convention (#nnnJCL or
#   #nnnREX where nnn is 001 through 999). Note: the jobname MUST match
#   the filename.
# - XMI file(s) that make up the release
#
# The package XMI is built entirely in Python using the `xmi` library
# (pip package `xmi-reader`, imported as `import xmi`,
# https://github.com/mainframed/xmi). No live Hercules/MVS-CE instance is
# required to run this script -- it works standalone on plain Linux.
#
# Author: Soldier of FORTRAN
# License: GPLv3

import os
import sys
import shutil
import tempfile
import argparse
from datetime import datetime

import xmi  # pip install xmi-reader

with open("build.log", 'w') as log:
    now = datetime.now()
    current_time = now.strftime("%x %X")
    log.write("This package was generated with package_release.py\n")
    log.write("Package generated on: {}\n".format(current_time))
    log.write("Command arguments: ")
    log.write(str(sys.argv))

my_parser = argparse.ArgumentParser()
my_parser.add_argument('--xmi-files', '-x', required=True, help="xmi file(s) to be included", nargs="+")
my_parser.add_argument('--task-files', '-t', required=True, help="JCL/REXX file(s) to be included", nargs="+")
my_parser.add_argument('--name', '-a', default="RELEASE.xmit", help="Release XMI file output path/name")
my_parser.add_argument('--dsn', default=None, help="Dataset name to embed in the XMI metadata (defaults to the uppercased output file name)")
my_parser.add_argument('--from-user', default="MVP", help="NETDATA origin userid embedded in the XMI (max 8 chars)")
my_parser.add_argument('--from-node', default="MVP", help="NETDATA origin node name embedded in the XMI (max 8 chars)")
args = my_parser.parse_args()


def is_task_file(path):
    '''Validate that a task file follows the #nnnJCL/#nnnREX naming convention'''
    name = os.path.basename(path)
    return (
        len(name) >= 5 and
        name[0] == "#" and
        name[2:4].isnumeric() and
        name[4:].split('.')[0] in ("JCL", "REX")
    )


staged_files = []
for i in args.task_files:
    print("Reading {}".format(i))
    if is_task_file(i):
        staged_files.append(i)
    else:
        print("File {} does not match #nnnJCL/#nnnREX naming convention, skipping".format(i))

for i in args.xmi_files:
    print("Reading {}".format(i))
    staged_files.append(i)

dsn = args.dsn or os.path.splitext(os.path.basename(args.name))[0].upper()

with tempfile.TemporaryDirectory() as staging_dir:
    for f in staged_files:
        shutil.copy(f, os.path.join(staging_dir, os.path.basename(f)))

    xmi.create_xmi(
        staging_dir,
        output_file=args.name,
        dsn=dsn,
        from_user=args.from_user,
        from_node=args.from_node,
        to_user=args.from_user,
        to_node=args.from_node,
    )

print("Wrote package {}".format(args.name))
