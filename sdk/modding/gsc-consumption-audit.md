# Native GSC consumption witness: prepared integration contract

`audit_gsc_consumption.py` binds the original `.gscbin` bytes to a dedicated
native decoder's final bytecode and symbol-stack cursors. It is a separate utility;
Creator, Finalizer, Recipient and the Beacon evidence gates are unchanged.

**Current status: native steps passed; overall build acceptance is still blocked.**
The 2026-10-12 v4 attempt compiled the auditor, passed reader CTest and all thirteen
native tests, then produced bound complete-consumption measurements for the two
retained Beacon inputs. The original job still had one unqualified descendant
after its two-second drain, so its supervisor correctly marked the attempt failed,
stopped that original job, confirmed zero active members and released the lease.
These real measurements do not convert the failed supervision into a successful
build or reopen Creator/Recipient gates. No retail script was audited.

The thirteen earlier wrapper tests remain synthetic/mock/pipe evidence, separate
from the new native results. See [v4 result](gsc-consumption-native-20261012.json)
and the [private source archive](../../tools-source/gsc-consumption-tool/README.md).

The separate tooling source is based on xensik/gsc-tool commit
`3300e430d1efef00e54c66a8bd416e18a2a9882a`, branch
`codex/iw7-strict-consumption-audit`, in the coordinator-approved independent
`IW7-Tools/gsc-tool-audit` checkout. Its `audit/README.md` records the source,
strict checks, prepared native tests and admission plan. No shared provider,
runtime input, game asset or original Beacon GSC is changed.

The preserved v4 source is `6f650cb9c981317b970dad0abae6846165f80166`; the local
executable SHA256 is `54f0ce337fda98acfeb75e54e538d4936f820d42f530589060f6ac65966d3398`.
Its header-order correction compiled successfully. The earlier v1 CIM failure and
v3 zlib-header failure remain in source history and immutable ignored run roots.
The text patch archive reconstructs the exact source tree, while its `git am`
commits can have different identities; it makes no binary reproducibility claim.

The variant consumed all 1,480 bytecode bytes and 1,808 stack bytes across eight
functions. Its 15,850-byte assembly matches the prior observed disassembly hash.
The original consumed all 1,455 bytecode bytes and 1,394 stack bytes across seven
functions; its assembly explicitly contains both utility `flag_exist`/`flag` far
calls. The variant had no observed far-call line. Both bound receipts still set
external-GSC dependency absence, full asset closure, runtime readiness and owner
acceptance false. Complete structural consumption is not a general import proof.

At the v4 checkpoint, the remaining build-lifecycle issue needed original-job descendant identity
evidence and a reviewed closure policy. No identity was captured for v4's residual
member, so it must not be retrospectively classified as harmless telemetry. Do
not lengthen the drain, kill by process name or label the existing run successful.
Any future native attempt requires a fresh reviewed Plan and coordinator GO.

The separately admitted v5 diagnostic then ran source
`f813f9758006e33857339c19ece48a642212ac5f` and repeated all functional passes.
Its original-job observer identified one residual `vctip.exe` from MSVC
14.44.35207, with image-file SHA256
`d591358c6aee4b673562ca3b3a15c250e612708394fe3b44a7a7eda2470570a5` and size 335,288
bytes. Creation time, kernel parent PID and original-job membership were captured;
the complete observation and file hash took 31 ms. The parent process's identity
was not captured, so no compiler ancestry or harmless-telemetry classification is
inferred from its PID. This v5 identity does not retroactively identify v4's member.

V5 preserved `Success=false`, stopped only the original job, confirmed zero active
members and released the lease. Its candidate executable is
`9cb1d946403e9e49812ed3db8bb59d7fefc0607078f65b963fc610eac04a564a`; it was rehashed
after closure with source, dependency, compiler and input pins unchanged. See the
[sanitized v5 checkpoint](gsc-residual-diagnostic-20261012.json). The next decision
concerned a reviewed closure contract with sufficient positive ownership and identity
evidence; the diagnostic itself did not add one or authorize another native attempt.

## V6: native audit and qualified original-job closure passed

The single explicitly authorized v6 attempt ran on 2026-10-12 from 07:34:52 to
07:35:50 UTC, using tool source `eabe74ab65d8ce2a943b54d24b15a60749a0cf2a`, SDK
revision `b85b6203a338834487ecc0ae9d69044bb6bd68d5` and Plan SHA256
`5db9aee8505b0ef36a253ac6efa8e94f945cf4a5534ee1550a479e6d1d42d9a8`. The source
tree `74143703049b4fbb9ba702d1ea74bc58be5607ac` belongs to the tool, not the SDK.
Fresh full 4 GiB RAM / 6 GiB commit admission used zero RAM reserve and 20% commit
reserve, an empty lease registry and no other builder. Main's identity was preserved.

All seven build/test/binder steps and their wrappers exited zero; CTest passed
1/1 and all 13 native test methods passed. The schema `/2` candidate receipt bound
the exact run, root, Plan, lease, source, configured compiler, executable, ordered
steps and 17 independently reread artifacts. Both input/assembly witnesses passed.
The executable SHA256 is `99f72711793cc51403da802336a8fca510cc3865fd7cec8e41e7c0ca902fad45`;
combined source SHA256 is `7c4517fed76c14bc4c4f95996cb8eed5b353f18ceeb1e6f17f41b6117fd180e6`.

Two real original-job captures at 07:35:50.2682020 and 07:35:50.4724413 UTC each
contained one matching pinned `vctip.exe` member, with the same PID, creation time,
full image path and kernel parent PID, positive original-job membership and no
query error. Its creation followed the root's creation. The file hash and size
matched the reviewed pin. Parent-process identity and compiler ancestry remain
unproven; the isolated identity predicate still grants no action or acceptance.

The complete collector held read guards through the final capture and original-job
Stop, then confirmed fresh root exit zero / active members zero. It read 2,546,462
guarded bytes. Guard disposal preceded the supervisor's final fresh check; this is
execution of the reviewed guard lifetime, not a separate runtime OS-lock probe.
The first root exit was observed at 57,141 ms, fresh post-Stop zero at 57,406 ms,
and the final check at 57,453 ms: **312 ms of the unchanged 2,000 ms drain**.
Global `Success`, `TreeClosed` and `LeaseReleased` are true. A fresh 07:36:56 UTC
inventory confirmed the registry empty, former run processes/builders absent and
Main unchanged. Source, dependency, compiler, provider, tool and input pins were
rehashed unchanged. No retry, game staging or Main/package promotion occurred.

The variant again consumed 1480/1480 bytecode and 1808/1808 stack bytes, with zero
observed far/pointer opcodes. The original consumed 1455/1455 and 1394/1394, with
two far calls and zero pointer opcodes. These are bounded assembly observations;
external dependency absence, full asset closure, runtime and owner gates remain
false. **v4 and v5 remain immutable global failures.** See the
[sanitized v6 checkpoint](gsc-qualified-closure-20261012.json) for separate native,
identity, guard, closure, lease and remaining-gate evidence.

The native audit must read the original container from binary stdin, verify exact
container/zlib lengths, require the initial `OP_End`, respect each declared
function size including the final one, reject unbounded strings/seeks and unknown
instructions, and attest exact consumption of **both** buffers. No speculative
padding is accepted. Jump/switch destinations must resolve to an instruction
boundary inside their function. The emitted assembly bytes must belong to that same run.

The wrapper requires explicit executable, source revision, source digest and table
digest pins. It verifies input/buffer/assembly hashes, lengths, both cursor values
and contiguous per-function ranges. The executable is hashed before and after
execution. Both output pipes share a limit enforced during reading, with timeout
and termination through the owned process handle; oversized, failed or truncated
results are refused. The native witness must have exactly the declared schema
fields, so added claims or unknown keys are refused. Its source/table claims are trusted only through a reviewed build and
the supplied executable pin. These are audit receipts, not signed attestations.

After native admission and successful tests, invoke it with:

```text
python -B sdk/modding/audit_gsc_consumption.py --tool REVIEWED_EXE --tool-sha256 REVIEWED_EXE_SHA256 --source-revision REVIEWED_TOOL_COMMIT --source-sha256 REVIEWED_SOURCE_DIGEST --tables-sha256 REVIEWED_TABLE_DIGEST --input ORIGINAL_GSCBIN --output FRESH_DIAGNOSTICS_DIRECTORY
```

Success produces the native witness and bound pins in `consumption.json`, plus
the exact emitted `disassembly.gscasm`. `complete_consumption_verified=true` is
only set after a real successful native response matches every required field.
The wrapper always keeps external-GSC dependency absence, complete asset closure,
runtime readiness and owner acceptance false. Import analysis and dependency
closure remain separate consumer responsibilities.

Before adapting existing gates, require real positive and negative controls,
review the exact tool source/head, complete the coordinator's private build and
publication workflow, and pin the resulting executable. Distinguish the specific
qualified v6 run above from historical failed runs and source/mock tests; this
auditor build result does not itself promote any consumer package or runtime gate.

## Encoded-reference source candidate, 2026-10-12

The archived source chain now includes `bfa2d4af` (reference contract), `805f076`
(reviewed literal-offset correction), and `42e6c403` (supervised reference recipe).
The original and corrected contracts and the `42e6c403` recipe received favorable
independent source review. The exact Plan and explicit GO remain required before
any native execution.
The existing v6 receipts and historical failed-run evidence are unchanged.

The independent reader visits all encoded instructions and operands under the
pinned IW7 profile, resolves local targets and numeric namespace/function IDs,
separates native builtins/assets, and blocks unknown or pointer targets with exact
positions. Source-only reads of the retained variant cover 570 instructions with
zero blockers; the original covers 560 and exposes utility `flag_exist` at
bytecode 212 / stack 318 and `flag` at 226 / 345. The checked absence is scoped to
encoded GSC references, not all engine/builtin/asset dependencies.

The separate native mode must still generate real reference witnesses. Plan `/2`
and receipt `/3` add an eighth required phase with all 153 opcode specimens,
four unresolved/dynamic controls and both Beacon inputs (159 planned invocations).
Consumption `/1`, CTest and the 13 existing native methods remain mandatory.
Closure requires the native/bound pairs, written pins/control summary and matching
old consumption evidence under the unchanged guard/deadline limits. The reader can
return `encoded_external_script_reference_absence=true` after exact native-to-byte
agreement; this result alone cannot promote native semantics, asset closure,
package readiness, runtime or owner acceptance.

The source tranche passed 367 PowerShell checks and 28 Python tests. No new native
build, Run, lease or Creator change has occurred. The archive reuses the retained
reconstruction and preserves the first twelve patches. The
[source checkpoint](gsc-reference-source-20261012.json) records the relevant hashes
without including binaries, machine paths or a fabricated native reference proof.

## V7: native references passed, global supervision failed

The single authorized `v7-final` execution used source `42e6c403` and SDK `7008cce6`
on 2026-10-12. All eight phases exited zero: CMake version/configuration/build,
CTest (1/1), the 13 existing native test methods, both consumption witnesses, and
the new reference phase (159 native invocations, all three methods passed without
failure or skip). The variant's native stream and independent reader agree on
570 instructions, complete 1480/1808 bytecode/stack consumption and encoded
external-reference absence. The original agrees on 560 instructions, 1455/1394
consumption and the two utility blockers. The linked consumption/ASM bytes and
all 27 recorded artifacts were rechecked unchanged without rerunning native code.

**V7 remains a global failure.** The closure collector rejected `Complete
lowercase SHA256 required` before granting completion/closure qualification.
The actual Plan is a `PSCustomObject`; the new dictionary-style Plan indexer
returned null, while the dynamic property returned the correct digest. The
existing mocks used an ordered hashtable and missed that type difference.
No fix had been applied at this failure checkpoint.

The owned failure cleanup stopped the original job, confirmed root exit zero and
Active=0, and released its lease. Fresh observation at 08:59:31 UTC found no lease,
builder or former run processes, with Main unchanged. The first member capture
showed one original-job `vctip.exe`; no second qualification capture or guarded
image identity was reached. This cleanup is not a successful qualified closure.
The 2-second drain, resource budgets and all unrelated readiness gates stayed
unchanged. No retry or game staging occurred. V4/V5 remain failures and V6 remains
its separately proven success.

See [the immutable V7 failure checkpoint](gsc-reference-v7-failure-20261012.json)
for separate phase results, witness hashes, flags and cleanup evidence. The next
step is a separate source correction with the real JSON-loaded Plan type and a
read-only collector diagnostic on retained artifacts, followed by a new reviewed
Plan. None of those steps can retroactively promote this failed Run.

## V7 collector correction and retained-content diagnostic

The failure checkpoint was committed first as `aedd53528ff624bbc2fd4ad41002d5de684441ee`.
The separate source correction is `03d3956d648b7aa4637fe1007f9d69ea463631e9`,
archived as patch sixteen. It replaces the three invalid dictionary-style Plan
accesses with dynamic properties. A regression round-trips the Plan through JSON,
asserts the actual `PSCustomObject` type and validates all 27 receipt artifacts.
The new regression failed before the fix; all 369 PowerShell checks pass afterward.

The corrected collector also passed a read-only content diagnostic using the
actual retained V7 Plan, receipt and artifacts: 28 guarded files including the
receipt, 1,900,800 bytes, all guards released and original evidence unchanged.
The 509 ms diagnostic duration is not a qualified drain measurement. It performed
no job observation, closure/deadline qualification, native execution or resource
lease acquisition. **V7's global failure remains authoritative.** Neither Creator
nor a consumer may promote these results without a successful new supervised Run.

The [correction checkpoint](gsc-reference-collector-correction-20261012.json)
records source, archive and diagnostic pins. The existing source reconstruction
matches all 35 changed blobs, the exact tree and physical table pins; prior patches
and native evidence remain unchanged. The next step is review of a fresh Plan
pinned to this correction and the completed SDK archive, followed only by an
explicit execution GO.
