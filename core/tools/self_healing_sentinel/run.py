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


def remediate_crash_incident(incident, dry_run=False):
    """Autonomously triage and remediate a crashed application."""
    source_file = incident.pop('_source_file', None)
    simulated = dry_run or bool(incident.pop('_simulated', False)) or is_simulated_incident(incident, source_file)
    app_id = incident.get('app') or incident.get('target_app') or 'system'
    actions = []

    app_dir = os.path.join('/opt/floworkos/apps', app_id)
    craft_bin = '/opt/floworkos/bin/craft-app'
    if os.path.exists(craft_bin) and os.path.isdir(app_dir):
        try:
            test_res = subprocess.run([craft_bin, 'test', app_id], capture_output=True, text=True, timeout=8)
            if test_res.returncode != 0:
                actions.append(f'Detected failure in {app_id}: {test_res.stderr.strip()[:100]}')
                rollback_bin = '/opt/floworkos/bin/flowork-rollback'
                if not simulated and os.path.exists(rollback_bin):
                    rb_res = subprocess.run([rollback_bin, 'latest'], capture_output=True, text=True, timeout=10)
                    actions.append(f'Executed rollback: exit {rb_res.returncode}')
            else:
                actions.append(f'Integrity test passed for {app_id}; app is structurally sound.')
        except subprocess.TimeoutExpired:
            actions.append(f'Headless integrity check timed out for {app_id}.')
    else:
        actions.append(f'Logged crash trap for process {app_id}.')

    try:
        bus_port = os.environ.get('FLOWORK_BUS_PORT', '18095')
        bus_url = f'http://127.0.0.1:{bus_port}/api/bus/publish'
        evt = json.dumps({
            'type': 'system.crash.remediated',
            'app_id': app_id,
            'simulated': simulated,
            'incident': incident,
            'actions': actions
        }).encode('utf-8')
        req = urllib.request.Request(bus_url, data=evt)
        req.add_header('Content-Type', 'application/json')
        with urllib.request.urlopen(req, timeout=2) as _:
            pass
        actions.append(f'Emitted system.crash.remediated event for {app_id} over Neural Bus.')
    except Exception:
        pass

    if simulated:
        actions.append(f'Simulated crash triage completed in dry-run mode for {app_id} (sidebar wakeup & desktop popup suppressed).')
        return actions

    try:
        subprocess.run(
            ['notify-send', '-i', 'dialog-warning', 'Mr. Flow Sentinel', f'Process/App [{app_id}] crash intercepted & remediated.'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=2
        )
    except Exception:
        pass

    # Wake up Mr. Flow autonomous agent (cooldown & headless-only guarded)
    if wake_up_mrflow_agent(incident, actions):
        actions.append(f'Dispatched autonomous turn to Mr. Flow sidebar for {app_id}.')
    else:
        actions.append('Mr. Flow agent wakeup deferred (busy, cooldown active, or guarded).')

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


def heal_system(diagnosis, dry_run=False):
    actions_taken = []
    comps = diagnosis.get('components', {})

    # 1. Sysd healing
    if not dry_run and not comps.get('flowork_sysd', {}).get('healthy', False):
        try:
            subprocess.run(['systemctl', '--user', 'restart', 'flowork-sysd'], check=False, timeout=8)
            actions_taken.append('Restarted flowork-sysd service via systemctl user daemon.')
        except Exception as e:
            actions_taken.append(f'Failed to restart sysd: {e}')

    # 2. Connector healing
    if not dry_run and not comps.get('sovereign_connector', {}).get('healthy', False):
        start_sh = '/opt/floworkos/connector/start.sh'
        if os.path.exists(start_sh):
            try:
                subprocess.Popen(
                    ['/bin/bash', start_sh],
                    cwd='/opt/floworkos/connector',
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                actions_taken.append('Spawned connector start.sh background launcher.')
            except Exception as e:
                actions_taken.append(f'Failed to start connector: {e}')

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
        rem_actions = remediate_crash_incident(incident, dry_run=dry_run)
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

        if action == 'diagnose':
            diag = diagnose_all(consume_traps=False)
            print(json.dumps(diag, indent=2))
        elif action in ('heal', 'daemon_tick'):
            diag = diagnose_all(consume_traps=True)
            actions = heal_system(diag, dry_run=dry_run)
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
