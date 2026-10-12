# Creator command: real plan, explicit build boundary

`Creator.ps1` accepts a local project directory containing the existing SDK
`manifest.json`; payload paths remain relative to that project. It runs the real
SDK and Distribution compatibility functions, not a second manifest validator.

```powershell
./sdk/modding/Creator.ps1 -Project ./sdk/modding/examples/beacon -Adapter BeaconV1 `
  -ClientSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -ServerSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 -Protocol 2
```

Default `-Action Plan` writes no files, starts no native adapter and acquires no
lease. It shows project contract, active dependencies/target, adapter identity,
adapter plan, missing payload/closure evidence, build and package as distinct
steps. The example passes its contract while clearly retaining unbuilt payload
and incomplete closure as pending. `-Json` returns the same report for automation.
Exit 0 means a valid plan, never a build, archive or runtime acceptance. Omitted
source/protocol arguments leave compatibility blocked; no installed binary is
inferred from this source baseline.

Use `-ActiveProject` for every other intended active project directory. Exact
dependency versions, namespace/destination/asset collisions, explicit conflicts,
one fs_game, capabilities and source/protocol assertions are checked by the
existing Distribution checker. Planning does not certify active payload bytes.

`-Adapter None` supports generic contract planning. `BeaconV1` is deliberately
limited to `sdk_beacon` on `cp_zmb` and the exact reviewed original-template GSC.
It does not accept an arbitrary edited game project as a working compiler input.
`AnimationProbe` and `MaterialV2` are named extension points with explicit blocked
status until their actual adapters and evidence paths are connected.

For an already prepared original-beacon project, optional `-BuildParameters`
accepts the existing local `Build-BeaconFF.ps1` argument object. Creator rejects
unknown fields (including `Run`), binds `SourceRoot` to the project and `OpsRoot`
to the reviewed tools tree, and calls the actual adapter in read-only plan mode.
Stock absence or stale receipts therefore fails the real adapter's checks.
`-ToolsRoot` is an explicit operator override for a complete reviewed checkout
during isolated integration; it is never read from project content.

## Build integration in progress

`-Action Build` currently refuses **before mutation**, even after a valid plan.
The stock binding and finalization API must be integrated and reviewed first.
There is no dummy build, fabricated receipt, native invocation or ZIP on this
path. The intended complete command adds `-BuildParameters`, `-FinalizeRoot`
(fresh candidate directory) and `-Output` (fresh ZIP), retaining the same target
and active-project arguments.

The coordinated finalizer is owned by Distribution:

```text
python -B sdk/modding/Finalize-BeaconProject.py --project PROJECT --build-root RUNROOT --output-root FRESH
  --client-source PIN --server-source PIN [--recipient-proof JSON --recipient-root ROOT]
```

It consumes fixed `state.local.json`, `mod.ff`, `assets.csv` and
`work/dump/sdk_beacon` paths, validates real source/build/restoration identity and
materializes a measured manifest. Its `beacon-finalize/1` result distinguishes
successful materialization from `closure_complete` and static `package_ready`.
Missing recipient evidence must remain a final package blocker. Creator will
invoke `Package-CommunityMod.py` only after those checks; that existing tool
remains the sole ZIP writer and repeats its payload/compatibility checks.

This tranche does not change public schemas, common helpers, native tools,
recipient proof semantics or existing completed runs. CLI tests invoke the real
pure validators and verify no filesystem mutation for Plan/refused Build.
