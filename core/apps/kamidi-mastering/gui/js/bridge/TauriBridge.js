/**
 * TauriBridge.js - Zero Trust Adapter
 * ====================================
 * Satu-satunya file yang boleh memanggil window.__TAURI__.
 * Semua komunikasi Frontend <-> Backend melewati file ini.
 * Termasuk validasi data di sisi JS sebelum dikirim ke Rust.
 */

export class TauriBridge {
    constructor() {
        this._isTauri = typeof window !== 'undefined' && window.__TAURI__ !== undefined;
        this._browserFiles = []; // For browser fallback: store File objects
    }

    /** Check if running inside Tauri */
    isTauri() { return this._isTauri; }

    /** Get App Version */
    async getAppVersion() {
        if (this._isTauri) {
            try {
                // Requires '@tauri-apps/api/app' to be exposed or 'app:all' in capabilities
                const { getVersion } = window.__TAURI__.app;
                return await getVersion();
            } catch (err) {
                console.warn('[TauriBridge] Gagal mendapatkan versi Tauri:', err);
                return "0.5.0";
            }
        } else {
            // Fallback for browser testing
            try {
                const res = await fetch('../../package.json');
                const pkg = await res.json();
                return pkg.version;
            } catch (err) {
                return "0.5.0";
            }
        }
    }

    /**
     * Open native file picker dialog for audio files (MULTI-SELECT).
     * Menggunakan HTML5 Input File agar kita mendapatkan objek File secara instan
     * (menghilangkan delay IPC Tauri dan masalah CORS).
     * @returns {Promise<Array<{path: string, name: string, _browserIndex: number}>|null>}
     */
    async openAudioFiles() {
        if (this._isTauri) {
            return await this._tauriOpenFiles();
        }
        return await this._browserOpenFiles();
    }

    /**
     * Read audio bytes for a specific file.
     * Menggunakan browser cache (File.arrayBuffer) yang jauh lebih cepat daripada IPC.
     * @param {{path: string, name: string, _browserIndex?: number}} fileInfo
     * @returns {Promise<ArrayBuffer>}
     */
    async readAudioBytes(fileInfo) {
        if (this._isTauri && fileInfo.path && !('_browserIndex' in fileInfo)) {
            const { readFile } = window.__TAURI__.fs;
            const uint8Array = await readFile(fileInfo.path);
            return uint8Array.buffer;
        }
        const file = this._browserFiles[fileInfo._browserIndex];
        if (!file) throw new Error('File tidak ditemukan di browser cache. Harap load ulang file.');
        return await file.arrayBuffer();
    }

    /**
     * Dapatkan URL file untuk keperluan streaming (HTMLMediaElement)
     * Menggunakan Blob URL dari File API yang 100% instan dan bebas CORS.
     * @param {{path: string, name: string, _browserIndex?: number}} fileInfo
     * @returns {Promise<string>}
     */
    async getAudioUrl(fileInfo) {
        if (this._isTauri && fileInfo.path && !('_browserIndex' in fileInfo)) {
            try {
                // Baca file ke RAM menggunakan fs plugin karena fs scope sudah "**" (bebas akses ke semua drive).
                // Ini memotong batasan ketat dari assetProtocol scope di Tauri v2.
                const { readFile } = window.__TAURI__.fs;
                const uint8Array = await readFile(fileInfo.path);
                
                // Deteksi mime type dasar
                const ext = fileInfo.path.split('.').pop().toLowerCase();
                let mimeType = 'audio/wav';
                if (ext === 'mp3') mimeType = 'audio/mpeg';
                else if (ext === 'flac') mimeType = 'audio/flac';
                else if (ext === 'ogg') mimeType = 'audio/ogg';
                else if (ext === 'm4a' || ext === 'aac') mimeType = 'audio/mp4';
                
                const blob = new Blob([uint8Array], { type: mimeType });
                return URL.createObjectURL(blob);
            } catch (err) {
                console.warn('[TauriBridge] Gagal read file ke blob, fallback ke convertFileSrc:', err);
                const { convertFileSrc } = window.__TAURI__.core;
                return convertFileSrc(fileInfo.path);
            }
        }
        const file = this._browserFiles[fileInfo._browserIndex];
        if (!file) throw new Error('File tidak ditemukan di browser cache. Harap load ulang file.');
        return URL.createObjectURL(file);
    }

    /**
     * Save WAV data to disk using native Save As dialog.
     * Falls back to browser download in browser mode.
     * @param {Uint8Array} wavData - WAV file bytes
     * @param {string} suggestedName - Suggested filename
     * @returns {Promise<string|null>} - Saved file path or null
     */
    async saveAudioFile(wavData, suggestedName) {
        // Zero Trust: Validate WAV data before sending to Rust
        if (!this._validateWavData(wavData)) {
            throw new Error('Data WAV tidak valid. Export dibatalkan.');
        }

        if (this._isTauri) {
            return await this._tauriSaveFile(wavData, suggestedName, 'Export Mastered Audio', [{ name: 'WAV Audio', extensions: ['wav'] }]);
        } else {
            return this._browserSaveFile(wavData, suggestedName, 'audio/wav');
        }
    }

    async saveZipFile(zipData, suggestedName) {
        if (this._isTauri) {
            return await this._tauriSaveFile(zipData, suggestedName, 'Export Batch Mastered Audio', [{ name: 'ZIP Archive', extensions: ['zip'] }]);
        } else {
            return this._browserSaveFile(zipData, suggestedName, 'application/zip');
        }
    }

    async saveTextFile(textData, suggestedName) {
        if (this._isTauri) {
            return await this._tauriSaveTextFile(textData, suggestedName, 'Save Summary Report', [{ name: 'Text File', extensions: ['txt'] }]);
        } else {
            return this._browserSaveFile(textData, suggestedName, 'text/plain');
        }
    }

    /**
     * Tampilkan dialog save untuk mendapatkan path.
     */
    async promptSavePath(suggestedName, isZip = false) {
        if (!this._isTauri) return suggestedName; // Fallback untuk browser
        try {
            const { save } = window.__TAURI__.dialog;
            return await save({
                title: isZip ? 'Export Batch Mastered Audio' : 'Export Mastered Audio',
                defaultPath: suggestedName,
                filters: isZip ? [{ name: 'ZIP Archive', extensions: ['zip'] }] : [{ name: 'WAV Audio', extensions: ['wav'] }]
            });
        } catch (err) {
            console.error('[TauriBridge] Save dialog error:', err);
            return null;
        }
    }

    /**
     * Tulis data langsung ke path yang sudah dipilih.
     */
    async writeFileData(savePath, data, mimeType = 'application/octet-stream') {
        if (this._isTauri) {
            try {
                const { writeFile } = window.__TAURI__.fs;
                await writeFile(savePath, data);
                return savePath;
            } catch (err) {
                throw new Error('Gagal menulis file: ' + (err.message || err));
            }
        } else {
            return this._browserSaveFile(data, savePath, mimeType);
        }
    }

    // ============================================================
    // TAURI IMPLEMENTATIONS
    // ============================================================

    async _tauriOpenFiles() {
        try {
            const { open } = window.__TAURI__.dialog;
            const selected = await open({
                title: 'Load Audio Tracks',
                filters: [{
                    name: 'Audio Files',
                    extensions: ['wav', 'mp3', 'flac', 'ogg', 'aac', 'm4a', 'aiff', 'aif', 'wma']
                }],
                multiple: true
            });

            if (!selected) return null;

            // Normalize: single string or array
            const paths = Array.isArray(selected) ? selected : [selected];
            if (paths.length === 0) return null;

            return paths.map(p => {
                const filePath = typeof p === 'string' ? p : p.path;
                return {
                    path: filePath,
                    name: filePath.split(/[\\/]/).pop()
                };
            });
        } catch (err) {
            console.error('[TauriBridge] Multi-load error:', err);
            throw new Error('Gagal memuat file: ' + (err.message || err));
        }
    }

    async _tauriSaveFile(data, suggestedName, title, filters) {
        try {
            const { save } = window.__TAURI__.dialog;
            const savePath = await save({
                title: title,
                defaultPath: suggestedName,
                filters: filters
            });

            if (!savePath) return null;

            const { writeFile } = window.__TAURI__.fs;
            await writeFile(savePath, data);

            console.log(`[TauriBridge] File saved: ${savePath} (${(data.length / 1024 / 1024).toFixed(1)}MB)`);
            return savePath;
        } catch (err) {
            console.error('[TauriBridge] Save error:', err);
            throw new Error('Gagal menyimpan file: ' + (err.message || err));
        }
    }

    async _tauriSaveTextFile(data, suggestedName, title, filters) {
        try {
            const { save } = window.__TAURI__.dialog;
            const savePath = await save({
                title: title,
                defaultPath: suggestedName,
                filters: filters
            });

            if (!savePath) return null;

            const { writeTextFile } = window.__TAURI__.fs;
            await writeTextFile(savePath, data);

            console.log(`[TauriBridge] Text file saved: ${savePath}`);
            return savePath;
        } catch (err) {
            console.error('[TauriBridge] Save text error:', err);
            throw new Error('Gagal menyimpan file teks: ' + (err.message || err));
        }
    }

    // ============================================================
    // BROWSER FALLBACK IMPLEMENTATIONS
    // ============================================================

    _browserOpenFiles() {
        return new Promise((resolve) => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'audio/*';
            input.multiple = true;
            input.onchange = (e) => {
                const files = Array.from(e.target.files);
                if (files.length === 0) { resolve(null); return; }
                this._browserFiles = files;
                resolve(files.map((f, i) => ({
                    path: f.name,
                    name: f.name,
                    _browserIndex: i
                })));
            };
            input.click();
        });
    }

    _browserSaveFile(data, suggestedName, mimeType) {
        const blob = new Blob([data], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = suggestedName;
        a.click();
        setTimeout(() => URL.revokeObjectURL(url), 5000);
        return suggestedName;
    }

    // ============================================================
    // ZERO TRUST VALIDATION (JS Side)
    // ============================================================

    _validateWavData(data) {
        if (!data || data.length < 44) return false;
        // Check RIFF header
        if (data[0] !== 0x52 || data[1] !== 0x49 || data[2] !== 0x46 || data[3] !== 0x46) return false;
        // Check WAVE marker
        if (data[8] !== 0x57 || data[9] !== 0x41 || data[10] !== 0x56 || data[11] !== 0x45) return false;
        return true;
    }

    // ============================================================
    // PRESET MANAGEMENT (Physical Storage - Individual Files)
    // ============================================================

    async selectFolder(title = 'Pilih Folder Tujuan', defaultPath) {
        if (!this._isTauri) return null;
        try {
            const { open } = window.__TAURI__.dialog;
            const selected = await open({
                title: title,
                defaultPath: defaultPath || undefined,
                directory: true,
                multiple: false
            });
            return selected;
        } catch (err) {
            console.error('[TauriBridge] Select folder error:', err);
            return null;
        }
    }

    /**
     * Pastikan subfolder "File Mastering" ada di dalam parentFolder.
     * Jika sudah ada, buat "File Mastering (1)", dst.
     * @returns {Promise<string>} Path ke subfolder
     */
    async ensureMasteringFolder(parentFolder) {
        if (!this._isTauri) return parentFolder;
        try {
            const { exists, mkdir } = window.__TAURI__.fs;
            const baseFolder = parentFolder.replace(/[\\/]+$/, '');
            let masteringFolder = baseFolder + '/File Mastering';
            let counter = 1;
            
            while (await exists(masteringFolder)) {
                masteringFolder = baseFolder + '/File Mastering (' + counter + ')';
                counter++;
            }
            
            await mkdir(masteringFolder, { recursive: true });
            return masteringFolder;
        } catch (err) {
            console.error('[TauriBridge] ensureMasteringFolder error:', err);
            return parentFolder;
        }
    }

    async selectPresetFolder(currentFolder) {
        return this.selectFolder('Pilih Folder Penyimpanan Preset Mastering', currentFolder);
    }

    async openPresetFile() {
        if (this._isTauri) {
            try {
                const { open } = window.__TAURI__.dialog;
                const { readTextFile } = window.__TAURI__.fs;
                const selected = await open({
                    title: 'Pilih File Preset',
                    filters: [{ name: 'JSON Preset', extensions: ['json'] }],
                    multiple: false
                });

                if (!selected) return null;
                const filePath = typeof selected === 'string' ? selected : selected.path;
                const name = filePath.split(/[\\/]/).pop();
                const content = await readTextFile(filePath);
                
                return { name, content, path: filePath };
            } catch (err) {
                console.error('[TauriBridge] Open preset error:', err);
                return null;
            }
        } else {
            return new Promise((resolve) => {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = '.json';
                input.multiple = false;
                input.onchange = async (e) => {
                    const file = e.target.files[0];
                    if (!file) { resolve(null); return; }
                    const text = await file.text();
                    resolve({ name: file.name, content: text, path: file.name });
                };
                input.click();
            });
        }
    }

    async getPresetFiles(folderPath) {
        if (!this._isTauri) return [];
        try {
            const { invoke } = window.__TAURI__.core;
            const targetFolder = folderPath.replace(/[\\/]+$/, '');
            
            // Bypass Tauri Scope
            const files = await invoke('bypass_read_dir_presets', { folder: targetFolder });
            
            return files.map(name => ({
                name: name.replace(/\.json$/i, ''),
                path: targetFolder + '\\' + name
            }));
        } catch (err) {
            console.error('[TauriBridge] getPresetFiles error:', err);
            return [];
        }
    }

    async loadPresetFile(filePath) {
        if (!this._isTauri) return null;
        try {
            const { invoke } = window.__TAURI__.core;
            const content = await invoke('bypass_read_preset', { path: filePath });
            return JSON.parse(content);
        } catch (err) {
            console.error('[TauriBridge] loadPresetFile error:', err);
            return null;
        }
    }

    async savePresetFile(presetObj, presetName, folderPath) {
        if (!this._isTauri) return;
        try {
            const { invoke } = window.__TAURI__.core;
            const targetFolder = folderPath.replace(/[\\/]+$/, '');
            const fileName = presetName.replace(/[\\/:*?"<>|]/g, '_') + '.json';
            const filePath = targetFolder + '\\' + fileName;
            
            await invoke('bypass_write_preset', { 
                path: filePath, 
                content: JSON.stringify(presetObj, null, 2) 
            });
            return filePath;
        } catch (err) {
            console.error('[TauriBridge] savePresetFile error:', err);
            throw err;
        }
    }

    async deletePresetFile(filePath) {
        if (!this._isTauri) return;
        try {
            const { invoke } = window.__TAURI__.core;
            await invoke('bypass_delete_preset', { path: filePath });
        } catch (err) {
            console.error('[TauriBridge] deletePresetFile error:', err);
            throw err;
        }
    }

    async writeFileData(filePath, data, mimeType) {
        if (!this._isTauri) return false;
        try {
            let uint8Array;
            if (data instanceof Uint8Array) {
                uint8Array = data;
            } else if (data instanceof ArrayBuffer) {
                uint8Array = new Uint8Array(data);
            } else if (data && typeof data.arrayBuffer === 'function') {
                const arrayBuffer = await data.arrayBuffer();
                uint8Array = new Uint8Array(arrayBuffer);
            } else {
                throw new TypeError("Tipe data tidak didukung untuk writeFileData");
            }
            
            await window.__TAURI__.fs.writeFile(filePath, uint8Array);
            return true;
        } catch (error) {
            console.error('[TauriBridge] Gagal menyimpan data file:', error);
            throw error;
        }
    }

    async deleteFile(filePath) {
        if (!this._isTauri) return;
        try {
            await window.__TAURI__.core.invoke('bypass_delete_preset', { path: filePath });
            console.log('[TauriBridge] File temp dihapus:', filePath);
        } catch (err) {
            console.warn('[TauriBridge] Gagal menghapus file temp:', err);
        }
    }

    // ============================================================
    // FFMPEG SIDECAR (LUFS Normalization)
    // ============================================================

    /**
     * Jalankan FFmpeg Dual-Pass LUFS Normalization
     * Pass 1: Ukur audio
     * Pass 2: Terapkan gain linear & TP Limiter, output ke 24-bit WAV
     */
    async runFfmpegLoudnorm(tempPath, outputPath, onProgress) {
        if (!this._isTauri) throw new Error("FFmpeg sidecar hanya tersedia di versi desktop.");
        const { Command } = window.__TAURI__.shell;

        if (onProgress) onProgress(0, 'Menganalisis dinamika audio...');

        // --- PASS 1: Measurement ---
        const args1 = [
            '-y',
            '-i', tempPath,
            '-af', 'loudnorm=print_format=json',
            '-f', 'null',
            '-'
        ];
        
        const cmd1 = Command.sidecar('bin/ffmpeg', args1);
        const child1 = await cmd1.execute();
        const pass1Stderr = child1.stderr || '';

        if (child1.code !== 0) {
            console.error('FFmpeg Pass 1 Error Output:\n', pass1Stderr);
            throw new Error('Gagal menganalisis audio (Kode: ' + child1.code + ')\nDetails: ' + pass1Stderr);
        }

        // Cari JSON di stderr
        const jsonStart = pass1Stderr.lastIndexOf('{');
        const jsonEnd = pass1Stderr.lastIndexOf('}') + 1;
        if (jsonStart === -1 || jsonEnd === 0) {
            throw new Error('Gagal memproses metrik analisis audio.\nOutput:\n' + pass1Stderr);
        }
        
        const metrics = JSON.parse(pass1Stderr.substring(jsonStart, jsonEnd));
        console.log('[FFmpeg Pass 1] Metrics:', metrics);

        if (onProgress) onProgress(50, 'Menerapkan True Peak Limiter...');

        // --- PASS 2: Application ---
        // Validate and clamp metrics to prevent FFmpeg crashes with out-of-range values
        // Note: 32-bit float audio can have LUFS > 0. FFmpeg loudnorm limits measured_I to [-99, 0].
        const clamp = (val, min, max) => Math.max(min, Math.min(max, parseFloat(val) || min));
        const safe_I = clamp(metrics.input_i, -99.0, 0.0);
        const safe_TP = clamp(metrics.input_tp, -99.0, 99.0);
        const safe_LRA = clamp(metrics.input_lra, 0.0, 99.0);
        const safe_thresh = clamp(metrics.input_thresh, -99.0, 0.0);
        const safe_offset = parseFloat(metrics.target_offset || 0);

        const afArgs = `loudnorm=I=-14:TP=-1.0:LRA=11:measured_I=${safe_I}:measured_TP=${safe_TP}:measured_LRA=${safe_LRA}:measured_thresh=${safe_thresh}:offset=${safe_offset}:linear=true`;
        
        const args2 = [
            '-y',
            '-i', tempPath,
            '-af', afArgs,
            '-c:a', 'pcm_s24le', // 24-bit output (Studio Master Standard)
            outputPath
        ];
        
        const cmd2 = Command.sidecar('bin/ffmpeg', args2);
        
        const child2 = await cmd2.execute();
        if (child2.code !== 0) {
            console.error('FFmpeg Pass 2 Error Output:\n', child2.stderr);
            throw new Error('Gagal menerapkan limiter akhir (Kode: ' + child2.code + ')\nDetails: ' + child2.stderr);
        }

        if (onProgress) onProgress(100, 'Pemrosesan akhir selesai.');
        
        // Return metrics untuk summary report
        return {
            input_i: parseFloat(metrics.input_i),
            input_tp: parseFloat(metrics.input_tp),
            input_lra: parseFloat(metrics.input_lra),
            output_i: parseFloat(metrics.output_i),
            output_tp: parseFloat(metrics.output_tp),
            output_lra: parseFloat(metrics.output_lra)
        };
    }
}
