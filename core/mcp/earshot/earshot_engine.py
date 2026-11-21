#!/usr/bin/env python3
"""
👑 FLOWORK OS — EARSHOT PROCEDURAL AUDIO DSP ENGINE (earshot_engine.py)
Pure Python & NumPy Procedural Audio Synthesizer, Sound Bank, and Acoustic Critic.
Zero external audio buffer dependencies (CPU-only mathematical synthesis).

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
    samples = np.clip(samples, -1.0, 1.0)
    int_samples = (samples * 32767.0).astype(np.int16)

    channels = 1 if len(samples.shape) == 1 else samples.shape[1]
    with wave.open(filename, "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
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
    def thock(duration=0.08, pitch=260.0):
        """Deep mechanical keyboard keypress with housing resonance."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        env = np.exp(-t * 60.0)
        tone1 = np.sin(2 * np.pi * pitch * t) * 0.7
        tone2 = np.sin(2 * np.pi * (pitch * 1.6) * t) * 0.25
        snap = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 300.0) * 0.35
        return (tone1 + tone2 + snap) * env

    @staticmethod
    def knock(duration=0.10, pitch=380.0):
        """Solid wood door/surface knock with warm hollow body."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        env = np.exp(-t * 50.0)
        tone = np.sin(2 * np.pi * pitch * t) * 0.8
        sub = np.sin(2 * np.pi * (pitch * 0.5) * t) * 0.3
        impact = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 220.0) * 0.25
        return (tone + sub + impact) * env

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
        envelope = np.exp(-t * 9.0)
        p1 = np.sin(2 * np.pi * pitch * t)
        p2 = np.sin(2 * np.pi * (pitch * 2.76) * t) * 0.3
        p3 = np.sin(2 * np.pi * (pitch * 5.4) * t) * 0.15
        return (p1 + p2 + p3) * envelope * 0.6

    @staticmethod
    def success(duration=0.55, root_freq=523.25):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
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
        tone1 = np.sin(2 * np.pi * freq1 * t)
        tone2 = np.sin(2 * np.pi * freq2 * t)
        return (tone1 + tone2) * env * 0.5

    @staticmethod
    def whoosh(duration=0.22, freq_center=800.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = (np.random.rand(len(t)) * 2 - 1)
        envelope = np.sin(np.pi * (t / duration)) ** 2
        mod = np.sin(2 * np.pi * (freq_center * (1.0 - t / duration)) * t) * 0.2
        return (noise * 0.7 + mod) * envelope

    @staticmethod
    def swish(duration=0.15):
        """Fast bright swish/cut swipe."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = (np.random.rand(len(t)) * 2 - 1)
        env = np.sin(np.pi * (t / duration)) ** 3
        high_tone = np.sin(2 * np.pi * np.linspace(2400, 600, len(t)) * t) * 0.3
        return (noise * 0.7 + high_tone) * env

    @staticmethod
    def sub_hit(duration=0.35, freq_start=110.0, freq_end=38.0):
        """Low-frequency cinematic punch / bass hit for video cut emphasis."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        freq = np.linspace(freq_start, freq_end, len(t))
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        env = np.exp(-t * 12.0)
        click = (np.random.rand(len(t)) * 2 - 1) * np.exp(-t * 250.0) * 0.3
        return (np.sin(phase) + click) * env * 0.9

    @staticmethod
    def riser(duration=0.80, start_freq=180.0, end_freq=1600.0):
        """Exponential audio riser for scene build-ups and transitions."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        freq = start_freq * ((end_freq / start_freq) ** (t / duration))
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        env = (t / duration) ** 2
        noise = (np.random.rand(len(t)) * 2 - 1) * 0.15 * env
        return (np.sin(phase) * 0.85 + noise) * env

    @staticmethod
    def chime_run(duration=0.60):
        """Sparkling pentatonic celestial chime sweep."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        sig = np.zeros_like(t)
        freqs = [880.0, 987.77, 1174.66, 1318.51, 1567.98, 1760.0]
        step = duration / (len(freqs) + 1)
        for i, f in enumerate(freqs):
            delay = (i + 1) * (step * 0.7)
            mask = t >= delay
            t_sub = t[mask] - delay
            env = np.exp(-t_sub * 16.0)
            sig[mask] += (np.sin(2 * np.pi * f * t_sub) + 0.2 * np.sin(4 * np.pi * f * t_sub)) * env * 0.25
        return sig

    @staticmethod
    def water_drop(duration=0.18, freq_start=1400.0, freq_end=600.0):
        """Liquid water droplet plop."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        freq = freq_start * np.exp(-t * 22.0) + freq_end
        phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
        env = np.sin(np.pi * np.clip(t / duration, 0, 1)) * np.exp(-t * 18.0)
        return np.sin(phase) * env

    @staticmethod
    def glitch(duration=0.12):
        """Cyber bitcrushed audio glitch burst."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = (np.random.rand(len(t)) * 2 - 1)
        # Quantize / bitcrush
        noise = np.round(noise * 4.0) / 4.0
        square = np.sign(np.sin(2 * np.pi * 440 * t)) * 0.4
        env = np.exp(-t * 30.0)
        return (noise * 0.6 + square) * env

    @staticmethod
    def reverse_cymbal(duration=0.75):
        """Reverse rising cymbal / suction sweep."""
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        noise = (np.random.rand(len(t)) * 2 - 1)
        env = ((t / duration) ** 3)
        tone = np.sin(2 * np.pi * 2200 * t) * 0.1 * env
        return (noise * 0.8 + tone) * env

    @staticmethod
    def shutter(duration=0.08):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        res = np.zeros_like(t)
        t1 = t[t < 0.03]
        res[t < 0.03] = ((np.random.rand(len(t1)) * 2 - 1) * 0.5 + np.sin(2 * np.pi * 1400 * t1) * 0.5) * np.exp(-t1 * 200.0)
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
        wave_sig = np.sin(phase) + 0.3 * np.sin(3 * phase)
        return np.clip(wave_sig * 1.5, -1.0, 1.0) * envelope * 0.7

    @staticmethod
    def glass_tap(duration=0.30, pitch=1420.0):
        t = np.linspace(0, duration, int(SAMPLE_RATE * duration), endpoint=False)
        p1 = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 18.0)
        p2 = np.sin(2 * np.pi * (pitch * 2.05) * t) * np.exp(-t * 24.0) * 0.35
        p3 = np.sin(2 * np.pi * (pitch * 3.12) * t) * np.exp(-t * 32.0) * 0.15
        return (p1 + p2 + p3) * 0.65


CATALOG = {
    "click": {"desc": "Subtle UI mechanical click", "func": ProceduralSoundBank.click},
    "thock": {"desc": "Deep mechanical keyboard keypress", "func": ProceduralSoundBank.thock},
    "knock": {"desc": "Organic solid wood knock", "func": ProceduralSoundBank.knock},
    "pop": {"desc": "Dock hover / bubble pop", "func": ProceduralSoundBank.pop},
    "bell": {"desc": "Metallic chime / terminal bell", "func": ProceduralSoundBank.bell},
    "success": {"desc": "Task completion / cyber major triad", "func": ProceduralSoundBank.success},
    "error": {"desc": "Dissonant alert / task failure", "func": ProceduralSoundBank.error},
    "whoosh": {"desc": "Smooth air sweep / window transition", "func": ProceduralSoundBank.whoosh},
    "swish": {"desc": "Fast cutting blade / whip swipe", "func": ProceduralSoundBank.swish},
    "sub_hit": {"desc": "Low-frequency 40Hz punch for video cuts", "func": ProceduralSoundBank.sub_hit},
    "riser": {"desc": "Exponential build-up tension riser", "func": ProceduralSoundBank.riser},
    "chime_run": {"desc": "Sparkling celestial pentatonic chime run", "func": ProceduralSoundBank.chime_run},
    "water_drop": {"desc": "Liquid water droplet plop", "func": ProceduralSoundBank.water_drop},
    "glitch": {"desc": "Cyber bitcrushed audio glitch burst", "func": ProceduralSoundBank.glitch},
    "reverse_cymbal": {"desc": "Reverse rising cymbal suction sweep", "func": ProceduralSoundBank.reverse_cymbal},
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

    players = ["pw-play", "paplay", "ffplay"]
    for p in players:
        if shutil.which(p):
            try:
                cmd = [p, wav_path]
                if p == "ffplay":
                    cmd = [p, "-nodisp", "-autoexit", "-loglevel", "quiet", wav_path]
                subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True
            except Exception:
                continue
    return False


def audit_audio_file(filepath):
    """Calculates RMS, Peak dBFS, duration, and DC offset for quality verification."""
    if not os.path.isfile(filepath):
        return {"error": f"File not found: {filepath}"}

    try:
        with wave.open(filepath, "rb") as wf:
            n_frames = wf.getnframes()
            rate = wf.getframerate()
            duration = n_frames / float(rate)
            raw = wf.readframes(n_frames)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0

        peak = np.max(np.abs(samples)) if len(samples) > 0 else 0.0
        peak_dbfs = 20 * np.log10(peak) if peak > 0 else -100.0
        rms = np.sqrt(np.mean(samples**2)) if len(samples) > 0 else 0.0
        rms_dbfs = 20 * np.log10(rms) if rms > 0 else -100.0
        dc_offset = np.mean(samples) if len(samples) > 0 else 0.0

        return {
            "duration_seconds": round(duration, 3),
            "sample_rate": rate,
            "peak_dbfs": round(float(peak_dbfs), 2),
            "rms_dbfs": round(float(rms_dbfs), 2),
            "dc_offset": round(float(dc_offset), 5),
            "status": "HEALTH_OK" if peak <= 1.0 and abs(dc_offset) < 0.05 else "CLIPPED_OR_BIASED"
        }
    except Exception as e:
        return {"error": str(e)}
