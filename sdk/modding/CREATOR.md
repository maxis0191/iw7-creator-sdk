# Creator command: plan, build, finalize and package gates

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
Python validates and hashes one bounded byte snapshot of BuildParameters.
PowerShell independently reads one bounded snapshot, requires the same hash and
parses those exact bytes; it never reopens the path between hashing and parsing.
A separate explicit allowlist is checked immediately before both builder splats,
so the builder's own support for `Run` cannot authorize that key from JSON. Build
also obtains and verifies a fresh snapshot after adapter planning.
`-ToolsRoot` is an explicit operator override for a complete reviewed checkout
during isolated integration; it is never read from project content.

## Explicit Build orchestration

`-Action Build` runs the real BeaconV1 chain after its complete plan passes.
It requires `-BuildParameters`, `-FinalizeRoot` (fresh candidate directory) and
`-Output` (fresh ZIP), retaining the target and active-project arguments. RunRoot,
FinalizeRoot and Output must have existing parents, be fresh, separate and
non-nested, and be outside input projects. Existing outputs are preserved.

BuildParameters must explicitly include the final candidate and job-source
hashes, plus `StockBindingReceipt`, `StockBindingReceiptSHA256`,
`ReviewedStockManifest` and `ReviewedStockManifestSHA256`. These bind the relocated
stock through the common reviewed helper. A checkout whose builder lacks those
parameters is refused before execution. SourceRoot and OpsRoot must still match
the explicit project and reviewed ToolsRoot; no command comes from the manifest.

Creator calls the real `Build-BeaconFF.ps1 -Run`. The builder owns resource
admission, the native process tree, deadlines, byte limits and restoration;
Creator does not acquire an additional reservation. `build_executed` means the
builder was invoked, including a failed attempt. `build_verified` becomes true
only after the finalizer verifies the persisted source/build/restoration evidence.
Failed builds retain their diagnostics; Creator does not delete their output.

The coordinated finalizer is owned by Distribution:

```text
python -B sdk/modding/Finalize-BeaconProject.py --project PROJECT --build-root RUNROOT --output-root FRESH
  --client-source PIN --server-source PIN [--recipient-proof JSON --recipient-root ROOT]
```

It consumes fixed `state.local.json`, `mod.ff`, `assets.csv` and
`work/dump/sdk_beacon` paths, validates real source/build/restoration identity and
materializes a measured manifest. Its `beacon-finalize/1` result distinguishes
successful materialization from `closure_complete` and static `package_ready`.
Missing recipient evidence remains a final package blocker. Creator invokes
`Package-CommunityMod.py` only after those checks; that existing tool
remains the sole ZIP writer and repeats its payload/compatibility checks.

Exit 0 for Build requires a ZIP whose path, size and hash match the package
receipt. Materialization with incomplete closure exits 1, reports the retained
candidate and blockers, and never calls the ZIP writer. Neither a successful
build nor archive changes `runtime_ready=false` or `owner_accepted=false`.

The current beacon finalizer intentionally keeps recipient material/transitive
dependencies and compiled utility/import evidence blocked. The historical first
build also lacks Plan.SourceReceiptSHA256; new builds preserve that measured
binding. No old receipt is edited, and this orchestration does not close these
evidence gaps itself. The authorized execution below verifies the native chain
through materialization; source tests and the read-only stock plan remain
separate evidence.

This tranche does not change public schemas, common helpers, native tools,
recipient proof semantics or existing completed runs. CLI tests invoke the real
pure validators and verify no filesystem mutation for Plan/refused Build. Flow
tests use explicitly synthetic builder/finalizer doubles and text payloads with
the real compatibility validators and ZIP writer: they verify orchestration,
failure retention and the package gate, not FF compilation or finalizer evidence.
Two additional integration cases use the real finalizer and its asset-free
synthetic receipt fixtures. Consistent source-bound receipts must materialize but
keep the two recipient blockers and no ZIP; an altered FF must leave both candidate
and archive absent. Only the native builder is replaced in these cases. Run these
tests with a ToolsRoot containing the integrated Finalize-BeaconProject commit;
they fail if that dependency is missing rather than silently skipping it.

Regression tests rewrite the parameter file at each old read/hash boundary and
after adapter planning. Both old read/hash races reproduced an unintended Run
in the synthetic builder under Action Plan; the corrected snapshot logic permits
no such transition. These tests use small fixture files and a synthetic builder,
not native execution or stock.

## Actual Creator execution, 2026-10-12

One coordinator-authorized `Creator -Action Build -Adapter BeaconV1` execution
completed the real build, verify, dump and independent reader phases, each with
exit 0 and zero job members at closure. The real finalizer then materialized a
23,036-byte candidate and verified `Plan.SourceReceiptSHA256` against the project
receipt. `build_verified`, `materialized` and `source_receipt_bound` are true.
The [sanitized validation record](creator-validation-2026-10-12.json) binds the
measured artifacts and source hashes without local paths or reservation tokens.

The new `mod.ff` is 1,048 bytes, SHA256
`3fa49bcdfd08857bb37c198af7a49af78675b940b022e160343552d3f8b71da8`.
It is a distinct artifact from the first native beacon build, whose same-size FF
hash is `76ed0701dc1480c501604db04999f300394c65877aa24a70dfe7afc2cd662d4a`.
The historical artifact/receipt were preserved. No byte-determinism claim or
explanation for the hash difference is established by this run.

Creator returned **exit 1 only at the package gate**. Two blockers remained:
recipient material resolution with transitive image/technique dependencies, and
the current compiled `scripts/engine/utility` plus its imports. No recipient proof
was fabricated; the ZIP writer was not called and no ZIP was created. The target
client/server pins `77e6d4d24e918ee363b3feee3735c3b889dff7d7` were contract
assertions, not measurements of installed binary provenance. `closure_complete`,
`package_ready`, `runtime_ready` and `owner_accepted` remain false.

Effective admission was 8 GiB physical/11 GiB commit, confirmed from the retained
registry predecessor. All 78 staged inputs were removed, restoration and source
preservation were confirmed, no owned process remained and the reservation was
released. At the final observation the registry was empty and Main's process
identity and UDP 27016 owner were unchanged. Maximum observed build output was
1,220,100 bytes, below the unchanged 64 MiB threshold; every stderr was empty.
The nine reviewed source files retained their before/after hashes. No client or
test dedicated was launched, no Main deployment occurred, and there was no retry.
