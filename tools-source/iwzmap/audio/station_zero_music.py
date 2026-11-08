"""Station Zero music cues: horror, despair and curiosity, never heroic (owner direction 2026-11-08).

    python station_zero_music.py --out <dir> --chime <copper_chime.flac> --static <pa_buzz.flac>
                                 --horn <train horn.flac> --rumble <trolley loop.flac> --metal <metal rattle.flac>...
                                 [--breath <low swell.flac>] [--seed 26]

Sound design in code (numpy + scipy, ffmpeg I/O), deterministic for a seed. No generated music: the material is
stock game recordings (listed per cue in cues.json) plus plain synthesis (sine partials, filtered noise, comb
resonators, convolution with a synthetic decaying-noise room).

Leitmotif: the station's own PA chime, three strikes of a stock copper chime transposed to 0 / -5 / +2 semitones
(ding - dong - ding, ending on the second above: a question that never resolves). Each cue corrupts it: detuned,
slowed, reversed, cut off by PA static, or played on a small music box (synthesized comb tines) heard through
walls. Underneath: low beating drones, the trolley rumble an octave down, the distant train horn bent down in
pitch, metal rattles run through comb resonators tuned to a minor-second / tritone cluster, breath-like noise
swells, and hard silences.

Cues (alias -> files):
  mus_iwz_intro              intro.flac             15 s
  mus_zombies_newwave        round_start_0..2.flac  5..7 s   "something just changed"
  mus_zombies_endwave        round_end_0..2.flac    5..7 s   a sigh
  mus_zombies_eventwave_start event_start_0..1.flac 6..7 s
  mus_zombies_eventwave_end  event_end_0.flac       7 s
  mus_zombies_gameover       gameover.flac          15 s     the music box winds down, the last note never comes
  mus_iwz_power              power_on.flac          11 s     the chime plays right once, then goes wrong
  zmb_iwz_ee_activate        ee_activate.flac       2.4 s    a reversed tine into one music-box note (mono)
Every cue is normalized to the same active loudness (RMS of its non-silent 100 ms blocks, --level dBFS) with a
peak ceiling, so the bank volume decides the balance against the ambience.
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np
from scipy import signal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audio_measure as am  # noqa: E402

R = 48000
MOTIF = [0.0, -5.0, 2.0]                      # semitones of the PA chime (ding - dong - ding)
BOX = [0, -5, 2, 0, -2, -5, -7, -4]           # music-box phrase built on the motif, minor, ends unresolved


# ---------------------------------------------------------------- basic signal tools
def load(path):
    return am.mono(am.decode(path)).astype(np.float64)


def write_flac(path, x):
    """16-bit FLAC with fixed 1024-frame blocks: the only block size the IW7 sound banks play."""
    x = np.clip(np.asarray(x, np.float64), -1.0, 1.0)
    if x.ndim == 1:
        x = x[:, None]
    pcm = (x * 32767.0).astype('<i2').tobytes()
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 's16le', '-ar', str(R), '-ac', str(x.shape[1]), '-i', '-',
                    '-c:a', 'flac', '-sample_fmt', 's16', '-frame_size', '1024', path], input=pcm, check=True)


def write_wav(path, x):
    x = np.clip(np.asarray(x, np.float64), -1.0, 1.0)
    if x.ndim == 1:
        x = x[:, None]
    import wave
    with wave.open(path, 'wb') as w:
        w.setnchannels(x.shape[1])
        w.setsampwidth(2)
        w.setframerate(R)
        w.writeframes((x * 32767.0).astype('<i2').tobytes())


def sec(t):
    return int(round(t * R))


def norm(x, peak=1.0):
    m = float(np.max(np.abs(x))) if len(x) else 0.0
    return x * (peak / m) if m > 0 else x


def fade(x, fin=0.0, fout=0.0):
    y = np.array(x, np.float64, copy=True)
    a, b = sec(fin), sec(fout)
    if a:
        y[:a] *= np.linspace(0, 1, a)[:, None] if y.ndim == 2 else np.linspace(0, 1, a)
    if b:
        y[-b:] *= np.linspace(1, 0, b)[:, None] if y.ndim == 2 else np.linspace(1, 0, b)
    return y


def sos(kind, f, order=4):
    return signal.butter(order, f, btype=kind, fs=R, output='sos')


def filt(x, kind, f, order=4):
    return signal.sosfilt(sos(kind, f, order), x, axis=0)


def speed(x, ratio):
    """Pitch and speed together (tape): ratio > 1 higher and shorter."""
    n = max(2, int(len(x) / ratio))
    return np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x)


def bend(x, r0, r1, power=1.0):
    """Tape speed gliding from r0 to r1 over the output (a horn bent down when r1 < r0)."""
    pos, out, i = 0.0, [], 0
    est = int(len(x) / ((r0 + r1) / 2)) + 1
    t = np.linspace(0, 1, est) ** power
    rate = r0 + (r1 - r0) * t
    p = np.cumsum(rate)
    p = p[p < len(x) - 1]
    return np.interp(p, np.arange(len(x)), x)


def reverb(x, rt60=2.6, wet=0.45, seed=1, lp=3500.0, pre=0.025):
    """Stereo convolution with an exponentially decaying noise room (concrete hall)."""
    rng = np.random.default_rng(seed)
    n = sec(rt60 * 1.2)
    t = np.arange(n) / R
    decay = np.exp(-6.91 * t / rt60)
    irs = []
    for _ in range(2):
        ir = rng.standard_normal(n) * decay
        ir = filt(ir, 'low', lp, 2)
        ir = np.concatenate([np.zeros(sec(pre)), ir])
        irs.append(ir / np.sqrt(np.sum(ir * ir)))
    dry = x if x.ndim == 1 else am.mono(x)
    w = np.stack([signal.fftconvolve(dry, ir) for ir in irs], axis=1)
    d = np.zeros_like(w)
    d[:len(dry)] = dry[:, None] if x.ndim == 1 else x
    return (1 - wet) * d + wet * w * 0.9


def pan(x, p):
    """Mono -> stereo, p in -1..1 (equal power)."""
    a = (p + 1) * np.pi / 4
    return np.stack([x * np.cos(a), x * np.sin(a)], axis=1)


class Track:
    def __init__(self, seconds):
        self.buf = np.zeros((sec(seconds), 2))
        self.parts = []

    def add(self, x, t, gain=1.0, p=0.0, name=None):
        y = pan(x, p) if x.ndim == 1 else x
        a = sec(t)
        if a < 0:                                  # a swell that ends at t: its head before the cue start is dropped
            y, a = y[-a:], 0
        if a >= len(self.buf) or not len(y):
            return
        b = min(len(self.buf), a + len(y))
        self.buf[a:b] += gain * y[:b - a]
        if name:
            self.parts.append(name)

    def cut(self, t0):
        """Cut off: everything added so far stops dead at t0 (3 ms ramp); later layers enter after the silence."""
        a, r = sec(t0), sec(0.003)
        self.buf[a:] = 0
        self.buf[max(0, a - r):a] *= np.linspace(1, 0, min(r, a))[:, None]


# ---------------------------------------------------------------- instruments
class Kit:
    def __init__(self, args):
        self.rng = np.random.default_rng(args.seed)
        x = load(args.chime)
        env = np.abs(signal.hilbert(x))
        env = signal.sosfilt(sos('low', 30, 2), env)
        d = np.diff(env, prepend=0.0)
        peaks, _ = signal.find_peaks(d, distance=sec(0.5))
        best = int(sorted(peaks, key=lambda q: -d[q])[0])
        s = x[max(0, best - sec(0.008)):best + sec(2.4)]
        s = s * np.exp(-np.arange(len(s)) / (0.9 * R))
        self.strike = norm(fade(s, 0, 0.3), 0.8)
        spec = np.abs(np.fft.rfft(self.strike[:sec(0.5)] * np.hanning(sec(0.5))))
        f = np.fft.rfftfreq(sec(0.5), 1 / R)
        self.strike_hz = float(f[np.argmax(spec * (f > 150))])
        self.static = load(args.static)
        self.horn = load(args.horn)
        self.rumble = load(args.rumble)
        self.metal = [load(p) for p in args.metal]
        self.breath_src = load(args.breath) if args.breath else None
        self.sources = {'chime': args.chime, 'static': args.static, 'horn': args.horn, 'rumble': args.rumble,
                        'metal': args.metal, 'breath': args.breath}

    # the PA chime: one strike transposed (tape), optionally detuned in cents, slowed further
    def chime(self, semis, cents=0.0, slow=1.0):
        return speed(self.strike, 2 ** ((semis + cents / 100.0) / 12.0) / slow)

    def pa(self, x, drive=2.0):
        y = filt(x, 'band', [350, 3200])
        y = norm(y, 0.7)
        return np.tanh(y * drive) / np.tanh(drive)

    def static_burst(self, dur, seed=0):
        rng = np.random.default_rng(seed)
        n = sec(dur)
        a = int(rng.integers(0, max(1, len(self.static) - n)))
        s = self.static[a:a + n]
        if len(s) < n:
            s = np.concatenate([s, self.static[:n - len(s)]])
        return norm(filt(s, 'band', [350, 3200]), 0.6)

    # a small comb-tine music box (synthesis): fundamental, octave, and the bright 6.27x mode that dies fast
    def tine(self, hz, dur=2.2, detune_cents=0.0):
        t = np.arange(sec(dur)) / R
        f = hz * 2 ** (detune_cents / 1200.0)
        x = (np.sin(2 * np.pi * f * t) * np.exp(-t / 1.1)
             + 0.10 * np.sin(2 * np.pi * 2.0 * f * t) * np.exp(-t / 0.5)
             + 0.30 * np.sin(2 * np.pi * 6.27 * f * t) * np.exp(-t / 0.09))
        click = self.rng.standard_normal(sec(0.004)) * np.linspace(1, 0, sec(0.004)) * 0.3
        x[:len(click)] += filt(click, 'high', 3000, 2)
        return x * np.minimum(1, t / 0.002)

    def music_box(self, degrees, root=880.0, step=0.42, drift_cents=0.0, slow_end=1.0, drop=(), wall=True):
        """A phrase on the box; drift_cents bends the whole box down over the phrase (a dying spring),
        slow_end > 1 stretches the last steps (winding down), drop = indices of tines that do not sound."""
        n = len(degrees)
        times, t = [], 0.0
        for i in range(n):
            times.append(t)
            t += step * (1 + (slow_end - 1) * (i / max(1, n - 1)) ** 2)
        out = np.zeros(sec(t + 2.5))
        for i, (deg, at) in enumerate(zip(degrees, times)):
            if i in drop:
                continue
            c = drift_cents * i / max(1, n - 1) + self.rng.normal(0, 6)
            x = self.tine(root * 2 ** (deg / 12.0), detune_cents=c)
            a = sec(at)
            out[a:a + len(x)] += x[:len(out) - a]
        if wall:                                   # heard through walls: low-passed, thin
            out = filt(out, 'low', 950, 4) * 1.6
        return out

    def drone(self, notes_hz, dur, beat_cents=7.0, swell=(0.4, 0.5)):
        t = np.arange(sec(dur)) / R
        x = np.zeros_like(t)
        for hz in notes_hz:
            for c in (-beat_cents, beat_cents):
                f = hz * 2 ** (c / 1200.0)
                ph = self.rng.uniform(0, 2 * np.pi)
                x += np.sin(2 * np.pi * f * t + ph) + 0.25 * np.sin(2 * np.pi * 2 * f * t + ph) \
                    + 0.08 * np.sin(2 * np.pi * 3 * f * t + ph)
        e = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 1.5
        x = filt(x * e, 'low', 900, 2)
        return fade(norm(x, 0.5), swell[0] * dur * 0.3, swell[1] * dur * 0.3)

    def sub_rumble(self, dur):
        n = sec(dur)
        x = speed(self.rumble, 0.5)
        while len(x) < n:
            x = np.concatenate([x, x])
        x = filt(x[:n], 'low', 140, 4)
        return fade(norm(x, 0.6), dur * 0.35, dur * 0.35)

    def thud(self, f0=70.0, f1=32.0):
        t = np.arange(sec(1.4)) / R
        f = f1 + (f0 - f1) * np.exp(-t / 0.12)
        ph = 2 * np.pi * np.cumsum(f) / R
        x = np.sin(ph) * np.exp(-t / 0.45)
        nz = filt(self.rng.standard_normal(len(t)), 'low', 400, 2) * np.exp(-t / 0.05) * 0.4
        return norm(x + nz, 0.9)

    def bent_horn(self, r0=1.0, r1=0.6):
        return norm(filt(bend(self.horn, r0, r1, 0.7), 'low', 2500, 2), 0.7)

    def scrape_chord(self, chord_hz, dur, which=0, fb=0.985):
        """A metal rattle through comb resonators tuned to the chord: the scrape rings as a cluster."""
        src = self.metal[which % len(self.metal)]
        n = sec(dur)
        while len(src) < n:
            src = np.concatenate([src, src[::-1]])
        src = filt(src[:n], 'high', 120, 2)
        out = np.zeros(n)
        for hz in chord_hz:
            d = int(round(R / hz))
            a = np.zeros(d + 1)
            a[0], a[-1] = 1.0, -fb
            out += signal.lfilter([1.0 - fb], a, src)
        out = filt(out, 'low', 3000, 2)
        return fade(norm(out, 0.6), dur * 0.25, dur * 0.4)

    def breath(self, dur, inhale=True, seed=0):
        """A breath-like swell: noise through a band that brightens (in) or darkens (out, a sigh)."""
        rng = np.random.default_rng(seed)
        n = sec(dur)
        w = rng.standard_normal(n)
        b, a = [0.049922035, -0.095993537, 0.050612699, -0.004408786], [1, -2.494956002, 2.017265875, -0.522189400]
        pink = signal.lfilter(b, a, w)
        lo = filt(pink, 'band', [250, 800], 2)
        hi = filt(pink, 'band', [900, 2600], 2)
        t = np.linspace(0, 1, n)
        mix = t if inhale else 1 - t
        x = lo * (1 - mix) + hi * mix * 0.7
        e = np.sin(np.pi * t) ** 2
        if self.breath_src is not None and not inhale:
            low = speed(self.breath_src, 0.7)[:n]
            x[:len(low)] += 0.5 * norm(low, 1.0) * e[:len(low)]
        return norm(x * e, 0.6)


# ---------------------------------------------------------------- cues
def cue_intro(k):
    """15 s: it ends with a static tick just before the first round-start cue (the stock wave loop starts the
    first wave about 15 s after the intro screen, when the module plays this cue)."""
    T = Track(15.0)
    T.add(k.sub_rumble(7.0), 0.0, 0.55, name='trolley rumble an octave down')
    T.add(k.breath(2.6, True, 1), 0.3, 0.35, -0.3, name='breath in')
    # the PA chime through the station horn speakers, third note flat and cut by static
    pa = np.zeros(sec(3.2))
    for j, (s, at) in enumerate(zip(MOTIF, (0.0, 0.62, 1.24))):
        x = k.chime(s, cents=(-62.0 if j == 2 else 0.0), slow=1.15)
        a = sec(at)
        pa[a:a + len(x)] += x[:len(pa) - a]
    pa = k.pa(pa)
    T.add(reverb(pa, 2.8, 0.5, 2), 1.4, 0.75, name='PA chime (stock copper chime, motif 0/-5/+2, last note -62 cents)')
    T.add(k.static_burst(0.55, 3), 2.82, 0.55, name='PA static')
    T.cut(3.37)
    # the music box behind the walls, slowed and sinking, one tine missing
    box = k.music_box(BOX, root=880.0, step=0.55, drift_cents=-45.0, slow_end=1.6, drop=(5,))
    T.add(reverb(box, 2.2, 0.35, 4), 4.3, 0.6, 0.25, name='music box through walls (synth tines), drifting -45 cents')
    T.add(k.drone([73.4, 77.8, 110.0], 7.5), 6.0, 0.5, name='drone D2/D#2/A2 beating')
    T.add(reverb(k.bent_horn(0.95, 0.55), 3.5, 0.7, 5), 7.6, 0.45, -0.6, name='distant train horn bent down')
    T.add(reverb(k.scrape_chord([146.8, 155.6, 207.7], 3.5, 0), 2.5, 0.4, 6), 10.2, 0.4, 0.4,
          name='metal rattle tuned to D/D#/G# cluster')
    rev = k.chime(MOTIF[0], cents=-30.0, slow=1.6)
    rev = reverb(rev, 2.4, 0.6, 7)[::-1]
    T.add(norm(k.pa(am.mono(rev)), 0.7), 14.0 - len(rev) / R, 0.6, name='reversed PA chime swell')
    T.cut(14.0)
    T.add(k.static_burst(0.06, 9), 14.6, 0.25, name='static tick')
    return T


def cue_round_start(k, v):
    if v == 0:
        T = Track(6.0)
        rev = reverb(k.chime(MOTIF[2], cents=-40.0, slow=1.3), 2.0, 0.65, 11)[::-1]
        r = am.mono(rev)
        T.add(r, 1.7 - len(r) / R, 0.7, name='reversed chime swell')
        T.cut(1.7)
        T.add(k.thud(), 2.05, 0.8, name='sub thud')
        T.add(reverb(bend(k.scrape_chord([138.6, 146.8, 196.0], 3.8, 1), 1.0, 0.82), 2.2, 0.45, 12), 2.1, 0.55,
              name='tuned metal cluster bending down')
    elif v == 1:
        T = Track(6.5)
        for i, at in enumerate((0.0, 0.21, 0.52)):
            T.add(k.static_burst(0.09 + 0.03 * i, 20 + i), at, 0.45, name='static stutter' if i == 0 else None)
        x = k.pa(k.chime(MOTIF[0], cents=-25.0, slow=2.0))
        T.add(reverb(x, 3.0, 0.6, 21), 0.85, 0.75, name='first chime note at half speed')
        T.add(k.drone([65.4, 69.3], 5.0), 1.0, 0.55, name='drone C2/C#2')
        T.cut(5.6)
    else:
        T = Track(6.5)
        T.add(k.breath(1.4, True, 30), 0.0, 0.55, name='breath in')
        T.cut(1.4)
        T.add(reverb(k.bent_horn(0.8, 0.5), 2.8, 0.7, 31), 1.85, 0.5, 0.5, name='horn bent down')
        T.add(reverb(k.scrape_chord([155.6, 164.8, 233.1], 4.0, 2), 2.0, 0.4, 32), 2.2, 0.45, -0.4,
              name='tuned metal cluster')
    return T


def cue_round_end(k, v):
    T = Track(6.5)
    T.add(k.breath(3.4, False, 40 + v), 0.0, 0.6, 0.0, name='breath out (sigh)')
    if v == 0:
        box = k.music_box([BOX[-2], BOX[-1] - 0.5], root=880.0, step=0.9, drift_cents=-60.0)
        T.add(reverb(box, 2.2, 0.35, 41), 0.9, 0.6, 0.3, name='music box, last two notes, sinking')
    elif v == 1:
        x = np.concatenate([k.chime(MOTIF[1], -20.0, 2.4), np.zeros(sec(0.2)), k.chime(MOTIF[1] - 1, -20.0, 2.8)])
        T.add(reverb(k.pa(x, 1.4), 3.2, 0.6, 42), 0.7, 0.55, name='chime falling a semitone, slowed')
    else:
        T.add(reverb(k.scrape_chord([110.0, 116.5, 155.6], 4.5, 3), 3.0, 0.5, 43), 0.5, 0.5, name='metal cluster decaying')
        T.add(k.static_burst(0.8, 44) * np.linspace(0, 0.5, sec(0.8)), 4.6, 0.4, name='static whisper')
    T.add(k.drone([55.0, 58.3], 5.5, 9.0), 0.4, 0.35, name='low drone dissolving')
    return T


def cue_event_start(k, v):
    T = Track(7.0)
    T.add(k.thud(80, 30), 0.0, 0.8, name='sub thud')
    T.add(reverb(k.bent_horn(1.0, 0.45 if v == 0 else 0.6), 2.6, 0.6, 50 + v), 0.15, 0.6, -0.3 + 0.6 * v,
          name='horn bent down')
    for i, at in enumerate((1.6, 1.75, 2.3, 2.38)):
        T.add(k.static_burst(0.07, 52 + i + 4 * v), at, 0.4, name='static stutter' if i == 0 else None)
    chord = [130.8, 138.6, 185.0] if v == 0 else [123.5, 130.8, 174.6]
    T.add(reverb(k.scrape_chord(chord, 4.5, v), 2.0, 0.4, 56), 2.0, 0.6, name='tuned metal cluster')
    T.add(k.thud(60, 28), 2.9, 0.55)
    T.cut(6.4)
    return T


def cue_event_end(k):
    T = Track(7.0)
    seq = np.zeros(sec(3.4))
    for j, (s, at) in enumerate(zip(MOTIF[::-1], (0.0, 0.9, 1.8))):
        x = k.chime(s, -35.0 * j, 1.8)[::-1]
        a = sec(at)
        seq[a:a + len(x)] += x[:len(seq) - a]
    T.add(reverb(k.pa(seq, 1.5), 3.0, 0.6, 60), 0.3, 0.6, name='motif backwards, reversed strikes, slowed')
    T.add(k.drone([61.7, 65.4, 92.5], 6.5, 8.0), 0.0, 0.4, name='drone B1/C2/F#2')
    T.add(k.breath(3.0, False, 61), 3.6, 0.45, name='breath out')
    return T


def cue_gameover(k):
    T = Track(15.0)
    box = k.music_box(BOX + [BOX[0]], root=880.0, step=0.55, drift_cents=-140.0, slow_end=3.2, drop=(len(BOX),))
    T.add(reverb(box, 2.4, 0.35, 70), 0.3, 0.65, 0.2, name='music box phrase winding down (-140 cents, 3.2x slower), last note missing')
    T.add(k.drone([49.0, 51.9, 73.4], 11.0, 6.0), 1.5, 0.45, name='drone G1/G#1/D2')
    T.add(k.sub_rumble(8.0), 4.0, 0.4, name='rumble')
    T.add(k.static_burst(0.7, 71), 11.2, 0.35, name='static')
    T.cut(11.9)
    far = reverb(k.pa(k.chime(MOTIF[2], -80.0, 1.4), 1.3), 4.0, 0.8, 72)
    T.add(far, 13.2, 0.25, 0.6, name='one far chime note, 80 cents flat')
    return T


def cue_power(k):
    T = Track(11.5)
    T.add(k.static_burst(0.35, 80), 0.0, 0.5, name='PA crackles on')
    clean = np.zeros(sec(3.0))
    for s, at in zip(MOTIF, (0.0, 0.55, 1.1)):
        x = k.chime(s)
        a = sec(at)
        clean[a:a + len(x)] += x[:len(clean) - a]
    T.add(reverb(k.pa(clean, 1.3), 2.8, 0.45, 81), 0.45, 0.7, name='PA chime as designed (the only clean statement)')
    wrong = np.zeros(sec(4.5))
    for j, (s, at) in enumerate(zip(MOTIF, (0.0, 0.8, 1.7))):
        x = k.chime(s, cents=(-20.0, -45.0, -95.0)[j], slow=1.25 + 0.25 * j)
        a = sec(at)
        wrong[a:a + len(x)] += x[:len(wrong) - a]
    T.add(reverb(k.pa(wrong, 1.6), 3.2, 0.55, 82), 3.4, 0.6, name='repeat, each strike flatter and slower')
    T.add(k.drone([73.4, 103.8], 7.5, 5.0), 3.0, 0.45, name='drone D2 + G#2 (tritone)')
    T.add(reverb(k.scrape_chord([146.8, 207.7, 220.0], 4.0, 1), 2.5, 0.4, 83), 6.4, 0.35, -0.5,
          name='tuned metal (tritone + minor second)')
    T.cut(10.6)
    return T


def cue_ee_activate(k):
    tine = k.tine(880.0 * 2 ** (2 / 12.0), 1.6, -20.0)
    rev = reverb(tine, 1.8, 0.6, 90)
    r = am.mono(rev)[::-1]
    r = fade(r[-sec(1.2):], 0.8, 0.0)
    x = np.concatenate([r, k.tine(880.0 * 2 ** (-5 / 12.0), 1.2, -35.0)])
    return norm(filt(x, 'low', 4000, 2), 0.8)


# ---------------------------------------------------------------- loudness
def active_rms(x, floor=-45.0):
    m = am.mono(x) if np.asarray(x).ndim == 2 else x
    n = sec(0.1)
    lv = np.array([am.dbfs(m[i:i + n]) for i in range(0, len(m) - n + 1, n)])
    act = lv[lv > floor]
    return float(10 * np.log10(np.mean(10 ** (act / 10)))) if len(act) else -200.0


def finish(x, level, ceiling):
    x = np.asarray(x, np.float64)
    g = 10 ** ((level - active_rms(x)) / 20.0)
    y = x * g
    pk = float(np.max(np.abs(y)))
    lim = 10 ** (ceiling / 20.0)
    if pk > lim:                                   # soft ceiling: tanh above it keeps transients from clipping
        y = np.tanh(y / lim) * lim
    return fade(y, 0.0, 0.02)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    ap.add_argument('--out', required=True)
    ap.add_argument('--chime', required=True)
    ap.add_argument('--static', required=True)
    ap.add_argument('--horn', required=True)
    ap.add_argument('--rumble', required=True)
    ap.add_argument('--metal', required=True, nargs='+')
    ap.add_argument('--breath')
    ap.add_argument('--seed', type=int, default=26)
    ap.add_argument('--level', type=float, default=-20.0, help='active RMS of every cue (dBFS)')
    ap.add_argument('--ceiling', type=float, default=-3.0, help='peak ceiling (dBFS)')
    ap.add_argument('--wav', help='also write WAV copies here (the owner listening pack)')
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    k = Kit(a)
    cues = [('intro', 'mus_iwz_intro', lambda: cue_intro(k))]
    cues += [('round_start_%d' % v, 'mus_zombies_newwave', (lambda v=v: cue_round_start(k, v))) for v in range(3)]
    cues += [('round_end_%d' % v, 'mus_zombies_endwave', (lambda v=v: cue_round_end(k, v))) for v in range(3)]
    cues += [('event_start_%d' % v, 'mus_zombies_eventwave_start', (lambda v=v: cue_event_start(k, v))) for v in range(2)]
    cues += [('event_end_0', 'mus_zombies_eventwave_end', lambda: cue_event_end(k)),
             ('gameover', 'mus_zombies_gameover', lambda: cue_gameover(k)),
             ('power_on', 'mus_iwz_power', lambda: cue_power(k))]
    report = {'seed': a.seed, 'level_dbfs': a.level, 'ceiling_dbfs': a.ceiling, 'chime_strike_hz': k.strike_hz,
              'motif_semitones': MOTIF, 'music_box_degrees': BOX, 'sources': k.sources, 'cues': []}
    for name, alias, make in cues:
        T = make()
        y = finish(T.buf, a.level, a.ceiling)
        path = os.path.join(a.out, name + '.flac')
        write_flac(path, y)
        if a.wav:
            os.makedirs(a.wav, exist_ok=True)
            write_wav(os.path.join(a.wav, name + '.wav'), y)
        report['cues'].append({'cue': name, 'alias': alias, 'file': path, 'seconds': round(len(y) / R, 2),
                               'active_rms_dbfs': round(active_rms(y), 1), 'peak_dbfs': round(20 * np.log10(np.max(np.abs(y)) + 1e-12), 1),
                               'made_of': T.parts})
    y = finish(cue_ee_activate(k), a.level + 2, a.ceiling)
    path = os.path.join(a.out, 'ee_activate.flac')
    write_flac(path, y)
    if a.wav:
        write_wav(os.path.join(a.wav, 'ee_activate.wav'), y)
    report['cues'].append({'cue': 'ee_activate', 'alias': 'zmb_iwz_ee_activate', 'file': path, 'seconds': round(len(y) / R, 2),
                           'active_rms_dbfs': round(active_rms(y), 1), 'peak_dbfs': round(20 * np.log10(np.max(np.abs(y)) + 1e-12), 1),
                           'made_of': ['reversed music-box tine with its room (synth)', 'one tine a fourth below, flat']})
    with open(os.path.join(a.out, 'cues.json'), 'w') as f:
        json.dump(report, f, indent=1)
    for c in report['cues']:
        print('%-14s %-28s %5.2f s  active %6.1f  peak %5.1f' % (c['cue'], c['alias'], c['seconds'], c['active_rms_dbfs'], c['peak_dbfs']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
