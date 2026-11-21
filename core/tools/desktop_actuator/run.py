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
    with urllib.request.urlopen(req, data=body, timeout=30) as resp:
        return json.loads(resp.read().decode('utf-8'))

def main():
    try:
        raw_in = sys.stdin.read().strip()
        params = json.loads(raw_in) if raw_in else {}
        action = params.get('action', 'telemetry')

        # High-Speed Action Batching / Macro Sequences
        if 'sequence' in params or 'batch' in params or 'steps' in params or action in ('sequence', 'batch'):
            steps = params.get('sequence') or params.get('batch') or params.get('steps') or []
            res = http_req('/api/agent/input/hardware', data={'action': 'sequence', 'sequence': steps}, method='POST')
            print(json.dumps(res))
            return

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
                'clicks': params.get('clicks', 1),
                'interval_ms': params.get('interval_ms', 20),
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
        elif action in ('mouse_down', 'down'):
            payload = {
                'action': 'mouse_down',
                'button': params.get('button', 'left')
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action in ('mouse_up', 'up'):
            payload = {
                'action': 'mouse_up',
                'button': params.get('button', 'left')
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'drag':
            payload = {
                'action': 'drag',
                'via': params.get('via', []),
                'button': params.get('button', 'left'),
                'step_delay_ms': params.get('step_delay_ms', 5)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'scroll':
            payload = {
                'action': 'scroll',
                'delta': params.get('delta', 0)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action in ('key_press', 'key'):
            payload = {
                'action': 'key',
                'keycode': params.get('keycode', 28)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'key_down':
            payload = {
                'action': 'key_down',
                'keycode': params.get('keycode', 28)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'key_up':
            payload = {
                'action': 'key_up',
                'keycode': params.get('keycode', 28)
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action == 'hotkey':
            payload = {
                'action': 'hotkey',
                'keycodes': params.get('keycodes', [])
            }
            res = http_req('/api/agent/input/hardware', data=payload, method='POST')
            print(json.dumps(res))
        elif action in ('type_text', 'type'):
            payload = {
                'action': 'type_text',
                'text': params.get('text', '')
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
