# P1 · The perks of Station Zero: what runs, what was measured

Package P1 of `12-BUILD-PLAN.md`, the design in `06-PERKS.md`, the code in `tools-source/iwzmap/perks/`
(`README.md` there says how it rests on the stock code). Every number below comes from a headless or client run on
Station Zero (runs and their conditions in section 6) unless it is marked "stock code" (read from the game's scripts,
not measured here).

## 1. The ten machines

| Perk | Zone (scene) | Price | Power | Machine on this map | HUD icon |
|---|---|---|---|---|---|
| Up 'N Atoms | the Cordon | 1500 (500 alone) | its own generator, on from the start | stock machine | stock |
| Tuff 'Nuff | Platform A East | 2500 | power | stock machine | stock |
| Racin' Stripes | Platform A West | 2000 | power | stock machine | stock |
| Bang Bangs | Transit Police Post | 2000 | power | stock machine | stock |
| Quickies | Car Barn | 3000 | power | stock machine | stock |
| Deadeye Dewdrops | Signal Cabin | 1500 | power | PLACEHOLDER body `park_soda_machine` + the perk's icon over it | stock icon (image from the cp_disco dump) |
| Baker's Dozens | Lodestar Exchange | 3000 | power | PLACEHOLDER body `popcorn_machine_iw6` + icon | PLACEHOLDER icon |
| Bon Voyages | the Parlour | 2000 | power | PLACEHOLDER body `zmb_mobile_ticket_booth` + icon | PLACEHOLDER icon |
| Sour Grudges | the Boneyard | 2500 | power | PLACEHOLDER body `park_arcade_standing_09` + icon | PLACEHOLDER icon |
| Double Takes | Underpass Arcade | 3000 | power | PLACEHOLDER body `park_arcade_standing_05_off` + icon | PLACEHOLDER icon, a dim copy while it recharges |

Rules on this map: at most six perks; every perk is lost on going down (the stock rule; the new perks are in the stock
perk table, so it applies to them); a perk used again at its machine is sold back for nothing (stock); the Validated
Ticket makes one purchase free and does not raise the limit.

What is placeholder, plainly: the five bodies are stock props until P2's authored machines; the four new icons are
vector pictograms in the map's icon style (`perks/make_perk_icons.py`) until P2; the new perks' jingles do not exist
(only the stock candy-box sound plays); Deadeye Dewdrops' jingle and candy gesture are not in this map's zone (its
sound aliases and gesture weapon belong to another map); the Double Takes image is the shooting gallery's flat
civilian cut-out `zmb_civilian_target_02`, not the player's own figure; the Sour Grudges mark is the stock green
souvenir glow on the zombie's head; the Sour Grudges rim is four thin green bars on the screen edges.

## 2. Measured: purchases, limit, edges

| Question | Result |
|---|---|
| Up 'N Atoms before the power, alone | sells for 500, given |
| Tuff 'Nuff before the power | refused, 0 paid |
| The five machines without a stock machine (Deadeye and the four new) | see section 6 (build p1) |
| A sixth perk | bought at its price (Tuff 'Nuff 2500) |
| A seventh perk | refused, 0 paid, still six (the stock purchase test of every other machine also refuses) |
| A perk used again | sold back, 0 paid, five |
| Validated Ticket | next perk free (0 paid); the one after is refused at six |
| A second player | holds its own six; its seventh refused while the first player's purchase test says yes |
| Rounds 1 to 3 (stock spawning, 57 kills) | every perk and Baker's counter (5) survive |
| Down (a lethal hit, two players) and revive | every perk lost (2 to 0); revived; Tuff 'Nuff bought again for 2500 |

## 3. Measured: the four new perks

| Perk | What was measured |
|---|---|
| Baker's Dozens | 12 hits counted; the 13th dealt exactly 3.0 times its own damage (90 for 30); it passed through the 2 zombies behind on the line (both lost health); it paid its hit points again (10 more); 13 hits with a wonder weapon counted 0 and punched nothing; a second dozen punched again |
| Sour Grudges | the zombie that hit (20) was marked; killed in time with a rifle: the next hit (30) took 0; the one after (25) took 25 (one forgiven hit only); a kill with a wonder weapon and a kill after the 6 s mark earned nothing; a zombie typed as the Night Inspector was not marked |
| Bon Voyages | trap 375 instead of 750, postage 250 instead of 500, its own trap does not hurt the owner, 4 s at 1.2 speed after an arrival |
| Double Takes | a zombie hit takes 45 at every round 1 to 30 (seven rounds measured, 64 hits); 100 to 55 does not trigger, 55 to 10 does; the three zombies within 400 units were lured and the one typed as the Night Inspector was not; no second trigger inside the cooldown (60 s) |

Double Takes' threshold stays as the bible wrote it: the bible's fallback ("the first hit after 10 s unhurt") was for
two-hit deaths at round 25, and the measurement shows a flat 45 a hit from round 1 to 30, so from 100 health a player
always survives one hit under 35 % (55 then 10); with Tuff 'Nuff (200): 155, 110, then 65 triggers.

## 4. Balance against the stock six

| Perk | Damage | Survival | Economy / movement | Measured size |
|---|---|---|---|---|
| Tuff 'Nuff | no | +100 health, always | no | 200 health (second player) = two more 45 hits before going down, every time |
| Bang Bangs | yes, every bullet | no | no | see section 6 (plain vs Bang Bangs hits) |
| Quickies, Racin' Stripes, Deadeye, Up 'N Atoms | handling, movement, aim, revive | Up 'N Atoms only | yes | stock code |
| Baker's Dozens | one hit in 13 x3, through 2 more | no | the punched hit's points again | +15.4 % damage over 13 body hits ((12 + 3) / 13); its value is where the 13th lands |
| Bon Voyages | no | no | half-price traps and postage, 4 s x1.2 after arrivals | 375 saved per Third Rail |
| Sour Grudges | no | at most one 45 hit forgiven per mark earned | no | needs a kill of one given zombie inside 6 s, a forgiven hit inside 8 s |
| Double Takes | no | one 4 s lure a minute | 1.5 s x1.2 | triggers on the second 45 hit from full health |

## 5. Why none is broken

- Damage: Baker's Dozens adds 15 % on bodies; the stock Bang Bangs multiplies every bullet and doubles the fire rate.
  The punch is capped like any hit by the zombie's own health, never touches wonder weapons, and pays one hit's
  points (10), not a kill.
- Survival: the stock Tuff 'Nuff gives +100 health every second of the game. Sour Grudges forgives at most one hit
  per earned mark (the first hit always lands, a second zombie's hit lands, a late or wonder-weapon kill earns
  nothing); Double Takes gives four seconds once a minute and does nothing against a crowd farther than 400 units.
  Both scale down with the crowd, Tuff 'Nuff does not.
- Economy: Bon Voyages saves money and time, kills nothing.
- None multiplies another: Baker's ignores wonder weapons, Sour Grudges ignores wonder-weapon kills, Double Takes
  cannot trigger while it recharges. With a limit of six, taking all four new perks means giving up two of Tuff 'Nuff,
  Quickies, Bang Bangs and Racin' Stripes.
- The base game's perk table and Fate & Fortune cards were read (`scripts/cp/zombies/zombies_consumables.gsc`,
  `zombies_perk_machines.gsc`): no match; closest are the card "force push near death" (low health, kills nearby)
  for Double Takes and Bang Bangs for Baker's Dozens, both different mechanics.

## 6. Runs and their conditions
