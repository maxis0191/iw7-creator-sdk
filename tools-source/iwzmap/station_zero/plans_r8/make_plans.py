"""Round 8 Forge plans for the Arcade layer (worker SZ8). usage: python make_plans.py <emit folder of the layer> <out dir> <usermap folder>"""
import json, os, sys
emit, out, um = sys.argv[1:4]
L = json.load(open(os.path.join(emit, 'layout.json')))
I = L['interactions']
at = {i['kind']: [round(v, 1) for v in i['origin']] for i in I if i['kind'].startswith('perk_machine_') or i['kind'] == 'generator'}
buys = [i for i in I if i.get('groupname') == 'wall_buy' and -3000 < i['origin'][0] < -1200 and 3500 < i['origin'][1] < 4700]
doors = [i for i in I if i['kind'].startswith('debris_') and -1300 < i['origin'][0] < -1100 and 3700 < i['origin'][1] < 4100]
print('buys', buys, 'doors', doors)
NEW = ['perk_machine_deadeye', 'perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge', 'perk_machine_double']
PRICE = {'perk_machine_deadeye': 1500, 'perk_machine_bakers': 3000, 'perk_machine_voyage': 2000, 'perk_machine_grudge': 2500, 'perk_machine_double': 3000}


def call(fn, *a, s=1): return {'do': 'call', 'fn': fn, 'args': list(a), 's': s}
def exp(that, op, v, why): return {'do': 'expect', 'that': that, op: v, 'why': why}
def use(name, kind, near=None, s=4): return {'do': 'use', 'name': name, 'kind': kind, 'near': near or at[kind], 's': s}
def plan(name, about, libs, steps, cond='quiet'): return {'schema': 'iw7.gamelab-plan/1', 'name': name, 'map': 'cp_iwz', 'conditions': cond, 'libraries': libs, 'about': about, 'steps': steps}
def save(p): json.dump(p, open(os.path.join(out, p['name'] + '.json'), 'w'), indent=1)


os.makedirs(out, exist_ok=True)
D = max(doors, key=lambda d: d['origin'][0]) if doors else None
dn = D['origin'] if D else [-1160, 3900, 24]
dk = D['kind'] if D else 'debris_1000'
ys = [3850, 3900, 3950]
def tr(n): return {'do': 'trace', 'name': n, 'hull': True, 'points': [[-1140, y, 20, -1270, y, 20] for y in ys]}


# ---- 1 doors, zone, spawners, wall buys
st = [{'do': 'waves', 'on': False}, {'do': 'money', 'value': 20000},
      {'do': 'tp', 'at': [-1000, 3900, 1], 'yaw': 180, 'snap': True}, {'do': 'state', 'name': 'start'},
      call('g1_zone', 'zone_arc_closed', 'arcade'),
      exp('probe:zone_arc_closed.defined', 'eq', 1, "the layer's zone is a spawn volume of the map"),
      exp('probe:zone_arc_closed.active', 'eq', 0, 'not active before its door is bought'),
      tr('closed'), exp('trace:closed_0.hit', 'eq', 1, 'the closed D4 stops the hull (y 3850)'), exp('trace:closed_1.hit', 'eq', 1, 'at y 3900'), exp('trace:closed_2.hit', 'eq', 1, 'at y 3950'),
      call('dp_cross', 'cross_closed', 0, -1200, 3900, 10),
      exp('probe:cross_closed.phys_blocked', 'eq', 1, 'a player-physics line across the door plane is stopped'),
      {'do': 'spawn', 'tag': 'shut', 'at': [-1400, 3900, 1], 'count': 2, 'place': True},
      {'do': 'chase', 'tag': 'shut', 's': 20, 'reach': 96, 'allow_partial': True},
      exp('chase:shut.reached', 'eq', 0, 'zombies placed in the Arcade do not path through the closed door'),
      {'do': 'kill', 'tag': 'shut'},
      {'do': 'use', 'name': 'door', 'kind': dk, 'near': dn},
      exp('use:door.found', 'eq', 1, "D4's purchase struct is a stock interaction"), exp('use:door.spent', 'eq', 1000, 'the door costs what the document says'),
      {'do': 'wait', 's': 1}, tr('open'),
      exp('trace:open_0.hit', 'eq', 0, 'the bought door lets the hull through (y 3850)'), exp('trace:open_1.hit', 'eq', 0, 'y 3900'), exp('trace:open_2.hit', 'eq', 0, 'y 3950'),
      {'do': 'spawn', 'tag': 'thru', 'at': [-1400, 3900, 1], 'count': 2, 'place': True},
      {'do': 'chase', 'tag': 'thru', 's': 30, 'reach': 96, 'allow_partial': True},
      exp('chase:thru.reached', 'eq', 2, 'control: the same placed zombies come through once the door is bought'),
      {'do': 'kill', 'tag': 'thru'},
      call('g1_zone', 'zone_arc_open', 'arcade'), exp('probe:zone_arc_open.active', 'eq', 1, 'buying the door activates the Arcade zone'),
      {'do': 'tp', 'at': [-2000, 3900, 1], 'yaw': 0, 'snap': True},
      call('g1_zone', 'zone_arc_in', 'arcade'), exp('probe:zone_arc_in.touching', 'eq', 1, 'the player in the Arcade is in its volume'),
      {'do': 'spawn', 'tag': 'new', 'at': [-2300 + 62, 4535, 1], 'count': 2, 'place': False},
      {'do': 'chase', 'tag': 'new', 's': 40, 'reach': 96, 'allow_partial': True},
      exp('chase:new.reached', 'eq', 2, "zombies of the Arcade's own spawner (bay 3) reach the player in the Arcade (no 'no nav cell under the source')"),
      {'do': 'kill', 'tag': 'new'},
      {'do': 'spawn', 'tag': 'old', 'at': [-96, 4416, 1], 'count': 2, 'place': False},
      {'do': 'chase', 'tag': 'old', 's': 120, 'reach': 96, 'allow_partial': True},
      exp('chase:old.reached', 'eq', 2, 'zombies of a ticket hall spawner cross the hall and the bought door to the player in the Arcade'),
      {'do': 'kill', 'tag': 'old'}]
for k, b in enumerate(buys):
    st += [{'do': 'tp', 'at': [b['origin'][0], 3560, 1], 'yaw': 270, 'snap': True}, {'do': 'use', 'name': 'buy%d' % k, 'kind': b['kind'], 'near': b['origin']},
           exp('use:buy%d.found' % k, 'eq', 1, 'wall buy %d (%s) is a stock interaction' % (k, b['kind'])), exp('use:buy%d.has' % k, 'eq', 1, 'the player holds the weapon')]
st += [{'do': 'state', 'name': 'end'}]
save(plan('sz8_doors', 'Round 8: the Arcade layer behind D4 (debris_1000, hall wall x -1200, y 3804..3996): closed blocks hull and zombies, bought opens, zone active, the Arcade spawners and a hall spawner reach the player inside, both wall buys.', ['doorprobe', 'g1probe'], st))

# ---- 2 power and perks
st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 100000},
      call('szp_setup', 'b_setup'), call('szp_state', 'b0'),
      use('revive', 'perk_machine_revive'), use('tough_nopower', 'perk_machine_tough', s=3), use('deadeye_nopower', 'perk_machine_deadeye', s=3),
      call('sz_power_direct', 'power', 20), call('szp_state', 'b_power')]
for k in NEW:
    st += [use('b_' + k[13:], k)]
st += [call('szp_state', 'b_end')]
ex = [exp('probe:b_setup.module', 'eq', 1, 'the perk module runs in the map'),
      exp('use:revive.perks1', 'eq', 1, "Up 'N Atoms given before the power (its own generator)"),
      exp('use:tough_nopower.spent', 'eq', 0, "Tuff 'Nuff refuses before the power"), exp('use:tough_nopower.perks1', 'eq', 1, 'nothing given before the power'),
      exp('use:deadeye_nopower.spent', 'eq', 0, 'Deadeye (a new perk) refuses before the power'), exp('use:deadeye_nopower.perks1', 'eq', 1, 'nothing given before the power'),
      exp('probe:power.found', 'eq', 1, 'the generator interaction exists'), exp('probe:power.power', 'eq', 1, 'power on after the generator'),
      exp('probe:b_end.count', 'eq', 6, 'the player holds six perks: revive and the five new ones')]
ex += [exp('use:b_%s.spent' % k[13:], 'eq', PRICE[k], '%s at %d' % (k[13:], PRICE[k])) for k in NEW]
ex += [exp('use:b_%s.perks1' % k[13:], 'eq', i + 2, '%s is active (perk count %d)' % (k[13:], i + 2)) for i, k in enumerate(NEW)]
save(plan('sz8_power_perks', "Round 8: power off then on (the map's own generator activation), perk machines gated by power, each of the five new perks bought at its price and active (six perks held).", ['szperks', 'szaccept'], st + ex))

# ---- 3 rounds in the Arcade
st = [{'do': 'money', 'value': 20000}, {'do': 'use', 'name': 'door', 'kind': dk, 'near': dn}, exp('use:door.spent', 'eq', 1000, 'D4 bought'),
      {'do': 'tp', 'at': [-2000, 3900, 1], 'yaw': 0, 'snap': True}, call('g1_zone', 'zone_in', 'arcade'), exp('probe:zone_in.touching', 'eq', 1, 'the player stands in the Arcade'),
      {'do': 'ignore', 'on': False}, {'do': 'waves', 'on': True}]
for w in (1, 2, 3):
    st += [call('sz8_round_play', 'r%d' % w, w, 0, 240, 60, s=0.5), exp('probe:r%d.started' % w, 'eq', 1, 'round %d began' % w), exp('probe:r%d.stall' % w, 'eq', 0, 'round %d did not stall' % w),
           exp('probe:r%d.stuck' % w, 'eq', 0, 'no zombie stuck in round %d' % w), exp('probe:r%d.seen' % w, 'ge', 3, 'round %d spawned zombies' % w)]
save(plan('sz8_rounds', 'Round 8: rounds 1 to 3 played with the stock spawning and round loop, the player standing in the Arcade behind the bought D4; every zombie that stays in play must reach the player (stuck 0, stall 0).', ['g1probe', 'szaccept', 'sz8arc'], st, 'normal'))

# ---- 4 HUD icons of the new perks (a client plan: the frames carry the HUD)
st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'money', 'value': 100000}, call('szp_setup', 'b_setup'), call('sz_power_direct', 'power', 20),
      {'do': 'tp', 'at': [-2000, 3900, 1], 'yaw': 0, 'snap': True}, {'do': 'wait', 's': 2}, {'do': 'capture', 'name': 'hud_0_none', 'pause': 0.5}]
for i, k in enumerate(['perk_machine_revive'] + NEW):
    st += [call('szp_give', k), {'do': 'wait', 's': 2}, {'do': 'capture', 'name': 'hud_%d_%s' % (i + 1, k[13:]), 'pause': 0.5}, call('szp_state', 'st_%s' % k[13:])]
save(plan('sz8_hud', 'Round 8: the HUD perk row with each new perk given in turn (the player stands in the Arcade, power on): one frame after each, the HUD on.', ['szperks', 'szaccept'], st))
json.dump({'schema': 'iw7.gamelab-batch/1', 'runs': [{'name': n, 'plan': n + '.json', 'usermap': um, 'library_dir': os.path.join(out, 'lib')} for n in ('sz8_doors', 'sz8_power_perks', 'sz8_rounds', 'sz8_hud')]}, open(os.path.join(out, 'batch.json'), 'w'), indent=1)
