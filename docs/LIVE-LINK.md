# Live link: the running game as the viewport of a map tool

Line T1 and T3 of [MAP-BUILDER-FINAL.md](MAP-BUILDER-FINAL.md). A game session stays up on a map; a prop placed, moved or deleted
outside shows in the game within a second; a frame comes back on request; a person in the game can place and turn props with keys and the
outside tool records what they did.

**State (22 Nov 2026): built, offline-tested, not yet run in the game.** Measured offline: the protocol, the record, the difference sync,
the section write-back, BMP to PNG, and the game script's logic in Forge's script VM (gscvm). Not measured: everything that needs the engine
(the table at the end says which).

## Parts

| Part | Where | What |
|---|---|---|
| game script | `live/livelink.gsc` in the **Forge** repository (`C:\forge`) | `live_serve( name, seconds )`: one call from a plan, a thread that reads the dvar `iwz_live` every server frame and runs the ops in it |
| session | `forge live ...` (`C:\forge\README.md`, section "forge live"; code `forge/live.py`) | boots or reuses a client cell, starts the plan with the script, holds the session, sends ops through the game's console, reads the acks from the cell's log, takes frames, keeps `live_state.json` |
| client | `tools-source/iwzmap/live/iwzlive.py` | `Session` (start, prop, delete, camera, shot, sync, edits), a CLI, and `apply_edits_to_section` |
| proof | `tools-source/iwzmap/live/prove_live.py` | line T1: 50 placements, 10 moves, 10 deletes, 5 frames, a reload |

The script is **not** in a repository's gamelab library: Forge compiles the live plan with the script from its own folder (`forge/overlay.py` copies the
workspace's plan compiler plus the tool's `*.gsc` into an overlay; `forge run --library-dir <folder>` does the same for any plan). Any tool can hand Forge
its own script file (`forge live start --script <file.gsc>`); no change has to be on a main line first.

## The protocol

A command is one console line: `set iwz_live "<seq> <op> <args>|<seq> <op> <args>"` (at most 900 characters; longer batches are split). The script runs each op once
(an op whose `seq` is not above the last one is skipped) and prints `[IWZ local] LIVE ack seq=<n> op=<op> ok=<0|1> key=value ...`. Values hold no space, `|`, `;`, `"` or `\`.

| Op | Does | Status |
|---|---|---|
| `ping` | ack only | built |
| `prop <id> <model> x y z pitch yaw roll [scale]` | creates the script_model `<id>` or updates it in place. `ok=0 why=model_not_loaded` when the level did not load the model (see Limits) | built; scale is **not possible** (no script call sets a script_model's scale in this engine's function list): the ack says `scale=ignored` |
| `del <id>`, `clear`, `list` | delete, delete all, print `LIVE prop id=.. model=.. origin=x,y,z angles=p,y,r` per prop | built |
| `cam x y z yaw pitch` | the eye goes there and stays: the player is linked to a `script_origin` anchor (the runtime's own `freeze` hold), the eye height is measured and corrected; the ack carries `eye=` and `err=` | built, unmeasured |
| `shot <name>` | `capture_frame iwz_live_<name>` as the plan step `capture` does, waits for `paris_see_done`; ack `file=iwz_live_<name>.bmp taken_ms=` | built, unmeasured |
| `gun 0\|1`, `ui 0\|1` | the view model (`disableweapons`) and the 2D HUD (`cg_draw2d`) off for clean frames | built, unmeasured |
| `hud <text>` | one status line on screen | built, unmeasured; each new text is a new string of the engine's pool: change it rarely |
| `light <targetname> <intensity> [r g b [radius]]` | sets the lights a **map** carries (`light_spot` entities with a targetname, as the darkness module's station lights): `setlightintensity` (proven by the darkness module), `setlightcolor`, `setlightradius` (in the engine function list, argument forms never run here) | built, partly unmeasured. **Creating or moving a light at run time is not possible**: no `spawn("light")` or origin call exists in the function list |
| `fly 0\|1` | free flight for a human: releases the anchor and sends the engine's console `noclip` (a toggle; the state is tracked) | built, unmeasured; needs a human client and may need cheats |
| `edit 0\|1`, `grid <n>`, `palette <model>` | the in-game editor below | built, unmeasured |
| `e_place`, `e_select`, `e_delete`, `e_turn <deg>` | the editor's actions without a key, from the view the player has (`cam` puts it anywhere): the same code the keys run, so a live session can exercise the editor | built, unmeasured |

## In-game editing (phase 1: keys, no menu)

With `edit 1` (weapons disabled so the buttons do not fire):

| Key | Does |
|---|---|
| attack | places a copy of the palette model at the crosshair's hit point (`bullettrace` 2000 units), snapped to the grid (default 8), yaw rounded to 15 degrees; it becomes the selection |
| ads | selects the live prop nearest the crosshair ray (within 80 units; script models without collision are not hit by traces, so the ray distance is used) |
| use | deletes the selection |
| frag / tactical | turn the selection +15 / -15 degrees |

Each change prints `[IWZ local] LIVE edit op=<place\|turn\|delete> id=.. model=.. origin=x,y,z angles=p,y,r`; `forge live edits` and `Session.watch_edits()` return them and
`apply_edits_to_section` writes them into a section. **The keys cannot be pressed in a Forge live session as built:** the client cell runs on a hidden desktop (`winproc.py`) and `ClientCell.begin()` starts no key relay, so the edit keys only work for a person at a visible client; use `e_*` ops to test the editor. The smallest change to press keys from outside: start the gamelab key relay (`gamelab_input.Relay`, as `ClientCell.run` does for a plan with input) in `begin()` and have the script print `CLIREQ keydown:attack` cues. **Not built:** a move key (no key was specified), selection of the map's own static models (they are not script entities), a menu, undo,
save-by-key (saving is the outside tool's `save_section`). The button queries used (`attackbuttonpressed`, `adsbuttonpressed`, `usebuttonpressed`, `fragbuttonpressed`,
`secondaryoffhandbuttonpressed`) are in the engine's function list; whether they read while weapons are disabled is unmeasured.

## Using it

```
python -B C:\forge\forge.py live start --usermap <folder> --models a,b,c        # prints the session; blocks until the script answers a ping
python -B C:\forge\forge.py live send "prop a trashbin_01_iw6 244 200 0 0 90 0" "cam 100 100 60 45 0"
python -B C:\forge\forge.py live shot --name v1 --cam 100,100,60,45,0 --out C:\tmp\v1.png
python -B C:\forge\forge.py live edits --since 0 --wait 5
python -B C:\forge\forge.py live reload            # the map again, props and camera back; a rebuilt usermap is a new cell (about a cold boot)
python -B C:\forge\forge.py live status | stop
```

```python
import sys; sys.path.insert(0, r"tools-source/iwzmap/live")
from iwzlive import Session
s = Session.start(usermap=r"...\um_final2\cp_iwz", models=["trashbin_01_iw6"])
s.sync({"a": {"model": "trashbin_01_iw6", "origin": [244, 200, 0], "angles": [0, 90, 0]}})
png = s.shot("v1", cam=(100, 100, 60, 45, 0))
for e in s.watch_edits(): print(e)                  # place / turn / delete from the keys in the game
s.save_section("section.json", zone="room_a")       # in-game edits into the section's props (rows {id, zone, model, origin, angles [pitch, yaw, roll], scale, static, clip})
```

A section row without an `id` is known to the game as `p<index>`; a prop the game placed has `e<n>`. `docs/SECTIONS.md` (the section contract) did not exist on
`origin/claude/iwz-sections-core` when this was written; the rows above are the brief's.

## Limits and costs (read before relying on it)

- **Models are fixed at the session's start.** The engine ignores `setmodel` of a model the level did not precache at its start (docs/GAMELAB.md, measured 11 Nov 2026), and the
  plan can precache at most 64 (`--models`). A session therefore places only the models it was started with; another model needs `forge live start --models ... --fresh`
  (a new level, not a new cell). Detection: the entity's `model` field must change after `setmodel`; if not, `ok=0 why=model_not_loaded` and nothing changes.
- **The session holds the machine's only client slot** (`max_client_cells` is 1). It ends by itself after 30 minutes without a command (`--idle-min`), and `forge live stop` ends it
  at once; the record stays in `C:\forge-run\live\live_state.json`, and the next `start` on the same map puts the props and camera back.
- A daemon restart (`forge restart`) ends the session; `forge live start` restores it from the record (the same map and usermap folder; another one starts empty). `reload` keeps the process; a rebuilt usermap (its `.ff` changed) or `reload --hard` takes a new cell. `stop` hands the cell back with the 2D HUD on again; the map restart of the next plan resets the rest.
- A model the level cannot precache may end the plan before the script is ready: `start` then fails at once with the log line (script runtime error, `GL END`), it does not wait.
- The live plan's conditions are `quiet` (no zombies, no damage, rounds held); change with `--conditions`.
- Frames are PNG made from the client's BMP in Forge (no image library); they are the game's frames, nothing is judged here.

## What exists, what is unproven

| | State |
|---|---|
| protocol, record, splitting, ack parsing, difference sync, section write-back, BMP to PNG, overlay | measured offline (Forge `tests/test_live.py`, SDK `live/tests`) |
| the script's op loop, parser, props, list/clear/del, snap, model refusal logic | measured offline in gscvm; compiled with the pinned gsc-tool |
| the live plan's compile (gsc-tool, real compiler) | measured offline: `real_compile ok` for the plan with the script |
| ack latency, frame latency, camera hold and eye error, `capture_frame` by a live thread, `ent.model` after `setmodel`, console line length, edit keys, `fly`, light calls, reload | unmeasured: first run is `prove_live.py` |
| scale, run-time lights, selecting stock static models, a move key, a menu | do not exist |

## Not written (decided with the lead on 22 Nov)

The server repository was dropped from this work (the script lives in Forge and travels by path), so there is **no `docs/FORGE.md` "forge live" section and no `docs/GAMELAB.md` or DEVKIT row**
in `iw7-paris-server`. The text for them is the Forge README section "forge live" and this page; copy from there when the lead lands the work.
