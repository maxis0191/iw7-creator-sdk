# Creative capabilities: proof, gaps and implementation steps

This2026-10-12 map uses reviewed project `21b91e3` and the program's single prior
official-source review. No new upstream update check, build or game test was run.
The desired BO3-like freedom is a target: easy original/H1 assets, custom HUD,
gameplay, weapons/enemies/maps, multiplayer distribution and public dedicateds.
A server GSC module catalogue alone does not deliver that target.

| Creative operation | Strongest retained witness | Missing proof / next implementation |
| --- | --- | --- |
| Server gameplay, private HUD | Existing CP modules; normal native dedicated and HudElem paths | Shared VM/canonical-string/reliable-command budgets; new beacon compiled/link/pair cleanup. No arbitrary sandboxed plugins. |
| Original rigid geometry | [1040B model witness](deployments/2026-10-07-model-visible.json): visible24-vertex cube at two poses, downloaded exact FF, LOD fix | Dark geometry only; full material/lighting, donor conversion and animated weights are distinct. Earlier MODEL-LAB pending paragraphs predate this witness. |
| Client Lua/LUI in FF | [HUD delivery](deployments/2026-10-07-hud-delivery.json): visible Lua text, cold cache, corrected seeded update | Native loader/version required; per-frame gameplay data bridge, complex menus, independent two-client/WAN tests remain. GSC HudElem is not LUI. |
| H1 rigid/skinned import | Existing pinned H1 converter plus new bounded blend reader/patch from H1 owner | Converter group/count/subdivision errors need actual tool compilation, roundtrip and recipient pixels. Full H1 import is unproved. |
| Original resident image/material | ZoneTool reader supports resident DDS/TGA; source fix prepared by surfaces owner | Material resolution currently depends on zone-name prefix/early DB lookup. Prove generic-name FF and resident images without PAK before exposing easy imports. |
| Skeletal animation | Animation owner's bounded H1/IW7 XAB envelope/bone/notetrack preflight | Compressed tracks not decoded; no imported motion. Two-bone original keyed clip, native writer/readback, two rendered poses and notetrack next. |
| New weapons | Weapon JSON/reference paths exist in pinned ZoneTool | View/world model, hands/rig, fire/reload/PAP, sounds/FX, notetracks and peer replication. No playable custom weapon witnessed. |
| New enemies/AI | Retail enemy-port experiments, GSC/callback/BT/ASM research | Imported model does not supply behavior; callback registration, animclass/ATR, movement/attack/death/FX/audio and late join require complete closure. |
| More active actors | Known native allocation/serialization/client audit | Previous64 candidate crashed;48 requires coherent engine+client patch, not a dvar or static-renderer list expansion. |
| Custom maps/gametypes | Later pinned downloader has usermap allowlist | No complete map compiler/collision/nav/lighting/spawn/stock gameplay or playable new-map proof. Not qualified in community v1. |
| Community multiplayer | Small local mod FF download/cache-update proof; dedicated foundations | One fs_game, content/version/source checks, two fresh clients, update and rollback, WAN/public join; no EXE/DLL auto-delivery. |
| Independent mod composition | Exact dependencies/conflicts and transport graph validation | No native multi-mod linker/isolated namespace/ABI. One asset-bearing fs_game; compose only through a reviewed build with joint closure and tests. |

The machine-readable [catalogue](../sdk/modding/capabilities.json) keeps blocked
features named so authors can plan them. It refuses their package stage until a
reviewed capability change records appropriate proof. Adding a JSON flag alone
cannot qualify a native feature. Evidence references are claims to audit, not
authenticated attestations. Runtime/owner acceptance remains separate.

## H1/model owner: actual converter correction

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
H1 owner's commit. After review/admission, compile the patched existing tool,
convert one bounded input with known bones/weights, re-read XMB/XSB/FF and exercise
the beacon pair scene. A group5–8 donor must fail before output instead of silently
producing corrupt geometry. Retain failed negative tests alongside visible proof.

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
godmode/inactivity0/cheats0 and Main. The model fixture currently requires one
player; merely calling it twice cannot validate multiplayer. A second client
needs the documented simultaneous-receiver exception and complete pair admission.
Assert actual Use effects/replicated model orientation/HUD counts; a dispatched
input acknowledgment or READY_MODEL log is insufficient. Use full-quality frames
for material/animation claims, reduced clients only for qualified logic evidence.

Milestones keep the same contract: original beacon → H1 geometry with corrected
blend handling → resident material with generic zone name → keyed two-bone motion
→ complete weapon/enemy. Each milestone gets its own measured payload/closure,
join/update/teardown evidence and explicit supported source pins. Public release
also needs content provenance/redistribution decisions and a real public-server
join witness. None of those is inferred from this source-only SDK delivery.
