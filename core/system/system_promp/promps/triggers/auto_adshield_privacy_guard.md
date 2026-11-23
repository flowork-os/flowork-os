# 🛡️ PASSIVE TRIGGER: FLOWORK SOVEREIGN ADSHIELD & VIDEO AD ERADICATION

> **SOVEREIGN DIRECTIVE:** Flowork OS enforces a hardened Dual-Shield ad and tracker eradication architecture across Layer 3/4 network and Layer 7 browser DOM.

### 1. DUAL-SHIELD ARCHITECTURE
- **Layer 3/4 Network DNS Blackhole:** `/etc/hosts` maps 77,700+ tracker and ad domains to `0.0.0.0` (Connection Refused in <8ms). Managed via `flowork-adshield {enable|disable|status|update}` and updated weekly via `flowork-adshield-update.timer`.
- **Layer 7 In-Stream Video Ad Blocker:** First-party video ads (YouTube `*.googlevideo.com`, Facebook sponsored cards) cannot be blocked by DNS without breaking media streams due to TLS 1.3 encryption and shared CDNs. Eradicated via standalone unpacked uBlock Origin in `/opt/floworkos/apps/uBlock0.chromium`.

### 2. CHROME ENTERPRISE POLICY & WRAPPER
- Managed Policy: `/etc/opt/chrome/policies/managed/flowork-adshield.json` forces `ExtensionManifestV2Availability: 2` (permits MV2 extensions), `DnsOverHttpsMode: "off"` (prevents bypassing `/etc/hosts`), and `BuiltInDnsClientEnabled: false`.
- Binary Wrapper: `/opt/google/chrome/google-chrome` automatically injects and merges `--load-extension=/opt/floworkos/apps/uBlock0.chromium` with user-defined extensions.

### 3. OPERATIONAL INVARIANTS
- Never claim DNS blackhole alone stops YouTube pre-roll ads; always verify uBlock Origin is loaded in Chrome runtime.
- Maintain system loopback records (`127.0.0.1 localhost`, `127.0.1.1 mrflow`, and IPv6) during hosts updates.
