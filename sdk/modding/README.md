# IW7 community SDK v1

Start with [platform contract and beacon walkthrough](../../docs/MODDING-PLATFORM.md)
and [capability evidence / importer milestones](../../docs/MODDING-CAPABILITIES.md).
The [BO3/T7 import profiles](BO3-IMPORT-PROFILES.md) distinguish the first static
pilot from the SDK's broader, versioned import and content-extension objective.

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

Use [Creator](CREATOR.md) to plan a project or package an existing statically
ready project with `-Action Package -Output <fresh-zip>`. Packaging reuses the
existing distribution gates and ZIP writer, requires explicit source/protocol
assertions, and does not build a fastfile or qualify runtime acceptance.

The [original author inputs](ORIGINAL-AUTHORING.md) add three independently editable
geometry/texture/behavior source projects through ModelLabV2 Plan and the existing
Bind/Materialize entrypoints for retained authored plan/3 receipts. This route
retains an explicitly blocked capability until new build/readback and an
unchanged-runtime independent creator trial are qualified. It does
not reinterpret the retained Beacon, BO3 prop or cube proof as a new asset proof.

The [editable server-only spawn-tip example](examples/server-spawn-tip/sdk_spawn_tip.gsc)
has a valid planning [manifest](examples/server-spawn-tip/manifest.json), with
payload/closure qualifications and runtime evidence still pending. Package
therefore refuses the example as shipped; it is a source starting point.
