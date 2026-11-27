# B1: the generated base without Pack-a-Punch, the lit-first switch, the trip to the Terminus (27 Nov 2026)

Worker B1, branch `claude/sz-film-b1` of iw7-creator-sdk. Data: `C:\studio-data\sz\film\b1`. Brief: PLAN decision 4 and
TERMINUS-AND-GAPS sections A to C. What is measured is marked **[m]**, what is built but not proven **[b]**.

## 1. Regeneration of the base (proven equal)

The generator environment is `info.generator.env` of `C:\studio-data\sb\base_sb\build.json`, with its roots
(`{sdk}` = the SDK's `tools-source/iwzmap`, `{runtime}` = `Documents\IW7-Runtime`) written out. The dump is
`{runtime}\iwz-map-ref-a\dump\cp_zmb` (`C:\studio\compile\paths.py` `TEMPLATE_DUMP`). The script
`C:\studio-data\sz\film\b1\regen.sh <out> [VAR=value ...]` runs exactly this:

```
SDK=C:/Users/ezvalo/Documents/IW7-Products/worktrees/sdk-film-b1/tools-source/iwzmap
RT=C:/Users/ezvalo/Documents/IW7-Runtime
env IWZ_AUDIO=1 IWZ_DARK=1 IWZ_DARK_ZONE_FILL=1 IWZ_DOUBLE_SIDED=1 \
 IWZ_FX_TXT=$SDK/fx/station_zero_fx_dark.txt IWZ_KIT=1 \
 IWZ_KIT_MATERIAL_MAP=mopw/glass_opaque_02=m/clk_glass_grunge_mild IWZ_LIGHTS=1 IWZ_NAV_OBSTACLES=1 IWZ_P1=1 \
 IWZ_PROBES=neutral IWZ_SMODELS=1 IWZ_STAIR_STYLE=g27 IWZ_TRAIN=1 IWZ_TRAIN_CARS=3 \
 IWZ_TRAIN_CAR_BOXES=$RT/iwz-stage2/train/port/banzai_v5/collision/iwz_t7e_subway_car_a.json \
 IWZ_TRAIN_CONSIST_END_X=1800 IWZ_TRAIN_PROPS=$RT/iwz-stage2/level/props_g27d.json IWZ_TRAIN_SET=g27e \
 IWZ_TRAIN_TRACK_EAST_X=2848 PYTHONHASHSEED=0 \
 python -I $SDK/station_zero2.py $RT/iwz-map-ref-a/dump/cp_zmb <out>
```

4.6 s. **[m]** On `757c219` (the branch start), output `b1\regen0` against `base_sb`, sha256 of every file
(`b1\cmp.py`): **18 of 19 equal**. The generator owns all 19 files of `base_sb` (`build.json` is written by
`sz2_recipe.py` at the end of the same run; the Studio build adds nothing to an emit folder). The one difference,
`build.json`, is `darkness.power = {flag power_on, interaction generator}`, added to `sz2_recipe.py` in `017dd1e`
(26 Nov 22:54), after `base_sb` was written (17:37). No geometry, entity, script or layout byte differs.

## 2. Pack-a-Punch out of the generated base

Removed from `station_zero2.py`: the opening `a_control_pap` and the space `pap_alcove` (room, lintel and reveals,
backing plane, region), the threshold strip, cable trays and switchgear, `sign_pap`, the `PAP` table, the
`weapon_upgrade` struct, the `pap_machine` relocation and the `iwz_pap_spot` struct, the shutter (2 script models
`gate_warehouse_refinery_01`, 4 blocker brushes `*12`, the `pap_shutter` struct, the fixture door row), the three
relays (structs, panel and beacon script models) and the two models parked only for the relay swap
(`icbm_electricpanel9_on`, `beacon_light_plasticcase_red_off`). `sz2_materials.py`: `sign_pap` out of `SIGNS`.
`cp_iwz2.gsc`: the relay precaches and effects, `iwz_pap_quest`, `iwz_pap_gate`, `iwz_open_pap_shutter`,
`iwz_relay_wait`, `iwz_relay_on`, the relay count of the report line (127 lines). Kept: `level.player_pap_machines`,
the `pap` and `upgrade` words of the registry's keep list (the stock `weapon_upgrade` interaction stays registered for
the Terminus section), the camo variables. The control room's north wall is one wall from x 2599 to 3601.

**[m]** `regen0` against `regen1` (stock switch off):

| | regen0 | regen1 |
|---|---|---|
| entities in `ents.txt` | 354 | 334 |
| script_model / script_struct / script_brushmodel | 156 / 150 / 24 | 146 / 144 / 20 |
| `iwz_pap_shutter`, `iwz_relay_*`, `iwz_pap_spot` names | 7, 9, 2 | 0, 0, 0 |
| `weapon_upgrade` struct, `pap_machine` row in `scriptables.txt` | 1, 1 | 0, 0 |
| lights (the PaP hint glow) | 150 | 149 |
| static models (`smodels.txt`, the 4 switchgear panels) | | -4 |
| quads in `surfaces.json` | | -130, +8 (the north wall's two pieces and trims, now whole) |
| nav cells / regions | 10262 | 10222 (-40: `pap_alcove`, `portal:a_control_pap`) |
| collision triangles | 34036 | 33984 |

`iwz_emitcheck diff`: 68 collision triangles and 48 nav cells changed, all in `zone:control_room`; every other zone's
verdict carries. Every removed quad lies in x 2599..3601, y 3988..4161 (the alcove and the north wall).
`iwz_emitcheck check regen1`: 0 errors, the same 18 warnings as `regen0`. Ents lint
(`IW7-Paris-Server\ops\iwzmap\iwzmap_ents_lint.py`, the server's, not in this tree): 0 errors; its finding
`IMPORTANT no Pack-a-Punch (weapon_upgrade) interaction` is what this base is now (the Terminus section adds it).

Still naming the old place, outside B1's files (harmless, for their owners): `fixtures/sz2_local.gsc:619` (a
`pap_shutter` case of the door check, never reached now), `sz2_artlint.py:242`, `sz_interactions.py`,
`blender/blend_core.py`, the server library `ops/gamelab/lib/szaccept.gsc` (`sz_relay`).

## 3. The lit-first switch `IWZ_LIT_FIRST=1`

Every light of `layout.json` goes to the baked group `emergency` and `light_groups` is counted after it
(`station_zero2.py`, before `light_groups`). Default off: **[m]** with it off the emit is byte-equal to the one
without the code (19 of 19). **[m]** With it on, on the PaP-in generator, `layout.json` is byte-equal to the lead's
hand-made `C:\studio-data\sz\film\base_lit` (only `build.json` differs: the recipe now records the variable).

`C:\studio-data\sz\film\b1\base_lit_nopap` = `regen.sh <out> IWZ_LIT_FIRST=1` at the branch head. **[m]**
`b1\litcheck.py`: 149 lights, 0 outside `emergency`, `light_groups` `{emergency 149, power 0, flicker 0}` = the recount.

`b1\doc` is a copy of `film\base\doc` with `map.json` base path `b1\base_lit_nopap`, name `sz_b1_nopap`, and all
134 lights of `layers\lights.json` `group: emergency`. Studio must read this SDK, not the main checkout:
`STUDIO_CONFIG=C:/studio-data/sz/film/b1/studio_b1.json` (key `sdk`) and `IWZ_SDK=<this worktree>`.
**[m]** `studio check b1\doc`: `ok: true`, `build.networked_entities.total` **484** (lit-first with Pack-a-Punch:
501, `film\allbaked2\check.json`). The 17: script_model -10 (6 relay panels and beacons, 2 shutter gates, 2 parked
relay models), script_brushmodel -4 (shutter blockers), gameplay_spawn -3 (the relays' use entities). The Studio
emit (`b1\doc_emit`) rebuilds `modules/` and keeps the cab row with its box.

## 4. The trip: `tools-source/iwzmap/modules/terminus.gsc`

Cut from `modules/quest.gsc:704-1004`, reworked after TERMINUS-AND-GAPS C. State in `level.iwz_terminus`
(`state` init / no_terminus / unarmed / idle / boarding / crossing / away / returning / cooldown; `visits`, `riders`,
`returned`, `pushed_out`, `paused`, `pause_seconds`, `refused`, `events`); every change prints
`[IWZ level] TERMINUS ...`.

- Places from the marker table: `quest_cab` (origin, yaw, and `lo`, `hi` = car 1's box) and `terminus_arrival`
  (origin, yaw, `lo`, `hi` = the Terminus box). If either is missing or has no box: `state = no_terminus`, **one** log
  line `TERMINUS IDLE cab=.. terminus=..`, no cab entity, nothing else runs.
- **`terminus_armed()`** is the hook: version 1 returns the `power_on` flag. The four-clock quest of the bible
  (04-PAP-QUEST section 2) replaces this one function.
- The cab: a `tag_origin` usable 48 above the marker. Refusals (downed, not armed, not idle) play the deny sound
  and log `REFUSED why=..`.
- The trip: 4 s boarding (two ticks); riders = players alive in the car box, downed included, not `iwz_busy`;
  zombies in the car box `setorigin` to the nearest nav point 70 beyond the box's platform side; nobody aboard ->
  idle; riders `iwz_busy = "terminus"`, 3 s crossing (white screen, portal sound, shake), arrival slots 48 apart
  across the Terminus marker; 40 s away; return of every player alive in the Terminus box (not the rider list) to
  aisle slots of car 1 (x = box x0 + 80 + 110 k, the box's middle y); 150 s cooldown; idle.
- Protections: no damage and `is_off_grid` from the start of the crossing out **until the return** (as the stock
  hidden room, `zombie_fast_travel.gsc:672-688`; `zombies_spawning.gsc` `_id_FF55` and `zombie_agent.gsc:234` drop
  an off-grid player as a target, so the zombies of a player left outside do not chase the unreachable one).
- The pause: every 0.5 s while away, `level.zombies_paused = 1` when someone stands and every standing player is in
  the Terminus box; only a pause this module set is released (when that stops being true, at the return, at
  `game_ended`). A late joiner spawns in the station, stands outside, the pause drops.
- `game_ended`: our pause released, `is_off_grid`, `iwz_busy` and the damage modifier cleared.
- Never `activate_volume_by_name` on the Terminus volume (the module calls nothing of the spawning).
- Not built: holding a downed outside player's bleed-out while the others are away (bible, section 3).

The generator declares `quest_cab` (`station_zero2.py`, after the Capsule Post block): car 1 = `train_spec.cars[0]`,
the westmost car at platform A, origin (465.5, 1488); marker at (265.5, 1488, -323.01), yaw 180 (24 inside the west
end bulkhead, on the aisle); area = the car's nav-cut half extents, floor -24 .. floor +150:
(197.5, 1421.5, -347.01) .. (733.5, 1554.5, -173.01). `IWZ_TERMINUS=0` leaves marker and module out.
`layout['modules']` is `['post', 'terminus']`; the level script starts both (`//@POST@` takes every module's call);
the generator emits only the listed modules and removes a stale file of one switched off.
**[m]** `iwz_emitcheck at`: the cab point, the four return slots (x 277.5, 387.5, 497.5, 607.5, y 1488) on the car
floor -320.4, on the nav (offset 0); the put-out point (400, 1624, -320) on the platform floor.

`sz_modules.py`: a module whose first line is `// sz_modules: opt-in` is written only when a map names it
(`only=`); a bare `emit` (the 19-zone `scenegen` line) leaves it out, so that scene keeps its one trip in
`quest.gsc` and `test_sz_q1t1` still sees `cap, post, quest`.

## 5. The weapon upgrade prompt

`cp_iwz2.gsc` `iwz_register_interactions`, after the stock registry and the perks:
`level.interactions["weapon_upgrade"].hint_func = ::iwz_weapon_upgrade_hint` and
`level.interaction_hintstrings["weapon_upgrade"]`. The function is the stock `weapon_upgrade_hint_logic`
(`interaction_weapon_upgrade.gsc:44-64`) with the two upgrade strings swapped; the refusals keep the stock strings
(`COOP_INTERACTIONS_UPGRADE_MAXED`, `CP_ZMB_INTERACTIONS_UPGRADE_WEAPON_FAIL`, "" for melee and phase shift). The stock
code fills `&&1` (weapon) and `&&2` (cost), `cp_interaction.gsc:859-874`. The two refusal lines the cp_zmb monitor
shows itself (`cp_zmb_interactions.gsc:504-556`) are stock and not covered.

PLACEHOLDER COPY, for the copy writer (in `perks/strings.json`, the file the build's `add_localize` reads):

| Key | Text |
|---|---|
| `IWZ_INTERACTIONS_VALIDATE_WEAPON` | `Hold ^3[{+activate}]^7 to validate your &&1 [Cost: &&2]` |
| `IWZ_INTERACTIONS_VALIDATE_WEAPON_AGAIN` | `Hold ^3[{+activate}]^7 to validate again your &&1 [Cost: &&2]` |

The cab's prompts in `modules/terminus.gsc` (plain strings, marked PLACEHOLDER COPY there): before power the stock
`COOP_INTERACTIONS_REQUIRES_POWER`; idle `Press ^3[{+activate}]^7 to depart for the Terminus`; `BOARDING`;
`NOT IN SERVICE`. Whether a plain (not localized) hint string shows on a real client is not proven.

## 6. Proof

**[m]** Forge's GSC VM (`C:\forge\gscvm`, virtual time): `tools-source/iwzmap/tests/test_terminus.py`, 5 tests in
about 0.05 s, emitting the module through `sz_modules.emit` as the generator does: idle without the Terminus marker
(one line, no cab, no error); refused before power and when downed; the full trip (2 riders of whom one downed, a
third player outside, a zombie in the car put out, protections during the stay, no pause while one stands outside,
pause when all stand in the Terminus, released when one stands outside again, return of both into car 1 with
protections off, cooldown refusal, idle after 150 s); a pause of another system never released and taken only once
it is free; game end mid-visit; nobody aboard. The hint function on the template: the five branches.

In the game: **not proven yet (paused 27 Nov by the owner).** Built: `studio live start b1\doc` (rc 0, 164 s,
draft bake 67 s), usermap `C:\studio-data\live\doc-85084890\cp_iwz`; the zone carries both modules
(`rawfile,scripts/cp/maps/cp_iwz/cp_iwz_terminus.gsc`) and the two `IWZ_INTERACTIONS_VALIDATE_*` strings
(`zonetool\cp_iwz\localizedstrings\cp_iwz.json`). The session was stopped. The batch
`C:\studio-data\sz\film\b1\plans\batch_b1.json` (b1_terminus, sz8_doors, sz8_power_perks, sz8_rounds on that usermap,
library dir `b1\plans\lib` with `szterm.gsc`) was stopped before any run reported. `sz8_power_perks` needed no
change: it has no Pack-a-Punch expectation.

**Resume:** `cd C:\studio-data\sz\film\b1\plans && python -B C:\forge\forge.py batch batch_b1.json` (background).
If the usermap folder has been swept, first rebuild it with `studio live start b1\doc` (env: `STUDIO_CONFIG`,
`IWZ_SDK`, `IWZ_ZONETOOL_EXE`, section 3), then `live stop` again once the plans have run.

## Not done here (for the next packages)

- The Terminus room, its zone, the machine (`pap` object) and the `terminus_arrival` marker: the Terminus section.
  Studio markers carry no `area` today (TERMINUS-AND-GAPS B, package 3): until they do, the section's marker reaches the
  module without a box and the module stays idle.
- `sz_q1t1.py` still writes its Q1 plans only for the 19-zone line (`quest_cab` + volume `platform_east`); a trip plan
  on this base comes with the Terminus section.
