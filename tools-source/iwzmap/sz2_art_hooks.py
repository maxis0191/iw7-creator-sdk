"""Art drop-in hooks for Station Zero v2 (g25 art request list, level\\g25-fixlist.md "Art requests").

The art agent delivers images to iwz-stage2\\art\\ (any sub folder) named exactly as the request list:
  clock_face_stopped, departure_board_suspended, evac_signal_diagram, notice_closed_layers, notice_quarantine,
  notice_do_not_restart, poster_missing (or poster_missing_1/_2/_3), ad_panel_broken, grime_mask_floor,
  junction_grime, water_streak, sign_grime_overlay, decal_blood_feathered, decal_grime_feathered,
  poster_illustration_2
as .tga or .png. A present image becomes a custom map material (colour texture replaced on a stock base:
'poster' = the opaque poster material, 'decal' = the blended wall_stain_01_dec decal) and is placed by
station_zero2.py at the spots of ART_PLACE; a missing image changes nothing (the build stays identical).
PNG files are converted to 32-bit TGA in art\\hooks_tga\\ (PIL). Engine look of each hook: NOT_PROVEN until a run.
"""
import os

import sz2_materials as MT

ART_ROOT = MT.ART
DECAL_BASE = 'wall_stain_01_dec'        # w_l_sm_ndw_blend_i0c0: blended colour (alpha) + identity normal
NAMES = ['clock_face_stopped', 'departure_board_suspended', 'evac_signal_diagram', 'notice_closed_layers', 'notice_quarantine',
         'notice_do_not_restart', 'poster_missing', 'poster_missing_1', 'poster_missing_2', 'poster_missing_3',
         'poster_missing_a', 'poster_missing_b', 'poster_missing_c', 'poster_station_zero_v2', 'ad_panel_broken',
         'grime_mask_floor', 'junction_grime', 'water_streak', 'sign_grime_overlay', 'decal_blood_feathered',
         'decal_grime_feathered', 'poster_illustration_2',
         'decal_blood_hand_smear', 'decal_blood_drag', 'decal_blood_spatter', 'decal_blood_pool']   # art c10c5ad blood set
KIND = {'departure_board_suspended': 'poster', 'evac_signal_diagram': 'poster', 'notice_quarantine': 'poster',
        'notice_do_not_restart': 'poster', 'poster_missing': 'poster', 'poster_missing_1': 'poster', 'poster_missing_2': 'poster',
        'poster_missing_3': 'poster', 'ad_panel_broken': 'poster', 'poster_illustration_2': 'poster',
        'poster_missing_a': 'poster', 'poster_missing_b': 'poster', 'poster_missing_c': 'poster', 'poster_station_zero_v2': 'poster',
        'grime_mask_floor': 'multiply'}   # the rest: decal (alpha)
MULTIPLY_BASE = 'dirt_water_stain_01'   # w_unlit_multiply_lin_ndw: colour only, white = no change (art NOTES)
BLOOD = 'decal_blood_feathered'        # variants decal_blood_feathered[_a.._d | _1.._4]: rotated / mirrored per placement


def find(name):
    hits = []
    for root, dirs, files in os.walk(ART_ROOT):
        dirs[:] = [d for d in dirs if d not in ('hooks_tga',)]
        for f in files:
            stem, ext = os.path.splitext(f)
            if stem.lower() in (name, name + '_c') and ext.lower() in ('.tga', '.png'):
                hits.append(os.path.join(root, f))
    hits.sort(key=lambda p: (not p.lower().endswith('.tga'), 'g25' not in p.lower(), len(p)))     # delivered g25 set first
    return hits[0] if hits else None


BLOOD_GRADE = os.environ.get('IWZ_BLOOD_GRADE', '1') == '1'


def blood_graded(path, name):
    """(g27d, review item 18: blood read flat saturated red, a marble-veined pool, a pink spray) dried-blood grade of a
    delivered blood image: luminance mapped onto dark red-brown (no pink highlights, no full-saturation red), the pool's
    colour softened (its veins), alpha kept. Written to art\\hooks_tga\\<name>_graded_c.tga."""
    from PIL import Image, ImageFilter
    out_dir = os.path.join(ART_ROOT, 'hooks_tga')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + '_graded_c.tga')
    if os.path.exists(out) and os.path.getmtime(out) >= os.path.getmtime(path) and os.path.getmtime(out) >= os.path.getmtime(__file__):
        return out
    im = Image.open(path).convert('RGBA')
    r, g, b, a = im.split()
    lum = Image.merge('RGB', (r, g, b)).convert('L')
    if 'pool' in name:
        lum = lum.filter(ImageFilter.GaussianBlur(max(2, im.size[0] // 64)))
    # uneven drying: a low-frequency mottle (darker crusted patches) instead of one flat red
    import random as _r
    _r.seed(sum(map(ord, name)))
    n_ = Image.new('L', (8, 8))
    n_.putdata([_r.randrange(150, 256) for _ in range(64)])
    mott = n_.resize(im.size, Image.BICUBIC)
    lum = Image.composite(lum, lum.point(lambda v: v * 0.6), mott)
    R = lum.point(lambda v: int(26 + 0.36 * v))
    G = lum.point(lambda v: int(7 + 0.11 * v))
    Bc = lum.point(lambda v: int(6 + 0.085 * v))
    Image.merge('RGBA', (R, G, Bc, a)).save(out)
    return out


def tga_of(path, name):
    if BLOOD_GRADE and name.startswith('decal_blood'):
        return blood_graded(path, name)
    if path.lower().endswith('.tga'):
        return path
    from PIL import Image
    out_dir = os.path.join(ART_ROOT, 'hooks_tga')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, name + '_c.tga')
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(path):
        Image.open(path).convert('RGBA').save(out)
    return out


AVAILABLE = {}       # name -> material key
BLOOD_VARIANTS = []  # material keys of the delivered blood variants
AGED_SIGNS = []      # signs whose material now uses the aged image


def register():
    if os.environ.get('IWZ_ART_HOOKS', '1') != '1':
        return AVAILABLE
    for n in NAMES:
        p = find(n)
        if not p:
            continue
        key = 'art_' + n
        tga = tga_of(p, n)
        if KIND.get(n) == 'poster':
            MT.custom_image(key, 'art_' + n + '_c', tga)
        elif KIND.get(n) == 'multiply':
            MT.custom_image(key, 'art_' + n + '_c', tga, base=MULTIPLY_BASE)
            MT.MATERIALS[key]['collide'] = False
        else:
            MT.custom_image(key, 'art_' + n + '_c', tga, base=DECAL_BASE)
            MT.MATERIALS[key]['collide'] = False
        AVAILABLE[n] = key
    # blood variants (any suffix after the base name), in name order
    seen = set()
    for root, dirs, files in os.walk(ART_ROOT):
        dirs[:] = [d for d in dirs if d not in ('hooks_tga',)]
        for f in sorted(files):
            stem, ext = os.path.splitext(f)
            stem = stem[:-2] if stem.endswith('_c') else stem
            if stem.startswith(BLOOD + '_') and ext.lower() in ('.tga', '.png') and stem not in seen and stem not in AVAILABLE:
                p = find(stem)
                if p:
                    seen.add(stem)
                    MT.custom_image('art_' + stem, 'art_' + stem + '_c', tga_of(p, stem), base=DECAL_BASE)
                    MT.MATERIALS['art_' + stem]['collide'] = False
                    BLOOD_VARIANTS.append('art_' + stem)
    BLOOD_VARIANTS.sort()
    # aged signs (art g25\signs_aged\<sign>_c.tga): the sign materials take them; no extra grime overlay then
    for s_ in MT.SIGNS:
        p = os.path.join(ART_ROOT, 'g25', 'signs_aged', s_ + '_c.tga')
        if os.path.exists(p) and s_ in MT.CUSTOM:
            MT.CUSTOM[s_]['tga'] = p
            AGED_SIGNS.append(s_)
    return AVAILABLE


def key(name):
    return AVAILABLE.get(name)
