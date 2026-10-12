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
