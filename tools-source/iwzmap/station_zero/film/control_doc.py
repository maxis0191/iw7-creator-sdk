r"""control_doc: the control document = the whole station document + the lifted stock room on an island (worker C1, 28 Nov 2026).

    python control_doc.py --mode bounce|baked [--out <folder>]

The base + the room alone was tried first (fastest bake), but `live start` refuses it: the base by itself fails the build's walk gate
(a drop-only floor where the Arcade layers stand). So the whole station document is loaded and the room added; the room stands alone
in the empty gap between the Terminus and the base (control_room.OFFSET): nothing of the Arcade or the Terminus is seen from its cameras or reaches it with light. The settings block
(kit dumps, darkness, the lit vision = light_rules.LIT_VISION, the dark exposure) is the station document's, unchanged, so the room goes
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


def build(mode, station_doc=os.path.join(STATION, 'doc'), base=os.path.join(STATION, 'base'), whole=True, probe_room=True):
    if whole:
        # the whole station document + the room: the base alone fails the build's own walk gate (its Arcade region is a drop-only floor that
        # the Arcade layers replace), so `live start` refuses base + room (first session, 28 Nov: "gate check failed")
        m = Map.load(station_doc)
        m.path = None
        m.name, m.title = 'sz_control_' + mode, 'Control: the station document + cp_disco east subway station lifted on an island (%s lights)' % mode
    else:
        src = json.load(open(os.path.join(station_doc, 'map.json'), encoding='utf-8'))
        m = Map('sz_control_' + mode, title='Control: cp_disco east subway station lifted onto the station base (%s lights)' % mode,
                base={'kind': 'emit', 'path': base}, settings=copy.deepcopy(src['settings']))
        # the station's kit model list names the Arcade's and the Terminus's models, which this document does not place: dropped, so that
        # use_kit below writes only the room's (the build's assemble_key passes the list on one command line: TOOL-FAULTS C1-4)
        m.settings['build']['kit'].pop('models', None)
    rep = control_room.build(m, mode, probe_room=probe_room)
    rep['models_no_dump_holds'] = FX.use_kit(m)
    fl = m.flat()
    rep['prefab_report'] = [r for r in (getattr(fl, 'prefabs', None) or [])]
    return m, rep


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--mode', choices=('bounce', 'baked'), required=True)
    ap.add_argument('--out')
    ap.add_argument('--base-only', action='store_true', help='the station base + the room (no Arcade, no Terminus)')
    ap.add_argument('--no-probe-room', action='store_true', help='C1's documents: the room in no probe room (R2 E1 control)')
    a = ap.parse_args(argv)
    out = a.out or os.path.join(DATA, 'doc_' + a.mode)
    m, rep = build(a.mode, whole=not a.base_only, probe_room=not a.no_probe_room)
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
