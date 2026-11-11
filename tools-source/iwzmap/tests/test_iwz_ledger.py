"""Entity and pool ledger (TF8): synthetic sources and a synthetic template (no real map data)."""
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import iwz_ledger as lg  # noqa: E402


def ent(cls, **kv):
    body = '157 "%s"\n' % cls + ''.join('%s "%s"\n' % (k.lstrip('k'), v) for k, v in kv.items())
    return '{\n' + body + '}\n'


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', newline='\n') as h:
        h.write(text)


def template(root, triggers=4, static=3, scriptable=2):
    maps = os.path.join(root, 'maps', 'cp')
    ents = ent('worldspawn') + ''.join(ent('trigger_use', k497='?%d' % i) for i in range(triggers)) + ent('script_struct')
    write(os.path.join(maps, 'cp_zmb.d3dbsp.ents'), ents)
    lights = [{'type': 1}] + [{'type': 2}] * static + [{'type': 2}] * scriptable
    write(os.path.join(maps, 'cp_zmb.d3dbsp.commap.json'), json.dumps(
        {'primaryLight': lights, 'firstScriptablePrimaryLight': 1 + static, 'scriptablePrimaryLightCount': scriptable}))


def source(root, entities=3, triggers=1, lights=1, named=0, budget=None, uses_template_trigger=False):
    ents = ent('worldspawn') + ''.join(ent('script_model') for _ in range(entities - 1)) + ent('script_struct') * 2
    if uses_template_trigger:
        ents += ent('trigger_use', k497='?0')
    write(os.path.join(root, 'ents.txt'), ents)
    write(os.path.join(root, 'triggers.txt'), ''.join('28000001 100 100 100\n' for _ in range(triggers)))
    write(os.path.join(root, 'lights.txt'), ''.join('omni 0 0 0 1 1 1 100 40\n' for _ in range(lights)) +
          ''.join('omni 0 0 0 1 1 1 100 40 name=l%d\n' % i for i in range(named)))
    if budget is not None:
        write(os.path.join(root, 'entity_budget.json'), json.dumps({'rows': [{'package': 'X', 'entities': budget, 'why': 't'}]}))


class LedgerTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.tpl = os.path.join(self.tmp.name, 'tpl')
        self.src = os.path.join(self.tmp.name, 'src')
        template(self.tpl)

    def tearDown(self):
        self.tmp.cleanup()

    def test_counts_entities_without_structs(self):
        source(self.src, entities=3)
        o = lg.ledger(self.src, self.tpl)
        self.assertEqual(o['entities']['entity_list'], 3)
        self.assertEqual(o['entities']['structs'], 2)
        self.assertEqual(o['refusals'], [])

    def test_one_entity_over_the_ceiling_is_refused(self):
        source(self.src, entities=3, budget=7)
        self.assertEqual(lg.ledger(self.src, self.tpl, ceiling=10)['refusals'], [])
        source(self.src, entities=3, budget=8)
        refusals = lg.ledger(self.src, self.tpl, ceiling=10)['refusals']
        self.assertEqual(len(refusals), 1)
        self.assertIn('entities', refusals[0])

    def test_one_trigger_too_many_is_refused(self):
        source(self.src, triggers=4)
        self.assertEqual(lg.ledger(self.src, self.tpl)['refusals'], [])
        source(self.src, triggers=5)
        self.assertIn('trigger_shapes', ' '.join(lg.ledger(self.src, self.tpl)['refusals']))

    def test_template_trigger_named_by_the_source_is_not_free(self):
        source(self.src, triggers=4, uses_template_trigger=True)
        self.assertIn('trigger_shapes', ' '.join(lg.ledger(self.src, self.tpl)['refusals']))

    def test_lights_named_and_static_share_the_template_slots(self):
        source(self.src, lights=3, named=2)
        self.assertEqual(lg.ledger(self.src, self.tpl)['refusals'], [])
        source(self.src, lights=4, named=2)
        self.assertIn('lights', ' '.join(lg.ledger(self.src, self.tpl)['refusals']))

    def test_check_exit_code(self):
        source(self.src, triggers=5)
        argv = sys.argv
        try:
            sys.argv = ['iwz_ledger.py', 'check', self.src, '--template', self.tpl]
            import contextlib, io
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(lg.main(), 1)
        finally:
            sys.argv = argv


if __name__ == '__main__':
    unittest.main()
