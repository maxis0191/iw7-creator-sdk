# Final verification B: the corrected STATION ZERO bible and build plan

Reviewer: independent, no stake, read-only (this file is the only write). Date 2026-11-11.
Read in full: 00, 02, 03, 04, 05, 06, 07, 08, 09, 12, 13, 14, `review/reviewer-B.md`,
`review/CHANGES-AFTER-REVIEW.md`. 10 read at the sections the first review cited (3.7, 5.3, 7, 8, 9 and the
binding notes); 11 checked for the two minor items; 01-LORE and wiki checked by search for stale names and
for the lore corrections. Research checked where a claim depended on it (`zombie_idle_spot` in C and E).
Nothing launched, built or committed.

Verdict words: RESOLVED (the fix is in the text, or the unknown is named with a first probe and a written
fallback); PARTLY (what remains is quoted); NOT RESOLVED.

---

## 1. Status of every finding of the first review

### 1.1 Findings F1 to F44

| # | Status | Evidence in the current text / what remains |
|---|---|---|
| F1 | RESOLVED | 07 2.2: "a body is **at least two entities**, more if hit volumes are entities. E1's first measure is the real entity cost ... 78 is the target, the ledger decides." (But see new problem N3: the body count itself is wrong.) |
| F2 | PARTLY | 07 2.2 and 5 and 13 risk 22 are correct (three routes, clone ceiling 1,000, drop hybrid if all fail). **12 §1 still says**: "Collision for imported models ... avoided by design: ... actors use script hit boxes." Also 07's presence rule ("does not block ... bullets meant for other targets") contradicts route (1) ("the stock zombie model's own collision on a script model"), which would block bullets. |
| F3 | RESOLVED | 07 2.1 State cell: "Proven: only the shared flow field ... its animation, hits, deaths and network came from the engine and do not transfer." |
| F4 | RESOLVED | 07 2.2 "One enemy registry" lists weapons, traps, power-ups, perks, round-end count, counter, recycling, commuting; E1 provides it, E2(a) moves systems onto it; 05 Common rules repeats it. |
| F5 | PARTLY | 07 2.2 "Presence" specifies spacing (40), stand-off (96), anti-stuck rules. Remains: "Inside 96 units a body is either promoted or attacking. So a player never walks through a zombie that looks solid" is false for a body that is attacking with no free record (non-solid and within 96 units). See N4. |
| F6 | RESOLVED | 07 2.5.1 soak runner, 2 to 3 h, stated round skip; 2.5.2 arena dvar, lab-client detection, official-client 20-body sample. |
| F7 | RESOLVED | 07 3 and 4: "The stand-in is the shipping version until the actor kit's probes pass"; 07 5 row "Bullet hits on a script-driven body ... unproven". |
| F8 | RESOLVED | 02 §1 and 12 TF8 (absolute counts against 2,048, ceiling 1,800, worst case per package, lint and script counter). |
| F9 | RESOLVED | 02 §1: "Until TF10 proves a donor-free static model in the game, the prop budget counts those models as entities"; TF10 in wave 0 with the earlier crash reproduced first. |
| F10 | RESOLVED | 02 §1 pools with named fallbacks; 12 TF8 (2) counts pools and refuses an over-budget source. (Minor: 02 and 13 risk 24 say TF2 counts the pools, 12 gives it to TF8.) |
| F11 | PARTLY | Police Post moved (y 3600..4600, now shares y = 4600 with the Cordon), chute removed, Escalator Hall link corrected, bays moved. **D1 still joins boxes that do not touch**: Fare Hall "y 3200..4400", Cordon "y 4600..5800": a 200-unit gap. "the flight ... lies inside the Cordon's box" does not close it, and "Every door joins two boxes that share an edge in plan" is false for D1. Bays: "x from -2960 to -1360 in steps of 330" does not compute (five 320-wide bays at step 330 end at -1320). |
| F12 | RESOLVED | 02 §4.9: "the pit under the cars is therefore not walkable ... the walkable pit, its spawners and the trap are all west of car 1"; collector shoe "in the open pit just west of car 1". |
| F13 | PARTLY | 02 §6 is now right ("the stock stair construction everywhere ... navigation lay 14 to 36 units under the generated smooth collision ramp"; a nav-versus-surface check at 6 units). Remains: **13 risk 7** "long ramps and straight flights only ... eight heights, every ramp"; **12 §1** "The layout as data, with terraces, long ramps"; **12 TF2** "terraces at eight heights; long ramps". 02 still describes Shelter 7 "a ramp down from the blast door" and the Breach "a raw ramp" without saying these are built as stair construction. |
| F14 | RESOLVED | 02 8.1: water, rain, sky, Terminus white, screens, rectifier flicker, each with a probe and a fallback. |
| F15 | PARTLY | Spawners 186 and "4 to 14 per zone" (fixed); seven heights (fixed); 190 u/s marked as an assumption replaced by TF2/W1a (fixed); 03's false "never both at once" removed (fixed); 02 §1 now "about 19,500 m2 of gross plan area ... walkable ... near 15,000" (fixed). Remains: **00** "about 18,900 m2 walkable (2.8 times the present map)"; **02 §1.1** density still computed on "6,000 props over 18,900 m2"; **02 Totals** "props 9,110 planned" while the per-zone budgets sum to 8,870, "Lights 604" while they sum to 586. |
| F16 | RESOLVED | 04 §1 and 06: the Cordon has "its own generator struct that is on from the first second". |
| F17 | PARTLY | 04 §4/§7: the Terminus is "a spawn volume of its own with no spawners and no neighbours". Remains: 04 §7 says Q1 tests "all players in the Terminus for **75 s** at round 20" (the stay is now 40 s), and **12 Q1's proof list does not contain the case at all**. The new "spawning pauses" rule has no mechanism (N11). |
| F18 | RESOLVED | 04 §7: "about 40 plate models, at most 5 shown ... counted in the entity ledger (TF8); if the ledger is tight the board keeps only whole-line plates". |
| F19 | RESOLVED | 03 §6 (rider counted in the destination zone from launch) and §9 (T1 reads zone and spawner activity). (12 T1's proof does not repeat it: see N7.) |
| F20 | RESOLVED | 05 "Mechanics that are unproven" table (sticking projectile, arc, aim as trigger, flight, spray, holding at a waiting place, mode chain) with fallbacks; 12 WW2 to WW4 first probes. |
| F21 | PARTLY | 05 Common rules: "in the map's own zone ... Putting them in the servers' global mod instead is a recommendation left to the owner"; 14 §2 row; 10 binding note. Remains: **12 §5** "WW1 to WW4 \| weapon assets in the mod zone, which the official client already downloads by itself"; **12 §5** "M1, M2, CF4 \| clips in the mod zone"; **14 §1** "Not client capabilities: ... weapons in the mod zone"; 08 "512 if the mod size budget requires". |
| F22 | RESOLVED | 05: "a player may hold two different ones" (no extra-slot perk); 02 Lost Property is now a buy-back window; SI1 owns the per-map feature profile. |
| F23 | RESOLVED | 12 W1b "five stock perks ... (Deadeye Dewdrops waits for P1)"; 06 §4. |
| F24 | RESOLVED | 06 §4 Double Takes row: unproven, P1 first probe, fallback "lose the player as a target for 4 s"; Lucky Dips removed. |
| F25 | RESOLVED | 08 Building notes (2): new camo row from the map zone as K1's first probe, two fallbacks in order. |
| F26 | RESOLVED | 09 §3: one allocator, per-state table, admission by priority, proof per state. |
| F27 | RESOLVED | 09 §4: one write per player per 5 s, a server-wide token bucket shared with Maxis and the wheel (16 per 10 s with eight players). |
| F28 | RESOLVED | 10 binding note: "zombies keep targeting the player and hits land on the player's real collision". |
| F29 | RESOLVED | 12 §3 wave 0 lists TF4; W1a depends on TF4. (Cosmetic: the TF4 row still sits in the wave 2 table with "(moved to wave 0)"; 13 risk 5 still makes TF4 conditional on "Over 30 minutes".) |
| F30 | RESOLVED | 12 TF9 with a provoked +1 ms proof, before E1. (Under-specified: N18.) |
| F31 | PARTLY | One number (85 %) in 07 2.4 and 12 §5; 1920 x 1080; "then runs this one" gone; weaker machine moved to ST1. Remains: ST1's "weakest machine the project can use" is not named and no second machine is known (a sub-thread must ask); 07 2.4 still says "package Z1 adds the first number from a weaker machine"; "fixed points" are not defined as named atlas points. |
| F32 | RESOLVED | ST1 after W1b; TF5's build half "before any zone is dressed beyond W2"; "script hiding only helps entities". |
| F33 | RESOLVED | E1 in wave 1, "may start on a shipped map from a bench"; 13's three first tests reordered accordingly. |
| F34 | RESOLVED | TF6 in wave 0 on the present map; W1a reuses kept dressing "so that the first playable is not worse than today's map anywhere". |
| F35 | RESOLVED | HO1, TF8, TF9, TF10, SI1 (size, profile, 64 entries, journal) added; staff doors removed by design (plates). |
| F36 | PARTLY | W1 split (W1a L, W1b M); E2 in four steps, E3/E4 in two. Remains: **TF2** still one L package, not split into "data model + emitter for the present nine zones, diff-identical build" then the new layout. |
| F37 | PARTLY | M0 added; 13 risk 3 no longer cites E5. Remains: **00 still lists `REVIEW.md`**; K1 and WW1 still depend only on "cleanup" while using `Test-WeaponVisual.ps1` / `Test-WeaponE2E.ps1`, with no instruction to run them through a bench root. |
| F38 | PARTLY | W1b: "a 15-round run with bots on the soak runner". Remains: **12 M3** "a plan picks all 65 by pointer" (needs a client with input, not a bot); whether the soak runner loads a custom map from a bench is not part of TF1's proof. |
| F39 | RESOLVED | 12 §1 rows added (static twins, ledgers, hits, registry, meters, looks, camo rows, failed download, hero objects, size); the rest is in §4's distrust list. |
| F40 | PARTLY | 14 §2 and 00 now say plainly that a manual install is not acceptable and recommend private servers only. Remains: **12 §5 row "TF6, CF3" fallback: "a join message with install steps"**, which is exactly the Rule 2 violation. |
| F41 | PARTLY | 14 says "Where this page says what should or should not be offered on public servers, it is a recommendation" and labels both rows "Recommendation to the owner". Remains: **13 risk 20** mitigation "Station Zero stays out of public rotations and at four slots until CF3 and CF5 are in players' hands" (a deployment stated as the plan's); **12 §5** "it never sits in a rotation". |
| F42 | RESOLVED | 14 §2: "In hybrid mode no zombie depends on agent records beyond 24; that every body is actually drawn is what proof 2 ... measures, nothing is assumed". |
| F43 | PARTLY | CF3a first, CF2 called "not a small change", order CF3a, CF1, CF5, CF3b, CF4, CF2. Remains: no capability for "UI sound from Lua" if 11's probe fails (not mentioned in 14). |
| F44 | RESOLVED | 14 §2 feature table is complete and honest. |

### 1.2 Contradictions C1 to C17

| # | Status | Note |
|---|---|---|
| C1 | RESOLVED | 186 in 02 and 07 |
| C2 | RESOLVED | 07 2.3 "4 to 14 spawners (186 in all)" |
| C3 | RESOLVED | 85 % in both |
| C4, C5, C6, C7 | RESOLVED | |
| C8 | RESOLVED | "W-C" gone |
| C9 | RESOLVED | |
| C10 | PARTLY | 02 says seven heights; 12 TF2 and 13 risk 7 still say "eight heights" |
| C11 | RESOLVED | (loop 3 still writes "Platform A East, Escalator Hall", skipping West; harmless) |
| C12 | RESOLVED | |
| C13 | RESOLVED | |
| C14 | PARTLY | the flight is inside the Cordon box, but the 200-unit gap remains (F11) |
| C15 | RESOLVED | |
| C16 | **NOT RESOLVED** | 00 line 90 still lists "`REVIEW.md`", which does not exist |
| C17 | PARTLY | 12 now states the model rule as "owner's rule of 11 Nov 2026, relayed by the environment session that night", with no file a sub-thread can open; AGENTS.md point 10 and the memory note "Subagent models: Fable medium" still say otherwise. Cite a file (or add the rule to AGENTS.md through the environment session) |

### 1.3 Part 6 missing risks

| Missing risk | Status | Where |
|---|---|---|
| Hits on script bodies / clones | RESOLVED | 13 risk 22 |
| Static models without a donor | RESOLVED | risk 23 |
| Template pools | RESOLVED | risk 24 |
| Mod change re-downloads for everyone; failed download kills client | PARTLY | failure covered (risks 9, 20, CF3a); the re-download size and frequency of the global mod is only in 10 §7, not a 13 risk |
| `MAX_ARENAS` 64 | PARTLY | in 14 3b and SI1, not a 13 risk |
| GSC limits | RESOLVED | risk 28 |
| Join stall 1 in 3 | RESOLVED | risk 27 |
| Server frame overrun | RESOLVED | risk 25 (body count wrong, N3) |
| Snapshot and bandwidth with extra movers | PARTLY | 07 2.2 network bullet (E2 measures before cap > 36); no 13 risk |
| Bots instead of humans | RESOLVED | risk 27 |
| Visual target with a stop rule | RESOLVED | risk 29 |
| Licences of library clips | PARTLY | 10 §1 and notes record terms; no 13 risk |
| Machine contention | RESOLVED | risk 30 |
| Present map's failures recurring (stair up, bottom-landing spawners, suitcase on nav) | PARTLY | risk 7 exists but with the inverted mitigation text (F13); no offline gate per failure class |

**Counts.** F1 to F44: 30 RESOLVED, 14 PARTLY, 0 NOT RESOLVED. C1 to C17: 13 RESOLVED, 3 PARTLY, 1 NOT
RESOLVED (C16). Part 6: 9 RESOLVED, 5 PARTLY. **All items: 52 RESOLVED, 22 PARTLY, 1 NOT RESOLVED.**

---

## 2. New problems introduced or exposed by the rewrite

Severity as in the first review (MAJOR = costs a failed package or an unmet rule; MINOR = a builder trips).

### 2.1 World plan (02), box by box

All 18 boxes and the Terminus were rechecked. No two boxes overlap. Every door shares an edge **except D1**:

| Door | Boxes | Shared edge |
|---|---|---|
| D1 Cordon / Fare Hall | y 4600..5800 / y 3200..4400 | **none: 200-unit gap** |
| D2 Cordon / Police | y = 4600, x 1000..2200 | yes (fixed) |
| D3 Fare / Escalator | y = 3200, x -800..-200 | yes |
| D4 Fare / Arcade | x = -1200, y 3500..4300 | yes |
| D5 Fare / Police | x = 1000, y 3600..4400 | yes |
| D6 Fare / Breach | 16-unit wall | yes |
| D7 Arcade / Shelter | x = -3000, y 3700..4300 | yes |
| D8 West / Boneyard | 16-unit wall | yes |
| D9 Boneyard / Parlour | 16-unit wall (y 2584 / 2600) | yes |
| D10 Parlour / Bellows | x = -3800, y 2600..3400 | yes |
| D11 East / Signal | x = 2400, y 1700..2400 | yes |
| D12 Signal / Converter | x = 3000, y 2200..2400 (200; with a -160 to -320 drop inside it) | yes |
| D13 tunnel mouth / Car Barn | x = 3500, y 1216..1584 | yes |
| D14 Car Barn / Converter | y = 2200, x 3500..4200 | yes |
| D15 Car Barn / Sump | y = 800, x 3500..4700 | yes |
| D16 Converter / Exchange | y = 3000 | yes |
| D17 Exchange / Staff Stair / Police | x = 3000 and x = 2200, y 3700..4000 | yes |

- **N1 MAJOR. D1 is not buildable as written** (TF2 is told to refuse it). Fix: extend the Fare Hall box to
  y 3200..4600 (2200 x 1400). Checked: it then touches the Arcade (x = -1200), the Police Post (x = 1000) and
  the Cordon (y = 4600) without overlapping the bays (x ≤ -1320). Add about 280 m2 to the gross area.
- **N2 MINOR.** Arcade bays: give the five x ranges (-2960..-2640, -2630..-2310, -2300..-1980,
  -1970..-1650, -1640..-1320).
- **N19 MINOR (numbers).** Props 9,110 vs 8,870 summed; lights 604 vs 586; density on 18,900 m2 vs 19,500.
- **N23 MINOR.** ALL STAND, commuting and Rollers all need waiting places (`zombie_idle_spot`, which the shipped
  map has 43 of: E §7), but W1a's scope does not place them and no density rule exists. Fix: W1a places them
  with a coverage rule (every walkable cell within 400 units of a place with room for 6) and lists the count.

### 2.2 Capsule Post (03)

- **N5 MAJOR. The address dial has no input.** The server can read fire, aim, melee, use and the view direction
  (09 §4, B). "a pointer the rider turns" is not an interaction a builder can implement without inventing one.
  Fix: state it, e.g. "Use cycles the pointer through the three addresses (the plate shows name, price and
  lamps); hold Use 0.6 s sends"; or three separate Use spots at each hatch, one per address. Add the
  multi-player case (two riders dialling at once).
- **N6 MAJOR (balance). The Post is a cheap way to drop the Inspector's mark.** 07: the mark is re-chosen
  when the marked player "becomes skipped for 5 s", and riders are skipped. A 9 s ride (400 points) or a 40 s
  Terminus visit sheds the mark and the fines. Fix: a rider or a Terminus visitor keeps the mark (paused);
  re-choose only on down, away, spectate or disconnect.
- **N7 MINOR. T1's proof is stale**: "a plan rides all four hops in both directions" belongs to the old ring.
  Now: 12 origin-destination pairs on BLOW and on DRAW, each time (5/9/13 s, or 2.5/4.5/6.5 in version 1) and
  price read back, plus the rider's zone during the ride (03 §9) and the busy-flag refusals.
- MINOR: in version 1 (black-out) say where the rider's body is during the black-out (held at a hidden point
  inside the destination zone is consistent with 03 §6).

### 2.3 Wonder weapons (05)

- **N9 MAJOR. SEND has no navigation rule.** "posted to the point under your crosshair (up to 1,200 units
  away, on any surface in sight)": a zombie sent onto a ledge, a roof beam, a train roof or the off-nav pit
  under the cars is stuck, and a stuck zombie blocks the round's end. Fix: the destination snaps to the nearest
  navigation point within 64 units of the aim point, otherwise the send is refused (the puff). Same rule for
  "sending into a hatch". RETURN TO SENDER's "walks back toward the place it was stamped for 4 s" is a goal
  override of an engine agent, unflagged: add it to the unproven table with the fallback "stands for 4 s".
- **N8 MAJOR. ALL STAND has undefined cases.** No free waiting place within 400 units (all full, or none
  near); a parked zombie next to a player (does it attack?); a parked zombie woken by a shot (does R28 still
  land?); a walk to the place longer than the paint lasts. "MAGENTA with every waiting place full" is a named
  test with no expected result. Fix: no free place within 400 → the 6 s stand where it is (the written
  fallback); parked zombies do not attack until woken; a woken zombie takes no R28.
- **N10 MAJOR. "Flat rated damage" and "withholding hit points" have no mechanism and are not in the
  unproven table.** To deal exactly R24 to engine agents and bodies, the weapon definition's damage must be
  neutralised and the damage applied by script, and the stock modifiers (Bang Bangs' fire rate is fine, but
  head multipliers, Insta-Kill, PaP and Baker's Dozens' exclusion) must be stated. Withholding the stock 10
  hit points (EXACT CHANGE) and paying double hit points (Baker's Dozens' 13th hit) both need a hook on the
  stock points award. Fix: add both to WW1's and P1's first probes; fallback for points: subtract or add the
  difference by script right after the stock award.
- **N15a MINOR.** Tokens: 05 "12 tokens in all" vs 12 §5 "20 tokens alive" per player.
- MINOR: kills by a send or a burst: say who gets the kill points.

### 2.4 Night Inspector and Rollers (07)

- **N3 MAJOR. The crowd count is wrong by six.** 07 2.2: "Of the 24, 6 are reserved from round 10 on.
  Ordinary zombies use 18." At cap 78 that is 18 agents and **60** bodies, not "up to 54"; 120 entities at
  two per body, not 108. Affects 07 2.1 table, 07 2.2 entity sentence and network bullet ("108 more"), E1's
  "cost per body for 1, 20, 54", 13 risks 3 and 25, and 00's "78 bodies of which 24 are engine zombies".
- **N4 MAJOR (honesty).** "a player never walks through a zombie that looks solid" is false for an attacking
  crowd body inside 96 units. Fix: an attacking body is first in the promotion queue; while no record is free
  the script pushes the player out of its 24-unit radius (or the sentence is withdrawn and the case stated).
  Also resolve the conflict with hit route (1), whose collision would block bullets.
- **N12 MAJOR. Rollers' "skating reach" is undefined data.** "Rollers cannot skate stairs, tight rooms or
  train cars", "out of skating reach for 10 s", "every level has walk-in spawners for them": nothing in the
  map source marks skateable cells, so E3 would invent it. Fix: a skate mask in TF2's scene description (cells
  tagged skateable, minimum width), out of reach = no skateable cell within 300 units with line of sight;
  thrown skates written in the entity ledger (24 Rollers x 1 skate in flight). The E3/E4 budget in 12 §5
  says "16 Rollers" while 07 allows 24 with four players.
- **N13 MINOR. The Conductor closes every car's doors** (07 §1) while 04 §7 makes even car 1's doors a
  pool-dependent fallback ("the doors stay open"). Fix: the Conductor's door closing depends on TF8's brush
  count, with a fallback (leaves move, no blocker).
- **N14 MINOR. The Inspector stand-in is under-specified.** E0 puts "the mark, fine, inspection-plate travel,
  reward on the stock mini boss", which is "hurt only in the head" and spawns from its own structs. Say whether
  the stand-in keeps stock damage rules and whether it can spawn and travel by plates (a probe), or uses
  `brute_hide_org` as the shipped map does.
- MINOR: plates "lift" (17 moving entities) are not yet in any ledger line; the marked-player tie rule
  ("nearest the plate") is circular when the plate is chosen by the marked player's zone.

### 2.5 New perks (06)

- **N20 MINOR.** Sour Grudges' "green fume ... seen only by you" needs a per-client effect; not shown anywhere
  in the research. Fallback: a per-player HUD marker or a fume everyone sees.
- **N22 MINOR (honesty).** "none repeats an effect of a perk or a card of the base game or of its sister
  series" is an unverified claim (no list checked). Make it a P1 check against the base game's perk and card
  tables, or soften it.
- Baker's Dozens' counter, half-price traps, "a trap you bought does not hurt you": scriptable on project-made
  traps; covered by P1's plans. No issue beyond N10.

### 2.6 Terminus (04)

- **N11 MAJOR. "The round's spawning pauses and the zombies alive wait where they are" has no mechanism**,
  is not in 04 §7's buildability table, and Q1's proof does not test it. Fix: Q1 case "every living player in
  the Terminus at round 20: alive count, spawns during the 40 s, script errors"; candidate mechanisms (cap
  temporarily equal to the alive count; alive zombies sent to waiting places); fallback (the round simply
  continues and the cooldown stays 150 s). Also correct "75 s" to 40 s, and decide what happens to a downed
  player left outside car 1 while every living player is away (bleeds out? paused?).
- MINOR: the clock from 23:59:20 to 23:59:59 runs 39 s, not 40 (04 §3, wiki "the-terminus.md"). Start it at
  23:59:19.
- MINOR (lore): 00 "sent through a forgotten Victorian pneumatic tunnel" and 04 §6 "the bypass through
  Vayle's tunnel" contradict the binding lore correction ("driven **around** Vayle's tube ... A six-car train
  never ran inside the eleven-seat tube"; 01-LORE line 21 is correct).

### 2.7 The new packages in 12

| Package | Scope | Dependencies | Proof | Size | Problem |
|---|---|---|---|---|---|
| TF8 | clear | N2 | measurable | M | fine; 02 and 13 risk 24 still give the pool count to TF2 |
| TF9 | clear aim | cleanup | provoked +1 ms server and heavy pass client | L | **no inputs, no tools, no candidate mechanism** (N18): name the candidates (time wrappers in map scripts, the dedicated's frame log, the engine-map/perf recorder in iw7-mod-components, RenderDoc package J) and the fallback (A/B toggle measurement on server frame time) |
| TF10 | clear | N1, N2 | both drawn, zero entities, earlier crash reproduced | L | no inputs: cite C §2.2, D §5 and §6 (the AV at iw7_ship+0xDCE6E7, the five excluded models) |
| ST1 | clear | W1b, TF9 | table + written decision | M | **"the weakest machine the project can use" is not identified** (N17): a sub-thread must ask. Name it, or define a GPU-bound proxy on the reference machine (2560 x 1440 and 3840 x 2160 render) and record the owner question separately |
| HO1 | clear list | A1, TF10 | reviewers 7/10, ledger status | L in batches | fine; absent from §5 |
| SI1 | clear | W2 | profile test, size table | M | 2a says wave 3, §3 draws it in wave 2; absent from §5 |
| M0 | clear | TF1 | yes/no with frames | S | fine; "seen by a second client" needs a client plan, not headless: say so |
| CF3a | clear | (none stated) | cut download on fork client, mod and map | S | fine; name the tool that cuts the download (netlab) |
| CF3b | clear | TF6 | fresh profile joins and plays | L | fine |
| W1a | clear | TF1, TF2, TF4, TF8 | file checks, climbs 90 %, timed walk | L | add waiting places (N23) and the skate mask (N12) to its scope |
| W1b | clear | W1a | 15 rounds on the soak runner, baselines | M | soak runner on a custom map from a bench is not proven by TF1 |

**Order (§3).** Coherent: wave 0 tools, wave 1 W1a → W1b → ST1 with E1 and M0 in parallel, wave 2 the look
and TF5's build half, etc. Defects: the TF4, TF6, TF5 and E1 rows still sit in later wave tables marked
"(moved)"; E2 "Depends on ... TF5" although TF5's build half runs only "if ST1's numbers demand it" (write
"TF5, or ST1's written decision that it is not needed").

**Section 5 completeness. Not every package is present.** Missing rows: **TF8, TF9, TF10, ST1, HO1, SI1, M0,
CF3a, CF3b** (only "CF3"). TF10 and HO1 put models into the map zone (size, entities, look) and SI1 changes
what a player meets on the server (feature profile), so they need delivery, budget and fallback lines.
Rows that contradict the chapters: WW1 to WW4 "in the mod zone" (05, 14 say map zone); "20 tokens alive"
(05: 12 in all); TF6/CF3 fallback "a join message with install steps" (14: not acceptable); M1/M2 "clips in the
mod zone" (10 note: map zone by default); E3/E4 "16 Rollers" (07: up to 24). (N15)

### 2.8 Stale lines left by the rewrite (N19, MINOR, one edit each)

12 §4 item 2 "zombies can be put in the dance state from script (WW2)" (ALL STAND replaced the dance);
12 W4 "the 27 lore pickups" (25 in the binding changes); 12 TF2 "eight heights; long ramps"; 12 §1 "long
ramps"; 13 risk 7; 13 risk 5; 07 2.4 "Z1 adds the first number from a weaker machine" (ST1); 08 "mod size
budget"; 00 area and `REVIEW.md`.

---

## 3. Honesty and deployment wording

- **00** overclaims the area ("about 18,900 m2 **walkable** (2.8 times the present map)"; 02 says gross
  19,500, walkable near 15,000, "a little over twice") and the agent share ("24 are engine zombies"; 18 at the
  cap). Its "What a player gets" section is otherwise honest.
- **07 2.2** "a player never walks through a zombie that looks solid" (N4); **12 §1** "actors use script hit
  boxes" (F2); **06** originality claim (N22).
- **Deployment wording.** 14 is now correct. Still voiced as the plan's own decision: **13 risk 20** ("Station
  Zero stays out of public rotations and at four slots until CF3 and CF5 are in players' hands") and **12 §5**
  ("it never sits in a rotation that would send an unprepared client into it"). Both should read
  "recommended to the owner (14 §2)". 07 2.1's "Decision" block is a technical build order (Route H first,
  one dvar) and is acceptable; its sentence "A server started with the capacity profile admits only clients
  that have it" is a technical behaviour, not a deployment. Z2 correctly leaves deployment to the owner.
- No remaining text proposes posting to the client project; 14 §3 rule 4 and 12's rules forbid it.

---

## 4. Verdict per chapter

| Chapter | Verdict | Fixes required |
|---|---|---|
| 00 PITCH | BUILDABLE WITH THE FIXES | area (gross, about twice), 18 agents at cap, remove `REVIEW.md`, lore line "around" the tube |
| 01 LORE / WIKI | BUILDABLE AS WRITTEN | (39 s vs 40 s clock nit) |
| 02 WORLD | BUILDABLE WITH THE FIXES | N1 (D1: Fare Hall to y 4600), N2 bays, totals and density area, "ramp" descriptions → stair construction, waiting places (N23) |
| 03 TRANSPORT | BUILDABLE WITH THE FIXES | N5 dial input, N6 mark kept during a ride, rider position in version 1 |
| 04 PAP QUEST | BUILDABLE WITH THE FIXES | N11 spawn pause mechanism and Q1 case, 75 s → 40 s, downed-player-left-behind rule, lore line |
| 05 WONDER WEAPONS | BUILDABLE WITH THE FIXES | N9 send snaps to nav, N8 ALL STAND cases, N10 flat-damage and points hooks as first probes, kill credit for sends |
| 06 PERKS | BUILDABLE WITH THE FIXES | N10 points hook (Baker's Dozens), N20 per-client fume, N22 originality check |
| 07 ENEMIES | BUILDABLE WITH THE FIXES (was NOT BUILDABLE) | N3 60 bodies / 120 entities, N4 presence and route (1) conflict, N12 skate mask and thrown skates, N13 Conductor doors, N14 stand-in spec, Z1 → ST1 |
| 08 CAMOS | BUILDABLE AS WRITTEN | ("mod size budget" → map) |
| 09 TAB AND HUD | BUILDABLE AS WRITTEN | |
| 10 EMOTES | BUILDABLE WITH THE FIXES | body text of 5.3 and 7 still says mod zone (the binding note overrides; edit it); M3's pointer plan needs a client with input |
| 11 AUDIO DIRECTION | BUILDABLE AS WRITTEN (sections checked) | bank size now owned by SI1; 18 beds with no Terminus music is consistent |
| 12 BUILD PLAN | BUILDABLE WITH THE FIXES | §5 rows for TF8, TF9, TF10, ST1, HO1, SI1, M0, CF3a, CF3b and the five contradicting rows; §1 hit-box row; stale TF2/W4/§4 lines; T1 and Q1 proofs; TF9/TF10 inputs; ST1 machine; rows moved to their waves; E2's TF5 dependency |
| 13 RISKS | BUILDABLE WITH THE FIXES | risk 7 (stair lesson, seven heights), risk 5, risk 20 (recommendation), risks 3 and 25 (60 bodies); add the four PARTLY risks of 1.3 |
| 14 CLIENT CAPABILITIES | BUILDABLE WITH THE FIXES | §1 "weapons in the mod zone" line; optionally a Lua UI-sound capability |

---

## 5. Final judgement

**Can build sub-threads execute 12-BUILD-PLAN.md without inventing or asking? Not yet: no, but close.** The
rewrite fixed the structural failures of the first review: the blockers (hits, entity cost, the ledger,
donor-free statics) are now first probes with fallbacks, the order is tool-first, E1 and the stress test are
early, and 14 is honest about what the official client gets. What still forces a sub-thread to invent or ask
is narrower: a door between boxes that do not touch (TF2 would refuse its own input), one input mechanism and
several rule gaps in the redesigned mechanics (the dial, sends off the navigation, ALL STAND with no place,
the Terminus pause, Rollers' reach), a machine nobody has named for ST1, and a section 5 that still contradicts
the chapters on where the weapons and clips ship and on the map's fallback.

The three things I would change first:
1. **Give 12 one voice.** Complete §5 with the nine missing packages and correct its five contradicting rows
   (map zone for weapons and clips, 12 tokens, no install-message fallback, 24 Rollers); delete the stale lines
   (§1 hit boxes and long ramps, TF2 eight heights, §4 dance state, W4 27 pickups); move the "(moved)" rows to
   their waves; fix T1's and Q1's proofs; give TF9 and TF10 their inputs; name ST1's second machine or its
   GPU-bound proxy.
2. **Fix the numbers that drive budgets and geometry.** D1 (Fare Hall to y 4600), 60 crowd bodies and 120
   entities at the cap (07, 13, 00), the bays, the props and lights totals, the area in 00.
3. **Specify the redesigned mechanics' missing rules before their packages start.** Dial input; the mark kept
   through a ride or a Terminus visit; sends snapped to navigation; ALL STAND with no free place; the Terminus
   spawn pause with a Q1 case and a fallback; Rollers' skate mask in the scene description; and the flat-damage
   and hit-point hooks added to WW1's and P1's first probes.
