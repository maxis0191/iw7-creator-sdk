# STATION ZERO · THE FILM LAYER

Review of the bible (`sdk-sz20\docs\station-zero\`), 27 Nov 2026. `01-LORE.md` stays canon; changes I ask for are proposals (section 7). Quoted wording is placeholder for the copy writer.

## 0. Verdict

The bible is a strong **setting** and a strong **story inside the film** (the commuter dead, the board, the thirteen minutes, the Terminus). It is **not yet a Willard Wyler film**. The five base films share a cinema frame; here it is five sentences of lore and one poster. Searched over the whole bible: "projector", "theatre", "title card", "Afterlife", "soul key" appear in no design (one sound-prompt tag aside); Wyler has **0 of 254** voice slots (`11` §5.7), no place on the map and one hook (H9). A player is in a haunted station, not in a picture about one. The Arcade complaint has the same root: names without owners, trades or a part in the night.

## 1. The Wyler checklist, scored

Films: S Spaceland, R Rave, Sh Shaolin, A Attack, B Beast. Base-game cells are from memory unless a public guide confirmed them (confirmed: the five settings, the four guests, the Pack-a-Punch routes, three hidden songs); "?" = unsure. The wiki refused automated reading.

| # | What every Wyler film has | Films | Station Zero | Evidence |
|---|---|---|---|---|
| 1 | Cinema frame: Wyler's theatre, an intro, a title | all (theatre walkable in B) | **absent** in the map | `wiki/behind-the-film`; `11` §3.1 M13 has no title |
| 2 | Poster and tagline | all | **thin**: one hoarding; a minimalist design, wrong for 1986 | `01` §1; `02` zone 1 |
| 3 | One decade, one genre, in architecture, music, costume | S 80s park, R 90s camp slasher, Sh 70s kung fu and disco, A 50s creature feature, B sci-fi | setting **strong**, film grammar **thin** | `01` §5; `02` §8 |
| 4 | Four actors recast as period types | all (types per film: ?) | **strong**: role, reason, a zone each | `01` §7 |
| 5 | Wyler present: the sardonic voice over the match | all (memory) | **absent** | `11` §5; H9 |
| 6 | Guest star as themself, with a room and a helper job | S DJ booth, R, Sh dojo, A TV studio; B none ? | **thin**: a hook, no face, "credited nowhere" | H4; `wiki/the-voice-of-the-rapid` |
| 7 | Helper device | S, B the robot; others the guest | **strong**: the split-flap board | `04` §5 |
| 8 | Film wonder weapons with build quests | all | **strong** | `05` |
| 9 | Pack-a-Punch in a projection room behind a portal | S portals; R, Sh film reels on a projector; A the guest opens it; B teleporter | place **strong**, cinema motif **absent** | `04` §4 |
| 10 | Candy perks as product placement, with jingles | all | **strong** | `06`; `11` §3.8 |
| 11 | Other in-film brands with a job | all | **thin**: named, not owned or placed | `02` zone 4 |
| 12 | Afterlife Arcade | all | **absent**: never says what a dead actor sees | `research/E` §4 only |
| 13 | Soul Key piece, Director's Cut | all | **absent**; H10 could carry it | `01` §12 |
| 14 | Boss = the film's title monster | R, Sh, A, B; S ? | **thin**: mini boss strong; title monster undecided (ZERO, Vayle, Dellinger, the train) | `07` §3; H2 H5 H6 |
| 15 | Special-round enemy | all | **strong**: the Rollers | `07` §4 |
| 16 | Hidden song | S, R, A verified; Sh, B ? | **strong**, our own | `11` §3.7 |
| 17 | Traps as attractions, a ride, activities | S most; all some | **strong**: four traps, Capsule Post, Lost Property | `02` §5 |
| 18 | Colour script | all | per zone **strong**, per act **absent** | `02` §8 |
| 19 | Period score | all | **thin** by decision: no main theme | `11` §3 |
| 20 | Humour: camp, puns, Wyler's sarcasm | all | deadpan **strong**; the camp half left with Wyler | `01` §1 |

Score: 8 strong, 7 thin, 5 absent. Every absent line is frame, not story.

**Decade clash.** Spaceland already is the 1980s film. Station Zero must be the other 1980s: night, sodium, grime, synth dread; no pastel neon, no arcade cabinets, no teen types. The wiki's "withdrawn after eleven days" is why it is not among the five: the lost picture.

## 2. Genre grammar for a 1986 transit horror

Currents to learn from, as grammar only (no title, character, line or design is taken):

- **Urban-decay subway thrillers**: sodium and green fluorescent spill, wet black floors, long lenses that flatten a platform.
- **Killer-computer films**: green phosphor, screen text as dialogue, a corporate serif that smiles.
- **Body horror**: effects made on the day: the amber eye is a bulb behind gel, the Inspector a man in a suit.
- **New Year's Eve slashers**: the countdown as structure, paper hats in the worst scene.
- **Roller-disco pictures**: mirror-ball speckle, satin, a camera at wheel height.
- **Shelter paranoia**: yellow and black instruction graphics, a calm narrator.

The film's own:

- **Poster**: a painted one-sheet. Low headlamp flare, four painted figures looking the wrong way, a crowd of cuffed hands holding tickets, airbrushed chrome title, the canon tagline, a credit block.
- **Title card**: the canopy's back-lit box letters coming on one at a time on black, the "0" last; hard cut.
- **Trailer voice**: gravel baritone, present tense, three short beats then the title. On the tape box and the loading screen.
- **Score**: one cold synth main theme (sequenced bass, a detuned lead quoting the Three-Tone) at the title and the end only. Rounds stay silent as `11` decided.
- **Practical effects**: fog and back-light, gels, rear projection in the train windows during the crossing (unproven; fallback a static streak texture), a painted backdrop beyond the Terminus edge.
- **Against "assembled assets"**: five eras, one production designer: the same amber key and prop-house hand everywhere.

## 3. The missing film layer: buildable things

Cost: **T** texture on a proven sign surface; **P** props (entities unless a template donor exists: TF8 ledger); **S** script and server-drawn HUD (text and tinted rectangles, 24 elements a player: `09` §3, §4); **A** audio, later; **U** unproven, with fallback.

| # | Thing | Zone | What the player sees or does | Cost |
|---|---|---|---|---|
| 1 | Cold open | Cordon | black bars open on the spawn view; credit line, title, tagline, "REEL 1"; bars leave at the first Three-Tone. Nine seconds, never blocks | S, 6 HUD elements; A |
| 2 | The one-sheet | Cordon hoarding, lit; one Escalator Hall box; Needle Drop window | the painted poster | T |
| 3 | Four doors | Cordon | each hero's way in: barrier booth with a year of tally marks; clipboard and fuse at a hatch; storm grating lifted, wet prints; the van | P, 4 groups |
| 4 | The camera that is already there | Cordon, Fare Hall, Platform A East, Car Barn, Terminus | the missing cameraman's Channel 9 camera on a tripod, tally lamp red, aimed at the door the players enter by; the van's monitor shows that view, empty | P, one model five times; T |
| 5 | Reel changes | all | a cue dot top right, then a slate: at power, first Terminus arrival, first Inspector. Game over: "REEL 4 MISSING" | S |
| 6 | The seam | Car Barn, behind the jacked car | the one place the set shows (the wiki: shot in a tram shed): plywood flats, braces, a slate, a canvas chair with its back to us | P, about 10 |
| 7 | Objects from 1986 | Needle Drop; Platform A West kiosk; Boneyard | the film's own rental tape on a shelf; its one-star review among papers of 31 Dec 1984; mural 5 (canon) | T |
| 8 | A face for Evelyn Marsh | Escalator Hall (3 boxes), Fare Hall (gala standee), Hole Number Nine (signed photo), the one-sheet | the most-seen face in the station before she is met | T, one painted portrait |
| 9 | Her booth as a star's room | Fare Hall mezzanine | through the glass: mirror bulbs, fresh flowers with a 1984 card, her script binder | P, static |
| 10 | Terminus as projection room | Terminus | section 6 | T, 2; A |
| 11 | The Arcade's identity | Arcade | section 5 | T, about 12; P, about 40 |
| 12 | Brand trail | Fare Hall, the 23:47, Police Post | favour bags of the ten sweets on the banquet table and car seats; Hole Number Nine urns and cups; Channel 9's card on two televisions | T |
| 13 | The stuffed horn | Shelter 7 | its PA horn packed with blankets and tape, one corner loose | P, 1 |
| 14 | Wyler's voice, later | all | a Wyler group in `11` §5. First, one file check: do the stock announcer lines already play on this map? | A; frozen |

**The first 30 seconds.** Spawn faces the canopy: poster left, van right, the camera in the middle, its cable pulled tight down the stair. Item 1 plays over that view. No voice needed.

**Where Wyler is.** Nowhere, and behind the camera (items 1, 4, 5, 6, 7). He is the projectionist changing reels, and things from the film's release leak into a station sealed since 1984. One seam only, or the map becomes a backlot. These items extend the inherited base-game frame (bars, reels, projector); nothing else is borrowed.

**The guest star.** H4 is the right choice: the voice heard all match is the star, as the DJ was. As written it fails. A real guest brings fame, a face, a room and a job; a fictional one needs her fame **manufactured inside the map**: a face everywhere (8), billing "as herself", a room (9), a past (two earlier Wyler roles on tape boxes, titles ours), later a job (the Fare Hall pay phone as her request line).

**Three acts.**

| Reel | Progression | Turn |
|---|---|---|
| 1 Going down | Cordon, Fare Hall, platform, power | the station lights zone by zone |
| 2 The thirteen minutes | clocks, road, Conductor, cab; the Rollers are the party scene | first Terminus arrival: their footprints |
| 3 Inspection | the Night Inspector from round 10 | the clock stops at 23:59:59 |
| 4 Missing | H3, H5, H6 | a frame for the hooks, not an answer: completing the run is shooting the last reel |

## 4. The 19 scenes

| Zone | The scene shot here | The image | Props-only vignette |
|---|---|---|---|
| 1 Cordon | four strangers arrive by four doors; the Reporter loses her cameraman | the lit canopy as the title | camera, tight cable down the stair |
| 2 Fare Hall | Dellinger's gala frozen at 23:47; the machine addresses them in Marsh's voice | the board in a black hall | ribbon uncut, scissors on the floor, full flutes |
| 3 Escalator Hall | the commercial break (Marsh), then the first sight of the train | train light climbing dead escalators | Evelyn's face in three boxes |
| 4 Arcade | the city at 23:30; the Painter reads the first tag | a polisher circling under five dead signs | five "back after midnight" cards, five hands |
| 5 Shelter 7 | false safety: the crews the Cop waved down hid here and still walked out | one long table, every chair pushed back the same way | item 13 |
| 6 Police Post | the Cop's confession | the report in the typewriter | the network map, one station inked out |
| 7 Staff Stair and Dock | the Engineer learns the company was packing | 58 cards with no OUT | Lodestar's notice bolted over the Rapid's |
| 8 Platform A West | "it never left": he measures from zero | the stud under the stopped clock | the 1986 review in the kiosk |
| 9 Platform A East | they board a train of people who stand up: Dellinger, Strand, the Orbit party | the clean lit train | forty pairs of street shoes; the Chairman's last speech card |
| 10 Signal Cabin | the Engineer sets the road for the train he came to stop | the long window, a projection booth over the platform | register at 23:44, two cups |
| 11 Car Barn | the Painter finds the paint store; Wyler's seam | a car on jacks with no wheels | item 6 |
| 12 Converter Hall | end of reel 1: they restart what the last Lodestar crew locked out | violet arcs in glass | the tag, signed by four hands |
| 13 Exchange | ZERO prints their names; the Engineer reads them | a room knee-deep in paper | a chair, paper drifted up its legs |
| 14 Sump | the Painter's way in | a rope from a bent grille over black water | party hats, a skate, his first wet tag |
| 15 Breach | Strand's flashback: they knew | three eras in one wall | desk lamp on, a Hole Number Nine bag |
| 16 Parlour | the origin; the Reporter faces the listener | the eyeless portrait over capsule 12 | eleven seats with 1897 tickets, a new token on the twelfth |
| 17 Bellows Vault | Vayle's low note | looking up the pipes | Lodestar cable ties on organ stops |
| 18 Boneyard | the last King left the Painter a warning and a portrait | mural 5 | a colour chart relabelled with verbs |
| 19 Terminus | the reel that was never shot; Strand's last tape | their own footprints, ink wet | section 6 |

**Weak reasons to exist.** Shelter 7 is the weakest: "the authority forgot it" is not a scene; item 13 gives it one. The Sump stands only on the Painter's entrance, so his mark at spawn (item 3) must point to it. The Staff Stair is honest as the one bare corridor.

## 5. The Underpass Arcade

One device for all: each keeper left a card on the door and went to watch the 23:47 leave. A directory board at gate D4 carries the logos.

| Shop | Owner | Trade in the window | Logo | Its part that night | Hosts, and why |
|---|---|---|---|---|---|
| Needle Drop | Gil Amory (wiki) | sleeve wall, cassette rack, rental tapes, a Roll-In poster | tone arm as a clock hand on a black disc; black and hot orange; fat rounded display | dubbed the party's timed tape for Brandvold's daughter and carried it down to car 6 | jukebox (canon); the hidden-song trail starts at that tape's empty case |
| Copy Stop | Ines Varga (placeholder), a draughtswoman the Rapid let go in 1979; at the gala with the programmes she printed | copiers, blueprint machine, a tray of uncollected jobs | a page and its copy out of register; process blue and white; condensed italic grotesque | printed the invitations; the uncollected forty-copy job is Strand's 1983 memo | mystery wheel in the blueprint bay: the shop of duplicates |
| Photo booth | Copy Stop's | sample strips | same mark, four stacked frames | the gala's souvenir | Double Takes, the strip secret (canon) |
| Hole Number Nine | Dolores Kemp (wiki) | racks, urn, stools, a television on Channel 9 | a doughnut drawn as a 9; pink and brown; brush script | catered the gala; Strand's order waits bagged | tape 2 (canon); sub-machine gun behind the counter; its logo on the Baker's Dozens machine explains that machine in the Exchange |
| Heel & Key | Tomas Brill (placeholder), cobbler and locksmith; on the platform to see his key ride | shoe lasts, key carousel, tagged shoes never collected | a key whose bow is a heel print; oxblood and cream; slab serif | engraved the ceremonial Dead-Man's Handle: its mould is on the bench; one hook of the blank board is tagged "0" | marksman rifle on the pegboard; first sight of the quest key and of H10: the shop of things made to fit |

**The other brands.** Orbit Rink: owner, charter, Party Car, trophies: strong. Lodestar: the antagonist, everywhere: strong. Channel 9: one van and a microphone flag: thin; items 4 and 12 fix it. The candies: machines and advertising boxes but no reason in the plot; the gala's favour bags (item 12) give one.

## 6. Pack-a-Punch without the words

The Terminus is the best room in the bible, but as written it is ZERO's room, not Wyler's. It is half a projection room by accident: fan-fold paper has **sprocket holes**. Use them.

- The paper platform is one frame of a strip; the perforation lines are frame lines.
- The stock machine (a film projector in Spaceland; check the model this map carries) stands on the validator post and throws a rectangle across the track onto the paper: in it, the second platform and its train (H5), the next reel.
- Along the edge, printed leader numerals count 8 to 2 and never reach 1, as the clock never reaches midnight.
- Sound: projector chatter inside the line printer's rhythm.
- Naming: the board says "047 · TERMINUS"; the sign over the machine is "FARE VALIDATION" (canon); overhead signs gain a wordless pictogram (a ticket entering a slot, leaving striped) once the road is set. Two places still say the words: the stock use prompt (override unproven; fallback: it stays) and the Tab screen's "PaP 1" tags (`09` page 3).

## 7. Proposals that touch written text

1. `wiki/behind-the-film`: the poster becomes the painted one-sheet.
2. `wiki/the-voice-of-the-rapid`: Marsh is a known face with two earlier Wyler roles, billed as herself; "credited nowhere" goes.
3. `11` §3.1: M13 gains a 15 s title theme (the wiki's "the score is a chime" then means after the main title); a Wyler voice group is added.
4. `04` §4: H5 is projected, not printed faintly; one beam joins the flat light.
5. `02` zone 4: the photo booth is Copy Stop's, the passport corner goes (duplicate); the two wall weapons get the shops above.
6. `01` §1: add "four reels, the fourth missing", and name one title monster before the poster is painted. I recommend the 23:47 itself, the Inspector as its face.
7. `02`: one line on the Afterlife Arcade. Keep the stock one: it is Wyler's, not the film's.
8. Section 5 adds four small facts (the tape dub, caterer, engraver, the memo copies) and two owners. None contradicts `01`; keepers who died on the concourse stand outside the count of 510, as the M3 dead do.
9. `09` page 3: the "PaP" tags become a pictogram.
10. Item 6, the seam, goes beyond the base frame: as far as I know no base film shows its own set. It is the first item to drop if refused.
