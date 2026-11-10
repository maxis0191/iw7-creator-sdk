# World patch: change the props of a studio-made map

`tools-source/worldkit/iw7_worldpatch.py` changes the placed props (static models) of one of the game's own maps.
It works on a **copy** of the map's render world file from a dump (see [WORLDKIT](WORLDKIT.md)): it never touches the
dump, the game or the asset tool. What it writes is the input of a zone build; building the zone, loading it and
proving it in the game is the server repository's `ops/worldpatch/Invoke-WorldPatch.ps1` (its `docs/WORLDPATCH.md`
says what is proven in the game and what is not).

Standard library only. Tests use a synthetic world (`tests/test_worldpatch.py`, 20 tests).

## A patch

```json
{
 "schema": "iw7.worldpatch/1",
 "map": "cp_zmb",
 "fingerprint": "<SHA-256 of the render world file the patch was written against>",
 "ops": [
  {"op": "remove", "box": [-133, 3077, -200, 1067, 4277, 800], "why": "empty the plaza"},
  {"op": "remove", "model": "zmb_bench_*"},
  {"op": "remove", "index": [3086], "collision": "remove"},
  {"op": "restore", "index": [120]},
  {"op": "move", "index": 3085, "to": [467, 3777, 0], "yaw": 90}
 ]
}
```

| Operation | Selects | Writes |
| --- | --- | --- |
| `remove` | `box` (origin inside; corner order free), `model` (name pattern, `*` and `?`, case kept), `index` (one or a list); several selectors in one operation are combined with "and" | scale 0 in the prop's draw record. Measured in the running game: a prop with scale 0 is not drawn, and nothing else of the record needs to change |
| `remove` with `"collision": "remove"` | the same | also takes the prop out of the collision file's list of colliding props (`.colmap`), so the patched collision file is written next to the render world file |
| `restore` | the same | undoes an earlier `remove` of the same patch (operations apply in the order written) |
| `move` | one `index` | new origin; optional `yaw` (degrees added about the vertical axis; quarter turns exact) and `scale`. The stored bounds and lighting origin move by the same vector. A moved prop is no longer removed |

The `fingerprint` ties a patch to one dump: a patch for another version of the map is refused, because indexes and
positions would mean other props.

## Commands

```
python -B tools-source/worldkit/iw7_worldpatch.py new    --db <worldkit db> [--out patch.json]
python -B tools-source/worldkit/iw7_worldpatch.py plan   --patch patch.json --db <worldkit db> [--out plan.json] [--json]
python -B tools-source/worldkit/iw7_worldpatch.py apply  --patch patch.json --db <worldkit db> --dump <dump folder> --out <new folder> [--json]
python -B tools-source/worldkit/iw7_worldpatch.py verify --plan <plan.json> --dump <dump folder> --out <folder> [--json]
```

* `new` prints an empty patch that carries the map name and the fingerprint of a database.
* `plan` resolves the patch against the database into a plan: one entry per changed prop (index, model, where it
  stands, what changes), ascending index, and the number of props each operation matched. The same patch and
  database always give the same plan.
* `apply` writes `<out>/<same relative name as in the dump>` (and the collision file when asked) plus
  `<out>/worldpatch-plan.json`, then verifies. It refuses a dump whose file is not the one the database was built
  from, and refuses to write into the dump folder.
* `verify` repeats the verification on files written earlier.

Every failure is exit code 2 with one sentence on stderr.

## What "verified" means

After writing, the tool parses the patched file again with the worldkit reader (which must reach the exact last
byte), and compares it with the source: the size is equal, every planned field holds the planned value, and
**every other byte is equal to the source**. It prints the number of records parsed, fields written, bytes
changed, and props with scale 0 before and after. For the collision file: the new list is the old list without
the removed props, the prop records and everything outside the list are equal to the source.

Measured on the Spaceland dump: a box over the player start changes 503 of 17,010 props, 1,110 bytes of a
100,110,337 byte file, in 0.9 s including verification; with collision removal the collision file shrinks by
2,012 bytes (503 indexes).

## How the collision file names props

The collision file lists every placed prop again (model, origin, inverse scaled axis) and then the indexes of the
props that collide (on Spaceland: all 17,010). Its order is **not** the render world's order, so the tool matches
each prop by model name, origin (within 0.05 units) and nearest axis; a prop with no match is an error, not a
guess. 61 Spaceland props share model and origin with another one; the axis decides between them.

## Limits

* Props only. World surfaces (walls, floors), lights, entities, navigation and the baked lighting are not
  changed: a removed prop leaves its baked shadow and its light where they were.
* `move` changes where a prop is drawn, not when: the game decides visibility with data computed for the old
  place (see the server document for what was measured). The collision of a moved prop stays at the old place
  unless it is removed.
* No `add` yet: the file's record count is never changed. Moving a prop that is not needed elsewhere is the way
  to place something new today.
* Proven on one real map (Spaceland) and the synthetic world.
