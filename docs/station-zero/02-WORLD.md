# 02 · THE WORLD OF STATION ZERO

One city block cut open from the street down to 1893. Eighteen playable zones in five districts, plus the
Terminus. Not a chain of stations: there is one platform, one train that never moves, and around them a
plaza, a shopping underpass, a police post, a fallout shelter, a depot, a power hall, a computer exchange, a
storm sump, a painters' siding and a buried Victorian salon with its machine. Counted honestly: **thirteen
distinct places** (the platform is one place in two spawn zones; the Escalator Hall, the Breach, the Staff
Stair and the Signal Cabin are passages or a booth, each with one thing to see or do), in eighteen spawn zones.

Units: 1 unit = 1 inch; x east, y north, z up; a player is 72 tall. All boxes are plan boxes of the walkable
room. The generator builds axis-aligned rooms and **no zone may lie above another** (the navigation grid holds
one height per 32-unit cell). The "layers" of the lore are therefore built as terraces side by side at
different heights, joined by stairs and ramps. This is a tool limit that the layout obeys everywhere.

## 1. Scale targets

Measured facts used (sources: `docs/CREATION-CORE.md`, `research/C-current-map.md`, `research/E-shipped-map-numbers.md`):

| | Station Zero today | Shipped map (Spaceland) | **Target, first complete version** | **Stretch (needs culling, package N5)** |
|---|---|---|---|---|
| Zones | 9 | 13 + its Pack-a-Punch room | **18 + the Terminus** | same |
| Area | 6,808 m2 of walkable navigation cells | 27,806 m2 as the footprint of its 13 spawn volumes (its walkable floor is not decoded; it is smaller) | **about 19,500 m2 of gross plan area** (room boxes, including walls' share, the pit under the train and the Terminus); the walkable figure is printed by the generator (TF2) and is expected near 15,000 m2, a little over twice today's | same |
| World surfaces | 264 | 10,760 | **3,500** | 8,000 |
| Props (static models) | 170 static + 229 entities | 17,010 | **6,000 compiled static**, under 150 entities | 14,000 |
| Lights | 137 records | 1,039 | **520** | 900 |
| Reflection probes | template's | 160 | 60 (one to four per zone) | 120 |
| Spawners | 56 | 197 | **186** (4 to 14 per zone; the sum of section 4) | same |
| Doors | 5 (4,750 points) | 14 debris doors (18,000 points) and 3 team doors | **17** (19,750 points) | same |
| Perk machines | 4 | 10, limit 5 per player | **10**, limit 6 | same |
| Wall-weapon spots | 5 | 20 (10 different guns, 500 to 1,500) | **21** (500 to 2,000) | same |
| Mystery wheel positions | 3 | 9 (950 a spin) | **7** | same |
| Traps | 1 | 5 kinds at 750 | **4** at 750 | same |

Why the first target is about a third to a half of the shipped map and not equal to it: a generated map has
no visibility culling, so every surface and prop is drawn every frame from everywhere
(`research/A-tools-readiness.md` section a). The shipped map hides most of itself at any moment. Matching its
totals without culling would spend the frame budget that the 78 zombies need. The stretch column is unlocked
only by a measured culling result. What must match the shipped map from the first version is **density where
the player stands**: props, lights and surfaces per room of the same size (section 1.1), because that is what
reviewers and players see.

Rule for every zone: props are **compiled static models** (drawn with no entity cost). Two facts limit this
today and are tool work before any dressing (`12-BUILD-PLAN.md`, TF10 and TF8):

- A model with no static twin in the template map stays an entity, and earlier attempts to compile such models
  as static crashed (`research/C` 2.2, `research/D` 5 and 6). Kit models from the other shipped maps and every
  object we author are in that class. Until TF10 proves a donor-free static model in the game, the prop budget
  counts those models as **entities**, and TF7's kit lists mark each model "has a template donor" or not.
- Entities are a hard pool (2,048 in the engine; the project's working ceiling is 1,800; an earlier overlay
  dropped the game at about 240 visible entities above a shipped map's own). Nobody kept a ledger. **TF8 keeps
  one**, in absolute counts, in the map source: every package adds its worst case before it builds (moving
  dressing, quest objects, board plates, capsules, weapon objects such as tokens and stakes, crowd bodies at
  their measured entity cost, specials, emote rigs). The zombie cap of `07-ENEMIES.md` is derived from what the
  ledger leaves, not fixed in advance.

The template map also lends finite pools that the generator borrows: trigger shapes (about 54 usable), door
blocker brush models, switchable light slots, probes. TF2's first output is the count of each pool against
this chapter's needs; where a pool is short, the fallback is named there (doors on a clip box and a moved
model, as the old shutter did; trap and slow-down areas as script distance tests instead of trigger volumes).

### 1.1 The shipped map's measured room numbers

From `research/E-shipped-map-numbers.md` (queries on the scene database `cp_zmb.sqlite`; each number has its
query there):

| Per zone of the shipped map (13 zones) | Minimum | Median | Maximum |
|---|---|---|---|
| Spawn-volume footprint | 630 m2 | 2,791 m2 | 7,215 m2 |
| Props | 399 | 962 | 2,189 |
| Lights | 26 | 75 | 108 |
| Props per 100 m2 of footprint | 13.9 | **31.8** | 66.3 |

Whole shipped map: 916 distinct models; lights are 893 spot, 142 omni, 3 directional; 3.7 lights and 38.7
surfaces per 100 m2 of footprint.

**The density rule for Station Zero.** First version: 6,000 props over 19,500 m2 = **30.8 props per 100 m2**,
close to the shipped map's median. Full dressing (8,870 props): 45 per 100 m2, between its median and its maximum.
No zone ships under 20 per 100 m2 (the shipped minimum is 13.9; the old Station Zero had 5.9). Lights: 2.75
per 100 m2 in the first version and 3.2 at full dressing, against 3.7; the gap is deliberate, because this
map is meant to be darker than a theme park and its lights are all motivated (section 8). Distinct models:
at least 350 (the old map used 41), so that no model is seen more than about 25 times in a zone.
Areas here and in the shipped figures are footprints, so the comparison is like with like.

Our zones are smaller than the shipped ones on purpose (median about 800 m2 against 2,791 m2 of footprint):
eighteen distinct places instead of thirteen large ones, because the owner's complaint about the old map was
sameness, and because small zones keep the spawner-to-player distance short for 78 zombies.

## 2. Plan

```
                                   N
        y 5800  +-------------------------------------------+
                |        THE CORDON  z+192 (sunken plaza)   |
        y 4600  +--------+----------+---------+-------------+
   +--------+---+ UNDERPASS ARCADE  | FARE    +-----------+
   |SHELTER |   shops along north   | HALL    | TRANSIT   +---staff stair---+
   |  7     |        z 0            | z 0     | POLICE z0 |   z0 -> -320    |   (the Police Post's north wall is the Cordon's south wall)
   | z -96  +----+------------------+----+----+-----+-----+-----+-----------+----+
   +--------+    | THE BREACH (ramp)|ESCAL.|                    | LODESTAR       |
 +---------+-----+--+ z -384 -> 0   | HALL |                    | EXCHANGE z-320 |
 | BELLOWS | PARLOUR|               |0->-320                    +----------------+
 | VAULT   | z -384 +---+-----------+------+-------------------++ CONVERTER HALL |
 | z -384  |        |   PLATFORM A WEST    |  PLATFORM A EAST  ||    z -320      |
 +---------+--+-----+   z -320 (pit -384)  |  the 23:47        |SIGNAL+----------+
              |BONE- |   zero stud          |  cars 1 to 4      |CABIN |          |
              |YARD  +----------------------+-------------------+z-160 | CAR BARN |
              |z -384   (track continues west)   east tunnel mouth: cars 5, 6 ->  | z -320   |
              +------+                                           +-----+ pits -384|
                                                                       +----+-----+
                                                                            |THE SUMP|
                                                                            | z -448 |
      (far away, reached only by the 23:47:  THE TERMINUS)                  +--------+
```

## 3. Zone graph, doors and walking times

Door prices follow the shipped map's ladder (cheap near spawn, dearer with depth); 17 purchases, 19,750 points
to open everything.

| # | From | To | Kind | Price |
|---|---|---|---|---|
| D1 | Cordon | Fare Hall | the entrance stair under the "STATION 0" canopy (debris); the flight, 384 long for its 192 of fall, lies inside the Cordon's box | 750 |
| D2 | Cordon | Transit Police Post | Lodestar's hoist stair cut through the pavement, landing inside the post (the flight lies inside the Cordon's box) | 750 |
| D3 | Fare Hall | Escalator Hall | the fare gates (a roll shutter behind the turnstiles) | 1000 |
| D4 | Fare Hall | Underpass Arcade | concertina gate | 1000 |
| D5 | Fare Hall | Transit Police Post | the post's public counter door | 1000 |
| D6 | Fare Hall | the Breach | Lodestar hoarding, "AUTHORISED PERSONNEL" | 1250 |
| D7 | Underpass Arcade | Shelter 7 | the blast door, half open, to be wound | 1250 |
| D8 | Platform A West (pit level) | the Boneyard | the Cordon crew's welded track gate | 1250 |
| D9 | the Boneyard | the Parlour | the Zero Kings' hole in the brickwork | 1250 |
| D10 | the Parlour | the Bellows Vault | Vayle's bronze doors | 1500 |
| D11 | Platform A East | Signal Cabin | the cabin's steel stair gate | 1000 |
| D12 | Signal Cabin | Converter Hall | gantry door | 1250 |
| D13 | Platform A East (tunnel cess, beside cars 5 and 6) | Car Barn | the depot road's roller door | 1250 |
| D14 | Car Barn | Converter Hall | cable-way door | 1000 |
| D15 | Car Barn | the Sump | the pit grate (opens the catwalk door as well) | 1500 |
| D16 | Converter Hall | Lodestar Exchange | Lodestar's keypad door, jammed | 1250 |
| D17 | Lodestar Exchange | Staff Stair and Transit Police Post | the staff stair's cage door | 1500 |

Free links: Escalator Hall to Platform A West (its foot lands on the west half); Platform A West to East (one
platform, two spawn zones); the Breach to the Parlour (the ramp's foot). Every door joins two boxes that share
an edge in plan; the generator (TF2) refuses a door between boxes that do not.

**Loops** (a map is trained in loops, so every district is on at least one):

1. **Upper west loop**: Fare Hall, the Breach, the Parlour, the Boneyard, Platform A West, Escalator Hall, Fare Hall.
2. **East works loop**: Platform A East, Signal Cabin, Converter Hall, Car Barn, the tunnel cess, Platform A East.
3. **Great east loop**: Fare Hall, Police Post, Staff Stair, Exchange, Converter Hall, Signal Cabin, Platform A East, Escalator Hall, Fare Hall.
4. **Street loop**: Cordon, Fare Hall, Police Post, Cordon.
5. Pockets (one way in or two doors on the same neighbour; high reward): Shelter 7, the Bellows Vault, the Sump.

**Shortest way to power**: D1, D3, D11, D12 = 4000 points.

**Walking times** at an assumed 190 units per second (an assumption: the game sets run speed by animation and
the measuring helper could not read it; TF2's route table and one timed walk in W1a replace it), door to door,
from the plan: Cordon to Converter Hall 38 s; Cordon to the Bellows Vault 47 s; Bellows Vault to the Sump 62 s (the
longest walk; one Capsule Post hop on DRAW); Fare Hall to Platform A 9 s; Car Barn to Exchange 14 s. These are
plan estimates; `iwz_emitcheck.py route` gives the real lengths once the source exists and this table is
replaced by its output.

## 4. The zones

Each entry: plan box, height; purpose; look and landmarks; gameplay role; contents; spawn sources; budget.
Budgets are props (compiled static) / lights / spawners. Perk details are in `06-PERKS.md`.
Wall weapons are given as class and price tier (the builder picks the stock weapon of that class from the
shipped map's wall-buy list; the present map already uses a revolver at 500, a sub-machine gun at 1250, a
rifle at 1500, a shotgun at 750 and a carbine at 500).

### Street

**1. THE CORDON** (spawn) · x -1400..2200, y 4600..5800 (3600 x 1200) · floor +192, canopy at +620
- *Purpose*: where the film starts. Halcyon Plaza is a sunken plaza; the city walled it in.
- *Look*: night, rain on a torn quarantine canopy, sodium floodlights on stands, concrete barrier slabs with
  stencilled "CORDON · HRT", the station's entrance canopy "STATION 0" glowing, the Channel 9 van with its
  mast up and its door open, two Lodestar decontamination tents, a trailer generator, a stopped street clock
  (23:47), the film's poster on a hoarding. Flowers and candles at the barrier.
- *Landmarks*: the lit entrance; the news van; the tent with the PLAZA Capsule Post hoist.
- *Role*: safe-ish opening rounds, long sightlines, two exits. Later the Cordon is where a team resets by Capsule Post.
- *Contents*: Up 'N Atoms (on its own generator struct, powered at match start: the stock game powers areas separately; the main switch powers everything else); wall weapons: pistol-class 500, carbine 500; the
  **Decon Foam** trap (the second tent's corridor fills with foam: 750, 15 s; zombies inside wade at a fifth of
  their speed and attack at half their rate; players are not slowed; 45 s cooldown); Capsule Post hatch PLAZA; Strand tape 1 (in the van); clock (not a quest clock).
- *Spawns*: 12: from under the barrier slabs (floor), from the storm grating (floor), out of the tents'
  dark ends (walk-in), from the canopy's service hatch (ceiling).
- *Budget*: 520 / 40 / 12.

### Concourse (z 0)

**2. FARE HALL** · x -1200..1000, y 3200..4600 (2200 x 1400; its north wall is the Cordon's south wall, where door D1 stands) · ceiling 320
- *Purpose*: the station's public face and ZERO's face: the split-flap board.
- *Look*: white and charcoal tile, a checkerboard marble floor, the inauguration frozen: bunting, a ribbon
  across the fare gates, a banquet table with fallen chairs, a brass band's music stands. Token booths with
  rounded glass. The board, six metres wide, lit, flapping.
- *Landmarks*: the board; the ribbon; the Announcer's Booth window high on the east wall with "ON AIR" lit
  (locked; hook H4); the Lost Property window.
- *Role*: the hub. Wide, three columns, good for a first training circle; five exits make it leaky later.
- *Contents*: mystery wheel (the match's first position); wall weapons: shotgun 750, sub-machine gun 1250;
  **Lost Property** window (buys back the weapon a player last swapped away, 1000 points, once per round); quest clock 1; the board (objectives in the world); pay phone;
  token booth with the Zero token on display (hook H10); Vayle page 1 framed as "station history".
- *Spawns*: 14: floor (broken tile by the booths), wall vents, two ceiling hatches, and the dark behind the
  token booths (walk-in).
- *Budget*: 640 / 46 / 14. Kept from the old map: the room, the turnstile kit, the board art, the signs.

**3. ESCALATOR HALL** · x -800..-200, y 2400..3200 (600 x 800) · floor 0 falling to -320
- *Purpose*: the way down; the first view of the platform and the train.
- *Look*: three lanes: two dead escalators with ribbed steel steps and a stair between; illuminated
  advertising boxes down both walls (the film's fake products: the perk candies, Orbit Rink, Lodestar
  "The Future Runs Itself"); a tiled barrel soffit drawn as a stepped ceiling.
- *Role*: the map's first chokepoint and a shooting gallery downward from the Fare Hall landing. Half-way
  down, a locked side stair with a lit sign climbs to the **Announcer's Booth**: through its wired glass the
  booth's back is visible, a chair, a cardigan on it, a red lamp (hook H4).
- *Contents*: wall weapon: light machine gun 2000 at the foot (a reward for holding the bottom).
- *Spawns*: 8: wall vents behind advertising boxes, two floor grates at the foot.
- *Budget*: 180 / 18 / 8. Built with the stock stair construction (section 6).

**4. UNDERPASS ARCADE** · x -3000..-1200, y 3500..4300 (1800 x 800) plus five shop bays on the north side, each 320 x 300 (y 4300..4600, x from -2960 to -1360 in steps of 330), so that no bay reaches under the Cordon · ceiling 256
- *Purpose*: the 1978 shopping underpass: where commuters spent money. The map's most "1980s" place.
- *Look*: brown and orange floor tiles, a low ceiling of lit panels (half dead), five shop fronts with their
  shutters half up: **Needle Drop** (records), **Copy Stop** (a copy and print shop: photocopiers still
  flashing under their lids, a blueprint machine, a passport-photo corner), **Hole Number Nine** (doughnuts and coffee), **Heel & Key** (shoe repair and keys), and the photo
  booth corner. Neon signs, hand-written sale cards, a floor polisher left running in a circle.
- *Landmarks*: Copy Stop's flashing copiers; the photo booth; the floor polisher.
- *Role*: a long straight for runners with five pockets to duck into; pockets are dead ends.
- *Contents*: **Double Takes** (new perk, at the photo booth); mystery wheel position (inside Copy Stop);
  wall weapons: sub-machine gun 1000, marksman rifle 1500; jukebox in Needle Drop (100 points: changes the
  zone's music; the servers' playlist feature can feed it); photo booth secret (500); Top to Bottom
  hint (a Zero Kings tag pointing to the Boneyard); Strand tape 2 (in Hole Number Nine).
- *Spawns*: 12: shop back rooms (walk-in), ceiling panels, floor drains.
- *Budget*: 760 / 52 / 12.

**5. SHELTER 7** · x -3800..-3000, y 3700..4700 (800 x 1000) · floor -96 (a ramp down from the blast door)
- *Purpose*: the 1961 civil-defence shelter the authority forgot. The Lodestar cleaners used it as a canteen.
- *Look*: painted concrete, two rows of steel bunks, water drums, cracker tins stacked to the ceiling, a
  hand-cranked ventilator, a wall of yellowing instruction posters in our own design, a half-eaten meal.
- *Role*: a pocket: one door, the best loot per square metre, the worst place to be caught.
- *Contents*: mystery wheel position; wall weapon: heavy shotgun 1500; Live Rail part (cable drum, one of
  its three places); a supply locker that gives one free lethal refill per player per round; Vayle page 2
  (he is quoted on a 1961 poster: the civil-defence planners had found his tunnel too).
- *Spawns*: 10: ventilation shafts (ceiling), behind bunks (floor), the escape hatch (walk-in).
- *Budget*: 420 / 20 / 10.

**6. TRANSIT POLICE POST** · x 1000..2200, y 3600..4600 (1200 x 1000) · ceiling 256
- *Purpose*: the Transit Cop's own post. He signed the report here.
- *Look*: a public counter with a glass screen, a duty desk with the report still in the typewriter, a
  holding cell with its door open and scratch marks inside, an armoury cage, an evidence cage, lockers, a
  wall map of the network with one station blacked out with marker.
- *Role*: a fortress with three ways in (street, hall, staff stair). Short sightlines.
- *Contents*: **Bang Bangs**; wall weapons: rifle 1500 and shotgun 1000 (in the armoury cage); Live Rail
  part (hot-stick, one of its three places, evidence cage); Strand tape 3 (evidence tag);
  pay phone; the typed report (lore).
- *Spawns*: 10: the cell's back wall (wall), ceiling tiles, the locker room's dark end (walk-in).
- *Budget*: 480 / 26 / 10.

**7. STAFF STAIR AND DOCK** · x 2200..3000, y 3700..4000 (800 x 300) · 0 falling east to -320
- *Purpose*: the staff-only link between the public station and Lodestar's works; a spawn zone of its own (the 18th).
- *Look*: bare painted brick, a caged lamp every four metres, clocking-in machine and card rack (the 58
  night-staff cards, none clocked out), Lodestar's "NO HRT STAFF BEYOND THIS POINT" notice bolted over an HRT one.
- *Role*: a connector and a chokepoint.
- *Contents*: the card rack (lore: the roster with an empty OUT column, kept from the old map); at the foot,
  Lodestar's loading dock: eleven crated parts of ZERO's core on a hand truck, addressed and never shipped,
  one crate missing (hook H7); a wall weapon is not sold here on purpose: it is the map's one bare passage.
- *Spawns*: 4. *Budget*: 90 / 8 / 4.

### Platforms (z -320, track pit -384)

**8. PLATFORM A WEST** · x -2400..0, y 1200..2400 (deck 800 deep, pit 400)
- *Purpose*: the open end of the platform and the network's zero point.
- *Look*: the classic station: white tile, yellow edge line, tiled columns, benches, an enamel network map,
  a newspaper kiosk (the papers dated 31 December 1984), the brass **zero stud** in the floor under a
  hanging clock, the stopped clock itself.
- *Role*: the big training ground of the map, with the track pit as a risk lane (the trap) and the Escalator
  Hall as its exit.
- *Contents*: **Racin' Stripes**; wall weapon: rifle 1500; quest clock 2; the **Third Rail** trap (kept from
  the old map: 750, 25 s, kills in the open pit west of the train, hurts players in it, 60 s cooldown); Live
  Rail part (collector shoe, in the open pit just west of car 1, one of its three places); the zero stud (secret);
  fuse box 1 (Live Rail fuse swap); mural 1 (on the pit wall).
- *Spawns*: 14: ballast (floor, in the pit), the west tunnel's dark (walk-in), wall vents, kiosk roof (ceiling).
- *Budget*: 620 / 44 / 14. Rework of the old platform's west half: the eight identical columns become six in
  two different tile schemes with a kiosk and a stair landing breaking the strip.

**9. PLATFORM A EAST: THE 23:47** · x 0..2400, y 1200..2400, and the east tunnel mouth x 2400..3500, y 1216..1584
- *Purpose*: the train. Everything the map is about stands here with its doors open.
- *Look*: run 047, six silver cars, unpainted, lit from inside. Car 1 (the cab) is at the west end of the
  train, mid-platform, a champagne bottle unbroken on its coupler. Each car is 534 units long. Cars 1 to 4 stand at the platform (x 264..2400); cars 5
  and 6 (1,068 units) are inside the east tunnel mouth (1,100 units). All six interiors are walkable end to end; the pit under the cars is therefore not walkable (one height per
  cell: the car floor takes those cells), so the walkable pit, its spawners and the trap are all west of car 1. Car 6 is the **Party
  Car**: streamers, a mirror ball, a sound system, forty pairs of street shoes in a neat row (their owners
  left on skates). A narrow walkway (the cess) runs beside cars 5 and 6 to the depot's roller door.
- *Landmarks*: the lit train; the cab; the Party Car; the east signal (red, later green).
- *Role*: a second, tighter training loop (through the train and back along the platform) and the map's
  best ambush place: zombies step out of car doors. The cess is the most dangerous corridor on the map.
- *Contents*: **Tuff 'Nuff** (beside car 3); mystery wheel position; wall weapon: sub-machine gun 1250;
  the cab (quest step 4; the Pack-a-Punch teleport); the Conductor's walk (step 3); Roller-round main spawn (car 6); a skate-wheel trophy (hidden
  song, 1 of 3); Strand tape 4 (car 2, on a seat).
- *Spawns*: 14: car doors (walk-in, six of them), platform floor, ceiling, the tunnel beyond car 6.
- *Budget*: 700 / 48 / 14. Kept: the car model, track and edge kit, "RUN 047" and "23:47" plates. Reworked:
  three static cars with one walkable become six walkable.

**10. SIGNAL CABIN** · x 2400..3000, y 1700..2400 (600 x 700) · floor -160 (a steel stair up from the platform)
- *Purpose*: where the road was set for the Midnight Service.
- *Look*: a long window looking west down the whole platform; the lever frame (forty levers, colour-banded,
  eight with polished handles); the illuminated track diagram; a stove, a kettle, a train register open at its last entries,
  23:44; Lodestar's grey control desk shoved in beside the old frame, its screen showing one line of text.
- *Role*: the overwatch. The only place to shoot the whole platform from; one stair in, one door out.
- *Contents*: **Deadeye Dewdrops**; wall weapon: marksman rifle 1500; quest step 2 (the levers); Live Rail
  RED fuse (relay cupboard, after the road is set); Live Rail part (hot-stick, one of its places).
- *Spawns*: 6: ceiling vent, the relay cupboard (wall), the stair foot.
- *Budget*: 240 / 16 / 6.

### Works (z -320)

**11. CAR BARN** · x 3500..5300, y 800..2200 (1800 x 1400) · ceiling 448 · two inspection pits at -384
- *Purpose*: the depot where the Zero Line cars were fitted out. The biggest room on the map.
- *Look*: a spare car up on four jacks with its bogies rolled out, two inspection pits with work lamps, an
  overhead crane on rails with a wheel set hanging from it, a wheel lathe, a paint store, the foreman's
  glass office with its clock, a wall of tools on shadow boards, oil.
- *Role*: the second great training room (a loop round the jacked car, pits as obstacles to jump or avoid).
  Favours the Rollers. Far from spawn: the place a team moves to mid-game.
- *Contents*: **Quickies**; mystery wheel position; wall weapons: light machine gun 2000, rifle 1500; the
  **workbench** (Live Rail is built here); Live Rail part (collector shoe, one of its places); quest clock 3
  (the foreman's); Capsule Post hatch BARN; fuse box 2; pay phone; a skate-wheel trophy (2 of 3); Strand tape 5.
- *Spawns*: 14: pits (floor), the roller door's dark (walk-in), roof lights (ceiling), under the jacked car.
- *Budget*: 820 / 54 / 14.

**12. CONVERTER HALL** · x 3000..4200, y 2200..3000 (1200 x 800) · ceiling 352
- *Purpose*: traction power. Power is switched on here.
- *Look*: generator G-2 with its "DO NOT RESTART" tag; behind it, in two wire cages, the **mercury-arc
  rectifiers**: man-sized glass bulbs with many arms, a pool of mercury, and (after power) a violet arc that
  lights the whole hall and flickers on every wall; a marble switchboard with knife switches and brass meters.
- *Role*: the first objective. After power its light makes it the most readable room on the map.
- *Contents*: the power breaker; wall weapon: shotgun 1250; the **Flashover** trap (750: the switchboard
  throws the hall dark and the rectifiers flash: every zombie in the hall is blinded for 8 s, standing with
  its hands over its eyes and taking double damage; 60 s cooldown); Live Rail part (cable drum, one
  of its places); Live Rail GREEN fuse (fuse board, after all four Capsule Post hatches are unsealed); fuse box 3.
- *Spawns*: 10: cable trenches (floor), ventilation louvres (wall), ceiling.
- *Budget*: 460 / 30 (two of them the rectifiers, animated flicker) / 10. Kept: G-2, its art, the breaker.

**13. LODESTAR EXCHANGE** · x 3000..4200, y 3000..4000 (1200 x 1000) · ceiling 288
- *Purpose*: where ZERO lives: a telephone exchange turned into a computer.
- *Look*: six aisles between racks of relays that click in travelling waves; two tape drives turning; green
  screens; in the back room a line printer still printing, the room knee-deep in fan-fold paper (the
  timetable of the dead, and the manifest with the players' names). One rack has an empty bay (hook H7).
- *Role*: a maze of short sightlines: the opposite of the platform. Dangerous for a lone player, strong for
  a team that holds two aisle ends.
- *Contents*: **Baker's Dozens** (new perk); wall weapon: sub-machine gun 1500; Capsule Post hatch EXCHANGE; Live Rail
  part (cable drum, one of its places, printer room); Strand tapes 6 and 7; the printer (secret).
- *Spawns*: 12: under the raised floor (floor), cable risers (wall), ceiling trays.
- *Budget*: 680 / 44 / 12 (racks are a few models repeated with three damage states, which is true to the place).

**14. THE SUMP** · x 3500..4700, y -400..800 (1200 x 1200) · floor -448, ankle-deep water · catwalk ring at -384
- *Purpose*: the pump room that keeps the station dry, and the storm drain the Graffiti King came in by.
- *Look*: black water with a slow current, three big pumps (one running, shaking), a steel catwalk round
  the walls, a storm culvert with a bent grille and a rope still hanging from it, tide marks, things
  floating: party hats, a clipboard, a skate.
- *Role*: a pocket with two entrances from the same neighbour (pit ramp and catwalk door): a small loop on
  two levels that are side by side, not stacked (the catwalk rings the pool). Water slows players slightly
  (10 %) but not on the catwalk.
- *Contents*: mystery wheel position; wall weapon: heavy weapon 2000; Live Rail part (hot-stick, one of its
  places); a skate-wheel trophy (3 of 3); mural 2 (inside the culvert mouth).
- *Spawns*: 10: out of the water (floor), the culvert (walk-in), pump housings (wall).
- *Budget*: 380 / 22 / 10.

### Underneath (z -384)

**15. THE BREACH** · x -2048..-1216, y 3000..3400 (832 x 400) · floor 0 at the east end falling west to -384
- *Purpose*: Lodestar's 1983 excavation: the cut through which the 1980s reached the 1890s.
- *Look*: a raw ramp of scaffold boards and steel plates through layers the players can read on the walls:
  1978 tile, 1931 brick, rubble fill, then Vayle's glazed brick. Work lamps on a cable, core samples in
  trays, Dr. Strand's field desk with her lamp still on.
- *Role*: a connector with a story; a long flight is a strong position looking down.
- *Contents*: wall weapon: carbine 750; Vayle page 3; Strand's desk (lore).
- *Spawns*: 6. *Budget*: 200 / 14 / 6. Rework of the old second stair.

**16. THE PARLOUR** · x -3800..-2064, y 2600..3400 (1736 x 800) · ceiling 448
- *Purpose*: the Atmospheric's booking salon, 1893: where parcels, and for one season people, were weighed, tuned and addressed. The most beautiful room on the map and the Capsule Post's home.
- *Look*: herringbone parquet, green panelled dado, white glazed brick above, a coffered ceiling, gas
  chandeliers (three lit after power: Lodestar wired them), **the fork wall** (144 steel tuning forks in a walnut frame, each stamped with a passenger class and a pitch:
  Vayle had every passenger "tuned" before boarding; one fork rings by itself when a zombie passes), **the
  listening horn** (a brass horn the size of a carriage door facing a ring of velvet seats), a ticket desk with a brass grille, the **dispatch desk** with its four
  hatches, Vayle's portrait with the eyes cut out, his long-case clock, and in the arch of the west wall, on a
  brass cradle, his own capsule: No. 12, the only one with a window on the inside.
- *Role*: a medium room with furniture islands: an intricate training route for a good player, a trap for a
  careless one. Everything in it is breakable-looking and nothing is.
- *Contents*: **Bon Voyages** (new perk); mystery wheel position; the dispatch desk (Capsule Post hatch PARLOUR; the
  Dispatcher's quest); quest clock 4; wall weapon: revolver-class 1000; Vayle pages 4 and 5; capsule No. 12 (secret).
- *Spawns*: 12: under the parquet (floor), the ticket desk's back room (walk-in), chandelier roses (ceiling).
- *Budget*: 720 / 40 / 12. Rework of the old "old station" room, whose wood and brick scheme was the
  best-scored zone of the old map; enlarged and given its reason.

**17. THE BELLOWS VAULT** · x -5000..-3800, y 2400..3600 (1200 x 1200) · ceiling 640
- *Purpose*: Vayle's machine. The Capsule Post's engine and its direction lever.
- *Look*: a two-storey rotary blower in riveted iron with a brass maker's plate, an organ console bolted to
  its side with pipes rising up the walls, a grated intake three metres across, Lodestar's motor and
  switchgear grafted on in yellow. The tallest room on the map; the only one where the player looks up.
- *Role*: a pocket behind the dearest door. Small floor, big danger, three strong rewards.
- *Contents*: the **BLOW / DRAW lever**; the **Bellows** trap (750: the intake draws zombies within 300
  units into the blades for 15 s; players in the same circle are pulled, not killed; 90 s cooldown); the
  Dispatcher's charging place; Vayle page 6; mural 3 (the Zero Kings were here first).
- *Spawns*: 8: the intake (walk-in), pipe chases (wall), the tube mouth beyond capsule No. 12.
- *Budget*: 360 / 24 / 8.

**18. THE BONEYARD** · x -3600..-2416, y 1216..1584 and x -3800..-3000, y 1584..2584 · floor -384
- *Purpose*: the dead-end siding where the Zero Kings lived and painted: HRT's own livery painters, sacked in
  the 1979 cuts, who never left.
- *Look*: the track runs in from Platform A West and ends at a buffer stop. Two wrecked car shells stacked
  aslant, every surface painted: the map's only saturated colour before Top to Bottom. A paint shop in exile: trestles, spray booths made of tarpaulin, drums of HRT green and cream, colour charts
  pinned up, a driver's seat as the foreman's chair, a barrel fire. Murals 4 and 5, six metres
  long, lit by the players' flashlights and one string of stolen lamps.
- *Role*: a bent corridor that opens into a camp: fight in the bend, loot in the camp.
- *Contents*: **Sour Grudges** (new perk); wall weapon: shotgun 1000; the Zero Kings' stash (Top to Bottom's
  CYAN can); Live Rail part (collector shoe, one of its places); murals 4 and 5; Strand tape (none here:
  the Kings have their own voice, on the walls).
- *Spawns*: 10: inside the car shells (walk-in), ballast, a roof fall (ceiling).
- *Budget*: 540 / 28 / 10. Rework of the old service tunnel (the worst-scored zone): same position, new reason.

### Nowhere

**19. THE TERMINUS** · far box, about 1400 x 900 · the station as a timetable knows it: a platform made of green-bar printer paper, printed signs, four benches, a clock, 312 pairs of printed footprints and one more pair per player; see `04-PAP-QUEST.md`. Budget 60 / 12 / 0.

**Totals**: props 8,870 planned against the 6,000 target: the per-zone figures are the *full* dressing; the
first complete version ships each zone at two thirds of its figure (6,000 in all) and the rest is added
zone by zone while the frame rate is re-measured. Lights 586 planned, 520 in the first version. Spawners 186.
The Night Inspector's **inspection plates**: one in every zone except the Staff Stair and the Terminus (17), each
a brass floor plate a metre across, cast "HRT INSPECTION", set where a floor spawner could stand; they are the
zombies' own floor-spawn construction with our dressing, and W1a places them.

## 5. Where things are (summary tables)

| Perk | Zone | | Perk | Zone |
|---|---|---|---|---|
| Up 'N Atoms | Cordon | | Deadeye Dewdrops | Signal Cabin |
| Tuff 'Nuff | Platform A East | | Double Takes (new) | Underpass Arcade |
| Racin' Stripes | Platform A West | | Baker's Dozens (new) | Lodestar Exchange |
| Bang Bangs | Transit Police Post | | Bon Voyages (new) | the Parlour |
| Quickies | Car Barn | | Sour Grudges (new) | the Boneyard |

| Thing | Count | Where |
|---|---|---|
| Mystery wheel positions | 7 | Fare Hall (first), Arcade (Copy Stop), Shelter 7, Platform A East, Car Barn, Sump, Parlour |
| Wall weapons | 21 | every zone except the Staff Stair, Bellows Vault and Terminus; prices 500 to 2000 rising with depth |
| Traps | 4, four different verbs | Decon Foam (Cordon: holds), Third Rail (Platform A West: kills in a lane), Flashover (Converter Hall: blinds), the Bellows (Vault: pulls in) |
| Capsule Post hatches | 4 | Cordon, Exchange, Car Barn, Parlour |
| Fuse boxes | 3 | Platform A West, Car Barn, Converter Hall |
| Quest clocks | 4 | Fare Hall, Platform A West, Car Barn, Parlour (three more clocks exist: the Cordon's and the Exchange's, stopped and not part of this quest, and the Terminus clock, the only one that runs) |
| Pay phones | 3 | Fare Hall (rings once a match: a line assembled from the Voice), Police Post (rings when the Night Inspector arrives: his roster read out), Car Barn (rings only if lifted: Dr. Strand's number, engaged) |
| Strand tapes | 8 | Cordon, Arcade, Police Post, Platform A East, Car Barn, Exchange (2), Terminus |
| Vayle pages | 6 | Fare Hall, Shelter 7, Breach, Parlour (2), Bellows Vault |
| Zero Kings murals | 5 | Platform A West, Sump, Bellows Vault, Boneyard (2) |
| Other activities | 4 | Lost Property (Fare Hall), jukebox and photo booth (Arcade), supply locker (Shelter 7) |

## 6. Vertical variety and sightlines

| Height | Zones |
|---|---|
| +192 | Cordon |
| 0 | Fare Hall, Arcade, Police Post |
| -96 | Shelter 7 |
| -160 | Signal Cabin |
| -320 | Platform A (deck), Car Barn, Converter Hall, Exchange |
| -384 | track pit, Car Barn pits, Parlour, Bellows Vault, Boneyard, Sump catwalk |
| -448 | Sump water |

Seven walking heights where the old map had three. Designed long sightlines: Cordon down the entrance stair
into the Fare Hall; Fare Hall landing down the Escalator Hall to the train; Signal Cabin window along the
whole platform (about 120 m); the Breach from top to Parlour floor; the Bellows Vault upward. Designed short
ones: the Exchange aisles, the train interior, the tunnel cess, the Arcade's shop pockets.

Changes of level use **the stock stair construction everywhere**: a clip sheet over risers of about 8 units,
with the navigation cells' corner heights sloped and lying about 4 units above the surface. The lesson of the
old map, read correctly (`research/D` 5 and 7): its two wells failed because the navigation lay 14 to 36
units *under* the generated smooth collision ramp, so zombies would not take it; its long stairs passed. The
cause was the ramp construction, not the length of the steps. The pit west of the train is reached by two
such flights. Two file checks gate every build: `sz2_navconn.py` on every level change, and a new check (part
of TF2) that compares navigation height with the collision surface along every flight and fails over 6 units.

## 7. Every existing room: keep, rework or erase

| Old room | Verdict | What happens | Reason |
|---|---|---|---|
| ticket_hall | **rework** | becomes the Fare Hall, widened east by 600; the street alcove becomes the real entrance stair to the Cordon | its bones and signage scored best; it lacked a reason and a centrepiece (the board) |
| street alcove (6 rubble steps, visual only) | **erase** | replaced by the walkable entrance stair | a place you can see and not enter is filler |
| stair_a | **rework** | becomes the Escalator Hall, three lanes, widened to 600, in the stock stair construction | zero props, one module |
| platform_a | **rework and split** | Platform A West and East; half of its length is now inside the train or broken by the kiosk and landings | it was half the map as one strip with eight identical columns |
| the two platform wells | **erase** | replaced by two flights in the stock stair construction | zombies could not climb them: the navigation lay under the generated ramp |
| east tunnel mouth (visual only) | **rework** | becomes walkable: cars 5 and 6 and the cess to the Car Barn | same rule: enterable or gone |
| hero train (3 cars, 1 walkable) | **keep and extend** | six cars, all walkable | the best story object of the old map |
| maint_corridor | **erase** | its space becomes the Signal Cabin and the wall between platform and works | a corridor with ribs every 200 units and nothing to do |
| generator_room | **rework** | becomes the Converter Hall; G-2 stays; the rectifiers and switchboard give the room its light and trap | one hero object in an empty hall |
| control_room | **erase and replace** | the Lodestar Exchange stands on its site with a different plan (aisles) | reviewers: "hangar-sized, sparse, tidy"; three identical desk pairs |
| pap_alcove and the three-relay quest | **erase** | Pack-a-Punch moves to the Terminus; the relays are replaced by the clock quest | an alcove behind a shutter is the least interesting way to hide the best machine |
| service_tunnel | **rework** | becomes the Boneyard | worst-scored zone; now the Zero Kings' home with the murals |
| dead west stub, Platform B trench, generator catwalk, faux cage door (all visual only) | **erase** | | filler by the same rule |
| platform_b ("old station") | **rework** | becomes the Parlour, enlarged, ceiling raised | its wood and brick scheme was the best-scored look; it needed to *be* something |
| stair_b | **rework** | becomes the Breach | a second copy of the same stair, now the excavation |
| Third Rail trap | **keep** | | works, tested, fits |
| 66 identical door planks, 18 identical barricades | **erase** | each of the 17 doors gets its own dressing named in section 3 | one plank model 66 times |
| 27 rubble piles and 23 electrical boxes placed to satisfy a density check | **erase** | density comes from what a room is for | the code comment itself calls them "bare-wall fills" |
| signs, posters, story plates, missing-person posters, roster, evacuation diagram | **keep** | re-hung where the new plan needs them; text checked against `01-LORE.md` | best-reviewed assets (6 to 7 of 10) |
| hidden toy bear and its song | **erase** | replaced by the three skate-wheel trophies and our own song | both were another publisher's property |
| lighting scheme (flat, bright, coloured casts) | **erase** | relit per zone from `11-AUDIO-DIRECTION.md`'s companion table in section 8 | the main standing criticism of every review |
| darkness kit, power-on sequence, flashlight, audio bank and emitters, effects placement | **keep** | re-targeted to the new zones | built and partly proven |

## 8. Light, per zone (the fix for "flat and showroom-bright")

Every zone is designed in **two states at once**: before power (emergency only) and after. One key colour,
one accent, and real darkness between pools: no fill light, no unmotivated colour. A light exists only where
a fixture model stands.

| Zone | Before power | After power: key | Accent | Darkest part |
|---|---|---|---|---|
| Cordon | lit from the start | sodium floods, orange-pink, hard shadows through the canopy | cold white from the news van; the entrance sign | behind the tents |
| Fare Hall | the board's own amber glow, 3 red emergency lamps | warm white tubes, one row in three dead | the board; ON AIR red | behind the booths |
| Escalator Hall | advertising boxes dead | half of the advertising boxes lit, in their own colours | train light from below | the foot |
| Arcade | Copy Stop's copier flashes only | lit ceiling panels, half dead, slightly green | each shop's neon | shop back rooms |
| Shelter 7 | one hand lamp | bare bulbs, yellow | none | bunk rows |
| Police Post | desk lamp | cold tubes | the cell's single bulb | locker room |
| Platform A West | emergency red at exits | warm tubes over the deck; the pit unlit | the kiosk; the trap's blue-white arcs | the pit and west tunnel |
| Platform A East | **the train's interior light**, on from the start | the same, plus half the platform tubes | the east signal | the tunnel beside cars 5 and 6 |
| Signal Cabin | diagram lamps | one green-shaded desk lamp; the diagram | lever lamps | under the frame |
| Car Barn | pit lamps | high sodium bays, pools on an oily floor | welding-blue from the lathe (sparks) | under the jacked car |
| Converter Hall | none | **the rectifiers' violet, flickering** | amber meters | behind G-2 |
| Exchange | relay lamps twinkling | cold tubes, low | green screens | printer room |
| Sump | none | two caged lamps reflected in water | daylight-blue from the culvert | under the catwalk |
| Breach | work lamps | the same | Strand's desk lamp | the rubble layer |
| Parlour | none | gas chandeliers, gold | the dispatch desk's brass | the car in the arch |
| Bellows Vault | none | shafts from high gratings | Lodestar yellow beacons | the intake |
| Boneyard | barrel fire | barrel fire and a string of stolen lamps | the murals under torchlight | the bend |
| Terminus | (always lit) | flat office fluorescent on paper, even | the running clock; the Pack-a-Punch, the only colour | none |

### 8.1 Looks that no tool is proven to make (each has a first probe and a fallback)

| Look asked for | Why it is unproven | First probe (in W2 or the zone's dressing package) | Fallback, already acceptable |
|---|---|---|---|
| Water in the Sump (dark, slightly moving, reflecting) | the stock puddle material rendered as opaque squares on the old map; no custom shader | a stock water material from one of the five shipped maps (TF7 finds it), tested on one generated quad | still water as a dark glossy stock floor material with wet decals and drips; the 10 % slow-down is a script distance test either way |
| Rain on the Cordon's canopy | particle clouds never drew on the old map; sprite effects did | sprite rain streaks and splash sprites under the canopy's tears | no falling rain: a wet street (glossy material, puddle decals that pass the alpha test), dripping sprites at the tears, rain as sound only |
| Night sky over the Cordon | the template map supplies sun and sky; an open-topped generated room is untried | the canopy with tears that show the template's sky | a closed canopy: the Cordon becomes a roofed tent city, which the lore supports |
| The paper beyond the Terminus's edge, and the second platform printed on it | large custom textures on a stock technique are proven for signs and posters, not at room size | four 2048 textures tiled on the room's quads, the faint second platform on a backdrop plane | the same at lower resolution with visible tiling, which printer paper forgives |
| Screens that change (Copy Stop's machines, the Exchange's terminals), turning tape drives, relays, the mirror ball's speckle | animated materials are not documented; a moving model is an entity | the same stock scrolling technique K1 looks for, on a screen quad; the speckle as a sprite effect | static screen images, three variants; tape drives still; the relays' "waves" are sound and blinking fixture swaps on a few lamps |
| The rectifiers' flickering violet light | switchable lights are a finite template pool | two switchable lights driven by the darkness kit's flicker | a steady violet key with a flickering sprite glow |

## 9. Conventions the stock zombie mode expects from the map

The checklist with file and line references is section 7 of `research/E-shipped-map-numbers.md`: spawn
volumes with a collision shape, a link name and a target; spawner structs marked "static"; the special
spawner structs (`dog_spawner`, `brute_hide_org`); `player_respawn_loc`; door pairs with the zone they open;
perk, wall-buy, wheel, generator, trap and Pack-a-Punch interaction structs; the data tables. The present
map already satisfies it for 9 zones and its lint (`iwzmap_ents_lint.py`) checks it in seconds; the new map
adds zones, not new kinds of entity, except: the 27 boarded windows of the shipped map have no equivalent
here (the generator has none) and are not required.
