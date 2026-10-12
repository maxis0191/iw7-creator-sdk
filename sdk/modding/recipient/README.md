# Recipient evidence: pure verification and completion path

This directory is a source-only follow-up to Beacon finalization. `verify.py`
reads existing local files; it launches no process, copies no stock or retail
payload, and writes no candidate, receipt, ZIP or shared manifest. No current
Beacon source or finalizer gate is changed. Tests use invented bytes only.

The producer contract was coordinated with the H1 recipient runner at
`cb3d9ac8684a99c5e711c39b02912bfc5a98a084`, under
`tools-source/asset-bridge/recipient/`. Its two
`iw7.recipient-phase-result/1` receipts retain their existing meanings. This
consumer adds no replacement public receipt/package schema.

Producer `4867081fff69dcecf382a50b4a4208525b7a9690` additionally declares
optional `capture` metadata. The consumer accepts the exact five diagnostic
fields with strict types/bounds: raw pipe size 0, closed drain threads for a
successful phase, bounded byte counts, and `tree_closure_verified: false`.
These are producer declarations, not newly measured log or process facts; they
are not promoted into the analysis result. Older receipts without this object
remain supported. The separate `native-start.json` is only a locator: its observed
spawn time is not a verified process creation time. It cannot replace a phase
receipt, the original-job identity or outer closure/restoration evidence.

## Available analyses

```powershell
python -B sdk/modding/recipient/verify.py `
  --work <existing-recipient-work-directory> `
  --phase-receipt <existing-phase.json>
python -B -m unittest discover -s sdk/modding/tests -p test_recipient_evidence.py
```

Exit 0 / `phase_bytes_verified: true` means the phase declaration agrees with
the retained CSV and exported bytes. It does not verify the surrounding run,
producer authenticity, stock identity, live target, package or gameplay. Errors
return exit 1; usage errors return exit 2. No output file is created.

Importable standard-library functions:

| Function | What it establishes | What it does not establish |
| --- | --- | --- |
| `verify_phase(work, receipt_path)` | Exact agreed phase fields, tool declaration, successful exit, CSV digest and remeasured observation | Original job closure/restoration, stock, load order, map generation or current DB |
| `reference_manifest(raw)` | Exact four ordered `type,name,verified` rows | Any asset-content hash or transitive edge |
| `gscbin(raw, module)` | Actual module/NUL/three int32 lengths, exact payload extent, full serialized and component hashes, bounded exact zlib stack expansion | Disassembled imports, bytecode validity, non-default status or script behavior |
| `script_manifest(files, raw)` | One exact utility export row, contained fixed path, size/hash and parsed compiled container | Decompilation or graph closure |
| `streamed_image_header(raw, name)` | Pinned IW7 serialized header/name/layout, positive stream byte requirements including unused tails | GPU validity, full image semantics or current residency |
| `image_manifest(files, raw, name)` | Selected header plus every required stream, exact per-file hashes and sizes | Other images in the manifest, current DB binding or a composite SDK node hash |
| `material_dependencies(raw)` | Raw JSON hash, actual explicit technique-set/image names, presence of submaterials | Material sidecars, technique passes, shaders or transitive completeness |
| `audit_graph(roots, dependencies)` | Reachability, missing nodes and unknown edge inventories; returns true for a structurally closed graph | Content verification, a proven terminal boundary or permission to package |

`Files(root)` rejects unsafe/redirected paths and checks file identity around
bounded reads. Content hashes are computed from bytes, never asset names or CSV
reference rows. Default limits are 2 MiB per file and expanded script stack,
64 files and 16 MiB read per file-reader group; text CSVs/receipts have 64 KiB
limits. These are deliberately narrower **analysis** limits than the native
exporter's 64 MiB per script buffer. Oversize input is refused, not truncated or
silently considered verified. Future larger analysis needs a reviewed bound.
Filesystem checks are cooperative consistency guards, not a hostile-race sandbox.

## What the native script export really contains

Reviewed source is owner-fork ZoneTool
`fab935826c898806855376662a8a03317b3ad8f1`:

- `src/zonetool/zonetool/iw7/zonetool.cpp`, `check_enemy_references` around 1551
  and `dump_enemy_scripts` around 2051; SHA-256
  `f1c9fb861b81727dc7e3882f5116231e6dc0d1a0e6f5838953a62232171059bc`.
- `src/zonetool/zonetool/shared/assets/scriptfile.hpp`, `dump`;
  SHA-256 `5f6b30e5540563c41e8ce5d5d42d388f687e138ba7e5c2dbb30dc7eb720fc823`.

For `scripts/engine/utility`, native output is its 22 ASCII name bytes, NUL,
three signed little-endian int32 values (`compressedLen`, `len`, `bytecodeLen`),
then exactly the compressed buffer and bytecode. `len` is the expanded auxiliary
stack length, not an additional plaintext source buffer in the export. The whole
file is `35 + compressedLen + bytecodeLen` bytes. The separately reported
`payload_sha256_without_name` hashes the real three lengths and payload bytes,
matching the native catalog's representation; it never hashes only a name.

The native exporter indexes effective `ScriptFile::name` values, rejects a
requested name mapping to different pointers, and compares serialized bytes to
the loaded struct before hashing. That is stronger than a diagnostic string,
but it does not explicitly apply `DB_IsXAssetDefault` to the requested script.
The reference phase performs that check for its **four material/techset/image
requests only**. Do not transfer those four results to the utility script.

Successful zlib verification is recorded as a new analysis fact. The producer's
`decompressed: false` and `transitive_imports_verified: false` remain unchanged.
A string such as `scripts/common/flags` in the expanded stack is not an import
inventory: instruction decoding determines how stack fields are consumed.

## Image and material representation boundaries

The streamed-image parser follows the same pin's `utils/io/assetmanager.hpp`
(`674f3fd82ff519fa76d2105c05e09c7a950857a7c598ab019fbea3bab8a75b83`),
`iw7/structs.hpp`
(`adb62e481a533d27f97829e64d9038b13c5e9cd88e6b4aee8cac339b9492921a`),
and `iw7/assets/gfximage.cpp`
(`71ba077cca8727d7c79c61797463239c5b47e12d0f86774868737f71a7a003d1`).
`dump_single` is array tag 8, present byte 1, uint32 count 1, followed by the
0x70-byte x64 `GfxImage`; the separate name is string tag 6, present byte 1 and
NUL-terminated bytes. Stream descriptors start at struct offset 72; cumulative
pixel sizes occupy the low 26 bits of each descriptor word at offsets 76/84/92/100.
Every positive size delta needs its exact `_streamN.pixels` component. Holes,
descending sizes, missing/extra components, truncated headers and unsupported framing
are refused. The resident-image format is intentionally unsupported here.

These offsets are source-derived and tested with synthetic layouts; this task
has not exercised a real retail image or independent native layout fixture. The
header contains historical process pointer values. They are hashed as retained
bytes and are never dereferenced or called stable engine-content identities.

`material.cpp` at the same pin (SHA-256
`a2e42a0be8a53c77f1e86cd8242bdb682ed82323b78f79847934ffe252a6e081`)
exports `techniqueSet->name`, `textureTable[*].image` and possible submaterial
identifiers. It separately writes `.stateinfo`, `.statebits`, `.statebitsmap`,
and, when applicable, `.cbi`/`.cbt`. JSON alone is therefore not a complete
material representation. Submaterial identifiers without a measured resolver
remain unknown edges. A material's sidecars do not substitute for the technique
set itself, its `.technique` passes, vertex declarations or shader bytecode.

An image has multiple real files. The verifier returns their measured component
set and `single_asset_sha256: null`; it does not pretend the header digest covers
pixel streams. Before filling a common SDK image node, review a deterministic
content representation (for example, an explicitly framed binary bundle of all
real component bytes), independently read/hash that representation and keep its
definition in the proof. A hash of a component-name list is not a substitute.

## Concrete route to a complete recipient gate

1. **Bind run context.** Consume the reviewed outer
   `iw7.recipient-closure-run/1` state, not only phase JSON. Recheck tool/provider,
   request, stock binding/container and actual load-order hashes; require the
   exact recipient map, common source identity across both phases, original-job
   closure and confirmed restoration. Compare the outer `Phases[].Result` with
   the actual phase files and all nested observation hashes. Failed, stale,
   mixed-context or incomplete runs stay blocked. This binder is not implemented
   in the present primitive and must be reviewed against the final runner state.
2. **Decode real script dependencies.** Bind a disassembler run to the exact
   exported `.gscbin`, tool/source/token dictionary pins and output bytes. The
   locally read gsc-tool dependency is
   `3300e430d1efef00e54c66a8bd416e18a2a9882a`, not the older standalone-tool pin.
   IW7 uses little endian, `str4`, `tok4`, `offs9`. Its disassembler reads function
   extents and names from the expanded stack while decoding instructions from
   bytecode. Far calls and `OP_GetFarFunction` consume 32-bit file/function token
   IDs (or decoded strings), not a searchable plaintext import table. Require
   full instruction coverage and consumption of **both** buffers; the existing
   outer loop stops when either buffer ends, so a zero exit alone is insufficient.
   Preserve instruction offsets and resolved module/function edges. Unknown
   tokens, malformed opcodes, unaccounted tails and dynamic call targets must
   remain blockers until resolved or bounded by reviewed evidence. A source
   decompilation and roundtrip with ignored tails do not satisfy this gate.
3. **Close content sets.** Measure the material with its applicable sidecars,
   both images including every declared stream, and the technique set with all
   pass/shader/vertex-declaration requirements. Obtain matching non-default
   resolution/context evidence for newly discovered dependencies. Recurse to
   explicitly justified terminal content boundaries; never assume an empty
   dependency list because the current parser does not understand an asset.
4. **Build and validate the graph.** Populate edges only from those reviewed
   analyses. `None` means unknown, `[]` means a positively justified terminal.
   `audit_graph` already distinguishes them and can succeed on fully inventoried
   graphs, including legitimate script cycles. Structural success must then be
   combined with content-set integrity, current resolution, shared provenance
   and boundary evidence for every reachable node.
5. **Review the finalizer adapter.** Only after the representation and proof
   contract are agreed should a new supported adapter consume all four preceding
   results, fill actual recipient hashes/edges and permit `closure_complete`.
   Package compatibility, payload rechecks, runtime and owner acceptance remain
   separate checks. There is no proposed `allow-missing` flag or schema relaxation.

Source-only output from this task advances steps 1--4 with reusable parsers and
tests. Missing native observations and bytecode/techset analysis are explicit
remaining work, not a permanent hardcoded completion result.

## Possible later Beacon variant

The retained utility decompilation at
`1dd48a78e55ef9c99519fc5221a206168ce2e98a`, SHA-256
`007f026cb956a4c256977d60c2691cc554e0cc78a13dfd1694469acf707bbdf7`,
shows `flag_exist` (line 532) checking `level.flag` and its indexed member, and
`flag` (line 540) returning that member. A separately reviewed future Beacon
variant could perform those guarded reads locally and remove this module import.
It would need a new exact GSC hash, source validation and an admitted intro/spawn
behavior test. Historical source alone does not establish current engine parity.
BeaconV1, its live session, current template and hashes are unchanged by this work.

## Verification performed on 2026-10-12

Twenty-three asset-free tests cover the CLI's lack of writes, the agreed phase fields,
real byte hashes, malformed/truncated/oversize script envelopes, bounded zlib
expansion, false readiness claims, omitted/tampered image components, material
references, graph cycles/missing nodes/unknown edges, and path/reparse guards.
The producer's actual `check_output` loaded from commit `cb3d9ac` was also run on
the two tiny synthetic phase fixtures; both resulting observations were accepted
unchanged by this consumer. This verifies the producer/consumer interface only.
No retained retail export, new native execution, stock load, lease or network
operation was used to establish these results. The additional capture/locator
tests verify metadata compatibility without converting diagnostic declarations
into process identity or tree-closure proof.
