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
binding, even if some logs or outputs exist. A fatal-text diagnostic cannot supply
one either. No successful real Run was used to validate this adapter; the tests
are synthetic, asset-free fixtures. Compatibility with D's prospective plan and
small stock receipts was checked separately; that does not assert D succeeded.

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

## Explicit supplemental stock profile

The reviewed `fde8c49b` producer adds `RecipientStockBindingReceipt` and
`RecipientStockBindingReceiptSHA256` to the original spec, the receipt to
`source_pins`, and `StockBudget` to the plan. This complete combination selects
the supplemental contract. Partial combinations are rejected. The extra producer
roles `Recipient.Stock.ps1`, `recipient_dialog.py` and `Recipient.Light.ps1` are
then all mandatory and rehashed. Unknown roles still fail; recognizing one new
filename or trusting a declared hash alone does not enable an overlay.

The supplemental contract also requires `FatalTextDiagnostic=false` in the plan,
`DiagnosticOnly=false` in the final state, and the exact retained diagnostic
limits (250 ms poll, 16 KiB text, eight controls, 200 ms message timeout, 64 KiB
record). The ordinary 240/245/600-second limits remain unchanged. An observer
receipt or fatal dialog cannot replace positive reference output and closure.

Four bounded JSON receipts are rehashed and semantically linked:

- The fixed historical baseline SHA `4cf67ebe1645c6c0761b9a24cb4e4630edee9c5d737742c704d624fe60cb3850`
  must describe its closed, restored 72-entry 63-link/9-copy profile.
- The current `iw7.ff-stock-observation/1` must bind that baseline and the fixed
  reviewed manifest SHA `9116255ef148a324df15fa914795a7917615f023973111fdc39ae7329a9dcbf4`.
  Each of its 72 descriptors is checked against the baseline and reviewed content
  row, with the exact external TLS exception. These become 71 links and the
  existing 77-byte sentinel copy. Historical and current source IDs are kept
  distinct; relocation metadata is not promoted into fresh content proof.
- The reviewed content manifest supplies the immutable expected names, sizes and
  hashes. Duplicate names or malformed rows fail.
- The separate `iw7.recipient-stock-observation/1` must have the exact
  `observed-cp-paks-17-19-37-53` profile, tool source
  `fab935826c898806855376662a8a03317b3ad8f1`, stock root, reviewed-manifest hash,
  timestamp, and `ContentVerification=DeferredUntilAdmittedRun`.

The overlay contains exactly these four ordered entries, with the reviewed
content hashes also fixed by the adapter's `PAKS` contract:

| Target | Declared bytes | Source |
| --- | ---: | --- |
| `zone/assetfile17.pak` | 104595492 | Stock root `assetfile17.pak` |
| `zone/assetfile19.pak` | 418201636 | Stock root `assetfile19.pak` |
| `zone/assetfile37.pak` | 53477412 | Stock root `assetfile37.pak` |
| `zone/assetfile53.pak` | 3817508 | Stock root `assetfile53.pak` |

Each observation requires its recorded NTFS source identity, timestamp, ordinary
writable attributes, exact hash/size and hardlink mode. Unknown overlay fields,
target-ID claims, extra/reordered PAKs, traversal, source-root changes, read-only
or reparse attributes fail. The derived 72+4 descriptors must equal the reviewed
plan and final inputs. The budget is recalculated from these descriptors, with
identity deduplication rejecting inconsistent sizes/hashes for an aliased ID.
It must declare 580092048 supplemental bytes under the fixed 600 MiB ceiling,
zero supplemental copies, 75 stock hardlinks and 77 total copied stock bytes.
`ContentVerified` and `AdditionalResidentBytesMeasured` must remain false.

All 79 managed inputs, including E7 and the two requests, remain subject to the
same original-job closure, exact restoration transaction, recorded source/target
identity checks and current temporary-path absence checks. The overlay cannot
be omitted from recovery. A positive result adds `stock_profile_binding` with
the receipt hashes, four supplemental input records and recomputed budget;
`content_remeasured` stays false.
Plans without an overlay keep `stock_profile_binding=null` and do not silently
gain PAK roles.

### Named four- and five-PAK producer contracts

The reviewed producer `a8c16c037c92aae058ade16355240a409a150af0` has two
explicit stock profiles. The adapter supports three exact record shapes:

| Observation | Plan/input shape | Supplemental scope and ceiling |
| --- | --- | --- |
| `/1`, `observed-cp-paks-17-19-37-53` | Historical budget, no `StockProfileId` | Four PAKs, 580092048 bytes, 600 MiB ceiling |
| Same `/1` profile | Both named budget fields and every supplemental `StockProfileId` | Same four PAKs and ceiling |
| `/2`, `observed-cp-paks-17-19-37-53-69` | Both named budget fields and every supplemental `StockProfileId` | Five PAKs, exactly 966557876 bytes and ceiling |

The named fields are `SupplementalProfile` and `AdditionalBytesBeyondFourPAKs`.
The latter must be zero for four PAKs or 386465828 for five. Every supplemental
input's `StockProfileId` must equal the observation's explicit profile. Partial
named fields, missing/mixed input IDs, unknown profiles and cross-schema receipts
are rejected. A five-PAK plan cannot use the historical unnamed shape. No profile
is inferred from file availability, an input count or a caller-supplied budget.

The fifth and last input must be `zone/assetfile69.pak`, sourced directly from
the same stock root, with 386465828 bytes and reviewed expected SHA256
`042c8d62a3a24acd21a5502a5a111e6e426e870505da3cdd62ada3c3a23c496f`.
The `/2` observation additionally requires `AdditionalDependencyEvidenceSHA256`
equal to the original E2 fatal record's reviewed digest
`867e858ecd4bffde50a04e62488e42b73f528177e0e01b51a081bc030dbbb280`.
This checks a fixed evidence reference; the adapter does not reopen that fatal
record or reinterpret its failure as a positive observation. The `/1` observation
does not accept this extra field. A sixth entry, another PAK, reordered entries
or changed source/hash/size/identity/attributes still fail.

The five-PAK profile produces 77 stock descriptors, 76 stock hardlinks and the
existing 77-byte sentinel copy: 80 managed paths with E7 and both requests.
All 80 require exact restoration entries and current absence. The actual
reviewed baseline plus this overlay declares 46 unique stock identities and
1419496893 hash-read bytes. These totals are recomputed from receipt metadata;
they are not retail reads or memory measurements. Supplemental copying remains
zero, and content/closure/package/runtime/owner qualification remains false.

`stock_profile_binding` reports `observation_schema`, the explicit `profile`,
`producer_contract` (`legacy-four-pak/1` or `named-profile/1`) and the fixed
`additional_dependency_evidence_sha256` (null for four PAKs). The existing
receipt hashes, descriptors and recomputed budget remain included. The outer
plan, Run and binding schemas stay `/1`; an unchanged outer schema does not
authorize arbitrary new inner fields.

### Complete 33-asset PAK profile

The separately reviewed source contract `9f9b56f` adds only the explicit profile
`doom-reviewed-all-asset-paks-20261012`, observation schema
`iw7.recipient-stock-observation/3`. It adds 32 ordered `zone/assetfile*.pak`
descriptors to the existing baseline `zone/assetfile1.pak`. The 33 fixed names,
sizes and historical expected hashes come from inventory proposal `f57b530`
and are pinned as `BASE_PAK`/`COMPLETE_PAKS` in the adapter. No directory scan,
missing-file retry or automatic profile growth is accepted. The 49 `imagefile`
entries recorded by the inventory are excluded from staging and the byte budget.

This profile requires both of these independent evidence references:

- `AdditionalDependencyEvidenceSHA256` must be F's fatal digest
  `67995123ab95d54de3ddb9ffb0f52015daa0978f3c782c977a7c9a3a3c9f58f3`.
  It explains the expansion and does not make F successful.
- `CompleteInventoryEvidenceSHA256` must be
  `683c8a39b6bd289a2acc0a27129a038361d5a217d6ef129d07da739feb6f76bf`.
  The original spec must additionally supply `RecipientCompleteInventoryReceipt`
  and `RecipientCompleteInventoryReceiptSHA256`; that exact file is mandatory
  in the independent source pins and the reviewed plan's `SourceHashes`.

The complete inventory is a fifth stock JSON receipt. It is limited to **128 KiB
on every read**, including the initial source-pin pass and final hash recheck.
The reader hashes and parses the same bounded byte snapshot, checks handle/file
identity around each read, rejects changes across reads and retains each file's
strictest read limit. It does not use a separate unbounded JSON open after hashing.
BOM bytes are included in the digest and removed only for JSON decoding. The
producer snapshot fix `e0654a74` also holds its Windows read guard through hashing
and parsing. This adapter does not re-attest that historical guard or claim that
its own repeated reads are an atomic hostile-writer snapshot.

`iw7.recipient-pak-inventory-proposal/1` must bind the same stock root and reviewed
manifest, contain exactly 82 unique file descriptors (33 `assetfile`, 49
`imagefile`), and retain zero retail bytes read, no missing reviewed entries and
no unsafe attributes. Each descriptor remains metadata with `ContentVerified=false`.
The 33 asset entries require distinct recorded IDs, exactly 4705977508 logical
bytes, and the fixed reviewed names/sizes/hashes. For baseline pak1 and every
supplemental entry, ID, size, seven-digit timestamp, attributes and expected hash
must match that independent inventory. These are recorded IDs, not current NTFS
measurements. A changed inventory cannot self-authorize itself by changing its
spec/source pin: the fixed inventory digest must still match.

The named budget must use exactly 4695508096 supplemental bytes and ceiling,
4115416048 additional bytes beyond the original four PAKs, zero PAK copies,
103 stock hardlinks and the unchanged 77-byte sentinel copy. With the actual
baseline, the descriptors account for 73 distinct stock IDs and 5148447113
declared hash-read bytes. There are 104 stock inputs and 107 managed paths;
every managed path remains part of the exact restoration/absence gate. The
budget calculator also checks the ordered profile scope itself.

Legacy, named four-PAK and five-PAK contracts reject the complete-inventory fields
and source role. The complete profile requires both fields, `/3`, its own fatal
and inventory pins, all 32 named input IDs, and its exact budget. No old ceiling,
partial source role, imagefile substitution or mixed contract is accepted.
The report adds `complete_inventory_metadata_bound=true` and
`complete_inventory_sha256` only for this profile; older profiles receive false
and null. All stock-content, dependency/closure, package/runtime and owner claims
remain false. This source support does not approve a Plan or authorize a Run.

**No retail source is opened or hashed by these semantic checks.** Stock source
paths are compared lexically and attributes/identities are checked as recorded
metadata. Actual current retail ancestry or identities are not inspected here.
The historical content check belongs to the pinned admitted producer; this
adapter binds its records without inventing a separate measured content witness.
Only the small receipts, producer/provider sources, tool, requests and retained
outputs go through the bounded file reader. Local unsigned records remain
subject to the trust limits below.

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

The 63 adapter tests pass alongside the existing 26 recipient tests. The 35
Finalizer tests remain unchanged: 34 pass and one platform symlink-privilege
test is skipped on this Windows host. The adapter's reparse-attribute test runs.

Fixtures cover references-only and both phases, cross-run paths, copied phases,
missing/changed outputs, forged summary fields, independent pin mismatches,
exact requests, log order/errors/counts, closure/registration/restoration gaps,
duplicate JSON fields, reparse paths and changes during analysis. Fixture tool
hashes are explicitly mocked; no synthetic executable is launched. A real
successful retained Run remains necessary for an integration witness.

The overlay fixtures use synthetic 72-entry baseline metadata and mock only its
baseline/manifest pins; PAK names, sizes, hashes and profile ceilings use the real
fixed contracts. They cover both phase modes, incomplete/unknown source
roles, changed baseline/overlay receipts, false content claims, path/ID/hash/size/
attribute changes, alias inconsistencies, missing recovery entries and remaining
temporary links. A reader spy rejects any retail/PAK open during the valid test.
The separate read-only comparison of D's actual prospective plan and four small
stock receipts passed: 45 distinct IDs and 1033031065 declared hash-read bytes,
with 794820 bytes read including rechecks and zero retail reads. It is a receipt
compatibility check, not a native success or a fresh stock-content measurement.

The named-profile additions cover all three supported shapes, strict schema/E2
evidence binding, the fifth PAK, partial/mixed IDs, wrong budgets, both phases,
failed Run refusal, original-job closure and recovery/absence of the fifth path.
The synthetic baseline is deliberately tiny and has different ID deduplication
from retail; its hash-read totals are not presented as real stock totals.

A separate read-only check of F's independently pinned prospective plan, spec
and four small stock JSON receipts passed: 77 stock inputs, 80 managed paths,
966557876 supplemental bytes, 46 IDs and 1419496893 declared hash-read bytes.
Six JSON files were read, totaling 797904 bytes including the second hash pass;
no retail source was opened. F's real, separately pinned final state is failed
after an `assetfile101.pak` fatal request. The adapter rejects it at the completed
status gate even though its tree and restoration were reported closed. This
negative check read only the plan and state and supplied no fabricated source,
output or observation pins. It proves the rejection gate, not a complete positive
Run integration. E2 and F remain failures; stock sufficiency remains unresolved.

Fourteen complete-profile additions cover 107-path linkage without a retail
open, both phase selections, exact inventory/fatal/source roles, old-profile
exclusion, fixed inventory pin versus caller repinning, full descriptor matching,
pak1 binding, inventory name/ID/content failures, exact larger budget, failed F,
original-job closure, last-PAK recovery/absence and the persistent 128 KiB cap.
Fixture baseline IDs and non-PAK sizes remain synthetic; they are not reported
as the actual stock totals.

A separate bounded read of seven existing JSON files checked only the stock
metadata linkage in the original G plan/spec and its five stock receipts. It
read 918724 bytes including rechecks, no retail files, and recomputed 32 additions,
4695508096 supplemental bytes, 73 distinct IDs, 5148447113 declared hash-read
bytes and 107 managed paths. **This did not qualify Plan G, its source freshness
or a native Run.** G was prepared before the separate producer snapshot correction;
its old Core pin cannot establish that correction. New source/plan review and
an independently authorized Run remain separate coordinator decisions.
