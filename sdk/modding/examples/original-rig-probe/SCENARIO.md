# Original rig: DISPLAY / ANIMATE experiment

This opt-in GSC supplies source calls for the retained original two-bone fixture.
It is not an animation adapter or a qualified package. The existing manifest
remains an experimental Plan with blocked skeletal capability. Demo owns the
private runner, installation, protection, captures and rollback; the SDK owner
owns subsequent manifest binding. Do not run through the rigid ModelLabV2 gate.

## Exact interoperation

Use the observed `sdk_original_rig_probe` FF: 1,064 bytes, SHA-256
`ea7ba4be1d5e6f0878431b51e7b9b1ba9d2b10bf74b1ad21da14d55c414e145d`.
Its seven inventory rows include two models/surfaces, the original
`paris_original_probe_bend` clip, a rawfile and the recipient material reference
`mopw/character_park_clown_zombie_shoes`. It contains no NCS, animtree or GSC.
The 281-byte clip redump hashes to
`a9cd7a3de12b805f5f3e73e5442980a714e39294912f689992f55e3d65576444`.
These hashes describe files, not loaded engine assets.

Stage the FF on both private dedicated and base client at
`mods/sdk_original_rig_probe/mod.ff`, preserving any existing file. Install this
source only on the private dedicated as
`iw7-mod/custom_scripts/cp/sdk_original_rig_probe.gsc`. Select
`fs_game mods/sdk_original_rig_probe` before map load. Use `cp_zmb`, dedicated
mode, a non-Main loopback port, a random nonempty password, `sv_lanOnly 1` from
launch and native heartbeat suppression. Keep `sv_cheats 0`. Preserve Main27016
and occupied clients. The runner must verify fresh actual engine godmode and
inactivity protection before exposure; this GSC neither applies nor proves them.

Pinned Aurora source `77e6d4d24e918ee363b3feee3735c3b889dff7d7` provides:

- `fastfiles.cpp`: automatic `mod` load in global MP/CP loading; `Sys_CreateFile`
  redirects `mod.ff` to `fs_basepath/fs_game`; `loadzone` is asynchronous and
  `listassetpool` can enumerate registered asset names. Prefer the normal mod
  load here. A manual loadzone return would not establish completion.
- `gsc/script_loading.cpp`: custom `init` executes before the retail
  `Scr_LoadLevel` call. This source precaches before any wait.
- `patches.cpp`: `NetConstStrings_IsPrecacheAllowed` is patched true. This is
  not proof that custom model/animation names resolve on a connected client.

Retained retail source pin `1dd48a78e55ef9c99519fc5221a206168ce2e98a` uses
`precachempanim(name)` before its first wait in `scripts/mp/animatedmodels.gsc`,
then `scriptmodelplayanim(name)`; CP Spaceland UFO uses the same playback method.
The source route is established; the original clip's runtime binding is pending.
The durable native958 manifest's fixed legacy `Protocol=1` is not a measured
game handshake. Pinned game source defines `PROTOCOL=2`; verify `getInfo.protocol`
and the actual executable hash in the runtime slot. Preserve the old manifest.

After map loading, collect these existing console queries on each process:

```text
listassetpool 8 paris_doom_skin_two_bone_first_a
listassetpool 8 paris_doom_skin_two_bone_second_a
listassetpool 7 paris_doom_skin_two_bone_first_a_lod0
listassetpool 7 paris_doom_skin_two_bone_second_a_lod0
listassetpool 6 paris_original_probe_bend
listassetpool 10 mopw/character_park_clown_zombie_shoes
```

Pool IDs come from that pinned `XAssetType` enum. A matching name establishes
enumeration only, not the in-memory skeleton, GPU resource or rendered result.

## Two short runs

For each fresh map load set the following before the source `init`:

```text
sdk_original_rig_probe_enable 1
sdk_original_rig_probe_mode DISPLAY
sdk_original_rig_probe_play 0
sdk_original_rig_probe_stop 0
```

1. **DISPLAY:** join the protected client and finish the stock intro. Record
   `PRECACHE_BEGIN`, `PRECACHE_RETURNED`, three `MODEL_CALL_RETURNED` and
   `DISPLAY_READY`. Inspect actual loaded XModel/XModelSurfs and material names
   on both processes, then capture the three static ribbons. Actor 0 is the
   static first-profile control, actor 1 also first, actor 2 second. Default mesh,
   unresolved material, absent ribbon or a precache error is a failed display
   result. Preserve the earliest diagnostic before cleanup.
2. **ANIMATE:** repeat with mode `ANIMATE`, keeping play zero. This also calls
   `precachempanim` before the first wait. Capture the same static scene and
   record registry observations for `paris_original_probe_bend`. After fresh
   protection/camera verification, set `sdk_original_rig_probe_play 1` through
   the runner's existing native console route. The source calls playback once
   on actors 1 and 2 and leaves actor 0 static. Capture several cycles in native
   frames with their actual timestamps. `PLAY_CALL_RETURNED` proves only that
   the script call returned; it does not prove deformation, cadence or pixels.

The scene is 160 units ahead of the joining player's horizontal heading, raised
48 units; actors are spaced 64 units laterally and scaled 3. Their yaw equals the
player's initial yaw, placing the observer on local negative X facing the YZ
ribbon. Actual entity IDs, origins and angles are printed. Keep the camera fixed
and use that observed pose; the printed player origin is not an eye-position or
rendered-camera witness. Geometry is eight vertices / six triangles per actor,
with root `tag_origin` and child `tag_probe`, bind pivot `(0,0,8)`. Compare neutral
and both bends against the existing CPU pose reference; do not infer blend-weight
direction from one bone tag. Loop duration is measured, not assumed from 30/30.

No event consumer is attached for `probe_contact`. Native notetrack delivery,
remote/late joins, AI behavior and owner acceptance remain unqualified. Do not
manufacture a timer or notification and call it animation evidence. If precache
or binding fails, retain the exact failing name/phase and coordinate only the
demonstrated missing primitive with the native owner; do not invent NCS assets.

Set `sdk_original_rig_probe_stop 1` to delete the actors and stop scene threads;
native game end also cleans up. The external runner restores changed files,
profile/config and dvars, checks hashes and closes only its own exact processes.
This source changes no player weapons, perks, health, origin or camera.

## Source validation

On 2026-10-13, GSC Tool 1.5.1.359 (SHA-256
`1adfd67414a9b886cbad57ee0378f622eed485bcef7711322aee478e298fadcb`)
parsed and compiled this source for IW7/PC in dry mode. The source has no script
imports. The four existing original-rig Plan tests and product ownership gate
passed. Offline compilation does not prove engine loading or custom playback.
No native build, asset rebuild, game launch or owner gameplay occurred here.
