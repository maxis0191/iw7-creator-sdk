"""Station Zero v2 material table.

MATERIALS: key -> {'path': world material asset, 'su'/'sv': texture world size in units (one texture repeat),
'collide': default collision for quads using it, 'verified': engine evidence label}. Stock materials come from
the cp_zmb template zone (zonetool/<map>/materials/w/*.json, techset in the comment).
CUSTOM: materials the generator writes into the map zone, cloned from a verified stock world material:
  'base': stock material json the clone starts from, 'image': TGA (colour, texture semantic 2) to add to the zone,
  'tint': colorTint override, 'emissive': emissivePara override.
UV scales were checked in the engine gallery (IWZ_GALLERY=1 build, see level/REPORT.md); 'verified' records it.
"""
import os

ART = os.environ.get('IWZ_ART_DIR', r'C:\Users\ezvalo\Documents\IW7-Runtime\iwz-stage2\art')


# Colour image size of every stock material (GrayWolf PNG export of cp_zmb, 2026-11-08; material_dims.json). Many stock
# trims are strips (steel_trim 1024x128, ibeam 2048x256, stair_tread 1024x256): mapping them square stretched them 4-16x
# (review A6: jambs, pilasters, beam sides, stair treads). S() now keeps the image aspect (sv = su * h / w) and TRIM
# materials are strip-mapped by brushkit (u along the face's long edge, v exactly once across its short side).
import json as _json
_DIMS = _json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'material_dims.json')))
_DIMS_BY_PATH = {}
TRIM = {'frame', 'light_line_yellow', 'arrow_stripes', 'conc_trim_floor', 'steel_trim', 'ibeam', 'ibeam_bare', 'molding',
        'cornertrim', 'chrome_trim', 'stair_tread', 'wood_trim', 'light_diffuser', 'rubber_trim', 'yellow_line', 'conc_tiles_trim'}
TRIM_MAX = 96.0       # a face whose short side is longer than this tiles the trim with its true aspect instead


def S(path, su, sv=None, **kw):
    d = {'path': 'w/' + path, 'su': float(su), 'sv': float(sv if sv is not None else su), 'verified': 'NOT_PROVEN'}
    d.update(kw)
    if sv is None:
        d['aspect_pending'] = True        # resolved against material_dims.json below
    return d


MATERIALS = {
    # metro tiles (w_l_sm_replace_i0c0s0n0p0)
    'tile_white':     S('dt_tile_ceramic_white', 64),
    'tile_black':     S('fac_tile_black_01', 32),
    'tile_floor':     S('stone_floor_tiles_01', 128),               # ..s0o0n0p0
    'checker':        S('stone_marble_tile_checker_01', 128),
    'marble':         S('fah_marble_floor_01', 128),
    'conc_tiles':     S('concrete_tiles_01', 64),
    'conc_tiles_trim': S('concrete_tiles_01_trim', 64),
    'restaurant':     S('fah_restaurant_tiles_01', 96),
    # concrete / plaster / brick
    'conc_lined':     S('concrete_wall_12_lined_dirty', 256),       # w_l_sm_replace_i0c0n0
    'conc_seam':      S('concrete_wall_04_seam_grey', 256),
    'conc_wall':      S('ch_concretewall02', 256),
    'conc_painted':   S('concrete_wall_painted_01', 256),
    'conc':           S('concrete_01', 256),
    'conc_dark':      S('clk_concrete_bunker_dark', 256),
    'conc_floor':     S('concrete_floor_polished_01', 256),
    'conc_trim_floor': S('concrete_trim_floor_01', 64),
    'conc_floor_gray': S('concrete_painted_floor_glossy_01_gray', 256),
    'brick_white':    S('frag_brick_painted_white_01', 128),
    'brick_gray':     S('frag_brick_painted_gray', 128),
    'herringbone':    S('t7_brick_herringbone_dirty_02', 128),
    'plaster_green':  S('plaster_wall_04_green_light', 256),
    'plaster_grey':   S('plaster_wall_04_grey_dark_01', 256),
    'drywall_gray':   S('iw7_drywall_painted_gray_01', 256),        # ..n0q0p0 (detail)
    'drywall_green':  S('iw7_drywall_painted_green_01', 256),
    'ceil_tiles':     S('plaster_ceiling_tiles_01', 128),
    'ceil_tile':      S('ceiling_tile_01', 96),
    # metal
    'steel_trim':     S('metal_bare_steel_trim_01', 64),
    'steel_trim_sheet': S('metal_bare_steel_trim_sheet_01', 64),
    'chrome_trim':    S('metal_chrome_trim_03', 64),
    'ibeam':          S('metal_ibeam_trim_painted_01', 64),
    'ibeam_bare':     S('metal_ibeam_trim_bare_02', 64),
    'beam_yellow':    S('metal_painted_scratched_yellow', 128),
    'grate':          S('fac_metal_grate_01', 64, collide=False),   # alpha test
    'grating_under':  S('metal_grating_underside_02', 64, collide=False),
    'diamond':        S('metal_bare_diamondplate_01', 128),
    'rollup':         S('door_metal_rollup_grey_large_01', 128),
    'vent':           S('metal_vent_02', 64),
    'panel_dark':     S('metal_panel_dark_01', 128),
    'panel_wall':     S('metal_painted_wall_panel_04', 128),
    'metal_red':      S('metal_painted_red_01', 128),
    'metal_black':    S('metal_painted_01_black', 128),
    'metal_blue':     S('metal_painted_dark_blue', 128),
    'brushed':        S('fac_brushedmetal_02', 128),
    'corrugated':     S('metal_corrugated_01', 128),
    'frame':          S('metal_trim_frame_01', 64),
    'metal_floor':    S('metal_floor_grey_01', 128),
    'deck_black':     S('metal_deck_painted_black_01', 128),
    # rubber / wood / misc
    'rubber_trim':    S('fac_rubber_trim_black', 64),
    'rubber_mat':     S('fac_rubber_mat_black', 128),
    'stair_tread':    S('rubber_non_skid_stair_01', 64),
    'yellow_grip':    S('sidewalkgrip_01_yellow', 64),
    'wood_planks':    S('fah_wood_planks_01', 128),
    'wood_floor':     S('wood_rustic_floor_02', 128),
    'wood_trim':      S('wood_trim_wall_01', 64),
    'wood_green':     S('wood_worn_painted_01_green', 128),
    'molding':        S('plaster_molding_02_white_trim', 64),
    'chainlink':      S('mtl_zeb_fence_chainlink', 64, collide=False),
    'map_board':      S('zombies_underground_map', 1),               # explicit uvs
    'exit_sign':      S('signage_zmb_exit_sign_01', 1),
    # light emitting / unlit
    'light_panel':    S('plastic_wall_panel_light_02_on', 64),      # ..n0e0p0 emissive
    'light_panel_red': S('plastic_wall_panel_light_02_on_red', 64),
    'light_diffuser': S('glass_led_light_diffuser_01', 64),
    'light_line_yellow': S('light_line_yellow_02', 64),
    'neon_orange':    S('zmb_neon_orange', 64, collide=False),        # unlit
    'black':          S('com_black_true', 64),                       # unlit black (tunnel depth)
    # decals / blends (drawn 0.5 in front of a surface, no collision)
    'glass':          S('glass_clear_generic_01', 128),              # blend add; collision kept (windows)
    'cornertrim':     S('cornertrim_concrete_01', 64, collide=False),
    'arrow_stripes':  S('paint_arrow_stripes_01', 128, collide=False),
    'yellow_line':    S('paint_lines_01_thick_yellow_clean', 64, collide=False),
    'water_stain':    S('dirt_water_stain_01', 128, collide=False),   # unlit multiply
    'ceiling_stain':  S('ceiling_waterstains1', 256, collide=False),
    'leak_stain':     S('dirt_stain_leaking_01', 128, collide=False),
    'wall_stain':     S('wall_stain_01_dec', 128, collide=False),
    'blood_pool':     S('t7_decal_blood_pool_01', 96, collide=False),
    'blood_splat':    S('t7_decal_blood_splatter_01_rvl', 96, collide=False),
    'puddle':         S('water_puddle_tiling_01_rvl', 128, collide=False),
    # art pass 2 (engine check in the views runs: sz2_propcheck / frames)
    'ballast':        S('fac_rooftop_ground_01', 128),               # track bed gravel
    'drip_stain':     S('dirt_stain_water_drips_01', 128, collide=False),
    'top_stain':      S('dirt_stain_top_01', 128, collide=False),
    'floor_stain':    S('dirt_water_stain_01', 128, collide=False),
}

for _k, _m in MATERIALS.items():
    _d = _DIMS.get(_k) or {}
    if _d.get('w') and _d.get('h'):
        _m['img'] = (_d['w'], _d['h'])
        if _m.pop('aspect_pending', False):
            _m['sv'] = _m['su'] * _d['h'] / _d['w']
    _m.pop('aspect_pending', None)
    if _k in TRIM:
        _m['trim'] = True
        _m['trim_max'] = TRIM_MAX

# custom materials written into the map zone (path, stock base material, colour image / constants)
POSTER_BASE = 'zombies_theater_poster01'      # w_l_sm_replace_i0c0: identity normal + colour (semantic 2)
EMISSIVE_BASE = 'emissive_light_panel_pink'   # w_l_sm_replace_i0c0em0: colour tint + emissive
CUSTOM = {}


def custom_image(key, image_name, tga, base=POSTER_BASE, tint=None):
    CUSTOM[key] = {'path': 'w/iwz_' + image_name, 'base': base, 'image': image_name, 'tga': tga, 'tint': tint}
    MATERIALS[key] = {'path': 'w/iwz_' + image_name, 'su': 1.0, 'sv': 1.0, 'verified': 'NOT_PROVEN', 'custom': True}


def custom_tint(key, name, base, tint, emissive=None, su=64):
    CUSTOM[key] = {'path': 'w/iwz_' + name, 'base': base, 'tint': tint, 'emissive': emissive}
    MATERIALS[key] = {'path': 'w/iwz_' + name, 'su': float(su), 'sv': float(su), 'verified': 'NOT_PROVEN', 'custom': True}


SIGNS = ['sign_station_zero', 'sign_station_zero_plain', 'sign_old_station', 'sign_to_platforms', 'sign_northbound',
         'sign_to_old_station', 'sign_staff_only', 'sign_signal_control', 'sign_generator', 'sign_network_map']
for _s in SIGNS:
    custom_image(_s, _s + '_c', os.path.join(ART, 'signs', _s + '_c.tga'))
for _p in ('poster_mindgap', 'poster_lasttrain', 'poster_station_zero'):
    custom_image(_p, _p + '_c', os.path.join(ART, 'out', _p + '_c.tga'))

# light fixture faces: the stock emissive panel with our own colour (fluorescent, sodium, emergency red)
custom_tint('lamp_cool', 'lamp_cool', EMISSIVE_BASE, (0.85, 0.93, 1.0, 1.0), emissive=(1.6, 0, 0, 0))
custom_tint('lamp_warm', 'lamp_warm', EMISSIVE_BASE, (1.0, 0.58, 0.22, 1.0), emissive=(1.6, 0, 0, 0))
custom_tint('lamp_red', 'lamp_red', EMISSIVE_BASE, (1.0, 0.06, 0.04, 1.0), emissive=(1.8, 0, 0, 0))
custom_tint('lamp_green', 'lamp_green', EMISSIVE_BASE, (0.1, 1.0, 0.2, 1.0), emissive=(1.6, 0, 0, 0))
# tinted stock surfaces
custom_tint('tile_green', 'tile_green', 'dt_tile_ceramic_white', (0.42, 0.62, 0.45, 1.0), su=64)
custom_tint('tile_cream', 'tile_cream', 'dt_tile_ceramic_white', (1.0, 0.93, 0.78, 1.0), su=64)
custom_tint('metal_silver', 'metal_silver', 'metal_painted_wall_panel_04', (0.82, 0.85, 0.9, 1.0), su=128)
custom_tint('carriage_red', 'carriage_red', 'metal_painted_red_01', (0.75, 0.08, 0.06, 1.0), su=128)
custom_tint('panel_wall_red', 'panel_wall_red', 'metal_painted_wall_panel_04', (1.0, 0.42, 0.38, 1.0), su=128)
custom_tint('panel_dark_red', 'panel_dark_red', 'metal_panel_dark_01', (1.0, 0.5, 0.46, 1.0), su=128)
custom_tint('ceil_red', 'ceil_red', 'ceiling_tile_01', (1.0, 0.62, 0.58, 1.0), su=96)
custom_tint('seat_blue', 'seat_blue', 'fac_rubber_mat_black', (0.25, 0.35, 0.8, 1.0), su=64)


def material_rows():
    """zone csv rows for the custom materials."""
    return ['material,' + c['path'] for c in CUSTOM.values()]


# engine verification (material gallery, run level/runs/views-g2, frames analysis-g2/gallery_*.jpg):
# PROVEN = renders as expected on generated world quads; FAILED = do not use on world quads with this vertex format
_FAILED = {
    'puddle': 'FAILED: renders as an opaque grey square (reveal/v0 blend needs vertex alpha or reveal data)',
    'blood_splat': 'FAILED: renders as an opaque red square (_rvl reveal techset)',
    'yellow_line': 'FAILED: renders as an opaque yellow board (v0 techset)',
    'exit_sign': 'PROVEN renders, but the art is a Spaceland "thanks for visiting" sign: not used',
}
_UNCHECKED = {'water_stain', 'ceiling_stain', 'leak_stain', 'wall_stain', 'glass', 'ballast', 'drip_stain', 'top_stain', 'floor_stain'}   # blends, not readable on the gallery's black wall
for _k, _m in MATERIALS.items():
    if _k in _FAILED:
        _m['verified'] = _FAILED[_k]
    elif _k in _UNCHECKED:
        _m['verified'] = 'NOT_PROVEN (blend: not measurable on the gallery wall; glass PROVEN visually in the carriage windows)'
    else:
        _m['verified'] = 'PROVEN (gallery views-g2)'
for _k in ('panel_wall_red', 'panel_dark_red', 'ceil_red'):
    MATERIALS[_k]['verified'] = 'NOT_PROVEN in the gallery (tint clone of a PROVEN material; checked in zone views)'
