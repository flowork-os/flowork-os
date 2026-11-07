/**
 * Flowork Sovereign Stealth Engine - Main World Hardware Masker
 * Embedded Configuration & Synthetic Hardware DNA Interceptor
 */

(function () {
  'use strict';

  // Prevent multiple injections
  if (window.__FLOWORK_STEALTH_LOADED__) return;
  window.__FLOWORK_STEALTH_LOADED__ = true;

  const cfg = {
  "profileId": "crypto-whale",
  "profileName": "Crypto Whale",
  "preset": "win11-rtx4070",
  "os": "windows",
  "platform": "Win32",
  "userAgent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
  "appVersion": "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
  "hardwareConcurrency": 16,
  "deviceMemory": 16,
  "webglVendor": "Google Inc. (NVIDIA)",
  "webglRenderer": "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
  "screenWidth": 1920,
  "screenHeight": 1080,
  "screenColorDepth": 24,
  "screenPixelDepth": 24,
  "canvasSeed": 922394,
  "audioSeed": 354251,
  "disableWebRTCLeak": true,
  "proxy": "",
  "notes": "Finance & Airdrop Farming Profile"
};
  const cfg = window.__FLOWORK_STEALTH_CONFIG__ || {
    profileId: "default",
    profileName: "Sovereign Stealth",
    platform: "Win32",
    userAgent: "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    appVersion: "5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    hardwareConcurrency: 16,
    deviceMemory: 16,
    webglVendor: "Google Inc. (NVIDIA)",
    webglRenderer: "ANGLE (NVIDIA, NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0, D3D11)",
    canvasSeed: 48291,
    audioSeed: 82914,
    screenWidth: 1920,
    screenHeight: 1080,
    screenColorDepth: 24,
    screenPixelDepth: 24,
    disableWebRTCLeak: true
  };

  // Helper to make hooked functions look authentic and native
  const makeNative = (fn, name) => {
    try {
      Object.defineProperty(fn, 'name', { value: name || '', configurable: true });
    } catch (_) {}
    const nativeStr = `function ${name || ''}() { [native code] }`;
    const customToString = function toString() {
      if (this === customToString) return 'function toString() { [native code] }';
      return nativeStr;
    };
    try {
      Object.defineProperty(fn, 'toString', {
        value: customToString,
        configurable: true,
        writable: true
      });
    } catch (_) {}
    return fn;
  };

  // 1. NAVIGATOR MASKING (Prototype level to pass hasOwnProperty checks)
  try {
    const navProto = Navigator.prototype;

    // Eradicate automation / webdriver flags
    Object.defineProperty(navProto, 'webdriver', {
      get: makeNative(() => undefined, 'get webdriver'),
      configurable: true,
      enumerable: true
    });

    if ('userAgent' in navProto) {
      Object.defineProperty(navProto, 'userAgent', {
        get: makeNative(() => cfg.userAgent, 'get userAgent'),
        configurable: true,
        enumerable: true
      });
    }

    if ('appVersion' in navProto) {
      Object.defineProperty(navProto, 'appVersion', {
        get: makeNative(() => cfg.appVersion, 'get appVersion'),
        configurable: true,
        enumerable: true
      });
    }

    if ('platform' in navProto) {
      Object.defineProperty(navProto, 'platform', {
        get: makeNative(() => cfg.platform, 'get platform'),
        configurable: true,
        enumerable: true
      });
    }

    if ('hardwareConcurrency' in navProto) {
      Object.defineProperty(navProto, 'hardwareConcurrency', {
        get: makeNative(() => cfg.hardwareConcurrency, 'get hardwareConcurrency'),
        configurable: true,
        enumerable: true
      });
    }

    if ('deviceMemory' in navProto) {
      Object.defineProperty(navProto, 'deviceMemory', {
        get: makeNative(() => cfg.deviceMemory, 'get deviceMemory'),
        configurable: true,
        enumerable: true
      });
    }
  } catch (err) {}

  // 2. SCREEN RESOLUTION & COLOR DEPTH MASKING
  try {
    const screenProto = Screen.prototype;
    const screenProps = {
      width: cfg.screenWidth,
      height: cfg.screenHeight,
      availWidth: cfg.screenWidth,
      availHeight: cfg.screenHeight - 40,
      colorDepth: cfg.screenColorDepth || 24,
      pixelDepth: cfg.screenPixelDepth || 24
    };

    for (const [prop, val] of Object.entries(screenProps)) {
      try {
        Object.defineProperty(screenProto, prop, {
          get: makeNative(() => val, `get ${prop}`),
          configurable: true,
          enumerable: true
        });
      } catch (_) {}
    }
  } catch (err) {}

  // 3. WEBGL GPU & RENDERER MASKING
  const patchWebGL = (contextProto) => {
    if (!contextProto) return;
    try {
      const origGetParameter = contextProto.getParameter;
      contextProto.getParameter = makeNative(function (pname) {
        // UNMASKED_VENDOR_WEBGL (37445) or VENDOR (7936)
        if (pname === 37445 || pname === 7936) {
          return cfg.webglVendor;
        }
        // UNMASKED_RENDERER_WEBGL (37446) or RENDERER (7937)
        if (pname === 37446 || pname === 7937) {
          return cfg.webglRenderer;
        }
        return origGetParameter.apply(this, arguments);
      }, 'getParameter');
    } catch (e) {}
  };

  if (window.WebGLRenderingContext) patchWebGL(WebGLRenderingContext.prototype);
  if (window.WebGL2RenderingContext) patchWebGL(WebGL2RenderingContext.prototype);

  // 4. CANVAS FINGERPRINT SEEDING (Deterministic Subtle Pixel Perturbation)
  try {
    const origGetImageData = CanvasRenderingContext2D.prototype.getImageData;
    CanvasRenderingContext2D.prototype.getImageData = makeNative(function (sx, sy, sw, sh) {
      const imgData = origGetImageData.apply(this, arguments);
      if (!imgData || !imgData.data || imgData.data.length === 0) return imgData;

      const seed = cfg.canvasSeed || 48291;
      const data = imgData.data;
      const step = Math.max(4, Math.floor(data.length / 32));
      for (let i = 0; i < data.length; i += step) {
        const offset = ((seed + i) % 3) - 1; // -1, 0, or 1
        data[i] = Math.min(255, Math.max(0, data[i] + offset));
      }
      return imgData;
    }, 'getImageData');

    const origToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = makeNative(function () {
      try {
        const ctx = this.getContext('2d');
        if (ctx && this.width > 0 && this.height > 0) {
          const w = Math.min(this.width, 16);
          const h = Math.min(this.height, 16);
          const sample = ctx.getImageData(0, 0, w, h);
          ctx.putImageData(sample, 0, 0);
        }
      } catch (_) {}
      return origToDataURL.apply(this, arguments);
    }, 'toDataURL');
  } catch (err) {}

  // 5. AUDIOCONTEXT FREQUENCY & BUFFER SPOOFING
  try {
    if (window.AudioBuffer) {
      const origGetChannelData = AudioBuffer.prototype.getChannelData;
      AudioBuffer.prototype.getChannelData = makeNative(function (channel) {
        const f32 = origGetChannelData.apply(this, arguments);
        if (!f32 || f32.length === 0) return f32;
        const seed = cfg.audioSeed || 82914;
        const factor = 1e-7;
        const step = Math.max(10, Math.floor(f32.length / 100));
        for (let i = 0; i < f32.length; i += step) {
          f32[i] += Math.sin(i * seed) * factor;
        }
        return f32;
      }, 'getChannelData');
    }
  } catch (err) {}

  // 6. WEBRTC LOCAL IP LEAK PROTECTION
  if (cfg.disableWebRTCLeak && window.RTCPeerConnection) {
    try {
      const origSetLocalDescription = RTCPeerConnection.prototype.setLocalDescription;
      RTCPeerConnection.prototype.setLocalDescription = makeNative(function (desc) {
        if (desc && desc.sdp) {
          // Strip candidate lines containing local IPs (typ host)
          desc.sdp = desc.sdp.replace(/a=candidate:.*typ host.*\r\n/g, '');
        }
        return origSetLocalDescription.apply(this, arguments);
      }, 'setLocalDescription');
    } catch (err) {}
  }

  window.__FLOWORK_STEALTH_CONFIG__ = cfg;
  console.info(`%c[Flowork OS] Sovereign Stealth Active • Profile: ${cfg.profileName} (${cfg.platform})`, 'color: #00ff66; font-weight: bold;');
})();
