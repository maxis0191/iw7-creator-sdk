# Station Zero perks (package P1)

The ten perks of `docs/station-zero/06-PERKS.md` in the map's own zone: the six stock perks the owner named, Deadeye
Dewdrops (a stock perk the template map lacks) and the four new perks, with this map's limit of six. Results and the
balance table: `docs/station-zero/P1-PERKS.md`.

## Files

| File | What |
|---|---|
| `cp_iwz_perks.gsc` | the core: registration in the stock interaction and perk tables, the limit of six, payment, Validated Ticket, machines of the perks without a stock machine, the damage hooks, the other packages' hooks |
| `cp_iwz_perk_bakers.gsc` | Baker's Dozens |
| `cp_iwz_perk_voyages.gsc` | Bon Voyages |
| `cp_iwz_perk_grudges.gsc` | Sour Grudges |
| `cp_iwz_perk_doubletakes.gsc` | Double Takes |
| `add_perks.py` | build step (always run by `build-sz2.ps1`): the scripts as rawfiles after the level script, one 2D icon material per new perk, Deadeye's stock icon material (image from the cp_disco dump), five new rows in the stock HUD bit table |
| `make_perk_icons.py` | the new perks' icons (vector-drawn placeholders, 128 x 128 TGA, and a contact sheet); `add_perks.py` draws them into the work folder when missing |
| `p1plans.py` | the headless test plans (library `szperks` of iw7-paris-server) |
| `add_localize.py`, `strings.json` | build step: every localized string the zone's scripts use, from the dumped English language zones (`zonetool -dumpzonetypes eng_cp_zmb localize`, `eng_patch_cp_zmb`; the zones must be under `<work>\zone\english`), plus the new perks' own hint strings; a usermap loads no language zone of its template, so without it raw keys show |
| `add_perk_sounds.py` | build step: the stock perk jingles (attract, purchase) of the six stock perks and the machine power-on sound into the map's bank (aliases from the cp_zmb and cp_disco alias tables, audio from the stock banks) |
| `add_deadeye_machine.py` | build step: Deadeye Dewdrops' own machine (the cp_disco scriptable `zm_perk_machine_deadeye_sign`, its two models by the kit import) on the spare template perk scriptable `perk_machine_blue_bolts_sign` that scenegen relocates; the stock Deadeye machine code then runs it |
| `machines/` | the four new perks' machines, authored: textures drawn in code, geometry in headless Blender, ported with env-model `t7_env_port.py` (`machines/README.md`) |

Shared files changed by one or a few lines: `cp_iwz3.gsc` (`init()` in `main()`, `register()` after the stock
registry, the Third Rail's price and owner rule), `scenegen.py` (the five perks without a stock machine become
interaction structs `perk_machine_<name>` that need power, with a placeholder body `iwz_perk_body`), `build-sz2.ps1`
(runs `add_perks.py`).

## How it rests on the stock code

Every perk is a stock interaction (`perk_machine_<name>`, spend type `perk`) and a stock perk callback, so the stock
give and take, the loss of every perk on going down, and the HUD bit (`zm_active_perks`) are the stock ones. The stock
limit of five is two hard-coded tests; no stock function is replaced: each perk interaction's own fields are set
(`cost`, `can_use_override_func`, `activation_func`, `hint_func`), which the map's purchase loop reads. The override
runs before the payment and refuses a seventh perk; the activation gives the perk without the test of five.

The HUD: the stock perk row draws the icon of each bit set in `zm_active_perks`, reading the icon's material name
from `cp/zombies/zombie_perks_bit_mask_table.csv` (stock Lua `ui/utils/cp/ingamecoopdatasources.lua`). The map zone
carries its own copy of the table with rows 18 to 22, so a new perk's icon is drawn by the stock row on any client that
loaded the map: no client change. Double Takes shows a dim icon while it recharges by swapping its bit for row 22
(`perk_machine_double_cd`), the way Change Chews swaps its sub-perks.

## Other packages

| Hook | Caller | Effect |
|---|---|---|
| `level.iwz_price_func( player, base, kind )` | traps (`kind` "trap"), the Capsule Post (T1, `kind` "postage") | Bon Voyages: half price |
| `level.iwz_trap_hurts_func( player, owner )` | every trap that hurts players | 0 when the owner holds Bon Voyages |
| `level.iwz_arrival_func( player, how )` | Capsule Post and train arrivals (T1) | Bon Voyages: weapon up, 20 % faster for 4 s |
| `level.iwz_grant_ticket_func( player )` | the Night Inspector (E4) | the Validated Ticket: the next perk is free |
| `level.szp_ww_weapons` | wonder-weapon packages (WW1 to WW4) | base names the new perks ignore |
| `level.szp_unmarkable` | enemies (E3, E4) | agent types the new perks ignore (default `zombie_inspector`, `zombie_roller`) |

Each caller tests `isdefined()` first, so nothing depends on this module being in the zone.

## Commands

```powershell
python -I -B perks\make_perk_icons.py <out>                 # <out>\*.tga, *.png, icons_sheet.png
python -I -B perks\p1plans.py <src> <plans out> [--given]    # --given: the five perks without a stock machine given by script
```

Fast loop with no map build: the level script and the module as loose files over a built map
(`-ServerCopy '<file>|iw7-mod/scripts/cp/maps/cp_iwz/<file>'` of the headless runner): iw7-mod reads a script file from
the game folder before the zone's rawfile (`src/client/component/gsc/script_loading.cpp`, `read_raw_script_file`).
Measured 11 Nov 2026: the purchase plan passed on build e with the module loose, 200 s from command to verdict, no build.
