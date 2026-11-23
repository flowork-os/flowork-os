#!/usr/bin/env python3
"""
FLOWORK OS CARTOON BROADCAST AUDIO MASTERING ENGINE
- Features synthesized orchestral cartoon instruments (Tuba, Horn Stabs, Snare, Glockenspiel, Crash Cymbal)
- Solves Low Volume: Implements YouTube Shorts Broadcast Mastering (-14.0 LUFS)
- Auto Voice Ducking: Sidechain ducking of background music under speech
- Zero Distortion: True Peak ceiling at -1.0 dBTP via EBU R128 loudnorm
"""

import os, sys, math, subprocess, wave
import numpy as np
import cartoon_instruments as inst

SR = 48000

def generate_orchestral_soundtrack(total_dur=57.5, sfx_events=None):
    total_samples = int(SR * total_dur)
    bgm = np.zeros((total_samples, 2), dtype=np.float32)
    sfx = np.zeros((total_samples, 2), dtype=np.float32)
    
    # 128 BPM Energetic Cartoon March Beat
    bpm = 128
    beat_dur = 60.0 / bpm
    total_beats = int(total_dur / beat_dur)
    
    # Tuba bass progression (F, C, Dm, Bb)
    # MIDI notes: F2=41, C2=36, D2=38, Bb1=34
    root_notes = [41, 36, 38, 34]
    
    rng = np.random.default_rng(42)
    
    def add_to_buffer(buf, sample, start_sec, gain_l=1.0, gain_r=1.0):
        s_idx = int(start_sec * SR)
        dur = len(sample)
        if s_idx < total_samples:
            end_idx = min(s_idx + dur, total_samples)
            n_copy = end_idx - s_idx
            buf[s_idx:end_idx, 0] += sample[:n_copy] * gain_l
            buf[s_idx:end_idx, 1] += sample[:n_copy] * gain_r

    print(f"🎵 Synthesizing {total_beats} beats of procedural cartoon march...")
    for beat in range(total_beats):
        bt = beat * beat_dur
        bar = (beat // 4) % len(root_notes)
        sub_beat = beat % 4
        
        # 1. BASS (Beat 0 & 2): Authentic Cartoon Tuba
        if sub_beat in [0, 2]:
            note = root_notes[bar] if sub_beat == 0 else root_notes[bar] + 7
            tuba = inst.brass(inst.m2f(note), 0.22, vel=0.88, kind="tuba")
            add_to_buffer(bgm, tuba, bt, 0.55, 0.55)
            
            # Kick punch underneath tuba
            kt = np.linspace(0, 0.15, int(0.15 * SR))
            freq = 140 * np.exp(-kt * 30)
            kick = np.sin(2 * np.pi * freq * kt) * np.exp(-kt * 22) * 0.45
            add_to_buffer(bgm, kick, bt, 0.5, 0.5)
            
        # 2. AFTER-BEATS (Beat 1 & 3): Cartoon Horn Stabs & Field Snare
        else:
            # Horn Chord (Root + 5th)
            horn_f = inst.m2f(root_notes[bar] + 12 + 4)
            horn = inst.brass(horn_f, 0.14, vel=0.75, kind="horn")
            add_to_buffer(bgm, horn, bt, 0.35, 0.42)
            
            # Field Snare Hit
            sn = inst.snare(vel=0.82, tune=1.05)
            add_to_buffer(bgm, sn, bt, 0.45, 0.45)
            
        # 3. High Glockenspiel Melody Accents on bar start
        if sub_beat == 0 and beat > 0:
            glk_note = root_notes[bar] + 24 + 7
            glk = inst.glock(inst.m2f(glk_note), vel=0.65, dur=1.2)
            add_to_buffer(bgm, glk, bt, 0.3, 0.4)
            
    # Process custom SFX events
    if sfx_events:
        for ev in sfx_events:
            ev_type = ev.get("type")
            t_sec = ev.get("t", 0.0)
            
            if ev_type == "chime":
                # Star Chime (Dual harmonic glockenspiel)
                ch1 = inst.glock(inst.m2f(84), vel=0.9, dur=1.8)
                ch2 = inst.glock(inst.m2f(91), vel=0.75, dur=1.8)
                add_to_buffer(sfx, ch1, t_sec, 0.7, 0.5)
                add_to_buffer(sfx, ch2, t_sec + 0.04, 0.5, 0.7)
            elif ev_type == "smash":
                # Comic Hammer Smash: Boom Timpani + Clash Cymbal + Anvil
                timp = inst.timpani(75, vel=1.0, dur=1.8)
                cym = inst.cymbal(vel=0.9, dur=2.0)
                add_to_buffer(sfx, timp, t_sec, 0.9, 0.9)
                add_to_buffer(sfx, cym, t_sec, 0.75, 0.75)
            elif ev_type == "cymbal":
                cym = inst.cymbal(vel=0.85, dur=2.2)
                add_to_buffer(sfx, cym, t_sec, 0.6, 0.6)
            elif ev_type == "buzzer":
                t_arr = np.linspace(0, 0.45, int(0.45 * SR))
                buzz = (np.sin(2 * np.pi * 120 * t_arr) + np.sin(2 * np.pi * 124 * t_arr)) * 0.55
                add_to_buffer(sfx, buzz, t_sec, 0.6, 0.6)
            elif ev_type == "whoosh":
                t_arr = np.linspace(0, 0.35, int(0.35 * SR))
                wh = np.sin(2 * np.pi * (300 + 1200 * t_arr) * t_arr) * np.exp(-t_arr * 7) * 0.5
                add_to_buffer(sfx, wh, t_sec, 0.5, 0.5)
                
    # Normalize BGM + SFX bus before master sidechain
    bgm_sfx = bgm * 0.65 + sfx * 0.85
    bgm_sfx = np.clip(bgm_sfx, -0.98, 0.98)
    int_data = (bgm_sfx * 32767).astype(np.int16)
    
    bgm_path = "/tmp/flowork_orchestral_bgm_sfx.wav"
    with wave.open(bgm_path, 'w') as wf:
        wf.setnchannels(2); wf.setsampwidth(2); wf.setframerate(SR)
        wf.writeframes(int_data.tobytes())
        
    print(f"✅ BGM & SFX bus written to {bgm_path}")
    return bgm_path

def master_broadcast_audio(voice_wav, bgm_wav, out_final_wav, total_dur=57.5):
    """
    Broadcast Vocal Mastering Chain:
    - Voice presence boost & crisp phone speaker articulation
    - Intelligent sidechain vocal ducking (BGM ducks automatically when voice talks)
    - Master EBU R128 loudness normalization to exact -14.0 LUFS with True Peak <= -1.0 dBTP
    """
    print(f"🎛️ Mastering broadcast audio to -14.0 LUFS standard...")
    
    # FFmpeg filter complex:
    # 1. Voice processing: Highpass 80Hz + Presence boost at 3.4kHz + Vocal Compressor + Gain
    # 2. Sidechain ducking: BGM ducks -7 dB when voice is present
    # 3. Mixing with normalize=0 to preserve full headroom
    # 4. Final Loudnorm to exactly -14.0 LUFS, TP -1.0 dBTP, LRA 4.0
    filter_complex = (
        "[1:a]highpass=f=80,equalizer=f=3400:t=q:w=1.2:g=4.2,"
        "acompressor=threshold=-18dB:ratio=4:attack=5:release=50,"
        "volume=2.2,asplit=2[v_clean][v_sc];"
        "[0:a][v_sc]sidechaincompress=threshold=0.12:ratio=5:attack=10:release=180[bgm_ducked];"
        "[bgm_ducked][v_clean]amix=inputs=2:weights='0.45 1.9':normalize=0[amix_out];"
        "[amix_out]loudnorm=I=-14.0:TP=-1.0:LRA=4.0[aout]"
    )
    
    cmd = [
        "ffmpeg", "-y",
        "-i", bgm_wav,
        "-i", voice_wav,
        "-filter_complex", filter_complex,
        "-map", "[aout]",
        "-t", str(total_dur),
        "-ar", str(SR),
        out_final_wav
    ]
    subprocess.run(cmd, check=True)
    print(f"🎉 Final Master Audio ready at {out_final_wav} (-14.0 LUFS)")

if __name__ == "__main__":
    dur = 57.5
    sfx = [
        {"type": "buzzer", "t": 5.0},
        {"type": "whoosh", "t": 11.8},
        {"type": "whoosh", "t": 14.0},
        {"type": "smash", "t": 38.2},
        {"type": "chime", "t": 46.5},
        {"type": "chime", "t": 49.0},
        {"type": "chime", "t": 52.0},
        {"type": "cymbal", "t": 55.0}
    ]
    bgm_file = generate_orchestral_soundtrack(dur, sfx)
    master_broadcast_audio("/tmp/opencode_voice.wav", bgm_file, "/tmp/opencode_final_audio_mastered.wav", dur)
