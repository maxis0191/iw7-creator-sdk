r"""bake_all_dumps: `studio bake <doc>` with the baker told where EVERY placed model's bounds are (worker C1, 28 Nov 2026; pipeline check b).

    python bake_all_dumps.py <doc> [--final|--draft] [--keep <folder>]

Found: Studio hands the SDK baker one dump root for prop bounds, the template zone's (studio/bake.py `run`: job['dumps'] = [template_dump()]).
The baker's prop shadows (SDK bake/occluders.py) box only the static models whose xmodel it finds there: on the station document 607 of 894
static models (147 models: every model of another zone, cp_disco, cp_town, cp_final, cp_rave, ours) are `unknown` and throw no baked shadow.
This driver is the variant that tells the baker the document's own kit dump roots too (settings.build.kit.dumps of the document and of its
base's build.json, `{runtime}` resolved): `studio.bake.recipe_job` is wrapped so the job's `dumps` = template root + kit roots. Nothing of
Studio or of the SDK is edited; the bake is remembered for the document as any `studio bake` (the cache key does not include the dumps).
"""
import json
import os
import sys

sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
from studio import Map  # noqa: E402
from studio import bake as BK  # noqa: E402

RUNTIME = os.environ.get('IWZ_RUNTIME') or os.path.join(os.path.expanduser('~'), 'Documents', 'IW7-Runtime')


def kit_roots(doc):
    m = json.load(open(os.path.join(doc, 'map.json'), encoding='utf-8'))
    kits = [((m.get('settings') or {}).get('build') or {}).get('kit') or {}]
    base = (m.get('base') or {}).get('path')
    if base and os.path.isfile(os.path.join(base, 'build.json')):
        kits.append(json.load(open(os.path.join(base, 'build.json'), encoding='utf-8')).get('kit') or {})
    out = []
    for k in kits:
        for zone, roots in (k.get('dumps') or {}).items():
            for r in roots:
                r = os.path.normpath(r.replace('{runtime}', RUNTIME))
                if os.path.isdir(r) and r.lower() not in [x.lower() for x in out]:
                    out.append(r)
    return out


def main(argv):
    doc = argv[0]
    setting = 'final' if '--final' in argv else 'draft'
    keep = argv[argv.index('--keep') + 1] if '--keep' in argv else None
    extra = kit_roots(doc)
    tmpl = BK.template_dump()
    roots = ([tmpl] if tmpl else []) + extra
    real = BK.recipe_job

    def recipe_job(emit, st):
        j = real(emit, st)
        j['dumps'] = roots
        return j
    BK.recipe_job = recipe_job
    m = Map.load(doc)
    r = BK.bake_document(m, None, setting, keep=keep)
    r['dump_roots'] = roots
    print(json.dumps(r, indent=1, default=str))


if __name__ == '__main__':
    main(sys.argv[1:])
