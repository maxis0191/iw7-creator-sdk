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

The remaining build-lifecycle issue needs original-job descendant identity
evidence and a reviewed closure policy. No identity was captured for v4's residual
member, so it must not be retrospectively classified as harmless telemetry. Do
not lengthen the drain, kill by process name or label the existing run successful.
Any future native attempt requires a fresh reviewed Plan and coordinator GO.

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
publication workflow, and pin the resulting executable. No native success or
successful build should be inferred from this source-only delivery.
