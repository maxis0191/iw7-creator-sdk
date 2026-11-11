"""Station Zero Q1 (the road to Pack-a-Punch) and T1 (the Capsule Post): the map's headless test plans and their report.

  sz_q1t1.py plans <src> <out>          gamelab plans (library szq of iw7-paris-server ops/gamelab/lib), headless:
      <map>_q1_steps        power, the four clocks, the road (a wrong lever, then the three lit ones), the Conductor (leaves
                            at a round end, comes back), the Handle, the cab, the teleport, Pack-a-Punch at the Terminus,
                            the return and the cooldown, solo, in order; every refusal before its step
      <map>_q1_order_coop   out of order (clocks 4..1, levers in reverse), two to four players: the burst size, the Handle
                            carrier going down and leaving, a downed player and zombies inside car 1 at departure, a player
                            left outside (the spawn pause holds off)
      <map>_q1_late_round   waves on from round 20: every player at the Terminus for 40 s, the spawn pause read back
      <map>_t1_routes       the four hatches unsealed, all 12 routes on BLOW, the lever, all 12 on DRAW (24 rides)
      <map>_t1_rules        every refusal, the dial (tap and hold of Use), capsules, rest, changeover, inspection,
                            blowback, a player standing on the hatch, two riders on the last capsule, a rider who leaves
  sz_q1t1.py report <run> [<run> ...]   every T1 ride sample (position and zone each 0.25 s), the Q1 and T1 events and
                            the script errors of the runs, as one JSON summary (exit 1 if a ride left its zone)
"""
import argparse, glob, json, os, re, sys

RING = ['PLAZA', 'EXCHANGE', 'BARN', 'PARLOUR']
PRICE = {1: 250, 2: 400, 3: 550}


def segs(a, b, d):
    ia, ib = RING.index(a), RING.index(b)
    return (ib - ia) % 4 if d == 'BLOW' else (ia - ib) % 4


def head(money=500000):
    return [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': money}]


def exp(that, op, v, why):
    return {'do': 'expect', 'that': that, op: v, 'why': why}


def plan(mapname, name, about, steps, libs=('szq',)):
    return {'schema': 'iw7.gamelab-plan/1', 'name': '%s_%s' % (mapname, name), 'map': mapname, 'about': about,
            'libraries': list(libs), 'steps': steps}


class Lay:
    def __init__(self, src):
        self.lay = json.load(open(os.path.join(src, 'layout.json')))
        self.map = self.lay.get('map', 'cp_iwz')
        self.m = {}
        for m in self.lay['markers']:
            self.m.setdefault(m['kind'], []).append(m)
        its = self.lay['interactions']
        self.gen = next(i for i in its if i['kind'] == 'generator')['origin']
        self.pap = next(i for i in its if i['kind'] == 'weapon_upgrade')['origin']
        self.hatch = {m['id']: m for m in self.m.get('hatch', [])}

    def at(self, kind, id_=None):
        for m in self.m.get(kind, []):
            if id_ is None or m['id'] == id_:
                return [round(c, 1) for c in m['origin']]
        raise KeyError(kind, id_)


def q1_power(L):
    return [{'do': 'use', 'name': 'power', 'kind': 'generator', 'near': L.gen, 's': 6}]


def q1_steps(L):
    car = L.at('quest_cab')
    clocks = [m for m in L.m['quest_clock']]
    s = head() + [{'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'}, {'do': 'take', 'give': 'iw7_g18_zm'},
                  {'do': 'call', 'fn': 'szq_state', 'args': ['q_start'], 's': 1}]
    e = [exp('probe:q_start.q1', 'eq', 1, 'the quest module runs on this map'), exp('probe:q_start.nclocks', 'eq', 4, 'four clocks are placed'),
         exp('probe:q_start.nlevers', 'eq', 8, 'eight levers are placed'), exp('probe:q_start.power', 'eq', 0, 'the power is off at the start'),
         exp('probe:q_start.tp', 'eq', 'idle', 'the teleport waits')]
    # refusals before power
    s += [{'do': 'use', 'name': 'clock_nopower', 'ent': 'iwz_q1_' + clocks[0]['id'], 'near': clocks[0]['origin'], 's': 1},
          {'do': 'use', 'name': 'cab_nohandle', 'ent': 'iwz_q1_cab', 'near': car, 's': 1},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_nopower'], 's': 1}]
    e += [exp('probe:q_nopower.clocks', 'eq', 0, 'a clock does not wind before the power'),
          exp('probe:q_nopower.armed', 'eq', 0, 'the cab needs the Handle')]
    s += q1_power(L)
    # a lever before the clocks; a tap (not a hold) on a clock
    s += [{'do': 'call', 'fn': 'szq_lever', 'args': [1, 0], 's': 2},
          {'do': 'dvar', 'name': 'iwz_test_hold', 'value': '0'},
          {'do': 'use', 'name': 'clock_tap', 'ent': 'iwz_q1_' + clocks[0]['id'], 'near': clocks[0]['origin'], 's': 1},
          {'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_early'], 's': 1}]
    e += [exp('probe:q_early.power', 'eq', 1, 'the power is on'), exp('probe:q_early.pulled', 'eq', 0, 'the levers are locked until the clocks are wound'),
          exp('probe:q_early.clocks', 'eq', 0, 'a tap does not wind a clock (hold Use 3 s)')]
    for k, c in enumerate(clocks):
        s += [{'do': 'use', 'name': 'clock_%d' % (k + 1), 'ent': 'iwz_q1_' + c['id'], 'near': c['origin'], 's': 3},
              {'do': 'call', 'fn': 'szq_state', 'args': ['q_clock%d' % (k + 1)], 's': 1}]
        e.append(exp('probe:q_clock%d.clocks' % (k + 1), 'eq', k + 1, 'clock %s (%s) is wound' % (c['id'], c['zone'])))
    e += [exp('probe:q_clock4.bursts', 'eq', 4, 'each clock raises a burst'), exp('probe:q_clock4.burstmade', 'ge', 12, 'the bursts spawned zombies (4 solo each)')]
    s += [{'do': 'call', 'fn': 'szq_kill_all', 's': 1},
          {'do': 'call', 'fn': 'szq_lever', 'args': [0, 0], 's': 2},
          {'do': 'call', 'fn': 'szq_lever', 'args': [1, 0], 's': 2},
          {'do': 'call', 'fn': 'szq_lever', 'args': [1, 1], 's': 2},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_two'], 's': 1},
          {'do': 'call', 'fn': 'szq_lever', 'args': [0, 1], 's': 2},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_sprung'], 's': 1},
          {'do': 'call', 'fn': 'szq_lever', 'args': [1, 0], 's': 2},
          {'do': 'call', 'fn': 'szq_lever', 'args': [1, 1], 's': 2},
          {'do': 'call', 'fn': 'szq_lever', 'args': [1, 2], 's': 2},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_road'], 's': 1}]
    e += [exp('probe:q_two.pulled', 'eq', 2, 'two lit levers lock over'), exp('probe:q_two.wrong', 'eq', 1, 'the first wrong lever counted'),
          exp('probe:q_sprung.pulled', 'eq', 0, 'a wrong lever springs every pulled lever back'), exp('probe:q_sprung.wrong', 'eq', 2, 'second wrong lever'),
          exp('probe:q_road.road', 'eq', 1, 'the three lit levers set the road'), exp('probe:q_road.bursts', 'eq', 6, 'each wrong lever drops 4 zombies (a burst)')]
    # the Conductor: comes within 20 s, leaves at a round end, comes back at the next start
    s += [{'do': 'wait', 's': 9}, {'do': 'call', 'fn': 'szq_state', 'args': ['q_cond'], 's': 1},
          {'do': 'call', 'fn': 'szq_round_end', 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['q_left'], 's': 1},
          {'do': 'call', 'fn': 'szq_round_start', 's': 1}, {'do': 'wait', 's': 4}, {'do': 'call', 'fn': 'szq_state', 'args': ['q_back'], 's': 1},
          {'do': 'call', 'fn': 'szq_kill_conductor', 's': 3}, {'do': 'call', 'fn': 'szq_state', 'args': ['q_dead'], 's': 1}]
    e += [exp('probe:q_cond.conductor', 'eq', 'walking', 'the Conductor steps out after the road is set'),
          exp('probe:q_cond.chealth', 'gt', 300, 'he has three times a zombie\'s health'),
          exp('probe:q_left.conductor', 'eq', 'left', 'he leaves when the round ends'), exp('probe:q_left.handle', 'eq', 'none', 'nothing dropped when he leaves'),
          exp('probe:q_back.conductor', 'eq', 'walking', 'he comes back at the next round'), exp('probe:q_back.cspawns', 'eq', 2, 'second appearance'),
          exp('probe:q_dead.conductor', 'eq', 'dead', 'killed'), exp('probe:q_dead.handle', 'eq', 'dropped', 'he drops the Dead-Man\'s Handle')]
    s += [{'do': 'use', 'name': 'handle', 'ent': 'iwz_q1_handle', 'near': car, 's': 1},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_carry'], 's': 1},
          {'do': 'use', 'name': 'cab_fit', 'ent': 'iwz_q1_cab', 'near': car, 's': 2},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_armed'], 's': 1},
          {'do': 'use', 'name': 'cab_go', 'ent': 'iwz_q1_cab', 'near': car, 's': 1},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['away', 12], 's': 12},
          {'do': 'use', 'name': 'pap', 'kind': 'weapon_upgrade', 'near': L.pap, 's': 6, 'again': True},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_terminus'], 's': 1},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['cooldown', 45], 's': 45},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_back_car'], 's': 1},
          {'do': 'use', 'name': 'cab_cooldown', 'ent': 'iwz_q1_cab', 'near': car, 's': 1},
          {'do': 'call', 'fn': 'szq_state', 'args': ['q_end'], 's': 1}]
    e += [exp('probe:q_carry.handle', 'eq', 'carried', 'the Handle is taken'), exp('probe:q_armed.armed', 'eq', 1, 'the Handle fitted in the cab arms the teleport'),
          exp('probe:tp_away.got', 'eq', 'away', 'boarding 4 s then the crossing'), exp('probe:tp_away.volume', 'eq', 'terminus', 'the player stands in the Terminus'),
          exp('probe:tp_away.paused', 'eq', 1, 'every player at the Terminus: the round\'s spawning pauses'),
          exp('use:pap.spent', 'gt', 0, 'Pack-a-Punch at the Terminus takes points'),
          exp('probe:q_terminus.travellers', 'eq', 1, 'one traveller'),
          exp('probe:tp_cooldown.got', 'eq', 'cooldown', 'the 40 s stay ends'), exp('probe:q_back_car.volume', 'eq', 'platform_east', 'back in car 1 on Platform A'),
          exp('probe:q_back_car.returned', 'eq', 1, 'the traveller came back'), exp('probe:q_back_car.paused', 'eq', 0, 'the spawning runs again'),
          exp('probe:q_end.tp', 'eq', 'cooldown', 'not in service for 150 s'), exp('probe:q_end.visits', 'eq', 1, 'one visit')]
    return plan(L.map, 'q1_steps', 'Q1 in order, solo: refusals, power, four clocks, the road with wrong levers, the Conductor (round end and return), the Handle, the cab, the Terminus and Pack-a-Punch, the return (headless).', s + e)


def q1_order_coop(L):
    car = L.at('quest_cab')
    clocks = list(reversed(L.m['quest_clock']))
    inside = [car[0] + 120, car[1], car[2]]
    outside = [car[0] + 200, car[1] + 160, car[2]]
    s = head() + [{'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'}, {'do': 'call', 'fn': 'szq_bots', 'args': [1], 's': 8}]
    s += q1_power(L)
    s += [{'do': 'call', 'fn': 'szq_lever', 'args': [1, 2], 's': 2}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_locked'], 's': 1}]
    e = [exp('probe:c_locked.pulled', 'eq', 0, 'the road before the clocks is refused')]
    for k, c in enumerate(clocks):
        s += [{'do': 'use', 'name': 'oclock_%d' % k, 'ent': 'iwz_q1_' + c['id'], 'near': c['origin'], 's': 3}]
        if k == 0:
            s += [{'do': 'wait', 's': 6}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_burst2'], 's': 1}]
    s += [{'do': 'call', 'fn': 'szq_kill_all', 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_clocks'], 's': 1}]
    e += [exp('probe:c_burst2.burstmade', 'eq', 6, 'two players: a clock raises 6 zombies'),
          exp('probe:c_clocks.clocks', 'eq', 4, 'the clocks wind in any order')]
    s += [{'do': 'call', 'fn': 'szq_lever', 'args': [1, 2], 's': 2}, {'do': 'call', 'fn': 'szq_lever', 'args': [1, 1], 's': 2},
          {'do': 'call', 'fn': 'szq_lever', 'args': [1, 0], 's': 2}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_road'], 's': 1},
          {'do': 'call', 'fn': 'szq_bots', 'args': [2], 's': 12}]
    e += [exp('probe:c_road.road', 'eq', 1, 'the lit levers in any order set the road'), exp('probe:bots.players', 'eq', 4, 'four players after two more joined')]
    # the Handle: bot 0 takes it and goes down (dropped), bot 1 takes it and leaves (dropped), then the tested player
    s += [{'do': 'wait', 's': 6}, {'do': 'call', 'fn': 'szq_kill_conductor', 's': 3},
          {'do': 'call', 'fn': 'szq_bot_use', 'args': [0, 'iwz_q1_handle'], 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_bot_carry'], 's': 1},
          {'do': 'call', 'fn': 'szq_bot_down', 'args': [0], 's': 6}, {'do': 'wait', 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_down_drop'], 's': 1},
          {'do': 'call', 'fn': 'szq_bot_use', 'args': [1, 'iwz_q1_handle'], 's': 1},
          {'do': 'call', 'fn': 'szq_bot_kick', 'args': [1], 's': 2}, {'do': 'wait', 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_left_drop'], 's': 1},
          {'do': 'use', 'name': 'c_handle', 'ent': 'iwz_q1_handle', 'near': car, 's': 1},
          {'do': 'use', 'name': 'c_fit', 'ent': 'iwz_q1_cab', 'near': car, 's': 2}]
    e += [exp('probe:c_bot_carry.handle', 'eq', 'carried', 'a second player takes the Handle'),
          exp('probe:down_0.downed', 'eq', 1, 'the carrier is down'), exp('probe:c_down_drop.handle', 'eq', 'dropped', 'a downed carrier drops the Handle'),
          exp('probe:kick_1.players', 'eq', 3, 'the carrier left'), exp('probe:c_left_drop.handle', 'eq', 'dropped', 'a carrier who leaves drops the Handle')]
    # departure: the downed bot 0 inside car 1 travels, bot 2 stays outside on its feet, two zombies inside car 1 are put out
    s += [{'do': 'call', 'fn': 'szq_bot_to', 'args': [0, inside], 's': 1}, {'do': 'call', 'fn': 'szq_bot_to', 'args': [2, outside], 's': 1},
          {'do': 'spawn', 'tag': 'car', 'at': [car[0] + 300, car[1], car[2]], 'count': 2, 'place': True},
          {'do': 'use', 'name': 'c_go', 'ent': 'iwz_q1_cab', 'near': car, 's': 1},
          {'do': 'call', 'fn': 'szq_zombies_to', 'args': [[car[0] + 300, car[1], car[2]], 1200], 's': 0.5},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['away', 12], 's': 12}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_away'], 's': 1},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['cooldown', 45], 's': 45}, {'do': 'call', 'fn': 'szq_state', 'args': ['c_back'], 's': 1}]
    e += [exp('probe:c_away.travellers', 'eq', 2, 'the player at the cab and the downed player inside car 1 travel'),
          exp('probe:c_away.pushedout', 'ge', 1, 'zombies inside car 1 are put out on the platform'),
          exp('probe:c_away.paused', 'eq', 0, 'a player on his feet outside: the round goes on'),
          exp('probe:c_away.volume', 'eq', 'terminus', 'the tested player is at the Terminus'),
          exp('probe:c_back.returned', 'ge', 2, 'both came back'), exp('probe:c_back.volume', 'eq', 'platform_east', 'back in car 1')]
    return plan(L.map, 'q1_order_coop', 'Q1 out of order with two to four players: refusals, clocks 4..1, levers in reverse, the burst size, the Handle carrier down and leaving, departure with a downed player inside and zombies in car 1, a player left outside (headless).', s + e)


def q1_late_round(L):
    car = L.at('quest_cab')
    clocks = L.m['quest_clock']
    s = [{'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 500000}, {'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'},
         {'do': 'waves', 'on': False}]
    s += q1_power(L)
    for k, c in enumerate(clocks):
        s.append({'do': 'use', 'name': 'lclock_%d' % k, 'ent': 'iwz_q1_' + c['id'], 'near': c['origin'], 's': 2})
    s += [{'do': 'call', 'fn': 'szq_kill_all', 's': 1}] + [{'do': 'call', 'fn': 'szq_lever', 'args': [1, k], 's': 2} for k in range(3)]
    s += [{'do': 'wait', 's': 6}, {'do': 'call', 'fn': 'szq_kill_conductor', 's': 3},
          {'do': 'use', 'name': 'l_handle', 'ent': 'iwz_q1_handle', 'near': car, 's': 1},
          {'do': 'use', 'name': 'l_fit', 'ent': 'iwz_q1_cab', 'near': car, 's': 2},
          {'do': 'call', 'fn': 'szq_set_wave', 'args': [19], 's': 1}, {'do': 'rounds', 'name': 'r20', 'to': 20, 's': 150}, {'do': 'waves', 'on': True}, {'do': 'wait', 's': 15},
          {'do': 'call', 'fn': 'szq_state', 'args': ['l_before'], 's': 1},
          {'do': 'use', 'name': 'l_go', 'ent': 'iwz_q1_cab', 'near': car, 's': 1},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['away', 12], 's': 12}, {'do': 'call', 'fn': 'szq_state', 'args': ['l_away0'], 's': 1},
          {'do': 'wait', 's': 30}, {'do': 'call', 'fn': 'szq_state', 'args': ['l_away30'], 's': 1},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['cooldown', 20], 's': 20}, {'do': 'wait', 's': 10},
          {'do': 'call', 'fn': 'szq_state', 'args': ['l_after'], 's': 1}, {'do': 'waves', 'on': False}]
    e = [exp('probe:set_wave.wave', 'eq', 19, 'the next round is 20'), exp('probe:l_before.wave', 'ge', 20, 'round 20 runs'),
         exp('probe:l_away0.volume', 'eq', 'terminus', 'the only player is at the Terminus'),
         exp('probe:l_away0.paused', 'eq', 1, 'the round\'s spawning pauses'),
         exp('probe:l_away30.alive', 'le', '@probe:l_away0.alive', 'no zombie spawns while everyone is away'),
         exp('probe:l_after.paused', 'eq', 0, 'the spawning resumes'), exp('probe:l_after.volume', 'eq', 'platform_east', 'back in car 1')]
    return plan(L.map, 'q1_late_round', 'Q1: the whole team at the Terminus for 40 s in round 20 with waves on: the spawn pause and the zombies alive read back (headless).', s + e)


def t1_routes(L):
    s = head() + [{'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'}, {'do': 'call', 'fn': 'szq_state', 'args': ['t_start'], 's': 1}]
    e = [exp('probe:t_start.t1', 'eq', 1, 'the Capsule Post module runs'), exp('probe:t_start.dir', 'eq', 'BLOW', 'the Bellows starts on BLOW')]
    s += q1_power(L)
    for h in RING:
        m = L.hatch[h]
        s.append({'do': 'use', 'name': 'unseal_' + h.lower(), 'ent': 'iwz_t1_hatch_' + h.lower(), 'near': m['origin'], 's': 1})
        e.append(exp('use:unseal_%s.spent' % h.lower(), 'eq', 750, 'unsealing %s costs 750' % h))
    s.append({'do': 'call', 'fn': 'szq_state', 'args': ['t_open'], 's': 1})
    e.append(exp('probe:t_open.unsealed', 'eq', 4, 'all four hatches unsealed'))
    zone = {h: L.hatch[h]['zone'] for h in RING}
    for d in ('BLOW', 'DRAW'):
        if d == 'DRAW':
            lv = L.at('post_lever')
            s += [{'do': 'use', 'name': 'lever', 'ent': 'iwz_t1_lever', 'near': lv, 's': 1}, {'do': 'call', 'fn': 'szq_wait_changeover', 's': 14}]
            e.append(exp('probe:changeover_done.dir', 'eq', 'DRAW', 'the lever swaps BLOW for DRAW after 12 s'))
        for a in RING:
            for b in RING:
                if a == b:
                    continue
                n = ('r_%s_%s_%s' % (d, a, b)).lower()[:40]
                sg = segs(a, b, d)
                s += [{'do': 'call', 'fn': 'szq_rest_clear', 'args': [1], 's': 0}, {'do': 'call', 'fn': 'szq_ride', 'args': [n, a, b], 's': 9}]
                e += [exp('probe:%s.arrived' % n, 'eq', 1, '%s %s to %s arrives' % (d, a, b)),
                      exp('probe:%s.spent' % n, 'eq', PRICE[sg], '%d segment(s): %d points' % (sg, PRICE[sg])),
                      exp('probe:%s.lsegs' % n, 'eq', sg, 'ring distance on %s' % d),
                      exp('probe:%s.volume' % n, 'eq', zone[b], 'the rider stands in %s' % zone[b]),
                      exp('probe:%s.hdist' % n, 'le', 80, 'at the %s hatch' % b)]
    return plan(L.map, 't1_routes', 'T1: the four hatches unsealed, all 12 routes on BLOW, the Bellows lever, all 12 routes on DRAW; rider position and zone sampled every 0.25 s (headless).', s + e)


def t1_rules(L):
    P, B, E = L.hatch['PLAZA'], L.hatch['BARN'], L.hatch['EXCHANGE']
    lv = L.at('post_lever')
    s = head(500) + [{'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'},
                     {'do': 'use', 'name': 'nopower', 'ent': 'iwz_t1_hatch_plaza', 'near': P['origin'], 's': 1}]
    s += q1_power(L)
    s += [{'do': 'use', 'name': 'poor_unseal', 'ent': 'iwz_t1_hatch_plaza', 'near': P['origin'], 's': 1},
          {'do': 'money', 'value': 500000},
          {'do': 'use', 'name': 'unseal_plaza', 'ent': 'iwz_t1_hatch_plaza', 'near': P['origin'], 's': 1},
          {'do': 'call', 'fn': 'szq_ride', 'args': ['to_sealed', 'PLAZA', 'BARN'], 's': 2},
          {'do': 'use', 'name': 'unseal_barn', 'ent': 'iwz_t1_hatch_barn', 'near': B['origin'], 's': 1},
          {'do': 'dvar', 'name': 'iwz_test_hold', 'value': '0'},
          {'do': 'use', 'name': 'tap1', 'ent': 'iwz_t1_hatch_plaza', 'near': P['origin'], 's': 1},
          {'do': 'call', 'fn': 'szq_state', 'args': ['dial1'], 's': 1},
          {'do': 'use', 'name': 'tap2', 'ent': 'iwz_t1_hatch_plaza', 'near': P['origin'], 's': 1},
          {'do': 'call', 'fn': 'szq_state', 'args': ['dial2'], 's': 1},
          {'do': 'dvar', 'name': 'iwz_test_hold', 'value': '1'},
          {'do': 'use', 'name': 'hold_send', 'ent': 'iwz_t1_hatch_plaza', 'near': P['origin'], 's': 7},
          {'do': 'call', 'fn': 'szq_state', 'args': ['sent'], 's': 1},
          {'do': 'call', 'fn': 'szq_ride', 'args': ['rest', 'BARN', 'PLAZA'], 's': 2}]
    e = [exp('probe:dial1.dial_plaza', 'eq', 2, 'a tap turns the dial to the only unsealed address (BARN)'),
         exp('probe:dial2.dial_plaza', 'eq', 2, 'a tap on a dial with one address does nothing'),
         exp('probe:to_sealed.started', 'eq', 0, 'a sealed address is refused'), exp('probe:to_sealed.spent', 'eq', 0, 'a refusal takes nothing'),
         exp('use:poor_unseal.spent', 'eq', 0, 'not enough points to unseal: nothing taken'),
         exp('probe:sent.arrivals', 'eq', 1, 'holding Use at the hatch sends the rider'),
         exp('probe:sent.lto', 'eq', 'BARN', 'to the dialled address'), exp('probe:sent.lprice', 'eq', 400, 'two segments: 400'),
         exp('probe:sent.volume', 'eq', B['zone'], 'the rider stands in the Car Barn'),
         exp('probe:rest.started', 'eq', 0, 'a rider who just arrived rests 45 s')]
    # capsules: PLAZA has used one; one more leaves, the third is refused
    s += [{'do': 'call', 'fn': 'szq_rest_clear', 'args': [0], 's': 0}, {'do': 'call', 'fn': 'szq_ride', 'args': ['back1', 'BARN', 'PLAZA'], 's': 9},
          {'do': 'call', 'fn': 'szq_rest_clear', 'args': [0], 's': 0}, {'do': 'call', 'fn': 'szq_ride', 'args': ['cap2', 'PLAZA', 'BARN'], 's': 9}]
    s += [{'do': 'call', 'fn': 'szq_ride', 'args': ['cap_x', 'BARN', 'PLAZA'], 's': 2}]   # BARN: rest not cleared -> rest
    # the capsule rule on PLAZA: both used within 30 s
    s += [{'do': 'call', 'fn': 'szq_bots', 'args': [2], 's': 10},
          {'do': 'call', 'fn': 'szq_bot_ride', 'args': [0, 'PLAZA', 'BARN'], 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['caps'], 's': 1}]
    e += [exp('probe:back1.arrived', 'eq', 1, 'BARN to PLAZA'), exp('probe:cap2.arrived', 'eq', 1, 'the second PLAZA capsule leaves'),
          exp('probe:botride_0.started', 'eq', 0, 'no third capsule within 30 s'), exp('probe:caps.r_capsule', 'ge', 1, 'refused: no capsule')]
    # changeover and the lever's reset
    s += [{'do': 'use', 'name': 'lever', 'ent': 'iwz_t1_lever', 'near': lv, 's': 1}, {'do': 'call', 'fn': 'szq_rest_clear', 'args': [0], 's': 0},
          {'do': 'call', 'fn': 'szq_ride', 'args': ['during_change', 'PLAZA', 'BARN'], 's': 1}, {'do': 'call', 'fn': 'szq_wait_changeover', 's': 14},
          {'do': 'use', 'name': 'lever_again', 'ent': 'iwz_t1_lever', 'near': lv, 's': 1}, {'do': 'call', 'fn': 'szq_state', 'args': ['after_change'], 's': 1}]
    e += [exp('probe:during_change.started', 'eq', 0, 'no launch during the changeover'), exp('probe:changeover_done.dir', 'eq', 'DRAW', 'DRAW after 12 s'),
          exp('probe:after_change.throws', 'eq', 1, 'the lever cannot be thrown again for 45 s'), exp('probe:after_change.r_changeover', 'ge', 1, 'refused: changeover')]
    # inspection: a stand-in Inspector at PLAZA closes it, and for 15 s after he goes
    s += [{'do': 'call', 'fn': 'szq_inspector', 'args': [P['origin']], 's': 2}, {'do': 'call', 'fn': 'szq_rest_clear', 'args': [0], 's': 0},
          {'do': 'call', 'fn': 'szq_ride', 'args': ['inspected', 'PLAZA', 'BARN'], 's': 1},
          {'do': 'call', 'fn': 'szq_inspector', 'args': [[8700, 8700, 0]], 's': 2}, {'do': 'call', 'fn': 'szq_state', 'args': ['insp_after'], 's': 1},
          {'do': 'wait', 's': 15}, {'do': 'call', 'fn': 'szq_state', 'args': ['insp_open'], 's': 1}]
    e += [exp('probe:inspected.started', 'eq', 0, 'INSPECTION: the hatch sells nothing'), exp('probe:insp_after.insp_plaza', 'eq', 1, 'closed until 15 s after he moved away'),
          exp('probe:insp_open.insp_plaza', 'eq', 0, 'open again')]
    # downed, busy, points
    s += [{'do': 'call', 'fn': 'szq_bot_down', 'args': [1], 's': 6}, {'do': 'call', 'fn': 'szq_bot_ride', 'args': [1, 'BARN', 'PLAZA'], 's': 1},
          {'do': 'call', 'fn': 'szq_busy', 'args': [1], 's': 0}, {'do': 'call', 'fn': 'szq_rest_clear', 'args': [1], 's': 0},
          {'do': 'call', 'fn': 'szq_ride', 'args': ['busy', 'PLAZA', 'BARN'], 's': 1}, {'do': 'call', 'fn': 'szq_busy', 'args': [0], 's': 0},
          {'do': 'money', 'value': 100}, {'do': 'call', 'fn': 'szq_ride', 'args': ['poor', 'PLAZA', 'BARN'], 's': 1}, {'do': 'money', 'value': 500000},
          {'do': 'call', 'fn': 'szq_state', 'args': ['refusals'], 's': 1}]
    e += [exp('probe:botride_1.started', 'eq', 0, 'a downed player cannot board'), exp('probe:busy.started', 'eq', 0, 'a busy player (emote, Terminus) is refused'),
          exp('probe:poor.started', 'eq', 0, 'not enough points'), exp('probe:poor.spent', 'eq', 0, 'nothing taken'),
          exp('probe:refusals.r_downed', 'ge', 1, 'refused: downed'), exp('probe:refusals.r_busy', 'ge', 1, 'refused: busy'),
          exp('probe:refusals.r_points', 'ge', 2, 'refused: points (unseal and ride)'), exp('probe:refusals.r_power', 'ge', 1, 'refused: power'),
          exp('probe:refusals.r_rest', 'ge', 2, 'refused: rest'), exp('probe:refusals.r_sealed', 'ge', 1, 'refused: sealed'),
          exp('probe:refusals.r_inspection', 'ge', 1, 'refused: inspection')]
    # blowback: three zombies at the PLAZA mouth come out at BARN 2 s after the rider; bot 0 stands on the BARN hatch
    s += [{'do': 'call', 'fn': 'szq_rest_clear', 'args': [1], 's': 0}, {'do': 'call', 'fn': 'szq_bot_to', 'args': [0, B['origin']], 's': 1},
          {'do': 'call', 'fn': 'szq_hatch_zombies', 'args': ['PLAZA', 3], 's': 12},
          {'do': 'call', 'fn': 'szq_ride', 'args': ['blowback', 'PLAZA', 'BARN'], 's': 9}, {'do': 'wait', 's': 2.5},
          {'do': 'call', 'fn': 'szq_near_hatch', 'args': ['bb_out', 'BARN'], 's': 1}, {'do': 'call', 'fn': 'szq_kill_all', 's': 1}]
    e += [exp('probe:blowback.lbb', 'ge', 1, 'zombies at the hatch are drawn in'), exp('probe:bb_out.blowout', 'ge', 1, 'they come out of the destination hatch'),
          exp('probe:bb_out.near', 'ge', 1, 'standing at the BARN hatch')]
    # two riders on the last capsule in the same frame; a rider who leaves mid-ride
    s += [{'do': 'call', 'fn': 'szq_race', 'args': [0, 'PLAZA', 'BARN'], 's': 9},
          {'do': 'call', 'fn': 'szq_ride_kick', 'args': [0, 'BARN', 'PLAZA'], 's': 10}, {'do': 'call', 'fn': 'szq_state', 'args': ['t_end'], 's': 1}]
    e += [exp('probe:race.first', 'eq', 1, 'the first Use wins the last capsule'), exp('probe:race.second', 'eq', 0, 'the second is refused'),
          exp('probe:ride_kick.started', 'eq', 1, 'the leaving rider had launched'), exp('probe:ride_kick.riding', 'eq', 0, 'the capsule completed empty: nobody riding')]
    return plan(L.map, 't1_rules', 'T1: every refusal, the dial (tap and hold), capsules, rest, changeover, inspection, blowback, a player on the hatch, the last capsule raced, a rider who leaves (headless).', s + e)


def travel_points(L):
    """every place a player arrives by the Post or the teleport: [(name, zone, point)]"""
    import math
    pts = []
    for h in RING:
        m = L.hatch[h]
        yaw = math.radians(m['yaw'] or 0)
        o = m['origin']
        pts.append(('hatch_' + h.lower(), m['zone'], [round(o[0] + math.cos(yaw) * 40, 1), round(o[1] + math.sin(yaw) * 40, 1), o[2]]))
    car = L.at('quest_cab')
    pts.append(('car1', 'platform_east', [car[0] + 200, car[1], car[2]]))
    pts.append(('terminus', 'terminus', L.at('terminus_arrival')))
    return pts


def travel(L, src, count=3, part=None, parts=3):
    """body walks and zombie cases at the travel points (the W1a method of scenegen.py labplans): the player walks with
    player physics from each arrival point to the zone's standing point and back, and zombies from that standing point
    reach a player standing on the arrival point. The Terminus has no spawner: the walk only, to Pack-a-Punch."""
    import math
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import iwz_emitcheck as EC
    from scenegen import simplify, NAV_LIFT
    nav = EC.Emit.load(src).nav
    zp = L.lay.get('zone_points', {})
    steps, e = head(), []
    tp_ = travel_points(L)
    for name, zone, p in [x for i, x in enumerate(tp_) if part is None or i * parts // len(tp_) == part]:
        goal = list(L.pap) if zone == 'terminus' else zp[zone]
        ln, path = nav.route(nav.nearest(p[0], p[1], p[2] + NAV_LIFT), nav.nearest(goal[0], goal[1], goal[2] + NAV_LIFT))
        if ln is None:
            e.append(exp('probe:no_route_%s.n' % name, 'eq', 1, 'no navigation route from %s to the zone point' % name))
            continue
        pts = [list(nav.a[k]['c']) for k in path]
        eps, s_ = 12.0, simplify(pts, 12.0)
        while len(s_) > 40:
            eps *= 1.5
            s_ = simplify(pts, eps)
        s_ = [[round(q[0], 1), round(q[1], 1), round(q[2] + 8, 1)] for q in s_]
        # car 1's doors are 84 units high: the headless walk's hull trace (18-unit step-up) cannot pass them, so the walk out
        # of car 1 is the client plan's real walk (walk:car_exit)
        if name != 'car1':
            steps += [{'do': 'move', 'name': name + '_out', 'path': s_}, {'do': 'move', 'name': name + '_in', 'path': s_[::-1]}]
            e += [exp('move:%s_out.reached' % name, 'eq', len(s_) - 1, 'a player walks from the %s arrival into %s' % (name, zone)),
                  exp('move:%s_in.reached' % name, 'eq', len(s_) - 1, 'and back to the %s arrival' % name)]
        if zone != 'terminus':
            tag = 'tz_' + name
            chase = max(30, int(math.ceil(ln / 20.0 + 10)))
            steps += [{'do': 'tp', 'at': p}, {'do': 'spawn', 'tag': tag, 'at': goal, 'count': count, 'place': True},
                      {'do': 'chase', 'tag': tag, 's': chase, 'allow_partial': True}, {'do': 'kill', 'tag': tag}]
            e.append(exp('chase:%s.reached' % tag, 'ge', count, 'zombies from the %s standing point reach a player at the %s arrival' % (zone, name)))
    return {'schema': 'iw7.gamelab-plan/1', 'name': '%s_q1t1_travel%s' % (L.map, '' if part is None else part + 1), 'map': L.map,
            'about': 'Q1/T1 travel points: body walks with player physics from every hatch, car 1 and the Terminus arrival, and zombie cases reaching a player standing on each arrival point (headless).',
            'steps': steps + e}


def client(L):
    """one private client session with real input (keys/1 channel): the whole quest, the Terminus trip and one Capsule Post
    ride, Use held and tapped by the game's own key handling; the prompts and the HUD read by UI dumps (ui steps), the
    Terminus and the arrival captured with their camera and depth for the frame-facts tool"""
    car = L.at('quest_cab')
    pap = list(L.pap)
    P, B = L.hatch['PLAZA'], L.hatch['BARN']
    s = head() + [{'do': 'take', 'give': 'iw7_g18_zm'}] + q1_power(L)
    e = []
    for k, c in enumerate(L.m['quest_clock']):
        s += [{'do': 'call', 'fn': 'szq_face', 'args': ['iwz_q1_' + c['id'], 44], 's': 1}]
        if k == 0:
            s += [{'do': 'ui', 'name': 'clock_hint'}]
        s += [{'do': 'hold', 'button': 'use'}, {'do': 'wait', 's': 3.6}, {'do': 'release', 'button': 'use'}, {'do': 'wait', 's': 1}]
        if k == 0:
            s += [{'do': 'ui', 'name': 'clock_wound'}]
    s += [{'do': 'call', 'fn': 'szq_state', 'args': ['k_clocks'], 's': 1}, {'do': 'call', 'fn': 'szq_kill_all', 's': 1}]
    e += [exp('probe:k_clocks.clocks', 'eq', 4, 'four clocks wound by holding Use (real input)')]
    for n in range(3):
        s += [{'do': 'call', 'fn': 'szq_face_lit', 'args': [n], 's': 1}, {'do': 'press', 'button': 'use', 's': 0.3}, {'do': 'wait', 's': 0.6}]
    s += [{'do': 'ui', 'name': 'road_set'}, {'do': 'call', 'fn': 'szq_state', 'args': ['k_road'], 's': 1},
          {'do': 'wait', 's': 6}, {'do': 'call', 'fn': 'szq_kill_conductor', 's': 3},
          {'do': 'call', 'fn': 'szq_face', 'args': ['iwz_q1_handle', 30], 's': 1}, {'do': 'press', 'button': 'use', 's': 0.3}, {'do': 'wait', 's': 0.6},
          {'do': 'ui', 'name': 'handle'},
          {'do': 'call', 'fn': 'szq_face', 'args': ['iwz_q1_cab', 36], 's': 1}, {'do': 'ui', 'name': 'cab_hint'},
          {'do': 'hold', 'button': 'use'}, {'do': 'wait', 's': 2.2}, {'do': 'release', 'button': 'use'}, {'do': 'wait', 's': 0.5},
          {'do': 'call', 'fn': 'szq_state', 'args': ['k_armed'], 's': 1},
          {'do': 'press', 'button': 'use', 's': 0.3}, {'do': 'wait', 's': 1}, {'do': 'ui', 'name': 'boarding'},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['away', 12], 's': 12},
          {'do': 'lookat', 'at': [pap[0], pap[1], pap[2] + 40]}, {'do': 'ui', 'name': 'terminus'},
          {'do': 'dvar', 'name': 'cg_drawGun', 'value': '0'}, {'do': 'dvar', 'name': 'cg_draw2D', 'value': '0'},
          {'do': 'capture', 'name': 'terminus', 'depth': True, 'pause': 0.5},
          {'do': 'dvar', 'name': 'cg_drawGun', 'value': '1'}, {'do': 'dvar', 'name': 'cg_draw2D', 'value': '1'},
          {'do': 'call', 'fn': 'szq_wait_tp', 'args': ['cooldown', 45], 's': 45}, {'do': 'ui', 'name': 'back_car'},
          {'do': 'call', 'fn': 'szq_state', 'args': ['k_back'], 's': 1},
          {'do': 'walk', 'name': 'car_exit', 'path': [[car[0] + 117, car[1], car[2] + 8], [car[0] + 117, car[1] + 140, car[2] + 8], [car[0] + 400, car[1] + 300, car[2] + 8]], 's': 15}]
    e += [exp('probe:k_road.road', 'eq', 1, 'the road set with three real Use presses on the lit levers'),
          exp('probe:k_armed.armed', 'eq', 1, 'the Handle fitted by holding Use in the cab'),
          exp('probe:tp_away.volume', 'eq', 'terminus', 'a real press of Use at the cab sends the player to the Terminus'),
          exp('probe:k_back.volume', 'eq', 'platform_east', 'back in car 1 after 40 s'),
          exp('walk:car_exit.reached', 'eq', 2, 'a real player walks out of car 1 onto the platform')]
    for h in (P, B):
        s += [{'do': 'call', 'fn': 'szq_face', 'args': ['iwz_t1_hatch_' + h['id'].lower(), 44], 's': 1}]
        if h is P:
            s += [{'do': 'ui', 'name': 'hatch_sealed'}]
        s += [{'do': 'hold', 'button': 'use'}, {'do': 'wait', 's': 2}, {'do': 'release', 'button': 'use'}, {'do': 'wait', 's': 0.5}]
    s += [{'do': 'call', 'fn': 'szq_face', 'args': ['iwz_t1_hatch_plaza', 44], 's': 1},
          {'do': 'press', 'button': 'use', 's': 0.2}, {'do': 'wait', 's': 0.8}, {'do': 'ui', 'name': 'dial'},
          {'do': 'call', 'fn': 'szq_state', 'args': ['k_dial'], 's': 1},
          {'do': 'hold', 'button': 'use'}, {'do': 'wait', 's': 1.3}, {'do': 'release', 'button': 'use'}, {'do': 'wait', 's': 1},
          {'do': 'ui', 'name': 'riding'}, {'do': 'wait', 's': 4.5}, {'do': 'ui', 'name': 'arrived'},
          {'do': 'dvar', 'name': 'cg_drawGun', 'value': '0'}, {'do': 'dvar', 'name': 'cg_draw2D', 'value': '0'},
          {'do': 'capture', 'name': 'arrival', 'depth': True, 'pause': 0.5},
          {'do': 'dvar', 'name': 'cg_drawGun', 'value': '1'}, {'do': 'dvar', 'name': 'cg_draw2D', 'value': '1'},
          {'do': 'call', 'fn': 'szq_state', 'args': ['k_end'], 's': 1}, {'do': 'wait', 's': 2}]
    e += [exp('probe:k_dial.unsealed', 'eq', 2, 'two hatches unsealed by holding Use'), exp('probe:k_dial.dial_plaza', 'eq', 2, 'a tap of Use dials BARN'),
          exp('probe:k_end.arrivals', 'eq', 1, 'holding Use sent the rider'), exp('probe:k_end.lto', 'eq', 'BARN', 'to BARN'),
          exp('probe:k_end.volume', 'eq', B['zone'], 'the player stands in the Car Barn')]
    return {'schema': 'iw7.gamelab-plan/1', 'name': '%s_q1t1_client' % L.map, 'map': L.map, 'libraries': ['szq'],
            'about': 'Q1 and T1 with a real player and real input (Use held and tapped): the whole quest, the Terminus trip and return, one Capsule Post ride; prompts and HUD as UI dumps, the Terminus and the arrival as frames with camera and depth.',
            'steps': s + e}


def all_plans(src):
    L = Lay(src)
    return [q1_steps(L), q1_order_coop(L), q1_late_round(L), t1_routes(L), t1_rules(L)] + [travel(L, src, part=k) for k in range(3)] + [client(L)]


# ------------------------------------------------------------------------------------------------ report

LINE = re.compile(r'\[IWZ level\] (Q1|T1) (\S+)(.*)')
PAIR = re.compile(r'(\w+)=(\([^)]*\)|\S+)')


def report(runs):
    rides, samples, events, errors = {}, [], [], []
    zone_by_hatch = {'PLAZA': 'cordon', 'EXCHANGE': 'exchange', 'BARN': 'car_barn', 'PARLOUR': 'parlour'}
    for run in runs:
        logs = glob.glob(os.path.join(run, '**', 'client.stdout.log'), recursive=True)
        for lg in logs:
            with open(lg, encoding='utf-8', errors='replace') as fh:
                lines_ = fh.readlines()
            for ln in lines_:
                m = LINE.search(ln)
                if m:
                    sysname, ev, rest = m.groups()
                    f = dict(PAIR.findall(rest))
                    if ev == 'RIDE_S':
                        samples.append(dict(f, run=lg))
                    elif ev in ('LAUNCH', 'ARRIVE'):
                        events.append(dict(f, ev=ev, run=lg))
                    else:
                        events.append({'sys': sysname, 'ev': ev, 'run': lg})
                if 'script runtime error' in ln.lower() or 'unresolved' in ln.lower():
                    errors.append(ln.strip()[:240])
        for res in glob.glob(os.path.join(run, '**', 'result.local.json'), recursive=True):
            try:
                errors += [e for e in (json.load(open(res, encoding='utf-8-sig')).get('EngineErrors') or [])]
            except Exception:
                pass
    launches = [e for e in events if e.get('ev') == 'LAUNCH']
    bad = []
    for e in launches:
        key = (e['run'], e['ride'])
        dest = zone_by_hatch.get(e['to'])
        rs = [s for s in samples if (s['run'], s['ride']) == key]
        off = [s for s in rs if s.get('zone') != dest]
        rides[key] = {'from': e['from'], 'to': e['to'], 'dir': e['dir'], 'segs': int(e['segs']), 'price': int(e['price']), 'samples': len(rs),
                      'samples_in_dest_zone': len(rs) - len(off), 'engine_volume': sorted({s.get('volume') for s in rs})}
        if off or not rs:
            bad.append({'ride': e['ride'], 'to': e['to'], 'off': len(off), 'samples': len(rs)})
    counts = {}
    for e in events:
        k = '%s %s' % (e.get('sys', 'T1'), e['ev'])
        counts[k] = counts.get(k, 0) + 1
    out = {'rides': len(rides), 'ride_samples': len(samples), 'rides_left_zone': bad, 'events': counts, 'script_errors': len(errors),
           'error_lines': errors[:20], 'per_ride': [dict(v, run=k[0], ride=k[1]) for k, v in rides.items()]}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('plans'); p.add_argument('src'); p.add_argument('out')
    p = sub.add_parser('report'); p.add_argument('runs', nargs='+'); p.add_argument('--json')
    a = ap.parse_args(argv)
    if a.cmd == 'plans':
        os.makedirs(a.out, exist_ok=True)
        for pl in all_plans(a.src):
            path = os.path.join(a.out, pl['name'] + '.json')
            json.dump(pl, open(path, 'w'), indent=1)
            print('%s: %d steps' % (path, len(pl['steps'])))
        return 0
    r = report(a.runs)
    if a.json:
        json.dump(r, open(a.json, 'w'), indent=1)
    print(json.dumps({k: v for k, v in r.items() if k != 'per_ride'}, indent=1))
    return 1 if r['rides_left_zone'] or r['script_errors'] else 0


if __name__ == '__main__':
    sys.exit(main())
