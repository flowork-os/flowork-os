# 🛡 FLOWORK STEALTH BROWSER & ANTI-DETECT DOCTRINE

> **SOVEREIGN MANDATE:** Flowork OS features a native, 100% free C++ Anti-Detect Browser (`flowork-stealth`) powered by the Camoufox engine, completely replacing commercial subscription alternatives like ixBrowser, AdsPower, and Multilogin.

### 1. ARCHITECTURE & LOCAL ROOT
- System Core: `/opt/floworkos/apps/flowork-stealth/`
- Engine Virtualenv: `/opt/floworkos/apps/camoufox/venv/`
- User Profiles: `/opt/floworkos/apps/flowork-stealth/profiles/<slug>/user_data`
- Launcher CLI: `/usr/local/bin/flowork-stealth` (`list`, `create`, `launch`, `delete`, `gui`)
- Glass HUD GUI: `/opt/floworkos/apps/flowork-stealth/gui/flowork-stealth-gui.py` (PyQt6)
- Detached Session Runner: `/opt/floworkos/apps/flowork-stealth/bin/stealth_runner.py`

### 2. C++ ENGINE-LEVEL HARDWARE MASKING
- **Native C++ Engine Spoofing:** Operates at the Gecko/Playwright binary layer, altering `navigator.platform` (Win32), `oscpu` (Windows NT 10.0), WebGL shaders, screen metrics, and fonts without fragile JS shims.
- **Carrier-Grade NAT & GeoIP Alignment:** Built-in MaxMind GeoIP dynamically aligns browser timezone (`TZ=Asia/Jakarta`), locale (`id-ID`), and WebRTC candidates with the exit IP.
- **Embedded Sovereign AdBlock:** Bundles native uBlock Origin (`UBO`), instantly wiping YouTube video ads and tracking beacons without external extensions.
- **Audited Fingerprint Score:** Achieves 100/100 Trust Score ("Trustworthy") on Iphey and full consistency on BrowserLeaks.

### 3. OPERATIONAL RULES
- Never run commercial Windows anti-detect tools via Wine. Always deploy sovereign `flowork-stealth`.
- When testing fingerprint consistency, verify against Iphey, BrowserLeaks, and Pixelscan.
