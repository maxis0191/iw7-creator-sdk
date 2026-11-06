"""Measure game audio captures against source audio (numpy + scipy; ffmpeg decodes).

    python audio_measure.py match --ref song.flac --rec capture.wav [--rec-start S --rec-dur D] [--ref-max S]
    python audio_measure.py levels --rec capture.wav --windows windows.json [--ref hint.flac]
    python audio_measure.py run --rec capture.wav --log result.local.json --song song.flac --hint hint.flac
                                [--activate act.flac] [--out report.json] [--plot curve.png]

match  finds where a recorded window sits in the reference (FFT cross-correlation of the mono signals,
       normalized), then reports for that alignment: the normalized correlation peak, the Pearson r of the
       aligned waveforms, the Pearson r of their log spectrograms, and the gain (dB) from source to capture.
levels RMS (dBFS) and the level of a reference signal's band per window ({"label", "start", "end"} list).
run    the Station Zero audio witness: aligns the fixture timeline ([IWZ audio] lines with gettime) to the
       capture through the song onset, then measures the hint loop level per distance step, the song match
       and the activation sound; writes one JSON report (and optionally a PNG of level vs distance).
"""
import argparse
import json
import math
import re
import subprocess
import sys

import numpy as np
from scipy import signal

RATE = 48000


def decode(path, rate=RATE):
    """Any audio file -> float32 array (frames, channels) at `rate` via ffmpeg."""
    probe = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'a:0', '-show_entries', 'stream=channels',
                            '-of', 'csv=p=0', path], capture_output=True, text=True, check=True)
    ch = int(probe.stdout.strip().split(',')[0] or 1)
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'f32le', '-acodec', 'pcm_f32le', '-ar', str(rate), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, ch)


def mono(x):
    return x.mean(axis=1) if x.ndim == 2 else x


def dbfs(x):
    r = float(np.sqrt(np.mean(np.square(x)))) if len(x) else 0.0
    return 20 * math.log10(r) if r > 0 else -200.0


def xcorr_lag(needle, hay):
    """Best offset of `needle` inside `hay` and the normalized correlation at that offset."""
    n = len(needle)
    corr = signal.fftconvolve(hay, needle[::-1], mode='valid')
    # normalize by the energy of each hay window
    c = np.concatenate([[0.0], np.cumsum(np.square(hay, dtype=np.float64))])
    e = np.sqrt(np.maximum(c[n:] - c[:-n], 0.0)) * np.sqrt(np.sum(np.square(needle, dtype=np.float64)))
    norm = corr / np.maximum(e, 1e-12)
    i = int(np.argmax(norm))
    return i, float(norm[i]), norm


def spec_corr(a, b, rate=RATE):
    """Pearson r between the log-magnitude spectrograms of two aligned signals."""
    _, _, sa = signal.stft(a, rate, nperseg=2048, noverlap=1024)
    _, _, sb = signal.stft(b, rate, nperseg=2048, noverlap=1024)
    la, lb = np.log10(np.abs(sa) + 1e-6).ravel(), np.log10(np.abs(sb) + 1e-6).ravel()
    return float(np.corrcoef(la, lb)[0, 1])


def match(ref, rec, rec_start=0.0, rec_dur=20.0, ref_max=None, rate=RATE):
    """Locate rec[rec_start : rec_start+rec_dur] inside ref; correlation figures at the best alignment."""
    r = mono(ref)
    if ref_max:
        r = r[:int(ref_max * rate)]
    a, b = int(rec_start * rate), int((rec_start + rec_dur) * rate)
    w = mono(rec)[a:b]
    if len(w) < rate // 2 or not np.any(w):
        return {'error': 'empty or silent capture window', 'rec_start': rec_start, 'rec_dur': rec_dur}
    if len(w) <= len(r):
        # the capture window sits somewhere inside the (longer) reference
        i, peak, norm = xcorr_lag(w, r)
        aligned = r[i:i + len(w)]
        ref_offset, rec_offset = i / rate, 0.0
    else:
        # a short reference (one-shot) sits somewhere inside the capture window
        i, peak, norm = xcorr_lag(r, w)
        aligned, w = r, w[i:i + len(r)]
        ref_offset, rec_offset = 0.0, i / rate
    pearson = float(np.corrcoef(aligned, w)[0, 1])
    gain = dbfs(w) - dbfs(aligned)
    # how far the best peak stands above the rest of the correlation curve (outside +-50 ms)
    guard = int(0.05 * rate)
    rest = np.concatenate([norm[:max(0, i - guard)], norm[i + guard:]])
    second = float(rest.max()) if len(rest) else 0.0
    return {'ref_offset_s': ref_offset, 'rec_start_s': rec_start + rec_offset, 'rec_dur_s': len(w) / rate,
            'ref_time_at_rec_zero_s': ref_offset - rec_start - rec_offset,
            'xcorr_peak': peak, 'xcorr_second': second, 'pearson_r': pearson,
            'spectral_r': spec_corr(aligned, w, rate), 'gain_db': gain,
            'rec_rms_dbfs': dbfs(w), 'ref_rms_dbfs': dbfs(aligned)}


def band_filter(x, ref, rate=RATE):
    """x filtered to the band holding 90% of the reference's energy."""
    f, p = signal.welch(mono(ref), rate, nperseg=4096)
    c = np.cumsum(p) / np.sum(p)
    lo, hi = f[np.searchsorted(c, 0.05)], f[np.searchsorted(c, 0.95)]
    lo, hi = max(lo, 20.0), min(hi, rate / 2 - 100)
    sos = signal.butter(4, [lo, hi], btype='band', fs=rate, output='sos')
    return signal.sosfilt(sos, mono(x)), (float(lo), float(hi))


def band_level(x, ref, rate=RATE):
    """Level (dB) of x inside the band holding 90% of the reference's energy."""
    y, band = band_filter(x, ref, rate)
    return dbfs(y), band


def median_level(x, rate=RATE, block=0.25):
    """Median of 250 ms block levels: a steady loop's level, robust to one-shot transients."""
    n = int(block * rate)
    blocks = [dbfs(x[i:i + n]) for i in range(0, len(x) - n + 1, n)]
    return float(np.median(blocks)) if blocks else -200.0


def levels(rec, windows, ref=None, rate=RATE):
    out = []
    for w in windows:
        a, b = int(w['start'] * rate), int(w['end'] * rate)
        seg = rec[a:b]
        row = dict(w, rms_dbfs=dbfs(mono(seg)), median_dbfs=median_level(mono(seg), rate))
        if ref is not None and len(seg):
            y, row['band_hz'] = band_filter(seg, ref, rate)
            row['band_dbfs'] = dbfs(y)
            row['band_median_dbfs'] = median_level(y, rate)
        out.append(row)
    return out


def plot_png(path, rows, silence_db=None, dist_max=550):
    """Level vs distance chart (PIL, no plotting library needed)."""
    from PIL import Image, ImageDraw
    W, H, L, R, T, B = 760, 420, 70, 20, 40, 50
    img = Image.new('RGB', (W, H), 'white')
    g = ImageDraw.Draw(img)
    xs = [r['distance'] for r in rows]
    ys = [r['band_median_dbfs'] for r in rows] + [r['median_dbfs'] for r in rows]
    x0, x1 = 0, max(xs) * 1.05
    y0, y1 = min(-80.0, min(ys)) - 5, max(ys) + 5
    px = lambda x: L + (x - x0) / (x1 - x0) * (W - L - R)
    py = lambda y: T + (y1 - max(y, y0)) / (y1 - y0) * (H - T - B)
    for yv in range(int(y0 // 10 * 10), int(y1) + 1, 10):
        g.line([(L, py(yv)), (W - R, py(yv))], fill=(230, 230, 230))
        g.text((8, py(yv) - 6), '%d dB' % yv, fill='black')
    for xv in range(0, int(x1) + 1, 100):
        g.text((px(xv) - 10, H - B + 8), str(xv), fill='black')
    g.line([(px(dist_max), T), (px(dist_max), H - B)], fill=(220, 0, 0))
    g.text((px(dist_max) + 4, T + 2), 'dist_max %d' % dist_max, fill=(220, 0, 0))
    if silence_db is not None:
        g.line([(L, py(silence_db)), (W - R, py(silence_db))], fill=(150, 150, 150))
    for key, colour in (('median_dbfs', (120, 120, 200)), ('band_median_dbfs', (0, 90, 180))):
        pts = sorted((px(r['distance']), py(r[key])) for r in rows)
        g.line(pts, fill=colour, width=2)
        for x, y in pts:
            g.ellipse([x - 4, y - 4, x + 4, y + 4], outline=colour, width=2)
    g.text((L, 10), 'Hint loop level vs distance (in-game capture): dark = hint band median, light = full band median',
           fill='black')
    g.text((W // 2 - 90, H - 20), 'player distance to the bear (units)', fill='black')
    g.rectangle([L, T, W - R, H - B], outline='black')
    img.save(path)


LINE = re.compile(r'\[IWZ audio\] (\w+)(.*)')


def parse_lines(lines):
    events = []
    for line in lines:
        m = LINE.search(line)
        if not m:
            continue
        kv = dict(re.findall(r'(\w+)=([^\s;]+)', m.group(2)))
        events.append({'event': m.group(1), **kv})
    return events


def run(args):
    rec = decode(args.rec)
    with open(args.log, encoding='utf-8-sig') as f:
        log = json.load(f)
    events = parse_lines(log.get('Lines', []))
    song = decode(args.song)
    hint = decode(args.hint)
    report = {'capture': args.rec, 'capture_seconds': len(rec) / RATE, 'capture_rms_dbfs': dbfs(mono(rec)),
              'events': events}
    start = next((e for e in events if e['event'] == 'SONG_START'), None)
    if not start:
        report['error'] = 'no SONG_START line'
        return report
    # 1. song: search the first 60 s of the song in the capture after the fixture's estimated start
    g_song = int(start['t'])
    tail = mono(rec)
    # locate the song onset in the capture: correlate the first 8 s of the song over the whole capture
    head = mono(song)[:8 * RATE]
    i, peak, _ = xcorr_lag(head, tail)
    onset = i / RATE
    report['song_onset_capture_s'] = onset
    report['song_onset_xcorr_peak'] = peak
    dur = min(args.song_window, len(tail) / RATE - onset - 0.5)
    report['song'] = match(song, rec, onset, dur, ref_max=dur + 30)
    # offset between the GSC clock and the capture clock (song start latency included)
    clock = onset - g_song / 1000.0
    report['gsc_to_capture_offset_s'] = clock
    # 2. hint loop steps: HINT_STEP d=<units> t=<ms> hold=<ms>
    steps = [e for e in events if e['event'] == 'HINT_STEP']
    windows = []
    for e in steps:
        t0 = int(e['t']) / 1000.0 + clock
        hold = int(e.get('hold', 4000)) / 1000.0
        windows.append({'label': 'd=%s' % e['d'], 'distance': float(e['d']), 'start': t0 + 0.75, 'end': t0 + hold - 0.25})
    lv = levels(rec, windows, hint)
    looped = np.concatenate([hint, hint, hint])   # the loop wraps inside a window: match against the loop
    for row in lv:
        m = match(looped, rec, row['start'], 2.0)
        row['hint_xcorr_peak'] = m.get('xcorr_peak')
        row['hint_spectral_r'] = m.get('spectral_r')
    report['hint_steps'] = lv
    if lv:
        d = np.array([r['distance'] for r in lv])
        L = np.array([r['band_median_dbfs'] for r in lv])
        order = np.argsort(d)
        # level never rises by more than 2 dB when the player moves away (inside the audible range)
        report['hint_monotonic_decreasing_with_distance'] = bool(np.all(np.diff(L[order]) <= 2.0))
        report['hint_level_near_minus_far_db'] = float(L[order][0] - L[order][-1])
        inside = d <= args.dist_max
        if inside.sum() >= 2:
            report['hint_slope_db_per_100u_inside'] = float(np.polyfit(d[inside], L[inside], 1)[0] * 100)
        report['hint_audible_steps'] = [float(x) for x, y in zip(d, L) if y > -80]
    # 3. ambience window and silence baseline, if the fixture printed them
    for name in ('SILENCE', 'AMBIENCE'):
        e = next((x for x in events if x['event'] == name), None)
        if e:
            t0 = int(e['t']) / 1000.0 + clock
            hold = int(e.get('hold', 5000)) / 1000.0
            report[name.lower()] = levels(rec, [{'label': name, 'start': t0 + 0.5, 'end': t0 + hold - 0.25}])[0]
    # 4. activation sound right before the song
    act = next((e for e in events if e['event'] == 'EE_ACTIVATED'), None)
    if act and args.activate:
        a = decode(args.activate)
        t0 = int(act['t']) / 1000.0 + clock
        report['activation'] = match(a, rec, max(0.0, t0 - 0.5), 3.0)
    if args.plot and lv:
        plot_png(args.plot, lv, report.get('silence', {}).get('median_dbfs'), args.dist_max)
        report['plot'] = args.plot
    return report


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('match')
    p.add_argument('--ref', required=True)
    p.add_argument('--rec', required=True)
    p.add_argument('--rec-start', type=float, default=0.0)
    p.add_argument('--rec-dur', type=float, default=20.0)
    p.add_argument('--ref-max', type=float)
    p = sub.add_parser('levels')
    p.add_argument('--rec', required=True)
    p.add_argument('--windows', required=True)
    p.add_argument('--ref')
    p = sub.add_parser('run')
    p.add_argument('--rec', required=True)
    p.add_argument('--log', required=True)
    p.add_argument('--song', required=True)
    p.add_argument('--hint', required=True)
    p.add_argument('--activate')
    p.add_argument('--song-window', type=float, default=30.0)
    p.add_argument('--dist-max', type=float, default=550.0, help='hint alias dist_max (falloff end)')
    p.add_argument('--out')
    p.add_argument('--plot')
    args = ap.parse_args(argv)
    if args.cmd == 'match':
        result = match(decode(args.ref), decode(args.rec), args.rec_start, args.rec_dur, args.ref_max)
    elif args.cmd == 'levels':
        with open(args.windows) as f:
            result = levels(decode(args.rec), json.load(f), decode(args.ref) if args.ref else None)
    else:
        result = run(args)
        if args.out:
            with open(args.out, 'w') as f:
                json.dump(result, f, indent=1)
    print(json.dumps(result, indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
