# Station Zero: from the nine-zone release candidate to the bible's map (22 Nov 2026)

State: the nine-zone map (`station_zero2.py`, builds g27*) is a playable release candidate
([STATION-ZERO-G27J.md](STATION-ZERO-G27J.md), RC3 in progress). The bible (`docs/station-zero/`) describes a larger map:
19 zones, the Terminus quest, four wonder weapons, two new enemies, Tab pages, camos, emotes. This page says what does not
exist yet, what each piece needs from the engine and the tools, and the order. Every line is real engine or map work; no
script stand-in counts as a piece done.

## One line, not two

Two generators make a map called cp_iwz: the nine-zone g27 line and the 19-zone scene line (`scenegen.py`,
`scenes/station_zero.json`, with W1 blockout, W2 dressing of four zones, Q1 quest and T1 Capsule Post proven headless on
11 Nov). The g27 line has what the scene line lacks: the train set, darkness, P1 perk machines, FX, audio, the door,
well and stair fixes of 20-22 Nov. Keeping both doubles every fix. Decision: the scene line becomes the one line. The nine
g27 zones map onto bible zones (ticket hall = Fare Hall, platform A = Platform A West/East, maint corridor + generator room
= Converter Hall, control room = Signal Cabin, service tunnel + platform B = Car Barn approach). Step 0 below moves the g27
systems into the scene line and proves the same acceptance suite on it before anything new is built.

## Packages (order; each ends in a measured proof)

| # | Piece | Exists today | Engine / tool work it needs | Proof |
|---|---|---|---|---|
| 0 | One line: g27 systems into the scene line (train, darkness with the lit-exposure finding, P1, FX, audio, door tiles shown, stock stairs on every flight, Capsule Post with travelling blowback) | scene line has 19 zones as rooms, Q1, T1 | none new; `szaccept` / `szq` suites run on both | the g27 acceptance suite (doors, economy, wells, stairs, rounds 1-15, post routes and rules, PaP with real keys) passes on the scene map |
| 1 | 19 zones dressed (W3a-d) | 4 zones dressed (W2) | static models without a template twin (TF10, open): until it passes, props stay template donors; prop budget per view (`tome_cull.py`) | three independent reviewers at 7.5 per zone, frame time against the W1 baseline |
| 2 | Terminus quest (Q1) end to end with its hero objects (clocks, levers, board plates: HO1) | Q1 rules on stand-in models (11 Nov, 37/43 then fixed) | authored static models (HO1) through kit import; Terminus collision encoder fix (done 11 Nov) | Q1 plans on the dressed map; reviewers on the hero objects |
| 3 | Wonder weapons (WW1 EXACT CHANGE first, then WW2-4) | none on this map; the mod's ElevenLabs one-shots exist (names in server `ops/audio/elevenlabs_aliases.json`) | a weapon end to end from Blender on a donor animation set (A1), sticking projectile and alternate-mode chain probes (WW2-4) | the seven proofs of `05-WONDER-WEAPONS.md` each |
| 4 | Night Inspector and Rollers (E3, E4) | none | our animation playing in the game (C1, C2: not yet), actor kit hits on script bodies (E1) | `07-ENEMIES.md` proofs; stand-ins are not the feature |
| 5 | Tab pages and HUD (H1 server-drawn, UT Lua) | none | Lua from a map zone (CF1, unreleased upstream) for UT; H1 needs no client change | element budget, three languages, reviewers on frames |
| 6 | Camos (K1), emotes (M0-M4) | none | camo index of a custom map; full-body animation on a player (M0 probe) | `08-CAMOS.md`, `10-EMOTES.md` criteria |
| 7 | Crowd above 24 (CF2) | engine capacity work in the client fork (server `docs/ZOMBIE-CAPACITY.md`) | native agent capacity, already a separate engine package | the seven proofs of `07-ENEMIES.md` 2.5 with real agents |

## Lighting finding that every later zone uses

Stock cp_zmb renders at mean luma 0.175 (p90 0.34) under the same vision values the generated map uses; the generated map
rendered at 0.442 (p90 0.82) because its many evenly spread lights and fill give the auto exposure nothing dark to keep.
Fields the renderer reads and their offsets: `<runtime>\iwz-stage2\darkness\NOTES.md`, 22 Nov. Dressing a zone includes its
light budget against that target.
