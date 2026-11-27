# Station Zero: the rebuild (lead decisions, 27 Nov 2026)

The owner rejected the map of 27 Nov (round 19): shops that are coloured boxes, a room with a "PACK-A-PUNCH" sign,
ugly assets, "an assembly of limited assets". This page is the lead's decisions for the rebuild. Evidence:
[INVENTORY](INVENTORY.md) (what the tools can author), [QUALITY-BAR](QUALITY-BAR.md) (25 measured rules; round 19
fails 18), [FILM-LAYER](FILM-LAYER.md) (the Wyler frame is absent from the map), [TERMINUS-AND-GAPS](TERMINUS-AND-GAPS.md).
Frames of round 19 at 73 cameras, both power states: `C:\studio-data\sz\film\base` (sheets in `sheets\`).
Art direction targets (image generator, not the game): `C:\studio-data\sz\film\concept\{poster,arcade,terminus}.png`.

## 1. What went wrong (so that it is not repeated)

- The bible (`docs/station-zero/`) describes 19 zones, each with a reason. The built map is the nine-zone generator map
  plus one Arcade layer. Rounds 1 to 19 added fill lights and procedural dressing to that; none built a place of the bible.
- The Arcade's shops are five copies of one bay (a 232 x 120 hole in a wall, shelves, cardboard boxes: the same carton
  124 times), one text band each. No authored geometry (603 boxes), no trade, no gameplay inside.
- Pack-a-Punch stands behind a shutter in a hangar under a sign that names it; the bible had already erased that room.
- The lit state (95 % of a match) has no bounced light: every power light is a direct-only runtime light, one network
  record each (167 of 695 records; the official client holds 768).

## 2. Decisions

1. **The film is canon, and it must be on the screen.** `01-LORE.md` stays canon. Accepted from FILM-LAYER section 7:
   proposals 1 (painted one-sheet), 2 (Evelyn Marsh has a face and billing), 4 (the second platform is projected at the
   Terminus), 5 (the photo booth is Copy Stop's; the two Arcade wall weapons go into shops), 6 (four reels, the fourth
   missing; the title monster is the 23:47, the Inspector its face), 7 (stock Afterlife Arcade kept), 8 (shop owners and
   their part in the night), 9 (pictogram instead of "PaP"). Held back: 3 (title theme: audio, later) and 10 (the film-set
   seam in the Car Barn).
2. **One Studio document, sections at the bible's coordinates.** Each section is one self-contained module (its own
   file, its own layers) that survives a change of base. The nine generator zones are replaced section by section;
   base gameplay that must move (Pack-a-Punch first) is removed in the generator and re-declared in a section.
3. **Lit-first lighting** (measured 27 Nov, `C:\studio-data\sz\film\allbaked`, `allbaked2`): every lamp is baked with
   bounce (`group: emergency` on this base); the pre-power state is the dark vision at a manual exposure of -5.5 EV (at -3
   the baked pools read as "dim light on", at -5.5 as darkness); records 695 -> 501. Open, later: emergency lamps as a few
   runtime lights so that they stay bright in the dark state, and three or four hero power lights per zone for the
   power-on moment (TERMINUS-AND-GAPS E, option ii).
   Base for all new work: `C:\studio-data\sz\film\base_lit` (the generator emit with every light in the baked group).
   **Revised 28 Nov ([LIGHTING-GAP](LIGHTING-GAP.md), measured on the Arcade's pass 8):** baking every lamp traded
   "runtime, no bounce" for "bounce, no runtime": a baked light gives no highlight and no coloured pool, and the stock
   maps have both. The rule is now: key lights (shop pools, sign lights, hero fixtures) are always-on runtime lights
   whose bounce is baked; fill stays baked. An unnamed runtime light takes a static template slot and no network record,
   so the count stays at 494. The dark state stays an exposure. Reflection probes are neutral today (one flat colour a
   room): a real reflection source is its own package (W4 of LIGHTING-GAP).
4. **Pack-a-Punch moves to the Terminus** (bible zone 19; target frame `concept\terminus.png`): the stock projector
   machine on a validator post in a room of green-bar printer paper, reached from the cab of the 23:47 for a timed visit.
   No sign names the machine. The alcove, the shutter, `sign_pap` and the three-relay quest leave the generator.
5. **The quality bar is QUALITY-BAR part C.** A section is done when its document counts pass the rules that apply and
   three blind reviewers prefer or cannot tell its frames from stock frames of the same kind of place.
6. **Copy** (anything a player reads) is written by Gemini 4 Neon (`aside exec -p antigravity -m gemini-4-neon`), from
   briefs in `C:\studio-data\sz\film\copy`. Until its text is in, a sign carries canon names only.

## 3. Section 4, the Underpass Arcade (the first slice)

Box x -3000..-1200, y 3500..4300, floor 0, ceiling 256; shop units on the north side, y 4300..4600; entry D4 (1000) in
the Fare Hall's west wall, x -1200, y 3804..3996. Target: `concept\arcade.png`. The entrance is at the east end, so the
shops are on the player's right.

| Unit (west to east) | x | Shop | Front | Inside | Hosts |
|---|---|---|---|---|---|
| U1 | -2960..-2640 | **Needle Drop** (Gil Amory): black and hot orange, a record whose tone arm is a clock hand | door left, window right full of sleeves; shutter a quarter down | sleeve wall, bins, cassette carousel, rental tapes, the jukebox glowing at the back: it closes the long view | jukebox (static now), spawn from the back room |
| U2+U3 | -2630..-1980 | **Copy Stop** (Ines Varga): process blue and white, a page and its copy out of register | double front, central doors open, two windows | two copiers with a bar of green-white light under the lids, blueprint machine, uncollected jobs, the photo booth in the east corner | mystery wheel position (blueprint bay), photo booth (static now), spawn from the back room |
| U4 | -1970..-1650 | **Hole Number Nine** (Dolores Kemp): pink and brown, a doughnut drawn as a 9 | serving counter open to the hall, door at the side | racks, urn, stools, a television, the gala's order bagged on the counter | sub-machine gun 1000 on the side wall, spawn from the kitchen |
| U5 | -1640..-1320 | **Heel & Key** (Tomas Brill): oxblood and cream, a key whose bow is a heel print | a stall: counter across the front, shutter half down; not entered | lasts, key carousel, pegboard of tagged shoes, the key machine, the mould of the Dead-Man's Handle | marksman rifle 1500 on the pegboard at the counter |

Rules of the build (numbers are QUALITY-BAR rules):

- Each front is its own design: full-height glazing between piers, a door or a counter, a fascia box 300 x 68 or larger
  with the shop's logo and name as a picture (rule 2), a roll shutter at a different height, a door card. No two units
  share a light row (11) or a dominant hue (12): orange, blue-white with the copier green as accent, pink, tungsten.
- The trade's own goods are at least 45 % of what stands behind the glass (5); cartons, crates and trash never lead (6).
- Hall: one row of square columns in the hall's own tile (cream with an orange band), pitch 288, on the south third;
  the north lane in front of the shops stays clear for a runner. Tile kit of five (24): wall tile, its damaged twin, the
  orange band, a dark tile, the brown and orange floor. A suspended ceiling of panels, the lit ones emissive, half dead.
- South wall: the directory board with the four logos (the landmark of the entrance, rule 25), four advertising light
  boxes, a row of pay phones, the transit notices. West end: the Shelter 7 blast door, closed (zone 5 comes later).
- The floor polisher stands in its polished circle in the middle of the hall (static until script models land).
- Light: at most 70 lights in the hall and 5 a shop (9, 14); median radius 175 or more (10); 65 % of lights on a fixture
  model (13); every light baked. Budget of network records: the round-19 layer's count, not more.
- Gameplay: zone `arcade`, door D4, 10 to 12 spawners (shop back rooms walked out of, two floor drains in the hall), the
  two wall buys and the wheel position above. Double Takes waits for the perk to exist in a section.
- Named static fallbacks for what a layer cannot do yet (INVENTORY 10): the polisher does not turn, the copier light
  does not move, the jukebox and the photo booth are not used. Each is said in the report, none is hidden.

## 4. Work packages (27 Nov)

| Id | What | Where | Closes with |
|---|---|---|---|
| P1 | Studio: `B.material` (our own tiling material: colour, normal, gloss), far-room collision sections of at most 1,024, marker `area`, Pack-a-Punch offsets for any yaw | `C:\studio`, branch `claude/film-p1` | unit tests; a frame of a wall in our own material; a hull trace grid on a far floor |
| B1 | Base without Pack-a-Punch and without the relay quest; the trip module and the prompt override | SDK `station_zero2.py`, `cp_iwz2.gsc`, `modules/terminus.gsc` | unchanged regeneration equal to the base first; then the diff; headless plans |
| A1 | Arcade art: four logos, fascias, directory, light boxes, cards, notices, bunting; Terminus paper set | `C:\studio-data\sz\film\art`, prompts and manifest in `tools-source/iwzmap/station_zero/film/art` | every picture looked at; manifest with sizes in units |
| A2 | Arcade shell: architecture, fronts, columns, ceiling, floor, lights, gameplay | `tools-source/iwzmap/station_zero/film/arcade_shell.py` | `studio check`; QUALITY-BAR counts; frames lit and unlit |
| A3 | Arcade interiors, two workers after A2: the goods of each shop | `film/arcade_shops_*.py` | rule 5 per shop; frames |
| R1 | Stock reference frames (Shaolin Shuffle's shop row and station, the projection room, Spaceland) | Forge client plans | frames in `C:\studio-data\sz\film\stockref` |
| T1 | The Terminus section | `film/terminus.py` | after P1 and B1: the trip in the game, frames against `concept\terminus.png` |

## 5. PAUSED by the owner (27 Nov 2026, about 22:30)

Every worker is stopped; no `studio live` session is recorded for any document of this package; every branch below is
pushed (0 unpushed, clean worktrees). One idle Forge cell on `cp_iwz` is the daemon's own. Nothing was reviewed by the
lead yet: every line below is a worker's claim until its change and its run are read.

| Lot | Branch (repository) | State at the pause | First thing on resume |
|---|---|---|---|
| P1 | `claude/film-p1` 2796954 (iw7-studio, worktree `studio-film-p1`) | `B.material`, far-room collision sections of 1,024, marker `area`: unit tests 818/0 (805 before). No game frame, no trace. Not done: Pack-a-Punch offsets (the code is SDK `blender/blend_core.py:1249-1250`; the patch is in the worker's report) and the SDK one-liner for marker `area`. Found, not fixed: an island room added by a layer gets no navigation on a Studio-emit base (`based._nav_polygons` seeds from the base's starts only): it blocks the Terminus | read the diff; `live start` + two shots on `C:\studio-data\sz\film\p1\doc`; the hull trace plan `p1\p1_far_floor.json`; the in-game A/B on `p1\doc_based` (`IWZ_MAX_SECTION=0` against the fix); then merge |
| B1 | `claude/sz-film-b1` (iw7-creator-sdk, worktree `sdk-film-b1`); note `B1-BASE.md` | generator without the alcove, shutter, sign, relays and relay quest; lit-first switch; `modules/terminus.gsc` with its unit test; prompt override with placeholder strings. Built once (`live start b1\doc`, 164 s); **no plan ran in the game** | `cd C:\studio-data\sz\film\b1\plans && python -B C:\forge\forge.py batch batch_b1.json` (rebuild with `live start b1\doc` if the usermap was swept); read the regeneration equality table and the diff in `B1-BASE.md` |
| A1 | `claude/sz-film-art` (worktree `sdk-film-art`): prompts, PIL scripts, `manifest.json` (65 entries) | 32 Arcade pictures and 17 Terminus pictures in `C:\studio-data\sz\film\art`; the worker was stopped before its final report; no contact sheet seen by the lead | look at every picture (logos first), reject what is not one hand per brand; the manifest says what was left out |
| A2 | `claude/sz-film-shell` 6183c42 (worktree `sdk-film-shell`); note `A2-ARCADE-SHELL.md` | the whole shell is written (architecture, four fronts, 34 baked lights, 23 picture slots on A1's real files); **never run in the game, no frame**; `studio check` still answers `ok: false` (cause not read), reach 61/61, records 494 of 501 | `python -m studio check C:\studio-data\sz\film\arcade\shell\doc`, read why it is not ok, widen the two `WALKABLE_OFF_NAV` passages, then the first live frames against `concept\arcade.png` |

Copy: Gemini 4 Neon is refused for this account through the Aside CLI (`antigravity/gemini-4-neon`: "not available");
the Arcade's sign copy (`C:\studio-data\sz\film\copy\arcade_copy.json`) is Gemini 4 Hydrogen's, canon-checked, to be
rewritten by Neon when a route exists. Not started: A3 (interiors), R1 (stock reference frames), T1 (the Terminus
section), the blind review.

Then, in the bible's order and one slice at a time: Fare Hall (the board), Escalator Hall, Platform A and the six-car
train, Converter Hall (rectifiers), Lodestar Exchange, Signal Cabin, the Cordon, and the rest of `02-WORLD.md`.
