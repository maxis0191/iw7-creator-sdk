# 12 · BUILD PLAN

The bible cut into packages for sub-threads. Rules that bind every package (owner's rules and the project's
workflow, `AGENTS.md` "Current workflow"):

- Nothing is built or run in the game, and nothing is committed, until the environment session reports the
  repository cleanup done.
- File checks before any build; a bench root, never the owner's game folder; headless before client; one
  plan answers many questions; the exit code is the verdict; problems go into the ledger.
- A result is a measured run. A look is judged by independent reviewers on frames from the game, never by
  the builder. Nothing is posted to the public client project. Nothing is deployed to the public servers.
- Tool first: when a tool is slow, buggy or blind, the package stops and the tool is fixed, proven, documented.
- Models (owner's rule of 11 Nov 2026, relayed by the environment session that night; it replaces the earlier
  lines in `AGENTS.md` point 10 and in older notes, which a sub-thread must not follow): only the orchestrating session runs Fable 5.2
  and keeps planning and orchestration. Helpers and sub-threads' workers: **Opus 5.5 medium** for all real
  work, **Sonnet 5.5 medium** for cheap and easy tasks (searches, inventories, reading, mechanical writing).
- **Playable by real players** (owner's principle of 11 Nov): every feature must reach a player's game by
  itself on the public servers, hold its performance budget, and be clear and finished. Where the official
  client lacks a capability, the capability is built as its own clean, minimal package in the project's fork
  of the client (`maxis0191/iw7-mod`; nothing is posted to the client project now), and the feature ships
  with a graceful fallback for a player on today's official client: never a crash, never a broken screen.
  `14-CLIENT-CAPABILITIES.md` lists each capability; section 5 below gives, for every package, its player
  delivery, its performance budget and its fallback.
- Each package leaves: the thing, its test, a document, and the readiness table of `docs/CREATION-CORE.md`
  updated where a "missing" became "works".

Sizes: S = hours, M = about a day, L = several days, XL = a week or more of agent work. Ids that already
exist in `docs/CREATION-CORE.md` (N1 to N6, A1 to A3, C1 to C4, U1 to U3, S1) keep their ids there; this plan
names what Station Zero needs from them.

## 1. What does not exist yet (checked against the readiness table) and who builds it

| Need of the bible | Readiness today | Package |
|---|---|---|
| Map compiler and generator on the main lines | being landed (N1, N2) | prerequisite, environment session |
| Test a custom map headless, from a bench root | **missing**: headless loads only the five stock maps; the map playtest needs a client and stages files into the base game folder | **TF1** |
| The layout as data, with terraces, stock-construction flights, 19 zones | the generator is 3,400 lines of code for 9 zones on one storey | **TF2** |
| Rooms dressed from shipped-map props; kit models as compiled static props | a prefab can be lifted, the generator cannot place it (N3 queued) | **TF3** (= N3) |
| A build in minutes, not 20 and growing | open (N4) | **TF4** (= N4) |
| A large map that stays fast with no culling | open (N5) | **TF5** (= N5) |
| The map reaching players from a dedicated server | unproven (N6); a failed download closes the official client | **TF6** (= N6) and **CF3** |
| Finding the right stock model, material, effect for a zone | models catalogued (13,113); the rest open (A3) | **TF7** |
| Collision for imported models | missing (A2) | avoided by design: imported things stand in generated niches with clip boxes, actors use script hit boxes. A2 stays useful, not blocking |
| New shaders | missing | avoided by design: stock techniques with our textures; camo motion only if a stock scrolling technique is found (K1) |
| Blender to a game animation; our animation playing in the game | missing (C1 running, C2 open) | prerequisite for E3, E4, M1; weapons ship on donor animation sets until then |
| A brand-new enemy | missing (C3) | **E1** builds the actor kit on Station Zero's first need (the crowd body) |
| More than 24 zombies | suspended native work with a recorded failure | **CF2** (the capability, in the client fork) and **E2** (the crowd system: native agents where the client has CF2, the hybrid crowd as the fallback on today's official client) |
| A new perk | no recipe | **P1** |
| A new weapon behaviour family | only push and chain exist | **WW2, WW3, WW4** each add one |
| Lua UI for players | merged in the client project's development line, unreleased (U2) | **CF1** keeps the capability in the fork; Tab and wheel ship a server-drawn tier first (**H1, M3**) as the official-client fallback; Lua versions (**UT, M4**) for clients that have CF1 |
| Third person and a full-body animation on a real player | unproven | **M1** proves it on the stock client or hands it to **CF4** |
| Sound measured from the game | tool merged, never used as a gate | **AU1** makes it a gate |
| Static models with no twin in the template map | earlier attempts crashed; such models stay entities | **TF10** |
| A count of entities and of the template's pools | nobody keeps one | **TF8** |
| Bullet hits on a script-driven body | unproven | **E1**, probe 3 |
| One list of enemies for every system (weapons, traps, perks, counters) | missing | **E1**, **E2** |
| Server script cost, server frame time, graphics-card time per pass | no tool | **TF9** |
| Water, rain, open sky, changing screens | no tool; one known failure | probes in **W2** and the zone packages, fallbacks in `02-WORLD.md` 8.1 |
| New camo rows for a custom map | not stated | **K1**, first probe |
| A failed download that does not close the client | missing in the official client | **CF3a** |
| Hero objects (rectifiers, Bellows, clocks, plates) | no package owned them | **HO1** |
| A size budget for the download | none | **SI1** |

## 2. The packages

### Wave 0 · Tools first (no map work depends on luck)

| Id | Scope | Inputs | Tools used | Depends on | Proof that closes it | Size | Model |
|---|---|---|---|---|---|---|---|
| **TF1** | Headless test plans on a custom map from a bench root; the map playtest harness off the base game folder | `docs/GAMELAB.md`, `docs/IWZ-PLAYTEST.md` | `Invoke-GameLabHeadless.ps1`, `New-BenchRoot.ps1`, `Test-IWZMapPlaytest.ps1` | cleanup; N1, N2 | the present map (rc build) loads headless on a bench in under 60 s and a plan reads zombie positions; the playtest phases run from a bench; documented in `docs/DEVKIT.md` | L | Opus 5.5 medium |
| **TF2** | Generator driven by a scene description: zones, heights, links, doors, ramps, spawners, interactions as data; terraces at seven heights; flights in the stock stair construction with the navigation-against-surface check; a skate mask and waiting places per zone; doors refused between rooms that do not share an edge; far boxes (Terminus). Emits the 19 zones of `02-WORLD.md` as empty rooms | `02-WORLD.md` sections 2 to 4, 6; `research/C-current-map.md` | `station_zero2.py`, `brushkit.py`, `iwz_emitcheck.py`, `sz2_navconn.py`, `iwzmap_ents_lint.py` | N2 | offline only: `emitcheck check` clean; `sz2_navconn` passes every level change; ents lint clean against the stock recipe; `emitcheck route` gives the walking-time table that replaces the estimates in `02-WORLD.md` | L | Opus 5.5 medium |
| **TF3** | Props of a lifted prefab and of kit zones placed by the generator as compiled static models; then surfaces with collision | `docs/WORLDKIT.md`, CREATION-CORE N3 | `iw7_world.py extract/place`, `kit_import.py`, map compiler | N1, N2 | CREATION-CORE's own proof for N3: a room of the custom map in the game with counts equal to the source and reviewers' score against the source room | L | Opus 5.5 medium |
| **TF7** | Kit lists: for each of the 19 zones, the stock models (all five shipped maps), materials and effects that fit its look, with counts, sizes and where the shipped maps use them; gaps listed as models to author | `02-WORLD.md` section 4 and 8 | `iwzcat.py`, `iw7_world.py find-model / where-model`, dumps | catalogue on main | one table per zone, at least 350 distinct models over the map, every name verified present in a dump; gaps list with sizes | M | Sonnet 5.5 medium |

### Wave 1 · Playable early: the whole new map as grey rooms with every system

| Id | Scope | Inputs | Tools | Depends on | Proof | Size | Model |
|---|---|---|---|---|---|---|---|
| **W1a** | Blockout, geometry: the 19 zones as rooms at their heights, the 17 doors, every flight in the stock stair construction, navigation, 186 spawners, the 17 inspection plates, respawn points. The rooms kept from the old map (Fare Hall, platform, train, G-2) reuse their existing dressing and signs so that the first playable is not worse than today's map anywhere | `02-WORLD.md`; E's checklist section 7 | TF2 generator, map compiler, TF1 | TF1, TF2, TF4, TF8 | file checks first (`emitcheck`, `sz2_navconn`, navigation-against-surface, ents lint, pool and entity ledgers); then the playtest harness: bounds, isolation, walk, stairs, spawners, routes, **climbs at 90 % or more on every level change**; one timed walk to calibrate the walking-time table | L | Opus 5.5 medium |
| **W1b** | Blockout, systems: power (with the Cordon's own generator), five stock perks at their places (Deadeye Dewdrops waits for P1), 21 wall weapons, 7 wheel positions, the Third Rail trap, special-enemy structs, rounds | `02-WORLD.md` | level script, TF1 | W1a | harness: buy, cleanup, rounds; a 15-round run with bots on the soak runner; frame rate recorded at fixed points as the big map's baseline (1920 x 1080 and 1280 x 720) | M | Opus 5.5 medium |
| **Q1** | Power sequence, the four quest steps, the cab, the teleport, the Terminus room logic and timer, reset per match, late join | `04-PAP-QUEST.md` | level script, TF1 plans | W1 | harness `quest` cases: each step solo and with four; wrong lever; Conductor not killed; carrier down; teleport out and back with 1 and 4 players; every player in the Terminus for 40 s at round 20 (zombie count, spawner state and script errors read back; the spawn pause or its fallback); a downed player inside and one left outside car 1; zombies in car 1 at departure; 20 matches in a row start clean | M | Opus 5.5 medium |
| **T1** | Capsule Post rules, version 1 (black-out ride): unsealing, postage, two capsules, ring and lever, blowback, refusals, Inspector closure, test entry | `03-TRANSPORT.md` | level script, TF1 plans | W1 | a plan rides all 12 routes on each lever setting (24 rides) and reads the rider's position and zone each 0.25 s; the dial input (tap and hold of Use) from a client with real input; every row of the failure table reproduced; blowback count checked with placed zombies | M | Opus 5.5 medium |
| **E0** | Enemy rules on stand-ins: outfit tables per district (stock bodies until looks pass), commuting idle, the Cleaner, the cap table and dvar (capped at 24 until E2), the Inspector's mark, fine, inspection-plate travel, reward on the stock mini boss; Roller-round schedule on the stock special enemy | `07-ENEMIES.md` | level script, TF1 plans | W1 | plans: mark follows points earned in the last two rounds and skips away, downed and absent players; fine amounts; reward given once; special round schedule over 30 simulated rounds | M | Opus 5.5 medium |
| **H1** | Server-drawn HUD H1 to H9, the STATION terminal page, `.tab`, `.where`, `.journal`, `.carried`, three languages | `09-TAB-AND-HUD.md` | `paris_ui.gsc` patterns, localisation generator | W1, Q1 | element count at or under 24 in the worst case; localisation check; frames to reviewers | M | Opus 5.5 medium |

**After wave 1 a team can play the whole new layout, do the quest, be sent by the Capsule Post and meet the
mark mechanic; the rooms kept from the old map look as they do today, the new ones are grey.** Everything after
this is improvement in steps.

### Wave 2 · The look is proven on two rooms before it is spent on nineteen

| Id | Scope | Inputs | Tools | Depends on | Proof | Size | Model |
|---|---|---|---|---|---|---|---|
| **W2** | Vertical slice: the **Fare Hall** and **the Parlour** dressed to full figure (640 and 720 props), lit in two states, with their signs, effects and sound beds. Writes the dressing recipe the other zones follow | `02-WORLD.md` 4, 8; TF7 lists; `11-AUDIO-DIRECTION.md` | TF3, kit import, `lmbake.py`, darkness kit, `fx_place.py`, art generators | TF3, TF7, W1 | density equal to target by count; brightness and contrast per room measured against two shipped rooms of the same kind (`lm_measure.py` and frames); **three independent reviewers, same cameras, against shipped rooms: at least 7 of 10 each**; frame rate against the W1 baseline | L | Opus 5.5 medium |
| **TF4** | (moved to wave 0) Build time: bake and zone only what changed | CREATION-CORE N4 | compiler, baker | N1, N2 | proven first on the present map: a one-room change rebuilt and loaded in under 5 minutes, measured; then the same on the 19-zone blockout | L | Opus 5.5 medium |
| **K1** | Camos: find the camo index a custom map gets; list and test stock scrolling techniques on a weapon; build CARRIER and MERCURY ARC (layer S, then layer M if the test passes) | `08-CAMOS.md` | material tools, weapon audits, `Test-WeaponVisual.ps1` | cleanup | the judging criteria of `08-CAMOS.md` on frames from the game, pistol and LMG | L | Opus 5.5 medium |
| **P1** | Perk logic: limit six on this map, Deadeye Dewdrops linked or re-made, the four new perks, Validated Ticket, server-drawn icons, the Double Takes cut-out | `06-PERKS.md` | level script, kit import, TF1 plans | W1 | first a dummy perk through the stock table; then per perk a plan with scripted hits, magazines and spins checking every number in `06-PERKS.md`; loss on going down; limit | M | Opus 5.5 medium |
| **WW1** | EXACT CHANGE, end to end: it is the simplest behaviour and so it proves the route for an original weapon (model from Blender on a donor animation set, sounds, effects, wheel entry, upgrade) | `05-WONDER-WEAPONS.md` 1 | weapon audits, mod preflight, `Test-WeaponE2E.ps1`, audio witness | cleanup; A1 | the seven proofs at the end of `05-WONDER-WEAPONS.md`; first probes: flat rated damage applied by script, withholding hit points; end-to-end time recorded | L | Opus 5.5 medium |

### Wave 3 · The map fills in; the remaining systems land

| Id | Scope | Inputs | Depends on | Proof | Size | Model |
|---|---|---|---|---|---|---|
| **W3a** | Dress the street and concourse: Cordon, Escalator Hall, Arcade, Shelter 7, Police Post, Staff Stair | `02-WORLD.md`; W2 recipe | W2 | per zone: counts, light measures, three reviewers at 7 of 10, frame rate re-measured after each zone | L | Opus 5.5 medium |
| **W3b** | Dress the platforms: Platform A West and East, the six walkable cars, the Party Car, Signal Cabin | same | W2 | same | L | Opus 5.5 medium |
| **W3c** | Dress the works: Car Barn, Converter Hall (rectifiers), Exchange, Sump | same | W2 | same | L | Opus 5.5 medium |
| **W3d** | Dress underneath and nowhere: Breach, Bellows Vault, Boneyard, the Terminus | same | W2 | same | L | Opus 5.5 medium |
| **W4** | Traps (Decon Foam, Flashover, the Bellows) and activities (Lost Property with buy-back, jukebox, photo booth, supply locker, pay phones, the 25 collectables, the three trophies and the song trigger) | `02-WORLD.md` 4, 5; `01-LORE.md` 11 | W1 | harness `trap` phase per trap; one plan per activity | M | Opus 5.5 medium |
| **W5** | 2D art: board plates, zone signs, the fake-product advertising, shop fronts, notices, the five murals, the film poster; texts from the wiki in three languages where they are read | `wiki/`, `02-WORLD.md` | W2 | art lint; reviewers on in-game frames; murals: the image tool is allowed with strict briefs, every result judged | M | Opus 5.5 medium |
| **T2** | Capsule Post version 2: capsule, hatch and pipe models; the visible ride path through the zones; bystander view | `03-TRANSPORT.md` 5, 9 | T1, W3 zones on the path | path points verified outside walls by `emitcheck at`; reviewers on a recorded ride; frame time during a ride | M | Opus 5.5 medium |
| **P2** | The four perk machines (models), icons, jingles in the bank | `06-PERKS.md` | P1, A1, AU1 | reviewers on frames; jingles measured audible | M | Opus 5.5 medium |
| **WW2** | TOP TO BOTTOM: the status family, the three cans, the can finds | `05-WONDER-WEAPONS.md` 4 | WW1 | the seven proofs of `05`; first probes: a continuous spray; holding a zombie at a waiting place from script; the three-way alternate-mode chain | L | Opus 5.5 medium |
| **WW3** | LIVE RAIL: the segment family, the three fuses, the parts and the workbench | `05` 2 | WW1, W4 | the seven proofs of `05`; first probe: a projectile that sticks and reports its point | L | Opus 5.5 medium |
| **WW4** | THE DISPATCHER: stamp, send, the capped burst, sending into a hatch, the "Undelivered" quest | `05` 3 | WW1, T1 | the seven proofs of `05`; first probes: the aim button as a second trigger; a zombie flown to a point | L | Opus 5.5 medium |
| **AU1** | Sound: beds, emitters and cues for 19 zones; the audio witness as a gate; then the music (Roller track, power-on cue, the hidden song, four jingles) | `11-AUDIO-DIRECTION.md` | W1 for positions | every cue measured audible from the game; loudness in target; at most 36 loops at 20 sampled positions; independent listeners on a recorded walk | L | Opus 5.5 medium |
| **TF5** | Staying fast, build half (wave 2, before any zone is dressed beyond W2): if ST1's numbers demand it, per-zone visibility cells in the generated visibility data so that zones not in view are not drawn (script hiding only helps entities, which are a small share) | CREATION-CORE N5 | ST1 | the frame-rate floor held at every measuring point with ST1's 6,000 props placed; then re-measured after each dressed zone | L | Opus 5.5 medium |
| **TF6** | (moved to wave 0) Does the official client already receive a custom map from a dedicated server? Measured with the **present** map on a private server: join with a profile that lacks the map; what happens, how long, what the client's log says; the full map list with a custom map installed | CREATION-CORE N6 | cleanup | a written finding with logs: works, works with conditions, or fails and how. It decides what CF3b must build | M | Opus 5.5 medium |

### Wave 4 · Actors: the crowd, the Rollers, the Inspector; the Lua screens; emotes

| Id | Scope | Inputs | Depends on | Proof | Size | Model |
|---|---|---|---|---|---|---|
| **E1** | (moved to wave 1; can start on a shipped map from a bench before the blockout exists) Actor kit, first use: one crowd body. Probes in order, each measured: (1) a script model playing stock zombie clips, seen by a client; (2) its entity cost with head and hit volumes; (3) **bullet hits** by the three routes of `07-ENEMIES.md` 2.2, 100 shots logged with hit locations, clone calls counted; (4) movement on the shared flow field with the anti-stuck rules; (5) script attack; (6) the one enemy registry | `07-ENEMIES.md` 2.2 | TF1, TF8, TF9 | each probe has a pass or fail line in the result; cost per body for 1, 20, 54 on the server meter; a written verdict: hybrid mode is possible, possible with limits (and which cap), or not possible | L | Opus 5.5 medium |
| **E2** | The crowd to its cap, in steps that each end in a measure: (a) spawner integration and the registry under every system that lists enemies; (b) promotion; (c) 36, then 48, then 62, then 78, each only while the entity ledger, the server meter and the network measure hold; (d) the seven proofs | `07` 2.2 to 2.5 | E1 passed, W3 (a dense zone), TF5, ST1 | **the seven proofs of `07-ENEMIES.md` 2.5**; the cap that ships is the highest step that passed, stated as such | XL in four steps | Opus 5.5 medium |
| **E3** | The Rollers: three bodies, 17 clips, behaviour, the round. Split: first one clip and one body measured in the game (the glide), then the rest | `07` 4 | C1, C2, E1 (hits), looks pipeline (A1) | clips measured in the game against their source (C2's measure); behaviour plan (pass, coast, crash, conga, throw, counters); reviewers on footage; replaces the stand-in | XL in two steps | Opus 5.5 medium |
| **E4** | The Night Inspector: model, 19 clips with notetracks, behaviour, the inspection plates | `07` 3 | E3 (the kit proven on the easier enemy first) | attack timings read back against the table; lamp windows; the mark rules (earned points, skipped players); reviewers on footage; replaces the stand-in | XL in two steps | Opus 5.5 medium |
| **E5** | superseded by **CF2** (section 2b): native capacity is the real feature and is built in the client fork | | | | | |
| **UT** | The Lua Tab screen (three pages) on the lab client | `09-TAB-AND-HUD.md` | U1; H1 | layout as data clean at three resolutions and 1, 4, 8 players; reviewers on frames | L | Opus 5.5 medium |
| **M1** | Emote system: rules, cancels, the busy flag shared with T1 and Q1, built on what M0 found | `10-EMOTES.md` C, E | M0, C1, C2 | one clip of ours seen by a second client and measured | L | Opus 5.5 medium |
| **M2** | The 65 clips (19 library clips retargeted, 21 original dances and the calm set animated or retargeted), in two waves; rewrites the emote table from the review notes first | `10-EMOTES.md` A, B and its notes | M1; library access (an account sign-in is a human step: asked once, when the package starts) | each clip plays in a plan and passes the bone-error measure; five judged by reviewers | L | Opus 5.5 medium |
| **M3** | The server-drawn wheel (`.e`) for every player | `10-EMOTES.md` D, E | M1 | element budget; a plan picks all 65 by pointer | M | Opus 5.5 medium |
| **M4** | The Lua wheel on the lab client | `10-EMOTES.md` D | U1, M1 | layout as data; input latency under 150 ms | M | Opus 5.5 medium |
| **L1, L2** | Hero looks version 2 and the eight zombie outfits (their own thread, from the earlier hand-off; costume texts corrected in `01-LORE.md` 7 and 8) | `heroes\ART-DIRECTION.md`, `ZOMBIE-ROSTER.md`, `01-LORE.md` | A1 | reviewers at 7 of 10 against stock characters, in the game | XL | Opus 5.5 medium |

### 2a · Packages added after the reviews

| Id | Wave | Scope | Depends on | Proof | Size | Model |
|---|---|---|---|---|---|---|
| **TF8** | 0 | The ledgers. (1) Entities in absolute counts against the engine's 2,048 and the project's ceiling of 1,800, kept in the map source and checked by the ents lint and by a script counter in every soak; every package writes its worst case before it builds. (2) The template map's pools (trigger shapes, door blocker brush models, switchable light slots, probes, light-grid instances) counted against the bible's needs; the generator refuses a source that exceeds a pool | N2 | the counts for the present map equal a manual count; a source with one entity or one trigger too many is refused | M | Sonnet 5.5 medium for the counting, Opus 5.5 medium for the lint |
| **TF9** | 0 | The meters the budgets need and no tool gives today: cost of script per function and per thread on the dedicated server; server frame time over a session; graphics-card time per pass from a capture (the existing capture scripts) | cleanup | a provoked +1 ms of script on the server and a provoked heavy pass on the client are each found and named by the tool | L | Opus 5.5 medium |
| **TF10** | 0 | A static model with no twin in the template map: one kit model from another shipped map and one authored model compiled as static models, lit by the light grid, no crash (earlier attempts crashed) | N1, N2 | both drawn in the game from a bench, counted as zero entities; the crash of the earlier attempt reproduced first and its cause named | L | Opus 5.5 medium |
| **ST1** | 1, right after W1b | The stress number: the blockout plus 6,000 stock props placed by a generator option (static if TF10 passed, and said so), plus 78 bodies (E1's if ready, else animated dummy models), measured at 1920 x 1080 and 1280 x 720 at fixed points on this map and on the shipped map, on the reference machine and on a second, weaker machine if the project has one; if it has none (to be stated in the result), the stand-in is the reference machine at 3840 x 2160 with the game limited to four processor cores | W1b, TF9 | a table of frame rate and frame-time percentiles; a written decision: budgets stand, budgets shrink (to what), or TF5's build half starts now | M | Opus 5.5 medium |
| **HO1** | 2 and 3 | Hero objects authored in Blender, each reviewed alone in the game before it is placed: the two rectifiers, the Bellows and its organ console, Vayle's car, the fork wall and the listening horn, clock faces and hands, the lever frame, the split-flap board's plates, the inspection plates, the Party Car's dressing, the Terminus signs and footprints | A1; TF10; `02-WORLD.md`, `04-PAP-QUEST.md` | each object: reviewers at 7 of 10 on frames from the game; its entity or static status written in the ledger | L, in batches of three objects | Opus 5.5 medium |
| **SI1** | 3 | Server integration and size: which server features are on for this map (the per-map feature profile: the limit of six perks, the away protection and its link to the Inspector's mark, the bank and `.pay` left as they are because the mark no longer reads unspent points); the map list entry and the 64-entry limit; the per-player journal file; **the size budget**: a number per zone and for the banks, tracked from W2 (the old nine-zone build was 507 MB plus 108 MB of banks, far too much to download: the target for the whole map is set after W2 from measured sizes, and textures are sized to meet it) | W2 | the feature profile test passes on a private server; the size table exists and W3 packages are held to it | M | Opus 5.5 medium |
| **M0** | 1 | Emote probe with **stock** clips, needing none of ours: can a stock full-body clip play on a real player's world model and be seen by a second client; can a third-person view be driven from the server | TF1 | yes or no for each, with frames; it decides CF4 early | S | Opus 5.5 medium |

### 2b · Client-capability packages (the project's fork of the client; clean, minimal, proposable later)

Each is separate, with its own test, so that it can be offered to the client project when the owner decides.
None is posted now. Order: CF3a, CF1, CF5, CF3b, CF4 (only if M0 says so), CF2. CF2 is the exception to
"small": it is a deep change in two programs, kept as clean as its nature allows, and it is last. Details and fallbacks: `14-CLIENT-CAPABILITIES.md`.

| Id | Capability | Needed by | Proof | Size | Model |
|---|---|---|---|---|---|
| **CF1** | Lua and LUI from a mod or map zone (already merged in the client project's development line, unreleased; the fork's copy stays identical to that change) plus two small additions: named custom client-to-server UI events (today only four retail names can be reused) and a key binding that a Lua screen can register | UT, M4, perk icons in the stock row | the Maxis Lua tier rendered on a fork client for the first time; one custom event round trip; a bound key opens a screen; the official client joining the same server shows the server-drawn tier with no error | M | Opus 5.5 medium |
| **CF2** | Agent capacity of 96 in server and client (78 ordinary zombies, specials, margin), negotiated at connect: a server started with the capacity profile accepts only clients that have it and tells any other client why in one clear sentence | E2's native mode | the seven proofs of `07-ENEMIES.md` 2.5 with real agents; the old failure (invisible beyond 24, the crash) reproduced first, then fixed with its cause named; an official client is refused cleanly | XL | Opus 5.5 medium |
| **CF3a** | **First fork package.** A failed download (mod or map) returns to the menu with a message instead of closing the client. The smallest change; it protects every player today, whenever the servers' mod changes | everything that is downloaded | a download cut mid-way on a fork client: menu, message, no crash; the same on mod and map | S | Opus 5.5 medium |
| **CF3b** | What TF6 finds missing for a custom map to arrive from a dedicated server on connect; then progress and resume; the map list surviving an installed map | TF6's finding | a fresh profile joins a private server, gets the map and plays | L | Opus 5.5 medium |
| **CF4** | Third-person view and a full-body animation on a player's world model, only if M1 shows that the stock client cannot do them from server script alone | M1 to M4 | M1's proof on a fork client; on the official client: first person for the emoter, and either others see the emote or the command answers "needs the updated client" | M | Opus 5.5 medium |
| **CF5** | Scoreboard and portraits for eight players without the per-frame error on slots 5 to 8 | UT, the servers' eight slots | eight clients, no interface error, frame rate equal to four | M | Opus 5.5 medium |

### Sound effects with the generator

| Id | Scope | Inputs | Depends on | Proof | Size | Model |
|---|---|---|---|---|---|---|
| **SFX1** | Generate the map's sound effects with the ElevenLabs tools from the briefs in `11-AUDIO-DIRECTION.md` (the complete list is there). **Credit budget**: the plan gives 30,000 credits a month, renewed on the 9th. Before every batch the package reads the remaining credits and stops if the batch would leave fewer than 5,000. Batches of at most 10 sounds. Each result is measured (length, peak, loudness against the target in its brief) and judged critically by a second listener agent against the brief's "must not sound like" before it is kept; a rejected result is regenerated at most twice, then its brief is rewritten. A call that may have succeeded is never repeated. Voice lines are not generated. The key is never printed | `11-AUDIO-DIRECTION.md`, sound-effects list | AU1's bank layout | every kept file has its measured values in a manifest beside it and the format the bank needs; credits used are reported per batch | L | Opus 5.5 medium for the calls and the judging; Sonnet 5.5 medium for measuring and the manifest |

### Wave 5 · Whole-map proof

| Id | Scope | Proof | Size | Model |
|---|---|---|---|---|
| **Z1** | Full qualification of the map as one thing | one-hour soak with seven bots at the cap; network lab at 100 and 200 ms; the atlas of every place; an eight-player private session; the official client end to end (join, download, play to round 15); three independent reviewers scoring the **whole map against shipped maps: at least 7.5 of 10**; the ledger empty of open defects above "minor" | L | Opus 5.5 medium |
| **Z2** | The owner plays it | his word; deployment to the public servers is his separate decision, then both servers | | |

### Later (the owner's deferred todos; hooks are in `01-LORE.md` 12)

| Id | Scope | Hooks | Needs first |
|---|---|---|---|
| **X1** | The guest character: Evelyn Marsh, the Voice of the Rapid, in the Announcer's Booth | H4 | actor kit (E1 to E4), voice |
| **X2** | Voice lines with the voice generator: the Voice, the four roles, Strand's tapes, the Inspector, the Conductor (slots in `11-AUDIO-DIRECTION.md`) | | the owner's choice of voices; credits checked before any batch |
| **X3** | The main quest: make the run complete | H1, H3, H7, H8, H10 | the map accepted |
| **X4** | The boss fight at the second platform | H2, H5, H6 | actor kit; X3 |

## 3. Order and what blocks what

```
cleanup done ──> N1, N2 landed
wave 0 (tools, in parallel):  TF1   TF2   TF4   TF8   TF9   TF10   TF3   TF7   TF6 (on the present map)   CF3a
wave 1 (playable):            W1a ─> W1b ─> ST1          E1 (may start on a shipped map)     M0
                              then Q1, T1, E0, H1 in parallel on the blockout
wave 2 (the look, proven):    W2 (two rooms)   TF5 build half if ST1 says so   SI1 size budget
                              K1   P1   WW1   HO1 first batch   CF1
wave 3 (the map fills in):    W3a  W3b  W3c  W3d   W4   W5   T2   P2   WW2  WW3  WW4   AU1 ─> SFX1   CF5  CF3b
wave 4 (actors, screens):     E2 (steps to the cap)   C1 ─> C2 ─> E3 ─> E4     UT   M1 ─> M2, M3, M4   CF4?   CF2
wave 5:                       Z1 ─> Z2 (the owner)          L1, L2 run in their own thread throughout
```

What a player could be given after each wave (if the owner chose to): after wave 1, the whole new layout
with quest, Capsule Post and stand-in enemies, grey in the new rooms and as good as today in the kept ones;
after wave 2, two finished rooms and the first weapon and perks; after wave 3, the finished map at cap 24
with stock stand-ins; after wave 4, the crowd, the Rollers, the Inspector and the screens, each only if its
probes passed.

Tool first, concretely: TF4 (build time) and TF1 (tests without a client) come before the first package that
needs many builds; the meters (TF9) come before the first budget is claimed; the ledgers (TF8) before the
first entity is spent; ST1 before any dressing budget is trusted; E1's probes before anything is designed
around a crowd body.

Running at the same time without touching the same files: all of wave 0; Q1, T1, E0 and H1 after W1b; the
four dressing packages (one district each) and the three weapon packages. Builds stay exclusive on the
machine, so packages queue their builds.

## 4. The first things each sub-thread should distrust

1. The walking times, areas and budgets in `02-WORLD.md` are plan estimates until TF2 prints the real ones.
2. "Stock zombie clips play on a script model" (E1) and "a zombie can be held at a waiting place from script"
   (WW2) are assumptions; each is the first probe of its package and has a written fallback.
3. The stock perk table accepting a new perk (P1), the three-way alternate-mode chain (WW2), the camo index of
   a custom map and any scrolling technique (K1), replacing the scoreboard on Tab from Lua (UT), third
   person on a real player (M1): all unproven, all first probes, all with fallbacks in their chapters.
4. Unproven and first-probed in their packages, with written fallbacks: bullet hits on a script body and its
   entity cost (E1); static models without a template twin (TF10); a sticking projectile, the aim button as a
   trigger, a continuous spray, a zombie held at a waiting place (WW2 to WW4); a decoy as a zombie target
   (P1); new camo rows (K1); water, rain, an open sky, changing screens (`02-WORLD.md` 8.1); what the stock
   spawner does when every player is in a zone with no spawners (Q1); a rider's zone during a ride (T1).
5. The readiness documents disagree with each other on what is merged (`research/A-tools-readiness.md`
   section 6). Check the main lines, not the tables, before assuming a tool is there.

## 5. For every package: player delivery, performance budget, fallback

"An ordinary machine" has no measured stand-in in the project yet: every figure comes from one reference
machine (i5-13400F, RTX 3080, 1280 x 720). So budgets are written as **parity with the shipped map**: with
four players and a full wave, Station Zero must hold at least **85 %** of the shipped map's frame rate (one number, the same as
`07-ENEMIES.md` 2.4), measured at fixed points on both maps, three runs a side, at 1920 x 1080 as well as
1280 x 720 (at the low resolution on the fast reference machine a map with no culling is limited by the
processor and hides its real cost). The first weaker-machine number comes from ST1 in wave 1, not at the end.
"Four players and a full wave" on one machine is produced with bots on the server and one measuring client;
proofs that need several real clients say so and count their join retries. Server-side and graphics-card
figures below are measured with TF9's meters; until TF9 exists they are targets, not claims.

| Package | How it reaches a player's game by itself | Budget it must hold (four players, full wave) | Fallback on today's official client |
|---|---|---|---|
| TF1, TF2, TF4, TF7 | tools: nothing reaches players | not applicable | not applicable |
| TF3, W1, W2, W3a to W3d, W5 | inside the map's own files, downloaded on connect (TF6 and CF3) | whole map: parity with the shipped map; each dressed zone re-measured: no zone may cost more than 0.4 ms of frame time over its blockout state at any atlas point | recommendation to the owner: until TF6 or CF3b succeeds, private test servers only (`14-CLIENT-CAPABILITIES.md`); whether and where the map is offered is his decision |
| TF5 | part of the map build | the parity rule at every atlas point with full dressing | the first-version prop budget |
| TF6, CF3a, CF3b | the client's own download | the download does not stall other players; rate as measured on the servers' file host | none that is acceptable: a manual install breaks the rule that online content installs itself. Until TF6 or CF3b succeeds the map stays on private test servers (a recommendation to the owner); a client is never sent into a download that can close it |
| Q1, T1, T2, W4, E0 | server scripts inside the map; nothing else to download | under 0.3 ms of server frame together; a ride or the teleport causes no frame over 33 ms for anyone | none needed: stock client features only |
| H1, M3 | drawn by the server; no download | at most 24 owned HUD elements per player; writes within 24 per 10 s | this is the fallback tier itself |
| UT, M4 | Lua in the map's own zone; needs CF1 in the client | under 0.2 ms of client frame while open; nothing while closed | the server-drawn tier (H1, M3) |
| P1, P2 | scripts and models in the map zone; icons as 2D materials in the map zone | under 0.1 ms of server frame; machines counted in their zone's budget | icons drawn by the server beside the stock perk row |
| K1 | materials in the map's own zone | four upgraded weapons on screen within noise of the stock camo | the static layer if no stock scrolling technique exists |
| WW1 to WW4 | weapon assets in the map's own zone, delivered with the map (the global mod is the owner's option, see `05`) | four players firing wonder weapons into a full wave: effects under 0.5 ms of client frame, scripts under 0.5 ms of server frame; per player at most 2 fences, 3 slicks, 6 stakes; 12 tokens in all | donor animation sets until our own animations can play; nothing else depends on the client |
| AU1, SFX1 | the map's sound bank files, downloaded with the map | at most 36 loops audible; bank inside the map's size budget | none needed |
| E1, E2 in hybrid mode | server scripts; stock models and clips already in the game | the seven proofs; crowd update and flow field under 4 ms of server frame; clients at the parity rule with 78 bodies | this is the official-client mode of "78" |
| CF2, E2 in native mode | needs the fork client and a server capacity profile | the seven proofs with real agents | the hybrid crowd on every server that official clients join; a capacity server refuses an official client with one sentence |
| E3, E4 | models and clips in the map zone, played by server script through the actor kit | 24 Rollers or 2 Inspectors: under 0.5 ms of client frame and under 1 ms of server frame; thrown skates in the entity ledger | the stock stand-ins (E0) wherever our clips cannot play or bodies cannot be hit |
| M0, M1, M2, CF4 | clips in the map's own zone (the global mod is the owner's option, see `10`) | an emote costs nothing to players who are not looking at it; eight players emoting under 0.3 ms | first person for the emoter, or a clear "needs the updated client" reply |
| TF8, TF9, TF10, ST1 | tools and measures: nothing reaches players | not applicable (they are what makes the other budgets measurable) | not applicable |
| HO1 | objects in the map zone | each object's triangle and entity cost written in the ledger; no object over 0.05 ms at its closest view | a stock model of the same footprint until the object passes review |
| SI1 | server configuration and the per-player journal file | the journal file is read once at connect and written on change only | without the journal file the Tab shows the match's finds only |
| CF1, CF5 | fork client | no cost when unused | the server-drawn tier; the four-row stock scoreboard |
| L1, L2 | models in the map zone | body triangle counts at the stock bodies' (about 17,000 for a hero); 78 zombies inside the parity rule | stock bodies |
| Z1 | not applicable | the parity rule, the soak, the network lab, eight players, the first ordinary-machine number | not applicable |
