"""Prepare zonetool/<map>_art: the main-menu map browser art of a zombies usermap.

usage: build_art.py <work dir> <map> <assembled map dir (techsets, materials)> <art dir> [<cp_frontend dump dir>]

Art dir: image_<map>.tga and image_<map>_vote.tga (2D map list images; the client, iw7-mod arena.cpp, loads
usermaps/<map>/<map>_art.ff in the frontend and defaults the arena mapimage / mapvoteimage to these names), and
optionally zmb_poster_<map>_c.tga: the theater poster of the zombies map browser. Aurora's frontend usermaps.gsc
sets the model zmb_poster_<map> on the theater poster entity when the map is focused (dvar ui_usermap_posters,
published by arena.cpp for every cp_ usermap with an art zone). The poster model reuses the stock poster mesh of
cp_frontend (zmb_poster_dlc1: one quad surface) with its own material and image.
"""
import json, os, shutil, sys

work, mapname, assembled, art = sys.argv[1:5]
frontend = sys.argv[5] if len(sys.argv) > 5 else None
zone = mapname + '_art'
dst = os.path.join(work, 'zonetool', zone)
if os.path.isdir(dst):
    shutil.rmtree(dst)
os.makedirs(os.path.join(dst, 'materials'))
os.makedirs(os.path.join(dst, 'images'))

POSTER_TECHSET = 'mo_l_sm_replace_i0c0s0'   # lit model material of the stock signage (cp_zmb)

# technique sets, techniques and shaders (hardlinks; buildzone keeps only what the art assets reference)
src_ts = os.path.join(assembled, 'techsets')
for root, _, files in os.walk(src_ts):
    rel = os.path.relpath(root, assembled)
    for f in files:
        if True:
            os.makedirs(os.path.join(dst, rel), exist_ok=True)
            os.link(os.path.join(root, f), os.path.join(dst, rel, f))

rows = ['// %s: map browser art' % zone]
for name in ('image_' + mapname, 'image_' + mapname + '_vote'):
    shutil.copyfile(os.path.join(art, name + '.tga'), os.path.join(dst, 'images', name + '.tga'))
    material = {
        "techniqueSet->name": "2d", "gameFlags": 0, "unkFlags": 0, "sortKey": 41, "renderFlags": 1,
        "textureAtlasRowCount": 1, "textureAtlasColumnCount": 1, "textureAtlasFrameBlend": 0, "textureAtlasAsArray": 0,
        "surfaceTypeBits": 0, "stateFlags": 64, "cameraRegion": 4, "materialType": 0, "assetFlags": 0,
        "constantTable": [{"name": "colorTint", "nameHash": 3054254906, "literal": [1.0, 1.0, 1.0, 1.0]}],
        "textureTable": [{"image": name, "semantic": 0, "samplerState": 243, "lastCharacter": 112,
                          "firstCharacter": 99, "typeHash": 2695565377}],
    }
    json.dump(material, open(os.path.join(dst, 'materials', name + '.json'), 'w'), indent=4)
    rows.append('material,' + name)

poster_c = 'zmb_poster_' + mapname + '_c'
if frontend and os.path.isfile(os.path.join(art, poster_c + '.tga')):
    model = 'zmb_poster_' + mapname
    material_name = 'mo/iwz_poster_' + mapname
    # material: the stock signage material layout with the poster image (colour) and a flat spec/gloss image
    sign = json.load(open(os.path.join(assembled, 'materials', 'mo', 'zmb_caricature_signs.json')))
    assert sign['techniqueSet->name'] == POSTER_TECHSET
    for entry in sign['textureTable']:
        if entry['semantic'] == 2:
            entry['image'] = poster_c
        elif entry['semantic'] == 8:
            entry['image'] = 'zmb_poster_' + mapname + '_sg'
    os.makedirs(os.path.join(dst, 'materials', 'mo'), exist_ok=True)
    json.dump(sign, open(os.path.join(dst, 'materials', 'mo', 'iwz_poster_' + mapname + '.json'), 'w'), indent=4)
    for image in (poster_c, 'zmb_poster_' + mapname + '_sg'):
        shutil.copyfile(os.path.join(art, image + '.tga'), os.path.join(dst, 'images', image + '.tga'))
    # model: the stock poster model with its name and material replaced (strings are null terminated)
    data = open(os.path.join(frontend, 'xmodel', 'zmb_poster_dlc1.xmb'), 'rb').read()
    for old, new in ((b'zmb_poster_dlc1\0', model.encode() + b'\0'),
                     (b'mo/zombies_theater_poster02\0', material_name.encode() + b'\0')):
        assert data.count(old) == 1, old
        data = data.replace(old, new)
    os.makedirs(os.path.join(dst, 'xmodel'), exist_ok=True)
    open(os.path.join(dst, 'xmodel', model + '.xmb'), 'wb').write(data)
    os.makedirs(os.path.join(dst, 'xsurface'), exist_ok=True)
    surf = 'zmb_poster_spaceland_01_lod010v1p0_0011.xsb'
    shutil.copyfile(os.path.join(frontend, 'xsurface', surf), os.path.join(dst, 'xsurface', surf))
    rows.append('xmodel,' + model)
    # the poster technique set shares its techniques with the stock technique set zones (as the map zone does)
    rows[1:1] = ['require,' + z for z in ('techsets_common', 'techsets_global', 'techsets_common_core_mp',
                                          'techsets_global_core_mp', 'techsets_common_mp', 'techsets_global_mp',
                                          'techsets_common_cp', 'techsets_global_cp', 'techsets_cp_zmb')]

os.makedirs(os.path.join(work, 'zone_source'), exist_ok=True)
open(os.path.join(work, 'zone_source', zone + '.csv'), 'w', newline='\n').write('\n'.join(rows) + '\n')
print('prepared', dst, len(rows) - 1, 'assets')
