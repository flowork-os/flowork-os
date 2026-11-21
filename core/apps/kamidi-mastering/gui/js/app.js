/**
 * app.js - UI Logic Controller
 * Menghubungkan DOM (Knob, Preset, Transport) dengan AudioEngine dan TauriBridge.
 * File ini BOLEH mengakses DOM, tapi TIDAK boleh memanggil Tauri API langsung.
 */

import { AudioEngine } from './engine/AudioEngine.js';
import { TauriBridge } from './bridge/TauriBridge.js';
import { PRESETS } from './presets.js';
import { SmartLogic } from './engine/SmartLogic.js';

// ============================================================
// SECURITY / ANTI-SPY
// ============================================================
// Disable right-click (context menu)
document.addEventListener('contextmenu', event => event.preventDefault());

// Disable DevTools shortcuts (F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U)
document.addEventListener('keydown', event => {
    if (
        event.key === 'F12' ||
        (event.ctrlKey && event.shiftKey && (event.key === 'I' || event.key === 'i' || event.key === 'J' || event.key === 'j' || event.key === 'C' || event.key === 'c')) ||
        (event.ctrlKey && (event.key === 'U' || event.key === 'u'))
    ) {
        event.preventDefault();
    }
});

// ============================================================
// INSTANCES
// ============================================================
const engine = new AudioEngine();
const smartLogic = new SmartLogic(engine);
const bridge = new TauriBridge();

// ============================================================
// PRESET DEFINITIONS
// ============================================================
let CUSTOM_PRESETS = {}; // Format: { "Preset Name": { path: "...", settings: {...} } }

// ============================================================
// DOM REFERENCES
// ============================================================
const $ = (id) => document.getElementById(id);

let DOM = {};
let spectrumCtx = null;
let masterWaveformCtx = null;
let eqCurveCtx = null;
let compCurveCtx = null;
let subbassWaveformCtx = null;
let animFrameId = null;
let loadedFileName = 'NO TRACK LOADED';

// Batch mastering state
let trackQueue = [];       // [{path, name, _browserIndex?}]
let isBatchMode = false;
let activeQueueIndex = 0;
let isLoopMode = false;
let isRandomMode = false;
let loadRequestId = 0; // Counter to cancel stale load requests
let currentAudioUrl = null;

function initDOM() {
    DOM = {
        btnPlay: $('btn-play'),
        btnPrev: $('btn-prev'),
        btnNext: $('btn-next'),
        btnLoop: $('btn-loop'),
        btnRandom: $('btn-random'),
        btnClear: $('btn-clear'),
        btnPlaylist: $('btn-playlist'),
        playlistSection: $('playlist-section'),
        playlistContainer: $('playlist-container'),
        playlistCount: $('playlist-count'),
        playlistResizeHandle: $('playlist-resize-handle'),
        playIcon: $('btn-play')?.querySelector('.play-icon'),
        timeCurrent: $('time-current'),
        timeTotal: $('time-total'),
        seekBar: $('seek-bar'),
        trackTitle: $('track-title'),
        spectrumCanvas: $('spectrum-canvas'),
        masterWaveformCanvas: $('master-waveform-canvas'),
        subbassWaveformCanvas: $('subbass-waveform-canvas'),
        meterFill: $('meter-fill'),
        grMeter: $('gr-meter'),
        grText: $('gr-text'),
        presetSelector: $('preset-selector'),
        presetDesc: $('preset-desc'),
        btnLoad: $('btn-load'),
        btnExport: $('btn-export'),
        smoothingSlider: $('smoothing-slider'),
        smoothingValue: $('smoothing-value'),
        eqCurveCanvas: $('eq-curve-canvas'),
        compCurveCanvas: $('comp-curve-canvas'),
        exportModal: $('export-modal'),
        exportProgress: $('export-progress'),
        exportStatus: $('export-status'),
        toast: $('toast'),
        badgeMastered: $('badge-mastered'),
        badgeChannels: $('badge-channels'),
        
        // Preset Persistent UI
        btnSavePreset: $('btn-save-preset'),
        btnDeletePreset: $('btn-delete-preset'),
        optgroupCustom: $('optgroup-custom'),
        presetFolderDisplay: $('pm-preset-folder-display'),
        btnChangeFolder: $('btn-pm-change-folder'),
        btnUploadPreset: $('btn-pm-upload-preset'),

        
        // Custom Prompt Modal
        promptModal: $('prompt-modal'),
        promptInput: $('prompt-input'),
        btnPromptCancel: $('btn-prompt-cancel'),
        btnPromptSave: $('btn-prompt-save'),
        
        // Custom Confirm Modal
        confirmModal: $('confirm-modal'),
        confirmMessage: $('confirm-message'),
        btnConfirmOk: $('btn-confirm-ok'),
        btnConfirmCancel: $('btn-confirm-cancel'),
        
        // Custom Alert Modal
        alertModal: $('alert-modal'),
        alertTitle: $('alert-title'),
        alertMessage: $('alert-message'),
        btnAlertOk: $('btn-alert-ok')
    };
}

// ============================================================
// FADER SYSTEM
// ============================================================
function setupFader(id, callback, formatValue, defaultVal) {
    const el = $(id);
    if (!el) return;
    const container = el.closest('.fader-container');
    const valDisplay = container?.querySelector('.fader-value');

    // Mencegah double event listener
    if (el.hasAttribute('data-initialized')) return;
    el.setAttribute('data-initialized', 'true');

    const min = el.hasAttribute('min') ? parseFloat(el.min) : 0;
    const max = el.hasAttribute('max') ? parseFloat(el.max) : 100;

    const updateVisuals = (val) => {
        if (valDisplay) valDisplay.innerText = formatValue(val);
        callback(val);
    };

    // Initialize with current value
    updateVisuals(parseFloat(el.value));

    // Setup custom pointer events on the wrapper for perfect vertical dragging
    const wrapper = el.parentElement;

    let startY = 0;
    let startVal = 0;

    el.addEventListener('pointerdown', (e) => {
        el.focus();
        e.preventDefault();
        
        startY = e.clientY;
        startVal = parseFloat(el.value);
        const rect = wrapper.getBoundingClientRect();
        const range = max - min;
        let lastCallTime = 0;
        
        const onMove = (evt) => {
            // Throttle: max 30 updates/detik untuk mencegah parameter bombardment
            const now = Date.now();
            if (now - lastCallTime < 33) return;
            lastCallTime = now;
            
            const deltaY = evt.clientY - startY;
            // Fader vertikal: geser ke atas (deltaY negatif) berarti nilai bertambah
            const deltaPct = -(deltaY / rect.height);
            const step = parseFloat(el.step) || 1;
            
            let newVal = startVal + (deltaPct * range);
            newVal = Math.round(newVal / step) * step;
            newVal = Math.max(min, Math.min(max, newVal));
            el.value = newVal;
            updateVisuals(newVal);
        };
        
        const onUp = () => {
            document.removeEventListener('pointermove', onMove);
            document.removeEventListener('pointerup', onUp);
        };
        
        document.addEventListener('pointermove', onMove);
        document.addEventListener('pointerup', onUp);
    });

    el.addEventListener('input', () => {
        updateVisuals(parseFloat(el.value));
    });

    el.addEventListener('dblclick', () => {
        const resetVal = defaultVal !== undefined ? defaultVal : (min + max) / 2;
        el.value = resetVal;
        updateVisuals(resetVal);
    });

    // Expose for preset system — dengan support visual-only mode
    el._updateValue = (newVal, visualOnly = false) => { 
        el.value = newVal;
        if (visualOnly) {
            // Hanya update display, JANGAN trigger engine callback
            if (valDisplay) valDisplay.innerText = formatValue(parseFloat(newVal));
        } else {
            updateVisuals(parseFloat(newVal));
        }
    };
}

// ============================================================
// INITIALIZE FADERS
// ============================================================
function initFaders() {
    // EQ
    setupFader('fader-eq-hpf', v => { engine.setEQHpfFreq(v); drawEQCurve(); }, v => `${v.toFixed(0)}Hz`, PRESETS.default.hpf);
    setupFader('fader-eq-low', v => { engine.setEQLow(v); drawEQCurve(); }, v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, PRESETS.default.low);
    setupFader('fader-eq-low-freq', v => { engine.setEQLowFreq(v); drawEQCurve(); }, v => `${v.toFixed(0)}Hz`, PRESETS.default.lFreq);
    setupFader('fader-eq-mid', v => { engine.setEQMid(v); drawEQCurve(); }, v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, PRESETS.default.mid);
    setupFader('fader-eq-mid-freq', v => { engine.setEQMidFreq(v); drawEQCurve(); }, v => `${v.toFixed(0)}Hz`, PRESETS.default.mFreq);
    setupFader('fader-eq-mid-q', v => { engine.setEQMidQ(v); drawEQCurve(); }, v => v.toFixed(1), PRESETS.default.mQ);
    setupFader('fader-eq-high', v => { smartLogic.onEQHighChange(v); drawEQCurve(); }, v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, PRESETS.default.high);
    setupFader('fader-eq-high-freq', v => { engine.setEQHighFreq(v); drawEQCurve(); }, v => `${v.toFixed(0)}Hz`, PRESETS.default.hFreq);

    // Compressor
    setupFader('fader-comp-thresh', v => { engine.setCompThreshold(v); drawCompCurve(); }, v => `${v.toFixed(1)}`, PRESETS.default.cThresh);
    setupFader('fader-comp-ratio', v => { engine.setCompRatio(v); drawCompCurve(); }, v => `${v.toFixed(1)}:1`, PRESETS.default.cRatio);
    setupFader('fader-comp-knee', v => { engine.setCompKnee(v); drawCompCurve(); }, v => `${v.toFixed(1)}`, PRESETS.default.cKnee);
    setupFader('fader-comp-attack', v => engine.setCompAttack(v / 1000), v => `${v.toFixed(0)}ms`, PRESETS.default.cAtt * 1000); // internal in seconds
    setupFader('fader-comp-release', v => engine.setCompRelease(v / 1000), v => `${v.toFixed(0)}ms`, PRESETS.default.cRel * 1000); // internal in seconds
    setupFader('fader-comp-makeup', v => { engine.setMakeupGain(v); drawCompCurve(); }, v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, PRESETS.default.mkp);
    setupFader('fader-comp-mix', v => engine.setCompMix(v/100), v => `${Math.round(v)}%`, PRESETS.default.cMix !== undefined ? PRESETS.default.cMix * 100 : 100);

    // Multiband Compressor
    setupFader('fader-mbc-low-thresh', v => engine.setMBCompLowThreshold(v), v => `${v.toFixed(1)}`, -24);
    setupFader('fader-mbc-low-ratio', v => engine.setMBCompLowRatio(v), v => `${v.toFixed(1)}:1`, 2);
    setupFader('fader-mbc-low-attack', v => engine.setMBCompLowAttack(v / 1000), v => `${v.toFixed(0)}ms`, 30);
    setupFader('fader-mbc-low-release', v => engine.setMBCompLowRelease(v / 1000), v => `${v.toFixed(0)}ms`, 200);
    setupFader('fader-mbc-low-makeup', v => engine.setMBCompLowMakeup(v), v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, 0);

    setupFader('fader-mbc-mid-thresh', v => engine.setMBCompMidThreshold(v), v => `${v.toFixed(1)}`, -24);
    setupFader('fader-mbc-mid-ratio', v => engine.setMBCompMidRatio(v), v => `${v.toFixed(1)}:1`, 2);
    setupFader('fader-mbc-mid-attack', v => engine.setMBCompMidAttack(v / 1000), v => `${v.toFixed(0)}ms`, 20);
    setupFader('fader-mbc-mid-release', v => engine.setMBCompMidRelease(v / 1000), v => `${v.toFixed(0)}ms`, 150);
    setupFader('fader-mbc-mid-makeup', v => engine.setMBCompMidMakeup(v), v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, 0);

    setupFader('fader-mbc-high-thresh', v => engine.setMBCompHighThreshold(v), v => `${v.toFixed(1)}`, -24);
    setupFader('fader-mbc-high-ratio', v => engine.setMBCompHighRatio(v), v => `${v.toFixed(1)}:1`, 2);
    setupFader('fader-mbc-high-attack', v => engine.setMBCompHighAttack(v / 1000), v => `${v.toFixed(0)}ms`, 10);
    setupFader('fader-mbc-high-release', v => engine.setMBCompHighRelease(v / 1000), v => `${v.toFixed(0)}ms`, 100);
    setupFader('fader-mbc-high-makeup', v => engine.setMBCompHighMakeup(v), v => `${v > 0 ? '+' : ''}${v.toFixed(1)}`, 0);

    setupFader('fader-mbc-low-knee', v => engine.setMBCompLowKnee(v), v => `${v.toFixed(1)}`, 6);
    setupFader('fader-mbc-low-mix', v => engine.setMBCompLowMix(v/100), v => `${Math.round(v)}%`, 100);
    setupFader('fader-mbc-low-width', v => engine.setMBCompLowWidth(v/100), v => `${Math.round(v)}%`, 0);

    setupFader('fader-mbc-mid-knee', v => engine.setMBCompMidKnee(v), v => `${v.toFixed(1)}`, 6);
    setupFader('fader-mbc-mid-mix', v => engine.setMBCompMidMix(v/100), v => `${Math.round(v)}%`, 100);
    setupFader('fader-mbc-mid-width', v => engine.setMBCompMidWidth(v/100), v => `${Math.round(v)}%`, 100);

    setupFader('fader-mbc-high-knee', v => engine.setMBCompHighKnee(v), v => `${v.toFixed(1)}`, 6);
    setupFader('fader-mbc-high-mix', v => engine.setMBCompHighMix(v/100), v => `${Math.round(v)}%`, 100);
    setupFader('fader-mbc-high-width', v => engine.setMBCompHighWidth(v/100), v => `${Math.round(v)}%`, 120);

    setupFader('fader-mbc-xover-low', v => { engine.setMBCompLowMidFreq(v); }, v => `${v.toFixed(0)}Hz`, 250);
    setupFader('fader-mbc-xover-high', v => { engine.setMBCompMidHighFreq(v); }, v => `${v.toFixed(0)}Hz`, 4000);

    // Clipper
    setupFader('fader-clip-thresh', v => engine.setClipperThreshold(v), v => `${v.toFixed(1)}`, PRESETS.default.clip);

    // Limiter
    const defLimThresh = PRESETS.default.lThresh !== undefined ? PRESETS.default.lThresh : -1.0;
    setupFader('fader-lim-thresh', v => engine.setLimiterThreshold(v), v => `${v.toFixed(1)}`, defLimThresh);
    setupFader('fader-lim-ceiling', v => engine.setLimiterCeiling(v), v => `${v.toFixed(1)}`, PRESETS.default.lCeil);
    setupFader('fader-lim-release', v => engine.setLimiterRelease(v / 1000), v => `${v.toFixed(0)}ms`, PRESETS.default.lRel * 1000);



    // Noise Reduction
    setupFader('fader-nr-thresh', v => engine.setNoiseReductionThreshold(v), v => `${v.toFixed(0)}dB`, -60);
    setupFader('fader-nr-amount', v => engine.setNoiseReductionAmount(v), v => `${Math.round(v * 100)}%`, 0.5);

    // Transient Shaper
    setupFader('fader-ts-attack', v => engine.setTransientAttack(v), v => `${Math.round(v)}%`, 0);
    setupFader('fader-ts-sustain', v => engine.setTransientSustain(v), v => `${Math.round(v)}%`, 0);

    // 808 Sub Bass
    setupFader('fader-sb-freq', v => engine.setSubBassFreq(v), v => `${Math.round(v)}Hz`, 50);
    setupFader('fader-sb-drive', v => smartLogic.onSubBassDriveChange(v), v => `${Math.round(v)}%`, 0);
    setupFader('fader-sb-sub', v => engine.setSubBassSub(v), v => `+${(v / 100 * 12).toFixed(1)}dB`, 20);
    setupFader('fader-sb-clean', v => engine.setSubBassClean(v), v => `${v > 0 ? '-' : ''}${(v / 100 * 10).toFixed(1)}dB`, 40);
    setupFader('fader-sb-mix', v => engine.setSubBassMix(v), v => `${Math.round(v)}%`, 50);

    // Dynamic EQ
    setupFader('fader-deq-low-freq', v => engine.setDynEqFreq(0, v), v => `${v.toFixed(0)}Hz`, 100);
    setupFader('fader-deq-low-thresh', v => engine.setDynEqThresh(0, v), v => `${v.toFixed(1)}dB`, -8);
    setupFader('fader-deq-lmid-freq', v => engine.setDynEqFreq(1, v), v => `${v.toFixed(0)}Hz`, 400);
    setupFader('fader-deq-lmid-thresh', v => engine.setDynEqThresh(1, v), v => `${v.toFixed(1)}dB`, -8);
    setupFader('fader-deq-hmid-freq', v => engine.setDynEqFreq(2, v), v => `${v.toFixed(0)}Hz`, 3000);
    setupFader('fader-deq-hmid-thresh', v => engine.setDynEqThresh(2, v), v => `${v.toFixed(1)}dB`, -8);
    setupFader('fader-deq-high-freq', v => engine.setDynEqFreq(3, v), v => `${v.toFixed(0)}Hz`, 8000);
    setupFader('fader-deq-high-thresh', v => engine.setDynEqThresh(3, v), v => `${v.toFixed(1)}dB`, -8);

    // Generate scale labels for all faders
    generateFaderScales();
}

// ============================================================
// FADER SCALE LABELS
// ============================================================
function generateFaderScales() {
try {
    const wrappers = document.querySelectorAll('.fader-track-wrapper');
    wrappers.forEach(wrapper => {
        const input = wrapper.querySelector('.fader-vertical');
        if (!input) return;

        // Remove existing scales
        wrapper.querySelectorAll('.fader-scale').forEach(el => el.remove());

        const min = parseFloat(input.min);
        const max = parseFloat(input.max);
        const range = max - min;

        // Determine nice tick count (4-6 labels)
        let tickCount = 5;
        const steps = [0.1, 0.2, 0.25, 0.5, 1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000];
        let stepSize = 1;
        for (const s of steps) {
            if (range / s >= 3 && range / s <= 7) { stepSize = s; break; }
        }

        // Generate tick values
        const ticks = [];
        let start = Math.ceil(min / stepSize) * stepSize;
        for (let v = start; v <= max; v += stepSize) {
            ticks.push(v);
        }
        // Always include min and max
        if (ticks[0] !== min) ticks.unshift(min);
        if (ticks[ticks.length - 1] !== max) ticks.push(max);

        // Create scale container (left side)
        const scaleLeft = document.createElement('div');
        scaleLeft.className = 'fader-scale fader-scale-left';

        // Create scale container (right side)
        const scaleRight = document.createElement('div');
        scaleRight.className = 'fader-scale fader-scale-right';

        ticks.forEach(val => {
            const pct = ((val - min) / range) * 100;
            // Fader goes bottom=min, top=max, so invert position
            const topPct = 100 - pct;

            let tickText = Math.round(val) === val ? val : val.toFixed(1);
            if (input.id === 'fader-sb-sub') {
                const dbVal = (val / 100) * 12;
                tickText = (dbVal > 0 ? '+' : '') + Math.round(dbVal);
                if (Math.round(dbVal) === 0) tickText = "0";
            } else if (input.id === 'fader-sb-clean') {
                const dbVal = -((val / 100) * 10);
                tickText = Math.round(dbVal).toString();
                if (Math.round(dbVal) === 0) tickText = "0";
            }

            const labelL = document.createElement('span');
            labelL.className = 'fader-scale-tick';
            labelL.style.top = `${topPct}%`;
            labelL.textContent = tickText;
            scaleLeft.appendChild(labelL);

            const labelR = document.createElement('span');
            labelR.className = 'fader-scale-tick';
            labelR.style.top = `${topPct}%`;
            labelR.textContent = tickText;
            scaleRight.appendChild(labelR);
        });

        wrapper.appendChild(scaleLeft);
        wrapper.appendChild(scaleRight);
    });
} catch (err) {
    alert("Error generateFaderScales: " + err.message);
}
}

// ============================================================
// MODULE TOGGLES (Bypass)
// ============================================================
function initToggles() {
    // EQ Bypass (Whole module)
    const btnEq = $('btn-eq-bypass');
    if (btnEq) btnEq.addEventListener('click', () => {
        const isActive = btnEq.classList.contains('active');
        if (isActive) {
            btnEq.classList.remove('active'); btnEq.classList.add('bypassed'); btnEq.innerText = 'NON-ACTIVE';
            engine.toggleEQ('low', false); engine.toggleEQ('mid', false); engine.toggleEQ('high', false);
        } else {
            btnEq.classList.add('active'); btnEq.classList.remove('bypassed'); btnEq.innerText = 'ACTIVE';
            engine.toggleEQ('low', true); engine.toggleEQ('mid', true); engine.toggleEQ('high', true);
        }
        drawEQCurve();
    });
    
    // Compressor Bypass
    const btnComp = $('btn-comp-bypass');
    if (btnComp) btnComp.addEventListener('click', () => {
        const isActive = btnComp.classList.contains('active');
        if (isActive) {
            btnComp.classList.remove('active'); btnComp.classList.add('bypassed'); btnComp.innerText = 'NON-ACTIVE';
            engine.toggleCompressor(false);
        } else {
            btnComp.classList.add('active'); btnComp.classList.remove('bypassed'); btnComp.innerText = 'ACTIVE';
            engine.toggleCompressor(true);
        }
        drawCompCurve();
    });


    // Clipper Bypass
    const btnClip = $('btn-clip-bypass');
    if (btnClip) btnClip.addEventListener('click', () => {
        const isActive = btnClip.classList.contains('active');
        if (isActive) {
            btnClip.classList.remove('active'); btnClip.classList.add('bypassed'); btnClip.innerText = 'NON-ACTIVE';
            engine.toggleClipper(false);
        } else {
            btnClip.classList.add('active'); btnClip.classList.remove('bypassed'); btnClip.innerText = 'ACTIVE';
            engine.toggleClipper(true);
        }
    });
    // Multiband Comp Bypass
    const btnMBC = $('btn-mbcomp-bypass');
    if (btnMBC) btnMBC.addEventListener('click', () => {
        const isActive = btnMBC.classList.contains('active');
        if (isActive) {
            btnMBC.classList.remove('active'); btnMBC.classList.add('bypassed'); btnMBC.innerText = 'NON-ACTIVE';
            engine.toggleMBComp(false);
        } else {
            btnMBC.classList.add('active'); btnMBC.classList.remove('bypassed'); btnMBC.innerText = 'ACTIVE';
            engine.toggleMBComp(true);
        }
    });

    // Multiband Imager Bypass (now integrated into MBComp)
    const btnMBI = $('btn-mbimager-bypass');
    if (btnMBI) btnMBI.addEventListener('click', () => {
        const isActive = btnMBI.classList.contains('active');
        if (isActive) {
            btnMBI.classList.remove('active'); btnMBI.classList.add('bypassed'); btnMBI.innerText = 'NON-ACTIVE';
            engine.toggleMBComp(false);
        } else {
            btnMBI.classList.add('active'); btnMBI.classList.remove('bypassed'); btnMBI.innerText = 'ACTIVE';
            engine.toggleMBComp(true);
        }
    });

    // Transient Shaper Bypass
    const btnTS = $('btn-ts-bypass');
    if (btnTS) btnTS.addEventListener('click', () => {
        const isActive = btnTS.classList.contains('active');
        if (isActive) {
            btnTS.classList.remove('active'); btnTS.classList.add('bypassed'); btnTS.innerText = 'NON-ACTIVE';
            engine.toggleTransientShaper(false);
        } else {
            btnTS.classList.add('active'); btnTS.classList.remove('bypassed'); btnTS.innerText = 'ACTIVE';
            engine.toggleTransientShaper(true);
        }
    });

    // Limiter Bypass
    const btnLim = $('btn-lim-bypass');
    if (btnLim) btnLim.addEventListener('click', () => {
        const isActive = btnLim.classList.contains('active');
        if (isActive) {
            btnLim.classList.remove('active'); btnLim.classList.add('bypassed'); btnLim.innerText = 'NON-ACTIVE';
            engine.toggleLimiter(false);
        } else {
            btnLim.classList.add('active'); btnLim.classList.remove('bypassed'); btnLim.innerText = 'ACTIVE';
            engine.toggleLimiter(true);
        }
    });

    // 808 Sub Bass Bypass
    const btnSubBass = $('btn-subbass-bypass');
    if (btnSubBass) btnSubBass.addEventListener('click', () => {
        const isActive = btnSubBass.classList.contains('active');
        if (isActive) {
            btnSubBass.classList.remove('active'); btnSubBass.classList.add('bypassed'); btnSubBass.innerText = 'NON-ACTIVE';
            engine.toggleSubBass(false);
        } else {
            btnSubBass.classList.add('active'); btnSubBass.classList.remove('bypassed'); btnSubBass.innerText = 'ACTIVE';
            engine.toggleSubBass(true);
        }
    });
}

// ============================================================
// PRESET SYSTEM (Persistent)
// ============================================================
const LS_MASTER_FOLDER_KEY = 'kamidi_master_preset_folder';

async function getDefaultMasterFolder() {
    let saved = localStorage.getItem(LS_MASTER_FOLDER_KEY) || '';
    if (saved) return saved;

    if (window.__TAURI__?.path?.appDataDir) {
        try {
            let appData = await window.__TAURI__.path.appDataDir();
            appData = appData.replace(/[\\/]+$/, ''); // Hapus slash di akhir
            
            // appData biasanya: C:\Users\Name\AppData\Roaming\com.tauri.kamidi-mastering
            // Kita mundur DUA folder (lewati com.tauri... dan Roaming) agar sampai di AppData
            const parts = appData.split(/[\\/]/);
            parts.pop(); // Buang folder bawaan aplikasi (com.tauri...)
            parts.pop(); // Buang folder Roaming
            
            // Hasil: C:\Users\Name\AppData\Preset\KamidiStudioProv5
            const presetDir = parts.join('\\') + '\\Preset\\KamidiStudioProv5';
            
            localStorage.setItem(LS_MASTER_FOLDER_KEY, presetDir);
            return presetDir;
        } catch (e) { console.error('[Presets] Failed to resolve default folder:', e); }
    }
    return '';
}

async function reloadMasteringPresets() {
    try {
        const folder = await getDefaultMasterFolder();
        if (DOM.presetFolderDisplay) DOM.presetFolderDisplay.value = folder;
        
        const files = await bridge.getPresetFiles(folder);
        CUSTOM_PRESETS = {};
        
        if (DOM.optgroupCustom) DOM.optgroupCustom.innerHTML = '';
        
        for (const file of files) {
            // We store the path so we can load/delete it later
            CUSTOM_PRESETS[file.name] = { path: file.path };
            
            if (DOM.optgroupCustom) {
                const opt = document.createElement('option');
                opt.value = `CUSTOM:${file.name}`;
                opt.innerText = file.name;
                DOM.optgroupCustom.appendChild(opt);
            }
        }
        
        console.log(`[Presets] Loaded ${files.length} custom presets from ${folder}`);
    } catch (e) {
        console.warn('[Presets] Failed to reload custom presets:', e);
    }
}

async function initPresets() {
    if (!DOM.presetSelector) return;

    // CRITICAL: Change listener HARUS terpasang PERTAMA
    DOM.presetSelector.addEventListener('change', async (e) => {
        const val = e.target.value;
        let p = null;

        try {
            if (val.startsWith('CUSTOM:')) {
                const name = val.replace('CUSTOM:', '');
                const presetData = CUSTOM_PRESETS[name];
                if (presetData && presetData.path) {
                    p = await bridge.loadPresetFile(presetData.path);
                }
            } else {
                p = PRESETS[val];
            }
        } catch (err) {
            console.error('[Preset] Gagal memuat preset:', err);
        }

        if (!p) {
            console.warn('[Preset] Preset ' + val + ' tidak ditemukan atau gagal dimuat.');
            return;
        }
        
        console.log('[Preset] Menerapkan preset: ' + val, p);

        // Update Delete button state (Only custom presets can be deleted)
        if (DOM.btnDeletePreset) {
            DOM.btnDeletePreset.disabled = !val.startsWith('CUSTOM:');
            DOM.btnDeletePreset.style.cursor = val.startsWith('CUSTOM:') ? 'pointer' : 'default';
        }

        // Description
        if (DOM.presetDesc) DOM.presetDesc.innerText = p.desc || 'Custom Preset: ' + val.replace('CUSTOM:', '');

        // Update engine
        try {
            engine.applyPreset(p);
            smartLogic.recalculateAll(); // Trigger Smart Logic recalculation for preset
        } catch (err) {
            console.error('[Preset] applyPreset error:', err);
            alert('Error applyPreset: ' + err.message);
        }

        // Update fader visuals
        const fadersMap = {
            'fader-eq-hpf': p.hpf !== undefined ? p.hpf : 20,
            'fader-eq-low': p.low !== undefined ? p.low : 0,
            'fader-eq-low-freq': p.lFreq !== undefined ? p.lFreq : 250,
            'fader-eq-mid': p.mid !== undefined ? p.mid : 0,
            'fader-eq-mid-freq': p.mFreq !== undefined ? p.mFreq : 1000,
            'fader-eq-mid-q': p.mQ !== undefined ? p.mQ : 1.0,
            'fader-eq-high': p.high !== undefined ? p.high : 0,
            'fader-eq-high-freq': p.hFreq !== undefined ? p.hFreq : 4000,
            'fader-comp-thresh': p.cThresh !== undefined ? p.cThresh : -24,
            'fader-comp-ratio': p.cRatio !== undefined ? p.cRatio : 4,
            'fader-comp-knee': p.cKnee !== undefined ? p.cKnee : 6,
            'fader-comp-attack': p.cAtt !== undefined ? p.cAtt * 1000 : 50,
            'fader-comp-release': p.cRel !== undefined ? p.cRel * 1000 : 250,
            'fader-comp-makeup': p.mkp !== undefined ? p.mkp : 0,
            'fader-comp-mix': p.cMix !== undefined ? p.cMix * 100 : 100,
            
            'fader-mbc-low-thresh': p.mbcLowThresh !== undefined ? p.mbcLowThresh : -24,
            'fader-mbc-low-ratio': p.mbcLowRatio !== undefined ? p.mbcLowRatio : 2,
            'fader-mbc-low-attack': p.mbcLowAtt !== undefined ? p.mbcLowAtt * 1000 : 30,
            'fader-mbc-low-release': p.mbcLowRel !== undefined ? p.mbcLowRel * 1000 : 200,
            'fader-mbc-low-makeup': p.mbcLowMkp !== undefined ? p.mbcLowMkp : 0,
            'fader-mbc-low-knee': p.mbcLowKnee !== undefined ? p.mbcLowKnee : 6,
            'fader-mbc-low-mix': p.mbcLowMix !== undefined ? p.mbcLowMix * 100 : 100,
            'fader-mbc-low-width': p.mbcLowWidth !== undefined ? p.mbcLowWidth * 100 : 0,
            
            'fader-mbc-mid-thresh': p.mbcMidThresh !== undefined ? p.mbcMidThresh : -24,
            'fader-mbc-mid-ratio': p.mbcMidRatio !== undefined ? p.mbcMidRatio : 2,
            'fader-mbc-mid-knee': p.mbcMidKnee !== undefined ? p.mbcMidKnee : 6,
            'fader-mbc-mid-attack': p.mbcMidAtt !== undefined ? p.mbcMidAtt * 1000 : 20,
            'fader-mbc-mid-release': p.mbcMidRel !== undefined ? p.mbcMidRel * 1000 : 150,
            'fader-mbc-mid-makeup': p.mbcMidMkp !== undefined ? p.mbcMidMkp : 0,
            'fader-mbc-mid-mix': p.mbcMidMix !== undefined ? p.mbcMidMix * 100 : 100,
            'fader-mbc-mid-width': p.mbcMidWidth !== undefined ? p.mbcMidWidth * 100 : 100,
            
            'fader-mbc-high-thresh': p.mbcHighThresh !== undefined ? p.mbcHighThresh : -24,
            'fader-mbc-high-ratio': p.mbcHighRatio !== undefined ? p.mbcHighRatio : 2,
            'fader-mbc-high-knee': p.mbcHighKnee !== undefined ? p.mbcHighKnee : 6,
            'fader-mbc-high-attack': p.mbcHighAtt !== undefined ? p.mbcHighAtt * 1000 : 10,
            'fader-mbc-high-release': p.mbcHighRel !== undefined ? p.mbcHighRel * 1000 : 100,
            'fader-mbc-high-makeup': p.mbcHighMkp !== undefined ? p.mbcHighMkp : 0,
            'fader-mbc-high-mix': p.mbcHighMix !== undefined ? p.mbcHighMix * 100 : 100,
            'fader-mbc-high-width': p.mbcHighWidth !== undefined ? p.mbcHighWidth * 100 : 120,
            
            'fader-mbc-xover-low': p.mbcXoverLow !== undefined ? p.mbcXoverLow : 250,
            'fader-mbc-xover-high': p.mbcXoverHigh !== undefined ? p.mbcXoverHigh : 4000,
            
            // Noise Reduction
            'fader-nr-thresh': p.nrThresh !== undefined ? p.nrThresh : -60,
            'fader-nr-amount': p.nrAmount !== undefined ? p.nrAmount : 0.5,
            
            // Transient Shaper (Preset bawaan bernilai desimal, preset custom bernilai persentase bulat)
            'fader-ts-attack': p.tsAtt !== undefined ? (p.tsAtt > -1 && p.tsAtt < 1 ? p.tsAtt * 100 : p.tsAtt) : 0,
            'fader-ts-sustain': p.tsSus !== undefined ? (p.tsSus > -1 && p.tsSus < 1 ? p.tsSus * 100 : p.tsSus) : 0,
            
            // Dynamic EQ
            'fader-deq-low-freq': p.dynEq && p.dynEq[0] ? p.dynEq[0].freq : 100,
            'fader-deq-low-thresh': p.dynEq && p.dynEq[0] ? p.dynEq[0].thresh : -20,
            'fader-deq-lmid-freq': p.dynEq && p.dynEq[1] ? p.dynEq[1].freq : 500,
            'fader-deq-lmid-thresh': p.dynEq && p.dynEq[1] ? p.dynEq[1].thresh : -20,
            'fader-deq-hmid-freq': p.dynEq && p.dynEq[2] ? p.dynEq[2].freq : 2000,
            'fader-deq-hmid-thresh': p.dynEq && p.dynEq[2] ? p.dynEq[2].thresh : -20,
            'fader-deq-high-freq': p.dynEq && p.dynEq[3] ? p.dynEq[3].freq : 8000,
            'fader-deq-high-thresh': p.dynEq && p.dynEq[3] ? p.dynEq[3].thresh : -20,
            
            'fader-clip-thresh': p.clip !== undefined ? p.clip : 0,
            'fader-lim-ceiling': p.lCeil !== undefined ? p.lCeil : -1.5,
            'fader-lim-thresh': p.lThresh !== undefined ? p.lThresh : -1.0,
            'fader-lim-release': p.lRel !== undefined ? p.lRel * 1000 : 250,
            
            // 808 Sub Bass
            'fader-sb-freq': p.subBass && p.subBass.freq !== undefined ? p.subBass.freq : 50,
            'fader-sb-drive': p.subBass && p.subBass.drive !== undefined ? p.subBass.drive : 30,
            'fader-sb-sub': p.subBass && p.subBass.sub !== undefined ? p.subBass.sub : 50,
            'fader-sb-clean': p.subBass && p.subBass.clean !== undefined ? p.subBass.clean : 40,
            'fader-sb-mix': p.subBass && p.subBass.mix !== undefined ? p.subBass.mix : 60
        };

        try {
            for (const [id, value] of Object.entries(fadersMap)) {
                const el = $(id);
                if (value === undefined || !el) {
                    console.warn(`[Preset] Fader '${id}' tidak ditemukan atau value undefined.`);
                    continue;
                }
                // Clamp value ke range slider agar slider mau bergerak
                const min = parseFloat(el.min);
                const max = parseFloat(el.max);
                const clamped = Math.max(min, Math.min(max, value));
                if (clamped !== value) {
                    console.warn(`[Preset] Fader '${id}': value ${value} di-clamp ke ${clamped} (range: ${min}-${max})`);
                }
                if (typeof el._updateValue === 'function') {
                    el._updateValue(clamped, true); // visual-only: jangan kirim ke engine (sudah di-set oleh applyPreset)
                } else {
                    // Fallback jika _updateValue belum terpasang
                    console.warn(`[Preset] Fader '${id}' tidak punya _updateValue, fallback ke el.value`);
                    el.value = clamped;
                }
            }
        } catch (err) {
            console.error('[Preset] fadersMap error:', err);
            alert('Error fadersMap: ' + err.message);
        }

        // Update FX visuals from engine's resolved state
        const resolvedFxState = engine.getFXState();
        const formatRules = {
            'fx-delay-time': v => `${v.toFixed(2)}s`,
            'fx-delay-feedback': v => `${Math.round(v*100)}%`,
            'fx-delay-mix': v => `${Math.round(v*100)}%`,
            'fx-reverb-decay': v => `${v.toFixed(1)}s`,
            'fx-reverb-mix': v => `${Math.round(v*100)}%`,
            'fx-widener-width': v => `${Math.round(v*100)}%`,
            'fx-sat-drive': v => `${Math.round(v*100)}%`,
            'fx-sat-mix': v => `${Math.round(v*100)}%`,

            'fx-chorus-rate': v => `${v.toFixed(1)}Hz`,
            'fx-chorus-depth': v => `${Math.round(v*1000)}ms`,
            'fx-chorus-mix': v => `${Math.round(v*100)}%`
        };

        const applyFXUI = (fxName, stateObj) => {
            // Update toggles
            const toggle = $(`fx-toggle-${fxName}`);
            const tab = $(`fx-tab-${fxName}`);
            const panel = $(`fx-panel-${fxName}`);
            
            if (toggle && tab && panel) {
                if (stateObj.active) {
                    toggle.classList.add('on');
                    tab.classList.add('fx-on');
                    panel.classList.remove('disabled');
                } else {
                    toggle.classList.remove('on');
                    tab.classList.remove('fx-on');
                    panel.classList.add('disabled');
                }
            }

            // Update sliders
            for (const key of Object.keys(stateObj)) {
                if (key === 'active') continue;
                
                // Specific mapping since saturation uses 'fx-sat-drive' etc.
                let inputId = `fx-${fxName}-${key}`;
                if (fxName === 'saturation' && key === 'drive') inputId = 'fx-sat-drive';
                if (fxName === 'saturation' && key === 'mix') inputId = 'fx-sat-mix';

                const slider = $(inputId);
                if (slider) {
                    slider.value = stateObj[key];
                    const valEl = $(`${inputId}-val`);
                    if (valEl && formatRules[inputId]) {
                        valEl.innerText = formatRules[inputId](stateObj[key]);
                    }
                }
            }
        };

        for (const fxName of Object.keys(resolvedFxState)) {
            applyFXUI(fxName, resolvedFxState[fxName]);
        }

        // Sync bypass buttons
        const syncBypassBtn = (id, isActive) => {
            const btn = $(id);
            if (!btn) return;
            if (isActive) {
                btn.classList.add('active'); btn.classList.remove('bypassed'); btn.innerText = 'ACTIVE';
            } else {
                btn.classList.remove('active'); btn.classList.add('bypassed'); btn.innerText = 'NON-ACTIVE';
            }
        };

        const currentSettings = engine.getCurrentSettings();
        syncBypassBtn('btn-eq-bypass', currentSettings.lowActive || currentSettings.midActive || currentSettings.highActive);
        syncBypassBtn('btn-comp-bypass', currentSettings.compActive);
        syncBypassBtn('btn-mbcomp-bypass', currentSettings.mbcActive);
        syncBypassBtn('btn-mbimager-bypass', currentSettings.mbcActive);
        syncBypassBtn('btn-clip-bypass', currentSettings.clipActive);
        syncBypassBtn('btn-lim-bypass', currentSettings.limActive);
        syncBypassBtn('btn-nr-bypass', currentSettings.nrActive);
        syncBypassBtn('btn-ts-bypass', currentSettings.tsActive);
        syncBypassBtn('btn-dyneq-bypass', currentSettings.dynEqActive);
        syncBypassBtn('btn-subbass-bypass', currentSettings.subBassActive);

        // Sync Auto Release UI
        const btnAutoRelUI = $('btn-lim-auto-rel');
        const faderRelUI = $('fader-lim-release');
        if (btnAutoRelUI) {
            const isAuto = currentSettings.lAutoRel;
            btnAutoRelUI.classList.toggle('active', isAuto);
            btnAutoRelUI.style.background = isAuto ? 'var(--accent)' : 'transparent';
            btnAutoRelUI.style.color = isAuto ? '#000' : 'var(--text-dim)';
            btnAutoRelUI.style.borderColor = isAuto ? 'var(--accent)' : 'var(--text-dim)';
            if (faderRelUI) {
                faderRelUI.disabled = isAuto;
                faderRelUI.style.opacity = isAuto ? 0.3 : 1;
            }
        }

        // Sync Auto Export LUFS -14 UI
        const btnAutoLufsUI = $('btn-auto-lufs');
        if (btnAutoLufsUI) {
            const isLufs = currentSettings.autoLufs;
            btnAutoLufsUI.classList.toggle('active', isLufs);
            btnAutoLufsUI.style.background = isLufs ? 'var(--accent)' : 'transparent';
            btnAutoLufsUI.style.color = isLufs ? '#000' : 'var(--text-dim)';
            btnAutoLufsUI.style.borderColor = isLufs ? 'var(--accent)' : 'var(--text-dim)';
        }

        drawEQCurve();
        drawCompCurve();
    });

    console.log('[Presets] Change listener terpasang pada preset-selector.');

    // ════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•
    // ASYNC OPERATIONS (boleh gagal tanpa menghancurkan preset system)
    // ════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•════•
    try {
        // 1. Setup Change Folder button
        if (DOM.btnChangeFolder) {
            DOM.btnChangeFolder.addEventListener('click', async () => {
                try {
                    const current = await getDefaultMasterFolder();
                    const selected = await bridge.selectPresetFolder(current);
                    if (selected) {
                        localStorage.setItem(LS_MASTER_FOLDER_KEY, selected);
                        await reloadMasteringPresets();
                        showToast('Folder preset berhasil diubah!');
                    }
                } catch (err) {
                    console.error('[Presets] Change folder error:', err);
                }
            });
        }

        // 2. Load initial presets
        await reloadMasteringPresets();

        // 3. Setup Save button
        if (DOM.btnSavePreset) {
            DOM.btnSavePreset.addEventListener('click', () => {
                if (!DOM.promptModal) return;
                
                // Tampilkan modal
                DOM.promptModal.classList.add('show');
                DOM.promptInput.value = '';
                setTimeout(() => DOM.promptInput.focus(), 100);

                const closePrompt = () => {
                    DOM.promptModal.classList.remove('show');
                    // Cleanup temporary listeners
                    DOM.btnPromptSave.removeEventListener('click', onSaveClick);
                    DOM.btnPromptCancel.removeEventListener('click', closePrompt);
                    DOM.promptInput.removeEventListener('keydown', onKey);
                };

                const onSaveClick = async () => {
                    const name = DOM.promptInput.value.trim();
                    if (!name) { 
                        DOM.promptInput.focus(); 
                        return; 
                    }
                    
                    try {
                        // Nonaktifkan tombol sementara
                        DOM.btnPromptSave.disabled = true;
                        DOM.btnPromptSave.innerText = 'SIMPAN...';

                        const settings = engine.getCurrentSettings();
                        const folder = await getDefaultMasterFolder();
                        
                        await bridge.savePresetFile(settings, name, folder);
                        await reloadMasteringPresets();
                        
                        // Set selector ke preset baru
                        if (DOM.presetSelector) {
                            DOM.presetSelector.value = `CUSTOM:${name}`;
                            DOM.presetSelector.dispatchEvent(new Event('change'));
                        }
                        
                        showToast(`Preset '${name}' berhasil disimpan!`);
                        closePrompt();
                    } catch (err) {
                        console.error('Save error:', err);
                        showToast('Gagal menyimpan: ' + (err.message || err), true);
                    } finally {
                        DOM.btnPromptSave.disabled = false;
                        DOM.btnPromptSave.innerText = 'SIMPAN';
                    }
                };

                const onKey = (e) => {
                    if (e.key === 'Enter') onSaveClick();
                    if (e.key === 'Escape') closePrompt();
                };

                // Bind listeners
                DOM.btnPromptSave.addEventListener('click', onSaveClick);
                DOM.btnPromptCancel.addEventListener('click', closePrompt);
                DOM.promptInput.addEventListener('keydown', onKey);
            });
        }

        // 4. Setup Delete button
        if (DOM.btnDeletePreset) {
            DOM.btnDeletePreset.addEventListener('click', async () => {
                const val = DOM.presetSelector.value;
                if (!val.startsWith('CUSTOM:')) return;
                
                const name = val.replace('CUSTOM:', '');
                const presetData = CUSTOM_PRESETS[name];
                if (!presetData || !presetData.path) return;

                // Show custom confirm
                DOM.confirmMessage.innerText = `Hapus preset '${name}' secara permanen?`;
                DOM.confirmModal.classList.add('show');

                const closeConfirm = () => {
                    DOM.confirmModal.classList.remove('show');
                    DOM.btnConfirmOk.removeEventListener('click', onOk);
                    DOM.btnConfirmCancel.removeEventListener('click', closeConfirm);
                };

                const onOk = async () => {
                    try {
                        DOM.btnConfirmOk.disabled = true;
                        DOM.btnConfirmOk.innerText = 'MENGHAPUS...';
                        
                        await bridge.deletePresetFile(presetData.path);
                        await reloadMasteringPresets();
                        
                        DOM.presetSelector.value = 'default';
                        DOM.presetSelector.dispatchEvent(new Event('change'));
                        
                        showToast(`Preset '${name}' telah dihapus.`);
                        closeConfirm();
                    } catch (err) {
                        showToast('Gagal menghapus: ' + err.message, true);
                    } finally {
                        DOM.btnConfirmOk.disabled = false;
                        DOM.btnConfirmOk.innerText = 'HAPUS';
                    }
                };

                DOM.btnConfirmOk.addEventListener('click', onOk);
                DOM.btnConfirmCancel.addEventListener('click', closeConfirm);
            });
        }

        // 5. Setup Upload Preset button
        if (DOM.btnUploadPreset) {
            DOM.btnUploadPreset.addEventListener('click', async () => {
                const fileData = await bridge.openPresetFile();
                if (!fileData) return;
                
                try {
                    const parsed = JSON.parse(fileData.content);
                    const requiredKeys = ['low', 'mid', 'high', 'cThresh', 'cRatio', 'cAtt', 'cRel', 'mkp', 'lCeil'];
                    const isValid = requiredKeys.every(key => typeof parsed[key] === 'number');
                    
                    if (!isValid) {
                        showCustomAlert('File preset tidak cocok dengan spesifikasi Kamidi Mastering.', 'Format Tidak Valid');
                        return;
                    }
                    
                    const folder = await getDefaultMasterFolder();
                    const presetName = fileData.name.replace(/\.json$/i, '');
                    
                    await bridge.savePresetFile(parsed, presetName, folder);
                    await reloadMasteringPresets();
                    
                    if (DOM.presetSelector) {
                        DOM.presetSelector.value = `CUSTOM:${presetName}`;
                        DOM.presetSelector.dispatchEvent(new Event('change'));
                    }
                    showToast(`Preset '${presetName}' berhasil diunggah!`);
} catch (err) {
                    showCustomAlert('Gagal membaca file preset. Format tidak dikenali atau rusak.', 'Kesalahan');
                }
            });
        }
    } catch (err) {
        console.error('[Presets] Error saat inisialisasi preset (change listener tetap aktif):', err);
    }
}

window.addEventListener('error', (event) => {
    alert(`Error: ${event.message}`);
});

window.addEventListener('unhandledrejection', (event) => {
    // AbortError dari play()/pause() race condition — abaikan (harmless)
    if (event.reason && event.reason.name === 'AbortError') {
        event.preventDefault();
        return;
    }
    alert(`Unhandled Promise Rejection: ${event.reason}`);
});

// ============================================================
// TRANSPORT CONTROLS
// ============================================================
function initTransport() {
    // Play/Pause
    DOM.btnPlay?.addEventListener('click', async () => {
        await engine.init(); // Ensure context exists (autoplay policy)
        if (engine.isPlaying) {
            engine.pause();
            DOM.btnPlay.classList.remove('playing');
            updatePlayIcon(false);
            renderPlaylist(); // Update playlist icons
        } else {
            if (!engine.hasBuffer()) { showToast('Muat file audio terlebih dahulu!', true); return; }
            engine.play();
            DOM.btnPlay.classList.add('playing');
            updatePlayIcon(true);
            startUILoop();
            renderPlaylist(); // Update playlist icons
        }
    });

    // Seek
    DOM.seekBar?.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        e.target.style.setProperty('--progress', `${(val / (DOM.seekBar.max || 1)) * 100}%`);
        if (DOM.timeCurrent) DOM.timeCurrent.innerText = formatTime(val);
        if (engine.hasBuffer()) engine.seek(val);
    });

    // Playback modes
    DOM.btnLoop?.addEventListener('click', () => {
        isLoopMode = !isLoopMode;
        if (isLoopMode) DOM.btnLoop.classList.add('active');
        else DOM.btnLoop.classList.remove('active');
    });

    DOM.btnRandom?.addEventListener('click', () => {
        if (trackQueue.length <= 2) return;
        isRandomMode = !isRandomMode;
        if (isRandomMode) DOM.btnRandom.classList.add('active');
        else DOM.btnRandom.classList.remove('active');
    });

    // On track ended
    engine.onEnded = () => {
        if (isLoopMode) {
            if (isBatchMode) {
                let nextIndex = activeQueueIndex + 1;
                if (isRandomMode) {
                    do { nextIndex = Math.floor(Math.random() * trackQueue.length); } 
                    while (nextIndex === activeQueueIndex && trackQueue.length > 1);
                } else if (nextIndex >= trackQueue.length) {
                    nextIndex = 0; // loop back to start
                }
                loadQueueTrack(nextIndex).then(() => {
                    engine.play();
                    DOM.btnPlay?.classList.add('playing');
                    updatePlayIcon(true);
                    startUILoop();
                    renderPlaylist();
                });
            } else {
                // Single audio loop
                engine.seek(0);
                engine.play();
                DOM.btnPlay?.classList.add('playing');
                updatePlayIcon(true);
                startUILoop();
                renderPlaylist();
            }
        } else {
            if (isBatchMode && activeQueueIndex < trackQueue.length - 1) {
                let nextIndex = activeQueueIndex + 1;
                if (isRandomMode) {
                    do { nextIndex = Math.floor(Math.random() * trackQueue.length); } 
                    while (nextIndex === activeQueueIndex && trackQueue.length > 1);
                }
                // Auto-play next track in queue
                loadQueueTrack(nextIndex).then(() => {
                    engine.play();
                    DOM.btnPlay?.classList.add('playing');
                    updatePlayIcon(true);
                    startUILoop();
                    renderPlaylist();
                });
            } else {
                DOM.btnPlay?.classList.remove('playing');
                updatePlayIcon(false);
                resetTransportUI();
            }
        }
    };

    // Playlist Toggle
    DOM.btnPlaylist?.addEventListener('click', () => {
        if (!DOM.playlistSection) return;
        const isHidden = DOM.playlistSection.style.display === 'none';
        DOM.playlistSection.style.display = isHidden ? 'flex' : 'none';
    });

    // Playlist Resize Handle
    initPlaylistResize();
}

// ============================================================
// PLAYLIST RESIZE
// ============================================================
function initPlaylistResize() {
    const handle = DOM.playlistResizeHandle;
    const container = DOM.playlistContainer;
    if (!handle || !container) return;

    const line = handle.querySelector('.playlist-resize-line');
    if (!line) return;

    let isDragging = false;
    let startY = 0;
    let startHeight = 0;

    line.addEventListener('mousedown', (e) => {
        isDragging = true;
        startY = e.clientY;
        startHeight = container.offsetHeight;
        document.body.style.cursor = 'ns-resize';
        document.body.style.userSelect = 'none';
        e.preventDefault();
    });

    window.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        const delta = e.clientY - startY;
        const newHeight = Math.max(50, Math.min(400, startHeight + delta));
        container.style.maxHeight = newHeight + 'px';
    });

    window.addEventListener('mouseup', () => {
        if (isDragging) {
            isDragging = false;
            document.body.style.cursor = '';
            document.body.style.userSelect = '';
        }
    });
}

// ============================================================
// LOAD TRACK (via TauriBridge — supports multi-select)
// ============================================================
function initLoadTrack() {
    DOM.btnLoad?.addEventListener('click', async () => {
        await engine.init();
        try {
            if (DOM.trackTitle) DOM.trackTitle.innerText = 'SEDANG MEMUAT AUDIO...';

            // Disable playback modes during loading
            if (DOM.btnLoop) {
                DOM.btnLoop.style.opacity = '0.3';
                DOM.btnLoop.style.cursor = 'not-allowed';
                DOM.btnLoop.disabled = true;
            }
            if (DOM.btnRandom) {
                DOM.btnRandom.style.opacity = '0.3';
                DOM.btnRandom.style.cursor = 'not-allowed';
                DOM.btnRandom.disabled = true;
            }

            const files = await bridge.openAudioFiles();
            if (!files || files.length === 0) {
                if (DOM.trackTitle) DOM.trackTitle.innerText = loadedFileName;
                // Re-enable if we already had a valid queue
                if (trackQueue.length > 0 && DOM.btnLoop) {
                    DOM.btnLoop.style.opacity = '1';
                    DOM.btnLoop.style.cursor = 'pointer';
                    DOM.btnLoop.disabled = false;
                }
                if (trackQueue.length > 2 && DOM.btnRandom) {
                    DOM.btnRandom.style.opacity = '1';
                    DOM.btnRandom.style.cursor = 'pointer';
                    DOM.btnRandom.disabled = false;
                }
                return;
            }

            // Stop current playback
            engine.stop();
            if (DOM.btnPlay) DOM.btnPlay.classList.remove('playing');
            updatePlayIcon(false);

            // Setup queue
            if (currentAudioUrl) {
                URL.revokeObjectURL(currentAudioUrl);
                currentAudioUrl = null;
            }
            trackQueue = [];
            const totalFiles = files.length;
            isBatchMode = totalFiles > 1;
            activeQueueIndex = 0;

            // Tambahkan semua file secara instan tanpa perlu read bytes (Lazy loading)
            for (let i = 0; i < totalFiles; i++) {
                trackQueue.push(files[i]);
            }

            if (trackQueue.length === 0) {
                if (DOM.trackTitle) DOM.trackTitle.innerText = 'NO TRACK LOADED';
                showToast('Tidak ada file yang dipilih.', true);
                return;
            }

            isBatchMode = trackQueue.length > 1;
            await loadQueueTrack(0, true); // true = ini adalah loading awal

            // Enable playback modes now that audio is ready
            if (DOM.btnLoop) {
                if (trackQueue.length > 0) {
                    DOM.btnLoop.style.opacity = '1';
                    DOM.btnLoop.style.cursor = 'pointer';
                    DOM.btnLoop.disabled = false;
                } else {
                    DOM.btnLoop.style.opacity = '0.3';
                    DOM.btnLoop.style.cursor = 'not-allowed';
                    DOM.btnLoop.disabled = true;
                    isLoopMode = false;
                    DOM.btnLoop.classList.remove('active');
                }
            }

            if (DOM.btnRandom) {
                if (trackQueue.length > 2) {
                    DOM.btnRandom.style.opacity = '1';
                    DOM.btnRandom.style.cursor = 'pointer';
                    DOM.btnRandom.disabled = false;
                } else {
                    DOM.btnRandom.style.opacity = '0.3';
                    DOM.btnRandom.style.cursor = 'not-allowed';
                    DOM.btnRandom.disabled = true;
                    isRandomMode = false;
                    DOM.btnRandom.classList.remove('active');
                }
            }
            
            if (DOM.btnClear) {
                DOM.btnClear.style.display = 'flex';
            }

            // Show playlist button & auto-open if batch
            if (DOM.btnPlaylist) {
                DOM.btnPlaylist.style.display = 'flex';
            }
            if (isBatchMode && DOM.playlistSection) {
                DOM.playlistSection.style.display = 'flex';
            }
            renderPlaylist();

            // Info notifikasi sudah tidak relevan karena UI langsung update seketika
        } catch (err) {
            showToast(err.message || 'Gagal memuat file.', true);
            if (DOM.trackTitle) DOM.trackTitle.innerText = loadedFileName;
        }
    });

    // Navigation Events (wrap around / loop)
    DOM.btnPrev?.addEventListener('click', () => {
        if (!isBatchMode || trackQueue.length < 2) return;
        const prevIndex = activeQueueIndex <= 0 ? trackQueue.length - 1 : activeQueueIndex - 1;
        loadQueueTrack(prevIndex).then(() => {
            engine.play();
            DOM.btnPlay?.classList.add('playing');
            updatePlayIcon(true);
            startUILoop();
            renderPlaylist();
        });
    });

    DOM.btnNext?.addEventListener('click', () => {
        if (!isBatchMode || trackQueue.length < 2) return;
        const nextIndex = activeQueueIndex >= trackQueue.length - 1 ? 0 : activeQueueIndex + 1;
        loadQueueTrack(nextIndex).then(() => {
            engine.play();
            DOM.btnPlay?.classList.add('playing');
            updatePlayIcon(true);
            startUILoop();
            renderPlaylist();
        });
    });

    DOM.btnClear?.addEventListener('click', () => {
        engine.stop();
        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
            currentAudioUrl = null;
        }
        trackQueue = [];
        isBatchMode = false;
        activeQueueIndex = 0;
        loadedFileName = 'NO TRACK LOADED';
        
        if (DOM.trackTitle) DOM.trackTitle.innerText = loadedFileName;
        if (DOM.timeCurrent) DOM.timeCurrent.innerText = '0:00';
        if (DOM.timeTotal) DOM.timeTotal.innerText = '0:00';
        if (DOM.seekBar) { DOM.seekBar.max = 100; DOM.seekBar.value = 0; DOM.seekBar.style.setProperty('--progress', '0%'); }
        if (DOM.badgeChannels) DOM.badgeChannels.innerText = 'STEREO';
        if (DOM.btnPlay) DOM.btnPlay.classList.remove('playing');
        updatePlayIcon(false);
        resetTransportUI();

        if (DOM.btnPrev) DOM.btnPrev.style.display = 'none';
        if (DOM.btnNext) DOM.btnNext.style.display = 'none';
        
        if (DOM.btnLoop) {
            DOM.btnLoop.style.opacity = '0.3';
            DOM.btnLoop.style.cursor = 'not-allowed';
            DOM.btnLoop.disabled = true;
            isLoopMode = false;
            DOM.btnLoop.classList.remove('active');
        }
        if (DOM.btnRandom) {
            DOM.btnRandom.style.opacity = '0.3';
            DOM.btnRandom.style.cursor = 'not-allowed';
            DOM.btnRandom.disabled = true;
            isRandomMode = false;
            DOM.btnRandom.classList.remove('active');
        }
        
        if (DOM.btnClear) DOM.btnClear.style.display = 'none';
        
        // Hide playlist
        if (DOM.btnPlaylist) DOM.btnPlaylist.style.display = 'none';
        if (DOM.playlistSection) DOM.playlistSection.style.display = 'none';
        if (DOM.playlistContainer) DOM.playlistContainer.innerHTML = '';
    });
}

async function loadQueueTrack(index, isInitialLoad = false) {
    if (index < 0 || index >= trackQueue.length) return;
    
    // Cancel any previous in-progress load
    const thisRequestId = ++loadRequestId;
    
    activeQueueIndex = index;
    const file = trackQueue[index];
    const wasPlaying = engine.isPlaying;

    try {
        if (DOM.trackTitle) {
            if (isInitialLoad) {
                DOM.trackTitle.innerText = 'SEDANG MEMUAT AUDIO...';
            } else {
                DOM.trackTitle.innerText = `MEMUAT: ${file.name.toUpperCase()}...`;
            }
        }

        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
            currentAudioUrl = null;
        }
        const url = await bridge.getAudioUrl(file);
        currentAudioUrl = url;
        
        // If a newer request was made while we were loading, abort this one
        if (thisRequestId !== loadRequestId) return;
        
        const info = await engine.loadUrl(url);
        
        // Double-check after decode (in case another click happened during decode)
        if (thisRequestId !== loadRequestId) return;

        // Update display
        if (isBatchMode) {
            loadedFileName = `${trackQueue.length} TRACKS ◆ BATCH MODE | ${file.name}`;
            if (DOM.btnPrev) {
                DOM.btnPrev.style.display = '';
                DOM.btnPrev.style.opacity = '1';
                DOM.btnPrev.style.cursor = 'pointer';
            }
            if (DOM.btnNext) {
                DOM.btnNext.style.display = '';
                DOM.btnNext.style.opacity = '1';
                DOM.btnNext.style.cursor = 'pointer';
            }
        } else {
            loadedFileName = file.name;
            if (DOM.btnPrev) DOM.btnPrev.style.display = 'none';
            if (DOM.btnNext) DOM.btnNext.style.display = 'none';
        }

        if (DOM.trackTitle) DOM.trackTitle.innerText = loadedFileName;
        if (DOM.timeTotal) DOM.timeTotal.innerText = formatTime(info.duration);
        if (DOM.seekBar) { DOM.seekBar.max = info.duration; DOM.seekBar.value = 0; DOM.seekBar.style.setProperty('--progress', '0%'); }
        if (DOM.timeCurrent) DOM.timeCurrent.innerText = '0:00';

        // Update badges
        if (DOM.badgeChannels) DOM.badgeChannels.innerText = info.channels >= 2 ? 'STEREO' : 'MONO';
        
        // Auto-play if previously playing, or just reset play button
        if (wasPlaying) {
            engine.stop();
            engine.play();
            if (DOM.btnPlay) DOM.btnPlay.classList.add('playing');
            updatePlayIcon(true);
            startUILoop();
        } else {
            if (DOM.btnPlay) DOM.btnPlay.classList.remove('playing');
            updatePlayIcon(false);
        }

        // Update playlist active state
        renderPlaylist();
    } catch (err) {
        showToast(`Gagal memuat track: ${file.name}`, true);
        console.error(err);
    }
}


function removeTrackFromQueue(index) {
    if (index < 0 || index >= trackQueue.length) return;

    // Remove the track
    trackQueue.splice(index, 1);

    if (trackQueue.length === 0) {
        // Clear all
        DOM.btnClear?.click();
        return;
    }

    // Update batch mode flag
    isBatchMode = trackQueue.length > 1;

    // Adjust activeQueueIndex and playback
    if (index === activeQueueIndex) {
        // We deleted the currently active track
        if (activeQueueIndex >= trackQueue.length) {
            // It was the last track, now activeQueueIndex should be the new last track
            activeQueueIndex = trackQueue.length - 1;
        }
        
        const wasPlaying = engine.isPlaying;
        engine.stop();
        resetMaxMeters();
        
        // Load the new active track
        loadQueueTrack(activeQueueIndex).then(() => {
            if (wasPlaying) {
                engine.play();
                DOM.btnPlay?.classList.add('playing');
                updatePlayIcon(true);
                startUILoop();
            }
        });
    } else if (index < activeQueueIndex) {
        // We deleted a track before the active one, shift index down
        activeQueueIndex--;
        // Re-render
        renderPlaylist();
    } else {
        // Deleted track after active one, just re-render
        renderPlaylist();
    }
}

// ============================================================
// PLAYLIST RENDERER
// ============================================================
function renderPlaylist() {
    if (!DOM.playlistContainer) return;
    DOM.playlistContainer.innerHTML = '';

    if (DOM.playlistCount) {
        DOM.playlistCount.innerText = `${trackQueue.length} TRACK${trackQueue.length !== 1 ? 'S' : ''}`;
    }

    trackQueue.forEach((file, idx) => {
        const item = document.createElement('div');
        item.className = 'playlist-item' + (idx === activeQueueIndex ? ' active' : '');

        // Track number
        const numEl = document.createElement('span');
        numEl.style.cssText = 'font-size:0.6rem; color:var(--text-dim); font-family:"JetBrains Mono",monospace; min-width:24px; flex-shrink:0;';
        numEl.textContent = String(idx + 1).padStart(2, '0');

        // Track name
        const nameEl = document.createElement('span');
        nameEl.className = 'playlist-item-name';
        nameEl.textContent = file.name;

        // Play/Pause button icon
        const playBtn = document.createElement('button');
        playBtn.className = 'playlist-play-btn';
        const isActiveAndPlaying = idx === activeQueueIndex && engine.isPlaying;
        playBtn.innerHTML = isActiveAndPlaying
            ? '<svg width="10" height="10" viewBox="0 0 24 24"><path d="M6 4h4v16H6zM14 4h4v16h-4z" fill="currentColor"/></svg>'
            : '<svg width="10" height="10" viewBox="0 0 24 24"><path d="M8 5v14l11-7z" fill="currentColor"/></svg>';
        
        // Make entire item clickable
        item.style.cursor = 'pointer';
        item.addEventListener('click', () => {
            if (idx === activeQueueIndex && engine.hasBuffer()) {
                // Prevent reloading if it's already the active track
                if (!engine.isPlaying) {
                    engine.play();
                    DOM.btnPlay?.classList.add('playing');
                    updatePlayIcon(true);
                    startUILoop();
                    renderPlaylist(); // Update playlist icons
                } else {
                    engine.seek(0); // Restart if already playing
                }
            } else {
                loadQueueTrack(idx).then(() => {
                    engine.play();
                    DOM.btnPlay?.classList.add('playing');
                    updatePlayIcon(true);
                    startUILoop();
                    renderPlaylist(); // Update playlist icons
                });
            }
        });

        // Delete button
        const delBtn = document.createElement('button');
        delBtn.className = 'playlist-del-btn';
        delBtn.innerHTML = '<svg width="10" height="10" viewBox="0 0 24 24"><path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z" fill="currentColor"/></svg>';
        delBtn.title = "Hapus dari antrean";
        delBtn.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent triggering item click
            removeTrackFromQueue(idx);
        });

        // Active dot (merah)
        const dot = document.createElement('div');
        dot.className = 'playlist-active-dot';

        item.appendChild(numEl);
        item.appendChild(nameEl);
        item.appendChild(playBtn);
        item.appendChild(delBtn);
        item.appendChild(dot);

        DOM.playlistContainer.appendChild(item);
    });

    // Scroll active item into view
    const activeItem = DOM.playlistContainer.querySelector('.playlist-item.active');
    if (activeItem) {
        activeItem.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
    }
}

// ============================================================
// EXPORT (via TauriBridge + OfflineAudioContext)
// ============================================================
// --- Max Meter Tracking ---
let maxMeterStats = {
    lufs: -60, tp: -60, peakL: -60, peakR: -60,
    compGR: 0, limGR: 0, clipGR: 0
};
function resetMaxMeters() {
    maxMeterStats = { lufs: -60, tp: -60, peakL: -60, peakR: -60, compGR: 0, limGR: 0, clipGR: 0 };
}

let isExportCancelled = false;

function initExport() {
    DOM.btnExport?.addEventListener('click', async () => {
        if (!engine.hasBuffer() && trackQueue.length === 0) {
            showToast('Tidak ada audio yang dimuat.', true);
            return;
        }

        // Pause audio if currently playing before starting export
        if (engine.isPlaying) {
            engine.pause();
            if (DOM.btnPlay) DOM.btnPlay.classList.remove('playing');
            updatePlayIcon(false);
            renderPlaylist();
        }

        // Jika Auto LUFS -14 NON-AKTIF, tampilkan popup konfirmasi
        if (!engine.autoLufsNormalize) {
            const lufsChoice = await showLufsConfirmModal();
            if (lufsChoice === 'cancel') return; // BATAL → tidak jadi export
            if (lufsChoice === 'yes') {
                engine.toggleAutoLufs(true); // Aktifkan sementara untuk export ini
            }
            // lufsChoice === 'no' → lanjut export tanpa LUFS -14
        }

        isExportCancelled = false;

        if (isBatchMode && trackQueue.length > 1) {
            await doBatchExport();
        } else {
            await doSingleExport();
        }

        // Kembalikan state LUFS -14 ke kondisi tombol UI sebenarnya
        const btnAutoLufs = document.getElementById('btn-auto-lufs');
        const uiIsActive = btnAutoLufs ? btnAutoLufs.classList.contains('active') : false;
        engine.toggleAutoLufs(uiIsActive);
    });

    const btnCancel = document.getElementById('btn-cancel-export');
    if (btnCancel) {
        btnCancel.addEventListener('click', () => {
            isExportCancelled = true;
            updateExportStatus('Membatalkan...');
        });
    }
}

// ============================================================
// LUFS -14 CONFIRMATION POPUP
// ============================================================
function showLufsConfirmModal() {
    return new Promise((resolve) => {
        const modal = document.getElementById('lufs-confirm-modal');
        if (!modal) { resolve('no'); return; }
        
        modal.classList.add('show');
        
        const btnYes = document.getElementById('btn-lufs-confirm-yes');
        const btnNo = document.getElementById('btn-lufs-confirm-no');
        const btnCancel = document.getElementById('btn-lufs-confirm-cancel');
        
        function cleanup(result) {
            modal.classList.remove('show');
            btnYes.removeEventListener('click', onYes);
            btnNo.removeEventListener('click', onNo);
            btnCancel.removeEventListener('click', onCancel);
            resolve(result);
        }
        
        function onYes() { cleanup('yes'); }
        function onNo() { cleanup('no'); }
        function onCancel() { cleanup('cancel'); }
        
        btnYes.addEventListener('click', onYes);
        btnNo.addEventListener('click', onNo);
        btnCancel.addEventListener('click', onCancel);
    });
}

// ============================================================
// SUMMARY REPORT
// ============================================================
function initSummary() {
    const btnSummary = document.getElementById('btn-summary');
    const modalSummary = document.getElementById('summary-modal');
    const btnClose = document.getElementById('btn-summary-close-icon');
    const btnOk = document.getElementById('btn-summary-ok');
    const btnDownload = document.getElementById('btn-summary-download');
    const btnCopy = document.getElementById('btn-summary-copy');
    const textElement = document.getElementById('summary-text');

    if (!btnSummary || !modalSummary) return;

    btnSummary.addEventListener('click', () => {
        if (!engine.hasBuffer() && (typeof trackQueue === 'undefined' || trackQueue.length === 0)) {
            if (typeof showToast === 'function') {
                showToast('Tidak ada audio yang dimuat.', true);
            }
            return;
        }

        const report = generateSummaryReport();
        textElement.textContent = report;
        modalSummary.classList.add('show');
    });

    const closeModal = () => modalSummary.classList.remove('show');
    btnClose?.addEventListener('click', closeModal);
    btnOk?.addEventListener('click', closeModal);

    btnCopy?.addEventListener('click', async () => {
        try {
            const text = generateSummaryReport();
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(text);
                if (typeof showToast === 'function') showToast('Summary disalin ke clipboard!');
                
                // Visual feedback (flash color)
                const originalBg = btnCopy.style.background;
                const originalColor = btnCopy.style.color;
                const originalHtml = btnCopy.innerHTML;
                
                btnCopy.style.color = 'var(--accent)';
                btnCopy.style.borderColor = 'var(--accent)';
                btnCopy.innerHTML = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> COPIED!';
                
                setTimeout(() => {
                    btnCopy.style.color = originalColor;
                    btnCopy.style.borderColor = '';
                    btnCopy.innerHTML = originalHtml;
                }, 1000);
            }
        } catch (err) {
            console.error('Copy failed:', err);
            if (typeof showToast === 'function') showToast('Gagal menyalin teks.', true);
        }
    });

    btnDownload?.addEventListener('click', async () => {
        const text = generateSummaryReport().replace(/\n/g, '\r\n');
        const dateStr = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
        const fileName = `Kamidi_Mastering_Summary_${dateStr}.txt`;
        
        try {
            const savedPath = await bridge.saveTextFile(text, fileName);
            if (savedPath) {
                if (typeof showToast === 'function') showToast(`Report disimpan: ${savedPath}`);
            }
        } catch (err) {
            if (typeof showToast === 'function') showToast(`Gagal menyimpan: ${err.message}`, true);
        }
    });
}

function generateSummaryReport() {
    const d = new Date();
    const dateStr = d.toLocaleString();

    let output = `=========================================\n`;
    output += `KAMIDI MASTERING PRO V5 - SUMMARY REPORT\n`;
    output += `Date: ${dateStr}\n`;
    output += `=========================================\n\n`;

    // 1. OUTPUT METERS
    output += `[ OUTPUT METERS ]\n`;
    
    // P1 & P2: Gunakan hasil export jika ada, jika tidak fallback ke live meter
    let _stats = {};
    if (window.lastExportStats) {
        _stats = window.lastExportStats;
    } else if (engine.getLoudnessStats) {
        _stats = engine.getLoudnessStats();
    }

    const stats = {
        lufs: typeof _stats.lufs === 'number' ? _stats.lufs : -60,
        tp: typeof _stats.tp === 'number' ? _stats.tp : -60,
        dr: typeof _stats.dr === 'number' ? _stats.dr : 0
    };
    
    const _level = engine.getMasterLevel ? engine.getMasterLevel() : {};
    const level = {
        peakL: typeof _level.dbL === 'number' ? _level.dbL : -60,
        peakR: typeof _level.dbR === 'number' ? _level.dbR : -60
    };
    
    const compGR = engine.getGainReduction ? (engine.getGainReduction() || 0) : 0;
    const limGR = engine.getLimiterReduction ? (engine.getLimiterReduction() || 0) : 0;
    const clipGR = engine.getClipperReduction ? (engine.getClipperReduction() || 0) : 0;
    
    output += `LUFS-I           : ${stats.lufs <= -59 ? '-INF' : stats.lufs.toFixed(1)} LUFS  (Max: ${maxMeterStats.lufs <= -59 ? '-INF' : maxMeterStats.lufs.toFixed(1)} LUFS)\n`;
    output += `True Peak (Final): ${stats.tp <= -59 ? '-INF' : stats.tp.toFixed(1)} dB  (Live Max: ${maxMeterStats.tp <= -59 ? '-INF' : maxMeterStats.tp.toFixed(1)} dB)\n`;
    output += `Dynamic Range    : ${stats.dr.toFixed(1)} \n`;
    output += `L/R Peak         : ${level.peakL <= -59 ? '-INF' : level.peakL.toFixed(1)} dB / ${level.peakR <= -59 ? '-INF' : level.peakR.toFixed(1)} dB  (Max: ${maxMeterStats.peakL <= -59 ? '-INF' : maxMeterStats.peakL.toFixed(1)} / ${maxMeterStats.peakR <= -59 ? '-INF' : maxMeterStats.peakR.toFixed(1)})\n`;
    output += `Compressor GR    : ${compGR.toFixed(1)} dB  (Max: ${maxMeterStats.compGR.toFixed(1)} dB)\n`;
    output += `Limiter Reduction: ${limGR.toFixed(1)} dB  (Max: ${maxMeterStats.limGR.toFixed(1)} dB)\n`;
    output += `Clipper Clip     : ${clipGR.toFixed(1)} dB  (Max: ${maxMeterStats.clipGR.toFixed(1)} dB)\n\n`;

    // 2. MODULE SETTINGS
    output += `[ MODULE SETTINGS ]\n\n`;
    const s = engine.getCurrentSettings ? engine.getCurrentSettings() : {};

    if (s.nrThresh !== undefined) {
        output += `--- NOISE REDUCTION ---\n`;
        output += `Status    : ${s.nrActive ? 'ON' : 'OFF'}\n`;
        if (s.nrActive) {
            output += `Threshold : ${s.nrThresh} dB\n`;
            output += `Amount    : ${s.nrAmount}\n`;
        }
        output += `\n`;
    }

    if (s.tsAtt !== undefined) {
        output += `--- TRANSIENT SHAPER ---\n`;
        output += `Status    : ${s.tsActive ? 'ON' : 'OFF'}\n`;
        if (s.tsActive) {
            output += `Attack    : ${s.tsAtt}%\n`;
            output += `Sustain   : ${s.tsSus}%\n`;
        }
        output += `\n`;
    }

    if (s.hpf !== undefined) {
        output += `--- PARAMETRIC EQ ---\n`;
        const eqActive = s.lowActive || s.midActive || s.highActive;
        output += `Status    : ${eqActive ? 'ON' : 'OFF'}\n`;
        if (eqActive) {
            output += `Low Cut   : ${s.hpf} Hz\n`;
            output += `Low Band  : ${s.low} dB (${s.lFreq} Hz)\n`;
            output += `Mid Band  : ${s.mid} dB (${s.mFreq} Hz, Q: ${s.mQ})\n`;
            output += `High Band : ${s.high} dB (${s.hFreq} Hz)\n`;
        }
        output += `\n`;
    }

    if (s.dynEq) {
        output += `--- DYNAMIC EQ ---\n`;
        output += `Status    : ${s.dynEqActive ? 'ON' : 'OFF'}\n`;
        if (s.dynEqActive) {
            s.dynEq.forEach((b, i) => {
                output += `Band ${i+1}    : Thresh ${b.thresh} dB | Freq ${b.freq} Hz | Ratio ${b.ratio}:1\n`;
            });
        }
        output += `\n`;
    }

    if (s.cThresh !== undefined) {
        output += `--- COMPRESSOR ---\n`;
        output += `Status    : ${s.compActive ? 'ON' : 'OFF'}\n`;
        if (s.compActive) {
            output += `Threshold : ${s.cThresh} dB\n`;
            output += `Ratio     : ${s.cRatio}:1\n`;
            output += `Knee      : ${s.cKnee}\n`;
            output += `Attack    : ${s.cAtt} ms\n`;
            output += `Release   : ${s.cRel} ms\n`;
            output += `Makeup    : ${s.mkp} dB\n`;
            output += `Mix       : ${s.cMix * 100}%\n`;
        }
        output += `\n`;
    }

    if (s.mbcXoverLow !== undefined) {
        output += `--- MULTIBAND COMPRESSOR ---\n`;
        output += `Status    : ${s.mbcActive ? 'ON' : 'OFF'}\n`;
        if (s.mbcActive) {
            output += `XOver Low : ${s.mbcXoverLow} Hz\n`;
            output += `XOver High: ${s.mbcXoverHigh} Hz\n`;
            output += `Low Band  : Thresh ${s.mbcLowThresh}dB | Ratio ${s.mbcLowRatio}:1 | Makeup ${s.mbcLowMkp}dB\n`;
            output += `Mid Band  : Thresh ${s.mbcMidThresh}dB | Ratio ${s.mbcMidRatio}:1 | Makeup ${s.mbcMidMkp}dB\n`;
            output += `High Band : Thresh ${s.mbcHighThresh}dB | Ratio ${s.mbcHighRatio}:1 | Makeup ${s.mbcHighMkp}dB\n`;
        }
        output += `\n`;
    }


    if (s.subBass !== undefined) {
        output += `--- 808 SUB BASS ---\n`;
        output += `Status    : ${s.subBassActive ? 'ON' : 'OFF'}\n`;
        if (s.subBassActive) {
            output += `Freq      : ${s.subBass.freq} Hz\n`;
            output += `Drive     : ${s.subBass.drive} %\n`;
            output += `Sub Gain  : ${s.subBass.sub} %\n`;
            output += `Clean     : ${s.subBass.clean} %\n`;
            output += `Mix       : ${s.subBass.mix} %\n`;
        }
        output += `\n`;
    }

    if (s.clip !== undefined) {
        output += `--- CLIPPER ---\n`;
        output += `Status    : ${s.clipActive ? 'ON' : 'OFF'}\n`;
        if (s.clipActive) {
            output += `Threshold : ${s.clip.toFixed(1)} dB\n`;
        }
        output += `\n`;
    }

    if (s.fx) {
        output += `--- FX CHAIN ---\n`;
        output += `Delay     : ${s.fx.delay?.active ? 'Mix ' + (s.fx.delay.mix || 0) : 'OFF'}\n`;
        output += `Reverb    : ${s.fx.reverb?.active ? 'Mix ' + (s.fx.reverb.mix || 0) : 'OFF'}\n`;
        output += `Widener   : ${s.fx.widener?.active ? 'Width ' + (s.fx.widener.width || 0) : 'OFF'}\n`;
        output += `Sat       : ${s.fx.saturation?.active ? 'Mix ' + (s.fx.saturation.mix || 0) : 'OFF'}\n`;
        output += `Chorus    : ${s.fx.chorus?.active ? 'Mix ' + (s.fx.chorus.mix || 0) : 'OFF'}\n\n`;
    }

    if (s.lCeil !== undefined) {
        output += `--- LIMITER & MASTERING ---\n`;
        output += `Status    : ${s.limActive ? 'ON' : 'OFF'}\n`;
        if (s.limActive) {
            output += `Ceiling   : ${s.lCeil} dB\n`;
            output += `Threshold : ${s.lThresh} dB\n`;
            output += `Release   : ${s.lRel} s\n`;
            output += `Auto Rel  : ${s.lAutoRel ? 'ON' : 'OFF'}\n`;
        }
        output += `Auto LUFS : ${s.autoLufs ? 'ON (-14 LUFS)' : 'OFF'}\n`;
        output += `\n`;
    }

    output += `=========================================\n`;
    return output;
}

async function doSingleExport() {
    const file = trackQueue[activeQueueIndex];
    if (!file) return;
    const baseName = file.name;
    const originalName = baseName.replace(/\.[^.]+$/, '') + '.wav';
    
    let targetFolder = null;
    if (bridge.isTauri()) {
        let baseFolder = undefined;
        if (file.path) {
            const lastSlash = Math.max(file.path.lastIndexOf('\\'), file.path.lastIndexOf('/'));
            if (lastSlash > 0) baseFolder = file.path.substring(0, lastSlash);
        }
        targetFolder = await bridge.selectFolder('Pilih Folder Tujuan Export', baseFolder);
        if (!targetFolder) {
            showToast('Export dibatalkan.', false);
            return;
        }
        targetFolder = await bridge.ensureMasteringFolder(targetFolder);
    }

    showExportModal(true);
    try {
        updateExportStatus('Menyiapkan buffer audio...');
        const bytes = await bridge.readAudioBytes(file);
        
        updateExportStatus('Merender audio offline...');
        const { wav: wavData, stats: exportStats } = await engine.renderOffline(bytes, (progress) => {
            updateExportProgress(progress * 80);
            if (progress >= 0.7) updateExportStatus('Mengonversi ke format WAV...');
        });
        
        // Simpan metrik akurat hasil render offline untuk Summary Report (P1 & P2)
        window.lastExportStats = exportStats;
        
        updateExportProgress(85);
        updateExportStatus('Menyimpan file...');

        if (isExportCancelled) throw new Error('Dibatalkan oleh pengguna');

        // Tulis file ke lokasi
        let finalPath = originalName;
        if (bridge.isTauri() && targetFolder) {
            finalPath = targetFolder + '/' + originalName;
            
            if (engine.autoLufsNormalize) {
                const tempPath = targetFolder + '/~temp_export.wav';
                await bridge.writeFileData(tempPath, wavData, 'audio/wav');
                
                updateExportStatus('Menyelesaikan pemrosesan audio...');
                const finalStats = await bridge.runFfmpegLoudnorm(tempPath, finalPath, (prog, msg) => {
                    updateExportProgress(85 + (prog * 0.15));
                    if (msg) updateExportStatus(msg);
                });
                
                try { await bridge.deleteFile(tempPath); } catch(e) {}
                window.lastExportStats = finalStats;
            } else {
                await bridge.writeFileData(finalPath, wavData, 'audio/wav');
            }
        } else {
            await bridge.saveExportWav(wavData, originalName);
        }

        if (isExportCancelled) throw new Error('Dibatalkan oleh pengguna');

        updateExportProgress(100);
        updateExportStatus('Export berhasil!');
        setTimeout(() => { showExportModal(false); showToast(`Export berhasil: ${finalPath}`); }, 800);
    } catch (err) {
        showExportModal(false);
        if (err.message === 'Dibatalkan oleh pengguna') {
            showToast('Export dibatalkan.', false, true);
        } else {
            showToast('Export gagal: ' + (err.message || err), true);
        }
    }
}

async function doBatchExport() {
    let targetFolder = null;
    
    // Jika di Tauri, minta user pilih folder tujuan
    if (bridge.isTauri()) {
        let baseFolder = undefined;
        const firstFile = trackQueue[0];
        if (firstFile && firstFile.path) {
            const lastSlash = Math.max(firstFile.path.lastIndexOf('\\'), firstFile.path.lastIndexOf('/'));
            if (lastSlash > 0) baseFolder = firstFile.path.substring(0, lastSlash);
        }
        targetFolder = await bridge.selectFolder('Pilih Folder Tujuan Export Batch', baseFolder);
        if (!targetFolder) {
            showToast('Batch export dibatalkan.', false);
            return;
        }
        targetFolder = await bridge.ensureMasteringFolder(targetFolder);
    }

    showExportModal(true);
    try {
        const total = trackQueue.length;
        let successCount = 0;
        let failCount = 0;

        for (let i = 0; i < total; i++) {
            const file = trackQueue[i];
            const num = i + 1;

            try {
                // Step 1: Read Bytes for Export
                updateExportStatus(`Memuat track ${num}/${total}: ${file.name}`);
                updateExportProgress((i / total) * 100);

                const bytes = await bridge.readAudioBytes(file);

                // Step 2: Render offline with current mastering settings
                updateExportStatus(`Rendering ${num}/${total}: ${file.name}`);
                const { wav: wavData, stats: exportStats } = await engine.renderOffline(bytes, (progress) => {
                    const base = (i / total) * 100;
                    const slice = (1 / total) * 100;
                    updateExportProgress(base + progress * slice);
                });
                
                // Simpan metrik akurat untuk Summary Report
                window.lastExportStats = exportStats;

                if (isExportCancelled) {
                    updateExportStatus('Membatalkan batch...');
                    throw new Error('Dibatalkan oleh pengguna');
                }

                // Step 3: Save to Folder (or trigger download in browser)
                const originalName = file.name.replace(/\.[^.]+$/, '') + '.wav';
                if (bridge.isTauri() && targetFolder) {
                    const finalPath = targetFolder + '/' + originalName;
                    
                    if (engine.autoLufsNormalize) {
                        const tempPath = targetFolder + '/~temp_export_' + num + '.wav';
                        await bridge.writeFileData(tempPath, wavData, 'audio/wav');
                        
                        updateExportStatus(`Memproses LUFS Normalization ${num}/${total}...`);
                        const finalStats = await bridge.runFfmpegLoudnorm(tempPath, finalPath, (prog, msg) => {
                            const base = (i / total) * 100;
                            const slice = (1 / total) * 100;
                            const currentFileProg = 80 + (prog * 0.2);
                            updateExportProgress(base + (currentFileProg / 100) * slice);
                            if (msg) updateExportStatus(msg);
                        });
                        
                        try { await bridge.deleteFile(tempPath); } catch(e) {}
                        window.lastExportStats = finalStats;
                    } else {
                        await bridge.writeFileData(finalPath, wavData, 'audio/wav');
                    }
                } else {
                    // Browser fallback: trigger multiple downloads
                    await bridge.saveExportWav(wavData, originalName);
                }
                successCount++;
            } catch (err) {
                if (err.message === 'Dibatalkan oleh pengguna') {
                    throw err; // Lempar ke luar loop agar batch benar-benar berhenti
                }
                console.error(`Gagal export track ${file.name}:`, err);
                failCount++;
            }
        }

        if (successCount === 0) {
            throw new Error('Semua track gagal diproses atau rusak.');
        }

        updateExportProgress(100);
        updateExportStatus(`Batch export selesai! (${successCount} sukses, ${failCount} gagal)`);
        setTimeout(() => {
            showExportModal(false);
            if (targetFolder) {
                showToast(`Batch export selesai: ${successCount} sukses → ${targetFolder}`);
            } else {
                showToast(`Batch export selesai: ${successCount} sukses diunduh.`);
            }
        }, 1500);

        // Reload first track back for preview
        if (currentAudioUrl) {
            URL.revokeObjectURL(currentAudioUrl);
        }
        const firstUrl = await bridge.getAudioUrl(trackQueue[0]);
        currentAudioUrl = firstUrl;
        await engine.loadUrl(firstUrl);
    } catch (err) {
        showExportModal(false);
        if (err.message === 'Dibatalkan oleh pengguna') {
            showToast('Batch export dibatalkan.', false, true);
        } else {
            showToast('Batch export gagal: ' + (err.message || err), true);
        }
    }
}

// ============================================================
// SMOOTHING CONTROL
// ============================================================
function initSmoothing() {
    DOM.smoothingSlider?.addEventListener('input', (e) => {
        const val = parseFloat(e.target.value);
        engine.setSmoothing(val);
        if (DOM.smoothingValue) DOM.smoothingValue.innerText = val.toFixed(1);
    });
}

// ============================================================
// BYPASS TOGGLE (MASTERED badge)
// ============================================================
function initBypassToggle() {
    DOM.badgeMastered?.addEventListener('click', async () => {
        await engine.init();
        const isBypassed = !engine.bypassed;
        engine.setBypassed(isBypassed);

        if (DOM.badgeMastered) {
            if (isBypassed) {
                DOM.badgeMastered.classList.remove('active');
                DOM.badgeMastered.classList.add('bypassed');
                DOM.badgeMastered.innerText = 'BYPASS';
                showToast('Bypass ON — mendengarkan audio asli tanpa efek.');
            } else {
                DOM.badgeMastered.classList.remove('bypassed');
                DOM.badgeMastered.classList.add('active');
                DOM.badgeMastered.innerText = 'MASTERED';
                showToast('Mastered — semua efek aktif.');
            }
        }
    });
}

// ============================================================
// VISUALIZERS (Spectrum + Meter + GR)
// ============================================================
function initCanvas() {
    if (DOM.spectrumCanvas) {
        spectrumCtx = DOM.spectrumCanvas.getContext('2d');
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);
    }
    if (DOM.masterWaveformCanvas) {
        masterWaveformCtx = DOM.masterWaveformCanvas.getContext('2d');
        resizeMasterCanvas();
        window.addEventListener('resize', resizeMasterCanvas);
    }
    if (DOM.subbassWaveformCanvas) {
        subbassWaveformCtx = DOM.subbassWaveformCanvas.getContext('2d');
        resizeSubbassCanvas();
        window.addEventListener('resize', resizeSubbassCanvas);
    }
    if (DOM.eqCurveCanvas) {
        eqCurveCtx = DOM.eqCurveCanvas.getContext('2d');
        resizeEQCanvas();
        window.addEventListener('resize', resizeEQCanvas);
        drawEQCurve();
    }
    if (DOM.compCurveCanvas) {
        compCurveCtx = DOM.compCurveCanvas.getContext('2d');
        resizeCompCanvas();
        window.addEventListener('resize', resizeCompCanvas);
        drawCompCurve();
    }
}

function resizeCanvas() {
    if (!DOM.spectrumCanvas) return;
    DOM.spectrumCanvas.width = DOM.spectrumCanvas.clientWidth;
    DOM.spectrumCanvas.height = DOM.spectrumCanvas.clientHeight;
}

function resizeMasterCanvas() {
    if (!DOM.masterWaveformCanvas) return;
    DOM.masterWaveformCanvas.width = DOM.masterWaveformCanvas.clientWidth;
    DOM.masterWaveformCanvas.height = DOM.masterWaveformCanvas.clientHeight;
}

function resizeSubbassCanvas() {
    if (!DOM.subbassWaveformCanvas) return;
    DOM.subbassWaveformCanvas.width = DOM.subbassWaveformCanvas.clientWidth;
    DOM.subbassWaveformCanvas.height = DOM.subbassWaveformCanvas.clientHeight;
}

function resizeEQCanvas() {
    if (!DOM.eqCurveCanvas) return;
    DOM.eqCurveCanvas.width = DOM.eqCurveCanvas.clientWidth;
    DOM.eqCurveCanvas.height = DOM.eqCurveCanvas.clientHeight;
    drawEQCurve();
}

function resizeCompCanvas() {
    if (!DOM.compCurveCanvas) return;
    DOM.compCurveCanvas.width = DOM.compCurveCanvas.clientWidth;
    DOM.compCurveCanvas.height = DOM.compCurveCanvas.clientHeight;
    drawCompCurve();
}

let spectrumGradients = new Array(256);
let lastSpectrumHeight = 0;

function drawSpectrum() {
    if (!spectrumCtx || !DOM.spectrumCanvas) return;
    const w = DOM.spectrumCanvas.width, h = DOM.spectrumCanvas.height;

    if (!engine.isPlaying) {
        spectrumCtx.fillStyle = '#0b0c10';
        spectrumCtx.fillRect(0, 0, w, h);
        return;
    }

    const data = engine.getSpectrumData();
    spectrumCtx.fillStyle = '#0b0c10';
    spectrumCtx.fillRect(0, 0, w, h);

    if (h !== lastSpectrumHeight) {
        spectrumGradients = new Array(256);
        lastSpectrumHeight = h;
    }

    const startIndex = 4; // Lewati 4 bin pertama untuk menghindari visual artefak DC offset dan transien awal
    const binsToDraw = data.length - startIndex;
    const barWidth = (w / binsToDraw) * 2.5;
    let x = 0;
    for (let i = startIndex; i < data.length; i++) {
        const val = data[i];
        if (val === 0) {
            x += barWidth + 1;
            continue;
        }

        if (!spectrumGradients[val]) {
            const barH = (val / 255) * h;
            const g = spectrumCtx.createLinearGradient(0, h, 0, h - barH);
            g.addColorStop(0, 'rgba(224, 148, 18, 0.6)');
            g.addColorStop(0.5, 'rgba(224, 148, 18, 0.9)');
            g.addColorStop(1, 'rgba(240, 164, 24, 1)');
            spectrumGradients[val] = g;
        }

        const barH = (val / 255) * h;
        spectrumCtx.fillStyle = spectrumGradients[val];
        spectrumCtx.fillRect(x, h - barH, barWidth, barH);
        x += barWidth + 1;
        if (x > w) break; // Optimasi: berhenti menggambar jika sudah di luar canvas
    }
}

function drawMasterWaveform() {
    if (!masterWaveformCtx || !DOM.masterWaveformCanvas) return;
    const w = DOM.masterWaveformCanvas.width, h = DOM.masterWaveformCanvas.height;
    masterWaveformCtx.clearRect(0, 0, w, h);
    if (!engine.isPlaying) return;

    const waveData = engine.getMasterWaveformData();
    if (!waveData || waveData.length === 0) return;

    masterWaveformCtx.beginPath();
    masterWaveformCtx.lineWidth = 1.5;
    // Disamakan dengan warna puncak Spectrum Analyzer
    masterWaveformCtx.strokeStyle = 'rgba(240, 164, 24, 0.9)'; 
    const sliceWidth = w * 1.0 / waveData.length;
    let waveX = 0;
    
    // Auto-Scaling logic
    let maxAmp = 0.01;
    for (let i = 0; i < waveData.length; i++) {
        const absVal = Math.abs(waveData[i]);
        if (absVal > maxAmp) maxAmp = absVal;
    }
    const scaleFactor = maxAmp > 1.0 ? maxAmp * 1.05 : 1.05;

    for (let i = 0; i < waveData.length; i++) {
        const v = waveData[i] / scaleFactor;
        const y = (h / 2) - (v * (h / 2)); 

        if (i === 0) {
            masterWaveformCtx.moveTo(waveX, y);
        } else {
            masterWaveformCtx.lineTo(waveX, y);
        }
        waveX += sliceWidth;
    }
    masterWaveformCtx.stroke();
}

function drawSubBassWaveform() {
    if (!subbassWaveformCtx || !DOM.subbassWaveformCanvas) return;
    const w = DOM.subbassWaveformCanvas.width, h = DOM.subbassWaveformCanvas.height;

    subbassWaveformCtx.clearRect(0, 0, w, h);

    if (!engine.isPlaying) return;

    // Check if subbass is bypassed
    const btnSubBass = document.getElementById('btn-subbass-bypass');
    const isBypassed = btnSubBass && btnSubBass.classList.contains('bypassed');

    subbassWaveformCtx.beginPath();
    subbassWaveformCtx.lineWidth = 2;
    
    // Warnanya diredupkan jika non-active
    if (isBypassed) {
        subbassWaveformCtx.strokeStyle = 'rgba(255, 255, 255, 0.2)'; // Abu-abu redup
    } else {
        subbassWaveformCtx.strokeStyle = 'rgba(240, 164, 24, 0.9)'; // Disamakan persis dengan Spectrum & Master Waveform
    }
    
    // Gradient fill di bawah waveform
    const gradient = subbassWaveformCtx.createLinearGradient(0, 0, 0, h);
    if (isBypassed) {
        gradient.addColorStop(0, 'rgba(255, 255, 255, 0.05)');
        gradient.addColorStop(1, 'rgba(255, 255, 255, 0.0)');
    } else {
        gradient.addColorStop(0, 'rgba(240, 164, 24, 0.3)'); // Menyesuaikan warna gradient dengan stroke
        gradient.addColorStop(1, 'rgba(240, 164, 24, 0.0)');
    }

    subbassWaveformCtx.moveTo(0, h/2);

    if (isBypassed) {
        // Gambar garis lurus jika non-active
        subbassWaveformCtx.lineTo(w, h/2);
    } else {
        const data = engine.getSubBassWaveformData();
        if (!data || data.length === 0) return;

        // Cari amplitudo tertinggi di frame ini (Auto-Scaling)
        let maxAmp = 0.01; // nilai minimal agar tidak bagi nol
        for (let i = 0; i < data.length; i++) {
            const absVal = Math.abs(data[i]);
            if (absVal > maxAmp) maxAmp = absVal;
        }

        // Set headroom 15% dari gelombang tertinggi
        const scaleFactor = maxAmp * 1.15; 

        const sliceWidth = w * 1.0 / data.length;
        let x = 0;

        for (let i = 0; i < data.length; i++) {
            // Normalisasi secara dinamis (Auto-Scale)
            const v = data[i] / scaleFactor;
            let y = (h / 2) - (v * (h / 2));
            
            if (y < 0) y = 0;
            if (y > h) y = h;

            if (i === 0) {
                subbassWaveformCtx.moveTo(x, y);
            } else {
                subbassWaveformCtx.lineTo(x, y);
            }
            x += sliceWidth;
        }
    }
    
    subbassWaveformCtx.stroke();

    subbassWaveformCtx.lineTo(w, h/2);
    subbassWaveformCtx.lineTo(0, h/2);
    subbassWaveformCtx.fillStyle = gradient;
    subbassWaveformCtx.fill();
}

function drawEQCurve() {
    if (!eqCurveCtx || !DOM.eqCurveCanvas) return;
    const w = DOM.eqCurveCanvas.width, h = DOM.eqCurveCanvas.height;
    if (w === 0 || h === 0) return;

    eqCurveCtx.clearRect(0, 0, w, h);
    const settings = engine.getCurrentSettings();
    const mid = h / 2;
    const scale = h / 30; // ±12dB => ±12*scale px

    eqCurveCtx.beginPath();
    
    // HPF (Low Cut) representation
    const hpfFreq = settings.hpfActive !== false ? settings.hpf : 0;
    // Map 20Hz-250Hz into 0 to 15% of canvas width smoothly
    const hpfX = ((hpfFreq - 20) / 230) * (w * 0.15); 
    
    if (hpfFreq > 20 && hpfX > 0) {
        // Mulai dari titik bawah yang masuk akal (misal mendekati bottom margin, bukan mentok border)
        const startY = Math.min(h, mid + 12 * scale); // limit to -12dB visually
        eqCurveCtx.moveTo(0, startY);
        // Buat kurva bezier yang sangat mulus menuju titik 0dB (mid)
        eqCurveCtx.bezierCurveTo(
            hpfX * 0.4, startY,     // Tahan di bawah sebentar
            hpfX * 0.8, mid,        // Mulai naik dengan cepat ke tengah
            Math.max(w * 0.05, hpfX + 10), mid // Mulus masuk ke garis tengah
        );
    } else {
        eqCurveCtx.moveTo(0, mid);
    }

    // Low shelf influence (0 - 33%)
    const lowY = mid - (settings.lowActive !== false ? settings.low : 0) * scale;
    eqCurveCtx.bezierCurveTo(w * 0.15, lowY, w * 0.2, lowY, w * 0.33, mid - ((settings.lowActive !== false ? settings.low : 0) + (settings.midActive !== false ? settings.mid : 0)) / 2 * scale);
    // Mid peaking (33% - 66%)
    const midY = mid - (settings.midActive !== false ? settings.mid : 0) * scale;
    eqCurveCtx.bezierCurveTo(w * 0.4, midY, w * 0.6, midY, w * 0.66, mid - ((settings.midActive !== false ? settings.mid : 0) + (settings.highActive !== false ? settings.high : 0)) / 2 * scale);
    // High shelf (66% - 100%)
    const highY = mid - (settings.highActive !== false ? settings.high : 0) * scale;
    eqCurveCtx.bezierCurveTo(w * 0.8, highY, w * 0.85, highY, w, highY);

    const btnEq = document.getElementById('btn-eq-bypass');
    const isBypassed = btnEq && btnEq.classList.contains('bypassed');

    if (isBypassed) {
        eqCurveCtx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        eqCurveCtx.lineWidth = 2;
        eqCurveCtx.shadowBlur = 0;
    } else {
        eqCurveCtx.strokeStyle = 'rgba(240, 164, 24, 0.9)';
        eqCurveCtx.lineWidth = 2;
        eqCurveCtx.shadowColor = 'rgba(240, 164, 24, 0.5)';
        eqCurveCtx.shadowBlur = 8;
    }
    
    eqCurveCtx.stroke();
    eqCurveCtx.shadowBlur = 0;
}

function drawCompCurve() {
    if (!compCurveCtx || !DOM.compCurveCanvas) return;
    const w = DOM.compCurveCanvas.width, h = DOM.compCurveCanvas.height;
    if (w === 0 || h === 0) return;

    compCurveCtx.clearRect(0, 0, w, h);
    const settings = engine.getCurrentSettings();
    const active = settings.compActive !== false;
    const thresh = settings.cThresh; 
    const ratio = settings.cRatio;
    const makeup = settings.mkp; // Makeup gain in dB
    const knee = settings.cKnee; // Knee width in dB
    
    // Scale mapping for -60dB to 0dB
    const map = (db) => ((db + 60) / 60);
    const getX = (db) => map(db) * w;
    const getY = (db) => h - (map(db) * h);

    // Grid guide 1:1
    compCurveCtx.beginPath();
    compCurveCtx.strokeStyle = 'rgba(255, 255, 255, 0.1)';
    compCurveCtx.lineWidth = 1;
    compCurveCtx.moveTo(getX(-60), getY(-60));
    compCurveCtx.lineTo(getX(0), getY(0));
    compCurveCtx.stroke();

    compCurveCtx.beginPath();
    if (!active) {
        compCurveCtx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
        compCurveCtx.lineWidth = 2;
        compCurveCtx.moveTo(getX(-60), getY(-60));
        compCurveCtx.lineTo(getX(0), getY(0));
        compCurveCtx.stroke();
        return;
    }

    // Draw compressed curve with makeup gain
    compCurveCtx.beginPath();
    
    // Draw point by point to simulate the knee smoothly
    // X axis goes from -60 to 0
    let first = true;
    for (let input = -60; input <= 0; input += 1) {
        let output = input;
        
        // Soft Knee Calculation (standard dB math)
        // If input is below the knee floor, output = input
        // If input is above the knee ceiling, output = thresh + (input - thresh)/ratio
        // If inside the knee, use a smooth quadratic spline
        if (knee > 0 && input > (thresh - knee/2) && input < (thresh + knee/2)) {
            // Inside soft knee
            const diff = input - thresh + knee/2;
            output = input + ((1/ratio - 1) * Math.pow(diff, 2)) / (2 * knee);
        } else if (input > thresh) {
            // Above threshold & knee
            output = thresh + (input - thresh) / ratio;
        }

        // Apply Makeup Gain
        output += makeup;

        // Clip visually so line doesn't draw way out of canvas bounds unnecessarily
        // But keep going a bit above 0 visually to see the makeup offset
        
        const px = getX(input);
        const py = getY(output);

        if (first) {
            compCurveCtx.moveTo(px, py);
            first = false;
        } else {
            compCurveCtx.lineTo(px, py);
        }
    }

    compCurveCtx.strokeStyle = 'rgba(240, 164, 24, 0.9)';
    compCurveCtx.lineWidth = 2;
    compCurveCtx.shadowColor = 'rgba(240, 164, 24, 0.5)';
    compCurveCtx.shadowBlur = 8;
    compCurveCtx.stroke();
    compCurveCtx.shadowBlur = 0;
}

function mapLUFSToPct(db) {
    if (db <= -30) return 0;
    if (db <= -20) return 0 + ((db - -30) / 10) * 25;
    if (db <= -14) return 25 + ((db - -20) / 6) * 25;
    if (db <= -6) return 50 + ((db - -14) / 8) * 25;
    if (db <= 0) return 75 + ((db - -6) / 6) * 25;
    return 100;
}

function mapTPToPct(db) {
    if (db <= -30) return 0;
    if (db <= -15) return 0 + ((db - -30) / 15) * 25;
    if (db <= -6) return 25 + ((db - -15) / 9) * 25;
    if (db <= -1) return 50 + ((db - -6) / 5) * 25;
    if (db <= 0) return 75 + ((db - -1) / 1) * 25;
    return 100;
}

function updateMeters() {
    if (!engine.isPlaying) {
        if ($('meter-l-fill')) $('meter-l-fill').style.width = '0%';
        if ($('meter-r-fill')) $('meter-r-fill').style.width = '0%';
        if ($('gr-comp-fill')) $('gr-comp-fill').style.width = '0%';
        if ($('gr-lim-fill')) $('gr-lim-fill').style.width = '0%';
        if ($('gr-clip-fill')) $('gr-clip-fill').style.width = '0%';
        if ($('meter-fill')) $('meter-fill').style.width = '0%'; // Main spectrum meter
        return;
    }

    // --- Left Main Meter (Spectrum section) ---
    const levelOld = engine.getMasterLevel(); // Re-use this for the small header meter
    let pctMain = (levelOld.dbL + 48) / 51 * 100; // Using L channel roughly
    pctMain = Math.max(0, Math.min(100, pctMain));
    if (DOM.meterFill) {
        DOM.meterFill.style.width = `${pctMain}%`;
        DOM.meterFill.style.backgroundColor = levelOld.dbL > -0.1 ? '#ef4444' : '';
        DOM.meterFill.style.boxShadow = levelOld.dbL > -0.1 ? '0 0 10px #ef4444' : '0 0 10px var(--accent)';
    }

    // --- Right Sidebar Meters ---
    const level = engine.getMasterLevel();
    const mapPct = (db) => Math.max(0, Math.min(100, (db + 30) / 30 * 100)); // Map -30 to 0 dB
    const setBar = (fillId, valId, db) => {
        const fill = $(fillId); const val = $(valId);
        if (fill) {
            fill.style.width = `${mapPct(db)}%`;
            if (db > -0.1) fill.classList.add('clip'); else fill.classList.remove('clip');
        }
        if (val) val.innerText = db < -60 ? '-INF' : db.toFixed(1);
    };
    setBar('meter-l-fill', 'meter-l-val', level.dbL);
    setBar('meter-r-fill', 'meter-r-val', level.dbR);

    // Loudness (Bar Meters)
    const stats = engine.getLoudnessStats();
    
    // LUFS-I: range -30 to 0
    const lufsVal = stats.lufs < -60 ? -60 : stats.lufs;
    const lufsPct = mapLUFSToPct(lufsVal);
    if ($('stat-lufs')) $('stat-lufs').innerText = stats.lufs < -60 ? '-INF' : stats.lufs.toFixed(1);
    if ($('lufs-fill')) $('lufs-fill').style.width = `${lufsPct}%`;

    // True Peak: range -30 to 0
    const tpVal = stats.tp < -48 ? -48 : stats.tp;
    const tpPct = mapTPToPct(tpVal);
    if ($('stat-tp')) $('stat-tp').innerText = stats.tp < -48 ? '-INF' : stats.tp.toFixed(1);
    if ($('tp-fill')) {
        $('tp-fill').style.width = `${tpPct}%`;
        // Merah terang jika TP > -1 dB (clipping zone)
        $('tp-fill').style.background = stats.tp > -1 ? '#ef4444' : '#f59e0b';
    }

    // Dynamic Range: range 0 to 20
    // Cegah DR mengkalkulasi noise floor saat hening (ketika lagu baru diplay / stop)
    const isSilent = stats.tp < -48;
    const drVal = (stats.dr < 1 || isSilent) ? 0 : stats.dr;
    const drPct = Math.max(0, Math.min(100, drVal / 20 * 100));
    if ($('stat-dr')) $('stat-dr').innerText = (stats.dr < 1 || isSilent) ? '--.-' : stats.dr.toFixed(1);
    if ($('dr-fill')) $('dr-fill').style.width = `${drPct}%`;

    // Gain Reduction
    const compGR = engine.getGainReduction();
    const limGR = engine.getLimiterReduction();
    const clipGR = engine.getClipperReduction();

    const setGR = (fillId, valId, gr) => {
        const fill = $(fillId); const val = $(valId);
        if (fill) fill.style.width = `${Math.min(100, Math.abs(gr) / 12 * 100)}%`;
        if (val) val.innerText = `${gr.toFixed(1)} dB`;
    };
    setGR('gr-comp-fill', 'gr-comp-val', compGR);
    setGR('gr-lim-fill', 'gr-lim-val', limGR);
    setGR('gr-clip-fill', 'gr-clip-val', clipGR);

    const mbCompGR = engine.getMBCompGainReduction();
    if (mbCompGR) {
        setGR('mbc-meter-low', 'gr-mbc-low-val', mbCompGR.low || 0);
        setGR('mbc-meter-mid', 'gr-mbc-mid-val', mbCompGR.mid || 0);
        setGR('mbc-meter-high', 'gr-mbc-high-val', mbCompGR.high || 0);
    }

    // --- Max Meter Tracking ---
    if (engine.isPlaying) {
        if (stats.lufs > maxMeterStats.lufs && stats.lufs < 10) maxMeterStats.lufs = stats.lufs;
        if (stats.tp > maxMeterStats.tp && stats.tp < 10) maxMeterStats.tp = stats.tp;
        if (level.dbL > maxMeterStats.peakL) maxMeterStats.peakL = level.dbL;
        if (level.dbR > maxMeterStats.peakR) maxMeterStats.peakR = level.dbR;
        if (compGR < maxMeterStats.compGR) maxMeterStats.compGR = compGR; // GR is negative
        if (limGR < maxMeterStats.limGR) maxMeterStats.limGR = limGR;
        if (clipGR < maxMeterStats.clipGR) maxMeterStats.clipGR = clipGR;
    }
}

function updateTransportUI() {
    const current = engine.getCurrentTime();
    const duration = engine.getDuration();
    if (DOM.seekBar && !DOM.seekBar.matches(':active')) {
        DOM.seekBar.value = current;
        DOM.seekBar.style.setProperty('--progress', `${(current / (duration || 1)) * 100}%`);
    }
    if (DOM.timeCurrent) DOM.timeCurrent.innerText = formatTime(current);
}

function resetTransportUI() {
    if (DOM.seekBar) { DOM.seekBar.value = 0; DOM.seekBar.style.setProperty('--progress', '0%'); }
    if (DOM.timeCurrent) DOM.timeCurrent.innerText = '0:00';
}

// ============================================================
// ANIMATION LOOP
// ============================================================
function startUILoop() {
    if (animFrameId) return;
    function loop() {
        if (!engine.isPlaying || document.hidden) { 
            animFrameId = null; 
            if (!document.hidden) {
                drawSpectrum(); drawMasterWaveform(); drawSubBassWaveform(); updateMeters();
            }
            return; 
        }
        drawSpectrum();
        drawMasterWaveform();
        drawSubBassWaveform();
        updateMeters();
        updateTransportUI();

        animFrameId = requestAnimationFrame(loop);
    }
    animFrameId = requestAnimationFrame(loop);
}

// Global Visibility Listener to pause/resume rendering
document.addEventListener('visibilitychange', () => {
    if (!document.hidden && engine.isPlaying) {
        startUILoop();
    }
});

// ============================================================
// HELPERS
// ============================================================
function formatTime(sec) {
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function updatePlayIcon(playing) {
    const icon = DOM.btnPlay?.querySelector('.play-icon');
    if (icon) icon.innerHTML = playing
        ? '<path d="M6 4h4v16H6zM14 4h4v16h-4z" fill="currentColor"/>'
        : '<path d="M8 5v14l11-7z" fill="currentColor"/>';
}

function showToast(msg, isError = false, isWarning = false) {
    if (!DOM.toast) return;
    
    // Clear any existing timeout
    if (DOM.toast.timeoutId) clearTimeout(DOM.toast.timeoutId);
    
    let className = 'toast show';
    if (isError) className += ' error';
    else if (isWarning) className += ' warning';
    
    DOM.toast.className = className;
    DOM.toast.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start; gap: 12px; width:100%;">
            <span style="flex:1;">${msg}</span>
            <button onclick="document.getElementById('toast').className='toast'" style="background:transparent; border:none; color:inherit; cursor:pointer; padding:2px; margin-right:-4px; opacity: 0.8; transition: opacity 0.2s;" onmouseover="this.style.opacity='1'" onmouseout="this.style.opacity='0.8'"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg></button>
        </div>
    `;
    
    DOM.toast.timeoutId = setTimeout(() => { DOM.toast.className = 'toast'; }, 3500);
}

function showExportModal(visible) {
    if (DOM.exportModal) DOM.exportModal.className = 'modal-overlay' + (visible ? ' show' : '');
    if (!visible) updateExportProgress(0);
}
function updateExportProgress(pct) {
    if (DOM.exportProgress) DOM.exportProgress.style.width = `${pct}%`;
}
function updateExportStatus(text) {
    if (DOM.exportStatus) DOM.exportStatus.innerText = text;
}

function showCustomAlert(message, title = 'Perhatian') {
    if (!DOM.alertModal) {
        alert(message);
        return;
    }
    if (DOM.alertTitle) DOM.alertTitle.innerText = title;
    if (DOM.alertMessage) DOM.alertMessage.innerText = message;
    DOM.alertModal.classList.add('show');

    const closeAlert = () => {
        DOM.alertModal.classList.remove('show');
        DOM.btnAlertOk.removeEventListener('click', closeAlert);
    };

    if (DOM.btnAlertOk) DOM.btnAlertOk.addEventListener('click', closeAlert);
}

// BOOTSTRAP
// ============================================================
window.addEventListener('error', function(event) {
    console.error("GLOBAL ERROR:", event.error);
    alert("Terjadi Error: " + event.message + "\nSilakan periksa Console (Ctrl+Shift+I) atau kirimkan pesan error ini ke AI.");
});

let isAppInitialized = false;

document.addEventListener('DOMContentLoaded', () => {
    if (isAppInitialized) return;
    isAppInitialized = true;
    
    initDOM();
    initFaders();
    initToggles();
    initPresets();
    initTransport();
    initLoadTrack();
    initExport();
    initSummary();
    initSmoothing();
    initBypassToggle();
    initCanvas();
    initFXBar();

    // Ensure engine and UI strictly follow the default preset on startup
    if (typeof PRESETS !== 'undefined' && PRESETS.default) {
        if (DOM.presetSelector) {
            DOM.presetSelector.value = 'default';
            DOM.presetSelector.dispatchEvent(new Event('change'));
        } else {
            engine.applyPreset(PRESETS.default);
        }
    }

    // Load and Display App Version
    bridge.getAppVersion().then(version => {
        const badge = $('app-version-badge');
        if (badge && version) {
            badge.innerText = `Pro v${version}`;
            badge.style.display = 'inline-block';
        }
    });

    console.log(`[KamidiMastering] Initialized (Tauri: ${bridge.isTauri()})`);
});

// ============================================================
// FX BAR SYSTEM
// ============================================================
function initFXBar() {
    const fxNames = ['delay', 'reverb', 'widener', 'saturation', 'chorus'];

    // --- Tab switching ---
    fxNames.forEach(name => {
        const tab = $(`fx-tab-${name}`);
        const panel = $(`fx-panel-${name}`);
        if (!tab || !panel) return;

        tab.addEventListener('click', (e) => {
            // If click was on toggle, don't switch tab
            if (e.target.closest('.fx-tab-toggle')) return;
            // Deactivate all
            fxNames.forEach(n => {
                $(`fx-tab-${n}`)?.classList.remove('active');
                $(`fx-panel-${n}`)?.classList.remove('active');
            });
            tab.classList.add('active');
            panel.classList.add('active');
        });
    });

    // --- Toggle ON/OFF ---
    fxNames.forEach(name => {
        const toggle = $(`fx-toggle-${name}`);
        const panel = $(`fx-panel-${name}`);
        if (!toggle) return;

        toggle.addEventListener('click', async (e) => {
            e.stopPropagation();

            // Auto-select tab saat klik switch
            fxNames.forEach(n => {
                $(`fx-tab-${n}`)?.classList.remove('active');
                $(`fx-panel-${n}`)?.classList.remove('active');
            });
            $(`fx-tab-${name}`)?.classList.add('active');
            panel?.classList.add('active');

            const isOn = toggle.classList.contains('on');
            if (isOn) {
                toggle.classList.remove('on');
                $(`fx-tab-${name}`)?.classList.remove('fx-on');
                panel?.classList.add('disabled');
                engine.setFXActive(name, false);
                engine.markFXManual(name, true);
            } else {
                toggle.classList.add('on');
                $(`fx-tab-${name}`)?.classList.add('fx-on');
                panel?.classList.remove('disabled');
                await engine.init();
                engine.setFXActive(name, true);
                engine.markFXManual(name, true);
            }
        });

        // Initial state: disabled
        panel?.classList.add('disabled');
    });

    // --- Slider wiring ---
    function wireSlider(id, callback, format, valId) {
        const slider = $(id);
        const valEl = $(valId);
        if (!slider) return;
        slider.addEventListener('input', () => {
            const v = parseFloat(slider.value);
            callback(v);
            if (valEl) valEl.innerText = format(v);
        });
    }

    // Delay
    wireSlider('fx-delay-time', v => engine.setDelayTime(v), v => `${v.toFixed(2)}s`, 'fx-delay-time-val');
    wireSlider('fx-delay-feedback', v => engine.setDelayFeedback(v), v => `${Math.round(v*100)}%`, 'fx-delay-feedback-val');
    wireSlider('fx-delay-mix', v => engine.setDelayMix(v), v => `${Math.round(v*100)}%`, 'fx-delay-mix-val');

    // Reverb
    wireSlider('fx-reverb-decay', v => engine.setReverbDecay(v), v => `${v.toFixed(1)}s`, 'fx-reverb-decay-val');
    wireSlider('fx-reverb-mix', v => engine.setReverbMix(v), v => `${Math.round(v*100)}%`, 'fx-reverb-mix-val');

    // Widener
    wireSlider('fx-widener-width', v => engine.setWidenerWidth(v), v => `${Math.round(v*100)}%`, 'fx-widener-width-val');

    // Saturation
    wireSlider('fx-sat-drive', v => engine.setSatDrive(v), v => `${Math.round(v*100)}%`, 'fx-sat-drive-val');
    wireSlider('fx-sat-mix', v => engine.setSatMix(v), v => `${Math.round(v*100)}%`, 'fx-sat-mix-val');



    // Chorus
    wireSlider('fx-chorus-rate', v => engine.setChorusRate(v), v => `${v.toFixed(1)}Hz`, 'fx-chorus-rate-val');
    wireSlider('fx-chorus-depth', v => engine.setChorusDepth(v), v => `${Math.round(v*1000)}ms`, 'fx-chorus-depth-val');
    wireSlider('fx-chorus-mix', v => engine.setChorusMix(v), v => `${Math.round(v*100)}%`, 'fx-chorus-mix-val');

    // --- Reset Buttons ---
    const FX_DEFAULTS = {
        delay: { 'delay-time': 0.25, 'delay-feedback': 0.2, 'delay-mix': 0.15 },
        reverb: { 'reverb-decay': 1.5, 'reverb-mix': 0.10 },
        widener: { 'widener-width': 1.2 },
        saturation: { 'sat-drive': 0.15, 'sat-mix': 0.3 },

        chorus: { 'chorus-rate': 0.8, 'chorus-depth': 0.003, 'chorus-mix': 0.10 }
    };

    document.querySelectorAll('.btn-fx-reset').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.stopPropagation();
            const fxName = btn.dataset.fx;
            const defs = FX_DEFAULTS[fxName];
            if (!defs) return;
            
            for (const [key, val] of Object.entries(defs)) {
                const slider = $(`fx-${key}`);
                if (slider) {
                    slider.value = val;
                    slider.dispatchEvent(new Event('input'));
                }
            }
            showToast(`Preset default ${fxName.toUpperCase()} dipulihkan.`);
        });
    });
}


// ============================================================



    const btnNrBypass = document.getElementById('btn-nr-bypass');
    if (btnNrBypass) {
        btnNrBypass.addEventListener('click', () => {
            const isActive = btnNrBypass.classList.contains('active');
            if (isActive) {
                btnNrBypass.classList.remove('active'); btnNrBypass.classList.add('bypassed'); btnNrBypass.innerText = 'NON-ACTIVE';
                engine.toggleNoiseReduction(false);
            } else {
                btnNrBypass.classList.add('active'); btnNrBypass.classList.remove('bypassed'); btnNrBypass.innerText = 'ACTIVE';
                engine.toggleNoiseReduction(true);
            }
        });
    }

    const btnDyneqBypass = document.getElementById('btn-dyneq-bypass');
    if (btnDyneqBypass) {
        btnDyneqBypass.addEventListener('click', () => {
            const isActive = btnDyneqBypass.classList.contains('active');
            if (isActive) {
                btnDyneqBypass.classList.remove('active'); btnDyneqBypass.classList.add('bypassed'); btnDyneqBypass.innerText = 'NON-ACTIVE';
                engine.toggleDynEq(false);
            } else {
                btnDyneqBypass.classList.add('active'); btnDyneqBypass.classList.remove('bypassed'); btnDyneqBypass.innerText = 'ACTIVE';
                engine.toggleDynEq(true);
            }
        });
    }


// ============================================================
// ============================================================
// AUTO RELEASE
// ============================================================
function setupAutoButtons() {

    const btnAutoRel = document.getElementById('btn-lim-auto-rel');
    if (btnAutoRel) {
        btnAutoRel.addEventListener('click', () => {
            const isActive = !btnAutoRel.classList.contains('active');
            btnAutoRel.classList.toggle('active', isActive);
            btnAutoRel.style.background = isActive ? 'var(--accent)' : 'transparent';
            btnAutoRel.style.color = isActive ? '#000' : 'var(--text-dim)';
            btnAutoRel.style.borderColor = isActive ? 'var(--accent)' : 'var(--text-dim)';
            
            if (typeof engine.toggleLimiterAutoRelease === 'function') {
                engine.toggleLimiterAutoRelease(isActive);
            }
            
            // Disable manual fader if auto is on
            const faderRel = document.getElementById('fader-lim-release');
            if (faderRel) {
                faderRel.disabled = isActive;
                faderRel.style.opacity = isActive ? 0.3 : 1;
            }
        });
    }

    // AUTO EXPORT LUFS -14
    const btnAutoLufs = document.getElementById('btn-auto-lufs');
    if (btnAutoLufs) {
        btnAutoLufs.addEventListener('click', () => {
            const isActive = !btnAutoLufs.classList.contains('active');
            btnAutoLufs.classList.toggle('active', isActive);
            btnAutoLufs.style.background = isActive ? 'var(--accent)' : 'transparent';
            btnAutoLufs.style.color = isActive ? '#000' : 'var(--text-dim)';
            btnAutoLufs.style.borderColor = isActive ? 'var(--accent)' : 'var(--text-dim)';
            
            if (typeof engine.toggleAutoLufs === 'function') {
                engine.toggleAutoLufs(isActive);
            }
        });
    }
}

setTimeout(setupAutoButtons, 1500); // Initialize after DOM

setTimeout(() => {
    const btnGuide = document.getElementById('btn-guide');
    const guideModal = document.getElementById('guide-modal');
    const btnGuideClose = document.getElementById('btn-guide-close');
    
    if (btnGuide && guideModal && btnGuideClose) {
        btnGuide.addEventListener('click', () => {
            guideModal.classList.add('show');
        });
        btnGuideClose.addEventListener('click', () => {
            guideModal.classList.remove('show');
        });
        guideModal.addEventListener('click', (e) => {
            if (e.target === guideModal) guideModal.classList.remove('show');
        });
    }
}, 1000);

// --- KamidiLabs Donation Popup Logic ---
document.addEventListener('DOMContentLoaded', () => {
    const modalOverlay = document.getElementById('kamidi-donation-modal');
    const view1 = document.getElementById('kamidi-donation-view1');
    const view2 = document.getElementById('kamidi-donation-view2');
    
    const btnYes = document.getElementById('btn-donation-yes');
    const btnNo = document.getElementById('btn-donation-no');
    const btnClose = document.getElementById('btn-donation-close');
    
    const titleEl = document.getElementById('kamidi-donation-title');
    const textEl = document.getElementById('kamidi-donation-text');

    window.showKamidiDonationPopup = (_context) => {
        return Promise.resolve();
    };

    const closeModal = () => {
        if (modalOverlay) {
            modalOverlay.classList.add('hidden');
        }
        if (window._kamidiDonationResolve) {
            window._kamidiDonationResolve();
            window._kamidiDonationResolve = null;
        }
    };

    if (btnNo) {
        btnNo.addEventListener('click', closeModal);
    }

    if (btnClose) {
        btnClose.addEventListener('click', closeModal);
    }

    if (btnYes) {
        btnYes.addEventListener('click', () => {
            // Switch view
            view1.classList.add('hidden');
            view2.classList.remove('hidden');

            // Load QRIS Image
            const imgQris = document.getElementById('img-qris');
            const qrisLoading = document.getElementById('qris-loading');
            
            const rawUrl = 'https://raw.githubusercontent.com/snmsc83-art/KamidiLabsQris/main/KamidiLabsQris.jpg';
            if (imgQris) {
                imgQris.src = rawUrl;
                imgQris.onload = () => {
                    if (qrisLoading) qrisLoading.style.display = 'none';
                    imgQris.style.display = 'block';
                };
                imgQris.onerror = () => {
                    if (qrisLoading) qrisLoading.innerText = 'Gagal memuat QRIS. Pastikan koneksi internet Anda aktif.';
                };
            }
        });
    }
});





