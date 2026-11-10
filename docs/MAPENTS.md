# Change a shipped map's entities with no build

Status: run live on 10 Nov 2026 (see "Run live on 10 Nov 2026"). Tool: `tools-source/mapents/iw7_mapents.py`
(Python standard library, tests next to it).

## What it is for

Every map the game ships carries an **entity list**: player start points, zombie and dog spawners, trigger volumes,
interaction points (wall buys, perk machines, doors, the magic box), placed script models, lights, sound
emitters, navigation links. The engine reads that list when it loads the map. The IW7-Mod loader lets a plain
text file **replace the whole list at map load**, so an agent can change one of the game's own maps without
building a map, a zone or a mod file:

1. `export`: read the stock list from a map dump (once per map).
2. `stats`, `find`: understand what is in it.
3. `patch`: remove, change or add entities by a small JSON file. A rule that matches nothing is an error.
4. `write`: produce the file the loader reads.
5. Copy it into the game folder of the session and load the map.

What it can change: which things exist on the map and where (spawn points, spawners, interaction points, doors,
triggers that already exist, placed models, sound and effect markers), and the fields the map's script reads from
them (`targetname`, `script_noteworthy`, `script_parameters`, `origin`, `angles`, `model`, `target`, spawn flags...).

What it cannot change (it only replaces the entity text):

- the world's geometry, props compiled into the world, collision, lighting that is baked, the navigation mesh;
- the **shape** of a trigger or a brush: a trigger names its compiled shape with `model "?108"`, a brush entity with
  `model "*36"`. Those numbers point into data of the map zone (`<map>.d3dbsp.ents.data`: trigger hulls, brush models,
  scriptable instances, splines). You can move, remove or reuse such an entity, and point a new entity at an
  existing number, but a new shape needs a new zone;
- a model, effect or sound that is not loaded in the map's zone: a new `script_model` can only use models the map
  already has (take the name from an existing `script_model`).

Entities that never exist as entities in a running game are still in the list: the engine consumes vehicle nodes,
node negotiation links and the world entity at load, and the map's `script_struct` entries become script structs
(not entities). Remove them with the same patch; count them with `getstructarray` (the `ents` step of the test
runner does both).

## The loader, exactly

Source: `mapents.cpp` of IW7-Mod (component `mapents`), with the file system of `filesystem.cpp`.

- **File name.** `<clip map name>.ents`. For Spaceland the name is `maps/cp/cp_zmb.d3dbsp`, so the file is
  `maps/cp/cp_zmb.d3dbsp.ents`. The same text file is what ZoneTool dumps next to a map as `cp_zmb.d3dbsp.ents`
  (the dump keeps `maps/cp/` as folders). Confirmed live: the file at that name changed the running map.
- **Where it is looked for**, first hit wins: `<game folder>/iw7-mod/`, then the mod data folder (`cdata` of the
  mod's app data, or the bench's `lab-appdata/cdata`), then the engine's own search paths (`<base>/<fs_game>`).
  So `iw7-mod/maps/cp/cp_zmb.d3dbsp.ents` in the game folder is enough. With no such file the stock list is used.
- **Client and dedicated server.** The hook is in the shared collision-map load of the game executable, and the
  component has no client-only or server-only switch. A dedicated server and a client each read the file from their
  own search paths when they load the map. Proven on a dedicated server (below). Not run on a client.
- **Text format.** `{` and `}` in column 0 open and close an entity; every other line is `key "value"`
  (regular expression `(.+) "(.*)"`). The key is lowercased and left-trimmed.
  - a **numeric key** is a token id of the game's script string table and is passed through unchanged; this is the
    form the dump uses (`157 "script_model"`: 157 = `classname`, 543 = `origin`, 822 = `targetname`, 65 = `angles`,
    497 = `model`, 638 = `script_noteworthy`, 820 = `target`, 687 = `spawnflags`, 61049 = `script_parameters`);
  - a **quoted key** (`"classname" "script_model"`) is converted to its id through the game's token list; a name the
    list does not know is dropped with a warning (`Key '...' not found`);
  - a pair with an empty value is dropped; a line that is not a pair is skipped with a warning;
  - `//` lines and `/* ... */` blocks are comments. A one-line `/* x */` is a trap: the loader enters comment mode and
    never leaves it, so the rest of the file is lost. This tool refuses such text;
  - an unexpected `{` or `}` makes the loader reject the whole file and use the stock list, with an error line;
  - a value must not contain a quote or a line break.
  The same parser also runs on the stock list when no file exists, so the numeric form is certain to be accepted.
- **What it logs.** Only problems: `[map_ents parser] Failed to parse line N (...)`, `Key 'x' not found, on line N
  (...)`, `Unexpected '{' on line N`. The line "Reading raw ents file" is a debug print that is compiled out of the
  release executable, so a clean file leaves **no line**. Proof that the file was used has to come from the game
  (counts, below) or from a deliberate warning. The parser runs three times at each map load, so a warning
  appears three times.

## Use

```powershell
$t = 'tools-source/mapents/iw7_mapents.py'
python -B $t export --dump <map dump folder> --out cp_zmb.ents.json     # 3,695 entities for Spaceland
python -B $t stats  cp_zmb.ents.json                                    # classnames, top targetnames, origin box
python -B $t find   cp_zmb.ents.json --targetname bumper_car            # index and key fields
python -B $t find   cp_zmb.ents.json --near 467 3677 40 --radius 300
python -B $t patch  cp_zmb.ents.json --patch my.patch.json --out cp_zmb.mine.ents.json
python -B $t diff   cp_zmb.ents.json cp_zmb.mine.ents.json
python -B $t write  cp_zmb.mine.ents.json --out-dir out                 # out/maps/cp/cp_zmb.d3dbsp.ents
```

`export --dump` finds `maps/<prefix>/<map>.d3dbsp.ents` in a ZoneTool dump. `write` writes the numeric form (the
stock text byte for byte, minus the dump's trailing NUL; with `--readable` the quoted-name form, which the loader
converts). `--tokens <iw7_token.cpp>` names more numeric keys from a gsc-tool token list. Keys the tool has no id
for are written by name and reported.

`find` selectors combine with AND: `--classname`, `--targetname`, `--key K --value V`, `--box x1 y1 z1 x2 y2 z2`,
`--near x y z --radius r`, `--index N`.

### Patch file

```json
{
  "schema": "iw7.ents-patch/1",
  "remove": [ {"targetname": "pf405_auto67"} ],
  "set":    [ {"where": {"targetname": "bumper_car", "index": 1648}, "values": {"script_noteworthy": "overlay_changed"}} ],
  "add":    [ {"classname": "script_model", "targetname": "overlay_probe", "origin": "467 3677 40", "model": "toy_zombies_plastic_egg"} ]
}
```

A selector is any combination of `classname`, `targetname`, `script_noteworthy`, `model`, `target`, `key`+`value`,
`box`, `near`+`radius`, `index`. Selectors name entities of the **input** list (indexes too); removals are applied
first, then changes (to what is left), then additions. A value `null` in `values` deletes the key; `origin` may be a
list of three numbers. A rule that matches nothing is an **error** and nothing is written, unless the rule carries
`"optional": true`. The output records what each rule matched (`patch` block of the result file).
`examples/spaceland-overlay-probe.patch.json` is the patch used in the live proof.

### Test it in a private session

Install the written file as `iw7-mod/maps/cp/<map>.d3dbsp.ents` of the session's game folder and census the
entities from inside the game: the server repository's headless runner takes `-ServerCopy 'file|iw7-mod/maps/cp/cp_zmb.d3dbsp.ents'`
and its `ents` plan step prints `GL ENTS name=... key=... value=... n=...` (see its `docs/GAMELAB.md`).

## Which players get a change

- **Server side (reaches every player with nothing installed on their side):** everything the map's scripts do with
  entities on the server: spawn points and spawners, interaction points and their types, doors and barriers, triggers,
  placed script models (a client receives the entity and shows the model, which must be in the map's zone),
  anything a script looks up by `targetname` or `script_noteworthy`. All of it was measured only on a dedicated server.
- **Needed on the client too:** anything the client loads from its own copy of the entity list. The loader reads the
  file on the client as well, so a client given the same file would see the same list; which classes a client really
  uses was not measured. Candidates are the client-side classes in the list (`client_trigger_occluder_audio`,
  `light_spot`, `audio_pa_speaker`). Treat a visual or audio change of that kind as unproven for players who do not
  have the file.
- A client that connects to a server does not receive the file from it. Distributing the file to players is the
  server's mod download, not this tool.

## Run live on 10 Nov 2026

Private headless dedicated server (one bot, no client), Spaceland, stock executable build of the day, entity file
installed with the runner's `-ServerCopy`. The census is the `ents` step of the test runner.

| Run | Result |
|---|---|
| Baseline, no file | the live counts equal the export for every value chosen: basketball hoop prefab (targetname `pf405_auto67`) 5, `bumper_car` 3, `gator_mouth` 1, `toy_yeti` 1, `trigger_damage` 13, `default_player_start` 4 (structs). Where the game differs from the export: of 3,695 entries 2,930 are script structs (not entities) and 765 are entities; 348 of those 765 are consumed at load and are never live (124 vehicle nodes, 220 node negotiation links, 3 jump nodes, the world entity); scripts spawn more `script_model` (115 in the file, 177 live) and `script_origin` (12, 15), and delete one brush model (92, 91); the whole live list is 754 or 755 (it moved by one between runs: something spawns or leaves at the time of the count) |
| 2. Round trip: `export`, then `write`, no patch | file accepted, no parser line, every one of the 29 counts equal to the baseline (754 for the whole list in both) |
| 2b. Same, `--readable` form plus two deliberate bad lines | counts equal to the baseline; the log shows `[map_ents parser] Failed to parse line 2 (this line is a canary)` and `Key 'zzz_canary_key' not found, on line 3` (three times each): the file was read and the quoted-name path works |
| 3. Real edit | remove the 5 entities of `pf405_auto67`: count 5 to 0. Add `overlay_probe` (script_model, `toy_zombies_plastic_egg`) at 467 3677 40: 0 to 1. Change `script_noteworthy` of one bumper car (index 1648) to `overlay_changed`: 0 to 1. The whole list 754 to 750. 6 of 6 expectations pass, the bot spawns, the plan reaches DONE, no script error line |

The removed entities are one basketball arcade game: a `trigger_multiple` (`hoop_trig`), two brush models
(`hoop_clip`, `rim`), a `script_origin` (`bball_sound_ent`) and the visible `script_model` `park_basketball_arcade_hoop`,
at about x -9754, y 288, z -1750. A player who goes there finds no hoop and no mini-game; the three other hoops
of the map are untouched. The game printed nothing about the entity file in the clean runs.

Not verified: a client reading the file (nothing was seen on screen); a player joining a server that has the file;
adding a trigger or brush entity; maps other than Spaceland (the loader file name for another map is built from the
same pattern and was not run); several files for several maps in one session.
