# ONE WAY: the mod-zone source (`mod`)

    python -B make_zone.py --fragment <view-model fragment>/zonetool --dump <IW7-Runtime>/iwz-map-ref-a/dump --out <dir>
    python iw7_mod_preflight.py <dir>/zonetool/mod --csv <dir>/zone_source/mod.csv --json <dir>/preflight.json
    (preflight: tools-source/asset-bridge/t7-weapons, branch xzte-oneway; plain `python`, numpy from the user site)

Run on 28 Nov 2026 with the r14 fragment to `C:\studio-data\sz\weapons\one-way\zone\z1`. The lead builds `mod.ff` from
`zonetool\mod` + `zone_source\mod.csv` (the stock lists beside the csv are copies for the preflight) and loads it with
`--fs-game mods/szoneway --mod-ff <mod.ff>`.

## Sounds (`--sounds`, 28 Nov 2026)

    python foley_synth.py render sounds/one_way_sounds.json --out <sound>/flac          (x64-zt-extensions iw7-audio/foley, branch claude/oneway-foley)
    python foley_bank.py bank sounds/one_way_sounds.json --flac <sound>/flac --template <dump>/cp_zmb/sound/cp_zmb.all.aliases.csv --sfx-template <dump>/cp_zmb/sfxpkg/iw7_atomizer_mp_sfxpackage.json --out <sound>/bank
    python -B make_zone.py ... --out <dir> --sounds <sound>/bank

Adds bank `mod.all` (zone `mod`: 33 alias rows, 31 aliases, all `ow_*`), the sfx package `iw7_szoneway_zm_sfxpackage` (the Atomizer's, with our fire,
dry, raise and putaway aliases and the npc raise/reload fields emptied), and the notetrack sound map (27 keys, each key is the alias name: an animation
note called `ow_band_tear` plays `ow_band_tear`). Rows: `soundbank,mod.all` and `sfxpkg,iw7_szoneway_zm_sfxpackage` in `mod.csv`. Recipes and wiring:
`sounds/one_way_sounds.json`; measured levels: `sounds/levels.json`.

The fire rows are `loaded` since 28 Nov evening: the Atomizer row they were cloned from is `hybrid_pcm` (a loaded head, the
rest streamed from `mod.sabs`), and in the client's recording the first press started a 4.4 s broadband bed that none of
our 31 files matches (normalized cross-correlation 0.01 to 0.09 over 11.5-17 s), ending at the last-ticket press. Every
`loaded` row of the bank was heard clean (`ow_band_tear` 0.95).

## Effects (`--fx`, 28 Nov 2026)

    python -B make_fx.py --dump <dump> --vfx-tool <x64-zt-extensions>/tools-source/asset-bridge/t7-weapons --out <fx>
    python -B make_zone.py ... --fx <fx>

Nine particle systems of ours under `vfx/iwz/oneway/` (emitters cloned from stock cp_zmb systems and rewritten: life,
counts, sizes, velocities, colours, materials; table in `make_fx.py`), the tracer `szoneway_ticket` and the effect package
`iw7_szoneway_zm_vfxpackage` (view, ADS and world flash: card dust, card chips, press spark, a 30 ms warm light). The
weapon's `vfxPackage` and `tracerType` point at them. The script plays the rest: a card on the chest per ticket
(`playfxontag`, cleared at the bell), a door of carriage light at each zombie taken, carried or put back (at most 12 a
bell, each has a light), the cards of the taken, the bell at each holder, the full-train stroke, the lamp ticks.

## Name (`--name`, 28 Nov 2026)

`--name "ALLER SIMPLE"` writes `localizedstrings/szoneway.json` (`{"WEAPON_SZONEWAY": ...}`, ZoneTool's flat JSON
localize format) and the row `localize,szoneway`, and sets the weapon's `szDisplayName` to `WEAPON_SZONEWAY`. A zone
holds one language: the Paris servers' players read French, so the built zone says ALLER SIMPLE (English ONE WAY,
DESIGN.md section 12, until Neon rewrites the copy).

## What the zone holds

- Embedded: 3 materials (`mo/weapon_iwz_oneway_acc`, `_glass`, `_body`), the view model `weapon_iwz_oneway_vm`
  (surface, 7 images, techset state and constant-buffer copies), the anim package `iw7_szoneway_zm_package`, the weapon `iw7_szoneway_zm`.
- Weapon = stock `iw7_atomizer_mp` (cp_zmb) with: `szInternalName`, view model (`gunXModel`, `defaultViewModel`), clip 12,
  `iMaxAmmo`/`iStartAmmo` 60, `iFireTime` 400, `reloadDisabled` false (the template cannot reload), reserve counter shown,
  damage range flat to 1,500 (`maxDamageRange` = `minDamageRange` = 1,500, `minDamage` = `damage`), scope attachment cleared.
  Damage values are the template's (the script sets the real damage).
- Atomizer facts: bullet weapon (`weapType` 1, no projectile fields, `iProjectileSpeed` 0), semi-automatic (`fireType` 1),
  `weapClass` 5 (the pistol/SMG class of every stock zombies pistol), so a hit is expected to book bullet damage (`MOD_PISTOL_BULLET`; assumed from the class, not measured).
- Reload: IW7 keeps reload time in the anim package, not the weapon. `iw7_szoneway_zm_package` is a copy of the stock FTL pistol
  package with reload 2,400 ms (empty 2,800), ammo-in at the template's share of the animation (2,240 / 2,614), interrupt at
  84%, fast-reload (perk) at 65%.
- Csv (`zone_source/mod.csv`): `ignore,<12 stock zone lists>` (every stock asset is a reference), `require,<9 techset zones>`
  (the list of the map builds), then `material` x3, `xmodel`, `animpkg`, `weapon`.

## Stand-ins (the template's, referenced from the stock zones)

World model `weapon_ftlpistol_wm`, the third-person hand packages, the sprint and jump slots of the package (stock FTL
pistol), the impact table row (`vfxImpactType`/`sfxImpactType` 16, the Atomizer's), icons, rumble, stow, display name
`WEAPON_ATOMIZER`, and the feel (spread, sway, accuracy graph). With `--sounds --anims --fx` the view model, 13 first-person
clips, the sound and effect packages and the tracer are ours. Full list in `make_zone_report.json`.

## Preflight

Exit 0, 0 errors, 0 warnings, 2 notes: no catalog (the one weapon file is its own entry), and two images no material uses
(`weapon_iwz_oneway_acc_packed_a`, `_main_packed_a`: the opaque materials take no alpha map, so they are not built).

## Not proven

- (Proven since: ZoneTool builds the zone, the game loads `mod.ff`, the weapon is given, fires, reloads and draws; see
  `docs/station-zero/weapons/one-way/STATE.md`.)
- Assumed: `iMaxAmmo` is the reserve outside the clip (stock zombies weapons hold it at a multiple of the clip, 8/80, 14/126,
  20/160, and the script reads `getweaponammostock`); if it counts the clip, the reserve is 48.
- Assumed: the damage range is what limits a bullet; no weapon field was found that cuts a trace at 1,500 units.
- Unknown: whether the engine stretches the 2.0 s stock reload animation to 2.4 s (if not, the gun idles 0.4 s before it is ready,
  and the ammo goes in 0.24 s after the animation ends). The stock fire animation may also be longer than 0.4 s.
- The scope attachment was cleared on the assumption that it only serves the template's own model.
