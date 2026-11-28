"""light_rules: the lighting rules of the Station Zero rebuild that more than one builder uses (worker L1, 28 Nov 2026; LIGHTING-GAP W2).

LIT_VISION: the keys set over the `--lit` vision of the darkness recipe, the PROPOSED lit vision for the whole map (the Arcade uses it; other
zones are their owners'). Chosen from a sweep of one-document sessions at five fixed cameras (docs/station-zero/redesign/L1-LIGHTING.md, W2):
  exposure -2.5 (as before)  p5 0.005, up to 18.7 % of pixels under 0.03, p99 0.56
  -1.5                        p5 0.031, up to 6.9 %, p99 0.72
  -1.0                        p5 0.040, up to 3.2 %, p99 0.78, clipping 0.15 % (the fronts start to read bright: a showroom risk)
  -1.25 is taken between them. Fog at -1.25: 0.5 / density 150 moved nothing; 0.95 / 30 lifts the blacks (p5 0.037 to 0.066, 0 to 2.1 %
  under 0.03, p99 0.70 to 0.87, clipping 0.11 %); 0.95 / 3000 lowers them (a lower density is a denser fog). Taken: 0.95 / 30. Veil 0.04 is stock cp_disco's measured bloom (LIGHTING-GAP C3). Fog 0.5 at density 150 and the volumetric keys
  changed the frames by less than the sweep's noise with these lights (no haze seen with the key lights at 27,000 a unit); they are kept low.
"""
LIT_VISION = {
    'veilStrength': '0.04',
    'fogMaxOpacity': '0.95',
    'fogDensity': '30',
    'tonemapAutoExposureAdjust': '-1.25',
    'volumetricAmbientBrightness': '0.2',
    'volumetricAirDensity': '0.02',
    'volumetricSpotBrightness': '0.15',
    # L2 (28 Nov): stock cp_disco's colour cast (R2-PARITY section 15: the fog colour and the sky terms are what turned our floor blue-green). The hue and the sky
    # terms are stock's; the fog colour's intensity is NOT stock's 0.1: our fog (opacity 0.95, density 30) is what lifts the blacks (L1 W2), and 0.1 of a warm
    # fog is 2.7 times less light than the 1.25 of the blue-green one, so the intensity is set to give the SAME fog luminance (0.147 x 1.25 = 0.67 x 0.27).
    'fogColor': '0.7490196 0.6509804 0.5215687',
    'fogColorIntensity': '0.27',
    'fogSkyIntensity': '1',
    'fogSkyMin': '0',
    'fogSkyMax': '80',
    'r_hdrSkyIntensity': '0.15',
}


def apply_lit(settings, keys=None):
    """set `keys` (default LIT_VISION) over the `--lit` argument of settings['build']['darkness']['args'] -> the new argument"""
    args = settings['build']['darkness']['args']
    i = args.index('--lit') + 1
    kv = dict(x.split('=', 1) for x in args[i].split(';') if x)
    kv.update(keys or LIT_VISION)
    args[i] = ';'.join('%s=%s' % (k, v) for k, v in kv.items())
    return args[i]
