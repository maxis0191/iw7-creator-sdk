"""Where each Station Zero music cue sounds in an in-game capture (fixture iwzmap_soundscape.gsc mode 4).

    python music_find.py --report <run>/scape/report.json --cues <cues dir with cues.json> [--threshold 0.5]
                         [--out music.json] [--pack <dir> --pack-window music]

For every cue file: the normalized cross-correlation of the cue against the whole capture (mono), every peak above
the threshold at least one cue length apart = one occurrence (capture time, xcorr, level of the capture over the
cue's length, gain against the file). The run's own log lines on the same clock (audio_measure.py scape report:
WAVE_START, SCAPE_CUE, SCAPE kind=intro/power_music, SCAPE_ENDGAME, SCAPE_POWER_ON) are listed beside them, so each
occurrence can be tied to the moment that should trigger it. --pack writes the named zone window of the capture
(the 2-minute round end -> round start span) as a WAV for the owner.
"""
import argparse
import json
import os
import sys

import numpy as np
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_measure as am  # noqa: E402


def norm_xcorr(ref, rec):
    """Normalized cross-correlation of ref along rec (valid lags), FFT based."""
    r = ref - ref.mean()
    n = len(r)
    num = signal.fftconvolve(rec, r[::-1], mode='valid')
    c = np.cumsum(np.concatenate([[0.0], rec * rec]))
    energy = np.sqrt(np.maximum(c[n:] - c[:-n], 1e-12))
    return num / (energy * np.sqrt(np.sum(r * r)) + 1e-12)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--report', required=True)
    ap.add_argument('--cues', required=True)
    ap.add_argument('--log', help='the run result.local.json: SCAPE_CUE / SCAPE_ENDGAME / SCAPE_POWER_ON lines as marks')
    ap.add_argument('--threshold', type=float, default=0.5)
    ap.add_argument('--out')
    ap.add_argument('--pack')
    ap.add_argument('--pack-window', default='music')
    a = ap.parse_args(argv)
    rep = json.load(open(a.report))
    rec = am.mono(am.decode(rep['capture'])).astype(np.float64)
    R = am.RATE
    cues = json.load(open(os.path.join(a.cues, 'cues.json')))['cues']
    found = []
    for c in cues:
        ref = am.mono(am.decode(os.path.join(a.cues, os.path.basename(c['file'])))).astype(np.float64)
        ref = ref[:int(min(len(ref), 8 * R))]                    # the first 8 s identify a cue
        x = norm_xcorr(ref, rec)
        peaks, _ = signal.find_peaks(x, height=a.threshold, distance=len(ref))
        for p in peaks:
            seg = rec[p:p + len(ref)]
            found.append({'cue': c['cue'], 'alias': c['alias'], 'capture_s': round(p / R, 2), 'xcorr': round(float(x[p]), 3),
                          'level_dbfs': round(am.dbfs(seg), 1), 'gain_db': round(am.dbfs(seg) - am.dbfs(ref), 1)})
    found.sort(key=lambda f: f['capture_s'])
    clock = rep.get('gsc_to_capture_offset_s', 0.0)
    marks = []
    for e in rep.get('events', []):
        if e.get('kind') in ('intro', 'power_music'):
            marks.append({'capture_s': round(e['capture_s'], 2), 'what': '%s %s' % (e['kind'], e['alias'])})
    for w in rep.get('waves', []):
        marks.append({'capture_s': round(w['capture_s'], 2), 'what': 'WAVE_START %s' % w.get('kind')})
    if a.log:
        import re
        with open(a.log, encoding='utf-8-sig') as f:
            lines = json.load(f).get('Lines', [])
        for line in lines:
            m = re.search(r'\[IWZ audio\] (SCAPE_CUE|SCAPE_ENDGAME|SCAPE_POWER_ON|SCAPE_ZONE)(.*?) t=(\d+)', line)
            if m:
                marks.append({'capture_s': round(int(m.group(3)) / 1000.0 + clock, 2), 'what': (m.group(1) + m.group(2)).strip()})
    out = {'capture': rep['capture'], 'threshold': a.threshold, 'found': found, 'marks': sorted(marks, key=lambda m: m['capture_s'])}
    if a.pack:
        z = next((z for z in rep['zones'] if z['zone'] == a.pack_window), None)
        if z:
            os.makedirs(a.pack, exist_ok=True)
            full = am.decode(rep['capture'])
            seg = full[int(z['start_s'] * R):int((z['start_s'] + z['seconds']) * R)]
            path = os.path.join(a.pack, 'ingame_%s_%ds.wav' % (a.pack_window, int(len(seg) / R)))
            am.write_wav(path, seg)
            out['pack'] = path
    if a.out:
        json.dump(out, open(a.out, 'w'), indent=1)
    for f in found:
        print('%8.2f s  %-14s %-28s xcorr %.3f  level %6.1f dBFS' % (f['capture_s'], f['cue'], f['alias'], f['xcorr'], f['level_dbfs']))
    print('-- log marks')
    for m in out['marks']:
        print('%8.2f s  %s' % (m['capture_s'], m['what']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
