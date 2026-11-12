"""szdress: placement, checks and output on a synthetic scene and a synthetic models table (no game data)."""
import json, os, sqlite3, sys, tempfile, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import szdress as D

SCENE = {
    "map": "cp_t", "start": {"zone": "a", "points": [[200, 200, 0, 0]]},
    "zones": [{"id": "a", "boxes": [[0, 0, 1000, 600]], "floor": 0, "ceiling": 256, "spawners": {}}],
    "doors": [], "links": [], "interactions": [], "markers": [],
}
MODELS = [  # name, bounds
    ("box32", (-16, -16, 0, 16, 16, 40)),
    ("sign", (0, -10, -5, 3, 10, 5)),           # back at x = 0, faces +x
    ("tarp", (0, -2, 0, 104, 0, 56)),            # thin sheet
    ("lamp", (-4, -4, -10, 4, 4, 0)),            # hangs below its origin
]


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, 'm.sqlite')
        c = sqlite3.connect(self.db)
        c.execute('create table models (name, bmin_x, bmin_y, bmin_z, bmax_x, bmax_y, bmax_z)')
        for n, b in MODELS:
            c.execute('insert into models values (?,?,?,?,?,?,?)', (n,) + b)
        c.commit(); c.close()
        self.scene = os.path.join(self.tmp, 'scene.json')
        json.dump(SCENE, open(self.scene, 'w'))

    def run_spec(self, zone_spec, vignettes=None, layout=None):
        spec = {"vignettes": vignettes or {}, "zones": {"a": zone_spec}}
        sp, out = os.path.join(self.tmp, 'spec.json'), os.path.join(self.tmp, 'dress.json')
        json.dump(spec, open(sp, 'w'))
        lp = None
        if layout:
            lp = os.path.join(self.tmp, 'layout.json'); json.dump(layout, open(lp, 'w'))
        rep = D.build(sp, self.scene, self.db, out, lp)
        return rep, json.load(open(out))['a']

    def test_rotation_box(self):
        b = D.world_box((-10, -2, 0, 30, 2, 5), 0, 90, 0, 1)
        self.assertAlmostEqual(b[0], -2); self.assertAlmostEqual(b[1], -10); self.assertAlmostEqual(b[4], 30)

    def test_wall_piece_faces_room_and_touches_wall(self):
        rep, a = self.run_spec({"items": [{"m": "sign", "wall": "north", "s": 500, "h": 100, "id": "s"}]})
        p = a['props'][0]
        self.assertEqual(rep['errors'], [])
        self.assertAlmostEqual(p['yaw'] % 360, 270)              # front (+x) turned to -y, into the room
        self.assertAlmostEqual(p['at'][1], 600 - 0.5, places=3)   # back plane on the wall, 0.5 gap
        self.assertAlmostEqual(p['z'], 105)                       # bottom of the bounds at h 100

    def test_overlap_and_on(self):
        rep, _ = self.run_spec({"items": [{"m": "box32", "at": [100, 100], "id": "a"}, {"m": "box32", "at": [110, 100], "id": "b"}]})
        self.assertTrue(any('intersect' in e for e in rep['errors']))
        rep, a = self.run_spec({"items": [{"m": "box32", "at": [100, 100], "id": "a"},
                                          {"m": "box32", "at": [100, 100], "h": 40, "on": "a", "id": "b"}]})
        self.assertEqual(rep['errors'], [])

    def test_outside_and_budget(self):
        rep, _ = self.run_spec({"budget": 1, "items": [{"m": "box32", "at": [5, 100], "id": "a"}, {"m": "box32", "at": [300, 300], "id": "b"}]})
        self.assertTrue(any('outside' in e for e in rep['errors']))
        self.assertTrue(any('budget' in e for e in rep['errors']))

    def test_thin_clip_box_has_thickness(self):
        rep, a = self.run_spec({"items": [{"m": "tarp", "at": [300, 300], "clip": True, "id": "t"}]})
        cb = a['props'][0]['clip_box']
        self.assertGreaterEqual(cb[4] - cb[1], 4.0)
        self.assertGreater(cb[3] - cb[0], 90)

    def test_ceiling_hang_and_vignette_turn(self):
        vig = {"pair": {"items": [{"m": "box32", "at": [60, 0], "id": "x"}],
                        "lights": [{"at": [60, 0], "h": 50, "type": "omni", "color": [1, 1, 1], "radius": 100, "pool": 0.3}]}}
        rep, a = self.run_spec({"items": [{"m": "lamp", "at": [500, 300], "ceil": 0, "id": "l"},
                                          {"v": "pair", "at": [400, 200], "yaw": 90}]}, vig)
        lamp = next(p for p in a['props'] if p['id'] == 'l')
        self.assertAlmostEqual(lamp['z'], 256)                    # top of the bounds (0) at the ceiling
        box = next(p for p in a['props'] if p['id'].endswith('x'))
        self.assertAlmostEqual(box['at'][0], 400, places=3); self.assertAlmostEqual(box['at'][1], 260, places=3)
        self.assertGreater(a['lights'][0]['intensity'], 0)

    def test_scatter_keeps_off_props_and_spawners(self):
        lay = {"spawners": [{"zone": "a", "origin": [500, 300, 0], "kind": "ground"}], "interactions": [], "markers": [], "starts": []}
        rep, a = self.run_spec({"items": [{"m": "box32", "at": [480, 280], "clip": False, "near_ok": True, "id": "a"},
                                          {"scatter": {"n": 30, "rect": [420, 220, 580, 380], "seed": 1, "min_gap": 8, "pick": ["lamp"]}}]},
                               layout=lay)
        for p in a['props']:
            if 'scatter' in p['id']:
                self.assertGreaterEqual((p['at'][0] - 500) ** 2 + (p['at'][1] - 300) ** 2, 60 ** 2)


if __name__ == '__main__':
    unittest.main()
