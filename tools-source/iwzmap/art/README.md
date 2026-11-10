# iwzmap/art: 2D art generators for generated IW7 zombies maps (Station Zero)

The generators are deterministic and seeded: re-running gives the same bytes. Python 3 with numpy, scipy and Pillow;
fonts come from `C:\Windows\Fonts` (override with `IWZ_FONT_DIR`). Run from `tools-source/iwzmap` as modules.

| module | what |
|---|---|
| `noise.py` | Tileable FFT spectral noise, fBm, domain warp, wrap-aware blobs, gravity flow streaks, border falloff, a seam metric |
| `masks.py` | Grime mask for floors (tileable multiply), junction grime strip, water streak, sign grime overlay, feathered blood and grime decals |
| `paper.py` | `Doc`: ink layers typeset from real fonts at 3x, composited by multiply onto synthesized paper. Ageing: yellowing, folds, water stains, foxing, grime, handling dirt, torn edges, tape, staples, photocopy, halftone |
| `blood.py` | Four blood decals with distinct physics: hand smear, body drag, impact spatter, dried pool |
| `boards.py` | Stopped station clock (with glass cracks), split-flap departure board, signal and evacuation diagram (from level coordinates) |
| `notices.py` | Layered torn notices, evacuation/quarantine order, generator lock-out with shift roster, missing-person flyers, cracked lit ad panel, film poster composition with roundel paint-over |
| `age.py` | Ages a folder of `*_c.tga` signs with the overlay synthesized at each sign's own size |
| `texio.py` | Writes `<name>.png` + `<name>_c.tga` (32-bit, the shipped path) + `<name>_c.dds` (RGBA8 with a full mip chain, gamma-aware, premultiplied) |
| `preview.py` | Composites RGBA/multiply assets over tile, concrete or plate for review |
| `make_station_zero_art.py` | Builds all g25 art requests and `manifest.json` (method, sha256, suggested base material) |
| `test_art.py` | Self-test: determinism, tiling, zero-alpha borders, DDS layout, board copy |

```
python -m art.make_station_zero_art <out> <selected model images dir> [--only a,b] [--signs <signs dir>]
python -m art.test_art
python -m art.age <signs dir> <out dir> [strength]
```

Rules this code follows:
- Legible text is always typeset, never generated.
- Model images (the `imagegen` skill) are only used for painterly content (snapshot portraits, an ad illustration,
  a poster painting). Prompts and rejects are logged in the stage folder: `art/imagegen-log.md`.
- Decals keep alpha 0 on the border (feathered).
- Tiling masks pass `noise.tile_seam_error` close to 1.

Material bases for drop-in: see `art/NOTES.md` in the stage folder. Opaque art uses `zombies_theater_poster01`.
Alpha decals use `wall_stain_01_dec` (w_l_sm_ndw_blend_i0c0). The multiply mask uses `dirt_water_stain_01`.
