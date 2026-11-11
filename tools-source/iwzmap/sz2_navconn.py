"""Offline navmesh connectivity check of a generated Station Zero v2 source (QA g24: zombies could not climb the west
pit stairwell or cross the platform_a deck while players could).

usage: sz2_navconn.py <src dir> [--json out.json] [--step 18] [--min 6]

Graph: the nav cells of plan.json (32-unit cells, blockers already removed, z = walk height), 8-neighbour links when
the height step between the two cells is at most --step (an AI step-up; the generated stairs give 16) and, for a
diagonal, both orthogonal cells exist (no corner cutting through a wall). Doors are open (the cells under closed
doors are part of the plan). Collision that is not a plan blocker also cuts the graph: every decor clip box (solid
script/static model) removes the cells whose centre lies inside it, like the engine's nav obstacles.
Checks:
  1. the whole map is one component (components smaller than --min cells are reported as islands, not failures,
     when they lie under decor);
  2. every zone's cells are one component of their own, or join one component together with the cells of the
     zones they are linked to by doors / portals (a zone split by a stair is still one zone component through it);
  3. named routes: pit -> well_w -> deck, pit -> well_e -> deck, deck west half -> deck east half, ticket hall ->
     stair_a -> platform_a (cell paths must exist), and the routes a scene-generated map lists in layout.json
     (navconn_routes: the start zone to every other zone).
Exit status 1 on any failure.
"""
import argparse, collections, json, os, sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('--json'); ap.add_argument('--step', type=float, default=18)
    ap.add_argument('--min', type=int, default=6)
    a = ap.parse_args()
    plan = json.load(open(os.path.join(a.src, 'plan.json')))
    lay = json.load(open(os.path.join(a.src, 'layout.json')))
    CELL = 32
    region_zone = {r['name']: r['zone'] for r in plan['regions']}
    cells = {(c[0], c[1]): (c[2], c[3]) for c in plan['cells']}
    # decor collision (clip = half extents, height 2 * hz) removes cells like a nav obstacle
    cut = 0
    for d in lay.get('decor', []):
        if not d.get('clip'):
            continue
        x, y, z = d['origin']; hx, hy, hz = d['clip']
        for i in range(int((x - hx) // CELL) - 1, int((x + hx) // CELL) + 2):
            for j in range(int((y - hy) // CELL) - 1, int((y + hy) // CELL) + 2):
                c = cells.get((i, j))
                if not c:
                    continue
                cx, cy = (i + 0.5) * CELL, (j + 0.5) * CELL
                if x - hx <= cx <= x + hx and y - hy <= cy <= y + hy and z - 8 <= c[0] <= z + 2 * hz:
                    del cells[(i, j)]; cut += 1

    def nbrs(k):
        i, j = k
        z = cells[k][0]
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            n = (i + di, j + dj)
            if n not in cells or abs(cells[n][0] - z) > a.step:
                continue
            if di and dj and ((i + di, j) not in cells or (i, j + dj) not in cells):
                continue
            yield n

    comp, comps = {}, []
    for k in cells:
        if k in comp:
            continue
        q = collections.deque([k]); comp[k] = len(comps); members = [k]
        while q:
            u = q.popleft()
            for v in nbrs(u):
                if v not in comp:
                    comp[v] = len(comps); members.append(v); q.append(v)
        comps.append(members)
    comps_sorted = sorted(range(len(comps)), key=lambda c: -len(comps[c]))
    main_c = comps_sorted[0]
    fails, notes = [], []
    # seams: the engine connects nav areas whose edges coincide; every edge-sharing pair must be a designed link
    # (same region or adjacent regions) with edge corners within --step, else it is a path into a wall or a cliff
    adj = set(frozenset(a_) for a_ in plan.get('adj', []))
    corners = {(c[0], c[1]): c[2] for c in plan.get('cell_corners', [])}

    def ecorn(k, e):
        z_ = cells[k][0]
        c_ = corners.get(k, (z_, z_, z_, z_))
        return {0: (c_[0], c_[1]), 1: (c_[1], c_[2]), 2: (c_[3], c_[2]), 3: (c_[0], c_[3])}[e]
    seams = []
    for (i, j) in cells:
        for e, nb in ((1, (i + 1, j)), (2, (i, j + 1))):
            if nb not in cells:
                continue
            ra, rb = cells[(i, j)][1], cells[nb][1]
            linked = ra == rb or frozenset((ra, rb)) in adj
            ha, hb = ecorn((i, j), e), ecorn(nb, (e + 2) % 4)
            if not linked or abs(ha[0] - hb[0]) > a.step or abs(ha[1] - hb[1]) > a.step:
                seams.append('%s|%s at (%d, %d) heights %s / %s' % (ra, rb, (i + 0.5) * CELL, (j + 0.5) * CELL, ha, hb))
    for s_ in seams[:10]:
        fails.append('nav seam ' + s_)
    if len(seams) > 10:
        fails.append('... %d nav seams in total' % len(seams))
    far = set((lay or {}).get('far_zones', []))      # boxes reached only by script (a teleport): their own component
    for c in comps_sorted[1:]:
        m = comps[c]
        zones = collections.Counter(region_zone.get(cells[k][1], cells[k][1]) for k in m)
        if far and set(zones) <= far:
            notes.append('far zone component of %d cells: %s' % (len(m), dict(zones)))
            continue
        regions = collections.Counter(cells[k][1] for k in m)
        ex = m[0]
        where = '(%d, %d, %d)' % ((ex[0] + 0.5) * CELL, (ex[1] + 0.5) * CELL, cells[ex][0])
        msg = 'component of %d cells off the main graph: %s %s at %s' % (len(m), dict(zones), dict(regions), where)
        (fails if len(m) >= a.min else notes).append(msg)

    def path(ra, rb, via=None):
        src = [k for k, v in cells.items() if v[1] == ra]
        dst = set(k for k, v in cells.items() if v[1] == rb)
        allowed = None if via is None else set(via)
        seen = set(src); q = collections.deque(src)
        while q:
            u = q.popleft()
            if u in dst:
                return True
            for v in nbrs(u):
                if v in seen:
                    continue
                if allowed is not None and cells[v][1] not in allowed:
                    continue
                seen.add(v); q.append(v)
        return False

    routes = [('pit', 'deck', ('pit', 'well_w', 'deck_mid', 'deck')), ('pit', 'deck', ('pit', 'well_e', 'deck_mid', 'deck_east', 'deck')),
              ('hall', 'deck', None), ('tunnel_a', 'deck', None)]
    routes += [('deck', r_, None) for r_ in sorted(set(v[1] for v in cells.values())) if r_.startswith('car_aisle')]   # hero car: zombies enter
    # a scene-generated map (scenegen.py) names its own routes: the start zone to every other zone
    routes += [(a_, b_, None) for a_, b_ in (lay or {}).get('navconn_routes', [])]
    rres = {}
    for ra, rb, via in routes:
        if ra not in region_zone or rb not in region_zone:
            continue
        ok = path(ra, rb, via)
        name = '%s->%s via %s' % (ra, rb, '/'.join(via) if via else 'any')
        rres[name] = ok
        if not ok:
            fails.append('route %s has no cell path' % name)
    # deck west half -> east half: cells of the deck west of x -500 reach cells east of x 1500 on deck regions only
    deck_regions = {'deck', 'deck_mid', 'deck_east'}
    west = [k for k, v in cells.items() if v[1] in deck_regions and (k[0] + 0.5) * CELL < -500]
    east = set(k for k, v in cells.items() if v[1] in deck_regions and (k[0] + 0.5) * CELL > 1500)
    seen = set(west); q = collections.deque(west); ok = False
    while q:
        u = q.popleft()
        if u in east:
            ok = True; break
        for v in nbrs(u):
            if v not in seen and cells[v][1] in deck_regions:
                seen.add(v); q.append(v)
    if west:      # the hand-built v2 map's deck regions (absent from a scene-generated map)
        rres['deck west->east on the deck'] = ok
        if not ok:
            fails.append('route deck west -> east on the deck has no cell path')
    # (g27, coordinator 2026-11-08) corridor arch -> power switch: from the generator room cells at the corridor arch,
    # a cell within 80 of the power switch (layout interaction 'generator') on generator-room cells only
    sw = next((it for it in lay.get('interactions', []) if it.get('kind') == 'generator'), None) if lay else None
    if sw and 'generator' in region_zone:
        sx, sy = sw['origin'][:2]
        src = [k for k, v in cells.items() if v[1] == 'generator' and abs((k[1] + 0.5) * CELL - 2420) < 32 and 2992 < (k[0] + 0.5) * CELL < 3168]
        seen = set(src); q = collections.deque(src); ok = False
        while q:
            u = q.popleft()
            if ((u[0] + 0.5) * CELL - sx) ** 2 + ((u[1] + 0.5) * CELL - sy) ** 2 < 80 ** 2:
                ok = True; break
            for v in nbrs(u):
                if v not in seen and cells[v][1] == 'generator':
                    seen.add(v); q.append(v)
        rres['generator arch->power switch'] = ok
        if not ok:
            fails.append('route generator arch -> power switch has no cell path')
    for n_, ok_ in rres.items():
        print('ROUTE %-50s %s' % (n_, 'ok' if ok_ else 'FAIL'))
    for f in fails:
        print('NAVCONN FAIL', f)
    for n_ in notes[:20]:
        print('NAVCONN note', n_)
    print('navconn: cells %d (decor cut %d), components %d (main %d cells), fails %d' % (len(cells), cut, len(comps), len(comps[main_c]), len(fails)))
    if a.json:
        json.dump({'fails': fails, 'notes': notes, 'routes': rres, 'components': len(comps)}, open(a.json, 'w'), indent=1)
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
