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
         'notice_do_not_restart', 'poster_missing', 'poster_missing_1', 'poster_missing_2', 'poster_missing_3', 'ad_panel_broken',
         'grime_mask_floor', 'junction_grime', 'water_streak', 'sign_grime_overlay', 'decal_blood_feathered',
         'decal_grime_feathered', 'poster_illustration_2']
KIND = {'departure_board_suspended': 'poster', 'evac_signal_diagram': 'poster', 'notice_quarantine': 'poster',
        'notice_do_not_restart': 'poster', 'poster_missing': 'poster', 'poster_missing_1': 'poster', 'poster_missing_2': 'poster',
        'poster_missing_3': 'poster', 'ad_panel_broken': 'poster', 'poster_illustration_2': 'poster'}   # the rest: decal (alpha)


def find(name):
    hits = []
    for root, dirs, files in os.walk(ART_ROOT):
        dirs[:] = [d for d in dirs if d not in ('hooks_tga',)]
        for f in files:
            stem, ext = os.path.splitext(f)
            if stem.lower() in (name, name + '_c') and ext.lower() in ('.tga', '.png'):
                hits.append(os.path.join(root, f))
    hits.sort(key=lambda p: (not p.lower().endswith('.tga'), len(p)))
    return hits[0] if hits else None


def tga_of(path, name):
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
        else:
            MT.custom_image(key, 'art_' + n + '_c', tga, base=DECAL_BASE)
            MT.MATERIALS[key]['collide'] = False
        AVAILABLE[n] = key
    return AVAILABLE


def key(name):
    return AVAILABLE.get(name)
