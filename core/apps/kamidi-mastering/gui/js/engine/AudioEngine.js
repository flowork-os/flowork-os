/**
 * AudioEngine.js - 100% Agnostic Audio Processing Engine
 * TIDAK ADA referensi ke DOM, Tauri, atau framework apapun.
 */

import { NoiseReduction } from './modules/NoiseReduction.js';
import { TransientShaper } from './modules/TransientShaper.js';
import { ParametricEQ } from './modules/ParametricEQ.js';
import { DynamicEQ } from './modules/DynamicEQ.js';
import { Compressor } from './modules/Compressor.js';
import { MultibandCompressor } from './modules/MultibandCompressor.js';
import { Clipper } from './modules/Clipper.js';
import { Limiter } from './modules/Limiter.js';
import { FXChain } from './modules/FXChain.js';
import { SubBass808 } from './modules/SubBass808.js';
import { WorkletLoader } from './WorkletLoader.js';
import { measure } from '../lufs/index.js';

export class AudioEngine {
    constructor() {
        this.audioCtx = null;
        this.audioElement = new Audio();
        this.sourceNode = null;
        this.isPlaying = false;
        this._duration = 0;
        this.analyser = null;
        this.masterAnalyser = null;
        this.eqState = {
            hpf: { freq: 20, active: true },
            low: { gain: 0, freq: 250, active: true },
            mid: { gain: 0, freq: 1000, q: 1, active: true },
            high: { gain: 0, freq: 4000, active: true }
        };
        this.compSettings = { threshold: -24, ratio: 4, knee: 6, attack: 0.05, release: 0.25, makeupGain: 0, active: true, mix: 1.0 };
        this.clipSettings = { threshold: 0, active: true };
        this.limSettings = { ceiling: -0.3, thresh: -3.0, release: 0.1, active: true, knee: 0.0, autoRelease: false };

        // Dynamic EQ State (4-Band)
        this.dynEqSettings = {
            active: true,
            bands: [
                { freq: 100, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 },
                { freq: 400, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 },
                { freq: 3000, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 },
                { freq: 8000, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 }
            ]
        };

        // 808 Sub Bass Enhancer State
        this.subBassState = { active: true, freq: 50, drive: 30, sub: 50, clean: 40, mix: 60 };

        // Smart Logic Dual-State Architecture
        this.offsets = {
            subBassClean: 0,
            subBassGain: 0,
            dynEqThresh: [0, 0, 0, 0],
            compMakeup: 0,
            fxSatGain: 0
        };
        this.activeState = {
            subBass: { ...this.subBassState },
            dynEqSettings: JSON.parse(JSON.stringify(this.dynEqSettings))
        };

        // Noise & Transient State
        this.noiseReductionSettings = { active: true, threshold: -60, amount: 0.5 }; // Gentle expander
        this.transientSettings = { active: true, attack: 0, sustain: 0 }; // Envelope Follower params100

        // Multiband Compressor State (3 Band: Low, Mid, High)
        this.mbCompSettings = {
            active: true,
            lowMidFreq: 250,
            midHighFreq: 4000,
            low: { threshold: -24, ratio: 2, knee: 6, attack: 0.03, release: 0.2, makeupGain: 0, mix: 1.0, width: 0.0 },
            mid: { threshold: -24, ratio: 2, knee: 6, attack: 0.02, release: 0.15, makeupGain: 0, mix: 1.0, width: 1.0 },
            high: { threshold: -24, ratio: 2, knee: 6, attack: 0.01, release: 0.1, makeupGain: 0, mix: 1.0, width: 1.0 }
        };

        this.onEnded = null;
        this.smoothingFactor = 0.5;
        this.bypassed = false;
        this.bypassGain = null;
        this.autoLufsNormalize = true; // LUFS -14 normalization saat export

        // FX State
        this.fxState = {
            delay:   { active: false, time: 0.25, feedback: 0.2, mix: 0.15 },
            reverb:  { active: false, decay: 1.5, mix: 0.10 },
            widener: { active: false, width: 1.2 },
            saturation: { active: false, drive: 0.15, mix: 0.3 },
            gate:    { active: false, threshold: -50, attack: 0.002, release: 0.05 },
            chorus:  { active: false, rate: 0.8, depth: 0.003, mix: 0.10 }
        };
        this.manualFX = {};
        this.fxNodes = {};
    }


    async init() {
        if (this.audioCtx) return;
        this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioCtx.createAnalyser();
        this.analyser.fftSize = 2048;
        this.analyser.smoothingTimeConstant = this.smoothingFactor;
        this.masterAnalyser = this.audioCtx.createAnalyser();
        this.masterAnalyser.fftSize = 16384; 

        // Bypass path
        this.bypassGain = this.audioCtx.createGain();
        this.bypassGain.gain.value = 1;

        // Instantiate Modules
        this.modules = {
            noise: new NoiseReduction(this.audioCtx, this.noiseReductionSettings),
            transient: new TransientShaper(this.audioCtx, this.transientSettings),
            eq: new ParametricEQ(this.audioCtx, this.eqState),
            subBass: new SubBass808(this.audioCtx, this.subBassState),
            dynEq: new DynamicEQ(this.audioCtx, this.dynEqSettings),
            comp: new Compressor(this.audioCtx, this.compSettings),
            mbc: new MultibandCompressor(this.audioCtx, this.mbCompSettings),
            clipper: new Clipper(this.audioCtx, this.clipSettings),
            fx: new FXChain(this.audioCtx, this.fxState),
            limiter: new Limiter(this.audioCtx, this.limSettings)
        };

        // Mastering chain order:
        // 1. Noise Reduction  — pembersihan
        // 2. Parametric EQ    — tonal shaping
        // 3. Transient Shaper — attack/sustain control
        // 4. Dynamic EQ       — frequency-dependent dynamics (HYBRID)
        // 5. FX Chain         — saturation, widener, dll
        // 6. Compressor       — single-band dynamics (HYBRID)
        // 7. Multiband Comp   — multiband dynamics (HYBRID)
        // 8. 808 Sub Bass     — bass enhancement (SETELAH MBC agar tidak dikompensasi!)
        // 9. Clipper          — peak shaping + loudness (HYBRID)
        // 10. Limiter         — final ceiling protection (HYBRID)
        this.chain = [
            this.modules.noise,
            this.modules.eq,
            this.modules.transient,
            this.modules.dynEq,
            this.modules.fx,
            this.modules.comp,
            this.modules.mbc,
            this.modules.subBass,
            this.modules.clipper,
            this.modules.limiter
        ];

        // Wire Modules (placeholder bypass connections first)
        for (let i = 0; i < this.chain.length - 1; i++) {
            this.chain[i].connect(this.chain[i + 1]);
        }
        
        // Final connections
        this.chain[this.chain.length - 1].connect(this.analyser);
        this.bypassGain.connect(this.analyser);
        this.analyser.connect(this.masterAnalyser);
        this.masterAnalyser.connect(this.audioCtx.destination);

        // ===== HYBRID ENGINE: Muat AudioWorklet processors via Blob URL =====
        // WorkletLoader meng-embed semua kode DSP sebagai inline string,
        // sehingga tidak bergantung pada path file (menghindari masalah Tauri CSP).
        try {
            const loader = new WorkletLoader(this.audioCtx);
            await loader.loadAll();
            
            // Inisialisasi worklet node untuk semua modul yang butuh
            this.modules.noise.initWorklet();
            this.modules.dynEq.initWorklet();
            this.modules.comp.initWorklet();
            this.modules.mbc.initWorklet();
            this.modules.subBass.initWorklet();
            this.modules.clipper.initWorklet();
            this.modules.limiter.initWorklet();

            // ============================================================
            // KRITIS: Re-sinkronisasi state engine → worklet.
            // applyPreset() bisa dipanggil SEBELUM init() (dari DOMContentLoaded),
            // sehingga parameter preset tidak sampai ke worklet karena
            // workletNode belum ada saat itu. Kirim ulang SEMUA state terkini.
            // ============================================================
            this.modules.dynEq.update(this.activeState.dynEqSettings);
            this.modules.comp.update({ ...this.compSettings });
            this.modules.mbc.update({
                active: this.mbCompSettings.active,
                lowMidFreq: this.mbCompSettings.lowMidFreq,
                midHighFreq: this.mbCompSettings.midHighFreq,
                low: { ...this.mbCompSettings.low },
                mid: { ...this.mbCompSettings.mid },
                high: { ...this.mbCompSettings.high }
            });
            this.modules.subBass.update(this.activeState.subBass);
            this.modules.clipper.update({ ...this.clipSettings });
            this.modules.limiter.update({ ...this.limSettings });

            console.log('[AudioEngine] 🔄 State re-synced ke worklet:', {
                comp: { threshold: this.compSettings.threshold, ratio: this.compSettings.ratio, makeupGain: this.compSettings.makeupGain, active: this.compSettings.active },
                limiter: { ceiling: this.limSettings.ceiling, thresh: this.limSettings.thresh, active: this.limSettings.active },
                clipper: { threshold: this.clipSettings.threshold, active: this.clipSettings.active },
                mbc: { lowMidFreq: this.mbCompSettings.lowMidFreq, midHighFreq: this.mbCompSettings.midHighFreq, active: this.mbCompSettings.active },
                dynEq: { active: this.dynEqSettings.active }
            });
            console.log('[AudioEngine] ✅ Hybrid Engine: Semua AudioWorklet aktif.');
        } catch (e) {
            console.warn('[AudioEngine] ❌ Hybrid Engine gagal, menggunakan fallback bypass.', e);
        }
    }

    async loadUrl(url) {
        if (!this.audioCtx) await this.init();
        
        return new Promise((resolve, reject) => {
            this.stop();
            
            if (this.audioElement.src && this.audioElement.src.startsWith('blob:')) {
                URL.revokeObjectURL(this.audioElement.src);
            }
            
            this.audioElement.src = url;
            this.audioElement.load();

            this.audioElement.onloadedmetadata = () => {
                this._duration = this.audioElement.duration;
                resolve({ 
                    duration: this._duration, 
                    sampleRate: this.audioCtx.sampleRate, 
                    channels: 2 
                });
            };
            this.audioElement.onerror = () => reject(new Error('Gagal memuat streaming audio.'));
        });
    }

    play() {
        if (!this.audioElement.src || this.isPlaying) return false;
        if (this.audioCtx.state === 'suspended') this.audioCtx.resume();
        
        if (!this.sourceNode) {
            this.sourceNode = this.audioCtx.createMediaElementSource(this.audioElement);
            this.sourceNode.connect(this.bypassed ? this.bypassGain : this.chain[0].input);
        }
        
        // Simpan play promise agar bisa di-catch saat pause/stop dipanggil cepat
        this._playPromise = this.audioElement.play();
        if (this._playPromise) {
            this._playPromise.catch(err => {
                // AbortError terjadi saat pause()/stop() dipanggil sebelum play() selesai — ini normal
                if (err.name !== 'AbortError') {
                    console.error('[AudioEngine] Play error:', err);
                }
            });
        }
        this.isPlaying = true;
        
        this.audioElement.onended = () => { if (this.isPlaying) { this.stop(); if (this.onEnded) this.onEnded(); } };
        return true;
    }

    pause() {
        if (!this.isPlaying) return;
        // Tunggu play promise selesai sebelum pause untuk menghindari AbortError
        if (this._playPromise) {
            this._playPromise.then(() => {
                this.audioElement.pause();
            }).catch(() => {});
            this._playPromise = null;
        } else {
            this.audioElement.pause();
        }
        this.isPlaying = false;
    }

    stop() {
        if (this._playPromise) {
            this._playPromise.then(() => {
                this.audioElement.pause();
                this.audioElement.currentTime = 0;
            }).catch(() => {});
            this._playPromise = null;
        } else {
            this.audioElement.pause();
            this.audioElement.currentTime = 0;
        }
        this.isPlaying = false;
    }

    seek(time) {
        this.audioElement.currentTime = Math.max(0, Math.min(time, this._duration));
    }

    getCurrentTime() { return this.audioElement.currentTime; }
    getDuration() { return this._duration; }
    hasBuffer() { return !!this.audioElement.getAttribute('src'); }

// --- Noise Reduction ---
    setNoiseReductionThreshold(v) { this.noiseReductionSettings.threshold = parseFloat(v); if(this.modules) this.modules.noise.update({ threshold: parseFloat(v) }); }
    setNoiseReductionAmount(v) { this.noiseReductionSettings.amount = parseFloat(v); if(this.modules) this.modules.noise.update({ amount: parseFloat(v) }); }
    toggleNoiseReduction(active) { this.noiseReductionSettings.active = active; if(this.modules) this.modules.noise.update({ active: active }); }

    // --- Transient Shaper ---
    setTransientAttack(v) { this.transientSettings.attack = parseFloat(v); if(this.modules) this.modules.transient.update({ attack: parseFloat(v) }); }
    setTransientSustain(v) { this.transientSettings.sustain = parseFloat(v); if(this.modules) this.modules.transient.update({ sustain: parseFloat(v) }); }
    toggleTransientShaper(active) { console.log(`[Toggle] Transient Shaper -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.transientSettings.active = active; if(this.modules) this.modules.transient.update({ active: active }); }

    // --- Dynamic EQ ---
    setDynEqFreq(band, v) { this.dynEqSettings.bands[band].freq = v; this._updateDynamicEQ(); }
    setDynEqQ(band, v) { this.dynEqSettings.bands[band].q = v; this._updateDynamicEQ(); }
    setDynEqThresh(band, v) { this.dynEqSettings.bands[band].thresh = v; this._updateDynamicEQ(); }
    setDynEqRatio(band, v) { this.dynEqSettings.bands[band].ratio = v; this._updateDynamicEQ(); }
    toggleDynEq(active) { console.log(`[Toggle] Dynamic EQ -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.dynEqSettings.active = active; this._updateDynamicEQ(); }

    setDynEqThreshOffset(band, val) {
        this.offsets.dynEqThresh[band] = parseFloat(val) || 0;
        this._updateDynamicEQ();
    }

    _updateDynamicEQ() {
        if (!this.modules) return;

        this.activeState.dynEqSettings = JSON.parse(JSON.stringify(this.dynEqSettings));
        
        for (let i = 0; i < this.activeState.dynEqSettings.bands.length; i++) {
            const baseThresh = this.dynEqSettings.bands[i].thresh;
            const offset = this.offsets.dynEqThresh[i];
            // Tambahkan offset, tapi jangan sampai threshold > 0
            this.activeState.dynEqSettings.bands[i].thresh = Math.min(0, baseThresh + offset);
        }

        this.modules.dynEq.update(this.activeState.dynEqSettings);
    }
    // EQ
    setEQHpfFreq(v) { this.eqState.hpf.freq = parseFloat(v); if(this.modules) this.modules.eq.update({ hpf: { freq: parseFloat(v) } }); }
    setEQLow(v) { this.eqState.low.gain = parseFloat(v); if(this.modules) this.modules.eq.update({ low: { gain: parseFloat(v) } }); }
    setEQLowFreq(v) { this.eqState.low.freq = parseFloat(v); if(this.modules) this.modules.eq.update({ low: { freq: parseFloat(v) } }); }
    setEQMid(v) { this.eqState.mid.gain = parseFloat(v); if(this.modules) this.modules.eq.update({ mid: { gain: parseFloat(v) } }); }
    setEQMidFreq(v) { this.eqState.mid.freq = parseFloat(v); if(this.modules) this.modules.eq.update({ mid: { freq: parseFloat(v) } }); }
    setEQMidQ(v) { this.eqState.mid.q = parseFloat(v); if(this.modules) this.modules.eq.update({ mid: { q: parseFloat(v) } }); }
    setEQHigh(v) { this.eqState.high.gain = parseFloat(v); if(this.modules) this.modules.eq.update({ high: { gain: parseFloat(v) } }); }
    setEQHighFreq(v) { this.eqState.high.freq = parseFloat(v); if(this.modules) this.modules.eq.update({ high: { freq: parseFloat(v) } }); }
    toggleEQ(band, active) { 
        this.eqState[band].active = active; 
        console.log(`[Toggle] EQ ${band.toUpperCase()} -> ${active ? 'ACTIVE' : 'BYPASS'}`);
        if(this.modules) {
            const upd = {}; upd[band] = { active: active };
            this.modules.eq.update(upd);
        }
    }

    // --- 808 Sub Bass ---
    setSubBassFreq(v) { this.subBassState.freq = parseFloat(v); this._updateSubBass(); }
    setSubBassDrive(v) { this.subBassState.drive = parseFloat(v); this._updateSubBass(); }
    setSubBassSub(v) { this.subBassState.sub = parseFloat(v); this._updateSubBass(); }
    setSubBassClean(v) { this.subBassState.clean = parseFloat(v); this._updateSubBass(); }
    setSubBassMix(v) { this.subBassState.mix = parseFloat(v); this._updateSubBass(); }
    toggleSubBass(active) { console.log(`[Toggle] 808 Sub Bass -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.subBassState.active = active; this._updateSubBass(); }

    setSubBassCleanOffset(val) { this.offsets.subBassClean = parseFloat(val) || 0; this._updateSubBass(); }
    setSubBassGainOffset(val) { this.offsets.subBassGain = parseFloat(val) || 0; this._updateSubBass(); }

    _updateSubBass() {
        if (!this.modules) return;
        
        // Base + Offset
        const finalClean = Math.min(100, Math.max(0, this.subBassState.clean + this.offsets.subBassClean));
        const finalMix = Math.min(100, Math.max(0, this.subBassState.mix + this.offsets.subBassGain));
        
        this.activeState.subBass = {
            ...this.subBassState,
            clean: finalClean,
            mix: finalMix
        };
        
        this.modules.subBass.update(this.activeState.subBass);
    }

    // Compressor
    setCompThreshold(v) { this.compSettings.threshold = parseFloat(v); if(this.modules) this.modules.comp.update({ threshold: parseFloat(v) }); }
    setCompRatio(v) { this.compSettings.ratio = parseFloat(v); if(this.modules) this.modules.comp.update({ ratio: parseFloat(v) }); }
    setCompKnee(v) { this.compSettings.knee = parseFloat(v); if(this.modules) this.modules.comp.update({ knee: parseFloat(v) }); }
    setCompAttack(v) { this.compSettings.attack = parseFloat(v); if(this.modules) this.modules.comp.update({ attack: parseFloat(v) }); }
    setCompRelease(v) { this.compSettings.release = parseFloat(v); if(this.modules) this.modules.comp.update({ release: parseFloat(v) }); }
    setMakeupGain(vDB) { this.compSettings.makeupGain = vDB; if(this.modules) this.modules.comp.update({ makeupGain: vDB }); }
    setCompMix(v) { this.compSettings.mix = parseFloat(v); if(this.modules) this.modules.comp.update({ mix: parseFloat(v) }); }
    toggleCompressor(active) { console.log(`[Toggle] Compressor -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.compSettings.active = active; if(this.modules) this.modules.comp.update({ active: active }); }

    // Multiband Compressor
    setMBCompLowThreshold(v) { this.mbCompSettings.low.threshold = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { threshold: parseFloat(v) } }); }
    setMBCompLowRatio(v) { this.mbCompSettings.low.ratio = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { ratio: parseFloat(v) } }); }
    setMBCompLowKnee(v) { this.mbCompSettings.low.knee = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { knee: parseFloat(v) } }); }
    setMBCompLowAttack(v) { this.mbCompSettings.low.attack = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { attack: parseFloat(v) } }); }
    setMBCompLowRelease(v) { this.mbCompSettings.low.release = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { release: parseFloat(v) } }); }
    setMBCompLowMakeup(v) { this.mbCompSettings.low.makeupGain = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { makeupGain: parseFloat(v) } }); }
    setMBCompLowMix(v) { this.mbCompSettings.low.mix = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { mix: parseFloat(v) } }); }

    setMBCompMidThreshold(v) { this.mbCompSettings.mid.threshold = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { threshold: parseFloat(v) } }); }
    setMBCompMidRatio(v) { this.mbCompSettings.mid.ratio = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { ratio: parseFloat(v) } }); }
    setMBCompMidKnee(v) { this.mbCompSettings.mid.knee = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { knee: parseFloat(v) } }); }
    setMBCompMidAttack(v) { this.mbCompSettings.mid.attack = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { attack: parseFloat(v) } }); }
    setMBCompMidRelease(v) { this.mbCompSettings.mid.release = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { release: parseFloat(v) } }); }
    setMBCompMidMakeup(v) { this.mbCompSettings.mid.makeupGain = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { makeupGain: parseFloat(v) } }); }
    setMBCompMidMix(v) { this.mbCompSettings.mid.mix = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { mix: parseFloat(v) } }); }

    setMBCompHighThreshold(v) { this.mbCompSettings.high.threshold = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { threshold: parseFloat(v) } }); }
    setMBCompHighRatio(v) { this.mbCompSettings.high.ratio = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { ratio: parseFloat(v) } }); }
    setMBCompHighKnee(v) { this.mbCompSettings.high.knee = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { knee: parseFloat(v) } }); }
    setMBCompHighAttack(v) { this.mbCompSettings.high.attack = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { attack: parseFloat(v) } }); }
    setMBCompHighRelease(v) { this.mbCompSettings.high.release = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { release: parseFloat(v) } }); }
    setMBCompHighMakeup(v) { this.mbCompSettings.high.makeupGain = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { makeupGain: parseFloat(v) } }); }
    setMBCompHighMix(v) { this.mbCompSettings.high.mix = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { mix: parseFloat(v) } }); }

    setMBCompLowMidFreq(v) { this.mbCompSettings.lowMidFreq = parseFloat(v); if(this.modules) this.modules.mbc.update({ lowMidFreq: parseFloat(v) }); }
    setMBCompMidHighFreq(v) { this.mbCompSettings.midHighFreq = parseFloat(v); if(this.modules) this.modules.mbc.update({ midHighFreq: parseFloat(v) }); }
    toggleMBComp(active) { console.log(`[Toggle] Multiband -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.mbCompSettings.active = active; if(this.modules) this.modules.mbc.update({ active: active }); }
    getMBCompGainReduction() { return this.modules ? this.modules.mbc.getReduction() : { low: 0, mid: 0, high: 0 }; };

    // Clipper
    setClipperThreshold(v) { this.clipSettings.threshold = parseFloat(v); if(this.modules) this.modules.clipper.update({ threshold: parseFloat(v) }); }
    toggleClipper(active) { console.log(`[Toggle] Clipper -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.clipSettings.active = active; if(this.modules) this.modules.clipper.update({ active: active }); }

    // Limiter
    setLimiterThreshold(v) { this.limSettings.thresh = parseFloat(v); if(this.modules) this.modules.limiter.update({ thresh: parseFloat(v) }); }
    setLimiterCeiling(v) { this.limSettings.ceiling = parseFloat(v); if(this.modules) this.modules.limiter.update({ ceiling: parseFloat(v) }); }
    setLimiterRelease(v) { this.limSettings.release = parseFloat(v); if(this.modules) this.modules.limiter.update({ release: parseFloat(v) }); }
    setLimiterKnee(v) { this.limSettings.knee = parseFloat(v); if(this.modules) this.modules.limiter.update({ knee: parseFloat(v) }); }
    toggleLimiterAutoRelease(active) { this.limSettings.autoRelease = active; if(this.modules) this.modules.limiter.update({ autoRelease: active }); }
    toggleLimiter(active) { console.log(`[Toggle] Limiter -> ${active ? 'ACTIVE' : 'BYPASS'}`); this.limSettings.active = active; if(this.modules) this.modules.limiter.update({ active: active }); }
    toggleAutoLufs(active) { console.log(`[Toggle] Auto LUFS -14 -> ${active ? 'ON' : 'OFF'}`); this.autoLufsNormalize = active; }

    // Smoothing
    setSmoothing(v) { this.smoothingFactor = Math.min(v, 0.95); if (this.analyser) this.analyser.smoothingTimeConstant = this.smoothingFactor; }

    // Bypass toggle
    setBypassed(bypassed) {
        this.bypassed = bypassed;
        if (!this.sourceNode) return;
        // Reconnect source to the correct path
        this.sourceNode.disconnect();
        this.sourceNode.connect(this.bypassed ? this.bypassGain : this.chain[0].input);
        
        console.log(`[MASTER BYPASS] ${bypassed ? '🔇 BYPASS (audio asli)' : '🎛️ MASTERED (melalui chain)'}`);
        if (!bypassed) {
            // Log semua module bypass status untuk debugging
            const moduleStatus = {};
            for (const [name, mod] of Object.entries(this.modules)) {
                moduleStatus[name] = {
                    bypassed: mod.isBypassed,
                    mainGain: mod.mainGain.gain.value,
                    bypassGain: mod.bypassGain.gain.value,
                    hasWorklet: !!mod.workletNode
                };
            }
            console.table(moduleStatus);
            console.log('[DIAG] Limiter state:', JSON.stringify(this.limSettings));
            console.log('[DIAG] Comp state:', JSON.stringify(this.compSettings));
        }
    }

    // Channel info
    getChannelCount() {
        return this.hasBuffer() ? 2 : 0;
    }

    // Analyzer
    getSpectrumData() { if (!this.analyser) return new Uint8Array(0); const d = new Uint8Array(this.analyser.frequencyBinCount); this.analyser.getByteFrequencyData(d); return d; }

    getMasterWaveformData() {
        if (!this.masterAnalyser) return new Float32Array(0);
        const d = new Float32Array(this.masterAnalyser.fftSize);
        this.masterAnalyser.getFloatTimeDomainData(d);
        return d;
    }

    getSubBassWaveformData() {
        if (!this.modules.subBass) return new Float32Array(0);
        return this.modules.subBass.getWaveformData();
    }
    getMasterLevel() {
        if (!this.masterAnalyser) return { peakL: 0, peakR: 0, dbL: -Infinity, dbR: -Infinity };
        // We only have 1 master analyser, let's approximate L/R for visualization
        const d = new Float32Array(this.masterAnalyser.fftSize);
        this.masterAnalyser.getFloatTimeDomainData(d);
        let maxL = 0, maxR = 0;
        for (let i = 0; i < d.length; i+=2) { 
            const vL = Math.abs(d[i]); if (vL > maxL) maxL = vL; 
            const vR = Math.abs(d[i+1]); if (vR > maxR) maxR = vR; 
        }
        return { 
            peakL: maxL, peakR: maxR, 
            dbL: 20 * Math.log10(maxL || 0.000001), // Min -120dB
            dbR: 20 * Math.log10(maxR || 0.000001)
        };
    }
    
    getLoudnessStats() {
        if (!this.masterAnalyser) return { lufs: -Infinity, tp: -Infinity, dr: 0 };
        const d = new Float32Array(this.masterAnalyser.fftSize); 
        this.masterAnalyser.getFloatTimeDomainData(d);
        
        let max = 0;
        let sumSq = 0;
        for (let i = 1; i < d.length - 2; i++) {
            const p0 = d[i - 1], p1 = d[i], p2 = d[i + 1], p3 = d[i + 2];
            sumSq += p1 * p1;
            
            const absP1 = Math.abs(p1);
            if (absP1 > max) max = absP1;
            
            // P1: 4x Cubic Oversampling for Live Meter
            if (absP1 > 0.05 || Math.abs(p2) > 0.05) {
                const v0 = (p2 - p0) * 0.5;
                const v1 = (p3 - p1) * 0.5;
                for (let k = 1; k < 4; k++) {
                    const t = k / 4.0;
                    const t2 = t * t, t3 = t * t2;
                    const interp = (2 * p1 - 2 * p2 + v0 + v1) * t3 + (-3 * p1 + 3 * p2 - 2 * v0 - v1) * t2 + v0 * t + p1;
                    const absInterp = Math.abs(interp);
                    if (absInterp > max) max = absInterp;
                }
            }
        }
        // Account for edges in RMS
        if (d.length > 0) {
            sumSq += d[0]*d[0] + d[d.length-2]*d[d.length-2] + d[d.length-1]*d[d.length-1];
            if (Math.abs(d[0]) > max) max = Math.abs(d[0]);
            if (Math.abs(d[d.length-1]) > max) max = Math.abs(d[d.length-1]);
        }

        const rms = Math.sqrt(sumSq / d.length);
        const tp = 20 * Math.log10(max || 0.0001);
        const lufs = 20 * Math.log10(rms || 0.0001) + 3; // Aproksimasi RMS untuk live meter (angka akurat ada di Summary Report via lufs-web)
        const lra = tp - (20 * Math.log10(rms || 0.0001));
        return { lufs, tp, dr: lra };
    }

    getGainReduction() { return this.modules ? this.modules.comp.getReduction() : 0; }
    getLimiterReduction() { return this.modules ? this.modules.limiter.getReduction() : 0; }
    getClipperReduction() { return this.modules ? this.modules.clipper.getReduction() : 0; }



    // ==================== FX SYSTEM ====================
    // --- FX Setters ---
    setFXActive(fxName, active) { 
        this.fxState[fxName].active = active; 
        if (this.modules) { 
            const upd = {}; upd[fxName] = { active: active }; 
            this.modules.fx.update(upd); 
        } 
    }

    setDelayTime(v) { this.fxState.delay.time = parseFloat(v); if(this.modules) this.modules.fx.update({ delay: { time: parseFloat(v) } }); }
    setDelayFeedback(v) { this.fxState.delay.feedback = parseFloat(v); if(this.modules) this.modules.fx.update({ delay: { feedback: parseFloat(v) } }); }
    setDelayMix(v) { this.fxState.delay.mix = parseFloat(v); if(this.modules) this.modules.fx.update({ delay: { mix: parseFloat(v) } }); }

    setReverbDecay(v) { 
        this.fxState.reverb.decay = parseFloat(v); 
        if (this.modules) {
            if (this._reverbDebounceTimer) clearTimeout(this._reverbDebounceTimer);
            this._reverbDebounceTimer = setTimeout(() => {
                this.modules.fx.updateReverbDecay(v);
            }, 150);
        }
    }
    setReverbMix(v) { this.fxState.reverb.mix = parseFloat(v); if(this.modules) this.modules.fx.update({ reverb: { mix: parseFloat(v) } }); }

    setWidenerWidth(v) { this.fxState.widener.width = parseFloat(v); if(this.modules) this.modules.fx.update({ widener: { width: parseFloat(v) } }); }

    // Multiband Imager
    setMBCompLowWidth(v) { this.mbCompSettings.low.width = parseFloat(v); if(this.modules) this.modules.mbc.update({ low: { width: parseFloat(v) } }); }
    setMBCompMidWidth(v) { this.mbCompSettings.mid.width = parseFloat(v); if(this.modules) this.modules.mbc.update({ mid: { width: parseFloat(v) } }); }
    setMBCompHighWidth(v) { this.mbCompSettings.high.width = parseFloat(v); if(this.modules) this.modules.mbc.update({ high: { width: parseFloat(v) } }); }
            
    setSatDrive(v) { this.fxState.saturation.drive = parseFloat(v); if(this.modules) this.modules.fx.update({ saturation: { drive: parseFloat(v) } }); }
    setSatMix(v) { this.fxState.saturation.mix = parseFloat(v); if(this.modules) this.modules.fx.update({ saturation: { mix: parseFloat(v) } }); }

    setGateThreshold(v) { this.fxState.gate.threshold = parseFloat(v); if(this.modules) this.modules.fx.update({ gate: { threshold: parseFloat(v) } }); }
    setGateAttack(v) { this.fxState.gate.attack = parseFloat(v); if(this.modules) this.modules.fx.update({ gate: { attack: parseFloat(v) } }); }
    setGateRelease(v) { this.fxState.gate.release = parseFloat(v); if(this.modules) this.modules.fx.update({ gate: { release: parseFloat(v) } }); }

    // Call this in the animation loop
    processGate() { /* Managed by DSP if implemented, otherwise dummy */ }

    setChorusRate(v) { this.fxState.chorus.rate = parseFloat(v); if(this.modules) this.modules.fx.update({ chorus: { rate: parseFloat(v) } }); }
    setChorusDepth(v) { this.fxState.chorus.depth = parseFloat(v); if(this.modules) this.modules.fx.update({ chorus: { depth: parseFloat(v) } }); }
    setChorusMix(v) { this.fxState.chorus.mix = parseFloat(v); if(this.modules) this.modules.fx.update({ chorus: { mix: parseFloat(v) } }); }

    markFXManual(fxName, isManual = true) {
        if (!this.manualFX) this.manualFX = {};
        this.manualFX[fxName] = isManual;
    }

    getFXState() { return JSON.parse(JSON.stringify(this.fxState)); }
    applyFXState(s) {
        if (!s) return;
        for (const name of Object.keys(s)) {
            if (this.fxState[name]) Object.assign(this.fxState[name], s[name]);
        }
    }

    // Preset
    applyPreset(p) {
        // EQ — selalu set semua parameter, gunakan default jika tidak ada di preset
        this.setEQHpfFreq(p.hpf !== undefined ? p.hpf : 20);
        this.setEQLow(p.low !== undefined ? p.low : 0);
        this.setEQLowFreq(p.lFreq !== undefined ? p.lFreq : 250);
        this.setEQMid(p.mid !== undefined ? p.mid : 0);
        this.setEQMidFreq(p.mFreq !== undefined ? p.mFreq : 1000);
        this.setEQMidQ(p.mQ !== undefined ? p.mQ : 1.0);
        this.setEQHigh(p.high !== undefined ? p.high : 0);
        this.setEQHighFreq(p.hFreq !== undefined ? p.hFreq : 4000);
        if (p.hpfActive !== undefined) this.toggleEQ('hpf', p.hpfActive); else this.toggleEQ('hpf', true);
        if (p.lowActive !== undefined) this.toggleEQ('low', p.lowActive); else this.toggleEQ('low', true);
        if (p.midActive !== undefined) this.toggleEQ('mid', p.midActive); else this.toggleEQ('mid', true);
        if (p.highActive !== undefined) this.toggleEQ('high', p.highActive); else this.toggleEQ('high', true);

        // Compressor — selalu set semua
        this.setCompThreshold(p.cThresh !== undefined ? p.cThresh : -24);
        this.setCompRatio(p.cRatio !== undefined ? p.cRatio : 4);
        this.setCompKnee(p.cKnee !== undefined ? p.cKnee : 6);
        this.setCompAttack(p.cAtt !== undefined ? p.cAtt : 0.05);
        this.setCompRelease(p.cRel !== undefined ? p.cRel : 0.25);
        this.setMakeupGain(p.mkp !== undefined ? p.mkp : 0);
        this.setCompMix(p.cMix !== undefined ? p.cMix : 1.0);
        if (p.compActive !== undefined) this.toggleCompressor(p.compActive); else this.toggleCompressor(true);

        // Multiband Compressor
        this.setMBCompLowMidFreq(p.mbcXoverLow !== undefined ? p.mbcXoverLow : 250);
        this.setMBCompMidHighFreq(p.mbcXoverHigh !== undefined ? p.mbcXoverHigh : 4000);
        this.setMBCompLowThreshold(p.mbcLowThresh !== undefined ? p.mbcLowThresh : -24);
        this.setMBCompLowRatio(p.mbcLowRatio !== undefined ? p.mbcLowRatio : 2);
        this.setMBCompLowAttack(p.mbcLowAtt !== undefined ? p.mbcLowAtt : 0.03);
        this.setMBCompLowRelease(p.mbcLowRel !== undefined ? p.mbcLowRel : 0.2);
        this.setMBCompLowMakeup(p.mbcLowMkp !== undefined ? p.mbcLowMkp : 0);
        this.setMBCompMidThreshold(p.mbcMidThresh !== undefined ? p.mbcMidThresh : -24);
        this.setMBCompMidRatio(p.mbcMidRatio !== undefined ? p.mbcMidRatio : 2);
        this.setMBCompMidAttack(p.mbcMidAtt !== undefined ? p.mbcMidAtt : 0.02);
        this.setMBCompMidRelease(p.mbcMidRel !== undefined ? p.mbcMidRel : 0.15);
        this.setMBCompMidMakeup(p.mbcMidMkp !== undefined ? p.mbcMidMkp : 0);
        this.setMBCompHighThreshold(p.mbcHighThresh !== undefined ? p.mbcHighThresh : -24);
        this.setMBCompHighRatio(p.mbcHighRatio !== undefined ? p.mbcHighRatio : 2);
        this.setMBCompHighAttack(p.mbcHighAtt !== undefined ? p.mbcHighAtt : 0.01);
        this.setMBCompHighRelease(p.mbcHighRel !== undefined ? p.mbcHighRel : 0.1);
        this.setMBCompHighMakeup(p.mbcHighMkp !== undefined ? p.mbcHighMkp : 0);

        // Multiband Width (integrated into MBComp)
        this.setMBCompLowWidth(p.mbcLowWidth !== undefined ? p.mbcLowWidth : (p.mbiLowWidth !== undefined ? p.mbiLowWidth : 0.0));
        this.setMBCompMidWidth(p.mbcMidWidth !== undefined ? p.mbcMidWidth : (p.mbiMidWidth !== undefined ? p.mbiMidWidth : 1.0));
        this.setMBCompHighWidth(p.mbcHighWidth !== undefined ? p.mbcHighWidth : (p.mbiHighWidth !== undefined ? p.mbiHighWidth : 1.2));
        if (p.mbcActive !== undefined) this.toggleMBComp(p.mbcActive); else this.toggleMBComp(true);

        // Clipper — selalu set
        this.setClipperThreshold(p.clip !== undefined ? p.clip : 0);
        if (p.clipActive !== undefined) this.toggleClipper(p.clipActive); else this.toggleClipper(true);

        // Limiter
        const limThresh = p.lThresh !== undefined ? p.lThresh : -1.0;
        this.setLimiterThreshold(limThresh);
        this.setLimiterCeiling(p.lCeil !== undefined ? p.lCeil : -1.5);
        this.setLimiterRelease(p.lRel !== undefined ? p.lRel : 0.25);
        this.setLimiterKnee(p.lKnee !== undefined ? p.lKnee : 0.0);
        this.toggleLimiterAutoRelease(p.lAutoRel !== undefined ? p.lAutoRel : false);
        this.toggleAutoLufs(p.autoLufs !== undefined ? p.autoLufs : true);
        if (p.limActive !== undefined) this.toggleLimiter(p.limActive); else this.toggleLimiter(true);

        // Noise Reduction
        if(p.nrThresh !== undefined) { this.setNoiseReductionThreshold(p.nrThresh); this.setNoiseReductionAmount(p.nrAmount); }
        this.toggleNoiseReduction(p.nrActive !== undefined ? p.nrActive : true);
        
        if(p.tsAtt !== undefined) {
            // Preset bawaan menyimpan desimal (0.08), konversi ke persen (8) agar konsisten dengan fader
            const att = Math.abs(p.tsAtt) < 1.01 ? p.tsAtt * 100 : p.tsAtt;
            const sus = Math.abs(p.tsSus) < 1.01 ? p.tsSus * 100 : p.tsSus;
            this.setTransientAttack(att);
            this.setTransientSustain(sus);
        }
        this.toggleTransientShaper(p.tsActive !== undefined ? p.tsActive : true);

        // 808 Sub Bass
        if (p.subBass) {
            this.setSubBassFreq(p.subBass.freq !== undefined ? p.subBass.freq : 50);
            this.setSubBassDrive(p.subBass.drive !== undefined ? p.subBass.drive : 30);
            this.setSubBassSub(p.subBass.sub !== undefined ? p.subBass.sub : 50);
            this.setSubBassClean(p.subBass.clean !== undefined ? p.subBass.clean : 40);
            this.setSubBassMix(p.subBass.mix !== undefined ? p.subBass.mix : 60);
        }
        this.toggleSubBass(p.subBassActive !== undefined ? p.subBassActive : true);
        
        // Dynamic EQ bands

        // Dynamic EQ
        if (p.dynEq) {
            for (let i=0; i<4; i++) {
                if (p.dynEq[i]) {
                    this.setDynEqFreq(i, p.dynEq[i].freq);
                    this.setDynEqQ(i, p.dynEq[i].q);
                    this.setDynEqThresh(i, p.dynEq[i].thresh);
                    this.setDynEqRatio(i, p.dynEq[i].ratio);
                }
            }
        }
        this.toggleDynEq(p.dynEqActive !== undefined ? p.dynEqActive : true);

        // Default values for FX reset
        const defaultFX = {
            delay:   { active: false, time: 0.25, feedback: 0.2, mix: 0.15 },
            reverb:  { active: false, decay: 1.5, mix: 0.10 },
            widener: { active: false, width: 1.2 },
            saturation: { active: false, drive: 0.15, mix: 0.3 },
            gate:    { active: false, threshold: -50, attack: 0.002, release: 0.05 },
            chorus:  { active: false, rate: 0.8, depth: 0.003, mix: 0.10 }
        };

        if (!this.manualFX) this.manualFX = {};

        // Apply FX state if present in preset
        if (p.fx) {
            this.applyFXState(p.fx);
            // Re-apply active FX nodes with restored parameters
            for (const name of Object.keys(p.fx)) {
                this.manualFX[name] = false; // Preset overrides manual state
                const s = p.fx[name];
                switch (name) {
                    case 'delay':
                        this.setDelayTime(s.time); this.setDelayFeedback(s.feedback); this.setDelayMix(s.mix);
                        this.setFXActive('delay', s.active);
                        break;
                    case 'reverb':
                        this.setReverbDecay(s.decay); this.setReverbMix(s.mix);
                        this.setFXActive('reverb', s.active);
                        break;
                    case 'widener':
                        this.setWidenerWidth(s.width);
                        this.setFXActive('widener', s.active);
                        break;
                    case 'saturation':
                        this.setSatDrive(s.drive); this.setSatMix(s.mix);
                        this.setFXActive('saturation', s.active);
                        break;
                    case 'gate':
                        this.setGateThreshold(s.threshold); this.setGateAttack(s.attack); this.setGateRelease(s.release);
                        this.setFXActive('gate', s.active);
                        break;
                    case 'chorus':
                        this.setChorusRate(s.rate); this.setChorusDepth(s.depth); this.setChorusMix(s.mix);
                        this.setFXActive('chorus', s.active);
                        break;
                }
            }
        } else {
            // Preset DOES NOT HAVE FX: Reset non-manual FX to default
            for (const name of Object.keys(defaultFX)) {
                if (!this.manualFX[name]) {
                    const s = defaultFX[name];
                    this.fxState[name] = { ...s };
                    switch (name) {
                        case 'delay':
                            this.setDelayTime(s.time); this.setDelayFeedback(s.feedback); this.setDelayMix(s.mix);
                            this.setFXActive('delay', s.active);
                            break;
                        case 'reverb':
                            this.setReverbDecay(s.decay); this.setReverbMix(s.mix);
                            this.setFXActive('reverb', s.active);
                            break;
                        case 'widener':
                            this.setWidenerWidth(s.width);
                            this.setFXActive('widener', s.active);
                            break;
                        case 'saturation':
                            this.setSatDrive(s.drive); this.setSatMix(s.mix);
                            this.setFXActive('saturation', s.active);
                            break;
                        case 'gate':
                            this.setGateThreshold(s.threshold); this.setGateAttack(s.attack); this.setGateRelease(s.release);
                            this.setFXActive('gate', s.active);
                            break;
                        case 'chorus':
                            this.setChorusRate(s.rate); this.setChorusDepth(s.depth); this.setChorusMix(s.mix);
                            this.setFXActive('chorus', s.active);
                            break;
                    }
                }
            }
        }
    }
    getCurrentSettings() {
        return {
            hpf: this.eqState.hpf.freq,
            low: this.eqState.low.gain, lFreq: this.eqState.low.freq,
            mid: this.eqState.mid.gain, mFreq: this.eqState.mid.freq, mQ: this.eqState.mid.q,
            high: this.eqState.high.gain, hFreq: this.eqState.high.freq,
            hpfActive: this.eqState.hpf.active, lowActive: this.eqState.low.active,
            midActive: this.eqState.mid.active, highActive: this.eqState.high.active,
            
            cThresh: this.compSettings.threshold, cRatio: this.compSettings.ratio,
            cKnee: this.compSettings.knee, cAtt: this.compSettings.attack,
            cRel: this.compSettings.release, mkp: this.compSettings.makeupGain,
            cMix: this.compSettings.mix, compActive: this.compSettings.active,
            
            mbcXoverLow: this.mbCompSettings.lowMidFreq, mbcXoverHigh: this.mbCompSettings.midHighFreq,
            mbcLowThresh: this.mbCompSettings.low.threshold, mbcLowRatio: this.mbCompSettings.low.ratio, mbcLowAtt: this.mbCompSettings.low.attack, mbcLowRel: this.mbCompSettings.low.release, mbcLowMkp: this.mbCompSettings.low.makeupGain,
            mbcMidThresh: this.mbCompSettings.mid.threshold, mbcMidRatio: this.mbCompSettings.mid.ratio, mbcMidAtt: this.mbCompSettings.mid.attack, mbcMidRel: this.mbCompSettings.mid.release, mbcMidMkp: this.mbCompSettings.mid.makeupGain,
            mbcHighThresh: this.mbCompSettings.high.threshold, mbcHighRatio: this.mbCompSettings.high.ratio, mbcHighAtt: this.mbCompSettings.high.attack, mbcHighRel: this.mbCompSettings.high.release, mbcHighMkp: this.mbCompSettings.high.makeupGain,
            mbcActive: this.mbCompSettings.active,
            
            clip: this.clipSettings.threshold, clipActive: this.clipSettings.active,
            
            lCeil: this.limSettings.ceiling, lThresh: this.limSettings.thresh,
            lRel: this.limSettings.release, lKnee: this.limSettings.knee, limActive: this.limSettings.active,
            lAutoRel: this.limSettings.autoRelease,
            autoLufs: this.autoLufsNormalize,
            
            nrThresh: this.noiseReductionSettings.threshold, nrAmount: this.noiseReductionSettings.amount, nrActive: this.noiseReductionSettings.active,
            tsAtt: this.transientSettings.attack, tsSus: this.transientSettings.sustain, tsActive: this.transientSettings.active,
            dynEqActive: this.dynEqSettings.active, dynEq: JSON.parse(JSON.stringify(this.dynEqSettings.bands)),
            
            subBass: { ...this.subBassState }, subBassActive: this.subBassState.active,
            
            fx: this.getFXState()
        };
    }

    // Offline Render for Export
    // PENTING: Export SELALU melewati seluruh chain mastering tanpa bypass.
    // Bypass hanya berfungsi untuk membandingkan audio saat preview saja.
    async renderOffline(data, onProgress) {
        if (!data) throw new Error('Data audio tidak valid untuk render.');
        if (onProgress) onProgress(0.01);
        
        let arrayBuffer = data;
        if (typeof data === 'string') {
            const response = await fetch(data);
            arrayBuffer = await response.arrayBuffer();
        }
        
        if (onProgress) onProgress(0.1);
        const tempCtx = new (window.AudioContext || window.webkitAudioContext)();
        const renderBuffer = await tempCtx.decodeAudioData(arrayBuffer);
        await tempCtx.close();
        
        // Gunakan sample rate dari file asli untuk export yang ringan dan stabil
        // (mencegah file size meledak jika hardware user diset ke 192kHz)
        const ch = renderBuffer.numberOfChannels;
        const sr = renderBuffer.sampleRate;
        const len = Math.ceil(renderBuffer.duration * sr);
        if (onProgress) onProgress(0.2);
        
        const offCtx = new OfflineAudioContext(ch, len, sr);
        const oSource = offCtx.createBufferSource(); 
        oSource.buffer = renderBuffer;

        // Muat AudioWorklet ke OfflineAudioContext agar hasil export akurat
        try {
            const loader = new WorkletLoader(offCtx);
            await loader.loadAll();
        } catch (e) {
            console.warn('[AudioEngine] ❌ Gagal memuat Worklet di Offline Render, fallback ke bypass DSP.', e);
        }

        // ============================================================
        // GUNAKAN STATE ACTIVE/NON-ACTIVE SESUAI PILIHAN USER
        // Modul yang dimatikan (non-active) akan di-bypass saat export
        // untuk mempercepat proses rendering.
        // ============================================================
        const exportNoiseSettings = { ...this.noiseReductionSettings };
        const exportTransientSettings = { ...this.transientSettings };
        const exportEqState = JSON.parse(JSON.stringify(this.eqState));
        const exportSubBassState = { ...this.activeState.subBass }; // SmartLogic Dual-State
        const exportDynEqSettings = JSON.parse(JSON.stringify(this.activeState.dynEqSettings)); // SmartLogic Dual-State
        const exportCompSettings = { ...this.compSettings };
        const exportMbCompSettings = JSON.parse(JSON.stringify(this.mbCompSettings));
        const exportClipSettings = { ...this.clipSettings };
        const exportFxState = JSON.parse(JSON.stringify(this.fxState));
        const exportLimSettings = { ...this.limSettings };

        // Offline render chain — HARUS IDENTIK dengan live chain order
        // 0:Noise 1:EQ 2:SubBass 3:Transient 4:DynEQ 5:FX 6:Comp 7:MBC 8:Clip 9:Lim
        const offlineChain = [
            new NoiseReduction(offCtx, exportNoiseSettings),
            new ParametricEQ(offCtx, exportEqState),
            new SubBass808(offCtx, exportSubBassState),
            new TransientShaper(offCtx, exportTransientSettings),
            new DynamicEQ(offCtx, exportDynEqSettings),
            new FXChain(offCtx, exportFxState),
            new Compressor(offCtx, exportCompSettings),
            new MultibandCompressor(offCtx, exportMbCompSettings),
            new Clipper(offCtx, exportClipSettings),
            new Limiter(offCtx, exportLimSettings)
        ];

        // Inisialisasi worklet untuk offline chain agar efek diterapkan
        // SEMUA modul yang menggunakan AudioWorklet HARUS di-init di sini
        try {
            offlineChain[0].initWorklet(); // noise
            offlineChain[2].initWorklet(); // subBass808 ← WAJIB agar sub-bass masuk ke export
            offlineChain[3].initWorklet(); // transientShaper ← WAJIB agar transient masuk ke export
            offlineChain[4].initWorklet(); // dynEq
            offlineChain[5].initWorklet(); // fxChain ← WAJIB agar FX masuk ke export
            offlineChain[6].initWorklet(); // comp
            offlineChain[7].initWorklet(); // mbc
            offlineChain[8].initWorklet(); // clipper
            offlineChain[9].initWorklet(); // limiter
        } catch(e) {
            console.warn('[AudioEngine] ❌ initWorklet gagal di offline chain.', e);
        }

        // Pastikan modul yang NON-ACTIVE benar-benar di-bypass secara routing (bukan cuma parameternya) 
        // untuk menghemat CPU usage secara maksimal saat offline render.
        offlineChain.forEach(mod => {
            if (typeof mod.setBypass === 'function' && mod.state && mod.state.active !== undefined) {
                mod.setBypass(!mod.state.active);
            }
        });

        // Salin impulse response reverb dari live FXChain agar identik
        // (karena impulse menggunakan random noise, generate ulang = hasil beda)
        if (this.modules && this.modules.fx && this.modules.fx.convolver && this.modules.fx.convolver.buffer) {
            const liveImpulse = this.modules.fx.convolver.buffer;
            const offlineImpulse = offCtx.createBuffer(
                liveImpulse.numberOfChannels,
                liveImpulse.length,
                sr
            );
            for (let c = 0; c < liveImpulse.numberOfChannels; c++) {
                offlineImpulse.getChannelData(c).set(liveImpulse.getChannelData(c));
            }
            offlineChain[5].convolver.buffer = offlineImpulse;
        } else {
            // Fallback: generate baru jika live belum punya impulse
            offlineChain[5].updateReverbDecay(exportFxState.reverb.decay);
        }

        // Sambungkan chain: source → modul[0] → modul[1] → ... → destination
        let current = oSource;
        for (const mod of offlineChain) {
            current.connect(mod.input);
            current = mod.output;
        }
        current.connect(offCtx.destination);

        // Sinkronisasi Worklet: Beri waktu bagi semua postMessage parameter untuk tiba
        // di thread worklet sebelum OfflineAudioContext mulai memproses miliaran sampel dalam sekejap.
        await new Promise(resolve => setTimeout(resolve, 150));

        if (onProgress) onProgress(0.3);
        oSource.start(0);
        const rendered = await offCtx.startRendering();
        if (onProgress) onProgress(0.7);
        
        // P2: Hitung LUFS, LRA, dan True Peak dari full buffer setelah render selesai menggunakan lufs-web
        const channelData = [];
        for (let ch = 0; ch < rendered.numberOfChannels; ch++) {
            channelData.push(rendered.getChannelData(ch));
        }
        
        const loudnessResult = measure({
            sampleRate: rendered.sampleRate,
            channels: channelData
        });

        let tp = loudnessResult.truePeakDB;
        let lufs = loudnessResult.integratedLUFS;
        let lra = loudnessResult.lra; // LRA (Loudness Range) per EBU Tech 3342 / BS.1771

        // ============================================================
        // AUTO LUFS -14 NORMALIZATION (Delegated to FFmpeg Sidecar)
        // ============================================================
        // Linear gain manual dihentikan karena menyebabkan hard-clipping.
        // Proses LUFS -14 dengan True Peak Limiter akan ditangani sepenuhnya 
        // oleh FFmpeg di TauriBridge / app.js setelah ekspor WAV ini.
        if (this.autoLufsNormalize) {
            console.log(`[LUFS Norm] Mendelegasikan proses ke FFmpeg (Ekspor 24-bit PCM)`);
        }

        const wav = this._audioBufferToWav(rendered, 24);
        if (onProgress) onProgress(1.0);
        
        return { wav, stats: { tp, lufs, dr: lra } };
    }

    _audioBufferToWav(buf, bitDepth = 24) {
        const nc = buf.numberOfChannels, sr = buf.sampleRate;
        const bps = (bitDepth === 16 || bitDepth === 32) ? bitDepth : 24;
        let interleaved;
        if (nc === 1) { 
            interleaved = buf.getChannelData(0); 
        } else { 
            const l = buf.getChannelData(0), r = buf.getChannelData(1); 
            interleaved = new Float32Array(l.length * 2); 
            for (let i = 0; i < l.length; i++) { 
                interleaved[i * 2] = l[i]; 
                interleaved[i * 2 + 1] = r[i]; 
            } 
        }
        const bytesPerSample = bps / 8;
        const blockAlign = nc * bytesPerSample;
        const byteRate = sr * blockAlign;
        const dataSize = interleaved.length * bytesPerSample;
        const total = 44 + dataSize;
        const ab = new ArrayBuffer(total);
        const v = new DataView(ab);
        this._ws(v, 0, 'RIFF'); 
        v.setUint32(4, total - 8, true); 
        this._ws(v, 8, 'WAVE');
        this._ws(v, 12, 'fmt '); 
        v.setUint32(16, 16, true); 
        v.setUint16(20, bps === 32 ? 3 : 1, true); // Format 3 = IEEE Float, 1 = PCM
        v.setUint16(22, nc, true);
        v.setUint32(24, sr, true); 
        v.setUint32(28, byteRate, true); 
        v.setUint16(32, blockAlign, true); 
        v.setUint16(34, bps, true);
        this._ws(v, 36, 'data'); 
        v.setUint32(40, dataSize, true);
        let off = 44; 
        for (let i = 0; i < interleaved.length; i++) {
            if (bps === 32) {
                v.setFloat32(off, interleaved[i], true);
                off += 4;
            } else if (bps === 24) {
                const s = Math.max(-1, Math.min(1, interleaved[i]));
                const val = Math.round(s < 0 ? s * 0x800000 : s * 0x7FFFFF);
                v.setUint8(off, val & 0xFF);
                v.setUint8(off + 1, (val >> 8) & 0xFF);
                v.setUint8(off + 2, (val >> 16) & 0xFF);
                off += 3;
            } else {
                const s = Math.max(-1, Math.min(1, interleaved[i]));
                v.setInt16(off, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
                off += 2;
            }
        }
        return new Uint8Array(ab);
    }
    _ws(v,o,s){for(let i=0;i<s.length;i++)v.setUint8(o+i,s.charCodeAt(i));}

    destroy() { 
        this.stop(); 
        if(this.audioCtx&&this.audioCtx.state!=='closed')this.audioCtx.close(); 
        this.audioCtx=null; 
        if (this.audioElement.src && this.audioElement.src.startsWith('blob:')) {
            URL.revokeObjectURL(this.audioElement.src);
        }
        this.audioElement.removeAttribute('src'); 
    }
}


