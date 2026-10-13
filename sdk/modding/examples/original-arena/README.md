# Original arena author plan

This source-only example describes an authored seven-box arena on `cp_zmb`:
`paris_original_arena`, `paris_original_arena_lod0`, one root (`tag_origin`),
one bone/LOD/surface, 168 vertices and 84 triangles. It uses an explicit existing
IW7 recipient material reference. It contains no BO3 geometry or textures.

The plan deliberately requires blocked `original-arena-display/1` and the
existing NCS capability. The historical 24-vertex cube proof does not qualify
this geometry. Every package hash/source and qualification record is pending.
The standalone `sdk_original_arena.gsc` is an author requirement, not a supplied
or generated runtime script. No FF or game asset is included.

Use the source package produced by `bootstrap.ps1`. World owns preparation and
staging through `tools-source/asset-bridge/world/original-arena/model_lab.py`.
Its material-bound source variant leaves the frozen null-material native plan
unchanged. Staging writes the existing `iw7.model-ff-plan/1`, with geometry
profile `iw7-original-arena-rigid-v1`, zone `paris_model_probe`, five payloads
and eight explicit validation inputs. No cube-only `prepare_ff` path is used.

```powershell
./sdk/modding/Creator.ps1 -Project ./sdk/modding/examples/original-arena `
  -Action Plan -Adapter OriginalArenaV1 -ModelSourceRoot <absolute-staged-source> `
  -ClientSource <exact-source> -ServerSource <exact-source> -Protocol 2 -Json
```

Plan takes stable snapshots of all eight source inputs before the World reader,
then checks their identities and bytes again. It reads no FF, tool executable,
stock or native state. The generic SDK contract can pass while Creator still
returns failure for missing client capability source proof. That refusal remains
explicit; source selection is not installed-client or rendering qualification.

After a separately reviewed display script and a restored successful ModelFF
build exist, `Bind` can record the existing `composition.json` with explicit
`ModelSourceRoot`, `BuildRoot` and `ReviewReference`. Its existing
`derived_receipt_sha256` field binds `evidence/arena-writer-source.json` for this
adapter. `Materialize` independently rechecks geometry, packed attributes,
inventory, build phases, restoration and script bytes through the same existing
workflow. Both Creator actions retain the compatibility refusal until actual
client capability evidence exists. Neither action launches the builder.

Direct library materialization produces a local candidate with incomplete
closure and all readiness/owner flags false. Recipient material, technique and
image closure, generated rawfile representation, GSC imports, client/server
linking and visible pixels still need qualification. A goal trigger is a volume;
solid collision/Havok/player movement and gameplay remain separate work. The
first runtime target is visible original geometry around a protected player.
