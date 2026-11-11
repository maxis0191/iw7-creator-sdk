# Crowd module: more than 24 zombies alive on Station Zero (package E2)

The engine holds 24 zombie agents, in the server and in every client. This module fills the rest of the round's alive
cap with **crowd bodies**: one script model each, a full-body zombie model that carries **no scriptable**, playing the
stock zombie clips, walked along the navigation mesh by script, attacking and taking damage by script. The stock round
is unchanged: its wave loop spawns its agents; the module counts every crowd body as a spawned enemy and its death as a
round death through the loop's own counters, and lists the crowd in the stock list of enemies.

Why no scriptable: the server links a model's scriptable into one pool of 2,048 reserved scriptable parts and ends the
match when it is empty (server repository `docs/ZOMBIE-CAPACITY.md`, section 7). `police_officer_zombie` carries
`zombie_cop_scriptable` (its dismemberment parts, 28 to 31 a body). The map's copy `iwz_crowd_cop` has none, so a crowd
body costs 0 parts by construction. **What it loses: dismemberment.** Engine agents keep theirs.

Nothing here is new to the client: the official client draws the crowd from the map's own fastfile with stock engine
code (no client change).

| File | What |
|---|---|
| `crowd_model.py` | `make` a renamed copy of a stock `xmodel/<name>.xmb` with the scriptable reference set to none (ZoneTool dump format); `check` a file |
| `cp_iwz_crowd.gsc` | the game module (rawfile `scripts/cp/maps/cp_iwz/cp_iwz_crowd.gsc`) |
| `add_crowd.py` | puts both in an assembled zone: the model and its `xmodel` row, the script and its `rawfile` row, the level script's call (marker `//@CROWD@` of `cp_iwz3.gsc`, or before `//@AUDIO@` in an older level script) |

Build: `build-sz2.ps1 ... -Crowd [-CrowdModel police_officer_zombie]`. Tests: `tests/test_crowd.py`.

## Dvars (server)

| Dvar | Default | Meaning |
|---|---|---|
| `iwz_zombie_cap` | 0 | 0: the cap table of `docs/station-zero/07-ENEMIES.md` 2.3 (by round and players: solo 24 / 30 / 38 / 47, four players 24 / 36 / 48 / 62 / 78 at rounds 1, 10, 15, 20, 25); a number: that fixed alive cap; 24 or less: the stock game (no crowd) |
| `iwz_crowd_model` | `iwz_crowd_cop` | the crowd body model |
| `iwz_crowd_log` | 0 | 1: one server log line per crowd spawn and death; a `[IWZ crowd] STATUS` line is printed every 5 s while a crowd exists |

## What a crowd body does and does not do

- Spawns at an active stock spawner within 2,000 units of a player (two a pass, every 0.5 s) while the round owes
  enemies; the 24 agent records stay the agents' (the crowd holds at most cap - 24). Not in a stock special round
  (event waves of clowns or goons).
- Health and move mode of the round's own zombies (read from a living agent).
- Walks the path the engine's path finder gives (`findpath`, at most 8 paths a pass, a new path every 2 to 3 s), keeps
  30 units from other bodies, swings within 56 units (40 damage at the contact time if the player is still within 72).
- Shots: every `weapon_fired` of a player is tested from the eye against a head sphere and a torso capsule (bullets do not
  collide with a script model; server repository `docs/ACTOR-KIT.md`, probe 3): instant-hit only, damage by weapon class
  (a table), head x2. Engine damage on the model (explosions, scripted weapons, traps) counts too.
- Death: a death clip, 60 points (100 for a head), the stock power-up drop rule, the round's counters. The stock nuke
  kills the crowd too (it lists agents itself; the module follows `level.nuke_zombies_paused`).
- A body that has not moved for 10 s and is farther than 1,500 units from every player is recycled (spawned again near
  the players).
- Not done: blending between clips (cuts), dismemberment, the instant-kill power-up on crowd shots, the about 100 stock
  call sites that list agents directly (`getaliveagentsofteam`), promotion of a crowd body to a free agent record.

Measured results: server repository `docs/ZOMBIE-CAPACITY.md`, section 9.
