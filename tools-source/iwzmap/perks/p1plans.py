"""Headless test plans of Station Zero's perks (package P1): every number of 06-PERKS.md read as data.

usage: python -I -B p1plans.py <generated source dir (layout.json)> <out dir> [--given]

--given: the five perks with no stock machine are given by script instead of bought (a build that has no machines for
them, such as the W1 blockout with the module loaded as loose files). Without it, every perk is bought at its machine.

Plans (all headless, gamelab library "szperks" of iw7-paris-server, map cp_iwz):
  p1_buy    the ten machines: prices, power, the limit of six (the seventh refused, nothing paid), a perk sold back,
            the Validated Ticket (one free perk, the limit still holds), Up 'N Atoms at 500 alone
  p1_effect Baker's Dozens (the 13th hit tripled, two more zombies, points), Sour Grudges (mark, earned, forgiven,
            wonder weapon and expiry and the Night Inspector refused), Bon Voyages (half prices, arrival, own trap)
  p1_edge   Double Takes (threshold, lure, cooldown, the Night Inspector passes), a second player (own limit), down and
            revive (every perk lost, bought again), rounds (perks and counters survive)
  p1_hurt   what a zombie's hit takes at rounds 1 to 30 (Double Takes' threshold decision)
"""
import json, math, os, sys

RIFLE = 'iw7_m4_zm'
WW = 'iw7_facemelter_zm'
NEW = ['perk_machine_deadeye', 'perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge', 'perk_machine_double']
PRICE = {'perk_machine_revive': 1500, 'perk_machine_tough': 2500, 'perk_machine_run': 2000, 'perk_machine_rat_a_tat': 2000,
         'perk_machine_flash': 3000, 'perk_machine_deadeye': 1500, 'perk_machine_bakers': 3000, 'perk_machine_voyage': 2000,
         'perk_machine_grudge': 2500, 'perk_machine_double': 3000}


def call(fn, *args, s=1):
    return {'do': 'call', 'fn': fn, 'args': list(args), 's': s}


def exp(that, op, v, why):
    return {'do': 'expect', 'that': that, op: v, 'why': why}


def plan(name, about, steps):
    return {'schema': 'iw7.gamelab-plan/1', 'name': name, 'map': 'cp_iwz', 'about': about, 'libraries': ['szperks'], 'steps': steps}


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    src, out = argv[0], argv[1]
    given = '--given' in argv
    L = json.load(open(os.path.join(src, 'layout.json')))
    at = {}
    yaw_of = {}
    for i in L['interactions']:
        if i['kind'].startswith('perk_machine_') or i['kind'] == 'generator':
            at[i['kind']] = [round(v, 1) for v in i['origin']]
            yaw_of[i['kind']] = i.get('yaw', 0)
    zp = L['zone_points']
    trap = next(i for i in L['interactions'] if i['kind'] == 'trap_third_rail')
    box = L['trap_third_rail']['box']
    pit = [(box[0] + box[3]) / 2 + 600, (box[1] + box[4]) / 2, box[2] + 4]
    os.makedirs(out, exist_ok=True)

    def frame(kind):
        # a frame of the machine from 140 units in front of it, eye on the machine: what a player walking up sees
        o, y = at[kind], math.radians(yaw_of.get(kind, 0))
        p = [round(o[0] + 140 * math.cos(y), 1), round(o[1] + 140 * math.sin(y), 1), o[2]]
        return [{'do': 'tp', 'at': p, 'snap': True}, {'do': 'lookat', 'at': [o[0], o[1], o[2] + 48]}, {'do': 'wait', 's': 1},
                {'do': 'capture', 'name': 'm_' + kind[13:], 'pause': 0.5}, {'do': 'ui', 'name': 'm_' + kind[13:]}]

    def use(name, kind, s=4):
        return {'do': 'use', 'name': name, 'kind': kind, 'near': at[kind], 's': s}

    def buy(name, kind):
        return [use(name, kind)] if (kind not in NEW or not given) else [call('szp_give', kind)]

    # ---- p1_buy -----------------------------------------------------------------------------------------------
    st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 100000},
          call('szp_setup', 'b_setup'), call('szp_assets', 'assets'), call('szp_state', 'b0'),
          use('revive', 'perk_machine_revive'), use('tough_nopower', 'perk_machine_tough', 3),
          use('power', 'generator', 6)]
    for k in ['perk_machine_deadeye', 'perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge']:
        st += buy('b_' + k[13:], k)
    st += [call('szp_state', 'b5'), use('tough', 'perk_machine_tough'), call('szp_state', 'b6'),
           use('run_seventh', 'perk_machine_run'), call('szp_try', 'try_flash', 'perk_machine_flash'),
           call('szp_try', 'try_double', 'perk_machine_double'), call('szp_state', 'b6b'),
           use('tough_return', 'perk_machine_tough'), call('szp_state', 'b5r'),
           call('szp_ticket', 'ticket'), use('run_ticket', 'perk_machine_run'), call('szp_state', 'b6t'),
           use('flash_full', 'perk_machine_flash'), call('szp_state', 'b_end')]
    if not given:
        st += [use('double_full', 'perk_machine_double')]
    ex = [exp('probe:b_setup.module', 'eq', 1, 'the perk module runs in the map'),
          exp('use:revive.spent', 'eq', 500, "Up 'N Atoms costs 500 to a player alone, before the power (its own generator)"),
          exp('use:revive.perks1', 'eq', 1, "Up 'N Atoms is given"),
          exp('use:tough_nopower.spent', 'eq', 0, "Tuff 'Nuff refuses before the power"),
          exp('use:tough_nopower.perks1', 'eq', 1, "Tuff 'Nuff gives nothing before the power"),
          exp('probe:b5.count', 'eq', 5, 'five perks'),
          exp('use:tough.spent', 'eq', 2500, "Tuff 'Nuff at its stock price"),
          exp('use:tough.perks1', 'eq', 6, 'a sixth perk: the limit on this map is six'),
          exp('use:run_seventh.spent', 'eq', 0, 'the seventh perk is refused and nothing is paid'),
          exp('use:run_seventh.perks1', 'eq', 6, 'the seventh perk is refused'),
          exp('probe:try_flash.ok', 'eq', 0, 'the purchase test refuses a seventh perk'),
          exp('probe:b6b.count', 'eq', 6, 'still six'),
          exp('use:tough_return.spent', 'eq', 0, 'a perk used again is sold back for nothing (stock rule)'),
          exp('use:tough_return.perks1', 'eq', 5, 'the perk is gone'),
          exp('probe:ticket.ticket', 'eq', 1, 'the Validated Ticket is held'),
          exp('use:run_ticket.spent', 'eq', 0, 'the ticket makes this perk free'),
          exp('use:run_ticket.perks1', 'eq', 6, "Racin' Stripes given with the ticket"),
          exp('probe:b6t.ticket', 'eq', 0, 'the ticket is used'),
          exp('use:flash_full.spent', 'eq', 0, 'the ticket did not raise the limit: a seventh is refused'),
          exp('use:flash_full.perks1', 'eq', 6, 'still six')]
    if not given:
        ex += [exp('use:b_%s.spent' % k[13:], 'eq', PRICE[k], '%s at %d' % (k, PRICE[k])) for k in ['perk_machine_deadeye', 'perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge']]
        ex += [exp('use:double_full.spent', 'eq', 0, 'Double Takes refused at six'), exp('probe:assets.bodies', 'eq', 4, 'the four authored machines are in the map'),
               exp('probe:assets.deadeye_scriptable', 'eq', 1, 'Deadeye stands in its own cp_disco machine'),
               exp('probe:b_setup.module', 'eq', 1, 'module'),
               ] + [exp('probe:assets.snd%d' % i, 'eq', 1, 'stock perk sound alias %d is in the map bank' % i) for i in (0, 1, 2, 4, 6, 7, 8, 9)] + [
               exp('probe:assets.tuff_jingle_ms', 'gt', 10000, 'the Tuff Nuff jingle has its stock length'),
               exp('probe:assets.bit_bakers', 'eq', 18, "Baker's Dozens has its HUD bit row in the zone's table"),
               exp('probe:assets.bit_double_cd', 'eq', 22, "Double Takes' recharging icon row")]
    json.dump(plan('p1_buy', 'P1: the ten machines, prices, power, limit of six, sold back, Validated Ticket (headless).', st + ex),
              open(os.path.join(out, 'p1_buy.json'), 'w'), indent=1)

    # ---- p1_effect --------------------------------------------------------------------------------------------
    c = zp['converter_hall']
    near = [c[0] + 160, c[1], c[2]]
    st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 100000},
          {'do': 'tp', 'at': c, 'yaw': 0, 'snap': True}, call('szp_setup', 'e_setup'),
          call('szp_give', 'perk_machine_bakers'), call('szp_give', 'perk_machine_grudge'), call('szp_give', 'perk_machine_voyage'),
          {'do': 'give', 'weapon': RIFLE},
          # Baker's Dozens
          {'do': 'spawn', 'tag': 'bk', 'at': near, 'count': 3, 'place': True}, call('szp_hold', 'bk', 1),
          call('szp_hits', 'bk12', 'bk', 12, 10, RIFLE, 1, s=3), call('szp_state', 'bk_at12'),
          call('szp_line_hit', 'bkline', 'bk', 10, RIFLE), {'do': 'wait', 's': 0.5}, call('szp_state', 'bk_punch'),
          call('szp_ww_add', 'facemelter'), call('szp_hits', 'bkww', 'bk', 13, 10, WW, 1, s=3), call('szp_state', 'bk_ww'),
          call('szp_hits', 'bk13', 'bk', 13, 10, RIFLE, 1, s=3), call('szp_state', 'bk_second'),
          {'do': 'kill', 'tag': 'bk'},
          # Sour Grudges
          {'do': 'spawn', 'tag': 'sg', 'at': near, 'count': 1, 'place': True}, call('szp_hold', 'sg', 1),
          {'do': 'spawn', 'tag': 'sg2', 'at': near, 'count': 1, 'place': True}, call('szp_hold', 'sg2', 1),
          call('szp_zombie_hit', 'sg_h1', 'sg', 20), call('szp_state', 'sg_marked'),
          call('szp_kill_with', 'sg_k', 'sg', RIFLE), call('szp_state', 'sg_earned'), call('szp_heal', 'sg_heal1'),
          call('szp_zombie_hit', 'sg_h2', 'sg2', 30), call('szp_state', 'sg_forgiven'), {'do': 'wait', 's': 1},
          call('szp_zombie_hit', 'sg_h3', 'sg2', 25), call('szp_heal', 'sg_heal2'),
          call('szp_kill_with', 'sg_ww', 'sg2', WW), call('szp_state', 'sg_after_ww'),
          {'do': 'spawn', 'tag': 'sg3', 'at': near, 'count': 1, 'place': True}, call('szp_hold', 'sg3', 1),
          call('szp_zombie_hit', 'sg_h4', 'sg3', 20), {'do': 'wait', 's': 7}, call('szp_kill_with', 'sg_late', 'sg3', RIFLE),
          call('szp_state', 'sg_after_late'), call('szp_heal', 'sg_heal3'),
          {'do': 'spawn', 'tag': 'sg4', 'at': near, 'count': 1, 'place': True}, call('szp_hold', 'sg4', 1), call('szp_retype', 'sg4', 'zombie_inspector'),
          call('szp_zombie_hit', 'sg_h5', 'sg4', 20), call('szp_state', 'sg_inspector'), call('szp_retype', 'sg4', ''),
          {'do': 'kill'}, call('szp_heal', 'sg_heal4'),
          # Bon Voyages
          call('szp_prices', 'bv_prices'), call('szp_arrive', 'bv_arrive'), use('power', 'generator', 6),
          {'do': 'tp', 'at': [round(v, 1) for v in trap['origin']]},
          {'do': 'use', 'name': 'bv_trap', 'ent': 'iwz_trap_third_rail_use', 'near': [round(v, 1) for v in trap['origin']], 's': 2},
          {'do': 'tp', 'at': pit}, {'do': 'wait', 's': 3}, call('szp_state', 'bv_in_pit'),
          # the stock comparison for the balance table: a series of hits plain, then with Bang Bangs
          {'do': 'tp', 'at': c, 'yaw': 0, 'snap': True}, call('szp_take', 'perk_machine_bakers'),
          {'do': 'spawn', 'tag': 'bb', 'at': near, 'count': 1, 'place': True}, call('szp_hold', 'bb', 1),
          call('szp_hits', 'plain12', 'bb', 12, 10, RIFLE, 1, s=2), call('szp_give', 'perk_machine_rat_a_tat'),
          call('szp_hits', 'bang12', 'bb', 12, 10, RIFLE, 1, s=2)]
    ex = [exp('probe:bk_at12.bakers_count', 'eq', 12, 'twelve hits counted'),
          exp('probe:bk_punch.bakers_punches', 'eq', 1, 'the thirteenth hit is punched'),
          exp('probe:bkline.ratio', 'near', 3, 'the punched hit deals triple damage (tol 0.05)'),
          exp('probe:bk_punch.bakers_last_extra', 'eq', 2, 'the punch passes through two more zombies'),
          exp('probe:bkline.lost1', 'gt', 0, 'the second zombie on the line is hit'),
          exp('probe:bkline.lost2', 'gt', 0, 'the third zombie on the line is hit'),
          exp('probe:bkline.lost1', 'eq', '@probe:bkline.lost0', 'the zombies behind take the punched damage, not more'),
          exp('probe:bk_punch.bakers_last_bonus', 'gt', 0, 'the punched hit pays its points again'),
          exp('probe:bk_ww.bakers_count', 'eq', 0, 'wonder-weapon hits neither count nor punch'),
          exp('probe:bk_ww.bakers_punches', 'eq', 1, 'no punch from a wonder weapon'),
          exp('probe:bk_second.bakers_punches', 'eq', 2, 'a second dozen punches again'),
          exp('probe:sg_h1.taken', 'eq', 20, 'the first hit lands in full'),
          exp('probe:sg_marked.grudge_mark', 'ge', 0, 'the zombie that hit is marked'),
          exp('probe:sg_earned.grudge_shield', 'eq', 1, 'killing the marked zombie in time earns one forgiven hit'),
          exp('probe:sg_h2.taken', 'eq', 0, 'the next hit does no damage'),
          exp('probe:sg_forgiven.grudge_forgiven', 'eq', 1, 'one hit forgiven'),
          exp('probe:sg_h3.taken', 'eq', 25, 'only one hit is forgiven'),
          exp('probe:sg_after_ww.grudge_earned', 'eq', 1, 'a wonder-weapon kill earns nothing'),
          exp('probe:sg_after_late.grudge_earned', 'eq', 1, 'a kill after the 6 s mark earns nothing'),
          exp('probe:sg_inspector.grudge_mark', 'eq', -1, 'the Night Inspector is never marked'),
          exp('probe:bv_prices.trap', 'eq', 375, 'traps at half price'),
          exp('probe:bv_prices.postage', 'eq', 250, 'postage at half price'),
          exp('probe:bv_prices.own_trap_hurts', 'eq', 0, "the owner's own trap does not hurt them"),
          exp('probe:bv_arrive.until_ms', 'gt', 3500, 'after an arrival: faster for 4 s'),
          exp('probe:bv_arrive.until_ms', 'le', 4000, 'after an arrival: faster for 4 s'),
          exp('use:bv_trap.spent', 'eq', 375, 'the Third Rail costs the owner 375'),
          exp('probe:bv_in_pit.health', 'eq', 100, "the owner's own Third Rail does not hurt them in the pit")]
    json.dump(plan('p1_effect', "P1: Baker's Dozens, Sour Grudges, Bon Voyages read as data (headless).", st + ex),
              open(os.path.join(out, 'p1_effect.json'), 'w'), indent=1)

    # ---- p1_edge ----------------------------------------------------------------------------------------------
    a = zp['exchange']
    far = [a[0] + 250, a[1], a[2]]
    st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 100000},
          {'do': 'tp', 'at': a, 'yaw': 0, 'snap': True}, call('szp_setup', 'g_setup'),
          use('power', 'generator', 6), {'do': 'tp', 'at': a, 'yaw': 0, 'snap': True},
          call('szp_give', 'perk_machine_double'),
          {'do': 'spawn', 'tag': 'dt', 'at': far, 'count': 3, 'place': True}, call('szp_hold', 'dt', 1),
          {'do': 'spawn', 'tag': 'dti', 'at': far, 'count': 1, 'place': True}, call('szp_hold', 'dti', 1), call('szp_retype', 'dti', 'zombie_inspector'),
          # a zombie's hit takes 45 at every round 1 to 30 (p1_hurt): 100 -> 55 (above 35 %), 55 -> 10 (under: trigger)
          call('szp_zombie_hit', 'dt_h1', 'dt', 45), call('szp_state', 'dt_above'), {'do': 'wait', 's': 1},
          call('szp_zombie_hit', 'dt_h2', 'dt', 45), call('szp_step', -300, 0), {'do': 'wait', 's': 4},
          call('szp_state', 'dt_after'), call('szp_retype', 'dti', ''), call('szp_heal', 'dt_heal'), {'do': 'wait', 's': 2},
          call('szp_zombie_hit', 'dt_h3', 'dt', 45), {'do': 'wait', 's': 1}, call('szp_zombie_hit', 'dt_h4', 'dt', 45),
          call('szp_state', 'dt_cooldown'), {'do': 'kill'}, call('szp_heal', 'dt_heal2'),
          # a second player: own perks, own limit
          call('szp_add_player', 'p2')]
    for k in ['perk_machine_tough', 'perk_machine_run', 'perk_machine_flash', 'perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge']:
        st.append(call('szp_p2_give', k))
    st += [call('szp_p2_state', 'p2_six'), call('szp_p2_try', 'p2_try7', 'perk_machine_rat_a_tat'),
           call('szp_try', 'p1_try', 'perk_machine_rat_a_tat'), call('szp_state', 'p1_with_p2'),
           # rounds: perks and counters live on (the stock rounds, the player protected again)
           call('szp_give', 'perk_machine_bakers'), {'do': 'spawn', 'tag': 'rk', 'at': far, 'count': 1, 'place': True}, call('szp_hold', 'rk', 1),
           call('szp_hits', 'rk5', 'rk', 5, 10, RIFLE, 1, s=1.5), {'do': 'kill', 'tag': 'rk'}, call('szp_state', 'r_before'),
           call('szp_protect', 'r_protect'), {'do': 'rounds', 'name': 'r', 'to': 3, 's': 150}, {'do': 'waves', 'on': False}, {'do': 'kill'},
           call('szp_setup', 'r_setup'), call('szp_state', 'r_after'),
           # down and revive: every perk lost (stock rule), bought again
           {'do': 'spawn', 'tag': 'dn', 'at': far, 'count': 1, 'place': True},
           call('szp_down', 'down', 'dn', s=2), call('szp_state', 'down_state'), call('szp_revive', 'revive', s=6),
           {'do': 'kill'}, {'do': 'tp', 'at': a, 'yaw': 0, 'snap': True}, use('rebuy', 'perk_machine_tough'), call('szp_state', 'g_end')]
    ex = [exp('probe:dt_above.double_triggers', 'eq', 0, 'a hit that leaves 55 % does not trigger'),
          exp('probe:dt_after.double_triggers', 'eq', 1, 'falling under 35 % triggers'),
          exp('probe:dt_after.double_lured', 'eq', 3, 'the three zombies within 400 units go for the image; the Night Inspector does not'),
          exp('probe:dt_after.double_nearer_image', 'ge', 2, 'the lured zombies closed on the image'),
          exp('probe:dt_after.double_ready', 'eq', 0, 'recharging'),
          exp('probe:dt_cooldown.double_triggers', 'eq', 1, 'no second trigger inside the 60 s cooldown'),
          exp('probe:dt_cooldown.double_cooldown_ms', 'gt', 50000, 'the cooldown is about 60 s'),
          exp('probe:p2.added', 'eq', 1, 'a second player joined'),
          exp('probe:p2_six.count', 'eq', 6, 'the second player holds six'),
          exp('probe:p2_try7.ok', 'eq', 0, "the second player's seventh is refused"),
          exp('probe:p1_try.ok', 'eq', 1, "the first player's own count decides for them"),
          exp('probe:r_before.bakers_count', 'eq', 5, 'five hits counted'),
          exp('rounds:r.advanced', 'ge', 1, 'rounds advanced'),
          exp('probe:r_after.bakers_count', 'eq', 5, "Baker's counter survives the round change"),
          exp('probe:r_after.count', 'eq', '@probe:r_before.count', 'every perk survives the round change'),
          exp('probe:down.laststand', 'eq', 1, 'the player is down'),
          exp('probe:down.perks1', 'eq', 0, 'every perk is lost on going down'),
          exp('probe:revive.laststand', 'eq', 0, 'revived'),
          exp('use:rebuy.perks1', 'eq', 1, 'a perk can be bought again after the revive'),
          exp('use:rebuy.spent', 'eq', 2500, 'at its price')]
    json.dump(plan('p1_edge', 'P1: Double Takes, a second player, rounds, down and revive (headless).', st + ex),
              open(os.path.join(out, 'p1_edge.json'), 'w'), indent=1)

    # ---- p1_hurt: what a zombie's hit takes, by round ------------------------------------------------------------
    st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'},
          {'do': 'tp', 'at': a, 'yaw': 0, 'snap': True}, call('szp_setup', 'h_setup'), call('szp_protect', 'h_protect')]
    for w in (1, 5, 10, 15, 20, 25, 30):
        st += [call('szp_wave', w), {'do': 'spawn', 'tag': 'h%d' % w, 'at': far, 'count': 1, 'place': True},
               call('szp_hurt_reset', 'hr%d' % w), {'do': 'chase', 'tag': 'h%d' % w, 's': 12, 'reach': 64, 'allow_partial': True},
               {'do': 'wait', 's': 4}, call('szp_hurt', 'hurt%d' % w), {'do': 'kill'}, {'do': 'ignore', 'on': True}]
    ex = [exp('probe:hurt%d.hits' % w, 'ge', 1, 'a zombie at round %d hit the player at least once' % w) for w in (1, 10, 20, 30)]
    json.dump(plan('p1_hurt', "P1: what one zombie's hit takes at rounds 1 to 30 (Double Takes' threshold), headless.", st + ex),
              open(os.path.join(out, 'p1_hurt.json'), 'w'), indent=1)
    # ---- p1_client: a real player buys all ten; the HUD read as data (UI dump) and frames of the machines ----------
    # conditions: client (lab client with the UI dump), waves off, zombies ignore the player, every door open, no
    # damage taken, money set; the perks sold back to make room (limit six) are the stock rule of a second use
    if not given:
        st = [{'do': 'waves', 'on': False}, {'do': 'ignore', 'on': True}, {'do': 'doors'}, {'do': 'money', 'value': 200000},
              call('szp_setup', 'c_setup'), use('power', 'generator', 6), {'do': 'wait', 's': 3}]
        first = ['perk_machine_revive', 'perk_machine_tough', 'perk_machine_run', 'perk_machine_rat_a_tat', 'perk_machine_flash', 'perk_machine_deadeye']
        for k in first:
            st += [use('c_' + k[13:], k, 5)] + frame(k)
        st += [call('szp_state', 'c_six'), {'do': 'ui', 'name': 'six'}]
        for k in ['perk_machine_tough', 'perk_machine_run', 'perk_machine_rat_a_tat', 'perk_machine_flash']:
            st += [use('c_back_' + k[13:], k, 3)]
        for k in ['perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge', 'perk_machine_double']:
            st += [use('c_' + k[13:], k, 5)] + frame(k)
        st += [call('szp_state', 'c_new'), {'do': 'spawn', 'tag': 'ck', 'at': at['perk_machine_double'], 'count': 1, 'place': True},
               call('szp_hold', 'ck', 1), {'do': 'give', 'weapon': RIFLE}, call('szp_hits', 'ck12', 'ck', 12, 10, RIFLE, 1, s=2),
               call('szp_state', 'c_hits'), call('szp_ticket', 'c_ticket'), {'do': 'wait', 's': 1}, {'do': 'ui', 'name': 'new'}, {'do': 'capture', 'name': 'hud_new', 'pause': 0.5}]
        ex = [exp('use:c_%s.perks1' % k[13:], 'eq', n + 1, '%s bought' % k) for n, k in enumerate(first)]
        ex += [exp('use:c_%s.spent' % k[13:], 'eq', PRICE[k] if k != 'perk_machine_revive' else 500, '%s at its price' % k) for k in first]
        ex += [exp('use:c_%s.spent' % k[13:], 'eq', PRICE[k], '%s at its price' % k) for k in ['perk_machine_bakers', 'perk_machine_voyage', 'perk_machine_grudge', 'perk_machine_double']]
        ex += [exp('probe:c_new.count', 'eq', 6, 'six: the four new perks, Up N Atoms, Deadeye'), exp('probe:c_hits.bakers_count', 'eq', 12, 'twelve hits on the counter')]
        json.dump(plan('p1_client', 'P1: a real player buys all ten (six, four sold back, the four new); HUD as data and machine frames (client).', st + ex),
                  open(os.path.join(out, 'p1_client.json'), 'w'), indent=1)
    print('wrote p1 plans to %s (given=%s)' % (out, given))


if __name__ == '__main__':
    main()
