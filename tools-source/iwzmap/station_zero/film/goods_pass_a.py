r"""goods_pass_a: one live pass of the goods of Needle Drop and Heel & Key (worker A3a): start, power on, shots, power off, shots, stop.

    python goods_pass_a.py <pass folder> [doc folder]

Writes <pass>\{on,off}\<camera>.png, sheets sheet_{on,off}_<k>.jpg (six a sheet, the camera named), blind crops blind_<camera>.jpg
(the ON frame with its top 30 % cut away: the fascia out of the picture, for the question "what does this shop sell?"), pass.json.
One session, started and stopped here; nothing else is touched.
"""
import json
import os
import subprocess
import sys
import time

DOC = r'C:\studio-data\sz\film\arcade\goods_a\doc'
STUDIO = r'C:\studio'
CAMS = ['arc_needle_drop_front', 'arc_needle_drop_oblique', 'arc_needle_drop_inside', 'needle_drop_window_close',
        'arc_heel_key_front', 'arc_heel_key_oblique', 'heel_key_counter_close', 'arc_east_long']


def studio(*args):
    env = dict(os.environ, STUDIO_ROOT='C:/studio',
               IWZ_ZONETOOL_EXE=r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-serve\build\bin\x64\Release\zonetool.exe')
    t = time.time()
    p = subprocess.run([sys.executable, '-m', 'studio'] + list(args), cwd=STUDIO, env=env, capture_output=True, text=True)
    try:
        r = json.loads(p.stdout)
    except ValueError:
        r = {'ok': False, 'stdout': p.stdout[-1500:], 'stderr': p.stderr[-1500:]}
    r['_s'] = round(time.time() - t, 1)
    return r


def sheets(folder, state):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 26)
    out = []
    for s in range(0, len(CAMS), 6):
        sheet = Image.new('RGB', (1920, 720), (0, 0, 0))
        for k, c in enumerate(CAMS[s:s + 6]):
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


def blind(folder):
    from PIL import Image
    out = []
    for c in ('arc_needle_drop_front', 'arc_heel_key_front'):
        p = os.path.join(folder, 'on', c + '.png')
        if os.path.isfile(p):
            im = Image.open(p).convert('RGB')
            w, h = im.size
            q = os.path.join(folder, 'blind_%s.jpg' % c)
            im.crop((0, int(h * 0.30), w, h)).save(q, quality=90)
            out.append(q)
    return out


def main():
    folder = sys.argv[1]
    doc = sys.argv[2] if len(sys.argv) > 2 else DOC
    os.makedirs(folder, exist_ok=True)
    rep = {'start': studio('live', 'start', doc, '--idle-min', '20'), 'power': {}, 'shots': {}}
    if rep['start'].get('ok'):
        for state in ('on', 'off'):
            os.makedirs(os.path.join(folder, state), exist_ok=True)
            rep['power'][state] = studio('live', 'power', doc, state)
            for c in CAMS:
                r = studio('live', 'shot', doc, '--clean', '--camera', c, '--out', os.path.join(folder, state, c + '.png'))
                rep['shots']['%s/%s' % (state, c)] = {k: r.get(k) for k in ('ok', 'settled', 'error', 'stale', 'stderr', '_s')}
        rep['sheets'] = sheets(folder, 'on') + sheets(folder, 'off')
        rep['blind'] = blind(folder)
    rep['stop'] = studio('live', 'stop', doc)
    json.dump(rep, open(os.path.join(folder, 'pass.json'), 'w', encoding='utf-8'), indent=1, default=str)
    print(json.dumps({'start_ok': rep['start'].get('ok'), 'start_s': rep['start'].get('_s'), 'sheets': rep.get('sheets'),
                      'failed': [k for k, v in rep['shots'].items() if not v.get('ok')], 'start_error': None if rep['start'].get('ok') else rep['start']},
                     indent=1, default=str)[:3000])


if __name__ == '__main__':
    main()
