# Materialize a retained Model Lab v2 build

`Creator.ps1 -Action Materialize -Adapter ModelLabV2` joins an existing, restored
Model Lab v2 build to an explicitly supplied server script and community
manifest. It creates a local candidate with measured payloads and **incomplete
closure**. It does not build, stage stock, reserve resources, run a game, create
a ZIP or install anything. `Plan` and `Build` are not connected for this adapter.

This source implementation has been checked with small original synthetic
geometry and a text FF stand-in only. No real T7 export or opaque game/tool
artifact was used to validate it. Successful synthetic materialization is not
qualification of the future real export, rendered model or script.

## Existing route and explicit inputs

The upstream route remains [Model Lab resident preparation](../../ops/model-lab/RESIDENT-RIGID.md):
`prepare_ff.py --export-root ... --material-rebinds ...`, then the existing
`Build-ModelFF.ps1`. Creator consumes the retained results; it never calls either
operation. The [existing Model Lab scene](../../ops/model-lab/RESIDENT-RIGID.md#existing-ff-and-runtime-route)
can test the independently reviewed FF before an SDK archive exists.

The author `Project` must contain `manifest.json`, an existing `<namespace>.gsc`
and `composition.json`. Project, retained Model Lab source, BuildRoot and the
fresh FinalizeRoot must be separate nonnested roots. No author script is generated,
renamed, substituted from Beacon or declared reviewed by this adapter.

The command uses the existing parameters; all paths/pins below refer to a future
separately authorized materialization, not a new execution instruction:

```powershell
./sdk/modding/Creator.ps1 -Action Materialize -Adapter ModelLabV2 `
  -Project $authorProject -BuildRoot $restoredModelBuild `
  -FinalizeRoot $freshCandidate -ToolsRoot $reviewedToolsRoot `
  -ClientSource $clientRevision -ServerSource $serverRevision -Protocol 2 -Json
```

`ClientSource`/`ServerSource` are explicit compatibility assertions, not measured
installed binaries. This profile uses `Target stock`, protocol 2 and `cp_zmb`.
`BuildParameters`, `Output`, `GscAuditEvidence` and legacy `RecipientProof/Root`
are refused. Other active projects still go through Creator's ordinary collision
and compatibility checks before materialization.

`composition.json` has exactly `schema`, `assets` and `script`. Its schema is
`iw7.creator-model-composition/1`. Every field below is required; unknown fields
are refused and no descriptor field is an executable command.

| Object | Exact fields and binding |
| --- | --- |
| `assets` | `source_root` (absolute existing prepared Model Lab directory); `source_plan_sha256` for its `model-ff-plan.json`; `derived_receipt_sha256` for `derived-export.json`; `build_receipt_sha256` for BuildRoot's `state.local.json`; `roundtrip_sha256` for `geometry-roundtrip.json`; `ff_bytes` and `ff_sha256` for `mod.ff` |
| `script` | `path` (exactly `<namespace>.gsc`); measured `bytes`/`sha256`; nonempty `review_reference`; `closure_sha256` binding the author manifest's complete **declared graph**, including the script's dependencies |

For `script.closure_sha256`, hash UTF-8 bytes of
`json.dumps(manifest['package']['closure'], sort_keys=True, indent=2,
ensure_ascii=True, allow_nan=False) + '\n'`. Every other input hash binds the
exact saved file bytes. A graph change needs a new explicit source/closure review
declaration. These references are operator-supplied, hash-bound declarations;
Creator does not authenticate the reviewer or compile/audit the GSC's imports.
Missing source, review reference, closure binding or inconsistent pins is a refusal.

## Source, build and manifest checks

The source plan must be `iw7.model-ff-plan/2` with
`geometry_profile=t7-iw7-resident-static-v2`. Creator reuses
`rigid_export.py::verify_dump`, including `verify_stage`, to check the preserved
original export snapshots, declared material/LOD derivation, five source inputs
and all retained surface bytes. It does not implement a second geometry reader.
Original `model_name`, `mesh_name`, `surface_records`, ordered
`material_references` and the `256 + 384*N + 60*V + 12*T` work bound remain bound.

The state must be `iw7.model-ff-build/1`, `Status=BootstrapInventoryVerified`,
restored with stock preserved and no retained lease, failure or cleanup error.
Build/Offline/Dump/GeometryReader must report integer exit 0. Creator checks the
source-plan and derivation hashes, the FF tuple, retained reader stdout and
`iw7.model-rigid-roundtrip/2` against the recomputed report. Both `assets.csv`
and the retained loading callbacks must match the exact existing Model Lab
inventory. Stock, tool and EXE paths in a historical state are never followed.
These checks bind retained statements and bytes; they do not authenticate native
execution history or establish correspondence to unobserved T7 donor buffers.

The author manifest remains the existing `iw7.community-mod/1` contract:

- `package.delivery=mod`, `maps=[cp_zmb]`, protocol 2 and
  `coexistence=exclusive-fs-game`.
- Exactly one client file destined for `mods/<id>/mod.ff` and one server file
  destined for `iw7-mod/custom_scripts/cp/<id>.gsc`, each bound to its own root.
- The server lifecycle is the reviewed `custom_scripts/cp/<id>.gsc::init`.
  Its graph depends on the actual model and includes any reviewed script imports.
  The laboratory's protection/utility-dependent fixture is not automatically a
  standalone distribution script.
- Four client nodes: actual XModel, actual XSurface, the existing
  `netconststrings:ncs_mdl_paris_model_probe`, and `rawfile:paris_model_probe`.
  The model references these plus the recipient placeholder material. The real
  model name is retained in the verified NCS source; no Beacon renaming occurs.
- `closure.status=incomplete`; all five source-check/offline-load/runtime-link/
  render/gameplay records remain pending with null references and empty map lists.

The materializer fills payload sizes/hashes and measured node representations,
refusing conflicting supplied hashes. The model/surface representations are
retained FF dumps; NCS evidence is explicitly a **source input**, not a dumped
asset. The generated zone rawfile has inventory evidence only. Recipient nodes
and the rawfile do not acquire invented representation hashes or qualification.

## Slots, materials and qualification

Five slots need five explicit ordered `--material-rebinds` entries upstream;
this is separate from the five Model Lab source files. Repeated material and
geometry aliases do not collapse logical slots. Shared defining material strings
are patched once; the XSB and the undeclared XMB bytes stay unchanged.

The current Model Lab policy binds every slot to
`mopw/character_park_clown_zombie_shoes`. This is the same IW7 recipient
**placeholder** across all surfaces, not preservation or conversion of the T7
material appearance. No T7 texture, material payload, technique or shader is
ported by this adapter. Recipient material/technique/image closure, compiled GSC
imports, native provenance, runtime linking, rendering and owner gameplay remain
unverified and appear explicitly in `finalization.json` and Creator's blockers.

## Candidate and bounds

Success creates six files: `mod.ff`, the supplied GSC, `manifest.json`,
`finalization.json`, `validation-plan.json` and `validation-package.json`.
Source/build files are rechecked before and after writing; each candidate file
is reread and compared byte for byte before success. A failed or interrupted
write retains the partial candidate for diagnosis; existing paths are never
overwritten or recursively deleted.

This adapter retains the existing 32 MiB FF, 1 MiB XMB and 16 MiB XSB limits,
with 1 MiB metadata documents, 64 KiB script/descriptor/inventory and a 96 MiB
aggregate unique-label input allowance. The output allowance is 36 MiB including
metadata. These are bounded read/write checks, not an OS quota or permission
for a native operation. Beacon's separate 2 MiB candidate budget is unchanged.

Creator returns `materialized=true`, `build_verified=true` for the retained
evidence and `creator_output_verified=true`. `build_executed`, `packaged`,
`closure_complete`, `package_ready`, `runtime_ready` and `owner_accepted` remain
false. The stored package validation intentionally reports incomplete closure.
No later gate is bypassed: the unchanged `Package -Adapter None` remains the ZIP
route once the project is independently qualified. Delivery additionally needs
passed source-check/offline-load/runtime-link evidence for the declared map.

Source tests: `python -B sdk/modding/tests/test_creator_model_materialize.py -v`.
Fixtures are bounded below 8 MiB and never passed to an engine. The first test
pass exposed a prefixed SDK error (`package: Dependency closure incomplete`);
the adapter now checks the exact existing result rather than inventing another
validator convention. No real export was used to correct or validate this case.

Source checkpoint, 2026-10-13: all 19 new tests passed, together with eight
distinct targeted existing Creator/Beacon composition regressions. Python and
PowerShell syntax, relative documentation links and `git diff --check` passed.
The largest observed new-test preparation tree was 57,031 bytes against the
8 MiB preparation limit. This was source/fixture validation only; the complete
SDK suite and real-export materialization were not run for this checkpoint.
