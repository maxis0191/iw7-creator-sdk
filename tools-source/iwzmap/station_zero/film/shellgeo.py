"""shellgeo: authored triangle meshes for the Arcade shell (inches, z up, right-hand normals face out).

Each function returns (tris, uvs): tris [[p0, p1, p2], ...], uvs [[[u, v] x3], ...] in repeats of the image (one repeat = UV units).
"""
import math

UV = 32.0


def _rot_to(d):
    """3x3 matrix taking local +z to the unit vector d (columns: local x, y, z in world)"""
    dx, dy, dz = d
    n = math.sqrt(dx * dx + dy * dy + dz * dz)
    z = (dx / n, dy / n, dz / n)
    a = (0.0, 0.0, 1.0) if abs(z[2]) < 0.9 else (1.0, 0.0, 0.0)
    x = _norm(_cross(a, z))
    y = _cross(z, x)
    return x, y, z


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(v):
    n = math.sqrt(sum(c * c for c in v)) or 1.0
    return tuple(c / n for c in v)


def _xf(p, frame, origin):
    x, y, z = frame
    return [round(origin[i] + p[0] * x[i] + p[1] * y[i] + p[2] * z[i], 3) for i in range(3)]


def cylinder(a, b, r, segs=16, caps=True):
    """a closed cylinder from point a to point b"""
    d = [b[i] - a[i] for i in range(3)]
    h = math.sqrt(sum(c * c for c in d))
    fr = _rot_to(d)
    tris, uvs = [], []
    circ = 2 * math.pi * r
    for i in range(segs):
        a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
        p00 = (r * math.cos(a0), r * math.sin(a0), 0.0)
        p10 = (r * math.cos(a1), r * math.sin(a1), 0.0)
        p01 = (p00[0], p00[1], h)
        p11 = (p10[0], p10[1], h)
        u0, u1 = circ * i / segs / UV, circ * (i + 1) / segs / UV
        v1 = h / UV
        w = [_xf(p, fr, a) for p in (p00, p10, p11, p01)]
        tris += [[w[0], w[1], w[2]], [w[0], w[2], w[3]]]
        uvs += [[[u0, 0], [u1, 0], [u1, v1]], [[u0, 0], [u1, v1], [u0, v1]]]
        if caps:
            c0, c1 = _xf((0, 0, 0), fr, a), _xf((0, 0, h), fr, a)
            tris += [[c1, w[3], w[2]], [c0, w[1], w[0]]]
            cu = lambda p: [p[0] / UV, p[1] / UV]
            uvs += [[[0, 0], cu(p01), cu(p11)], [[0, 0], cu(p10), cu(p00)]]
    return tris, uvs


def torus(c, normal, R, r, segs=20, tube=6):
    """a ring of radius R and tube radius r centred on c, its axis along `normal`"""
    fr = _rot_to(normal)
    tris, uvs = [], []

    def pt(i, j):
        a = 2 * math.pi * i / segs
        b = 2 * math.pi * j / tube
        rr = R + r * math.cos(b)
        return _xf((rr * math.cos(a), rr * math.sin(a), r * math.sin(b)), fr, c)
    for i in range(segs):
        for j in range(tube):
            p00, p10, p11, p01 = pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)
            u0, u1 = i / segs * 4, (i + 1) / segs * 4
            v0, v1 = j / tube, (j + 1) / tube
            tris += [[p00, p10, p11], [p00, p11, p01]]
            uvs += [[[u0, v0], [u1, v0], [u1, v1]], [[u0, v0], [u1, v1], [u0, v1]]]
    return tris, uvs


def ribbon(points, width, z=0.15):
    """a flat strip on the floor along a polyline (a cable lying on the floor), facing up"""
    tris, uvs = [], []
    run = 0.0
    for k in range(len(points) - 1):
        (x0, y0), (x1, y1) = points[k], points[k + 1]
        L = math.hypot(x1 - x0, y1 - y0) or 1.0
        nx, ny = -(y1 - y0) / L * width / 2, (x1 - x0) / L * width / 2
        a = [x0 + nx, y0 + ny, z]
        b = [x0 - nx, y0 - ny, z]
        c = [x1 - nx, y1 - ny, z]
        d = [x1 + nx, y1 + ny, z]
        u0, u1 = run / UV, (run + L) / UV
        run += L
        tris += [[b, c, d], [b, d, a]]
        uvs += [[[u0, 0], [u1, 0], [u1, 1]], [[u0, 0], [u1, 1], [u0, 1]]]
    return tris, uvs


def merge(*parts):
    tris, uvs = [], []
    for t, u in parts:
        tris += t
        uvs += u
    return tris, uvs


def yaw_points(tris, origin, yaw):
    """rotate local tris (around z) by yaw degrees and move them to origin"""
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    out = []
    for t in tris:
        out.append([[round(origin[0] + p[0] * c - p[1] * s, 3), round(origin[1] + p[0] * s + p[1] * c, 3), round(origin[2] + p[2], 3)] for p in t])
    return out
