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

SKY_TAG = b'\x07\x01'


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
        if old != img:
            _rewrite(base + '.gfxmap', set_sky_name(buf, img))
        rep['sky_image'] = [old, img]
    if eng:
        com = json.load(open(base + '.commap.json', encoding='utf-8'))
        n = set_sun(com, eng['dir'], eng['color'], eng.get('strength', 1.0), toward_sun=TOWARD_SUN)
        _rewrite(base + '.commap.json', json.dumps(com).encode('utf-8'))
        rep['sun_lights'] = n
    return rep
