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
    e = np.sqrt(np.convolve(np.square(hay), np.ones(n), mode='valid')) * np.sqrt(np.sum(np.square(needle)))
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
    if len(w) < rate or not np.any(w):
        return {'error': 'empty or silent capture window', 'rec_start': rec_start, 'rec_dur': rec_dur}
    i, peak, norm = xcorr_lag(w, r)
    aligned = r[i:i + len(w)]
    pearson = float(np.corrcoef(aligned, w)[0, 1])
    gain = dbfs(w) - dbfs(aligned)
    # how far the best peak stands above the rest of the correlation curve (outside +-50 ms)
    guard = int(0.05 * rate)
    rest = np.concatenate([norm[:max(0, i - guard)], norm[i + guard:]])
    second = float(rest.max()) if len(rest) else 0.0
    return {'ref_offset_s': i / rate, 'rec_start_s': rec_start, 'rec_dur_s': len(w) / rate,
            'ref_time_at_rec_zero_s': i / rate - rec_start,
            'xcorr_peak': peak, 'xcorr_second': second, 'pearson_r': pearson,
            'spectral_r': spec_corr(aligned, w, rate), 'gain_db': gain,
            'rec_rms_dbfs': dbfs(w), 'ref_rms_dbfs': dbfs(aligned)}


def band_level(x, ref, rate=RATE):
    """Level (dB) of x inside the band holding 90% of the reference's energy."""
    f, p = signal.welch(mono(ref), rate, nperseg=4096)
    c = np.cumsum(p) / np.sum(p)
    lo, hi = f[np.searchsorted(c, 0.05)], f[np.searchsorted(c, 0.95)]
    lo, hi = max(lo, 20.0), min(hi, rate / 2 - 100)
    sos = signal.butter(4, [lo, hi], btype='band', fs=rate, output='sos')
    return dbfs(signal.sosfilt(sos, mono(x))), (float(lo), float(hi))


def levels(rec, windows, ref=None, rate=RATE):
    out = []
    for w in windows:
        a, b = int(w['start'] * rate), int(w['end'] * rate)
        seg = rec[a:b]
        row = dict(w, rms_dbfs=dbfs(mono(seg)))
        if ref is not None and len(seg):
            row['band_dbfs'], row['band_hz'] = band_level(seg, ref, rate)
        out.append(row)
    return out


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
    for row in lv:
        a, b = int(row['start'] * RATE), int(row['end'] * RATE)
        m = match(hint, rec, row['start'], row['end'] - row['start'])
        row['hint_xcorr_peak'] = m.get('xcorr_peak')
        row['hint_spectral_r'] = m.get('spectral_r')
    report['hint_steps'] = lv
    if lv:
        d = np.array([r['distance'] for r in lv])
        L = np.array([r['band_dbfs'] for r in lv])
        order = np.argsort(d)
        report['hint_monotonic_decreasing_with_distance'] = bool(np.all(np.diff(L[order]) <= 1.0))
        report['hint_level_near_minus_far_db'] = float(L[order][0] - L[order][-1])
        inside = d <= 550
        if inside.sum() >= 2:
            report['hint_slope_db_per_100u_inside_550'] = float(np.polyfit(d[inside], L[inside], 1)[0] * 100)
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
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.plot([r['distance'] for r in lv], [r['band_dbfs'] for r in lv], 'o-', label='hint loop band level')
        ax.plot([r['distance'] for r in lv], [r['rms_dbfs'] for r in lv], 's--', alpha=0.6, label='full-band RMS')
        if 'silence' in report:
            ax.axhline(report['silence']['rms_dbfs'], color='gray', ls=':', label='silence baseline')
        ax.axvline(550, color='red', ls=':', label='alias dist_max 550')
        ax.set_xlabel('player distance to the bear (units)')
        ax.set_ylabel('dBFS')
        ax.set_title('Hint loop level vs distance (in-game capture)')
        ax.legend()
        ax.grid(alpha=0.3)
        fig.tight_layout()
        fig.savefig(args.plot, dpi=110)
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
