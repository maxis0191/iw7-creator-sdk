"""Build every Station Zero g25 2D art request (level/g25-fixlist.md, "Art requests (exact sizes)") in one command.

usage (from tools-source/iwzmap):
  python -m art.make_station_zero_art <out dir> <selected imagegen dir> [--only name,name] [--signs <signs dir>]

<selected imagegen dir> holds the reviewed model images the painterly assets need (stage folder
art/imagegen/selected): missing_a.png, missing_b.png, missing_c.png (fictional snapshot portraits), adpanel.png (beach
illustration), poster2.png (stairwell film-poster painting). Everything else is procedural or typeset.
Writes <name>.png + <name>_c.tga + <name>_c.dds per asset and manifest.json (size, alpha, method, sha256, suggested
material base and decal use). --signs also writes aged copies of the existing sign art to <out>/signs_aged.
"""
import argparse
import hashlib
import json
import os
import time

import numpy as np
from PIL import Image

from . import age, boards, masks, notices, texio

DECAL_BASE = 'wall_stain_01_dec'          # w_l_sm_ndw_blend_i0c0: colour + alpha blend, lit (stock cp_zmb)
OPAQUE_BASE = 'zombies_theater_poster01'  # w_l_sm_replace_i0c0: the base of every shipped sign/poster
MULTIPLY_BASE = 'dirt_water_stain_01'     # w_unlit_multiply_lin_ndw: colour multiply (white = no change)


def assets(sel):
    j = lambda n: os.path.join(sel, n)
    return [
        # name, builder, method, alpha, material base, use
        ('clock_face_stopped', lambda: boards.clock_face_stopped(), 'typographic (PIL, Bahnschrift) + procedural ageing/cracks',
         True, DECAL_BASE, 'decal over every clock disc (sign_clock_04): 23:47, cracked glass'),
        ('departure_board_suspended', lambda: boards.departure_board_suspended(), 'typographic split-flap renderer',
         False, OPAQUE_BASE, 'ticket hall departure board face'),
        ('evac_signal_diagram', lambda: boards.evac_signal_diagram(), 'typographic diagram from the level layout',
         False, OPAQUE_BASE, 'control room wall diagram (replaces the Spaceland evacuation map)'),
        ('notice_closed_layers', lambda: notices.notice_closed_layers(), 'typographic + procedural paper/tears/tape',
         True, DECAL_BASE, 'platform B: replaces the blank faded rectangle'),
        ('notice_quarantine', lambda: notices.notice_quarantine(), 'typographic + procedural paper ageing', False,
         OPAQUE_BASE, 'platform A / hall notice boards'),
        ('notice_do_not_restart', lambda: notices.notice_do_not_restart(), 'typographic + procedural paper ageing',
         False, OPAQUE_BASE, 'maintenance corridor / generator room notice board'),
        ('poster_missing_a', lambda: notices.poster_missing('a', j('missing_a.png')),
         'imagegen photo (fictional) + typeset flyer + photocopy/ageing', False, OPAQUE_BASE, 'missing poster 1 (signal tech)'),
        ('poster_missing_b', lambda: notices.poster_missing('b', j('missing_b.png')),
         'imagegen photo (fictional) + typeset flyer + ageing', False, OPAQUE_BASE, 'missing poster 2 (passenger)'),
        ('poster_missing_c', lambda: notices.poster_missing('c', j('missing_c.png')),
         'imagegen photo (fictional) + typeset flyer + rain fading', False, OPAQUE_BASE, 'missing poster 3 (commuter)'),
        ('ad_panel_broken', lambda: notices.ad_panel_broken(j('adpanel.png')),
         'imagegen illustration + typeset copy + procedural backlight/cracks', False, OPAQUE_BASE,
         'stair A light box (replaces the black panel); an emissive base would sell "lit"'),
        ('grime_mask_floor', lambda: masks.grime_mask_floor(), 'procedural (spectral fBm, domain warp, blobs), tileable',
         False, MULTIPLY_BASE, 'generator room diamond-plate floor overlay, multiply (RGB, white = no change)'),
        ('junction_grime', lambda: masks.junction_grime(), 'procedural, tiles horizontally', True, DECAL_BASE,
         'floor/wall junction strip (junction = bottom edge; flip V for ceilings)'),
        ('water_streak', lambda: masks.water_streak(), 'procedural flow streaks', True, DECAL_BASE,
         'wall decal below a ceiling crack (crack = top edge)'),
        ('sign_grime_overlay', lambda: masks.sign_grime_overlay(), 'procedural', True, None,
         'ageing overlay for sign art (art.age applies it at each sign size)'),
        ('decal_blood_feathered', lambda: masks.decal_blood_feathered(), 'procedural', True, DECAL_BASE,
         'floor drag smear (pool at the bottom, drag toward the top)'),
        ('decal_grime_feathered', lambda: masks.decal_grime_feathered(), 'procedural', True, DECAL_BASE,
         'floor grime patch'),
    ]


def sha(path):
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('selected')
    ap.add_argument('--only', default='')
    ap.add_argument('--signs', default='')
    a = ap.parse_args()
    only = set(x for x in a.only.split(',') if x)
    os.makedirs(a.out, exist_ok=True)
    mpath = os.path.join(a.out, 'manifest.json')
    manifest = json.load(open(mpath)) if os.path.exists(mpath) else {'assets': {}}
    for name, build, method, alpha, base, use in assets(a.selected):
        if only and name not in only:
            continue
        t = time.time()
        arr = build()
        info = texio.save_all(arr, a.out, name, alpha=alpha)
        info.update({'method': method, 'alpha': alpha, 'material_base': base, 'use': use,
                     'sha256_png': sha(os.path.join(a.out, name + '.png')),
                     'sha256_tga': sha(os.path.join(a.out, name + '_c.tga')), 'seconds': round(time.time() - t, 1)})
        manifest['assets'][name] = info
        print(name, info['size'], info['mode'], 'mips', info['mips'], info['seconds'], 's')
    # second film poster: the text-free illustration (with the Zero Line roundel painted on) and the composed poster
    if not only or 'poster_illustration_2' in only:
        poster, plain = notices.poster_station_zero_v2(os.path.join(a.selected, 'poster2.png'))
        small = lambda x: np.asarray(Image.fromarray((x * 255 + 0.5).astype(np.uint8)).resize((512, 768), Image.LANCZOS),
                                     np.float32) / 255
        for name, arr, use in (('poster_illustration_2', small(plain), 'text-free painting for a second poster'),
                               ('poster_station_zero_v2', small(poster), 'composed STATION ZERO poster on the new painting '
                                                                         '(sign_4: no longer shares the train painting)')):
            info = texio.save_all(arr, a.out, name, alpha=False)
            info.update({'method': 'imagegen painting (reviewed) + Z roundel paint-over + typeset title', 'alpha': False,
                         'material_base': OPAQUE_BASE, 'use': use,
                         'sha256_png': sha(os.path.join(a.out, name + '.png')),
                         'sha256_tga': sha(os.path.join(a.out, name + '_c.tga'))})
            manifest['assets'][name] = info
            print(name, info['size'])
    if a.signs:
        manifest['signs_aged'] = age.age_dir(a.signs, os.path.join(a.out, 'signs_aged'), 1.0)
        print('aged signs', len(manifest['signs_aged']))
    json.dump(manifest, open(mpath, 'w'), indent=2)


if __name__ == '__main__':
    main()
