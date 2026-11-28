# C1: the control room and three pipeline checks (worker C1, 28 Nov 2026)

DRAFT: written while the bakes and sessions run; the answer and the pairs are filled in when the frames exist.

## Established before any frame [m = measured, r = read in code]

- **Stock pose and field of view [m].** The stock reference sidecars carry the engine's own projection of 320 world points. A least-squares
  camera fit gives every frame exactly: eye = feet + 60.0 (z 346.12 on the east platform), the sidecar's yaw and pitch, horizontal fov
  **80.69** (cg_fov 65 at 16:9), max error 0.001 px. `live shot` labels its frames fov 80.0 (`studio/live.py:122`, a label, not a setting);
  our frames are checked by registration against stock instead (`film/control_compare.py`: phase correlation of edge maps).
- **SSAO is not running on the client cells, for stock or for us [m].** Offline RenderDoc replay (`control\ao\rdoc_ssao.py`): the
  640 x 360 R8 occlusion target of stock cp_disco at the subway_east_1 eye (`captures\lightgap_cp_disco\cam1.rdc`) is 255 at every
  pixel (read by 522 pixel draws, written once); our Arcade's (`captures\arcade_um6\cam1.rdc`) is 99.97 % at 255. The map vision sets
  `r_ssaoStrength 2`; the client dvar is `r_ssao` (a server cell's config_mp.cfg writes `seta r_ssao "MDAO"`).
- **Props of other zones throw no baked shadow [m].** Studio gives the baker one dump root for prop bounds, the template's
  (`studio/bake.py:116-117`). On the control emit 607 of 894 static models (147 models) are `unknown` to `bake/occluders.py`: 285
  occluder boxes; in the lifted station 92 of 537 props. With the document's kit dump roots: 824 boxes, 503 in the station.
  Every world surface (render-only boxes, meshes, signs, decals) is baked and occludes (`lmbake.build_charts`: only sky is skipped).
- **Texel [r].** One global texel; the atlas is capped at 4096 x 4096 (`lmbake.py:262`). Station: 1,585,343 texels at 8 on 4096 x 2048
  (bake 357 s). Texel 4 is about 6.3 M (fits); texel 2 about 25 M does not fit for the whole document, and no region option exists.
- **What the lift carries and loses [m].** Box stock x -150..1260, y 1950..3400, z 230..760 (both platforms, the track, the stair feet,
  the mezzanine edge), placed by a pure translation (-7850, -6750, -400) (corrected by R2: the first placement was moved, see `control_room.OFFSET`). 79,838 render triangles with shipped materials and UVs, 19,690
  collision triangles, 537 static props (the subway car bodies included), 29 stock spots transcribed (below). Lost by the route:
  blend materials (187 of them, **32.7 % of the lifted surface area**, the platform floor among them: `*622n_89_91_282n` drawn as its base
  `concrete_bare_patches_clean_03`): their layer mix of dirt, wet and damage is gone; `wc/` decal and glass materials (blood smears,
  rustic wall decal, chain-link fence, cracked glass: 212 triangles) are not drawn; `caulk_shadow` (1,044 triangles, stock's invisible
  shadow casters) not drawn; nothing outside the box (the tunnel north of y 3400, the street above z 760); no effects, no sound, the
  base's sky; stock's 87 captured probes are not carried (our room gets the neutral cube fill); stock's lightmap and grid are not used.
- **Lights [m].** 29 stock spots (all `light_point_linear`); colour / peak, intensity = peak / 27,000 (L1's measured row scale), beam =
  minus the stock dir, half cones from cosHalfFov, stock radius, shadow flag from canUseShadowMap (26 of 29). The emitted lights.txt rows
  equal stock: row 26,087.4 for stock 26,086.9, the same radius, cone 90, angles = the stock dir. Not carried: isVolumetric (259 of
  cp_disco's spots; our compiler writes 0), shadow softness / bias, falloff, bulb size. Studio's prefab light route is wrong (TOOL-FAULTS C1-1).
