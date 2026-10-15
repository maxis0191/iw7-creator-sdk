# Creative freedom: current evidence and next proof

The objective is the deepest practical control of IW7: original content, engine
inspection, rendering, physics, AI, gameplay, networking and creator tools.
BO3 is a reference and a source of demonstrations, not a ceiling. Individual
extensions can go deeper than reproducing an editor; superiority over every
BO3 tool or unrestricted control of every IW7 subsystem is not established.
Authentic BO3 textures, a usable Ray Gun with real PAP/projectile behavior, and
the adapted full HUD remain the immediate visible goals.

## 2026-10-15: five surfaces for deeper creator control

Snapshot: 11:24 UTC, before completion of the separately owned authored FF case.
This source audit launches no runtime probe and qualifies no new native result.

**Source** means an implemented input/API and its source checks. **Measured**
means the named native/offline or engine observation actually occurred.
**Visible/playable** requires the relevant client pixels or behavior; it does
not follow from serialization, logging, process exit or a manifest. Owner
acceptance remains separate. Each level describes its stated witness, without
promoting the machine-readable capability catalogue or universal compatibility.

| Creator capability | Existing surface and owner | Acquired evidence | Next decisive witness |
| --- | --- | --- | --- |
| Inspect the engine and test actual input effects | Native owns [debug scopes/cadence](https://github.com/maxis0191/iw7-mod-components/blob/7f8a140d58cbf2e249d01e937e9168d67374cb0c/src/native/paris_debugger.cpp); server Ops owns protected scenarios. | Source provides bounded native scopes and render-callback telemetry. Actual [HUD 0.12 input/capture evidence](https://github.com/maxis0191/iw7-paris-server/blob/5235fd1e07744584924edd3bf6353a3c85ea2b7d/docs/deployments/2026-10-15-bo3-hud-core012-run.json) is distinct from dispatch acknowledgement and Source mocks. Callback rate is not displayed-frame/GPU-draw proof. | Reuse the existing probes to correlate an edited project's inputs, actual world/inventory state and original frames, then compare teardown and frame-time/cadence. |
| Author different geometry, texture and behavior with the same tools | SDK owns [editable projects/Creator inputs](../sdk/modding/ORIGINAL-AUTHORING.md); assets owns the [DDS/material seam](https://github.com/maxis0191/x64-zt-extensions/blob/2d84d015163fd8c2a68b3e0bd659d1342609f897/tools-source/asset-bridge/surfaces/AUTHORED-DDS-MATERIAL.md) and geometry writer/readers. | Source accepts distinct names, geometry, pixels and editable GSC rather than the Beacon template hash. Material C measured an original-image FF build/readback; it does not qualify these new projects or their rendered materials. Current authored FF integration is a separate pending witness. | A second independently edited project builds, packages and appears with its own texture/Use behavior on unchanged runtime/tool interfaces, without another per-asset hook or allowlist; then test a second client and late join/cleanup. |
| Create/remove real native collision from authored bounds | Native owns the [box provider](https://github.com/maxis0191/iw7-mod-components/blob/7f8a140d58cbf2e249d01e937e9168d67374cb0c/docs/COLLISION-PROVIDER.md); server Ops owns [player contact](https://github.com/maxis0191/iw7-mod-components/blob/7f8a140d58cbf2e249d01e937e9168d67374cb0c/docs/COLLISION-PLAYER-CONTACT.md); World supplies geometry/bounds. | The zero-client engine episode measured point/actor queries changing after insertion and returning after removal. The player-contact caller is Source. Standing, prediction, client colliders and world reset are not qualified by those queries. | At the same measured pose: fall without the body, land/stand and move with it, then fall after removal. Correlate visible authored geometry and exact world bounds. This proves an added platform, not a new-map compiler. |
| Author mechanics and connect actual state to presentation | Native/weapon owns the [weapon/PAP route](https://github.com/maxis0191/iw7-mod-components/blob/7f8a140d58cbf2e249d01e937e9168d67374cb0c/docs/RAYGUN-WEAPON.md); UI owns [LUI and native subscriptions](https://github.com/maxis0191/iw7-mod-components/blob/7f8a140d58cbf2e249d01e937e9168d67374cb0c/docs/BO3-ZOMBIES-HUD.md); server/SDK own integration. | Weapon definitions and normal engine/PAP paths are Source; no playable custom Ray Gun is proved. Real HUD cases show bounded state/ammo effects; each unseen factory/state still needs observation. | Qualify grant, projectile travel/impact, reload/damage, a real paid PAP transaction and peer replication. Preserve actual engine state/visibility in the UI rather than manufacturing state for a visual proof. |
| Make iteration and module lifetimes reversible | UI owns generation-aware callbacks and hooks restored only while still owned; SDK owns the [lifecycle/compatibility contract](MODDING-PLATFORM.md). | Source contains those ownership mechanisms. Completed scenarios restore files after the owned client closes; that is not live restoration of instantiated widgets. A manifest/namespace does not execute lifecycle code or isolate a VM. | Extract the useful existing ownership/cleanup seam when a second module needs it; test two consumers through unload/disconnect/map change. Controlled live reload, a native plugin ABI and arbitrary multi-mod composition remain unqualified extensions. |

The first reusable creator milestone is the second project on the same
toolchain/runtime. It is a foundation, not a limit on later engine innovation.
Original IW7 authoring does not depend on BO3 texture descriptors, XPAK layout
or retail mip counts: supplied original DDS/TGA data follows its own supported
IW7 path. Import research continues without becoming an authoring prerequisite.

Reuse existing owners and one admitted heavy group. The current writer/FF,
weapon, texture-RE and HUD scenarios retain their separate ownership; this
roadmap creates no parallel implementation or execution authority. Keep one
coherent end-to-end hypothesis per next runtime case. Content identity and
compatibility still matter, while a visual version needs an Ops contract change
only when its diagnostic/API contract changes. No new framework or runner is
required for the proposed witnesses.

The [capability catalogue](../sdk/modding/capabilities.json) remains the package
gate. This documentation changes no blocked level, dependency pin, runtime
permission or owner acceptance. Historical recipes are evidence only: use the
current owning product workflows/resources and preserve all human prohibitions
on restoring deleted stock, retired labs, services or access bridges.

## Retained 2026-10-12 source snapshot

The remainder preserves the earlier assessment, proposals and failed approaches.
Its present-tense statements describe that date, not the current programme.
Cross-product evidence links use their canonical owning repositories; they are
not instructions to resume historical experiments.

The initial 2026-10-12 map used reviewed project `21b91e3` and the program's single
prior official-source review. That historical source/offline snapshot is distinct
from the later [SelfContained Use/rejoin Plan B checkpoint](https://github.com/maxis0191/iw7-paris-server/blob/5235fd1e07744584924edd3bf6353a3c85ea2b7d/docs/SELF-CONTAINED-BEACON-RUNTIME.md)
and [BO3 catalogue J observation](https://github.com/maxis0191/x64-zt-extensions/blob/130aa6e015fc591615a5378f5c6ae73f81775084/tools-source/asset-bridge/t7-bridge/catalogue-runtime-j-20261012.json).
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
| Original rigid geometry | [1040B model witness](https://github.com/maxis0191/iw7-paris-server/blob/5235fd1e07744584924edd3bf6353a3c85ea2b7d/docs/deployments/2026-10-07-model-visible.json), plus five usable Plan B frames showing the original 24-vertex/12-triangle cube | Observed shape/HUD only; one rejoin frame is nearly black. Texture/UV/normal/lighting conformity, donor conversion and animated weights remain distinct. |
| Beacon FF serialization and interaction | [1048B offline FF](../sdk/modding/beacon-ff-validation-2026-10-12.json) and later [Plan B runtime](https://github.com/maxis0191/iw7-paris-server/blob/5235fd1e07744584924edd3bf6353a3c85ea2b7d/docs/SELF-CONTAINED-BEACON-RUNTIME.md): Use/HUD, same server entity/team state and reset personal state across controlled client restart | Recipient shoes-material appearance and overall pixels remain unqualified. This is one sequential client, not independent multiplayer or WAN; package readiness remains false. |
| Client Lua/LUI in FF | [HUD delivery](https://github.com/maxis0191/iw7-paris-server/blob/5235fd1e07744584924edd3bf6353a3c85ea2b7d/docs/deployments/2026-10-07-hud-delivery.json): visible Lua text, cold cache, corrected seeded update | Native loader/version required; per-frame gameplay data bridge, complex menus, independent two-client/WAN tests remain. GSC HudElem is not LUI. |
| BO3/T7 asset import; retained H1 history | [Closed F checkpoint](https://github.com/maxis0191/x64-zt-extensions/blob/130aa6e015fc591615a5378f5c6ae73f81775084/tools-source/asset-bridge/t7-bridge/CATALOGUE-TWENTY-2026-10-12.md#subsequent-f-attempt-first-catalogue-with-names): CatalogueWithNames, ten names, eight resolved nondefault entries plus two references; native/host exit zero and independent closure | CatalogueObservedPendingDonorReview: no asset-zone ownership, geometry, export or runtime compatibility proof; one resident-only donor/LOD is proposed for source review. Ready remains false. H1 import is skipped; its converter notes remain historical. |
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

The separately reviewed [FLAC build C](https://github.com/maxis0191/x64-zt-extensions/blob/130aa6e015fc591615a5378f5c6ae73f81775084/tools-source/asset-bridge/surfaces/sound/native-checksum/FLAC-BUILD-C.md)
qualifies compilation and the bounded C++ probe. The subsequent actual
[DumpOnly A checkpoint](https://github.com/maxis0191/x64-zt-extensions/blob/130aa6e015fc591615a5378f5c6ae73f81775084/tools-source/asset-bridge/surfaces/sound/dump-only-checkpoint-2026-10-12.json)
proves corrected 4096/4096 block metadata and unchanged seek/frame bytes on the
preserved F banks. [The subsequent strict codec run](https://github.com/maxis0191/x64-zt-extensions/blob/130aa6e015fc591615a5378f5c6ae73f81775084/tools-source/asset-bridge/surfaces/sound/dump-only-codec-checkpoint-2026-10-12.json)
recovers the exact original PCM and full WAV. Native alias lookup and audible
playback remain unproved. The original F decoder failure is retained unchanged.

### Retained H1/model converter correction; import skipped

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

### Surfaces owner: remove a concrete import trap

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

### Animation/AI owner: make the next motion measurable

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

### Distribution and agent dependencies

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
