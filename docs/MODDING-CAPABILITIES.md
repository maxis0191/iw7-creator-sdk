# Creative capabilities: proof, gaps and implementation steps

The initial 2026-10-12 map used reviewed project `21b91e3` and the program's single
prior official-source review. That historical source/offline snapshot is distinct
from the later [SelfContained Use/rejoin Plan B checkpoint](SELF-CONTAINED-BEACON-RUNTIME.md)
and [BO3 catalogue J observation](../tools-source/asset-bridge/t7-bridge/catalogue-runtime-j-20261012.json).
The owner now prioritizes BO3/T7 asset work and skips H1 import. Retained H1,
image and animation notes below are historical boundaries, not newly revalidated
capabilities or instructions to resume those experiments. This document update
performs no upstream check or runtime test.
The desired BO3-like freedom remains a target: easy original/BO3 assets, custom HUD,
gameplay, weapons/enemies/maps, multiplayer distribution and public dedicateds.
A server GSC module catalogue alone does not deliver that target.

| Creative operation | Strongest retained witness | Missing proof / next implementation |
| --- | --- | --- |
| Server gameplay, private HUD | [SelfContained Plan B](../sdk/modding/self-contained-use-rejoin-b-20261012.json): fresh source compile/load/init, two real protected Use events and visible HudElem counters | Two known OP_CastFieldObject errors remain; runtime integrity and owner acceptance are false. Independent two-player/WAN proof and shared VM/canonical-string/reliable-command budgets remain. No arbitrary sandboxed plugins. |
| Original rigid geometry | [1040B model witness](deployments/2026-10-07-model-visible.json), plus five usable Plan B frames showing the original 24-vertex/12-triangle cube | Observed shape/HUD only; one rejoin frame is nearly black. Texture/UV/normal/lighting conformity, donor conversion and animated weights remain distinct. |
| Beacon FF serialization and interaction | [1048B offline FF](../sdk/modding/beacon-ff-validation-2026-10-12.json) and later [Plan B runtime](SELF-CONTAINED-BEACON-RUNTIME.md): Use/HUD, same server entity/team state and reset personal state across controlled client restart | Recipient shoes-material appearance and overall pixels remain unqualified. This is one sequential client, not independent multiplayer or WAN; package readiness remains false. |
| Client Lua/LUI in FF | [HUD delivery](deployments/2026-10-07-hud-delivery.json): visible Lua text, cold cache, corrected seeded update | Native loader/version required; per-frame gameplay data bridge, complex menus, independent two-client/WAN tests remain. GSC HudElem is not LUI. |
| BO3/T7 asset import; retained H1 history | [Closed E checkpoint](../tools-source/asset-bridge/t7-bridge/CATALOGUE-TWENTY-2026-10-12.md#subsequent-e-attempt-next-localized-zone-named): 22 bootstraps, complete correlated diagnostic naming en_mp_freerun_04; normal closure/host exit one and independent absence confirmed | E remains Failed/NoCatalogue. Initialization-complete, asset export and engine compatibility remain unproved; the exact 1536-byte singleton/F are preparation only. H1 import is skipped; its converter notes remain historical. |
| Original resident image/material | ZoneTool reader supports resident DDS/TGA; source fix prepared by surfaces owner | Material resolution currently depends on zone-name prefix/early DB lookup. Prove generic-name FF and resident images without PAK before exposing easy imports. |
| Skeletal animation | Animation owner's bounded H1/IW7 XAB envelope/bone/notetrack preflight | Compressed tracks not decoded; no imported motion. Two-bone original keyed clip, native writer/readback, two rendered poses and notetrack next. |
| New weapons | Weapon JSON/reference paths exist in pinned ZoneTool | View/world model, hands/rig, fire/reload/PAP, sounds/FX, notetracks and peer replication. No playable custom weapon witnessed. |
| New enemies/AI | Retail enemy-port experiments, GSC/callback/BT/ASM research | Imported model does not supply behavior; callback registration, animclass/ATR, movement/attack/death/FX/audio and late join require complete closure. |
| More active actors | Known native allocation/serialization/client audit | Previous64 candidate crashed;48 requires coherent engine+client patch, not a dvar or static-renderer list expansion. |
| Custom maps/gametypes | Later pinned downloader has usermap allowlist | No complete map compiler/collision/nav/lighting/spawn/stock gameplay or playable new-map proof. Not qualified in community v1. |
| Community multiplayer | Small local FF download/cache-update proof; Plan B retains the exact cache and server state across controlled client restart | One sequential client does not prove two independent players or WAN/public join. Content/version/source checks, joint update/rollback and one fs_game remain required; no EXE/DLL auto-delivery. |
| Independent mod composition | Exact dependencies/conflicts and transport graph validation | No native multi-mod linker/isolated namespace/ABI. One asset-bearing fs_game; compose only through a reviewed build with joint closure and tests. |

The machine-readable [catalogue](../sdk/modding/capabilities.json) keeps blocked
features named so authors can plan them. It refuses their package stage until a
reviewed capability change records appropriate proof. Adding a JSON flag alone
cannot qualify a native feature. Evidence references are claims to audit, not
authenticated attestations. Runtime/owner acceptance remains separate.

Plan B's HUD displays personal/team `0/0 -> 1/1`, then `0/1 -> 1/2` after
controlled client restart. The cube uses the recipient shoes material; its
normals writer remains an H1 encoding candidate. Neither the dark faces nor the
weapon's apparent green laser prove texture or normal correctness. Issue150's
two known errors remain open despite successful targeted interaction.

The separately reviewed [FLAC build C](../tools-source/asset-bridge/surfaces/sound/native-checksum/FLAC-BUILD-C.md)
qualifies compilation and the bounded C++ probe. The subsequent actual
[DumpOnly A checkpoint](../tools-source/asset-bridge/surfaces/sound/dump-only-checkpoint-2026-10-12.json)
proves corrected 4096/4096 block metadata and unchanged seek/frame bytes on the
preserved F banks. [The subsequent strict codec run](../tools-source/asset-bridge/surfaces/sound/dump-only-codec-checkpoint-2026-10-12.json)
recovers the exact original PCM and full WAV. Native alias lookup and audible
playback remain unproved. The original F decoder failure is retained unchanged.

## Retained H1/model converter correction; import skipped

This section preserves the earlier source proposal. It is not the current BO3/T7
work plan and does not authorize a new H1 build, conversion or runtime.

Source base is owner fork `bigmangeekf/x64-zt` at
`fab935826c898806855376662a8a03317b3ad8f1`, already retained. The parallel owner's
`tools-source/asset-bridge/model/zonetool-fab9358-h1-xsurface.patch` changes only
`h1/converter/iw7/assets/xsurface.cpp`: refuse unsupported groups5–8, invalid
negative/over-vertex counts and missing blend data; require index multiples64
before division; read source subdivision count before destination copy. This is
not an XModel-bounds fix or proof subdivision renders.

The accompanying `blend_bridge.py` converts raw H1 uint16 indices to supported
IW7 groups1–4, checks skeleton1..255 (H1 uint8 count) and exact byte length/readback, preserving
opaque weights. The reported apply/reverse and byte tests are source preparation,
not native compilation. Integration reference: `docs/ASSET-BRIDGE-H1.md` and the
H1 owner's commit. The historical proposed proof was a patched tool compilation,
one bounded conversion with known bones/weights, XMB/XSB/FF readback and a beacon
pair scene. A group5–8 donor had to fail before output rather than silently produce
corrupt geometry. These requirements remain recorded; H1 import is not resumed.

## Surfaces owner: remove a concrete import trap

Pinned `iw7/assets/material.cpp` retains JSON image/techset names for later
dependency loading only for zone names starting `paris_enemy_`. Other names use
`DB_Find` too early and can bind a default. The surfaces owner is preparing the
real parser/dependency correction and targeted tests. A new `sdk_beacon` resident
material must not merely rename itself to hide this problem.

Use a tiny original DDS/TGA resident image (`stream=0`), explicit material/techset
closure and generic zone name; native build/inventory then a properly lit client
frame establishes whether texture/normals/shading bind. PNG is not direct input
at this pin. The original beacon's recipient-material reference is a control,
not evidence that this custom-material bug is fixed. Mod PAK is absent from the
downloader, so resident textures remove that transport dependency for the small
vertical. Sounds remain a separate alias/SABL/SABS closure and hearing witness.

## Animation/AI owner: make the next motion measurable

`tools-source/asset-bridge/animation/xab_preflight.py` inspects H1/IW7 XAB envelopes
(216/136-byte structures), count/bounds, bone identity, notetrack time0..1,
root-delta trans/quat2/quat4 and frame255/256 boundary. The owner's23 standard-
library tests qualify `serialized-envelope-only`: compressed tracks are not
decoded and runtime is false. H1 IK/secondary/alternative/blendshape/viewmodel
and aliased blobs are explicitly unsupported, not automatically converted.

Next fixture is original `tag_origin` + `tag_probe`, matching the skin probe.
Decode/write one keyed original clip; independently read back exact tracks,
then observe two poses/bend and one timed notetrack in the beacon scene.
An actual enemy additionally requires animclass/.atr/XAnim/ASM/BT/callbacks and
network registration closure. Integration reference: `docs/ANIMATION-AI-BRIDGE.md`.

## Distribution and agent dependencies

Distribution consumes [community manifest v1](MODDING-PLATFORM.md) directly,
checks active dependency payloads, exact versions, both-direction conflicts,
namespace/path/asset collisions, protocol and reviewed native-source capabilities.
Its package mirrors client FF to the dedicated and separates server GSC from
FastDL; a deterministic ZIP is not a compatible executable or deployed service.
`77e6d4d` protocol2 source is the current declared baseline, not measured installed
binary identity. Cache-update correction/provenance must be tracked separately.

Agent testing must extend the reviewed existing fixture, preserving fresh engine
godmode/inactivity0/cheats0 and Main. Plan B uses one sequential protected
player; its two client generations do not validate independent multiplayer. A second client
needs the documented simultaneous-receiver exception and complete pair admission.
The retained Plan B observations include actual Use effects and HUD counts;
a dispatched input acknowledgment or READY_MODEL log alone is insufficient.
Use full-quality controlled frames for material/animation claims. Reduced frames
support the limited visible shape/HUD observations already recorded, without
qualifying texture, UV, normal or lighting fidelity.

The current priority is one BO3/T7 asset through an actual catalogue/export and
its measured closure; H1 geometry is no longer a prerequisite. The original
Beacon's protected Use/restart and limited geometry/HUD witness are retained.
Resident material fidelity, keyed motion and complete weapon/enemy behavior remain
separate milestones. Each milestone gets its own measured payload/closure,
join/update/teardown evidence and explicit supported source pins. Public release
also needs content provenance/redistribution decisions and a real public-server
join witness. The targeted SDK runtime pass does not qualify those broader goals.
