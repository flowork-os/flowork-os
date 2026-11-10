#!/usr/bin/env python3
"""
👑 FLOWORK OS — EARSHOT PROCEDURAL AUDIO DSP ENGINE (earshot_engine.py)
Pure Python & NumPy Procedural Audio Synthesizer, Sound Bank, and Acoustic Critic.
Zero external audio buffer dependencies (CPU-only synthesis).

Universal root: /opt/floworkos
Author: Flowork Architecture Board & Dr. Flow
"""

import os
import sys
import math
import wave
import struct
import shutil
import subprocess
import numpy as np

SAMPLE_RATE = 44100


def save_wav(filename, samples, sample_rate=SAMPLE_RATE):
    """Write 1-channel or 2-channel float samples (-1.0 to 1.0) into 16-bit PCM WAV."""
    os.makedirs(os.path.dirname(os.path.abspath(filename)), exist_ok=True)
    # Clip to valid range
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767.0).astype(np.int16)

    channels = 1 if len(samples.shape) == 1 else samples.shape[1]
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(sample_rate)
        wf.writeframes(int_samples.tobytes())
    return filename


class ProceduralSoundBank:
    """Library of procedural mathematical sound recipes for Flowork OS."""

    @staticmethod
    def click(duration=0.015, pitch=1200.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        envelope = np.exp(-t * 250.0)
        noise = (np.random.rand(len(t)) * 2 - 1) * 0.4
        tone = np.sin(2 * np.pi * pitch * t) * 0.6
        return (tone + noise) * envelope

    @staticmethod
    def pop(duration=0.04, freq_start=700.0, freq_end=220.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        freq = np.linspace(freq_start, freq_end, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        envelope = np.exp(-t * 120.0)
        return np.sin(phase) * envelope

    @staticmethod
    def bell(duration=0.45, pitch=880.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        # Modal resonators: fundamental + non-harmonic partials
        p1 = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 12.0)
        p2 = np.sin(2 * np.pi * (pitch * 2.76) * t) * np.exp(-t * 18.0) * 0.4
        p3 = np.sin(2 * np.pi * (pitch * 5.40) * t) * np.exp(-t * 26.0) * 0.2
        return (p1 + p2 + p3) * 0.65

    @staticmethod
    def success(duration=0.35, root_freq=523.25):  # C5 major triad shimmer
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        # 3 arpeggiated notes: C5 (523Hz), E5 (659Hz), G5 (784Hz)
        chord = np.zeros_like(t)
        notes = [(root_freq, 0.0), (root_freq * 1.2599, 0.06), (root_freq * 1.4983, 0.12)]
        for freq, delay in notes:
            mask = t >= delay
            t_sub = t[mask] - delay
            env = np.exp(-t_sub * 14.0)
            tone = np.sin(2 * np.pi * freq * t_sub)
            harmonic = np.sin(4 * np.pi * freq * t_sub) * 0.25
            chord[mask] += (tone + harmonic) * env * 0.45
        return chord

    @staticmethod
    def error(duration=0.25, freq1=180.0, freq2=220.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        env = np.exp(-t * 10.0)
        # Dissonant minor second pulse
        tone1 = np.sin(2 * np.pi * freq1 * t)
        tone2 = np.sin(2 * np.pi * freq2 * t)
        return (tone1 + tone2) * env * 0.5

    @staticmethod
    def whoosh(duration=0.22, freq_center=800.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = (np.random.rand(len(t)) * 2 - 1)
        # Smooth hanning/bell envelope
        envelope = np.sin(np.pi * (t / duration)) ** 2
        # Modulation
        mod = np.sin(2 * np.pi * (freq_center * (1.0 - t / duration)) * t) * 0.2
        return (noise * 0.7 + mod) * envelope

    @staticmethod
    def shutter(duration=0.08):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        res = np.zeros_like(t)
        # Click 1
        t1 = t[t < 0.03]
        res[t < 0.03] = ((np.random.rand(len(t1)) * 2 - 1) * 0.5 + np.sin(2 * np.pi * 1400 * t1) * 0.5) * np.exp(-t1 * 200.0)
        # Click 2
        t2_mask = t >= 0.035
        t2 = t[t2_mask] - 0.035
        res[t2_mask] = ((np.random.rand(len(t2)) * 2 - 1) * 0.4 + np.sin(2 * np.pi * 1800 * t2) * 0.6) * np.exp(-t2 * 220.0)
        return res

    @staticmethod
    def laser(duration=0.18, freq_start=1800.0, freq_end=120.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        freq = freq_start * ((freq_end / freq_start) ** (t / duration))
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        envelope = np.exp(-t * 18.0)
        # Slightly saturated square/saw mix
        wave_sig = np.sin(phase) + 0.3 * np.sin(3 * phase)
        return np.clip(wave_sig * 1.5, -1.0, 1.0) * envelope * 0.7

    @staticmethod
    def glass_tap(duration=0.30, pitch=1420.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        # Sovereign Quantum Glass HUD high-Q impulse
        p1 = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 18.0)
        p2 = np.sin(2 * np.pi * (pitch * 2.05) * t) * np.exp(-t * 24.0) * 0.35
        p3 = np.sin(2 * np.pi * (pitch * 3.12) * t) * np.exp(-t * 32.0) * 0.15
        return (p1 + p2 + p3) * 0.65


CATALOG = {
    "click": {"desc": "Subtle UI mechanical click", "func": ProceduralSoundBank.click},
    "pop": {"desc": "Dock hover / bubble pop", "func": ProceduralSoundBank.pop},
    "bell": {"desc": "Metallic chime / terminal bell", "func": ProceduralSoundBank.bell},
    "success": {"desc": "Task completion / cyber major triad", "func": ProceduralSoundBank.success},
    "error": {"desc": "Dissonant alert / task failure", "func": ProceduralSoundBank.error},
    "whoosh": {"desc": "Smooth air sweep / window transition", "func": ProceduralSoundBank.whoosh},
    "shutter": {"desc": "Screen capture / camera shutter", "func": ProceduralSoundBank.shutter},
    "laser": {"desc": "Sci-fi laser blaster / retro beep", "func": ProceduralSoundBank.laser},
    "glass_tap": {"desc": "Sovereign Quantum Glass HUD tap", "func": ProceduralSoundBank.glass_tap}
}


def render_sound(name, output_path=None, **kwargs):
    """Render procedural sound by name to WAV file."""
    if name not in CATALOG:
        raise ValueError(f"Unknown sound '{name}'. Available: {list(CATALOG.keys())}")

    func = CATALOG[name]["func"]
    samples = func(**kwargs) if kwargs else func()

    if not output_path:
        output_path = f"/opt/floworkos/sounds/{name}.wav"

    return save_wav(output_path, samples)


def play_sound(name_or_file):
    """Play sound file or procedural sound directly via PipeWire / PulseAudio."""
    if os.path.isfile(name_or_file):
        wav_path = name_or_file
    else:
        wav_path = f"/tmp/flowork_sfx_{name_or_file}.wav"
        render_sound(name_or_file, output_path=wav_path)

    # Play non-blocking or short blocking
    players = ["pw-play", "paplay", "ffplay"]
    for p in players:
        if shutil.which(p):
            if p == "ffplay":
                cmd = [p, "-nodisp", "-autoexit", "-loglevel", "quiet", wav_path]
            else:
                cmd = [p, wav_path]
            try:
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2.0)
                return True
            except Exception:
                continue
    return False


def audit_audio_file(wav_path):
    """Inspect WAV audio quality: clipping, DC offset, peak dBFS, duration."""
    if not os.path.exists(wav_path):
        return {"error": f"File does not exist: {wav_path}"}

    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        width = wf.getsampwidth()
        rate = wf.getframerate()
        frames = wf.getnframes()
        duration = frames / float(rate)
        raw_bytes = wf.readframes(frames)

    if width == 2:
        samples = np.frombuffer(raw_bytes, dtype=np.int16).astype(np.float32) / 32768.0
    elif width == 1:
        samples = (np.frombuffer(raw_bytes, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    else:
        samples = np.frombuffer(raw_bytes, dtype=np.int32).astype(np.float32) / 2147483648.0

    peak = float(np.max(np.abs(samples))) if len(samples) > 0 else 0.0
    dc_offset = float(np.mean(samples)) if len(samples) > 0 else 0.0
    rms = float(np.sqrt(np.mean(samples ** 2))) if len(samples) > 0 else 0.0
    peak_dbfs = 20 * math.log10(peak) if peak > 1e-6 else -99.0
    rms_dbfs = 20 * math.log10(rms) if rms > 1e-6 else -99.0

    clipped_samples = int(np.sum(np.abs(samples) >= 0.999))
    has_clipping = clipped_samples > 0

    return {
        "file": wav_path,
        "duration_seconds": round(duration, 3),
        "sample_rate": rate,
        "channels": channels,
        "peak_amplitude": round(peak, 4),
        "peak_dbfs": round(peak_dbfs, 2),
        "rms_dbfs": round(rms_dbfs, 2),
        "dc_offset": round(dc_offset, 5),
        "clipped_samples": clipped_samples,
        "status": "warning_clipping" if has_clipping else ("warning_dc_offset" if abs(dc_offset) > 0.02 else "clean")
    }
