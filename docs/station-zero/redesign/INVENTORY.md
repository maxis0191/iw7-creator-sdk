# Station Zero: what our tools can author today (27 Nov 2026)

Read-only research. Studio `C:\studio` `25d640f`; SDK worktree `sdk-sz20` `0ab32f9` (`claude/sz-r19`, not merged). **[v: x]** = I read the code or data, or ran the command. **[doc]** = a document says so; evidence not checked. `ST` = `C:\studio\studio`, `SDK` = `sdk-sz20\tools-source\iwzmap`, `CHK` = `C:\studio-data\sz\film\r19_check.json`, `TF` = `sz\TOOL-FAULTS.md`.

**Read first.** r19 has no final bake (`r19\FDONE` = `BAKEFAIL`, `bake.json` empty) [v]. `studio budget` answers `ok:false` (`lights_named` 72 of 25): a stale rule that counts every light with a `group`; `check` passes [v: `ST\answers.py`, CHK]. r19's only fixtures, 9 emergency lamp props, are never drawn (`MODEL_NOT_BROUGHT`, no kit entry) [v: CHK]. Stale lines: README "lights of a layer are not merged" (r19 merges 142) and `BASED.md` "a power spot becomes an omni" (CHK lists `iwz_power spot` rows) [v].

## 1. Object kinds (30) [v: `ST\expand.py` KINDS, `ST\build.py`]

| Kind | Key fields |
|---|---|
| box | box, material, mode both/render/collision/clip, uv per face {fit, tile, offset, flip} |
| wall, floor, ceiling, room | box or rect+z, materials, openings, holes, thick |
| beam, column, arch, vault | ends or rect, sides, rise, segments |
| stair | at, yaw, steps, rise, run, width (clip ramp and rails added) |
| mesh | inline tris+uvs, or a .obj/.glb/.gltf file; origin, yaw, scale, mode |
| prefab | a lifted stock room: at, yaw, clip_to, cut, fill, openings, select |
| sign, decal | at, normal, size; material, or text+font+color, or picture file; sign: emissive, lamp, hanging |
| prop | model, origin, angles, scale, static, clip, emissive |
| light | origin, color, radius, intensity, omni/spot, dir, cone, group, runtime, shadows, bake |
| fx, camera | name; eye, yaw, pitch |
| zone, link, door, start, spawner, perk, wallbuy, wheel, pap, power, marker | box or at/yaw, cost, zones |
| replace | zone or box; what = render, collision, nav, props; clip |

Not kinds, only builders: `clip`, `fixture` (prop + lights), `doorway` (replace + three meshes), `prop_row`, `prop_scatter`, `props.scatter`, `dress_like`.

**The frozen base.** A layer removes base render, collision, nav triangles and static props in a zone or box, and adds its own [v: `ST\based.py`]. It cannot re-skin a base surface (only remove and redraw), nor move or delete a base perk, wheel, PaP, power switch, door, spawner, light or script model (FE32) [v: `ST\basegame.py`, CHK `not_emitted`]. Layer `fx`, script-model props and cameras are not emitted into a base [v: `expand.py:240`, `based.py:466`]. The rest is `SDK\station_zero2.py` (3,599 lines), then a regenerated base.

## 2. Custom geometry and new models

- **Mesh.** OBJ (inches, z up) or glTF (metres, y up); UVs kept; one record per `usemtl` [v: `ST\meshio.py`, `expand.mesh_records`]. Collision = the same triangles, or a second collision-only mesh. Lightmap UVs come from the baker's charts. 65,535 triangles a surface. Material: any `w/` name. In game: `examples\bo3_room.py` [doc: `port\README.md`]. r19: 3 inline meshes, no file [v].
- **New model of ours.** Exists outside Studio: Blender `.glb` + `materials.json` -> `x64-zt-extensions\tools-source\asset-bridge\env-model\t7_env_port.py` -> a dump root -> `settings.build.kit.dumps` + `kit.models`. Each material's colour, normal and gloss maps are baked to BC7 images of at most 1024 on the `mo/barrier_handrail` template; emissive on the exit-sign template; glass = stock; collision by voxel boxes [v: env-model `README.md`, `SDK\perks\machines\README.md`]. 34 such models exist (track kit, platform edge, subway car, genset, turnstiles, ticket booth, wall clock, metro signs) and the base places some as static rows (`iwz_platform_edge_128` x34, `iwz_track_256` x25) [v: port roots, `base_sb\smodels.txt`]. Proof tools exist (`SDK\train_proof.py`, `kit_proof.py`: drawn, textured, lit from A/B frames); I found no result record, so in game: not verified. Hand steps, no `studio` command.

## 3. Materials and textures

| Need | Route | State |
|---|---|---|
| Stock world material of any of 572 zones | name it, the build brings it | r19: 39 template + 21 brought, mp and sp zones too [v: CHK] |
| Our PNG or text on a quad | `B.sign`, `B.decal` -> `<data>\signs` -> `custom_materials.json` -> `SDK\sz2_assemble.py` clones a stock base | colour only; 8 px a unit, max 1024, mips [v: `ST\signs.py`] |
| Transparency | blend base, the picture's alpha | [v] |
| Glow | emissive base, `emissivePara` | one radiance in both power states; near black with power on (FE62) [doc] |
| Lit picture | `lamp=True` | one `power` spot = one snapshot record [v: `signs.lamp_light`] |
| Own colour + normal + gloss | `ext` entry on `concrete_01` | assembler reads it [v: `sz2_assemble.py:71`]; only `port\emit_custom.py` writes it; no `B.*` block |
| Colour variant of a stock tiling material | generator `SDK\sz2_materials.py` CUSTOM (`base` + `tint`) | 10 in the base (`w/iwz_tile_green`, `iwz_tile_cream`, `iwz_panel_wall_red` ...) [v: `base_sb\custom_materials.json`]; a layer may name them (not judged, `ST\answers.py:452`); r19 uses none [v] |
| Own tiling wall or floor image | same table takes `image` (colour, semantic 2) on a stock base | no such entry exists: all 52 own images sit on poster, decal or emissive bases [v]; no `B.*` block |

No power-switched emissive (FE52, measured) [doc]. Neon = stock neon models.

## 4. Models

- Dumps (xmodel files): cp_zmb 2,850, cp_disco 3,093, cp_final 2,407, cp_rave 2,323, cp_town 2,356, ours 34 [v: counted]. Index: 21,706 model names, 572 zones [v: `store stats`]. `fixtures.use_kit(m)` writes the kit from these five dumps only [v: `ST\fixtures.py`, `rooms\assets.py`]; another zone needs its dump root added by hand.
- Look first: `python -m store find <words> --zone a,b [--show]`, `store list`, `store facts model`, `store show <model>` (six views, axes, back side; 5 to 10 s cold; starts ZoneTool, not run here). After a frame: `studio pick`.
- 168 lifted stock rooms (`rooms.find --fits WxD --theme shop`) [doc]; r19 uses 7 [v].
- GrayWolf: BO3 and IW installed. BO3 holds the gaps: mannequins, an escalator kit (mp_metro), gramophone, phonograph, typewriter, pianos, Victorian couches, transformers, kiosks [v: `find_assets`]; each needs the port of section 2.

| Space | Covered (hits in the five zombies zones) | 0 hits in all IW7 zones |
|---|---|---|
| Metro | subway 34, bench 20, clock 8, ticket 6, payphone, lockers | departure board, split flap; escalator only in mp zones (15) |
| 1978 arcade | arcade 63, marquee 57, neon 38, shop 75, record 10, CRT 6 | photo booth, pinball, cassette, VHS, boombox; mannequin = 1 bust |
| Plaza | tent 26, awning 16, barricade 4, body bag 2 | hazmat, quarantine, decon |
| Converter hall, cabin, relay room | electrical 34, console 21, generator 19, fuse 9, transformer 2, insulator 1 | rectifier, relay, oscilloscope; lever 2; server racks 27 in other zones |
| 1893 salon | curtain 23, statue 22, painting 12, mirror 12, chandelier 6 | organ, armchair, gramophone, typewriter; piano 1 |

**60 hero props (names in the index) [v: `store find`].** Metro: cp_disco_subway_turnstyle_animated, cp_disco_subway_lockers_02, cp_disco_worn_subway_bench, cp_disco_firstt_subway_entrance, cp_disco_2nd_subway_gate_bars_01, cp_disco_subway_station_power_door, cp_disco_subway_traffic_light_red, cp_disco_subway_construction_barrier_01, cp_disco_subway_train_bsp2xmodel, cp_disco_street_telephone_booth_emissive, cp_disco_street_news_vending_01, sign_clock_04, cp_final_theater_ticket_window_01, zmb_mobile_ticket_booth, iwz_zm_zod_ticket_booth, iwz_mou_clock_wall, iwz_zur_metro_long_sign_a, iwz_zur_metro_round_display_01, iwz_machine_vending_food. Arcade: cp_disco_storefront_doors_left, cp_disco_storefront_security_gate, arch_rollup_door_bottom, park_arcade_standing_09, ct_arcade_claw_machine, park_basketball_arcade_01, cp_town_jukebox, cp_town_cash_register, cp_disco_record_milk_crate, cp_town_45_record_01, cp_town_tape_recorder, zmb_tv_crt_01, cp_rave_tv_crt_01_on, popcorn_machine_iw6, p7_mannequin_bust_vintage_01, cp_disco_beaded_curtain, cp_rave_projector_with_reels. Power and signal: com_electrical_transformer, utility_transformer_small01, electric_insulator_01, electrical_control_panel_01, park_ride_control_panel, fac_sort_machine_fuse_box_set_01, ship_hallway_fuse_box, crr_switch_wall_boxes, iwz_g2_genset, cp_disco_street_lamp_signal_light_01. Salon: chair_victorian_velvet_01_red, cp_final_chandelier_d, decor_light_chandelier_candle_bulbs_01, cp_rave_fireplace, decor_globe_antique_01_dlc1, cp_town_willard_painting, dh_theater_curtain_05, pb_curtain_fancy, dt_mirror, mp_flip_lion_statue_02. Plaza: corpse_bodybag_01_dust, equipment_medical_folding_backboard_stretcher, cp_town_cdc_bed_restraint, misc_clear_vinyl_curtain_01.

## 5. Lighting

- `B.light`: omni or spot; baked (lightmap + light grid) by default; `runtime=True` an engine light; `shadows=True` a shadow slot [v: `build.py`].
- On this base: `emergency` = baked, on in both states; `power`, `flicker` = runtime lights switched by zone bank, **no bounce**; no group = `power` [v: `ST\BASED.md`, `baselights.py`]. One shadow per zone [doc]. Per zone only an intensity factor [v: `SDK\darkness\cp_iwz_darkness.gsc:131`]. Fog, exposure, vision: per map and per power state (`darkness.args --dark --lit --variants`); per-zone fog not found.
- Darkness needs the generator base: only `station_zero2.py:3560` writes `light_groups` [v]. A document without a base has one light state.
- **Motivated light** = `B.fixture`: a stock `_on` model with its light at the measured centroid of its lit surfaces (`fixtures_measured.json`). 33 kinds [v: `python -m studio.fixtures`]: ceiling_tube, ceiling_tube_blue, pendant, pendant_warm, ceiling_dome, downlight, industrial_strip, caged_bar, track_spot, spot_can, chandelier, cobra_head, wall_led, wall_sconce, wall_lantern, outdoor_wall, exit_sign, emergency_beacon, emergency_wall, bulkhead, beacon_wall, light_box, neon_open, neon_bar, neon_peep, neon_crank, neon_tube, desk_lamp, lantern, hanging_lantern, bare_bulb, bulb_strip, string_bulbs. neon_bar, neon_peep, neon_crank carry foreign words.
- Also: emissive props; world materials named `*lamp*` or `*_on` emit in the bake; sky and sun (`cp_town`, `mp_overflow`, `mp_paris`, `cp_zmb`) [doc].
- Caps: 256 visible lights a frame; voxel light lists 65,535 entries (cost grows with radius cubed); texel 8 [v: `ST\voxellights.py`].

## 6. Budgets of r19, base + layers [v: CHK unless noted]

| Budget | r19 | Cap |
|---|---|---|
| Snapshot records | 695 power on, 649 off, 710 with four players | 768 official client, 2,048 lab client |
| Runtime light rows | 198 | 256 |
| Voxel light entries | 75,576 raw; 59,191 with the budget compiler | 65,535 |
| Static props | 1,109 layers + 361 base | 65,535; 6,000 visible |
| Distinct models | 246 + 74 | 64 live slots (others rebuild when added) |
| Triangles | 36,530 render, 36,209 collision | 65,535 a surface |
| World materials | 122 in layers: 60 stock, 62 own pictures | none found |
| Zone | 181 MB reference + 116 MB sound [v: `live\doc-b8c53fc5`]; full 442 MB [doc] | |

Snapshot records: 214 reserved scriptables, 156 script models, 28 door brushes, 167 power lights, 83 gameplay, 46 at power-on. Free: static props, baked lights, structs, triggers. Headroom 58: each new `power` light, sign lamp, script model, door or interaction costs.

## 7. Gameplay objects

Base (generator): 9 zones, 5 doors, 9 perks, PaP, power, 3 wheels, 5 wall buys, 51 spawners, 4 starts [v: `base_sb\layout.json`]. Layers add zones, links, doors, spawners, starts, perks, wall buys, wheels, markers [v: `basegame.py` KINDS]; r19 adds 1 zone, 1 door, 12 spawners, 2 wall buys [v]. Refused: a second PaP or power switch, a perk the base places, a 1,500 door [doc: README]. Wall buys sell at the stock price [v: CHK warning]. Traps: the base has one, the Third Rail (fuse box, 750) [v: `base_sb\ents.txt:1686`, `cp_iwz.gsc:363`]; no document kind (`scenegen.py:1481` item only, none in `blend_core.py`) [v]. Of `cp_iwz.gsc` only the door, link, price and wheel tables are rewritten; `iwzmap_sz2_local.gsc` is the test fixture (door and probe tables only). Per-kind file table: `ST\BASED.md`.

## 8. Changing the layout

A zone behind a base wall is one layer (`doorway`, `room`, `zone`, `door`, `spawner`); nav is generated on the 32 lattice and linked. Proven by r19 (+1,382 cells, reach 63 of 63) [v: CHK] and the annex in game [doc]. Stairs and stacked floors: `B.stair`, `B.floor(holes=)`, `examples\testmap1.py` [v: code; game proof doc]; a stair in a layer on this base: no proof found. The nine base zones change only in the generator.

## 9. Iteration speed (Arcade)

| Step | Time |
|---|---|
| info, budget | 0.04 s, 0.2 s [v: ran] |
| check | 9.9 s [v: CHK stages] |
| live start, bake remembered | 74 to 85 s (build 35 to 46, game 30) [v: `r19\lf_run1`, `lf_run2`] |
| power on; shot --clean; stop | 17 to 18 s; 3.0 to 3.3 s; 0.2 s [v] |
| final bake; draft bake | 74 to 96 s; 18 to 23 s [doc]; r19's not measured |
| sync, prop or runtime light with a live slot | about 1 s [doc] |
| sync, power-light edit on this base | 78 to 95 s [doc: TF FE39] |
| variant into an open session | 12 to 16 s [doc: TF FE64] |

## 10. Cannot be done today

| Limit | Where | Change |
|---|---|---|
| Own tiling material (image, normal, gloss) from a document | `ST\signs.py` writes quads; `sz2_materials.py` CUSTOM is generator-only; `ext` only via `port\emit_custom.py` | small |
| Authored model in one command, known to `store` | env-model is outside Studio | medium |
| Kit models from zones outside the five dumps | `rooms\assets.py dump_roots` | small to medium |
| Move, delete, re-skin base gameplay, lights, script models | `basegame.py`, `based.py` | medium, or regenerate |
| Darkness without the generator base | `station_zero2.py:3560` | medium to large |
| Sign that glows only with power; neon text of ours | emissive technique (FE52) | engine, or a model pair |
| Per-zone fog or vision | not found | unknown |
| fx, script models, animated props from a layer | `expand.py:240`, `based.py:466` | medium |
| Traps, new interactions | no kind | medium + script |
| Over 768 records for official players | engine snapshot cap | client release |
| Bounce from power lights | dark split | large |
| Preview of our sign materials | 62 `PREVIEW_CANNOT_DRAW` [v: CHK] | medium |
| `studio free`, `scatter` on base floors | FE57 [doc] | small |

## Ten things the redesign should exploit that the current map does not use

1. **Authored meshes.** r19 is 603 render-only boxes, no mesh file, no arch, vault, column, beam or stair [v: layer profile].
2. **Authored and ported hero models**: the route made 34 for the base, none for the Arcade.
3. **BO3 as the source for the gaps** (escalators, mannequins, Victorian furniture, gramophone, typewriter, transformers).
4. **Materials of all 572 zones and tint variants**: r19 names 60; 237 boxes share one dark grey paint; top models are p7_box_cardboard_c_closed x124 and cp_rave_tiki_key_hook_01 x58 [v].
5. **A fixture for every light**: the generator's only `B.fixture` call is for `emergency` lamps [v: `arcade_layer14.py:484`]; 134 lights are placed by hand.
6. **Lifted stock rooms**: 7 of 168.
7. **Picture signs with our own `.ttf`** and `uv fit` panels, lit by `lamp`, inside the 58-record headroom.
8. **Arches, vaults, columns** for the salon and converter hall; sky and sun for the plaza.
9. **Gameplay in new sections**: r19 adds no perk or wheel; nine wheel scriptables exist, the base uses three [v: `scenegen.py:1424`, `base_sb\scriptables.txt`].
10. **Look before building**: `store show`, `rooms.find`, `studio light --survey`, `studio pick`, variant `sync --session`.
