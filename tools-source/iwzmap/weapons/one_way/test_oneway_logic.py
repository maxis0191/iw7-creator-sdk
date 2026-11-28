"""ONE WAY: the mechanic's rules, run outside the game in milliseconds (Forge's gscvm, virtual time).

    python -B -m unittest test_oneway_logic -v          (from this folder; needs C:\\forge)

What this proves: the logic of cp_sz_oneway.gsc (tickets, the beat, the sums, taken / carried / stayed, the six
cars, the 12 s rule, the refund, the arrivals, credit between two owners). What it does not prove: anything the
engine does (the real damage callback and its multipliers, agents, hiding, moving, points). The stock damage
callback is a stand-in here (t_callback below): it calls level.onzombiedamage_func as retail does
(scripts/cp/agents/gametype_zombie.gsc, the line before `min( damage, self.maxhealth )`), then takes the health.
"""
import os
import sys
import unittest

FORGE = os.environ.get("FORGE_ROOT", r"C:\forge")
if FORGE not in sys.path:
    sys.path.insert(0, FORGE)
try:
    from gscvm import GscVM
    from gscvm import builtins as gb
    from gscvm.values import GscArray, Undefined
except Exception:  # pragma: no cover
    GscVM = None

HERE = os.path.dirname(os.path.abspath(__file__))
W = "iw7_szoneway_zm"

HARNESS = r"""
t_callback( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc )
{
    if ( self.health <= 0 )
        return;
    if ( isdefined( self.t_early ) && mod == "MOD_UNKNOWN" )
        return;                         // retail returns before the hook in some cases (explosive touch on a special...)
    damage = self [[ level.onzombiedamage_func ]]( inflictor, attacker, damage, flags, mod, weapon, point, dir, hitloc, 0, 0, "" );
    damage = int( min( damage, self.maxhealth ) );
    self.t_hits[self.t_hits.size] = damage;
    self.health = self.health - damage;
    if ( self.health <= 0 )
    {
        self.health = 0;
        if ( isdefined( attacker ) )
            attacker.t_kills++;
        self notify( "death" );
    }
}
t_shoot( z, head )
{
    loc = "torso_upper";
    if ( head )
        loc = "head";
    z t_callback( self, self, 100, 0, "MOD_RIFLE_BULLET", self.t_weapon, z.origin, ( 1, 0, 0 ), loc );
}
t_tickets( z )
{
    if ( !isdefined( z.ow_tix ) )
        return 0;
    return z.ow_tix.size;
}
t_stat( key )
{
    if ( isdefined( self.ow_stats ) && isdefined( self.ow_stats[key] ) )
        return self.ow_stats[key];
    return 0;
}
"""


@unittest.skipIf(GscVM is None, "gscvm not found (C:\\forge)")
class OneWay(unittest.TestCase):
    def setUp(self):
        vm = self.vm = GscVM(lenient=True)
        self.zs = []
        test = self

        def b_dodamage(vm, obj, dmg, pos=Undefined, attacker=Undefined, inflictor=Undefined, mod=Undefined,
                       weapon=Undefined):
            vm.call("t", "t_callback", [inflictor, attacker, dmg, 0, mod, weapon, pos, (0, 0, 0), Undefined],
                    self_obj=obj)

        def b_prim(vm, obj):
            return GscArray.from_list([obj.f["t_weapon"]])

        def b_getstock(vm, obj, w=Undefined):
            return obj.f.get("t_stock", 0)

        def b_setstock(vm, obj, w, n):
            obj.f["t_stock"] = n

        def b_alive(vm, obj, team=Undefined):
            return GscArray.from_list([z for z in test.zs if z.f.get("health", 0) > 0])

        def b_mode(vm, obj, mode):
            obj.f["t_mode"] = mode
            obj.f.setdefault("t_modes", []).append(mode)

        def b_nav(vm, obj, p):
            return p

        vm.builtins.update({"dodamage": b_dodamage, "getweaponslistprimaries": b_prim,
                            "getweaponammostock": b_getstock, "setweaponammostock": b_setstock,
                            "getclosestpointonnavmesh": b_nav, "t_alive": b_alive, "t_mode": b_mode})
        vm.load_source("getaliveagentsofteam( team ) { return t_alive(); }", r"scripts\cp\cp_agent_utils")
        vm.load_source("bb_requestmovetype( mode ) { self t_mode( mode ); }", r"scripts\asm\asm_bb")
        vm.load_source(open(os.path.join(HERE, "cp_sz_oneway.gsc"), encoding="utf-8").read(), "ow")
        vm.load_source(HARNESS, "t")
        vm.load_source("t_hook0( a, b, c, d, e, f, g, h, i, j, k, l ) { return c; }\n"
                       "t_reward0( a, b, c, d, e, f ) { return 1; }\n"
                       "t_setup() { level.onzombiedamage_func = ::t_hook0; level.eligable_for_reward_func = ::t_reward0; }",
                       "t0")
        vm.call("t0", "t_setup")
        vm.call("ow", "ow_init")
        self.p = self.player("Ann")

    def tearDown(self):
        # a script error inside a thread ends that thread only: it must not pass silently
        self.assertEqual(self.vm.errors, [])
        self.assertLessEqual(set(self.vm.unknown_calls), {"setgoalpos", "anglestoforward"},
                             "only engine calls with no effect on the rules may be unmodelled")

    # ---- helpers
    def player(self, name, weapon=W):
        p = self.vm.world.add_player(name)
        p.f.update(t_weapon=weapon, t_stock=10, t_kills=0, origin=(0, 0, 0))
        return p

    def zombie(self, health, kind="generic_zombie", origin=(300, 0, 0), mode="sprint"):
        z = self.vm.world.spawn_zombie()
        z.f.update(health=health, maxhealth=health, agent_type=kind, origin=origin, movemode=mode,
                   t_hits=GscArray())
        self.zs.append(z)
        return z

    def now(self):
        return gb.BUILTINS["gettime"](self.vm, None)

    def sync(self, ms):
        """advance virtual time until `ms` are left before the next bell (frames are 50 ms)"""
        for _ in range(400):
            if 6000 - self.now() % 6000 == ms:
                return
            self.vm.run_for(0.05)
        self.fail("no sync")

    def shoot(self, z, head=0, who=None):
        self.vm.call("t", "t_shoot", [z, head], self_obj=who or self.p)

    def stat(self, key, who=None):
        return self.vm.call("t", "t_stat", [key], self_obj=who or self.p)

    def tickets(self, z):
        return self.vm.call("t", "t_tickets", [z])

    def bell(self):
        """run to just after the next bell"""
        self.vm.run_for((6000 - self.now() % 6000) / 1000.0 + 0.1)

    # ---- the rules
    def test_ticket_is_no_damage_then_taken_on_the_bell_with_refund(self):
        zs = [self.zombie(1045) for _ in range(12)]
        self.sync(5000)
        for z in zs:
            self.shoot(z)
        self.assertEqual([z.f["health"] for z in zs], [1045] * 12)
        self.assertEqual([self.tickets(z) for z in zs], [1] * 12)
        self.assertEqual(self.stat("issued"), 12)
        self.vm.run_for(4.8)
        self.assertEqual(sum(z.f["health"] > 0 for z in zs), 12, "nothing before the bell")
        self.bell()
        self.assertEqual(sum(z.f["health"] > 0 for z in zs), 0)
        self.assertEqual(self.stat("taken"), 12)
        self.assertEqual(self.p.f["t_kills"], 12)
        self.assertEqual(self.stat("full"), 1)
        self.assertEqual(self.stat("refund"), 6)
        self.assertEqual(self.p.f["t_stock"], 16)

    def test_five_taken_is_no_full_train(self):
        zs = [self.zombie(1045) for _ in range(5)]
        self.sync(3000)
        for z in zs:
            self.shoot(z)
        self.bell()
        self.assertEqual((self.stat("taken"), self.stat("full"), self.p.f["t_stock"]), (5, 0, 10))

    def test_six_cars_carried_two_stay_then_put_back_then_taken(self):
        zs = [self.zombie(4365) for _ in range(8)]
        self.sync(5000)
        for i, z in enumerate(zs):
            self.shoot(z)
            self.vm.run_for(0.05)       # ticket ages differ: the oldest six are carried
        self.bell()
        self.assertEqual((self.stat("taken"), self.stat("carried"), self.stat("stayed")), (0, 6, 2))
        self.assertEqual([z.f["health"] for z in zs], [395] * 8, "flat 3,970 each")
        carried = [z for z in zs if "ow_carry" in z.f and z.f["ow_carry"] is not Undefined]
        self.assertEqual(carried, zs[:6], "oldest tickets first")
        hidden = [c[1] for c in self.vm.calls if c[0] == "hide"]
        self.assertEqual(hidden, zs[:6])
        # a carried zombie is off the platform: a bullet does nothing to it and books nothing
        self.shoot(zs[0])
        self.assertEqual((zs[0].f["health"], self.tickets(zs[0])), (395, 0))
        self.bell()
        shown = [c[1] for c in self.vm.calls if c[0] == "show"]
        self.assertEqual(sorted(shown, key=id), sorted(zs[:6], key=id))
        self.assertTrue(all(z.f.get("ow_carry", Undefined) is Undefined for z in zs))
        # the 12 s rule: ticketed and hurt, neither calmed nor carried
        self.vm.run_for(1.6)
        for z in zs:
            self.shoot(z)
        self.bell()
        self.assertEqual(self.stat("taken"), 8)
        self.assertEqual(self.stat("refund"), 4)

    def test_put_back_zombie_is_not_carried_again_for_12_s(self):
        z = self.zombie(20000)
        self.sync(3000)
        self.shoot(z)
        self.bell()                      # carried
        self.bell()                      # back
        self.assertEqual(self.stat("carried"), 1)
        self.vm.run_for(1.6)
        self.shoot(z)
        self.bell()
        self.assertEqual((self.stat("carried"), self.stat("stayed")), (1, 1))
        self.assertEqual(z.f["health"], 20000 - 3970 * 2)
        self.vm.run_for(12.0)
        self.shoot(z)
        self.bell()
        self.assertEqual(self.stat("carried"), 2, "after 12 s it is carried again")

    def test_first_class(self):
        a, b = self.zombie(9357), self.zombie(10293)
        self.sync(3000)
        self.shoot(a, head=1)
        self.shoot(b, head=1)
        self.bell()
        self.assertEqual((a.f["health"], b.f["health"]), (0, 373))
        self.assertEqual((self.stat("first"), self.stat("taken"), self.stat("carried")), (2, 1, 1))

    def test_three_tickets_a_zombie_the_fourth_is_wasted(self):
        z = self.zombie(11322)
        self.sync(5000)
        for _ in range(4):
            self.shoot(z)
        self.assertEqual((self.tickets(z), self.stat("issued"), self.stat("wasted")), (3, 3, 1))
        self.bell()
        self.assertEqual((z.f["health"], self.stat("taken")), (0, 1))
        self.assertEqual(list(z.f["t_hits"].d.values())[-1], 11322, "3 x 3,970 = 11,910, capped by the callback at max health")

    def test_doors_closing(self):
        z = self.zombie(1045)
        self.sync(400)
        self.shoot(z)
        self.bell()
        self.assertEqual((z.f["health"], self.stat("taken"), self.tickets(z)), (1045, 0, 1))
        self.bell()
        self.assertEqual((z.f["health"], self.stat("taken")), (0, 1))
        y = self.zombie(1045)
        self.sync(550)
        self.shoot(y)
        self.bell()
        self.assertEqual(y.f["health"], 0, "with 550 ms left the ticket is for this bell")

    def test_beat_is_the_matchs_clock_not_the_tickets(self):
        z = self.zombie(1045)
        self.sync(1000)
        t0 = self.now()
        self.shoot(z)
        self.vm.run_for(0.95)
        self.assertEqual(z.f["health"], 1045)
        self.vm.run_for(0.15)
        self.assertEqual(z.f["health"], 0)
        self.assertEqual((t0 + 1000) % 6000, 0)

    def test_calm_flinch_then_walk_then_restored(self):
        z = self.zombie(50000)
        self.sync(5000)
        self.shoot(z)
        self.assertEqual(z.f.get("stunned"), 1)
        self.vm.run_for(0.7)
        self.assertIs(z.f.get("stunned", Undefined), Undefined)
        self.assertEqual(z.f.get("t_mode"), "walk")
        self.bell()                      # carried, hidden
        self.bell()                      # back, down 1.5 s
        self.vm.run_for(1.6)
        self.assertEqual(z.f.get("t_mode"), "sprint", "its own mode comes back")
        self.shoot(z)                    # inside the 12 s: no calm
        self.vm.run_for(0.7)
        self.assertEqual(z.f.get("t_mode"), "sprint")

    def test_special_is_capped_not_calmed_not_carried(self):
        z = self.zombie(50000, kind="zombie_brute")
        self.sync(5000)
        for _ in range(3):
            self.shoot(z, head=1)
        self.vm.run_for(0.7)
        self.assertIsNone(z.f.get("t_mode"))
        self.bell()
        self.assertEqual(z.f["health"], 48000)
        self.assertEqual((self.stat("carried"), self.stat("stayed")), (0, 1))

    def test_other_weapons_and_script_damage_pass_through(self):
        z = self.zombie(5000)
        q = self.player("Bob", weapon="iw7_fhr_zm")
        self.shoot(z, who=q)
        self.assertEqual((z.f["health"], self.tickets(z)), (4900, 0))

    def test_two_owners_share_the_beat_and_the_zombie(self):
        q = self.player("Bob")
        z = self.zombie(11000)
        self.sync(5000)
        self.shoot(z, who=q)
        self.shoot(z)
        self.shoot(z)
        self.shoot(z, who=q)             # the fourth: wasted, Bob's
        self.bell()
        self.assertEqual(z.f["health"], 0)
        self.assertEqual((self.stat("taken"), self.stat("taken", q)), (1, 0), "the kill is whoever issued most")
        self.assertEqual((self.p.f["t_kills"], q.f["t_kills"], self.stat("wasted", q)), (1, 0, 1))

    def test_upgraded_refund_and_arrivals(self):
        up = self.player("Cy", weapon=W + "+pap1")
        taken = [self.zombie(8507, origin=(300 + 10 * i, 0, 0)) for i in range(12)]
        near = [self.zombie(7020, origin=(320, 40, 0)), self.zombie(3000, origin=(300, 100, 0))]
        far = self.zombie(3000, origin=(900, 0, 0))
        self.sync(5000)
        for z in taken:
            self.shoot(z, who=up)
        self.bell()
        self.assertEqual((self.stat("taken", up), self.stat("refund", up)), (12, 8))
        self.assertEqual((near[0].f["health"], near[1].f["health"], far.f["health"]), (7020, 3000, 3000))
        self.bell()
        self.assertEqual(self.stat("arrivals", up), 12)
        self.assertEqual(near[0].f["health"], 0, "two arrivals of 3,970 and no more: 7,940 covers 7,020")
        self.assertEqual(len([h for h in near[0].f["t_hits"].d.values() if h > 0]), 2)
        self.assertEqual(near[1].f["health"], 0)
        self.assertEqual(far.f["health"], 3000)
        self.assertEqual(self.stat("arrival_kills", up), 2)
        self.bell()
        self.assertEqual(self.stat("arrivals", up), 12, "an arrival makes no arrival")


    def test_rated_damage_is_never_left_for_the_next_hit(self):
        z = self.zombie(50000, kind="zombie_brute")
        z.f["t_early"] = 1               # the stock callback returns before the hook for this bell
        q = self.player("Bob", weapon="iw7_fhr_zm")
        self.sync(3000)
        self.shoot(z, head=1)
        self.bell()
        self.assertEqual(z.f["health"], 50000, "the bell's damage did not reach the hook")
        self.shoot(z, who=q)
        self.assertEqual(z.f["health"], 49900, "another weapon's hit is its own 100, not the stale 2,000")

    def test_special_that_stays_is_not_stunned(self):
        z = self.zombie(50000, kind="zombie_brute")
        self.sync(3000)
        self.shoot(z)
        self.bell()
        self.assertIs(z.f.get("stunned", Undefined), Undefined)
        self.assertEqual(self.stat("stayed"), 1)

    def test_a_player_who_leaves_cancels_his_tickets(self):
        q = self.player("Bob")
        a, b = self.zombie(1045), self.zombie(1045)
        self.sync(5000)
        self.shoot(a, who=q)
        self.shoot(b)
        self.vm.notify(q, "disconnect", [])
        self.vm.run_for(0.05)
        self.bell()
        self.assertEqual((a.f["health"], b.f["health"]), (1045, 0))
        self.assertEqual((self.stat("taken"), q.f["t_kills"]), (1, 0))

    def test_four_owners(self):
        ps = [self.p] + [self.player(n) for n in ("Bob", "Cy", "Di")]
        z = self.zombie(11000)
        mine = [[self.zombie(1045) for _ in range(6)] for _ in ps]
        self.sync(5000)
        for who in ps[1:]:
            self.shoot(z, who=who)       # Bob, Cy, Di: one ticket each on the shared zombie; Ann's is the fourth
        self.shoot(z)
        for who, zs in zip(ps, mine):
            for y in zs:
                self.shoot(y, who=who)
        self.bell()
        self.assertEqual(z.f["health"], 0, "three owners' tickets add on one zombie")
        self.assertEqual([self.stat("taken", w) for w in ps], [6, 7, 6, 6], "equal tickets: the first to issue has the kill")
        self.assertEqual(self.stat("wasted"), 1)
        self.assertEqual([self.stat("full", w) for w in ps], [1, 1, 1, 1], "each weapon counts its own full train")
        self.assertEqual([w.f["t_stock"] for w in ps], [13, 13, 13, 13])

    def test_six_carried_per_owner(self):
        q = self.player("Bob")
        za = [self.zombie(4365) for _ in range(7)]
        zb = [self.zombie(4365) for _ in range(7)]
        self.sync(5000)
        for y in za:
            self.shoot(y)
        for y in zb:
            self.shoot(y, who=q)
        self.bell()
        self.assertEqual((self.stat("carried"), self.stat("stayed")), (6, 1))
        self.assertEqual((self.stat("carried", q), self.stat("stayed", q)), (6, 1))

    def test_insta_kill_makes_any_ticket_enough(self):
        z, boss = self.zombie(47300), self.zombie(47300, kind="zombie_brute")
        self.vm.level.f["insta_kill"] = 1
        self.sync(3000)
        self.shoot(z)
        self.shoot(boss)
        self.bell()
        self.assertEqual((z.f["health"], boss.f["health"]), (0, 45300))
        self.assertEqual(self.stat("taken"), 1)


if __name__ == "__main__":
    unittest.main()
