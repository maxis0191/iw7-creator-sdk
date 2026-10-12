# Community mod SDK: first executable contract

Current checkpoint, 2026-10-12: PR148 is merged as `178708b` under the recorded
owner CI-admission exception; CI did not pass. The SDK now has real Beacon FF
build/readback and Creator finalization evidence, plus protected run 5 Use/HUD and
controlled base-client restart/rejoin with verified Aurora cdata and restoration.
Run 5 retains two unresolved retail errors in issue 150; it is a targeted witness,
not global engine integrity, human acceptance or actual second-player/WAN proof.
Material C adds offline geometry/pixel-byte verification, not rendered material.

The follow-up source tranche at `deb4169` recovers an original two-bone rig and
guarded chain plan, prepares references-only Recipient B, adds recipient evidence
analysis, a separate local-flag Beacon variant, a strict-consumption binder and
passive ticket telemetry in draft PR151. Source Test-Platform at `deb4169` passes
425 cases (422 pass, three skips) and four actual GSC syntax parses. B is authorized
once; a Fatal Error window is observed after `global_mp`, with final result pending.
Binder output/key fixes `960bd55`/`e8ca4f6` pass source/transport review, while the
native reader corrections/review/build remain pending. Full compiled dependency absence
is not established by observed disassembly. The rig has not been played, no real
H1 donor is imported, and recipient/package closure remains open. This is beta
progress toward creative freedom, not BO3 equivalence or weapon/AI qualification.
[Current evidence](STATE.md), [runtime limits](MODDING-ENGINE-RE.md).

The original source-only SDK checkpoint was based on `21b91e3`; its contract and
preparation behavior below remain applicable to fresh inputs. It must not be read
as the current validation status of the whole platform.

## Files and commands

- [manifest.py](../sdk/modding/manifest.py): Python standard-library validator,
  CLI and importable API, with no installation/network/game side effects.
- [manifest.schema.json](../sdk/modding/manifest.schema.json): strict envelope
  shape. The embedded `package` is additionally validated by the existing
  [transport validator](../ops/Validate-ModPackage.py); JSON Schema alone is
  deliberately insufficient to certify that object or semantic cross-checks.
- [capabilities.json](../sdk/modding/capabilities.json): reviewed IDs, sides,
  evidence level and limits. This is an evidence registry, not an engine query.
- [beacon example](../sdk/modding/examples/beacon/manifest.json),
  [original GSC](../sdk/modding/examples/beacon/sdk_beacon.gsc) and
  [zone recipe](../sdk/modding/examples/beacon/zone.csv).
- [prepare_beacon.py](../sdk/modding/prepare_beacon.py): composes a fresh tiny
  source staging directory by reusing the existing measured original-model gate.

```powershell
python -B sdk/modding/manifest.py sdk/modding/examples/beacon/manifest.json
python -B -m unittest discover -s sdk/modding/tests -v
# After the parent permits preparation; reuse the measured original writer:
python -B sdk/modding/prepare_beacon.py --writer-run <existing-writer-run> --output <fresh-output>
```

The prepared directory contains an opt-in GSC, `manifest.json`, original XMB/XSB,
NCS table, the existing recipient-material ignore recipe and `sdk_beacon.csv`.
For each freshly prepared directory, only the server source hash is initially
filled. The admitted [Beacon builder](../sdk/modding/Build-BeaconFF.ps1) and
[Creator](../sdk/modding/CREATOR.md) supply measured FF/inventory receipts; the
already completed Beacon experiments do not fill facts for an arbitrary new build.
Rendering and acceptance remain separately gated, and unresolved recipient
dependencies still prevent distribution. The historical model-only wrapper is
not a substitute for the now-reviewed named Beacon route.

Preparation requires the existing original writer's exact source pin,
24 vertices/12 triangles/one bone/LOD, measured material reference, LOD distance
1000000, shadow sentinel6, collision sentinel255, bounded payload sizes and
matching hashes. It does not accept arbitrary H1 data disguised as that witness,
build a FF, authenticate producer evidence or re-run a native reader. On partial
failure it leaves the new output for diagnosis; existing outputs are refused.

## Contract `iw7.community-mod/1`

One manifest contains one `package` object of existing type `iw7.mod-package/1`.
ID/version, maps, files, size/SHA256, asset closure and evidence exist **only there**.
The envelope adds these fields:

| Field | Meaning / enforced limit |
| --- | --- |
| `namespace` | Exactly `package.id`; stable namespace across updates. |
| `requires.engine/client/server` | Versioned IDs from the reviewed catalogue, explicitly assigned to their execution side. Unknown/wrong-side IDs fail. Asset kinds imply minimum capabilities. |
| `dependencies` | Exact `{id, version}` requirements; no ranges, self or duplicate requirements. The distribution graph checker resolves installed content and cycles. |
| `conflicts` | `{id, reason}` applies to every version; self, duplicate and required conflicts fail. Distribution checks both directions. |
| `lifecycle` | Map-load activation, map-unload deactivation, `hot_reload:false`; explicit entrypoints and cleanup obligations. |
| `compatibility` | IW7/CP only in v1, exact network protocol (null only during planning), `exact-content` client match and `server-only` or `exclusive-fs-game`. |

Server entrypoint is `custom_scripts/cp/<id>.gsc::init`, bound to a standalone
`iw7-mod/custom_scripts/cp/<id>.gsc` payload and matching ScriptFile graph node.
Client entrypoint is `ui_scripts/<id>/__init__.lua::module`, bound to a client
LuaFile node and the separately gated fastfile loader capability. Entry paths
cannot traverse roots or invent arbitrary executable hooks. The manifest is not
executed by the current engine: these refer to its actual loaders. `namespace`
is a collision convention, not VM isolation or a security sandbox.

Cleanup declares owned entities, HUD, threads and player state as appropriate.
Authors must implement and test it on disconnect, native game end and new map;
the validator cannot infer source behavior. Hot reload, dynamic native DLL
loading, multiple simultaneous `fs_game` packages, a stable native plugin ABI,
custom maps and new MP gametypes are deliberately not qualified by v1. Existing
transport usermap research remains available separately. These are explicit
next capabilities to build, not a claim that the engine can never support them.

Imported assets use existing graph kinds (`xmodel`, `material`, `image`, `anim`,
`weapon`, `bt`, `asm`, etc.) and edges. H1/material/animation milestones add
catalogued capabilities and measured closure, without requiring a new schema.
`other` retains typed logical IDs for XModelSurfs/NCS/RawFile in the legacy
transport graph. A declaration is not a scanner for hidden asset dependencies.

## Validation boundary and distribution interface

`validate(data, root=None, stage="plan", target="stock", client_source=None,
server_source=None)` preserves the transport API. `load_manifest(path)` rejects
duplicates, nonfinite JSON, malformed input and documents over1MiB. `plan` permits
explicit null payload facts and returns `ready:false`. `package` verifies real
payload bytes/paths/hashes and completed closure declarations; blocked capabilities
cannot become packages. `delivery` adds the existing declared technical evidence
gate. Runtime readiness and owner acceptance always remain false in this API.
Historical evidence levels describe the cited experiment, not this new package.

`ready:true` means static community/transport integrity only. Actual target
capabilities, source/protocol compatibility, exact installed dependency versions,
conflicts and active asset/path/namespace collisions require the distribution
preflight. Native executable provenance remains an independently measured gate;
supplying a commit argument does not measure a running binary. A plan or synthetic
test is never eligible for real publication merely because its JSON is valid.

The distribution owner consumes `.package.files`, not a second file manifest.
Client FF must also be present on the dedicated for load/hash; server GSC never
belongs in FastDL. Current mod transport allows `mod.ff`, optional `mod.sabl` and
`mod.sabs`; neither PAK nor EXE/DLL rides this route. Engine CRC32 and SDK SHA256
serve different checks. Native-client changes require a separate compatible
distribution path. See [existing transport contract](MOD-PACKAGES.md) and the
distribution owner's integration documentation.

## Beacon behavior and next decisive experiment

The GSC is outside deployed source and defaults off. It additionally requires
dedicated, `sdk_beacon_enable=1`, Spaceland and exactly `mods/sdk_beacon`. After the
stock intro, it places one original model in front of the first playable player.
Native Use is accepted server-side only for a live nearby player, capped to one
activation per750ms and9999 total. Each activation rotates the shared model and
updates private `You`/shared `Team` counters. No recurring unchanged HUD text is
sent. Late joins see current Team and zero personal uses; respawns retain their
connection state; reconnection gets fresh personal state. Disconnect/game end
cleanup owns the HUD/model/threads. Original assets share probe names with the
historical model pack, so that conflict is explicit. Runtime behavior is untested.

After the admin/network gates and parent admission:

1. Reuse the retained measured writer/source and existing ZoneTool. Build only
   the tiny beacon FF; inventory exactly custom model/surface/NCS/RawFile plus
   recipient material reference, then independently read back geometry. No retail
   material payload or new stock snapshot. Record newly measured hashes.
2. Use one retained dedicated + protected base client on a separate port. Bind
   real FF to server/client, cold-cache join, inspect actual model/material,
   trigger native Use, observe one increment and rotation, disconnect/rejoin,
   then map cleanup. Source parse is not VM linkage or pixels.
3. Add a second independently identified receiver only under the parent's full
   two-client budget. Prove A/B observe the same rotation/Team value while their
   own counters differ; hold Use, reconnect B, seed old cache/update, reject
   incompatible protocol/source and restore all modified files. Network logs
   alone do not prove both rendered clients. WAN/public hosting remains separate.
4. Replace original mesh with the H1 bridge output and resident material using
   the concrete patches in [capability roadmap](MODDING-CAPABILITIES.md). Re-run
   the same interaction/join witness; then two-bone motion/notetrack. This makes
   importer changes usable in a real content loop before full character/weapon AI.

Current preparation ceiling:100MiB per chat; this source SDK is under100KiB.
No lease, native compile, game, extraction or real asset preparation ran here.
Future proposed source/pack staging cap:32MiB per beacon variant, bounded logs/
frames128MiB per case, all within the parent's shared10GiB future ceiling.
Measured original FF was1040B; that is not an estimate for arbitrary H1 imports.
Existing model FF wrapper estimates8GiB RAM/11GiB commit for extraction and stall
diagnosis; a full-quality client plus dedicated is16GiB/16GiB. A reduced two-client
functional group is20GiB/20GiB, full quality28GiB/28GiB, subject to current actual
availability and independent20% commit headroom. Never lower admission to fit.

## Validation and integration record

2026-10-12:18 standard-library tests (including300 bounded malformed mutations)
pass, including malformed/duplicate keys,
wrong capability side, undeclared asset requirements, lifecycle/path conflicts,
unknown protocol, unsafe transport, complete-package hash tamper, blocked import
packaging and bounded original-writer staging/refusal. The GSC Tool1.5.1 parser
passes the beacon. Existing transport regression suite:25 pass, one host symlink
case skipped. Synthetic fixture bytes are labelled and do not prove FF or
XMB validity. No native compilation, runtime link or gameplay was executed.

Only local source is prepared in this tranche. Parent integration must include
the SDK tests in appropriate source checks, review the final combined diff and
complete the authorized private PR/exact-head CI/merge workflow. Shared STATE,
BUGS, CHANGELOG, VALIDATION and PLAN updates belong to that integration owner to
avoid cross-chat edits. Main27016, owner client, banks/configs are unchanged.

The agent observer can bind actual Use to `level.sdk_beacon.model` (entity number)
and its `sdk_beacon_total`, updated in the accepted trigger handler together with
`level.sdk_beacon.total` and `player.sdk_beacon.uses`. Ready/activation markers
include the entity number. This is source preparation for the observer; logs alone
do not prove remote rendering. The enclosing harness must supply session nonce,
map generation, exact process identity and fresh safety checks. The model's
`sdk_beacon_instance` is its creation game time within that map generation.
`player notify("sdk_beacon_used", model, total, personalUses)` occurs only after
an accepted trigger updates rotation and HUD. The external fixture can listen
without coupling production source to `paris_test_*` native methods.
`player.sdk_beacon.rendered_total/rendered_uses` records settext intent only;
there is no Lua HUD or client pixel acknowledgment in this GSC example.

## Actual original-beacon preparation, 2026-10-12

After explicit parent authorization for tiny asset preparation, `prepare_beacon.py`
ran against the retained `modular-agent-platform` writer run
`runtime/model-lod1m-source-20261007`. No new writer was needed. Rehashed writer,
source/header/geometry, original XMB/XSB and historical visible FF match their
retained provenance. The retained FF reader's inputs and stdout JSON also match
its evidence. This is fresh integrity checking of historical proof, not a new
native reader execution or game acceptance.

The ignored SDK worktree output is `runtime/beacon-v1-source-20261012`:
10 prepared files totaling14,427B, plus4,752B local receipt = **19,179B** new data.
No executable, stock or retail material bytes were copied. The two original
geometry inputs are978B XMB (`F4160133AB4D19DFD1868C4DF8A935505466BDEBCFBEEE5898DFC535E92CFB29`)
and1231B XSB (`3D55171CB581DFA2EA249BEA1DE1A1F939F6AAEBBC8995E291C005540E388F27`).
The4802B GSC is unchanged at
`8BA85B3F5B3014D0C4D02B0E71F49BF617959B486502E4C63243B065ABC2A0B6`
and passes the real parser. Prepared manifest validates as a plan only.

`source-receipt.local.json` hashes every prepared file and records writer
provenance, checked reader inputs, expected inventory and policy baseline. Its
SHA256 is `B8229D50751FA990A925B4CB3C3E2C8110A373D645764D0580959D55D78277AA`.
Use `-buildzone sdk_beacon` and expect `rawfile,sdk_beacon`; the retained
`model-ff-plan.json` is original-model staging provenance, not the new build name.
Do not relabel the old1040B model FF as the unbuilt beacon FF. All binary inputs
and raw local evidence remain ignored and outside commits.

Future runtime follows privacy baseline `24d5c4f`: random nonempty password,
`sv_lanOnly=1` in final configuration and launch, loopback by default, reviewed
native master-heartbeat suppression and fresh privacy telemetry before client
join. The parent alone coordinates the next admitted build/test. This preparation
acquired no lease and ran no native executable, ZoneTool, game or network service.
Material variant2 remains a separate measured-model/closure preparation.

The subsequent [bounded FF runbook](../sdk/modding/BEACON-FF.md) supplies a
default-plan-only SDK adapter for the actual `sdk_beacon` name. It reuses shared
transaction/admission/NTFS helpers and the H1 owner's final job implementation.
The real metadata plan passes without native loading; Run remains dependent on
the new macro-qualified ZoneTool receipt, final job source hash and parent GO.

## Native beacon FF checkpoint, 2026-10-12

Those prerequisites were subsequently met. The first admitted native execution
completed build, exact five-asset verification, dump and geometry readback with
exit 0 and zero job members in all four phases. The new FF is 1,048 bytes, SHA256
`76ed0701dc1480c501604db04999f300394c65877aa24a70dfe7afc2cd662d4a`.
The [execution record](../sdk/modding/beacon-ff-validation-2026-10-12.json)
binds the tool/source/state hashes and validation limits. All temporary input
entries were removed, stock preservation checks passed and the complete 8/11 GiB
reservation was released. No game was launched. This establishes FF serialization
and original-model readback, not rendering, interaction, recipient material
binding, H1 donor import or map support. Ready and owner acceptance remain false.

The [recipient closure audit](../sdk/modding/RECIPIENT-CLOSURE.md) recovers and
freshly hashes the existing retail material snapshot and diffuse-image export,
without copying their bytes or changing the schema. It supplies exact existing
ZoneTool requests for the missing recipient checks and compiled utility export.
Historical dump integrity, current DB resolution and transitive dependency proof
remain separate; the package closure is still incomplete.
