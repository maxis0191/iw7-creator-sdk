# Station Zero: the blockout's proofs (W1a, W1b) and the stress number (ST1)

Measured 11 Nov 2026 on the reference machine (i5-13400F, RTX 3080), private loopback benches, the lab client of
components 80d1aad (server meter, client recorder, `keys/1` input). Build e = the scene of this branch emitted by
`scenegen.py emit` (19 zones, 21 wall weapons at the price of their place, Third Rail use entity named), compiled by the
main-line ZoneTool (468.8 MB). Commands are in [SCENEGEN](SCENEGEN.md); the gamelab steps in the server's
`docs/GAMELAB.md`. Nothing here is a judgement of looks.

## W1a: geometry (closed)

| Proof | Result | Evidence |
|---|---|---|
| Lab plans, verdicts judged by arrivals against the number spawned | **9 of 9 plan verdicts pass**; 51 of 51 cases (28 climbs on 14 flights, 23 door and link crossings), every spawned zombie arrived; 102 of 102 player-hull walks; survey reaches all 18 non-far zones (1,850 points); 0 crashes | `level/w1a/runs/hl-f1`, `labreport_f1.json` |
| Timed real walk (lab client, forward key held, three routes) | **190.2 u/s along the walked path** (run 3; runs 1 and 2: 190.2 and 190.9). Real time = navigation length / **216 u/s**: Cordon to Converter Hall 27.1 s (table said 31.8), Fare Hall to Platform West 14.2 s (17.2), Car Barn to Exchange 14.4 s (14.7). Use `routes --speed 216` for walking times | `level/w1a/runs/walk-e1/run3`, `walkreport.json` |
| Client memory of that session | peak working set 3.1 to 3.7 GB, private 13.2 to 14.4 GB (declared 8 / 18 GB) | `result.local.json` of the walk runs |

Kept-room objects that still cannot come over: the turnstiles, the BO3-style booth, the train cars and the G-2 genset
are kit or ported models with no template twin, and need the static-model route of TF10 (landed today, x64-zt #14 and
SDK kit staging) wired into the scene's props: owner **TF3 / kit import**. The custom-image signs need the sign system
in the map build: owner **W5 (2D art)** with W2's recipe. The Cordon's generator exists as behaviour (Up 'N Atoms on its
own power) and as a marker; its model is dressing (W3a / HO1).

## W1b: systems (proven headless, one client check)

| Check | Result | How |
|---|---|---|
| Power | the Converter Hall switch sets the stock `power_on` flag | `use` on the stock generator struct |
| Perks | Up 'N Atoms sells before the power (500, solo price) and a real player gets it before the power (on the engine bot its gesture never ends: ledger); Tuff 'Nuff refuses before the power (0 spent); after it Tuff 'Nuff 2,500, Racin' Stripes 2,000, Bang Bangs 2,000, Quickies 3,000 are given (perks 1 to 4 in the stock `zombies_perks`) | `use`; client plan `cp_iwz_w1b_powered_client` |
| Wall weapons | **21 of 21** bought, each at the price of its place (500 to 2,000), the stock variant test true | plan `cp_iwz_w1b_walls`, 42/42 |
| Magic wheel | spin 950, weapon taken from the wheel's weapon entity (weapons 1 to 2); 9 wheel entities: 7 placed, 2 parked template wheels without a spinner | `use` on the wheel entity, then its weapon |
| Third Rail | 750 taken; the zombies in the track pit died; zombies that had climbed to the deck lived (the lane rule) | `deaths` counter and per-body lines |
| Special-enemy structs | 42 dog spawners, 1 brute hide, 32 respawn points in the running map | `ents` |
| Rounds | 0 to 7 in 229 s with the stock spawning, entities 405 to 416 (growth 11): cleaned up between rounds | `rounds` |
| 15 rounds with bots (soak, 3 bots, doors open, one zone a round) | **rounds 0 to 15 in 26 min**, server working set flat at 1.04 GB, entities 407 to 432, 0 script errors, 0 crashes. 43 stuck-zombie lines: all within 200 units of where the protected bots stood (zombies attacking an immortal bot, not stuck) | `level/w1a/soak/s1` |

Server frame time per zone (server meter, one window a round, the round's zombies coming to the bots in that zone):

| Zone (round) | median ms | p95 ms | p99 ms | max ms |
|---|---|---|---|---|
| Cordon (0) | 0.60 | 0.80 | 15.2 | 21.0 |
| Fare Hall (1) | 1.64 | 3.36 | 24.1 | 84.1 |
| Escalator Hall (2) | 1.68 | 3.36 | 22.9 | 99.5 |
| Arcade (3) | 2.51 | 5.04 | 35.5 | 348.4 |
| Shelter 7 (4) | 2.74 | 5.93 | 26.6 | 152.4 |
| Police Post (5) | 0.93 | 1.88 | 23.9 | 63.9 |
| Platform A West (6) | 1.49 | 4.75 | 22.1 | 104.2 |
| Platform A East (7) | 1.76 | 4.87 | 18.8 | 30.6 |
| Signal Cabin (8) | 1.59 | 5.15 | 21.3 | 103.4 |
| Car Barn (9) | 1.57 | 4.89 | 19.9 | 29.5 |
| Converter Hall (10) | 1.05 | 5.34 | 21.2 | 50.5 |
| Exchange (11) | 1.05 | 2.36 | 19.4 | 27.0 |
| Sump (12) | 0.96 | 5.69 | 21.7 | 34.4 |
| Parlour (13) | 0.95 | 5.74 | 20.4 | 32.8 |
| Bellows Vault (14) | 0.75 | 5.88 | 20.1 | 152.9 |

Client frame rate per zone is the ST1 baseline below (blockout, 0 props).

## ST1: the stress number

Method: `scenegen.py stressprops` adds stock static props (models with a template twin, so no entity) by floor area;
the map is rebuilt; gamelab `perfzones` measures the client recorder at every spawn zone (two views, 5 s each, no
zombie in view, uncapped). Shipped map: Spaceland (cp_zmb) the same way. One session a point (not three).

Median of the zone frame rates (worst zone) and the share of Spaceland's:

| Props | 1280 x 720 | 1920 x 1061 | stand-in: 4 cores, window asked 3840 x 2160 (got 1924 x 1061) |
|---|---|---|---|
| Spaceland | 387 fps (moon 187) | 403 (moon 210) | 227 (swamp_stage 174) |
| 0 (blockout) | 460 (119 %) | 461 (114 %) | 426 (188 %) |
| 2,000 | 291 (**75 %**) | 272 (**68 %**) | 203 (90 %) |
| 6,000 | 219 (57 %) | 223 (55 %) | 158 (70 %) |

- Props cost in **every zone**, not only where they stand (Boneyard, 90 of the 2,000: 609 to 303 fps): the generated map
  has no visibility culling, so every prop is drawn from everywhere.
- **Hard limit**: with 6,040 props the renderer reports "too many visible static models (record bytes 16392, limit
  16384)" in every view (311 lines a session); with 2,000 never. Past it, props are dropped from the frame.
- The windowed client cannot be larger than the screen: the 4K stand-in rendered at 1924 x 1061, so it measures a
  4-core processor, not 4K.
- Zombies: 24 stock agents cost nothing measurable at the measuring point (they were not in view: 0 within 1,500
  units); the 78-body crowd step (E1's kit) ended the match on this map twice (ledger `actorkit-78-match-ended-cp_iwz`).
  **The zombie part of ST1 is not measured.**
- Lights were not added (no switchable light slot is used; the template's 25 are untouched).

**Decision: budgets shrink, and TF5's build half starts now.** Without culling the whole map holds parity (85 % of
Spaceland at 1920 x 1061) at about **1,000 static props in all** (frame time 2.17 ms at 0 props, 3.67 ms at 2,000,
parity line 2.92 ms: about 0.75 microseconds a prop), i.e. about 55 a zone, against the bible's 6,000 first-version
figure. The renderer's visible-model limit lies between 2,000 and 6,000. With per-zone visibility cells (TF5) the budget
becomes per view: recommended until TF5 is measured, **55 props a zone**, and no zone dressed beyond W2's two rooms
before TF5 is measured on this map.
