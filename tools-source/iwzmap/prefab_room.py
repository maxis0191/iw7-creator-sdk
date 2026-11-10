"""Prefab Room: a small generated map that holds one room lifted out of a shipped map (a worldkit prefab).

A flat lot, the placed prefab on it (surfaces with their shipped materials, props as static models, lights,
collision), player starts, and nothing else: the least the game needs to load the map and spawn a player. It is the
proof map of prefab placement and a template for dressing a custom map with studio-made rooms.

usage: python -I prefab_room.py <template dump dir (cp_zmb)> <placed prefab dir> <output source dir>
           [--colmap <shipped collision .hkx>]   default: <template dump>/maps/cp/cp_zmb.d3dbsp.colmap.hkx
           [--collision shipped|render|none]     where the prefab's collision comes from (default shipped)
           [--lot-margin 384] [--lot-material w/concrete_floor_polished_01] [--lot-drop 1]
           [--lighting flat|template]            flat: lighting.txt with one ambient (any place in the world);
                                                 template: no lighting.txt, the template's own light grid stays
                                                 (only right when the prefab sits at its shipped coordinates)
           [--ambient R G B UP] [--no-lights] [--no-props] [--no-surfaces] [--map cp_pfr]

Writes world.bin, colmap.hkx, navgraph.bin, ents.txt, smodels.txt, lights.txt, lighting.txt, layout.json,
<map>.gsc (level script), <map>.arena and prefab_report.json (what went in, in numbers).
"""
import argparse, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import mapgen, hkcm_write, prefab_place as PP  # noqa: E402

LOT_TAG = 382                      # collision surface tag the generated maps use for plain solid floor
LOT_LM = (0.9408, 0.4061)          # a lit texel of the template lightmap (the generator's usual borrowed texel)

LEVEL_SCRIPT = '''// %(map)s "Prefab Room": a room of a shipped map placed in a generated map (prefab_room.py). No rounds, no zones:
// the map only has to load and spawn a player.
main()
{
    level.iwz_custom_map = 1;
    scripts\\mp\\mp_agent::init_agent( "mp/default_agent_definition.csv" );
    scripts\\mp\\agents\\zombie\\zombie_agent::registerscriptedagent();
    level.coop_weapontable = "cp/cp_weapontable.csv";
    level.disable_zombie_exo_abilities = 1;
    scripts\\cp\\maps\\cp_zmb\\cp_zmb_player_character_setup::init_player_characters();
}
'''

ARENA = '''{
	map			"%(map)s"
	longname	"PREFAB ROOM"
	gametype	"zombie Aliens escape"
	defaultgametype "zombie"
	description "A room of a shipped map placed in a generated map."
	mappack		"0"
}
'''


def build(tpl, prefab_dir, out, colmap=None, collision='shipped', lot_margin=384.0, lot_material='w/concrete_floor_polished_01',
          lot_drop=1.0, lighting='flat', ambient=(0.8, 0.8, 0.9, 0.6), lights=True, props=True, surfaces=True, mapname='cp_pfr',
          log=print):
    pre = PP.load(prefab_dir)
    os.makedirs(out, exist_ok=True)
    box = PP.placed_box(pre)
    starts = []
    for e in pre['ents']:
        kv = dict((k, v) for k, v in e['kv'])
        if kv.get('822') == 'default_player_start' or kv.get('targetname') == 'default_player_start':
            starts.append((tuple(e['origin']), kv.get('65') or kv.get('angles') or '0 0 0'))
    # collision first: the lot sits just under the lowest floor the starts stand on
    if collision == 'none':
        col, tags, col_from = [], [], 'none'
    else:
        col, tags, col_from = PP.prefab_collision(prefab_dir, pre, colmap if collision == 'shipped' else None, LOT_TAG)
    if starts:
        floor_z = min(s[0][2] for s in starts)
    else:
        floor_z = box[2]
    lot_z = floor_z - lot_drop
    lx0, ly0, lx1, ly1 = box[0] - lot_margin, box[1] - lot_margin, box[3] + lot_margin, box[4] + lot_margin
    if not starts:
        starts = [(((box[0] + box[3]) / 2 + dx, (box[1] + box[4]) / 2 + dy, floor_z), '0 0 0') for dx, dy in ((-48, -48), (48, -48), (-48, 48), (48, 48))]

    # ---- render world: the lot, then the prefab's surfaces in their shipped order
    w = PP.WorldWriter()
    w.add_quad(lot_material, [(lx0, ly0, lot_z), (lx1, ly0, lot_z), (lx1, ly1, lot_z), (lx0, ly1, lot_z)], (0.0, 0.0, 1.0), lm=LOT_LM)
    st = PP.add_surfaces(w, prefab_dir, pre) if surfaces else {'prefab_surfaces': len(pre['surfaces']), 'surfaces_written': 0,
                                                                 'triangles': 0, 'vertices': 0, 'materials': 0}
    data = w.tobytes()
    with open(os.path.join(out, 'world.bin'), 'wb') as f:
        f.write(data)

    # ---- collision: lot (two triangles per 512-unit tile, so no section spans the whole map) + the prefab's
    lot_tris = []
    step = 512.0
    x = lx0
    while x < lx1 - 1e-6:
        y = ly0
        xe = min(x + step, lx1)
        while y < ly1 - 1e-6:
            ye = min(y + step, ly1)
            lot_tris += [((x, y, lot_z), (xe, y, lot_z), (xe, ye, lot_z)), ((x, y, lot_z), (xe, ye, lot_z), (x, ye, lot_z))]
            y = ye
        x = xe
    # an unseen wall round the lot: nobody walks off the map
    wall_top = max(box[5], lot_z + 256.0) + 128.0
    ring = [(lx0, ly0), (lx1, ly0), (lx1, ly1), (lx0, ly1)]
    for k in range(4):
        (ax, ay), (bx, by) = ring[k], ring[(k + 1) % 4]
        n = int(max(abs(bx - ax), abs(by - ay)) // step) + 1
        for q in range(n):
            p0 = (ax + (bx - ax) * q / n, ay + (by - ay) * q / n); p1 = (ax + (bx - ax) * (q + 1) / n, ay + (by - ay) * (q + 1) / n)
            # counter-clockwise ring: these face inwards
            lot_tris += [((p0[0], p0[1], lot_z), (p1[0], p1[1], lot_z), (p1[0], p1[1], wall_top)),
                         ((p0[0], p0[1], lot_z), (p1[0], p1[1], wall_top), (p0[0], p0[1], wall_top))]
    all_tris = lot_tris + list(col)
    all_tags = [LOT_TAG] * len(lot_tris) + list(tags)
    hk = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in all_tris]
    blob, info = hkcm_write.encode(hk, colmap or os.path.join(tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.colmap.hkx'), tag=LOT_TAG,
                                   max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')), tags=all_tags)
    with open(os.path.join(out, 'colmap.hkx'), 'wb') as f:
        f.write(blob)

    # ---- navigation: walkable cells from the collision, kept to what a walker reaches from the starts
    cell = 32
    grid = PP.TriGrid(all_tris)
    cells = PP.nav_cells(all_tris, (lx0 + 16, ly0 + 16, lx1 - 16, ly1 - 16), cell, min_z=lot_z - 0.5, grid=grid)
    seeds = [(int(s[0][0] // cell), int(s[0][1] // cell)) for s in starts]
    link = PP.nav_link(grid, cells, cell)
    reach = PP.largest_island(cells, seeds, link=link)
    nav, nareas = mapgen.nav_graph(reach, cell, link)
    with open(os.path.join(out, 'navgraph.bin'), 'wb') as f:
        f.write(nav)

    # ---- entities: the template's worldspawn, the starts, an intermission camera
    ws = mapgen.stock_worldspawn(os.path.join(tpl, 'maps', 'cp', 'cp_zmb.d3dbsp.ents'))
    ents = []
    for o, ang in starts:
        ents.append([('157', 'script_struct'), ('822', 'default_player_start'), ('543', '%g %g %g' % tuple(round(c, 3) for c in o)), ('65', ang)])
    cx, cy = (box[0] + box[3]) / 2, (box[1] + box[4]) / 2
    ents.append([('157', 'mp_global_intermission'), ('543', '%g %g %g' % (cx, cy, floor_z + 200)), ('65', '20 0 0')])
    with open(os.path.join(out, 'ents.txt'), 'w', newline='\n') as f:
        f.write(mapgen.ents_text(ws, ents))

    # ---- props, lights, lighting
    sm = PP.smodel_lines(pre) if props else []
    with open(os.path.join(out, 'smodels.txt'), 'w', newline='\n') as f:
        f.write('\n'.join(sm) + ('\n' if sm else ''))
    ll, skipped = PP.light_lines(pre) if lights else ([], [])
    if ll:
        with open(os.path.join(out, 'lights.txt'), 'w', newline='\n') as f:
            f.write('\n'.join(ll) + '\n')
    elif os.path.exists(os.path.join(out, 'lights.txt')):
        os.remove(os.path.join(out, 'lights.txt'))
    lp = os.path.join(out, 'lighting.txt')
    if lighting == 'flat':
        r, g, b, up = ambient
        rows = ['ambient %.4f %.4f %.4f %.2f' % (r * 0.4, g * 0.4, b * 0.4, up),
                'room %g %g %g %g %g %g %.4f %.4f %.4f %.2f' % (box[0] - 256, box[1] - 256, box[2] - 256, box[3] + 256, box[4] + 256,
                                                             box[5] + 256, r, g, b, up)]
        with open(lp, 'w', newline='\n') as f:
            f.write('\n'.join(rows) + '\n')
    elif os.path.exists(lp):
        os.remove(lp)

    layout = {'map': mapname, 'starts': [list(s[0]) for s in starts], 'zones': {}, 'spawners': [], 'stairs': [],
              'prefab': {'name': pre['name'], 'at': pre['origin'], 'yaw': pre.get('yaw', 0.0), 'box': list(box)},
              'lot': [lx0, ly0, lx1, ly1, lot_z]}
    with open(os.path.join(out, 'layout.json'), 'w') as f:
        json.dump(layout, f, indent=1)
    with open(os.path.join(out, mapname + '.gsc'), 'w', newline='\n') as f:
        f.write(LEVEL_SCRIPT % {'map': mapname})
    with open(os.path.join(out, mapname + '.arena'), 'w', newline='\n') as f:
        f.write(ARENA % {'map': mapname})

    parsed = PP.read_world(data)
    report = {'schema': 'iw7.prefab-room/1', 'map': mapname, 'prefab': pre['name'], 'source_map': pre['source'].get('map'),
              'at': pre['origin'], 'yaw': pre.get('yaw', 0.0), 'box': list(box),
              'surfaces': {'prefab': st['prefab_surfaces'], 'written': st['surfaces_written'], 'triangles': st['triangles'],
                           'prefab_triangles': pre['counts']['triangles'], 'vertices': st['vertices'], 'materials': st['materials'],
                           'layered': st.get('layered_surfaces', 0), 'not_lightmapped': st.get('unlightmapped_surfaces', 0),
                           'with_shipped_tangents': st.get('with_tangents', 0)},
              'world': {'surfaces': len(parsed['surfaces']), 'vertices': parsed['vertices'], 'triangles': parsed['indices'] // 3,
                        'materials': len(parsed['materials']), 'bytes': len(data)},
              'props': {'lines': len(sm), 'models': len({ln.split()[0] for ln in sm}), 'noshadow': sum(1 for ln in sm if ' noshadow' in ln)},
              'lights': {'prefab': len(pre['lights']), 'lines': len(ll), 'spots': sum(1 for x in ll if x.startswith('spot')),
                         'skipped_types': skipped},
              'collision': {'from': col_from, 'prefab_triangles': len(col), 'lot_triangles': len(lot_tris), 'tags': len(set(tags)),
                            'havok': info, 'bytes': len(blob)},
              'nav': {'cells': len(cells), 'reachable': len(reach), 'areas': nareas, 'bytes': len(nav)},
              'starts': len(starts), 'lighting': lighting, 'ambient': list(ambient) if lighting == 'flat' else None,
              'entities_not_placed': len(pre['ents']) - sum(1 for e in pre['ents'] if dict((k, v) for k, v in e['kv']).get('822') == 'default_player_start')}
    with open(os.path.join(out, 'prefab_report.json'), 'w') as f:
        json.dump(report, f, indent=1)
    log('prefab room %s: surfaces %d of %d (%d triangles of %d, %d materials), props %d (%d models), lights %d of %d, '
        'collision %d triangles from %s + lot %d, nav %d cells (%d reachable), starts %d' % (
            mapname, st['surfaces_written'], st['prefab_surfaces'], st['triangles'], pre['counts']['triangles'], st['materials'],
            len(sm), report['props']['models'], len(ll), len(pre['lights']), len(col), col_from, len(lot_tris), len(cells),
            len(reach), len(starts)))
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description='a generated map holding one placed prefab')
    ap.add_argument('template'); ap.add_argument('prefab'); ap.add_argument('out')
    ap.add_argument('--colmap')
    ap.add_argument('--collision', choices=('shipped', 'render', 'none'), default='shipped')
    ap.add_argument('--lot-margin', type=float, default=384.0)
    ap.add_argument('--lot-material', default='w/concrete_floor_polished_01')
    ap.add_argument('--lot-drop', type=float, default=1.0)
    ap.add_argument('--lighting', choices=('flat', 'template'), default='flat')
    ap.add_argument('--ambient', type=float, nargs=4, default=(0.8, 0.8, 0.9, 0.6))
    ap.add_argument('--no-lights', action='store_true'); ap.add_argument('--no-props', action='store_true')
    ap.add_argument('--no-surfaces', action='store_true')
    ap.add_argument('--map', default='cp_pfr')
    a = ap.parse_args(argv)
    colmap = a.colmap or os.path.join(a.template, 'maps', 'cp', 'cp_zmb.d3dbsp.colmap.hkx')
    try:
        build(a.template, a.prefab, a.out, colmap, a.collision, a.lot_margin, a.lot_material, a.lot_drop, a.lighting,
              tuple(a.ambient), not a.no_lights, not a.no_props, not a.no_surfaces, a.map)
    except (PP.PrefabError, PP.iw7_world.WorldError, OSError) as e:
        print('prefab_room: %s' % e, file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
