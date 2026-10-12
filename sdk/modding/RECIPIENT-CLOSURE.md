# Beacon recipient closure: recovered bytes and missing observations

2026-10-12 read-only audit. No schema, package candidate, native code or runtime
was changed. All following native commands are **planned, not executed** by this
audit. The coordinator owns admission after the current engine/animation work.

## What the existing contract actually requires

`iw7.mod-package/1` distinguishes delivered client/server nodes from `recipient`
nodes. A recipient asset is a requirement on the installed retail game; it is
not automatically copied into the ZIP. `sha256` identifies an independently
inventoried representation, while only `files` payload hashes are measured by
the validator. This is documented in `docs/MOD-PACKAGES.md` and enforced in
`ops/Validate-ModPackage.py`. No defect justifies removing the recipient-hash gate.

For this beacon, Distribution explicitly uses actual ZoneTool serialized dump
bytes and separately delivered GSC bytes. A SHA of an asset name, reference-only
CSV row, native pointer, canonicalized JSON or diagnostic log must not replace
that representation hash. A successful direct DB lookup is resolution evidence,
not a hash of content. Both can be recorded without redistributing retail bytes.

## Targeted recovery, without another material dump

The retained `doom-negative-textures` stock root, `runtime/dt`, still contains
the exact material export referenced by `ops/model-lab/recipient.evidence.json`:

`dump/paris_enemy_doom_source/materials/mopw/character_park_clown_zombie_shoes.json`

Its 1,405 bytes freshly hash to
`687924c80afb088a285c5df4704475b0786310738687fc555db77a3974c7c8b6`.
The 2,188-byte closure CSV and 2,285-byte source-load log also match the retained
hashes. This is a historical serialized representation with fresh integrity
checking, not proof of today's client/server material resolution.

The JSON names the exact technique set and two images in
`recipient-material-requests.csv`. The same retained root contains the diffuse
image's 187-byte `.iw7Image` plus four pixel streams and their original manifest.
The [recovery record](recipient-recovery-2026-10-12.json) records fresh hashes;
none of these retail files was copied. An image header alone does not cover its
external pixel streams. No exact normal-image or full technique-set export was
found in the targeted source/image exports inspected; no absence elsewhere is
claimed. Per-material state/constant-buffer sidecars are not the technique set.

The historical `iw7-gsc-dump` utility source is 94,770 bytes at repository pin
`1dd48a78e55ef9c99519fc5221a206168ce2e98a`; SHA256
`007f026cb956a4c256977d60c2691cc554e0cc78a13dfd1694469acf707bbdf7`.
It is a decompilation, with no measured binding to today's retail ScriptFile.
It cannot fill the current recipient hash. It also contains cross-script calls
such as `scripts/common/flags::init_flags`; do not assume a complete transitive
closure merely from the two simple functions used by the beacon.

## Smallest available native observations

Use the already built ZoneTool candidate bound by the beacon FF execution:
source `fab935826c898806855376662a8a03317b3ad8f1`, EXE SHA256
`e7c956fd713f5d1b1b16cd55ef162aa487031430690ab1394ee60d3d02a13d04`.
Reuse the original shared Windows job, resource scheduler, bounded logs and
identity/restoration checks. These recipes are not standalone launch approval
and are not implemented by `Build-BeaconFF.ps1`, whose four verbs remain fixed.

1. With `recipient-material-requests.csv` staged as `recipient-material.csv`:

   ```text
   zonetool.exe -headless -unbuffered-io -strict-content-sources -enemy-reference-check cp_zmb recipient-material.csv sdk_beacon_recipient_a
   ```

   Require exactly four `type,name,verified` rows, exit 0, no missing/default rows
   and the exact requested names. The implementation uses direct registered
   entries and `DB_IsXAssetDefault`, with no default creation, unique type/name
   requests and CREATE_NEW output/readback. It does not serialize assets or
   verify their internal graph, pixel residency or gameplay. It observes the
   effective registered entry; it does not report its owning zone or detect all
   alternate-zone overrides. Keep the exact source-zone/load-order provenance.
   Its `techset` label
   is also present in the retained stock's working zone-source recipes.

2. With `recipient-script-requests.txt` staged unchanged as `recipient-scripts.txt`:

   ```text
   zonetool.exe -headless -unbuffered-io -strict-content-sources -enemy-script-dump cp_zmb recipient-scripts.txt paris_enemy_cp_zmb_sdk_beacon_recipient_scripts
   ```

   The request is `scripts/engine/utility`, **without `.gsc`**. Existing code
   indexes `ScriptFile::name` because DB keys can be numeric; ambiguous same-name
   entries pointing to different ScriptFiles are rejected. Require one manifest
   row with status `dumped`, the exact module and `.gscbin` path. Native code
   compares the emitted name/NUL/three lengths/compressed buffer/bytecode with
   the actual loaded ScriptFile, then hashes those exact bytes. Rehash that file
   independently. A source decompiler hash cannot stand in for this export.

Both commands call `load_enemy_source_zones(cp_zmb)`: up to two shared shader
zones, then available techsets/base/patch zones for code_post_gfx, global, common,
global_mp, global_cp, common_mp, common_cp and cp_zmb. This is a real, heavy
recipient-map load despite tiny output requests. The beacon bootstrap's 72-file
inventory alone does not establish all these inputs. Reuse a suitable existing
stock; no game clone or full-map export. Admission must cover the complete load
(retain the established 8 GiB RAM/11 GiB commit estimate unless evidence requires
more). Source-only tests do not measure its actual peak.

The old script exporter permits up to 64 MiB per buffer. A future strict 2 MiB
export ceiling therefore needs a pre-write bound on its three lengths; an outer
filesystem polling threshold is not a hard bound. This audit's new source/report
files stay below 2 MiB and authorize no export. Do not quietly reuse a larger
native limit under a smaller approved budget.

## Provenance and remaining gates

For the future observed run retain the exact tool/artifact/job hashes, requested
list hashes, actual loaded zone order and retail-container inventory hashes,
non-default resolution results, serialized bytes/lengths/hashes, captured
ScriptFile-name collision results and original job closure/restoration. Correlate
the exact game/native build, map generation and FF hash separately for runtime
evidence. Existing client model diagnostics can name material/techset/images;
they do not hash them, and their sampled shader pass is not full closure proof.

Inspect the compiled utility's imports using the existing GSC tool and keep
unmeasured dependencies explicit. Check the material's technique/image
dependencies against the recipient, without adding their retail files to the
delivered payload. A terminal recipient boundary can be used only with documented
evidence for that boundary; this audit does not silently declare it complete.

Current state remains `closure=incomplete`, package refused, runtime/owner
acceptance separate. The material snapshot can now be referenced honestly;
utility's current compiled representation and recipient resolution/transitive
evidence are still missing. No schema relaxation or invented successful status
was required to reach this narrower, executable next step.
