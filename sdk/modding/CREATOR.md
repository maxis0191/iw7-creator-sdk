# Creator command: plan, materialize, build and package gates

`Creator.ps1` accepts a local project directory containing the existing SDK
`manifest.json`; payload paths remain relative to that project. The explicitly
selected `BeaconSelfContainedV1` source-only plan can instead use the existing
variant folder without a manifest, as described below. Creator runs the real SDK
and Distribution compatibility functions, not a second manifest validator.

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

## Explicit self-contained source selection

The original Beacon remains blocked for concrete, separate reasons:

1. Its exact source contains two calls to `scripts/engine/utility`, and its
   compiled negative control emitted two `OP_ScriptFarFunctionCall` instructions.
   The current finalizer conservatively adds the utility dependency and requires
   the current compiled recipient script plus its imports.
2. `BeaconV1`, its preparation receipt, zone/rawfile names, native builder and
   finalizer all target the original `sdk_beacon` identity and exact GSC template.
   Replacing its GSC or changing a metadata summary cannot reuse that evidence.
3. The separate variant's historical disassembly reports zero observed external
   calls, but that run did not attest complete consumption of both bytecode and
   stack. Even a future full-consumption receipt needs a complete semantic import
   audit bound to the same source/compiler/container and opcode tables before
   dependency absence can be accepted. Structure alone does not prove absence.

The existing variant can be selected explicitly for a source-only **Plan**.
Its separate local composition route is documented below under Materialize:

```powershell
./sdk/modding/Creator.ps1 -Project ./sdk/modding/examples/beacon-self-contained `
  -Adapter BeaconSelfContainedV1 -Action Plan `
  -ClientSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -ServerSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 -Protocol 2 -Json
```

The source/protocol arguments are operator compatibility assertions, as in the
original example; this command does not inspect an installed client or server.
A separate folder containing the exact same `sdk_beacon_self_contained.gsc` is
also accepted. `creator_self_contained.py` requires the 5,535-byte source hash
`9de9b76dc25293146999c71653bd407d8cb639e107293f6de87084fed90eee1c` in both the selected
project and reviewed ToolsRoot. Sources are read as bounded stable snapshots;
redirects and a changed source are refused. The original example stays intact.

The selector loads the pinned
[Creator planning contract](creator_beacon_self_contained.manifest.json) into
memory and sends it through the same SDK/Distribution plan validators. It writes
no manifest, prepared project, source receipt, compiled input or output directory.
If the project already contains `manifest.json`, its parsed content must equal
that exact contract; a different manifest is refused rather than ignored. Both
the source and contract template are pinned in code, so editing both project and
ToolsRoot copies does not silently change the selected input.

The proposed identity is `sdk_beacon_self_contained`, with its own entrypoint,
enable dvar, `mods/sdk_beacon_self_contained` destination and proposed rawfile.
The model `paris_model_probe`, its surfaces and NCS names still collide with the
original Beacon/model probe. Explicit conflicts and the real delivered-asset
collision checker remain active. This source plan is not a coexistence claim.

The graph stays incomplete. Utility is an **unresolved qualification question**,
reported in `source_selection.unresolved_qualifications` with status
`unresolvedQualification`; the variant graph does not assert a utility dependency
edge. Qualifying its absence, and that of other external/dynamic targets, still
needs a complete source-bound compiled import audit. Material, technique-set,
image and further transitive recipient closure
remain separate requirements; four non-default presence rows cannot satisfy them.
All content hashes and offline/runtime evidence entries in the proposed package
contract remain pending.

The JSON `source_selection` records the measured source path/hash/length, planning
contract hash and proposed contract. Only `source_bytes_verified` becomes true.
Compiled input binding, complete bytecode/stack consumption, external-GSC absence,
recipient closure, build qualification, package/runtime readiness and owner
acceptance remain false. Local `validation.local.json` files and zero-Far summaries
are not accepted as evidence by this selector. The optional explicit
`GscAuditEvidence` consumer below reports compiled evidence separately, without
changing the proposed package contract or these source-only selection flags.
Existing native audit and recipient binders remain unchanged.

`Build` is explicitly refused before any builder or finalizer call. This adapter
also refuses `BuildParameters`, `RecipientProof`, `RecipientRoot`, `FinalizeRoot`
and `Output` in Plan, so it cannot accidentally route through `BeaconV1` or treat
historical proof as variant qualification. A valid Plan exits zero with pending
steps; it is neither a build permission nor a distributable package.

Local composition now has its own receipt and finalization policy. It reuses the
original FF without relabeling its build/source history or rawfile. Source-bound
compiled reference qualification and independent recipient content closure remain
separate. Native execution and distributable ZIP creation require a distinct
coordinator GO; this adapter supplies no native execution path.

The source-selection tests include 12 cases for this selector. They exercise the
real CLI and SDK/Distribution validators: exact source/contract selection,
canonical option spelling, missing compatibility, original-variant collisions,
unchanged BeaconV1 refusal, changed sources, forged closure claims, duplicate
manifest fields, forged zero-Far summaries and refusal before an instrumented
builder could run. Plan/refused-Build snapshots must stay unchanged. Existing
synthetic flow tests and real-finalizer fixture tests retain the original build,
materialization and recipient gates; no native tools or distributable ZIPs run.

### Attach retained GSC audit records

An explicit `-GscAuditEvidence <expectations.json>` is accepted only with
`-Adapter BeaconSelfContainedV1 -Action Plan`. It invokes the pure reader in
`creator_gsc_audit.py`, never the native audit runner. Other adapters and Build
reject this option before reading the evidence. The selected project still needs
the exact variant source and normal compatibility checks.

The expectation object has exactly these fields:

| Field | Required value |
| --- | --- |
| `schema` | `iw7.creator-gsc-audit-input/1` |
| `run_root` | Explicit absolute directory of the retained GSC audit Run |
| `source_sha256` | Exact variant source SHA above |
| `pins` | Independent `tool_sha256`, `source_revision`, `source_sha256`, `tables_sha256` accepted by the unchanged consumption validator |
| `files` | Exactly seven roles below, each `{ "path": absolute_path, "sha256": expected_raw_digest }` |

The roles are `compilation`, `plan`, `build`, `supervision`, `input`,
`consumption` and `assembly`. Build and supervision must be the Run's
`build-receipt.json` and `supervision.json`; consumption and assembly must be its
`witness-variant/consumption.json` and `witness-variant/disassembly.gscasm`.
The input must equal the reviewed plan's explicit variant container path/hash/size.
No directory discovery, executable read, process query, native launch, stock
inspection, resource admission or output write occurs in this command.

Supply hashes from an independent review. Do not derive trust anchors from an
untrusted final state. The reader can check consistency with the supplied pins;
it cannot establish that the caller reviewed them. Changing both evidence and
trusted pins remains outside that guarantee. Files use stable bounded snapshots
of at most 2 MiB each and a 16 MiB group bound, with a second hash pass. The
expectation file is limited to 1 MiB and checked again before returning. These
reads are not a transactional snapshot against a hostile concurrent writer.

The historical compilation record must be the corrected
`iw7.beacon-self-contained-offline/2` form, with exact source bytes, successful
parse/compile/disassembly phase records, container and assembly bindings. It must
keep external-dependency absence, asset closure, runtime and owner claims false.
The old local compilation record with a withdrawn absence claim is refused.
This is a linkage to a historical record, not a fresh compilation or authenticated
proof that a particular compiler produced the bytes.

The consumer imports only the pinned `audit_gsc_consumption.py` validator and
calls `validate_pins` and `validate_witness`. It remeasures container structure,
compressed stack integrity, exact bytecode/stack hashes and terminal function
cursors, then compares the witness's emitted assembly bytes with the separate
assembly file. The recorded variant command must bind the same input, output,
tool and source pins. Far/Pointer counts describe the emitted assembly only;
zero does not certify semantic import absence or a complete dependency graph.

The JSON `gsc_audit` has schema `iw7.creator-gsc-audit-observation/1` and keeps
these different questions separate:

- `artifact_records_bound`, `historical_compilation_record_bound` and
  `native_witness_bytes_bound`: selected bytes and records agree with the pins.
- `structural_consumption_measured`, bytecode/stack cursor values and observed
  opcode counts: the pure validator has checked the retained witness bytes.
- `supervision_success_reported`: the historical supervisor's boolean. A `/1`
  build, including v5, can display structural measurements while its global
  failure remains explicit. A `/1` success boolean never upgrades the protocol.
- `global_completion_record_linked`: only the reviewed `/2` producer
  `eabe74ab65d8ce2a943b54d24b15a60749a0cf2a`, with matching source digest, can
  link the exact plan/build/supervision, nonce/root/lease, successful completion
  fields, named steps/artifact roles and terminal closure within the recorded
  two-second drain and global/output limits. Missing or contradictory records
  fail. This consumer links the pinned supervisor report; it does not repeat
  its guarded completion validation.

`global_build_revalidated`, `native_execution_authenticated` and
`compilation_provenance_authenticated` stay false. Creator does not reopen the
compiler/tool, individual result files, original-control witnesses or historical
job guards. It cannot authenticate their past execution or guard lifetime from
unsigned local receipts. The full native build qualification belongs to the
separately reviewed producer and its retained evidence.

External GSC absence, recipient closure, finalization, package/runtime readiness
and owner acceptance stay false. The proposed package contract is unchanged.
`require_finalization(...)` re-reads the evidence and refuses with these remaining
requirements; it is not a new variant finalizer and is not routed through the
original Beacon builder. A valid observational Plan can exit zero with these
blocking requirements still listed in `pending`.

Validation: 42 real Creator CLI tests plus 19 pure consumer tests pass. They cover
independent pins, changed source/container/assembly, incomplete cursors, false
acceptance claims, wrong run/nonce, missing closure/release, deadlines, unknown
producer/schema, changed artifacts between passes and finalization refusal.
Native invocation is trapped as a test failure. The real v6 retained files also
pass the consumer and CLI: 1480 bytecode and 1808 stack bytes consumed, zero
observed Far/Pointer opcodes, and `/2` completion linkage true. No compiler,
executable rehash, stock read, lease, native run or package was performed by this
validation. V4/v5 retain their historical global failures.

### Encoded references from the reviewed Run /3

`iw7.creator-gsc-audit-input/2` is a distinct optional input, not a reinterpretation
of `/1`. It requires Plan `iw7.gsc-audit-build-plan/2`, build receipt
`iw7.gsc-audit-build-run/3` and the unchanged supervision `/1`, whose completion
record must also set `ReferenceContractVerified=true`. Only producer
`03d3956d648b7aa4637fe1007f9d69ea463631e9` with tool source digest
`23b4de72afa23b1cefc6b03172a18ac945b60e0ab530ea4c40e0493ea34ae350` is accepted.
This reviewed collector correction replaces three hashtable-style indexers on a
JSON-derived PSCustomObject Plan. It supersedes producer `42e6c403`, whose v7 Run
remains globally failed even though its reference witnesses were produced. The
reader, profile, harness, tables, wrapper and two GSC input pins are unchanged.
The explicit consumer pin update is source preparation only: V8 has not been
qualified here and no real reference proof is attached to the prepared project.

The top-level fields remain `schema`, `run_root`, `source_sha256`, `pins`, `files`,
with one additional `references` object: `{source_root, pins}`. The latter pins
contain `decoder` (equal to the top-level pins), `profile_sha256`,
`reference_validator_sha256` and `consumption_validator_sha256`, matching the
reviewed SDK contract. `source_root` is the retained reviewed GSC tool source,
not an executable path or a project-supplied command.

In addition to the seven `/1` file roles, `files` must contain exactly:

| Role | Required location |
| --- | --- |
| `original_input` | Exact original-control input path in Plan |
| `original_consumption` | Run `witness-original/consumption.json` |
| `reference_pins` | Run `reference-pins.json` |
| `reference_controls` | Run `references/controls.json` |
| `variant_native`, `variant_bound` | Run `references/variant-native.json`, `variant-bound.json` |
| `original_native`, `original_bound` | Run `references/original-native.json`, `original-bound.json` |

Each retains the existing `{path, sha256}` independent-pin shape. Creator links
all eight ordered phases and 27 artifact roles (29 with the separately supported
zlib preparation). The controls require 153 opcode cases, two unsupported-size
refusals, four unresolved controls, 159 invocations and zero failures/errors/skips.
It rechecks the pinned reader/profile/harness and eight source tables, executes
only the hash-verified Python reader snapshot, and calls `references.validate`
on both exact retained input containers and their new native witnesses. Each
embedded consumption must equal its companion from this same Run; recomputed
bound reports must exactly match the retained reports. The original control must
still expose `flag_exist` at 212/318 and `flag` at 226/345.

Only `encoded_external_script_reference_absence` may become true. The broader
`external_gsc_dependency_absence_verified`, native/builtin/loader semantics,
recipient closure, package/runtime and owner gates remain unqualified. Local
completion linkage is not authentication of past execution or guard lifetime.
The historical v6 witnesses cannot be converted to this protocol. No accepted
global `/3` Run was used to validate this source-only tranche. Successful reference
witnesses from a globally failed Run remain refused, including a collector failure
after all reference controls passed; they cannot override supervision failure.
The new binding tests use an explicitly synthetic decoder double; they establish
consumer enforcement, not a native qualification or a second operand-decoder test.
The producer-pin correction passes 15 reference-linkage, 19 historical audit and
19 composition tests. Additional cases refuse a consistently repinned old
producer, the old tool-source digest under the new revision, an old native witness
inside new records and even an identical reference file at another Run's path.
Global success and fresh same-Run completion remain mandatory; changing these
source constants cannot reclassify v7 or authorize another execution.

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

## Materialize an existing build locally

Use `Materialize` when a BeaconV1 build has finished and you want an inspectable
local candidate without running another compiler or creating an archive:

```powershell
./sdk/modding/Creator.ps1 -Project C:/author/beacon-source -Adapter BeaconV1 `
  -Action Materialize -BuildRoot C:/author/completed-beacon-build `
  -FinalizeRoot C:/author/fresh-local-candidate `
  -ClientSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -ServerSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 -Protocol 2 -Json
```

`BuildRoot` is the retained completed build directory containing its original
`state.local.json` and outputs. `FinalizeRoot` is a new directory under an existing
parent, separate from the source project, every active project and the build.
An existing destination is refused and preserved. `BuildRoot` belongs only to
this action; it does not change the behavior of `Plan` or `Build`.

This original-build Materialize route accepts only exact `BeaconV1` source/preparation and
keeps the usual source/protocol assertions and active-project compatibility
checks. It refuses `BuildParameters`, `Output` and `GscAuditEvidence`; it cannot
select a native build or ZIP destination. The self-contained source variant
uses the separate composition policy below. Optional `RecipientProof` and `RecipientRoot`
must be supplied together and retain their existing snapshot-only semantics.

Creator calls `Finalize-BeaconProject.py::finalize()` directly through
`creator_materialize.py`. It does not call the builder, even for planning, or
the package writer. The existing finalizer rechecks the source receipt, exact
template/recipe/NCS, completed build phases, original closure/restoration records,
FF/hash, retained inventories, geometry and dump bytes. It applies
`Plan.SourceReceiptSHA256` when present; a missing historical binding remains an
explicit blocker, while a present mismatching binding is a refusal. No source
receipt, prior build state or evidence gate is amended.

After finalization, Creator reopens the ten required candidate files through the
bounded reader, checks the total written byte count, FF/GSC/manifest hashes,
output paths, stored evidence and remaining blockers. Each of the four serialized
assets must match its exact ID/path/size/hash record and the manifest closure hash;
missing, duplicate or redirected representation records are refused. The two
validation reports must exactly match newly computed pure SDK reports for the
measured manifest and candidate. Creator then rechecks file identities and hashes.
`materialized=true` therefore requires actual checked files, not a positive boolean
returned by a finalizer. Changed post-write output is refused and retained for
inspection; Creator does not delete external replacements. These integrity checks
do not authenticate historical execution statements in the local evidence.

**Exit 0 means the local candidate was created and checked.** It can correctly
report `materialized=true`, `build_verified=true`, `package_ready=false` and
`runtime_ready=false`, with `build_executed=false` and `packaged=false`. Remaining
blockers appear both in `finalization.blockers` and the materialize step's human
readable details, as well as `pending`. The JSON also includes the candidate and
manifest paths, exact hashes, `creator_output_verified` and the ten measured file
records. Pending statements from the unchanged source manifest are retained as
`source_project_pending`; they no longer misleadingly label the created candidate's
FF as unestablished. Active-project pending statements remain in `pending`.
This is an authoring checkpoint, not package, gameplay or connection
acceptance. No ZIP, deployment, game launch, server connection or resource lease
is implicit.

Seventeen real CLI additions cover successful local output with blockers,
historical binding limits, changed FF/source hashes, unclosed/unrestored builds,
fresh/nonoverlapping destinations, missing inputs, refused build/ZIP/audit options,
recipient proofs, active-project collisions, unchanged Plan/Build options, a
builder that must never be called, a false success without files and post-write
payload drift. They use the existing asset-free finalizer fixtures. An initial
test-double indentation error was corrected; it did not execute a builder or
change a production gate.

Review of the first Materialize implementation found that merely rehashing the
four serialized assets did not compare them with their expected receipt/manifest
hashes. Flipping one byte in the XSurface after finalization, without changing its
size, incorrectly returned success. The corrective checks above reject that case
for all four assets, changed representation mappings/metadata, a corrupted asset
whose receipt hash was also updated, and altered plan/package reports. These
eleven post-write fault cases use only synthetic fixtures and preserve the rejected
candidate. The previously created real candidate was not modified for this review.
Correction validation: 78 Creator/consumer tests pass, including 59 real Creator
CLI test methods. The finalizer suite passes 34 tests; its one symlink-creation
case is skipped because Windows does not grant that operation in this session.

On 2026-10-12, the new action was also exercised against the retained real
source-bound build from the earlier Creator run. It returned exit 0 after
creating and reading back ten files totaling 23036 bytes. The 1048-byte FF kept
SHA256 `3fa49bcdfd08857bb37c198af7a49af78675b940b022e160343552d3f8b71da8`;
the manifest kept SHA256
`1b37643436183fe864f7057873f4c49039c8843ec78b2826b2c6bda1d8c5e861`.
The original source/build receipt hashes were checked before and after and did
not change. `source_receipt_bound` and `creator_output_verified` were true;
`build_executed`, `packaged`, runtime and owner acceptance remained false.
The two remaining blockers were recipient material/transitive image/technique
resolution and the compiled utility script/imports. No compiler, extractor,
retail read, lease, new native execution, ZIP or deployment was involved.

### Compose a reviewed script with retained assets

`BeaconSelfContainedV1 -Action Materialize` accepts a separate project folder
containing the exact reviewed variant source and an explicit `composition.json`:

```json
{
  "schema": "iw7.creator-composition/1",
  "script": {
    "policy": "beacon-self-contained-source/1",
    "path": "sdk_beacon_self_contained.gsc",
    "bytes": 5535,
    "sha256": "9de9b76dc25293146999c71653bd407d8cb639e107293f6de87084fed90eee1c"
  },
  "assets": {
    "policy": "beacon-retained-build/1",
    "project": "C:/author/original-beacon-source",
    "build_root": "C:/author/completed-beacon-build",
    "source_receipt_sha256": "independently reviewed original source-receipt.local.json digest",
    "build_receipt_sha256": "independently reviewed original state.local.json digest",
    "ff_sha256": "independently reviewed retained mod.ff digest"
  },
  "evidence": {"gsc": null, "recipient": null}
}
```

The three digest descriptions above must be replaced by actual lowercase SHA256
pins. Roots must be absolute, unredirected paths. `assets.build_root` must equal
the explicit CLI `-BuildRoot`. The source project must be separate from the
retained asset source/build, and output must be fresh and nonoverlapping.

```powershell
./sdk/modding/Creator.ps1 -Project C:/author/variant-project `
  -Adapter BeaconSelfContainedV1 -Action Materialize `
  -BuildRoot C:/author/completed-beacon-build -FinalizeRoot C:/author/fresh-composition `
  -ClientSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 `
  -ServerSource 77e6d4d24e918ee363b3feee3735c3b889dff7d7 -Protocol 2 -Json
```

`creator_composition.py` dispatches only the two registered policies above.
Unknown policies, extra fields, commands, edited scripts (even repinned) and
arbitrary assets are rejected. The contract separates script authorship policy,
asset provenance and evidence, so later reviewed policies can extend it without
changing those roles or accepting executable commands from JSON. This first
policy deliberately does not qualify arbitrary user scripts.

The shared `retained_beacon` checks the original exact project, inventories,
FF/dumps, geometry/readback and four closed/restored phases. A matching original
`Plan.SourceReceiptSHA256` is mandatory for composition. The FF and all four dump
representations are copied byte-for-byte. The actual `rawfile:sdk_beacon` stays
in the new manifest; its 28-byte marker is `Compiled using x64 ZoneTool.`. The
prospective `rawfile:sdk_beacon_self_contained` is not invented. The standalone
variant GSC, its namespace/fs_game, fresh manifest and `finalization.json`
composition receipt are distinct from original source/build records. No original
GSC payload or utility edge is added. Existing model/NCS conflicts remain active.

`evidence.gsc`, when supplied, is `{path, sha256}` for a bounded independently
pinned Creator audit expectation file, using `/1` or `/2` above. Historical
consumption evidence retains the encoded-reference question. A verified `/2`
input clears only that exact compiled-input question; it does not qualify native
builtin semantics, a script loader or the entire FF. Missing evidence is explicit
`unresolvedQualification` without an asserted utility dependency.

`evidence.recipient`, when supplied, is `{run_root, phase_sha256, csv_sha256}`.
Creator reads only fixed `references/phase.json` and
`work/enemy-catalog/sdk_beacon_recipient_a.csv`, verifies independent pins and
invokes the existing pure `verify_phase`. H can supply these four non-default
reference observations; this route does not invoke the fuller binder, rehash an
EXE/stock, attest the outer Run or infer content hashes from a CSV. Material hash,
techset/images and transitive unresolved nodes stay unchanged. An inconsistent
supplied proof fails rather than silently becoming pending.

Ten files are written through the shared exclusive writer and SDK validators.
The shared P2 verifier checks payload/node/manifest hashes, exact node mappings,
recomputed reports and final identities. Composition additionally pins its whole
finalization receipt. Failed post-write verification retains the candidate for
inspection. Exit 0 means this checked local composition exists; `asset_build_reused`
and `asset_source_receipt_bound` are true, `variant_ff_built` is false. Package,
closure, runtime and owner readiness remain false even with GSC and H evidence.
No source/build history is relabeled, and no builder or ZIP writer is called.

This tranche uses synthetic source/build/recipient fixtures and real Creator CLI
tests only. No real composition, native execution, lease, stock read, distributable ZIP or
deployment was performed. The previously corrected real Beacon candidate remains
separate evidence for the original Materialize route.

Validation: 105 Creator/consumer tests pass (61 CLI methods, 44 pure tests),
including 16 composition tests and 11 new reference-linkage tests. The shared
finalizer still passes 34 tests; one symlink-creation case is skipped because
Windows permission is unavailable. Existing Build-flow tests use only tiny
synthetic ZIP fixtures; no distributable archive was produced. Regressions cover
global collector failure despite successful witnesses and replacing a reader path
after its hash check: unverified replacement Python is never executed. Historical
audit files and all newly consumed reference inputs enter the final composition
identity/hash recheck before writing.

Post-review correction: the first composition implementation rechecked source
inputs only before writing. A same-size change to the retained FF during the
manifest write could therefore leave a stale source receipt beside an apparently
verified candidate. The shared writer now rechecks original inputs again after
all writes, outside its cleanup transaction, preserving a rejected candidate.
Both Materialize routes retain that same input reader and recheck it after the
final candidate readback, immediately before returning success. Composition's
script/descriptor, original asset records and every attached GSC/reference source
and recipient phase/CSV input are included. These are bounded repeated checks,
not a claim of a filesystem-wide atomic snapshot or a hostile-writer lock.

Synthetic regressions first reproduced the accepted stale-input result, then
verified refusal for the FF during writing and for the FF, GSC, descriptor,
recipient CSV, consumption witness and reference table after final readback.
A real CLI fixture also checks original Beacon input drift after its finalizer
returns. All rejected candidates remain available; no real asset was mutated.
Corrective validation: 109 Creator/consumer tests pass (62 CLI methods, 47 pure
tests); the finalizer passes 34 with the same one Windows symlink skip. The
prepared real composition output remains absent and its original pins unchanged.

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
