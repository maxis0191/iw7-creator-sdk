# D - State of the earlier Station Zero (cp_iwz) work, read critically

Researcher: read-only pass over `<runtime>/iwz-stage2\` (everything except `bible\`).
Date of source material: 2026-11-06 to 2026-11-10 (work paused by the owner 2026-11-09). Account and payment details that
appear in `heroes\HANDOFF.md` are deliberately not reproduced here.

Root = `<runtime>/iwz-stage2\` (abbreviated `S2\` below).

Folders present: `art, assets, audio, darkness, fx, gameplay, heroes, kitimport, level, lightmaps, server-profile,
smodels, srcpkg-shared, train, vision, volumes` plus `CONTEXT.md`, `LEVEL-DESIGN.md`. Per-topic notes are
`REPORT*.md` / `NOTES.md` in each. About 900 KB of markdown in total; I read the CONTEXT, LEVEL-DESIGN, all of heroes\ (docs),
all `vision\*\CONSOLIDATED.md`, every `review-A/B.md` header and score table, the `level`, `train`, `darkness`, `gameplay`,
`audio`, `fx`, `art`, `lightmaps`, `assets`, `smodels`, `kitimport`, `volumes`, `server-profile` reports and the key parts of the
long `NOTES.md` files (level NOTES read nearly in full). I did not open the 3250 frame images or the `g25-fixlist.md` beyond its first
sections.

---

## 1. Lore, premise, names and tone already decided

There is no standalone story document. The fiction is spread across four places: `S2\LEVEL-DESIGN.md` (tone line), `S2\heroes\ART-DIRECTION.md`
and `ZOMBIE-ROSTER.md` (hero and zombie fiction), the 2D art (`S2\art\REPORT.md`, `REVIEW.md`, `imagegen-log.md`, folder `art\story`),
and the train/G-2 story props (`S2\train\`, `S2\level\NOTES.md`). Everything below is quoted or paraphrased from those.

### Premise and tone (exact quotes)

- `S2\CONTEXT.md` line 3-8, the owner's request (2026-11-06): "turn Station Zero (`cp_iwz`, a generated IW7 zombies usermap that today is plain
  boxes with flat lighting) into a polished custom zombies map at the level of the IWZ (Infinite Warfare Zombies) maps". And: "Easter egg: a hidden BO3
  teddy bear with the BO1/BO2/BO3 hidden-song hint sound; activating it plays "Abracadavre" (BO1 Ascension) as the hidden song. Weapons stay the stock IWZ
  Spaceland ones".
- `S2\LEVEL-DESIGN.md` line 3-7: "Tone: IWZ retro B-movie. "Station Zero" is a 1980s metro station sealed after "the incident": the last train
  never left. White ceramic tiles with a black tile band, yellow platform-edge safety line, rusty steel, flickering
  fluorescents, warm sodium lamps in the maintenance wing, emergency red in the control room. Dirt, water stains,
  blood decals, debris piles where the street exits collapsed."
- `S2\heroes\ART-DIRECTION.md` line 3-6: "Map fiction: "STATION ZERO" is one more Willard Wyler B-movie. A 1980s metro station sealed after "the incident";
  the last train never left. Grimy white tile, yellow platform line, sodium lamps, red emergency light, signal relays.
  Like every IWZ map, the four actors are re-cast in roles of the film".
- `S2\heroes\ZOMBIE-ROSTER.md` line 3-5: "Who they were: the passengers of the last train, the night staff of the station, and the cleanup crew sent in after
  "the incident". 1980s New York-style metro. Common treatment: IWZ photoreal zombies, grey-green decayed skin,
  torn and soot-blackened clothes, dried and fresh blood, subway grime, faint amber glowing eyes."
- `S2\vision\CHECKLIST.md` class 7: "does the frame say "abandoned subway station after an incident, alone, dread"? Missing storytelling (abandoned belongings,
  notices, signs of what happened), wrong tone (clean, bright, showroom)."
- Darkness design brief (`S2\level\g25-fixlist.md` section D, `S2\darkness\REPORT.md`): pitch dark until the generator is switched on; amber hint glow at
  buys/doors/perks; route of emergency lamps hall -> platform A -> maintenance corridor -> generator room; power-on sequence "bank by bank starting at the generator" with
  stuttering lamps and a "garbled main power on" PA. The documents do not tie this to a narrative beat; it is a mechanic.

### Facts that the 2D art and story props establish (this is the actual lore, never gathered in one place)

From `S2\art\REPORT.md`, `REVIEW.md`, `imagegen-log.md`, `S2\train\REPORT.md`, `S2\level\NOTES.md` and the vision reviews:

- The transit line is branded "ZERO LINE" (badge on clock faces, a "Zero Line HELP POINT" plate, car destination blind "ZERO LINE / NOT IN SERVICE", then "ZERO LINE 23:47 / 047 / NOT IN SERVICE").
- The incident time is 23:47. The stopped clock face has "Hands at 23:47, second hand at 37 s, red 13-24 inner ring" (art\REPORT). The departures board shows
  every row "SERVICE SUSPENDED" with header clock 23:47 and rows named after the IWZ maps ("Cosmic Heights, Redwoods, Arcadia, Polar Peak"). The evacuation notice reads
  "EFFECTIVE 23:47", with a QUARANTINE stamp and "report any bite" (art\REVIEW).
- The last train is run 047 ("train 047 held at Platform A" on the evacuation signal diagram; RUN 047 plates on the cab). Car numbers 048/049 were never done.
- G-2 is the station's diesel generator. Placard text read in game (vision g27d review B): "G-2 LOCKED OUT / DO NOT RESTART / TRIPPED 23:47 / BY ORDER OF THE ENGINEER"; the main breaker
  carries a red lockout tag 0447 "TRIPPED 23:47 DO NOT RESTART" (train NOTES) - which is the stock power switch the player must throw. The drawn notice also says "re-energise the third rail".
  The documents never say why the player is allowed to restart it.
- A night-shift roster with an empty OUT column: "OUT not signed ... Control informed 23:55" (g27d review B: "the best single story beat in the map").
  Daniel Malone, one of the missing-person posters, "is on the roster".
- Three "missing" posters: Daniel Malone (46, photocopied, on the roster), Linda Prescott (28, colour print, party hat, "took the last train home"), Walter Hughes (67, rain-faded). Phone numbers 555-01xx. All fictional adults.
- Closed-station notices in three layers/eras: a 1984 serif notice, an engineering notice, a hurried slip (so the station had been closed once before). The old station (platform B) has "STATION CLOSED" notices, boarded windows, green dado.
- Posters: "THE LAST TRAIN" (painting of a commuter in a trench coat with a zombie hand from the track pit; palette cream, signal yellow, transit red, navy, mint), "THE CITY ABOVE IS NEXT" (composed STATION ZERO poster, zombies rising from a rainy stairwell, painted Z on a green station disc),
  "MIND THE GAP", and a broken light-box ad "THE BEACH IS 40 MINUTES AWAY" (Radioactive Beach; an in-joke referencing the other IWZ map). Meta/fourth-wall poster text was removed ("the poster's "custom map" line replaced", level REPORT-g25) - so a decision exists: no fourth-wall text.
- Zombie roster fiction: "the passengers of the last train, the night staff of the station, and the cleanup crew sent in after the incident".
- Original-brand rule: the punk gang patch was renamed "ZERO KINGS" to avoid "WARRIORS"; a poster batch was rejected because it showed the London Underground roundel (heroes\HANDOFF, art\imagegen-log). So: nothing recognisably copyrighted/trademarked.
- Hidden-song easter egg: teddy bear (BO3 `p7_zm_teddybear`) on the luggage rack above a seat inside the parked hero train car, behind a duffel bag, at (-200, 1445, -214) in the early build, later "on the hero car floor at (1425.5, 1448, -323) behind a bag"; hold Use; the hint loop (BO1 meteor hum) is audible 60-500 units;
  activation plays Abracadavre once for everyone (audio\REPORT-w1/w2/w3).
- Zone list and flow (LEVEL-DESIGN section "Zones and flow"): ticket_hall (start), stair_a, platform_a (the hero platform with the parked train), maint_corridor, generator_room, control_room (Pack-a-Punch behind a shutter), service_tunnel, platform_b ("old station"), stair_b. A loop for kiting and a branch to the control room.
- Gameplay hooks already designed (LEVEL-DESIGN): Pack-a-Punch quest of three signal relays (platform A column, old-station ticket booth, generator-room control panel), a "Third Rail" trap on the platform A track pit (25 s, 60 s cooldown, costs 750), the generator power switch, four stock perks relocated, five stock wall buys.

Not stated anywhere: what "the incident" was (the notices say quarantine and "report any bite", i.e. an outbreak; no cause); who the four heroes are in-universe; why they are there; any narrator or voiced character (voice lines are listed as a later item in the owner's memory file only); any ending. There is no per-character lore beyond the film roles.

---

## 2. Heroes: `S2\heroes\ART-DIRECTION.md` (v1, 2026-11-09) in full, plus `HANDOFF.md`, `fit\NOTES.md`, `writer\NOTES.md`

Names (fandom wiki, as quoted): Aaron "A.J." Jordaniels, Andre Wright, Poindexter Zittermann, Sally Simpson. Same stock faces and heads kept. Same colour identity: A.J. blue/red, Andre red, Poindexter green, Sally cyan/pink.

| Hero | Film role | Costume | Hair / head | Signature prop | Colour accent |
|---|---|---|---|---|---|
| A.J. (jock) | The Transit Cop | 1980s metro transit police: navy uniform shirt, shoulder patches "MTA POLICE", gold shield, rolled sleeves over a white tee, duty belt (radio, cuffs, nightstick loop), dark trousers, black boots, aviators hooked in the collar, torn sleeve, grime | slicked-back hair, eight-point patrol cap pushed back, thick 80s mustache | nightstick + Maglite on belt | navy + red trim |
| Andre (rapper) | The Graffiti King | paint-dripped olive/red MA-1 bomber with a hand-painted back piece, hoodie underneath, baggy painter jeans with spray stains, fat-laced shell-toe sneakers | backwards cap over a do-rag, headphones round the neck | spray-can bandolier + painter's respirator on the neck | red |
| Poindexter (nerd) | The Signal Engineer | transit authority orange coverall with silver reflective bands, green tee under it, tool belt (multimeter, wire spools, pliers), rubber lineman gloves clipped on the belt, pocket protector, work boots | yellow hard hat with headlamp, safety goggles over taped glasses | clipboard with signal schematics | green + safety orange |
| Sally (valley girl) | The Eyewitness Reporter | 80s TV field reporter: teal trench coat over a hot-pink blazer with big shoulder pads, white blouse with bow, high-waisted pleated trousers, white high-top aerobics sneakers, press pass on a lanyard | big permed 80s volume hair, gold hoop earrings | station microphone with a "CH 9 EYEWITNESS" flag, camera strap | cyan + pink |

Alternatives kept (art-direction file): A.J. varsity-bomber tough; Andre B-boy tracksuit; Poindexter new-wave punk nerd; Sally punk commuter.

Personality or backstory: not stated. The file gives costumes only. (The "Transit Cop", "Signal Engineer" and "Eyewitness Reporter" roles do tie into the map's props - MTA/transit police, signal relays in the PaP quest, a press angle - but nobody wrote that link down.)

Art-direction production rules (quoted): "Stock heads are kept (rigid on j_spine4/j_neck/j_head/j_helmet); new hair/headwear = new rigid head-attached models. Bodies: new skinned meshes on the stock 105-bone body skeleton; first-person arms rebuilt on the 114-bone viewmodel
skeleton (sleeves/gloves must match the body). Separate garments, not one fused mesh; A-pose to match the stock bind pose. Budget per body: about the stock count (jock body LOD0 ~17k tris over 5 surfaces), max 4 weights per vertex."

Pipeline summary (HANDOFF section 2): ChatGPT-image concept turnarounds (front/side/back per hero), image-to-3D (Hi3D v3.0 for heroes, Tencent Hunyuan 3D v3.1 for zombies), then a Blender "fit" pipeline that aligns the AI mesh to the stock skeleton, transfers weights, bakes textures, and a custom IW7 skinned-model writer + material cloning into the zone. Concept art lives in `S2\heroes\concepts\` (`<hero>_v1_0.png` sheets, `_front/_left/_back`), 3D in `S2\heroes\gen3d\`.

### Status of each look (state at the 2026-11-09 pause)

| Hero | Concept | AI 3D | Blender fit | In game (v1) | Review round 1 (2 independent reviewers) |
|---|---|---|---|---|---|
| A.J. | done | Hi3D v3.0 done | READY v2 (mustache, cap patch, forearm tone). Offline: leg pose RMS 23/22 -> 6/7 mm, arms 47/56 -> 10/10 mm, body 10,720 + 11,257 tris, hair 6,464 tris | PROVEN in game as v1 | DO NOT SHIP |
| Andre | done | Hi3D done | READY, "cap edge band". Body 11,657 + 10,260 tris | PROVEN in game as v1 | DO NOT SHIP |
| Poindexter | done | Hi3D done | READY, "patchy forearms". Body 7,379 + 14,573 tris | PROVEN in game as v1 | DO NOT SHIP |
| Sally | done, then redone (`sally2_*`: open coat, no bag, arms clear) | Hi3D v1 mesh had arms fused to the bag/coat; Hunyuan v2 mesh made | FAILED: neck-height scale 1.666 vs ICP 1.316, wrist tuck moved vertices up to 277 mm, edge stretch 68-132x, 708 bad edges in crouch | not run anywhere | none |

Scores (HANDOFF section 3): "Heroes v1 review round 1: both reviewers DO NOT SHIP (A: 4/4/3, B: 3/3/2)". The hero order of the three numbers is not stated; it is presumably A.J./Andre/Poindexter (the frame order in the review pack). The review prompt asks for scores "vs stock quality" (1-10) and the text of the reviewers is not saved in the folder (only the prompt `S2\heroes\writer\heroes_v1\review_r1\REVIEW_PROMPT.md` and the frames), so only the numbers and the HANDOFF's list of defects survive.

Defects listed after review (HANDOFF section 4, quoted in substance): faces looked black/missing (fixture attached heads wrongly; fixed by linking as own model, real player path untested); caps/hard hat/mustache not drawn; first-person arms (A.J. sleeves read as skin tubes with dark tears; Andre posterised orange-brown forearms and a red jacket lump clipping, left/right cuffs mismatch; Poindexter bare stock skin, no orange sleeve);
wrist skin-tone breaks (A.J. orange-pink, Poindexter pale, Andre near-black); textures "dark, flat, blurry; ~55% of each atlas empty, ~75% of A.J. AO unbaked, empty texels at max gloss"; torso folds at shoulders/spine in run/idle; silhouette drift from the concept (A.J. slimmer, Andre jacket shorter, Poindexter head small); seams; feet hovering; lighting stream approximated up to 6.8 in from the nearest stock vertex; 700-1300 vertices per body with more than 4 influences (clamped).

v2 build (newer READY fits, DirectX normal flip, packing fixes) exists as `heroes_v2\um\cp_iwz.ff` sha256 AD47695D...FC35B1 but "built, NOT run, NOT reviewed". Never seen as a real player in third person; never in a dedicated/other client; late join untested; Sally nowhere.

---

## 3. Zombies: `S2\heroes\ZOMBIE-ROSTER.md` (v1, 2026-11-09) in full

| # | Sex | Outfit | Key read at distance |
|---|---|---|---|
| M1 | male | The Wall Street Commuter: grey 80s double-breasted suit, loosened wide red tie, beige trench coat, Walkman headphones round the neck | beige trench + red tie |
| M2 | male | The Conductor: navy transit conductor uniform, peaked cap, ticket punch on a chain, brass buttons | navy + brass, cap |
| M3 | male | The Warriors-style gang punk: sleeveless leather vest with gang back patch over bare arms, studded wristbands, ripped jeans, mohawk, combat boots | mohawk + vest patch |
| M4 | male | The Track Worker: orange high-vis vest over a plaid flannel shirt, hard hat, work gloves, carpenter jeans | orange vest |
| F1 | female | The Office Commuter: shoulder-pad silk blouse, pencil skirt, nude tights, white sneakers with socks over them, big perm, tote bag strap | shoulder pads + sneakers |
| F2 | female | The Token Booth Clerk: transit uniform cardigan, name tag, glasses on a chain, knee-length uniform skirt | cardigan + glasses chain |
| F3 | female | The Club Kid: neon new-wave look, oversized off-shoulder sweatshirt, leggings, leg warmers, side ponytail, rubber bracelets | neon colours |
| F4 | female | The Hazmat Cleanup Crew (C.H.U.D. nod): yellow hazmat suit torn open, gas mask hanging off, rubber boots | yellow suit (also usable as a later special/elite) |

Rarity/role tiers: not stated (every zombie is a standard "generic zombie model"; only F4 is flagged as a possible later special/elite). No specials, bosses or named elites are designed beyond the stock clown and brute that Spaceland's round logic already runs. Common treatment: photoreal grey-green decayed skin, soot, blood, amber glowing eyes. The doc notes an "IW7 constraint (to confirm by the model-system audit)": outfits must be modular (torso, arms, legs, normal and damaged states, gore stages), heads separate.

Status: concept sheets done for all 8 (some views missing: M1, M2, F1 side views were refused by the image safety filter, so those three have front+back only). The punk patch reads "ZERO KINGS". AI 3D done for all 8 (Hunyuan 3D v3.1; F4 via the web app). Only M1 went through the kit (`S2\heroes\zombies\NOTES.md`): offline fit + split into torso/arms/legs/head + 5 damaged gibs + caps + materials + scriptable done and "PROVEN_LOCAL"; "NOT in a zone, NOT in game". M2-M4 and F1-F4: "3D models ready; kit not run". Known M1 issues: torso has 8 cap loops instead of 5; some coat shreds on legs; only 48% of coat weights transferred directly; gibs written as skinned 1-bone surfaces while stock gibs are rigid physics debris and "may not render"; straight leg gibs; one LOD only (crowd performance risk); the bones-only `zombie_male_outfit_1` xmodel must also be cloned (NOT_PROVEN); the stock roster list must be overridden after `cp_zmb::setup_generic_zombie_model_list()`. No reviewer has seen a zombie in a frame; no zombie is in game, no dismemberment, no crowd performance test.

---

## 4. Map reviews: every remark and score, grouped

Review method (`S2\vision\CHECKLIST.md`): independent agents look at full-resolution frames "as a demanding Call of Duty Zombies level artist and QA lead" against shipped IWZ maps (Spaceland, Rave, Shaolin, Attack, Beast). Eight defect classes (impossible geometry, fake placeholder construction, opaque/empty interiors, texture problems, lighting problems, composition, identity/mood, gameplay readability) and three severities. Rule added after g24: "Luma numbers, check tallies and previous reports are NOT evidence of quality. Look at the pixels." Rule added after g27: a fix counts only with a same-camera before/after crop pair (a "moved camera proves nothing").

### 4.1 Score history (0-10 "against shipped IWZ")

| Build | Reviewer A | Reviewer B | Reviewer C | Frames reviewed |
|---|---|---|---|---|
| g24 | zone scores 2-5, no overall number (platform_a 2, ticket_hall 2, generator 2) | zones 2-4, signage 7, kit props 6 | 95 findings, 28 BLOQUANT | not stated |
| g25t | 4.5 | zones 2-5 | zones 2.5-6 | 564 frames, 141 sheets |
| g27 | 4.8 | 4.7 | 4.5 (62 findings) | 559 frames |
| g27d | 5.0 | 5.5 | 4.8 (54 findings: 4 BLOQUANT, 26 IMPORTANT, 24 MINEUR) | 650 frames, 163 sheets |

Honest reading: three build rounds and roughly 700 frames gained about half a point; the best single score is 5.5. The reviewers never said "ship". The only element consistently scored 6-7 across all reviews is the 2D signage and story art.

### 4.2 Zone scores, latest (g27d)

| Zone | A | B | Verdict (reviewers' words, condensed) |
|---|---|---|---|
| Platform A (hero) | 4.5 | 6 | train with 047 and 23:47 headsign, luggage, cordons and the red tunnel mouth are a strong hero view; black floor stains read as holes, blue walkway, orange east flood, floating tunnel-end rubble |
| Platform B (old station) | 6.0 | 6.5 | best zone: boarded windows, green dado, layered STATION CLOSED notices, a red beacon with a visible source, Bang Bangs perk pools; wall buy straddles the pilaster, shallow trackbed |
| Ticket hall | 6.5 | 6 | strongest storytelling (missing posters, 23:47 board, barricades, blood); still showroom-bright, blue wedge, chalk board under a poster |
| Control room | 4.0 | 5 | big empty shell, blank walls, maroon wash; the evacuation diagram is excellent; fake cage door |
| Generator room / G-2 | 5.0 | 6 | G-2 lockout story reads; perk machine buried behind crates, white plastic burn barrels, lime radiator, no visible scorch |
| Maintenance corridor | 5.0 | 5 | roster is the best beat; clean, sparse, overexposed, white lockers |
| Service tunnel | 5.0 | 4 | steam and cones help; too bright and clean; saturated blood pool; floating rubble |
| Stair A | 4.0 (shared with B) | 5 | up from 2; sterile, blue light on treads, near-black ceiling, clock too small |
| Stair B | 4.0 | 4.5 | lime cast, clean concrete, nothing at eye level |

Earlier zone score extremes for context: g24 platform_a 2 and ticket_hall 2, stair_a 3; g25 stair_a 2-2.5; g27 stair_a 2 (a black void panel and faceless clock persisted from g24 to g27).

### 4.3 Grouped remarks

**Layout / geometry / construction (impossible or fake objects)**
- g24 BLOQUANTs (all fixed since): a wall/beam standing across the railway (fx_1), a box train with void windows, concrete-cube turnstiles, black void panels at stair exits, faceless black clock, black window voids in platform B, green slab booths, fake collapse slab.
- g25-g27 remaining: white placeholder block at the stair-B door (was a wall-spawner vent), leaning slab through the STATION ZERO sign, green slabs in platform B, poster boards inside stair openings; all confirmed fixed in g27d.
- g27d still open: floating rubble tiers at the tunnel ends (all three reviewers, BLOQUANT), barricade planks seen at an angle sticking out like shelf stubs (C, BLOQUANT), white drums floating above the floor and fire coming out of closed clean plastic drums (BLOQUANT), Racin' Stripes perk buried behind crates (BLOQUANT), flat lime untextured G-2 radiator back/side, mirrored 047 on the plate back, slanted grey skirt under the near car end, box-like car end caps, white untextured cabinets/lockers, fake shallow cage door in the control room, clipping of signs into lintels/beams, chain-like handrails, sunk tyre, duplicate half-sunk G-2 stencil.
- Gameplay readability: wall-buy chalk unreadable on light tile, Platform B buys without a board or straddling a pilaster, no prices (added in g27e source), models rotated/offset from outlines, wrong silhouette.

**Lighting**
- Persistent across all builds: "flat, bright, showroom" light, no pools or dark gaps, unmotivated colour casts (pink/green/mustard in g24; blue cess walkway, orange flood Platform A east and hall corner, maroon control room, lime stair B, red east tunnel in g27d), coloured light with no visible fixture, flicker that did not change the light (g24/g25), pixelated ceiling halos, blotchy coffers, near-black stair ceiling with "housing blob" shadows (g27d).
- Reviewers' remedy (g27d B): "lower the fill everywhere except Platform B and keep only pools with a visible source".
- Pre-power vs lit: darkness agent targeted 2-5% luma before power; measured 7-18% (dk9) and then more bright after exposure tuning; lit-state fill too dark in maint corridor/service tunnel/stair B/Platform B (-0.09 to -0.19), balanced elsewhere.

**Detail / texture / decals**
- Trim textures were stretched 4-16x (fixed in g25 by measuring all 72 stock textures), black floor stains and "parallelograms" were the stock `dirt_water_stain_01` multiply decal (g27d: "black holes", A counted ~35 frames), repeated ghost-poster squares, repeated blood drags in rows, marble-veined/saturated blood pools, mustard drag smear, stretched dirt rectangles, "The Last Train" poster repeated 5-6x, pink spray, white tile looks sterile ("hospital").
- Ceiling glyphs (pale glyph patterns on stair/hall ceilings): g24 to g27; finally attributed to strip-light placement (g27d STRIP_DROP 20) after SSR, probe, material and lightmap theories were all disproved offline.

**Coherence / story**
- Identity: strongest positives are signage (7/10 on every build), the evacuation diagram, the roster, the missing posters, 23:47 everywhere. Weaknesses: story only readable up close until g27d; control room, stairs and corridors are blank walls; generator room had no hero (fixed by G-2); "Spaceland leftovers" (soda machines, astronaut standees, cart, Spaceland frames) removed in g26c.
- Train: g24 box train (BLOQUANT) -> g25 BO3 car with broken skirt/underframe -> g27 3-car BO3 set "finally a believable centrepiece" -> g27d "pass, now a centrepiece" with 047 plates, 23:47 headsign, bogies.

**Performance**
- Not a review category; measured separately (section 5).

### 4.4 What was fixed vs what remains (g27d -> g27e source)

Fixed and confirmed by same-camera proof in g27d (all three reviewers): stair_a black panel and clock, white block at stair B, posters in stair openings, green slabs, leaning slab, platform B sunk track, ceiling glyphs, story at eye level (047 plate, 23:47 headsign, G-2 danger placard, departures board).
Fixed in the unbuilt g27e source (SDK `codex/iwzmap-station-zero-v2` 68f70aa), unproven in any frame: tunnel-end rubble on the floor, no deck stains, perk approaches cleared, planks inside the frame depth (lint catches 64 planks), rusted drums grounded plus an open burn drum, coloured lights clamped (radius 96, 60 %), ceiling = ceiling_tile_01, control room lower fill and panic dressing, subway lockers, platform B bed 40 deep, 112 lit master clock in the hall, chalk boards on dark boards with prices, muted stair B green.
Open in the source too: G-2 scorch (no non-black decal), ghost lettering under GENERATOR, wall-buy model alignment, blue corner wedges, train items (radiator back, mirrored plate), flat lime radiator (train agent's asset), car numbers.

---

## 5. Measured facts

All from the repository's own measured runs; labels PROVEN/PROVEN_LOCAL as in the reports.

**Build artefact:** current reviewed build g27d: `S2\level\um_g27d\cp_iwz.ff` 507,161,300 bytes, sha256 C992476E179575932A99300AC9699283738077D938573A3DF17F86C538B688B2, plus `.sabl` 43 MB and `.sabs` 64.6 MB of audio banks. Kit import: 34 stock/foreign models, 157 new materials, 310 image headers (pixels stream from the base game paks); FX import: 8 vfx; "Successfully compiled fastfile".
**Counts:** ents.txt 3256 lines with 257 script_model entries; smodels.txt 170 static models (g22: 167 of 184 compiled static, five stayed script models because of a compiler bug); lights, 132 layout lights in g25 (46 emergency / 82 power / 4 flicker), 137 lights incl. car lights in the train build, 50 named power lights in the dark build d15, 72 in d16 (51 lamps + 21 fills); 28 FX placed in g25 (21 in the dark file); 22 trigger volumes (0 failures); 12 doors; 9 zones; nav plan 10,557 cells. Overall surface count: not stated. Static-prop count seen by the props check 289-300 (255-270 seen, 0 flagged).
**Frame rate:** the QA harness measured "~300 fps median at 1280x720" on the early build; g5: "290-384 fps, p95 4-5 ms". Real maps: g27 p95 4.2-4.4 ms, g26c worst-5% 5.3 ms, rounds p95 5.4 ms, worst single frame after load 153 ms (g26c) / 122 ms (g27, door purchase teleports); on g25t the first car entry hitched 2.8 s and the first door 1.9 s (disk streaming of ~2.1 GB, cut by smaller train images -34 MB; gone on g26c). Darkness build uncapped 1280x720: dark 2.18-2.40 ms mean (1/4/8 players), lit 2.33-2.40 ms (but only 3-7 bots, no bot flashlights, so the 8-light cost is unmeasured). FX: +0.08 to +0.15 ms mean. Static models: p50 2.05 ms p95 3.5 ms. Train kit: p50 1.71 ms p95 3.55-3.75 ms. Runner capped at com_maxfps 30 in an early train perf run (noticed and fixed). Hardware: RTX 3080. Client with a second client rendering on the same GPU: 4.2/8.0 ms.
**Build/bake time:** lightmap bake 206 s (g19), 235 s (g27d), 254.6 s (train t15), 313 s (d15), 495 s (d16, with more lights) at texel 6 / ambient 0.012; ZoneTool compile time per build: not stated. Older rc1 baked in 14-35 s. A full chain (generate + gate + bake + compile) is one scripted command (`level\tools\chain-g27d.sh`), but a visual verification cycle with capture + three reviewers takes hours and was repeatedly blocked by the shared-game lease or by the owner's own Main client.
**Offline gates passing on g27d/g27e source:** nav plan 0 fails, art lint 0, seams 0 open, navconn 1 component, flatness none, volume check 22/0, entity lint 0 warnings, audio anchors 0 errors, kit import missing [], FX missing []. The mood gate counts 0 flat black void frames. These gates pass while reviewers still score 5: they test construction, not beauty.
**Gameplay QA (harness `codex/iwzmap-playtest`, `S2\gameplay\`):** rounds 1 to 12 in 494-556 s with the wave-6 clown event (9-14 clowns) completing and the wave-10/11 brute spawning and dying; door purchases with a real F press work on g27; power, perks, relay quest (3/3), PaP shutter, Third Rail trap (3/3 killed), magic wheel all PROVEN_LOCAL; stairs A/B both directions 5/5 on g27c; platform_a <- service_tunnel spawners 6/6 on g27; only stock script errors remain (leaderboards, directors_cut). Open gameplay defects: east pit stairwell climb dies mid-stair (g27/g27c-d: east 3/5, west 1/5), crowd of 8 on stairs 6/8-7/8, bottom-landing spawners to the hall 2/5, player-only collision stops at (-3231,1636) in the service tunnel, a hardshell suitcase on the nav. A solid-step fix for the wells made it worse (0/10), flag turned off.
**Audio:** soundscape per zone -35.6 to -44.2 dBFS median; horror music replaced the stock cues (PA-chime leitmotif); each cue found in the in-game recording 0.08-0.17 s after trigger; Abracadavre PROVEN, real F press on the bear PROVEN; unresolved: 2-7 full-scale clicks under 12 ms per capture (game or capture tool, not proven); other soundscape elements not owner-heard.
**Darkness:** scripted lights switch bank by bank (PROVEN), fixed-exposure vision, flashlight (a cp_disco train spot copy on `tag_flash`); after switching to the M4 the flashlight vanished in dk6-dk9 but d15 (VF1) reports "M4 switch 0.436" so it was fixed there; other players' flashlights never seen by a second client (second client stuck at the title screen).

### Known bugs list (from the reports)

- **Wells:** the two pit stairwells (platform A track pit up to the deck) - zombies leave the bottom landing at pit height (z -383), the nav is 14 units under the ramp 34 units in and 36 under the top, so they do not take the ramp and some fall out of the world. 6 low risers instead of 4 tall ones did not fix it, solid blocks made it worse. Stock stairs study: stock walking surface is a clip sheet with ~8 unit risers, nav 4 above it; ours is a solid sheet with 16 unit risers and nav at 0. Stair A/B themselves pass.
- **Train:** BO3 car placed correctly; remaining: mirrored 047 plate back, diagonal crease on livery, skirt wedge, box end caps, cars 048/049 not numbered (needs 3 car models), emergency light inside the cars and cordons unproven, only kit_v5 ballast proven in e9/e10 (13/13).
- **Darkness:** lit state too dark in the corridors, other players' flashlights unproven, white haze around lit lamps, `setlightintensity` calibration inconclusive, motes (dust) never read in the dark, FX lavender halo on the emergency glow, flicker lamps "still don't change the actual light" (g25) then fixed through named lights.
- **Compiler/engine pitfalls hit:** static model with no light-grid template instance crashed (AV at iw7_ship+0xDCE6E7) - found after three incidents, five models excluded; generated trigger volumes had no physics shape (fixed by borrowing template boxes); template reflection probes caused ghost glyphs unless parked ("neutral probes"); only ~54 usable template trigger boxes; zone `require,techsets_cp_disco` hangs ZoneTool.
- **Open art:** "Linda poster repeated", fourth-wall line replaced, ad panel only lit with an emissive base (unproven), DDS mip path unproven, `wall_stain_01_dec` alpha on world quads unproven.

### The resume list explained ("well probes/fix -> train e11 -> g27e build -> QA -> reviews -> darkness")

From the owner memory note `station-zero-stage2-state.md` and `S2\level\NOTES.md` "PAUSED 2026-11-09" section:
1. **Well probes/fix (level):** run `pwsh level\tools\run-stairprobe.ps1 -Tag g27d -Set far` to see whether the level builder's probe reproduces QA's well failures (west 1/5, east 3/5); then fix the ramp foot one candidate at a time (longer bottom landing / ramp start like stairs A/B that pass; closed under-flight without step blocks; stock stair style), 5 probes per well; QA harness is the gate.
2. **Train e11 (train agent):** `chain_e11.ps1`: engine proof for the train t16 ports (banzai_v5, kit_v6, genset_v6, props_v4); e10 proved 13/13, e11 "never ran". Then hand the ports to the level.
3. **g27e build:** `level\tools\chain-g27e.sh`, fresh bake with darkness, FX and train integrated.
4. **QA:** the QA chain27d leftovers on g27e: wells, down cases with valid starts, routes, spawners/props, real F doors, rounds.
5. **Reviews:** `chain-g27e-capture.sh`, three independent reviewers on full frames, fixproof at the same cameras.
6. **Darkness:** corridor fill (lit state 14-16/45 views within tolerance), second-client key press via DLL, final build on g27e. Then unify runners, server PR, owner question about `.revive/.drop/.mule` on cp_iwz. Later: characters and voices.

Note the dependencies: darkness is last because it needs its own bake (a dark light list, not a reuse of the lit bake) and the g27e source; heroes and zombies (their own zone copies "frozen at level build g27dw") need a Stage-OutfitZone refresh after g27e and a merge of the hero zone copy and the zombie zone copy into one build.

---

## 6. Technique lessons recorded (what a rebuild must respect)

**Proven to work**
1. The generated-map route works end to end: generator (`station_zero2.py` in the SDK) -> ZoneTool `-iwzcompile` with a cp_zmb template -> `cp_iwz.ff` loads and plays in the private runner with real navigation, doors, power, perks, PaP quest, trap, wheel, rounds to 12 with clown and brute events. The world is a conservative Umbra tome, Havok collision, bfx navmesh; decor = script_model entries and compiled static models.
2. Lightmaps: the map ships its own baked lightmap (3-bounce baker `bake/lmbake.py`, BC6H atlas), decoded from the IW7 shader (E = A + B*Dz); engine-calibrated (rendered luma vs predicted correlation 0.61-0.88). Baker runs in 2-8 minutes. Light "groups" (emergency / power / flicker) and named switchable lights make a power-on sequence possible.
3. Collision/volumes: spawn and trigger volumes need a donor physics shape (`IWZ_TRIGGER_SHAPES`, whole-box rescale of unused template boxes); props need explicit clip boxes (stock cp_zmb props have no collision, "walked through 29/32" without them; 24/24 blocked with them).
4. Door blockers: script_brushmodel blockers kept from the template (`IWZ_KEEP_SUBMODELS=1`), a trigger_use per door (`door_buy`), and the level script has to remove the barricade dressing because the stock code only makes the blockers non-solid.
5. Foreign assets: BO3 and cp_disco/cp_final models render textured and lit in cp_iwz via kit import (images stay in base game pak files, so a custom map's footprint is small); BO3 car, track kit and G-2 were authored through Blender 4.5 and a GrayWolf export; train kit sizing by texel density cut 34 MB.
6. Audio: usermap sound banks via `soundbank,cp_iwz.all` -> `.sabl/.sabs` (needs 1024-sample frame audio or music is silent); sound design from stock sources plus synthesis; per-zone beds; hidden song with a real Use-hold; bear conversion needed three repairs.
7. QA by tools, not eyes: offline gates (plan, art lint with ~15 rules, seams, nav connectivity, flatness, density, volume check) run before every bake; engine probes (stair probe, error-journal DLL, perf sampler), emitcheck/forensics tools added late. The art lint did catch real defects (planks over frame depth, fake objects, colour casts without fixtures).
8. Fixed-exposure vision (`tonemapAuto 0`, `tonemapMaxExposure`) applied 8 s and 14 s after spawn is the way to make "dark" actually dark; `tonemapExposure` does nothing; lit particles do receive flashlight light.
9. Stock-asset-first rule: "no BO3 environment prop recommended" in the first asset survey; later it was reversed for the hero train, genset and props, each ported by hand. The final line: use IW7's 629 native BO3-named `p7_*` models, port only what the story needs.

**Failed or dangerous (do not repeat)**
- The compiler's static model route crashed three times on five models with no same-model light-grid donor; keep those as script_models.
- Generated box props pretending to be objects (turnstiles, desks, booths, trains) were repeatedly read as fake; any "box that stands in for" a real thing is a BLOQUANT in every review. A lint rule `fake-object` was added.
- Black materials: the IW7 cutout template ignores the colour (texts rendered black), the decal template is faint; composite the art into opaque faces. Brushed metal on generated boxes renders black; light-grid fallback probe is near-black unless the generator overwrites it with ambient.
- `r_lightMap` / `r_lightGridIntensity` forcing changes nothing and crashes the client. A `require,techsets_cp_disco` row hangs ZoneTool. `attach()` does not draw heads on script models (hero fixtures must link models). A script model has no per-instance material override (car numbers).
- Native flashlight and runtime lightmap swap do not exist in IW7; two baked states cannot be swapped at power; the darkness route is dark bake + scripted named lights + vision.
- `trigger` volumes without a physics shape; navmesh seams (areas join only on coincident edges); flat per-cell nav under a ramp makes agents fall - nav cells must carry sloped corner heights; 16-unit risers with ~12-degree off-nav ramp starts make zombies die at stair feet.
- Rubble/tiers "floating": origin and floor z conventions per model differ; always trace down. White/cream drums and cabinets from stock templates read as plastic and untextured; ground and rust them.
- Planks with random yaw/pitch read as shelf stubs when seen obliquely; constrain in plane and inside jamb depth.
- Moved cameras make before/after proof meaningless; claims of "fixed in source" were wrong three builds in a row (stair_a). The verification protocol (same-camera pairs) is the lesson.
- Using the shared game as the test bed: runs got blocked, discarded or corrupted when the owner started Main/Client (a Runtime lease cannot be released while any process runs from the base game); a hook refuses subagent REPORT.md writes; chains left stale leases/locks.
- AI content: ChatGPT/Aside image safety filters refuse zombie prompts mentioning wounds or flesh, three zombies have no side views; image generators invented real trademarks (London Underground roundel) - all text must be typeset from fonts, never model-generated.
- Hero pipeline (the largest unproven chain): writer bodies rendered black until the per-vertex SH probe stream was transferred; every setmodel'd model must be precached; the fit leaves ~55% of the atlas empty; AI meshes with fused coat/bag (Sally) need regeneration; 1-LOD writer models are a crowd performance risk.
- Cost/time lesson stated by reviewers: three reviewers cost hours and only move scores ~0.3-0.5 per round while 5+ BLOQUANT classes (floors, lighting, rubble) recur; the lint passing is no sign of beauty.

---

## 7. Critical judgement (mine, not the earlier agents')

### Sound and proven, worth keeping

- **The pipeline and the tooling for a generated custom map** (compiler route, baker, kit import, door/volume/trigger tricks, art lint gates, QA harness, audio bank route, darkness module, hero/zombie writer): genuinely proven in engine, documented, reusable. A rebuild should reuse these, not re-derive them. Evidence: 12 doors, relay quest, rounds to 12, clown/brute events, runtime stable, no zombie escape through closed doors.
- **The premise and its signature devices**: 1980s metro, sealed after "the incident", 23:47 as the motif repeated on clocks, boards, placards, headsign and roster, the last train 047, G-2 lockout as the in-fiction reason the player's first act (power) is a transgression, missing-person posters, layered eras of notices. This is cohesive, original (a real attempt to avoid trademarks), and the reviewers keep naming it as the map's strongest asset (signage 7/10 on every review, roster "best story beat"). Keep.
- **The zone loop and gameplay skeleton** (hall -> stair A -> platform A with a branch to the generator and control room; a loop through the service tunnel, platform B, stair B): was designed from the stock recipe and the gameplay QA shows it plays.
- **The hero train** as centrepiece (3 BO3 cars, 047 plate, headsign, cordons, bogies) and **G-2** as a story prop: reviewers moved from "not a shipped asset" to "pass, now a centrepiece".
- **The dark-then-power structure** (pitch dark + faint amber cues + emergency route + bank-by-bank power-on + audio sequence): technically done and proven, matches IWZ-quality ambition; only its brightness tuning is unfinished.
- **The verification discipline** (same-camera before/after pairs, multiple independent reviewers, never trust luma): sound, and expensive lessons paid for.
- **Audio**: custom horror cues from a PA-chime leitmotif and the Abracadavre easter egg are working and measured.
- **The four hero roles and eight zombie outfits as design ideas**: coherent with the 1980s transit fiction and with each hero's stock colour identity (a clear "key read at distance" column for the zombies is good practice).

### Weak, unproven or likely to need redoing

1. **Visual quality is the actual blocker and stayed near 5/10.** Three rounds of defect-fixing gave +0.5; every round the reviewers list a fresh batch of "systemic" issues of the same kinds (lighting flat/bright, casts, floor decals, blank walls, fakes). This suggests the generator approach (procedural quads + stock textures + decals + kit props) hits a ceiling, not a bug list. Strategy risk, not a polish issue. A bible should state a visual target in concrete reference terms (named IWZ rooms) and a way to measure it earlier than frame reviews.
2. **Lighting is a design failure, not a tuning item.** The default was bright, even, showroom light in every build; the dark mode was bolted on later, still 7-18% at best versus a 2-5% goal, and the lit state is "too dark in the corridors" after the fill pass. The two states were never designed together (pre-power vs lit), and lighting was split between three agents (level, darkness, fx) with a hand-off contract. The unresolved question: which state is the hero look? The reviews all judged the lit/baked state.
3. **Wells: an unsolved structural gameplay bug** with five fix attempts reversing each other (6 low risers, solid blocks, landing change). Root cause is "agents do not ride the generated smooth ramp" at the foot; the stock-stair style (clip sheet, 8-unit risers) has not been tried on the wells. A rebuild should adopt the stock stair construction everywhere from the start (g27s stock variant was built but never fully run) rather than keep patching.
4. **Stair/ceiling "glyphs", black decals, blue walkways were diagnosed wrongly for several builds** (SSR, material, probe, bake were all blamed); the real causes were an ordinary light placement and the stock multiply-stain decal. Lesson: root-cause by bisecting the generator, not by theory; and generated geometry must never use that decal.
5. **The heroes and zombies are far from done: nothing is shippable.** Two independent reviewers said DO NOT SHIP (3-4/10 vs stock) for the three finished heroes; the improved v2 was never even run; Sally failed; no zombie has been in game; every zombie but one has never been through the kit; known crowd-performance risk (1 LOD), gibs risk, roster override unproven. The hero path is also heavily dependent on external, partly paid and rate-limited AI services (credits mostly used or expiring about 2026-11-16, 5 web generations per day) and on unproven real-player third-person rendering. Treat all eight zombies and four heroes as concept-only. The concepts and roles are the asset worth keeping; the meshes are not.
6. **No named in-universe characters, no incident explanation, no quest narrative.** The map has props that imply a story but nothing says who the heroes are, what the PaP "signal relay" quest narrates, why G-2 was locked out, what is under the "sealed" door. The fourth-wall line was removed but nothing replaced a framing device. This is the gap the new bible should fill.
7. **Stock-weapon constraint** with a separate BO3 wonder-weapon port: not an issue for the bible, but any lore must not rely on the wonder weapons; "weapons stay the stock IWZ Spaceland ones" is a standing decision.
8. **Performance is fine on average but untested where it matters**: 8-player flashlight cost, crowds with eight new outfits at one LOD, 507 MB fastfile (the other IWZ DLC maps' sizes were not compared), first-view image streaming hitch (2.1 GB read) which was reduced but not re-measured on later builds.
9. **Process cost and fragility**: the work depended on a single shared game install and lease scheme; 25+ builds (g1-g27e, d1-d16, t1-t16, e1-e11); runs wasted by the owner's game and stale leases; reviewers and agents duplicating each other. The owner's later rule ("tool first, no grinding"; DEVKIT) post-dates this work. A rebuild should start from the dev kit's bench-root and headless game-lab rather than the old runner.
10. **Unverified claims that look like facts**: the g27e fixes (rubble, drums, perks, planks, clock, prices) are "SRC + lint" only, with the previous lesson that this proves nothing; art assets such as the lit ad panel, DDS mips, floor-stain mask, car emergency lights, cordons, per-bank FX switching have no engine frame; the second-client flashlight and any real-player outfit view have never been seen. Also, the 650-frame reviews were each performed by agents that sometimes disagreed with the builder's own "FIXED" claims (A rejected 3 rows because the camera moved).
11. **Content scale looks right but mood scale is untested**: the control room is "hangar-sized", platform B and the hall are large. The map may be too sparse for its footprint: "blank walls", "empty floors", reviewer repeated "tidy, empty". Either shrink the footprint or invest in dressing density for the bible.

### Bottom line for the bible

The earlier work proved that a custom Station Zero is technically possible with real gameplay, a power-on darkness arc, custom audio and an easter egg, and it left a strong tone (1980s metro, 23:47, ZERO LINE, G-2, last train 047). It did not prove that the visuals can reach IWZ level, did not finish a single hero or zombie, and left no written lore beyond props and costume lists. The bible should lock the existing names/devices above, add the missing narrative layer (who, why, what happened at 23:47, what the player is doing, what the PaP quest and G-2 mean), choose the hero look state (lit vs dark) first, and specify lighting, density and an acceptance method before any more geometry is built.
