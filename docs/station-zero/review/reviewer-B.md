# Reviewer B: adversarial review of the STATION ZERO bible (00 to 14) and build plan

Reviewer: independent, no stake. Read-only; nothing launched, built or committed. Date 2026-11-11.
Read in full: 00, 02, 03, 04, 05, 06, 07, 08, 09, 12, 13, 14; 10 and 11 read by section (status, delivery,
budgets, facts tables, buildability); 01-LORE and wiki skimmed for names and numbers only. Research digests
A, C, E read in the relevant sections, B and D in the sections on limits and lessons; primary documents checked:
`docs/KINO.md` (findings), `docs/ORIGINAL-RIG-DEMO.md` (scriptmodelplayanim).

Severity: **BLOCKER** = the chapter or package cannot be built or cannot be proven as written;
**MAJOR** = it will cost a failed package, a wrong build or an unmet owner rule unless fixed first;
**MINOR** = a contradiction or gap a builder will trip on but can work around.

Abbreviations for evidence: A = `research/A-tools-readiness.md`, B = `research/B-maxis-ui.md`,
C = `research/C-current-map.md`, D = `research/D-earlier-state.md`, E = `research/E-shipped-map-numbers.md`,
KINO = `docs/KINO.md` of the server worktree.

---

## Part 1. Design elements against the research: claimed, flagged, or silently assumed

### 1.1 The hybrid crowd and every script-driven actor (07, 12 E1 to E4, 14)

**F1. BLOCKER. A crowd body cannot be "one entity (zombie parts attached)".**
07 §2.2: "A crowd body: one entity (zombie parts attached), animated with the stock walk, run, attack...".
07 §2.2: "Entities. 54 extra entities at most."
Evidence: D §6 "Failed or dangerous": "`attach()` does not draw heads on script models (hero fixtures must link
models)". A stock zombie is a body plus a head (plus gib parts). So a body is at least two linked script models,
and 54 bodies are at least 108 entities, before any hit volume (F2). The entity arithmetic of 02 §1 ("under 150 so
that 54 crowd bodies and the specials fit under the measured margin of about 240") is built on the wrong unit.
Fix: E1's first probe measures the real entity count of one visible, animated, hittable body (body + head + hit
volumes) and the bible's entity ledger (F8) is recomputed from that number; the cap table of 07 §2.3 is then
derived from the ledger, not fixed at 78 in advance.

**F2. BLOCKER. "Hit boxes are script boxes" has no mechanism and is presented as a fact.**
07 §5: "Collision for imported models | missing; not needed for actors (hit boxes are script boxes) | not a blocker
here". 12 §1: "actors use script hit boxes". 07 §2.2 "head and body boxes: head shots count".
Evidence: nothing in A, C, D or KINO shows a bullet hit on a script model registered with a hit location. The only
collision route proven for script-placed things is `clonebrushmodeltoscriptmodel` (KINO "Collision"), which ends
the match with fatal "HIE: 506609a5" after about 1,480 calls (KINO "Findings", A §a). A crowd that kills hundreds of
bodies per round (E §5.2: 510 zombies at wave 30 with four players, most of them crowd bodies when the cap is 78)
would pass 1,480 clone calls in a few rounds if each body clones its boxes. A pooled-clone scheme (KINO's answer)
is not described. New skinned models (Rollers, Inspector) have no collision either (A2 missing).
Fix: state in 07 §5 and 12 §1 that bullet hits on script bodies are UNPROVEN and are E1's first probe, with three
candidate routes in order (stock zombie xmodel's own collision on a `setcandamage` script model; a fixed pool of
cloned hit volumes reused for the whole match, never re-cloned; a trace from the shooter's eye on the weapon-fired
notify, which gives no hit location for non-hitscan weapons). Add the clone-call counter to every crowd soak and a
hard assertion under 1,000 per match.

**F3. MAJOR. The evidence that "its parts exist" is misapplied.**
07 §2.1 table: "its parts exist separately (script-moved zombies on a shared flow field passed 20 of 20 in the Kino
overlay...)". Evidence: KINO "Zombies" row and A §h: the Kino zombies were **real agents taken over** ("behavior
tree and ASM transitions suspended, retail `*_loop`/`attack_stand` animation states kept"). Their animation,
damage, hit locations, gibs, death and network came from the engine agent. None of that transfers to a script model.
The flow field transfers; nothing else does. Fix: rewrite the "State" cell to "only the flow field is proven; body
animation on a script model, hits, death, power-ups and every stock system that enumerates enemies are unproven".

**F4. MAJOR (missing work). Every stock and project system that counts or hurts zombies ignores crowd bodies.**
Silent assumption across 05, 06, 07, 09: wonder weapons (Thundergun-style cone, DG-2 chain, our four), traps
(Third Rail kills "every zombie inside the pit box", C §3), Nuke and Insta-Kill power-ups, Blue Bolts-type perks,
Last Licks penetration, Sour Grudges marking, Double Takes decoy, the round-end condition
(`desired_enemy_deaths`, E §5.6), the zombie counter H11 ("ALIVE 41 / 62"), Rush/AFK modules, the stock "recycle
far zombies" rule that 03 §6 relies on, idle "commuting". None of these is listed as needing a crowd-body path.
Fix: add to E1/E2 a single "enemy registry" API (`iwz_enemies()` returning agents and bodies, plus damage, kill and
remove functions), and make every package that touches enemies (WW1 to WW4, P1, W4 traps, E0, H1 counter) test
against a mixed population. Add the list above to E2's scope.

**F5. MAJOR. Bodies' physical presence is unspecified.**
07 does not say whether a crowd body blocks players, blocks bullets of other bodies, or overlaps other bodies.
A non-solid body lets players walk through 54 of 78 zombies (visibly wrong, trivialises training); a solid one
needs collision (F2). A flow field without separation stacks bodies in single file in corridors.
Fix: specify player-blocking (or explicit "no block, crowd stays outside 32 units of a player except to attack"),
body-body separation, and anti-stuck rules (KINO "Findings" lists four parking failure modes the Kino zombies hit).

**F6. MAJOR. Proof 2.5 cannot be run as written.**
- 2.5.1 "A match played from round 1 with four players (clients and bots) to round 26": with stock waves this is
  several hours; gamelab client sessions are capped at 600 s and headless runs one bot and no usermap (A §2.2).
  Only the soak tool (1 to 720 min) can host it, and it is not named. Name the tool, the expected duration and
  the godmode/inactivity protection, or allow a measured round-skip that keeps the spawn path natural.
- 2.5.2 "a fixed observer camera on the Fare Hall balcony sees the crowd": 02 has no balcony, and 78 bodies spread
  over three or more zones are never all in one view. The hide-one-body test only detects invisibility for bodies
  in view. The "method already proven for hidden props" is the live world editor (A §2.1: native, lab client,
  author only), which proof 2.5.7 forbids ("run with the official client build, not the lab one").
  Fix: drive the crowd into one measured arena (a dvar that sends every body's goal to a point in view), run the
  hide test with a lab client for detection, and run 2.5.7 with the official client only for the log and a
  frame-difference sample on, say, 20 bodies. Two measurements, both named.

**F7. MAJOR. Rollers and the Inspector are script-driven actors with no hit, damage or attack primitives proven.**
07 §3 and §4 give exact numbers (lamp 300 %, swipe window 0.25 s at 56 units). All depend on F2 and on C2 (our
clip playing in game, open). E3 and E4 are XL and depend on C1, C2, E1. This is honest about animation but not
about hits. Fix as F2; and E0's stand-ins (stock Brute, stock clown) should be declared the shipping versions until
E3/E4 pass, which 07 already implies.

### 1.2 Entity, trigger, brush and light pools: the ledger nobody keeps

**F8. BLOCKER. No entity ledger; the sums already exceed the margin the bible quotes.**
02 §1: "the whole map stays under 150 so that 54 crowd bodies and the specials fit under the measured margin of
about 240 extra visible entities". Items in the bible that are entities, uncounted anywhere:
- crowd bodies x2 or more (F1): 108+;
- Exact Change tokens "per player at most ... 20 tokens alive" (12 §5) = 80 with four players, 160 with eight;
- Live Rail stakes (2 fences x 2 to 3 stakes per player) = 16 to 24, plus fence effects;
- Wildstyle slicks (3 per player, "a timed box"), Dispatcher capsules, Double Takes cut-outs;
- Rollers (16 to 24), Inspectors (2), emote rigs and cameras (2 per emoting player, 16 with eight players);
- the board's flap plates (every state of "DEPARTURE n", "CLOCKS n/4", "ROAD SET FOR 047" etc. is a pre-made plate,
  04 §7), clock hands (10), 40 levers and lever lamps, Pneumo capsules (8), hatches, gauges, needles, pipes' moving
  capsule, door leaves, relays "that click in travelling waves", tape drives, the line printer, the floor polisher,
  arcade cabinets, the mirror ball, Party Car streamers;
- every authored model that has no stock static donor (F9).
KINO also says "deleted entities still count briefly": crowd churn makes spikes.
Evidence: KINO "Findings" (240 above the Spaceland baseline drops the game, `sv_running 0`); B (entities under 1800
of 2048); C §1.1 (old map: 229 script-model entities already). Fix: a package (TF8, S, Sonnet) that keeps an
entity ledger in the map source, computed by `iwzmap_ents_lint.py` plus a script-side counter, in absolute counts
against 2048 (the 240 figure is relative to Spaceland's baseline, which this map does not have). Every package
adds its worst case to it before building.

**F9. BLOCKER. "6,000 compiled static" assumes every model can be a static model. It cannot.**
02 §1: "props are compiled static models (drawn with no entity cost)". 12 TF3 / TF7: "at least 350 distinct models"
from "all five shipped maps".
Evidence: C §2.2: "Models without a stock static donor stay entities"; D §5 and §6: "static model with no
light-grid template instance crashed (AV at iw7_ship+0xDCE6E7) ... five models excluded; keep those as
script_models". The old map, with kit import, still had 229 of 399 props as entities (C §1.1). Models kit-imported
from cp_disco, cp_final and others, and every authored hero object (rectifiers, Bellows, capsules, hatches, clocks,
perk machines, Vayle's car), are exactly the class without a cp_zmb donor.
Fix: make "static model for a model with no template donor" its own tool package before TF3 (or TF3's first
milestone), with a measured proof (a kit model and an authored model compiled static, lit by the light grid, no
crash); until it passes, the props budget counts non-donor models as entities and TF7's lists mark donor status
per model.

**F10. MAJOR. Template pools for triggers, brush blockers and switchable lights are finite and not counted.**
- Triggers: D §5 "only ~54 usable template trigger boxes" (volumes borrow template physics shapes, C §2.8 "A new
  trigger/brush shape needs a template model"). Needed: 19 spawn volumes, trap volumes (Decon corridor, Rectifier
  aisle, Bellows circle, Third Rail pit), invalid_playspace, Pneumo hatch zones, the Sump water slowdown,
  Terminus, car 1 boarding volume, 17 `door_buy` triggers, use triggers.
- Door blockers: C §1.3 "24 brush models in total over the 5 doors and the PaP shutter", from the template
  (`IWZ_KEEP_SUBMODELS`, D §6). 17 doors plus car 1's doors (04 §3 "door blockers become solid") need about 85+.
  How many template brush models exist is not stated anywhere.
- Lights: the darkness route "extends the template's 25 scriptable light slots" (C §2.7); d16 had 72 named lights.
  02 §8 asks for two states in 19 zones with 520 lights; how many switchable lights the engine allows is not stated.
Fix: TF2's first deliverable is a count of each template pool (triggers, brush models, scriptable light slots,
reflection probes, light-grid instances) against the bible's needs; the generator refuses a source that exceeds a
pool. If brush blockers run short, doors use the clip-box + model-move route already used for shutters.

### 1.3 World layout (02)

**F11. MAJOR. Doors and links between zones that are not adjacent in plan (checked box by box).**
- **D2 Cordon to Transit Police Post**: Cordon x -1400..800, y 4600..6200; Police x 1000..2200, y 3300..4300. No
  shared edge: the gap is 200 in x and 300 in y. The "Street loop" (§3 loop 4) and "Shortest way to power: D2,
  chute, D11, D12" both depend on it.
- **Free link Escalator Hall to Platform A East**: Escalator Hall x -800..-200 ends 200 west of East (x 0..2400);
  it touches only West. (Harmless because West and East are joined, but the table is wrong.)
- **Police chute**: Police (z 0, y >= 3300) to Platform A East deck (z -320, y <= 2400): 900 units of plan through
  unclaimed space x 1000..2200, y 2400..3300, not a zone, no box. A 320 drop over 900 run is a 20-degree walkable
  ramp, not a one-way slide; 03 §1 itself rejects slides ("needs sloped slide collision; the generator has straight
  stairs only"). A player in it is in no spawn volume.
- **D1 entrance stair**: Fare Hall top y 4400, Cordon from y 4600: a 192 rise inside a 200 gap is a 44-degree
  flight, against §6's own rule ("long ramps ... at least 256"). It must sit inside the Cordon box; say so.
- **Arcade shop bays**: "five shop bays on the north side, each 320 x 400" put them at y 4300..4700; an east-most
  bay (x -1520..-1200) overlaps the Cordon (x >= -1400, y >= 4600). Give the bays' x positions.
Other pairs checked and adjacent: D3, D4, D5, D6 (16-unit wall), D7, D8 (16-unit wall), D9, D10, D11, D12 (200
units of shared edge only), D13, D14, D15, D16, D17; Breach-Parlour link (16-unit wall). No two boxes overlap
except the Arcade bays case above.
Fix: move the Police Post north-east of the Cordon's east edge or move D2 to Fare Hall; give the chute a box and a
zone, and build it as a drop (a vertical one-way fall with no nav link) or remove it; put D1's flight inside the
Cordon box; fix the bays.

**F12. MAJOR. Walkable train cars over the track pit break the "one height per cell" rule in two places.**
02 §4.9: "All six interiors are walkable end to end"; cars stand in the pit (C §2.7b: car centres at y 1488, pit
y 1200..1600). The car floor and the pit floor share plan cells. The present map solved it for one car by turning
the pit cells under it into car-floor cells, so the pit is **not walkable under the cars**. Yet the bible places
"Live Rail part (collector shoe, under car 3)" (02 §4.9, 05 §2) and "ballast" spawners in Platform A East, and the
Third Rail trap box spans x -2400..2600 under the train (C §3).
Fix: state that the pit under cars 1 to 6 is not walkable; move the collector shoe to the pit west of car 1; put
East's ballast spawners west of car 1 or in the tunnel; shorten the trap box to the open pit.

**F13. MAJOR. The stair lesson is inverted.**
02 §4.3 "Built as long collision ramps (no short steep steps: the old map's zombies failed on those)"; §6 "never
short steep steps: the old map's zombies failed to climb its two short wells".
Evidence: D §5 "Known bugs" and §7.3: the wells failed because "the nav is 14 units under the ramp 34 units in and 36
under the top", i.e. agents do not ride the **generated smooth collision ramp** at its foot; long Stair A/B passed;
the recommended fix is "adopt the stock stair construction everywhere (clip sheet, 8-unit risers, nav 4 above)".
"Long collision ramps" is the construction that failed, at any length.
Fix: rewrite §6: every level change uses the stock-stair construction (clip sheet, about 8-unit risers, nav cells
with sloped corner heights 4 above); `sz2_navconn` plus a new offline check that compares nav height with the
collision surface along every ramp (the cause of the old failure) gates every build. The "ramp" kind TF2 must add
(C §2.10: "ramps other than straight stairs" cannot be expressed today) inherits the same rule.

**F14. MAJOR. Water, rain, fog, animated screens: silent assumptions on things the generator and materials cannot do.**
- The Sump: "black water with a slow current", "ankle-deep", "reflected", "things floating", "water slows players
  10 %". C §2.3 "Engine-proven failures: `puddle` ... render as opaque squares"; no water material, no custom
  shader (A §f, C §2.10). Nothing in the bible flags it.
- The Cordon: "rain on a torn quarantine canopy", night street. GPU particle clouds never draw (C §2.5); an open
  sky over a generated room is not described anywhere.
- The Terminus: "Beyond the platform edge: no track, only pale fog. In the fog, the outline of a second platform".
  `vfx_knee_high_fog_dark` and particle clouds never draw (C §2.5); fog is a vision setting (C §2.7).
- Animated surfaces: TILT's cabinets "cycling attract screens", Exchange "green screens", "two tape drives turning",
  relays "click in travelling waves", mirror-ball light, the floor polisher. Animated materials are "not stated"
  (A §f) and moving models are entities (F8).
Fix: add each to 12 §1's table with "unproven" and a first probe (water: a stock water material from the five
maps found by TF7 and tested on a generated quad; rain and fog: sprite effects only; screens: the same scrolling
technique K1 looks for). Give each a written fallback (still water as a dark glossy stock material; no rain, wet
decals; a painted backdrop for the fog platform; static screen images).

**F15. MINOR. Numbers in 02 that do not add up.**
- Spawners: the per-zone figures sum to **186**, not 204 (12+14+8+12+10+10+4+14+14+6+14+10+12+10+6+12+8+10). 07
  §2.3 then says "Every zone has 10 to 14 spawners", contradicting 02's own 4, 6, 6, 8, 8.
- §6 "Eight walking heights" lists seven (+192, 0, -96, -160, -320, -384, -448).
- "about 18,900 m2 walkable (2.8 times today)": 18,918 m2 is the **gross plan-box** area including the Terminus,
  walls, the pit under the train and the Bellows trap circle; today's 6,808 m2 is **nav cells**. Compare like with
  like or say "gross".
- Walking times assume "about 190 units per second" with no source (E §8: run speed is set by the animation set,
  "not a script number").
- 03 §3: "the two longest walks ... become one hop in one of the two directions, never both at once". On BLOW both
  Parlour to Plaza and Barn to Parlour are single hops. The claim is false; 02 also gives the longest walk as 62 s
  (Bellows to Sump) against 03's target of 40 to 50 s.

**F16. MINOR. Power for the spawn perk contradicts itself.**
06: "All machines need power except Up 'N Atoms ... runs off Lodestar's trailer"; 04 §1: "Power is one switch for
the whole map (stock `power_all`)". The present map marks all perks `requires_power` (C §3). Stock power is
per-area generators (E §4.4). Fix: give the Cordon its own generator struct powered at match start (stock
per-area power), keep `power_all` for the rest; say so in 04.

### 1.4 Quest, transport, teleport (03, 04)

**F17. MAJOR. The Terminus as a zone-less far box is untested against the stock spawn logic.**
04 §3: everyone in the Terminus for 75 s, "no zombies spawn there". Stock spawning picks spawners from active
volumes around players (E §5.4, §7); with all players outside every volume the behaviour is unknown (stall,
script error, or recycling every zombie). Kino's PaP room lived inside Spaceland's own hidden room. Fix: make the
Terminus a spawn volume with no spawners and no adjacency, and add "all players in the Terminus for 75 s at round
20" as a Q1 case with the zombie count and script errors read back.

**F18. MINOR. The split-flap board is a large, uncounted set of entities and of art.** "DEPARTURE n" for any round
needs digit plates; "CLOCKS n/4", "NOW --:--" digits, Pneumo and Inspector lines. Count the plates and put them in
the ledger (F8), or reduce the board to a fixed set of whole-line plates.

**F19. MINOR. Pneumo riders and the stock zone system.** A linked rider passes through other zones' walls and is in
no spawn volume for 5 s; the stock code that tracks a player's zone may treat him as out of play. T1 should read
zone and spawner activity during a ride.

### 1.5 Weapons (05)

**F20. MAJOR. Three mechanics are new families and are not on the "distrust first" list.**
12 §4 lists the dance state and the alternate-mode chain. Not listed, equally unproven:
- Dispatcher "reading the aim button as a second trigger" while holding a pistol (the server can read
  `adsbuttonpressed`, B §2, but aiming also zooms and lowers the weapon client-side; inhale while ADS view is
  untested);
- Live Rail "the stake ... sticks in any world surface" from a launcher definition (projectile type of a weapon
  definition, A §g: "an attachment cannot override it");
- Wildstyle "continuous spray ... effect applied ten times a second" (no flamethrower-type weapon is in the stock
  wall/magic table, E §4.2-4.3).
Fix: add the three to 12 §4 and to WW2-WW4's first probes, each with a fallback (inhale on a held melee button;
stake as a grenade-type sticky projectile; spray as a full-auto weapon with zero damage and a script cone).

**F21. MAJOR. Weapons and emote clips in the global mod zone touch the public servers and every map.**
12 §5: "weapon assets in the mod zone, which the official client already downloads"; 10 §5.3: "The 84 clips go in
the mod zone `mods/paris`". Main and Canada run `fs_game mods/paris` (A §o, AGENTS). Any change to that mod changes
its hash, so every player on every map re-downloads the whole mod, and "a failed download terminates the official
client" (A §o, KINO "Upstream issue"). The mod zone also "must not name assets only one map carries" (A §2.4). This
is a deployment decision presented as an implementation detail. Fix: ship Station Zero's weapons, clips and camos
in the map's own zone (delivered with the map, CF3/TF6) and offer the mod route to the owner as a recommendation,
with the measured size of the mod after the change.

**F22. MINOR.** 05 §4 "package W-C first confirms" (no such id; it is WW2). 05 Common rules: "two different ones only
with the extra-slot perk the servers already run": Mule Munchies is not among the map's ten perks, and the
servers' `.mule` and late-join kit are off on cp_iwz (A §5 map profile excludes `loadout`; A §4 lists `.mule` among
commands to remove from cp_iwz). Same for 02 §4.2 "Lost Property window (the servers' late-join kit point)".

### 1.6 Perks (06)

**F23. MAJOR. W1 places Deadeye Dewdrops before P1 learns whether it exists.**
12 W1: "the six stock perks at their places"; 06 §4: Deadeye is "not among the shipped map's ten machines ...
first check of P1". E §4.1: `perk_machine_deadeye` is registered but not placed in cp_zmb, so its machine
scriptable and model are not in the template zone. Fix: W1 places five stock perks; Deadeye moves to P1.

**F24. MINOR. Perk mechanics not listed as unproven.** Double Takes "ordinary zombies within 400 units go for the
image": stock agents target players; redirecting them to a script model is not shown anywhere (Kino moved zombies
by suspending their behaviour tree). Lucky Dips "the wheel offers two weapons; Use for the left, melee for the
right": a replacement of the stock wheel's give path (`replacefunc` is proven for other hooks, A §g). Add both to
P1's first probes with fallbacks (Double Takes: zombies within 400 lose the player as target for 4 s; Lucky Dips:
re-roll offer).

### 1.7 Camos (08)

**F25. MAJOR. New camos need new camo-table rows, a global asset, not only "the camo index a custom map gets".**
08 asks which index the map gets. A new look on stock weapons is a `+camoN` index into the camo table (A §f); our two
camos are new rows. Where those rows live (map zone overriding a stock asset that the base game already loaded, or
the global mod zone that every map loads) is not stated; "Custom camo textures for new maps: NS" (A §f). Fix: K1's
first probe is "a new camo-table row from the map zone, used by `get_pap_camo` on cp_iwz, seen on a stock weapon";
fallback: re-texture an existing camo index only inside the map zone, or ship the camos in the wonder weapons'
own `_pap1` definitions only (A §g: "a PaP look change needs a definition swap").

### 1.8 Tab, HUD, emotes (09, 10)

**F26. MAJOR. The 24-element budget is double-spent between chapters.**
09 §3: worst case 15 map elements, "with the servers' own counter and timers (about 5) still inside it" = 20.
10 §5.2: the wheel takes 13, "leaving 11 for the map's own HUD". 13 + 20 = 33. The STATION terminal page (about 12)
and the map vote (4 to 12, B) also coexist with H1 to H9. Fix: one element allocator for the map (priority order,
admission refusal), and the worst case stated per screen state: wheel open hides H1, H3, H7, H8; terminal open hides
the wheel; the proof (09 §5.1) reads the count in each state.

**F27. MAJOR. The Lua data channel breaks the write budget with eight players.**
09 §4: `maxis_t` "at most one write per player per 3 s, inside the project's limit of 24 writes per 10 s".
B: "Write budget <= 24 per 10 s (all players)". Eight players x 10/3 = 26.7 writes per 10 s, before Maxis's own
writes and the wheel's `maxis_e`. Fix: one write per player per 5 s at most, coalesced, and a server-wide
token bucket that the soak (09 §5.5) asserts.

**F28. MINOR.** 10 §3.7 "hide the real player from every client" while still damageable and targeted: a hidden
player who is shot or swiped is a bug report waiting; state the rule (zombies keep targeting, hits land on the
player's real collision). 10 G3/G4 are honestly flagged.

### 1.9 Audio (11): no blocking finding. Two items:
- **MINOR.** 11 §3.9 (jukebox alias in the mod bank played from a usermap) is flagged as a first check: good. The
  map's bank size (507 MB map and 108 MB of banks for nine zones today, D §5) has no owner (F31).
- **MINOR.** §2.2 says 19 zones, §6.2 sizes 18 beds: consistent only if the Terminus has no bed; say so.

---

## Part 2. The build plan (12)

**F29. MAJOR. Tool-first is violated by the order: TF4 (build time) and the measuring tools come after the
build-heavy packages.**
12 §3: TF4 is in wave 2, in parallel with W2; 13 risk 5 only pulls it forward if W1 takes "over 30 minutes".
The old map took about 20 minutes a build for nine zones (A §p) and 25+ builds (D §7.9); W1 (19 zones, climb phase
at 90 % on every level change), Q1, T1, E0 and H1 all iterate on builds. The owner's rule: a wait of minutes for an
answer is a sign to fix the tool first. Fix: TF4 in wave 0, before W1, with its proof on the present map (one-room
change rebuilt and loaded under 5 minutes).

**F30. MAJOR. Server-side and GPU budgets are unmeasurable with the named tools; no package builds the meters.**
12 §5: "under 0.3 ms of server frame together", "under 0.1 ms of server frame", "crowd update and flow field under 4
ms of server frame", "effects under 0.5 ms of client frame". Evidence: the performance recorder is a client tool
(A §2.3); soak: "server frame times not done" (A §2.2); GPU time per pass: DP J, not stated as done; DP G
(server recorder) partial. Fix: add TF9 "server script cost per function on the dedicated (GSC profiler or
per-thread wait accounting) and GPU pass timing (RenderDoc package J)", before E1 and WW1, with a provoked +1 ms
detection proof.

**F31. MAJOR. The parity budget is weak where it matters and arrives late.**
12 §5: "A machine that runs the shipped map then runs this one." The only machine is an i5-13400F with an RTX 3080
at 1280 x 720 at 184 to 318 fps (A §2.3), CPU-bound; the risk of a map with no culling is GPU cost, invisible at
720p on a 3080. The first "ordinary machine" number is in Z1, after all dressing. Also "four players and a full
wave" on one machine means extra clients sharing the GPU (D §5: second client on the same GPU 4.2/8.0 ms), and "the
same test" on two different maps has no defined camera path. 07 §2.4 says the client must hold **85 %** of the
shipped map; 12 §5 says **no less than** (100 %). Fix: one number (85 %, as 07), a defined set of atlas points on
each map, 1920 x 1080 and a GPU-bound setting from W1 on, the weakest machine measured in wave 1 (stress test),
and drop the "then runs this one" sentence.

**F32. MAJOR. TF5 (culling) is placed after the dressing it is supposed to protect, and its mitigation does not act
on the cost.**
12: TF5 depends on W3a to W3d. 02 §1 locks the stretch budget behind it, 13 risk 2 says the stress test "decides
the budgets of everything else". If culling is needed, three L packages of dressing are already spent. TF5's
"far zones' entities hidden by script" touches only entities; the bulk (compiled static models and world
surfaces) cannot be hidden by script. The present tome is "one tile, one cell listing every object" (A §a): the
real lever is a generated multi-cell tome. Fix: TF5's measurement half (stress test with 6,000 statics + 78
bodies at 1080p) runs after W1; its build half (per-zone tome cells) starts in wave 2, before W3.

**F33. MAJOR. The three "early tests" of 13 cannot run early in 12's order.**
13: test 1 (78 scripted bodies), test 3 (one crowd body beside a real zombie) "in the first two waves". 12 puts E1
in wave 4. 13 risk 11 needs "the cap forced to 78 by dvar on scripted zombies" in wave 2. Fix: move E1 into wave 1
(it depends only on W1 or even the present map: a body walking on Spaceland via a bench answers the probe), and
make the stress test's 78 bodies E1's output.

**F34. MAJOR. Nothing better reaches a player early; the first playable is grey and undeliverable.**
Owner rule: "something playable and better must exist early and improve in steps". W1 is "no dressing beyond
materials", visually below the present map (reviewers 5 of 10, C §4), and no player can get it until TF6/CF3.
Fix: (1) run TF6 in wave 0 against the **present** rc map, so delivery is known first; (2) W1 reuses the present
map's dressing recipes and signage kit (02 §7 "keep" rows) on the rooms it keeps, so the first playable is at
least as good as today in those rooms.

**F35. MAJOR. Missing packages (the bible needs them, no package builds them).**
- Hero-object authoring: rectifiers (with animated flicker light), the Bellows blower and organ, Vayle's car, clock
  hands and faces, the lever frame, staff doors, Party Car dressing, board plates as models, Terminus banquet set.
  T2 (capsules, hatches), P2 (machines), WW1-4 (weapons) cover only their own. 13 risk 6 says "author only hero
  objects ... review each alone in the game before it is placed": no package does it.
- The Inspector's staff doors: 07 §3 "a staff door in the marked player's zone opens" in every zone; 02 places none.
- Static models without donors (F9), template pools (F10), entity ledger (F8), server and GPU meters (F30).
- Map size and download budget: 13 risk 9 "size budget per zone tracked from W2" has no owner and no number; the
  old map was 507 MB plus 108 MB of banks for nine zones (D §5); the Canada host serves 5.4 to 8.6 MB/s (A §o).
- Server integration: cp_iwz's module profile (which server features stay on), map vote and rotation entry,
  `MAX_ARENAS` (A §o: 64 shared, silent loss), the per-player journal file (09 §2 page 2).
- Water, rain, fog, animated screens (F14).

**F36. MAJOR. Packages sized too small or too large for one agent.**
- W1 (19 zones, 17 doors, 186-204 spawners, every level change at 90 % climb, rounds 1-15) is sized **M (a day)**.
  The old nine-zone map needed 25+ builds and never closed its wells (D §5, §7.3). Re-size L, split in W1a
  (geometry, nav, climb gate) and W1b (interactions, rounds).
- E2, E3, E4, CF2, L1/L2 are XL ("a week or more"): each is several agent sessions. Split each at its first
  measured probe (for E2: promotion; registry F4; 78 natural; performance).
- TF2 (scene-description generator, terraces, ramps kind, far boxes, 19 zones) is a rewrite of a 3,413-line
  generator; L is optimistic. Split: data model + emitter for the present nine zones first (diff-identical build),
  then the new layout.

**F37. MINOR. Dependencies.** M1 depends on C1, C2, but its first question (can a stock full-body animation play on
a player's world model and be seen by a second client; can a third-person camera be driven) needs no animation of
ours: probe it now with a stock clip, which decides CF4 early. K1 and WW1 depend only on "cleanup" but use
`Test-WeaponVisual.ps1` and the weapon E2E, which still take `-GameRoot <base game>` (KINO, A §6.5): route them
through bench roots (TF1). 13 risk 3 cites "E5", which 12 marks superseded by CF2. 00 lists a `REVIEW.md` that is
not in the folder.

**F38. MINOR. Tests and the workflow.** W1's "rounds 1 to 15 with bots headless" relies on TF1 delivering usermaps
headless; headless has one bot and plans "over a minute ... not verified" (A §2.2): TF1's proof should include a
15-round run, not only "loads in under 60 s and a plan reads zombie positions". M3 "a plan picks all 65 by pointer"
needs a client with input (bench client `keys/1`, A §2.2), not a bot.

**F39. The readiness check of 12 §1 is incomplete.** Present: compiler, headless, generator, prefabs, build time,
culling, delivery, catalogue, imported collision, shaders, animation, enemy, capacity, perks, behaviour families,
Lua, third person, sound. Missing rows: static-model donors (F9), template pools (F10), hits on script bodies (F2),
enemy registry (F4), water/fog/rain/animated materials (F14), camo-table rows (F25), aim-as-trigger, sticky
projectile, spray (F20), decoy targeting (F24), server and GPU timing (F30), entity count (F8), mod-download
failure (F40).

---

## Part 3. Player delivery and the client fork (14, 12 §2b and §5)

**F40. MAJOR. The official-client fallback for the map violates the owner's Rule 2, and the mod route has the same
crash as the map route.**
14 §2: "Until then it runs on a server whose join message says what to install". AGENTS ("Kino der Toten and
player-ready content", Rule 2): "anything meant for online play must install itself for other players ... no manual
downloads". A join message with install steps is a manual download. Also 14 §1 lists weapons, sounds and materials
as needing "nothing new" because "the official client already downloads the mod by itself": true, but "a failed
download terminates the official client" (A §o, KINO) applies to the mod as much as to a map, and F21's mod
changes make re-downloads frequent. CF3 covers only the map. Fix: (1) TF6 first measures whether the official
client's existing usermap path already works from a dedicated server (CCOMP: party joins only; dedicated
unproven), (2) CF3 covers both mod and map downloads (one clean change: report failures through the menu error
path, KINO's "Candidate clean PR"), (3) the honest fallback text in 14: "until CF3 is in players' hands, a player on
today's official client cannot receive Station Zero safely; the map is offered only on private servers" (a
recommendation to the owner, not a decision).

**F41. MAJOR. "Decision" in 14 is the owner's to make.**
14 §2 "**Decision**: Station Zero is not put in a public rotation until ..."; "**Decision**: Station Zero is offered
with at most four slots to official clients"; 07 §2.1 "**Decision** ... Route N is the real feature"; CF2 "a server
started with the capacity profile admits only clients that have it" (a separate public server profile). Placing
the map in public rotations, slot counts on public servers and running a capacity-profile server are deployments
(AGENTS "Owner approval, then deploy to BOTH servers"). Fix: reword each as "Recommendation to the owner", and keep
the technical decision (negotiation, refusal message) as the plan's.

**F42. MAJOR. "No invisible zombie is possible in this mode" (14 §2) overclaims.**
Script models are drawn by the stock client, but visibility still depends on the entity and snapshot limits the
hybrid mode pushes (KINO: 240 extra visible entities drop the game; deleted entities still count briefly), on
`attach()` not drawing heads (F1), and on LOD/distance. The earlier failure's symptom ("hits, sound and red
crosshair remain", A §i) can recur as a half-drawn body. Fix: "In hybrid mode no zombie depends on agent records
beyond 24; visibility is proven by 07 §2.5 proof 2", nothing stronger.

**F43. CF1 to CF5: complete? minimal? ordered?**
- CF1: right scope; note the server half (custom notify names need the dedicated's handler as well; our dedicated
  is project-built, so fine). Minimal: yes.
- CF2: not minimal (agent pools, character info, work tables, sentients, corpse indices, entity boundary,
  serialization widths in two executables, A §i). It is the opposite of a "clean, minimal package that can be
  proposed later"; 14 should say so. Its first step (reproduce and name the old crash) is right.
- CF3: extend to mod downloads (F40). Resume and progress are extras; the minimal proposable change is "a failed
  download returns to the menu", which should be split out as CF3a and done first: it protects every player today.
- CF4: right to wait on M1, but M1 should probe with stock clips now (F37).
- CF5: fine. Missing: a "UI sound from Lua" capability (11 F14) if the probe fails; a capability to raise
  `MAX_ARENAS` if the list fills (A §o).
- Order: CF3a first (it protects the official client from the project's own mod changes); CF1 next (smallest,
  unlocks Tab and wheel); CF5; CF2 last.

**F44. Feature by feature, does an official-client player get it by himself?**
Map: no, until TF6 or CF3 (F40). Quest, Pneumo, traps: yes once on the map. Perks: effects yes; icons server-drawn
(fine). Weapons: yes through the mod, with the crash risk on a failed download (F40) and the mod-change cost (F21).
78 zombies: hybrid yes, subject to F1, F2, F8. Rollers and Inspector: stand-ins until F2 and C2. HUD: yes within
the budget, subject to F26. Tab: four-row stock plus STATION page (honest). Emotes: only after G1 to G4; Tier 2
picker yes. Eight players: honest about the slot-5-to-8 error.

---

## Part 4. The 78-zombie plan, judged on its own

Feasibility, in the order a builder meets it:
1. Entity count: F1 and F8. At least two entities per body, plus hit volumes; tokens, stakes, Rollers and rigs
   share the same margin. Not demonstrated to fit.
2. Script cost: a per-player flow field on a nav graph about three times larger than the present map's 10,306
   cells (19 zones, 18,900 m2 gross) with eight players, plus 54 bodies moved, animated and attack-tested at 20 Hz.
   No server-side meter exists to check the 4 ms budget (F30). Kino's per-zombie recomputation already stopped a
   dedicated from answering (KINO).
3. Hit detection: F2. The single biggest unknown, and the one the bible calls "not a blocker".
4. Animation on script models: `scriptmodelplayanim` exists and was called in a lab (`ORIGINAL-RIG-DEMO.md`: "Pixels
   Verified/MotionVerified ... false"); stock zombie clips on a script model with matching skeleton are plausible but
   unproven, correctly flagged as E1's first probe. Clip blending (walk to run, pain over walk) is not available to a
   script model the way it is to an ASM; promotion "at the moment of a pain reaction" assumes a pain clip can
   interrupt cleanly.
5. Network: 54 more moving, animating entities and churn (spawn/delete) per snapshot; 07 §2.4 has a network row,
   but no package measures snapshot size; netlab is proven for one client, 30 s sessions (A §2.2).
6. Stock-system integration: F4.
7. Can the proof catch the earlier failure? In hybrid mode the agent-table failure cannot occur (never more than
   24 agents), so the relevant failure is "a body that is hit but not drawn". Proof 2's hide-and-diff catches it
   only for bodies in view (F6). In native mode (CF2) the same proof with real agents is the right test, provided
   the camera sees all 78 (arena method) and the client is the fork client.
Verdict on the honesty of "Route H": the principle (24 agents + bodies, stated plainly to the owner) is honest;
the "its parts exist" claim (F3) and "no invisible zombie is possible" (F42) are not; the mechanism for hits (F2)
and bodies' composition (F1) are unproven and drive everything else.

---

## Part 5. Internal contradictions a builder will trip on

| # | Where | Contradiction | Fix |
|---|---|---|---|
| C1 | 02 §1 / §4 totals | spawners 204 claimed, 186 summed | correct the table or the zones |
| C2 | 07 §2.3 vs 02 §4 | "Every zone has 10 to 14 spawners" vs zones with 4, 6, 6, 8, 8 | align |
| C3 | 07 §2.4 vs 12 §5 | client frame rate at least 85 % vs "no less than" the shipped map | one number |
| C4 | 06 / 04 §1 | Up 'N Atoms without power vs one `power_all` switch | F16 |
| C5 | 12 W1 / 06 §4 | Deadeye placed in W1 vs "first check of P1" | F23 |
| C6 | 09 §3 / 10 §5.2 | 15+5 map elements vs "leaving 11" after a 13-element wheel | F26 |
| C7 | 09 §4 / B | "inside 24 writes per 10 s" vs 26.7 with eight players | F27 |
| C8 | 05 §4 | package "W-C" | WW2 |
| C9 | 13 risk 3 | "native route runs in the lab (E5)" | CF2 |
| C10 | 02 §6 | "eight walking heights", seven listed | fix |
| C11 | 02 §3 | Escalator Hall "to Platform A West and East" | West only |
| C12 | 03 §3 | "never both at once" (false on BLOW); 40-50 s target vs 62 s longest | rewrite |
| C13 | 02 §4.2, 05 | late-join kit point, extra-slot perk: modules off on cp_iwz | F22 |
| C14 | 02 §4.1 vs §6 | D1 stair 192 rise in 200 run vs "at least 256" | F11 |
| C15 | 02 §4.9 / 05 §2 | part "under car 3" vs walkable car over the pit | F12 |
| C16 | 00 | `REVIEW.md` listed, absent | remove or add |
| C17 | 12 rules vs AGENTS point 10 | Opus/Sonnet split stated as the owner's 11 Nov rule; AGENTS.md still says Sonnet writes code and the global memory note says Fable for difficult work | cite the 11 Nov rule's source file so a sub-thread does not follow the older line |

---

## Part 6. Risks missing from 13

| Missing risk | Evidence | Early test |
|---|---|---|
| Bullet hits on script bodies fail or need clones that crash the match (HIE after about 1,480 clones) | KINO "Findings"; A §a | E1 probe: 100 shots at one body, hit locations logged; clone counter |
| Static models without a template donor crash the compiler or the game, forcing props back to entities | C §2.2; D §5, §6 | one kit model and one authored model compiled static, in wave 0 |
| Template pools (trigger shapes about 54, brush blockers, 25+ scriptable lights, probes) run out | D §5; C §1.3, §2.7 | TF2 pool count |
| The mod zone change re-downloads for every player on every map; a failed download kills the official client | A §o; KINO | measure mod size per change; CF3a |
| A usermap breaks the zombies map list; `MAX_ARENAS` 64 silently drops maps | A §o; ICM | TF6 with the official client and the full list |
| GSC limits: child-variable pool shared and exhausted, 4,000-row literal functions refused, canonical identifier budget (Beast floor 64) | KINO; A §5 | lint for function size; soak reads the variable count |
| Join stall 1 in 3 lab joins makes multi-client proofs flaky | A §4, CC S4 | count retries in every multi-client proof |
| Server frame overrun from flow fields on a three-times-larger nav | KINO (dedicated stopped answering) | TF9 meter with eight players on W1 |
| Snapshot and bandwidth with 54 extra animated movers plus eight players | 07 §2.4 only | netlab with two clients and the crowd |
| Bots cannot stand in for four humans in long proofs (no input, weapon switch never finishes) | A §2.2; KINO | state which proofs need real clients |
| Visual target 7 to 7.5 against a history of 5 to 5.5 after three rounds | D §4, §7.1 | W2 already; add a stop rule with a date |
| Licences of library animation clips in a publicly downloaded mod; account sign-in is a human step | 10 §1 | record terms at download (10 does) |
| Owner's game, Main and the Aside app's instances: shared machine contention during long soaks | AGENTS; memory notes | scheduler admission for multi-hour runs |
| The present map's known failures (stair B up, bottom-landing spawners, suitcase on nav) recur in a new layout | C §3 | TF2 offline gate for each class |

---

## Part 7. The ten most important findings, in order

1. **F2 BLOCKER**: hits on crowd bodies, Rollers and the Inspector have no mechanism ("script hit boxes" is
   asserted, not shown); the only proven route (cloned brush models) is fatal after about 1,480 calls a match.
   Fix: E1's first probe, three candidate routes, clone counter, and the claim removed from 07 §5 and 12 §1.
2. **F1 + F8 BLOCKER**: a crowd body is at least two entities (`attach()` does not draw heads), and no entity
   ledger exists while tokens (80 to 160), stakes, Rollers, rigs, board plates and non-donor models all draw on the
   same margin. Fix: TF8 entity ledger in absolute counts; cap derived from it.
3. **F9 BLOCKER**: "6,000 compiled static" ignores that models without a cp_zmb static donor crash or stay
   entities; kit and authored models are exactly those. Fix: a donor-free static-model tool package before TF3;
   budgets count non-donor models as entities until it passes.
4. **F4 MAJOR**: no system (weapons, traps, power-ups, perks, round end, counter) knows crowd bodies exist. Fix:
   one enemy registry in E1/E2; every enemy-touching package tests a mixed population.
5. **F40 + F41 MAJOR**: the map's official-client fallback ("join message says what to install") breaks Rule 2,
   the mod route shares the download crash, and 14's "Decisions" on public rotation and slots are the owner's.
   Fix: TF6 early on the present map; CF3a (failed download returns to menu) for mod and map first; reword as
   recommendations.
6. **F13 MAJOR**: the stair lesson is inverted: the old wells failed because agents do not ride the generated
   smooth ramp (nav under the collision), not because steps were short. Fix: stock-stair construction everywhere and
   an offline nav-versus-collision height check.
7. **F29 + F32 + F33 MAJOR**: order breaks tool-first: TF4 (build time) after build-heavy packages, TF5 (culling)
   after the dressing it protects, E1 in wave 4 although 13's first tests need it in wave 1. Fix: TF4 and the
   stress measurement in wave 0/1, E1 in wave 1, culling build before W3.
8. **F30 + F31 MAJOR**: server-frame and GPU budgets cannot be measured with any named tool, and "parity" is
   measured CPU-bound at 720p on one fast machine, with 85 % versus 100 % in two chapters. Fix: TF9 meters, one
   number, defined atlas points, 1080p and a weaker machine from W1.
9. **F11 + F12 MAJOR**: layout errors: D2 joins non-adjacent boxes, the Police chute is an unbuildable,
   zone-less slide, the pit under walkable cars cannot be walkable (yet holds a quest part and spawners). Fix as
   given; TF2's emitter must refuse doors between non-adjacent boxes.
10. **F10 + F14 MAJOR**: finite template pools (about 54 trigger shapes, brush blockers, scriptable lights) are not
    counted, and water, rain, fog and animated screens are designed with no tool and no flag. Fix: TF2 counts pools
    first; each look element gets a probe and a written fallback.

---

## Part 8. Verdict per chapter

| Chapter | Verdict | Main reasons |
|---|---|---|
| 00 PITCH | BUILDABLE WITH THE FIXES | numbers inherit 02's errors (spawners); dangling `REVIEW.md`; "78" sold before F1/F2 |
| 01 LORE / WIKI | BUILDABLE AS WRITTEN (skimmed for names and numbers only; no buildability issue found) | |
| 02 WORLD | BUILDABLE WITH THE FIXES | F9, F10, F11, F12, F13, F14, F15, F16 |
| 03 TRANSPORT | BUILDABLE WITH THE FIXES | black-out version 1 is sound; F15 ring claim, F19 zone tracking, capsule/hatch entities in F8 |
| 04 PAP QUEST | BUILDABLE WITH THE FIXES | F16 power, F17 Terminus zone, F18 board plates, car-1 brush blockers (F10), fog (F14) |
| 05 WONDER WEAPONS | BUILDABLE WITH THE FIXES | F20 three unflagged families, F21 mod zone, F4 crowd bodies, token entities (F8) |
| 06 PERKS | BUILDABLE WITH THE FIXES | F23 Deadeye ordering, F24 decoy and wheel, F16 power |
| 07 ENEMIES | NOT BUILDABLE as written | F1, F2, F3, F4, F5, F6, F7, F42: the hybrid crowd's body composition, hits and system integration are unproven and partly contradicted by recorded lessons; stand-ins (E0) are buildable |
| 08 CAMOS | BUILDABLE WITH THE FIXES | F25 camo-table rows; layer M honestly gated |
| 09 TAB AND HUD | BUILDABLE WITH THE FIXES | F26 element budget, F27 write budget; Tier 2 is honest |
| 10 EMOTES | BUILDABLE WITH THE FIXES | gates G1-G4 honest; F26, F21 (clips in mod), F28, M1 ordering (F37) |
| 11 AUDIO DIRECTION | BUILDABLE WITH THE FIXES | minor only (bank size owner, bed count) |
| 12 BUILD PLAN | BUILDABLE WITH THE FIXES | F29-F39: order, missing packages, sizes, unmeasurable budgets |
| 13 RISKS | BUILDABLE WITH THE FIXES | early tests not early in 12; stale E5; Part 6 missing risks |
| 14 CLIENT CAPABILITIES | BUILDABLE WITH THE FIXES | F40-F43: Rule 2 fallback, mod download crash, owner decisions, CF2 not minimal, CF3a first |
