"""Derived soundscape clips for Station Zero, made only from stock game audio (numpy + scipy; ffmpeg I/O).

    python soundscape_dsp.py pa --voices <dir with *_int_0.flac> --static <pa_buzz.flac> --out <dir> [--count 8] [--seed 7]
                                [--only main_power_on,elevator,...]
    python soundscape_dsp.py chime --source <copper_chime.flac> --out <file.flac>
    python soundscape_dsp.py trim --source <sting.flac> --seconds 11 --fade 2.5 --out <file.flac>

pa     broken station PA announcements: each clip = PA switch-on click and buzz, one stock PA voice line (BO3
       zm_island facility PA, interior take) band-limited to a cheap horn speaker (350..3200 Hz), lightly
       clipped, with 25..45 % of its 120..260 ms slices replaced by static from the stock PA buzz (BO3 zm_factory
       pa_buzz), a tremolo of failing power, then the buzz cut off. A few words stay intelligible, the rest is
       lost in static. Deterministic for a seed; a JSON sidecar lists the source line and the cut slices.
trim   the first N seconds of a stock music sting with a fade-out (the match intro sting must end before the first
       round-start sting of the stock wave loop, about 15 s after the intro screen)
chime  a subway door chime from a stock metal chime recording (BO3 mp_kung_fu copper_chime): the two strongest
       single strikes, each 0.9 s with a fast decay, the second a fourth lower (ding-dong), 0.32 s apart.
No synthesized or generated music: every sample comes from the listed stock recordings.
"""
import argparse
import glob
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_measure as am  # noqa: E402

RATE = 48000


def write_flac(path, x, rate=RATE):
    x = np.clip(np.asarray(x, np.float32), -1.0, 1.0)
    if x.ndim == 1:
        x = x[:, None]
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    pcm = (x * 32767.0).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(rate), '-ac', str(x.shape[1]), '-i', '-',
                    '-c:a', 'flac', '-sample_fmt', 's16', '-frame_size', '1024', path], input=pcm, check=True)


def norm_peak(x, peak=0.7):
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    return x * (peak / m) if m > 0 else x


def pa_clip(voice, static, rng):
    sos = signal.butter(4, [350, 3200], btype='band', fs=RATE, output='sos')
    v = signal.sosfilt(sos, voice)
    v = norm_peak(v, 0.6)
    v = np.tanh(v * 2.2) / np.tanh(2.2)                      # cheap horn speaker
    st = signal.sosfilt(sos, static)
    st = norm_peak(st, 0.45)
    out = v.copy()
    cuts = []
    i = int(0.15 * RATE)
    frac = rng.uniform(0.25, 0.45)
    while i < len(v):
        n = int(rng.uniform(0.12, 0.26) * RATE)
        if rng.random() < frac:
            a = int(rng.integers(0, max(1, len(st) - n)))
            seg = st[a:a + n]
            if len(seg) < n:
                seg = np.pad(seg, (0, n - len(seg)))
            seg = seg[:len(out[i:i + n])]
            fade = np.minimum(1.0, np.minimum(np.arange(len(seg)), np.arange(len(seg))[::-1]) / (0.004 * RATE))
            out[i:i + len(seg)] = out[i:i + len(seg)] * (1 - fade) + seg * fade
            cuts.append([round(i / RATE, 3), round((i + len(seg)) / RATE, 3)])
        i += n
    t = np.arange(len(out)) / RATE
    out *= 0.8 + 0.2 * np.sin(2 * np.pi * rng.uniform(5, 9) * t + rng.uniform(0, 6.28))   # failing power
    head = st[:int(0.35 * RATE)] * np.linspace(0.0, 1.0, int(0.35 * RATE))
    tail = st[int(0.35 * RATE):int(0.35 * RATE) + int(0.25 * RATE)]
    tail = tail * np.linspace(1.0, 0.0, len(tail))
    clip = np.concatenate([head, out, tail, np.zeros(int(0.05 * RATE))])
    return norm_peak(clip, 0.8), cuts


def cmd_pa(args):
    voices = sorted(glob.glob(os.path.join(args.voices, '*_int_0.flac')))
    if args.only:
        voices = [v for v in voices if any(k in os.path.basename(v) for k in args.only.split(','))]
    if not voices:
        raise SystemExit('no *_int_0.flac voice lines in %s' % args.voices)
    static = am.mono(am.decode(args.static))
    rng = np.random.default_rng(args.seed)
    order = rng.permutation(len(voices))
    report = []
    for k in range(args.count):
        src = voices[order[k % len(voices)]]
        clip, cuts = pa_clip(am.mono(am.decode(src)), static, rng)
        path = os.path.join(args.out, 'pa_%02d.flac' % k)
        write_flac(path, clip)
        report.append({'clip': path, 'voice': src, 'static': args.static, 'seconds': round(len(clip) / RATE, 2),
                       'static_slices': cuts, 'rms_dbfs': round(am.dbfs(clip), 1)})
    with open(os.path.join(args.out, 'pa_clips.json'), 'w') as f:
        json.dump({'seed': args.seed, 'clips': report}, f, indent=1)
    print(json.dumps([{k: r[k] for k in ('clip', 'seconds', 'rms_dbfs')} | {'voice': os.path.basename(r['voice'])} for r in report], indent=1))


def strikes(x, count=2, gap=0.5):
    env = np.abs(signal.hilbert(x))
    env = signal.sosfilt(signal.butter(2, 30, fs=RATE, output='sos'), env)
    d = np.diff(env, prepend=0.0)
    peaks, _ = signal.find_peaks(d, distance=int(gap * RATE))
    peaks = sorted(peaks, key=lambda p: -d[p])[:count]
    return sorted(int(p) for p in peaks)


def cmd_chime(args):
    x = am.mono(am.decode(args.source))
    ps = strikes(x)
    if len(ps) < 2:
        raise SystemExit('fewer than two strikes in %s' % args.source)
    n = int(0.9 * RATE)
    notes = []
    for j, p in enumerate(ps[:2]):
        a = max(0, p - int(0.01 * RATE))
        seg = x[a:a + n]
        seg = seg * np.exp(-np.arange(len(seg)) / (0.32 * RATE))
        if j == 1:                                        # a fourth lower: resample by 4/3
            seg = signal.resample(seg, int(len(seg) * 4 / 3))[:n]
            seg = seg * np.exp(-np.arange(len(seg)) / (0.45 * RATE))
        notes.append(norm_peak(seg, 0.7))
    gap = int(0.32 * RATE)
    clip = np.zeros(gap + len(notes[1]) + len(notes[0]))
    clip[:len(notes[0])] += notes[0]
    clip[gap:gap + len(notes[1])] += notes[1]
    write_flac(args.out, norm_peak(clip, 0.8))
    print(json.dumps({'out': args.out, 'source': args.source, 'strikes_s': [round(p / RATE, 3) for p in ps[:2]],
                      'seconds': round(len(clip) / RATE, 2)}))


def cmd_trim(args):
    x = am.decode(args.source)
    n, f = int(args.seconds * RATE), int(args.fade * RATE)
    y = x[:n].copy()
    y[-f:] *= np.linspace(1.0, 0.0, f)[:, None]
    write_flac(args.out, y)
    print(json.dumps({'out': args.out, 'source': args.source, 'seconds': round(len(y) / RATE, 2), 'fade': args.fade}))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('pa')
    p.add_argument('--voices', required=True)
    p.add_argument('--static', required=True)
    p.add_argument('--out', required=True)
    p.add_argument('--count', type=int, default=8)
    p.add_argument('--seed', type=int, default=7)
    p.add_argument('--only', help='comma list of name fragments: only these voice lines')
    p = sub.add_parser('chime')
    p.add_argument('--source', required=True)
    p.add_argument('--out', required=True)
    p = sub.add_parser('trim')
    p.add_argument('--source', required=True)
    p.add_argument('--seconds', type=float, required=True)
    p.add_argument('--fade', type=float, default=2.5)
    p.add_argument('--out', required=True)
    args = ap.parse_args(argv)
    {'pa': cmd_pa, 'chime': cmd_chime, 'trim': cmd_trim}[args.cmd](args)
    return 0


if __name__ == '__main__':
    sys.exit(main())
