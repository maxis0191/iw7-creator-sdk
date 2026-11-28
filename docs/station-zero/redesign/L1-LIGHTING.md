# L1: the Arcade's light against stock (lighting worker L1, 28 Nov 2026)

DRAFT: filled step by step; the final table is at the end.

## Tools made for this lot
- `tools-source/iwzmap/station_zero/film/light_measure.py`: `measure` = LIGHTING-GAP section 0's numbers for any frame (p5, p50, p95, p99, share
  under 0.03, clipping, floor band; for shop-front cameras the ground patch, its blue / red, the front patch above it and ground / front).
  The front patch is rows 60 to 70 % of the middle half: that band reproduces the diagnosis's column (stock `shopfronts_2` 0.039 / b/r 0.87
  against 0.038 / 0.71; our pass-8 pink shop 0.033 / 0.19 against 0.033 / 0.20). `shoot` = one session: start, power on, 10 s, the cameras,
  variants synced into the same session (`--session`), stop; a variant whose sync or power failed is skipped, a stale or failed frame is
  renamed `.rejected` and never measured, and each variant's compile log is kept beside its frames.
- `light_variants.py`: variant documents (floor material, pool mode, pool intensity, pool geometry, `--lit` vision keys) built by the
  Arcade's own builder, nothing of the shell's files changed.

## Step 0: baseline (reproduced)
Document `C:\studio-data\sz\film\light\doc` (`film/arcade_doc.py`, all four goods), real `live power on`, 10 s, `--clean`, frames
`C:\studio-data\sz\film\light\s0_base\on\`, numbers `light\m_s0_base.json`. Pink shop ground 0.0146, b/r 0.134 (diagnosis 0.015 / 0.13);
Copy Stop 0.0133 / 0.33 (0.013 / 0.33). Stock in the same script: `shopfronts_2` ground 0.094 b/r 1.41, ground / front 2.38; `shopfronts_13`
0.057 / 3.48 / 2.58; subway (8) median p5 0.070, p50 0.170, p99 0.733, under 0.03 0.04 %, floor band 0.261.

## Step 1: E1 (session 1, `light\e1\shots`, the documents beside them)
Ground patch at the three front cameras (linear luminance; b/r; ground / front):

| variant | Hole Number Nine | Copy Stop | Needle Drop |
|---|---|---|---|
| baseline (all baked, quarry tile) | 0.0146 / 0.13 / 0.44 | 0.0133 / 0.33 / 0.09 | 0.0157 / 0.08 / 0.47 |
| B: pools runtime x1 (rows 4,000 to 5,500) | 0.0091 / 0.16 / 0.23 | 0.0085 / 0.39 / 0.05 | 0.0094 / 0.14 / 0.23 |
| B x0.3 | 0.0088 | 0.0083 | 0.0092 |
| B x3 (rows 12,000 to 16,500) | 0.0097 | 0.0092 | 0.0102 |
| A: stock `concrete_floor_polished_01_ssr`, pools baked | 0.0400 / 0.64 / 1.56 | 0.0361 / 1.10 / 0.26 | 0.0449 / 0.26 / 1.59 |
| C: A + runtime pools | 0.0228 / 0.69 / 0.77 | 0.0173 / 0.96 / 0.11 | 0.0235 / 0.54 / 0.71 |
| stock `shopfronts_2` / `_13` | 0.094 / 1.41 / 2.38 | 0.057 / 3.48 / 2.58 | |

Read: (1) the floor's colour (C4) is the largest single lever measured: a grey polished floor takes the same baked pool to 2.7 times the
ground light and to the pool's hue (pink b/r 0.13 -> 0.64); (2) runtime pools at stock-range rows (stock cp_disco spots: median 6,355, 90th
percentile 28,004, radius 270 to 450, `grammar\db\cp_disco.sqlite`) add almost nothing to the floor: a tenfold change of the row moves the
ground by 10 %. The only lit change of x3 against x0.3 (`e1\diff_hi_lo_*.png`) is a stripe on the Heel & Key shutter housing about 20 units
from its spot. (3) No mirror image of the fronts is visible in A's floor (frames `e1\shots\docA\on`); A0 (same family without `_sref0`)
separates the reflection from the albedo: session 2.

## W1: the light mode "runtime with baked bounce" (built, unit-proven)
- SDK `bake/layout_lights.py`: a layout light with `runtime: true, bake: 'bounce'` becomes a baker light with `direct: false`.
  `bake/lmbake.py`: such lights get their own `direct_light` call; their irradiance (`Ebounce`) is added to what surfaces throw in every
  bounce (`Lout`) and to what the light grid's cells see (`Lfinal`), and is left out of `B`, the direction image and the grid's delta term
  (`light_grid` receives the baked lights only). With no such light the baker's arithmetic is unchanged (`Ebounce` is 0).
  `blender/blend_core.py` (documents without a base) carries `bake: 'bounce'` into the layout record.
- Studio: `B.light(..., bake='bounce')` (implies `runtime`), `B.fixture(..., bake='bounce')`; `baselights.merge` writes BOTH the layout record
  and the `lights.txt` row on a base with darkness (a pure runtime light gets no record there, and the dark split zips the layout with the baker
  list, so the record must exist); a bounce light of group `power`/`flicker` on such a base is refused (its bounce would be baked into the dark
  state). `expand.py` carries the value; `loop.py` never makes such a light a live op (its bounce is in the lightmap).
  `lightwhy` (`studio light`) counts it once (as baked, in baker units): no double count.
- Tests: SDK `tests/test_lmbake_light.py::test_runtime_light_bounce_only` (one room: B under the lamp 27.35 baked, 0.000 bounce-only; the wall's
  A 0.921 both; the grid's c0 sum 51.2 against 12.95); Studio `tests/test_bounce_bake.py` (the document path through `baselights.merge` and the
  SDK's baker: B 25.07 -> 0.000, A 0.845 both) and three merge tests in `tests/test_baselights.py`.
- Records: `studio check` `build.networked_entities` 494 before and 494 after with 17 key lights in bounce mode (unnamed rows take static
  template slots). Light rows 5 -> 22 (cap 256); voxel light entries 13 -> 371 (cap 65,535), predicted by `studio check`.

## C2 notes for the lead
- Route a (`_sref0` base with OUR floor pictures): `concrete_floor_polished_01_ssr` (techset `w_l_sm_replace_i0c0s0o0n0p0_sref0`, constants
  `colorTint`, `reflectionRa`) reads semantic 14 (`_packed_cs`) and 15 (`_packed_nog`), the same semantics as our `concrete_01` route. Our
  packed 15 image (`port/matconv.pack_normal_gloss`) writes R gloss, G/A octahedral normal and B = 1.0, which is the occlusion channel of the
  `_nog` layout: the pictures fit unchanged. Studio refuses the base today (`materials.BASES`). The patch (Studio `studio/materials.py`, not in
  this lot): add `'concrete_floor_polished_01_ssr': {'route': 'ext', 'normal': True, 'gloss': True}` to `BASES`, and in `entry()` write
  `e['ext'] = {'base': base, ...}` instead of `EXT_BASE`; the document's `settings.build.kit` must bring the material (`fixtures.use_kit` does
  for a placed model only: add `cp_disco:w/concrete_floor_polished_01_ssr` to the kit's materials).
- Route d needs no compiler change: the probe fill runs only when `IWZ_PROBES` is `neutral` (`iwzmap.cpp:677-678`); a document's
  `settings.build` `{"compiler": {"env": {"IWZ_PROBES": "template"}}}` merges over the base's recipe (checked: the emitted `build.json` carries
  it) and leaves the template's captured cubes in place.
