# ⚡ WEBKIT & AUDIO DSP UI PERFORMANCE OPTIMIZATION (FLOWORK SOVEREIGN DOCTRINE)

## 1. WebKit2GTK Software Compositor Prevention (Zero-Lag Mandate)
- **Problem:** When WebKit2GTK runs with `HardwareAccelerationPolicy.ALWAYS` on Linux X11 systems without hardware DRI3 devices, Mesa forces `llvmpipe` (CPU OpenGL emulation). This consumes 150% CPU on `WebKitWebProcess` and locks `Xorg` at 100% CPU.
- **Rule:** For all hybrid WebKit GTK desktop apps, strictly enforce:
  1. `os.environ["WEBKIT_DISABLE_COMPOSITING_MODE"] = "1"`
  2. `os.environ["LIBGL_ALWAYS_SOFTWARE"] = "1"`
  3. `settings.set_hardware_acceleration_policy(WebKit2.HardwareAccelerationPolicy.NEVER)`
  4. `settings.set_enable_write_console_messages_to_stdout(False)`

## 2. 30 FPS Visualizer Throttling & Audio Isolation
- **Problem:** Unthrottled `requestAnimationFrame` loops (60-144 FPS) redrawing multiple `<canvas>` visualizers (FFT spectrum, waveforms) saturate software rasterizers and starve user input.
- **Rule:** Always wrap `requestAnimationFrame` with a 30 FPS frame-rate limiter (`minInterval = 33.3ms`).
- **Rule:** AudioWorklet DSP runs independently on the high-priority Web Audio thread. Never allow UI visualizer loops to choke the main thread.

## 3. Preset Switch Transition Smoothing
- **Problem:** Synchronously setting 50+ faders and updating AudioWorklet ports causes frame drops if canvas loops compete at the same millisecond.
- **Rule:** When preset change triggers, temporarily defer canvas redraws for ~100ms. Faders and DSP synchronize instantly with zero UI stutter.
