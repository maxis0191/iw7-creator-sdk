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
| Deadeye Dewdrops | Signal Cabin | 1500 | power | the game's own Deadeye machine (cp_disco scriptable `zm_perk_machine_deadeye_sign`, models `cp_disco_perk_dewdrops[_off]`) on the spare template perk scriptable; the stock Deadeye machine code runs its sign and lights (from build p2) | stock icon (image from the cp_disco dump) |
| Baker's Dozens | Lodestar Exchange | 3000 | power | authored machine `iwz_perk_machine_bakers` (perks/machines) + icon over it (from build p2) | vector icon (to redraw with P2) |
| Bon Voyages | the Parlour | 2000 | power | authored machine `iwz_perk_machine_voyage` + icon (from build p2) | vector icon |
| Sour Grudges | the Boneyard | 2500 | power | authored machine `iwz_perk_machine_grudge` + icon (from build p2) | vector icon |
| Double Takes | Underpass Arcade | 3000 | power | authored machine `iwz_perk_machine_double` + icon (from build p2) | vector icon, a dim copy while it recharges |

Rules on this map: at most six perks; every perk is lost on going down (the stock rule; the new perks are in the stock
perk table, so it applies to them); a perk used again at its machine is sold back for nothing (stock); the Validated
Ticket makes one purchase free and does not raise the limit.

What is not finished, plainly (state of build p2, 14 Nov 2026, section 2c): the four authored machines score a
median 6 of 10 against the stock machines (target 7: bodies too dark, no self-lit neon topper); the four new icons are
vector pictograms (`perks/make_perk_icons.py`); the new perks' jingles do not exist (to make as sound effects);
Deadeye Dewdrops' candy gesture is not in this map's zone; the Double Takes image is the shooting gallery's flat
civilian cut-out `zmb_civilian_target_02`, not the player's own figure; the Sour Grudges mark is the stock green
souvenir glow on the zombie's head; the Sour Grudges rim is four thin green bars on the screen edges.

## 2. Measured: purchases, limit, edges

| Question | Result |
|---|---|
| Up 'N Atoms before the power, alone | sells for 500, given |
| Tuff 'Nuff before the power | refused, 0 paid |
| The five machines without a stock machine | Deadeye 1500, Baker's 3000, Bon Voyages 2000, Sour Grudges 2500 paid at their machines after the power; Double Takes refused at six; five bodies in the map; the HUD rows 18 (Baker's) and 22 (Double Takes recharging) read from the zone's table |
| A sixth perk | bought at its price (Tuff 'Nuff 2500) |
| A seventh perk | refused, 0 paid, still six (the stock purchase test of every other machine also refuses) |
| A perk used again | sold back, 0 paid, five |
| Validated Ticket | next perk free (0 paid); the one after is refused at six |
| A second player | holds its own six; its seventh refused while the first player's purchase test says yes |
| Rounds 1 to 3 (stock spawning) | every perk and Baker's counter (5) survive |
| Down (a lethal hit, two players) and revive | every perk lost (2 to 0); revived; Tuff 'Nuff bought again for 2500 |

## 2b. What the player sees (client session, HUD read as data)

A real player (lab client, the stock HUD Lua unchanged) bought all ten at their machines in one session: the six of the first group, four sold back, then the four new ones (run c2, PASS 18/18). The UI dump (`iw7_ui.py find --id PerkIcon`) read the stock perk row:

- after the first six: six icons at y 669, 43 x 43 each, x 534 to 707: `cp_zmb_perk_icon_revive`, `_tough`, `_run`, `_ratatat`, `_flash`, `_deadeye`;
- after the four new: `cp_zmb_perk_icon_revive`, `cp_zmb_perk_icon_deadeye`, `iwz_perk_icon_bakers`, `iwz_perk_icon_voyage`, `iwz_perk_icon_grudge`, `iwz_perk_icon_double`, drawn by the stock row from the zone's table rows 18 to 21;
- the Baker's counter (server-drawn, `12`) at 898,658 28 x 29, the Validated Ticket line at 27,525; `iw7_ui.py check` found no overlap or off-screen defect in any of them.

The official client runs the same stock HUD Lua and reads the same table from the downloaded map zone, so the same row is expected there; the official client binary itself was not run (the lab client is the official client plus the dump).

An independent reviewer on the frames of run c2 found: the stock machines and the perk row correct; the five placeholder bodies not recognisable as perk machines (scores 1 to 2 of 10: two arcade cabinets read as arcade games, the Exchange and Parlour spots too dark, the frames taken too close), no floating icon drawn over them (fixed after: the icon now follows an anchor entity, see run c3), the four new icons readable but small at 25 px (the face and figure pictograms hard to read), and a raw string key `COOP_PERK_MACHINES_REMOVE_PERK` on screen at a machine (the map zone carries no localized strings: ledger).

## 2c. Build p2: machines, sounds and strings in the map (14 Nov 2026)

Build p2 (`build-sz2.ps1` on main, 475 MB zone, 2,199 s: compile 1,473, assembly 683, zone 42) carries the four
authored machines, Deadeye's own cp_disco machine, 12 stock perk sounds in the map bank (sabl 1.9 MB, sabs 6.2 MB) and
449 localized strings. Runs on it, zone scripts only (no loose files):

| Run | Conditions | Result |
|---|---|---|
| d1 p1_buy (headless) | one dedicated server, no client, zombies held, player protected | 38/39: bodies 4, Deadeye scriptable 1 (`DEADEYE_MACHINE stock=1`), 10 of 10 sound aliases present, HUD bits 18/9/22; `tuff_jingle_ms` 0 (the probe asks a dedicated server, which loads no audio: the bank report gives 14.275 s; ledger) |
| d1 p1_effect (headless) | same | PASS 27/27 |
| d1 p1_edge (headless) | same, two players, rounds 1-3, a lethal hit | PASS 20/20 |
| c5 p1_client (lab client) | one client + private server on loopback, waves off, zombies ignore the player, no damage | PASS 18/18, 11 frames; no raw string key in any of the 12 UI dumps; at a new machine the use prompt is the stock price widget (`3000`) |
| o2 p1_client_official | same plan, the official stable client (aurora-update-20261017) | not in game: the client reports `Map "cp_iwz" doesn't exist` with the map in `usermaps\cp_iwz\`, where the lab client loads it (ledger) |

Machine frames of c5, two independent reviewers (Sonnet 5.5) against the stock machines: Baker's 6 and 8, Bon Voyages
6 and 5, Sour Grudges 4 and 7, Double Takes 5 and 6; median 6. Both: the bodies are near black below the sign and
there is no self-lit topper like the stock neon signs. The floating machine icons show at the top centre of the frame
(the anchor 96 units up is above the view from 140 units away); the UI dump lists the waypoint elements as not drawn,
so the dump does not see them.

## 3. Measured: the four new perks

| Perk | What was measured |
|---|---|
| Baker's Dozens | 12 hits counted; the 13th dealt exactly 3.0 times its own damage (90 for 30); it passed through the 2 zombies behind on the line (both lost health); it paid its hit points again (10 more); 13 hits with a wonder weapon counted 0 and punched nothing; a second dozen punched again |
| Sour Grudges | the zombie that hit (20) was marked; killed in time with a rifle: the next hit (30) took 0; the one after (25) took 25 (one forgiven hit only); a kill with a wonder weapon and a kill after the 6 s mark earned nothing; a zombie typed as the Night Inspector was not marked |
| Bon Voyages | trap 375 instead of 750, postage 250 instead of 500, its own trap does not hurt the owner, 4 s at 1.2 speed after an arrival |
| Double Takes | a zombie's hit takes 45 at every round measured (rounds 1, 5, 10, 15, 20, 25, 30; 63 hits, every non-zero one 45); 100 to 55 does not trigger, 55 to 10 does; the three zombies within 400 units were lured, the one typed as the Night Inspector was not; 2 of the 3 had closed 30 units or more on the image 3.5 s later while the owner had stepped 300 units away; no second trigger inside the 60 s cooldown (more than 50 s left) |

Double Takes' threshold stays as the bible wrote it: the bible's fallback ("the first hit after 10 s unhurt") was for
two-hit deaths at round 25, and the measurement shows a flat 45 a hit from round 1 to 30, so from 100 health a player
always survives one hit under 35 % (55 then 10); with Tuff 'Nuff (200): 155, 110, then 65 triggers.

## 4. Balance against the stock six

| Perk | Damage | Survival | Economy / movement | Measured size |
|---|---|---|---|---|
| Tuff 'Nuff | no | +100 health, always | no | 200 health (second player) = two more 45 hits before going down, every time |
| Bang Bangs | yes, every bullet | no | no | 30 to 39 per hit (x1.3) in the same series of 12 hits, and the stock double-fire attachment on top (not measurable headless) |
| Quickies, Racin' Stripes, Deadeye, Up 'N Atoms | handling, movement, aim, revive | Up 'N Atoms only | yes | stock code |
| Baker's Dozens | one hit in 13 x3, through 2 more | no | the punched hit's points again (10) | measured series: 12 hits of 30 then 90 = 34.6 a hit on average (+15.4 %), against Bang Bangs' 39 (+30 %) before its fire rate |
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

All on Station Zero, private loopback servers, the scheduler's queue. Headless = dedicated server and one engine bot as the tested player, no client. Conditions common to the headless plans: round spawning off (`waves` off; the round number still advances by the stock code), the player ignored by zombies except in the measured hits, every door open, money set, the runtime's health top-up switched off where health is measured (`gl_protect_off`, stock health 100), the plan's zombies held in place (`szp_hold`) except during the Double Takes lure and the rounds, hits given by script (`dodamage` with a player or zombie attacker, through the stock damage callbacks), no inactivity kick on the private server.

| Run | Build / scripts | Plan | Result |
|---|---|---|---|
| a1 | build e + perk module as loose files | p1_buy (five perks given by script) | PASS 20/20, 200 s, no map build |
| a1 | same | p1_effect | lost: placed zombies were free and downed the bot (environment fault, fixed with szp_hold and gl_protect_off, ledger) |
| a2 | same | p1_hurt (rounds set by script, the player protected by values, one zombie chasing per round) | PASS: 45 a hit at rounds 1 to 30 |
| a5 | same | p1_effect | PASS 26/26 |
| b2 | build p1b (zone scripts only) | p1_effect | PASS 27/27 (punch through: the zombies behind lose 90, the same as the first) |
| b2 | build p1b | p1_edge (two players for the down; rounds 1 to 3 with the stock spawning, the player protected by values) | PASS 20/20 |
| b2 | build p1b | p1_buy (all ten at their machines) | 14/28: the five new machines never powered on (init bug, ledger); fixed |
| b3 | build p1b + the fixed module loose | p1_buy | PASS 28/28 |
