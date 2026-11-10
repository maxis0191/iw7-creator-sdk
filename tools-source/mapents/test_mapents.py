"""Tests for iw7_mapents.py: synthetic entity text only (no game files)."""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import iw7_mapents as m  # noqa: E402

# A small map in the form the dump tool writes: numeric keys, a trailing NUL, duplicate keys, quotes in no value.
STOCK = '''{
157 "worldspawn"
9613 "1"
}
{
157 "script_struct"
822 "default_player_start"
543 "466.4 3680.2 0"
65 "0 270 0"
}
{
157 "script_struct"
822 "default_player_start"
543 "514.4 3680.2 0"
}
{
157 "script_model"
822 "hoop"
497 "park_basketball_arcade_hoop"
543 "100 200 300"
638 "hoop"
}
{
157 "trigger_multiple"
822 "hoop"
543 "110 200 300"
497 "?108"
638 "hoop_trig"
}
{
157 "script_origin"
543 "5000 -5000 40"
51961 "triggermodeldummydefault"
51961 "second value of a duplicate key"
}
\0'''


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = m.main(argv)
    return code, out.getvalue(), err.getvalue()


class Base(unittest.TestCase):
    def setUp(self):
        self._d = tempfile.TemporaryDirectory()
        self.tmp = self._d.name
        self.addCleanup(self._d.cleanup)
        self.ents, _ = m.parse_text(STOCK)

    def path(self, *parts):
        return os.path.join(self.tmp, *parts)

    def write(self, name, text):
        p = self.path(name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)
        return p

    def doc_file(self, ents=None, name='stock.ents.json'):
        p = self.path(name)
        m.save_doc(m.make_doc(ents if ents is not None else self.ents, 'cp_zmb', 'maps/cp/cp_zmb.d3dbsp.ents'), p)
        return p


class Parse(Base):
    def test_numeric_keys_get_their_names_and_duplicates_keep_order(self):
        self.assertEqual(len(self.ents), 6)
        self.assertEqual(self.ents[1], [['classname', 'script_struct'], ['targetname', 'default_player_start'],
                                        ['origin', '466.4 3680.2 0'], ['angles', '0 270 0']])
        self.assertEqual(self.ents[5][-2:], [['51961', 'triggermodeldummydefault'], ['51961', 'second value of a duplicate key']])

    def test_the_dumps_trailing_nul_is_ignored(self):
        ents, warns = m.parse_text(STOCK)
        self.assertEqual(warns, [])
        self.assertEqual(m.parse_text('{\n157 "a"\n}\n\0garbage { } ""')[0], [[['classname', 'a']]])

    def test_quoted_names_numeric_ids_and_case_are_the_same_key(self):
        ents, _ = m.parse_text('{\n"ClassName" "x"\n543 "1 2 3"\n"origin" "4 5 6"\n  "targetname" "t"\n}\n')
        self.assertEqual([k for k, _ in ents[0]], ['classname', 'origin', 'origin', 'targetname'])

    def test_comments_crlf_and_blank_lines(self):
        text = '// a comment\r\n/* start\r\nanything { here\r\nend */\r\n{\r\n157 "a"\r\n\r\n}\r\n'
        ents, warns = m.parse_text(text)
        self.assertEqual(ents, [[['classname', 'a']]])
        self.assertEqual(warns, [])

    def test_a_one_line_block_comment_is_refused_because_the_loader_would_swallow_the_file(self):
        with self.assertRaises(m.MapEntsError) as cm:
            m.parse_text('/* note */\n{\n157 "a"\n}\n')
        self.assertIn('loader', str(cm.exception))

    def test_malformed_text_is_an_error(self):
        for bad in ('{\n{\n}\n', '}\n', '157 "a"\n', '{\n157 "a"\n'):
            with self.assertRaises(m.MapEntsError, msg=bad):
                m.parse_text(bad)

    def test_what_the_loader_skips_is_reported(self):
        ents, warns = m.parse_text('{\nnot a pair\n157 "a"\n822 ""\n}\n')
        self.assertEqual(ents, [[['classname', 'a']]])
        self.assertEqual(len(warns), 2)
        self.assertIn('skips', warns[0])
        self.assertIn('drops', warns[1])

    def test_the_token_list_names_more_keys(self):
        p = self.write('tokens.cpp', '    { 0x9999, "my_custom_key" },\n    { 0x0001, "" },\n')
        try:
            self.assertEqual(m.load_tokens(p), 1)
            self.assertEqual(m.norm_key('39321'), 'my_custom_key')
            self.assertEqual(m.key_id('my_custom_key'), '39321')
        finally:
            m.KEYS.pop('39321', None)
            m.IDS.pop('my_custom_key', None)


class Text(Base):
    def test_numeric_form_round_trips_the_stock_text_exactly(self):
        text, by_name = m.to_text(self.ents)
        self.assertEqual(by_name, [])
        self.assertEqual(text, STOCK.split('\0')[0].rstrip('\n') + '\n')
        self.assertEqual(m.parse_text(text)[0], self.ents)

    def test_readable_form_quotes_every_known_name_and_keeps_unknown_numbers(self):
        text, by_name = m.to_text(self.ents, readable=True)
        self.assertIn('"classname" "script_model"', text)
        self.assertIn('51961 "triggermodeldummydefault"', text)
        self.assertIn('classname', by_name)
        self.assertEqual(m.parse_text(text)[0], self.ents)

    def test_a_key_with_no_id_is_written_by_name_and_reported(self):
        text, by_name = m.to_text([[['classname', 'a'], ['my_field', 'x']]])
        self.assertIn('"my_field" "x"', text)
        self.assertIn('157 "a"', text)
        self.assertEqual(by_name, ['my_field'])

    def test_values_the_loader_would_mangle_are_refused(self):
        for bad in ('a"b', 'two\nlines', ''):
            with self.assertRaises(m.MapEntsError, msg=repr(bad)):
                m.to_text([[['classname', bad]]])

    def test_numbers_and_vectors_are_written_as_the_game_reads_them(self):
        text, _ = m.to_text([[['classname', 'a'], ['origin', [1, 2.5, -3]], ['speed', 7], ['radius', 0.25]]])
        self.assertIn('543 "1 2.5 -3"', text)
        self.assertIn('691 "7"', text)
        self.assertIn('599 "0.25"', text)


class Query(Base):
    def test_stats(self):
        s = m.stats(self.ents)
        self.assertEqual(s['entities'], 6)
        self.assertEqual(s['by_classname'][0], ('script_struct', 2))
        self.assertEqual(dict(s['by_targetname'])['hoop'], 2)
        self.assertEqual(s['with_model'], 2)
        self.assertEqual(s['with_origin'], 5)
        self.assertEqual(s['origin_box'], [[100.0, -5000.0, 0.0], [5000.0, 3680.2, 300.0]])

    def test_selectors(self):
        pick = lambda sel: m.select(self.ents, sel)       # noqa: E731
        self.assertEqual(pick({'classname': 'script_struct'}), [1, 2])
        self.assertEqual(pick({'targetname': 'hoop'}), [3, 4])
        self.assertEqual(pick({'targetname': 'hoop', 'classname': 'script_model'}), [3])
        self.assertEqual(pick({'key': 'script_noteworthy', 'value': 'hoop_trig'}), [4])
        self.assertEqual(pick({'key': '638'}), [3, 4])                          # by number, no value: has the key
        self.assertEqual(pick({'script_noteworthy': 'hoop'}), [3])
        self.assertEqual(pick({'box': [90, 190, 290, 120, 210, 310]}), [3, 4])
        self.assertEqual(pick({'box': [120, 210, 310, 90, 190, 290]}), [3, 4])     # corners in any order
        self.assertEqual(pick({'near': [100, 200, 300], 'radius': 5}), [3])
        self.assertEqual(pick({'index': 4}), [4])
        self.assertEqual(pick({'index': [1, 5]}), [1, 5])
        self.assertEqual(pick({'classname': 'worldspawn', 'box': [0, 0, 0, 1, 1, 1]}), [])    # no origin: never in a box
        self.assertEqual(pick({'key': 'origin', 'value': [100, 200, 300]}), [3])

    def test_bad_selectors_are_refused(self):
        for bad in ({}, {'colour': 'red'}, {'value': 'x'}, {'near': [0, 0, 0]}, {'box': [1, 2, 3]}, {'index': -1}, {'index': 'x'},
                    {'radius': 3}):
            with self.assertRaises(m.MapEntsError, msg=str(bad)):
                m.check_selector(bad, 'test')


PATCH = {'schema': m.PATCH_SCHEMA}


def patch(**rules):
    return dict(PATCH, **rules)


class Patching(Base):
    def test_remove_set_add(self):
        out, rep = m.apply_patch(self.ents, patch(
            remove=[{'targetname': 'hoop'}],
            set=[{'where': {'classname': 'script_struct', 'index': 1}, 'values': {'angles': '0 90 0', 'script_noteworthy': 'x'}}],
            add=[{'classname': 'script_model', 'targetname': 'probe', 'origin': [1, 2, 3], 'model': 'm'}]))
        self.assertEqual((rep['before'], rep['after'], rep['removed'], rep['changed'], rep['added']), (6, 5, 2, 1, 1))
        self.assertEqual(rep['remove'][0]['matched'], 2)
        self.assertEqual(rep['remove'][0]['indices'], [3, 4])
        self.assertEqual(m.get(out[1], 'angles'), '0 90 0')
        self.assertEqual(m.get(out[1], 'script_noteworthy'), 'x')
        self.assertEqual(out[-1], [['classname', 'script_model'], ['targetname', 'probe'], ['origin', '1 2 3'], ['model', 'm']])
        self.assertEqual(rep['add'][0]['index'], 4)
        self.assertEqual(self.ents, m.parse_text(STOCK)[0], 'the input is not changed')

    def test_a_rule_that_matches_nothing_is_an_error_unless_optional(self):
        for rule in ({'remove': [{'targetname': 'nothing_like_this'}]},
                     {'set': [{'where': {'targetname': 'nothing_like_this'}, 'values': {'angles': '0 0 0'}}]},
                     {'remove': [{'classname': 'script_model', 'index': 1}]}):
            with self.assertRaises(m.MapEntsError, msg=str(rule)) as cm:
                m.apply_patch(self.ents, patch(**rule))
            self.assertIn('matched no entity', str(cm.exception))
        out, rep = m.apply_patch(self.ents, patch(remove=[{'targetname': 'nothing', 'optional': True}],
                                                  set=[{'where': {'targetname': 'nothing'}, 'values': {'angles': '1'}, 'optional': True}]))
        self.assertEqual(out, self.ents)
        self.assertEqual((rep['remove'][0]['matched'], rep['remove'][0]['optional']), (0, True))

    def test_every_failing_rule_is_named_in_one_error(self):
        with self.assertRaises(m.MapEntsError) as cm:
            m.apply_patch(self.ents, patch(remove=[{'targetname': 'a_missing'}, {'targetname': 'b_missing'}]))
        self.assertIn('remove[0]', str(cm.exception))
        self.assertIn('remove[1]', str(cm.exception))

    def test_a_change_to_a_removed_entity_matches_nothing(self):
        with self.assertRaises(m.MapEntsError) as cm:
            m.apply_patch(self.ents, patch(remove=[{'targetname': 'hoop'}],
                                           set=[{'where': {'script_noteworthy': 'hoop_trig'}, 'values': {'angles': '1 1 1'}}]))
        self.assertIn('left after the removals', str(cm.exception))

    def test_indexes_name_the_input_list_not_the_shrinking_one(self):
        out, rep = m.apply_patch(self.ents, patch(remove=[{'index': 1}], set=[{'where': {'index': 5}, 'values': {'speed': 3}}]))
        self.assertEqual(m.get(out[-1], 'speed'), '3')
        self.assertEqual(len(out), 5)

    def test_set_replaces_a_duplicate_key_once_and_null_deletes(self):
        out, _ = m.apply_patch(self.ents, patch(set=[{'where': {'index': 5}, 'values': {'51961': 'only'}},
                                                     {'where': {'index': 1}, 'values': {'angles': None}}]))
        self.assertEqual([p for p in out[5] if p[0] == '51961'], [['51961', 'only']])
        self.assertIsNone(m.get(out[1], 'angles'))

    def test_set_with_no_such_key_appends_it(self):
        out, _ = m.apply_patch(self.ents, patch(set=[{'where': {'index': 2}, 'values': {'script_noteworthy': 'new'}}]))
        self.assertEqual(out[2][-1], ['script_noteworthy', 'new'])

    def test_bad_patches_are_refused(self):
        for bad in ({'schema': 'x'}, patch(remover=[]), patch(add=[{'targetname': 'no_classname'}]), patch(add=[{}]),
                    patch(set=[{'where': {'index': 1}}]), patch(set=[{'where': {'index': 1}, 'values': {'a': 'b"c'}}]),
                    patch(set=[{'where': {'index': 1}, 'values': {'angles': ''}}]), patch(add=[{'classname': 'a', 'origin': True}]),
                    patch(set=[{'where': {'index': 1}, 'values': {'a': 'b'}, 'extra': 1}]), patch(remove=[{'colour': 1}]), 'x'):
            with self.assertRaises(m.MapEntsError, msg=str(bad)):
                m.apply_patch(self.ents, bad)

    def test_an_empty_patch_changes_nothing(self):
        out, rep = m.apply_patch(self.ents, patch())
        self.assertEqual(out, self.ents)
        self.assertEqual((rep['removed'], rep['changed'], rep['added']), (0, 0, 0))


class Diffing(Base):
    def test_removed_added_changed(self):
        new, _ = m.apply_patch(self.ents, patch(remove=[{'index': 2}],
                                                set=[{'where': {'index': 3}, 'values': {'model': 'other'}}],
                                                add=[{'classname': 'script_origin', 'origin': '9 9 9'}]))
        d = m.diff(self.ents, new)
        self.assertEqual([i for i, _ in d['removed']], [2])
        self.assertEqual(len(d['added']), 1)
        self.assertEqual(m.get(d['added'][0][1], 'classname'), 'script_origin')
        self.assertEqual([(i, j, k) for i, j, _, k in d['changed']], [(3, 2, [('model', 'park_basketball_arcade_hoop', 'other')])])

    def test_identical_lists_have_no_difference(self):
        d = m.diff(self.ents, m.parse_text(STOCK)[0])
        self.assertEqual((d['removed'], d['added'], d['changed']), ([], [], []))


class Commands(Base):
    def dump(self):
        self.write('dump/maps/cp/cp_zmb.d3dbsp.ents', STOCK)
        self.write('dump/maps/cp/cp_zmb.d3dbsp.ents.data', 'binary stuff')
        return self.path('dump')

    def test_export_finds_the_entity_text_among_the_dump_files(self):
        out = self.path('stock.ents.json')
        code, text, _ = run(['export', '--dump', self.dump(), '--out', out])
        self.assertEqual(code, 0, text)
        doc = m.load_doc(out)
        self.assertEqual((doc['map'], doc['loader_name'], doc['count']), ('cp_zmb', 'maps/cp/cp_zmb.d3dbsp.ents', 6))
        self.assertEqual(doc['index']['targetname']['hoop'], [3, 4])
        self.assertEqual(doc['index']['classname']['script_struct'], [1, 2])
        with open(out, encoding='utf-8') as f:
            self.assertEqual(len(f.read().split('\n')) > 8, True)           # one entity a line, not one long line

    def test_export_refuses_what_it_cannot_use(self):
        os.makedirs(self.path('empty'))
        self.assertEqual(run(['export', '--dump', self.path('empty'), '--out', self.path('a.json')])[0], 2)
        self.write('two/maps/cp/a.d3dbsp.ents', STOCK)
        self.write('two/maps/cp/b.d3dbsp.ents', STOCK)
        self.assertEqual(run(['export', '--dump', self.path('two'), '--out', self.path('a.json')])[0], 2)
        self.assertEqual(run(['export', '--out', self.path('a.json')])[0], 2)
        self.assertFalse(os.path.exists(self.path('a.json')))

    def test_stats_and_find_commands(self):
        f = self.doc_file()
        code, text, _ = run(['stats', f])
        self.assertEqual(code, 0)
        self.assertIn('script_struct', text)
        self.assertIn('hoop', text)
        s = json.loads(run(['stats', f, '--json'])[1])
        self.assertEqual(s['entities'], 6)
        code, text, _ = run(['find', f, '--targetname', 'hoop'])
        self.assertIn('2 matching entities', text)
        self.assertIn('#3 classname=script_model', text)
        hits = json.loads(run(['find', f, '--classname', 'script_struct', '--json'])[1])
        self.assertEqual([h['index'] for h in hits], [1, 2])
        self.assertIn('1 matching', run(['find', f, '--near', '100', '200', '300', '--radius', '5'])[1])
        self.assertIn('1 matching', run(['find', f, '--box', '90', '190', '290', '105', '210', '310'])[1])
        self.assertIn('1 matching', run(['find', f, '--key', 'script_noteworthy', '--value', 'hoop_trig'])[1])
        self.assertIn('1 matching', run(['find', f, '--index', '4'])[1])
        self.assertEqual(run(['find', f])[0], 2)

    def test_patch_command_writes_a_report_and_fails_on_a_dead_rule(self):
        f = self.doc_file()
        p = self.path('p.json')
        with open(p, 'w') as fh:
            json.dump(patch(remove=[{'targetname': 'hoop'}], add=[{'classname': 'script_origin', 'origin': '1 2 3'}]), fh)
        out = self.path('new.ents.json')
        code, text, _ = run(['patch', f, '--patch', p, '--out', out])
        self.assertEqual(code, 0, text)
        self.assertIn('6 -> 5', text)
        doc = m.load_doc(out)
        self.assertEqual(doc['patch']['removed'], 2)
        self.assertEqual(doc['count'], 5)
        self.assertEqual((doc['map'], doc['loader_name']), ('cp_zmb', 'maps/cp/cp_zmb.d3dbsp.ents'))
        with open(p, 'w') as fh:
            json.dump(patch(remove=[{'targetname': 'not_there'}]), fh)
        code, _, err = run(['patch', f, '--patch', p, '--out', self.path('never.json')])
        self.assertEqual(code, 2)
        self.assertIn('matched no entity', err)
        self.assertFalse(os.path.exists(self.path('never.json')))

    def test_write_puts_the_file_where_the_loader_looks_and_keeps_the_stock_bytes(self):
        f = self.doc_file()
        out = self.path('install')
        code, text, _ = run(['write', f, '--out-dir', out])
        self.assertEqual(code, 0, text)
        dest = os.path.join(out, 'maps', 'cp', 'cp_zmb.d3dbsp.ents')
        with open(dest, 'rb') as fh:
            data = fh.read()
        self.assertEqual(data.decode('ascii'), STOCK.split('\0')[0].rstrip('\n') + '\n')
        self.assertNotIn(b'\0', data)
        self.assertNotIn(b'\r', data)
        self.assertIn('iw7-mod/maps/cp/cp_zmb.d3dbsp.ents', text)

    def test_write_name_overrides_and_refusals(self):
        f = self.doc_file()
        out = self.path('install2')
        self.assertEqual(run(['write', f, '--out-dir', out, '--map', 'cp_rave'])[0], 0)
        self.assertTrue(os.path.isfile(os.path.join(out, 'maps', 'cp', 'cp_rave.d3dbsp.ents')))
        self.assertEqual(run(['write', f, '--out-dir', out, '--loader-name', 'maps/x/custom.ents'])[0], 0)
        self.assertTrue(os.path.isfile(os.path.join(out, 'maps', 'x', 'custom.ents')))
        self.assertEqual(run(['write', f, '--out-dir', out, '--loader-name', '../escape.ents'])[0], 2)
        self.assertEqual(run(['write', f, '--out-dir', out, '--loader-name', '/abs.ents'])[0], 2)
        self.assertEqual(run(['write', self.doc_file([], 'empty.ents.json'), '--out-dir', out])[0], 2)
        bad = self.write('bad.json', '{"schema": "other"}')
        self.assertEqual(run(['write', bad, '--out-dir', out])[0], 2)
        self.assertEqual(run(['write', self.path('missing.json'), '--out-dir', out])[0], 2)

    def test_write_readable_and_unknown_keys_are_said(self):
        f = self.doc_file()
        code, text, _ = run(['write', f, '--out-dir', self.path('r'), '--readable'])
        self.assertEqual(code, 0)
        with open(self.path('r', 'maps', 'cp', 'cp_zmb.d3dbsp.ents')) as fh:
            self.assertIn('"classname" "worldspawn"', fh.read())
        self.assertIn('written by name', text)

    def test_the_whole_chain_export_patch_write_and_diff(self):
        self.dump()
        a, b = self.path('a.json'), self.path('b.json')
        self.assertEqual(run(['export', '--dump', self.path('dump'), '--out', a])[0], 0)
        with open(self.path('p.json'), 'w') as fh:
            json.dump(patch(remove=[{'classname': 'trigger_multiple'}], set=[{'where': {'targetname': 'default_player_start', 'index': 1}, 'values': {'origin': [1, 2, 3]}}]), fh)
        self.assertEqual(run(['patch', a, '--patch', self.path('p.json'), '--out', b])[0], 0)
        code, text, _ = run(['diff', a, b])
        self.assertEqual(code, 0)
        self.assertIn('1 removed, 0 added, 1 changed', text)
        self.assertIn('origin: 466.4 3680.2 0 -> 1 2 3', text)
        d = json.loads(run(['diff', a, b, '--json'])[1])
        self.assertEqual((len(d['removed']), len(d['added']), len(d['changed'])), (1, 0, 1))
        self.assertEqual(run(['write', b, '--out-dir', self.path('o')])[0], 0)
        with open(self.path('o', 'maps', 'cp', 'cp_zmb.d3dbsp.ents'), encoding='ascii') as fh:
            ents, warns = m.parse_text(fh.read())
        self.assertEqual((len(ents), warns), (5, []))
        self.assertEqual(m.get(ents[1], 'origin'), '1 2 3')


class Hygiene(unittest.TestCase):
    def test_the_tool_files_are_ascii_and_name_no_machine(self):
        for name in ('iw7_mapents.py', 'test_mapents.py'):
            with open(os.path.join(HERE, name), encoding='utf-8') as f:
                text = f.read()
            text.encode('ascii')
            for banned in ('C:' + chr(92) + 'Users', 'ez' + 'valo', 'iw_game' + '_files'):
                self.assertNotIn(banned, text, name)
        for name in os.listdir(os.path.join(HERE, 'examples')):
            with open(os.path.join(HERE, 'examples', name), encoding='utf-8') as f:
                f.read().encode('ascii')


if __name__ == '__main__':
    unittest.main()
