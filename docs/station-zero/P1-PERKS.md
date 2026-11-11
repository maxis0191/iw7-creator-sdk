# P1 · The perks of Station Zero: what runs, what was measured

Package P1 of `12-BUILD-PLAN.md`, the design in `06-PERKS.md`, the code in `tools-source/iwzmap/perks/`
(`README.md` there says how it rests on the stock code). Every number below is a measured headless or client run on
Station Zero unless marked otherwise.

## 1. The ten machines

| Perk | Zone (scene) | Price | Power | Machine on this map | HUD icon |
|---|---|---|---|---|---|
| Up 'N Atoms | the Cordon | 1500 (500 alone) | its own generator, on from the start | stock machine | stock |
| Tuff 'Nuff | Platform A East | 2500 | power | stock machine | stock |
| Racin' Stripes | Platform A West | 2000 | power | stock machine | stock |
| Bang Bangs | Transit Police Post | 2000 | power | stock machine | stock |
| Quickies | Car Barn | 3000 | power | stock machine | stock |
| Deadeye Dewdrops | Signal Cabin | 1500 | power | PLACEHOLDER: stock vending machine `park_soda_machine` + the perk's icon over it | stock icon, image from the cp_disco dump |
| Baker's Dozens | Lodestar Exchange | 3000 | power | PLACEHOLDER: `popcorn_machine_iw6` + icon | PLACEHOLDER icon (vector-drawn) |
| Bon Voyages | the Parlour | 2000 | power | PLACEHOLDER: `zmb_mobile_ticket_booth` + icon | PLACEHOLDER icon |
| Sour Grudges | the Boneyard | 2500 | power | PLACEHOLDER: `park_arcade_standing_09` + icon | PLACEHOLDER icon |
| Double Takes | Underpass Arcade | 3000 | power | PLACEHOLDER: `park_arcade_standing_05_off` + icon | PLACEHOLDER icon, dim while recharging |

Limit: six (the stock five does not apply on this map). Loss on going down: every perk (the stock rule, which the new
perks follow because they are in the stock perk table). A perk used again at its machine is sold back for nothing
(stock). The Validated Ticket makes one purchase free and does not raise the limit.

Placeholders: the five bodies are stock props until P2's authored machines; the icons are simple vector pictograms in
the map's icon style (`make_perk_icons.py`) until P2; the new perks' jingles do not exist yet (only the stock
candy-box purchase sound plays); the Double Takes image is the shooting gallery's flat civilian cut-out
(`zmb_civilian_target_02`), not the player's own figure; the Sour Grudges mark is a stock green glow effect on the
zombie's head. Deadeye Dewdrops has no candy gesture on this map (its gesture weapon is not in the template zone);
the new perks have none by design until P2.

## 2. Measured

(see section 5 for the runs)

## 3. Balance

(see section 4)

## 4. Why none is broken

(filled from the measurements)

## 5. Runs and their conditions
