# L1: the Arcade's light against stock (lighting worker L1, 28 Nov 2026)

DRAFT: filled step by step; the final table is at the end.

## Tools made for this lot
- `tools-source/iwzmap/station_zero/film/light_measure.py`: `measure` = LIGHTING-GAP section 0's numbers for any frame (p5, p50, p95, p99, share
  under 0.03, clipping, floor band; for shop-front cameras the ground patch, its blue / red, the front patch above it and ground / front).
  The front patch is rows 60 to 70 % of the middle half: that band reproduces the diagnosis's column (stock `shopfronts_2` 0.039 / b/r 0.87
  against 0.038 / 0.71; our pass-8 pink shop 0.033 / 0.19 against 0.033 / 0.20). `shoot` = one session: start, power on, 10 s, the cameras,
  variants synced into the same session (`--session`), stop; a variant whose sync or power failed is skipped and a stale or failed frame is
  renamed `.rejected`, never measured.
- `light_variants.py`: variant documents (floor material, pool mode, pool intensity, pool geometry, `--lit` vision keys) built by the
  Arcade's own builder, nothing of the shell's files changed.
