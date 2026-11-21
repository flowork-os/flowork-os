#!/usr/bin/env python3
"""
Flowork Sovereign Stealth Supervisor
Attaches to Chrome via CDP (Chrome DevTools Protocol) and injects
the synthetic Hardware DNA before any webpage script executes.
Bypasses Chrome 137+ --load-extension restrictions with 100% reliability.
"""

import asyncio
import json
import urllib.request
import subprocess
import time
import sys
from pathlib import Path

async def inject_stealth(port, config_dict, target_url):
    retries = 25
    tabs = None
    for _ in range(retries):
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/json", timeout=1) as resp:
                tabs = json.loads(resp.read().decode())
                if tabs:
                    break
        except Exception:
            await asyncio.sleep(0.2)

    if not tabs:
        print(f"[!] Could not connect to Chrome on port {port}")
        return False

    pages = [t for t in tabs if t.get("type") == "page"]
    if not pages:
        return False
    target = pages[0]
    ws_url = target.get("webSocketDebuggerUrl")
    if not ws_url:
        return False

    import websockets
    async with websockets.connect(ws_url) as ws:
        # Enable Page and Target domains
        await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        await ws.send(json.dumps({
            "id": 2,
            "method": "Target.setAutoAttach",
            "params": {"autoAttach": True, "waitForDebuggerOnStart": False, "flatten": True}
        }))

        # Generate Stealth Injection Script
        cfg = config_dict
        os_family = cfg.get("os", "windows")
        uad_platform = "Windows" if os_family == "windows" else ("macOS" if os_family == "mac" else "Linux")
        uad_version = "15.0.0" if os_family == "windows" else ("14.5.0" if os_family == "mac" else "6.8.0")
        
        stealth_code = f"""
        (function() {{
            'use strict';
            if (window.__FLOWORK_STEALTH_ATTACHED__) return;
            window.__FLOWORK_STEALTH_ATTACHED__ = true;

            const makeNative = (fn, name) => {{
                try {{ Object.defineProperty(fn, 'name', {{ value: name || '', configurable: true }}); }} catch(_) {{}}
                const nativeStr = 'function ' + (name || '') + '() {{ [native code] }}';
                const customToString = function toString() {{
                    if (this === customToString) return 'function toString() {{ [native code] }}';
                    return nativeStr;
                }};
                try {{
                    Object.defineProperty(fn, 'toString', {{ value: customToString, configurable: true, writable: true }});
                }} catch(_) {{}}
                return fn;
            }};

            // 1. NAVIGATOR MASKING
            const navProto = Navigator.prototype;
            Object.defineProperty(navProto, 'webdriver', {{ get: makeNative(() => undefined, 'get webdriver'), configurable: true }});
            Object.defineProperty(navProto, 'platform', {{ get: makeNative(() => '{cfg.get("platform", "Win32")}', 'get platform'), configurable: true }});
            Object.defineProperty(navProto, 'userAgent', {{ get: makeNative(() => '{cfg.get("userAgent")}', 'get userAgent'), configurable: true }});
            Object.defineProperty(navProto, 'appVersion', {{ get: makeNative(() => '{cfg.get("appVersion")}', 'get appVersion'), configurable: true }});
            Object.defineProperty(navProto, 'hardwareConcurrency', {{ get: makeNative(() => {cfg.get("hardwareConcurrency", 16)}, 'get hardwareConcurrency'), configurable: true }});
            Object.defineProperty(navProto, 'deviceMemory', {{ get: makeNative(() => {cfg.get("deviceMemory", 16)}, 'get deviceMemory'), configurable: true }});

            // 2. CLIENT HINTS (navigator.userAgentData)
            const fakeUAD = {{
                brands: [
                    {{ brand: 'Chromium', version: '130' }},
                    {{ brand: 'Google Chrome', version: '130' }},
                    {{ brand: 'Not?A_Brand', version: '99' }}
                ],
                mobile: false,
                platform: '{uad_platform}',
                getHighEntropyValues: makeNative(function(hints) {{
                    return Promise.resolve({{
                        brands: fakeUAD.brands,
                        mobile: false,
                        platform: '{uad_platform}',
                        platformVersion: '{uad_version}',
                        architecture: 'x86',
                        bitness: '64',
                        model: ''
                    }});
                }}, 'getHighEntropyValues'),
                toJSON: makeNative(function() {{
                    return {{ brands: fakeUAD.brands, mobile: false, platform: '{uad_platform}' }};
                }}, 'toJSON')
            }};
            Object.defineProperty(navProto, 'userAgentData', {{ get: makeNative(() => fakeUAD, 'get userAgentData'), configurable: true }});

            // 3. SCREEN PROPERTIES
            const screenProto = Screen.prototype;
            Object.defineProperty(screenProto, 'width', {{ get: makeNative(() => {cfg.get("screenWidth", 1920)}, 'get width'), configurable: true }});
            Object.defineProperty(screenProto, 'height', {{ get: makeNative(() => {cfg.get("screenHeight", 1080)}, 'get height'), configurable: true }});
            Object.defineProperty(screenProto, 'availWidth', {{ get: makeNative(() => {cfg.get("screenWidth", 1920)}, 'get availWidth'), configurable: true }});
            Object.defineProperty(screenProto, 'availHeight', {{ get: makeNative(() => {cfg.get("screenHeight", 1080) - 40}, 'get availHeight'), configurable: true }});

            // 4. WEBGL GPU & RENDERER MASKING
            const patchGL = (proto) => {{
                if (!proto) return;
                const orig = proto.getParameter;
                proto.getParameter = makeNative(function(pname) {{
                    if (pname === 37445 || pname === 7936) return '{cfg.get("webglVendor", "Google Inc. (NVIDIA)")}';
                    if (pname === 37446 || pname === 7937) return '{cfg.get("webglRenderer", "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)")}';
                    return orig.apply(this, arguments);
                }}, 'getParameter');
            }};
            if (window.WebGLRenderingContext) patchGL(WebGLRenderingContext.prototype);
            if (window.WebGL2RenderingContext) patchGL(WebGL2RenderingContext.prototype);

            // 5. CANVAS FINGERPRINT SEEDING
            try {{
                const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
                CanvasRenderingContext2D.prototype.getImageData = makeNative(function(sx, sy, sw, sh) {{
                    const imgData = origGetImageData.apply(this, arguments);
                    if (!imgData || !imgData.data || imgData.data.length === 0) return imgData;
                    const seed = {cfg.get("canvasSeed", 48291)};
                    const data = imgData.data;
                    const step = Math.max(4, Math.floor(data.length / 32));
                    for (let i = 0; i < data.length; i += step) {{
                        const offset = ((seed + i) % 3) - 1;
                        data[i] = Math.min(255, Math.max(0, data[i] + offset));
                    }}
                    return imgData;
                }}, 'getImageData');

                const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
                HTMLCanvasElement.prototype.toDataURL = makeNative(function() {{
                    try {{
                        const ctx = this.getContext('2d');
                        if (ctx && this.width > 0 && this.height > 0) {{
                            const w = Math.min(this.width, 16);
                            const h = Math.min(this.height, 16);
                            const sample = ctx.getImageData(0, 0, w, h);
                            ctx.putImageData(sample, 0, 0);
                        }}
                    }} catch (_) {{}}
                    return origToDataURL.apply(this, arguments);
                }}, 'toDataURL');
            }} catch(e) {{}}

            // 6. AUDIOCONTEXT FREQUENCY SPOOFING
            try {{
                if (window.AudioBuffer) {{
                    const origGetChannelData = AudioBuffer.prototype.getChannelData;
                    AudioBuffer.prototype.getChannelData = makeNative(function(channel) {{
                        const f32 = origGetChannelData.apply(this, arguments);
                        if (!f32 || f32.length === 0) return f32;
                        const seed = {cfg.get("audioSeed", 82914)};
                        const factor = 1e-7;
                        const step = Math.max(10, Math.floor(f32.length / 100));
                        for (let i = 0; i < f32.length; i += step) {{
                            f32[i] += Math.sin(i * seed) * factor;
                        }}
                        return f32;
                    }}, 'getChannelData');
                }}
            }} catch(e) {{}}

            // 7. WEBRTC LOCAL IP LEAK PROTECTION
            if (window.RTCPeerConnection) {{
                try {{
                    const origSetLocalDescription = RTCPeerConnection.prototype.setLocalDescription;
                    RTCPeerConnection.prototype.setLocalDescription = makeNative(function(desc) {{
                        if (desc && desc.sdp) {{
                            desc.sdp = desc.sdp.replace(/a=candidate:.*typ host.*\\r\\n/g, '');
                        }}
                        return origSetLocalDescription.apply(this, arguments);
                    }}, 'setLocalDescription');
                }} catch(e) {{}}
            }}

            console.info('%c[Flowork Stealth Active] Persona: {cfg.get("profileName")} ({uad_platform})', 'color: #00ff66; font-weight: bold;');
        }})();
        """

        # Register stealth script on new document
        await ws.send(json.dumps({
            "id": 3,
            "method": "Page.addScriptToEvaluateOnNewDocument",
            "params": {"source": stealth_code}
        }))
        await asyncio.sleep(0.2)

        # Navigate to target URL
        await ws.send(json.dumps({
            "id": 4,
            "method": "Page.navigate",
            "params": {"url": target_url}
        }))
        await asyncio.sleep(0.5)

    return True

def main():
    if len(sys.argv) < 4:
        print("Usage: stealth_supervisor.py <port> <config_json_path> <target_url>")
        sys.exit(1)

    port = int(sys.argv[1])
    cfg_path = Path(sys.argv[2])
    target_url = sys.argv[3]

    with open(cfg_path, "r") as f:
        config_dict = json.load(f)

    asyncio.run(inject_stealth(port, config_dict, target_url))

if __name__ == "__main__":
    main()
