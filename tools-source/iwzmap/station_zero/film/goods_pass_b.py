r"""goods_pass_b: one live pass of the goods of Copy Stop and Hole Number Nine, in one command (start, power on, shots, power off, shots, stop).

    python goods_pass_b.py <pass folder> [doc folder]          (run it once, in the background: about 4 minutes)

The darkness fix (e9af6d9: an all-baked map releases the dark vision at power-on) is in this branch's SDK, not in the main checkout:
Studio is pointed at this worktree (IWZ_SDK, and a studio.json beside the pass whose `sdk` is this worktree's tools-source/iwzmap).
Writes <pass>/<state>/<camera>.png, sheets sheet_<state>_<k>.jpg (six a sheet, names burned in), blind crops (the fascia band cut away)
blind_<state>.jpg, luma.json (mean luma of every frame, ON against OFF), and pass.json (every step's answer).
"""
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
WORKTREE = os.path.normpath(os.path.join(HERE, '..', '..', '..', '..'))
DOC = r'C:\studio-data\sz\film\arcade\goods_b\doc'
STUDIO = r'C:\studio'
CAMS = ['arc_copy_stop_front', 'arc_copy_stop_oblique', 'arc_copy_stop_inside', 'copy_stop_far', 'copy_stop_window_close', 'copy_stop_interior',
        'copy_stop_booth_close', 'copy_stop_memo_close', 'arc_hole_nine_front', 'arc_hole_nine_oblique', 'arc_hole_nine_inside', 'hole_nine_far',
        'hole_nine_counter_close', 'hole_nine_interior', 'hole_nine_back_wall', 'arc_east_long']
BLIND = ['copy_stop_far', 'arc_copy_stop_front', 'hole_nine_far', 'arc_hole_nine_front']


def env(folder):
    cfg = os.path.join(folder, 'studio_goods_b.json')
    json.dump({'sdk': os.path.join(WORKTREE, 'tools-source', 'iwzmap').replace('\\', '/')}, open(cfg, 'w'))
    return dict(os.environ, STUDIO_ROOT='C:/studio', STUDIO_CONFIG=cfg, IWZ_SDK=WORKTREE,
                IWZ_ZONETOOL_EXE=r'C:\Users\ezvalo\Documents\IW7-Products\worktrees\x64-zt-serve\build\bin\x64\Release\zonetool.exe')


def studio(e, *args, timeout=900):
    t = time.time()
    p = subprocess.run([sys.executable, '-m', 'studio'] + list(args), cwd=STUDIO, env=e, capture_output=True, text=True, timeout=timeout)
    try:
        r = json.loads(p.stdout)
    except ValueError:
        r = {'ok': False, 'stdout': p.stdout[-1500:], 'stderr': p.stderr[-1500:]}
    if isinstance(r, dict):
        r['_s'] = round(time.time() - t, 1)
    return r


def sheets(folder, state, cams):
    from PIL import Image, ImageDraw, ImageFont
    f = ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf', 26)
    out = []
    for s in range(0, len(cams), 6):
        sheet = Image.new('RGB', (1920, 720), (0, 0, 0))
        for k, c in enumerate(cams[s:s + 6]):
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


def blind(folder, state):
    """the frames from the hall with the top 45 % (fascias, the bulkhead) cut away: 'what does this shop sell?'"""
    from PIL import Image
    ims = []
    for c in BLIND:
        p = os.path.join(folder, state, c + '.png')
        if os.path.isfile(p):
            im = Image.open(p).convert('RGB')
            ims.append(im.crop((0, int(im.height * 0.45), im.width, im.height)).resize((960, 297)))
    if not ims:
        return None
    s = Image.new('RGB', (1920, 297 * ((len(ims) + 1) // 2)))
    for k, im in enumerate(ims):
        s.paste(im, ((k % 2) * 960, (k // 2) * 297))
    p = os.path.join(folder, 'blind_%s.jpg' % state)
    s.save(p, quality=90)
    return p


def luma(folder, states):
    from PIL import Image, ImageStat
    out = {}
    for c in CAMS:
        row = {}
        for s in states:
            p = os.path.join(folder, s, c + '.png')
            if os.path.isfile(p):
                row[s] = round(ImageStat.Stat(Image.open(p).convert('L')).mean[0], 2)
        out[c] = row
    return out


def main():
    folder = sys.argv[1]
    doc = sys.argv[2] if len(sys.argv) > 2 else DOC
    states = os.environ.get('GB_STATES', 'on,off').split(',')
    os.makedirs(folder, exist_ok=True)
    e = env(folder)
    rep = {'steps': {}}
    rep['steps']['start'] = studio(e, 'live', 'start', doc, '--idle-min', '20', timeout=1800)
    if rep['steps']['start'].get('ok') is False:
        json.dump(rep, open(os.path.join(folder, 'pass.json'), 'w'), indent=1, default=str)
        print(json.dumps({'start_failed': rep['steps']['start']}, default=str)[:3000])
        return
    try:
        for state in states:
            os.makedirs(os.path.join(folder, state), exist_ok=True)
            rep['steps']['power_' + state] = studio(e, 'live', 'power', doc, state)
            for c in CAMS:
                r = studio(e, 'live', 'shot', doc, '--clean', '--camera', c, '--out', os.path.join(folder, state, c + '.png'))
                rep['steps']['%s/%s' % (state, c)] = {k: r.get(k) for k in ('ok', 'settled', 'error', 'stale', 'stderr', '_s')}
    finally:
        rep['steps']['stop'] = studio(e, 'live', 'stop', doc)
    rep['sheets'] = [p for s in states for p in sheets(folder, s, CAMS)]
    rep['blind'] = [blind(folder, s) for s in states]
    rep['luma'] = luma(folder, states)
    json.dump(rep, open(os.path.join(folder, 'pass.json'), 'w'), indent=1, default=str)
    print(json.dumps({'sheets': rep['sheets'], 'blind': rep['blind'], 'start_s': rep['steps']['start'].get('_s'),
                      'failed': [k for k, v in rep['steps'].items() if isinstance(v, dict) and v.get('ok') is False],
                      'power': {s: rep['steps'].get('power_' + s, {}).get('ok') for s in states},
                      'luma_on_off': {c: v for c, v in rep['luma'].items()}}, indent=1, default=str))


if __name__ == '__main__':
    main()
