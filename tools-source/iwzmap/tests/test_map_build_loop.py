"""The map build loop: the key of an incremental assembly, incremental equals full, one compiler, a map of its own.

Every test runs on a fake tree in a temporary folder: no game, no ZoneTool, no machine path.
"""
import hashlib
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import assemble_key as ak  # noqa: E402
import map_identity as mi  # noqa: E402
import split_zone as sz  # noqa: E402


def write(path, data=b''):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(data, str):
        data = data.encode()
    with open(path, 'wb') as f:
        f.write(data)


def snapshot(root, skip=()):
    out = {}
    for dp, _, fn in os.walk(root):
        for n in fn:
            if n in skip:
                continue
            p = os.path.join(dp, n)
            out[os.path.relpath(p, root).replace('\\', '/')] = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    return out


class FakeStock:
    """Three stock dumps the way assemble.py reads them: <dump>/<dump>.csv and the files the rows name."""

    def __init__(self, root):
        self.patch = os.path.join(root, 'patch_cp_zmb')
        self.tech = os.path.join(root, 'techsets_cp_zmb')
        self.zmb = os.path.join(root, 'cp_zmb')
        write(os.path.join(self.patch, 'patch_cp_zmb.csv'),
              'rawfile,cp/zombies/note.txt\nstringtable,cp/zombies/cp_zmb_cashimages.csv\nmaterial,mo/stockmat\n'
              'xmodel,,mo_model\nscriptfile,scripts/cp/zombies/zombie_x\n')
        write(os.path.join(self.patch, 'cp/zombies/note.txt'), 'note')
        write(os.path.join(self.patch, 'cp/zombies/cp_zmb_cashimages.csv'), '0,\n')
        write(os.path.join(self.patch, 'materials/mo/stockmat.json'), '{"stock": 1}')
        write(os.path.join(self.tech, 'techsets_cp_zmb.csv'), 'techset,ts1\n')
        write(os.path.join(self.tech, 'techsets/ts1.json'), '{}')
        write(os.path.join(self.zmb, 'cp_zmb.csv'), 'xmodel,mo_model\nmaterial,mo/other\n')
        write(os.path.join(self.zmb, 'xmodel/mo_model.xmb'), 'model')
        write(os.path.join(self.zmb, 'materials/mo/other.json'), '{"other": 1}')
        self.dumps = [self.patch, self.tech, self.zmb]


LEVEL = ('main()\n{\n    scripts\\cp\\maps\\cp_iwz\\cp_iwz_perks::init();\n'
         '    scripts\\cp\\maps\\cp_iwz\\cp_iwz_perks::register();\n}\n')


def run_assemble(work, mapname, level, dumps, incremental=False):
    cmd = [sys.executable, '-I', '-B', os.path.join(HERE, 'assemble.py'), work, mapname, level] + dumps
    if incremental:
        cmd.append('--incremental')
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    return r.stdout


class AssembleKeyTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stock = FakeStock(os.path.join(self.tmp, 'dump'))
        self.exe = os.path.join(self.tmp, 'zonetool.exe')
        write(self.exe, 'compiler-1')
        self.tool = os.path.join(self.tmp, 'tools')
        write(os.path.join(self.tool, 'perks', 'add_perks.py'), 'v1')
        self.asm = os.path.join(self.tmp, 'assemble.py')
        write(self.asm, 'asm-1')

    def key(self, text='args-1', extra=()):
        parts = [('text', 'map=cp_blend_a'), ('text', text), ('file', self.exe), ('file', self.asm), ('tree', os.path.join(self.tool, 'perks'))]
        parts += [('manifest', d) for d in self.stock.dumps] + list(extra)
        return ak.make_key(parts)[0]

    def test_same_inputs_same_key(self):
        self.assertEqual(self.key(), self.key())

    def test_every_input_moves_the_key(self):
        base = self.key()
        seen = {base}

        def moved(label):
            k = self.key()
            self.assertNotIn(k, seen, label + ' must change the key')
            seen.add(k)

        write(self.exe, 'compiler-2'); moved('the compiler')
        write(self.asm, 'asm-2'); moved('assemble.py')
        write(os.path.join(self.tool, 'perks', 'add_perks.py'), 'v2'); moved('a module source')
        write(os.path.join(self.tool, 'perks', 'new_module.gsc'), 'x'); moved('a new module file')
        write(os.path.join(self.stock.zmb, 'xmodel/mo_model.xmb'), 'modeL-longer'); moved('a dump file of another size')
        p = os.path.join(self.stock.zmb, 'materials/mo/other.json')
        st = os.stat(p)
        write(p, '{"other": 2}')                      # same size, new content
        os.utime(p, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
        moved('a dump file replaced by one of the same size (a re-dump: new time)')
        write(os.path.join(self.stock.patch, 'extra.bin'), 'z'); moved('a new dump file')
        os.remove(os.path.join(self.stock.tech, 'techsets/ts1.json')); moved('a removed dump file')
        self.assertNotIn(self.key(text='args-2'), seen, 'the arguments')

    def test_stamp_sees_a_re_dump_and_a_replaced_file_but_not_a_untouched_tree(self):
        def stamp():
            return ak.make_key([('stamp', self.stock.zmb)])[0]
        k = stamp()
        self.assertEqual(k, stamp())
        csv = os.path.join(self.stock.zmb, 'cp_zmb.csv')
        st = os.stat(csv)
        write(csv, 'xmodel,mo_model\nmaterial,mo/other\nmaterial,mo/third\n')
        self.assertNotEqual(k, stamp(), 'the dump csv is rewritten by every dump run')
        k = stamp()
        os.remove(os.path.join(self.stock.zmb, 'xmodel', 'mo_model.xmb'))      # a file replaced below a directory: the directory's time moves
        write(os.path.join(self.stock.zmb, 'xmodel', 'mo_model.xmb'), 'replaced')
        os.utime(os.path.join(self.stock.zmb, 'xmodel'), ns=(st.st_atime_ns, st.st_mtime_ns + 7_000_000_000))   # the time a real replace would leave
        self.assertNotEqual(k, stamp())

    def test_dump_order_is_part_of_the_key(self):
        a = ak.make_key([('manifest', self.stock.patch), ('manifest', self.stock.zmb)])[0]
        b = ak.make_key([('manifest', self.stock.zmb), ('manifest', self.stock.patch)])[0]
        self.assertNotEqual(a, b)

    def test_missing_input_is_an_error_not_an_empty_input(self):
        with self.assertRaises(FileNotFoundError):
            ak.make_key([('manifest', os.path.join(self.tmp, 'nope'))])
        with self.assertRaises(FileNotFoundError):
            ak.make_key([('file', os.path.join(self.tmp, 'nope.exe'))])
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'assemble_key.py'), '--file', os.path.join(self.tmp, 'nope.exe')],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)

    def test_command_line_matches_the_library(self):
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'assemble_key.py'), '--text', 'map=cp_blend_a', '--text', 'args-1',
                            '--file', self.exe, '--file', self.asm, '--tree', os.path.join(self.tool, 'perks')] +
                           sum([['--manifest', d] for d in self.stock.dumps], []), capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), self.key())

    def test_argfile_gives_the_same_key_as_the_command_line(self):
        long_text = 'kit=' + ','.join('model_%d' % i for i in range(5000))        # 50k characters: over the Windows command line
        args = ['--text', 'map=cp_blend_a', '--text', long_text, '--file', self.exe, '--file', self.asm]
        af = os.path.join(self.tmp, 'args.json')
        with open(af, 'w', encoding='utf-8') as f:
            json.dump(args, f)
        r = subprocess.run([sys.executable, '-I', '-B', os.path.join(HERE, 'assemble_key.py'), '--argfile', af], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(r.stdout.strip(), ak.make_key([('text', 'map=cp_blend_a'), ('text', long_text), ('file', self.exe), ('file', self.asm)])[0])
        self.assertEqual(ak.expand_argfiles(['--text', 'a', '--argfile', af, '--text', 'z'])[-2:], ['--text', 'z'])


class AssembleTreeTest(unittest.TestCase):
    """Incremental assembly leaves the same tree and the same zone csv as a full one: the property the key protects."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stock = FakeStock(os.path.join(self.tmp, 'dump'))
        self.level = os.path.join(self.tmp, 'level.gsc')
        write(self.level, LEVEL)

    def generated(self, work, mapname, files):
        gen = os.path.join(work, 'dump', mapname)
        if os.path.isdir(gen):
            shutil.rmtree(gen)
        for rel, data in files.items():
            write(os.path.join(gen, rel), data)

    G1 = {'maps/cp/cp_blend_a.d3dbsp.ents': 'ents-1', 'materials/mo/stockmat.json': '{"generated": 1}', 'gone.txt': 'will go'}
    G2 = {'maps/cp/cp_blend_a.d3dbsp.ents': 'ents-2', 'added.txt': 'new'}

    def test_incremental_equals_full(self):
        m = 'cp_blend_a'
        inc, full = os.path.join(self.tmp, 'inc'), os.path.join(self.tmp, 'full')
        self.generated(inc, m, self.G1)
        run_assemble(inc, m, self.level, self.stock.dumps)
        dst = os.path.join(inc, 'zonetool', m)
        self.assertEqual(open(os.path.join(dst, 'materials/mo/stockmat.json')).read(), '{"generated": 1}', 'a generated file shadows the stock one')
        write(os.path.join(dst, 'sentinel.kept'), 'x')            # not from any dump or generated file: only a kept tree still has it
        self.generated(inc, m, self.G2)
        out = run_assemble(inc, m, self.level, self.stock.dumps, incremental=True)
        self.assertIn('incremental:', out)
        self.assertTrue(os.path.exists(os.path.join(dst, 'sentinel.kept')), 'the incremental assembly kept the tree')
        self.assertEqual(open(os.path.join(dst, 'materials/mo/stockmat.json')).read(), '{"stock": 1}', 'the stock file the old world shadowed is back')
        self.assertFalse(os.path.exists(os.path.join(dst, 'gone.txt')), 'a file the new world no longer has is gone')
        self.generated(full, m, self.G2)
        run_assemble(full, m, self.level, self.stock.dumps)
        a = snapshot(dst, skip=('sentinel.kept',))
        b = snapshot(os.path.join(full, 'zonetool', m))
        self.assertEqual(a, b, 'same tree as a full assembly')
        ca = open(os.path.join(inc, 'zone_source', m + '.csv')).read()
        cb = open(os.path.join(full, 'zone_source', m + '.csv')).read()
        self.assertEqual(ca, cb, 'same zone csv as a full assembly')

    def test_other_dumps_assemble_everything(self):
        m = 'cp_blend_a'
        work = os.path.join(self.tmp, 'w')
        self.generated(work, m, self.G1)
        run_assemble(work, m, self.level, self.stock.dumps)
        dst = os.path.join(work, 'zonetool', m)
        write(os.path.join(dst, 'sentinel.kept'), 'x')
        out = run_assemble(work, m, self.level, self.stock.dumps[:2], incremental=True)
        self.assertIn('assembling everything', out)
        self.assertFalse(os.path.exists(os.path.join(dst, 'sentinel.kept')))

    def test_references_held_in_full_become_full_rows(self):
        m = 'cp_blend_a'
        work = os.path.join(self.tmp, 'w')
        self.generated(work, m, self.G1)
        run_assemble(work, m, self.level, self.stock.dumps)
        rows = open(os.path.join(work, 'zone_source', m + '.csv')).read().splitlines()
        self.assertIn('xmodel,mo_model', rows)
        self.assertNotIn('xmodel,,mo_model', rows)


class MapIdentityTest(unittest.TestCase):
    """A map with its own name: no cp_iwz left in the zone tree, the script paths, the tables, the arena."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stock = FakeStock(os.path.join(self.tmp, 'dump'))

    def build(self, m):
        level = os.path.join(self.tmp, 'level.gsc')
        write(level, LEVEL)
        work = os.path.join(self.tmp, 'work_' + m)
        write(os.path.join(work, 'dump', m, 'maps/cp/%s.d3dbsp.ents' % m), 'ents')
        run_assemble(work, m, level, self.stock.dumps)
        return work

    def test_names(self):
        for ok in ('cp_blend_a', 'cp_blend_b', 'cp_iwz', 'cp_a1'):
            self.assertEqual(mi.check_name(ok), ok)
        for bad in ('blend', 'cp_Blend', 'cp_', 'cp_blend a', 'cp_zmb', 'cp_blend_abcdefgh', 'cp_x_art', 'cp_x_base', 'cp_x_load', 'cp_blend-1', ''):
            with self.assertRaises(ValueError, msg=bad):
                mi.check_name(bad)

    def test_title_and_arena(self):
        self.assertEqual(mi.default_title('cp_blend_a'), 'BLEND A')
        text = mi.arena_text('cp_blend_a', 'BLEND A')
        self.assertIn('map\t\t\t"cp_blend_a"', text)
        self.assertIn('mapimage    "image_cp_blend_a"', text)
        self.assertIn('mapvoteimage "image_cp_blend_a_vote"', text)
        self.assertIn('longname\t"BLEND A"', text)
        self.assertTrue(text.startswith('{\r\n') and text.endswith('}\r\n'))
        self.assertNotIn('cp_iwz', text)
        self.assertEqual(text.count('{'), 1)
        for bad in ('', 'x' * 31, 'a"b', 'tab\there'):
            with self.assertRaises(ValueError, msg=bad):
                mi.arena_text('cp_blend_a', bad)

    def test_two_maps_share_nothing(self):
        a, b = mi.arena_text('cp_blend_a', 'BLEND A'), mi.arena_text('cp_blend_b', 'BLEND B')
        self.assertNotEqual(a, b)
        self.assertNotIn('cp_blend_b', a)
        self.assertNotIn('cp_blend_a', b)

    def test_strings_carry_the_title(self):
        base = os.path.join(self.tmp, 'base.json')
        write(base, json.dumps({'IWZ_PERK': 'x'}))
        out = mi.strings('cp_blend_a', 'BLEND A', base)
        self.assertEqual(out['IWZ_MAPNAME_CP_BLEND_A'], 'BLEND A')
        self.assertEqual(out['IWZ_PERK'], 'x')

    def test_resolve_reads_the_exporter_name(self):
        src = os.path.join(self.tmp, 'emit')
        write(os.path.join(src, 'layout.json'), json.dumps({'map': 'cp_blend_a'}))
        self.assertEqual(mi.resolve(src), 'cp_blend_a')
        self.assertEqual(mi.resolve(src, 'cp_blend_a'), 'cp_blend_a')
        with self.assertRaises(ValueError):
            mi.resolve(src, 'cp_blend_b')                       # an emit named cp_blend_a cannot be renamed at build time
        write(os.path.join(src, 'layout.json'), json.dumps({'map': 'cp_iwz'}))
        self.assertEqual(mi.resolve(src, 'cp_blend_b'), 'cp_blend_b')           # a cp_iwz emit without modules can
        write(os.path.join(src, 'modules', 'cp_iwz_post.gsc'), 'x')
        with self.assertRaises(ValueError):
            mi.resolve(src, 'cp_blend_b')                       # but not one whose modules are named after cp_iwz
        os.remove(os.path.join(src, 'layout.json'))
        self.assertEqual(mi.resolve(src), 'cp_iwz')
        write(os.path.join(src, 'layout.json'), json.dumps({'map': 'Bad Name'}))
        with self.assertRaises(ValueError):
            mi.resolve(src)

    def test_zone_tree_of_a_renamed_map(self):
        m = 'cp_blend_a'
        work = self.build(m)
        dst = os.path.join(work, 'zonetool', m)
        csv = open(os.path.join(work, 'zone_source', m + '.csv')).read()
        script = open(os.path.join(dst, 'scripts', 'cp', 'maps', m, m + '.gsc')).read()
        self.assertIn('scripts\\cp\\maps\\%s\\cp_iwz_perks::init' % m, script)      # the perk module sits under the map, keeps its own name
        self.assertIn('scripts\\cp\\maps\\%s\\cp_iwz_perks::register' % m, script)
        self.assertNotIn('maps\\cp_iwz\\', script)
        self.assertIn('rawfile,scripts/cp/maps/%s/%s.gsc' % (m, m), csv)
        self.assertIn('stringtable,cp/zombies/%s_cashimages.csv' % m, csv)          # the stock table renamed from cp_zmb
        self.assertIn('stringtable,cp/zombies/%s_playercash_images.csv' % m, csv)   # the content table the engine looks up by level.script
        self.assertTrue(os.path.isfile(os.path.join(dst, 'cp', 'zombies', '%s_playercash_images.csv' % m)))
        self.assertIn('gfx_map_trzone,' + m, csv)
        self.assertIn('maps/cp/%s.d3dbsp' % m, csv)
        self.assertNotIn('cp_iwz', csv, 'no cp_iwz row in the zone csv')
        names = [os.path.relpath(os.path.join(dp, n), dst) for dp, _, fn in os.walk(dst) for n in fn + [os.path.basename(dp)]]
        self.assertFalse([n for n in names if 'cp_iwz' in n], 'no cp_iwz file name in the zone tree')
        for rel in os.listdir(os.path.join(dst, 'cp', 'zombies')):
            data = open(os.path.join(dst, 'cp', 'zombies', rel), 'rb').read()
            self.assertNotIn(b'cp_iwz', data)

    def test_cp_iwz_is_still_station_zero(self):
        work = self.build('cp_iwz')
        csv = open(os.path.join(work, 'zone_source', 'cp_iwz.csv')).read()
        self.assertIn('stringtable,cp/zombies/cp_iwz_playercash_images.csv', csv)
        script = open(os.path.join(work, 'zonetool', 'cp_iwz', 'scripts', 'cp', 'maps', 'cp_iwz', 'cp_iwz.gsc')).read()
        self.assertEqual(script, LEVEL)

    def test_two_maps_in_one_work_folder(self):
        level = os.path.join(self.tmp, 'level.gsc')
        write(level, LEVEL)
        work = os.path.join(self.tmp, 'shared')
        for m in ('cp_blend_a', 'cp_blend_b'):
            write(os.path.join(work, 'dump', m, 'maps/cp/%s.d3dbsp.ents' % m), m)
            run_assemble(work, m, level, self.stock.dumps)
        for m, other in (('cp_blend_a', 'cp_blend_b'), ('cp_blend_b', 'cp_blend_a')):
            csv = open(os.path.join(work, 'zone_source', m + '.csv')).read()
            self.assertNotIn(other, csv)
            self.assertEqual(open(os.path.join(work, 'zonetool', m, 'maps', 'cp', m + '.d3dbsp.ents')).read(), m)



class SplitZoneTest(unittest.TestCase):
    """The experiment tool: stock rows to the base csv, the map's own rows to the map csv, ignore first."""

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.stock_csv = os.path.join(self.tmp, 'stock.csv')
        write(self.stock_csv, 'xmodel,gun\nmaterial,,mat_ref\nimage,img_a\nrawfile,scripts/cp/zombies/x.gsc\n')
        write(os.path.join(self.tmp, 'zone_source', 'cp_blend_a.csv'),
              '// cp_blend_a: generated world\nrequire,techsets_common\nrawfile,scripts/cp/maps/cp_blend_a/cp_blend_a.gsc\n'
              'xmodel,gun\nmaterial,,mat_ref\nimage,img_a\nimage,my_custom_tga\nnetconststrings,ncs_efx_level\n'
              'stringtable,cp/zombies/cp_blend_a_playercash_images.csv\nrawfile,scripts/cp/zombies/x.gsc\ncom_map,maps/cp/cp_blend_a.d3dbsp\n')

    def read(self, name):
        with open(os.path.join(self.tmp, 'zone_source', name)) as f:
            return f.read()

    def test_split(self):
        nb, nm = sz.split(self.tmp, 'cp_blend_a', 'iwz_base', [self.stock_csv])
        base = self.read('iwz_base.csv').splitlines()
        own = self.read('cp_blend_a.csv').splitlines()
        self.assertEqual(base, ['// cp_blend_a: generated world', 'require,techsets_common', 'xmodel,gun', 'material,,mat_ref', 'image,img_a',
                                'rawfile,scripts/cp/zombies/x.gsc'])
        self.assertEqual(own[:3], ['// cp_blend_a: generated world', 'ignore,iwz_base', 'require,techsets_common'], 'ignore comes before any asset row')
        self.assertEqual(own[3:], ['rawfile,scripts/cp/maps/cp_blend_a/cp_blend_a.gsc', 'material,,mat_ref', 'image,my_custom_tga',
                                   'netconststrings,ncs_efx_level', 'stringtable,cp/zombies/cp_blend_a_playercash_images.csv',
                                   'com_map,maps/cp/cp_blend_a.d3dbsp'])
        self.assertEqual((nb, nm), (4, 6))
        full = self.read('cp_blend_a.full.csv').splitlines()
        self.assertEqual({row for row in full if not row.startswith('//')} - set(base) - set(own), set(), 'no row of the full csv is lost')
        sz.split(self.tmp, 'cp_blend_a', 'iwz_base', [self.stock_csv])
        self.assertEqual(full, self.read('cp_blend_a.full.csv').splitlines(), 'the full copy is never overwritten')
        self.assertEqual(base, self.read('iwz_base.csv').splitlines(), 'a second run gives the same base csv, not references only')
        self.assertEqual(own, self.read('cp_blend_a.csv').splitlines(), 'and the same map csv')

    def test_a_new_assembly_replaces_the_full_copy(self):
        sz.split(self.tmp, 'cp_blend_a', 'iwz_base', [self.stock_csv])
        write(os.path.join(self.tmp, 'zone_source', 'cp_blend_a.csv'), '// new\nxmodel,gun\nimage,another_custom\n')     # the next build's assembly
        sz.split(self.tmp, 'cp_blend_a', 'iwz_base', [self.stock_csv])
        self.assertEqual(self.read('cp_blend_a.full.csv').splitlines(), ['// new', 'xmodel,gun', 'image,another_custom'])
        self.assertEqual(self.read('iwz_base.csv').splitlines(), ['// new', 'xmodel,gun'])


class OneCompilerTest(unittest.TestCase):
    """The compiler is named in one place: machine.ps1."""

    def text(self, name):
        return pathlib.Path(HERE, name).read_text(encoding='utf-8', errors='replace')

    def test_the_pin_is_in_machine_ps1_only(self):
        self.assertIn('zonetool-lightvol-ea60b19.exe', self.text('machine.ps1'))
        for name in ('build-g.ps1', 'build-sz2.ps1', 'build-blend.ps1'):
            t = self.text(name)
            self.assertNotRegex(t, r'compiler-landing', name + ' names a compiler file itself')
            self.assertIn('MapCompiler', t, name)
        self.assertNotIn('x64-zt-iwz-map', self.text('build-sz2.ps1'))

    def test_assembly_is_incremental_by_default(self):
        for name in ('build-sz2.ps1', 'build-blend.ps1'):
            t = self.text(name)
            self.assertIn('Get-AssembleKey.ps1', t, name)
            self.assertIn('FullAssemble', t, name)
            self.assertRegex(t, r'Remove-Item -LiteralPath \$keyFile', name + ': the key goes before the assembly changes the tree')
            self.assertLess(t.index('Remove-Item -LiteralPath $keyFile'), t.index('assemble.py" $W'), name)
            self.assertNotRegex(t, r'if\(\$Incremental -and', name + ' still waits for -Incremental')
        t = self.text('build-sz2.ps1')
        for module in ('audio', 'darkness', 'effects', 'foreign kit models'):
            self.assertIn("$unproven+='%s'" % module, t, 'a module never measured incrementally must force a full assembly')
        self.assertIn('-not $TrustModules', t)

    def test_build_blend_validates_before_it_builds(self):
        t = self.text('build-blend.ps1')
        self.assertLess(t.index('map_identity.py" validate'), t.index('Run-Gate \'emitcheck\''))
        self.assertLess(t.index('map_identity.py" validate'), t.index('Invoke-Zt'))


if __name__ == '__main__':
    unittest.main()
