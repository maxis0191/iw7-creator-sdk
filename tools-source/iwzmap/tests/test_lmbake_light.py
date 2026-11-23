"""Baker light settings that a map document can reach (R7 follow-up, 23 Nov 2026): baked prop shadows, emissive materials and props,
ambient / sky / bounces. Each test bakes a tiny synthetic emit (quick settings) and reads the float images in bake.npz.
Needs the bake environment (numba, scipy, Pillow) and texconv (the baker encodes its images): a check without them skips.
Run with the bake python: python -B tests/test_lmbake_light.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    import numpy as np
    import synth_world as SW
    import lmbake
    import iw7image
    import layout_lights
    import occluders
except ImportError as e:
    raise unittest.SkipTest('bake environment missing: %s' % e)
if not os.path.isfile(iw7image.TEXCONV):
    raise unittest.SkipTest('texconv missing: %s' % iw7image.TEXCONV)

LIGHT = {'zone': 'z', 'origin': [128.0, 128.0, 100.0], 'type': 'omni', 'color': [1.0, 1.0, 1.0], 'radius': 400.0, 'intensity': 1.0, 'fixture': ''}


def bake_emit(work, quads, materials, layout, smodels=None, extra=None, quick=True, extra_cfg=None):
    src = os.path.join(work, 'emit')
    SW.write_emit(src, SW.make_world(quads, materials), layout, smodels, extra)
    cfg, rep = layout_lights.build_config(src, texel=8.0)
    cfg.update(extra_cfg or {})
    lj = os.path.join(work, 'lights.json')
    json.dump(cfg, open(lj, 'w'))
    out = os.path.join(work, 'out')
    if os.path.isdir(out):
        shutil.rmtree(out)
    lmbake.bake(src, lj, out, texel=8.0, bounces=None, quick=quick, denoise=0)
    z = np.load(os.path.join(out, 'bake.npz'))
    return {k: z[k] for k in z.files}, cfg, rep, json.load(open(os.path.join(out, 'bake.json')))


def nearest(z, x, y, zz=0.0):
    d = np.linalg.norm(z['tx_pos'] - np.array([x, y, zz]), axis=1)
    return int(np.argmin(d))


class Light(unittest.TestCase):
    def setUp(self):
        self.work = tempfile.mkdtemp(prefix='iwzlight_')

    def tearDown(self):
        shutil.rmtree(self.work, ignore_errors=True)

    # ---------------------------------------------------------------- item 2: a prop casts a baked shadow
    def test_prop_shadow_darkens_the_floor_under_a_table(self):
        floor = [SW.floor_quad(0, 0, 0, 256, 256)]
        lay = {'lights': [LIGHT]}
        sm = ['test_table 128 128 0 0 0 0 1']
        side = {'smodel_bounds.json': {'test_table': {'mins': [-24, -24, 30], 'maxs': [24, 24, 40]}}}
        on, cfg_on, rep, _ = bake_emit(self.work, floor, ['w/concrete_floor'], dict(lay), sm, side)
        self.assertEqual(len(cfg_on['occluders']), 1)
        self.assertEqual(rep['prop_shadows']['bounds_source'], 'smodel_bounds.json')
        lay_off = dict(lay, lighting={'prop_shadows': False})
        off, cfg_off, _, _ = bake_emit(self.work, floor, ['w/concrete_floor'], lay_off, sm, side)
        self.assertNotIn('occluders', cfg_off)
        under, open_ = nearest(on, 128, 128), nearest(on, 24, 24)
        e_on, e_off = on['Edir'][under].sum(), off['Edir'][under].sum()
        print('floor under the table: %.4f with the shadow, %.4f without (factor %.3f); open floor %.4f / %.4f' %
              (e_on, e_off, e_on / e_off, on['Edir'][open_].sum(), off['Edir'][open_].sum()))
        self.assertGreater(e_off, 1.0)                                    # unshadowed: about I x 3 (power) x cos at d = 100
        self.assertLess(e_on / e_off, 0.05)                               # the umbra
        self.assertAlmostEqual(on['Edir'][open_].sum() / off['Edir'][open_].sum(), 1.0, delta=0.05)   # away from the table: unchanged

    def test_a_prop_that_holds_the_light_does_not_shadow_it(self):
        floor = [SW.floor_quad(0, 0, 0, 256, 256)]
        sm = ['test_lamp 128 128 90 0 0 0 1']
        side = {'smodel_bounds.json': {'test_lamp': {'mins': [-8, -8, 0], 'maxs': [8, 8, 20]}}}      # the light at z 100 is inside
        _, cfg, rep, _ = bake_emit(self.work, floor, ['w/concrete_floor'], {'lights': [LIGHT]}, sm, side)
        self.assertNotIn('occluders', cfg)
        self.assertEqual(rep['prop_shadows']['hold_a_light'], 1)

    def test_rotated_box_corners(self):
        c = occluders.oriented_corners([10, 20, 0], [0, 90, 0], 2.0, [-1, -2, 0], [1, 2, 3])     # yaw 90: local x -> world y
        xs = sorted({round(p[0], 3) for p in c}); ys = sorted({round(p[1], 3) for p in c}); zs = sorted({round(p[2], 3) for p in c})
        self.assertEqual(xs, [6.0, 14.0]); self.assertEqual(ys, [18.0, 22.0]); self.assertEqual(zs, [0.0, 6.0])

    # ---------------------------------------------------------------- item 3: emissive from the document
    def _corner(self):
        # a floor, a wall at x = 0 facing +x, and a panel at y = 0 facing +y (x 0..64, z 8..120): the wall's texels at small y see the panel
        return [SW.floor_quad(0, 0, 0, 256, 256), SW.wall_quad_x(1, 0.0, 0.0, 256.0, 0.0, 128.0),
                (2, [(64, 0, 8), (0, 0, 8), (0, 0, 120), (64, 0, 120)], (0, 1, 0))]

    def test_emissive_material_tints_the_next_wall(self):
        mats = ['w/concrete_floor', 'w/concrete_wall', 'w/neon_panel']
        base, _, _, _ = bake_emit(self.work, self._corner(), mats, {'lights': []})
        lay = {'lights': [], 'lighting': {'emissive': {'w/neon_panel': {'color': [1.0, 0.1, 0.1], 'strength': 2.0}}}}
        lit, cfg, rep, _ = bake_emit(self.work, self._corner(), mats, lay)
        self.assertEqual(rep['emissive_materials_from_document'], 1)
        self.assertEqual(cfg['emissive']['w/neon_panel'], [2.0, 0.2, 0.2])
        i = nearest(lit, 0.0, 16.0, 60.0)
        d = lit['Eind'][i] - base['Eind'][i]
        print('wall texel beside the panel: indirect change r %.3f g %.3f b %.3f' % tuple(d))
        self.assertGreater(d[0], 0.05)
        self.assertLess(abs(d[1]), 0.2 * d[0]); self.assertLess(abs(d[2]), 0.2 * d[0])      # the tint is the panel's colour
        far = nearest(lit, 0.0, 240.0, 60.0)
        self.assertLess(lit['Eind'][far][0] - base['Eind'][far][0], 0.5 * d[0])            # and fades with distance

    def test_name_rule_is_the_fallback(self):
        mats = ['w/concrete_floor', 'w/concrete_wall', 'w/lamp_panel']
        _, cfg, _, _ = bake_emit(self.work, self._corner(), mats, {'lights': []})
        self.assertIn('w/lamp_panel', cfg['emissive'])

    def test_emissive_prop_lights_the_wall(self):
        mats = ['w/concrete_floor', 'w/concrete_wall', 'w/concrete_wall']
        quads = self._corner()[:2]
        sm = ['test_sign 40 40 20 0 0 0 1']
        side = {'smodel_bounds.json': {'test_sign': {'mins': [-2, -16, 0], 'maxs': [2, 16, 40]}}}
        base, _, _, _ = bake_emit(self.work, quads, mats[:2], {'lights': []}, sm, side)
        lay = {'lights': [], 'lighting': {'emissive_props': [        # prop_shadows left at its default (on): the sign is boxed once, as an emitter
            {'model': 'test_sign', 'origin': [40, 40, 20], 'angles': [0, 0, 0], 'scale': 1.0, 'color': [0.1, 0.2, 1.0], 'strength': 3.0}]}}
        lit, cfg, rep, bj = bake_emit(self.work, quads, mats[:2], lay, sm, side)
        self.assertEqual(rep['emissive_props']['baked'], 1)
        self.assertEqual(len(cfg['occluders']), 1)                  # not once as an occluder and once as an emitter
        self.assertEqual(rep['prop_shadows']['emissive_boxed_elsewhere'], 1)
        self.assertEqual(bj['emissive_boxes'], 1)
        i = nearest(lit, 0.0, 40.0, 40.0)
        d = lit['Eind'][i] - base['Eind'][i]
        print('wall texel beside the emissive sign: indirect change r %.3f g %.3f b %.3f' % tuple(d))
        self.assertGreater(d[2], 0.05)
        self.assertGreater(d[2], 3.0 * d[0])

    # ---------------------------------------------------------------- item 4: ambient, sky, bounces
    def test_ambient_sky_and_bounces_reach_the_bake(self):
        floor = [SW.floor_quad(0, 0, 0, 256, 256)]
        lay = {'lights': [], 'lighting': {'ambient': {'color': [0.1, 0.2, 0.3], 'level': 1.0}, 'sky': [0.5, 0.25, 0.0], 'bounces': 1}}
        z, cfg, _, bj = bake_emit(self.work, floor, ['w/concrete_floor'], lay)
        self.assertEqual(cfg['bounces'], 1); self.assertEqual(bj['bounces_used'], 1)
        i = nearest(z, 128, 128)
        a = z['A'][z['tx_y'][i], z['tx_x'][i]]
        print('open floor: A %s (ambient 0.1 0.2 0.3 + sky 0.5 0.25 0)' % a.round(3))
        # open floor: every ray escapes -> the sky's radiance arrives as indirect light, plus the ambient fill (ao = 1)
        self.assertTrue(np.allclose(a, [0.6, 0.45, 0.3], atol=0.03))

    def test_the_sun_bounces_off_what_it_lights(self):
        # a floor and a wall at its west edge facing it; a red sun from the east (the light travels west and down) lights both. The wall's baked (indirect) light must hold
        # what the sunlit floor throws back; the sun's own light is in neither image (the engine adds it with the visibility S)
        quads = [SW.floor_quad(0, 0, 0, 256, 256), SW.wall_quad_x(0, 0, 0, 256, 0, 128, facing=1)]
        base = {'lights': [], 'lighting': {'ambient': {'color': [0, 0, 0], 'level': 0}, 'bounces': 2}}
        sun = {'lights': [], 'lighting': {'ambient': {'color': [0, 0, 0], 'level': 0}, 'bounces': 2, 'sun': {'dir': [-0.5, 0.0, -0.866], 'color': [2.0, 0.0, 0.0]}}}
        z0, _, _, _ = bake_emit(self.work, quads, ['w/concrete_floor'], base)
        z1, cfg, _, _ = bake_emit(self.work, quads, ['w/concrete_floor'], sun)
        i = nearest(z1, 0, 128, 40)                       # on the wall, 40 above the floor
        a0 = z0['A'][z0['tx_y'][i], z0['tx_x'][i]]; a1 = z1['A'][z1['tx_y'][i], z1['tx_x'][i]]
        print('wall beside a sunlit floor: baked light without the sun %s, with it %s' % (a0.round(3), a1.round(3)))
        self.assertTrue(np.allclose(a0, 0, atol=1e-6))
        alb = float(cfg['albedo']['w/concrete_floor'][0]) if 'w/concrete_floor' in cfg.get('albedo', {}) else float(cfg['default_albedo'][0])
        # the floor's radiance is albedo x 2 x 0.866; a wall at its edge sees it in about a third of its hemisphere (cosine weighted, 40 up a 256 deep floor)
        self.assertGreater(a1[0], 0.15 * alb * 2.0 * 0.866)
        self.assertLess(a1[0], 0.6 * alb * 2.0 * 0.866)
        self.assertTrue(np.allclose(a1[1:], 0, atol=1e-6))                     # a red sun: nothing in green and blue
        j = nearest(z1, 128, 128)
        self.assertTrue(np.allclose(z1['B'][z1['tx_y'][j], z1['tx_x'][j]], 0, atol=1e-6))      # the sun's own light is not baked as direct light
        self.assertGreater(z1['S'][z1['tx_y'][j], z1['tx_x'][j]], 0.99)                        # the floor sees the sun
        off = dict(sun, lighting=dict(sun['lighting']))
        z2, cfg2, _, _ = bake_emit(self.work, quads, ['w/concrete_floor'], off, extra_cfg={'sun_bounce': False})
        self.assertTrue(np.allclose(z2['A'][z2['tx_y'][i], z2['tx_x'][i]], 0, atol=1e-6))       # the switch

    def test_a_sky_box_is_no_occluder_and_no_chart(self):
        floor = [SW.floor_quad(0, 0, 0, 256, 256)]
        top = SW.floor_quad(1, -30000, -30000, 30000, 30000, z=30000.0)       # a huge surface of a sky material over the floor (material index 1)
        lay = {'lights': [], 'lighting': {'sky': [0.5, 0.25, 0.0], 'ambient': {'color': [0, 0, 0], 'level': 0}, 'bounces': 1}}
        z, cfg, _, bj = bake_emit(self.work, floor + [top], ['w/concrete_floor', 'w/sky_cp_zmb'], lay)
        i = nearest(z, 128, 128)
        a = z['A'][z['tx_y'][i], z['tx_x'][i]]
        self.assertTrue(np.allclose(a, [0.5, 0.25, 0.0], atol=0.03), a)       # the rays reach the sky through the sky box
        self.assertEqual(bj['triangles'], 2)                                   # the floor only: the box has no chart

    def test_defaults_are_unchanged(self):
        floor = [SW.floor_quad(0, 0, 0, 256, 256)]
        cfg, _ = layout_lights.build_config(self._emit(floor), texel=8.0)
        self.assertNotIn('bounces', cfg)                         # the baker's own default (2) stays for every route that does not ask
        cfg3, _ = layout_lights.build_config(self._emit(floor), texel=8.0, bounces_default=3)
        self.assertEqual(cfg3['bounces'], 3)                     # build-blend.ps1 --default-bounces 3
        self.assertEqual(cfg['ambient'], {'color': [0.02, 0.02, 0.022], 'ao_radius': 96})
        self.assertEqual(cfg['sky'], [0, 0, 0])

    def _emit(self, quads):
        src = os.path.join(self.work, 'emit0')
        SW.write_emit(src, SW.make_world(quads, ['w/concrete_floor']), {'lights': []})
        return src


if __name__ == '__main__':
    unittest.main()
