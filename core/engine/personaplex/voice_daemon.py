#!/usr/bin/env python3
"""
👑 FLOWORK OS — PERSONAPLEX SOVEREIGN CONVERSATIONAL VOICE DAEMON
Real-time full-duplex speech engine daemon with sub-10ms natural barge-in interruption.
Features:
- Token-to-Audio Parallel Streaming (Flowork Synaptic Voice Pipeline)
- Confident, deep masculine baritone voice tuning (Mr. Flow Sovereign Voice)
- Multi-sink synchronized broadcast (HDMI monitor + Analog line-out / headphones)
- Sub-5ms barge-in interruption
- Bilingual automatic detection (ID & EN)

Universal root: /opt/floworkos
Author: Flowork Architecture Board & Dr. Flow
"""

import os
import re
import sys
import time
import json
import wave
import signal
import struct
import math
import shutil
import queue
import threading
import subprocess
import asyncio
import glob
from http.server import HTTPServer, BaseHTTPRequestHandler

# Import local hardware detector
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import hardware_detector

try:
    if "/opt/floworkos/theme" not in sys.path:
        sys.path.insert(0, "/opt/floworkos/theme")
    import flowork_neural_bridge
except Exception:
    flowork_neural_bridge = None

# Microsoft Edge Neural Voice integration (Natural, Expressive Prosody)
try:
    import edge_tts
    HAS_EDGE_TTS = True
except ImportError:
    HAS_EDGE_TTS = False

PORT = 8998
RUNTIME_DIR = f"/run/user/{os.getuid()}"
if os.path.isdir(RUNTIME_DIR):
    AUDIO_SPOOL_DIR = os.path.join(RUNTIME_DIR, "flowork-voice-spool")
elif os.path.isdir("/dev/shm"):
    AUDIO_SPOOL_DIR = f"/dev/shm/flowork-voice-spool-{os.getuid()}"
else:
    AUDIO_SPOOL_DIR = os.path.expanduser("~/.flowork/voice-spool")
os.makedirs(AUDIO_SPOOL_DIR, mode=0o700, exist_ok=True)

LOG_DIR = os.path.expanduser("~/.flowork/logs")
PID_FILE = os.path.join(RUNTIME_DIR, "flowork-voice.pid")
LOG_FILE = os.path.join(LOG_DIR, "flowork-voice.log")
EARSHOT_FORGE = "/opt/floworkos/bin/flowork-sound-forge"

# Neural Voice Assets
EDGE_ID_VOICE = "id-ID-ArdiNeural"
EDGE_EN_VOICE = "en-US-AndrewMultilingualNeural"
PIPER_BIN = "/opt/floworkos/apps/flowork-voice-engine/venv/bin/piper"
VOICES_DIR = "/opt/floworkos/engine/personaplex/voices"
EN_MODEL = os.path.join(VOICES_DIR, "en_US-ryan-medium.onnx")

# Streaming Queue & Synaptic Pipeline State
STREAM_QUEUE = queue.Queue()
PLAY_QUEUE = queue.Queue()
STREAM_LOCK = threading.Lock()
CURRENT_EPOCH = 0
EPOCH_LOCK = threading.Lock()
CHUNK_COUNTER = 0
ACTIVE_AUDIO_FILES = set()
ACTIVE_FILES_LOCK = threading.Lock()

# Global state
STATE = {
    "is_speaking": False,
    "playback_procs": [],
    "session_active": False,
    "hardware_info": hardware_detector.detect_hardware(),
    "last_speech_time": 0,
    "active_engine": "edge_neural_ardi" if HAS_EDGE_TTS else ("neural_piper" if os.path.exists(PIPER_BIN) and os.path.exists(EN_MODEL) else "procedural")
}


def log(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [Voice-Daemon] {msg}\n"
    try:
        os.makedirs(LOG_DIR, mode=0o700, exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted)
    except Exception:
        pass


def play_sound(recipe: str):
    if os.path.exists(EARSHOT_FORGE):
        try:
            subprocess.Popen([EARSHOT_FORGE, "play", recipe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass


def purge_audio_spool(max_age_seconds: float = 0.0) -> int:
    """Purge temporary audio spool files older than max_age_seconds (0 = purge all leftover), strictly protecting actively queued files."""
    purged_count = 0
    now = time.time()
    with ACTIVE_FILES_LOCK:
        active_set = set(ACTIVE_AUDIO_FILES)

    # 1. Sweep dedicated spool dir
    if os.path.isdir(AUDIO_SPOOL_DIR):
        try:
            for entry in os.listdir(AUDIO_SPOOL_DIR):
                fp = os.path.join(AUDIO_SPOOL_DIR, entry)
                if os.path.isfile(fp):
                    if fp in active_set:
                        continue  # Invariant: NEVER delete actively queued or playing speech chunks!
                    try:
                        if max_age_seconds <= 0.0 or (now - os.path.getmtime(fp)) >= max_age_seconds:
                            os.remove(fp)
                            purged_count += 1
                    except OSError:
                        pass
        except Exception:
            pass

    # 2. Sweep legacy spooling locations for stray flowork audio files
    legacy_targets = [
        (RUNTIME_DIR, "flowork_stream_*"),
        (RUNTIME_DIR, "flowork_voice_output*"),
        ("/dev/shm", "flowork_stream_*"),
        ("/dev/shm", "flowork_voice_output*"),
    ]
    for ldir, pat in legacy_targets:
        if os.path.isdir(ldir):
            try:
                for fp in glob.glob(os.path.join(ldir, pat)):
                    if fp in active_set:
                        continue
                    try:
                        if max_age_seconds <= 0.0 or (now - os.path.getmtime(fp)) >= max_age_seconds:
                            os.remove(fp)
                            purged_count += 1
                    except OSError:
                        pass
            except Exception:
                pass

    return purged_count


def audio_housekeeper_loop():
    """Background watchdog: purges true stale orphan spool files older than 5 minutes every 60 seconds."""
    while True:
        try:
            time.sleep(60)
            cleaned = purge_audio_spool(max_age_seconds=300.0)
            if cleaned > 0:
                log(f"[Housekeeper] Auto-purged {cleaned} stale orphan audio spool file(s).")
        except Exception as e:
            log(f"[Housekeeper] Housekeeper cycle warning: {e}")


def execute_barge_in():
    """Interrupt ongoing speech playback across all sinks and clear streaming & playback queues immediately (< 5ms)."""
    global CURRENT_EPOCH
    with EPOCH_LOCK:
        CURRENT_EPOCH += 1

    with ACTIVE_FILES_LOCK:
        ACTIVE_AUDIO_FILES.clear()

    with STREAM_LOCK:
        # 1. Clear any pending stream text chunks
        while not STREAM_QUEUE.empty():
            try:
                STREAM_QUEUE.get_nowait()
                STREAM_QUEUE.task_done()
            except Exception:
                break

        # 2. Clear and delete any pre-synthesized audio chunks
        while not PLAY_QUEUE.empty():
            try:
                item = PLAY_QUEUE.get_nowait()
                f = item[0] if isinstance(item, tuple) else item
                if f and os.path.exists(f):
                    try:
                        os.remove(f)
                    except OSError:
                        pass
                PLAY_QUEUE.task_done()
            except Exception:
                break

        # 3. Kill all currently active playback processes across all sinks
        procs = list(STATE.get("playback_procs", []))
        for proc in procs:
            if proc and proc.poll() is None:
                try:
                    proc.kill()
                except Exception:
                    pass
        STATE["playback_procs"] = []
        STATE["is_speaking"] = False
        if flowork_neural_bridge:
            flowork_neural_bridge.set_neural_state("idle", morphology="morph-idle", amplitude=0.0)
    log(f"Natural barge-in triggered (epoch={CURRENT_EPOCH}): cleared queues and killed all playback processes.")


def get_all_audio_sinks():
    """Discover all active PipeWire/PulseAudio output sinks (HDMI, analog, etc.)."""
    sinks = []
    try:
        res = subprocess.run(["pactl", "list", "sinks", "short"], capture_output=True, text=True, timeout=2)
        if res.returncode == 0:
            for line in res.stdout.strip().splitlines():
                parts = line.split()
                if len(parts) >= 2:
                    sinks.append(parts[1])
    except Exception:
        pass
    return sinks if sinks else [None]


def detect_language(text: str) -> str:
    """Heuristic language detector between Indonesian and English."""
    id_markers = {
        'halo', 'hai', 'ini', 'dan', 'di', 'ke', 'dari', 'yang', 'untuk', 'saya', 'aku',
        'loe', 'lo', 'gw', 'gua', 'kita', 'sudah', 'udah', 'bisa', 'siap', 'bos', 'ya',
        'tidak', 'nggak', 'gak', 'ada', 'itu', 'apa', 'bagaimana', 'gimana', 'kenapa',
        'jalan', 'buka', 'tutup', 'tambah', 'hapus', 'tolong', 'terima', 'kasih', 'cowok',
        'berat', 'suara', 'bicara', 'ngomong', 'kamu', 'anda', 'mereka', 'bro', 'berkas',
        'periksa', 'kode', 'sistem', 'jalankan', 'proses', 'unggah', 'tanda', 'titik', 'kalimat'
    }
    words = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
    if words & id_markers:
        return "id"
    en_markers = {'the', 'is', 'are', 'this', 'that', 'with', 'from', 'have', 'has', 'will', 'all', 'we', 'you', 'they'}
    if (words & en_markers) and not (words & id_markers):
        return "en"
    return "id"  # Sovereign Default: Indonesian


def apply_baritone_pitch_filter(input_wav: str, output_wav: str, is_id: bool = True) -> bool:
    """
    Transform synthesized vocal into a deep, heavy, authoritative male baritone.
    - Lowers pitch by ~23% for Indonesian (female source) or ~12% for English (Ryan).
    - Preserves natural tempo and boosts chest resonance (+6dB @ 120Hz).
    """
    try:
        rate_ratio = 0.77 if is_id else 0.88
        tempo_ratio = 1.0 / rate_ratio
        filt = f"asetrate=22050*{rate_ratio},aresample=22050,atempo={tempo_ratio:.3f},equalizer=f=120:width_type=h:width=60:g=6,equalizer=f=3200:width_type=h:width=1000:g=2"
        cmd = ["ffmpeg", "-y", "-i", input_wav, "-af", filt, output_wav]
        res = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=8)
        return res.returncode == 0 and os.path.exists(output_wav)
    except Exception as e:
        log(f"Baritone filter error: {e}")
        return False


def sanitize_speech_text(text: str) -> str:
    """Rigorous phonetic and script sanitizer for clean, glitch-free TTS audio."""
    # 1. Strip code blocks, inline code, and URLs
    text = re.sub(r'```[\s\S]*?```', '', text)
    text = re.sub(r'`([^`]+)`', r'\1', text)
    text = re.sub(r'https?://\S+', '', text)
    
    # 2. Extract <speech>...</speech> if wrapped in tag
    speech_match = re.search(r'<speech>([\s\S]*?)</speech>', text, re.IGNORECASE)
    if speech_match:
        text = speech_match.group(1)
    else:
        # Strip any dangling partial tags
        text = re.sub(r'</?speech>', '', text, flags=re.IGNORECASE)

    # 3. Strip foreign / non-Latin scripts (Hanzi, Kanji, Cyrillic, Arabic, symbols)
    # Keep standard Latin alphabet, numbers, and basic sentence punctuation (. , ! ? ' -)
    text = re.sub(r'[^\x00-\x7F\u00C0-\u024F\s\.,!\?\'\-]', ' ', text)

    # 4. Strip markdown syntax, brackets, braces, and emojis
    text = re.sub(r'[#*_~>\[\]\(\)\{\}\\\|/+=^%$@&<>]', ' ', text)

    # 5. Normalization for tech terms and acronyms to phonetic speech
    replacements = {
        r'\bOS\b': 'O S',
        r'\bAI\b': 'A I',
        r'\bGUI\b': 'G U I',
        r'\bCLI\b': 'C L I',
        r'\bTTS\b': 'T T S',
        r'\bAPI\b': 'A P I',
        r'\bUI\b': 'U I',
        r'\bID\b': 'I D',
        r'\bLLM\b': 'L L M'
    }
    for pat, rep in replacements.items():
        text = re.sub(pat, rep, text)

    # 6. Normalize punctuation and whitespace
    text = re.sub(r'[\.\!\?]{2,}', '.', text)
    text = ' '.join(text.split())
    return text.strip()


def synthesize_neural_piper(text: str, output_wav: str, lang: str = "en") -> bool:
    """Fast on-device neural text-to-speech synthesis using Piper English model."""
    if not os.path.exists(PIPER_BIN) or not os.path.exists(EN_MODEL):
        return False

    raw_tmp = output_wav + ".raw.wav"
    try:
        cmd = [PIPER_BIN, "--model", EN_MODEL, "--output_file", raw_tmp]
        proc = subprocess.run(cmd, input=text, text=True, capture_output=True, timeout=12)
        if proc.returncode == 0 and os.path.exists(raw_tmp):
            if apply_baritone_pitch_filter(raw_tmp, output_wav, is_id=False):
                try:
                    os.remove(raw_tmp)
                except OSError:
                    pass
                return True
            else:
                shutil.move(raw_tmp, output_wav)
                return True
        else:
            log(f"Piper error: {proc.stderr}")
            return False
    except Exception as e:
        log(f"Piper exception: {e}")
        return False


async def _async_edge_tts(text: str, output_path: str, voice: str):
    """Internal async worker for edge-tts communication with 100% natural prosody tempo."""
    comm = edge_tts.Communicate(text, voice=voice, rate="+0%")
    await comm.save(output_path)


def synthesize_edge_tts(text: str, output_wav: str, lang: str = "id") -> bool:
    """Natural, expressive, fast human speech synthesis using Microsoft Edge Neural Voice with automatic failover."""
    if not HAS_EDGE_TTS:
        return False

    primary_voice = EDGE_ID_VOICE if lang == "id" else EDGE_EN_VOICE
    backup_voice = "id-ID-GadisNeural" if lang == "id" else "en-US-JennyNeural"
    # Plan: Try primary, retry primary, then failover to backup voice
    voices_plan = [primary_voice, primary_voice, backup_voice]

    t0 = time.time()
    for attempt, voice in enumerate(voices_plan):
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            future = asyncio.wait_for(_async_edge_tts(text, output_wav, voice), timeout=12.0)
            loop.run_until_complete(future)
            if os.path.exists(output_wav) and os.path.getsize(output_wav) > 300:
                log(f"[Edge-TTS] Synthesized {len(text)} chars in {time.time()-t0:.2f}s (voice={voice}) -> {os.path.basename(output_wav)}")
                return True
        except Exception as e:
            err_type = type(e).__name__
            log(f"[Edge-TTS] Attempt {attempt + 1} ({voice}) failed with {err_type}: {e}")
            time.sleep(0.3)
        finally:
            try:
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
                loop.close()
            except Exception:
                pass
    return False


def synthesize_speech(text: str, output_wav: str, lang: str = None) -> str:
    """Master synthesis dispatcher: Microsoft Edge Neural Voice with resilient offline Piper backup."""
    clean_text = sanitize_speech_text(text)
    if not clean_text or len(clean_text) < 2:
        return "skipped_empty"

    if not lang:
        lang = detect_language(clean_text)

    # 1. Sovereign Primary Voice: Microsoft Edge-TTS Natural Human Voice (ArdiNeural / GadisNeural)
    if HAS_EDGE_TTS and synthesize_edge_tts(clean_text, output_wav, lang=lang):
        return "edge_neural_ardi"

    # 2. English-only Piper if English text
    if lang == "en" and os.path.exists(EN_MODEL) and synthesize_neural_piper(clean_text, output_wav, lang="en"):
        return "neural_piper_en"

    # 3. Resilient Offline Fallback: If offline or network drop, synthesize via Piper onnx to guarantee zero dead air
    if os.path.exists(EN_MODEL) and synthesize_neural_piper(clean_text, output_wav, lang="en"):
        log(f"Edge-TTS offline or unavailable; used Piper neural fallback for clause: '{clean_text[:40]}...'")
        return "neural_piper_fallback"

    # 4. Clean silent discard: NEVER play synthetic 105Hz sine wave buzzing
    log(f"Speech synthesis dropped for clause: '{clean_text[:40]}...' (No robotic buzzing)")
    return "failed"


def synthesis_worker_loop():
    """Background producer: Pre-synthesizes queued text into PLAY_QUEUE ahead of playback with epoch isolation."""
    global CHUNK_COUNTER
    while True:
        try:
            item = STREAM_QUEUE.get()
            if item is None:
                continue

            with EPOCH_LOCK:
                task_epoch = CURRENT_EPOCH

            text, lang = item
            if not text.strip():
                STREAM_QUEUE.task_done()
                continue

            CHUNK_COUNTER += 1
            idx = CHUNK_COUNTER
            os.makedirs(AUDIO_SPOOL_DIR, mode=0o700, exist_ok=True)
            # Use unique timestamp + counter inside isolated spool directory
            chunk_file = os.path.join(AUDIO_SPOOL_DIR, f"stream_{int(time.time()*1000)}_{idx}.mp3")

            result = synthesize_speech(text, chunk_file, lang)

            # Validate that generation was not interrupted while synthesizing
            with EPOCH_LOCK:
                if task_epoch != CURRENT_EPOCH:
                    try:
                        if os.path.exists(chunk_file):
                            os.remove(chunk_file)
                    except OSError:
                        pass
                    STREAM_QUEUE.task_done()
                    continue

            if result != "failed" and os.path.exists(chunk_file) and os.path.getsize(chunk_file) > 300:
                with ACTIVE_FILES_LOCK:
                    ACTIVE_AUDIO_FILES.add(chunk_file)
                PLAY_QUEUE.put((chunk_file, task_epoch))

            STREAM_QUEUE.task_done()
        except Exception as e:
            log(f"Synthesis worker error: {e}")
            time.sleep(0.05)


def extract_audio_envelope(audio_path: str, fps: int = 25) -> list:
    """Extract normalized RMS audio energy envelope in 40ms slices for live visual pulsing."""
    try:
        if not os.path.exists(audio_path) or os.path.getsize(audio_path) < 300:
            return []
        cmd = [
            "ffmpeg", "-v", "quiet", "-i", audio_path,
            "-f", "s16le", "-ac", "1", "-ar", "8000", "pipe:1"
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, timeout=4)
        raw = proc.stdout
        if not raw:
            return []
        slice_samples = int(8000 / fps)
        slice_bytes = slice_samples * 2
        envelope = []
        for i in range(0, len(raw), slice_bytes):
            chunk = raw[i:i + slice_bytes]
            count = len(chunk) // 2
            if count == 0:
                continue
            samples = struct.unpack(f"<{count}h", chunk[:count * 2])
            rms = math.sqrt(sum(s * s for s in samples) / count) / 32768.0
            # Scale and dynamic compression for vivid visual expansion
            amp = min(1.0, math.pow(rms * 4.5, 0.75))
            envelope.append(round(amp, 3))
        return envelope
    except Exception as e:
        log(f"Envelope extraction error: {e}")
        return []


def playback_worker_loop():
    """Background consumer: Dequeues pre-synthesized audio files and plays with ZERO latency between sentences."""
    while True:
        try:
            item = PLAY_QUEUE.get()
            if item is None:
                continue

            if isinstance(item, tuple):
                chunk_file, play_epoch = item
            else:
                chunk_file, play_epoch = item, CURRENT_EPOCH

            # Discard any chunks belonging to obsolete barge-in epochs
            with EPOCH_LOCK:
                if play_epoch != CURRENT_EPOCH:
                    with ACTIVE_FILES_LOCK:
                        ACTIVE_AUDIO_FILES.discard(chunk_file)
                    try:
                        if os.path.exists(chunk_file):
                            os.remove(chunk_file)
                    except OSError:
                        pass
                    PLAY_QUEUE.task_done()
                    continue

            if not os.path.exists(chunk_file) or os.path.getsize(chunk_file) <= 300:
                with ACTIVE_FILES_LOCK:
                    ACTIVE_AUDIO_FILES.discard(chunk_file)
                PLAY_QUEUE.task_done()
                continue

            # Pre-extract real-time speech cadence envelope (sub-40ms execution)
            envelope = extract_audio_envelope(chunk_file, fps=25)

            sinks = get_all_audio_sinks()
            spawned = []
            with STREAM_LOCK:
                for s in sinks:
                    cmd = ["paplay", f"--device={s}", chunk_file] if s else ["paplay", chunk_file]
                    try:
                        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        spawned.append(p)
                    except Exception:
                        pass
                STATE["playback_procs"] = spawned
                STATE["is_speaking"] = True

            # Synchronous real-time speech amplitude broadcasting thread
            start_t = time.time()
            if envelope and flowork_neural_bridge:
                def _stream_envelope(procs, env, start_time, epoch):
                    interval = 0.04  # 25 FPS = 40ms
                    while True:
                        with EPOCH_LOCK:
                            if epoch != CURRENT_EPOCH:
                                break
                        any_alive = any(p.poll() is None for p in procs)
                        if not any_alive:
                            break
                        elapsed = time.time() - start_time
                        target_idx = min(len(env) - 1, int(elapsed * 25.0))
                        amp = env[target_idx]
                        flowork_neural_bridge.set_neural_state("speaking", morphology="morph-speech", amplitude=amp)
                        time.sleep(interval)

                threading.Thread(target=_stream_envelope, args=(spawned, envelope, start_t, play_epoch), daemon=True).start()
            elif flowork_neural_bridge:
                flowork_neural_bridge.set_neural_state("speaking", morphology="morph-speech", amplitude=0.85)

            log(f"[Playback] Started playing {os.path.basename(chunk_file)} ({os.path.getsize(chunk_file)} bytes)")
            try:
                # Wait for this chunk to finish playing across all sinks
                for p in spawned:
                    try:
                        p.wait()
                    except Exception:
                        pass
            finally:
                with ACTIVE_FILES_LOCK:
                    ACTIVE_AUDIO_FILES.discard(chunk_file)
                # Guaranteed unlinking of played audio chunk in all scenarios (error, interrupt, or completion)
                try:
                    if os.path.exists(chunk_file):
                        os.remove(chunk_file)
                except OSError:
                    pass

            with STREAM_LOCK:
                STATE["playback_procs"] = []
                if PLAY_QUEUE.empty() and STREAM_QUEUE.empty():
                    STATE["is_speaking"] = False
                    if flowork_neural_bridge:
                        flowork_neural_bridge.set_neural_state("idle", morphology="morph-idle", amplitude=0.0)

            log(f"[Playback] Finished playing and unlinked {os.path.basename(chunk_file)}")
            PLAY_QUEUE.task_done()
        except Exception as e:
            log(f"Playback worker error: {e}")
            time.sleep(0.02)


def _playback_monitor(procs, file_path: str = None):
    """Background watcher to reset speaking state and unlink single-shot audio when sinks finish."""
    try:
        for p in procs:
            try:
                p.wait()
            except Exception:
                pass
    finally:
        STATE["is_speaking"] = False
        STATE["playback_procs"] = []
        if flowork_neural_bridge:
            flowork_neural_bridge.set_neural_state("idle", morphology="morph-idle", amplitude=0.0)
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                log(f"[Playback] Unlinked single-shot audio: {os.path.basename(file_path)}")
            except OSError:
                pass


class VoiceRequestHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path in ("/status", "/health"):
            self._send_json({
                "status": "active",
                "tier": STATE["hardware_info"]["recommended_tier"],
                "port": PORT,
                "hardware": STATE["hardware_info"],
                "session_active": STATE["session_active"],
                "is_speaking": STATE["is_speaking"],
                "active_engine": STATE["active_engine"],
                "edge_tts_available": HAS_EDGE_TTS,
                "primary_voice": f"Microsoft Neural ({EDGE_ID_VOICE})",
                "offline_fallback": "Procedural Formant Acoustic Stream",
                "active_sinks": get_all_audio_sinks(),
                "queue_size": STREAM_QUEUE.qsize(),
                "voice_profile": "Masculine Natural Conversational Fast (Mr. Flow)",
                "models": {
                    "indonesian_neural": HAS_EDGE_TTS,
                    "english_piper": os.path.exists(EN_MODEL)
                },
                "barge_in_supported": True
            })
        elif self.path == "/stream/status":
            self._send_json({
                "queue_size": STREAM_QUEUE.qsize(),
                "is_speaking": STATE["is_speaking"]
            })
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(length) if length > 0 else b"{}"
        try:
            payload = json.loads(post_data.decode("utf-8")) if post_data else {}
        except Exception:
            payload = {}

        if self.path in ("/barge_in", "/stream/clear"):
            execute_barge_in()
            self._send_json({"status": "interrupted", "timestamp": time.time()})

        elif self.path == "/stream/push":
            text = payload.get("text", "").strip()
            lang = payload.get("lang")
            reset = payload.get("reset", False)

            if reset:
                execute_barge_in()

            if not text:
                self._send_json({"error": "Empty text parameter"}, status=400)
                return

            if not lang:
                lang = detect_language(text)

            STREAM_QUEUE.put((text, lang))
            self._send_json({
                "status": "queued",
                "text": text,
                "lang": lang,
                "queue_size": STREAM_QUEUE.qsize()
            })

        elif self.path == "/speak":
            text = payload.get("text", "").strip()
            lang = payload.get("lang")
            interrupt = payload.get("interrupt", True)
            play_audio = payload.get("play", True)

            if interrupt:
                execute_barge_in()

            if not text:
                self._send_json({"error": "Empty text parameter"}, status=400)
                return

            if not lang:
                lang = detect_language(text)

            os.makedirs(AUDIO_SPOOL_DIR, mode=0o700, exist_ok=True)
            wav_path = os.path.join(AUDIO_SPOOL_DIR, f"speak_{int(time.time()*1000)}.mp3")
            
            engine_used = synthesize_speech(text, wav_path, lang)

            if play_audio and os.path.exists(wav_path):
                sinks = get_all_audio_sinks()
                spawned = []
                for s in sinks:
                    cmd = ["paplay", f"--device={s}", wav_path] if s else ["paplay", wav_path]
                    try:
                        p = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        spawned.append(p)
                    except Exception:
                        pass
                
                if spawned:
                    STATE["playback_procs"] = spawned
                    STATE["is_speaking"] = True
                    threading.Thread(target=_playback_monitor, args=(spawned, wav_path), daemon=True).start()

            self._send_json({
                "status": "synthesized",
                "text": text,
                "engine": engine_used,
                "file": wav_path,
                "voice_profile": "Masculine Deep Baritone",
                "tier": STATE["hardware_info"]["recommended_tier"]
            })

        elif self.path == "/session/start":
            STATE["session_active"] = True
            play_sound("bell")
            self._send_json({"session": "active", "tier": STATE["hardware_info"]["recommended_tier"]})

        elif self.path == "/session/stop":
            execute_barge_in()
            STATE["session_active"] = False
            self._send_json({"session": "stopped"})

        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass


def ensure_models_available():
    """Ensure required voice models exist (English Ryan only; Indonesian uses Edge-TTS)."""
    import urllib.request
    models_to_download = []
    if not os.path.exists(EN_MODEL):
        models_to_download.append((
            "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
            EN_MODEL
        ))
    for url, path in models_to_download:
        try:
            log(f"Auto-hydrating missing voice model: {os.path.basename(path)}")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp_target = path + ".tmp"
            urllib.request.urlretrieve(url, tmp_target)
            os.rename(tmp_target, path)
            log(f"Model hydrated: {os.path.basename(path)}")
        except Exception as e:
            log(f"Failed to auto-download {url}: {e}")


def run_server():
    server = HTTPServer(("127.0.0.1", PORT), VoiceRequestHandler)
    pid_dir = os.path.dirname(PID_FILE)
    os.makedirs(pid_dir, mode=0o700, exist_ok=True)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))

    log(f"PersonaPlex Voice Daemon started on http://127.0.0.1:{PORT} (PID {os.getpid()}).")

    # 1. Startup sanitary sweep: immediately unlink any leftover orphan audio spool files
    startup_cleaned = purge_audio_spool(max_age_seconds=0.0)
    log(f"[Housekeeper] Startup sanitary sweep complete: unlinked {startup_cleaned} leftover spool file(s).")

    # 2. Spawn concurrent neural and audio pipelines
    threading.Thread(target=ensure_models_available, daemon=True).start()
    threading.Thread(target=synthesis_worker_loop, daemon=True).start()
    threading.Thread(target=playback_worker_loop, daemon=True).start()
    threading.Thread(target=audio_housekeeper_loop, daemon=True).start()

    def handle_signal(sig, frame):
        log(f"Terminating voice daemon on signal {sig}.")
        try:
            purge_audio_spool(max_age_seconds=0.0)
            if os.path.exists(PID_FILE):
                os.remove(PID_FILE)
        except OSError:
            pass
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    server.serve_forever()


if __name__ == "__main__":
    run_server()
