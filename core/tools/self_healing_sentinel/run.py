#!/usr/bin/env python3
import sys
import os
import re
import json
import socket
import hashlib
import urllib.request
import urllib.error
import subprocess
import time

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

def check_kernel_traps():
    """Scan dmesg and system logs for recent kernel traps, segfaults, and crash dumps."""
    traps = []
    seen_file = '/tmp/flowork_sentinel_seen_traps.json'
    seen_traps = set()
    is_initial_seed = False

    if os.path.exists(seen_file):
        try:
            with open(seen_file, 'r') as sf:
                seen_traps = set(json.load(sf))
        except Exception:
            seen_traps = set()
    else:
        is_initial_seed = True

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

                        if is_initial_seed:
                            seen_traps.add(line_hash)
                        elif line_hash not in seen_traps:
                            seen_traps.add(line_hash)
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

    crash_dir = '/tmp/flowork_crashes'
    if os.path.isdir(crash_dir):
        for f in os.listdir(crash_dir):
            if f.endswith('.json'):
                try:
                    f_hash = hashlib.sha256(f.encode('utf-8')).hexdigest()[:16]
                    if is_initial_seed:
                        seen_traps.add(f_hash)
                    elif f_hash not in seen_traps:
                        seen_traps.add(f_hash)
                        with open(os.path.join(crash_dir, f), 'r') as cf:
                            traps.append(json.load(cf))
                except Exception:
                    pass

    try:
        with open(seen_file, 'w') as sf:
            json.dump(list(seen_traps)[-500:], sf)
    except Exception:
        pass

    return traps

def wake_up_mrflow_agent(incident, actions):
    """Wake up Mr. Flow sidebar agent via Unix Domain Socket."""
    try:
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

        app_name = incident.get('app') or incident.get('target_app') or 'system'
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

        if not status_data.get("is_busy", False):
            prompt = (
                f"🚨 [AUTONOMOUS CRASH SENTINEL]: Terdeteksi insiden {trap_type} pada aplikasi/proses '{app_name}' (PID: {pid}). "
                f"Sentinel triage: {', '.join(actions)}. Analisis penyebab crash dan lakukan pemulihan mandiri sekarang."
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

def remediate_crash_incident(incident):
    """Autonomously triage and remediate a crashed application."""
    app_id = incident.get('app') or incident.get('target_app') or 'system'
    actions = []

    app_dir = os.path.join('/opt/floworkos/apps', app_id)
    craft_bin = '/opt/floworkos/bin/craft-app'
    if os.path.exists(craft_bin) and os.path.isdir(app_dir):
        test_res = subprocess.run([craft_bin, 'test', app_id], capture_output=True, text=True)
        if test_res.returncode != 0:
            actions.append(f'Detected failure in {app_id}: {test_res.stderr.strip()[:100]}')
            rollback_bin = '/opt/floworkos/bin/flowork-rollback'
            if os.path.exists(rollback_bin):
                rb_res = subprocess.run([rollback_bin, 'latest'], capture_output=True, text=True)
                actions.append(f'Executed rollback: exit {rb_res.returncode}')
        else:
            actions.append(f'Integrity test passed for {app_id}; app is structurally sound.')
    else:
        actions.append(f'Logged crash trap for process {app_id}.')

    try:
        bus_port = os.environ.get('FLOWORK_BUS_PORT', '18095')
        bus_url = f'http://127.0.0.1:{bus_port}/api/bus/publish'
        evt = json.dumps({
            'type': 'system.crash.remediated',
            'app_id': app_id,
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

    try:
        subprocess.run(
            ['notify-send', '-i', 'dialog-warning', 'Mr. Flow Sentinel', f'Process/App [{app_id}] crash intercepted & remediated.'],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except Exception:
        pass

    # Wake up Mr. Flow autonomous agent
    if wake_up_mrflow_agent(incident, actions):
        actions.append(f'Dispatched autonomous turn to Mr. Flow sidebar for {app_id}.')
    else:
        actions.append('Mr. Flow agent was notified or currently busy.')

    return actions

def diagnose_all():
    sysd_ok, sysd_resp = check_http('http://127.0.0.1:18090/api/kernel/status')
    conn_ok, conn_resp = check_http('http://127.0.0.1:9099/health')
    mem_stat = check_mem()
    shm_stat = check_shm_usage()
    traps = check_kernel_traps()

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

def heal_system(diagnosis):
    actions_taken = []
    comps = diagnosis.get('components', {})

    # 1. Sysd healing
    if not comps.get('flowork_sysd', {}).get('healthy', False):
        try:
            subprocess.run(['systemctl', '--user', 'restart', 'flowork-sysd'], check=False)
            actions_taken.append('Restarted flowork-sysd service via systemctl user daemon.')
        except Exception as e:
            actions_taken.append(f'Failed to restart sysd: {e}')

    # 2. Connector healing
    if not comps.get('sovereign_connector', {}).get('healthy', False):
        start_sh = '/opt/floworkos/connector/start.sh'
        if os.path.exists(start_sh):
            try:
                subprocess.Popen(['/bin/bash', start_sh], cwd='/opt/floworkos/connector')
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
        rem_actions = remediate_crash_incident(incident)
        actions_taken.extend(rem_actions)

    if not actions_taken:
        actions_taken.append('No degradation detected. All sovereign services healthy.')

    return actions_taken

def main():
    try:
        raw_in = sys.stdin.read().strip()
        params = json.loads(raw_in) if raw_in else {}
        action = params.get('action', 'diagnose')

        diag = diagnose_all()

        if action == 'diagnose':
            print(json.dumps(diag, indent=2))
        elif action in ('heal', 'daemon_tick'):
            actions = heal_system(diag)
            print(json.dumps({
                'status': 'ok',
                'initial_health': diag['status'],
                'actions_taken': actions,
                'post_healing': diagnose_all()
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
