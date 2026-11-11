# STATION ZERO bible: adversarial review (reviewer A)

Scope: every file `00-PITCH.md` to `14-CLIENT-CAPABILITIES.md`, all 40 pages of `wiki/`, and the numbers in
`research/E-shipped-map-numbers.md` (health per wave, kill and hit points, special-round and Brute rules, the
Fate and Fortune card list). `11-AUDIO-DIRECTION.md` was read without regard to its sound-effects list, which is
being appended. No game, build or repository was touched.

Severity: **BLOCKER** = would ship a broken or plainly derivative map; **MAJOR** = a player or the owner will
notice and judge it sloppy, generic or unfair; **MINOR** = an inconsistency or weakness to fix before production.

Reference numbers used throughout (from `research/E`, section 5 and 6): ordinary zombie health w10 1,045,
w25 4,365, w30 7,030, w40 18,234, w50 47,295; zombies per round 4 players w10 78, w25 361, w40 888; solo w10 33,
w25 80, w40 168; kill 60, head kill 100, 10 per hit; from wave 20 every zombie sprints; stock wonder weapons are a
flat 2,000 per hit (2 hits at w24, 10 hits at w40).

---

## 1. Balance (the most serious chapter of problems)

### B1 · BLOCKER · All four wonder weapons are percentage-of-health weapons and never fall off

`05-WONDER-WEAPONS.md`, Common rules: "Damage is written as a share of the target's full health ... Ours scale by
share, and stop one-shotting between rounds 24 and 35". And the summary table: "40 | head shots or go broke |
stuns only | bursts wound | control only ... Each weapon stops being a solution on its own at a different round".

The table is false by the weapons' own numbers. A share-of-health weapon that stops one-shotting keeps two-shotting
at every round, forever:

| Weapon | After its threshold | Applications to kill an ordinary zombie at w40, w60, w100 |
|---|---|---|
| EXACT CHANGE | body "half of full health per token"; head "kills at any round" | 2 body / 1 head, at every round |
| LIVE RAIL AMBER | "35 % of full health and ... stunned 1.5 s on each crossing"; direct hit "kills ... any round" | 3 crossings, or 1 stake |
| DISPATCHER | inhale: canned zombies "count as kills" with no round limit; burst "70 % of full health" | inhale = 1; 2 bursts |
| WILDSTYLE MAGENTA | "takes half its full health and resumes" | 2 tags |
| WILDSTYLE YELLOW | burst "60 % of full health to other zombies" | 2 overlapping bursts |

The stock weapons go from 1 hit (w16) to 10 hits (w40) and keep worsening; these stay at 1 to 3 applications at
round 100. Round 100 plays like round 30. That is the definition of a broken wonder weapon.

Fix: replace "share of full health" with the stock Fate and Fortune clamp pattern already measured in
`research/E` section 6 (`clamp(max health, 700, 1000)`-style): full share up to a round, then a flat cap that
falls behind the health curve. Remove every "kills at any round" clause (Exact Change head, Live Rail pin,
Dispatcher inhale) or cap each at a round (head-shot kill to w35, pin to w40, inhale to w30, then damage).

### B2 · BLOCKER · EXACT CHANGE is a money printer, and the "break-even" arithmetic is wrong

`05`, "At high rounds body shots need two tokens: 60 points to earn a 60-point kill, which is break-even, so
only head shots profit."

The sum forgets the 10 points per hit (`research/E` 6: "Hit points 10 per hit") and penetration ("passes
through 2 zombies, full damage to each"). Per pair of body tokens at w25 or w40 (fare 30 + 40 with surge): one
target pays 60 + 20 = 80; three targets in a line pay 240. A head-shot kill pays 100 + 10 and refunds the fare:
pure profit at any round. In the dense lines that 78 zombies make (the train cars, the Exchange aisles, the
Escalator Hall, the Rollers' conga chains), penetration is the normal case, not the lucky one.

Upgraded KEEP THE CHANGE makes it worse: pierce 4 (5 targets), a kill skips to one more, and "every kill drops a
brass token ... worth 30 points" (cap 20 lying). A body pair through a line of five plus the skip yields up to six
kills x (80 + 30) = about 660 points for about 70 spent, at round 40 or round 100.

Also: at 110 rounds per minute one shot leaves every 0.545 s, so "each further shot within 0.6 s of the last costs
10 more" applies to every sustained shot; the surge is the only brake, and a head-shot refund cancels it.

Fix: the refund only for a kill of a zombie at full health, once per 1.5 s; no hit points for token hits; pierce
targets beyond the first pay half; upgraded drops capped at one per shot and 6 lying; and the B1 cap.

### B3 · MAJOR · WILDSTYLE YELLOW is a chain-reaction nuke at any round, not "useless alone"

`05`, YELLOW: "If it dies in that time, by any cause, it bursts: 160 units, 60 % of full health to other zombies
(kills to round 30), and tags those it does not kill"; "useless alone: something else must do the killing".

(a) "60 % of full health ... kills to round 30" contradicts itself: 60 % of full health never kills a full-health
zombie. Decide which is meant. (b) Either way, the re-tag makes a cascade: in a packed horde every zombie is inside
160 units of several others, so the first death bursts, its neighbours are re-tagged YELLOW at 40 % health left,
the next death in the cluster kills them, and so on. Spray a 78-crowd for two seconds, kill one with the pistol,
the crowd detonates. The upgraded MASTERPIECE adds a colour splash on every death. "Useless alone" is the opposite
of the truth: it needs one bullet. Against the Night Inspector each burst near him takes 5 % of his full health
(`05` table), so a YELLOW cascade around him removes his whole health bar in seconds at any round.

Fix: bursts never re-tag; a zombie can be damaged by at most one YELLOW burst per 3 s; burst damage a flat value
(stock-style clamp); the Inspector takes burst damage at most once per 5 s.

### B4 · MAJOR · The density argument is backwards: 78 zombies make every area weapon stronger

`05`, Common rules: "this map puts up to 78 zombies in the fight where the stock map puts 24, and each weapon
carries its own brake". More bodies per square metre multiply every area effect: Dispatcher burst radius
180 / 240 / 300 (380 upgraded), RED fence chains "to 2 more within 160 units, and those to 1 more each" (up to 5
kills per charge, 60 per fence), MAGENTA's 380-unit cone tagging everything in it after 0.5 s, YELLOW above. The
cap is not a brake; it is an amplifier. None of the round tables tests the 78 case. Fix: test each weapon at w10,
25, 40 with 24 and 78 alive in the plan (as `05` "proofs" 2 promises) and set per-activation kill caps
(e.g. Dispatcher burst kills at most 8; RED chains at most 3 per charge; MAGENTA at most 6 tagged at once).

### B5 · MAJOR · DISPATCHER inhale is a free kill at any round, and the "not overpowered" paragraph undersells it

`05`: inhale "count as kills and pay normal points", no round limit; "Why it is not overpowered. A full cycle
(inhale three, launch) removes three zombies and damages a group". At w25 a full-load burst (r300) "kills to
round 35": a cycle removes three and kills the group, every 3 s, 12 cycles a refill. After w35 the inhale still
kills outright; two bursts kill. Fix: inhale removes only zombies under 50 % health (so it finishes, it does not
open), or inhale to w30 then becomes the air slug; burst kill cap per B4.

### B6 · MAJOR · LIVE RAIL line test can kill a stunned zombie ten times a second

`05`: "an ordinary zombie that comes within 20 units of the line dies, to round 30; after that it takes 35 % of
full health and is stunned 1.5 s on each crossing"; the segment test runs "ten times a second". A zombie stunned
on the line stays within 20 units; nothing says it is hit only once. Read literally that is 3.5 x full health per
second, i.e. an any-round kill that also eats the fence's 24 charges in ticks. Fix: one hit per zombie per fence
per 2 s, and the stunned zombie is pushed off the line.

### B7 · MAJOR · The Roller special round is trivialised by three of the four weapons and by geometry

`05`/`07`: "A Roller crossing an arc is killed" (any round, no charge rule stated); CYAN: "Rollers wipe out and
die"; EXACT CHANGE: "two kill". `07`: "They do not take stairs ... a Roller whose target changes level skates to
a walk-in spawner and re-enters on the new level"; "Narrow places make them crash"; crash = "1.5 s stunned ...
taking double damage"; turning needs "an arc of at least 200 units radius".

Dominant strategy: stand in a narrow room. The Signal Cabin (600 x 700, at -160, its own height, "one stair in",
spawners: "ceiling vent, the relay cupboard (wall), the stair foot", no walk-in), Shelter 7 (bunks, own height),
any train car, any Exchange aisle. Rollers either cannot reach, or crash into walls every pass and die at double
damage. Two CYAN slicks at a doorway finish the rest. The Max Ammo is free. Fix: Rollers dismount at stairs and
narrow rooms (a "skates off" walk state with low health), CYAN and fences trip rather than kill (they die only
to damage), and the round places spawners on every level including the Cabin.

### B8 · MAJOR · The Night Inspector's mark is gameable and griefable

`07`: "the living player with the most unspent points when he arrives; re-chosen when the marked player goes
down, or when another player has 2000 more unspent than the marked one for 5 s"; fine "10 % of their unspent
points (at most 1500)"; drop: "every fine he collected, as a pile of tokens anyone may pick up".

- The servers run a bank and a `.pay` command (`AGENTS.md`). Depositing dodges the mark; `.pay` lets a griefer
  push points onto a new player to make them the target, or ping-pong the mark across the 2000 threshold.
- AFK players: the servers' AFK protection (Aim + Knife or `.afk`) makes a player protected. A rich AFK player
  draws the Inspector to a corner forever, or the Inspector punches a protected body uselessly. Not addressed.
- Zero-points player or a team that spent everything: the fine is 0; the mark has no teeth. Experienced teams
  will simply always spend before round 10, and the "boss that reads the scoreboard" becomes a slow tank.
- Solo: the mark is always you; with 0 points it is a plain fight. Tie-break with equal points: unspecified.
- Fines "anyone may pick up": a teammate steals the marked player's money. A grief vector by design.
- He "walk[s] 110 units per second; he never runs" against a player at about 190: the marked player kites him
  indefinitely; zone changes cost him a 6 s door trip each time. Where the marked player is in the Terminus, a
  Pneumo capsule or the train, behaviour is unspecified. The "staff doors" he uses are placed in no zone of
  `02-WORLD.md`.
- Health "12 times ... multiplied by ... 2.2": w40 four players = 12 x 18,234 x 2.2 = about 481,000 with body hits
  at 25 %. Guns cannot kill him late; %-damage wonder weapons kill him in a fixed number of hits (25 lamp tokens
  of EXACT CHANGE at any round). The fight is impossible without a WW and trivial with one. What happens to an
  unkilled Inspector when the next one is due is not stated.

Fix: mark = highest score earned in the last two rounds (not unspent points), ignoring banked, paid and AFK or
protected players; fines go to the marked player's own pile (only they can pick it up, or it returns on kill);
he gains a short "stride" after 8 s without reaching the mark; staff doors listed per zone; health a flat curve
capped like the Brute (`research/E` 5.7), WW damage to him a flat number, not a share.

### B9 · MAJOR · The Terminus is a free 75-second safe room every 195 seconds

`04`: stay 75 s, cooldown 120 s, "no zombies spawn there", cost free; "Zombies inside car 1 at departure: killed,
no points". Stock Spaceland gives 30 s and kicks the player (`research/E` 4.4). At round 30+ a team in trouble
walks into car 1: every zombie in the car is deleted, then 75 s of health regeneration, reloads, revives and no
mark. What the horde does meanwhile (spawning continues? the cap fills with 78 "waiting" bodies around car 1?)
is not specified, nor is a downed player left on the platform (only "living" players travel; bleed-out is 35 s
< 75 s). Fix: 35 s, cooldown 150 s, the round's spawning pauses but the alive count is held, downed players
travel with the team, zombies in car 1 are ejected not killed.

### B10 · MAJOR · Degenerate combinations not tested anywhere

1. **DISPATCHER + SOUR GRUDGES + Tuff 'Nuff**: the zombie that hit you is at point-blank, inside the inhale cone;
   canning it (a kill at any round) returns the health. Near-immortality at any round, contradicting `06`
   "Round 40: it pays only with a wonder weapon in hand" (which is exactly the case) and "It scales down by
   itself".
2. **EXACT CHANGE head shots + SOUR GRUDGES**: same, with a refund.
3. **LIVE RAIL fence across a Pneumo arrival hatch**: blowback zombies "thrown out ... stunned for 1 s" land in
   the arc: free kills, points.
4. **DOUBLE TAKES decoy inside a Live Rail triangle (FOURTH RAIL) or on a CYAN slick**: zombies within 400 units
   path into a kill zone once a minute.
5. **WILDSTYLE YELLOW + any trap** (trap kills give no points, but they trigger "dies ... by any cause"): the
   trap seeds a cascade (B3) that does pay.
6. **Lost Property buy-back** (`02`: "buys back the weapon a player last swapped away, 1000 points, once per
   round"): swap a wheel wonder weapon at the wheel for the next roll, buy the WW back for 1000: two wonder
   weapons without the extra-slot perk, in contradiction with `05` "One per player slot".

Fix: list these as named test cases in the plans of WW1 and P1; Sour Grudges excludes kills by wonder weapons;
Lost Property excludes wonder weapons.

### B11 · MAJOR · Two new perks are too weak or too dull to pick, one copies this very game

- **LAST LICKS** (`06`): "The final 25 % of every magazine ... deals double damage". This is the Fate and Fortune
  card effect listed in our own research, "last bullets x2" (`research/E` 6, card effects). `06` claims "None of
  the four copies an effect of an existing perk in this game" — true only by the word "perk". It is also a pure
  number, the thing the pitch says the new perks are not ("perks that reward nerve rather than add numbers"), and
  it excludes the only weapons that matter after w25. At 3000 it is the worst value on the map.
- **LUCKY DIPS**: a second, never-wonder offer at the wheel plus 25 % off wall ammo. Its own text: "Round 40:
  nearly dead weight". With six slots and ten machines nobody takes it after round 10. Dull, not "very cool".
- **SOUR GRUDGES** is Bloodborne's "Rally" (regain the health you just lost by striking back within a short
  window) restricted to the attacker. Close enough that players will name it.
- **DOUBLE TAKES** is the strongest idea of the four but in hybrid mode (`07` 2.2) crowd bodies move on a flow
  field "one field per player"; a decoy is not a player, so 54 of 78 bodies ignore it unless the field code adds
  decoys. Not stated.

Fix: replace Last Licks and Lucky Dips with perks built on the map's own systems (e.g. a perk that turns your
next Pneumo hop free and makes you arrive at full speed; a perk that makes your purchases also wind/charge the
nearest quest object; a "season ticket" perk that halves the Inspector's fine and makes his mark skip you once).
Keep Sour Grudges only with a distinct mechanic (e.g. the heal goes to the nearest teammate, not to you).

### B12 · MINOR · LIVE RAIL AMBER is a dead variant once the others are found

AMBER "14 s, 24 charges"; RED "7 s, 12 charges" but up to 5 kills a charge; GREEN "no charge limit". Swapping is
"free" at three fuse boxes. After RED and GREEN are in hand nobody fits AMBER. Fix: give AMBER a job the others
cannot do (e.g. the only fuse whose fence blocks the Inspector's path, or the only one that can be planted on
ceilings).

---

## 2. Originality (names, mechanics, images)

### O1 · MAJOR · FEVER (MAGENTA) is Spaceland's own Dischord / disco-ball trap

`05`: "MAGENTA · FEVER: stops, and dances on the spot for 6 s"; the script note concedes "the shipped map's
scripts make zombies dance in one of its traps". In this very game, Spaceland's wonder weapon Dischord makes
zombies dance, and its disco-ball trap does the same. Outside the game: Ratchet & Clank's Groovitron, Fortnite's
Boogie Bomb. A "totally original" wonder weapon cannot have, as its headline effect, the headline effect of the
shipped map's wonder weapon. Fix: MAGENTA "FEVER" becomes something the Carrier logic owns, e.g. the tagged
zombie "boards": it walks to the nearest waiting place and stands behind the yellow line for 6 s (the map's own
commuter joke), then dies.

### O2 · MAJOR · "WILDSTYLE" is a film title and a film character

"Wild Style" (1983) is the founding graffiti film; "Wyldstyle" is the heroine of The LEGO Movie (2014). The owner
forbade names lifted from films. Fix: an invented tag-name (e.g. "SIGNAL PAINT", "TAGGER'S ORDERS", or the
painter's own crew tag).

### O3 · MAJOR · THE DISPATCHER is Kirby / the Poltergust

Inhale enemies into a container, then fire them as a projectile: Kirby's inhale-and-spit, Luigi's Mansion's
Poltergust (inhale, store, blow out). The brass-and-bellows dressing is ours; the verb is theirs. Fix: change the
verb: the Dispatcher **addresses** zombies (tags a target with a destination label) and the next Pneumo-style
blast **delivers** them, i.e. the shot drags labelled zombies along a tube-line to the impact point, a line
rather than a canister.

### O4 · MAJOR · The Parlour and the Atmospheric are the Beach Pneumatic Transit

`02` Parlour: "gas chandeliers, a dry marble fountain with goldfish bones, a grand piano under a dust sheet";
`wiki/the-atmospheric.md`: one tube, one car, a merchant-backed company, a fare, folded within a few years.
The real Beach Pneumatic Transit (New York, 1870) had exactly this waiting room (grand piano, fountain with a
goldfish tank, chandeliers), one car in one short tube, and folded; it was then reused on film (Ghostbusters II,
1989, the abandoned pneumatic line under the city). "Ambrose Vayle" also tracks its founder (Alfred Ely Beach)
initial for initial. The owner's rule is "inspired by period and genre only". Fix: drop the piano and goldfish
fountain and the single-car merchant line; make the Atmospheric something Beach never was (e.g. a pneumatic
**funeral** railway that carried coffins to a harbour cemetery ship, which also explains the dead) and give the
salon its own signature objects.

### O5 · MAJOR · The Night Inspector is Mr. X with a lamp

`07`: "2.5 m tall ... floor-length ... greatcoat ... peaked cap ... pulled low; no visible eyes"; "walks and never
runs"; follows one target and "goes through the nearest staff door and comes out of one in their zone". This is
Resident Evil 2's Tyrant (Mr. X): giant greatcoat, hat, slow unstoppable walk, follows you room to room through
doors. Fix: break the silhouette and the gait: an inspector who is short and wide, pushing a ticket-machine
trolley; or a figure that is several uniforms walking as one; he should not follow through doors but issue a
"warrant" that makes ordinary zombies converge.

### O6 · MAJOR · The Three-Tone is the NBC chime in pitch content, and a generic PA chime in contour

`11` M2: "G5 E5 C5". G, E, C is the note set of the NBC chimes, a registered sound trademark, and the falling
major triad is the stock airport and department-store PA "ding-ding-ding". It is the round-start sound of the
whole map. Fix: three falling notes that are not a triad (e.g. a falling whole tone then tritone), so the chime is
ours and slightly wrong, which also fits the "Carrier".

### O7 · MAJOR · The Terminus repeats The Shining's ballroom

`04`/`the-terminus.md`: a frozen gala at midnight, champagne tower, band instruments left on chairs, a waltz from
a small speaker, "a guest book ... the last names written in it are of people who have not signed it". The frozen
party where you were always a guest, proven by a record bearing your name, is The Shining's Gold Room and final
photograph. The photo booth's fourth frame ("someone stands behind you") is a stock ghost-photo creepypasta.
Fix: the Terminus is not a party but an **arrival hall that is still being built**: scaffolding, unfinished
tile, Lodestar's mock-up signs, a workforce of mannequins rehearsing the arrival; the proof of the players'
presence is a printed **arrival ticket** issued in their name by a ticket machine, not a guest book.

### O8 · MAJOR · Our own game already did this setting

Infinite Warfare Zombies' Shaolin Shuffle is 1970s New York: subway station, disco, street gangs; Spaceland is a
1980s arcade with a talking machine-head (N.E.I.L.). Station Zero is 1980s, subway, a street gang in back-patch
vests, roller disco, a coin-op arcade (TILT), a talking dispatch machine with a dotted acronym (Z.E.R.O.). Each
element is defensible; together, a player of the base game will say "Shaolin Shuffle plus Spaceland". Add the
genre parent The Warriors (1979: costumed subway gangs in back-patch vests, a roller-skating gang member in the
subway). Fix: cut TILT (the third coin-op arcade in IWZ), make the Zero Kings not a vest gang but squatting
**track painters** (the HRT's own sacked livery crew), rename Z.E.R.O. without dots.

### O9 · MAJOR · Real brands and phrases

- "Mind the gap" (`the-voice-of-the-rapid.md` announcement 4 verbatim "Mind the gap between the train and the
  platform"; emote 2 "Mind the Gap"; `11` V01): London Underground's signature phrase, protected by Transport for
  London as a mark on merchandise. In a US-style city (dollars, "sixty cents a token", call sign WPHX) it is also
  out of place.
- "Channel 9 Eyewitness" / "9 EYEWITNESS" (`01-LORE` 3, heroes' costume): "Eyewitness News" is a long-running real
  US local-news brand, used with channel numbers by real stations. Check the call sign WPHX against real stations
  before printing it.
- "the Midnight Run": a 1988 film title. "Sole Man": the 1965 song and the 1986 film "Soul Man". "Halcyon" is the
  colony of The Outer Worlds. "Commuter of the Dead" (emote 6): Romero's title formula.
- "Pneumo": verify against BioShock's Rapture tube signage before use; if it matches, rename ("the Breath", "the
  Draught").

Fix: rename each; keep W5's lint list (`13-RISKS.md` 8) and add these strings to it.

### O10 · MINOR · Clichés stacked under the good central joke

The commuter-dead joke ("not hungry, late") is genuinely ours and good. Around it: stopped clocks at the moment
of disaster (Great Expectations), the dead who do not know they are dead, the company that filed the scientist's
memo, the tape that ends mid-sentence, the Victorian spiritualist engineer, the bankrupt 1970s-NYC city. Fix: keep
two of these at most; the memo and the mid-sentence tape are the weakest.

---

## 3. Coherence (contradictions between files)

| # | Sev | Side A | Side B | Fix |
|---|---|---|---|---|
| C1 | MAJOR | `05`: "Fare per shot 30 points"; plate "FARE 30" | `wiki/tokens.md`: "fires them at 20 points a shot"; `the-wonder-weapons.md`: "a fare plate on its side reads 'FARE 20'" | one number everywhere (the plate is a model texture) |
| C2 | MAJOR | `01-LORE` 7: Andre is "the Graffiti King", who came "to paint" the train, not a Zero King (`the-four-heroes.md`: "A street painter whose name is on forty walls") | `the-wonder-weapons.md`: WILDSTYLE was "the rig of their best painter, the one the street called the Graffiti King"; `05`: "The Graffiti King's own rig" | two Graffiti Kings. Give the dead painter another tag name |
| C3 | MAJOR | `the-zero-kings.md`: "The Kings painted nothing after December 1984" | `the-wonder-weapons.md`: "The Kings found out ... that the Carrier reads colour ... paint a dead man the right colour"; "a Zero King taught the dead the meaning of colour" | the dead exist only from 31 Dec 1984; when did the Kings experiment? State that Kings were among the dead or move the discovery to the cleanup crews |
| C4 | MAJOR | `01-LORE` 12 H3: "Z.E.R.O. cannot log a failed run. What happens if the run completes?"; `zero.md`: "It has never logged an arrival" | `04` 6: clocks are "telling Z.E.R.O. that the thirteen minutes have passed and 047 has arrived"; the board reads "ARRIVAL 047"; the Terminus visit ends at 00:00:00; `11` 5.1 V26 "arrival"; `the-voice-of-the-rapid.md` announcement 7 "recorded for the opening, never played" | the PaP quest resolves the main-quest hook every match. Make the Terminus visit end at 23:59:59 ("not yet") and drop V26 |
| C5 | MAJOR | `the-conductor-of-047.md`: "The guard rides in the rear of the train, in car 6 ... holds the controller handle that would stop the train if he let go" | same page: the Handle "fits the controller in the cab of car 1 and nothing else"; `run-047.md`: Strand in the cab "with a hand on the controller" | a dead-man's handle held in car 6 for a controller in car 1 is impossible. Put Pask in the cab with Strand, or make the key a "guard's door key" |
| C6 | MAJOR | `10-EMOTES.md` 5.2: the Tier 2 wheel uses "13 elements, under the 24 budget, leaving 11 for the map's own HUD" | `09` 3: map HUD worst case "15 ... plus the servers' own counter and timers (about 5)" | 13 + 15 + 5 = 33 > 24. The wheel must hide H5 to H10 while open, or the budget fails |
| C7 | MINOR | `02` 1: "Spawners ... **204**"; `02` totals "Spawners 204"; `12` W1 "204 spawners" | the zone entries sum to 12+14+8+12+10+10+4+14+14+6+14+10+12+10+6+12+8+10 = **186** | correct one side |
| C8 | MINOR | `00`, `02` 1 and 5: "22 wall-weapon spots" | zone entries list 21 (Cordon 2, Fare 2, Escalator 1, Arcade 2, Shelter 1, Police 2, PlatW 1, PlatE 1, Cabin 1, Barn 2, Converter 1, Exchange 1, Sump 1, Breach 1, Parlour 1, Boneyard 1) | add one or say 21 |
| C9 | MINOR | `02` 5: "Pay phones 6: Fare Hall, Arcade, Shelter 7, Police Post, Platform A West, Car Barn" | `02` zone 13 Exchange contents: "pay phone" | 7 or 6 |
| C10 | MINOR | `02`: Sump "heavy weapon 2000"; Signal Cabin "marksman rifle 1500"; Rectifier Arc "750" | `the-car-barn-and-the-sump.md`: "a heavy weapon at 2500"; `the-signal-cabin.md`: "marksman rifle ... at 1750"; `the-mercury-arc-rectifiers-and-g2.md`: "The Rectifier Arc trap costs 1000 points" | align to `02` |
| C11 | MINOR | `01-LORE` 3: the Terminus is "frozen at midnight"; `00`: "frozen one minute from midnight" | `04`: its clock "runs", "starts at 23:58:45" | one statement |
| C12 | MINOR | `the-clocks.md`: "Six stand stopped ... All seven are the same business" | `10-EMOTES.md` 52 Check Watch: "all seven station clocks read 23:47" (one runs, one reads 11:47) | fix the emote note |
| C13 | MINOR | `the-clocks.md`: "a quarter of an hour that nobody has taken" | everywhere else: thirteen minutes | "thirteen minutes" |
| C14 | MINOR | `03` 3: "the two longest walks ... (Cordon to Parlour, Parlour to Car Barn) each become one hop in one of the two directions, never both at once" | ring on DRAW: PLAZA → PARLOUR → BARN: both walks are one hop each in the same direction (and on BLOW both reverse walks are) | the stated design reason is false; see T1 |
| C15 | MINOR | `06` 1: Tuff 'Nuff "two doors from spawn by either route" | `02` 3: D2 + the free Police chute reaches Platform A East with one door | rewrite or move |
| C16 | MINOR | `03` 1 candidate D: chutes need "sloped slide collision; the generator has straight stairs only" | `02` keeps "the Police chute" as a zone link and the shortest route to power | either the chute is a ramp or it is unbuildable |
| C17 | MINOR | `02` plan: Cordon x -1400..800, y 4600..6200; Police Post x 1000..2200, y 3300..4300 | D2 joins them "Lodestar's hoist ramp" | the boxes do not touch (200 x 300 gap); put the ramp in the plan |
| C18 | MINOR | `02` 9: cars 1 to 4 on x 0..2400 (600 each) | cars 5 and 6 "inside the east tunnel mouth x 2400..3500" = 1100 for two 600-unit cars | lengthen the tunnel box |
| C19 | MINOR | `01-LORE` 9 and `vayle-notebook.md`: pages "each beside something he built" | page 1 framed in the Fare Hall (1931), page 2 on a 1961 poster in Shelter 7 | say "where his work was found" |
| C20 | MINOR | `09` 2: journal "17 / 27 ever found"; `maxis_t` "found bits (27)" | 8 tapes + 6 pages + 5 murals + 3 OTHER = 22 (25 with trophies) | state what the 27 are |
| C21 | MINOR | `06` jingle ideas: Last Licks "a barbershop quartet countdown", Lucky Dips "a music-hall waltz on a fairground organ", Sour Grudges "sung by children" | `11` 3.8: the family is "a kit of electric piano, bells, a plucked synth bass, a drum machine"; Last Licks "ends on a drum-machine fill" | `11` still says "06-PERKS.md was not present"; reconcile |
| C22 | MINOR | `strand-tapes.md` full texts | `11` 5.3 examples (tape 1 "The tube answers", tape 2 doughnuts, tape 8 "We are exactly on time") | `11` says the wiki "was not found on disk"; replace the examples with the wiki text |
| C23 | MINOR | `00` bible list names `REVIEW.md` | no such file | remove or add |
| C24 | MINOR | `the-zero-line.md`: the bypass "ran through" Vayle's 290-metre tube, on an 11 km line; the Atmospheric tube was built for "a single round wooden car" with eleven seats | a six-car metro cannot run in that tube unless it was enlarged, and an enlarged organ pipe is no longer tuned | one sentence: Lodestar ran the bypass *alongside* the tube and the Carrier leaked into it |
| C25 | MINOR | `halcyon-rapid-transit.md`: HRT's central station of four lines, 41 stations | `station-zero.md`: "one platform, one train"; "Platform A" implies a B | say the other platforms are sealed behind the Cordon's plugs |
| C26 | MINOR | US setting (dollars, call sign, "car barn", tokens) | British railway voice: "Mind the gap", "All change", "revenue inspector", "signalwoman", "cess", "chainage" | pick one register; the US one is already in the money and the TV station |
| C27 | MINOR | the dead = 312 + 58 + 140 = 510 (`the-dead.md`) | the Zero Kings (about thirty, `the-zero-kings.md`) are an outfit (M3) but not counted; the night staff on the concourse died with no stated mechanism | one line for each |

---

## 4. Filler, generic, repetition

### F1 · MAJOR · Four of the eighteen zones are corridors, and two are one platform

Staff Stair (155 m2, "Contents: none bought", 4 spawners), the Breach (215 m2, a ramp with one wall weapon),
the Escalator Hall (310 m2, a ramp), the Signal Cabin (271 m2) are passages or a booth; Platform A West and East
are one platform split for the spawn system. Counting honestly the map has about thirteen places. The owner asked
for "massively larger"; 18,900 m2 is 2.8x the old map but below Spaceland's 27,806 m2 footprint, and the first
version ships 6,000 props against Spaceland's 17,010. Fix: merge the Staff Stair into the Exchange (as its
loading dock with something to do: the Lodestar core's crated parts, hook H7), give the Escalator Hall the
Announcer's Booth stair (hook H4 visible from it), and count zones honestly in the pitch ("thirteen places, eighteen
spawn zones").

### F2 · MAJOR · The same verb four times: lane electrocution

Decon Tunnel ("kills zombies inside the corridor"), Third Rail ("kills in the pit"), Rectifier Arc ("an arc jumps
between the two cages across the central aisle"), and LIVE RAIL ("an arc stands between the two"). Three of four
traps and one of four wonder weapons are "zombies die crossing a line". Suction is likewise used four times
(Bellows trap, Pneumo blowback, Dispatcher inhale, upgraded vacuum). Fix: replace the Rectifier Arc with a trap
of another verb (the switchboard throws the hall's lights off and the rectifier flash blinds and freezes zombies
in silhouette for 4 s), and the Decon Tunnel with a foam or spray that carries them (conveyor-like push to the
tent's far end).

### F3 · MAJOR · Zone contents are a checklist

Most zone entries read: one perk or wall weapon + one collectible + one pay phone + one Live Rail part place +
one mystery-wheel position. Pay phones in six (seven) zones and tapes in eight places are distributed for count,
not for reason (tape 5 "in the Car Barn" has no object; the Exchange has two tapes because the count had to be
eight). Fix: cut the pay phones to three, each with a different event, and give every collectible a placement
reason in the text (as the van, the doughnut counter and the evidence tag already have).

### F4 · MINOR · The Pneumo is, in the player's eyes, a loop line with four stops

`03` insists "Nothing in this system is a train", but it has four named stops on a loop, a fare per hop, a
direction, platforms (hatches) with "LINE BLOCKED" plates, and capsules that return to their stop. In a metro map
that is a metro line in miniature, which is what the owner asked not to get. See T1 for the fix.

---

## 5. Fast travel

### T1 · MAJOR · The Pneumo is not overpowered; it is tedious and mostly unused

- Cost: 4 x 750 to open, 250 per hop, 5 s ride + about 2 s boarding + 1.5 s "pressure legs" + 1 s weapon raise.
- The EXCHANGE ↔ BARN hop replaces "Car Barn to Exchange 14 s" (`02` 3) with about 9.5 s for 250 points.
- The PLAZA ↔ EXCHANGE hop replaces a two-door walk through the Police Post and Staff Stair.
- The direction lever sits in a pocket behind the dearest door; a 20 s changeover then a 60 s lock: in public
  play without voice, one player's throw blocks everyone's capsules for 20 s and locks a wrong direction for 60 s.
  It is a grief button and a coordination tax.
- "The ride resets the fight" (fresh spawns at the destination) and blowback brings up to three zombies.
- The real reasons to unseal it are not travel: the Dispatcher quest (three hops) and the GREEN fuse (all four
  stops). It is a quest toll.

Fix: make it a ring of **two-way** hops with no direction lever (the lever instead sets which hatch is an
"express" that skips one stop for double fare), keep 2 capsules per stop, remove pressure legs on an empty
arrival, and make blowback opt-in (a zombie only rides if it is touching the hatch). Better still, break the stop
pattern: the PARLOUR hatch sends a rider to **any** hatch the rider has personally unsealed (the desk is a
dispatch desk), the other three only to PARLOUR. That is a hub-and-spoke made from the lore, not a loop line.

---

## 6. First-time player: obscure steps and missing feedback

| # | Sev | Where | Problem | Fix |
|---|---|---|---|---|
| P1 | MAJOR | `05` Dispatcher step 3 | "stand in the Bellows' intake grille holding the pistol during a direction changeover": nothing in the world says so; the changeover is a team-wide action with a 60 s lock; the same grille is the Bellows trap that pulls players | the drawer note in the desk says it in one line; a lamp on the grille; charging works in any changeover or by holding Use at the organ |
| P2 | MAJOR | `05` WILDSTYLE CYAN | the stash "opens for a player who has looked at three of the five murals"; looking is "standing in front of each for three seconds", logged silently, per player | a spray-can icon and a click when a mural logs; stash lid shows 0/3 |
| P3 | MAJOR | `05` WILDSTYLE YELLOW | "dropped by the first Lodestar Cleaner ... that the player kills with Wildstyle"; Wildstyle does "5 per tick" and kills only through FEVER (to w30); Cleaners appear from w8 | YELLOW drops from any Cleaner tagged with any colour and killed by anything |
| P4 | MINOR | `05` LIVE RAIL GREEN | found "after all four Pneumo stops are unsealed": a weapon variant hidden behind 3000 points of fast-travel tolls with no hint | a fuse board lamp per unsealed stop |
| P5 | MAJOR | `07` the mark | "TICKET, PLEASE" tells the marked player nothing about what to do (spend, run, bait the punch) | the first time, the Voice says one sentence ("Passengers carrying excess fare will be inspected") and the HUD shows the fine he will take |
| P6 | MINOR | `03` BLOW/DRAW | "clockwise" on a map that is not a circle; players cannot predict "next" | each hatch shows the next stop's name, not an arrow |
| P7 | MINOR | `04` step 2 | "Pull the three that are lit": no reading, no puzzle; the lore offers a real one (`the-signal-cabin.md`: the register's 23:44 entry by Prescott) | the register names the three levers Prescott pulled; the diagram only lights the section |
| P8 | MINOR | `06` Lucky Dips | "Use for the left, melee for the right, 5 s": melee at the wheel in a crowd triggers by accident | Use cycles, hold Use takes |

---

## 7. Lore and wiki

- **L1 · MAJOR · Hook H3 resolved every match** (C4).
- **L2 · MAJOR · Graffiti King and the Kings' colour discovery** (C2, C3).
- **L3 · MINOR · Unlisted holes**: who broke the arch "from the inside" in February 1982 (`the-zero-kings.md`) is
  not among H1 to H10; Strand's tape 2 describes an untouched salon although the Kings had been in it for 18
  months (`the-zero-kings.md`: "The Kings were first in the Parlour"); why the 58 staff on the concourse died
  when the event happened to a train. Decide which are hooks and list them; fix the rest.
- **L4 · MINOR · Wiki template fatigue**: 40 pages of about 3 KB, each ending in an "In the map" paragraph that
  restates `02` (and now disagrees with it: C1, C10). `secrets.md`, `station-zero.md` and `index.md` repeat the same
  inventories three times. Fix: generate the "In the map" sections from `02` so they cannot drift, and spend the
  saved words on in-world documents (a staff notice, a Ledger front page, a Lodestar memo with its typos).
- **L5 · MINOR · Tone slips**: "a fare slot was bolted on for the one occasion when the cleanup crews decided to
  charge each other" (`the-pneumo.md`) and the Police chute "so that the night's drunks could be delivered
  directly to the last service" (`transit-police-post-0.md`) are sitcom jokes in a straight-faced film. Emote
  puns (C1 below) also break the straight face.
- What works and must be kept: the commuter-dead joke, Z.E.R.O.'s two log states, the zero stud, the "held
  breath" logo, the board as the interface, Pell's pencil ledger, Strand's tape 6.

---

## 8. Enemies and the cap

- **E1 · MAJOR · Every system must also act on crowd bodies, and none says so.** `07` 2.2: 54 of 78 bodies are
  script models moved on a per-player flow field. Exact Change penetration, Live Rail's segment test, the
  Dispatcher cone, Wildstyle tags, YELLOW bursts, traps, Sour Grudges' "zombie that last hit you", Double Takes'
  decoy, the Bellows pull, Pneumo blowback, Max Ammo's "last kill": each is written for agents. Fix: one
  "target set" function in the actor kit that every weapon, perk and trap calls, and a test row per system with
  a crowd body.
- **E2 · MINOR · Animation lists miss states the rules need**: the Inspector has no clip for the Live Rail stun
  (1 s), for taking a fine (the stamp), for a 180-degree turn, or for an idle-at-door wait; the Rollers have no
  clip for being dragged by the Dispatcher (2 s fall is "trip"? say so) or a level change exit. Fix: map every
  rule in the tables to a clip number.
- **E3 · MINOR · The Conductor** is "three times the health of a zombie of the round" and "walks and never runs":
  at w4 or w5 it is a 1,200 to 1,650 health walker, trivial; fine as a step, but he should do one thing (e.g.
  close the train doors as he passes, cutting the train loop) so the "enemy step" teaches something.

---

## 9. Camos, Tab and HUD, emotes

- **K1 · MAJOR · MERCURY ARC is a mirror on a dark map.** 62 % "metal 1.0, roughness 0.08" reflects whatever the
  reflection probes hold; `02` plans 60 probes for a map designed to be dark. In most zones the gun will read as
  a black or flat grey slab with purple veins. The look also leans on the liquid-chrome (T-1000) and
  "purple electric mastery camo" tropes the page forbids. Fix: raise roughness to 0.2 to 0.3 with a baked
  environment in the albedo (fake reflections of amber station lights), so the static layer passes in darkness;
  test in the Boneyard, not in the Terminus.
- **K2 · MINOR · CARRIER** is good and ours. Risk: amber lines on black at 1.5 mm read as a circuit board at
  first-person distance; the "must not" list cannot prevent it. Fix: thicker lines (3 mm), fewer routes (two to
  three), the roundel larger.
- **H1 · MAJOR · The "full Tab screen" does not reach real players.** `09` 4: on the official client the Tab
  overlay is "not possible"; players get `.menu 5` / `.tab` chat pages. The owner asked for a full Tab screen and
  for "everything playable by real players". This must be stated to the owner as unmet until CF1, not presented
  as delivered.
- **H2 · MINOR**: the Tab's NETWORK shows "zone-level" pips; the STATION page text of the official tier drops the
  map entirely; a player's Pneumo "next stop" is missing from both.
- **M1 · MAJOR · The 40 dances are mostly a stock catalogue.** 28 of 40 (13 to 40) are Mixamo library clips
  ("Hip Hop Dance", "Silly Dancing", "Chicken Dance", "Hokey Pokey", "Moonwalk", "Running Man", "Shopping Cart
  Dance") that appear in a great many games; names are puns pasted on: "Salsa Verde", "Belly Laugh", "Rumba
  Rush", "Hokey Local", "Silly Season", "House Call", "Locksmith" have no tie to the station. "Platform Moonwalk"
  is one performer's signature move; "Chicken Crossing" and "Hokey Local" break the chapter's own rule on
  song-tied choreography (`10` 9.7). "Trolley Dolly" is slang for a flight attendant, not a shopping cart. "Wave"
  (41) and "The Wave" (26) collide in the picker. "Take a Bow ... The Rave and Beast finales invite it"
  references other maps. Fix: at least 20 animated-by-us dances that come from the map (Pneumo pressure legs,
  the lever pull, the split-flap flip, the Night Inspector's punch as a dance, the Rollers' conga, the Bellows
  breath, the token flip); keep library clips only for real social dances, and rename them plainly.
- **M2 · MINOR**: the emote edge test and Conga placement slide real player entities by up to 150 units: a grief
  path to drag a teammate into a fence or off a ramp. Fix: joiners slide only themselves (already true) and
  only onto a slot with no enemy within 200 units.

---

## 10. Deliverability, said plainly

`14` and `07` are honest that the map is "not put in a public rotation until a client without the map can join",
that 54 of the 78 are script bodies on the official client, that no emote can ship before G1 to G4, and that the
Tab screen is Lua-only. That honesty is good. The pitch (`00`) does not carry it: it presents 78 dead commuters,
a full Tab screen and emotes as features. Fix: a three-line box in `00` with what a player on today's official
client gets.

---

## The ten most important findings, in order

1. **B1 · BLOCKER** · all four wonder weapons use share-of-health damage and "kills at any round" clauses, so they
   never fall off; round 100 plays like round 30. Fix: stock-style clamped damage, no any-round kills.
2. **B2 · BLOCKER** · EXACT CHANGE profits at every round (hit points and penetration are left out of the
   "break-even"); head shots are free one-shots forever; KEEP THE CHANGE prints about 660 points per pair. Fix:
   refund and pierce rules, capped drops, B1 cap.
3. **B3/B4 · MAJOR** · YELLOW's re-tag is a horde-wide chain nuke and the density of 78 amplifies every area
   weapon; nothing is tested at 78. Fix: no re-tag, per-activation kill caps, tests at 24 and 78.
4. **O1/O2/O3 · MAJOR** · FEVER is Spaceland's own Dischord, WILDSTYLE is a film title and a LEGO Movie
   character, the Dispatcher is Kirby/Poltergust. Fix: new verbs and names from the map's own systems.
5. **B8 · MAJOR** · the Inspector's mark is dodged by spending or banking, griefed by `.pay`, broken by AFK
   protection, toothless at 0 points, kited at 110 u/s, unkillable by guns late and trivial with %-WWs. Fix: mark
   by recent earnings, exclusions, owner-only fine pile, flat health curve.
6. **O4/O5/O7 · MAJOR** · the Parlour is the real Beach Pneumatic Transit (piano, goldfish fountain, one car);
   the Inspector is Mr. X; the Terminus is The Shining's ballroom and guest book. Fix: redesign the three images.
7. **B7/B9 · MAJOR** · the Roller round is beaten by standing in a narrow room or behind a fence, and the
   Terminus is a free 75 s safe room every 195 s. Fix: Rollers dismount, fences trip not kill; 35 s visits,
   paused spawning, downed players travel.
8. **C4/C2/C5 · MAJOR** · the PaP quest logs the arrival that hook H3 says has never happened; two Graffiti Kings;
   a dead-man's handle held in car 6 for a cab in car 1. Fix as in section 3.
9. **T1 + F4 · MAJOR** · the Pneumo is a four-stop loop line with fares (what the owner did not want), its design
   reason is arithmetically false, and its lever is a grief button. Fix: Parlour-hub dispatch, no direction lever.
10. **B11 + M1 · MAJOR** · two of four new perks are dull numbers (Last Licks copies this game's own "last bullets
    x2" card) and 28 of 40 dances are library clips with pasted puns. Fix: perks built on the map's systems,
    20 dances animated from the map.

## Scores by chapter (out of 10)

| Chapter | Score | Reason |
|---|---|---|
| 00 Pitch | 7 | strong premise and one-line joke; overstates zone count and hides the official-client limits |
| 01 Lore | 6 | the commuter-dead core is original; Beach-transit lift, H3 resolved by the PaP quest, Graffiti King twice |
| 01 Wiki | 6 | complete and readable; template restatement now drifts from `02` (fares, prices), a few sitcom slips |
| 02 World | 6 | careful plan and light design; spawner and wall-weapon counts wrong, four corridor "zones", checklist contents |
| 03 Transport | 4 | not overpowered but tedious, a loop line in all but name, a false design argument, a grief lever |
| 04 PaP quest | 7 | clear, signposted, lore-tied small steps; the Terminus is an over-long safe room and a Shining echo |
| 05 Wonder weapons | 3 | inventive dressing, but share-of-health damage breaks all four late, Exact Change prints money, two verbs borrowed |
| 06 Perks | 4 | Double Takes is good; Last Licks copies this game's card, Lucky Dips dull, Sour Grudges is Bloodborne's Rally |
| 07 Enemies | 5 | honest 78 plan; the Inspector's mark is gameable and his silhouette is Mr. X; Rollers cheesed by geometry |
| 08 Camos | 6 | CARRIER is ours and specific; MERCURY ARC will read black on this dark map and leans on liquid-chrome tropes |
| 09 Tab and HUD | 6 | thorough design; the real players' tier is chat pages; budget clash with the emote wheel |
| 10 Emotes | 4 | wheel and rules thorough; the dance list is mostly a library catalogue with puns, nothing ships before four gates |
| 11 Audio | 7 | disciplined and measurable; Three-Tone is the NBC note set, jingle and tape briefs out of date with `06` and the wiki |
| 12 Build plan | 7 | tools-first, measurable proofs; inherits the wrong counts |
| 13 Risks | 7 | the right three first tests; no risk for balance at 78 or for originality of mechanics |
| 14 Client capabilities | 7 | clear and honest fallbacks; needs to reach the pitch |
