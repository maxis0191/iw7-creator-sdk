r"""arcade_frames: one live pass of the Arcade shell: frames of every camera with the power on and off, and contact sheets.

    python arcade_frames.py <pass folder> [doc folder]      (an open `studio live` session of the document is required)

Writes <pass>\on\<camera>.png, <pass>\off\<camera>.png, <pass>\sheet_on_<k>.jpg, sheet_off_<k>.jpg (six frames a sheet, the camera name
burned in) and <pass>\frames.json (each shot's answer). The session is not started or stopped here.
"""
import json
import os
import subprocess
import sys

DOC = r'C:\studio-data\sz\film\arcade\shell\doc'
STUDIO = r'C:\studio'


def studio(*args):
    env = dict(os.environ, STUDIO_ROOT='C:/studio')
    p = subprocess.run([sys.executable, '-m', 'studio'] + list(args), cwd=STUDIO, env=env, capture_output=True, text=True)
    try:
        return json.loads(p.stdout)
    except ValueError:
        return {'ok': False, 'stdout': p.stdout[-800:], 'stderr': p.stderr[-800:]}


def sheets(folder, state, cams):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', 'arialbd.ttf'), 26)
    out = []
    for s in range(0, len(cams), 6):
        chunk = cams[s:s + 6]
        sheet = Image.new('RGB', (1920, 720), (0, 0, 0))
        for k, c in enumerate(chunk):
            p = os.path.join(folder, state, c + '.png')
            if not os.path.isfile(p):
                continue
            im = Image.open(p).convert('RGB').resize((640, 360))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 640, 34], fill=(0, 0, 0))
            d.text((8, 4), '%s  %s' % (c, state.upper()), fill=(255, 230, 0), font=f)
            sheet.paste(im, ((k % 3) * 640, (k // 3) * 360))
        p = os.path.join(folder, 'sheet_%s_%d.jpg' % (state, s // 6))
        sheet.save(p, quality=90)
        out.append(p)
    return out


def main():
    folder = sys.argv[1]
    doc = sys.argv[2] if len(sys.argv) > 2 else DOC
    sys.path.insert(0, os.environ.get('STUDIO_ROOT', r'C:\studio'))
    from studio import Map
    cams = [o['name'] for o in Map.load(doc).objects() if o['kind'] == 'camera']      # every camera of the document (shell and goods)
    rep = {'power': {}, 'shots': {}}
    states = os.environ.get('A2_STATES', 'on,off').split(',')       # 'lit' = a lit-vision variant shot as it is (no power switch)
    for state in states:
        os.makedirs(os.path.join(folder, state), exist_ok=True)
        if state in ('on', 'off'):
            rep['power'][state] = studio('live', 'power', doc, state)
        for c in cams:
            extra = ['--allow-stale'] if os.environ.get('A2_ALLOW_STALE') else []          # another worker rewrote shared pictures mid-pass (28 Nov)
            r = studio('live', 'shot', doc, '--clean', '--camera', c, '--out', os.path.join(folder, state, c + '.png'), *extra)
            rep['shots']['%s/%s' % (state, c)] = {k: r.get(k) for k in ('ok', 'settled', 'error', 'stale', 'stderr')}
    rep['sheets'] = [p for s in states for p in sheets(folder, s, cams)]
    json.dump(rep, open(os.path.join(folder, 'frames_%s.json' % '_'.join(states)), 'w', encoding='utf-8'), indent=1, default=str)
    print(json.dumps({'sheets': rep['sheets'], 'failed': [k for k, v in rep['shots'].items() if not v.get('ok')],
                      'power': {k: v.get('ok') for k, v in rep['power'].items()}}, indent=1))


if __name__ == '__main__':
    main()
