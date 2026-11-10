#!/usr/bin/env python3
import sys
import json
import urllib.request
import urllib.error

SYSD_URL = 'http://127.0.0.1:18090'

def http_req(path, data=None, method='GET'):
    url = f'{SYSD_URL}{path}'
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    body = json.dumps(data).encode('utf-8') if data is not None else None
    with urllib.request.urlopen(req, data=body, timeout=5) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    try:
        raw_in = sys.stdin.read().strip()
        params = json.loads(raw_in) if raw_in else {}
        action = params.get('action', 'telemetry')

        if action == 'telemetry':
            res = http_req('/api/system/display/drm')
            print(json.dumps({'status': 'ok', 'telemetry': res}))
        elif action == 'capture':
            res = http_req('/api/system/display/capture', data={}, method='POST')
            print(json.dumps({'status': 'ok', 'capture': res}))
        elif action == 'click':
            payload = {
                'action': 'click',
                'button': params.get('button', 'left'),
                'x': params.get('x', 100),
                'y': params.get('y', 100)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'mouse_move':
            payload = {
                'action': 'move',
                'dx': params.get('dx', 0),
                'dy': params.get('dy', 0)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'key_press':
            payload = {
                'action': 'key',
                'keycode': params.get('keycode', 28)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'list_windows':
            res = http_req('/api/system/windows')
            print(json.dumps({'status': 'ok', 'windows': res}))
        elif action == 'focus_window':
            win_id = params.get('window_id', 0)
            res = http_req('/api/system/windows/focus', data={'id': win_id}, method='POST')
            print(json.dumps(res))
        else:
            print(json.dumps({'status': 'error', 'message': f'Unknown action {action}'}))
            sys.exit(1)

    except urllib.error.URLError as e:
        sys.stderr.write(f'sysd communication error: {e}')
        print(json.dumps({'status': 'error', 'error': f'Failed to communicate with sysd: {e}'}))
        sys.exit(1)
    except Exception as e:
        sys.stderr.write(f'Actuator error: {e}')
        print(json.dumps({'status': 'error', 'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
