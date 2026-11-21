#!/usr/bin/env python3
"""
FLOWORK OS CARTOON INSTRUMENT & DSP SYNTHESIZER
Ported and enhanced from procedural additive/modal synthesis:
- Brass (tuba, horn, stabs)
- Mallets & Bells (glockenspiel, vibes)
- Percussion (field snare, buzz rolls, crash cymbal, timpani)
- Human Whistle & Fife
- 100% Procedural NumPy & SciPy (Zero samples, zero external audio assets, zero copyright)
"""

import numpy as np
from scipy import signal

SR = 48000
TAU = 2 * np.pi

def ns(t):
    return int(round(t * SR))

def tt(dur):
    return np.arange(ns(dur)) / SR

def dbg(db):
    return 10.0 ** (db / 20.0)

def rng(seed=0):
    return np.random.default_rng(seed)

def m2f(m):
    """MIDI note number to frequency in Hz (69 = A440)"""
    return 440.0 * 2 ** ((m - 69) / 12.0)

# ---------------------------------------------------------------- Filters
def _sos(kind, f, order=2):
    return signal.butter(order, f, btype=kind, fs=SR, output="sos")

def lp(x, f, order=2):
    return signal.sosfilt(_sos("lowpass", min(f, SR * 0.45), order), x, axis=-1)

def hp(x, f, order=2):
    return signal.sosfilt(_sos("highpass", f, order), x, axis=-1)

def bp(x, lo, hi, order=2):
    return signal.sosfilt(_sos("bandpass", [lo, min(hi, SR * 0.45)], order), x, axis=-1)

def biquad(kind, f0, q=0.707, gain_db=0.0):
    A = 10 ** (gain_db / 40)
    w = TAU * f0 / SR
    cw, sw = np.cos(w), np.sin(w)
    al = sw / (2 * q)
    if kind == "peak":
        b = [1 + al * A, -2 * cw, 1 - al * A]
        a = [1 + al / A, -2 * cw, 1 - al / A]
    elif kind == "bpf":
        b = [al, 0.0, -al]
        a = [1 + al, -2 * cw, 1 - al]
    else:
        raise ValueError(kind)
    a = np.array(a, float)
    return np.array(b, float) / a[0], a / a[0]

def peq(x, f0, gain_db, q=1.0):
    b, a = biquad("peak", f0, q, gain_db)
    return signal.lfilter(b, a, x, axis=-1)

def smooth_noise(n, r, rate_hz, ctrl=200):
    m = max(4, int(n / SR * ctrl) + 4)
    c = r.standard_normal(m)
    c = signal.sosfiltfilt(signal.butter(2, min(rate_hz / (ctrl / 2), 0.99), output="sos"), c)
    c /= np.max(np.abs(c)) + 1e-12
    return np.interp(np.arange(n) / SR * ctrl, np.arange(m), c)

def ramp(n, kind="cos"):
    u = np.linspace(0, 1, max(n, 1))
    return 0.5 - 0.5 * np.cos(np.pi * u) if kind == "cos" else u

def fades(x, fin=0.003, fout=0.01):
    x = np.array(x, dtype=float, copy=True)
    a, b = ns(fin), ns(fout)
    n = x.shape[-1]
    if a > 0:
        x[..., : min(a, n)] *= ramp(a)[: min(a, n)]
    if b > 0:
        x[..., max(0, n - b):] *= ramp(b)[::-1][-min(b, n):]
    return x

def phase(f):
    return TAU * np.cumsum(f) / SR

def modal(dur, modes, r=None, glide=0.0, glide_tau=0.02):
    t = tt(dur)
    y = np.zeros_like(t)
    g = 1 + glide * np.exp(-t / glide_tau) if glide else None
    for m in modes:
        f, a, tau = m[0], m[1], m[2]
        if f >= SR * 0.45:
            continue
        ph0 = r.uniform(0, TAU) if r is not None else 0.0
        if g is None:
            y += a * np.exp(-t / tau) * np.sin(TAU * f * t + ph0)
        else:
            y += a * np.exp(-t / tau) * np.sin(phase(f * g) + ph0)
    return y

def _env(n, att, dur_n, rel, curve=1.5):
    e = np.ones(n)
    a = max(1, ns(att))
    e[:a] = np.linspace(0, 1, a) ** curve
    if dur_n < n:
        e[dur_n:] *= np.linspace(1, 0, n - dur_n) ** 2
    return e

# ---------------------------------------------------------------- Brass & Tuba
def brass(f, dur, vel=0.8, r=None, kind="tuba", scoop=-22.0, rel=0.07, fall=0.0):
    """Additive brass: tuba bassline, horn after-beats, sharp stabs"""
    r = r or rng(0)
    n = ns(dur + rel)
    t = np.arange(n) / SR
    att = {"tuba": 0.035, "horn": 0.025, "stab": 0.012, "soft": 0.09}.get(kind, 0.03)
    env = _env(n, att, ns(dur), rel)
    env *= 1 + (0.25 if kind == "stab" else 0.14) * vel * np.exp(-((t - att) / 0.035) ** 2)
    env *= (0.72 if kind == "stab" else 0.85) + (0.28 if kind == "stab" else 0.15) * np.exp(-t / (0.09 if kind == "stab" else 0.16))
    cents = scoop * np.exp(-t / 0.03) + 4 * smooth_noise(n, r, 3.0)
    if fall:
        cents += fall * 100 * np.clip((t - dur * 0.55) / (dur * 0.45 + rel), 0, 1) ** 2
    ph = phase(f * 2 ** (cents / 1200))
    form = {"tuba": (420, 260), "horn": (900, 450), "stab": (1100, 700), "soft": (380, 220)}.get(kind, (500, 300))
    top = {"tuba": 2400, "horn": 5000, "stab": 7000, "soft": 1500}.get(kind, 3000)
    K = max(1, int(min(48, top / max(1.0, f))))
    bc = (1.8 + 6.5 * vel * env ** 1.4) * (1.3 if kind == "stab" else 1.0)
    y = np.zeros(n)
    for k in range(1, K + 1):
        fk = k * f
        ak = k ** -0.75 / (1 + (k / bc) ** 3) * (1 + 1.2 * np.exp(-((fk - form[0]) / form[1]) ** 2))
        y += ak * np.sin(k * ph + r.uniform(0, TAU))
    nz = bp(r.standard_normal(n), 300, 3000, 1) * np.exp(-t / 0.02) * 0.04 * vel
    return (y * env + nz) * vel

# ---------------------------------------------------------------- Mallets & Bells
def glock(f, vel=0.7, r=None, dur=1.8):
    """Glockenspiel / Cartoon Chime: modal metallic bell with stick click"""
    r = r or rng(0)
    t = tt(dur)
    k = (880.0 / max(1.0, f)) ** 0.35
    y = modal(dur, [(f, 1.0, 1.25 * k), (f * 2.756, 0.30 * vel, 0.22 * k), (f * 5.404, 0.12 * vel, 0.07), (f * 8.933, 0.05 * vel, 0.025)], r)
    click = hp(r.standard_normal(len(t)), 3000) * np.exp(-t / 0.0007) * 0.25 * vel
    return fades((y + click) * vel, 0.0005, 0.05)

# ---------------------------------------------------------------- Drums & Percussion
def snare(vel=0.8, r=None, dur=0.34, tune=1.0, snappy=1.0, buzz=False):
    """Field snare: body modes + snappy wire hiss + stick click"""
    r = r or rng(0)
    n = ns(dur)
    t = np.arange(n) / SR
    f0 = 196 * tune * (1 + 0.07 * vel * np.exp(-t / 0.01))
    ph = phase(f0)
    body = (0.9 * np.exp(-t / 0.05) * np.sin(ph) + 0.5 * np.exp(-t / 0.035) * np.sin(1.593 * ph + 1)
            + 0.3 * np.exp(-t / 0.028) * np.sin(2.136 * ph + 2) + 0.22 * np.exp(-t / 0.022) * np.sin(2.296 * ph + 0.5)
            + 0.14 * np.exp(-t / 0.018) * np.sin(2.653 * ph + 1.3))
    nz = r.standard_normal(n)
    tail = 0.055 + 0.07 * vel if not buzz else 0.035
    wires = bp(nz, 1700, 10500, 2) * np.exp(-t / tail) * (1 - np.exp(-t / 0.0012))
    wires = peq(wires, 4200, 3, 0.8)
    click = hp(r.standard_normal(n), 2500) * np.exp(-t / 0.0007)
    y = 0.55 * body * vel ** 1.2 + 0.85 * snappy * wires * vel ** 1.15 + 0.3 * click * vel
    return fades(y, 0.0002, 0.02)

def cymbal(vel=0.7, r=None, dur=2.4, bright=1.0):
    """Clash Cymbal: dense inharmonic partials + shimmer hiss"""
    r = r or rng(0)
    n = ns(dur)
    t = np.arange(n) / SR
    y = np.zeros(n)
    fs = np.exp(r.uniform(np.log(380), np.log(12500), 120))
    for f in fs:
        tau = 1.6 * (900 / f) ** 0.45
        y += r.uniform(0.3, 1.0) * np.exp(-t / tau) * np.sin(TAU * f * t + r.uniform(0, TAU)) / np.sqrt(120)
    hiss = hp(r.standard_normal(n), 5200, 2) * np.exp(-t / (0.7 * bright)) * 0.6
    y = (y + hiss) * (1 - np.exp(-t / 0.002))
    y += bp(r.standard_normal(n), 2000, 9000, 1) * np.exp(-t / 0.006) * 0.8
    return fades(y * vel, 0.0005, 0.2)

def timpani(f=82.4, vel=0.8, r=None, dur=2.0):
    """Timpani / Cartoon Boom Thump"""
    r = r or rng(0)
    t = tt(dur)
    modes = [(f, 1.0, 1.5), (f * 1.504, 0.55, 0.9), (f * 1.742, 0.3, 0.6), (f * 2.0, 0.35, 0.5)]
    y = modal(dur, modes, r, glide=0.025 * vel, glide_tau=0.06)
    thump = lp(r.standard_normal(len(t)), 400, 2) * np.exp(-t / 0.018) * 0.9
    return fades((y + thump) * vel, 0.001, 0.1)
