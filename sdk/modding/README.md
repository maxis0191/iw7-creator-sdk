# IW7 community SDK v1

Start with [platform contract and beacon walkthrough](../../docs/MODDING-PLATFORM.md)
and [capability evidence / importer milestones](../../docs/MODDING-CAPABILITIES.md).

```powershell
python -B sdk/modding/manifest.py sdk/modding/examples/beacon/manifest.json
python -B -m unittest discover -s sdk/modding/tests -v
```

Requires existing Python3.10+ and this repository's transport validator; no extra
dependency installation. `valid:true` for the example means a valid plan only.
Its fastfile and runtime evidence are intentionally unmeasured.

The GSC, zone recipe and preparation adapter are candidate sources. Nothing here
automatically installs, starts a game, resolves dependencies or changes Main.
Integration, builds and protected multiplayer tests are coordinated by the parent.
