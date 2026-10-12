# BeaconV1 candidate finalization

`Finalize-BeaconProject.py` replaces the machine-specific, ignored preparation
script for the existing BeaconV1 candidate. It materializes measured files and a
common SDK manifest from explicit, already completed source/build directories.
It does not compile, extract, start a game, acquire a lease, access stock, make
network calls, deploy or write a ZIP. `ops/modding/Package-CommunityMod.py` remains
the only community ZIP writer.

The read-only `retained_beacon` helper and exclusive `write_candidate` helper are
also reused by Creator's separate [script composition policy](CREATOR.md).
BeaconV1's exact-template checks, rawfile identity, utility edge, public result
and package blockers remain unchanged. Reusing its asset bytes does not rename
its historical source/build receipt or assert a new native build.

## Interface

Use Python 3.10 or newer, with the standard library only:

```powershell
python -B sdk/modding/Finalize-BeaconProject.py `
  --project <prepared-source-directory> `
  --build-root <completed-Build-BeaconFF-RunRoot> `
  --output-root <fresh-candidate-directory> `
  --client-source <exact-lowercase-40-character-commit> `
  --server-source <exact-lowercase-40-character-commit>
```

The two source arguments are optional target assertions. Omitting them leaves
the existing distribution capability/source checks blocked. They do not measure
a local or remote executable. No aliases or separate FF/dump/receipt paths are
accepted: these inputs are derived from the explicit project and build roots.

The importable function is:

```python
finalize(project, build_root, output_root, *, client_source=None,
         server_source=None, recipient_proof=None, recipient_root=None)
```

The CLI prints JSON with `api: "beacon-finalize/1"`. Exit 0 means that a candidate
was materialized, including a blocked candidate. Consumers must inspect
`materialized`, `closure_complete`, `package_ready`, `runtime_ready` and `blockers`;
exit 0 is not authorization to package or deploy. Input/materialization errors
return exit 1 and `materialized: false`; argparse usage errors use exit 2.
`candidate_root`, `manifest_path`, `exact_hashes`, `source_receipt_bound` and
`bytes_written` accompany success. There is no deployment-readiness field.

Current v1 always returns `closure_complete: false`, `package_ready: false` and
`runtime_ready: false`. It has no fresh recipient-resolution proof adapter.
Creator must surface blockers and stop before invoking the ZIP writer.

## Fixed inputs and outputs

The project must have the ten-file `iw7.beacon-source-receipt/1` inventory emitted
for this prepared original Beacon: the two model source files, three zone CSVs,
NCS JSON, `model-ff-plan.json`, `manifest.json`, `sdk_beacon.gsc` and
`beacon-preparation.json`. All recorded sizes and hashes are rechecked. The GSC
must exactly match `examples/beacon/sdk_beacon.gsc`; the manifest must match the
shipped example, optionally with the GSC hashes filled by `prepare_beacon.py`.
Zone/NCS identity is fixed. Arbitrary mod projects and edited GSC are unsupported.
Unlisted files are neither enumerated nor copied.

The build root must contain:

- `state.local.json`: successful `iw7.beacon-ff-build/1`, closed phases, confirmed
  restoration, preserved stock, verified inventory/readback and no retained
  lease or failure. Its source/work roots must match the explicit roots.
- `mod.ff`: the recorded bytes/SHA-256 and IW7 envelope, at most 1 MiB.
- `assets.csv`, `work/dump/sdk_beacon/sdk_beacon.csv` and `verify/stdout.log`:
  exactly the fixed five-asset inventory, with no recognized verification error.
- `build/phase.json`, `verify/phase.json`, `dump/phase.json`, `read/phase.json`:
  four successful native phase receipts. Native-child PIDs are not confused
  with the Python phase-parent PIDs in state.
- `read/stdout.log`: the same original 24-vertex, 12-triangle, single-bone/Lod1M
  geometry result as state. Each original model dump must equal the retained
  `roundtrip/` reader input. NCS meaning must match the source. The generated
  rawfile is the exact 28-byte `Compiled using x64 ZoneTool.` marker.

The fresh output contains the two payloads `mod.ff` and `sdk_beacon.gsc`,
`manifest.json`, `finalization.json`, `validation-plan.json`,
`validation-package.json`, and four small serialized dump snapshots under
`evidence/serialized-nodes/`. Manifest payload paths refer only to the two
payloads; evidence is not added as downloadable content. All evidence statuses
remain pending. Missing utility import coverage is added as an unresolved-hash
recipient node in the common closure, not hidden by the template omission.

Input reads have fixed size bounds; total written file bytes, including the last
validation report, cannot exceed 2 MiB. Redirected ancestors, symlinks/reparse
points, unsafe relative names and existing output roots are refused. The output
must be outside both project and build trees, with no ancestry overlap in either
direction. Inputs are rechecked immediately before writing. Error cleanup is
nonrecursive and checks the identities of files/directories it created; changed or unrelated content is
preserved. This is a local consistency guard, not a security boundary against a
hostile process racing filesystem operations under the same account.

## Receipt binding and recipient limitations

For prospective builds, the agreed field is
`state.local.json -> Plan.SourceReceiptSHA256`: the actual source receipt hash
measured by `Build-BeaconFF.ps1` after its initial hash check, retained under a
read guard and rechecked before staging. When this field exists, finalization
requires a valid SHA-256 matching the remeasured project receipt and reports
`source_receipt_bound: true`. A mismatch is rejected.

The retained historical build has no such field. It can produce a useful blocked
candidate with `source_receipt_bound: false` and an explicit blocker; it is never
silently rewritten or upgraded. A matching receipt hash establishes consistency
with the supplied build declaration, not publisher authentication. This helper
also does not parse arbitrary FF/model structures, execute the reader again or
prove that retained dump bytes originated from a particular FF. Those remain
limitations of the existing build records and native validation chain.

An optional pair `--recipient-proof <json> --recipient-root <directory>` accepts
only the exact reviewed `ops/model-lab/recipient.evidence.json` snapshot contract
(`iw7.model-recipient-evidence/1`). Its three historical material snapshot files
must still exist and match their pinned hashes in the explicit root. It can fill
the historical material JSON representation hash, but **cannot complete closure**.
Boolean readiness claims and other proof formats are rejected.

The material's current resolution and transitive image/technique dependencies
remain unqualified. So does the current compiled `scripts/engine/utility` and its
imports; the manifest node uses `.gsc`, while native lookup omits that suffix.
Decompiled source is not a substitute for the compiled script representation.
Dump-node hashes identify serialized snapshot bytes, not live engine objects.
Historical runtime observations or matching protocol/source pins do not change
these gates.

## Offline verification

```powershell
python -B -m unittest discover -s sdk/modding/tests -p test_beacon_finalize.py -v
```

The suite uses tiny synthetic FF bytes and receipts, with the real shipped GSC,
manifest and validators. It proves deterministic output, hash/shape/root checks,
failure and closure gates, total byte budget, prospective receipt binding and
selective cleanup. Synthetic receipts are not engine/load/render proof. The real
symlink test is skipped when the host cannot create symlinks; a separate injected
Windows reparse-attribute test still exercises the rejection path.

On 2026-10-12 the finalizer was also run read-only against the retained Beacon
source and completed FF build, producing a separate small candidate. The FF
remained 1,048 bytes, SHA-256
`76ed0701dc1480c501604db04999f300394c65877aa24a70dfe7afc2cd662d4a`;
the GSC remained 4,802 bytes, SHA-256
`8ba85b3f5b3014d0c4d02b0e71f49bf617959b486502e4c63243b065abc2a0b6`.
Both payloads passed the existing static hash checks, plan validation was valid,
and package validation remained blocked. No native tool or game ran for this
finalization check. The first local attempt rejected a mistaken expected newline
on the rawfile marker; inspecting the actual 28 bytes corrected that expectation
without changing the retained build or any readiness claim.

Review correction on 2026-10-12: the initial overlap check refused output ancestors
but allowed a fresh output below the project or build directory. Both directions
are now rejected before materialization. Two regression cases reproduced the old
failure and now verify refusal, absent output and unchanged input-tree contents.

Next: integrate with Creator, retain the prospective source-receipt binding in
new admitted builds, and obtain independently reviewed current recipient closure
before adding a supported proof adapter or allowing packaging.
