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

| Plan | What it proves | Result (headless, build e geometry, modules as server custom scripts) |
|---|---|---|
| `t1_routes` | 4 hatches unsealed (750 each), all 12 routes on BLOW, the lever (12 s changeover), all 12 on DRAW | **PASS 128/128**; 24 rides, 432 position samples every 0.25 s, every sample in the destination zone by the map's volume table and by the engine's own spawn volume (`sz_q1t1.py report`), 0 script errors |
| `t1_rules` | every refusal, dial tap and hold, capsules, rest, changeover and lever reset, inspection (stand-in Inspector) for 15 s after, downed, busy, points, blowback, a player on the hatch, two riders on the last capsule, a rider who leaves mid-ride | 38/39; the miss was the probe reading the blowback counter before the module counted it (3 zombies stood at the BARN hatch); module fixed (counted when they come out) |
| `q1_steps` | refusals before power and before the clocks, a tap is not a hold, 4 clocks (4 bursts of 4), wrong levers (spring back, 4 zombies), the road, the Conductor (450 health = 3x, leaves at a round end, back at the next), the Handle, the cab, the teleport, Pack-a-Punch at the Terminus (5,000 taken), the return, 150 s not in service | 37/43 on the first run; two causes found: the Conductor's leave was taken for a kill (fixed), and **the Terminus floor had no collision beyond x 8,381 / y 8,796** (the player fell at Pack-a-Punch; fixed in the collision encoder, below) |
| `q1_order_coop` | out of order, 2 then 4 players: burst of 6 with two players, the Handle carrier down (dropped) and leaving (dropped), a downed player inside car 1 travels, zombies inside car 1 put out, a player on his feet left outside keeps the round going | **PASS 16/16** |
| `q1_late_round` | round 20 (stock rounds), every player at the Terminus for 40 s | **PASS 7/7**: spawning paused 41 s; zombies alive 10 at arrival, 0 after 30 s (the stock cleanup recycles zombies far from every player), 6 again after the return; round 20 kept running |
| `q1t1_travel1..3` | body walks with player physics from every hatch arrival and the Terminus arrival into the zone and back, zombies reaching a player on each hatch and inside car 1 | hatches PASS 12/12; car 1 zombies 3/3; the Terminus walk fell (collision, above); the hull-trace walk cannot pass car 1's 84-unit doors (tool limit, ledger) |

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