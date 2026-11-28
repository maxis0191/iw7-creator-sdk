r"""station_doc: the ONE document of the Station Zero rebuild (integrator I1, 28 Nov 2026).

    the base without Pack-a-Punch, lit first (B1; regenerated from this SDK: C:\studio-data\sz\film\station\regen.sh <base> IWZ_LIT_FIRST=1)
  + the Underpass Arcade: the shell (arcade_shell.py, L1's key lights and lit vision) and the goods of its four shops (goods_<shop>.py)
  + the Terminus (terminus.build: zone island, the machine on its post, the arrival marker, its vision variant `term` on cp_frontend)

One Map, one settings block: the shell's recipe (allbaked2: kit dumps, darkness arguments with the dark exposure -5.5) with L1's lit keys
(light_rules.LIT_VISION) as the map's lit vision, the Terminus variant added by terminus.vision. The round-19 layers of B1's document (the old
Arcade, 1,808 of its 1,867 dressing objects inside the Arcade box) are NOT carried: the new Arcade replaces them.

    set STUDIO_ROOT=C:\studio
    python station_doc.py [--out <doc>] [--base <emit>] [--look]

--look also writes <doc>_look: the same document with the lit vision = the Terminus keys, for the Terminus room's own frames only (the camera of
`live shot` is no rider, so it never gets the rider's vision; T1-TERMINUS "Changes after the first frames").
"""
import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DATA = r'C:\studio-data\sz\film\station'
os.environ.setdefault('SZ_TERMINUS_DERIVED', os.path.join(DATA, 'art'))      # the Terminus's derived pictures (floor paper, reel, ink) of this document
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
import arcade_doc  # noqa: E402
import light_rules  # noqa: E402
import terminus  # noqa: E402
from studio import fixtures as FX  # noqa: E402

BASE = os.path.join(DATA, 'base')
OUT = os.path.join(DATA, 'doc')
NAME = 'sz_station'
DARK_EXPOSURE = '-5.5'


def _kv(arg):
    return dict(x.split('=', 1) for x in arg.split(';') if x)


def settings_report(m):
    """what the one settings block says, checked: the dark exposure, the lit keys, the Terminus variant and its alias"""
    a = m.settings['build']['darkness']['args']
    dark, lit = _kv(a[a.index('--dark') + 1]), _kv(a[a.index('--lit') + 1])
    variants = dict(v.split(':', 1) for v in a[a.index('--variants') + 1].split('|') if v)
    alias = dict(x.split('=', 1) for x in a[a.index('--alias') + 1].split(',') if x)
    out = {'dark_exposure': dark.get('tonemapExposureAdjust'),
           'lit_vision_is_light_rules': all(lit.get(k) == v for k, v in light_rules.LIT_VISION.items()),
           'term_variant': variants.get(terminus.VISION_VARIANT) == terminus.VISION_KEYS,
           'term_alias': alias.get(terminus.VISION_NAME) == terminus.VISION_VARIANT,
           'kit_models': len(m.settings['build']['kit'].get('models') or [])}
    bad = [k for k, v in out.items() if v is False] + ([] if out['dark_exposure'] == DARK_EXPOSURE else ['dark_exposure'])
    out['ok'] = not bad
    out['bad'] = bad
    return out


def build(base=BASE, name=NAME):
    m, done, missing = arcade_doc.build(name=name, base=base)      # the shell's recipe is the map's settings block
    if missing:
        raise SystemExit('station_doc: goods modules missing: %s' % ', '.join(missing))
    layers = terminus.build(m)                                      # its layers and its vision variant
    FX.use_kit(m)                                                   # one kit list: the models of both sections
    m.name, m.title = name, 'Station Zero: the base without Pack-a-Punch + the Underpass Arcade + the Terminus (I1)'
    return m, {'goods': done, 'terminus_layers': layers}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--out', default=OUT)
    ap.add_argument('--base', default=BASE)
    ap.add_argument('--look', action='store_true')
    a = ap.parse_args(argv)
    m, rep = build(a.base)
    st = settings_report(m)
    if not st['ok']:
        raise SystemExit('station_doc: settings block wrong: %s' % st)
    os.makedirs(a.out, exist_ok=True)
    m.save(a.out)
    out = {'folder': a.out, 'base': a.base, 'summary': m.summary(), 'settings': st, **rep}
    if a.look:
        terminus.look_copy(m)
        lk = a.out.rstrip('\\/') + '_look'
        os.makedirs(lk, exist_ok=True)
        m.path = None
        m.save(lk)
        out['look'] = lk
    print(json.dumps(out, indent=1, default=str))


if __name__ == '__main__':
    main()
