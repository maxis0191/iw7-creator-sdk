"""Small CPU ray tracer for the lightmap baker: triangle BVH (median split) and numba kernels.

Triangles are one-sided for shading but block rays from both sides. All kernels are parallel over rays.
"""
import math
import numpy as np
from numba import njit, prange

LEAF = 4


def build_bvh(v0, v1, v2):
    """v0, v1, v2: (n, 3) float64 triangle corners. Returns node arrays and the triangle order."""
    n = len(v0)
    cent = (v0 + v1 + v2) / 3.0
    tmin = np.minimum(np.minimum(v0, v1), v2)
    tmax = np.maximum(np.maximum(v0, v1), v2)
    order = np.arange(n)
    bmin, bmax, left, right, start, count = [], [], [], [], [], []

    def rec(lo, hi):
        idx = order[lo:hi]
        node = len(bmin)
        bmin.append(tmin[idx].min(0)); bmax.append(tmax[idx].max(0))
        left.append(-1); right.append(-1); start.append(lo); count.append(hi - lo)
        if hi - lo <= LEAF:
            return node
        c = cent[idx]
        ax = int(np.argmax(c.max(0) - c.min(0)))
        srt = idx[np.argsort(c[:, ax], kind='stable')]
        order[lo:hi] = srt
        mid = (lo + hi) // 2
        count[node] = 0
        l = rec(lo, mid); r = rec(mid, hi)
        left[node] = l; right[node] = r
        return node

    rec(0, n)
    return (np.array(bmin), np.array(bmax), np.array(left, np.int32), np.array(right, np.int32),
            np.array(start, np.int32), np.array(count, np.int32), order.astype(np.int32))


class Scene:
    def __init__(self, v0, v1, v2):
        self.v0 = np.ascontiguousarray(v0, np.float64)
        self.v1 = np.ascontiguousarray(v1, np.float64)
        self.v2 = np.ascontiguousarray(v2, np.float64)
        self.bmin, self.bmax, self.left, self.right, self.start, self.count, self.order = build_bvh(self.v0, self.v1, self.v2)

    def args(self):
        return (self.v0, self.v1, self.v2, self.bmin, self.bmax, self.left, self.right, self.start, self.count, self.order)


@njit(cache=True, fastmath=True)
def _box(o, inv, bmin, bmax, tmax):
    t0 = 0.0; t1 = tmax
    for a in range(3):
        ta = (bmin[a] - o[a]) * inv[a]
        tb = (bmax[a] - o[a]) * inv[a]
        if ta > tb:
            ta, tb = tb, ta
        if ta > t0: t0 = ta
        if tb < t1: t1 = tb
        if t0 > t1: return False
    return True


@njit(cache=True, fastmath=True)
def _tri(o, d, a, b, c):
    e1x = b[0] - a[0]; e1y = b[1] - a[1]; e1z = b[2] - a[2]
    e2x = c[0] - a[0]; e2y = c[1] - a[1]; e2z = c[2] - a[2]
    px = d[1] * e2z - d[2] * e2y; py = d[2] * e2x - d[0] * e2z; pz = d[0] * e2y - d[1] * e2x
    det = e1x * px + e1y * py + e1z * pz
    if abs(det) < 1e-12: return -1.0, 0.0, 0.0
    inv = 1.0 / det
    tx = o[0] - a[0]; ty = o[1] - a[1]; tz = o[2] - a[2]
    u = (tx * px + ty * py + tz * pz) * inv
    if u < 0.0 or u > 1.0: return -1.0, 0.0, 0.0
    qx = ty * e1z - tz * e1y; qy = tz * e1x - tx * e1z; qz = tx * e1y - ty * e1x
    v = (d[0] * qx + d[1] * qy + d[2] * qz) * inv
    if v < 0.0 or u + v > 1.0: return -1.0, 0.0, 0.0
    t = (e2x * qx + e2y * qy + e2z * qz) * inv
    return t, u, v


@njit(cache=True, fastmath=True)
def trace(o, d, tmax, any_hit, v0, v1, v2, bmin, bmax, left, right, start, count, order):
    """Closest hit (or any hit). Returns (t, triangle, u, v); triangle -1 = miss."""
    inv = np.empty(3)
    for a in range(3):
        inv[a] = 1.0 / d[a] if abs(d[a]) > 1e-12 else 1e12
    stack = np.empty(64, np.int32)
    sp = 0; stack[0] = 0; sp = 1
    best = tmax; bt = -1; bu = 0.0; bv = 0.0
    while sp > 0:
        sp -= 1
        nd = stack[sp]
        if not _box(o, inv, bmin[nd], bmax[nd], best):
            continue
        if count[nd] > 0:
            for k in range(start[nd], start[nd] + count[nd]):
                ti = order[k]
                t, u, v = _tri(o, d, v0[ti], v1[ti], v2[ti])
                if t > 1e-4 and t < best:
                    best = t; bt = ti; bu = u; bv = v
                    if any_hit:
                        return best, bt, bu, bv
        else:
            stack[sp] = left[nd]; sp += 1
            stack[sp] = right[nd]; sp += 1
    return best, bt, bu, bv


@njit(cache=True, fastmath=True)
def _hash(i, j):
    x = (i * 0x9E3779B1 + j * 0x85EBCA77 + 0x165667B1) & 0xFFFFFFFF
    x ^= x >> 15; x = (x * 0x2C1B3C6D) & 0xFFFFFFFF
    x ^= x >> 12; x = (x * 0x297A2D39) & 0xFFFFFFFF
    x ^= x >> 15
    return (x & 0xFFFFFF) / 16777216.0


@njit(cache=True, fastmath=True)
def _onb(n):
    if abs(n[2]) < 0.999:
        tx, ty, tz = -n[1], n[0], 0.0
    else:
        tx, ty, tz = 0.0, -n[2], n[1]
    l = math.sqrt(tx * tx + ty * ty + tz * tz)
    tx /= l; ty /= l; tz /= l
    bx = n[1] * tz - n[2] * ty; by = n[2] * tx - n[0] * tz; bz = n[0] * ty - n[1] * tx
    return tx, ty, tz, bx, by, bz


@njit(parallel=True, cache=True, fastmath=True)
def direct_light(pos, nrm, tu, tv, sub, lights, seed, v0, v1, v2, bmin, bmax, left, right, start, count, order):
    """Direct irradiance from point/spot lights with ray traced soft shadows.
    pos/nrm (n,3) texel centre and normal; tu/tv (n,3) texel half extents along the chart axes;
    sub = subsamples per axis; lights (m, 16): pos3 col3 intensity radius size dir3 cos_inner cos_outer type pad.
    Returns E (n,3) and the luminance-weighted direction sum (n,3) and, for the lights' share of the sun, nothing."""
    n = pos.shape[0]
    E = np.zeros((n, 3)); W = np.zeros((n, 3))
    for i in prange(n):
        o = np.empty(3); d = np.empty(3)
        ex = 0.0; ey = 0.0; ez = 0.0; wx = 0.0; wy = 0.0; wz = 0.0
        nx, ny, nz = nrm[i, 0], nrm[i, 1], nrm[i, 2]
        ns = sub * sub
        for s in range(ns):
            fu = ((s % sub) + _hash(i, s * 7 + seed)) / sub * 2.0 - 1.0
            fv = ((s // sub) + _hash(i, s * 7 + 3 + seed)) / sub * 2.0 - 1.0
            px = pos[i, 0] + tu[i, 0] * fu + tv[i, 0] * fv + nx * 0.5
            py = pos[i, 1] + tu[i, 1] * fu + tv[i, 1] * fv + ny * 0.5
            pz = pos[i, 2] + tu[i, 2] * fu + tv[i, 2] * fv + nz * 0.5
            for k in range(lights.shape[0]):
                L = lights[k]
                # jitter the light over its sphere (soft shadows)
                r1 = _hash(i * 31 + k, s + seed * 13); r2 = _hash(i * 17 + k, s + 5 + seed * 13); r3 = _hash(i * 13 + k, s + 9 + seed)
                jz = 2.0 * r1 - 1.0; ja = 6.2831853 * r2; jr = math.sqrt(max(0.0, 1.0 - jz * jz)) * L[8] * r3
                lx = L[0] + jr * math.cos(ja) - px; ly = L[1] + jr * math.sin(ja) - py; lz = L[2] + jz * L[8] * r3 - pz
                dist2 = lx * lx + ly * ly + lz * lz
                dist = math.sqrt(dist2)
                if dist < 1e-3 or dist > L[7]:
                    continue
                lx /= dist; ly /= dist; lz /= dist
                cos = nx * lx + ny * ly + nz * lz
                if cos <= 0.0:
                    continue
                att = (100.0 * 100.0) / max(dist2, 16.0 * 16.0)
                q = dist / L[7]; q = q * q; q = q * q
                win = max(0.0, 1.0 - q); att *= win * win
                if L[14] > 0.5:   # spot: smooth cone
                    cd = -(lx * L[9] + ly * L[10] + lz * L[11])
                    if cd <= L[13]:
                        continue
                    t = min(1.0, (cd - L[13]) / max(L[12] - L[13], 1e-4)); att *= t * t * (3.0 - 2.0 * t)
                o[0] = px; o[1] = py; o[2] = pz; d[0] = lx; d[1] = ly; d[2] = lz
                th, tri, _, _ = trace(o, d, dist - 1.0, True, v0, v1, v2, bmin, bmax, left, right, start, count, order)
                if tri >= 0:
                    continue
                f = L[6] * att * cos
                r = f * L[3]; g = f * L[4]; b = f * L[5]
                ex += r; ey += g; ez += b
                lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
                wx += lum * lx; wy += lum * ly; wz += lum * lz
        E[i, 0] = ex / ns; E[i, 1] = ey / ns; E[i, 2] = ez / ns
        W[i, 0] = wx / ns; W[i, 1] = wy / ns; W[i, 2] = wz / ns
    return E, W


@njit(parallel=True, cache=True, fastmath=True)
def gather_rays(pos, nrm, tu, tv, nrays, seed, v0, v1, v2, bmin, bmax, left, right, start, count, order):
    """Cosine-weighted hemisphere rays per texel: hit triangle, barycentrics and distance (-1 = escaped)."""
    n = pos.shape[0]
    tri = np.full((n, nrays), -1, np.int32)
    bu = np.zeros((n, nrays), np.float32); bv = np.zeros((n, nrays), np.float32)
    dist = np.full((n, nrays), 1e9, np.float32)
    side = np.zeros((n, nrays), np.int8)
    sq = int(math.sqrt(nrays))
    for i in prange(n):
        o = np.empty(3); d = np.empty(3)
        nv = nrm[i]
        tx, ty, tz, bx, by, bz = _onb(nv)
        for k in range(nrays):
            # stratified (sq x sq), remainder random
            if k < sq * sq:
                r1 = ((k % sq) + _hash(i, k + seed)) / sq; r2 = ((k // sq) + _hash(i + 7, k + seed)) / sq
            else:
                r1 = _hash(i, k + seed); r2 = _hash(i + 7, k + seed)
            phi = 6.2831853 * r1; sr = math.sqrt(r2)
            lx = sr * math.cos(phi); ly = sr * math.sin(phi); lz = math.sqrt(max(0.0, 1.0 - r2))
            d[0] = tx * lx + bx * ly + nv[0] * lz; d[1] = ty * lx + by * ly + nv[1] * lz; d[2] = tz * lx + bz * ly + nv[2] * lz
            fu = _hash(i * 3, k + seed) * 2.0 - 1.0; fv = _hash(i * 5, k + seed) * 2.0 - 1.0
            o[0] = pos[i, 0] + tu[i, 0] * fu + tv[i, 0] * fv + nv[0] * 0.5
            o[1] = pos[i, 1] + tu[i, 1] * fu + tv[i, 1] * fv + nv[1] * 0.5
            o[2] = pos[i, 2] + tu[i, 2] * fu + tv[i, 2] * fv + nv[2] * 0.5
            t, ti, u, v = trace(o, d, 1e9, False, v0, v1, v2, bmin, bmax, left, right, start, count, order)
            if ti >= 0:
                tri[i, k] = ti; bu[i, k] = u; bv[i, k] = v; dist[i, k] = t
                # front (+1) or back (-1) side of the hit triangle
                e1x = v1[ti, 0] - v0[ti, 0]; e1y = v1[ti, 1] - v0[ti, 1]; e1z = v1[ti, 2] - v0[ti, 2]
                e2x = v2[ti, 0] - v0[ti, 0]; e2y = v2[ti, 1] - v0[ti, 1]; e2z = v2[ti, 2] - v0[ti, 2]
                gx = e1y * e2z - e1z * e2y; gy = e1z * e2x - e1x * e2z; gz = e1x * e2y - e1y * e2x
                side[i, k] = 1 if gx * d[0] + gy * d[1] + gz * d[2] < 0.0 else -1
    return tri, bu, bv, dist, side


@njit(parallel=True, cache=True, fastmath=True)
def sphere_rays(pos, nrays, seed, v0, v1, v2, bmin, bmax, left, right, start, count, order):
    """Uniform sphere rays from points (light grid samples): directions, hits, barycentrics, side."""
    n = pos.shape[0]
    dirs = np.zeros((nrays, 3))
    sq = int(math.sqrt(nrays))
    for k in range(nrays):
        if k < sq * sq:
            r1 = ((k % sq) + 0.5) / sq; r2 = ((k // sq) + 0.5) / sq
        else:
            r1 = _hash(k, seed); r2 = _hash(k + 3, seed)
        z = 1.0 - 2.0 * r2; s = math.sqrt(max(0.0, 1.0 - z * z)); phi = 6.2831853 * r1
        dirs[k, 0] = s * math.cos(phi); dirs[k, 1] = s * math.sin(phi); dirs[k, 2] = z
    tri = np.full((n, nrays), -1, np.int32)
    bu = np.zeros((n, nrays), np.float32); bv = np.zeros((n, nrays), np.float32)
    side = np.zeros((n, nrays), np.int8)
    for i in prange(n):
        o = np.empty(3); d = np.empty(3)
        for k in range(nrays):
            o[0] = pos[i, 0]; o[1] = pos[i, 1]; o[2] = pos[i, 2]
            d[0] = dirs[k, 0]; d[1] = dirs[k, 1]; d[2] = dirs[k, 2]
            t, ti, u, v = trace(o, d, 1e9, False, v0, v1, v2, bmin, bmax, left, right, start, count, order)
            if ti >= 0:
                tri[i, k] = ti; bu[i, k] = u; bv[i, k] = v
                e1x = v1[ti, 0] - v0[ti, 0]; e1y = v1[ti, 1] - v0[ti, 1]; e1z = v1[ti, 2] - v0[ti, 2]
                e2x = v2[ti, 0] - v0[ti, 0]; e2y = v2[ti, 1] - v0[ti, 1]; e2z = v2[ti, 2] - v0[ti, 2]
                gx = e1y * e2z - e1z * e2y; gy = e1z * e2x - e1x * e2z; gz = e1x * e2y - e1y * e2x
                side[i, k] = 1 if gx * d[0] + gy * d[1] + gz * d[2] < 0.0 else -1
    return dirs, tri, bu, bv, side


@njit(parallel=True, cache=True, fastmath=True)
def visible(p, q, v0, v1, v2, bmin, bmax, left, right, start, count, order):
    """p (n,3) -> q (n,3) unoccluded?"""
    n = p.shape[0]
    out = np.zeros(n, np.bool_)
    for i in prange(n):
        o = np.empty(3); d = np.empty(3)
        dx = q[i, 0] - p[i, 0]; dy = q[i, 1] - p[i, 1]; dz = q[i, 2] - p[i, 2]
        l = math.sqrt(dx * dx + dy * dy + dz * dz)
        if l < 1e-6:
            out[i] = True; continue
        o[0] = p[i, 0]; o[1] = p[i, 1]; o[2] = p[i, 2]; d[0] = dx / l; d[1] = dy / l; d[2] = dz / l
        t, ti, u, v = trace(o, d, l - 0.5, True, v0, v1, v2, bmin, bmax, left, right, start, count, order)
        out[i] = ti < 0
    return out
