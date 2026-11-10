"""Map zone check: synthetic work folders with known defects (no real map data)."""
import io
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import iwz_zonecheck as zc  # noqa: E402

ZONE = 'mapz'
BSP = 'maps/cp/%s.d3dbsp' % ZONE
ENTS = '{\n157 "worldspawn"\n}\n{\n157 "script_model"\n1 "a"\n}\n{\n157 "script_model"\n}\n\x00'


def write(root, rel, data=b'x', when=None):
    path = os.path.join(root, *rel.split('/'))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        handle.write(data.encode('utf-8') if isinstance(data, str) else data)
    if when is not None:
        os.utime(path, (when, when))
    return path


MAP_ROWS = ['gfx_map,%s' % BSP, 'gfx_map_trzone,%s' % ZONE, 'col_map,%s' % BSP, 'com_map,%s' % BSP,
            'fx_map,%s' % BSP, 'glass_map,%s' % BSP, 'navmesh,%s' % BSP, 'map_ents,%s' % BSP,
            'aipaths,%s' % BSP, 'gfxlightmap,*lightmap0']
MAP_FILES = {
    BSP + '.gfxmap': b'g', 'transient_zones/%s.gfxmap_tr' % ZONE: b't', BSP + '.colmap': b'c',
    BSP + '.colmap.hkx': b'hkx-bytes', BSP + '.commap.json': '{"a": 1}', BSP + '.fxmap': b'f',
    BSP + '.glassmap': b'gl', BSP + '.navmesh': b'n', BSP + '.ents': ENTS, BSP + '.ents.data': b'd',
    BSP + '.aipaths': b'a', 'lightmaps/_lightmap0.json': '{"textures": []}',
}


def make_work(root, rows=None, files=None, ff=True, old=1000.0, new=2000.0):
    """A consistent work folder: every file at `old`, the compiled file at `new`."""
    rows = MAP_ROWS + ['material,mat_a', 'material,,mat_ref', 'image,*lightmap0_primary', 'image,img_a',
                       'xmodel,mod_a'] if rows is None else rows
    files = dict(MAP_FILES, **{'materials/mat_a.json': '{}', 'images/img_a.iw7Image': b'i',
                               'xmodel/mod_a.xmb': b'm'}) if files is None else files
    write(root, 'zone_source/%s.csv' % ZONE, '// header\nrequire,techsets_x\n' + '\n'.join(rows) + '\n', old)
    for rel, data in files.items():
        write(root, 'zonetool/%s/%s' % (ZONE, rel), data, old)
    if ff:
        write(root, 'zone/%s.ff' % ZONE, b'ff', new)
    return root


def codes(report, severity=None):
    return [f['code'] for f in report.findings if severity is None or f['severity'] == severity]


def find(report, code):
    return [f for f in report.findings if f['code'] == code]


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.work = os.path.join(self.tmp.name, 'work')
        self.saved = zc.collision_loader
        zc.collision_loader = lambda path: 12
        self.addCleanup(setattr, zc, 'collision_loader', self.saved)

    def run_audit(self, **kw):
        return zc.audit(self.work, ZONE, **kw)


class CleanTests(Base):
    def test_clean_folder_has_no_error_or_warning(self):
        make_work(self.work)
        report = self.run_audit()
        self.assertEqual(codes(report, 'error'), [])
        self.assertEqual(codes(report, 'warn'), [])
        self.assertEqual(report.facts['collision'][BSP + '.colmap.hkx'], {'triangles': 12})

    def test_missing_list_or_tree_is_an_error(self):
        report = self.run_audit()
        self.assertEqual(sorted(codes(report, 'error')), ['MAP-LIST-MISSING', 'MAP-TREE-MISSING'])

    def test_reference_toggle_and_empty_middle_field(self):
        make_work(self.work, rows=MAP_ROWS + ['reference,true', 'material,only_ref', 'reference,false',
                                              'material,real_one', 'material,,named_ref'],
                  files=dict(MAP_FILES, **{'materials/real_one.json': '{}'}))
        facts = self.run_audit().facts['types']['material']
        self.assertEqual((facts['rows'], facts['reference'], facts['with_file'], facts['without_file']), (3, 2, 1, 0))


class RowFileTests(Base):
    def test_listed_but_absent_is_an_error(self):
        files = dict(MAP_FILES)
        del files[BSP + '.navmesh']
        make_work(self.work, files=files)
        hits = find(self.run_audit(), 'MAP-ROW-NO-FILE')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['severity'], 'error')
        self.assertIn('navmesh', hits[0]['asset'])
        self.assertIn('never built', hits[0]['notice'])

    def test_both_files_of_collision_are_required(self):
        files = dict(MAP_FILES)
        del files[BSP + '.colmap.hkx']
        make_work(self.work, files=files)
        hits = find(self.run_audit(), 'MAP-ROW-NO-FILE')
        self.assertEqual(hits[0]['evidence']['missing'], [BSP + '.colmap.hkx'])

    def test_optional_companions_may_be_absent(self):
        make_work(self.work)    # no .ents.data.hkx, spawnList or spawners in the fixture
        self.assertEqual(find(self.run_audit(), 'MAP-ROW-NO-FILE'), [])

    def test_lookup_ignores_case_and_backslashes(self):
        make_work(self.work, rows=[r.replace('maps/cp', 'Maps\\CP') for r in MAP_ROWS])
        self.assertEqual(find(self.run_audit(), 'MAP-ROW-NO-FILE'), [])

    def test_lightmap_star_becomes_underscore(self):
        files = dict(MAP_FILES)
        del files['lightmaps/_lightmap0.json']
        make_work(self.work, files=files)
        self.assertIn('lightmaps/_lightmap0.json', find(self.run_audit(), 'MAP-ROW-NO-FILE')[0]['evidence']['missing'])


class PackedTests(Base):
    def test_built_but_not_listed_is_an_error(self):
        make_work(self.work, rows=[r for r in MAP_ROWS if not r.startswith('aipaths')])
        hits = find(self.run_audit(), 'MAP-FILE-NOT-PACKED')
        self.assertEqual([h['asset'] for h in hits], [BSP + '.aipaths'])
        self.assertIn('left out', hits[0]['notice'])

    def test_listed_file_is_silent(self):
        make_work(self.work)
        self.assertEqual(find(self.run_audit(), 'MAP-FILE-NOT-PACKED'), [])

    def test_row_with_other_name_leaves_the_file_unpacked(self):
        make_work(self.work, rows=[r.replace('col_map,' + BSP, 'col_map,maps/cp/other.d3dbsp') for r in MAP_ROWS])
        report = self.run_audit()
        self.assertIn(BSP + '.colmap', [h['asset'] for h in find(report, 'MAP-FILE-NOT-PACKED')])
        self.assertTrue(find(report, 'MAP-ROW-NO-FILE'))

    def test_unlisted_lightmap_and_transient_zone(self):
        make_work(self.work, rows=[r for r in MAP_ROWS if not r.startswith(('gfxlightmap', 'gfx_map_trzone'))])
        self.assertEqual(sorted(h['asset'] for h in find(self.run_audit(), 'MAP-FILE-NOT-PACKED')),
                         ['lightmaps/_lightmap0.json', 'transient_zones/%s.gfxmap_tr' % ZONE])

    def test_unknown_suffix_is_one_info_and_other_zone_is_noted(self):
        files = dict(MAP_FILES, **{BSP + '.weird': b'w', 'maps/cp/other.d3dbsp.gfxmap': b'o'})
        make_work(self.work, files=files)
        report = self.run_audit()
        unknown = find(report, 'MAP-FILE-UNKNOWN')
        self.assertEqual(len(unknown), 1)
        self.assertEqual(unknown[0]['severity'], 'info')
        self.assertEqual(unknown[0]['evidence']['files'], [BSP + '.weird'])
        self.assertEqual(find(report, 'MAP-FILE-NOT-PACKED'), [])
        self.assertEqual(len(find(report, 'MAP-FILE-OTHER-ZONE')), 1)


class KindTests(Base):
    def test_required_kind_missing_is_an_error(self):
        make_work(self.work, rows=[r for r in MAP_ROWS if not r.startswith('gfx_map,')])
        hits = [f for f in find(self.run_audit(), 'MAP-KIND-MISSING') if f['severity'] == 'error']
        self.assertEqual([h['asset'] for h in hits], ['gfx_map'])

    def test_each_required_kind_is_checked_separately(self):
        make_work(self.work, rows=[r for r in MAP_ROWS if r.split(',')[0] not in ('col_map', 'com_map', 'map_ents')])
        errors = [f['asset'] for f in find(self.run_audit(), 'MAP-KIND-MISSING') if f['severity'] == 'error']
        self.assertEqual(sorted(errors), ['col_map', 'com_map', 'map_ents'])

    def test_optional_kind_missing_is_info(self):
        make_work(self.work, rows=[r for r in MAP_ROWS if not r.startswith('fx_map')])
        hits = find(self.run_audit(), 'MAP-KIND-MISSING')
        self.assertEqual([(h['asset'], h['severity']) for h in hits], [('fx_map', 'info')])

    def test_unknown_map_kind_is_reported_not_passed(self):
        make_work(self.work, rows=MAP_ROWS + ['sky_map,%s' % BSP])
        hits = find(self.run_audit(), 'MAP-KIND-NOT-CHECKED')
        self.assertEqual([h['asset'] for h in hits], ['sky_map'])
        self.assertEqual(hits[0]['severity'], 'info')


class FileContentTests(Base):
    def test_empty_map_file_is_an_error(self):
        make_work(self.work, files=dict(MAP_FILES, **{BSP + '.navmesh': b''}))
        hits = find(self.run_audit(), 'MAP-FILE-EMPTY')
        self.assertEqual([h['asset'] for h in hits], [BSP + '.navmesh'])
        self.assertEqual(hits[0]['severity'], 'error')

    def test_bad_json_is_an_error_and_good_json_is_silent(self):
        make_work(self.work, files=dict(MAP_FILES, **{BSP + '.commap.json': '{"a": '}))
        hits = find(self.run_audit(), 'MAP-FILE-UNREADABLE')
        self.assertEqual([h['asset'] for h in hits], [BSP + '.commap.json'])
        make_work(self.tmp.name + '/ok')
        self.assertEqual(find(zc.audit(self.tmp.name + '/ok', ZONE), 'MAP-FILE-UNREADABLE'), [])

    def test_entities_are_counted(self):
        make_work(self.work)
        facts = self.run_audit().facts['entities']
        self.assertEqual(facts['count'], 3)
        self.assertEqual(facts['top20'], [['script_model', 2], ['worldspawn', 1]])

    def test_entity_file_in_another_format_is_info(self):
        make_work(self.work, files=dict(MAP_FILES, **{BSP + '.ents': b'\x01\x02binary'}))
        report = self.run_audit()
        self.assertEqual([f['severity'] for f in find(report, 'MAP-ENTS-NOT-READ')], ['info'])
        self.assertNotIn('entities', report.facts)

    def test_entity_file_without_closing_brace_is_not_read(self):
        make_work(self.work, files=dict(MAP_FILES, **{BSP + '.ents': '{\n157 "a"\n'}))
        self.assertTrue(find(self.run_audit(), 'MAP-ENTS-NOT-READ'))


class DuplicateTests(Base):
    def test_duplicate_row_warns(self):
        make_work(self.work, rows=MAP_ROWS + ['material,mat_a', 'material,mat_a', 'xmodel,mod_a'])
        hits = find(self.run_audit(), 'MAP-ROW-DUPLICATE')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['severity'], 'warn')
        self.assertEqual(hits[0]['evidence']['count'], 1)

    def test_same_name_of_different_type_is_silent(self):
        make_work(self.work, rows=MAP_ROWS + ['material,mat_a', 'image,mat_a'])
        self.assertEqual(find(self.run_audit(), 'MAP-ROW-DUPLICATE'), [])


class OtherTypeTests(Base):
    def rows_with_missing(self):
        return MAP_ROWS + ['material,mat_a', 'material,lost_one', 'material,,from_stock', 'material,,nowhere',
                           'brandnew,thing']

    def test_counts_and_no_stock_note(self):
        make_work(self.work, rows=self.rows_with_missing())
        report = self.run_audit()
        entry = report.facts['types']['material']
        self.assertEqual((entry['rows'], entry['with_file'], entry['without_file'], entry['reference']), (4, 1, 1, 2))
        self.assertEqual([f['severity'] for f in find(report, 'MAP-NO-STOCK')], ['info'])
        self.assertEqual(find(report, 'MAP-ROW-NOT-FOUND'), [])
        self.assertEqual([f['asset'] for f in find(report, 'MAP-TYPE-NOT-CHECKED')], ['types'])

    def test_stock_finds_rows_and_lists_the_rest(self):
        make_work(self.work, rows=self.rows_with_missing())
        stock = os.path.join(self.tmp.name, 'dump', 'zone_a')
        write(stock, 'materials/lost_one.json', '{}')
        write(stock, 'zone_a.csv', 'material,from_stock\n')
        report = self.run_audit(stock=[os.path.join(self.tmp.name, 'dump')])
        self.assertEqual(find(report, 'MAP-NO-STOCK'), [])
        by = {f['asset']: f for f in find(report, 'MAP-ROW-NOT-FOUND')}
        self.assertEqual(sorted(by), ['material (reference)'])
        self.assertEqual(by['material (reference)']['evidence']['first'], ['nowhere'])
        self.assertEqual(by['material (reference)']['severity'], 'info')

    def test_generated_lightmap_images_need_no_file(self):
        make_work(self.work)
        entry = self.run_audit().facts['types']['image']
        self.assertEqual((entry['generated'], entry['without_file']), (1, 0))

    def test_row_missing_everywhere_is_one_info_per_type(self):
        make_work(self.work, rows=MAP_ROWS + ['material,lost_a', 'material,lost_b', 'xmodel,lost_c'])
        stock = os.path.join(self.tmp.name, 'stock_zone')
        write(stock, 'materials/other.json', '{}')
        hits = find(self.run_audit(stock=[stock]), 'MAP-ROW-NOT-FOUND')
        self.assertEqual(sorted(h['asset'] for h in hits), ['material', 'xmodel'])
        self.assertEqual(next(h for h in hits if h['asset'] == 'material')['evidence']['count'], 2)


class FreshnessTests(Base):
    def test_compiled_older_than_a_map_file_warns(self):
        make_work(self.work)
        write(self.work, 'zonetool/%s/%s.navmesh' % (ZONE, BSP), b'n2', 3000.0)
        hits = find(self.run_audit(), 'MAP-FF-OLDER-THAN-SOURCE')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['severity'], 'warn')
        self.assertIn('navmesh', hits[0]['message'])
        self.assertIn('not running what was last built', hits[0]['notice'])

    def test_compiled_older_than_the_list_warns(self):
        make_work(self.work)
        os.utime(os.path.join(self.work, 'zone_source', ZONE + '.csv'), (3000.0, 3000.0))
        self.assertIn('source list', find(self.run_audit(), 'MAP-FF-OLDER-THAN-SOURCE')[0]['message'])

    def test_fresh_compiled_file_is_silent(self):
        make_work(self.work)
        self.assertEqual(find(self.run_audit(), 'MAP-FF-OLDER-THAN-SOURCE'), [])

    def test_missing_compiled_file_is_info(self):
        make_work(self.work, ff=False)
        hits = find(self.run_audit(), 'MAP-FF-MISSING')
        self.assertEqual([h['severity'] for h in hits], ['info'])


class EmitTests(Base):
    def make_emit(self, hkx=b'hkx-bytes'):
        emit = os.path.join(self.tmp.name, 'emit')
        write(emit, 'colmap.hkx', hkx)
        write(emit, 'navgraph.bin', b'nav')
        write(emit, 'layout.json', '{}')
        return emit

    def test_identical_collision_is_silent_and_the_rest_is_not_related(self):
        make_work(self.work)
        report = self.run_audit(emit=self.make_emit())
        self.assertEqual(find(report, 'MAP-EMIT-NOT-PACKED'), [])
        related = find(report, 'MAP-EMIT-NOT-RELATED')
        self.assertEqual(len(related), 1)
        self.assertEqual(sorted(related[0]['evidence']['files']), ['layout.json', 'navgraph.bin'])

    def test_different_collision_is_an_error(self):
        make_work(self.work)
        hits = find(self.run_audit(emit=self.make_emit(hkx=b'hkx-OTHER')), 'MAP-EMIT-NOT-PACKED')
        self.assertEqual([h['severity'] for h in hits], ['error'])
        self.assertIn('last emitted', hits[0]['notice'])

    def test_same_size_but_different_bytes_is_caught(self):
        make_work(self.work)
        self.assertTrue(find(self.run_audit(emit=self.make_emit(hkx=b'hkx-bytes'[::-1])), 'MAP-EMIT-NOT-PACKED'))

    def test_without_emit_nothing_is_compared(self):
        make_work(self.work)
        report = self.run_audit()
        self.assertEqual(find(report, 'MAP-EMIT-NOT-PACKED') + find(report, 'MAP-EMIT-NOT-RELATED'), [])


class CollisionTests(Base):
    def test_reader_failure_is_an_error_with_its_message(self):
        def broken(path):
            raise ValueError('no hknpCompressedMeshShapeData in ' + path)
        zc.collision_loader = broken
        make_work(self.work)
        hits = find(self.run_audit(), 'MAP-COLLISION-INVALID')
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]['severity'], 'error')
        self.assertIn('no hknpCompressedMeshShapeData', hits[0]['message'])

    def test_reader_that_cannot_load_is_info(self):
        def missing(path):
            raise ImportError('No module named hkcm')
        zc.collision_loader = missing
        make_work(self.work)
        hits = find(self.run_audit(), 'MAP-COLLISION-NOT-CHECKED')
        self.assertEqual([h['severity'] for h in hits], ['info'])

    def test_real_reader_rejects_garbage_bytes(self):
        zc.collision_loader = self.saved
        make_work(self.work)
        hits = find(self.run_audit(), 'MAP-COLLISION-INVALID')
        self.assertEqual(len(hits), 1)

    def test_empty_collision_file_is_not_reported_twice(self):
        zc.collision_loader = self.saved
        make_work(self.work, files=dict(MAP_FILES, **{BSP + '.colmap.hkx': b''}))
        report = self.run_audit()
        self.assertEqual(len(find(report, 'MAP-FILE-EMPTY')), 1)
        self.assertEqual(find(report, 'MAP-COLLISION-INVALID'), [])


class ReportShapeTests(Base):
    TOP = {'schema', 'tool', 'target', 'counts', 'findings', 'engine_questions', 'facts'}
    FINDING = {'severity', 'code', 'asset', 'message', 'proof', 'notice', 'evidence'}

    def test_dictionary_keys_are_pinned(self):
        files = dict(MAP_FILES)
        del files[BSP + '.navmesh']
        make_work(self.work, files=files)
        data = self.run_audit().as_dict()
        self.assertEqual(set(data), self.TOP)
        self.assertEqual(data['schema'], 'iw7.content-audit/1')
        self.assertEqual(data['tool'], 'map-zone-check')
        self.assertEqual(set(data['counts']), {'error', 'warn', 'info'})
        finding = next(f for f in data['findings'] if f['code'] == 'MAP-ROW-NO-FILE')
        self.assertEqual(set(finding), self.FINDING)
        self.assertEqual(finding['proof'], 'data')
        for f in data['findings']:
            self.assertTrue(set(f) <= self.FINDING | {'source'})

    def test_add_and_ask_follow_the_shared_contract(self):
        r = zc.Report('t', 'x')
        r.add('warn', 'T-A', 'a', 'm', notice='n', proof='engine', source='stock', value=1)
        self.assertEqual(r.findings[0], {'severity': 'warn', 'code': 'T-A', 'asset': 'a', 'message': 'm',
                                         'proof': 'engine', 'notice': 'n', 'source': 'stock', 'evidence': {'value': 1}})
        r.ask('see', 'a', 'q', 'w', cam='c')
        r.ask('see', 'a', 'q', 'w', cam='c')
        self.assertEqual(r.questions, [{'kind': 'see', 'asset': 'a', 'question': 'q', 'why': 'w', 'how': {'cam': 'c'}}])
        with self.assertRaises(ValueError):
            r.add('fatal', 'T-B', 'a', 'm')
        with self.assertRaises(ValueError):
            r.ask('smell', 'a', 'q', 'w')

    def test_text_lines_and_summary(self):
        r = zc.Report('t', 'x')
        r.add('error', 'T-E', 'a', 'broken', notice='players notice')
        r.add('info', 'T-I', 'b', 'fact')
        out = io.StringIO()
        r.write_text(out)
        lines = out.getvalue().splitlines()
        self.assertEqual(lines[0], '  ERROR T-E  a: broken')
        self.assertEqual(lines[1], '        player: players notice')
        self.assertEqual(lines[2], '  INFO  T-I  b: fact')
        self.assertEqual(lines[-1], 't x: errors 1, warnings 0, notes 1, engine questions 0')

    def test_exit_codes(self):
        r = zc.Report('t', 'x')
        self.assertEqual((r.exit_code(), r.exit_code(True)), (0, 0))
        r.add('warn', 'T-W', 'a', 'w')
        self.assertEqual((r.exit_code(), r.exit_code(True)), (0, 2))
        r.add('error', 'T-E', 'a', 'e')
        self.assertEqual((r.exit_code(), r.exit_code(True)), (1, 1))


class CommandLineTests(Base):
    def run_main(self, *extra):
        out = io.StringIO()
        saved, sys.stdout = sys.stdout, out
        try:
            code = zc.main([self.work, '--zone', ZONE] + list(extra))
        finally:
            sys.stdout = saved
        return code, out.getvalue()

    def test_clean_run_writes_json_and_exits_zero(self):
        make_work(self.work)
        target = os.path.join(self.tmp.name, 'out.json')
        code, text = self.run_main('--json', target, '--strict')
        self.assertEqual(code, 0)
        self.assertIn('errors 0, warnings 0', text.splitlines()[-1])
        with open(target, encoding='utf-8') as handle:
            self.assertEqual(json.load(handle)['schema'], 'iw7.content-audit/1')

    def test_error_exits_one_and_warning_exits_two_only_when_strict(self):
        make_work(self.work, files=dict(MAP_FILES, **{BSP + '.navmesh': b''}))
        self.assertEqual(self.run_main()[0], 1)
        make_work(self.tmp.name + '/w2')
        os.utime(os.path.join(self.tmp.name, 'w2', 'zone', ZONE + '.ff'), (10.0, 10.0))
        out = io.StringIO()
        saved, sys.stdout = sys.stdout, out
        try:
            plain = zc.main([self.tmp.name + '/w2', '--zone', ZONE])
            strict = zc.main([self.tmp.name + '/w2', '--zone', ZONE, '--strict'])
        finally:
            sys.stdout = saved
        self.assertEqual((plain, strict), (0, 2))

    def test_table_lists_every_kind(self):
        make_work(self.work)
        _code, text = self.run_main('--table')
        for kind in zc.MAP_KINDS:
            self.assertIn(kind, text)


if __name__ == '__main__':
    unittest.main()
