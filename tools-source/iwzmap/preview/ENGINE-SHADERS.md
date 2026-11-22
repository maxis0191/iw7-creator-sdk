# What the engine shaders do (read from a stock cp_zmb RenderDoc capture, offline)

Capture `IW7-Runtime/tf9/gpu-pass-base-L1/run1/frame_frame26095.rdc` (1280 x 720, stock cp_zmb), replayed offline by `rdoc_inspect.py`
(`python -B rdoc_run.py <request.json>`; qrenderdoc, no game). Shader names are the first 12 characters of the SHA-256 of the bytecode
(`gpu_passes.py` convention). Instruction numbers are the line numbers of RenderDoc's DXBC disassembly of that shader
(`shader_<hash>_ps.txt`, written by the inspector). A second capture, `iwz-local-rd3/frame_frame12490.rdc` (older generated map, 2560 x 1440), uses
the same shader hashes for the post passes and the same curve constants.

## 1. Post chain of a frame (events of the stock capture)

| event | pass | shader | what |
|---|---|---|---|
| 10462 .. 10489 | 64 x 360, 64 x 36 | `bf6635500453`, `fdd51fb79563` | max velocity tiles of the 640 x 360 velocity target |
| 10510 | HDR 1280 x 720 -> 83362 | `44119cb7a0f7` | motion blur along the velocity; identity when the velocity is 0 (measured: mean difference to the input 3.4e-05) |
| 10531 .. 10854 | bloom pyramid 1280 x 720 down to 5 x 2 and back up to 320 x 180 (`3f1e359ad01a`, `d1ecddf12941`, `1f9197ba6e44`), exposure compute | | the exposure compute (`c672eba77dc0`, `974052551c85`, `60925f7fd3f3`; buffers "Tonemapping exposure info / reduction buffer") only writes a buffer; the tone pass below does not read it |
| 10875 | tone map -> 83444 (R8G8B8A8) | `8881bdf370aa` | formula below |
| 10895 | anti aliasing and noise -> swapchain | `97833bfe6721` | FXAA (contrast thresholds 0.166 and 0.0312, `gather4`, lines 0-198) then `rgb += rgb * noise * (1 - L^2) * cb2[2].y`, cb2[2].y = 0.08 (lines 199-212); measured final vs tone map output: mean 1.15 levels |

### Tone map (`8881bdf370aa`, event 10875), measured on this capture

    c = cb2[4].y * scene + cb2[4].x * bloom(bilinear 320 x 180 -> full)                (lines 1-4; 0.9 and 0.1)
    per channel: set = (c < cb13[0].x) ? cb13[2] : cb13[1]                             (lines 5-13)
                 t = saturate((set.x * c + set.z) / (set.y * c + set.w))
    m = saturate(M . t)  with M = cb2[1..3] (identity here)                            (lines 14-16)
    s = max(1.055 * m ^ (1/2.4) - 0.055, 0)                                           (lines 17-21)
    out = LUT3D(s * 31/32 + 1/64)  (32^3 R8G8B8A8, trilinear, texture t2, id 1258)     (lines 22-24)
    out.a = dot(out.rgb, (0.2126, 0.7152, 0.0722))                                     (lines 25-27, used by FXAA)

Constants of the capture: cb13[0].x = 0.071506, cb13[1] = (27.888254, 27.613163, -0.5121, 4.523621) (shoulder: A, C, B, D),
cb13[2] = (6.124092, -1.118782, -0.0, 2.0) (toe), cb2[4] = (0.1, 0.9). The two curves meet at c = 0.071506 (0.2281 on both sides).
The same cb13[1], cb13[2] were read in the generated map capture (rd3). `cb13[0].w` and `cb13[3].w` differ between the captures (3.745 / 7.657 and
0.0043 / 8.5e-05) but this shader does not read them. The LUT is saved as `engine_tonemap_lut32.bin` (131072 bytes, index [b][g][r], RGBA8); it is the vision's colour grade.

Verification (`iwz_tonemap.py`, numpy, from the dumped targets 83362 and 83390 and the LUT): per pixel absolute error against the engine's 83444, in
8 bit levels, over all 921,600 pixels: mean 0.248, 99th percentile 0.523, maximum 0.608, no pixel above 1 level. Without the bloom term the mean is 2.30.

**There is no exposure multiply in this pass or in the world shader below.** The scene is exposed before this point: the world shader adds
lightmap texels and light colours as they are (the sun colour constant is 0.021, 0.046, 0.143). The exposure value is computed on the GPU
(`Tonemap Exposure ...` compute passes) and reaches the shaders only through CPU constants (dynamic light colours: dvars `r_lightIntensityAutoScale`,
`...Min`, `...Max`, "Dynamic light intensity global scale for tonemapping compensation", registered in `sub_140DF62C0`). Lightmap texels and the tone
curve have no per frame exposure in them.

## 2. Lightmapped world pixel shader `52036ba80dda` (events 5942 ...; t0 1024 BC7, t2 4096 x 2048 BC4, t3 4096 x 4096 BC6, t4 4096 x 2048 R8G8, t5 BC7)

Per pixel, in code order:

* **Albedo** (t0, `v1.xy`, lines 8-16): `c = rgb^2` (line 9: read as plain UNORM and squared, a gamma 2.0 decode, not the sRGB curve).
  `m = saturate(a - 0.1) * 1.1111` (alpha is a metalness like term); `diffuse = c * (1 - m) * cb3[0].xyz` (lines 15, 18; `cb3[0]` is a per draw colour
  tint, 0.347, 0.429, 0.651 on that draw); specular colour `F0 = m * c + min(a, 0.1)` (lines 12, 16).
* **Normal and gloss** (t5, lines 17-38): channel R = gloss, channels G and A = a two component packed normal
  (`x = (G' + A') / 2, y = (G' - A') / 2`, `G' = 2G - 1`, `z = max(1 - |x| - |y|, 0)`, normalised, rotated by the tangent frame `v2`, `v3`).
  `g = 1 - sqrt(1 - R)` (lines 24-26). **R is gloss, not occlusion** (it feeds the specular exponent `2 / (exp(20 g) + 2)`, lines 44-47, and the probe mip
  `5 - 5 g`, line 92); channel B is not read by this shader. This shader has no material occlusion map: the only occlusion terms are the lightmap and the screen space ssao.
* **Lightmap** (lines 60-83): `A = t3(u, v/2).rgb`, `B = t3(u, v/2 + 0.5).rgb` (one atlas, A on top, B below; `v1.zw` is the lightmap uv);
  `D = t4(u, v).rg` decoded as `p = 2 rg - 1; d = ((p.x + p.y)/2, (p.x - p.y)/2, 1 - |d.x| - |d.y|)`, normalised, turned into the world by the tangent frame
  (lines 64-80). `ssao = t14(screen)` (line 39, 640 x 360 R8).
  **`E = A + saturate(dot(N, D)) * ssao * B`** (lines 81-83): the same as `bake/lm_decode.py` with the ssao factor on B.
* **Reflection probes** (lines 85-229, only when `saturate(20 g - 4) > 0`, cb2[1] = (20, -4)): probes come from a clustered list (`t31`, structured, stride 128, box and parallax
  correction; `t32` raw bit masks). Each probe's cube (t1, `texturecubearray`, 128 x 128 BC6) is sampled along the box corrected reflection vector (lines 133-195) at mip `5 (1 - g)` and multiplied by a
  relight ratio `clamp(lum(E at the reflection direction) / SH(probe, direction), cb2[20].x, cb2[20].y)` (lines 196-213; SH = the probe's order 1 coefficients in `t33`,
  constants 0.282095 and 0.325735; cb2[20] = (0, 3)); weights accumulate to 1 (lines 217-220).
* **Combine** (lines 230-254): `ind = E + saturate(20 g - 4) * (probe - E)` (lines 230-232); the split sum environment BRDF `t11(NdotV * 0.984 + 0.0078, g)` gives scale and bias of the
  specular colour (lines 238-240), `spec = F0 * s + b`, `ind *= spec` (line 244); the diffuse term is `diffuse * Fd * (1 - max(spec)) * E` with `Fd` a Disney style retro reflection factor (lines 245-254).
  For a rough surface (g <= 0.2) the colour is `diffuse * (1 - max spec) * Fd * E`, E the lightmap.
* **Sun** (lines 255-317, only when `cb2[12].w != 0`): shadow mask `t2` (lightmap uv) and `t7`, direction `cb2[12].xyz`, colour `cb2[13].xyz`, GGX plus diffuse.
* **Runtime ("primary") lights** (lines 321-554): a loop over the clusters of the pixel: tile from the screen position (8 x 8 pixels, `cb2[15].xy`, lines 323-329), depth bin from `v0.w` (`>> 5`, `t37`,
  lines 330-346), per tile bit masks in `t35` (lines 358-366), light records in `t24` (structured, stride 88).
  - record: `+0` colour rgb (intensity already applied), `+16` axis xyz, `+28` flags (bits 8-9 == 2: spot) and tube vector (`+32..40`), `+44` source size, `+48` position (camera relative),
    `+60` 1 / radius, `+64` cone scale and bias, `+76` radial scale and angular lookup scale / bias; shadow index in the low byte of the word at `+28` of the second load
    (`!= 255`: shadow map array `t6` through the `t25` matrices, lines 413-435).
  - closest point on the tube segment (lines 383-388), `d` = distance to it (line 391).
  - angular profile: `cos = dot(axis, dir)`, `s2 = 1 - cos^2`, coordinate `(cos > 0 ? s2/2 : 1 - s2/2) * scale + bias`, `lut = t10(coord)` (256 x 1 R8) (lines 394-401).
  - cone (spots, lines 402-403): `saturate(cos * cone.x + cone.y)`.
  - **radial falloff: `a = saturate(k * (1 - d/R)) * cone * lut`, then `a = a^2 (3 - 2a)`** (lines 405-410), `k` = record `+76`, `R = 1 / (record +60)`. The light reaches exactly R and is a smoothstep, not inverse square.
  - optional exponential shadow map (lines 428-435); the sphere light illuminance (horizon wrapped N.L with the source size, lines 464-480) times `a`; GGX and Fresnel specular (lines 481-547):
    `out += F * color * a * spec + diffuse * (1 - maxcomp(F)) * color * a * illum` (lines 543-548).
  - The unit of the record colour is what the CPU makes of (map light colour x intensity x auto exposure scale); it goes straight into the HDR target. The shader does not say more.
* **Fog and volume** (lines 555-580): `lit = lit * T + fogcolor * (1 - T)` (exponential terms of `cb2[2..6]`), then `out = lit * t13.w + t12` (froxel volume transmittance and in-scatter, 3D textures 107 x 60 x N),
  `o0 = min(out, 32255)` (line 581).

## 3. What this means for the preview

* The HDR value of a lightmapped, rough surface is `diffuse_albedo * (1 - max spec) * Fd * E`, no exposure. The old per frame exposure and gamma were fitting a difference of power state.
* The tone is exactly section 1. The curve constants of the custom vision of the map are in no capture on disk; the stock constants are used.
* Runtime lights: section 2 gives the falloff; only the colour unit is open.

## 4. Runtime light limits and the dark room behind the generator room door (22 Nov 2026)

Question: in `lit_generator_room_1` the control room seen through the open door is dark while its bank is on. Is there a per view limit on runtime lights?

Engine limits found (engine map `iw7-engine-map.sqlite`, function `sub_140DF62C0` = dvar registration, `Dvar_RegisterInt` calls):

| limit | value | where |
|---|---|---|
| `r_primaryOmniLightLimit` "Maximum number of primary omni lights drawn per pixel simultaneously" | default 64 (0x40) | `140DF8CAD` .. `140DF8CD9` |
| `r_primarySpotLightLimit` (same, spot) | default 64 | `140DF8CE0` .. `140DF8D0C` |
| `r_dynamicOmniLightLimit`, `r_dynamicSpotLightLimit` "Maximum number of dynamic omni / spot lights drawn simultaneously" | default 32 each (0x20) | `140DF8D13`, `140DF8D46` |
| frustum light array (`t24` of the world shader) | 256 records of 88 bytes (`mov ecx, 0x100`, `edx = 0x58`) | `sub_1400C4950` at `1400C4BE4` |
| z bin buffer (`t37`) | 0x8000 entries | `sub_1400C4950` at `1400C4C00` |
| scriptable primary light slots of a map | the compiler's range 943 .. 1038 (96 lights) | darkness NOTES |

The 72 named lights of g27r are below every one of these. Measured on the preview's geometry of that view (`iwz_lights.region_report`): the largest number of
lights whose radius covers one pixel anywhere in `lit_generator_room_1` is **7** (mean 4.4), against a per pixel limit of 64. In the doorway region (rows 150-340,
columns 290-440, world x 3125 .. 3597, y 3179 .. 3996, z -322 .. -34) only five lights reach any pixel at all: control room `(3100, 3300, -54)` reaches 27 % of the
region's pixels with a mean weight a * N.L of 0.027, control room `(3450, 3300, -54)` 10 % with 0.010, two generator room lights and one shadowed control room light
`(2760, 3560, -54)` about 2 % with 0.000. The other control room lights are farther than their 518 unit radius from what is visible
through the door (floor at z -322 is 268 units under the lamps, and the falloff is a smoothstep that is 0 at the radius). The engine frame shows the room drawn and dim,
not black (the floor, ceiling fixtures and a box are visible). Verdict: **no engine limit is hit**; the room is dim because few lamps reach the surfaces seen through
the door and their smoothstep weight there is small, relative to a frame exposed for the bright generator room. The preview reproduces it (the room is dark in both).
