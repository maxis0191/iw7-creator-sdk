# 04 · POWER, THE ROAD TO PACK-A-PUNCH, AND THE TERMINUS

The owner's requirement: a teleport to Pack-a-Punch that must be activated through small steps. The main quest
and the boss fight are left for later; nothing here needs them.

The idea in one line: **every clock in the station stopped at 23:47, thirteen minutes short of the train's
arrival. Give ZERO its midnight and it will open the place where the train went.**

Each step is small, is announced by the station itself (the split-flap board in the Fare Hall and the Tab
screen), and takes the players through a different district, so the quest is also the tour of the map.

## 1. Power

| | |
|---|---|
| What | throw the breaker of standby generator **G-2** in the Converter Hall (stock power interaction, as on the present map) |
| Before power | the station is dark: emergency lamps, the players' flashlights, the lit split-flap board, the amber eyes. The Cordon (street) is fed from Lodestar's trailer and is lit from the start, so the spawn perk and the first wall weapons work without power |
| Feedback | 2.6 s of the diesel turning over, then light banks come on zone by zone outward from the Converter Hall (the existing darkness kit does this), the two mercury-arc rectifiers strike violet, every perk machine plays one bar of its jingle in turn, the Capsule Post gauges twitch, and the Voice of the Rapid says the map's first full sentence |
| Why here | G-2 was locked out at 23:47 with a "DO NOT RESTART" tag. Restarting it is the players' first act of making the station run again, which is what ZERO wants |
| Kept from the old map | the G-2 genset model, its tag art, the breaker interaction, the darkness and power-on sequence |

Power is one switch for the whole map (stock `power_all`), with one exception built the stock way: the Cordon has its own generator struct that is on from the first second (the stock game powers areas separately). Reason: a first-time player must never wonder which
of six generators a machine belongs to; the difficulty of this map is its size, not its wiring.

## 2. The four steps to the Terminus

State is held in level variables and nothing is saved: a new match starts with the clocks at 23:47, the levers
at rest, a new random lever set, no Handle. Late joiners inherit the team's progress.

### Step 1 · Wind the clocks (4 small actions)

| | |
|---|---|
| Where | four of the station's six stopped clocks: **Fare Hall** (above the board), **Platform A west** (over the zero stud), **Car Barn** (the foreman's clock), **the Parlour** (Vayle's long-case clock, stopped at 11:47 since 1897) |
| What the player does | holds Use for 3 s on the clock's winding key |
| Feedback | the hands sweep forward thirteen minutes to 12:00; that clock strikes once (each clock has its own bell); on the board one of four digits of "047 · DUE 00:00 · NOW --:--" flaps into place; the Tab screen ticks "CLOCKS 2/4" |
| Pressure | when a clock strikes, the Three-Tone plays and a burst rises in that zone: 4 zombies solo, 6 with two or three players, 8 with four or more, on top of the round |
| Order | any; each clock stays wound |
| Why | "the missing thirteen minutes". Players learn four districts and where the perks and the Capsule Post hatches are on the way |

### Step 2 · Set the road (1 action in 3 pulls)

| | |
|---|---|
| Where | the Signal Cabin, at the lever frame |
| What the player does | the train register on the cabin's desk lies open at 23:44 with three lever names entered in the signalwoman's hand (the same three the diagram lights). The cabin's track diagram lights three named sections out of eight (chosen at random each match: for example BYPASS UP, CROSSOVER, ZERO). Each of the eight working levers has a brass plate with one of the same names. Pull the three that are lit (Use on each, any order) |
| Feedback | each right lever locks over with a heavy clack and its lamp goes from amber to green. After the third, the signal at the east end of Platform A drops from red to green and the board reads "ROAD SET FOR 047" |
| Wrong lever | all pulled levers spring back, a buzzer sounds, and 4 zombies drop from the cabin's ceiling vent. No other penalty |
| Solo / four players | identical |
| Why | the diagram and the plates teach the player to read the cabin; nothing has to be looked up. The random set is what resets the step between matches |

### Step 3 · The Conductor (1 kill)

| | |
|---|---|
| Where | he steps out of the Party Car (car 6, in the east tunnel mouth) within 20 s of the road being set, comes through the train to the platform at car 4, and walks the platform west toward the cab |
| What the player does | kills **the Conductor of 047**: outfit M2, a hand lamp swinging amber, three times the health of a zombie of the round, walks and never runs, announces himself with a guard's whistle |
| Feedback | he drops the **Dead-Man's Handle** (a brass controller key with a red knob). Picking it up shows a key icon on the HUD of the carrier and on the Tab screen for all |
| If he is not killed | he reaches the cab, finds it locked, and turns back; if the round ends he leaves and returns at the start of the next round. He cannot be lost |
| If the carrier goes down or leaves | the Handle drops where they fell and stays, lit, until picked up |
| Why | the crew of the train still carries its key. One named zombie is the smallest possible "enemy step" and prepares players for the mini boss |

### Step 4 · The cab (1 action)

| | |
|---|---|
| Where | the driver's cab of car 1: the west end of the train, in the middle of Platform A (the train came back facing west; cars 5 and 6 are in the east tunnel mouth, see `02-WORLD.md`) |
| What the player does | holds Use for 1.5 s to fit the Handle |
| Feedback | cab lights and the car's interior lights come up warm, the headsign flaps from "047 ZERO LINE" to "047 TERMINUS", the door chime sounds twice, the board reads "047 · TERMINUS · BOARDING". The teleport is now armed for the rest of the match |

## 3. Using the teleport

| Rule | Value | Reason |
|---|---|---|
| Trigger | any player in car 1 uses the Handle | |
| Boarding window | 4 s of door chime; then the doors of car 1 close (door blockers become solid, door-leaf models slide) | lets a team gather; a late player waits for the next run |
| Who travels | every player inside car 1, downed players included (they can be revived at the Terminus; nobody is left bleeding on the platform) | |
| Zombies inside car 1 at departure | pushed out onto the platform as the doors close, unhurt | no free kills, no stowaways |
| The crossing | 3 s: interior lights rise to white, the Departure Note swells, the windows show the tunnel that is not there | |
| Arrival | players stand in an identical, spotless car at the Terminus; its doors open | |
| Stay | **40 s**. The Terminus clock is the only running clock of the map: it starts at 23:59:19 and **stops at 23:59:59**. Midnight never comes | the timer is in the world, not on the HUD; and the run has still not arrived (hook H3 stays open) |
| Return | at 23:59:59 everyone in the Terminus is back in car 1, whose doors open | |
| While the team is away | if every living player is in the Terminus, the round's spawning pauses and the zombies alive wait where they are (unproven: pausing the stock wave loop is a first probe of Q1; fallback: the round simply goes on and the zombies gather at car 1). Otherwise the round goes on for those who stayed. A downed player left outside car 1 bleeds out as normal; while everyone else is away their bleed-out timer is held | a visit is not a way to idle a round out, nor a way to lose a teammate |
| Cooldown | 150 s; the headsign reads "NOT IN SERVICE", then "047 TERMINUS" again | 40 s away in every 190 at most: the Terminus is not a shelter to chain (the shipped map allows 30 s in its room) |
| Cost | free | the cost was the quest; Pack-a-Punch itself is paid |
| Solo | identical | |
| Downs | downed players travel both ways with the team and can be revived there | |

The train does not move at any point. The players' joke, sooner or later: the last train never left, and
neither did they.

## 4. The Terminus (the Pack-a-Punch room)

**What it is.** The station **as a timetable knows it**. ZERO never saw Station 0; it knows a printout. The
Terminus is that printout made into a place: **a platform made of paper**.

- Size: one platform bay, about 1400 x 900 units, ceiling 320.
- Look: every surface is green-bar fan-fold printer paper, the kind that fills the Exchange's printer room,
  enlarged to the size of a room: pale green and cream bands across floor, walls and ceiling, sprocket holes
  the size of dinner plates down the edges, perforation lines where the walls meet. Everything on it is
  **printed** in a dot-matrix face, slightly out of register: the platform edge is a row of dashes, the
  yellow line a band of asterisks, the columns are columns of times, and every time reads 23:59. The light is
  flat office fluorescent, as over a desk.
- What is there, and nothing else: the printed edge; printed signs ("TERMINUS", "047", "WAY OUT" with an
  arrow that points into a wall of times); four benches drawn in outline and solid to sit against, numbered
  1 to 4; a clock; and on the floor **312 pairs of printed footprints** in rows, each pair with a passenger
  number, all facing the track.
- **The players' footprints.** When the team first arrives, one more pair per player is at the end of the last
  row, the ink still wet and in that hero's colour, numbered 313 onward. They are there on every later visit.
- **The Pack-a-Punch machine** (the stock machine and interaction) is the only solid, coloured object in the
  room. It stands where a ticket validator would, under a printed sign: "FARE VALIDATION". Cost and levels
  are the stock ones (5,000, then 10,000; the camos are in `08-CAMOS.md`).
- The clock runs from 23:59:19 and stops at 23:59:59.
- Beyond the platform edge the paper simply continues, blank, to a fold. On the far side of the fold, printed
  very faintly, the outline of a second platform with a train standing at it (hook H5; not reachable).
- One lore pickup: Dr. Strand's eighth tape, on bench 4.
- Sound: no music. The Departure Note, very low; a line printer somewhere, never stopping; the Voice, calm,
  reading times that are all the same time.

Reason for this look: it belongs to nothing else. It is built from the map's own object (the printout that
has filled a room in the Exchange), it is the cheapest zone to build (about 60 props and four large printed
textures on a stock technique), and it tells the player what ZERO is: a machine that has only ever seen paper.

**Where it lives in the level.** A separate box far from the station, reached only by script; a spawn volume
of its own with no spawners and no neighbours.

## 5. The order a first-time player discovers things

Nobody is told any of this by a menu. The station's own signs do it, as in a real station.

1. **Cordon (spawn).** A poster of the film, the Channel 9 van, the lit entrance canopy "STATION 0". One
   perk (Up 'N Atoms) and two cheap wall weapons. The first chime: "DEPARTURE 1".
2. **Down into the Fare Hall** (first door). Dark. The split-flap board is the brightest thing on the map and
   it is addressed to them: line 1 "DEPARTURE 1 · ZERO LINE · BOARDING", line 2 "POWER · G-2 OFFLINE",
   line 3 an arrow and "CONVERTER HALL". Overhead transit signs point the same way.
3. **Platform A.** They see the 23:47: clean, lit from inside, doors open. They can walk through it. The cab
   door has a keyhole plate: "DEAD-MAN'S HANDLE REQUIRED".
4. **Converter Hall: power.** The station wakes (section 1). The board changes to "047 · DUE 00:00 ·
   NOW --:--" and "CLOCKS 0/4". The clock above the board has started to glow at its winding key.
5. **Clocks.** The first is in front of them. The others pull them west (Platform A west, then the Breach and
   the Parlour) and east (Car Barn). On the way: the Capsule Post hatches (now with lamps), the perk machines, the
   wonder-weapon hints.
6. **Signal Cabin**, then **the Conductor**, then **the cab**: typically between rounds 6 and 9 for a team that
   is learning, round 4 or 5 for a team that knows.
7. **The Terminus.** A room made of printout, and their own footprints already printed on its floor. Pack-a-Punch.
8. **Round 10 or so: the Night Inspector** arrives to check tickets (`07-ENEMIES.md`).

A returning player can do steps 1 to 4 in any order that the doors allow; only power must come first and the
Conductor only walks once the road is set.

## 6. How it ties into the lore

| Step | What the players think they are doing | What they are actually doing |
|---|---|---|
| Power | turning the lights on | restarting the run that Lodestar's last crew locked out |
| Clocks | fixing clocks | making ZERO expect 047: it opens boarding. It does not log an arrival, and nothing in this quest makes it log one |
| Levers | opening a route | setting the points for the bypass that winds beside Vayle's tube |
| Handle | taking a key from a zombie | ZERO needed no driver, so the handle was ceremonial: the conductor carried it to hand to the Chairman at midnight. Taking it relieves the crew: the train now has a driver, and it is them |
| Cab | starting a teleporter | boarding the 23:47 as its passengers. The manifest printer in the Exchange adds their names |

Left open on purpose (hooks H3, H5, H8): two stopped clocks are still unwound (the Cordon's and the Exchange's); the run still has not *completed*; the
second platform in the fog is waiting.

## 7. Buildability

| Element | State today | Note |
|---|---|---|
| Power, darkness, power-on sequence | exists for the present map (G-2 breaker, darkness kit); proven locally | reuse |
| Hold-Use steps with model swaps and effects | exists (the present three-relay quest: 2 s hold, panel swap, effect) | the relay quest is replaced by this one; its code pattern is reused |
| Clock hands moving, levers moving, headsign and board flaps | script-moved or swapped models; the board is a set of pre-made plates shown and hidden, not live text | needs authored rigid models (clock hands, lever, flap plates); no collision needed |
| A named zombie with more health that drops an item | stock zombie with script-set health and a death callback | in a headless-style plan: spawn, kill, read the drop |
| Doors of car 1 closing | door blockers already exist as template brush models switched solid and not solid; the leaves are models moved by script | the car is a static prop with clip boxes, as now |
| The teleport and timed return | the project's Kino overlay has a script teleporter with a 30 s room and return, passed in its end-to-end test | same pattern |
| The Terminus as a far, separate box | the generator emits axis-aligned rooms anywhere; no zone may lie above another, which a far box satisfies. Unknown: what the stock spawner does when every player is outside all spawn volumes | the Terminus is a spawn volume of its own with no spawners and no neighbours; Q1 tests "all players in the Terminus for 40 s at round 20" and reads the zombie count and script errors |
| The split-flap board | a fixed set of whole-line plates and two digit wheels for the round number (about 40 plate models, at most 5 shown); every plate is an entity whether shown or not | counted in the entity ledger (TF8); if the ledger is tight the board keeps only whole-line plates and the round number stays on the HUD |
| Car 1's closing doors | door blockers are a finite pool of template brush models | counted in TF2's pool count; fallback: the doors stay open and departure takes whoever stands inside the car's box |
| Pack-a-Punch machine | stock interaction; worked on the present map with a real key press | reuse |
| The players' footprints | decals placed by script on first arrival (one model or effect per player) | counted in the entity ledger |
| In-world running clock | a `settimer`-style HUD is not in the world; the clock is two script-rotated hands driven by the same timer | authored model |
| Test | the map playtest harness has a `quest` phase; it is extended with clock, lever, conductor, cab and teleport cases | proof in `12-BUILD-PLAN.md`, package Q1 |
