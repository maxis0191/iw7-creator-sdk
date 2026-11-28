"""A private gamelab folder for ONE WAY's plans: the server repository's plan compiler at origin/main plus this
weapon's script and test driver as libraries. Nothing in any checkout is touched.

    python -B make_gamelab.py --server <iw7-paris-server checkout> --out <new or existing folder>
    python -B C:\\forge\\forge.py run plans\\sz-oneway-core.json --gamelab <out>\\ops\\gamelab

Why not `forge run --library-dir`: on 28 Nov 2026 the machine cache (C:\\IW7-Cache\\tools) was gone, and a
`--library-dir` run looks for the pinned gsc-tool only in its overlay and in that cache (ledger:
forge-library-dir-gsc-tool). A `--gamelab` folder is read with the tools folder beside it, so the pinned compiler of
the server checkout is copied there.
"""
import argparse
import io
import os
import shutil
import subprocess
import sys
import tarfile

HERE = os.path.dirname(os.path.abspath(__file__))
LIBS = ["cp_sz_oneway.gsc", "szoneway_driver.gsc"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--server", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ref", default="origin/main")
    a = ap.parse_args()
    out = os.path.abspath(a.out)
    os.makedirs(out, exist_ok=True)
    data = subprocess.run(["git", "-C", a.server, "archive", a.ref, "ops/gamelab"], check=True,
                          stdout=subprocess.PIPE).stdout
    old = os.path.join(out, "ops", "gamelab")
    if os.path.isdir(old):
        shutil.rmtree(old)
    with tarfile.open(fileobj=io.BytesIO(data)) as t:
        t.extractall(out)
    lib = os.path.join(out, "ops", "gamelab", "lib")
    for name in LIBS:
        shutil.copyfile(os.path.join(HERE, name), os.path.join(lib, name))
    tool = os.path.join(a.server, "tools", "gsc-tool", "gsc-tool.exe")
    if not os.path.isfile(tool):
        sys.exit("no pinned gsc-tool in " + tool)
    os.makedirs(os.path.join(out, "tools", "gsc-tool"), exist_ok=True)
    shutil.copyfile(tool, os.path.join(out, "tools", "gsc-tool", "gsc-tool.exe"))
    head = subprocess.run(["git", "-C", a.server, "rev-parse", "--short", a.ref], check=True,
                          stdout=subprocess.PIPE, text=True).stdout.strip()
    print("gamelab of %s at %s with %s -> %s" % (a.ref, head, ", ".join(LIBS), os.path.join(out, "ops", "gamelab")))


if __name__ == "__main__":
    main()
