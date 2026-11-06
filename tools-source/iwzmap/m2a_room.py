"""M2a: one original test room, to prove a generated world loads (render, collision, nav, spawn)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mapgen, hkcm_write

tpl, out = sys.argv[1], sys.argv[2]   # template dump dir (cp_zmb), output source dir
os.makedirs(out, exist_ok=True)
X0, Y0, Z0 = 0, 4800, 0
W, D, H = 1024, 1024, 256
LM_FLOOR = (0.9408, 0.4061)          # borrowed from a lit stock floor near the template spawn
mats = {'floor': 'w/concrete_floor_polished_01', 'wall': 'w/concrete_wall_panel_01', 'ceiling': 'w/ceiling_tile_01'}
m = mapgen.Mesh()
mapgen.box_faces(m, (X0, Y0, Z0), (X0 + W, Y0 + D, Z0 + H), mats, LM_FLOOR, inward=True)
pillar = {'floor': 'w/metal_bare_diamondplate_01', 'wall': 'w/frag_brick_painted_white_01', 'ceiling': 'w/metal_bare_diamondplate_01'}
mapgen.box_faces(m, (X0 + 448, Y0 + 448, Z0), (X0 + 576, Y0 + 576, Z0 + H), pillar, LM_FLOOR, skip=('top', 'bottom'))
nv, ni, ns, wb = mapgen.write_world(m, os.path.join(out, 'world.bin'))
col = [tuple(tuple(c * mapgen.HAVOK_SCALE for c in p) for p in t) for t in m.col]
blob, info = hkcm_write.encode(col, os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.colmap.hkx'), tag=382, max_tris=int(os.environ.get('IWZ_MAX_TRIS', '127')))
open(os.path.join(out, 'colmap.hkx'), 'wb').write(blob)
cell = 32
cells = {}
for i in range((X0 + 16) // cell, (X0 + W - 16) // cell):
    for j in range((Y0 + 16) // cell, (Y0 + D - 16) // cell):
        x, y = (i + 0.5) * cell, (j + 0.5) * cell
        if X0 + 448 - 16 < x < X0 + 576 + 16 and Y0 + 448 - 16 < y < Y0 + 576 + 16: continue
        cells[(i, j)] = Z0
nav, nareas = mapgen.nav_graph(cells, cell)
open(os.path.join(out, 'navgraph.bin'), 'wb').write(nav)
ws = mapgen.stock_worldspawn(os.path.join(tpl, 'maps/cp/cp_zmb.d3dbsp.ents'))
ents = []
for k, (x, y) in enumerate([(200, 200), (824, 200), (200, 824), (824, 824)]):
    ents.append([('157', 'script_struct'), ('822', 'default_player_start'), ('543', '%d %d %d' % (X0 + x, Y0 + y, Z0)), ('65', '0 45 0')])
ents.append([('157', 'mp_global_intermission'), ('543', '512 5312 160'), ('65', '20 0 0')])
open(os.path.join(out, 'ents.txt'), 'w', newline='\n').write(mapgen.ents_text(ws, ents))
print('verts', nv, 'indices', ni, 'surfaces', ns, 'bounds', wb, 'collision', info, 'nav areas', nareas, 'nav bytes', len(nav))
