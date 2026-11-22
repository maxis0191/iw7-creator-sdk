"""Shared paths and helpers of the asset library (pure Python + numpy, no bpy).

The library lives outside the repository: <runtime>/iwz-blend/library/{catalog.json, sheets/, blend/, prep/}.
Loaders are the preview's (preview/iwz_assets.py): dump index, material -> colour image, image decode, xmodel LOD0.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'preview'))
sys.path.insert(0, os.path.join(HERE, '..', 'catalog'))
import iwz_assets as A  # noqa: E402
import iwzgroups  # noqa: E402

EXCLUDED_GROUPS = iwzgroups.EXCLUDED
SHEET_GROUPS = ['architecture', 'structural', 'transit', 'retail', 'utilities', 'debris', 'furniture', 'vegetation',
                'vehicles', 'misc']


def runtime():
    return A.runtime()


def library_root():
    return os.environ.get('IWZ_LIBRARY') or os.path.join(runtime(), 'iwz-blend', 'library')


def catalog_path():
    return os.path.join(library_root(), 'catalog.json')


def load_catalog(path=None):
    return json.load(open(path or catalog_path()))


def library_models(cat, zones=None, groups=None, only_resolving=False):
    """Rows kept in the library: not weapon / character / vfx / attachment. zones: any of the model's zones."""
    out = []
    for m in cat['models']:
        if m['group'] in EXCLUDED_GROUPS:
            continue
        if groups and m['group'] not in groups:
            continue
        if zones and not set(zones) & set(m['zones']):
            continue
        if only_resolving and not m['resolves']:
            continue
        out.append(m)
    return out


def home_zone(m):
    """The zone a model is filed under (sheets, .blend files): the first of its zones in catalogue order, which
    is the build order (cp_zmb, cp_disco, cp_final, global_cp, ...)."""
    return m['zones'][0]


def dump_roots():
    """Every dump root holding models: the stock map dumps and the kit dumps, shared techset dumps last."""
    rt = runtime()
    ref = os.path.join(rt, 'iwz-map-ref-a', 'dump')
    kit = os.path.join(rt, 'iwz-stage2', 'kitimport', 'ztwork', 'dump')
    roots = []
    for z in ('cp_zmb', 'patch_cp_zmb', 'techsets_cp_zmb', 'global_cp', 'techsets_global_cp', 'global', 'techsets_global',
              'common_core_mp', 'techsets_common_core_mp', 'global_core_mp', 'techsets_global_core_mp', 'mp_frontend',
              'patch_cp_frontend'):
        roots.append(os.path.join(ref, z))
    for z in ('cp_disco', 'techsets_cp_disco', 'cp_final', 'techsets_cp_final'):
        roots.append(os.path.join(kit, z))
    ch = os.path.join(rt, 'chars58', 'ztwork', 'dump')     # full dumps of cp_rave and cp_town (with materials)
    for z in ('cp_rave', 'techsets_cp_rave', 'patch_cp_rave', 'cp_town', 'techsets_cp_town', 'patch_cp_town'):
        roots.append(os.path.join(ch, z))
    return [r for r in roots if os.path.isdir(r)]


_index = None


def dump_index():
    global _index
    if _index is None:
        _index = A.DumpIndex(dump_roots())
    return _index


def size_text(m):
    """Bounds size in inches, rounded: '96 x 24 x 40'."""
    return ' x '.join('%d' % round(v) for v in m['size'])


def safe(name):
    return name.replace('/', '_').replace('\\', '_').replace('*', '_')
