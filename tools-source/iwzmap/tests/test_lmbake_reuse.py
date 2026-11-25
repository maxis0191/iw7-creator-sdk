"""A bake that starts from an earlier bake (bake/lmreuse.py, `lmbake.bake(reuse=...)`), on a small synthetic case: a long lit room, then the same room with
a second room added behind a doorway in its end wall, with a light, an emissive panel and an ambient of its own.

  - the long room's charts far from the new room are the seed's texels value for value, at the same place of the atlas (and the same bytes in the
    encoded image when the atlas keeps its size); the charts near the doorway are baked again; the new room's charts are lit
  - the same map again: everything is carried, nothing is traced
  - a seed of other settings is refused and the bake is a full one

The rule itself (`lmreuse.classify`, numpy only) is tested without the baker at the end.
Needs the bake environment (numba, scipy, Pillow) and texconv for the bakes. Run with the bake python: python -B tests/test_lmbake_reuse.py"""
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'bake'))
import numpy as np
import lmreuse

try:
    import synth_world as SW
    import lmbake
    import iw7image
    import layout_lights
    BAKER = os.path.isfile(iw7image.TEXCONV)
    WHY = 'texconv missing: %s' % iw7image.TEXCONV
except ImportError as e:                       # (the rule's tests below still run)
    BAKER, WHY = False, 'bake environment missing: %s' % e

LEN, WID, H, T = 1024, 256, 128, 128           # the long room: x 0..LEN, y 0..WID; tiles of T
FLOOR, WALL, CEIL, PANEL = 0, 1, 2, 3
MATS = ['w/concrete_floor', 'w/plaster_wall', 'w/ceiling_tile', 'w/emissive_panel_test']


def room(x0, x1, open_w=None, open_e=None):
    """floor, ceiling and walls of a room x0..x1 (y 0..WID, z 0..H) in tiles of T, facing inward; open_w / open_e: (y0, y1) left open in that end wall"""
    q = []
    for x in range(x0, x1, T):
        for y in range(0, WID, T):
            q.append(SW.floor_quad(FLOOR, x, y, x + T, y + T, 0.0))
            q.append((CEIL, [(x, y + T, H), (x + T, y + T, H), (x + T, y, H), (x, y, H)], (0, 0, -1)))
        q.append((WALL, [(x, 0, 0), (x + T, 0, 0), (x + T, 0, H), (x, 0, H)], (0, 1, 0)))
        q.append((WALL, [(x + T, WID, 0), (x, WID, 0), (x, WID, H), (x + T, WID, H)], (0, -1, 0)))
    for y in range(0, WID, T):
        if not (open_w and open_w[0] <= y < open_w[1]):
            q.append(SW.wall_quad_x(WALL, x0, y, y + T, 0, H, 1))
        if not (open_e and open_e[0] <= y < open_e[1]):
            q.append(SW.wall_quad_x(WALL, x1, y, y + T, 0, H, -1))
    return q


LIGHT_A = {'zone': 'a', 'origin': [128.0, 128.0, 100.0], 'type': 'omni', 'color': [1.0, 0.9, 0.7], 'radius': 420.0, 'intensity': 2.0, 'fixture': ''}
LIGHT_A2 = {'zone': 'a', 'origin': [640.0, 128.0, 100.0], 'type': 'omni', 'color': [1.0, 0.9, 0.7], 'radius': 420.0, 'intensity': 2.0, 'fixture': ''}
LIGHT_B = {'zone': 'b', 'origin': [LEN + 128.0, 128.0, 100.0], 'type': 'omni', 'color': [0.7, 0.85, 1.0], 'radius': 100.0, 'intensity': 2.0, 'fixture': ''}


def base_map():
    return room(0, LEN), {'lights': [LIGHT_A, LIGHT_A2]}


def merged_map(ambient_room=True):
    q = room(0, LEN, open_e=(0, T)) + room(LEN, LEN + 256, open_w=(0, T))
    q.append((PANEL, [(LEN + 250, 96, 40), (LEN + 250, 160, 40), (LEN + 250, 160, 88), (LEN + 250, 96, 88)], (-1, 0, 0)))
    lay = {'lights': [LIGHT_A, LIGHT_A2, LIGHT_B], 'lighting': {'emissive': {MATS[PANEL]: {'color': [1.0, 0.3, 0.6], 'strength': 2.0}}}}
    if ambient_room:
        lay['lighting']['ambient_rooms'] = [{'box': [LEN, 0, 0, LEN + 256, WID, H], 'ambient': [0.05, 0.02, 0.02], 'zone': 'b'}]
    return q, lay


def do_bake(work, name, quads, layout, reuse=None, quick=True, bounces=None, extra_cfg=None, rays=16):
    src = os.path.join(work, name + '_emit')
    SW.write_emit(src, SW.make_world(quads, MATS), layout)
    cfg, _rep = layout_lights.build_config(src, texel=8.0)
    cfg.update(extra_cfg or {})
    lj = os.path.join(work, name + '_lights.json')
    json.dump(cfg, open(lj, 'w'))
    out = os.path.join(work, name)
    if os.path.isdir(out):
        shutil.rmtree(out)
    rep = lmbake.bake(src, lj, out, texel=8.0, nrays=rays, bounces=bounces, quick=quick, denoise=0, reuse=reuse)
    z = np.load(os.path.join(out, 'bake.npz'))
    return out, rep, {k: z[k] for k in z.files}


def flat_E(z):
    return z['A'] + z['B'] * lmbake.oct_decode(z['D'])[..., 2:3]


def chart_centres(rep, z):
    """the mean texel position of every chart -> (charts, 3)"""
    n = len(rep['chart_list'])
    out = np.zeros((n, 3))
    for ci in range(n):
        a0, a1 = np.searchsorted(z['tx_chart'], [ci, ci + 1])
        out[ci] = z['tx_pos'][a0:a1].mean(0)
    return out


@unittest.skipUnless(BAKER, WHY)
class Reuse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.work = tempfile.mkdtemp(prefix='iwzreuse_')
        q, lay = base_map()
        cls.base_dir, cls.base_rep, cls.base = do_bake(cls.work, 'base', q, lay)
        q, lay = merged_map()
        cls.inc_dir, cls.inc_rep, cls.inc = do_bake(cls.work, 'inc', q, lay, reuse={'baked': cls.base_dir})
        cls.full_dir, cls.full_rep, cls.full = do_bake(cls.work, 'full', q, lay)
        cls.grain_dir, cls.grain_rep, cls.grain = do_bake(cls.work, 'grain', q, lay, extra_cfg={'seed': 1234})      # the same bake with other bounce rays

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.work, ignore_errors=True)

    def test_a_bake_leaves_what_a_later_bake_needs(self):
        for n in ('bake.npz', 'bake.json', 'bake_config.json', 'world_unbaked.bin'):
            self.assertTrue(os.path.isfile(os.path.join(self.base_dir, n)), n)
        self.assertEqual(open(os.path.join(self.base_dir, 'world_unbaked.bin'), 'rb').read(), open(os.path.join(self.work, 'base_emit', 'world.bin'), 'rb').read())
        self.assertNotIn('reuse', self.base_rep)

    def test_far_charts_are_the_seeds_texels_and_near_ones_are_baked_again(self):
        ru = self.inc_rep['reuse']
        self.assertTrue(ru['used'])
        cen = chart_centres(self.inc_rep, self.inc)
        why = [c['bake'] for c in self.inc_rep['chart_list']]
        carried = [k for k, w in enumerate(why) if w == 'carried']
        self.assertGreater(len(carried), 10)
        self.assertEqual(ru['charts_carried'], len(carried))
        self.assertEqual(ru['charts_carried'] + ru['charts_baked'], len(why))
        self.assertLess(cen[carried, 0].max(), LEN - lmreuse.REACH)              # nothing within reach of the doorway and the new room is carried
        for k, w in enumerate(why):
            if cen[k, 0] > LEN:
                self.assertEqual(w, 'new', (k, cen[k]))                          # the new room
            elif cen[k, 0] > LEN - 200:
                self.assertIn(w, ('light', 'near', 'shadow', 'new'), (k, cen[k]))     # in the new light's radius or beside the new geometry
        self.assertGreater(why.count('bounce'), 0)
        self.assertEqual(self.inc_rep['atlas'][0], self.base_rep['atlas'][0])    # the new charts go under the seed's rows (the atlas may get taller)
        # value for value, at the seed's place: the whole rectangle of every carried chart, in every image
        for k in carried:
            x, y, w_, h_ = self.inc_rep['chart_list'][k]['rect']
            for img in ('A', 'B', 'D', 'S'):
                self.assertTrue(np.array_equal(self.inc[img][y:y + h_, x:x + w_], self.base[img][y:y + h_, x:x + w_]), (k, img))
        # ... and the same bytes in the encoded light image (BC6H: 16 bytes a 4 x 4 block, the top half holds A, the bottom half B)
        def blocks(d, rep):
            with open(os.path.join(d, 'lightmap', 'secondary.dds'), 'rb') as f:
                raw = f.read()[148:]
            W, Hh = rep['atlas']
            return np.frombuffer(raw, np.uint8).reshape(2 * Hh // 4, W // 4, 16), Hh // 4
        (ba, ha), (bb, hb) = blocks(self.inc_dir, self.inc_rep), blocks(self.base_dir, self.base_rep)
        same = 0
        for k in carried:
            x, y, w_, h_ = self.inc_rep['chart_list'][k]['rect']
            for fa, fb in ((0, 0), (ha, hb)):
                sa = ba[fa + y // 4:fa + (y + h_) // 4, x // 4:(x + w_) // 4]
                self.assertTrue(np.array_equal(sa, bb[fb + y // 4:fb + (y + h_) // 4, x // 4:(x + w_) // 4]), k)
                same += sa.shape[0] * sa.shape[1]
        self.assertGreater(same, 100)

    def test_the_new_room_is_lit_and_the_carried_light_is_the_full_bakes(self):
        E_inc, E_full = flat_E(self.inc), flat_E(self.full)
        pos = self.inc['tx_pos']
        self.assertTrue(np.allclose(pos, self.full['tx_pos']))
        ei = E_inc[self.inc['tx_y'], self.inc['tx_x']].sum(1)
        ef = E_full[self.full['tx_y'], self.full['tx_x']].sum(1)
        new = pos[:, 0] > LEN + 8
        self.assertGreater(ei[new].mean(), 0.2)                                  # lit by its own light
        self.assertLess(abs(ei[new].mean() - ef[new].mean()) / ef[new].mean(), 0.02)     # as a full bake lights it
        # the carried texels against a full bake of the merged map: what they miss is the new room's bounced light beyond `reach`
        car = np.zeros(len(pos), bool)
        for k, c in enumerate(self.inc_rep['chart_list']):
            if c['bake'] == 'carried':
                a0, a1 = np.searchsorted(self.inc['tx_chart'], [k, k + 1])
                car[a0:a1] = True
        self.assertGreater(car.sum(), 1000)
        eg = flat_E(self.grain)[self.grain['tx_y'], self.grain['tx_x']].sum(1)
        d = np.abs(ei[car] - ef[car])
        g = np.abs(eg[car] - ef[car])                                            # the grain: two full bakes of the same map with other rays
        sys.stderr.write('carried texels %d: mean light %.4f; carried against a full bake: mean %.5f, 99th centile %.5f; the grain (two full bakes): mean %.5f, 99th centile %.5f
'
                         % (car.sum(), ef[car].mean(), d.mean(), np.percentile(d, 99), g.mean(), np.percentile(g, 99)))
        self.assertLess(d.mean(), 1.5 * g.mean())
        self.assertLess(np.percentile(d, 99), 1.5 * np.percentile(g, 99))
        # the border: a carried texel and the baked texel beside it differ as two neighbours do inside a full bake
        seam_inc, seam_full = self.seam(E_inc, self.inc, car), self.seam(E_full, self.full, car)
        sys.stderr.write('border between carried and baked floor tiles, %d texel pairs: mean step %.5f; the same pairs in a full bake %.5f
' % (len(seam_inc), seam_inc.mean(), seam_full.mean()))
        self.assertLess(seam_inc.mean(), 1.5 * seam_full.mean() + 0.5 * g.mean())

    def seam(self, E, z, car):
        """|E(a) - E(b)| of floor texel pairs 8 units apart along x where a is carried and b is not"""
        pos = z['tx_pos']
        fl = np.nonzero((np.abs(pos[:, 2]) < 0.1))[0]
        key = {(int(round(pos[i, 0])), int(round(pos[i, 1]))): i for i in fl}
        e = E[z['tx_y'], z['tx_x']].sum(1)
        out = []
        for (x, y), i in key.items():
            j = key.get((x + 8, y))
            if j is not None and car[i] and not car[j]:
                out.append(abs(e[i] - e[j]))
        return np.array(out)

    def test_the_same_map_again_carries_everything(self):
        q, lay = base_map()
        out, rep, z = do_bake(self.work, 'again', q, lay, reuse={'baked': self.base_dir})
        ru = rep['reuse']
        self.assertEqual((ru['charts_baked'], ru['texels_baked']), (0, 0))
        for img in ('A', 'B', 'D', 'S'):
            self.assertTrue(np.array_equal(z[img], self.base[img]), img)
        self.assertEqual(open(os.path.join(out, 'world.bin'), 'rb').read(), open(os.path.join(self.base_dir, 'world.bin'), 'rb').read())
        for n in ('secondary.dds', 'primary.dds', 'secondunorm.dds'):
            self.assertEqual(open(os.path.join(out, 'lightmap', n), 'rb').read(), open(os.path.join(self.base_dir, 'lightmap', n), 'rb').read(), n)
        self.assertEqual(open(os.path.join(out, 'lighting.txt')).read(), open(os.path.join(self.base_dir, 'lighting.txt')).read())

    def test_the_ambient_of_a_room_lights_its_texels_only(self):
        q, lay = merged_map(ambient_room=False)
        _o, _r, z = do_bake(self.work, 'noamb', q, lay)
        pos = z['tx_pos']
        new = pos[:, 0] > LEN + 8
        a_with = self.full['A'][self.full['tx_y'], self.full['tx_x']]
        a_without = z['A'][z['tx_y'], z['tx_x']]
        self.assertGreater((a_with[new, 0] - a_without[new, 0]).mean(), 0.01)    # red ambient of the room
        far = pos[:, 0] < LEN - 8
        self.assertTrue(np.array_equal(a_with[far], a_without[far]))

    def test_a_seed_of_other_settings_is_refused_and_the_bake_is_full(self):
        q, lay = merged_map()
        _o, rep, z = do_bake(self.work, 'refused', q, lay, reuse={'baked': self.base_dir}, bounces=1)
        self.assertFalse(rep['reuse']['used'])
        self.assertIn('bounces', rep['reuse']['refused'])
        _o, rep2, z2 = do_bake(self.work, 'full1', q, lay, bounces=1)
        self.assertTrue(np.array_equal(z['A'], z2['A']))
        _o, rep, _z = do_bake(self.work, 'refused2', q, lay, reuse={'baked': self.base_dir}, extra_cfg={'sky': [1, 1, 1]})
        self.assertIn('`sky`', rep['reuse']['refused'])
        _o, rep, _z = do_bake(self.work, 'refused3', q, lay, reuse={'baked': os.path.join(self.work, 'nothing')})
        self.assertIn('has no bake.npz', rep['reuse']['refused'])

    def test_a_light_changed_in_the_seeds_map_bakes_its_radius_again(self):
        q, lay = base_map()
        lay = {'lights': [LIGHT_A, dict(LIGHT_A2, origin=[900.0, 128.0, 100.0], radius=60.0)]}
        _o, rep, z = do_bake(self.work, 'moved', q, lay, reuse={'baked': self.base_dir})
        ru = rep['reuse']
        self.assertEqual((ru['changes']['lights_added'], ru['changes']['lights_removed']), (1, 1))
        self.assertGreater(ru['charts']['light'], 0)
        self.assertEqual(ru['charts']['new'], 0)


class Rule(unittest.TestCase):
    """lmreuse.classify on boxes (no baker)"""

    def boxes(self, xs):
        mn = np.array([[x, 0, 0] for x in xs], float)
        return mn, mn + np.array([64, 64, 0], float)

    def why(self, xs, **kw):
        mn, mx = self.boxes(xs)
        a = dict(mat_changed=np.zeros(len(xs), bool), lights_changed=[], lights_kept=[], gmn=np.zeros((0, 3)), gmx=np.zeros((0, 3)), g_emits=np.zeros(0, bool), rooms_changed=[])
        a.update(kw)
        return [lmreuse.REASONS[k] for k in lmreuse.classify(mn, mx, **a)]

    def test_nothing_changed_carries_everything(self):
        self.assertEqual(self.why([0, 500, 1000]), ['carried'] * 3)

    def test_a_changed_light_bakes_its_radius_and_what_it_bounces_to(self):
        w = self.why([0, 300, 700, 2000], lights_changed=[{'origin': [32, 32, 50], 'radius': 200}])
        self.assertEqual(w, ['light', 'bounce', 'carried', 'carried'])           # 300: within 256 of the lit chart; 700: not

    def test_new_geometry_bakes_what_is_near_and_what_it_shadows(self):
        g = np.array([[500.0, 0, 0]]), np.array([[520.0, 64, 100]])
        w = self.why([0, 300, 900, 3000], gmn=g[0], gmx=g[1], g_emits=np.array([False]), lights_kept=[{'origin': [100, 32, 50], 'radius': 1200}])
        self.assertEqual(w[0], 'carried')                                        # between the light and the new wall, more than `reach` from it
        self.assertEqual(w[1], 'near')
        self.assertEqual(w[2], 'shadow')                                         # behind the new wall, inside the light's radius
        self.assertEqual(w[3], 'carried')                                        # behind it too, but outside the radius
        w = self.why([0, 100], gmn=g[0], gmx=g[1], g_emits=np.array([True]))
        self.assertEqual(w, ['near', 'near'])                                    # an emitting piece reaches twice as far

    def test_material_and_ambient(self):
        w = self.why([0, 200, 800], mat_changed=np.array([True, False, False]))
        self.assertEqual(w, ['material', 'bounce', 'carried'])
        w = self.why([0, 200, 800], rooms_changed=[[700, -10, -10, 900, 100, 10]])
        self.assertEqual(w, ['carried', 'carried', 'ambient'])                   # an ambient is not bounced: its own texels only

    def test_lights_reaching_is_the_light_rule(self):
        mn, mx = self.boxes([0, 300, 700])
        r = lmreuse.lights_reaching([{'origin': [32, 32, 50], 'radius': 200}], mn, mx)
        self.assertEqual(r.tolist(), [[True, False, False]])

    def test_the_multiset_delta(self):
        a, r = lmreuse._multiset_delta([{'x': 1}, {'x': 1}, {'x': 2}], [{'x': 1}, {'x': 3}])
        self.assertEqual((a, r), ([{'x': 3}], [{'x': 1}, {'x': 2}]))


if __name__ == '__main__':
    unittest.main()
