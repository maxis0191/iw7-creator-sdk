"""The build recipe (build.json) of Station Zero v2, written from the SAME switches the generator ran with.

recipe(env, emit_dir) -> dict      the recipe of the map (contract: compile/RECIPE.md of the Studio build, version 1)
write(env, emit_dir) -> path       writes <emit>/build.json (indent 1, fixed key order, LF, deterministic)

Every number and string of the recipe is in the table below, each with the build-g.ps1 / build-sz2.ps1 line it comes from. Nothing here
changes what build-g or build-sz2 builds (they ignore build.json); the Studio build reads it.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the table: values and where they come from ---------------------------------------------------------------------------------------
# paths below are written with the roots {runtime} {sdk} {dumps} {emit} (RECIPE.md rule 3); {runtime} = machine.ps1 Runtime
RT = '{runtime}/iwz-stage2'                                    # build-g.ps1 line 9: $RT = Runtime 'iwz-stage2'
KD = RT + '/kitimport/ztwork/dump'                             # build-g.ps1 line 151: $KD = "$RT\kitimport\ztwork\dump"
FXD = RT + '/fx/ztwork/dump/cp_disco'                          # build-g.ps1 line 169: $FD
LD2 = RT + '/level/ztwork/dump/techsets_cp_disco'              # build-g.ps1 line 171 (the level work folder dump, techsets_cp_disco)
COMPILER_EXE = 'pinned'                                        # build-g.ps1 line 15 / machine.ps1 MapCompiler: the one pinned compiler
GAP_REGIONS = ['portal:a_tunnel_platform_b', 'portal:d_hall_stair_a',     # build-sz2.ps1 line 91 (volume_check.py --gap-regions)
               'portal:d_platform_tunnel', 'portal:d_platform_corridor']
LOCALIZE_EXTRA = 'sdk'                                         # build-sz2.ps1 line 191 (perks/strings.json as it is)
ART = False                                                    # build-sz2.ps1 builds no <map>_art.ff
ARENA = '{runtime}/iwz-release/cp_iwz-rc1/usermaps/cp_iwz/cp_iwz.arena'   # g27r_build.json (RC4 manifest): the release's arena file
# train sets: build-g.ps1 lines 37 to 39 ($TrainSet -> $TP); the first folder holds collision\iwz_t7e_subway_car_a.json (line 41)
TRAIN_SETS = {'g27': ('banzai_v3', 'kit_v4', 'genset', 'props_v4'),
              'g27d': ('banzai_v4', 'kit_v5', 'genset_v5', 'props_v4'),
              'g27e': ('banzai_v5', 'kit_v6', 'genset_v6', 'props_v4')}
KIT_DUMPS = {'cp_disco': [KD + '/cp_disco', KD + '/techsets_cp_disco'],     # build-g.ps1 line 152 ($A['KitDumps'])
             'cp_final': [KD + '/cp_final', KD + '/techsets_cp_final']}
KIT_PLACED_FROM = ['train']                                    # build-g.ps1 lines 154 to 156 (-Kit -Train: placed port models)
TRAIN_DUMP_NAME = 'train'                                      # build-g.ps1 line 157 ("train=...")
FX_NCS = '{dumps}/cp_zmb/netconststrings/ncs_efx_level.json'   # build-g.ps1 line 173 ($ncs)
FX_CATALOG = '{sdk}/fx/fx_catalog.json'                        # build-g.ps1 line 178 ($S\fx\fx_catalog.json)
FX_VARIANT_ZONE = 'iwzv'                                       # build-g.ps1 line 183 ("iwzv=$VR;...")
FX_VARIANT_TECHSETS = RT + '/fx/techsets_all.txt'              # build-g.ps1 line 180 (fx_variant.py --techsets)
FX_VARIANT_ROOTS = [FXD, KD + '/cp_disco', LD2, '{dumps}/cp_zmb', '{dumps}/techsets_cp_zmb', '{dumps}/techsets_global_cp',
                    '{dumps}/techsets_common_cp', '{dumps}/techsets_global', '{dumps}/techsets_common_mp',
                    '{dumps}/techsets_global_mp']              # build-g.ps1 line 177 ($vroots)
FX_DUMPS = {'cp_disco': [FXD, KD + '/cp_disco', LD2]}          # build-g.ps1 line 185 ($fxd)
AUDIO_BANK = RT + '/audio/build/src15'                         # build-g.ps1 line 47 (AudioBank)
AUDIO_MODELS = RT + '/audio/build/src'                         # build-g.ps1 line 48 (AudioModels)
AUDIO_LAYOUT_SPEC = '{sdk}/audio/station_zero_audio_layout.json'   # build-sz2.ps1 line 144 (audio_layout.py --spec)
AUDIO_BANK_SPEC = '{sdk}/audio/station_zero_audio.json'        # build-sz2.ps1 line 144 (audio_layout.py --bank)
DARK_ZONE_FILL = ('maint_corridor:3.5:0.35:-40,service_tunnel:3.5:0.35:-40,stair_b:3.5:0.35:-40,'
                  'platform_b:3.5:0.35:-40')                   # build-g.ps1 line 1 (default of $DarkZoneFillSpec)
DARK_LIGHTS = {'ambient': 0.025, 'scale': 840, 'radius_scale': 1.8, 'cue_scale': 0.35}   # build-g.ps1 line 89 (dark_build.py --ambient --scale --radius-scale --cue-scale)
DARK_VFX_SOURCE = FXD + '/particlesystem/vfx/iw7/levels/cp_disco/subway_train/vfx_train_front_light_ch.iw7VFX'   # build-g.ps1 line 202 ($TL)
DARK_VFX_DEFAULTS = {'color': [1, 0.92, 0.8], 'near': 8, 'life': 100000}   # build-g.ps1 line 210 (--color 1,0.92,0.80 --near 8 --life 100000)
# (name, fov, inner, brightness, shadow, radius): build-g.ps1 lines 204 to 209
DARK_VFX_EFFECTS = [('vfx/iwz/vfx_iwz_flashlight_world', 40, 2, 3.5, 1, 900), ('vfx/iwz/vfx_iwz_flashlight_world_b', 40, 2, 3.5, 1, 900),
                    ('vfx/iwz/vfx_iwz_flashlight_world_c', 40, 2, 3.5, 1, 900), ('vfx/iwz/vfx_iwz_flashlight_world_d', 40, 2, 3.5, 1, 900),
                    ('vfx/iwz/vfx_iwz_flashlight_world_e', 40, 2, 3.5, 1, 900), ('vfx/iwz/vfx_iwz_flashlight_world_f', 40, 2, 3.5, 1, 900),
                    ('vfx/iwz/vfx_iwz_flashlight_lit', 40, 2, 1.05, 1, 900), ('vfx/iwz/vfx_iwz_flashlight_halo', 64, 0, 0.88, 0, 700),
                    ('vfx/iwz/vfx_iwz_flashlight_halo_lit', 64, 0, 0.26, 0, 700)]
LIT_K = ('fogMaxOpacity=0.03;volumetricSpotBrightness=0;volumetricAmbientBrightness=0;veilStrength=0;'
         'tonemapAdaptSpeed=0.3')                              # build-g.ps1 line 218 ($litK)
DARK_POWER = {'flag': 'power_on', 'interaction': 'generator'}     # Studio's `live power on|off` and `live shot --power` (compile/RECIPE.md, darkness.power)
DARK_ARGS = ['--dark', 'tonemapAuto=0;tonemapAdaptSpeed=1;tonemapExposureAdjust=-3',            # build-g.ps1 line 228 ($A['DarkArgs'])
             '--lit', LIT_K + ';tonemapAutoExposureAdjust=-2.5',                                # line 221 ($litShip)
             '--variants', ('fxa:%s;tonemapAuto=0;tonemapExposureAdjust=-1.5|fxb:%s;tonemapAuto=0;tonemapExposureAdjust=-2|'
                            'aua:%s;tonemapAutoExposureAdjust=-2|aub:%s;tonemapAutoExposureAdjust=-3') % ((LIT_K,) * 4),   # line 227 ($litV)
             '--alias', 'cp_zmb_int_triton_main=fxa,cp_zmb_int_triton_ride=fxb,cp_zmb_ghost_path=aua,cp_zmb_alien=aub']   # line 228
BAKE = {'rays': 256, 'bounces': 3, 'denoise': 1}               # build-g.ps1 line 1 (-Rays 256); RECIPE.md bake (bounces: the document's or 3)
# ---------------------------------------------------------------------------------------------------------------------------------------


def _documents():
    """machine.ps1: [Environment]::GetFolderPath('MyDocuments'); the home folder's Documents where that is not available."""
    try:
        import ctypes
        from ctypes import wintypes
        buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buf) == 0 and buf.value:     # CSIDL_PERSONAL
            return buf.value
    except Exception:
        pass
    return os.path.join(os.path.expanduser('~'), 'Documents')


def _fwd(p):
    return str(p).replace('\\', '/')


def _roots(env):
    """[(token, folder)] longest folder first: the roots a value can be written with (machine.ps1 Runtime / TemplateDump)."""
    runtime = _fwd(env.get('IWZ_RUNTIME') or os.path.join(_documents(), 'IW7-Runtime')).rstrip('/')
    dumps = _fwd(env.get('IWZ_TEMPLATE_DUMP') or runtime + '/iwz-map-ref-a/dump').rstrip('/')
    sdk = _fwd(HERE).rstrip('/')
    return sorted([('{runtime}', runtime), ('{sdk}', sdk), ('{dumps}', dumps)], key=lambda r: -len(r[1]))


def _root(path, roots):
    """A path with a root token ({runtime} ...) when it lies under a known root; else absolute with forward slashes."""
    p = _fwd(path)
    if p.startswith('{'):
        return p
    for token, folder in roots:
        if p.lower() == folder.lower():
            return token
        if p.lower().startswith(folder.lower() + '/'):
            return token + p[len(folder):]
    return p


def _flag(env, name):
    return str(env.get(name, '')).strip() == '1'


def _train_dumps(env, roots):
    """The four port folders of the train set: <port root>/<folder>, the port root read from IWZ_TRAIN_CAR_BOXES
    (<port root>/<banzai_vN>/collision/<file>.json); the set is IWZ_TRAIN_SET, else the one whose banzai folder the path names."""
    boxes = _root(env.get('IWZ_TRAIN_CAR_BOXES', ''), roots)
    parts = boxes.split('/')
    if len(parts) < 4 or parts[-2] != 'collision':
        raise ValueError('IWZ_TRAIN_CAR_BOXES is not <port root>/<banzai>/collision/<file>: %r' % boxes)
    banzai, port = parts[-3], '/'.join(parts[:-3])
    name = (env.get('IWZ_TRAIN_SET') or '').strip()
    if not name:
        named = [k for k, v in TRAIN_SETS.items() if v[0] == banzai]
        if len(named) != 1:
            raise ValueError('train set: no IWZ_TRAIN_SET and no set has the folder %r' % banzai)
        name = named[0]
    if name not in TRAIN_SETS:
        raise ValueError('IWZ_TRAIN_SET %r is not one of %s' % (name, ', '.join(sorted(TRAIN_SETS))))
    if TRAIN_SETS[name][0] != banzai:
        raise ValueError('IWZ_TRAIN_SET %s has the folder %s but IWZ_TRAIN_CAR_BOXES names %s' % (name, TRAIN_SETS[name][0], banzai))
    return [port + '/' + f for f in TRAIN_SETS[name]]


def _material_map(text):
    out = {}
    for kv in str(text or '').split(';'):
        if '=' in kv:
            k, v = kv.split('=', 1)
            out[k.strip()] = v.strip()
    return out


def recipe(env, emit_dir):
    """The recipe of the map the generator wrote into emit_dir with the switches in env (the same mapping as os.environ)."""
    roots = _roots(env)
    r = {'version': 1}
    compiler_env = {}
    if env.get('IWZ_PROBES'):
        compiler_env['IWZ_PROBES'] = str(env['IWZ_PROBES'])
        if env.get('IWZ_PROBES_SCALE'):
            compiler_env['IWZ_PROBES_SCALE'] = str(env['IWZ_PROBES_SCALE'])
    r['compiler'] = {'exe': COMPILER_EXE}
    if compiler_env:
        r['compiler']['env'] = compiler_env
    r['submodels'] = {'keep': True, 'nav_obstacles': _flag(env, 'IWZ_NAV_OBSTACLES'), 'gap_regions': list(GAP_REGIONS)}
    if _flag(env, 'IWZ_KIT'):
        kit = {'dumps': {k: list(v) for k, v in KIT_DUMPS.items()}, 'runtime_csv': [], 'layout_models': True}
        if _flag(env, 'IWZ_TRAIN'):
            kit['dumps'][TRAIN_DUMP_NAME] = _train_dumps(env, roots)
            kit['placed_from'] = list(KIT_PLACED_FROM)
        kit['material_map'] = _material_map(env.get('IWZ_KIT_MATERIAL_MAP'))
        r['kit'] = kit
    if env.get('IWZ_FX_TXT'):
        r['fx'] = {'place': _root(env['IWZ_FX_TXT'], roots), 'ncs': FX_NCS,
                   'variant': {'catalog': FX_CATALOG, 'roots': list(FX_VARIANT_ROOTS), 'techsets': FX_VARIANT_TECHSETS, 'zone': FX_VARIANT_ZONE},
                   'dumps': {k: list(v) for k, v in FX_DUMPS.items()}, 'ncs_skip': []}
    if _flag(env, 'IWZ_AUDIO'):
        r['audio'] = {'bank': AUDIO_BANK, 'models': AUDIO_MODELS, 'layout_spec': AUDIO_LAYOUT_SPEC, 'bank_spec': AUDIO_BANK_SPEC}
    dark = _flag(env, 'IWZ_DARK')
    if dark:
        lights = dict(DARK_LIGHTS)
        zf = str(env.get('IWZ_DARK_ZONE_FILL', '')).strip()
        if zf == '1':
            lights['zone_fill'] = DARK_ZONE_FILL
        elif zf and zf != '0':
            lights['zone_fill'] = zf
        effects = [{'name': n, 'fov': fov, 'inner': inner, 'brightness': b, 'shadow': sh, 'radius': rad}
                   for n, fov, inner, b, sh, rad in DARK_VFX_EFFECTS]
        vfx = {'source': DARK_VFX_SOURCE}
        vfx.update({k: (list(v) if isinstance(v, list) else v) for k, v in DARK_VFX_DEFAULTS.items()})
        vfx['effects'] = effects
        r['darkness'] = {'lights': lights, 'vfx': vfx, 'args': list(DARK_ARGS),
                         'power': dict(DARK_POWER)}     # how a session or a plan switches the power: the level flag and the interaction that sets it (cp_iwz_darkness.gsc)
    r['perks'] = {'p1': _flag(env, 'IWZ_P1')}
    r['bake'] = dict({'lights': 'dark' if dark else 'document'}, **BAKE)
    r['arena'] = ARENA
    r['localize'] = {'extra': LOCALIZE_EXTRA}
    r['art'] = ART
    genv = {k: _root(v, roots) for k, v in sorted(env.items()) if k.startswith('IWZ_') or k == 'PYTHONHASHSEED'}
    r['info'] = {'generator': {'env': genv}, 'written_by': 'sz2_recipe.py'}
    return r


def write(env, emit_dir):
    """Writes <emit_dir>/build.json and returns its path."""
    path = os.path.join(emit_dir, 'build.json')
    text = json.dumps(recipe(env, emit_dir), indent=1) + '\n'
    with open(path, 'w', newline='\n', encoding='utf-8') as f:
        f.write(text)
    return path
