"""Make a new IW7 particle spot/omni light effect (.iw7VFX, ZoneTool dump format) from a stock light effect.

The template must be a single-emitter light effect (LIGHT_SPOT or LIGHT_OMNI), e.g.
  cp_disco vfx/iw7/levels/cp_rave/vfx_cp_rave_vision_light   (camera-attached light of rave mode)
  cp_disco vfx/iw7/levels/cp_disco/subway_train/vfx_train_front_light_ch   (spot light carried by the train)
The tool patches the light parameters in place and renames the asset (the name is its own string token; every
other reference is by token index, so a longer or shorter name is safe), then writes
  <out root>/particlesystem/<new name>.iw7VFX
which fx_import.py takes as a dump root (`--dump <zone>=<out root>`).

Units: fov = full cone angle in degrees (stored as half angle in radians), radius = particle size x (the light's
falloff radius in world units), color = linear rgb 0..1, brightness = the module's brightness.

usage: make_vfx_light.py <template.iw7VFX> <out root> <new name> [--fov 32] [--inner 12] [--radius 800]
       [--color 1,0.93,0.82] [--brightness 3] [--uv 0] [--shadow 1] [--volumetric 0] [--json report.json]
"""
import argparse, json, math, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vfx_read as V


def find_name_token(d):
    """byte range of the asset name string (token after the ParticleSystemDef array)"""
    r = V.R(d)
    r.array(V.SIZES['system'])
    start = r.p
    t = r.u8(); assert t == 6, 'name token expected'
    assert r.u8() == 1, 'name missing'
    s = r.p
    e = d.index(b'\0', s)
    return start, s, e + 1


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('template'); ap.add_argument('out'); ap.add_argument('name')
    ap.add_argument('--fov', type=float, default=None); ap.add_argument('--inner', type=float, default=None)
    ap.add_argument('--radius', type=float, default=None); ap.add_argument('--radius2', type=float, default=None)
    ap.add_argument('--color', default=None); ap.add_argument('--brightness', type=float, default=None)
    ap.add_argument('--uv', type=float, default=None); ap.add_argument('--shadow', type=int, default=None)
    ap.add_argument('--volumetric', type=int, default=None); ap.add_argument('--near', type=float, default=None)
    ap.add_argument('--tonemap', type=float, default=None)
    ap.add_argument('--soft', type=float, default=None); ap.add_argument('--bias', type=float, default=None)
    ap.add_argument('--area', type=float, default=None)
    ap.add_argument('--json', default='')
    a = ap.parse_args(argv)

    src = V.parse(a.template)
    d = bytearray(open(a.template, 'rb').read())
    lights = list(V.light_states(src))
    if len(src['emitters']) != 1 or len(lights) != 1:
        raise SystemExit('template must be one light emitter (has %d emitters, %d light states)' % (len(src['emitters']), len(lights)))
    em, st = lights[0]
    col = [float(c) for c in a.color.split(',')] if a.color else None
    changes = []
    for g in st['groups']:
        for m in g:
            t = m['type']
            if t == 'INIT_LIGHT_SPOT':
                base = m['data_off'] + 8
                if a.fov is not None:
                    struct.pack_into('<f', d, base + 0, math.radians(a.fov / 2)); changes.append('fovOuter')
                if a.inner is not None:
                    struct.pack_into('<f', d, base + 4, math.radians(a.inner / 2)); changes.append('fovInner')
                if a.brightness is not None:
                    struct.pack_into('<f', d, base + 16, a.brightness); changes.append('brightness')
                if a.uv is not None:
                    struct.pack_into('<f', d, base + 24, a.uv); changes.append('intensityUV')
                if a.near is not None:
                    struct.pack_into('<f', d, base + 32, a.near); changes.append('shadowNearPlane')
                if a.tonemap is not None:
                    struct.pack_into('<f', d, base + 36, a.tonemap); changes.append('toneMappingScaleFactor')
                for off, v, nm in ((40, a.soft, 'shadowSoftness'), (44, a.bias, 'shadowBias'), (48, a.area, 'shadowArea')):
                    if v is not None:
                        struct.pack_into('<f', d, base + off, v); changes.append(nm)
                if a.volumetric is not None:
                    d[base + 52] = 0 if a.volumetric else 1; changes.append('disableVolumetric')
                if a.shadow is not None:
                    d[base + 53] = 0 if a.shadow else 1; changes.append('disableShadowMap')
            elif t == 'INIT_LIGHT_OMNI':
                if a.brightness is not None:
                    pass
            elif t == 'INIT_ATTRIBUTES':
                o = m['attr_off']
                for k in (0, 4):     # sizeMin, sizeMax (x = radius, y = second size term)
                    if a.radius is not None:
                        struct.pack_into('<f', d, o + 4 * k, a.radius)
                    if a.radius2 is not None:
                        struct.pack_into('<f', d, o + 4 * k + 4, a.radius2)
                for k in (8, 12):    # colorMin, colorMax
                    if col:
                        struct.pack_into('<3f', d, o + 4 * k, *col)
                if a.radius is not None or col:
                    changes.append('attributes')
            elif t == 'COLOR_LERP' and col:
                o = m['lerp_off']
                struct.pack_into('<3f', d, o, *col); struct.pack_into('<3f', d, o + 16, *col); changes.append('colorLerp')
            elif t == 'SIZE_GRAPH' and (a.radius is not None or a.radius2 is not None):
                o = m['sg_off']
                for k in (0, 4):
                    if a.radius is not None:
                        struct.pack_into('<f', d, o + 4 * k, a.radius)
                    if a.radius2 is not None:
                        struct.pack_into('<f', d, o + 4 * k + 4, a.radius2)
                hdr = m['curve_hdr']
                if a.radius is not None:
                    struct.pack_into('<f', d, hdr + 12, a.radius)
                if a.radius2 is not None:
                    struct.pack_into('<f', d, hdr + 16 + 12, a.radius2)
                changes.append('sizeGraph')
            elif t == 'COLOR_GRAPH' and col:
                raise SystemExit('template has a COLOR_GRAPH: colour curves are not patched by this tool')
    tok, s, e = find_name_token(bytes(d))
    new = bytes(d[:s]) + a.name.encode('latin1') + b'\0' + bytes(d[e:])
    path = os.path.join(a.out, 'particlesystem', a.name.replace('/', os.sep) + '.iw7VFX')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, 'wb').write(new)
    chk = V.parse(path)
    assert chk['name'] == a.name and chk['consumed'] == chk['size'], 're-parse failed'
    rep = {'template': a.template, 'name': a.name, 'path': path, 'changes': changes,
           'light': [{k: v for k, v in m.items() if k not in ('off', 'curves')} for g in list(V.light_states(chk))[0][1]['groups'] for m in g]}
    print(json.dumps({'name': a.name, 'path': path, 'changes': changes}))
    if a.json:
        json.dump(rep, open(a.json, 'w'), indent=1)


if __name__ == '__main__':
    main()
