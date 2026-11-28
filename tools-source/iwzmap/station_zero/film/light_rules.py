"""light_rules: the lighting rules of the Station Zero rebuild that more than one builder uses (worker L1, 28 Nov 2026; LIGHTING-GAP W2).

LIT_VISION: the keys set over the `--lit` vision of the darkness recipe, the PROPOSED lit vision for the whole map (the Arcade uses it; other
zones are their owners'). Chosen from a sweep of one-document sessions at five fixed cameras (docs/station-zero/redesign/L1-LIGHTING.md, W2):
  exposure -2.5 (as before)  p5 0.005, up to 18.7 % of pixels under 0.03, p99 0.56
  -1.5                        p5 0.031, up to 6.9 %, p99 0.72
  -1.0                        p5 0.040, up to 3.2 %, p99 0.78, clipping 0.15 % (the fronts start to read bright: a showroom risk)
  -1.25 is taken between them. Veil 0.04 is stock cp_disco's measured bloom (LIGHTING-GAP C3). Fog 0.5 at density 150 and the volumetric keys
  changed the frames by less than the sweep's noise with these lights (no haze seen with the key lights at 27,000 a unit); they are kept low.
"""
LIT_VISION = {
    'veilStrength': '0.04',
    'fogMaxOpacity': '0.5',
    'fogDensity': '150',
    'tonemapAutoExposureAdjust': '-1.25',
    'volumetricAmbientBrightness': '0.2',
    'volumetricAirDensity': '0.02',
    'volumetricSpotBrightness': '0.15',
}


def apply_lit(settings, keys=None):
    """set `keys` (default LIT_VISION) over the `--lit` argument of settings['build']['darkness']['args'] -> the new argument"""
    args = settings['build']['darkness']['args']
    i = args.index('--lit') + 1
    kv = dict(x.split('=', 1) for x in args[i].split(';') if x)
    kv.update(keys or LIT_VISION)
    args[i] = ';'.join('%s=%s' % (k, v) for k, v in kv.items())
    return args[i]
