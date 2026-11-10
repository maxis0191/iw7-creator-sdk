# Community mod SDK: first executable contract

This page is the contract: the files and commands, the manifest `iw7.community-mod/1`, the validation boundary
and the beacon example. The status paragraphs and validation records of 2026-10-12 that stood here are in
[archive/MODDING-PLATFORM-2026-10-12.md](archive/MODDING-PLATFORM-2026-10-12.md); they are history and do not
describe the present state. Nothing below has been re-qualified since that date.

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
