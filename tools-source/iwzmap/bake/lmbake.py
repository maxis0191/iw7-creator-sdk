"""Lightmap baker for generated IW7 worlds (iwzmap).

usage: lmbake.py <source dir> <lights.json> <out dir> [--texel 8] [--rays 100] [--bounces 2] [--quick] [--denoise 1]

<source dir> is an iwzcompile source (world.bin, colmap.hkx, ...). The out dir receives a copy of it with
  world.bin          lightmap coordinates rewritten to the baked atlas (one chart per planar triangle group)
  lightmap/          primary.dds (BC4), secondary.dds (BC6H, two halves), secondunorm.dds (R8G8): the
                     images the compiler (x64-zt iwzmap_lightmap.cpp) ships as the world lightmap
  lighting.txt       light grid relight boxes computed from the same bake (models match walls)
  bake.json          atlas, charts, light list, timings, encode error; bake.npz float images and texels
  preview_*.png      tone-mapped previews (E = irradiance seen by the flat surface normal)

Engine format (from the lit-surface pixel shaders, see bake/README.md):
  E = A + ssao * B * saturate(dot(N, D)),  diffuse = albedo * E   (no exposure constant)
  A = secondary top half, B = secondary bottom half, D = secondunorm (rotated octahedral, tangent frame:
  x tangent, y bitangent = cross(tangent, normal) for packed tangent w > 0, z normal), S = primary sun visibility.
The bake keeps lights' direct light in B along their luminance-weighted mean direction (B = E_direct / D.z so
the flat surface receives exactly E_direct) and indirect light (bounces, emissive surfaces, sky, ambient fill
with ambient occlusion) in A.

Units: lightmap values are radiance-like (the shader multiplies them by the albedo and outputs radiance).
A point light of intensity I gives E = I * (100 / d)^2 * cos(theta) * window(d / radius).

lights.json:
  {"texel": 8, "albedo": {"w/concrete_floor_polished_01": [r, g, b], ...}, "default_albedo": [0.5, 0.5, 0.5],
   "emissive": {"<material>": [r, g, b]}, "sky": [r, g, b], "ambient": {"color": [r, g, b], "ao_radius": 96},
   "sun": {"dir": [x, y, z], "color": [r, g, b]},          # optional: baked sun visibility -> primary
   "lights": [{"type": "point"|"spot", "origin": [x, y, z], "color": [r, g, b], "intensity": I,
               "radius": R, "size": s, "dir": [x, y, z], "inner": deg, "outer": deg}],
   "probe_cell": 128}
"""
import argparse, json, math, os, shutil, struct, sys, time
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import iw7image, rt

PAD = 2

VD = np.dtype([('pos', '<f4', 3), ('bs', '<f4'), ('col', 'u1', 4), ('uv', '<f4', 2), ('lm', '<f4', 2), ('n', '<u4'), ('t', '<u4')])
SD = np.dtype([('mat', '<u4'), ('first', '<u4'), ('vc', '<u4'), ('base', '<u4'), ('tc', '<u4'), ('mn', '<f4', 3), ('mx', '<f4', 3)])
assert VD.itemsize == 44 and SD.itemsize == 44


# ------------------------------------------------------------------ world.bin
def read_world(path):
    b = open(path, 'rb').read()
    magic, ver = struct.unpack_from('<II', b, 0)
    if magic != 0x575A5749 or ver != 1:
        raise SystemExit('world.bin: bad magic/version')
    off = 8
    nm, = struct.unpack_from('<I', b, off); off += 4
    mats = []
    for _ in range(nm):
        l, = struct.unpack_from('<H', b, off); off += 2
        mats.append(b[off:off + l].decode()); off += l
    nv, = struct.unpack_from('<I', b, off); off += 4
    verts = np.frombuffer(b, VD, nv, off).copy(); off += nv * VD.itemsize
    ni, = struct.unpack_from('<I', b, off); off += 4
    idx = np.frombuffer(b, '<u2', ni, off).copy(); off += ni * 2
    ns, = struct.unpack_from('<I', b, off); off += 4
    surfs = np.frombuffer(b, SD, ns, off).copy(); off += ns * SD.itemsize
    bounds = struct.unpack_from('<6f', b, off)
    return {'materials': mats, 'verts': verts, 'indices': idx, 'surfaces': surfs, 'bounds': bounds}


def write_world(w, path):
    out = bytearray(struct.pack('<II', 0x575A5749, 1))
    out += struct.pack('<I', len(w['materials']))
    for m in w['materials']:
        e = m.encode(); out += struct.pack('<H', len(e)) + e
    out += struct.pack('<I', len(w['verts'])) + w['verts'].tobytes()
    out += struct.pack('<I', len(w['indices'])) + w['indices'].astype('<u2').tobytes()
    out += struct.pack('<I', len(w['surfaces'])) + w['surfaces'].tobytes()
    out += struct.pack('<6f', *w['bounds'])
    open(path, 'wb').write(out)


def unpack(q):
    q = q.astype(np.int64)
    v = np.stack([(q >> 0) & 1023, (q >> 10) & 1023, (q >> 20) & 1023], -1) / 511.5 - 1.0
    return v, ((q >> 30) & 3) / 3.0


def norm(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def snap(v, eps=2e-3):
    a = np.abs(v)
    if a.max() > 1 - eps:
        out = np.zeros(3); k = int(np.argmax(a)); out[k] = np.sign(v[k]); return out
    return v


# ------------------------------------------------------------------ charts and atlas
def build_charts(w, texel):
    """Planar triangle groups per surface. Double-sided duplicates (same corners, reversed) are baked once."""
    verts = w['verts']
    pos = verts['pos'].astype(np.float64)
    nrm, _ = unpack(verts['n']); nrm = norm(nrm)
    tan, tw = unpack(verts['t'])
    charts, front = [], []          # front: (a, b, c, surface) baked triangles (global vertex ids)
    for si, s in enumerate(w['surfaces']):
        tri = w['indices'][s['base']:s['base'] + s['tc'] * 3].reshape(-1, 3).astype(np.int64) + s['first']
        seen = {}
        keep = []
        for a, b, c in tri:
            g = np.cross(pos[b] - pos[a], pos[c] - pos[a])
            if np.linalg.norm(g) < 1e-9: continue
            key = tuple(sorted((a, b, c)))
            facing = np.dot(g, nrm[a] + nrm[b] + nrm[c]) > 0
            if key in seen:
                if facing and not seen[key][1]:
                    keep[seen[key][0]] = (a, b, c); seen[key] = (seen[key][0], True)
                continue
            seen[key] = (len(keep), facing); keep.append((a, b, c))
        # union-find over shared corners (welded by position: generated meshes are often unindexed, one quad per
        # triangle pair), split by normal direction and plane
        parent = list(range(len(keep)))
        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]; x = parent[x]
            return x
        owner = {}
        for k, t in enumerate(keep):
            for v in t:
                # corner key: position and shading frame (corners shared by perpendicular walls stay apart)
                key = tuple(np.round(pos[v] * 8).astype(np.int64)) + tuple(np.round(nrm[v] * 64).astype(np.int64)) + \
                    tuple(np.round(tan[v] * 64).astype(np.int64)) + (int(tw[v] > 0),)
                if key in owner:
                    ra, rb = find(owner[key]), find(k)
                    q = keep[ra][0]
                    # same plane and the same shading frame (D is encoded in the frame of one chart vertex)
                    if ra != rb and np.dot(nrm[q], nrm[t[0]]) > 0.999 and np.dot(tan[q], tan[t[0]]) > 0.999 and \
                            tw[q] == tw[t[0]] and abs(np.dot(nrm[t[0]], pos[q] - pos[t[0]])) < 0.25:
                        parent[ra] = rb
                else:
                    owner[key] = k
        groups = {}
        for k in range(len(keep)): groups.setdefault(find(k), []).append(k)
        for g in groups.values():
            tris = [keep[k] for k in g]
            vs = sorted({v for t in tris for v in t})
            # layout frame from the geometry (exact plane; near-axis vectors snapped), shading frame from the
            # packed vertex normal/tangent the shader decodes (D is encoded in that frame)
            n = snap(norm(sum(np.cross(pos[b] - pos[a], pos[c] - pos[a]) for a, b, c in tris)))
            t0 = tan[vs[0]] - n * np.dot(tan[vs[0]], n)
            if np.linalg.norm(t0) < 1e-6:
                t0 = np.cross(n, [0, 0, 1] if abs(n[2]) < 0.9 else [1, 0, 0])
            t0 = snap(norm(t0))
            sgn = -1.0 if tw[vs[0]] > 0 else 1.0       # shader: bitangent = cross(N, T) * (w > 0 ? -1 : 1)
            bt = sgn * np.cross(n, t0)
            sn = norm(nrm[vs[0]]); st = norm(tan[vs[0]])
            sb = sgn * np.cross(sn, st)
            P = pos[vs]
            s2 = P @ t0; r2 = P @ bt
            s0, s1, r0, r1 = s2.min(), s2.max(), r2.min(), r2.max()
            ns = max(1, int(math.ceil((s1 - s0) / texel - 1e-6))); nr = max(1, int(math.ceil((r1 - r0) / texel - 1e-6)))
            charts.append({'surface': si, 'tris': tris, 'verts': vs, 'n': n, 't': t0, 'b': bt, 'd': float((P @ n).mean()),
                           'sn': sn, 'st': st, 'sb': sb,
                           's0': s0, 'r0': r0, 'ns': ns, 'nr': nr, 'ts': (s1 - s0) / ns if s1 > s0 else texel,
                           'tr': (r1 - r0) / nr if r1 > r0 else texel, 'mat': int(s['mat'])})
            front += [(a, b, c, si) for a, b, c in tris]
    return charts, front


def pack(charts):
    def a4(x): return (x + 3) & ~3
    for c in charts:
        c['w'] = a4(c['ns'] + 2 * PAD); c['h'] = a4(c['nr'] + 2 * PAD)
    order = sorted(range(len(charts)), key=lambda i: (-charts[i]['h'], -charts[i]['w']))
    for W in (256, 512, 1024, 2048, 4096):
        x = y = shelf = 0; ok = True
        for i in order:
            c = charts[i]
            if c['w'] > W: ok = False; break
            if x + c['w'] > W: x = 0; y += shelf; shelf = 0
            c['x'], c['y'] = x, y
            x += c['w']; shelf = max(shelf, c['h'])
        used = y + shelf
        H = 4
        while H < used: H *= 2
        if ok and H <= W:
            return W, H
    raise SystemExit('atlas does not fit 4096 x 4096 (increase --texel)')


def chart_texels(charts, w, W, H):
    """Texel centres, frames and coverage of every chart; vertex lightmap coordinates."""
    verts = w['verts']
    rows = []
    for ci, c in enumerate(charts):
        ii, jj = np.meshgrid(np.arange(c['ns']), np.arange(c['nr']), indexing='xy')
        s = c['s0'] + (ii.ravel() + 0.5) * c['ts']; r = c['r0'] + (jj.ravel() + 0.5) * c['tr']
        p = s[:, None] * c['t'] + r[:, None] * c['b'] + c['d'] * c['n']
        # coverage: texel centre inside a chart triangle (2D), with a small tolerance
        pos = verts['pos'].astype(np.float64)
        inside = np.zeros(len(s), bool)
        for a, b, cc in c['tris']:
            P = np.array([[pos[v] @ c['t'], pos[v] @ c['b']] for v in (a, b, cc)])
            v0 = P[1] - P[0]; v1 = P[2] - P[0]
            d = v0[0] * v1[1] - v0[1] * v1[0]
            if abs(d) < 1e-9: continue
            qx = s - P[0, 0]; qy = r - P[0, 1]
            u = (qx * v1[1] - qy * v1[0]) / d; v = (v0[0] * qy - v0[1] * qx) / d
            e = 0.5 * c['ts'] / max(np.linalg.norm(v0), 1e-6)
            inside |= (u >= -e) & (v >= -e) & (u + v <= 1 + e)
        rows.append({'chart': np.full(len(s), ci), 'x': c['x'] + PAD + ii.ravel(), 'y': c['y'] + PAD + jj.ravel(), 'pos': p,
                     'inside': inside})
        for v in c['verts']:
            pv = pos[v]
            verts['lm'][v, 0] = (c['x'] + PAD + (pv @ c['t'] - c['s0']) / c['ts']) / W
            verts['lm'][v, 1] = (c['y'] + PAD + (pv @ c['b'] - c['r0']) / c['tr']) / H
    cat = lambda k: np.concatenate([r[k] for r in rows])
    tx = {k: cat(k) for k in ('chart', 'x', 'y', 'pos', 'inside')}
    keep = tx['inside']
    for k in tx: tx[k] = tx[k][keep]
    ch = tx['chart']
    tx['n'] = np.array([charts[i]['n'] for i in range(len(charts))])[ch]
    tx['t'] = np.array([charts[i]['t'] for i in range(len(charts))])[ch]
    tx['b'] = np.array([charts[i]['b'] for i in range(len(charts))])[ch]
    tx['tu'] = tx['t'] * np.array([charts[i]['ts'] for i in range(len(charts))])[ch, None] * 0.5
    tx['tv'] = tx['b'] * np.array([charts[i]['tr'] for i in range(len(charts))])[ch, None] * 0.5
    tx['mat'] = np.array([charts[i]['mat'] for i in range(len(charts))])[ch]
    for k in ('sn', 'st', 'sb'):
        tx[k] = np.array([charts[i][k] for i in range(len(charts))])[ch]
    return tx


# ------------------------------------------------------------------ encoding helpers
def oct_encode(d):
    """Tangent-space unit vectors (z >= 0) -> rotated octahedral R8G8 (the shader's decode inverted)."""
    p = d / np.maximum(np.abs(d).sum(-1, keepdims=True), 1e-12)
    a = p[..., 0] + p[..., 1]; b = p[..., 0] - p[..., 1]
    rg = np.stack([(a + 1) * 0.5, (b + 1) * 0.5], -1)
    return np.clip(np.round(rg * 255), 0, 255) / 255.0


def oct_decode(rg):
    a = rg[..., 0] * 2 - 1; b = rg[..., 1] * 2 - 1
    x = (a + b) * 0.5; y = (a - b) * 0.5; z = 1 - np.abs(x) - np.abs(y)
    return norm(np.stack([x, y, z], -1))


def dilate(img, valid):
    from scipy import ndimage
    _, (iy, ix) = ndimage.distance_transform_edt(~valid, return_indices=True)
    return img[iy, ix]


def preview(path, rgb):
    from PIL import Image
    x = np.clip(rgb, 0, None) * 2.0
    x = x / (1 + x)
    Image.fromarray((np.power(x, 1 / 2.2) * 255).astype(np.uint8)).save(path)


# ------------------------------------------------------------------ bake
def chart_filter(val, x, y, chart, W, H, r):
    """(2r+1)^2 box filter of per-texel values restricted to texels of the same chart (no bleeding across
    charts, walls or corners)."""
    img = np.zeros((H + 2 * r, W + 2 * r, val.shape[1])); cid = np.full((H + 2 * r, W + 2 * r), -1, np.int64)
    img[y + r, x + r] = val; cid[y + r, x + r] = chart
    acc = np.zeros_like(val); cnt = np.zeros(len(val))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            m = cid[y + r + dy, x + r + dx] == chart
            acc[m] += img[y[m] + r + dy, x[m] + r + dx]; cnt[m] += 1
    return acc / np.maximum(cnt, 1)[:, None]


def bake(src, lights_path, out, texel=None, nrays=100, bounces=2, quick=False, pattern=None, denoise=1):
    t_start = time.time(); timing = {}
    cfg = json.load(open(lights_path))
    texel = texel or cfg.get('texel', 8)
    w = read_world(os.path.join(src, 'world.bin'))
    charts, front = build_charts(w, texel)
    W, H = pack(charts)
    tx = chart_texels(charts, w, W, H)
    n = len(tx['x'])
    print('charts %d, atlas %d x %d, texels %d (texel %.1f units), triangles %d' % (len(charts), W, H, n, texel, len(front)))
    timing['charts'] = time.time() - t_start

    # scene: baked triangles (+ occluder boxes)
    pos = w['verts']['pos'].astype(np.float64)
    F = np.array([(a, b, c) for a, b, c, _ in front], np.int64)
    tri_v = [pos[F[:, 0]], pos[F[:, 1]], pos[F[:, 2]]]
    lm = w['verts']['lm'].astype(np.float64)
    tri_lm = [lm[F[:, 0]], lm[F[:, 1]], lm[F[:, 2]]]
    tri_mat = np.array([int(w['surfaces'][si]['mat']) for *_, si in front])
    occ = cfg.get('occluders', [])
    for o in occ:                                   # axis-aligned boxes that only block light (decor)
        mn, mx = np.array(o['min'], float), np.array(o['max'], float)
        c = np.array([[mn[0], mn[1], mn[2]], [mx[0], mn[1], mn[2]], [mx[0], mx[1], mn[2]], [mn[0], mx[1], mn[2]],
                      [mn[0], mn[1], mx[2]], [mx[0], mn[1], mx[2]], [mx[0], mx[1], mx[2]], [mn[0], mx[1], mx[2]]])
        quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        for q in quads:
            for t in ((q[0], q[1], q[2]), (q[0], q[2], q[3])):
                for k in range(3): tri_v[k] = np.vstack([tri_v[k], c[t[k]][None]])
                for k in range(3): tri_lm[k] = np.vstack([tri_lm[k], [[-1, -1]]])
                tri_mat = np.append(tri_mat, -1)
    scene = rt.Scene(*tri_v)
    S_args = scene.args()

    # material properties
    mats = w['materials']
    alb = np.array([cfg.get('albedo', {}).get(m, cfg.get('default_albedo', [0.5, 0.5, 0.5])) for m in mats], float)
    emi = np.array([cfg.get('emissive', {}).get(m, [0, 0, 0]) for m in mats], float)

    # lights
    L = []
    for l in cfg.get('lights', []):
        d = norm(np.array(l.get('dir', [0, 0, -1]), float))
        ci = math.cos(math.radians(l.get('inner', 30))); co = math.cos(math.radians(l.get('outer', 45)))
        L.append(list(l['origin']) + list(l['color']) + [l['intensity'], l['radius'], l.get('size', 4.0)] + list(d) +
                 [ci, co, 1.0 if l.get('type') == 'spot' else 0.0, 0.0])
    L = np.array(L, float).reshape(-1, 16)
    p, nn = np.ascontiguousarray(tx['pos']), np.ascontiguousarray(tx['n'])
    tu, tv = np.ascontiguousarray(tx['tu']), np.ascontiguousarray(tx['tv'])
    t0 = time.time()
    Edir, Wdir = rt.direct_light(p, nn, tu, tv, 1 if quick else 3, L, 1, *S_args)
    timing['direct'] = time.time() - t0
    print('direct light: %d lights, %.1f s' % (len(L), timing['direct']))

    # indirect: one set of cosine rays per texel, reused by every bounce
    t0 = time.time()
    nr_ = 16 if quick else nrays
    tid = np.full((H, W), -1, np.int64)
    tid[tx['y'], tx['x']] = np.arange(n)
    tid = dilate(tid, tid >= 0)

    def hit_texels(tri, u, v, side):
        out = np.empty(tri.shape, np.int32)
        for r0 in range(0, len(tri), 8192):           # chunked: (texels, rays, 2) float arrays get large
            t, uu, vv, sd = tri[r0:r0 + 8192], u[r0:r0 + 8192], v[r0:r0 + 8192], side[r0:r0 + 8192]
            a, b, c = (tri_lm[k][np.maximum(t, 0)] for k in range(3))
            uvh = (1 - uu - vv)[..., None] * a + uu[..., None] * b + vv[..., None] * c
            xi = np.clip((uvh[..., 0] * W).astype(np.int64), 0, W - 1); yi = np.clip((uvh[..., 1] * H).astype(np.int64), 0, H - 1)
            h = tid[yi, xi]
            out[r0:r0 + 8192] = np.where(t < 0, -1, np.where((sd < 0) | (tri_mat[np.maximum(t, 0)] < 0), -2, h))
        return out

    sky = np.array(cfg.get('sky', [0, 0, 0]), float)
    amb = cfg.get('ambient', {})
    fill = np.array(amb.get('color', [0, 0, 0]), float)
    # rays traced in texel chunks and reduced at once to hit texel ids (int32: n x rays x 4 bytes is what stays)
    idx = np.empty((n, nr_), np.int32); ao = np.empty(n)
    for c0 in range(0, n, 65536):
        c1 = min(n, c0 + 65536)
        htri, hu, hv, hdist, hside = rt.gather_rays(p[c0:c1], nn[c0:c1], tu[c0:c1], tv[c0:c1], nr_, 7 + c0, *S_args)
        hits = hit_texels(htri, hu, hv, hside)        # -1 sky, -2 back face/occluder (black)
        idx[c0:c1] = np.where(hits == -1, n, np.where(hits == -2, n + 1, hits))
        ao[c0:c1] = (hdist > amb.get('ao_radius', 96)).mean(1)
        del htri, hu, hv, hdist, hside, hits
    timing['gather_rays'] = time.time() - t0
    a_tex = alb[tx['mat']]; e_tex = emi[tx['mat']]
    Eind = np.zeros((n, 3))
    for k in range(bounces):
        Lout = np.vstack([a_tex * (Edir + Eind) + e_tex, sky[None], np.zeros((1, 3))])
        Eind = np.concatenate([Lout[idx[r0:r0 + 8192]].mean(1) for r0 in range(0, n, 8192)])
    timing['indirect'] = time.time() - t0
    print('indirect: %d rays/texel, %d bounces, %.1f s; mean AO %.3f' % (nr_, bounces, timing['indirect'], ao.mean()))

    # light grid samples (lighting.txt): SH order 1 (constant + vertical) of the radiance around each cell centre
    t0 = time.time()
    Lfinal = np.vstack([a_tex * (Edir + Eind + fill * ao[:, None]) + e_tex, sky[None], np.zeros((1, 3))])
    light_lines, grid = light_grid(cfg, w, Lfinal, n, scene, tri_lm, tri_mat, tid, W, H, L, quick)
    timing['light_grid'] = time.time() - t0

    # encode: B along the dominant direction of the direct light, A the rest
    dirw = Wdir.copy()
    weak = np.linalg.norm(dirw, axis=1) < 1e-9
    dirw[weak] = nn[weak]
    D = norm(dirw)
    Dt = np.stack([(D * tx['st']).sum(1), (D * tx['sb']).sum(1), (D * tx['sn']).sum(1)], 1)
    Dt[:, 2] = np.maximum(Dt[:, 2], 0.05)
    Dt = norm(Dt)
    rg = oct_encode(Dt)
    zq = np.maximum(oct_decode(rg)[:, 2], 0.05)
    B = Edir / zq[:, None]
    A = Eind + fill * ao[:, None]
    if denoise > 0:                                  # indirect light is low frequency: chart-local box filter
        A = chart_filter(A, tx['x'], tx['y'], tx['chart'], W, H, denoise)
    # calibration patches (controlled engine experiments): texels inside a box get chosen A, B and direction
    for pt in (pattern or []):
        lo, hi = np.array(pt['box'][:3], float), np.array(pt['box'][3:], float)
        sel = np.all((p >= lo) & (p <= hi), 1) & ((nn @ np.array(pt.get('normal', [0, 0, 1]), float)) > 0.99)
        dz = float(pt.get('Dz', 1.0)); dx = math.sqrt(max(0.0, 1 - dz * dz))
        drg = oct_encode(np.array([[dx * pt.get('Dsign', 1.0), 0.0, dz]]))[0]
        rg[sel] = drg; A[sel] = pt.get('A', [0, 0, 0]); B[sel] = pt.get('B', [0, 0, 0])
        Edir[sel] = 0; Eind[sel] = A[sel]
        print('pattern %s: %d texels A %s B %s Dz %.3f (encoded %.3f)' % (pt.get('name', ''), sel.sum(), pt.get('A'), pt.get('B'),
                                                                         dz, oct_decode(drg)[2]))
    S = np.zeros(n)
    if cfg.get('sun'):
        sd = norm(np.array(cfg['sun']['dir'], float))
        far = p + nn * 0.5 - sd[None] * 1e5
        S = rt.visible(p + nn * 0.5, far, *S_args).astype(float) * (np.dot(nn, -sd) > 0)
    for pt in (pattern or []):                       # calibration patches may also force the sun visibility
        if 'S' in pt:
            lo, hi = np.array(pt['box'][:3], float), np.array(pt['box'][3:], float)
            S[np.all((p >= lo) & (p <= hi), 1) & ((nn @ np.array(pt.get('normal', [0, 0, 1]), float)) > 0.99)] = pt['S']

    imgA = np.zeros((H, W, 3), np.float32); imgB = np.zeros((H, W, 3), np.float32)
    imgD = np.zeros((H, W, 2), np.float32); imgS = np.zeros((H, W), np.float32)
    valid = np.zeros((H, W), bool)
    y, x = tx['y'], tx['x']
    imgA[y, x] = A; imgB[y, x] = B; imgD[y, x] = rg; imgS[y, x] = S; valid[y, x] = True
    imgD[~valid] = oct_encode(np.array([0.0, 0.0, 1.0]))
    imgA, imgB, imgD, imgS = dilate(imgA, valid), dilate(imgB, valid), dilate(imgD, valid), dilate(imgS, valid)

    os.makedirs(out, exist_ok=True)
    # the baked source is the whole source: files and folders (modules/ holds the game-script modules the level
    # script starts; a copy without it builds a map whose level script fails to link: ShutdownGame at load, W2 build b)
    for f in os.listdir(src):
        p = os.path.join(src, f)
        if os.path.abspath(src) == os.path.abspath(out) or f in ('lightmap', 'bake_tmp'):
            continue
        if os.path.isfile(p):
            shutil.copyfile(p, os.path.join(out, f))
        elif os.path.isdir(p):
            shutil.copytree(p, os.path.join(out, f), dirs_exist_ok=True)
    lmdir = os.path.join(out, 'lightmap'); os.makedirs(lmdir, exist_ok=True)
    work = os.path.join(out, 'bake_tmp')
    t0 = time.time()
    sec = np.concatenate([imgA, imgB], 0)
    sec_bc = iw7image.encode(sec, 'BC6H_UF16', work)
    iw7image.write_dds(os.path.join(lmdir, 'secondary.dds'), 95, W, 2 * H, sec_bc)
    iw7image.write_dds(os.path.join(lmdir, 'primary.dds'), 80, W, H, iw7image.encode(imgS[..., None], 'BC4_UNORM', work))
    iw7image.write_dds(os.path.join(lmdir, 'secondunorm.dds'), 49, W, H, iw7image.encode(imgD, 'R8G8_UNORM'))
    timing['encode'] = time.time() - t0
    dec = iw7image.decode(95, W, 2 * H, sec_bc, work)[..., :3]
    rel = np.abs(dec - sec)[np.concatenate([valid, valid])] / (np.abs(sec)[np.concatenate([valid, valid])] + 0.01)
    enc_err = {'bc6h_rel_err_mean': float(rel.mean()), 'bc6h_rel_err_p99': float(np.percentile(rel, 99)),
               'bc6h_rel_err_max': float(rel.max())}
    print('encode %.1f s: BC6H relative error mean %.4f p99 %.4f' % (timing['encode'], rel.mean(), np.percentile(rel, 99)))
    shutil.rmtree(work, ignore_errors=True)

    write_world(w, os.path.join(out, 'world.bin'))
    open(os.path.join(out, 'lighting.txt'), 'w', newline='\n').write('\n'.join(light_lines) + '\n')
    E_flat = imgA + imgB * oct_decode(imgD)[..., 2:3]
    preview(os.path.join(out, 'preview_E.png'), E_flat)
    preview(os.path.join(out, 'preview_A.png'), imgA)
    preview(os.path.join(out, 'preview_B.png'), imgB)
    np.savez_compressed(os.path.join(out, 'bake.npz'), A=imgA, B=imgB, D=imgD, S=imgS, valid=valid,
                        tx_pos=p, tx_n=nn, tx_x=x, tx_y=y, tx_mat=tx['mat'], tx_chart=tx['chart'], Edir=Edir, Eind=Eind, ao=ao,
                        grid=grid)
    rep = {'schema': 'iwzmap.lightbake/1', 'atlas': [W, H], 'texel': texel, 'texels': n, 'charts': len(charts),
           'triangles': len(front), 'occluder_boxes': len(occ), 'lights': len(L), 'rays_per_texel': nr_, 'bounces': bounces,
           'mean': {'A': imgA[valid].mean(0).tolist(), 'B': imgB[valid].mean(0).tolist(), 'E': E_flat[valid].mean(0).tolist(),
                    'ao': float(ao.mean())},
           'encode': enc_err, 'timing_s': {k: round(v, 2) for k, v in timing.items()}, 'total_s': round(time.time() - t_start, 1),
           'chart_list': [{'surface': c['surface'], 'material': mats[c['mat']], 'rect': [c['x'], c['y'], c['w'], c['h']],
                           'texels': [c['ns'], c['nr']], 'normal': [round(float(v), 3) for v in c['n']]} for c in charts]}
    json.dump(rep, open(os.path.join(out, 'bake.json'), 'w'), indent=1)
    print('bake done in %.1f s -> %s' % (time.time() - t_start, out))
    return rep


Y00 = 0.282095
Y1 = 0.488603


def light_grid(cfg, w, Lfinal, n, scene, tri_lm, tri_mat, tid, W, H, L, quick):
    """Order-1 SH (constant and vertical terms, the compiler's relight format) at cell centres of a regular grid
    over the world. Cells inside solid or outside the world (most rays hit back faces or escape) are skipped."""
    cell = cfg.get('probe_cell', 128)
    mn = np.array(w['bounds'][:3]); mx = np.array(w['bounds'][3:])
    xs = np.arange(mn[0] + cell / 2, mx[0], cell); ys = np.arange(mn[1] + cell / 2, mx[1], cell)
    zs = np.arange(mn[2] + min(cell / 2, 48), mx[2], cell)
    P = np.array(np.meshgrid(xs, ys, zs, indexing='ij')).reshape(3, -1).T
    nrays = 64 if quick else 256
    dirs, tri, bu, bv, side = rt.sphere_rays(np.ascontiguousarray(P), nrays, 3, *scene.args())
    a, b, c = (tri_lm[k][np.maximum(tri, 0)] for k in range(3))
    uvh = (1 - bu - bv)[..., None] * a + bu[..., None] * b + bv[..., None] * c
    xi = np.clip((uvh[..., 0] * W).astype(np.int64), 0, W - 1); yi = np.clip((uvh[..., 1] * H).astype(np.int64), 0, H - 1)
    h = tid[yi, xi]
    bad = (side < 0) | (tri < 0) | (tri_mat[np.maximum(tri, 0)] < 0)
    keep = bad.mean(1) < 0.25
    idx = np.where(tri < 0, n, np.where(bad, n + 1, h))
    rad = Lfinal[idx]                                       # (cells, rays, 3)
    c0 = rad.mean(1) * 4 * math.pi * Y00
    c10 = (rad * dirs[None, :, 2:3]).mean(1) * 4 * math.pi * Y1
    # direct light (delta lights): c_lm += pi * E_peak * Y_lm(l)
    for l in L:
        d = l[:3][None] - P
        dist = np.linalg.norm(d, axis=1); ld = d / np.maximum(dist, 1e-6)[:, None]
        q = (dist / l[7]) ** 4; win = np.maximum(0, 1 - q) ** 2
        e = l[6] * (100.0 ** 2) / np.maximum(dist ** 2, 256.0) * win
        if l[14] > 0.5:
            cd = -(ld @ l[9:12]); t = np.clip((cd - l[13]) / max(l[12] - l[13], 1e-4), 0, 1); e *= t * t * (3 - 2 * t)
        vis = rt.visible(np.ascontiguousarray(P), np.ascontiguousarray(np.repeat(l[None, :3], len(P), 0)), *scene.args())
        e = e * vis * (dist < l[7])
        c0 += math.pi * e[:, None] * l[3:6][None] * Y00
        c10 += math.pi * e[:, None] * l[3:6][None] * Y1 * ld[:, 2:3]
    up = np.clip((c10.sum(1)) / np.maximum(c0.sum(1), 1e-6), -1, 1)
    lines = []
    if keep.any():
        g = c0[keep].mean(0)
        lines.append('ambient %.4f %.4f %.4f %.2f' % (g[0], g[1], g[2], float(np.clip(up[keep].mean(), -1, 1))))
    # cells grown by one cell first (probes in and behind the walls), then the exact cells (inside the rooms)
    for grow in (cell, 0):
        for k in np.nonzero(keep)[0]:
            x0, y0, z0 = P[k] - cell / 2 - grow
            x1, y1, z1 = P[k] + cell / 2 + grow
            lines.append('room %d %d %d %d %d %d %.4f %.4f %.4f %.2f' % (x0, y0, z0, x1, y1, z1, c0[k, 0], c0[k, 1], c0[k, 2], up[k]))
    print('light grid: %d of %d cells kept, mean c0 %s' % (keep.sum(), len(P), c0[keep].mean(0).round(3) if keep.any() else '-'))
    return lines, np.hstack([P, c0, up[:, None], keep[:, None]])


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('src'); ap.add_argument('lights'); ap.add_argument('out')
    ap.add_argument('--texel', type=float); ap.add_argument('--rays', type=int, default=100)
    ap.add_argument('--bounces', type=int, default=2); ap.add_argument('--quick', action='store_true')
    ap.add_argument('--denoise', type=int, default=1, help='chart-local box filter radius of the indirect term (0 = off)')
    ap.add_argument('--pattern', help='json list of calibration patches {box, normal, A, B, Dz, name}')
    a = ap.parse_args()
    bake(a.src, a.lights, a.out, a.texel, a.rays, a.bounces, a.quick, json.load(open(a.pattern)) if a.pattern else None,
         a.denoise)
