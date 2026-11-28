r"""control_doc: the control document = the station document's base + the lifted stock room only (worker C1, 28 Nov 2026).

    python control_doc.py --mode bounce|baked [--out <folder>]

Chosen over "the whole station document + the room" because it builds and bakes fastest (no Arcade, no Terminus in the bake) and the room is
an island: nothing of the Arcade or the Terminus could light it or be seen from its cameras. The settings block (kit dumps, darkness, the
lit vision = light_rules.LIT_VISION, the dark exposure) is the station document's, copied unchanged from its map.json, so the room goes
through exactly the pipeline the station goes through. Writes the document and `control.json` (the lights as transcribed, the prefab's
expand report: substituted and skipped materials, props, collision; the models no dump holds).
"""
import argparse
import copy
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import Map  # noqa: E402
from studio import fixtures as FX  # noqa: E402
import control_room  # noqa: E402

STATION = r'C:\studio-data\sz\film\station'
DATA = r'C:\studio-data\sz\film\control'


def build(mode, station_doc=os.path.join(STATION, 'doc'), base=os.path.join(STATION, 'base')):
    src = json.load(open(os.path.join(station_doc, 'map.json'), encoding='utf-8'))
    m = Map('sz_control_' + mode, title='Control: cp_disco east subway station lifted onto the station base (%s lights)' % mode,
            base={'kind': 'emit', 'path': base}, settings=copy.deepcopy(src['settings']))
    rep = control_room.build(m, mode)
    rep['models_no_dump_holds'] = FX.use_kit(m)
    fl = m.flat()
    rep['prefab_report'] = [r for r in (getattr(fl, 'prefabs', None) or [])]
    return m, rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--mode', choices=('bounce', 'baked'), required=True)
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    out = a.out or os.path.join(DATA, 'doc_' + a.mode)
    m, rep = build(a.mode)
    os.makedirs(out, exist_ok=True)
    m.save(out)
    json.dump(rep, open(os.path.join(out, 'control.json'), 'w', encoding='utf-8'), indent=1, default=str)
    pr = rep['prefab_report'][0] if rep['prefab_report'] else {}
    print(json.dumps({'folder': out, 'summary': m.summary(), 'lights': len(rep['lights']), 'models_no_dump_holds': rep['models_no_dump_holds'],
                      'prefab': {k: pr.get(k) for k in ('render_triangles', 'collision_triangles', 'props', 'props_dropped', 'skipped_materials',
                                                        'substituted_materials', 'cleared_door_triangles', 'derived_floor_triangles', 'sealed_floor_edges')}},
                     indent=1, default=str))


if __name__ == '__main__':
    main()
