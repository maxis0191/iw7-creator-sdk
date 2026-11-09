# iwzmap darkness: dark until power, weapon flashlights, station lights by bank

Reusable for any generated IWZ usermap whose layout lights carry light groups.

## Engine route

- **Before power** the map's baked lighting (lightmap + light grid, `bake/lmbake.py`) holds only the `emergency`
  group: battery lamps, signal lamps, amber cue glows at every buy / door / perk / wheel / PaP / the power switch,
  and a faint ambient floor (`--ambient`). Power fixtures are not emissive in that bake, and in the world their
  diffusers are the dark panel (generator `IWZ_DARK=1`).
- **Station lights** (`power` and `flicker` groups) are real primary lights that script can switch: lights.txt
  lines with `name=iwz_power group=<bank>|<zone>|<on intensity>|<kind>` take scriptable light slots of the
  template (x64-zt `codex/iwzmap-darkness`: the compiler extends the template's 25 scriptable slots downwards when
  more are named) and get `light_spot` map entities (key 1 = light index), so `setlightintensity` drives them.
- **Power-on** (`cp_iwz_darkness.gsc`): stock flag `power_on` -> 2.65 s (audio: surge, breakers, hum) -> one bank
  per zone ordered from the power switch outwards, 0.8..1.3 s apart; each bank notifies
  `iwz_light_bank_on, <zone>` (audio relay thunk / tube strikes) and its tubes strike with 2..4 stutters; fixture
  models swap unlit -> lit; `flicker` lights keep stuttering light + model together; flag `iwz_power_lights_done`.
- **Flashlight** (`cp_iwz_flashlight.gsc`): a particle spot light (`PARTICLE_MODULE_INIT_LIGHT_SPOT`) bolted to each
  player's weapon tag with `playfxontag`, so every client sees every player's light; re-attached after weapon
  changes, last stand, revive, spawn (late join, afterlife return); killed at death.

## Files

| File | Role |
| --- | --- |
| `dark_build.py` | layout light groups -> dark baker list + named power lights in lights.txt + darkness.json report |
| `cp_iwz_darkness.gsc` | power lights / fixtures / flicker, bank sequence, audio notifies |
| `cp_iwz_flashlight.gsc` | per-player flashlight |
| `add_darkness.py` | adds both modules as rawfiles to the assembled zone (`build-sz2.ps1 -Darkness`) |
| `vfx_read.py` | reader of ZoneTool `.iw7VFX` dumps (emitters, states, modules, light parameters); `--spot` lists light effects |
| `make_vfx_light.py` | new light effect from a stock one: fov, inner fov, radius, colour, brightness, shadows, rename |
| `dk_measure.py` | frame metrics: pool (flashlight) area / luma / centroid, outside median, pair deltas, fxperf phases |

## Build (any map)

```powershell
$env:IWZ_DARK='1'                          # generator: dark diffusers, iwz_power_fixture models, //@DARK@ calls
python -I station_zero2.py <cp_zmb dump> <src>
python -I bake\layout_lights.py <src> lit.json --texel 6 --ambient 0.012
python -I darkness\dark_build.py <src> lit.json dark.json --ambient 0.03 --scale 9000
python -I bake\lmbake.py <src> dark.json <src>_lm --rays 256 --bounces 3 --denoise 1
python -I darkness\make_vfx_light.py <cp_disco dump>\particlesystem\vfx\iw7\levels\cp_disco\subway_train\vfx_train_front_light_ch.iw7VFX `
       <vfx root> vfx/iwz/vfx_iwz_flashlight_world --fov 32 --inner 12 --radius 900 --color 1,0.92,0.80 --brightness 1 --shadow 1 --near 8 --life 100000
build-sz2.ps1 -Src <src>_lm -Darkness -FxImport 'iwz:vfx/iwz/vfx_iwz_flashlight_world' -FxDumps 'iwz=<vfx root>' ...
```

The zonetool used must carry the named-light support (x64-zt `codex/iwzmap-darkness`).

Measurement: `python dk_measure.py <run dir> --frames 'dk_pre_*' --pair dk_pre_c0:dk_post_c0 --perf <fxperf file>
--phases 1=dark,2=dark4,... --json m.json --sheet sheet.jpg`.

## Coordination

Audio: `level.iwz_light_banks_external = 1`, `iwz_light_bank_on, <zone>`, `iwz_power_lights_done` (agreed in
`iwz-stage2\darkness\NOTES.md`). Flashlight click: `amb_iwz_flashlight_click` (played only when the bank has it).

## Engine proof (private local runner)

`dk_proof_fixture.gsc` (staged as the runner fixture; launch args in `dk_proof_fixture.args.txt`, mode
`paris_iwz_mode dkprobe8`; optional phases paris_iwz_dkfltest (carrier offsets / modes), paris_iwz_dkvsweep and
`paris_iwz_dklitsweep` (vision ladders), paris_iwz_dkdown (last stand), paris_iwz_dkshort (+ paris_iwz_dklit)): flashlight on / off / weapon switch, dark views, the FX agent's effect views, 4 and 8
players (bots), zombies walking into the light, the power-on transition every 0.25 s, the same views lit, fxperf phases
(1 dark, 2 dark 4p, 3 dark 8p, 4 transition, 5 lit, 6 lit 4p, 7 lit 8p). Frames are `iwzdk_*.bmp` (the runner only
collects `iwz*`). Then `dk_measure.py <run> --perf <fxperf> --phases ... --sheet`.

## Findings that shaped the route (engine runs dk2 .. dk11, darkness\NOTES.md)

- The stock train light used as the template is ONE particle with a 1 s life (intensity curve fading 0.75 -> 1.0)
  that is never re-spawned: without `--life` every flashlight copy goes dark ~1 s after `playfxontag`. The earlier
  "weapon switch loses the light" results (dk6 .. dk9) were this lifetime; pools had only been measured < 1 s after
  an attach. Always build the flashlight with `--life 100000`.
- IW7 auto exposure undoes a dark bake: a dark vision is required. add_darkness writes it as <map>_dark and under the
  spare stock name cp_zmb_int_basement; the module applies it 8 s and 14 s after each spawn (init-time calls are
  reset by stock spawn code). With tonemapAuto 0, tonemapMaxExposure -6 and -8 rendered identical frames (dk10 /
  dk11): it is not a manual exposure key (probably the auto-exposure clamp). The d11 build carries a fast-adapting
  ladder (auto clamped at max 2 / -2, manual tonemapExposure 13, tonemapExposureAdjust -3) under spare stock names;
  NOTES has the measured winner.
- Carrier: a fresh tag_origin model linked to tag_eye (mode `link`) does not depend on the weapon model. At eye +6
  forward the light lit the viewmodel hands (dk10); default forward 24.
- `killfxontag` + `playfxontag` of the same effect on the same entity soon after stays dark: every attach uses a
  fresh carrier entity.
- `setlightintensity` on compiler-named lights in the extended scriptable range switches them (bank frames).
- Lit state: fog 0.03 and volumetrics 0 remove the fog veil; the remaining white-out near fixtures is over-exposure
  (power scale 1400 clipped 8 .. 11 % of some views in dk10; d11 uses 840).
