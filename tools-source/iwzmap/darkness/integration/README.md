# darkness/integration: a patch for a script that is not in this repository

A record of the darkness work of 2026-11-10, kept unchanged. `apply_darkness_to_build_g.py` writes a patched copy of
a level build script, `level\tools\build-g.ps1`, adding the `-Darkness` options described in its header. That build
script lives in a runtime work folder of one machine and is in no repository, so nothing here can be run as it
stands. `build-g.darkness.diff` is the resulting difference; the four `*.ps1.txt` files are the snippets the patch
inserts (they contain the machine paths of the original runs).

The maintained route to a dark build is `darkness/build-g-dark.ps1` and `build-sz2.ps1 -Darkness`; see
`darkness/README.md`.
