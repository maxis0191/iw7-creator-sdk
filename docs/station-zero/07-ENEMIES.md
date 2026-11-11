> **Note (11 Nov 2026):** the hybrid crowd described in this document (2.2 and every mention of crowd bodies) is withdrawn. The crowd module was removed on 11 Nov 2026 because script-moved bodies are not real zombies; real capacity is engine work (server repository docs/ZOMBIE-CAPACITY.md).

# 07 · ENEMIES

Contents: the ordinary dead of Station Zero; seventy-eight at once (what it means, how, the proof); the mini
boss, **the Night Inspector**; the special round, **the Rollers**. Everything here is original to this map.

One tool carries this whole chapter: the **actor kit** (a body with our model and our animations, moved, hit
and made to attack by script). The crowd beyond 24, the Rollers and the Inspector are three uses of it. It
does not exist yet (`12-BUILD-PLAN.md`, packages C1 to C3 and E1). Until it does, the map plays with the
stock stand-ins named in each section, so nothing blocks a playable build.

---

## 1. The ordinary dead

**Who.** Passengers, staff and cleaners (`01-LORE.md` section 8). Eight outfits (M1 to M4, F1 to F4).

**Where each outfit appears** (weights per zone; a zone draws from its own table so the crowd tells you
where you are):

| District | Mostly | Some | Never |
|---|---|---|---|
| Cordon | F4 Lodestar Cleaner (from round 8), M1, F1 | M4 | M3 |
| Fare Hall, Underpass Arcade | M1 Commuter, F1 Office Commuter, F2 Token Clerk | F3 Club Kid | M3 |
| Platform A, the 23:47 | M1, F1, M2 Conductor, F3 (near car 6) | M4 | |
| Works (Car Barn, Converter Hall, Exchange, Sump, Signal Cabin) | M4 Track Worker, F4 Cleaner | M2 | F3 |
| Boneyard | M3 Zero King (paint-shop overalls) | M4 | F2 |
| Parlour, Bellows Vault, the Breach | F4 Cleaner, M4 | M1, F1 | |

**Behaviour.** The stock zombie of the game: its speeds by round, attacks, hit reactions and gibs are
unchanged. Reason: the stock zombie is the best-tested thing in the project; novelty goes into the specials.
Three additions, all script-side:

1. **They commute.** A zombie with no reachable target does not stand anywhere: it goes to the nearest
   "waiting place" (platform edge behind the yellow line, a turnstile queue, a bench, the escalator foot) and
   faces the track. Uses the stock idle-spot structs. Between rounds, the stragglers are found waiting for a train.
2. **The Lodestar Cleaner** (F4, from round 8, at most one in six): 25 % more health; on death the torn suit
   vents a pale cloud for 2 s that hides what is inside it (no damage). It is also the source of Top to Bottom's
   YELLOW can.
3. **The Conductor of 047** (M2 with a lamp): the quest zombie of `04-PAP-QUEST.md`. Once per match. As he
   walks the train he pulls each car's doors shut behind him (they reopen when he dies), so for a minute the
   train loop that players have been running is cut (door blockers are a finite pool: if the count leaves
   none for six cars he shuts only the platform doors of car 4, which cuts the loop just the same): the small enemy step teaches that this map's dead can
   change the room.

**Looks.** The eight outfits are the looks thread's work (hand-off of the earlier session; reviewers
rejected the first hero looks and no zombie has been seen in the game yet). Until an outfit passes review in
the game, that slot uses a stock zombie body.

---

## 2. Seventy-eight at once

The owner's requirement: remove the 24 cap on this map, push it to 78, and prove that 78 really spawned
naturally, appear properly, with no performance problem and room left for specials.

### 2.1 What the number 24 is

In script it is one function (`get_max_static_enemies`, `cp/zombies/zombies_spawning.gsc` line 3350 of the decompile, the same for any player count), but raising that number alone does nothing useful: the game allocates 24 agent records; the server and the client both carry fixed
tables built around it (18 player slots, 42 characters in total, map entities from index 58;
`research/A-tools-readiness.md` section i). The project's earlier attempt (64 records for 48 living
zombies) needed a matching client, and ended with the owner seeing zombies beyond 24 invisible and a server
crash; it is suspended. A stock client rejects such a server.

So "78" can be reached in two ways, and they are not equal:

| | Route N: native capacity | Route H: the hybrid crowd |
|---|---|---|
| What | enlarge the engine's agent tables to about 96 (78 ordinary, 8 specials, companions and margin), in the server and in the client | keep 24 agents; the other bodies (up to 60 once 6 records are reserved for specials) are **actor-kit bodies**: script-moved models with the zombie's own parts and animations, that can be shot, killed for points, and that attack |
| Who can play it | only players on a client this project builds | every player, on the official client, with no download beyond the map |
| State | archived work reached 48 with a recorded failure; cause unproven | not built. Proven: only the shared flow field (in the Kino overlay, which moved **real zombies taken over by script**, so its animation, hits, deaths and network came from the engine and do not transfer). Unproven: a script model playing zombie clips, bullet hits on it, its death, power-up drops, and every stock system that lists enemies |
| Risk | high: engine tables in two executables; players need our client | medium: quality of a script body next to a real agent |

**Decision** (owner's principle of 11 Nov: playable by real players; missing client features are built in
the project's fork of the client, with a graceful fallback meanwhile).

- **Route N is the real feature.** It is planned as its own package in the client fork (CF2 in
  `12-BUILD-PLAN.md`): capacity negotiated at connect, the old failure reproduced and its cause named before
  anything else. A server started with the capacity profile admits only clients that have it.
- **Route H is what a player on today's official client gets**, and it is built first, because it is the only
  form of "78" that can reach the public servers before the client changes. It is not a trick to be hidden:
  it is stated to the owner in plain words with footage when it reports, as 78 bodies in the fight of which
  at most 24 are engine agents at any moment.
- One dvar selects the mode (`iwz_zombie_mode`: `auto`, `hybrid`, `native`); the cap table, the spawn rules
  and the proof are the same for both.

### 2.2 How the hybrid crowd works (design; every line marked "unproven" is a probe of package E1 before anything is built on it)

- **Two kinds of body, one population.** The round's spawner (the stock wave loop) is unchanged except for the
  cap it counts against. When it spawns and an agent record is free and the spawn point is within 900 units of
  a player, it makes a stock zombie. Otherwise it makes a **crowd body** at the same spawner with the same
  outfit, health and round speed.
- **What a crowd body is made of (unproven).** A body model and a head model linked together: attaching a head
  to a script model does not draw it (a recorded finding of the looks work), so a body is **at least two
  entities**, more if hit volumes are entities. E1's first measure is the real entity cost of one visible,
  animated, hittable body; the entity ledger (TF8) and the cap table below are recomputed from it. If a body
  costs 2 entities, 60 bodies are 120; if the ledger cannot afford that, the cap comes down. 78 is the
  target, the ledger decides.
- **Animation (unproven).** The stock walk, run, attack, pain and death clips played on the script model
  (the call exists and was used once in a lab without visual proof). A script model has no blending between
  clips; transitions are cuts at clip ends, and E1 judges whether that is acceptable at crowd distance.
- **Bullet hits (unproven: the largest unknown of this chapter).** Nothing in the project shows a bullet hit
  landing on a script model with a hit location. Three routes, tried in this order by E1: (1) the stock zombie
  model's own collision on a script model set to take damage; (2) a fixed pool of cloned hit volumes, made
  once at map start and reused for the whole match, never cloned again (cloning per body is forbidden: an
  earlier overlay died with a fatal engine error after about 1,480 clone calls in a match; E1 and every soak
  count clone calls and fail above 1,000); (3) no collision at all: on each shot the script traces from the
  shooter's eye and applies the hit itself, which gives head and body for instant-hit weapons only. If none
  works well enough, crowd bodies cannot be shot fairly and the hybrid mode is dropped: the official-client
  cap is then 24 and "78" exists only with the client capability (CF2).
- **Presence.** A crowd body does not block players or bullets meant for other targets and does not stand
  inside another body: the flow field keeps bodies 40 units apart and keeps any body that is not attacking
  at least 96 units from every player. Inside 96 units a body is promoted first if a record is free. If none is free it attacks by script from
  64 units, and while it attacks the script holds players 40 units out of its centre (a soft push each
  frame), so a player never passes through a zombie that is swinging at them. The four parking failures recorded for script-moved zombies
  (stuck at corners, in doorways, on stairs, behind props) each get an anti-stuck rule and a test.
- **Promotion.** Twice a second, the crowd bodies nearest to players are swapped for real agents while
  records are free: same place, facing, health, outfit; the swap happens when no player has it inside a
  30-degree view cone within 600 units, or else at the cut to a pain clip.
- **Never harmless.** A crowd body that reaches a player with no record free attacks by script: the stock
  swipe clip, a hit at its contact frame if the player is still within 64 units, the round's damage.
- **One enemy registry.** Nothing in the stock game or in the servers' modules knows crowd bodies exist:
  weapons, traps, power-ups (the kill-all and instant-kill pickups), perks, the end-of-round count, the zombie
  counter, the rule that recycles far zombies, idle "commuting". E1 provides one interface (the list of all
  enemies of both kinds; damage, kill, remove) and E2's scope includes moving each of those systems onto it.
  Every package that touches enemies (the four weapons, the perks, the traps, the stand-in rules, the HUD
  counter) tests against a mixed crowd.
- **Records kept free for specials.** Of the 24, 6 are reserved from round 10 on. Ordinary zombies use 18.
- **Network (unmeasured).** Up to 120 more moving entities, created and deleted through a round, ride in
  every snapshot. E2 measures snapshot size and client update rate with two clients in the network lab before
  the cap is raised above 36.

### 2.3 The cap by round and by players

Seventy-eight on round 1 would be noise, and seventy-eight on a solo player would be a wall. The cap climbs.

| Round | Alive cap, 4 or more players | 3 players | 2 players | Solo |
|---|---|---|---|---|
| 1 to 9 | 24 | 24 | 24 | 24 |
| 10 to 14 | 36 | 32 | 28 | 24 |
| 15 to 19 | 48 | 44 | 36 | 30 |
| 20 to 24 | 62 | 56 | 46 | 38 |
| 25 and later | **78** | 70 | 58 | 47 |

- Dvar `iwz_zombie_cap` (0 = this table; a number = fixed cap for tests; 24 = stock behaviour).
- **Zombies per round**: the stock formula, unchanged (`research/E-shipped-map-numbers.md`, section 5:
  it already grows with the round and the player count, to 105 solo and 510 with four players at wave 30).
  Reason: a higher cap with the stock total makes rounds denser and shorter, which is the point; multiplying
  the total as well would make late rounds last a quarter of an hour.
- **Spawn tempo**: the stock delay between spawns is kept; while fewer than half the cap are alive, two
  spawn at a time from two different spawners.
- **Where 78 come from.** Zones have 4 to 14 spawners (186 in all) of the three kinds the generator can build
  (floor, wall vent, ceiling), dressed as what they are in this place: ballast and broken tile; ventilation
  grilles; ceiling hatches; and "walk-ins", floor spawners hidden in darkness beyond a tunnel mouth, a
  shutter or the open doors of a train car so that the body arrives on foot. With three zones active
  around a team that is 30 to 40 live spawners. Boarded windows do not exist in the generator and are not
  required; they are an optional later package.

### 2.4 Performance budget

The rule is **parity with the shipped map** (`12-BUILD-PLAN.md` section 5): with four players and the cap
reached, the client's frame rate is no lower than 85 % of what the shipped map gives with its 24 zombies in
the same test on the same machine, side by side, three runs each. The project's only measured machine is an
i5-13400F with an RTX 3080 at 1280 x 720 (the shipped map baselines at 184 and 318 frames per second there);
package ST1 adds the first number at 1920 x 1080 and from a weaker machine (or its stated stand-in) in wave 1.

| Measure | Budget at 78 alive, 4 players, densest zone |
|---|---|
| Client frame rate, median | at least 85 % of the shipped map's with 24 zombies, same test |
| Client frame time, 99th percentile | under 16.7 ms on the reference machine |
| Server frame | steady at its 20 per second; no frame over 50 ms in a 10-minute window |
| Script: flow field and crowd update (hybrid mode) | under 4 ms per server frame together |
| Entities | under 1800 of 2048 at the worst moment |
| Reliable-command ring | no overflow in a one-hour soak (crowd bodies send nothing through it) |
| Network, 100 ms added ping, 2 % loss | client update rate within 10 % of the 24-zombie run |

### 2.5 The proof that closes "78" (all measured; none by eye alone)

1. **Natural.** A match on the soak runner (it hosts sessions of up to twelve hours with bots; players are
   protected and inactivity is off, as in every agent test) from round 1 to round 26 with four player slots
   filled, no scripted spawn. Expected length two to three hours; a measured round skip (rounds 2 to 9 ended
   by the stock end-of-round path after ten kills) is allowed and stated in the result. The log shows the
   alive count reaching 78 through the wave loop, with the spawner name of every body.
2. **Visible.** Two measurements. (a) Detection, on a lab client: a test dvar sends every enemy's goal to one
   point of Platform A West in view of a fixed camera, so that all 78 stand in one frame; the test then hides
   each body in turn and measures the frame difference: 78 of 78 must change the frame; independent reviewers
   look at the same frames for bodies that float, sink, slide, miss a head or stand in a rest pose. (b) On the
   official client: the same arena, a frame-difference sample on 20 bodies by killing them one at a time, and
   the client's log free of errors.
3. **Whole.** Every one of the 78 is killed by a client's weapon: 78 deaths, 78 point awards, head shots
   counted, no body left standing or stuck (the playtest harness's `cleanup` phase).
4. **Room for specials.** With 78 alive, two Inspectors and sixteen Rollers are added: all move, all visible
   by the same hide test, entity count under budget, ten minutes without error.
5. **Performance.** The budgets of 2.4, with the performance recorder (three runs a side against cap 24), the
   one-hour soak with seven bots, and the network lab.
6. **Promotion is clean.** Reviewers judge 60 s of footage at close range for visible pops; the script log
   shows no swap inside a view cone.
7. **Official client.** In hybrid mode the whole proof is run with the official client build, not the lab one. In native mode it is run with the fork client, and the official client is shown being refused cleanly.

---

## 3. The mini boss: THE NIGHT INSPECTOR

**Concept.** Chief Fare Inspector Horace Pell, thirty-one years of service. He was to punch the first ticket of
the automated age. ZERO still rosters him. He does not hunt the team: he inspects **one passenger at a time**,
the one who has been earning the most, and he fines them.
Reason: a mini boss that reads the scoreboard makes one player's fight different from the others' and gives
the team a job (keep him off the marked one, open his lamp).

**Silhouette** (redesigned after review so that he is nobody else's monster). **Short, very wide, and
lamp-headed.** About 1.7 m tall and nearly as broad: a stout man-shape in a brass-buttoned HRT tunic that no
longer closes, short bowed legs, arms that reach his knees. Where the head should be there is a **hand signal
lamp**, amber, with a peaked cap sitting on top of it and a chin-strap round the lamp's cage. The lamp is his
face, his only light and his weak point. Right arm: a hydraulic ticket punch the size of a rail tong. Over the
left shoulder a satchel from which a paper ribbon of punched tickets trails five metres behind him on the
floor: at a distance he reads as a lit lamp at chest height above a wide dark block, dragging a white tail.

**How he moves.** He **hurries**. A brisk rolling waddle at 150 units per second (a running player does about
190) and, every 10 s, a 2 s scuttle at 260 with the punch held out in front. He never uses doors. He arrives,
and follows a marked player who has left his zone, by climbing out of a brass **inspection plate** in the
floor ("HRT INSPECTION", one in every zone, 17 in all): the plate rattles for 2 s, lifts, and he hauls himself
out. This is the zombies' own floor-spawn construction with our dressing, not a new kind of opening.

**Numbers.**

| Property | Value |
|---|---|
| First appearance | round 10 (round 11 solo) |
| Then | every 4 or 5 rounds (random), never on a Roller round |
| How many | 1; from round 20 with four or more players, 2 (they mark different players) |
| Arrival | 20 s into the round, from the inspection plate of the marked player's zone, with a guard's whistle |
| Health | flat: **6,000** at his first appearance in a match, **+1,500** for each later one, capped at 30,000; multiplied by 1.0, 1.4, 1.8, 2.2 for 1, 2, 3, 4 or more players. (The stock mini boss has at most 5,000 and is hurt only in the head.) Flat on purpose: bullet weapons can always kill him, and wonder weapons deal him flat damage too |
| Damage taken | from bullet weapons: body 25 %; **lamp, glass shut: 100 %; lamp, glass open: 300 %**. From wonder weapons: at most 2,000 a hit anywhere, no lamp bonus (the stock rule for the shipped mini boss), so that no wonder weapon ends the fight in two shots |
| If not killed | he leaves by the nearest plate when the round ends and the next one due comes with +1,500 as if he had been killed; he keeps the fines he took |

**The mark.**

| Rule | Value |
|---|---|
| Who | the living player who **earned the most points during the last two rounds**. Not unspent points: spending, banking or paying points to someone changes nothing. Ties: the player nearest the plate |
| Skipped when choosing | players who are downed, away (the servers' away protection) or spectating; if everyone is skipped he waits at the plate |
| A marked player who rides the Capsule Post or goes to the Terminus | **keeps the mark**: he goes to the plate of their destination, or waits at the platform's plate until the train returns. Leaving is a delay, not an escape |
| Re-chosen | when the marked player goes down or becomes skipped for 5 s; otherwise the mark stays for his whole visit |
| What the marked player sees | "TICKET, PLEASE", a lamp icon, and the fine he would take ("FINE 870"). The first time in a match, the Voice says one sentence: passengers found without a valid ticket will be charged a penalty fare |
| What others see | a small lamp over the marked player's name on the Tab screen and above their head |
| Solo | the mark is the player; the fight is the same without the team's job |

**Attacks.**

| Attack | Tell and timing | Effect | Answer |
|---|---|---|---|
| **The Punch** | raises the punch arm overhead; 0.9 s wind-up, hit at 0.9 s, 0.7 s recovery with the lamp glass open | 90 damage in a 70-unit reach in front; if it hits the marked player, a **penalty fare**: 10 % of the points they hold, at least 100 and at most 1,500 (a player with under 100 loses what they have and is slowed by half for 3 s instead) | step sideways; shoot the open lamp |
| **The Sweep** | draws the satchel arm back; 0.6 s wind-up | 50 damage in a 140-degree arc, 100-unit reach, knocks back 120 units | back away; it is his answer to players who hug him |
| **Penalty Notice** | plants his feet, punch to the floor; 1.2 s wind-up with a rising hydraulic whine | a ring on the floor, radius 220 units: 60 damage and slowed by half for 3 s | leave the ring; 12 s cooldown |
| **The Whistle** | three blasts over 1.5 s, lamp glass open throughout | six ordinary zombies rise around the marked player; once every 30 s, only under half health | the longest window on the lamp |

**Opening the lamp.** The glass is shut except: after a Punch (0.7 s), during the Whistle (1.5 s), when the
Dispatcher's stamp lands on it (3 s), when he slips on CYAN paint (1.5 s), on his first crossing of an AMBER
Live Rail fence (1 s, stunned). Baker's Dozens' thirteenth hit on the open lamp is the best bullet a team has.

**Death and reward.** The lamp bursts, the tunic empties, the cap drops onto the plate. He leaves: (1) **each
fined player's own pile** of tokens, marked with that player's colour, which only they can collect (their
fines returned in full); (2) his **ledger** (first kill of the match only: a lore fragment, hook H6); (3) a
**Validated Ticket for each living player**: that player's next perk machine purchase is free. From the second
Inspector of a match on, (3) becomes 500 points each.

**Full animation list** (19 clips; all original, authored on our own rig and skeleton; every rule above has its clip):

| # | Clip | Length | Notes |
|---|---|---|---|
| 1 | idle | 4.0 s loop | weight shifting foot to foot, lamp turning as if looking |
| 2 | waddle | 1.0 s loop | 150 units per second; satchel swing |
| 3 | scuttle | 0.6 s loop | 260 units per second; punch held forward |
| 4 | turn left 90 | 0.7 s | |
| 5 | turn right 90 | 0.7 s | |
| 6 | turn 180 | 1.0 s | |
| 7 | climb out of the plate | 2.6 s | plate lifts at 0.4 s; lamp flares when clear |
| 8 | climb down into the plate | 2.0 s | |
| 9 | mark | 1.6 s | lamp swings to the player, punch points |
| 10 | Punch | 2.2 s | contact notetrack at 0.9 s; lamp-open notetracks at 0.9 s and 1.6 s |
| 11 | fine | 0.8 s | the punch clacks, a ticket is torn off (plays after a Punch that landed on the marked player) |
| 12 | Sweep | 1.5 s | contact notetrack at 0.6 s |
| 13 | Penalty Notice | 2.4 s | contact notetrack at 1.2 s |
| 14 | Whistle | 1.9 s | three blasts; lamp open throughout |
| 15 | lamp held open | 3.0 s | reels with the glass swung wide (the Dispatcher's stamp) |
| 16 | stunned | 1.0 s | rigid, sparks (the AMBER fence) |
| 17 | slip | 1.5 s | one foot goes, catches himself on the punch arm |
| 18 | pain | 0.5 s | a full-body flinch (no additive layer is assumed) |
| 19 | death | 3.0 s | lamp bursts at 0.4 s, tunic collapses at 1.2 s, cap lands at 2.0 s |

**Sound.** A guard's whistle (arrival, summon), the lamp's wire handle squeaking with each step, the paper
ribbon dragging, hydraulic whine and a clean metallic "chunk" for the punch, a rubber stamp for the fine.

**Stand-in until he is built.** The stock mini boss of the shipped map (already registered and proven on the
present map at round 11), with the mark, the fine and the reward added by script. The stand-in keeps the stock boss's own health, damage rules (hurt only in the head) and arrival; nothing else of this section applies to it. It is the
shipping version until the actor kit's probes pass.

---

## 4. The special round: THE ROLLERS

**Concept.** Car 6 of the 23:47 was chartered by the Orbit Rink for its New Year "Roll-In": forty
skaters in satin jackets. They are still skating. A Roller round is the max-ammo round of this map.

**Why skaters.** They move unlike anything else in the game (they cannot stop, they cannot turn sharply,
they come in lines), they belong to 1984, they are funny until they hit you, and a glide needs far fewer
and far more forgiving animation clips than a run: the right first enemy for a tool that has never yet
played one of our animations in the game.

**Look.** Satin bomber in Orbit purple with a ringed-planet back patch, headband, tube socks, white quad
skates with amber wheels that glow like the zombies' eyes, a glow necklace. Three body variants (two female,
one male) on the Club Kid base.

**Rules of the round.**

| Property | Value |
|---|---|
| First Roller round | between rounds 5 and 7 (the stock rule: no earlier than wave 5) |
| Then | every 5 to 7 rounds (the stock interval) |
| Announcement | the Three-Tone, then the Voice: a party-train announcement; the round music becomes the Orbit's own track; a mirror-ball speckle sweeps Platform A |
| Count | the stock special-round schedule (12, 18, 24, 36, then 45 on successive special rounds, scaled by players as the stock round does); at most 16 alive (24 with four or more players); they roll out of car 6 and out of two other "walk-in" spawners per active zone |
| Ordinary zombies | none during the round |
| Health | 40 % of an ordinary zombie's health for that round |
| End | the last Roller drops **Max Ammo**; the round also pays 500 points per player |

**Behaviour, exact.**

- **Pass.** A Roller picks a straight line through its target's position that runs on 300 units past it, and
  skates it at 330 units per second (a sprinting player is slower). If the player is within 56 units of the
  Roller during a 0.25 s window as it passes, the swipe lands: 40 damage.
- **Coast and return.** After the line it coasts, turns in an arc of at least 200 units radius, and lines up
  again. It never stops by choice.
- **Walls.** If its line ends in a wall inside the 300 units because the player moved, it crashes: 1.5 s
  stunned on the floor, taking double damage.
- **Conga.** Rollers spawn in chains of 4 to 6: a leader and followers 80 units apart on the same path,
  hands on shoulders. Kill the leader and the next one leads, 10 % faster. The last of a chain is the fastest.
- **Dodge.** Step off the line. Stand with a wall close behind you and step aside late. Narrow places make
  them crash; open places (Platform A, the Car Barn) favour them.
- **Counters by weapon**: see `05-WONDER-WEAPONS.md`. Nothing kills a Roller outright: a token trips, an AMBER
  fence trips, a sent Roller is thrown and falls, CYAN paint trips. A tripped Roller slides, gets up after 2 s
  and can be shot while down.
- **No safe room.** Rollers cannot skate stairs, tight rooms or train cars. So when every living player has
  been out of skating reach for 10 s (on a stair, in the Signal Cabin, inside a car, in an Exchange aisle),
  the Rollers circle outside and **throw as they pass** ("skating reach" is data: the scene description carries a skate mask, the walkable floor at least 200 units wide and not on a stair or inside a car; a player standing off the mask is out of reach): each in turn hurls a spare skate (a slow, visible projectile, 30
  damage, one throw every 2 s per Roller) through the opening at each player who is out of reach, until that player comes out; players who are in reach are skated at as usual. Hiding turns the
  round into a shooting gallery aimed at the players.
- **Stairs.** They do not take stairs: on a Roller round, spawners are chosen on the players' level (every
  level has walk-in spawners for them, the Signal Cabin's stair foot included), and a Roller whose target
  changes level skates to a walk-in spawner and re-enters on the new level 3 s later.

**Full animation list** (17 clips):

| # | Clip | Length | Notes |
|---|---|---|---|
| 1 | glide | 1.2 s loop | stride left, stride right, arms loose; speed comes from script, not root motion |
| 2 | push-off | 0.8 s | three quick strides from standing |
| 3 | crossover turn left | 1.0 s | for the return arc |
| 4 | crossover turn right | 1.0 s | |
| 5 | swipe left | 0.6 s | upper body; contact notetrack at 0.25 s |
| 6 | swipe right | 0.6 s | |
| 7 | conga follow | 1.2 s loop | hands forward at shoulder height |
| 8 | spin | 1.0 s | one full turn on the spot (also the answer to Top to Bottom's MAGENTA) |
| 9 | trip | 0.7 s | feet go forward, lands on the back |
| 10 | slide | 1.0 s loop | on the back, legs up, wheels spinning |
| 11 | get up | 1.6 s | hands and one knee, wobble, upright |
| 12 | wall crash | 1.5 s | flat against it, slides down |
| 13 | death | 1.4 s | spin-out, one skate comes off and rolls away (the skate is a separate prop effect) |
| 14 | emerge | 1.5 s | ducking out of the car door, first stride |
| 15 | thrown | 0.9 s loop | airborne, limbs wide (sent by the Dispatcher); lands into clip 10 |
| 16 | throw a skate | 1.1 s | from a standstill at an opening; release notetrack at 0.6 s |
| 17 | circle | 1.2 s | one tight loop on the spot (the answer to MAGENTA paint) |

**Sound.** Polyurethane wheels on tile (the signature: you hear a line coming before you see it), a
referee-style whoop from the chain leader, a glitter-burst pop on death, the skate rolling away and tapping
a wall.

**Stand-in until they are built.** The shipped map's own special-round enemy, which the present map already
runs (12 of them at round 6 in the last test). It keeps the round structure and the Max Ammo; it is replaced
by Rollers when package E3 closes.

---

## 5. What must exist before any of this (honest list)

| Need | Today | Package |
|---|---|---|
| glTF from Blender to a game animation | missing (running) | C1 |
| One animation of ours measured playing on a model in the game | missing | C2 |
| Actor kit: body, clips, hit boxes, script state machine, flow-field movement | missing; the script-movement half is proven on taken-over zombies | C3, then E1 |
| Skinned models written from Blender | built, on the asset tool's line; hero outfits made with it were rejected on looks, not on function | A1 |
| Bullet hits on a script-driven body (crowd, Rollers, Inspector) | **unproven**; collision for imported models is missing, and per-body cloned collision is fatal after about 1,480 clones | E1's first probe (three routes, section 2.2). Until it passes, the stand-ins of package E0 are the shipping enemies |
| A crowd body playing stock zombie clips as a script model | unproven: the first probe of package E1 | E1 |
| Native capacity above 24 | suspended with a recorded failure | CF2, in the client fork |
