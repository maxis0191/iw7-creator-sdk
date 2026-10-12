# Recipient Run record binding

`bind_run.py` binds a retained `verify_phase` JSON report to one completed,
restored `iw7.recipient-closure-run/1`. It reads files only. It does not invoke
ZoneTool, reserve resources, restore stock, disassemble GSC, write a package or
change the Beacon Finalizer's gate.

Both reviewed producer modes are supported:

| Plan phases | Required completed status | Script bytes |
| --- | --- | --- |
| `references` | `ReferencesObservedScriptNotRun` | Must remain false |
| `references`, `script` | `ReferenceAndScriptObservationsVerified` | Must be true, with a measured dump |

A failed, timed-out, unfinished or quarantined Run cannot supply a positive
binding, even if some logs or outputs exist. Recipient B's diagnostic failure
does not become a successful reference observation. No successful real Run was
used to validate this adapter; the tests are synthetic, asset-free fixtures.

## Independent inputs

Call `bind_run(expectations)` or the read-only CLI:

```powershell
python -B sdk/modding/recipient/bind_run.py --expectations $expectationsPath
```

The CLI writes its result to stdout and exits zero only for a consistent local
binding; that exit code does not mean the package or dependency closure is ready.
Missing, changed or unsupported evidence exits nonzero. It never updates pins.
The JSON expectation file has exactly these fields:

| Field | Value and source of trust |
| --- | --- |
| `schema` | `iw7.recipient-run-expectations/1` |
| `run_root` | Explicit absolute local Run directory |
| `state_sha256` | Expected raw hash of its final `state.local.json`, supplied by the independent reviewer |
| `plan` | `{ "path": absolute_path, "sha256": expected_raw_hash }` for the reviewed prospective plan JSON |
| `spec_path` | Explicit absolute path of the original producer spec; its hash must be in `source_pins` |
| `source_pins` | Independent absolute-path-to-SHA256 map covering the original spec, producer sources, stock receipts, interpreter, candidate receipts and requests |
| `provider_pins` | Independent map of the twelve reviewed provider names to `{ "Path": absolute_path, "SHA256": expected_hash }` |
| `run_files` | Exact Run-relative-path-to-SHA256 map of the retained files below |
| `observation` | `{ "path": absolute_path, "sha256": expected_raw_hash, "phase": "references" or "script" }` for the existing external `verify_phase` report |

The original spec identifies `StockReceipt`, `StockBindingReceipt`,
`ReviewedStockManifest`, `PythonExe`, their `SHA256` fields, `CandidateRoot`,
`CandidateArtifactSHA256`, `RequestRoot` and both request hashes. Their roles
must agree with the reviewed plan and independent source pins. The candidate
EXE remains the exact E7 hash required by `verify.py`. The three candidate JSON
receipts are byte-bound; this adapter does not rerun their build validator.

Producer pins include `recipient_phase.py`, `recipient_contract.py`,
`Recipient.Core.ps1`, `Run-RecipientClosure.ps1`, `provider-pins.json`, and
`Recipient.Light.ps1` when present in the reviewed plan. Provider names are the
exact twelve in `PROVIDERS`; their current files are rehashed and compared with
the producer's pinned provider manifest. Unexpected source roles are refused.

**Do not generate these trust anchors from the untrusted final state.** Compare
the proposed plan, producer/provider revisions and source hashes independently;
retain the reviewed plan before execution. After the Run, supply separately
reviewed final-state, retained-file and external-report hashes. The program
cannot determine whether a caller really performed that independent review.
Changing both bytes and the caller's trusted hashes is outside its guarantee.

## Retained file set

`run_files` contains `backup/recovery.local.json` and, for every selected phase:

- `<phase>.json`, `<phase>/phase.json`, `<phase>/stdout.log`, `<phase>/stderr.log`;
- references: `work/enemy-catalog/sdk_beacon_recipient_a.csv`;
- script: `work/dump/paris_enemy_cp_zmb_sdk_beacon_recipient_scripts/scriptfile-manifest.csv`
  and `work/dump/paris_enemy_cp_zmb_sdk_beacon_recipient_scripts/scripts/engine/utility.gscbin`.

The state and external observation have separate hash fields. Optional
`native-start.json` and light diagnostics are not accepted as closure evidence.
They may remain in the directory but are outside this adapter's selected set.
No discovery, recursive scan or stock-content hashing is performed.

The original restoration removes the staged stock links, tool and request files
from `work`. The adapter rehashes their pinned **source** tool/request files and
small stock receipts. It compares all staged input descriptors to the reviewed
plan and checks that those temporary paths are absent now. It never recreates
them. The recovery JSON must match the state's restored transaction and exactly
describe the fresh Run's absent-before inputs and empty profile/protected sets.

The producer mutates the shared `StockInputs` objects by adding `SourceId` and
`TargetId`. Only these two additions are removed when comparing the final plan
with the prospective plan. The state's input records still require both IDs,
the expected source identity and the appropriate recorded link/copy relationship.
These historical NTFS identities are receipt data, not new stock measurements.

## Checks and limits

The adapter pins raw state, plan, phase specs, receipts, logs, outputs and external
observation bytes. It compares nested phase receipts with the actual files,
reruns `verify_phase`, and requires the complete external report to equal that
remeasurement. Actual stdout must contain the exact source-zone sequence derived
from the reviewed stock descriptors. Native error text and contradictory capture
counts are refused. The fixed native action and exact request bytes are bound
through the reviewed producer contract; there is no claim of captured argv.

Original Python job records must include creation identity, successful exit,
zero final members, a bounded ordered post-root drain sequence ending with zero
members, and resolved registration. `ClosedBeforeRegistration` is supported only
with that complete terminal evidence. The Python PID is not the native PID.
Successful capture threads and a locator PID alone never satisfy job closure.

Paths are absolute local allowlisted paths or fixed safe Run-relative paths.
Symlinks, reparse ancestry, traversal and Windows device/ADS paths are refused.
Individual evidence files are bounded to 2 MiB; source tool/interpreter reads are
streamed up to 64 MiB each. The whole group, including the second hash pass, is
bounded to 256 MiB and 128 distinct files. Identities and hashes are rechecked
across the group; temporary-input absence is also rechecked before returning.
This is not a transactional filesystem snapshot against a hostile concurrent
writer. Reject or retry changed evidence after the Run has stopped writing.

`closed_run_record_bound` and `observation_bytes_bound` mean that local records
and bytes agree with the supplied independent pins. Unsigned local JSON cannot
authenticate native execution, historical job ownership or retail provenance.
Two different origins producing identical bytes cannot be distinguished by a
hash. Copied identical output alone is not evidence of which process produced it.

Reference verification establishes the four recorded presence checks, with no
serialized material/image/techset content or dependency inventory. A script dump
adds exact named-container, compressed stack, expanded stack and bytecode hashes;
it still has no decoded import inventory. Do not silently reinterpret this native
named export as the different `GSC\0` container used by the separate GSC audit.
All native-authentication, stock-remeasurement, import/graph-completeness,
closure, package, runtime and owner-acceptance booleans remain false.

## Validation

```powershell
python -B -m unittest discover -s sdk/modding/tests -p test_recipient_run_binding.py -v
```

The 25 adapter tests pass alongside the existing 26 recipient tests. The 35
Finalizer tests remain unchanged: 34 pass and one platform symlink-privilege
test is skipped on this Windows host. The adapter's reparse-attribute test runs.

Fixtures cover references-only and both phases, cross-run paths, copied phases,
missing/changed outputs, forged summary fields, independent pin mismatches,
exact requests, log order/errors/counts, closure/registration/restoration gaps,
duplicate JSON fields, reparse paths and changes during analysis. Fixture tool
hashes are explicitly mocked; no synthetic executable is launched. A real
successful retained Run remains necessary for an integration witness.
