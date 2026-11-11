# E. Zombies in Spaceland (cp_zmb): measured numbers, the scale and convention bar

Read-only research, 2026-11-11. Nothing was launched, built, committed or changed in a repository or data file. All
databases were opened read-only; every script lives in a temp folder, copies of the ones used are in
`E-scripts/` next to this file (they hold absolute paths to the temp folder, run them only to re-measure).

The purpose is to match scale and conventions of a shipped map, not to copy content. 1 unit = 1 inch = 0.0254 m.

## 0. Sources, tools, and what they can and cannot say

| Short name | What it is |
| --- | --- |
| `DB` | `<runtime>/worldkit\cp_zmb.sqlite` (built by the world kit from the map dump `iwz-map-ref-a\dump\cp_zmb`, reader 1.0.0, built 2026-11-10). |
| `iw7_world.py`, `iw7_dump.py` | Extracted with `git show` from `origin/main` of iw7-creator-sdk (commit `7b9e7941a82989884b530e6685b84cfba62dbbab`, files `tools-source/worldkit/iw7_world.py` and `iw7_dump.py`) into `<temp>/wk\`. Command prefix used below: `python -B iw7_world.py <cmd> --db DB`. |
| `volume_check.py`, `hkpack.py` | Same repository and commit, `tools-source/iwzmap/`. It reads the Havok box shapes of the volumes from `maps/cp/cp_zmb.d3dbsp.ents.data(.hkx)`. Command: `python -I volume_check.py <dump>\cp_zmb\maps\cp cp_zmb --json vol.json`. This is the only way to get the real size of a spawn volume: the world kit database holds gfx brush models only. |
| `$GSC/` | `<server>/tools\iw7-gsc-dump\decompiled\scripts\`. The readable decompile (gsc-tool 1.5.1) of the retail scripts with names resolved. All `file:line` references below are relative to this folder. |
| `PATCH/` | `<runtime>/iwz-map-ref-a\dump\patch_cp_zmb\` (the tables: `cp\cp_weapontable.csv`, `mp\default_agent_definition.csv`, `cp\zombies\cp_zmb_loot.csv`, `scripts\cp\maps\cp_zmb\cp_zmb_crafting.csv`). |
| `WEAP/` | `...\iwz-map-ref-a\dump\cp_zmb\weapons\*.json` (140 weapon assets of the map zone). |
| `LOC` | `<runtime>/iw7-dump-lui\localize.json` (player-facing strings with the prices). |

Important about the scripts. The scripts in `iwz-map-ref-a\dump\cp_zmb\scripts` are compiled `.gscbin` files (zlib plus
bytecode), not text, and gsc-tool could not be fed them in the time available (the `.cgsc`/`.stack` split was not
solved: "couldn't resolve opcode enum"). The readable source is therefore `$GSC/`. How far it can be trusted:

* `$GSC/cp/maps/cp_zmb/cp_zmb.gsc` was compared with a decompile of the shipped patch file
  (`IW7-Runtime\afterlife\decomp\decompiled\iw7\cp_zmb.gsc`, decompiled from a `cp_zmb.gscbin` of 29307 bytes, the same
  size as `PATCH/scripts/cp/maps/cp_zmb/cp_zmb.gscbin`, base zone file is 28096 bytes): identical after
  `diff --strip-trailing-cr` except two lines where only the name resolution differs. So `$GSC` is at patch level for
  that file.
* The patch zone overrides these scripts: gametypes/zombie, cp_zmb, cp_zmb_dj, cp_zmb_ghost_activation,
  cp_zmb_ghost_wave, cp_zmb_interactions (+14 bytes of bytecode against base), cp_zmb_ufo, cp_zmb_vo,
  cp_zmb_player_character_setup, direct_boss_fight, directors_cut, contracts. For those, only `cp_zmb.gsc` was
  byte-verified. Everything the round, health, damage and perk numbers below come from (zombies_spawning,
  zombie_agent, gametype_zombie, perks, loot, laststand) is NOT in the patch zone, so it is the shipped code. Costs of
  perks and wall guns were cross-checked with `LOC` and `cp_weapontable.csv`.
* Variable names in the decompile are still partly `_id_XXXX`. Where a name is unresolved the function name is given
  with its line.

Method conventions: "zone" = one of the 14 `spawn_volume` entities (see section 2). A prop or light is counted in the
smallest zone volume that contains its position ("exclusive"), the volumes overlap.

## 1. Whole-map statistics

Command: `python -B iw7_world.py stats --db DB --limit 25`

| Quantity | Value | Where from |
| --- | --- | --- |
| World surfaces | 10,760 | stats (read = file header = ground truth) |
| Static models (props) | 17,010 | stats |
| Distinct models | 916 | stats |
| Primary lights | 1,039 | stats (spot 893, omni 142, dir 3, none 1; shadow-map capable 459; volumetric 585): `select type_name,count(*),sum(canUseShadowMap),sum(isVolumetric) from lights group by 1` |
| Reflection probes | 160 | stats |
| Brush models | 94 | stats |
| Triangles / vertices / indices | 403,042 / 514,927 / 1,209,126 | stats |
| Entities | 3,695 | stats |
| Umbra gates | 27 (+64 in tome 2) | `meta.gfx_header` |
| Dump files | gfxmap 100,110,337 B, transient zone 24,906,133 B, ents text 449,830 B, ents.data 1,163,862 B, colmap.hkx 14,227,360 B, navmesh 653,342 B, aipaths 107,449 B | `select value from meta where key='files'` |
| Props bounding box (all, includes the vista) | x -23707..15131, y -19788..17965, z -1928..1888 | stats |
| Surfaces bounding box (all, includes terrain vista) | x -34736..41104, y -46688..40128, z -6416..10944 | stats |
| Most placed props | cookies 326, machinery_bulkhead_attachment_01 284, theater chair spacer 284, baseball cap 278, square_hook 276, vista tree 261 | stats |

### Playable area (my measurement, not a stock number)

The stock map has no "playable box" entity. The best definition is the union of the 13 gameplay spawn volumes (the
14th, `hidden_room`, is the Pack-a-Punch room at x=-10224).

* Union of the 13 volumes, axis-aligned: **x -3272 .. 4951.75, y -3568 .. 3824, z -264 .. 792**, that is
  **8,224 x 7,392 units = 208.9 m x 187.8 m**, height up to 1,056 units (26.8 m). Script cross-check: the minimap is set
  to +/-3072 (`cp/maps/cp_zmb/cp_zmb.gsc:121`, `setminimap( "", 3072, 3072, -3072, -3072 )`).
* Footprint, union of the 13 volume rectangles rasterised at 16 units: **43,099,136 sq units = 27,806 m2** (2.78 ha).
  The plain sum of the 13 volume areas is 61.25 M sq units = 39,517 m2 (volumes overlap: moon, underground_route,
  moon_bumpercars, europa_tunnel, mars).
* Real floor is smaller than the footprint but is not decoded here (navmesh is not readable by the world kit). Two
  bounds, from up-facing world-surface samples inside the volumes (script `floor3.py`, 32-unit cells,
  `vertex normal z > 0.7`, excluding caulk/clip/sky/trigger materials): cells with at least one up-facing surface
  30,463 m2 summed over zones; counting separate vertical levels in a cell (gap > 96 units) 40,008 m2. These include
  roofs and counter tops, so call the **walkable floor roughly 15,000 to 25,000 m2** only as an informed guess; the
  hard facts are the footprint and the table in section 2.
* Everything inside the 13 volumes: props 12,372 (hidden room adds 200, 4,438 props lie outside all volumes: vista,
  skyline, planets), lights 830 (+5), triangles 315,485 (+407), 813 distinct models used in volumes.
  Command for the axis-aligned box over the playable AABB (a bit larger than the union):
  `python -B iw7_world.py box -3272 -3568 -264 4952 3824 792 --db DB --limit 0` returns props 13,897, lights 887,
  entities 2,538, surfaces touching 9,670, triangles inside 348,100.
* `python -B iw7_world.py rooms --db DB --cell 512` : 1,861 non-empty 512-unit cells; densest cell (x 1024, y 0)
  has 460 props, 5 lights, 2,649 triangles.

### Entity counts by classname

Query: `select classname,count(*) from ents group by 1 order by 2 desc`

| classname | count | classname | count |
| --- | --- | --- | --- |
| script_struct | 2,796 | trigger_hurt | 1 |
| script_struct_mini | 134 | script_origin | 12 |
| info_vehicle_node | 124 | audio_pa_speaker | 7 |
| script_model | 115 | node_jump | 3 |
| node_negotiation_begin / _end | 110 / 110 | worldspawn, physicsbroadphase, mp_global_intermission | 1 each |
| script_brushmodel | 92 | trigger_damage | 13 |
| info_volume | 64 | client_trigger_occluder_audio | 22 |
| trigger_multiple | 36 | light_spot (entity lights) | 25 |
| trigger_use | 28 | | |

The 2,796 structs are by far the biggest group: they are the gameplay data (interactions 295, ghost_spawn 172,
effect_loc 118, dog_spawner 114, delete_on_load 107, hidden_song_toy 54, ufo_zombie_spawn_loc 52, player_respawn_loc 51,
...). Top targetnames: `select classname,targetname,count(*) from ents group by 1,2 order by 3 desc`.

## 2. Zones (the gameplay areas)

### 2.1 The list

The zones are the 14 `info_volume` entities with targetname `spawn_volume` (`cp/zombies/zombies_spawning.gsc:89`,
`level.spawn_volume_array = getentarray( "spawn_volume", "targetname" )`). The zone name is the volume's
`script_linkname` with the `pf7_` prefix stripped (`_id_7859`, line 160). Start zone: `front_gate`
(`cp/maps/cp_zmb/cp_zmb.gsc:568`, `level.initial_active_volumes = [ "front_gate" ]`). Other `info_volume` entities
(64 in all): 33 `*_despawn_volume` mini zones (script_noteworthy `mini_zone`), `invalid_playspace`,
`power_exclusion_volume`, `no_pain_volume`, grenade/trap volumes, dance floor, astrocade tiles.

Sizes come from `volume_check.py` (Havok box shape extents) with the centre from the `ents` table; all 14 spawn volumes
have no rotation. Props and lights are exclusive assignments (smallest containing volume). Triangles are world-surface
triangles whose centroid lies in the volume. Spawners are the structs whose targetname equals the volume's `target`
(`_id_7CE3`, line 934). Goon locations are `dog_spawner` structs inside the volume (clown and brute spawn points,
`_id_9608`, line 821). Scripts: `analyze.py`, `mkzone.py`, `tri.py`.

| zone | box W x D x H (units) | box W x D (m) | footprint m2 | props | lights | tris | zombie spawners | goon locs | windows | respawn locs |
|---|---|---|---|---|---|---|---|---|---|---|
| front_gate (start) | 1000 x 976 x 248 | 25.4 x 24.8 | 630 | 399 | 27 | 8,241 | 12 | 5 | 1 | 4 |
| moon (central hub) | 1448 x 4392 x 776 | 36.8 x 111.6 | 4,103 | 2,189 | 108 | 35,924 | 25 | 15 | 3 | 6 |
| moon_outside_begin | 1676 x 3704 x 640 | 42.6 x 94.1 | 4,005 | 1,459 | 95 | 46,854 | 26 | 7 | 1 | 3 |
| moon_rocket_space | 1784 x 2344 x 640 | 45.3 x 59.5 | 2,698 | 673 | 79 | 36,989 | 14 | 10 | 2 | 4 |
| moon_bumpercars | 1671 x 2900 x 640 | 42.5 x 73.7 | 3,127 | 711 | 42 | 29,409 | 13 | 10 | 2 | 2 |
| arcade | 2104 x 1586 x 472 | 53.4 x 40.3 | 2,153 | 1,024 | 56 | 18,708 | 11 | 7 | 3 | 6 |
| arcade_back | 1968 x 1264 x 666 | 50.0 x 32.1 | 1,605 | 522 | 26 | 16,164 | 6 | 4 | 0 | 2 |
| europa_2 | 1520 x 1552 x 376 | 38.6 x 39.4 | 1,522 | 473 | 75 | 20,715 | 5 | 8 | 2 | 5 |
| europa_tunnel | 2640 x 2384 x 744 | 67.1 x 60.6 | 4,060 | 962 | 53 | 28,152 | 12 | 8 | 0 | 2 |
| swamp_stage | 2080 x 2080 x 312 | 52.8 x 52.8 | 2,791 | 887 | 75 | 23,648 | 19 | 10 | 0 | 5 |
| underground_route | 5216 x 2144 x 608 | 132.5 x 54.5 | 7,215 | 1,002 | 39 | 18,035 | 12 | 8 | 0 | 4 |
| mars | 3192 x 1938 x 640 | 81.1 x 49.2 | 3,991 | 999 | 79 | 17,010 | 30 | 13 | 4 | 2 |
| mars_3 | 2008 x 1248 x 816 | 51.0 x 31.7 | 1,617 | 1,072 | 76 | 15,636 | 12 | 8 | 4 | 6 |
| hidden_room (PaP) | 392 x 406 x 144 | 10.0 x 10.3 | 103 | 200 | 5 | 407 | 0 | 0 | 0 | 0 |
| **13 playable zones, total** | | | | 12,372 | 830 | 315,485 | 197 | 113 total over all | | |

Windows are the 27 `window_entrance` structs; 5 of them are outside every volume (counted in no row). Zone for the
zombie spawners of each volume: `moon_outside_begin` target `pf7_auto154`, `moon` -> `moon_spawner`, `front_gate` ->
`front_gate_spawner`, `arcade_back` -> `arcade_back_spawn`, `moon_bumpercars` -> `moon_bumpercars_spawn`,
`moon_rocket_space` -> `moon_rocket_space_spawn`, `europa_2` -> `europa_2_spawn`, `swamp_stage` -> `swamp_stage_spawn`,
`arcade` -> `arcade_spawn`, `underground_route` -> `underground_route_spawn`, `europa_tunnel` -> `europa_tunnel_spawn`,
`mars` -> `mars_spawn`, `mars_3` -> `mars_3_spawn`. Note that about half of the spawners are placed OUTSIDE their own
volume on purpose (volume_check reports e.g. moon_outside_begin 13 of 26 inside, front_gate 0 of 12: window and gate
spawners).

### 2.2 Distribution over the 13 playable zones (hidden room excluded)

| Measure | min | median | max |
|---|---|---|---|
| Volume footprint (m2) | 630 (front_gate) | 2,791 (swamp_stage) | 7,215 (underground_route) |
| Volume footprint (million sq units) | 0.98 | 4.33 | 11.18 |
| Longest side (m) | 25.4 | 59.5 | 132.5 |
| Props per zone | 399 | 962 | 2,189 |
| Lights per zone | 26 | 75 | 108 |
| Zombie spawners per zone | 5 | 12 | 30 |
| Props per 1000 sq units of volume | 0.090 | 0.205 | 0.428 |
| Props per 100 m2 of volume | 13.9 | 31.8 | 66.3 |
| Lights per 100 m2 of volume | 0.54 | 2.60 | 4.93 |
| Lights per 1000 sq units of volume | 0.0035 | 0.0168 | 0.0318 |
| Surface-covered floor (m2, from samples) | 599 | 2,118 | 5,312 |
| Props per 100 m2 of that floor | 24.0 | 44.5 | 76.0 |
| Lights per 100 m2 of that floor | 1.53 | 2.64 | 6.81 |

Per zone density (props / 1000 sq units of volume | props per 100 m2 of volume | lights per 100 m2 of volume):
front_gate 0.409 | 63.4 | 4.29; mars_3 0.428 | 66.3 | 4.70; moon 0.344 | 53.4 | 2.63; arcade 0.307 | 47.6 | 2.60;
moon_outside_begin 0.235 | 36.4 | 2.37; arcade_back 0.210 | 32.5 | 1.62; swamp_stage 0.205 | 31.8 | 2.69;
europa_2 0.201 | 31.1 | 4.93; mars 0.161 | 25.0 | 1.98; moon_rocket_space 0.161 | 24.9 | 2.93; europa_tunnel 0.153 | 23.7 | 1.31;
moon_bumpercars 0.147 | 22.7 | 1.34; underground_route 0.090 | 13.9 | 0.54. Rule of thumb for a custom map: a normal
combat room of 1,500 to 4,000 m2 volume carries 500 to 1,500 props and 40 to 110 lights; a dense "set piece" room
(front gate, mars_3) is about 60 props per 100 m2.

### 2.3 Adjacency (who connects to whom, what it costs)

Adjacency is built at runtime from the door structs: `set_adjacent_volume_from_door_struct`
(`cp/zombies/zombies_spawning.gsc:2359`) pairs two door structs that share the same `target` and have different
`script_area`; `_id_94D5` (line 2339) collects all interaction structs that have a `script_area`. `level.use_adjacent_volumes = 1`
(`cp/maps/cp_zmb/cp_zmb.gsc:20`). Exception coded: `level._id_C50A["mars_3"]["swamp_stage"] = 1` (line 2346) makes
mars_3 and swamp_stage NOT adjacent for spawning although a door joins them. No zone is adjacent to the start zone
without a purchase except by the 750 gate. Edges (cost in points; `xP` = 1000 per player count, see 3.2):

```
front_gate        - moon              750
moon              - moon_outside_begin team door "moon"   1000xP
moon              - mars              team door "kepler"  1000xP
moon              - europa_tunnel     team door "triton"  1000xP
moon_outside_begin- underground_route 1000
moon_outside_begin- arcade            1250
moon_outside_begin- moon_rocket_space 1500
moon_rocket_space - moon_bumpercars   1250
moon_bumpercars   - arcade            1250
moon_bumpercars   - underground_route 1250
arcade            - arcade_back       1500
arcade_back       - europa_2          1500
europa_2          - europa_tunnel     1250
europa_tunnel     - swamp_stage       1500
underground_route - swamp_stage       1250
mars              - mars_3            1250
mars_3            - swamp_stage       1500 (door exists, spawn adjacency excluded)
hidden_room       - PaP portal only
```

Counting only door/team-door edges, the map is a loop with the hub `moon`: 13 zones, 17 edges (14 debris + 3 team
doors). Cheapest way to open every zone (minimum spanning tree, Kruskal over these edges): 13,750 (1 player),
15,750 (2), 16,750 (3), 17,750 (4).

## 3. Doors and debris

### 3.1 Debris doors

Registered in `cp/maps/cp_zmb/cp_zmb_interactions.gsc:128-134`:
`register_interaction( "debris_1250", "door_buy", 1, undefined, interaction_openareas::clear_debris, 1250 )` and the
same for 350, 750, 1000, 1500, 2000, 2500 (350, 2000, 2500 are registered but unused on this map). The cost is the
number in the struct's `script_noteworthy`. Both sides of a door have an interaction struct with the same `target`;
buying one disables all with the same target (`disable_linked_interactions`, `cp/cp_interaction.gsc:2078`) and
`clear_debris` (`cp/zombies/interaction_openareas.gsc:221`) activates the zone on the other side. Query:
`select ... from ents e join ent_kv k on k.i=e.i and k.key_name='script_noteworthy' where e.targetname='interaction' and k.value like 'debris_%'`
(script `q5.py`). 34 interaction structs = **14 distinct purchases**; 19 `trigger_use` entities with targetname `door_buy`
are the use triggers (`q3.py`).

| door target | cost | zone A <-> zone B | structs |
|---|---|---|---|
| pf7_auto6 | 750 | front_gate <-> moon | 4 (two gates side by side, one target) |
| pf7_auto209 | 1000 | moon_outside_begin <-> underground_route | 2 |
| pf7_auto243 | 1250 | moon_rocket_space <-> moon_bumpercars | 2 |
| pf7_auto151 | 1250 | moon_outside_begin <-> arcade | 2 |
| pf7_auto198 | 1250 | europa_2 <-> europa_tunnel | 4 (two locations, one target) |
| pf7_auto178 | 1250 | mars <-> mars_3 | 4 (two locations, one target) |
| pf7_auto213 | 1250 | arcade <-> moon_bumpercars | 2 |
| pf7_auto210 | 1250 | underground_route <-> moon_bumpercars | 2 |
| pf7_auto211 | 1250 | underground_route <-> swamp_stage | 2 |
| pf7_auto189 | 1500 | europa_tunnel <-> swamp_stage | 2 |
| pf7_auto237 | 1500 | arcade <-> arcade_back | 2 |
| pf7_auto238 | 1500 | arcade_back <-> europa_2 | 2 |
| pf7_auto160 | 1500 | moon_rocket_space <-> moon_outside_begin | 2 |
| pf7_auto182 | 1500 | mars_3 <-> swamp_stage | 2 |

Count by price: 750 x1, 1000 x1, 1250 x7, 1500 x5. **Sum of debris = 18,000.**

### 3.2 Team doors (3)

`team_door_switch` structs (6, two per door), registered with cost 1000 (`cp_zmb_interactions.gsc:135`,
`use_team_door_switch`, `cp/zombies/interaction_openareas.gsc:59`). Each press donates 1000 and the door opens when
the counter reaches 3, but `post_nondeterministic_func` (`cp/maps/cp_zmb/cp_zmb.gsc:2508-2564`) pre-sets the counter by
player count: 1 player starts at 2 (one donation), 2 players at 1, 3 players at 0, 4 players at -1 (four donations).
So **each team door costs 1000 x number of players**. Doors: `moon` (target pf7_auto229, moon_outside_begin <-> moon),
`kepler` (pf7_auto226, moon <-> mars), `triton` (pf7_auto167, europa_tunnel <-> moon). Opening two of them
also sets `canFiresale` (interaction_openareas.gsc:111-116).

### 3.3 Total

* Debris 18,000 + team doors 3 x 1000 x players = **21,000 (solo), 24,000 (2p), 27,000 (3p), 30,000 (4p)**
  to open every door of the map (all 13 zones).
* Other gates not paid with points: generators (free interaction, 5 of them), 3 `dj_quest_door` (DJ quest), two
  `first_gate_bollard` (front gate bollards, `bollard_trigger` use triggers), the PaP portal chain (see 4.4).

## 4. Perks, weapons, box, Pack-a-Punch, power, traps, portals, activities

### 4.1 Perk machines (10 on this map, all need the power of their area)

Cost function `get_perk_machine_cost` (`cp/cp_interaction.gsc:394`), names and prices confirmed by `LOC`
(`COOP_PERK_MACHINES_*`). "perks:NNN" below means `cp/zombies/zombies_perk_machines.gsc:NNN`. The machine counts come from `select ... where script_noteworthy like 'perk_machine%'` (one
struct each). Registration: `cp/zombies/zombies_perk_machines.gsc:18-29`.

| internal name | in-game name | zone | cost | effect (script) |
|---|---|---|---|---|
| perk_machine_revive | Up N' Atoms | front_gate | 1,500 (**500 solo**, `cp_interaction.gsc:363-365`) | Solo: one self-revive (`give_revive_perk`, perks:797). Co-op: `revive_time_scalar = 2.0`. |
| perk_machine_tough | Tuff Nuff | moon_rocket_space | 2,500 | `max_health = 200` (`zombies_perk_machines.gsc:777-784`); 100 without (`cp/cp_globallogic.gsc:186-197`). |
| perk_machine_flash | Quickies | europa_2 | 3,000 | `specialty_fastreload` + `specialty_quickswap` (perks:1073). |
| perk_machine_more | Mule Munchies | moon_outside_begin | 2,000 | an extra weapon slot (the over-limit gun gets a mule icon), `pistol_overkill = 1` (perks:1087-1121). |
| perk_machine_rat_a_tat | Bang Bangs | swamp_stage | 2,000 | swaps guns to their `doubletap` variants; `bullet_damage_scalar = 2.0` gives x1.33 bullet damage (`gametype_zombie.gsc:412-413`) (perks:1175). |
| perk_machine_run | Racin' Stripes | moon | 2,000 | `specialty_longersprint`, `specialty_sprintfire`, suit `zom_suit_sprint` (perks:1331). |
| perk_machine_fwoosh | Trail Blazers | arcade | 1,500 | fire wave of radius 300 on sprint-slide, retrigger on energy replenished or 5 s (perks:1356-1377). |
| perk_machine_smack | Slappy Taffy | mars_3 | 2,000 | melee +1,500 damage (`gametype_zombie.gsc:351`) (perks:1379). |
| perk_machine_zap | Blue Bolts | moon_bumpercars | 1,500 | on reload, zap ring: damage `max(1045 x emptiness, 10)`, radius `max(128 x emptiness, 48)`; (emptiness = missing share of the clip); at most 4 consecutive reload zaps, the counter resets 3.25 s after the last one, the 5th gives no ring (perks:1409-1475). |
| perk_machine_boom | Bombstoppers | mars | 1,500 | explosive damage x2 (`gametype_zombie.gsc:384`) (perks:1399). |

All ten together: 19,500 (solo 18,500). Perk limit: a player may hold **5 perks** (`zombies_perks.size > 4` blocks,
`cp/cp_interaction.gsc:2056`), unless `have_permanent_perks`. Two more machine types are registered but not placed here
(`perk_machine_deadeye` 1500, `perk_machine_change` 1500). Perk-machine positions: `inter.py` output
(front_gate (258,3620), moon (1122,-640,-165 under the hub), moon_outside_begin (2614,1548), moon_rocket_space
(4428,2736), moon_bumpercars (3960,-1508), arcade (2140,-1864), europa_2 (-351,-3014), swamp_stage (-2632,-1486),
mars (-2624,1448), mars_3 (-2640,210)).

### 4.2 Wall weapons (20 structs, 10 distinct guns)

Registered in `cp_zmb_interactions.gsc:140-160` (`"wall_buy"`, plus two power wall buys at 161-162 not placed here); the model/attachment suffix after `+` is stripped
(`cp/zombies/coop_wall_buys.gsc:230`), so `iw7_erad_zm+eradscope` is the 1,250 erad. Count and zone from the structs
(`inter.py`). Buying a gun you already hold refills ammo for half price; a Pack-a-Punched gun refills for 4,500
(`get_interaction_cost`, `cp/cp_interaction.gsc:322-340`).

| gun | cost | structs | zones |
|---|---|---|---|
| iw7_m1c_zm | 500 | 3 | front_gate x3 |
| iw7_revolver_zm | 500 | 3 | front_gate x3 |
| iw7_sonic_zmr | 750 | 2 | underground_route, moon |
| iw7_nrg_zm | 750 | 1 | moon |
| iw7_ump45_zml | 1,250 | 3 | europa_2, mars_3, underground_route |
| iw7_erad_zm (+eradscope) | 1,250 | 2 | moon_outside_begin, mars |
| iw7_crb_zml | 1,250 | 1 | moon_bumpercars |
| iw7_ripper_zmr | 1,250 | 1 | europa_2 |
| iw7_ake_zml | 1,500 | 3 | moon_rocket_space, europa_2, swamp_stage |
| iw7_m4_zm | 1,500 | 1 | arcade |

Other registered wall costs not placed on this map: m8 1000, cheytac 1000, m1 500, spas 1250, kbs 1250, ar57 1500,
fmg 1500. Ticket purchases (cost in tickets, arcade zone): cryo grenade `zfreeze_semtex_mp` 350, Forgefreeze
`iw7_forgefreeze_zm` 500. The wall table is `PATCH/cp/cp_weapontable.csv` (53 weapons: 37 `magic`, 10 `wall`, 1 `tickets`).
Starting weapon `iw7_g18_zmr` (`cp/gametypes/zombie.gsc:73`), starting points 500 (`cp/cp_persistence.gsc get_starting_currency`).

### 4.3 Mystery box (the "magic wheel")

* **9 locations**: 9 `spinner` structs, 9 `wheel_fx_spot` structs and 9 `out_of_order` brush models (query
  `select ... where targetname='wheel_fx_spot'`). Zones: arcade, moon_outside_begin, swamp_stage x2, europa_2,
  arcade_back, mars, moon_bumpercars, moon_rocket_space. The wheel entities themselves (`getentarray( "magic_wheel",
  "script_noteworthy" )`, `cp/zombies/interaction_magicwheel.gsc:20`) are scriptable instances, not text entities, so
  they are not in the `ents` table.
* Only one wheel is active at a time (`level.activewheels`). The first location is random among `arcade_back`,
  `mars_3`, `moon_bumpercars` (`cp/maps/cp_zmb/cp_zmb.gsc:552-556`).
* Cost **950** per spin, 10 during Fire Sale (`interaction_magicwheel.gsc:111-115`). The wheel moves after spins:
  counter `_id_13D01`; from the 5th spin on a 50 % chance, forced at the 7th (`interaction_magicwheel.gsc:670-690`).
* Pool: the 37 weapons marked `magic` in `cp_weapontable.csv` (ar57, emc, fmg, kbs, m1, m8, spas, axe, lmg03,
  chargeshot, cheytac, devastator, fhr, glprox, mauler, sdfshotty, sdflmg, sdfar, lockon, g18c, ump45c, spasc, arclassic,
  cheytacc, udm45, rvn, crdb, vr, minilmg, mp28, mod2187, ba50cal, longshot, mag, gauss, tacburst, unsalmg); some are
  removed per player state (forgefreeze, venomx, nunchucks, lines 581-735).

### 4.4 Power, portals (fast travel) and Pack-a-Punch

**Power: per-region generators, 5 of them** (`generator` interaction structs, cost 0, `cp/zombies/zombie_power.gsc:94`
`generic_generator` and `:184` registration). Each struct's `script_parameters` lists the zones it powers (a
`<zone> power_on` notify per entry; no `power_all` entry is used on this map):

| generator (position) | powers |
|---|---|
| front_gate (1078, 3680) | hidden_room, moon, front_gate, underground_route |
| arcade (2349, -1829) | arcade, arcade_back |
| moon_outside_begin side (4730, 1249) | moon_outside_begin, moon_rocket_space, moon_second, moon_bumpercars, hidden_room |
| mars (-1364, -93) | hidden_room, swamp_stage, mars_3, mars |
| europa (-692, -2761) | europa_tunnel, room_europa, europa_2, roller_coast_back, hidden_room |

Each interaction with `script_parameters "requires_power"` gets its `power_area` from the spawn volume that contains it
(`get_area_for_power`, `cp/cp_interaction.gsc:100`). Things that require power: perk machines, portals, traps,
arcade, F&F machines, crafting stations, shooting gallery, coaster.

**Portals (fast travel)**: 5 `fast_travel` structs (script_area `mars`, `europa`, `arcade`, `moon`, and `main_street` =
the exit portal in the hub at (645, 707, 94)); `cp/zombies/zombie_fast_travel.gsc`. Unlocked by the power of their
region, then **free** (`var_3 = 0`, `run_fast_travel_logic`, line 263-290). Cycle: 3 s charging, **15 s open**, then
**30 s cooldown** (`_id_6B8B`, line 717-740). A region portal takes the player to the hub; first use per region
increments a 4-step announcer chain (`_id_CE6F`, line 374).

**Pack-a-Punch, reached like this**:
1. Power the regions (generators).
2. Use each of the 4 region portals once (`_id_1BF8`, line 551: all non-`main_street` spots have `used_once`).
3. The hub portal then becomes the hidden-room portal; each use opens a 30 s window, then a 60 s cooldown
   (`_id_15B6`, line 609-632). Inside the hidden room each player has a **30 s timer** (`pap_timer_start`, line 164)
   and is kicked out afterwards.
4. The machine `weapon_upgrade` (hidden_room, registered `cp_zmb_interactions.gsc:168` with cost **5,000**, needs
   power): first upgrade **5,000**, second **10,000** (`get_interaction_cost`, `cp_interaction.gsc:346-356`).
   `level.pap_max = 2` (`cp/gametypes/zombie.gsc:74`): weapons reach pap1 (level 2). A third level (pap2) opens only
   after the Grey/UFO quest fuses are inserted at the `pap_upgrade` struct (`cp/maps/cp_zmb/cp_zmb_ufo.gsc:1170-1182`:
   `level.pap_max = min( pap_max + 1, 3 )`). The four wonder weapons (shredder, headcutter, facemelter, dischord)
   cannot be upgraded before `fuses_inserted` (`cp/zombies/interaction_weapon_upgrade.gsc:80-82`).

### 4.5 Traps (5 types, 9 structs, all 750, need power)

Registered `cp_zmb_interactions.gsc:169-204` with cost 750: rocket trap (2 structs, moon_rocket_space, target pf134_auto653),
beam trap (2, europa_2), disco-ball trap (2, arcade), scrambler (2, moon_outside_begin), black hole trap (1, mars_3).
Cooldown after use = `max( uses_this_round x 45, 45 )` seconds, the use counters reset every round
(`cp/maps/cp_zmb/cp_zmb.gsc:243-254`; e.g. `cp/zombies/interaction_rockettrap.gsc:119`). Kills from traps give no points
(`should_get_currency_from_kill`, `gametype_zombie.gsc:1411`). Active time of the rocket trap about 21 s
(`interaction_rockettrap.gsc:104`).

### 4.6 Other interactables and activities (counts from the interaction structs)

| item | count | note |
|---|---|---|
| secure_window (barricades) | 27 | in zones: mars 4, mars_3 4, front_gate 4, arcade 4, moon 3, europa_2 2, moon_bumpercars 2, moon_rocket_space 2, moon_outside_begin 1, swamp_stage 1; cost 0, per-player reboard-points cap `50 x wave`, max 500 per round (`zombies_spawning.gsc:3177-3186`, `interaction_windowrepair.gsc:65`) |
| arcade cabinets (8 games: demon, robottank, barnstorming, riverraid, cosmic, pitfall, starmaster, spider) | 98 structs (90 in the arcade zone, 8 in the afterlife arcade) | cost 0, need power, they give tickets |
| fate and fortune machines (`jaroslav_machine`) | 3 | moon_rocket_space, moon, mars_3; 3,000 first refill, 6,000 second, no third |
| ticket prize counters | 6 per tier (small 25 tickets, medium 50, large 300) + counters ammo 150 + grenade 150 + gold teeth 300 | each tier has 6 locations |
| souvenir crafting | 5 crafting stations (mars_3, moon_bumpercars, moon, europa_tunnel, moon_outside_begin); 3 coin kinds (alien, space, ice); 10 recipes of 3 coins make 8 crafted items | `cp_zmb_crafting.csv` |
| lost and found | 2 (front_gate) | recovers weapons for 2,000 (`zombie_lost_and_found.gsc:250`) |
| ATM | 1 deposit (1000 step) + 1 withdrawal (moon) | |
| quest structs | neil_battery 6, neil_firmware 4, neil_head 1, neil_repair 1, dj_quest_speaker 7, dj_quest_door 3, dj_quest_part_1/2/3 3 each, wor_standee 4, ark_quest_station 1, gold_teeth 1 + gator_teeth_placement 2, hidden_song_toy 54+11 | |
| mini games | coaster 1 (europa_2), laughingclown 1, bowling_for_planets 1, clown_tooth_game 1, basketball 2, game_race 8 (4 arcade, 4 afterlife), shooting_gallery 4 (mars) + 4 afterlife | each game has an `_afterlife` twin inside the afterlife arcade (x about -9500..-10400) |
| bumper cars | 3 vehicles, 26 `bumper_car_throw_spots` | `cp_zmb_bumpercars.gsc` |
| afterlife arcade | 1 `afterlife_arcade` start structs (4) | self-revive door, spectate door |

## 5. Spawning and rounds (from the scripts)

All in `cp/zombies/zombies_spawning.gsc` unless stated. The wave loop is `_id_E81B` (line 2927).

### 5.1 Max alive and where it is set

* **Cap = 24**: `get_max_static_enemies( var_0 )` returns `24` for non-escape modes (**line 3350**, function line
  3332), assigned each wave in `_id_1081A` line 3191 (`level.max_static_spawned_enemies = get_max_static_enemies( var_0 )`).
  Also `goon_spawn_event_func` (clown wave) sets 24 (line 220), cp_zmb direct boss fight sets 24
  (`cp/maps/cp_zmb/cp_zmb.gsc:3011`), the DJ speaker defense sets 16 solo / 24 multi
  (`cp/maps/cp_zmb/cp_zmb_dj.gsc:1040-1044`). It is independent of player count.
* Enforced by `num_zombies_available_to_spawn` (line 1775): `max_static_spawned_enemies - current_num_spawned_enemies -
  reserved(_id_E1CC) - pending(_id_50F8)`, capped at 100 per call, and also `desired_enemy_deaths_this_wave -
  alive - deaths - pending`. A living Brute takes one reserved slot (`increase_reserved_spawn_slots`, line 4141 and
  `_id_3114` line 2719).
* The first wave starts 15 s after the intro (`enemy_spawning_run`, line 1067), then 10 s between waves
  (`_id_7D00`, line 3323: `return 10`; the first interval is 5 s, line 2930).

### 5.2 Zombies per round

`get_total_spawned_enemies` (line 3353-3374): let `e = players - 1`, `e = 0.5` if solo. For wave `w`:
`mult = [0, 0.25, 0.3, 0.5, 0.7, 0.9][w]` if `w < 6` else 1; `scale = 1` for `w < 6`, `w/5` for `6 <= w < 10`,
`0.03 w^2` for `w >= 10`; **total = int( ( 24 + e x 6 x scale ) x mult )**. Computed (script `formulas.py`):

| wave | 1p | 2p | 3p | 4p |
|---|---|---|---|---|
| 1 | 6 | 7 | 9 | 10 |
| 2 | 8 | 9 | 10 | 12 |
| 3 | 13 | 15 | 18 | 21 |
| 5 | 24 | 27 | 32 | 37 |
| 6 | 27 | 31 | 38 | 45 |
| 10 | 33 | 42 | 60 | 78 |
| 15 | 44 | 64 | 105 | 145 |
| 20 | 60 | 96 | 168 | 240 |
| 30 | 105 | 186 | 348 | 510 |
| 40 | 168 | 312 | 600 | 888 |
| 50 | 249 | 474 | 924 | 1,374 |

### 5.3 Health per round

`calculatezombiehealth` (line 2212-2250): wave 1 = 150; waves 2 to 9 = `150 + (w-1) x 100`; wave 10 and later =
`int( 950 x 1.1^(w-9) )`; hard cap 6,100,000 (reached at wave 101). Independent of player count. Table: w1 150, w2 250,
w5 550, w9 950, w10 1,045, w15 1,682, w20 2,710, w25 4,365, w30 7,030, w40 18,234, w50 47,295. `zombie_cop` uses
wave+3, skeletons wave+10 (not spawned in regular waves here). Clown health uses the same curve (no multiplier is ever
set in `level._id_8CB3`). The space-helmet armor exists but only from wave 6000 (`zombie_armor.gsc _id_782B`), so it is off.

### 5.4 Spawn delay

`_id_7C79` (line 1802): wave 1 = 2.0 s, otherwise `2 x 0.95^(w-1)`, floor 0.08 s (reached at wave 64), or
`level.spawndelayoverride`. Samples: w5 1.63, w10 1.26, w15 0.98, w20 0.75, w30 0.45, w40 0.27, w50 0.16.
Spawner choice: random among all spawners of all active volumes (`_id_7C8C`, line 2444). Spawn happens at the spawner
(window, ground, ceiling by `script_parameters`/`script_animation`, see 7).

### 5.5 Speeds by round

Zombie move mode is drawn once at spawn and refreshed (`calulatezombiemovemode`,
`mp/agents/zombie/zombie_agent.gsc:1237-1262`): wave 1 always `slow_walk`; otherwise `v = randomintrange( 4w, 4w+35 )`:
`v <= 32` slow_walk, `<= 55` walk, `<= 78` run, else sprint. Resulting share in percent (slow/walk/run/sprint):
w2 71/29/0/0, w4 49/51/0/0, w6 26/66/9/0, w8 3/66/31/0, w10 0/46/54/0, w12 0/23/66/11, w14 0/0/66/34, w16 0/0/43/57,
w18 0/0/20/80, **w20 and later 100 % sprint**. Extras: 25 % chance per 5 s window of a sprint speed-up (move rate 1.15),
the last zombie of a wave runs (`run_if_last_zombie`, `gametype_zombie.gsc:2173`; from wave 4 immediately, before that
after 80 s), and from wave 20 a 5 % chance for a sprinting zombie to walk if fewer than 3 "fake walkers". The actual
units per second come from the animation set (`moveratescale`), not from script.

### 5.6 Special rounds (clown rounds) and reward

* Which waves: `_id_FF9D` (line 3208): never before wave 5, never within 5 waves of the last special wave; chance
  `( waves_since_last - 4 ) / 3` = 33 % at +5, 66 % at +6, 100 % at +7. Gaps are 5 to 7 waves (mean about 5.9).
  An event wave replaces the normal wave (`_id_E7F0`, line 3244).
* Count: `_id_8455` (line 297): `players x 6 x 2` first event (12 per player), `x 9 x 2` second (18), `x 12 x 2` third (24),
  `x 12 x 3` fourth (36), `x 15 x 3` fifth and later (45). For 4 players: 48, 72, 96, 144, 180.
* Pace: groups of 2 (`get_spawner_and_spawn_goons`), delay `_id_8454` (line 264): base 3 / 2 / 1.5 / 1 s (event
  1 to 4+) minus `spawned / total`, floor 0.05 s. Same 24 cap.
* Reward: the last clown kill drops **Max Ammo** (`_id_5CF7`, line 231, registered as
  `level.zombie_killed_loot_func`, line 184: `loot::drop_loot( ..., "ammo_max" )` when
  `desired_enemy_deaths == current_enemy_deaths`).
* Also in regular waves from wave 21: `should_spawn_clown` (line 1656) gives `min( w - 19, 10 )` % per spawn tick to
  send two clowns, at most one such spawn per 15 s.

### 5.7 Mini boss: the Brute

* Scheduler `_id_C212` (line 1598): from **wave 10**; needs `level._id_A88E + 3 < wave` (at least 4 waves after the
  last Brute spawn); chance `level._id_2CDB`, 50 % at first, +50 % after each miss (so 50 % then 100 %), reset to 50
  after a spawn. Count is **1 up to wave 19, 2 from wave 20** (alive limit, not scaled by players). Spawns after a
  random number of ordinary zombies (a quarter to a half of the wave) at a random goon location, hidden at
  `brute_hide_org` (line 1525). Dvar `scr_force_boss_spawn` forces it.
* Health: `_id_13F13` (line 2027): `min( 2000 + int( zombie_health(w) x 2 x k ), 5000 )` with `k` = 1, 1.5, 2, 2.5 for
  1, 2, 3, 4 players. So 4,090 at wave 10 solo, **5,000 from wave 10 with 2+ players and from wave 14 solo**. Agent
  table default 5000 (`PATCH/mp/default_agent_definition.csv`).
* Only head, helmet and neck hits hurt it; every other hit does 1 damage. Head hits count at 1/3 of the damage and
  wonder-weapon hits are fixed at 2000 before that (`mp/agents/zombie_brute/zombie_brute_agent.gsc:170-215`).
  Kill reward 60 points, 500 xp (agent table).

## 6. Player damage numbers for balancing

| Topic | Value | Source |
|---|---|---|
| Player health | 100; 200 with Tuff Nuff | `cp/cp_globallogic.gsc:186-197`, perks:777 |
| Regeneration | on (`healthregeninit( 0 )`) | `cp/gametypes/zombie.gsc` |
| Last stand | bleed-out timer 35 s (60 with coagulant); revive time 5 s; solo: one self-revive from Up N' Atoms (500) | `cp/cp_laststand.gsc:293-335, get_normal_revive_time` |
| Perk list and limit | 10 perks, 5 per player | 4.1 |
| Pack-a-Punch | 5,000 / 10,000 points; levels capped at 2 until the fuse quest, 3 afterwards | 4.4 |
| PaP damage multiplier | no script multiplier; each `_pap1`/`_pap2` weapon is its own asset (shredder, headcutter, facemelter, dischord pap1 are identical to the base: damage 2000, clip 8, reserve 80, fire time 74 ms; axe melee 1100 at all levels; forgefreeze damage 1, clip 50, reserve 200) | `WEAP/*.json` |
| Hit points | **10 per hit** x `cash_scalar` (= 1) | `gametype_zombie.gsc:1795-1815` |
| Kill points | generic zombie 60 (table), headshot 100, melee (non-axe) 130; Brute 60; xp 50 / 75 / 100 | `gametype_zombie.gsc:1288-1294`, `PATCH/mp/default_agent_definition.csv` |
| Melee on zombies | flat 150 for non-axe melee, Slappy Taffy +1,500 | `gametype_zombie.gsc:1515, 351` |
| Grenade damage scaling | x `min( 2 + 0.5 w, 10 )` (wave based) | `gametype_zombie.gsc:403` |
| Damage cap | any hit is clamped to the victim's max health | `gametype_zombie.gsc:451` |
| Power-up drops | by score: every `randomintrange( 2000, 3000 )` points of team score, max 5 per round; weights nuke 10, instakill 10, max ammo 10, double points 5, carpenter 5, infinite ammo 5, fire sale 5, infinite grenades 5, upgrade weapons 1 | `cp/loot.gsc:60-72`, `PATCH/cp/zombies/cp_zmb_loot.csv` |
| Max ammo effect | `give_max_ammo_to_player`: GiveMaxAmmo on primaries (clip filled when max equals clip), recharge powers | `cp/loot.gsc:1212`, `docs/MAX-AMMO.md` of the server repo |

**How wonder weapons scale at high rounds.** Not by percent for the four stock wonder weapons: they are a flat
**2000 damage per hit** (weapon asset `damage 2000, minDamage 2000`, no range falloff) and rely on the clamp to max
health. Against the health curve that means one-shot kills up to wave 16 (1,851 health), 2 hits to wave 24 (3,968),
4 hits at wave 30 (7,030), 10 hits at wave 40 (18,234). Brutes: 2000 (scaled again for head hits) and the helmet
rule. The Fate and Fortune card weapons use health-relative rules (`fateandfortuneweaponscale`,
`gametype_zombie.gsc:1533-1577`):

| weapon | normal zombie | brute | grey / slasher / super slasher / insta-kill immune |
|---|---|---|---|
| iw7_atomizer_mp, iw7_penetrationrail_mp | damage = max health (instant kill at any round) | max health / 10 | 2,500 flat |
| iw7_steeldragon_mp, iw7_claw_mp | `clamp( max health, 700, 1000 )` (so 1000 flat after wave 17) | `clamp( 0.34 x max health, 300, 1000 )` | same as brute |
| iw7_blackholegun_mp | `min( damage x 10, 2000 )` | same | `clamp( 0.34 x max health, 300, 1000 )` |

The arcade weapon assets: steeldragon damage 12 (clip 100), claw 34 (clip 65), atomizer 135 (clip 7), penetration rail
58 (clip 8), black hole gun 250 (clip 3).

**Fate and Fortune cards in brief.** Deck of 3 slots (4 or 5 if unlocked, `get_card_deck_size`,
`cp/zombies/zombies_consumables.gsc:240`), a meter fills as the player scores (1,250 points of charge for the first deck,
3,000 after the first refill, 5,000 after the second, `get_max_meter` line 777); at full meter a card can be
activated from the D-pad. The Jaroslav machine (3 on the map) refills the deck for 3,000, then 6,000, no third refill
(`cp/zombies/zombies_consumable_replenishment.gsc:8-9, 100-182`). Card effects among the ones seen in the damage code:
double hit points, sharp shooter x3 headshot, damage booster x2, last bullets x2, increased melee, shock melee,
headshot explosion.

## 7. Script conventions a custom map must provide (checklist)

References are to `$GSC/`. KVP names are the real names; the entity file stores them as numeric ids (known ones:
157 classname, 822 targetname, 543 origin, 65 angles, 638 script_noteworthy, 820 target, 497 model, 61049
script_parameters, 60666 script_area, 636 script_linkname, 61097 script_side, 502 groupname, 599 radius).

Map script entry (`cp/maps/cp_zmb/cp_zmb.gsc:4-136` `main()`), the stock mode expects these level fields:
`level.initial_active_volumes` (568), `level.use_adjacent_volumes` (20), `level.map_interaction_func` (70, the interaction
registration), `level.wait_for_interaction_func`, `level.player_interaction_monitor`, `level.idle_spot_patch_func`,
`level.goon_spawner_patch_func`, `level.patch_update_spawners`, `level.coop_weapontable` (`cp/cp_weapontable.csv`),
`level.crafting_table`, `level.weapon_rank_event_table`, `level.tutorial_message_table`, a minimap (`setminimap`),
agent registration (`registerscriptedagents`, line 165: zombie, zombie_brute, the_hoff, plus clown and c6).

- [ ] **Spawn volumes**: `info_volume`, targetname `spawn_volume`, KVP `script_linkname` = `<prefix>_<zone>` (prefix
  `pf<N>_` is stripped, `zombies_spawning.gsc:160-176`), KVP `target` = targetname of the zombie spawner structs
  (`zombies_spawning.gsc:89-110, 934-952`). The volume needs a Havok entity shape, otherwise `ispointinvolume` is
  always false (documented in `volume_check.py`). One volume must be listed in `level.initial_active_volumes`.
- [ ] **Zombie spawners**: `script_struct` with targetname = volume.target, `script_noteworthy "static"` (all stock ones),
  `angles`, optional `script_parameters` (`ground_spawn`, `ground_spawn_no_boards`, `no_boards`) and a spawn-effect KVP
  (`script_fxid`/`script_animation`: `spawn_ground`, `spawn_ceiling`, `spawn_wall_low`) (`_id_10865`, line 1098-1130).
- [ ] **Window entrances**: `script_struct` targetname `window_entrance` with `target` (the barrier models), plus one
  `interaction` struct with `script_noteworthy "secure_window"` next to it (`zombies_spawning.gsc:2504`,
  `interaction_windowrepair.gsc:166-173`).
- [ ] **Goon spawn points** (clown and brute spawn): `script_struct` targetname `dog_spawner`, inside a spawn volume and
  outside `invalid_playspace` volumes (`zombies_spawning.gsc:821-860`); plus one struct `brute_hide_org`
  (lines 421, 1525). Optional `ghost_spawn` structs (ghost waves, line 868).
- [ ] **Player spawn and respawn**: `default_player_start` structs (4) and `player_respawn_loc` structs inside the
  volumes (`_id_F546`, line 4089; `cp/gametypes/zombie.gsc` respawn functions).
- [ ] **Idle spots**: `zombie_idle_spot` structs (31, plus 12 added in script `cp_zmb.gsc:2776`).
- [ ] **Invalid play space**: `info_volume` targetname `invalid_playspace` (`zombies_spawning.gsc:90`).
- [ ] **Interactions** (all gameplay objects): `script_struct` targetname `interaction`, KVP `script_noteworthy` = the
  registered interaction name (`level.interactions[name]`), `script_parameters "requires_power"` for powered things,
  `script_area` = zone name (door sides, portals), `target` = the entities it drives (door debris, doors, machine,
  light), `script_side` for team doors (`moon`, `kepler`, `triton`) (`cp/cp_interaction.gsc:13-62`,
  `register_interaction` line 688). Structs are dropped to the ground at load (`drop_interaction_structs_to_ground`, line 81).
- [ ] **Doors/debris**: interaction `debris_<cost>` on both sides with the same `target`, different `script_area`; a
  `trigger_use` `door_buy` plus the debris scriptable/brush with the same `targetname` as `target`
  (`interaction_openareas.gsc:221-253`). Registered costs in the map's `register_interactions`
  (`cp_zmb_interactions.gsc:128-135`). Team doors: `team_door_switch` structs with `script_side`, `target` to a
  brush set including a `progress` mover (`interaction_openareas.gsc:59-130`, `cp_zmb.gsc:2508`).
- [ ] **Perk machines**: interaction `perk_machine_<name>` (names in 4.1), `target` = machine scriptable, requires power
  (`zombies_perk_machines.gsc:4-29`).
- [ ] **Wall buys**: interaction with `script_noteworthy` = weapon name (suffix `+attachment` allowed), registered
  per weapon with a cost, and the weapon must be in `cp_weapontable.csv` as `wall` (`coop_wall_buys.gsc:44-75`).
- [ ] **Mystery box**: scriptable `magic_wheel` instances + a `spinner` struct and a `wheel_fx_spot` struct per
  location, `out_of_order` brush (`interaction_magicwheel.gsc:20-45`), weapon list in `cp_weapontable.csv` (`magic`).
- [ ] **Power**: `generator` interaction structs with `script_parameters` = comma list of zone names; consumers use
  `requires_power` (`zombie_power.gsc:94-140`).
- [ ] **Portals**: `fast_travel` structs (`script_area`, `target` = end positions, `requires_power`), the hub
  `main_street` struct, `portal_center` script models, `portal_trigger` triggers, `center_portal` scriptable,
  tubes `fast_travel_tube_start/_end`, `hidden_travel_tube_start/_end`, `hidden_room_spot`, `hidden_room_portal`
  (`zombie_fast_travel.gsc:4-80, 679`).
- [ ] **Pack-a-Punch**: `weapon_upgrade` and `pap_upgrade` interaction structs, scriptable `pap_machine`
  (`interaction_weapon_upgrade.gsc:1-40`).
- [ ] **Traps**: `rockettrap`, `beamtrap`, `interaction_discoballtrap`, `scrambler`, `blackhole_trap` interactions with
  `target` to the trap entities, cost 750 (`cp_zmb_interactions.gsc`).
- [ ] **Data tables**: `cp/cp_weapontable.csv`, `cp/zombies/cp_zmb_loot.csv`, `cp_zmb_crafting.csv`,
  `cp_zmb_weaponrank_event.csv`, `cp/zombies/cp_zmb_tutorial.csv`, `mp/default_agent_definition.csv`, plus the
  navmesh, aipaths, 110 `node_negotiation_begin/end` pairs, 32 `navmesh_seed_point` structs, `delete_on_load` structs
  (107, deleted at load) and `effect_loc` structs for effects.
- [ ] **Adjacency data**: nothing to author; it is derived from door pairs sharing a `target`
  (`zombies_spawning.gsc:2339-2400`). For doors that must not link spawning set `level._id_C50A[a][b]`.

## 8. What could not be determined (be strict with these)

* Real walkable floor area: needs the navmesh (`maps/cp/cp_zmb.d3dbsp.navmesh`, 653,342 bytes), not decoded by any
  tool here. The footprint and floor-cell numbers are bounds.
* Zombie run speed in units per second: set by the animation set and `moveratescale`, not a script number. Only the
  mode mix (5.5) is a script fact.
* The patched scripts other than `cp_zmb.gsc` were not byte-compared to the decompile in `$GSC` (see section 0).
* Player damage taken from zombies (melee and projectile): not located in the scripts; it is in weapon/agent assets.
* Standard gun damage (m1, revolver, ...): the `iw7_*_zm` guns are not part of the map zone's 140 weapon assets in this
  dump; only wonder, arcade, melee and utility weapons are, so no PaP multiplier for ordinary guns could be read.
* The Grey/UFO boss fight rules (wave 28 setup in `cp_zmb.gsc:3003-3018`, `cp_zmb_ufo.gsc`) were not analysed beyond
  the gating of PaP level 3.
* The exact bleed-out value when played with partners (35 s default; coagulant 60 s) comes from one function, other
  modifiers may exist.
