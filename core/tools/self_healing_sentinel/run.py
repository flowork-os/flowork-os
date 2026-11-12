#!/usr/bin/env python3
import sys
import os
import re
import json
import fcntl
import socket
import hashlib
import tempfile
import urllib.request
import urllib.error
import subprocess
import time

SEEN_TRAPS_FILE = '/tmp/flowork_sentinel_seen_traps.json'
SEEN_LOCK_FILE = '/tmp/flowork_sentinel_seen_traps.lock'
COOLDOWN_FILE = '/tmp/flowork_sentinel_cooldown.json'
CRASH_DIR = '/tmp/flowork_crashes'
PROCESSED_CRASH_DIR = '/tmp/flowork_crashes/.processed'
WAKE_COOLDOWN_SECS = 300


def _atomic_write_json(path, data):
    parent = os.path.dirname(path) or '/tmp'
    os.makedirs(parent, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(prefix='.tmp_sentinel_', dir=parent)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            json.dump(data, f)
            f.flush()
            os.fsync(f.fileno())
        os.chmod(tmp_path, 0o644)
        os.replace(tmp_path, path)
    except Exception:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass


def is_simulated_incident(incident, filename=None):
    """Detect synthetic QC/test crash payloads so they never wake interactive desktop agents or spawn GUI popups."""
    if not isinstance(incident, dict):
        return False
    if incident.get('simulated') is True or incident.get('dry_run') is True:
        return True
    if filename and os.path.basename(filename).startswith('qc_test_'):
        return True
    pid_str = str(incident.get('pid', '')).strip()
    if pid_str in ('77777', '99999', '0'):
        return True
    detail_str = str(incident.get('detail', '')).lower()
    if 'qc automated test' in detail_str or 'simulated' in detail_str:
        return True
    return False


def check_http(url, timeout=3):
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200, resp.read().decode('utf-8', errors='ignore')
    except Exception as e:
        return False, str(e)


def check_mem():
    mem = {}
    try:
        with open('/proc/meminfo', 'r') as f:
            for line in f:
                parts = line.split(':')
                if len(parts) == 2:
                    key = parts[0].strip()
                    val = parts[1].strip().split()[0]
                    mem[key] = int(val)
        total_kb = mem.get('MemTotal', 1)
        avail_kb = mem.get('MemAvailable', 1)
        used_pct = round(((total_kb - avail_kb) / total_kb) * 100, 1)
        return {
            'total_mb': total_kb // 1024,
            'available_mb': avail_kb // 1024,
            'used_pct': used_pct,
            'pressure': 'critical' if (avail_kb // 1024) < 150 else 'normal'
        }
    except Exception as e:
        return {'error': str(e)}


def check_shm_usage():
    shm_path = '/dev/shm'
    total_size = 0
    stale_files = 0
    now = time.time()
    try:
        for root, dirs, files in os.walk(shm_path):
            for file in files:
                fp = os.path.join(root, file)
                try:
                    stat = os.stat(fp)
                    total_size += stat.st_size
                    if now - stat.st_mtime > 300 and file.startswith(('frame_', 'tmp_', 'screenshot_')):
                        stale_files += 1
                except Exception:
                    pass
        return {
            'total_shm_mb': round(total_size / (1024 * 1024), 2),
            'stale_artifacts_count': stale_files
        }
    except Exception as e:
        return {'error': str(e)}


def _archive_crash_file(filepath, filename, simulated):
    """Consume processed crash JSON atomically so it can never re-trigger across daemon ticks or rotations."""
    try:
        if simulated or filename.startswith('qc_test_'):
            os.unlink(filepath)
            return
        os.makedirs(PROCESSED_CRASH_DIR, exist_ok=True)
        dest = os.path.join(PROCESSED_CRASH_DIR, f"{int(time.time())}_{filename}")
        os.replace(filepath, dest)
        # Retain only the newest 50 archived crash reports
        archived = sorted(
            [os.path.join(PROCESSED_CRASH_DIR, x) for x in os.listdir(PROCESSED_CRASH_DIR) if x.endswith('.json')],
            key=os.path.getmtime
        )
        for old_fp in archived[:-50]:
            try:
                os.unlink(old_fp)
            except Exception:
                pass
    except Exception:
        pass


def check_kernel_traps(consume=True):
    """Scan dmesg and crash dropbox for recent kernel traps, segfaults, and crash dumps under flock serialization."""
    traps = []
    lock_fd = None
    try:
        lock_fd = open(SEEN_LOCK_FILE, 'a+')
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        seen_list = []
        seen_traps = set()
        is_initial_seed = False

        if os.path.exists(SEEN_TRAPS_FILE):
            try:
                with open(SEEN_TRAPS_FILE, 'r', encoding='utf-8') as sf:
                    loaded = json.load(sf)
                    if isinstance(loaded, list):
                        seen_list = loaded
                        seen_traps = set(loaded)
            except Exception:
                seen_list = []
                seen_traps = set()
        else:
            is_initial_seed = True

        # 1. Kernel dmesg traps
        try:
            res = subprocess.run(['dmesg'], capture_output=True, text=True, timeout=3)
            if res.returncode == 0:
                lines = res.stdout.strip().splitlines()
                for line in lines[-200:]:
                    if any(k in line for k in ('segfault at', 'trap invalid opcode', 'trap int3', 'trap divide error', 'general protection fault')):
                        m1 = re.search(r"(\w+)\[(\d+)\]:\s+segfault\s+at\s+([0-9a-f]+)\s+ip\s+([0-9a-f]+)\s+sp\s+([0-9a-f]+)\s+error\s+(\d+)\s+in\s+([^\s\[]+)", line)
                        m2 = re.search(r"traps:\s+(\w+)\[(\d+)\]\s+trap\s+([^\s]+)\s+ip:([0-9a-f]+)\s+sp:([0-9a-f]+)\s+error:(\d+)\s+in\s+([^\s\[]+)", line)
                        m = m1 or m2
                        if m:
                            proc_name = m.group(1)
                            pid = m.group(2)
                            binary = m.group(7)
                            trap_type = 'segfault' if m1 else f"trap {m.group(3)}"
                            line_hash = hashlib.sha256(line.encode('utf-8')).hexdigest()[:16]

                            if line_hash not in seen_traps:
                                if is_initial_seed or consume:
                                    seen_traps.add(line_hash)
                                    seen_list.append(line_hash)
                                if not is_initial_seed:
                                    traps.append({
                                        'app': proc_name,
                                        'pid': pid,
                                        'type': trap_type,
                                        'binary': binary,
                                        'raw': line,
                                        'hash': line_hash
                                    })
        except Exception:
            pass

        # 2. App-level crash dropbox (/tmp/flowork_crashes/*.json)
        if os.path.isdir(CRASH_DIR):
            for f in sorted(os.listdir(CRASH_DIR)):
                if f.startswith('.') or f.endswith('.tmp') or not f.endswith('.json'):
                    continue
                fp = os.path.join(CRASH_DIR, f)
                if not os.path.isfile(fp):
                    continue
                try:
                    with open(fp, 'rb') as cf:
                        raw_bytes = cf.read()
                    if not raw_bytes.strip():
                        continue
                    incident = json.loads(raw_bytes.decode('utf-8'))
                    if not isinstance(incident, dict):
                        continue
                    sim_flag = is_simulated_incident(incident, f)
                    content_hash = hashlib.sha256(f.encode('utf-8') + b':' + raw_bytes).hexdigest()[:16]

                    if content_hash not in seen_traps:
                        if consume or is_initial_seed:
                            seen_traps.add(content_hash)
                            seen_list.append(content_hash)
                        incident_copy = dict(incident)
                        incident_copy['_source_file'] = f
                        incident_copy['_simulated'] = sim_flag
                        traps.append(incident_copy)
                        if consume:
                            _archive_crash_file(fp, f, sim_flag)
                    elif consume:
                        # Clean up leftover already-seen crash JSONs so they never accumulate
                        _archive_crash_file(fp, f, sim_flag)
                except Exception:
                    pass

        if consume or is_initial_seed:
            _atomic_write_json(SEEN_TRAPS_FILE, seen_list[-500:])
    except Exception:
        pass
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except Exception:
                pass

    return traps


def _check_and_mark_wake_cooldown(app_name):
    """Rate-limit sidebar wakeups per app to avoid runaway wakeup storms."""
    now = time.time()
    lock_fd = None
    try:
        lock_fd = open(SEEN_LOCK_FILE, 'a+')
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        data = {}
        if os.path.exists(COOLDOWN_FILE):
            try:
                with open(COOLDOWN_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        data = loaded
            except Exception:
                data = {}
        last_ts = float(data.get(app_name, 0))
        if now - last_ts < WAKE_COOLDOWN_SECS:
            return False
        data[app_name] = now
        # Prune entries older than 24h
        pruned = {k: v for k, v in data.items() if now - float(v) < 86400}
        _atomic_write_json(COOLDOWN_FILE, pruned)
        return True
    except Exception:
        return True
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except Exception:
                pass


def wake_up_mrflow_agent(incident, actions):
    """Wake up Mr. Flow sidebar agent via Unix Domain Socket for genuine non-recursive incidents."""
    try:
        if os.environ.get('FLOWORK_SENTINEL_NO_WAKE') == '1':
            return False
        app_name = incident.get('app') or incident.get('target_app') or 'system'
        # Prevent recursive self-wakeups if mrflow or sidebar itself reported an incident
        if str(app_name).lower() in ('mrflow', 'mrflow-sidebar', 'mrflow-tray-menu', 'mrflow-tray-applet'):
            return False

        user = os.environ.get("USER") or os.environ.get("LOGNAME") or os.path.basename(os.path.expanduser("~"))
        sock_path = f"/tmp/mrflow-sidebar-{user}.sock"
        if not os.path.exists(sock_path):
            return False

        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2.0)
        client.connect(sock_path)
        client.sendall(json.dumps({"action": "status"}).encode("utf-8"))
        res = client.recv(1024)
        client.close()
        status_data = json.loads(res.decode("utf-8")) if res else {}

        # Never interrupt or pop open sidebar when agent turn is already running
        if status_data.get("is_busy", False):
            return False

        # Enforce per-app cooldown before revealing HUD or dispatching a prompt
        if not _check_and_mark_wake_cooldown(app_name):
            return False

        pid = incident.get('pid', 'N/A')
        trap_type = incident.get('type', 'crash')

        if not status_data.get("is_open", False):
            client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            client.settimeout(2.0)
            client.connect(sock_path)
            client.sendall(json.dumps({"action": "show"}).encode("utf-8"))
            client.recv(1024)
            client.close()
            time.sleep(0.3)

        prompt = (
            f"🚨 [AUTONOMOUS CRASH SENTINEL]: Terdeteksi insiden {trap_type} pada aplikasi/proses '{app_name}' (PID: {pid}). "
            f"Sentinel triage: {', '.join(actions)}. "
            f"Analisis penyebab crash dari log/kode dan lakukan pemulihan mandiri menggunakan pemeriksaan headless (--check-health) saja; "
            f"JANGAN meluncurkan jendela GUI interaktif yang memblokir shell."
        )
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.settimeout(2.0)
        client.connect(sock_path)
        client.sendall(json.dumps({"action": "send_prompt", "prompt": prompt}).encode("utf-8"))
        client.recv(1024)
        client.close()
        return True
    except Exception:
        pass
    return False


CRASH_HISTORY_FILE = '/tmp/flowork_sentinel_crash_history.json'
QUARANTINE_FILE = '/tmp/flowork_sentinel_quarantine.json'
DEV_LANDMARK = '/opt/floworkos/flowork.dev'
MAX_HEAL_RETRIES = 2
LOOP_BREAKER_WINDOW_SECS = 600
LOOP_BREAKER_THRESHOLD = 2


def _bus_publish(event_type, payload):
    try:
        bus_port = os.environ.get('FLOWORK_BUS_PORT', '18095')
        bus_url = f'http://127.0.0.1:{bus_port}/api/bus/publish'
        pl = dict(payload) if isinstance(payload, dict) else {'data': payload}
        body = {
            'type': event_type,
            'source': 'self_healing_sentinel',
            'target': str(pl.get('app_id') or pl.get('app') or '*'),
            'action': event_type.split('.')[-1],
            'payload': pl,
        }
        req = urllib.request.Request(bus_url, data=json.dumps(body).encode('utf-8'))
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=2) as _:
            pass
        return True
    except Exception:
        return False


def _is_dev_mode_active():
    return os.path.exists(DEV_LANDMARK)


def _resolve_target_paths(app_id, incident):
    raw_dir = incident.get('app_dir')
    raw_file = incident.get('file')
    if raw_dir and os.path.isdir(raw_dir):
        app_dir = os.path.abspath(raw_dir)
    else:
        cand = os.path.join('/opt/floworkos/apps', app_id)
        app_dir = os.path.abspath(cand) if os.path.isdir(cand) else None

    if not raw_file and app_dir:
        for rel in ('bin/app.py', 'app.py', 'main.py'):
            p = os.path.join(app_dir, rel)
            if os.path.isfile(p):
                raw_file = p
                break
    file_path = os.path.abspath(raw_file) if raw_file and os.path.isfile(raw_file) else raw_file
    return app_dir, file_path


def _is_patch_allowed(app_id, app_dir, file_path):
    """Enforce Track 7.5 allowlist: only non-core /opt/floworkos/apps/<app> or /tmp/flowork_mock_apps/<app>, never @lock/@freez."""
    if not app_dir:
        return False, 'No writable app directory resolved'
    norm_dir = os.path.realpath(app_dir)
    forbidden_roots = (
        '/opt/floworkos/sysd',
        '/opt/floworkos/crates',
        '/opt/floworkos/bin',
        '/opt/floworkos/connector',
        '/opt/floworkos/system',
    )
    if any(norm_dir.startswith(r) for r in forbidden_roots):
        return False, f'Protected OS core directory rejected: {norm_dir}'

    allowed = norm_dir.startswith('/opt/floworkos/apps/') or norm_dir.startswith('/tmp/flowork_mock_apps/')
    if not allowed:
        return False, f'Outside self-heal allowlist: {norm_dir}'

    if file_path and os.path.isfile(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            if '@lock' in content or '@freez' in content:
                return False, f'Protected marker (@lock/@freez) in {file_path}'
        except Exception:
            pass
    return True, 'allowed'


def _record_crash_and_check_loop_breaker(app_id):
    """Track crashes within 10m window; quarantine app if >= 2 crashes in 10 minutes."""
    now = time.time()
    lock_fd = None
    try:
        lock_fd = open(SEEN_LOCK_FILE, 'a+')
        fcntl.flock(lock_fd, fcntl.LOCK_EX)

        quarantined = {}
        if os.path.exists(QUARANTINE_FILE):
            try:
                with open(QUARANTINE_FILE, 'r', encoding='utf-8') as qf:
                    quarantined = json.load(qf)
            except Exception:
                quarantined = {}

        q_until = float(quarantined.get(app_id, 0) or 0)
        if now < q_until:
            return True, int(q_until - now)

        history = {}
        if os.path.exists(CRASH_HISTORY_FILE):
            try:
                with open(CRASH_HISTORY_FILE, 'r', encoding='utf-8') as hf:
                    history = json.load(hf)
            except Exception:
                history = {}

        stamps = [float(t) for t in history.get(app_id, []) if now - float(t) < LOOP_BREAKER_WINDOW_SECS]
        stamps.append(now)
        history[app_id] = stamps
        _atomic_write_json(CRASH_HISTORY_FILE, history)

        if len(stamps) >= LOOP_BREAKER_THRESHOLD:
            quarantined[app_id] = now + LOOP_BREAKER_WINDOW_SECS
            _atomic_write_json(QUARANTINE_FILE, quarantined)
            return True, len(stamps)
        return False, len(stamps)
    except Exception:
        return False, 0
    finally:
        if lock_fd is not None:
            try:
                fcntl.flock(lock_fd, fcntl.LOCK_UN)
                lock_fd.close()
            except Exception:
                pass


def _run_ocr_and_ast_diagnosis(app_dir, file_path, line_num, detail):
    """Produce structured root-cause diagnosis using AST, /opt/floworkos/bin/ocr, and optional L0 SLM."""
    import ast as py_ast

    diag = {
        'file': file_path,
        'line': line_num,
        'ast_status': 'unknown',
        'ocr_summary': '',
        'root_cause': detail or 'Unknown failure',
        'snippet': '',
    }

    if file_path and os.path.isfile(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                src_lines = f.read().splitlines()
            src_text = '\n'.join(src_lines)
            if file_path.endswith('.py'):
                try:
                    py_ast.parse(src_text)
                    diag['ast_status'] = 'valid_syntax'
                except SyntaxError as se:
                    diag['ast_status'] = f'SyntaxError line {se.lineno}: {se.msg}'
                    if not diag['line'] and se.lineno:
                        diag['line'] = se.lineno

            center = max(1, int(diag['line'] or 1))
            lo = max(0, center - 10)
            hi = min(len(src_lines), center + 10)
            diag['snippet'] = '\n'.join(f'{i + 1}: {src_lines[i]}' for i in range(lo, hi))
        except Exception:
            pass

    ocr_bin = '/opt/floworkos/bin/ocr'
    if os.path.isfile(ocr_bin) and app_dir and os.path.isdir(os.path.join(app_dir, '.git')):
        try:
            rel_arg = os.path.relpath(file_path, app_dir) if file_path and file_path.startswith(app_dir) else '.'
            ocr_res = subprocess.run(
                [ocr_bin, 'scan', '--repo', app_dir, '--path', rel_arg, '--audience', 'agent', '--preview'],
                capture_output=True, text=True, timeout=5
            )
            if ocr_res.returncode == 0:
                diag['ocr_summary'] = ocr_res.stdout.strip()[:400]
        except Exception:
            pass

    # Query L0 Embedded SLM (:18090) briefly for fast local root-cause classification
    try:
        prompt = (
            f"Analyze crash in {file_path or 'unknown'} line {diag['line']}: {detail}\n"
            f"AST: {diag['ast_status']}\nCode:\n{diag['snippet'][:600]}"
        )
        req = urllib.request.Request(
            'http://127.0.0.1:18090/v1/chat/completions',
            data=json.dumps({
                'model': 'l0-router',
                'messages': [{'role': 'user', 'content': prompt}],
                'max_tokens': 160,
            }).encode('utf-8')
        )
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='ignore'))
            msg = data.get('choices', [{}])[0].get('message', {}).get('content', '')
            if msg:
                diag['l0_hint'] = msg[:300]
    except Exception:
        pass

    return diag


def _verify_app_target(app_id, app_dir, file_path):
    """Run headless structural & runtime health check on repaired application."""
    craft_bin = '/opt/floworkos/bin/craft-app'
    official_app_dir = os.path.join('/opt/floworkos/apps', app_id)
    if (
        app_dir == os.path.abspath(official_app_dir)
        and os.path.exists(craft_bin)
        and os.path.isfile(os.path.join(app_dir, 'app.json'))
    ):
        res = subprocess.run([craft_bin, 'test', app_id], capture_output=True, text=True, timeout=12)
        return res.returncode == 0, (res.stdout + '\n' + res.stderr).strip()[:300]

    candidates = []
    if file_path and os.path.isfile(file_path):
        candidates.append(file_path)
    if app_dir:
        for rel in ('bin/app.py', 'app.py', 'main.py'):
            p = os.path.join(app_dir, rel)
            if os.path.isfile(p) and p not in candidates:
                candidates.append(p)

    for cand in candidates:
        if cand.endswith('.py'):
            comp = subprocess.run([sys.executable, '-m', 'py_compile', cand], capture_output=True, text=True, timeout=5)
            if comp.returncode != 0:
                return False, comp.stderr.strip()[:300]
            try:
                run_res = subprocess.run(
                    [sys.executable, cand, '--check-health'],
                    cwd=app_dir or os.path.dirname(cand),
                    capture_output=True, text=True, timeout=5
                )
                if run_res.returncode != 0:
                    return False, (run_res.stderr or run_res.stdout).strip()[:300]
            except subprocess.TimeoutExpired:
                return False, 'Headless health check timed out'
            return True, 'py_compile + headless check passed (Exit Code 0)'

    return False, 'No runnable entrypoint verified'


def _attempt_sandboxed_mrflow_patch(app_id, app_dir, file_path, detail, diagnosis):
    """Invoke mrflow -p confined inside Landlock sandbox restricting writes strictly to app_dir."""
    mrflow_bin = '/opt/floworkos/bin/mrflow'
    sandbox_exec = '/opt/floworkos/bin/flowork-sandbox-exec'
    write_policy = '/opt/floworkos/policies/write.toml'
    if not (os.path.isfile(mrflow_bin) and os.path.isfile(sandbox_exec)):
        return False, 'mrflow or flowork-sandbox-exec missing'

    os.makedirs(CRASH_DIR, exist_ok=True)
    heal_hist_dir = os.path.join(CRASH_DIR, '.heal_history')
    os.makedirs(heal_hist_dir, exist_ok=True)
    heal_manifest = os.path.join(CRASH_DIR, f'.heal_manifest_{app_id}.json')
    _atomic_write_json(heal_manifest, {
        'permissions': {
            'profile': 'strict',
            'allow_network': True,
            'ipc_neural_bus': True,
            'read_paths': [app_dir, '/opt/floworkos'],
            'write_paths': [app_dir, heal_hist_dir, '~/.flowork'],
        }
    })

    fix_prompt = (
        f"You are executing an autonomous closed-loop bugfix ONLY inside {file_path or app_dir}. "
        f"Do NOT touch any file outside {app_dir}. Keep --check-health support intact.\n"
        f"Crash detail: {detail}. Line: {diagnosis.get('line')}. AST: {diagnosis.get('ast_status')}.\n"
        f"Snippet:\n{diagnosis.get('snippet', '')}\n"
        f"If the bug cannot be fixed without breaking requirements or relies on missing external hardware/ABI (e.g. UNFIXABLE), leave it unfixed or fail verification.\n"
        f"Apply the minimal safe code edit to {file_path or app_dir} now using replace/write file tools."
    )

    cmd = [
        sandbox_exec,
        '--app-id', f'heal_{app_id}',
        '--manifest', heal_manifest,
        '--',
        mrflow_bin,
        '--policy', write_policy,
        '--approval-mode', 'auto_edit',
        '--allowed-tools', 'read_file,replace,write_file',
        '--skip-trust',
        '-o', 'json',
        '-p', fix_prompt,
    ]
    sub_env = os.environ.copy()
    sub_env['FLOWORK_HISTORY_DIR'] = heal_hist_dir
    sub_env['FLOWORK_TRUST_WORKSPACE'] = '1'
    try:
        res = subprocess.run(cmd, cwd=app_dir, env=sub_env, capture_output=True, text=True, timeout=55)
        return res.returncode == 0, (res.stdout or res.stderr).strip()[:300]
    except subprocess.TimeoutExpired:
        return False, 'mrflow sandboxed heal timed out'
    except Exception as e:
        return False, str(e)


def _crystallize_heal_episode(app_id, detail, diag, snap_tag, actions):
    cryst_script = '/opt/floworkos/tools/memory_crystallizer/run.py'
    if not os.path.isfile(cryst_script):
        return False
    payload = {
        'action': 'index',
        'category': 'self_healing',
        'session_id': f'sentinel_{app_id}_{int(time.time())}',
        'source': 'sentinel_healer',
        'exit_code': 0,
        'problem': f"App {app_id} crashed ({detail[:140]}) at {diag.get('file')}:{diag.get('line')}",
        'solution': f"Pre-heal snapshot {snap_tag}; AST/OCR diagnosis; patched under Landlock jail and verified Exit 0. Actions: {'; '.join(actions[-3:])}",
        'keywords': ['self-healing', app_id, str(diag.get('ast_status', 'crash')), 'flowork-snapshot', 'rollback'],
    }
    try:
        res = subprocess.run([sys.executable, cryst_script], input=json.dumps(payload), capture_output=True, text=True, timeout=8)
        return res.returncode == 0
    except Exception:
        return False


def remediate_crash_incident(incident, dry_run=False, auto_heal=False):
    """Closed-loop self-healing triage: crash -> snapshot -> ocr/AST -> Landlock mrflow -> test -> restart/rollback."""
    source_file = incident.pop('_source_file', None)
    simulated = dry_run or bool(incident.pop('_simulated', False)) or is_simulated_incident(incident, source_file)
    app_id = incident.get('app') or incident.get('target_app') or 'system'
    detail = str(incident.get('detail') or incident.get('type') or 'unknown crash')
    line_num = incident.get('line')
    actions = []

    if simulated:
        craft_bin = '/opt/floworkos/bin/craft-app'
        official_dir = os.path.join('/opt/floworkos/apps', app_id)
        if os.path.exists(craft_bin) and os.path.isdir(official_dir):
            try:
                test_res = subprocess.run([craft_bin, 'test', app_id], capture_output=True, text=True, timeout=8)
                actions.append(f'Simulated integrity test exit {test_res.returncode} for {app_id}.')
            except Exception:
                pass
        _bus_publish('system.crash.remediated', {'app_id': app_id, 'simulated': True, 'incident': incident, 'actions': actions})
        actions.append(f'Simulated crash triage completed in dry-run mode for {app_id} (sidebar wakeup & desktop popup suppressed).')
        return actions

    app_dir, file_path = _resolve_target_paths(app_id, incident)
    diag = _run_ocr_and_ast_diagnosis(app_dir, file_path, line_num, detail)
    actions.append(f"AST/OCR diagnosis completed for {app_id} ({diag.get('ast_status')}).")

    # Dev-Mode Protection Guard (/opt/floworkos/flowork.dev)
    if _is_dev_mode_active() and not auto_heal:
        _bus_publish('system.crash.diagnosis_ready', {
            'app_id': app_id,
            'file': diag.get('file'),
            'line': diag.get('line'),
            'detail': detail[:240],
            'diagnosis': diag,
            'mode': 'diagnostic_only',
            'apply_fix_cmd': 'flowork-sentinel-daemon --heal --auto-heal',
        })
        actions.append(f'Dev mode active ({DEV_LANDMARK}): Diagnostic-Only triage published for {app_id}; awaiting Apply Fix confirmation.')
        wake_up_mrflow_agent(incident, actions)
        return actions

    # Scope Allowlist & @lock/@freez Guard
    allowed, scope_reason = _is_patch_allowed(app_id, app_dir, file_path)
    if not allowed:
        actions.append(f'Skipped auto-patch due to scope guard: {scope_reason}.')
        _bus_publish('system.crash.remediated', {'app_id': app_id, 'status': 'guarded_skip', 'reason': scope_reason, 'actions': actions})
        return actions

    # Loop Breaker (>= 2 crashes in 10 minutes -> quarantine & rollback)
    tripped, count_or_ttl = _record_crash_and_check_loop_breaker(app_id)
    if tripped:
        rb_code = 'none'
        if os.path.exists('/opt/floworkos/bin/flowork-rollback'):
            rb = subprocess.run(['/opt/floworkos/bin/flowork-rollback', 'latest'], capture_output=True, text=True, timeout=12)
            rb_code = str(rb.returncode)
        _bus_publish('system.crash.quarantined', {
            'app_id': app_id,
            'reason': 'loop_breaker_tripped',
            'crash_count_or_ttl': count_or_ttl,
            'rollback_exit': rb_code,
        })
        actions.append(f'Loop breaker tripped for {app_id}; marked quarantined & rolled back (exit={rb_code}).')
        return actions

    # Step 7.B: Atomic Pre-Heal Snapshot
    snap_tag = f"pre-heal-{app_id}-{int(time.time())}"
    snap_bin = '/opt/floworkos/bin/flowork-snapshot'
    snap_ok = False
    if os.path.exists(snap_bin):
        snap_res = subprocess.run(
            [snap_bin, 'create', '--tag', snap_tag, '--path', app_dir, '--desc', f'Pre-heal atomic snapshot for {app_id}'],
            capture_output=True, text=True, timeout=15
        )
        snap_ok = (snap_res.returncode == 0)
        actions.append(f'Created pre-heal snapshot {snap_tag} (ok={snap_ok}).')

    if not snap_ok:
        actions.append(f'Aborted auto-patch for {app_id}: pre-heal snapshot failed.')
        return actions

    # Step 7.C: Sandboxed Patch & Verification (Max retries)
    healed = False
    verify_detail = ''
    for attempt in range(1, MAX_HEAL_RETRIES + 1):
        ok_before, before_msg = _verify_app_target(app_id, app_dir, file_path)
        if ok_before and attempt == 1 and 'Crash' not in detail:
            healed = True
            verify_detail = before_msg
            actions.append(f'Target {app_id} already verified healthy.')
            break

        patch_ok, patch_msg = _attempt_sandboxed_mrflow_patch(app_id, app_dir, file_path, detail, diag)
        actions.append(f'Attempt {attempt}/{MAX_HEAL_RETRIES} Landlock mrflow patch (ok={patch_ok}): {patch_msg[:100]}')

        v_ok, v_msg = _verify_app_target(app_id, app_dir, file_path)
        verify_detail = v_msg
        if v_ok:
            healed = True
            actions.append(f'Verification passed on attempt {attempt}: {v_msg}')
            break

    if healed:
        # Preserve rolling 10-minute crash timestamps so rapid recurring crashes still trip Loop Breaker
        learned = _crystallize_heal_episode(app_id, detail, diag, snap_tag, actions)
        actions.append(f'Episodic learning crystallized={learned}.')
        _bus_publish('system.crash.remediated', {
            'app_id': app_id,
            'status': 'healed',
            'snapshot_tag': snap_tag,
            'verify': verify_detail,
            'episodic_learned': learned,
            'actions': actions,
        })
        try:
            subprocess.run(
                ['notify-send', '-i', 'emblem-default', 'Mr. Flow Self-Healing', f'App [{app_id}] repaired & verified cleanly.'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
            )
        except Exception:
            pass
    else:
        rb_bin = '/opt/floworkos/bin/flowork-rollback'
        rb_code = -1
        if os.path.exists(rb_bin):
            rb_res = subprocess.run([rb_bin, snap_tag], capture_output=True, text=True, timeout=15)
            rb_code = rb_res.returncode
        actions.append(f'Heal failed after {MAX_HEAL_RETRIES} attempts ({verify_detail[:80]}); Rolled back to {snap_tag} (exit={rb_code}).')
        _bus_publish('system.crash.remediated', {
            'app_id': app_id,
            'status': 'rolled_back',
            'snapshot_tag': snap_tag,
            'rollback_exit': rb_code,
            'actions': actions,
        })
        try:
            subprocess.run(
                ['notify-send', '-u', 'critical', '-i', 'dialog-error', 'Mr. Flow Rollback', f'Self-heal failed for [{app_id}]; restored snapshot {snap_tag}.'],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
            )
        except Exception:
            pass

    return actions


def diagnose_all(consume_traps=False):
    sysd_ok, sysd_resp = check_http('http://127.0.0.1:18090/api/kernel/status')
    conn_ok, conn_resp = check_http('http://127.0.0.1:9099/health')
    mem_stat = check_mem()
    shm_stat = check_shm_usage()
    traps = check_kernel_traps(consume=consume_traps)

    is_healthy = (sysd_ok and conn_ok and mem_stat.get('pressure') == 'normal' and len(traps) == 0)

    return {
        'status': 'healthy' if is_healthy else 'degraded',
        'components': {
            'flowork_sysd': {'healthy': sysd_ok, 'endpoint': '18090', 'detail': sysd_resp[:80] if sysd_ok else sysd_resp},
            'sovereign_connector': {'healthy': conn_ok, 'endpoint': '9099', 'detail': conn_resp[:80] if conn_ok else conn_resp},
            'memory_health': mem_stat,
            'shm_scratchpad': shm_stat,
            'kernel_traps': {'active_incidents': len(traps), 'traps': traps}
        }
    }


def heal_system(diagnosis, dry_run=False, auto_heal=False):
    actions_taken = []
    comps = diagnosis.get('components', {})

    # 1. Sysd healing
    if not dry_run and not comps.get('flowork_sysd', {}).get('healthy', False):
        try:
            subprocess.run(['systemctl', '--user', 'restart', 'flowork-sysd'], check=False, timeout=8)
            actions_taken.append('Restarted flowork-sysd service via systemctl user daemon.')
        except Exception as e:
            actions_taken.append(f'Failed to restart sysd: {e}')

    # 2. Connector healing (delegate via systemd mrflow-router.service to prevent :9099 port races)
    if not dry_run and not comps.get('sovereign_connector', {}).get('healthy', False):
        try:
            state_res = subprocess.run(
                ['systemctl', '--user', 'show', '-p', 'ActiveState', '--value', 'mrflow-router.service'],
                capture_output=True, text=True, timeout=3
            )
            router_state = state_res.stdout.strip()
        except Exception:
            router_state = ''

        if router_state == 'activating':
            actions_taken.append('Deferred connector healing while mrflow-router.service is activating.')
        else:
            started_via_systemd = False
            try:
                subprocess.run(['systemctl', '--user', 'reset-failed', 'mrflow-router.service'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
                res_sd = subprocess.run(['systemctl', '--user', 'restart', 'mrflow-router.service'],
                                        capture_output=True, text=True, timeout=8)
                if res_sd.returncode == 0:
                    actions_taken.append('Started mrflow-router.service via systemctl user daemon.')
                    started_via_systemd = True
            except Exception:
                pass

            if not started_via_systemd:
                daemon_bin = '/usr/local/bin/mrflow-router-daemon'
                if os.path.exists(daemon_bin):
                    try:
                        subprocess.Popen(
                            [daemon_bin],
                            stdin=subprocess.DEVNULL,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                            start_new_session=True,
                        )
                        actions_taken.append('Spawned headless mrflow-router-daemon fallback.')
                    except Exception as e:
                        actions_taken.append(f'Failed to start mrflow-router-daemon: {e}')

    # 3. Clean stale shm artifacts
    stale_cnt = comps.get('shm_scratchpad', {}).get('stale_artifacts_count', 0)
    if stale_cnt > 0:
        cleaned = 0
        now = time.time()
        for root, dirs, files in os.walk('/dev/shm'):
            for file in files:
                if file.startswith(('frame_', 'tmp_', 'screenshot_')):
                    fp = os.path.join(root, file)
                    try:
                        if now - os.stat(fp).st_mtime > 300:
                            os.remove(fp)
                            cleaned += 1
                    except Exception:
                        pass
        actions_taken.append(f'Pruned {cleaned} stale temporary frames from /dev/shm.')

    # 4. Remediate kernel crash traps
    trap_info = comps.get('kernel_traps', {})
    traps = trap_info.get('traps', [])
    for incident in traps:
        rem_actions = remediate_crash_incident(incident, dry_run=dry_run, auto_heal=auto_heal)
        actions_taken.extend(rem_actions)

    if not actions_taken:
        actions_taken.append('No degradation detected. All sovereign services healthy.')

    return actions_taken


def main():
    try:
        raw_in = sys.stdin.read().strip()
        params = json.loads(raw_in) if raw_in else {}
        action = params.get('action', 'diagnose')
        dry_run = (
            bool(params.get('dry_run', False))
            or os.environ.get('FLOWORK_SENTINEL_DRY_RUN') == '1'
            or '--dry-run' in sys.argv
        )
        auto_heal = (
            bool(params.get('auto_heal', False))
            or os.environ.get('FLOWORK_SENTINEL_AUTO_HEAL') == '1'
            or '--auto-heal' in sys.argv
        )

        if action == 'diagnose':
            diag = diagnose_all(consume_traps=False)
            print(json.dumps(diag, indent=2))
        elif action in ('heal', 'daemon_tick'):
            diag = diagnose_all(consume_traps=True)
            actions = heal_system(diag, dry_run=dry_run, auto_heal=auto_heal)
            print(json.dumps({
                'status': 'ok',
                'initial_health': diag['status'],
                'actions_taken': actions,
                'post_healing': diagnose_all(consume_traps=False)
            }, indent=2))
        else:
            print(json.dumps({'status': 'error', 'message': f'Unknown action {action}'}))
            sys.exit(1)

    except Exception as e:
        sys.stderr.write(f'Sentinel error: {e}')
        print(json.dumps({'status': 'error', 'error': str(e)}))
        sys.exit(1)


if __name__ == '__main__':
    main()
