// ==============================================================================
// 👑 FLOWORK OS — TAURI V2 COMPATIBILITY BRIDGE POLYFILL
// For Native Rust + WebKit2GTK Kamidi Mastering Pro Console
// ==============================================================================

(function() {
    console.log('[Kamidi Polyfill] Initializing Sovereign Tauri v2 Bridge...');

    async function apiRequest(endpoint, payload) {
        try {
            const res = await fetch('/api/' + endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (!res.ok) {
                const errText = await res.text();
                throw new Error(errText || 'Server error ' + res.status);
            }
            return await res.json();
        } catch (e) {
            console.error('[Kamidi API Error]', endpoint, e);
            throw e;
        }
    }

    const tauriCore = {
        invoke: async function(cmd, args) {
            return await apiRequest('invoke', { cmd: cmd, args: args || {} });
        },
        convertFileSrc: function(filePath) {
            return '/fs-stream?path=' + encodeURIComponent(filePath);
        }
    };

    const tauriDialog = {
        open: async function(options) {
            return await apiRequest('dialog/open', options || {});
        },
        save: async function(options) {
            return await apiRequest('dialog/save', options || {});
        }
    };

    const tauriFs = {
        readFile: async function(filePath) {
            const res = await fetch('/api/fs/read-binary?path=' + encodeURIComponent(filePath));
            if (!res.ok) throw new Error('Gagal membaca file: ' + filePath);
            const buf = await res.arrayBuffer();
            return new Uint8Array(buf);
        },
        readTextFile: async function(filePath) {
            const res = await fetch('/api/fs/read-text?path=' + encodeURIComponent(filePath));
            if (!res.ok) throw new Error('Gagal membaca text: ' + filePath);
            return await res.text();
        },
        writeFile: async function(filePath, data) {
            let body;
            if (data instanceof Uint8Array || data instanceof ArrayBuffer) {
                body = data;
            } else if (Array.isArray(data)) {
                body = new Uint8Array(data);
            } else {
                body = new TextEncoder().encode(String(data));
            }
            const res = await fetch('/api/fs/write-binary?path=' + encodeURIComponent(filePath), {
                method: 'POST',
                headers: { 'Content-Type': 'application/octet-stream' },
                body: body
            });
            if (!res.ok) throw new Error('Gagal menulis file: ' + filePath);
            return true;
        },
        writeTextFile: async function(filePath, text) {
            const res = await fetch('/api/fs/write-text?path=' + encodeURIComponent(filePath), {
                method: 'POST',
                headers: { 'Content-Type': 'text/plain; charset=utf-8' },
                body: text
            });
            if (!res.ok) throw new Error('Gagal menulis text: ' + filePath);
            return true;
        },
        exists: async function(filePath) {
            const res = await apiRequest('fs/exists', { path: filePath });
            return !!res.exists;
        },
        mkdir: async function(dirPath, options) {
            return await apiRequest('fs/mkdir', { path: dirPath, recursive: !!(options && options.recursive) });
        }
    };

    const tauriApp = {
        getVersion: async function() {
            return "5.0.10";
        }
    };

    const tauriPath = {
        appDataDir: async function() {
            const res = await apiRequest('path/app-data', {});
            return res.path;
        }
    };

    const tauriShell = {
        Command: {
            sidecar: function(program, args) {
                return {
                    execute: async function() {
                        return await apiRequest('shell/exec', { program: program, args: args });
                    }
                };
            }
        }
    };

    window.__TAURI__ = {
        core: tauriCore,
        dialog: tauriDialog,
        fs: tauriFs,
        app: tauriApp,
        path: tauriPath,
        shell: tauriShell
    };

    window.__TAURI_INTERNALS__ = {
        invoke: tauriCore.invoke,
        convertFileSrc: tauriCore.convertFileSrc
    };

    // Auto-resolve donation modal so it never blocks workflows
    window.showKamidiDonationPopup = function(context) {
        console.log('[Kamidi Polyfill] Bypassed donation popup for context:', context);
        return Promise.resolve();
    };

    console.log('[Kamidi Polyfill] window.__TAURI__ successfully mounted.');
})();
