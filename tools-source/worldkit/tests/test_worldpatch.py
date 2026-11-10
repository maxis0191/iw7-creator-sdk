"""World patch tests on the synthetic world of the worldkit tests (4 props). No game file is read."""
import contextlib
import io
import json
import os
import shutil
import struct
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

import iw7_dump as D  # noqa: E402
import iw7_world as W  # noqa: E402
import iw7_worldpatch as P  # noqa: E402
import synthetic as S  # noqa: E402

REL = 'maps/x/synth.d3dbsp.gfxmap'
COL = 'maps/x/synth.d3dbsp.colmap'
CLIP_ORDER = [2, 0, 3, 1]          # the collision file lists the props in another order than the render world


def colmap_bytes():
    """A collision file for the synthetic props, written with the dump conventions."""
    d = S.Dumper()
    hdr = bytearray(P.CLIPMAP_SIZE)
    struct.pack_into('<I', hdr, 16, 2)
    struct.pack_into('<I', hdr, 40, len(S.PROPS))
    struct.pack_into('<I', hdr, 56, len(S.PROPS))
    d.array(None, bytes(hdr), 1, P.CLIPMAP_SIZE)
    d.string('maps/x/synth.d3dbsp')
    d.array(None, bytes(40), 2, 20)
    recs = b''
    for k in CLIP_ORDER:
        model, o, p, y, r, sc = S.PROPS[k]
        ax = S.axis_for(p, y, r)
        inv = [ax[j][i] / sc for i in range(3) for j in range(3)]
        recs += struct.pack('<Q3f9f8x', 0, float(o[0]), float(o[1]), float(o[2]), *inv)
    d.array(None, recs, len(S.PROPS), P.CLIP_STATIC)
    for k in CLIP_ORDER:
        d.asset(S.PROPS[k][0])
    d.array(None, struct.pack('<4i', 0, 1, 2, 3), 4, 4)
    d.absent()
    d.asset('maps/x/synth.d3dbsp')
    return bytes(d.out) + b'TAIL-NOT-READ'


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix='worldpatch-test-')
        cls.dump = os.path.join(cls.tmp, 'dump')
        S.write_world(cls.dump)
        S.put(os.path.join(cls.dump, *COL.split('/')), colmap_bytes())
        cls.db = os.path.join(cls.tmp, 'world.sqlite')
        W.build(cls.dump, cls.db, log=lambda *a: None)
        con = P.open_db(cls.db)
        cls.meta = P.db_meta(con)
        cls.props = P.db_props(con)
        con.close()
        cls.sha = P.db_fingerprint(cls.meta)[1]
        with open(os.path.join(cls.dump, *REL.split('/')), 'rb') as f:
            cls.src = f.read()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def patch(self, *ops, **over):
        p = {'schema': P.SCHEMA, 'map': self.meta['map_name'], 'fingerprint': self.sha, 'ops': list(ops)}
        p.update(over)
        return p

    def plan(self, *ops, **over):
        return P.resolve(P.check_patch(self.patch(*ops, **over)), self.props, self.meta)

    def out_dir(self, name):
        d = os.path.join(self.tmp, name)
        shutil.rmtree(d, ignore_errors=True)
        return d

    def records(self, buf):
        d = D.parse_gfxmap(buf, 'test')
        SD = D.layout('GfxStaticModelDrawInst')
        rows = []
        for i in range(d.draw_insts.count):
            base = d.draw_insts.off + SD.size * i
            rows.append({'origin': struct.unpack_from('<3f', buf, base + SD.off('origin[0]')),
                         'axis': struct.unpack_from('<9f', buf, base + SD.off('axis[0]')),
                         'scale': struct.unpack_from('<f', buf, base + SD.off('scale'))[0],
                         'raw': buf[base:base + SD.size]})
        return d, rows


class ResolveTests(Base):
    def test_box_selects_by_origin_whatever_the_corner_order(self):
        a = self.plan({'op': 'remove', 'box': [0, 0, -5, 100, 100, 50]})
        b = self.plan({'op': 'remove', 'box': [100, 100, 50, 0, 0, -5]})
        self.assertEqual([c['i'] for c in a['changes']], [0, 1, 2])
        self.assertEqual(a['changes'], b['changes'])
        self.assertEqual(a['counts'], {'changed': 3, 'removed': 3, 'moved': 0, 'collision_removed': 0})
        self.assertEqual(a['ops'], [{'op': 'remove', 'matched': 3}])

    def test_model_pattern_and_index_and_their_combination(self):
        self.assertEqual([c['i'] for c in self.plan({'op': 'remove', 'model': 'model_a'})['changes']], [0, 1, 3])
        self.assertEqual([c['i'] for c in self.plan({'op': 'remove', 'model': '*_b'})['changes']], [2])
        self.assertEqual([c['i'] for c in self.plan({'op': 'remove', 'model': 'MODEL_A'})['changes']], [])
        self.assertEqual([c['i'] for c in self.plan({'op': 'remove', 'index': [3, 1]})['changes']], [1, 3])
        both = self.plan({'op': 'remove', 'model': 'model_a', 'box': [0, 0, -5, 100, 100, 50]})
        self.assertEqual([c['i'] for c in both['changes']], [0, 1])

    def test_operations_apply_in_order_and_restore_undoes(self):
        p = self.plan({'op': 'remove', 'box': [0, 0, -5, 100, 100, 50]}, {'op': 'restore', 'index': 1})
        self.assertEqual([c['i'] for c in p['changes']], [0, 2])
        self.assertEqual(p['counts']['removed'], 2)
        self.assertEqual([o['matched'] for o in p['ops']], [3, 1])

    def test_the_plan_is_deterministic_and_carries_the_fingerprint(self):
        ops = [{'op': 'remove', 'model': 'model_a'}, {'op': 'move', 'index': 2, 'to': [5, 6, 7], 'yaw': 30}]
        a, b = self.plan(*ops), self.plan(*ops)
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))
        self.assertEqual((a['fingerprint'], a['file'], a['props'], a['schema']), (self.sha, REL, 4, P.PLAN_SCHEMA))

    def test_move_keeps_the_scale_and_clears_a_removal(self):
        p = self.plan({'op': 'remove', 'index': 2}, {'op': 'move', 'index': 2, 'to': [1.5, 2.5, 3.5]})
        self.assertEqual(p['counts'], {'changed': 1, 'removed': 0, 'moved': 1, 'collision_removed': 0})
        ch = p['changes'][0]
        self.assertEqual(ch['origin'], [1.5, 2.5, 3.5])
        self.assertEqual([round(v, 3) for v in ch['at']], [90.0, 90.0, 10.0])
        self.assertNotIn('scale', ch)
        self.assertNotIn('axis', ch)

    def test_a_patch_for_another_dump_or_map_is_refused(self):
        with self.assertRaisesRegex(P.PatchError, 'another dump'):
            self.plan({'op': 'remove', 'index': 0}, fingerprint='0' * 64)
        with self.assertRaisesRegex(P.PatchError, 'is for map'):
            self.plan({'op': 'remove', 'index': 0}, map='cp_other')
        with self.assertRaisesRegex(P.PatchError, 'does not exist'):
            self.plan({'op': 'remove', 'index': 4})

    def test_bad_patches_are_named(self):
        bad = [({'schema': 'x'}, 'not a world patch'),
               (self.patch(), 'non-empty'),
               (self.patch({'op': 'paint', 'index': 0}), 'must be one of'),
               (self.patch({'op': 'remove'}), 'at least one'),
               (self.patch({'op': 'remove', 'box': [1, 2, 3]}), '6 finite numbers'),
               (self.patch({'op': 'remove', 'index': 'a'}), 'index'),
               (self.patch({'op': 'remove', 'index': 0, 'to': [1, 2, 3]}), 'unknown field'),
               (self.patch({'op': 'move', 'index': [0], 'to': [1, 2, 3]}), 'one "index"'),
               (self.patch({'op': 'move', 'index': 0}), '3 finite numbers'),
               (self.patch({'op': 'move', 'index': 0, 'to': [1, 2, 3], 'scale': 0}), 'above 0'),
               (self.patch({'op': 'remove', 'index': 0}, fingerprint='abc'), 'fingerprint')]
        for patch, text in bad:
            with self.assertRaisesRegex(P.PatchError, text):
                P.check_patch(patch)


class ApplyTests(Base):
    def test_remove_writes_scale_zero_and_nothing_else(self):
        plan = self.plan({'op': 'remove', 'box': [0, 0, -5, 100, 100, 50]})
        out = self.out_dir('o1')
        m = P.apply(plan, self.dump, out)
        with open(m['out'], 'rb') as f:
            buf = f.read()
        self.assertEqual(len(buf), len(self.src))
        _, before = self.records(self.src)
        d, after = self.records(buf)
        self.assertEqual([r['scale'] for r in after], [0.0, 0.0, 0.0, 1.0])
        for b, a in zip(before, after):
            self.assertEqual(b['origin'], a['origin'])
            self.assertEqual(b['axis'], a['axis'])
        diff = [k for k in range(len(buf)) if buf[k] != self.src[k]]
        SD = D.layout('GfxStaticModelDrawInst')
        allowed = set()
        for i in (0, 1, 2):
            base = d.draw_insts.off + SD.size * i + SD.off('scale')
            allowed.update(range(base, base + 4))
        self.assertTrue(diff and set(diff) <= allowed)
        self.assertEqual((m['records_parsed'], m['edits'], m['edits_differing'], m['scale_zero_before'], m['scale_zero_after']),
                         (4, 3, 3, 0, 3))
        self.assertEqual(m['bytes_changed'], len(diff))
        self.assertTrue(os.path.isfile(os.path.join(out, 'worldpatch-plan.json')))
        with open(os.path.join(self.dump, *REL.split('/')), 'rb') as f:
            self.assertEqual(f.read(), self.src)          # the dump itself is untouched

    def test_the_patched_dump_builds_a_database_with_the_same_rows_but_the_scale(self):
        plan = self.plan({'op': 'remove', 'index': [1]})
        out = self.out_dir('o2')
        P.apply(plan, self.dump, out)
        copy = self.out_dir('o2dump')
        shutil.copytree(self.dump, copy)
        shutil.copy(os.path.join(out, *REL.split('/')), os.path.join(copy, *REL.split('/')))
        db2 = os.path.join(self.tmp, 'o2.sqlite')
        W.build(copy, db2, log=lambda *a: None)
        con = P.open_db(db2)
        rows = P.db_props(con)
        con.close()
        self.assertEqual(len(rows), 4)
        for a, b in zip(self.props, rows):
            if a['i'] == 1:
                self.assertEqual(b['scale'], 0.0)
                b = dict(b, scale=a['scale'])
            self.assertEqual(a, b)

    def test_move_shifts_origin_bounds_and_lighting_origin_and_turns_the_axis(self):
        plan = self.plan({'op': 'move', 'index': 1, 'to': [60, 40, 8], 'yaw': 90, 'scale': 1.5})
        out = self.out_dir('o3')
        m = P.apply(plan, self.dump, out)
        with open(m['out'], 'rb') as f:
            buf = f.read()
        d0, before = self.records(self.src)
        d, after = self.records(buf)
        self.assertEqual(after[1]['origin'], (60.0, 40.0, 8.0))
        self.assertEqual(after[1]['scale'], 1.5)
        # prop 1 is stored with yaw 90 (forward = +y); another quarter turn makes forward = -x, exactly
        for got, want in zip(after[1]['axis'][:3], (-1.0, 0.0, 0.0)):
            self.assertAlmostEqual(got, want, places=6)
        SI = D.layout('GfxStaticModelInst')
        for fld in ('bounds.mid[0]', 'lightingOrigin[0]'):
            old = struct.unpack_from('<3f', self.src, d0.smodel_insts.off + SI.size + SI.off(fld))
            new = struct.unpack_from('<3f', buf, d.smodel_insts.off + SI.size + SI.off(fld))
            self.assertEqual([round(n - o, 4) for n, o in zip(new, old)], [10.0, 20.0, 8.0])
        for i in (0, 2, 3):
            self.assertEqual(before[i]['raw'], after[i]['raw'])
        self.assertEqual(m['scale_zero_after'], 0)

    def test_verify_accepts_the_written_file_and_refuses_a_stray_change(self):
        plan = self.plan({'op': 'remove', 'index': 0})
        out = self.out_dir('o4')
        m = P.apply(plan, self.dump, out)
        self.assertEqual(P.verify(plan, self.dump, out)['sha256'], m['sha256'])
        with open(m['out'], 'r+b') as f:
            f.seek(len(self.src) - 1)
            last = f.read(1)
            f.seek(len(self.src) - 1)
            f.write(bytes([last[0] ^ 1]))
        with self.assertRaises((P.PatchError, D.WorldError)):
            P.verify(plan, self.dump, out)
        d, _ = self.records(self.src)
        SD = D.layout('GfxStaticModelDrawInst')
        buf = bytearray(self.src)
        struct.pack_into('<f', buf, d.draw_insts.off + SD.off('scale'), 0.0)
        struct.pack_into('<f', buf, d.draw_insts.off + SD.size * 3 + SD.off('origin[0]'), 7.0)   # not in the plan
        with self.assertRaisesRegex(P.PatchError, 'outside the planned fields'):
            P.verify_bytes(self.src, bytes(buf), plan)

    def test_apply_refuses_a_dump_that_changed_and_the_dump_folder_as_output(self):
        plan = self.plan({'op': 'remove', 'index': 0})
        other = self.out_dir('otherdump')
        shutil.copytree(self.dump, other)
        with open(os.path.join(other, *REL.split('/')), 'r+b') as f:
            f.seek(40)
            b = f.read(1)
            f.seek(40)
            f.write(bytes([b[0] ^ 0xFF]))
        with self.assertRaisesRegex(P.PatchError, 'not the one the plan was made for'):
            P.apply(plan, other, self.out_dir('o5'))
        with self.assertRaisesRegex(P.PatchError, 'is the dump folder'):
            P.apply(plan, self.dump, self.dump)
        with open(os.path.join(self.dump, *REL.split('/')), 'rb') as f:
            self.assertEqual(f.read(), self.src)

    def test_a_plan_for_other_models_is_refused(self):
        plan = self.plan({'op': 'remove', 'index': 0})
        plan['changes'][0]['model'] = 'something_else'
        with self.assertRaisesRegex(P.PatchError, 'the plan expects'):
            P.apply(plan, self.dump, self.out_dir('o6'))


class CollisionTests(Base):
    def test_remove_with_collision_takes_the_props_out_of_the_collision_list(self):
        plan = self.plan({'op': 'remove', 'index': [0, 2], 'collision': 'remove'}, {'op': 'remove', 'index': 3})
        self.assertEqual(plan['counts'], {'changed': 3, 'removed': 3, 'moved': 0, 'collision_removed': 2})
        self.assertEqual(plan['collision']['file'], COL)
        out = self.out_dir('c1')
        m = P.apply(plan, self.dump, out)
        self.assertEqual((m['collision_before'], m['collision_after'], m['collision_removed']), (4, 2, 2))
        src = S.get(os.path.join(self.dump, *COL.split('/')))
        new = S.get(m['collision_out'])
        a, b = P.parse_colmap(src), P.parse_colmap(new)
        # prop 0 is collision record 1, prop 2 is record 0: records 2 and 3 stay
        self.assertEqual(b['index'], [2, 3])
        self.assertEqual(len(src) - len(new), 8)
        self.assertEqual(struct.unpack_from('<I', new, b['hdr'] + 56)[0], 2)
        self.assertEqual(b['names'], a['names'])
        self.assertTrue(new.endswith(b'TAIL-NOT-READ'))
        self.assertEqual(src[a['sm'].off:a['list_rec']], new[b['sm'].off:b['list_rec']])

    def test_props_are_matched_by_model_origin_and_axis(self):
        plan = self.plan({'op': 'remove', 'index': [1], 'collision': 'remove'})
        gfx = self.src
        col = S.get(os.path.join(self.dump, *COL.split('/')))
        self.assertEqual(P.clip_records_for(plan, gfx, col, P.parse_colmap(col)), [CLIP_ORDER.index(1)])
        moved = bytearray(col)
        cm = P.parse_colmap(col)
        struct.pack_into('<f', moved, cm['sm'].off + P.CLIP_STATIC * CLIP_ORDER.index(1) + 8, 5000.0)
        with self.assertRaisesRegex(P.PatchError, 'no record in the collision file'):
            P.clip_records_for(plan, gfx, bytes(moved), P.parse_colmap(bytes(moved)))

    def test_without_the_option_no_collision_file_is_written(self):
        plan = self.plan({'op': 'remove', 'index': [0]})
        self.assertNotIn('collision', plan)
        out = self.out_dir('c2')
        m = P.apply(plan, self.dump, out)
        self.assertNotIn('collision_out', m)
        self.assertFalse(os.path.exists(os.path.join(out, *COL.split('/'))))

    def test_restore_gives_the_collision_back_and_bad_values_are_refused(self):
        plan = self.plan({'op': 'remove', 'index': [0, 1], 'collision': 'remove'}, {'op': 'restore', 'index': 0})
        self.assertEqual([(c['i'], c.get('collision')) for c in plan['changes']], [(1, 'remove')])
        with self.assertRaisesRegex(P.PatchError, 'collision'):
            P.check_patch(self.patch({'op': 'remove', 'index': 0, 'collision': 'yes'}))
        with self.assertRaisesRegex(P.PatchError, 'unknown field'):
            P.check_patch(self.patch({'op': 'restore', 'index': 0, 'collision': 'remove'}))

    def test_a_changed_collision_file_is_refused(self):
        plan = self.plan({'op': 'remove', 'index': [0], 'collision': 'remove'})
        other = self.out_dir('c3dump')
        shutil.copytree(self.dump, other)
        with open(os.path.join(other, *COL.split('/')), 'ab') as f:
            f.write(b'x')
        with self.assertRaisesRegex(P.PatchError, 'collision file of the dump'):
            P.apply(plan, other, self.out_dir('c3'))
        src = S.get(os.path.join(self.dump, *COL.split('/')))
        out, _ = P.patch_colmap(src, P.parse_colmap(src), [1])
        bad = bytearray(out)
        bad[-1] ^= 1
        with self.assertRaisesRegex(P.PatchError, 'outside the collision list'):
            P.verify_colmap(src, bytes(bad), [1])


class CliTests(Base):
    def run_cli(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = P.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_new_plan_apply_verify(self):
        patch = os.path.join(self.tmp, 'cli-patch.json')
        code, out, _ = self.run_cli('new', '--db', self.db, '--out', patch)
        self.assertEqual(code, 0)
        with open(patch, encoding='utf-8') as f:
            doc = json.load(f)
        self.assertEqual((doc['schema'], doc['map'], doc['fingerprint']), (P.SCHEMA, 'synth', self.sha))
        doc['ops'] = [{'op': 'remove', 'box': [0, 0, -5, 100, 100, 50]}]
        with open(patch, 'w', encoding='utf-8') as f:
            json.dump(doc, f)
        code, out, _ = self.run_cli('plan', '--patch', patch, '--db', self.db)
        self.assertEqual(code, 0)
        self.assertIn('plan: 3 props change (3 removed, 0 moved)', out)
        o = self.out_dir('cli-out')
        code, out, _ = self.run_cli('apply', '--patch', patch, '--db', self.db, '--dump', self.dump, '--out', o, '--json')
        self.assertEqual(code, 0)
        res = json.loads(out)
        self.assertEqual(res['measured']['scale_zero_after'], 3)
        self.assertEqual(res['plan']['counts']['removed'], 3)
        code, out, _ = self.run_cli('verify', '--plan', os.path.join(o, 'worldpatch-plan.json'), '--dump', self.dump, '--out', o)
        self.assertEqual(code, 0)
        self.assertIn('nothing else changed', out)

    def test_errors_exit_2_with_a_message(self):
        patch = os.path.join(self.tmp, 'cli-bad.json')
        with open(patch, 'w', encoding='utf-8') as f:
            json.dump({'schema': P.SCHEMA, 'map': 'synth', 'fingerprint': '1' * 64, 'ops': [{'op': 'remove', 'index': 0}]}, f)
        code, _, err = self.run_cli('plan', '--patch', patch, '--db', self.db)
        self.assertEqual(code, 2)
        self.assertIn('another dump', err)
        code, _, err = self.run_cli('plan', '--patch', patch, '--db', os.path.join(self.tmp, 'missing.sqlite'))
        self.assertEqual(code, 2)
        self.assertIn('no database', err)


if __name__ == '__main__':
    unittest.main()
