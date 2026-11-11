# 03 · FAST TRAVEL: THE CAPSULE POST

The owner's requirement: a well-thought way to travel quickly between zones, not overpowered, and NOT "all metro
stations". Nothing in this system is a train, a line or a stop. It is **post**: the rider is a parcel with an
address. (The one train of the map, the 23:47, never moves: it is the Pack-a-Punch chamber, `04-PAP-QUEST.md`.)

## 1. Candidates

Scored 0 to 5 on the five tests of the brief.

| # | Candidate | Quick | Not overpowered | Fun | Fits the lore | Buildable with the tools | Total | Verdict |
|---|---|---|---|---|---|---|---|---|
| A | **The Capsule Post**: one-rider brass capsules sent through the Victorian dispatch tubes to an address the rider dials; near and far addresses are swapped by the Bellows' direction | 5 | 4 (two capsules per hatch, price and time by distance, blowback) | 5 (a ride you see, a choice at the dial, zombies drawn in behind you) | 5 (Vayle's tubes re-bored by Lodestar: both eras in one object) | 4 (script-moved rider; two authored rigid models and pipe dressing) | **23** | **chosen** |
| B | **Collect Call**: pay phones that carry the caller along the Carrier to another ringing phone | 5 | 2 (a teleport from any wall is an escape button) | 3 (instant, nothing to see) | 4 | 5 (script only) | 19 | rejected: a second teleport beside the Pack-a-Punch one makes both dull; kept as the pay-phone secret |
| C | **The Trolley**: a hand-pumped inspection trolley on the service track | 2 | 4 | 4 | 3 | 2 (a moving platform that carries players: moving collision in a built map is not stated as possible) | 15 | rejected: it is a small train on rails |
| D | **Drop chutes**: one-way slides from upper levels to lower ones | 4 | 5 | 3 | 3 | 2 (the generator has stairs only; no slide collision) | 17 | rejected: one-way only solves half the map and cannot be built |
| E | **Hub and spokes** from the Parlour's desk (every hatch sends to the Parlour, the Parlour to any) | 3 (two rides for most trips) | 4 | 3 | 4 | 4 | 18 | rejected: it is the shipped map's own portal pattern, and it makes the Parlour a room everyone passes through and nobody stays in |

## 2. The Capsule Post in one paragraph

Four hatches in four corners of the map; behind each, two brass capsules. A rider turns the hatch's **address
dial** to one of the other hatches and is sent there. The tubes form a ring driven by one blower, so an
address one segment downstream arrives in 5 seconds for 250 points, two segments in 9 seconds for 400, three
segments in 13 seconds for 550. Which addresses are downstream depends on the Bellows: one lever in the
Bellows Vault sets **BLOW** or **DRAW** and swaps near for far. So the Post is fast, every destination is
always reachable, but it is never free of thought: it carries two riders per hatch per half minute, the far
side of the map costs more than double, and a zombie touching the hatch when you leave comes out behind you.

## 3. Hatches and ring

| Hatch | Zone | Where exactly | Dressing |
|---|---|---|---|
| **PLAZA** | the Cordon (street) | inside Lodestar's decontamination tent, a capsule hoist rising from a cut in the pavement | yellow Lodestar steel frame over a Victorian cast-iron mouth |
| **EXCHANGE** | Lodestar Exchange (works, north-east) | end wall of the relay aisle, between two racks | hatch set in a rack bay, cables tied aside |
| **BARN** | the Car Barn (works, south-east) | beside the inspection pit, at floor level | hatch in a brick pier, oil-stained |
| **PARLOUR** | the Parlour (underneath, west) | the original 1893 dispatch desk: four hatches in carved walnut, two still glazed | the only untouched Victorian hatch; gilt lettering "DISPATCH" |

Ring order on BLOW: PLAZA, EXCHANGE, BARN, PARLOUR, PLAZA. On DRAW the order reverses.

| From PLAZA to | On BLOW | On DRAW |
|---|---|---|
| EXCHANGE | 1 segment: 5 s, 250 | 3 segments: 13 s, 550 |
| BARN | 2 segments: 9 s, 400 | 2 segments: 9 s, 400 |
| PARLOUR | 3 segments: 13 s, 550 | 1 segment: 5 s, 250 |

(The same pattern holds from every hatch: one near, one middle, one far; the lever swaps near and far.)
The dial shows the three addresses by **name** with their price and a one, two or three-lamp distance mark, so
nobody has to know what "clockwise" means. **Input** (the server can read only fire, aim, melee, use and the
view direction): a tap of Use at the hatch turns the dial to the next unsealed address (the use prompt shows
its name, price and time); holding Use for 0.8 s sends. A tap on a dial with one address does nothing.

Walking, for comparison (`02-WORLD.md`): the longest walk of the plan is about a minute; most cross-map walks
are 35 to 50 seconds through two or three doors' worth of zones.

## 4. Rules (exact)

| Rule | Value | Reason |
|---|---|---|
| Needs power | yes: the Bellows is electric since 1984 | fast travel comes after the first big objective, as on the shipped maps |
| Unsealing a hatch | 750 points, once per match per hatch, any player; hold Use 1.5 s on the pressure wheel | the team invests in the network piece by piece and learns where the hatches are |
| An address can be dialled when | both hatches are unsealed; a sealed address is shown dim with "TUBE SEALED" | simple to read |
| Postage | 250, 400 or 550 by distance, per rider | near trips are cheap enough for every round; the far side is a decision |
| Capsules | 2 per hatch; each returns 30 s after it leaves | the Post moves individuals; it does not evacuate a squad of four or eight |
| Per rider | a player who has just arrived cannot be sent again for 45 s (their dial shows "REST") | a ride is 5 to 13 s in which nothing can hurt the rider: without this, chained rides would be a shelter |
| Ride | 5, 9 or 13 s; the rider is linked inside the capsule, cannot shoot, takes no damage, sees through the glass | a ride, not a loading screen; the long ride is long on purpose |
| Arrival | the weapon comes up over 1.0 s; no slow-down | arriving into a crowd is a risk without being a punishment on an empty arrival |
| Blowback | every zombie within 48 units of the hatch at launch (up to 3) is drawn in and is thrown out of the destination hatch 2 s after the rider, knocked down for 1 s | clear the hatch before you leave, or bring company |
| The lever | in the Bellows Vault; any player; changeover takes 12 s, during which capsules still fly on the old direction and no new one launches (all lamps amber, the organ sounds the Departure Note); then 45 s before it can be thrown again | a shared tactical state. Because every address stays reachable in both directions, a thrown lever can annoy a team (one trip dearer) but cannot trap it |
| Downed players | cannot board | no rescue by tube |
| Night Inspector | hatches within 300 units of him show "INSPECTION" and sell nothing, until 15 s after he moves away | the mini boss shuts the nearest way out |
| Rollers | the Post works during their round | riding mostly costs points against something that fast |
| Refusals | not enough points, sealed, no capsule, changeover, inspection: each has its own plate text and a dull clunk; no points are taken | the player always knows why |
| Bon Voyages perk | postage half price; weapon already up on arrival; the 45 s rest still applies | `06-PERKS.md` |

Solo: identical. With eight players two capsules per hatch are deliberately too few.

## 5. What it looks and sounds like

- **Hatch**: a round cast-iron mouth 48 units across with a brass rim and a riveted glass door; above it a
  pressure gauge with a real needle, a lamp (green ready, amber wait, red closed), and the **address dial**: a
  brass ring with three enamel name plates and a pointer the rider turns. Lodestar's 1984 retrofit is bolted
  over it: yellow frame, hazard chevrons, a coin slot stencilled "POSTAGE", and "INSPECTION CAPSULE · ONE
  PERSON · KEEP ARMS IN".
- **Capsule**: a copper cylinder 84 units long with a glass canopy, a buttoned red leather pad from 1893 and a
  1984 lap belt; a parcel label holder on the lid in which the address card flips to the chosen name.
- **Tubes**: where they cross a zone they are visible as cast-iron pipe 52 units across with glass inspection
  windows every 256 units, hung from the ceiling or half-buried in a wall. A passing capsule is seen and heard
  by players in that zone (lit amber from inside): this is how new players learn the network exists.
- **The ride**: the hatch seals (cork-and-leather thump), a one-second inhale as the Bellows takes up, the
  launch. Through the glass the rider sees, as a blur, zones from angles nobody walks: above the platform,
  behind the relay racks, under the Parlour's floor. A far address passes through two other hatches' junctions
  with a double clack.
- **Sound** (`11-AUDIO-DIRECTION.md`): gauge needle ticking up; the Departure Note under every launch; a
  cork-pop; a whoosh with a pitch drop for bystanders; on arrival a hiss and a two-note brass bell.

## 6. How the zombies react

- Ordinary zombies cannot ride except by blowback. They re-path on foot. The stock rule that recycles zombies
  far from every player still applies, so a solo rider is met within seconds by fresh spawns at the
  destination: the ride resets the fight, it does not end it.
- Blown-back zombies arrive knocked down for 1 s, then behave normally.
- The Night Inspector does not ride. He closes hatches near him, and when his marked player has left his zone
  he climbs out of the inspection plate of the zone they are in 6 s later (`07-ENEMIES.md`).
- During a ride the rider is counted in the zone of the destination hatch from the moment of launch, so the
  spawn system never sees a player in no zone.

## 7. Failure cases and what the script does

| Case | Behaviour |
|---|---|
| Rider disconnects mid-ride | the capsule completes the path empty and returns; no stuck link |
| The destination hatch is blocked by a standing player | that player is pushed 64 units aside when the hatch opens |
| Match ends or the map changes mid-ride | riders are unlinked first in the end-of-game cleanup |
| Two players use the same capsule on the same frame | the first Use wins; the second is refused without charge if it was the last capsule |
| Lever thrown while capsules are in flight | they finish on the old direction; prices already paid stand |
| A rider holds a quest item | allowed; items ride |
| A late joiner | hatches already unsealed stay unsealed for everyone |
| A rider emoting, or in the Pack-a-Punch crossing | refused: one shared "busy" flag is set by the Post, the teleport and emotes |
| The Night Inspector's marked player rides | the mark is kept through the ride (and through a Terminus visit); the Inspector goes to the plate of the destination zone |
| Bots and the test harness | a script entry `iwz_post_ride(player, hatch)` rides without Use |

## 8. Why it is not overpowered, and why it is not tedious

1. Unavailable before power; 3000 points to open fully.
2. Two riders per hatch per 30 s.
3. Distance costs time and points: crossing the ring the long way is 13 s and 550.
4. Arrival may come with up to three zombies, and the weapon is down for a second.
5. The mini boss closes it locally.
6. Both ends are ordinary zones with live spawners: no safe room.
7. A rider cannot chain rides (45 s rest), and a marked player keeps the Inspector's mark through a ride.
8. And against tedium: the rider always goes where they dialled; the near trip is cheap and takes 5 s; the
   lever changes prices and times, never possibilities.

## 9. Buildability

| Need | State today | Plan |
|---|---|---|
| Move a linked player along a path by script | the base game's scripts do it, and the project has linked players to a moving entity (the boat set-up, the train fixture's view points) and built a script teleporter with return (Kino) | package T1; first proof: a plan rides every pair of hatches in both directions and reads the rider's position each 0.25 s |
| Capsule, hatch and dial models | authored rigid models are proven drawn in the game; collision for imported models is missing, so the hatch is built into a generated wall niche and the capsule never needs collision | two rigid models; pipe runs from stock pipe models if the kit lists have them, else one authored segment and one elbow. Their entity cost (8 capsules, 4 dials, gauge needles) is written in the entity ledger |
| The view through the glass | everything is always drawn, so the path may pass anywhere; the path is a list of axis-aligned points with elbows | path data in the map source so that `iwz_emitcheck.py at` verifies no point is inside a wall |
| Blowback | the stock spawner calls place a zombie at a point; the old one is removed without reward and a new one given the same health | script |
| The rider's zone during a ride | unknown how the stock zone tracking treats a linked player passing through walls | T1 reads zone and spawner activity during rides; the rule in section 6 is the fix if needed |
| Version 1 | a 2.5 s black-out with the full sound sequence and a camera shake (scaled 2.5, 4.5, 6.5 s by distance), same rules | rules first, the visible ride second (package T2) |
