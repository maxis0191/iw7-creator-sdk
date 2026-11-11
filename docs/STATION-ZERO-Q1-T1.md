# Station Zero: the road to Pack-a-Punch (Q1) and the Capsule Post (T1), version 1

The two systems of `station-zero/04-PAP-QUEST.md` and `station-zero/03-TRANSPORT.md` as game script on the 19-zone
blockout. Version 1 is the rules with stand-in stock models, stock sound aliases and stock effects; the hero objects
(clocks, levers, board, hatches, capsules: HO1), the visible ride (T2), the Tab page (H1) and the Night Inspector
himself (E4) come later and plug into the hooks below. Nothing here is deployed.

## Files

| File | What |
|---|---|
| `tools-source/iwzmap/modules/quest.gsc` | Q1: clocks, the road, the Conductor, the Handle, the cab, the teleport, the Terminus clock, the spawn pause |
| `tools-source/iwzmap/modules/post.gsc` | T1: four hatches, unsealing, the dial, postage, capsules, rest, the Bellows lever, blowback, refusals, inspection |
| `tools-source/iwzmap/sz_modules.py` | fills the modules' marker and volume tables; the level script starts them ([SCENEGEN](SCENEGEN.md), "Game-script modules") |
| `tools-source/iwzmap/sz_q1t1.py` | the map's Q1/T1 test plans and their report |
| `scenes/station_zero.json` | new markers: 8 `quest_lever`, `quest_diagram`, `quest_cab` (car 1's box as `area`), `quest_conductor`, `terminus_arrival` (the Terminus box), `post_lever` |
| server `ops/gamelab/lib/szq.gsc` | gamelab library: the state of both systems as `GL PROBE` lines, extra bots (co-op), downed and leaving players, the test ride |
| server `tests/fixtures/szq_soak.gsc` | soak exerciser: keeps the teleport and the Post in use during a soak (`Invoke-Soak.ps1 -ServerCopy`) |

## Q1 as built

| Step | Built | Player sees and hears |
|---|---|---|
| Power | the stock generator (W1b); Q1 waits for `power_on` | board line "047 - DUE 00:00 - NOW --:-- - CLOCKS 0/4" |
| 1. Clocks | four clocks (Fare Hall, Platform A West, Car Barn, Parlour), hold Use 3 s, any order; before power "THE CLOCK WILL NOT TURN: NO POWER" | the clock turns, bell, sparks, "A CLOCK STRIKES TWELVE (n/4)", board "CLOCKS n/4"; a burst of 4 / 6 / 8 zombies (1 / 2-3 / 4+ players) from the nearest spawner, on top of the round |
| 2. The road | eight levers in the Signal Cabin, three lit at random per match (the diagram and the levers' prompts name them); locked until the four clocks | right lever: clack, prompt "locked over, lamp green"; wrong lever: every pulled lever springs back, buzzer, 4 zombies; third right lever: board "ROAD SET FOR 047" |
| 3. The Conductor | a stock zombie from the spawner nearest car 6, 3x health, walks; leaves at a round end and comes back at the next round start; cannot be lost | whistle cue, board "THE CONDUCTOR IS ON THE PLATFORM"; on death the Dead-Man's Handle lies where he fell; a carrier who goes down or leaves drops it there |
| 4. The cab | hold Use 1.5 s in car 1's cab with the Handle; the teleport is armed for the match | "047 TERMINUS: BOARDING" |
| The teleport | Use at the cab: 4 s boarding, everybody inside car 1 travels (downed players too), zombies inside car 1 are put out on the platform, 3 s crossing (white light, portal sound, shake), 40 s at the Terminus (its clock's prompt runs 23:59:19 to 23:59:59), back in car 1, 150 s "NOT IN SERVICE" | board "AT THE TERMINUS", "NOT IN SERVICE", then "TERMINUS - BOARDING" again |
| Spawn pause | while every player on his feet is at the Terminus the stock `level.zombies_paused` is set; any player on his feet outside keeps the round going | |

Not built in version 1 (written in the bible, owned elsewhere or later): the split-flap plates (W5; the board is one
server-drawn line), the clock hands and lever models (HO1), the footprints, the Terminus room's look (W3d), holding a
downed outside player's bleed-out timer while the others are away, the Conductor walking a set path (he chases like
any zombie, at walking speed).

## T1 as built

Ring order on BLOW: PLAZA (Cordon), EXCHANGE, BARN (Car Barn), PARLOUR. One segment 250 points, two 400, three 550;
version 1 ride (black-out) 2.5, 4.5, 6.5 s. Unsealing 750 once per hatch (hold Use 1.5 s). A tap of Use turns the
hatch's dial to the next unsealed address (the prompt shows "To BARN ** 400 - tap Use: next address, hold Use:
send"), holding Use 0.8 s sends. Two capsules per hatch, each back 30 s after it leaves; 45 s rest per rider; the
Bellows lever: 12 s changeover (no launch, prompts "CHANGEOVER"), then 45 s before it can be thrown again. Blowback:
up to three zombies within 48 units of the hatch's mouth are hidden and held at launch and come out of the destination
hatch 2 s after the rider, standing still 1 s. The rider is placed at the destination hatch at launch, hidden, frozen,
protected and ignored, behind a black screen, so the spawn system counts him in the destination zone for the whole
ride. A player standing on the destination hatch is moved 64 units aside. Refusals take nothing and say why (no power,
not enough points, sealed, no capsule, changeover, inspection, rest, downed, busy) with the deny sound.

Hooks: `player.iwz_busy` (shared by the Post, the Terminus crossing and the emotes of M1); `player.iwz_bon_voyages`
(P1: half postage, weapon up on arrival); `level.iwz_inspector` (E4: an entity or array; hatches within 300 units say
INSPECTION until 15 s after he moved away); `level.iwz_post_ride` (the test entry: ride without Use, same rules).

## Tests (the map's suite)

`python -I -B sz_q1t1.py plans <src> <folder>` writes nine plans; all but the client plan run headless
(`Invoke-GameLabHeadless.ps1 -UsermapDir <built map>`, library `szq`). Lab sessions may answer a Use hold for the
bot: dvar `iwz_test_hold` 1 (held) or 0 (a tap); it is read only when the dvar `gamelab` or `soak_driver` is set.

Conditions of every headless run: one dedicated server, engine bots, no client; zombies only from the plan or from the
quest (stock waves off) except where stated; zombies ignore the tested bot, which is protected (999,999 health); no
inactivity kick.

| Plan | What it proves | Result |
|---|---|---|
| `t1_routes` | 4 hatches unsealed (750 each), all 12 routes on BLOW, the Bellows lever (12 s changeover), all 12 on DRAW | **PASS 128/128** on the map with the modules in the zone (build h); 24 rides at 250/400/550 exact; on build g 432 position samples every 0.25 s, all in the destination zone by the map's volume table and by the engine's own spawn volume |
| `t1_rules` | every refusal (power, points, sealed, capsule, changeover, inspection, rest, downed, busy), dial tap and hold, 2 capsules per 30 s, 45 s rest, the lever's reset, inspection for 15 s after (stand-in Inspector), blowback, a player on the hatch, two riders on the last capsule, a rider kicked mid-ride | **PASS 39/39** (build h) |
| `q1_steps` | refusals before power and before the clocks, a tap is not a hold, 4 clocks with 4 bursts, wrong levers (spring back, 4 zombies), the road, the Conductor (3x health; leaves at a round end and comes back), the Handle, the cab, the teleport, Pack-a-Punch at the Terminus (5,000 taken, the player standing on the floor), the return to car 1, 150 s not in service | **PASS 43/43** (build j) |
| `q1_order_coop` | out of order, 2 then 4 players: burst of 6 with two players, the Handle carrier down and leaving (dropped both times), a downed player inside car 1 travels, zombies inside car 1 put out, a player on his feet left outside keeps the round going | **PASS 16/16** (build h) |
| `q1_late_round` | stock rounds from 19 to 20, every player at the Terminus for 40 s | **PASS 7/7** (build h): spawning paused 41 s, the round went on after the return |
| `q1t1_travel1, 2` | player-physics walks from the four hatch arrivals into their zones and back; zombies from each zone reach a player standing on its hatch | **PASS 6/6 + 6/6** (build h) |
| soak `s3` | normal stock rounds (cleared after 60 s), 3 immortal bots, every door open, no client; `tests/fixtures/szq_soak.gsc` does the quest, then Terminus trips with all bots and a Capsule Post ride every 20 s, the lever every 3 min; the newest modules as loose scripts | **PASS**: 32 min, rounds 0 to 16, server working set flat at 1,044 MB, 0 script errors; 7 Terminus trips (20 returns of 21 departures, the last in flight at the end), 33 rides with 32 arrivals, 30 refusals (rest, capsule, changeover); the Conductor waited for a free agent (the four bursts filled all 24) and came 36 s later; 0 players stuck (3 flags were the exerciser counting a ride right after a trip as one long busy time; fixed); 28 stuck-zombie sentinels, all within about 100 units of where an immortal bot stood (car 1 after a return, the hatch arrivals) |
### The Terminus floor (found by these tests)

A trace sweep in the game (127 vertical traces every 100 units over the whole room, one headless session) hit the
Terminus floor only at 32 points: x <= 8,380 and y <= 8,750, and a ray starting beyond that found no wall either,
although the emitted collision has the floor everywhere (`iwz_emitcheck at`) and the compiled collision is byte for byte
the emitted one. Cause, read from the compiled clip map (`<work>\dump\cp_iwz\maps\cp\cp_iwz.d3dbsp.colmap`, floats at
0xC6): the map compiler kept the template's physics broadphase, Spaceland's x -13,600..8,384, y -7,864..8,760; physics
queries (traces, player movement, AI) are answered only inside it. With that box grown (10,424 / 9,932, written into
the dump for a proof build) the same sweep hits 127 of 127 points. Fix at the source: x64-zt `iwzmap.cpp`
`build_clip` grows the broadphase to hold the generated world plus 1,024 units (branch `claude/iwzmap-broadphase`).
A first theory (collision sections too wide) was wrong: splitting sections to 1,024 units changed nothing (32 of 127
again); that option stays available (`IWZ_MAX_SECTION`) but is off.