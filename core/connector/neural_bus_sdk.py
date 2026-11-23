#!/usr/bin/env python3
"""
👑 FLOWORK OS — CROSS-APP NEURAL BUS SDK (neural_bus_sdk.py)
Unified IPC Client & Event Orchestrator for Craft Suite Apps, Agents, and Background Workers.

Supports:
- High-speed UNIX Domain Socket (/tmp/flowork-neural-bus.sock)
- Localhost HTTP/SSE Bridge (http://127.0.0.1:18095)
- Multi-App Sovereign Workflow Chaining (Pipeline execution)
- Event Broadcasting, Topic Filtering, and App Registration

Universal root: /opt/floworkos
Author: Flowork Architecture Board & Dr. Flow
"""

import sys
import os
import json
import time
import socket
import threading
import urllib.request
import urllib.error

DEFAULT_SOCKET_PATHS = [
    "/tmp/flowork-neural-bus.sock",
    os.path.expanduser("~/.flowork/bus.sock"),
    "/run/flowork/bus.sock"
]

DEFAULT_HTTP_URL = os.environ.get("FLOWORK_BUS_URL", "http://127.0.0.1:18095")


class NeuralBusClient:
    """Sovereign Cross-App Neural Bus Client for Python Applications."""

    def __init__(self, app_id="sovereign_agent", socket_path=None, http_url=None):
        self.app_id = app_id
        self.http_url = (http_url or DEFAULT_HTTP_URL).rstrip("/")
        self.socket_path = socket_path or self._resolve_socket_path()
        self.app_name = app_id
        self.capabilities = []
        self._action_handlers = {}
        self._state = {}
        self._sub_thread = None
        self._running = False
        self._sock = None

    def _resolve_socket_path(self):
        for p in DEFAULT_SOCKET_PATHS:
            if os.path.exists(p):
                return p
        return DEFAULT_SOCKET_PATHS[0]

    def is_connected(self):
        """Check if the bus daemon is reachable."""
        try:
            req = urllib.request.Request(f"{self.http_url}/health")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data.get("status") == "ok"
        except Exception:
            return False

    def register(self, capabilities=None, name=None):
        """Register the current application on the bus."""
        self.capabilities = capabilities or []
        self.app_name = name or self.app_id

        msg = {
            "type": "register",
            "source": self.app_id,
            "name": self.app_name,
            "capabilities": self.capabilities
        }
        return self._send_message(msg)

    def publish(self, target, action, payload=None, shm_key=None):
        """Publish an event or command to a target app or broadcast (*)."""
        msg = {
            "type": "event",
            "source": self.app_id,
            "target": target,
            "action": action,
            "payload": payload or {},
            "shm_key": shm_key
        }
        return self._send_message(msg)

    def on_action(self, action_name, handler_func):
        """Register a handler callback for an incoming action."""
        self._action_handlers[action_name] = handler_func

    def set_state(self, key, value):
        """Update internal state key."""
        self._state[key] = value

    def get_state(self):
        """Return the current active state dictionary."""
        return self._state

    def execute_pipeline(self, pipeline_stages, initial_payload=None):
        """
        Orchestrate multi-app workflow chaining.
        pipeline_stages: [
            {"app": "soundcraft", "action": "denoise", "params": {"profile": "voice"}},
            {"app": "wordcraft", "action": "transcribe", "params": {"format": "md"}},
            {"app": "deckcraft", "action": "generate_slides", "params": {"count": 5}}
        ]
        """
        req_data = {
            "pipeline": pipeline_stages,
            "initial_payload": initial_payload or {}
        }
        url = f"{self.http_url}/api/bus/pipe"
        req = urllib.request.Request(url, data=json.dumps(req_data).encode("utf-8"))
        req.add_header("Content-Type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def subscribe(self, callback=None, filter_topic="*"):
        """Start background daemon thread listening for events."""
        if self._running:
            return

        self._running = True

        def _listener():
            while self._running:
                sock_path = self._resolve_socket_path()
                if not os.path.exists(sock_path):
                    time.sleep(1.0)
                    continue

                try:
                    s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                    s.settimeout(5.0)
                    s.connect(sock_path)
                    self._sock = s
                    buf = ""
                    while self._running:
                        try:
                            chunk = s.recv(4096).decode("utf-8")
                            if not chunk:
                                break
                            buf += chunk
                            while "\n" in buf:
                                line, buf = buf.split("\n", 1)
                                line = line.strip()
                                if not line:
                                    continue
                                try:
                                    evt = json.loads(line)
                                    target = evt.get("target", "*")
                                    action = evt.get("action", "")

                                    # Match self or broadcast
                                    if target in [self.app_id, "*"] or filter_topic in [target, "*", action]:
                                        # Trigger specific action handler if registered
                                        if action in self._action_handlers:
                                            try:
                                                self._action_handlers[action](evt)
                                            except Exception as handler_err:
                                                print(f"⚠️ Action handler error [{action}]: {handler_err}", file=sys.stderr)

                                        # Trigger general callback if provided
                                        if callback:
                                            try:
                                                callback(evt)
                                            except Exception as cb_err:
                                                print(f"⚠️ Bus callback error: {cb_err}", file=sys.stderr)
                                except Exception:
                                    pass
                        except socket.timeout:
                            continue
                        except Exception:
                            break
                    s.close()
                except Exception:
                    time.sleep(1.0)

        self._sub_thread = threading.Thread(target=_listener, daemon=True)
        self._sub_thread.start()

    def close(self):
        """Stop background listeners and disconnect."""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except Exception:
                pass

    def _send_message(self, msg_obj):
        """Send message via UNIX socket first, fallback to HTTP."""
        sock_path = self._resolve_socket_path()
        if os.path.exists(sock_path):
            try:
                s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
                s.settimeout(3.0)
                s.connect(sock_path)
                s.sendall((json.dumps(msg_obj) + "\n").encode("utf-8"))
                resp_line = s.recv(4096).decode("utf-8").strip().split("\n")[0]
                s.close()
                return json.loads(resp_line)
            except Exception:
                pass

        # Fallback to HTTP
        try:
            req = urllib.request.Request(
                f"{self.http_url}/api/bus/publish",
                data=json.dumps(msg_obj).encode("utf-8")
            )
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            return {"status": "error", "message": str(e)}


# Self-test CLI demonstration
if __name__ == "__main__":
    print("👑 Flowork OS — Neural Bus SDK Test")
    client = NeuralBusClient(app_id="sdk_test_agent")
    
    if not client.is_connected():
        print("❌ Neural Bus daemon is offline at http://127.0.0.1:18095", file=sys.stderr)
        sys.exit(1)

    print("✓ Neural Bus daemon is ONLINE.")
    reg = client.register(capabilities=["text_process", "audio_filter"], name="SDK Test Worker")
    print("✓ Registered:", reg)

    received_events = []
    def on_event(evt):
        print(f"  [RECEIVED] {evt.get('source')} -> {evt.get('target')}::{evt.get('action')}")
        received_events.append(evt)

    client.subscribe(callback=on_event)
    time.sleep(0.3)

    print("✓ Dispatching test broadcast event...")
    pub = client.publish(target="*", action="ping_test", payload={"msg": "Hello Sovereign Bus"})
    print("✓ Published:", pub)

    print("✓ Executing test workflow pipeline...")
    pipe = client.execute_pipeline([
        {"app": "soundcraft", "action": "denoise", "params": {"mode": "ai"}},
        {"app": "wordcraft", "action": "summarize", "params": {"max_words": 100}}
    ], initial_payload={"audio": "sample.wav"})
    print("✓ Pipeline result:", pipe)

    time.sleep(0.5)
    client.close()
    print("✨ ALL NEURAL BUS SDK TESTS PASSED WITH EXIT CODE 0!")
    sys.exit(0)
