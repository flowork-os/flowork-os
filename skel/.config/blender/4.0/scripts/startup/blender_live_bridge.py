import bpy
import socket
import json
import traceback
import math

HOST = "127.0.0.1"
PORT = 9876

_server_socket = None

def init_server_socket():
    global _server_socket
    if _server_socket is not None:
        return _server_socket
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((HOST, PORT))
        sock.listen(5)
        sock.setblocking(False)
        _server_socket = sock
        print(f"⚡ [BLENDER LIVE BRIDGE] Successfully listening on {HOST}:{PORT}")
        return _server_socket
    except Exception as e:
        print(f"⚠️ [BLENDER LIVE BRIDGE] Failed to bind {HOST}:{PORT}: {e}")
        return None

def trigger_viewport_redraw():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == 'VIEW_3D':
                area.tag_redraw()

def process_client(client_sock):
    try:
        data = client_sock.recv(65536)
        if not data:
            return False
            
        payload = json.loads(data.decode('utf-8'))
        code = payload.get("code", "")
        
        # Execute code in Blender context
        exec_globals = {
            "bpy": bpy,
            "context": bpy.context,
            "data": bpy.data,
            "ops": bpy.ops,
            "math": math
        }
        
        exec(code, exec_globals)
        trigger_viewport_redraw()
        
        resp = {"status": "ok", "message": "Executed successfully"}
        client_sock.sendall((json.dumps(resp) + "\n").encode('utf-8'))
        return True
    except Exception as e:
        err_msg = traceback.format_exc()
        resp = {"status": "error", "error": str(e), "traceback": err_msg}
        try:
            client_sock.sendall((json.dumps(resp) + "\n").encode('utf-8'))
        except:
            pass
        return False
    finally:
        try:
            client_sock.close()
        except:
            pass

def poll_bridge_events():
    global _server_socket
    if not _server_socket:
        _server_socket = init_server_socket()
        if not _server_socket:
            return 0.5  # retry later if failed
        
    try:
        while True:
            try:
                client_sock, addr = _server_socket.accept()
                client_sock.setblocking(True)
                process_client(client_sock)
            except (BlockingIOError, InterruptedError):
                break
    except Exception as e:
        pass
        
    return 0.05  # Poll every 50ms (ultra-responsive, near zero CPU)

def register():
    init_server_socket()
    if not bpy.app.timers.is_registered(poll_bridge_events):
        # persistent=True ensures timer persists across loading/opening new blend files!
        bpy.app.timers.register(poll_bridge_events, first_interval=0.05, persistent=True)
        print("🚀 [BLENDER LIVE BRIDGE] Registered into bpy.app.timers (persistent=True)")

def unregister():
    global _server_socket
    if bpy.app.timers.is_registered(poll_bridge_events):
        bpy.app.timers.unregister(poll_bridge_events)
    if _server_socket:
        try:
            _server_socket.close()
        except:
            pass
        _server_socket = None

# Bind socket immediately on import
init_server_socket()
register()
