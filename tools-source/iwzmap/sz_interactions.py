"""Station Zero interaction entities (stock CP interaction system: targetname "interaction", type in
script_noteworthy) and the template scriptables relocated into the map (perk machines, upgrade station)."""

K = {'classname': '157', 'targetname': '822', 'origin': '543', 'angles': '65', 'noteworthy': '638', 'target': '820',
     'area': '60666', 'parameters': '61049', 'model': '497', 'groupname': '502', 'radius': '599'}


def struct(ents, kind, origin, yaw=0, **kw):
    e = [(K['classname'], 'script_struct'), (K['targetname'], 'interaction'), (K['noteworthy'], kind),
         (K['origin'], '%g %g %g' % origin), (K['angles'], '0 %g 0' % yaw)]
    e += [(K[k], str(v)) for k, v in kw.items()]
    ents.append(e)


def model(ents, name, origin, yaw, xmodel, pitch=0):
    ents.append([(K['classname'], 'script_model'), (K['targetname'], name), (K['model'], xmodel),
                 (K['origin'], '%g %g %g' % origin), (K['angles'], '%g %g 0' % (pitch, yaw))])


# (perk interaction, template scriptable targetname, origin, yaw)
PERKS = [
    ('perk_machine_revive', 'perk_machine_up_n_atoms_sign', (1000, 4850, 0), 180),
    ('perk_machine_tough', 'perk_machine_tuff_nuff_sign', (2270, 5010, 0), 180),
    ('perk_machine_run', 'perk_machine_racin_stripes_sign', (1350, 6870, 0), 270),
    ('perk_machine_rat_a_tat', 'perk_machine_bang_bangs_sign', (2490, 6870, 0), 270),
]


def add(ents):
    """Returns the scriptables.txt lines (relocations of template scriptables)."""
    relocations = []
    # doors: a struct on each side; the area is the zone the purchase opens
    for x, yaw in ((984, 90), (1064, 270)):
        struct(ents, 'debris_750', (x, 5312, 24), yaw, area='generator', target='pf7_auto211')
    # door visuals: the two stock barrier scriptables named pf7_auto211, moved into the doorway
    relocations.append('pf7_auto211 0 1024 5272 0 90')
    relocations.append('pf7_auto211 1 1024 5352 0 90')
    for y, yaw in ((5656, 0), (5736, 180)):
        struct(ents, 'debris_1000', (1920, y, 24), yaw, area='platform', target='pf7_auto213')
    relocations.append('pf7_auto213 0 1920 5696 0 0')
    # power: the switch powers every zone
    struct(ents, 'generator', (2280, 5312, 54), 270, parameters='arrival,generator,platform', target='iwz_power_switch')
    model(ents, 'iwz_power_switch', (2296, 5312, 54), 270, 'icbm_electricpanel_switch_02', pitch=75)
    # wall buys
    struct(ents, 'iw7_revolver_zm', (16, 5312, 64), 90, groupname='wall_buy', model='weapon_kb_revolver_wm', radius=256)
    struct(ents, 'iw7_ump45_zml', (1552, 5100, 64), 90, groupname='wall_buy', model='weapon_kb_ump45_wm', radius=256)
    struct(ents, 'iw7_m4_zm', (2544, 6528, 64), 270, groupname='wall_buy', model='weapon_kb_m4_wm', radius=256)
    # perk machines (need power): interaction struct + the stock machine scriptable moved next to it
    for kind, scriptable, origin, yaw in PERKS:
        struct(ents, kind, origin, yaw, parameters='requires_power')
        relocations.append('%s 0 %g %g %g %g' % (scriptable, origin[0], origin[1], origin[2], yaw))
    # Pack-a-Punch
    struct(ents, 'weapon_upgrade', (1920, 6870, 0), 270, parameters='requires_power', target='iwz_pap_spot')
    relocations.append('pap_machine 0 1920 6880 0 270')
    ents.append([(K['classname'], 'script_struct'), (K['targetname'], 'iwz_pap_spot'), (K['origin'], '1920 6890 14'),
                 (K['angles'], '0 270 0'), (K['model'], 'weapon_e_ak47_rare_wm')])
    return relocations
