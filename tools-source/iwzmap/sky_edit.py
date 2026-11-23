"""The map's own sky and sun (layout.json `lighting.sky_image`, `lighting.sun`), written into the assembled zone before buildzone.

The compiler keeps the template's sun and sky (iwzmap.cpp: sun lights, sky image, sun flare) and writes no sky surface. Two files of the zone folder carry them:

* `maps/cp/<map>.d3dbsp.commap.json`  `primaryLight[]` entries of type 1 (directional): the engine's sun, lit onto models and the gun and multiplied with the
  baked sun visibility of the lightmap. `sun {dir, color, strength}`: `dir` is the direction the light travels (the bake's convention), colour x strength is written to `color`.
* `maps/cp/<map>.d3dbsp.gfxmap`  the stream tag `07 01 <name> 00` of the sky's `skyImage`: `sky_image` replaces the name (the stream is sequential, a different length is fine);
  `sky_surface`: the index of the world surface (material = a sky material) that the engine draws as the sky, written to `skyStartSurfs[0]` with `skySurfCount` 1.
"""
import json
import os
import struct

NULL_ARRAY, FULL_ARRAY = bytes([8, 0]), bytes([8, 1])
SKY_TAG = bytes([7, 1])
TOWARD_SUN = True      # the commap stores the vector from the surface towards the sun (confirmed by the sun patch in the game: Studio port/README, ninth pass)


def _find_sky(buf):
    """-> (offset of the sky struct's skySurfCount, offset of the 07 01 tag) in a gfxmap (the first sky: the array follows the GfxWorld struct)"""
    at = buf.find(SKY_TAG + b'sky_')
    if at < 0:
        raise ValueError('no sky image name in the gfxmap')
    return at


def sky_name(buf):
    at = _find_sky(buf) + 2
    return buf[at:buf.index(b'\0', at)].decode('latin1')


def set_sky_name(buf, name):
    at = _find_sky(buf) + 2
    end = buf.index(b'\0', at)
    return bytes(buf[:at]) + name.encode('latin1') + bytes(buf[end:])


def sun_lights(com):
    return [l for l in com['primaryLight'] if l.get('type') == 1]


def set_sun(com, direction, color, strength=1.0, toward_sun=True):
    """write the directional lights of a commap.json dict; `direction` = the way the light travels; `toward_sun` = the file stores the vector toward the sun (measured, see README)"""
    n = sum(c * c for c in direction) ** 0.5
    d = [c / n for c in direction]
    if toward_sun:
        d = [-c for c in d]
    ls = sun_lights(com)
    for l in ls:
        l['color'] = [float(c) * float(strength) for c in color]
        l['dir'] = d
    return len(ls)


def _worldkit():
    import sys
    wk = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worldkit')
    if wk not in sys.path:
        sys.path.insert(0, wk)
    import iw7_dump
    return iw7_dump


def _repeats(buf, tag):
    """parse the gfxmap with the worldkit reader and return ([(offset of a repeat record's entry index, index)], the entry number a new array at `tag` gets)"""
    D = _worldkit()
    reps, num = [], []
    orig_rep, orig_arr = D.Stream._repeat, D.Stream.array

    def rep(self, what):
        at = self.p
        r = orig_rep(self, what)
        reps.append((at, struct.unpack_from('<I', self.b, at)[0]))
        return r

    def arr(self, elem, expected, what, required=False):
        if self.p == tag:
            num.append(len(self.entries))
        return orig_arr(self, elem, expected, what, required)

    D.Stream._repeat, D.Stream.array = rep, arr
    try:
        D.parse_gfxmap(buf)
    finally:
        D.Stream._repeat, D.Stream.array = orig_rep, orig_arr
    if not num:
        raise ValueError('the sky start surface array was not met while parsing')
    return reps, num[0]


def set_sky_surface(buf, k):
    """the sky draws the world surface `k` (its position in the sorted surface list, which the compiler writes as the identity): skySurfCount 1 and the array
    `08 01 <count> <k>` in place of the compiler's null array `08 00`. The stream numbers its entries (arrays, strings, assets) and a later record repeats one by number:
    the new array takes a number, so every repeat of a later number is raised by one."""
    at = _find_sky(buf)
    if bytes(buf[at - 10:at - 4]) == FULL_ARRAY + struct.pack('<I', 1):
        if struct.unpack_from('<I', buf, at - 4)[0] == k:
            return bytes(buf)                       # already done (a second assembly of the same folder)
        raise ValueError('the world already lists another sky surface')
    tag, st = at - 2, at - 2 - 32
    if bytes(buf[tag:tag + 2]) != NULL_ARRAY:
        raise ValueError('the sky struct is not followed by the start surface array: %r' % bytes(buf[tag - 8:at]))
    reps, num = _repeats(buf, tag)
    out = bytearray(buf)
    for pos, idx in reps:
        if pos > tag and idx >= num:
            struct.pack_into('<I', out, pos, idx + 1)
    head = bytearray(out[st:tag])
    head[0:4] = struct.pack('<i', 1)
    head[8:16] = bytes.fromhex('f8474ce208000000')      # a non-null pointer: the array follows in the stream
    return bytes(out[:st]) + bytes(head) + FULL_ARRAY + struct.pack('<II', 1, k) + bytes(out[tag + 2:])


def sky_surface_index(gfxmap_path):
    """index of the first surface whose material is a sky material (worldkit's reader), None when there is none"""
    import sys
    wk = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'worldkit')
    if wk not in sys.path:
        sys.path.insert(0, wk)
    import iw7_dump
    w = iw7_dump.parse_gfxmap(open(gfxmap_path, 'rb').read())
    for i, m in enumerate(w.surface_materials):
        if m.startswith('w/sky_') or m.startswith('sky_'):
            return i
    return None


def _rewrite(path, data):
    """write through a new file (the zone folder holds hard links into the stock dumps)"""
    if os.path.exists(path):
        os.remove(path)
    with open(path, 'wb') as f:
        f.write(data)


def apply_to_zone(zone_dir, mapname, lighting):
    """lighting: layout.json `lighting`. `sky_image` -> the gfxmap's sky image name; `sun_engine` {dir, color, strength} -> the directional primary lights of the commap.
    -> report dict or None when the layout asks for neither"""
    lighting = lighting or {}
    img, eng = lighting.get('sky_image'), lighting.get('sun_engine')
    if not img and not eng:
        return None
    rep = {}
    base = os.path.join(zone_dir, 'maps', 'cp', mapname + '.d3dbsp')
    if img:
        buf = open(base + '.gfxmap', 'rb').read()
        old = sky_name(buf)
        new = set_sky_name(buf, img) if old != img else buf
        k = sky_surface_index(base + '.gfxmap')
        if k is not None:
            new = set_sky_surface(new, k)
        if new is not buf:
            _rewrite(base + '.gfxmap', new)
        rep['sky_image'] = [old, img]
        rep['sky_surface'] = k
    if eng:
        com = json.load(open(base + '.commap.json', encoding='utf-8'))
        n = set_sun(com, eng['dir'], eng['color'], eng.get('strength', 1.0), toward_sun=TOWARD_SUN)
        _rewrite(base + '.commap.json', json.dumps(com).encode('utf-8'))
        rep['sun_lights'] = n
    return rep
