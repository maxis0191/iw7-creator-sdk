# iwzmap asset catalog

Finds and validates stock IW7 assets for code-built zombies maps (`iwzmap`), from ZoneTool dumps, and
proves each picked model in the engine with a preview frame.

| File | Role |
| --- | --- |
| `ztdump.py` | readers for ZoneTool's binary dump format (`assetmanager::dumper` tokens): XModel `.xmb`, XModelSurfs `.xsb` (all surfaces, vertices, triangles, collision trees, subdiv, SH-probe data), GfxImage `.iw7Image` (incl. `XStreamFile` pak index/size), material `.json` |
| `iwzcat.py` | `build` a catalog JSON (one row per model), `query` it, list `fx` names of a zone with a category |
| `iwzmap_preview.gsc` | preview booth fixture for the local private runner: one `script_model` at a time in front of a held camera, engine bounds via `getpointinbounds`, `capture_frame` per model and background frames |
| `Run-Preview.ps1` | runs the booth on a stock map (or a usermap) through `iw7-paris-server/ops/iwzmap/Test-IWZMapLocal.ps1`, retrying while the machine resource lease is busy |
| `preview_analyze.py` | per frame: engine bounds vs catalog bounds, silhouette (background difference) vs projected LOD0 vertices (IoU), texture statistics (not black, not a two-tone checker); crops and contact sheets |
| `test_catalog.py` | unit tests on synthetic dumps (`python -I test_catalog.py`) |

## Dumps

```powershell
# from a ZoneTool work dir (zonetool.exe + iw7_ship.exe + hard links of the game .ff/.pak in zone\), under the lease
zonetool.exe -headless -unbuffered-io -dumpzonetypes cp_disco xmodel,xmodelsurfs,image
zonetool.exe -headless -unbuffered-io -dumpzonetypes techsets_cp_disco material   # IW7 materials live in techsets_<zone>
```

Facts the tool relies on (checked on the dumps, see the stage-2 asset report):

- `.xmb` = `dump_single(XModel)` (0x2E0 bytes) + name + bone names + arrays + material/LOD/physics asset names.
  Header `bounds` (midPoint/halfSize at +44) equals the LOD0 vertex bounds for every model of cp_zmb, cp_disco,
  cp_town, cp_final and cp_rave (vertices are model space, also for multi-bone models).
- `.xsb` per surface: verts (32 B), tris (6 B), rigid vert lists (+ collision tree 56 B, leafs 2 B, nodes 16 B),
  4 raws, subdiv, then SH-probe simplex data: 32 B/vert if flags&0x500==0x500, 8 B if flags&0x100, 24 B if flags&0x400.
- `.iw7Image`: GfxImage (0x70), name, pixel data only if the header pointer is set, then 4 `XStreamFile`
  (offset, end, `fileIndex` -> `imagefile<N>.pak`) when streamed.

## Catalog

```
python -I iwzcat.py build --zone cp_zmb=<dump>;<techsets_cp_zmb dump>;<techsets_global_cp dump> \
                          --zone cp_disco=<dump>;<techsets_cp_disco dump>;... --always-loaded cp_zmb \
                          --base-paks <game dir> --out catalog.json
python -I iwzcat.py query catalog.json --category pipe --zone cp_disco
python -I iwzcat.py fx --zone cp_disco=<dump> --category dust
```

Row fields: `name`, `zones`, `category` (name-based guess), `bounds`, `size`, `radius`, `vertBounds`,
`boundsMaxDiff`, `lods[]` (dist, surfs asset, verts, tris, materials), `materials[]` (techset, images),
`collision` (collSurfs, physicsAsset, Havok LOD data size/file), `numBones`, `cost` (surface bytes, embedded
image bytes, streamed bytes per `imagefile<N>.pak` and whether the base game ships that pak, missing images),
`inAlwaysLoadedOrTemplate`.

## Previews

```powershell
.\Run-Preview.ps1 -Map cp_disco -Models (Get-Content cand.txt) -Cam '0,0,1200,0,-5,rel' -OutputRoot <fresh dir>
python -I preview_analyze.py --run <dir> --catalog catalog.json --dump cp_disco=<dump> --out <dir>\analysis
```

The booth needs only the stock map that already holds the models (no build). Camera `rel` coordinates are
relative to the player spawn. A frame passes when the engine bounds equal the catalog bounds (<= 0.6 unit),
the silhouette box matches the projected LOD0 vertex box (IoU >= 0.7) and the masked pixels are lit and textured.
