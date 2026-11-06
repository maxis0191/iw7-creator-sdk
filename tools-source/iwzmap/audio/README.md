# iwzmap audio: Station Zero sound, hidden-song easter egg, capture and measurement

| File | Role |
| --- | --- |
| `station_zero_audio.json` | the map's sound bank `cp_iwz.all` (spec for x64-zt-extensions `iw7-audio/iwz_audio_bank.py`) |
| `cp_iwz_audio.gsc` | level module (rawfile `scripts/cp/maps/cp_iwz/cp_iwz_audio.gsc`): hidden-song easter egg + ambience |
| `add_audio.py` | after `assemble.py`: copies the module, bank and teddy bear sources into the zone root and inserts the zone CSV rows |
| `graywolf_mcp.py` | stdio client of the GrayWolf MCP server; `station-zero` re-exports every BO3 source below |
| `native/proc_loopback.cpp` | WASAPI process-loopback recorder: only the game client's own audio, wall-clock aligned |
| `audio_measure.py` | cross-correlation / spectral match of a capture against source audio, level per window, the full witness report |

## Sources (BO3 data on this machine; no Black Ops 1 install exists here)

| Asset | BO3 zone | BO3 name | Notes |
| --- | --- | --- | --- |
| Abracadavre | `zm_cosmodrome` (Chronicles Ascension) | alias `mus_abracadavre_intro`, file `all/mus/zm/dlc5/ee_final_mixes/abracadavre.flac` | 6:05, 48 kHz stereo; byte-identical to `mus_egg` (`all/zmb/zmb_blops/mus/zombie/cosmo/abracadavre.flac`) |
| hint loop | `zm_common` / `zm_cosmodrome_patch` | `zmb_egg_loop`, Chronicles song structs `zmb_ee_mus_lp` -> `all/zmb/egg/meteor_loop.flac` | the BO1 meteor hum, 7.8 s mono; BO3 3D 150..400(450) |
| activation | `zm_common` | `zmb_egg_activate` / `zmb_ee_mus_activate` -> `zmb/egg/meteor_affirm.flac` | 1.4 s mono |
| teddy bear | `zm_levelcommon` (and every BO3 zombies map) | xmodel `p7_zm_teddybear`, materials `mtl_p7_zm_teddybear`, `_fur` | converted by ZoneTool T7 `-dumpzoneto iw7` (normals fix); materials packed by `t7-weapons/t7_material_pack.py` from the single-UV stock IW7 teddy templates `mo/toy_teddy_bear_01` (body) and `mo/toy_teddy_bear_head_destroyed_01_fur_outside` (fur, blend) |

BO3's Chronicles hidden song (`_zm_audio_zhd.gsc`, decompiled from `zm_cosmodrome_patch` with gsc-tool
`-g t7`): each `songstructs` struct spawns a script_origin with a unitrigger, plays `zmb_ee_mus_lp`, and on
`trigger_activated` (Use) plays `zmb_ee_mus_activate`; when all are found the music system plays
`abracadavre`. Spaceland's own song quest (`cp_zmb.gsc` `init_hidden_song_quest` / `waitfordamage` /
`play_hidden_song`, patch_cp_zmb) uses teddy bears that take damage and plays the song 2.5 s after
`add_hidden_song_to_playlist`.

## Bank (`cp_iwz.all`, files `cp_iwz.sabl` + `cp_iwz.sabs`)

| Alias | Template row | Type | Notes |
| --- | --- | --- | --- |
| `mus_iwz_abracadavre` | `mus_zombies_newwave` | streamed, 2D `music_lr` | vol 0.5, MusicContent music |
| `zmb_iwz_ee_hint_lp` | `emt_light_hum_lp_03` | loaded, 3D `amb_elm_unres_3d`, looping | 100..550 units, default curve |
| `zmb_iwz_ee_activate` | `rollercoaster_sign_up` | loaded, 3D `equip_use_unres_3d` | 150..1200 units |
| `amb_cp_zmb_basement_lr` | stock | streamed, 2D `amb_bed_2d` loop | room tone bed (Spaceland basement) |
| `emt_appliance_hum_lp_01` | stock | loaded 3D loop, 35..450 | electrical hum |
| `emt_light_hum_lp_01` | stock | loaded 3D loop, 35..450 | fluorescent hum |
| `emt_water_drip_lp` | stock | loaded 3D loop, 65..450 | drips |
| `emt_small_metal_creak` | stock (6 variants) | loaded 3D one-shots, 55..350 | random creaks |
| `amb_iwz_train_rumble_dist` | `coaster_engine_low` | loaded 3D loop, 600..4000, vol 0.35 | distant train rumble (stock trolley loop) |

## GSC API (`cp_iwz_audio.gsc`)

```c
// in cp_iwz.gsc main():
level thread scripts\cp\maps\cp_iwz\cp_iwz_audio::song_ee_init( ( x, y, z ), ( 0, yaw, 0 ) );   // position from the level designer
emitters = [];
emitters[emitters.size] = scripts\cp\maps\cp_iwz\cp_iwz_audio::ambience_emitter( "emt_appliance_hum_lp_01", ( x, y, z ) );
emitters[emitters.size] = scripts\cp\maps\cp_iwz\cp_iwz_audio::ambience_emitter( "emt_small_metal_creak", ( x, y, z ), 1, 6, 15 ); // random one-shots
level thread scripts\cp\maps\cp_iwz\cp_iwz_audio::ambience_init( emitters, "amb_cp_zmb_basement_lr" );
```

`song_ee_init( origin, angles, opts )` options (a struct, all optional): `model`, `song`, `hint_alias`,
`activate_alias`, `use_radius` (72), `use_hold` (0.5 s), `look_dot` (0.85), `allow_damage` (1), `song_delay`
(2.5 s), `xp` (0). Interaction: hold Use within reach while looking at the bear, without a prompt (BO1/BO2/BO3
and the level design); a melee hit or shot also counts when the model takes damage (Spaceland). Level
notifies: `iwz_song_ee_activated` (player, method), `iwz_song_started`; `skip_song` ends the song early.
`ambience_stop()` stops emitters and beds. Every step prints `[IWZ audio] <EVENT> ... t=<gettime>`.

## Build

```
python graywolf_mcp.py station-zero <bo3 install> <bo3 export dir>
python <ext>/iw7-audio/iwz_audio_bank.py --spec station_zero_audio.json --out <bank dir> --var IW7_DUMP=<dumps> --var GAME=<iw7> --var BO3_EXPORT=<bo3 export dir>
python <ext>/t7-weapons/t7_material_pack.py <bo3 export>/iwz-teddy/bo3/models/p7_zm_teddybear/p7_zm_teddybear_LOD0.materials.json --template <zone>/materials/mo/toy_teddy_bear_01.json --texconv <texconv> --out <model dir> --only mtl_p7_zm_teddybear
python <ext>/t7-weapons/t7_material_pack.py ... --template <zone>/materials/mo/toy_teddy_bear_head_destroyed_01_fur_outside.json ... --only mtl_p7_zm_teddybear_fur
(move materials/*.json to materials/mc/, copy xmodel/p7_zm_teddybear.xmb + xsurface/p7_zm_teddybear_lod0*.xsb from the T7 -> IW7 dump)
python add_audio.py <work>/zone_source/cp_iwz.csv <work>/zonetool/cp_iwz cp_iwz --bank-root <bank dir> --model-root <model dir>
zonetool -buildzone cp_iwz      -> zone/cp_iwz.ff, cp_iwz.sabl, cp_iwz.sabs: ship all three in usermaps/cp_iwz/
```

## Witness

`native/proc_loopback.cpp` (build: `cl /EHsc /O2 proc_loopback.cpp /link ole32.lib mmdevapi.lib`) records the
client process tree only (other applications are excluded), 48 kHz stereo, and pads pauses with silence by
packet timestamp. The server runner `ops/iwzmap/Test-IWZMapLocal.ps1 -AudioCapture <exe>` records the whole
local session and stages `cp_iwz.sabl/.sabs`; fixture `tests/fixtures/iwzmap_audio.gsc` drives the ambience,
the distance sweep, the Use activation and the song. Then:

```
python audio_measure.py run --rec <run>/audio.wav --log <run>/result.local.json --song abracadavre.flac --hint meteor_loop.flac --activate meteor_affirm.flac --out report.json --plot hint_falloff.png
```
