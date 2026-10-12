# Native GSC consumption witness: prepared integration contract

`audit_gsc_consumption.py` binds the original `.gscbin` bytes to a dedicated
native decoder's final bytecode and symbol-stack cursors. It is a separate utility;
Creator, Finalizer, Recipient and the Beacon evidence gates are unchanged.

**Current status: source candidate only.** Nine wrapper tests pass with synthetic
framing and mocked native responses. The native executable has not been compiled
or executed. Neither Beacon nor any retail script has a complete-consumption
witness yet. The corrected Beacon offline record remains observed-only.

The separate tooling source is based on xensik/gsc-tool commit
`3300e430d1efef00e54c66a8bd416e18a2a9882a`, branch
`codex/iw7-strict-consumption-audit`, in the coordinator-approved independent
`IW7-Tools/gsc-tool-audit` checkout. Its `audit/README.md` records the source,
strict checks, prepared native tests and admission plan. No shared provider,
runtime input, game asset or original Beacon GSC is changed.

The native audit must read the original container from binary stdin, verify exact
container/zlib lengths, require the initial `OP_End`, respect each declared
function size including the final one, reject unbounded strings/seeks and unknown
instructions, and attest exact consumption of **both** buffers. No speculative
padding is accepted. Jump/switch destinations must resolve to an instruction
boundary inside their function. The emitted assembly bytes must belong to that same run.

The wrapper requires explicit executable, source revision, source digest and table
digest pins. It verifies input/buffer/assembly hashes, lengths, both cursor values
and contiguous per-function ranges. The executable is hashed before and after
execution. Its source/table claims are trusted only through a reviewed build and
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
