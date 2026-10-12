# Beacon variant with local intro flag guards

This separate original source variant replaces Beacon's two utility calls with
a local `intro_flag_ready()` helper. It keeps the polling interval, frozen-control
check and existing gameplay/cleanup logic. Its enable dvar, fs_game, state fields
and event name use `sdk_beacon_self_contained`, keeping the current Beacon source
unchanged. It is not supported by Creator's existing BeaconV1 adapter or finalizer.
No package manifest is supplied and no current runtime input is replaced.

The retained folder name “self-contained” describes the source-level replacement
of the utility calls; complete compiled GSC dependency absence is **not yet
proved**. The model still uses `paris_model_probe` and its NCS, with recipient
material, technique-set and image dependencies. This variant and the original
must not be loaded together: their asset names still collide even though their
script state is distinct.

## Inspected reference and undefined semantics

The local historical reference is `mjkzy/iw7-gsc-dump`, commit
`1dd48a78e55ef9c99519fc5221a206168ce2e98a`, file
`decompiled/scripts/engine/utility.gsc` (94,770 bytes, SHA256
`007f026cb956a4c256977d60c2691cc554e0cc78a13dfd1694469acf707bbdf7`).
The checkout has no local change to this file. This is a decompiled reference,
not a measured binding to the currently loaded retail ScriptFile.

At lines 532–538, `flag_exist` first checks whether `level.flag` is defined;
only then does it test the requested array entry. At lines 540–543, `flag` simply
returns that entry, with no guard. The original Beacon OR expression evaluates
the guarded existence test before calling the raw getter. The variant preserves
that order in one local function:

| Observed flag state | Local result and wait behavior |
| --- | --- |
| `level.flag` undefined | Return 0; never index it; keep waiting |
| Array exists but the intro entry is undefined | Return 0; keep waiting |
| Intro entry is defined and false/0 | Return its raw value; keep waiting |
| Intro entry is defined and true/nonzero | Return its raw value; continue only when controls are not frozen |

The helper does not create an array, initialize/set/clear a flag, send a notify or
yield. It preserves the raw value instead of inventing a default success value.
The 0.1-second wait remains outside it. As in the inspected retail code, this
assumes that a defined `level.flag` is a valid engine flag array; no new behavior
is claimed for malformed types. Missing flags can keep waiting indefinitely until
disconnect or game end, exactly as the original guarded polling intends.

## Actual offline compilation evidence

The existing pinned gsc-tool **1.5.1.359**, executable SHA256
`1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb`, parsed,
compiled the variant and returned a successful disassembly result. The real `.gscbin`
is 1,992 bytes, SHA256
`db486793b92e7e3c0a30c70b565fb432a4940e172a3f97da7e9db377f0e46d42`.
The 15,850-byte emitted disassembly shows 570 instructions, eight defined functions
and eight script calls; all observed script calls target local definitions. No
far-call/far-function-reference or dynamic pointer opcode was observed. Engine
builtin calls remain necessary and are not external GSC module imports.

The binary container lengths and compressed symbol stack were independently
checked. A literal string scan alone is **insufficient**: compiling the unchanged
original as a negative control yields two `OP_ScriptFarFunctionCall` instructions
to `scripts/engine/utility`, although its symbol stack contains no literal module
name (the retail namespace is encoded as a token). This negative control proves
that the audit detects the external calls emitted in that disassembly.

The retained disassembler loops while **both** bytecode and symbol-stack buffers
have data. A successful exit and syntactically closed assembly can therefore
leave a suffix of either buffer unread. Neither cursor was attested in the actual
run. Container framing and full zlib decompression do not establish disassembler
consumption. The audit reports **zero observed external calls**, while full
bytecode consumption, full stack consumption and complete external-GSC dependency
absence remain unverified. The earlier complete-absence claim is withdrawn;
the source and recorded compilation artifacts are unchanged.

The [sanitized record](validation-2026-10-12.json) retains exact source/compiler/
binary/disassembly hashes and the control result, with the corrected interpretation
in schema version 2. Generated binaries and logs remain ignored local diagnostics,
not package payloads. No retail dump, SDK copy,
game, ZoneTool process or resource reservation was needed.

`verify.py` reproduces the bounded, observed-only offline audit with the existing
compiler and already available reference file, writing only to a fresh output directory:

```text
python -B sdk/modding/examples/beacon-self-contained/verify.py --compiler EXISTING_GSC_TOOL --retail-reference EXISTING_UTILITY_GSC --output FRESH_IGNORED_DIRECTORY
python -B -m unittest discover -s sdk/modding/tests -p test_beacon_self_contained.py -v
```

The six source/audit tests pass. One executes the actual helper body and waiting
expression as JavaScript-compatible snippets in a host model for 70 combinations
of undefined/false/nonzero flags and frozen-control values. Getter counters prove
that the guards prevent premature reads; frozen objects reject writes. This is
not IW7 VM execution. The other cases check external/dynamic calls, missing local
definitions, container boundaries and preservation of the original template.
A regression case also supplies closed local assembly beside framing fixtures
with possible suffixes in either buffer: none can promote dependency absence or
full disassembler consumption to verified. These fixtures are not IW7 bytecode.

## Future integration, without changing current gates

1. Review a separately named adapter and manifest for `sdk_beacon_self_contained`.
   Create new source receipts, zone/FF recipes, rawfile identity and output roots;
   retain explicit collisions with the original model/NCS assets. Do not swap this
   GSC into BeaconV1, its completed builds or the current runtime experiment.
2. Build and measure the new FF/GSC candidate with a source-bound receipt. Extend
   a separate finalization path to accept this exact variant and require its own
   offline compilation evidence plus tool-level attestation that both bytecode
   and stack buffers were fully consumed before accepting a complete import audit.
   The existing finalizer's exact-template and utility gates remain unchanged;
   this folder supplies no bypass.
3. Close the material, technique-set and image dependencies with independent
   recipient evidence. Removal of this variant's proposed utility dependency
   remains conditional on a complete compiled import audit. It cannot complete
   asset closure or qualify recipient availability, client compatibility,
   distribution or a ZIP.
4. Under separate coordinator approval, test the variant on a protected private
   dedicated: missing/false intro flag, frozen controls, first usable spawn,
   activation/HUD updates, disconnect/rejoin and map cleanup. Use the new opt-in
   dvar and fs_game. Offline success is not gameplay or owner acceptance.
