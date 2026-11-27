"""modules/terminus.gsc, the trip to the Terminus, run outside the game in Forge's GSC VM (C:\\forge\\gscvm, virtual time).

The module is emitted the way the generator emits it (sz_modules.emit, marker table filled), loaded with one-line stand-ins
for the stock functions it calls by path (flags, damage modifiers, the white screen) and the engine builtins the VM does
not model, then driven: no Terminus marker (idle, one line), power off (refused), the trip (boarding 4 s, riders with a
downed player, a zombie put out, the stay with the protections on, the pause only when every standing player is away and
only a pause of ours released, the return of whoever is in the Terminus box, 150 s cooldown), and a match end mid-visit.
Skipped when C:\\forge\\gscvm is not on this machine (FORGE_ROOT overrides the folder).
"""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import sz_modules  # noqa: E402

FORGE = os.environ.get('FORGE_ROOT', r'C:\forge')
try:
    sys.path.insert(0, FORGE)
    from gscvm import GscVM  # noqa: E402
    from gscvm.values import GscArray, Undefined  # noqa: E402
except ImportError:      # pragma: no cover
    GscVM = None

MOD = r'scripts\cp\maps\cp_iwz\cp_iwz_terminus'
CAB = {'kind': 'quest_cab', 'id': 'car1', 'zone': 'platform_a', 'origin': [265.5, 1488, -323.01], 'yaw': 180,
       'area': [197.5, 1421.5, -347.01, 733.5, 1554.5, -173.01]}
ARRIVAL = {'kind': 'terminus_arrival', 'id': '', 'zone': 'terminus', 'origin': [8000, 8000, 0], 'yaw': 90,
           'area': [7300, 7550, -20, 8700, 8450, 320]}
HATCH = {'kind': 'hatch', 'id': 'HALL', 'zone': 'ticket_hall', 'origin': [-640, 4368, 0], 'yaw': 270}

STUBS = {
    r'scripts\engine\utility': '''
flag_exist( f ) { return isdefined( level.tflags ) && isdefined( level.tflags[f] ); }
flag( f ) { return isdefined( level.tflags ) && isdefined( level.tflags[f] ) && level.tflags[f]; }
is_true( v ) { return isdefined( v ) && v; }
''',
    r'scripts\cp\utility': '''
adddamagemodifier( name, v, add ) { if ( !isdefined( self.tdm ) ) self.tdm = []; self.tdm[name] = v; }
removedamagemodifier( name, add ) { if ( isdefined( self.tdm ) ) self.tdm[name] = undefined; }
''',
    r'scripts\cp\zombies\zombie_afterlife_arcade': '''
add_white_screen() { self.tws = 1; }
remove_white_screen( t ) { self.tws = undefined; }
''',
    r'test\terminus_rig': '''
power( on ) { if ( !isdefined( level.tflags ) ) level.tflags = []; level.tflags["power_on"] = on; }
end_game() { level notify( "game_ended" ); }
''',
}


def _ret_undef(vm, obj, *a):
    return Undefined


def undef(v):
    return v is None or v is Undefined


@unittest.skipIf(GscVM is None, 'Forge GSC VM not on this machine')
class TerminusTrip(unittest.TestCase):
    def vm(self, markers):
        with tempfile.TemporaryDirectory() as d:
            done = sz_modules.emit(d, markers, [], 'cp_iwz', only=['terminus'])
            self.assertEqual(done, ['terminus'])
            with open(os.path.join(d, 'cp_iwz_terminus.gsc'), encoding='utf-8') as f:
                src = f.read()
        self.assertNotIn('//@MARKERS@', src)
        vm = GscVM(lenient=False)
        vm.dvars['mapname'] = 'cp_iwz'
        for name, s in STUBS.items():
            vm.load_source(s, name)
        vm.load_source(src, MOD)
        b = vm.builtins
        for n in ('makeusable', 'earthquakeforplayer', 'dontinterpolate', 'setvelocity', 'setplayerangles'):
            b[n] = _ret_undef
        b['sethintstring'] = lambda vm_, obj, h=None, *a: obj.f.__setitem__('hint', h)
        b['visionsetnakedforplayer'] = lambda vm_, obj, v=None, *a: obj.f.__setitem__('vis', v)
        b['soundexists'] = lambda vm_, obj, n: True
        b['playerphysicstrace'] = lambda vm_, obj, a, z: (z[0], z[1], z[2] + 64)       # lands on the destination
        b['getclosestpointonnavmesh'] = lambda vm_, obj, p: p
        self.addCleanup(vm.close)
        return vm

    def log(self, vm):
        return [l for l in vm.output if 'TERMINUS' in str(l)]

    def place(self, vm, p, xyz):
        p.f['origin'] = tuple(float(v) for v in xyz)

    def cab(self, vm):
        c = [e for e in vm.world.entities if e.f.get('targetname') == 'iwz_terminus_cab']
        return c[0] if c else None

    def use(self, vm, p):
        vm.notify(self.cab(vm), 'trigger', [p])
        vm.drain()

    def state(self, vm):
        return vm.level.f['iwz_terminus'].f['state']

    def test_without_terminus_marker_idle_one_line_no_cab(self):
        vm = self.vm([HATCH, CAB])
        vm.call(MOD, 'init')
        vm.run_for(5)
        self.assertEqual(self.state(vm), 'no_terminus')
        lines = self.log(vm)
        self.assertEqual(len(lines), 1, lines)
        self.assertIn('IDLE cab=1 terminus=0', str(lines[0]))
        self.assertIsNone(self.cab(vm))
        self.assertEqual(vm.errors, [])

    def test_trip_full_cycle(self):
        vm = self.vm([HATCH, CAB, ARRIVAL])
        vm.call(MOD, 'init')
        a = vm.world.add_player('A')
        b = vm.world.add_player('B')
        c = vm.world.add_player('C')
        vm.run_for(1.5)
        self.assertEqual(self.state(vm), 'unarmed')
        self.place(vm, a, (300, 1488, -320))
        self.use(vm, a)
        self.assertIn('why=unarmed', str(self.log(vm)[-1]))
        vm.call(r'test\terminus_rig', 'power', [1])
        vm.run_for(1)
        self.assertEqual(self.state(vm), 'idle')
        # A and B (downed) in car 1, C on the platform, a zombie in the car
        self.place(vm, b, (500, 1480, -320))
        b.f['inlaststand'] = 1
        self.place(vm, c, (400, 1700, -320))
        z = vm.world.spawn_zombie()
        z.f['origin'] = (600.0, 1490.0, -320.0)
        vm.level.f['spawned_enemies'] = GscArray.from_list([z])
        self.use(vm, b)                                     # a downed player cannot start it
        self.assertIn('why=downed', str(self.log(vm)[-1]))
        self.use(vm, a)
        self.assertEqual(self.state(vm), 'boarding')
        self.use(vm, c)
        self.assertIn('why=boarding', str(self.log(vm)[-1]))
        vm.run_for(4.1)
        self.assertEqual(self.state(vm), 'crossing')
        self.assertGreater(z.f['origin'][1], 1554.5)        # put out on the platform side
        self.assertEqual(vm.level.f['iwz_terminus'].f['riders'], 2)
        vm.run_for(3.3)
        self.assertEqual(self.state(vm), 'away')
        for p in (a, b):
            self.assertTrue(7300 <= p.f['origin'][0] <= 8700 and 7550 <= p.f['origin'][1] <= 8450, p.f['origin'])
            self.assertEqual(p.f.get('is_off_grid'), 1)      # stock: protected for the whole stay
            self.assertEqual(p.f['tdm'].d.get('iwz_terminus'), 0.0)
            self.assertEqual(p.f.get('vis'), 'cp_frontend')   # the Terminus's own vision on arrival
        self.assertNotIn('is_off_grid', c.f)
        self.assertNotIn('vis', c.f)
        # C stands outside: no pause
        vm.run_for(2)
        self.assertFalse(vm.level.f.get('zombies_paused'))
        # C walks into the Terminus box (as if he had come along): every standing player away -> paused
        self.place(vm, c, (8100, 8000, 0))
        vm.run_for(1)
        self.assertEqual(vm.level.f.get('zombies_paused'), 1)
        self.assertGreater(z.f.get('delay_cleanup_until') or 0, 0)      # held from the stock far-zombie cleanup while paused
        # B is revived at the Terminus, then C leaves the box (stands outside): pause released
        b.f['inlaststand'] = 0
        self.place(vm, c, (400, 1700, -320))
        vm.run_for(1)
        self.assertEqual(vm.level.f.get('zombies_paused'), 0)
        vm.run_for(40 - 4.1)
        # back: whoever is in the Terminus box (A, B), into car 1, protections off
        vm.run_for(2)
        self.assertEqual(self.state(vm), 'cooldown')
        for p in (a, b):
            o = p.f['origin']
            self.assertTrue(197.5 <= o[0] <= 733.5 and 1421.5 <= o[1] <= 1554.5, o)
            self.assertTrue(undef(p.f.get('is_off_grid')))
            self.assertTrue(undef(p.f.get('iwz_busy')))
            self.assertEqual(p.f.get('vis'), '')               # the station's lit vision again (dvar unset: the map's own)
        self.assertEqual(vm.level.f['iwz_terminus'].f['returned'], 2)
        self.use(vm, a)
        self.assertIn('why=cooldown', str(self.log(vm)[-1]))
        vm.run_for(150)
        self.assertEqual(self.state(vm), 'idle')
        self.assertEqual(vm.errors, [])

    def test_pause_of_someone_else_is_not_released_and_game_end_cleans_up(self):
        vm = self.vm([CAB, ARRIVAL])
        vm.call(MOD, 'init')
        vm.call(r'test\terminus_rig', 'power', [1])
        a = vm.world.add_player('A')
        vm.run_for(1.5)
        self.place(vm, a, (300, 1488, -320))
        vm.level.f['zombies_paused'] = 1                    # a pause set by another system
        self.use(vm, a)
        vm.run_for(4.1 + 3.3 + 2)
        self.assertEqual(self.state(vm), 'away')
        self.assertEqual(vm.level.f['iwz_terminus'].f['paused'], 0)
        vm.level.f['zombies_paused'] = 0                    # the other system lets go: now the pause is ours
        vm.run_for(1)
        self.assertEqual(vm.level.f['iwz_terminus'].f['paused'], 1)
        self.assertEqual(vm.level.f.get('zombies_paused'), 1)
        vm.call(r'test\terminus_rig', 'end_game')           # the match ends mid-visit
        vm.drain()
        self.assertEqual(vm.level.f.get('zombies_paused'), 0)
        self.assertTrue(undef(a.f.get('is_off_grid')))
        self.assertTrue(undef(a.f.get('iwz_busy')))
        self.assertEqual(vm.errors, [])

    def test_nobody_aboard_goes_back_to_idle(self):
        vm = self.vm([CAB, ARRIVAL])
        vm.call(MOD, 'init')
        vm.call(r'test\terminus_rig', 'power', [1])
        a = vm.world.add_player('A')
        vm.run_for(1.5)
        self.place(vm, a, (300, 1488, -320))
        self.use(vm, a)
        self.place(vm, a, (300, 1700, -320))                # steps out during boarding
        vm.run_for(4.1)
        self.assertEqual(self.state(vm), 'idle')
        self.assertIn('NOBODY_ABOARD', str(self.log(vm)[-1]))


@unittest.skipIf(GscVM is None, 'Forge GSC VM not on this machine')
class WeaponUpgradeHint(unittest.TestCase):
    """cp_iwz2.gsc iwz_weapon_upgrade_hint: the stock branching with this map's two upgrade strings (PLACEHOLDER COPY)"""

    def test_branches(self):
        import re
        with open(os.path.join(os.path.dirname(HERE), 'cp_iwz2.gsc'), encoding='utf-8') as f:
            src = re.sub(r'= //@\w+@;', '= 0;', f.read()).replace('( //@WHEEL@ )', '( "x" )')
        vm = GscVM(lenient=False)
        vm.load_source('get_weapon_level( w ) { return level.tlvl; }\ncan_upgrade( w ) { return level.tcan; }', r'scripts\cp\cp_weapon')
        vm.load_source('is_melee_weapon( w, x ) { return level.tmelee; }', r'scripts\cp\utility')
        vm.load_source('is_true( v ) { return isdefined( v ) && v; }', r'scripts\engine\utility')
        vm.load_source(src, r'scripts\cp\maps\cp_iwz\cp_iwz')
        vm.builtins['getcurrentweapon'] = lambda vm_, obj: 'iw7_ar57_zm'
        p = vm.world.add_player('A')
        vm.level.f['pap_max'] = 3
        got = []
        for lvl, can, melee in ((1, 1, 0), (2, 1, 0), (3, 1, 0), (1, 0, 0), (1, 1, 1)):
            vm.level.f.update({'tlvl': lvl, 'tcan': can, 'tmelee': melee})
            got.append(str(vm.call(r'scripts\cp\maps\cp_iwz\cp_iwz', 'iwz_weapon_upgrade_hint', [None, p])))
        self.assertEqual(got, ['IWZ_INTERACTIONS_VALIDATE_WEAPON', 'IWZ_INTERACTIONS_VALIDATE_WEAPON_AGAIN',
                               'COOP_INTERACTIONS_UPGRADE_MAXED', 'CP_ZMB_INTERACTIONS_UPGRADE_WEAPON_FAIL', ''])
        with open(os.path.join(os.path.dirname(HERE), 'perks', 'strings.json'), encoding='utf-8') as f:
            import json
            strings = json.load(f)
        for k in got[:2]:
            self.assertIn(k, strings)
            self.assertNotIn('pack-a-punch', strings[k].lower())


if __name__ == '__main__':
    unittest.main()
