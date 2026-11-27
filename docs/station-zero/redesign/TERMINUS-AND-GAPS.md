# Terminus and layer gaps: research for the redesign (27 Nov 2026)

Read-only. **[v]** = I read the code or data, or ran the command. **[doc]** = a document says so (`BASED.md`, `STATION-ZERO-Q1-T1.md`, `TOOL-FAULTS.md`). **[nv]** = not verified. Nothing was built, emitted or run in the game.
`BASE` = `C:\studio-data\sb\base_sb` (the film document's base [v: `film\base\doc\map.json`]); `SDK` = `sdk-film\tools-source\iwzmap`; `GEN` = `SDK\station_zero2.py`; `TPL` = `SDK\cp_iwz2.gsc` (the level script's template); `ST` = `C:\studio\studio`; `STOCK` = `IW7-Paris-Server\tools\iw7-gsc-dump\decompiled\scripts`; `DUMP` = `IW7-Runtime\iwz-map-ref-a\dump\cp_zmb`.

## A. Pack-a-Punch today

| Part | Where [v] |
|---|---|
| Alcove 256 x 144, z -320..-112, behind the control room's north wall | `GEN:115` (opening `a_control_pap`), `:1429-1434`, `:1451`, `:1457`, strip and trays `:1462-1466`, switchgear `:2411-2415` |
| Sign | `GEN:1461` `sign_pap` 200 x 50 at (3104, 4000, -88); material `w/iwz_sign_pap_c` (`BASE\custom_materials.json:73-77`, list `SDK\sz2_materials.py:156`) |
| Interaction | struct `interaction` / `weapon_upgrade`, `requires_power`, target `iwz_pap_spot` (`BASE\ents.txt:1546-1560`; `GEN:2811`, `:3144-3147`) |
| Machine | relocated stock scriptable: `pap_machine 0 3104 4110 -320 270` (`BASE\scriptables.txt:11`, `GEN:3145`) |
| Shutter | 2 script models `gate_warehouse_refinery_01` (`ents.txt:2156-2168`, `GEN:3201-3206`), 4 blocker brushes `*12` (`ents.txt:1339-1374`, `GEN:3083-3084`), struct (`GEN:2818`), fixture row (`GEN:3500-3501`) |
| Relay quest | 3 structs + 6 script models (`ents.txt:1618-1677`; `GEN:2813-2817`, `:3167-3174`); script `TPL:27, 30, 44-45, 65, 195-196, 234-347` (= `BASE\cp_iwz.gsc:240-356`) |

Removing it frees 12 map records (8 script models, 4 brushes) plus 3 spawned use entities.

**The machine** is Spaceland's own projector-style one: scriptable `zmb_pap_machine`, model `zmb_pap_machine_animated` (`_blue` when upgraded), parts `machine`, `door`, `papfx`, `reels` [v: strings of `DUMP\scriptable\zmb_pap_machine`; `SDK\sz2_assemble.py:120`]. FILM-LAYER §6's projector idea needs no new model.

**The prompt.** Registered at `STOCK\cp\maps\cp_zmb\cp_zmb_interactions.gsc:168` with hint function `weapon_upgrade_hint_logic`, which returns `CP_ZMB_INTERACTIONS_UPGRADE_WEAPON`, `_GENERIC`, `_FAIL` or `COOP_INTERACTIONS_UPGRADE_MAXED` (`STOCK\cp\zombies\interaction_weapon_upgrade.gsc:44-64`); applied by `set_interaction_trigger_properties` (`cp_interaction.gsc:1062-1067`). The cp_zmb text is not in our localize dump [nv]; its DLC twin reads "Hold [use] to upgrade your &&1 ($&&2)" (`iw7-dump-lui\localize.json:18689`). The upgrade prompts found do not name Pack-a-Punch; the words are in tutorial and card strings only (`:15916`, `:15941`, `:16077`).
**Override: yes, by code read.** Stock sets hints two ways: a table `level.interaction_hintstrings[kind]` and a per-kind `hint_func`, and the function wins (`cp_interaction.gsc:1164` before `:1193`), so the table entry alone does nothing here. `level.interactions["weapon_upgrade"].hint_func = ::ours` after the registry (`BASE\cp_iwz.gsc:481`) is the same field the map's perk module sets (`SDK\perks\cp_iwz_perks.gsc:113`, own strings `:86-90`) and the server sets for lost-and-found (`src\custom_scripts\cp\paris_loadout.gsc:819`). Not covered: the two refusal lines the cp_zmb monitor shows itself (`cp_zmb_interactions.gsc:504-556`). In game for this interaction: [nv].

## B. Moving it

**Route 1: Studio layer on a regenerated base (recommended).**
- A first PaP in a layer is allowed: the clash test refuses only when the base relocates `pap_machine` or has a `weapon_upgrade` struct (`ST\basegame.py:135-137`); two in one document: `SDK\blender\blend_core.py:157`. Unit test `C:\studio\tests\test_basegame.py:281-305` (emitted; a second refused). In game: [nv].
- The writer offsets the machine and weapon spot by +10 / +20 in y whatever the yaw (`blend_core.py:1249-1250`): right only for yaw 270.
- **Far-room collision is unsafe today.** `ST\based.py:400` and `GEN:2949` encode collision without `max_extent`; `ST\emitcache.py:124` and `SDK\scenegen.py:1590` pass 1,024. The Q1 tests recorded the fault: the player fell through the Terminus floor because one section spanned 6,400 units [doc: `sdk-film\docs\STATION-ZERO-Q1-T1.md`, "The Terminus floor"].
- An island zone is not refused: links come from walkable adjacency (`blend_core.py:1187-1200`), the reach gate starts from spawners (`ST\answers.py:663`, `:777`) [code read]. A layer zone gets respawn, idle and dog structs on its nav cells [doc: `ST\BASED.md:15`], so the room needs its own nav island.
- Its lights must say `group: emergency`; the default on this base is `power` [doc: `BASED.md:94`].
- A layer cannot add a module: only the base's `modules` list (`['post']`) is rebuilt (`basegame.py:366-381`). Markers carry no `area` box (`ST\build.py:324`, `blend_core.py:1032-1035`), which `SDK\modules\quest.gsc:712-721` reads for car 1 and the Terminus.

Generator edits to drop PaP: `GEN:115`, `:317`, `:1429-1434`, `:1451`, `:1457-1466`, `:2411-2415`, `:2811`, `:2813-2818` (line 2812 opens the table that also holds the trap and the bear: keep), `:3083-3084`, `:3144-3147`, `:3167-3174` (3164-3166 place the trap's fuse box: keep), `:3198` (the two relay model names only), `:3201-3206`, `:3500-3501`; `sz2_materials.py:156`; the `TPL` lines above (keep `level.player_pap_machines` and the lamp precaches 28-29). Add: the trip module in `layout['modules']` and its start call (`GEN:3175-3181`, `:3309-3313`), a cab marker with car 1's box. About 55 lines out of `GEN`, 120 out of `TPL`. Also named by: server `ops\gamelab\lib\szaccept.gsc:108-140`, `SDK\fixtures\sz2_local.gsc:619`.

**Regeneration (reconstructed, not run):** `python -I SDK\station_zero2.py <DUMP> <out>` (`GEN:3`, `SDK\build-g.ps1:62`) with the 21 variables of `BASE\build.json` `info.generator.env` (`python -I` ignores `PYTHONHASHSEED`, `GEN:3587`), on SDK main at or after `b10072c` (in `origin/main`, `sz-film`, `sz-r19` [v: `git merge-base`]). `C:\studio\tools\emit_cmp.py` compares a *document's* emit with a reference folder (`:1-21`), not generator output. The test is a file compare: regenerate unchanged, expect 19 of 19 equal to `BASE` [nv; precedent 19/19, doc `sz\TOOL-FAULTS.md:193`], then diff the edited run.

**Route 2: generator only.** A tenth zone, a far `room()`, `PAP` moved: about 40 lines, same collision fix, and a Terminus hand-written in the 3,599-line script without picture signs, meshes or fixtures. Dead end.

## C. The trip

**Stock Spaceland** (`STOCK\cp\zombies\zombie_fast_travel.gsc`): `teleport_to_hidden_room` (`:672-688`) sets damage modifier 0 and `is_off_grid`, then `dontinterpolate`, `setorigin` to struct `hidden_room_spot`; a 30 s HUD timer (`:164-195`), then `hidden_room_exit_tube` (`:420-445`) clears both; cooldown 30 + 60 s (`:612-632`). No spawn pause, no zone activation, no downed case (`:694`), nothing for late joiners. Reuse the calls, not the flow.

**Already written:** `SDK\modules\quest.gsc:704-1004`, the bible's trip. Headless on the 19-zone blockout, modules as server custom scripts [doc: `STATION-ZERO-Q1-T1.md:62-66`]: `q1_order_coop` 16/16; `q1_late_round` 7/7 (paused 41 s; zombies alive 10, then 0 after 30 s, 6 after the return). `q1_steps` 37/43: it failed at the Terminus purchase (the fall) and its rerun is not recorded, so **buying at a Pack-a-Punch in the island room has no recorded pass**. Not on this base, never with a real client.

**Nav and zone.** The engine does not require a spawn zone [code read]. Zombie spawners are scored by `level.zombies_spawn_score_func` (`STOCK\cp\zombies\zombies_spawning.gsc:2444-2449`; set in `_id_0d60.gsc:7`, not read [nv]). The wave loops wait on `level.zombies_paused` (`:345`, `:1390`), which stops new spawns. What the zombies alive do is an open choice: a zombie drops an `is_off_grid` enemy (`STOCK\aitypes\zombie\zombie_agent.gsc:234`), and the stuck check kills only a zombie that holds a melee target and does not move (`zombies_spawning.gsc:2783-2890`). The quest module clears the flag after the crossing (`quest.gsc:904`), which fits its measured 10 to 0; stock keeps it for the stay, the likely way to the bible's "zombies wait where they are". One expectation decides: alive at +30 s equals alive at arrival. The volume should stay inactive, because activation publishes its respawn points (`:2464-2516`) [inference]; whether the stock interaction works in a never-activated volume is [nv].

```
init():   T.state = "idle"; T.armed = 0            // armed by the quest, not here
          cab = usable at marker quest_cab; boxes: car 1 (the marker's area), terminus (volume table)
cab_use(): forever: cab waittill( "trigger", p )
          if downed( p ) or !T.armed or T.state != "idle": deny; continue
          level thread trip()
trip():   T.state = "boarding"; chime; wait 4
          riders = players alive in the car box (downed included), not p.iwz_busy
          zombies in the car box: setorigin( getclosestpointonnavmesh( platform side ) )
          if !riders.size: T.state = "idle"; return
          T.state = "crossing"; each rider: iwz_busy = "terminus"; thread cross( arrival + slot, 3 )
          wait 3.2; T.state = "away"; level thread pause_watch()
          wait 40                                   // stock: 30 s, HUD omnvar
          T.state = "returning"
          each player alive in the terminus box: thread cross( car slot, 1 )   // who is there, not the rider list
          wait 1.2; clear iwz_busy and is_off_grid; T.state = "cooldown"; wait 150; T.state = "idle"
cross( dest, s ):
          adddamagemodifier( "iwz_cross", 0 ); is_off_grid = 1; add_white_screen(); wait s
          dontinterpolate(); setvelocity( 0 ); setorigin( playerphysicstrace( dest + 32, dest - 64 ) ); setplayerangles()
          remove_white_screen( 0.4 ); removedamagemodifier
          // open: is_off_grid stays until the return (stock) or is cleared here (quest.gsc)
pause_watch(): while T.state == "away", every 0.5 s:
          want = someone stands, and every standing player is in the terminus box
          level.zombies_paused = want               // only release a pause we set
on game_ended: release the pause, clear is_off_grid and iwz_busy
never:    activate_volume_by_name( "terminus" )
```
A late joiner spawns in the station and the pause drops. Not built anywhere: holding the bleed-out of a downed player left outside.

**Forge proof.** `forge run <plan> --usermap <folder>` (`docs\FORGE.md:38`). Steps (`docs\GAMELAB.md:210-249`): `use` (`ent`, or `kind: weapon_upgrade`; `picked`, `spent`), `call` (library `ops\gamelab\lib\szq.gsc`: volume, paused, alive), `spawn`, `rounds`, `trace` with `hull` (the grid that found the floor fault), `ents`, `expect`; `ui` for the prompt on a joined client. `SDK\sz_q1t1.py` writes the plans only when the layout has `quest_cab` (`:449-455`) and expects volume `platform_east` (`:141`, `:188`, `:215`, `:340`); here it is `platform_a`.

## D. Layer gaps

| Gap | Why [v] | Smallest correct change | Proof |
|---|---|---|---|
| `fx` | `ST\expand.py:239-240`. A base's effects are one file, recipe `fx.place`, patched into the staged script by `SDK\fx\fx_place.py` (`C:\studio\compile\build.py:111-177`) | on emit, write `<emit>\fx.txt` = the base's lines + one row per layer fx; set `fx.place` to `{emit}/fx.txt` (`ST\emit.py:65-89`; root `compile\recipe.py:64-69`); `B.fx` gains `mode`, `stage`, `angles`. About 70 lines | unit test; plan step `fx`; A/B frames |
| Script-model props | `ST\based.py:456-466`: only `smodels.txt` rows | append `script_model` blocks to `ents.txt` through the gameplay merge's parser; `B.prop` gains `targetname`, `noteworthy`; +1 record each (`recipe.py:605`). About 60 lines | unit test; plan step `ents`; measured snapshot |
| Animated things | no route | after the row above: a marked prop and a 15-line module calling `scriptmodelplayanim`; bringing the xanim [nv] | plan step `anim` |
| Power-switched emissive | emission is a material constant (`ST\signs.py:13-16`, `:52-54`); FE52 negative [doc: `TOOL-FAULTS.md:592`] | the switch exists: `iwz_power_fixture` models "zone\|off\|on" swapped with their zone's bank (`SDK\darkness\cp_iwz_darkness.gsc:64-93`, `:170-186`), generator-only (`GEN:3195-3197`). After script-model props, `B.fixture(power=True)` writes it. About 25 lines; unlit twin per kind [nv] | off/on frame pair, `tools\sign_ratio.py` |
| Neon text of ours | no tube geometry writer | a font-outline-to-tube tool feeding the env-model port, then the model pair above. Medium | same |
| Own tiling material | only sign and decal objects write entries (`signs.py:269-272`); the assembler already takes `image` on any base and `ext` colour + normal + gloss on `concrete_01` (`SDK\sz2_assemble.py:67-102`); only `C:\studio\port\emit_custom.py:31` writes `ext` | `B.material(name, colour, normal, gloss, base)` into the same `custom_materials.json` step. About 80 lines | unit test; game frame; `studio pick` |

- **Sign or decal with a normal map: no.** The lit base is "colour image + flat normal" and only semantic 2 is written (`signs.py:13`, `:329-334`).
- **Mesh with our image: only by a trick.** A mesh or an OBJ `usemtl` may name any `w/` material (`expand.py:288-290`, `ST\meshio.py:45-66`), but our pictures exist only as `w/iwz_sg_<hash>`, made when a sign object carries that picture (`signs.py:148-161`): poster base, no normal, tiling [nv]. Glass: stock materials only. Shopfront meshes need `B.material`.

## E. Lighting

Facts [v]: the dark bake holds emergency lights and ambient 0.025 (`SDK\darkness\dark_build.py:55-68`). Every power or flicker light is a named `light_spot` entity, one record each (`recipe.py:561-567`, measured 131 of 131), plus a fill light per power light in four zones (`dark_build.py:134-147`): 167 of r19's 695 (`film\r19_check.json`). They already share one targetname (`iwz_power`), so sharing saves nothing. The dark look is already a per-player manual-exposure vision (`cp_iwz_darkness.gsc:43-47`, `:326-386`), -3 EV (`SDK\darkness\README.md`). The baker separates direct and indirect light (`SDK\bake\lmbake.py:18`, `:425-476`) but has no per-light switch; only `runtime` + `bake: false` leaves a light out (`layout_lights.py:75`).

| Option | Exists | Unknown | Records; official client | First cheap probe |
|---|---|---|---|---|
| (i) bake everything; dark by vision and a few runtime lights | `bake.lights: document`; the dark vision | whether baked light pools read as "power off" at -3 to -5 EV; no bank-by-bank arrival | -167; yes | the experiment already running |
| (ii) hero runtime lights + baked bounce of the lit state | split, banks, `zone_fill` | the bounce is in the lightmap in both states, so the dark vision must hide it; the light grid gets it too | about -130 with 3 or 4 heroes a zone; yes | add `indirect_only` to the baker (about 30 lines), draft bake one zone (18 to 23 s), read it offline |
| (iii) switch without an entity each | stock scriptable light parts: `zm_light_triton`, part `light`, states `off` / `on` (`DUMP\scriptable`); `global_light` (`cp_zmb_environment_scriptable.gsc:39-45`); 214 scriptable records already paid (`recipe.py:575`) | one scriptable for many lights; whether our compiler can author one (it only relocates); the record cost of particle lights; no per-light dvar found [all nv] | unknown; yes if it works | decode the 1,092-byte definition and its instance (offline); a plan playing 50 light effects and reading the snapshot counter |
| (iv) two lightmap sets | three lightmap images per map (`C:\studio\view\renderer.md:37`) | any runtime swap; no script call known [nv] | 0, but needs a client patch: fails the official-client goal | engine xref of the lightmap bind; park |

Direction: (ii) on top of (i)'s vision, sized by (i)'s numbers. The largest part of the budget, 214 template scriptables, is not lights; whether the compiler can drop unused ones is [nv].

## Recommended work packages

1. **Platform, first: far-room collision.** `ST\based.py:400` passes `max_extent`. Closes: unit test (no section wider than 1,024) and a `trace` hull grid on a far floor, every point hit.
2. **SDK: base without PaP.** `GEN`, `TPL`, `sz2_materials.py`, `fixtures\sz2_local.gsc`; server `szaccept.gsc`. First step: unchanged regeneration equals `BASE` 19/19. Closes: file diff; `studio check` on the film document; `ents` shows 0 `iwz_pap_shutter`, 0 `iwz_relay_*`.
3. **SDK script: `modules\terminus.gsc`** (the trip, cut from `quest.gsc`), the hint override, `sz_q1t1.py` zone names. Closes, in this order: `use:pap.spent` = 5,000 in the never-activated volume; zombies alive at +30 s; three headless plans on this base; one real-time joined run with `ui` reading the prompt.
4. **Map: the Terminus layer** (room, zone, `pap` at yaw 270, emergency lights, printed signs). Needs 1 to 3.
5. **Platform, small:** PaP yaw offsets, marker `area` (`ST\build.py`, `blend_core.py:1032-1035`, `:1246-1250`). Off the critical path while the trip reads the Terminus box from the volume table.
6. **Platform, for the Arcade:** script-model props and the power fixture, then `B.material`, then `fx`. `ST\based.py`, `basegame.py`, `build.py`, `signs.py`, `emit.py`.
7. **Lighting:** baker `indirect_only` and a hero rule in `dark_build.py`, after (i) reports.
8. **Probes:** the scriptable light definition; the record cost of particle lights.
