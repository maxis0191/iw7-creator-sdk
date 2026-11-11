# STATION ZERO bible: final verification (reviewer A, second pass)

Scope: the rewritten `00` to `14`, all of `wiki/`, `review/CHANGES-AFTER-REVIEW.md`, checked against
`review/reviewer-A.md` and the measured numbers of `research/E-shipped-map-numbers.md` (health
`950 x 1.1^(w-9)` from w10; kill 60, head 100, 10 a hit; zombies per round 4p/solo: w10 78/33, w25 361/80,
w40 888/168, w50 1,374/249). Nothing was launched, built or committed. Quotes are from the current files.

Verdict scale: RESOLVED, PARTLY (what remains), NOT RESOLVED. A renamed thing with the same flaw counts as not
resolved.

---

## 1. Status of the first review's findings

### 1.1 The ten most important

| # | Finding | Status | Evidence (current text) and what remains |
|---|---|---|---|
| 1 | B1 share-of-health weapons never fall off | **PARTLY** | `05` now: "Damage is flat and rated by round ... Nothing in this chapter kills 'at any round'." True for one application, but the Dispatcher reintroduces an any-round kill by repetition: a survivor "lands there knocked down for 2 s and **keeps its stamp**", and SEND costs no ink and has no cooldown. At w50 four stamped zombies die after 7 sends (6 x 7,030 + burst), about 7 s, for 4 ink; upgraded (R38, 6 stamps) after 4 sends. "Past round 30 a send moves and wounds, it does not kill" is false. |
| 2 | B2 Exact Change prints money | **PARTLY** | Hit points withheld, pierced kills half pay: fixed. But "a head-shot kill on the first zombie returns that shot's fare" has no rate limit and refunds the *surged* fare, so the surge (the only brake the text cites: "sustained fire is dear") is cancelled for head shots exactly as before. Rounds 25 to 33: one free head token = +100 (+30 per pierced kill if pierce carries head damage), at 110 a minute. Upgraded: free one-shot heads to w41, and at w50 three heads (2 paid x 30, last refunded) earn 100: still profit. The section's own sums are wrong (see section 2.1). |
| 3 | B3/B4 YELLOW chain nuke; density amplifies area weapons; nothing tested at 78 | **PARTLY** | Cascade removed ("The burst does not tag ... one generation only"); every weapon now has "tested ... with 24 alive and with 78 alive" and named cases. No kill-count cap per activation: a YELLOW burst (R28, 160 units) and a Dispatcher send (four R24 bursts, "do not add on one target beyond two") still clear every body in the circle; YELLOW bursts on one target stack without limit. MAGENTA's brake ("a place holds 6") depends on waiting places that `02` never places or counts. |
| 4 | O1/O2/O3 Dischord dance, WILDSTYLE film title, Kirby inhale | **RESOLVED** | "MAGENTA · 'ALL STAND' ... walks to the nearest waiting place and stands behind the line"; "TOP TO BOTTOM"; "STAMP ... SEND". All three verbs now belong to the map. (New name risks: "Primer", "RETURN TO SENDER", see 2.6.) |
| 5 | B8 Inspector mark gameable, griefable, kiteable, unkillable/trivial | **PARTLY** | Fixed: "earned the most points during the last two rounds. Not unspent points"; skips "downed, away ..., in the Terminus, or riding the Capsule Post"; "each fined player's own pile"; flat health; plates per zone; "If not killed" rule; tie rule. Remains: (a) trivial with Exact Change: a head token on the open lamp is 9,920 x 3 = 29,760, more than the first four-player Inspector (13,200) and nearly half the capped one (66,000); a Dispatcher stamp holds the lamp open 3 s = five tokens; solo, one token on the *shut* lamp kills the first Inspector (6,000). (b) the mark is shed at will: ride the Post for 5 s and it is "re-chosen". (c) 150 u/s with a 2 s scuttle every 10 s averages 172 u/s against a 190 u/s player: still kiteable, and ignoring him costs nothing but the Validated Ticket. |
| 6 | O4/O5/O7 Beach Pneumatic Transit, Mr. X, The Shining | **PARTLY** | O5 resolved: "Short, very wide, and lamp-headed", "never uses doors", inspection plates. O7: the Shining gala is gone, but the replacement ("a white, shadowless platform", "beyond the platform edge ... only white ... a second platform with a dark train standing at it") is the white limbo station of *Harry Potter and the Deathly Hallows* ("King's Cross", where one may board a train onward) and close to *The Matrix Revolutions*' limbo station. O4: piano and goldfish fountain replaced by the fork wall and listening horn (good, ours), but the institution is still a single-car, single-tube Victorian pneumatic passenger line under a city square, driven by one giant rotary blower, folded within four years ("one tunnel, one car, driven by air"): the Beach Pneumatic Transit in every structural fact. |
| 7 | B7/B9 Roller round cheesed; Terminus a free safe room | **PARTLY** | B9 RESOLVED: "Stay 40 s", "Cooldown 150 s", downed players travel, zombies "pushed out ... unhurt", spawning pauses only when every player is away. B7: fences and CYAN now trip, every level gets walk-in spawners, and hiders are punished by "throw". But throwing Rollers "stop outside" an opening in line of sight with 40 % health: stationary targets for players behind cover, so hiding stays the best play; and the throw only triggers when *every* living player is out of reach, so one player on a stair is untouchable while a teammate runs. |
| 8 | C4/C2/C5 arrival logged; two Graffiti Kings; handle in car 6 | **PARTLY** | C2 and C5 RESOLVED ("Primer"; the handle is ceremonial, carried to the cab). C4 fixed in `04` 6 ("It does not log an arrival"), the board, the clocks page and `zero.md`, but `01-LORE.md` 9 (the canon that "wins") still says winding the clocks "is how the players make ZERO believe the run has arrived". |
| 9 | T1/F4 Pneumo a four-stop loop line with a grief lever | **PARTLY** | The lever can no longer trap anyone ("every destination is always reachable"), pressure legs gone, blowback opt-in (48 units). But it is still four nodes on a ring priced by distance (250/400/550), i.e. a loop line with fare zones and a dial; "hatch", "postage" and "address" are the old "stop", "fare" and "destination". A thrown lever still blocks every launch for 12 s in each 57 s. New exploit, section 2.3. |
| 10 | B11/M1 dull perks; library dances | **PARTLY** | Day Trippers (map-built) and the new Sour Grudges are real improvements. Baker's Dozens is still a number ("+15 % damage on average") wrapped in a counter. Dances: "21 originals ... 19 library clips", but four of the "station" originals are generic social steps (Sprinkler, Lawnmower, Step Class '84, Pendulum), Chicken Dance and Hokey Pokey are kept against the chapter's own song rule, "Take a Bow ... The Rave and Beast finales invite it" still points at other maps. |

### 1.2 Every BLOCKER and MAJOR item

| Item | Status | Current text / what remains |
|---|---|---|
| B1 | PARTLY | see 1.1 #1 (Dispatcher re-send) |
| B2 | PARTLY | see 1.1 #2 (refund cancels surge) |
| B3 | PARTLY | "does not tag ... one generation only": cascade gone; no per-target or per-burst cap, bursts stack on a tagged clump |
| B4 | PARTLY | 24/78 tests named in every weapon; kill caps only for RED ("arcs to 2 more ... no further jumps") |
| B5 | PARTLY | inhale replaced by stamp/send, but the re-send loop (1.1 #1) and the uncapped four-burst send |
| B6 | RESOLVED | "One hit per zombie per fence per 2 s", "pushed 48 units back off the line" |
| B7 | PARTLY | see 1.1 #7 |
| B8 | PARTLY | see 1.1 #5 |
| B9 | RESOLVED | 40 s / 150 s, downs travel, zombies pushed out (only the stale "75 s" in `04` 7 Q1 remains) |
| B10 | RESOLVED | "Sour Grudges ignores wonder-weapon kills"; "The Lost Property window never returns a wonder weapon"; named cases in WW1 to WW4 and P1 |
| B11 | PARTLY | see 1.1 #10; Double Takes now "a target in the crowd's flow field" (good) |
| B12 | RESOLVED | AMBER "the only fuse that acts on specials" |
| O1, O2, O3 | RESOLVED | see 1.1 #4 |
| O4 | PARTLY | see 1.1 #6 |
| O5 | RESOLVED | silhouette and gait new; the follow-the-target stalker loop survives through the floor plates (acceptable) |
| O6 | RESOLVED | `11`: "E5 D5 G sharp 4": falling whole tone then tritone |
| O7 | PARTLY | Shining gone; King's Cross limbo instead |
| O8 | PARTLY | dots removed, TILT cut in `02`, Kings now painters in overalls; but `01-LORE.md` 4 still lists "coin-op arcade" in the underpass; the setting is still 1980s subway + roller disco + graffiti hero + talking machine (Shaolin Shuffle + Spaceland) |
| O9 | PARTLY | Mind the gap, Eyewitness, Midnight Run, Sole Man, Pneumo all gone; "Halcyon" (The Outer Worlds' colony) kept without comment |
| F1 | RESOLVED (one slip) | "Counted honestly: thirteen distinct places ... in eighteen spawn zones"; the Staff Stair has the dock and H7 crates; the booth stair is in the Escalator Hall. Slip: the Staff Stair "counts as part of the Exchange's spawn zone", which makes seventeen spawn zones |
| F2 | RESOLVED | Flashover (blinds), Decon Foam (holds), the Dispatcher no longer sucks |
| F3 | PARTLY | three pay phones, each its own event; but tape 5 ("Strand tape 5.") still has no object, the Exchange still holds two tapes with no reason |
| T1 | PARTLY | see 1.1 #9 |
| P1 | RESOLVED | drawer card "Charge at the organ. Hold on."; "Hold Use at the organ console" |
| P2 | RESOLVED | "a rattle-and-click and a can icon; the stash lid shows three paint dots" |
| P3 | RESOLVED | YELLOW from a Cleaner "tagged with any colour, whoever kills it"; bulging can outline |
| P5 | RESOLVED | "FINE 870" on the HUD; one Voice sentence the first time |
| P4, P6, P7, P8 (MINOR) | RESOLVED | lamp per hatch; dial by name; register with the three lever names; Lucky Dips gone |
| L1 | PARTLY | `01-LORE.md` 9 still "believe the run has arrived" |
| L2 | PARTLY | one Graffiti King; but mural dating contradicts itself (section 3, C8) |
| L3 (MINOR) | PARTLY | 58 staff now explained; the arch "broken from the inside" in 1982 is still not among H1 to H10 |
| L4, L5 (MINOR) | L5 RESOLVED (sitcom lines gone); L4 NOT RESOLVED (every page still ends in a hand-written "In the map" restatement, now with small drift: "the BARN Capsule Post stop") |
| E1 | RESOLVED | "One enemy registry ... Every package that touches enemies ... tests against a mixed crowd" |
| E2, E3 (MINOR) | RESOLVED | Inspector clips 15 to 17 cover lamp-open, stun, slip; Conductor shuts the car doors |
| K1 | RESOLVED | "metal 1.0, roughness 0.24 ... a faint baked environment"; judged "in the Boneyard" first |
| H1 | RESOLVED | `09`: "Said plainly: on today's official client the owner's 'full Tab screen' is not delivered"; `00` carries the box |
| M1 | PARTLY | see 1.1 #10; plus "Roller Boogie" is a 1979 film title, "Lamp Swing" describes the old hand-lamp Inspector |

---

## 2. New problems introduced by the rewrite

### 2.1 Wonder-weapon arithmetic (stock health, kill 60 / head 100, no hit points for Exact Change)

Health: w10 1,045 · w25 4,365 · w40 18,234 · w50 47,295. Alive cap from `07` 2.3: four players w10 36, w25+ 78;
solo w10 24, w25+ 47 (so "78 alive solo" never occurs; the 78 rows below are four-player, or the test dvar).

| Weapon | w10 | w25 | w40 | w50 | 24 vs 78 alive |
|---|---|---|---|---|---|
| EXACT CHANGE body (R24 3,970) | 1 token; +30 a kill | 2 tokens (R24 x2 = 7,940 kills to w31, not w33 as written) | 5 tokens, about -90 a kill | 12 tokens, about -300 | 78 packs lines: a pierce through 3 pays 60+30+30 for one fare |
| EXACT CHANGE head (9,925) | 1, refunded: +100 | 1, refunded, +100 at any cadence (refund includes surge) | 2; the killing head shot is refunded by the rule: 30 paid, 100 earned, **+70** (`05` says "a loss on every kill") | 5; 120 paid, -20 | same |
| KEEP THE CHANGE head (21,270) | free kills | free kills | free kills to w41 | 3 heads: 60 paid, +40 | pierce 4: up to 100 + 4 x 30 + a 25 token per shot |
| LIVE RAIL AMBER (R30) | 1 crossing; 24 kills a fence | 1 crossing; charges gone in seconds at 78 | 3 crossings; at most 8 kills a fence | 7 crossings; about 3 kills a fence | fine; RED arcs (R24) stop killing at w25, which `05` does not say |
| DISPATCHER (stamp 600, send R30, bursts R24 x2 max) | 4 + every body within 140 units | 4 + every body within 140 (2 bursts kill) | **4 kills in 3 sends, about 3 s, for 4 ink** | **4 kills in 7 sends**; upgraded 6 kills in 4 sends | at 78 the burst circle holds about 8 to 15 bodies: uncapped |
| TOP TO BOTTOM MAGENTA (R28 after 6 s) | kills all parked | kills all parked | 32 % wound | 12 % wound | depends on waiting places nobody has placed |
| TOP TO BOTTOM YELLOW (R28, 160 units, stacks) | one bullet clears the clump | one bullet clears the clump | 4 gun kills on tagged bodies clear a tagged clump (4 x 5,810) | control only | denser = more per bullet; no cap |

Fixes: the Dispatcher's send consumes the stamp (or SEND costs one ink per parcel and has a 3 s cooldown);
the Exact Change refund returns the base 30 only, at most once per 1.5 s; correct the "sums" paragraph and the
round table (two body tokens to w31; w40 head shots profit); YELLOW: a body takes at most one burst per 2 s;
Dispatcher burst and YELLOW burst kill at most 6 bodies each; place and count waiting places per zone in `02`.

### 2.2 Perks at w10/25/40/50

| Perk | w10 | w25 | w40 | w50 | Issue and fix |
|---|---|---|---|---|---|
| Baker's Dozens | +15 % average | "a guaranteed kill every thirteen hits" is unprovable: gun damage is not in `research/E` (section 8) | lamp tool | lamp tool | shotgun pellets each count as a hit (a shotgun punches every second shell); say pellets count once per shot. Still a number perk |
| Day Trippers | saves postage and traps | trap 375 | free repositioning | same | **exploit**: free postage + 5 to 13 s of damage immunity per ride + 8 capsules returning every 30 s = an almost continuous invulnerable loop, and the Inspector mark is shed on every ride. Fix: half postage, not free; a 20 s per-player re-dispatch cooldown |
| Sour Grudges | strong 1v1 shield | half the marks expire | rarely pays | dead | fine; scales down as stated |
| Double Takes | `06`: "saves a careless player" | `06`: "needs Tuff 'Nuff to trigger at all" | empties a 400-unit circle | same | contradiction: whether a hit can leave a 100-health player above 0 and under 35 % depends on zombie hit damage, which is not a function of the round and is unknown (`research/E` 8). Measure it in P1 and rewrite both lines |

### 2.3 The Capsule Post

Not overpowered as travel, not tedious (dial by name, 5 s near trip, 250). Overpowered as a shelter: "the
rider ... takes no damage" for up to 13 s, two capsules per hatch, eight in the ring; with Day Trippers it is
free. A solo player can stay in the tubes most of a round, the round cannot progress, and the Inspector's mark
moves ("riding the Capsule Post" is skipped, "re-chosen ... for 5 s"). Fix: per-player cooldown after arrival,
mark not re-chosen while riding, Day Trippers at half price.

### 2.4 Night Inspector

Griefing mostly closed (earned points, own piles). Remaining: mark shedding by Post or Terminus (dumps the
fight on a teammate); the fine still reads *unspent* points ("10 % of the points they hold"), so spending to
zero turns every Punch into a slow. Fight quality: trivial with Exact Change (one open-lamp head token kills the
first four-player Inspector; one shut-lamp token kills him solo), long and dull with ordinary guns late (66,000
at the cap, body 25 %). Fix: wonder-weapon damage to him capped at 3,000 a hit before his multipliers (the stock
Brute rule caps WW hits at 2,000); lamp-open triple only for bullet weapons.

### 2.5 Rollers, Terminus, traps

- Rollers: hide-and-shoot remains dominant (throwers stand still in line of sight); one hider is immune while a
  teammate is in reach. Fix: throwers keep coasting past the opening (a throw on each pass); the throw rule
  applies per hiding player, not when "every living player" hides.
- Terminus: no real abuse left; 40 s in 190 with revives and reloads is acceptable.
- Decon Foam (new): "zombies inside ... cannot attack; players are not slowed" makes the foam corridor a 15 s
  invulnerable room every 60 s (375 points with Day Trippers). Fix: zombies in foam attack at half rate.

### 2.6 Names and images recognisably taken

| Name / image | Source | How close |
|---|---|---|
| The Terminus (white shadowless station, a train waiting at a second platform) | Harry Potter and the Deathly Hallows, "King's Cross" limbo; The Matrix Revolutions, limbo train station | close in concept and image |
| Orbit **Rollerdrome** | *Rollerdrome* (2022 video game, roller-skating shooter) | exact word |
| **Roller Boogie** (emote 4) | *Roller Boogie* (1979 roller-disco film) | exact title, same era and subject |
| **Primer** | *Primer* (2004 film) | exact title; also a paint word, low risk |
| **RETURN TO SENDER** | Elvis Presley song (1962) | exact title |
| **Day Trippers** | The Beatles, "Day Tripper" (1965) | plural of a song title |
| **The Night Inspector** | Frederick Busch's novel *The Night Inspector* (1999) | exact title, low profile |
| Port **Halcyon** | Halcyon colony of *The Outer Worlds* | kept from the first review |
| Copy Stop, Needle Drop | common real shop names; "The Needle Drop" is a known music-review brand | generic, low |
| The Atmospheric | Beach Pneumatic Transit (1870) | structural copy, see O4 |

Fix: rename Rollerdrome (e.g. "Orbit Skateland" is also real; pick an invented word), Roller Boogie, Return to
Sender, Day Trippers; give the Terminus a look of its own (for example the timetable as drawn: blueprint-blue
line work, everything at diagram scale, the footprints as printed dots) instead of white limbo.

---

## 3. Coherence: facts checked and contradictions

### 3.1 Checked and consistent (35)

Door prices and total 19,750 (`02` 3, sum verified); 17 doors (`00`, `02`, `station-zero.md`); spawners 186
(zone sum verified; `02`, `07`); 21 wall weapons (zone sum verified; `00`, `02`); 7 wheel positions; 10 perks
and their zones (`02` 5 = `06` = every wiki zone page); Live Rail part places (`05` = `02`); 3 fuse boxes
(`02`, `05`, `the-four-heroes.md`); RED in the Signal Cabin, GREEN in the Converter Hall; 3 pay phones and
their events (`02`, `01` 11, `secrets.md`, `pay-phones.md`, `transit-police-post-0.md`); 8 tapes and their
places (`02`, `secrets.md`, `strand-tapes.md`); 6 pages; 5 murals; 3 trophies; fare 30 (`05`, `tokens.md`,
`the-wonder-weapons.md`, `09` H6); upgraded tokens 25 points; Terminus 40 s / 150 s (`04`, `the-terminus.md`,
`11`); clock 23:59:20 to 23:59:59 (`00`, `04`, wiki, `11`); 312 footprints + one pair per player; seven
clocks, four quest clocks and their places (`04`, `02`, `the-clocks.md`); the board never says ARRIVAL
(`04`, `the-split-flap-board.md`, `zero.md`, `the-voice-of-the-rapid.md`); four hatches and their zones;
postage 250/400/550 and 5/9/13 s; blowback 48 units, 1 s knock-down; 17 inspection plates (`02`, `07`,
wiki); Inspector from round 10 (11 solo); fine 10 %, 100 to 1,500; Validated Ticket; Conductor 3x health,
shuts the doors; Handle 1.5 s; Roller reward Max Ammo + 500 per player; first Roller round 5 to 7; Day Trippers
"four traps at 375" = traps 750; Up 'N Atoms 1500 / 500 solo; Three-Tone E5 D5 G sharp 4 and its reverse;
`09` HUD worst case 14 -> 15 + 5 = 20 and wheel state 21; Inspector speeds; Kings sacked 1979, arch found
Feb 1982, contract Mar 1982; 58 + 312 + 140 = 510 with the M3 Kings outside it.

### 3.2 Contradictions (both sides quoted)

| # | Side A | Side B |
|---|---|---|
| C1 | `00`: "about 18,900 m2 walkable (2.8 times the present map)"; `02` 1.1: "6,000 props over 18,900 m2" | `02` 1: "about 19,500 m2 of gross plan area ... walkable ... expected near 15,000 m2, a little over twice today's" |
| C2 | `00`, `02` intro: "thirteen distinct places ... in eighteen spawn zones" | `02` zone 7: the Staff Stair "counts as part of the Exchange's spawn zone" (17) |
| C3 | `02` 3: "Every door joins two boxes that share an edge in plan" | D1 Cordon (y 4600..5800) to Fare Hall (y 3200..4400): a 200-unit gap; nothing occupies x -1200..1000, y 4400..4600 |
| C4 | `02` 9: cars 5 and 6 "inside the east tunnel mouth x 2400..3500" | 600-unit cars: 1,200 needed, 1,100 given (first review C18, still open) |
| C5 | `01-LORE.md` 9: winding the clocks "is how the players make ZERO believe the run has arrived" | `04` 6: "It does not log an arrival, and nothing in this quest makes it log one"; `the-clocks.md`: "expecting the train is as far as the winding goes" |
| C6 | `01-LORE.md` 3 and 6: Primer "made the murals and the paint rig in 1985" | `01-LORE.md` 11.3 and `secrets.md`: the murals are a map "drawn before Lodestar bored them" (bored "in 1983 and 1984", `the-capsule-post.md`); `the-zero-kings.md` mural 5 and H9: "dated 1984" |
| C7 | `04` 6: levers "setting the points for the bypass through Vayle's tunnel" | `01-LORE.md` 2 and `the-atmospheric.md`: "the express bypass was never driven through the tube" |
| C8 | `01-LORE.md` 4: underpass shops "record shop, coin-op arcade, ... lost property office" | `02` 4: Copy Stop replaced the arcade; `02` 2: the Lost Property window is in the Fare Hall |
| C9 | `04` 2 step 2: "the train register ... lies open at 23:44" | `02` 10: "a train register open at 23:47" |
| C10 | `04` 7: Q1 tests "all players in the Terminus for 75 s" | `04` 3: "Stay 40 s" |
| C11 | `05` sums: "Rounds 25 to 33: two body shots" | R24 x 2 = 7,940 < w32 8,506: three tokens at w32 and w33 |
| C12 | `05` sums: w40 "two head shots (60 paid for 100, no refund because the kill needs two)"; rule: "a head-shot kill on the first zombie returns that shot's fare" | the second shot is a head-shot kill and is refunded; and `05` table: w40 "a loss on every kill"; "past round 33 it pays only for head shots" (both cannot be true) |
| C13 | `05` 3: "Past round 30 a send moves and wounds, it does not kill" | `05` 3: a survivor "keeps its stamp" and SEND has no ink cost or cooldown (re-send kills at any round) |
| C14 | `05` 5 ledger: "12 tokens in all"; KEEP THE CHANGE "at most 12 lying" | `12` 2: "per player at most ... 20 tokens alive" |
| C15 | `09`, `secrets.md`, CHANGES: 25 collectables | `12` W4: "the 27 lore pickups" |
| C16 | `12` WW1: "the six proofs at the end of `05`" | `05` lists seven; `12` WW2 to WW4: "the seven proofs" |
| C17 | `10` 5.2: the wheel's "13 elements, under the 24 budget, leaving 11 for the map's own HUD" | `09` 3: in the wheel state "wheel 13, counter 5, H2 and H4 if active (3) = 21", the rest released |
| C18 | `10` row 20 Lamp Swing: "the right arm out with an imaginary lamp swung at arm's length" | `07` 3: the lamp is his head; "Right arm: a hydraulic ticket punch" |
| C19 | `06` Double Takes: "Round 10: saves a careless player once a minute" | same entry: "Round 25: needs Tuff 'Nuff to trigger at all" |
| C20 | `07` 4: Rollers "at most 16 alive (24 with four or more players)" | `11` 4: "four chains at most (16 Rollers ...)"; `07` 2.5 proof and `12`: "sixteen Rollers" |
| C21 | `03` 1 and 3: "Nothing in this system is a train, a line or a stop" | `the-car-barn-and-the-sump.md`: "the BARN Capsule Post stop"; `12` T1: "rides all four hops" |
| C22 | `03` 6: he "climbs out of the inspection plate of the zone they are in 6 s later" | `07` 3: no delay given; `the-night-inspector.md`: "climbs out of the next one along" |
| C23 | `00` bible list: "`REVIEW.md`" | no such file (first review C23, still open) |
| C24 | `01-LORE.md` 2 and `00`: "312 guests" | `01-LORE.md` 8, `the-dead.md`, `the-terminus.md`: "312 guests and crew" (`the-conductor-of-047.md`: crew of four "counted ... among the 312") |
| C25 | `04` 5 step 5: clocks "pull them west (Platform A west, then the Breach and the Parlour)" | `02` 3: the Breach is reached from the Fare Hall (D6); from Platform A West the way west is the Boneyard (D8, D9) |
| C26 | `10` row 47: "The Rave and Beast finales invite it" | a Station Zero emote note that refers to other maps (first review M1, still there) |

Minor typo: `01-LORE.md` 2: "called ZERO To save money" (missing full stop).

---

## 4. Scores

| Chapter | Score | Reason |
|---|---|---|
| 00 Pitch | 7.5 | honest client box, sharper premise; area figure contradicts `02`, stale `REVIEW.md`, Terminus image borrowed |
| 01 Lore | 7 | Kings, Primer and the 58 staff now cohere; §9 still logs the arrival, mural dating contradicts itself, Beach-model Atmospheric, cliché stack untouched |
| 01 Wiki | 7 | brought into line almost everywhere; a few stale words ("stop"), mural dating, hand-written "In the map" restatements |
| 02 World | 7 | honest place count, plan mostly adjoining, new traps with new verbs; D1 gap, cars 5 and 6, register time, area, waiting places uncounted |
| 03 Transport | 6.5 | dial and untrappable lever are good; still a four-node fare ring; invulnerable ride loop |
| 04 PaP quest | 7.5 | clean steps, H3 kept open, safe-room abuse closed; white-limbo Terminus, two stale lines |
| 05 Wonder weapons | 5.5 | flat ratings are the right model and verbs are now ours; Dispatcher re-send kills at any round, refund cancels surge, tables wrong, no burst caps, Inspector trivialised |
| 06 Perks | 6 | Day Trippers and new Sour Grudges are good; Baker's Dozens is a number, Double Takes contradicts itself, Day Trippers enables the Post loop |
| 07 Enemies | 6.5 | new Inspector silhouette and mark rules are strong, 78 plan honest; WW-trivial boss, Roller hide-and-shoot |
| 08 Camos | 7.5 | MERCURY ARC fixed for dark rooms, CARRIER specific |
| 09 Tab and HUD | 7.5 | budget and allocator fixed, honest tiers; small count mismatch |
| 10 Emotes | 5.5 | 21 originals is progress; generic "originals", two song dances, other-map note, stale Lamp Swing and budget line, a film title |
| 11 Audio | 7.5 | Three-Tone now ours, briefs follow `06` and the wiki |
| 12 Build plan | 7 | measurable and tool-first; 27 pickups, 20 tokens, six/seven proofs |
| 13 Risks | 7.5 | balance-at-78 risk added; fine |
| 14 Client capabilities | 8 | clear, honest, owner decisions marked as such |

## 5. Final paragraph

Yes, with conditions: the bible is now creative, largely coherent and mostly its own (the commuter dead, the
board as interface, the clock quest, the stamp-and-send pistol, ALL STAND, the lamp-headed inspector, the
Three-Tone). The layout, quest, Post version 1, HUD and audio waves can be handed to build teams today. The
wonder-weapon and perk packages should not start until chapter 05 and 06 are corrected. The three things I
would still change: (1) close the two any-round loops in `05` (a sent zombie loses its stamp; the Exact Change
refund returns 30 at most once per 1.5 s), cap burst kills, cap wonder-weapon damage to the Night Inspector,
and redo the sums tables; (2) remove the Capsule Post shelter (per-player cooldown, no mark shedding, Day
Trippers at half postage) and the foam safe room; (3) give the Terminus an image of its own instead of the
white limbo station, rename Rollerdrome, Roller Boogie, Return to Sender and Day Trippers, and clear the 26
contradictions of section 3 (above all `01-LORE.md` 9 and the mural dates, since the canon file "wins").
