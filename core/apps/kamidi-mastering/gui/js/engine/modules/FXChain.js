import { DSPNode } from './DSPNode.js';

export class FXChain extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            delay:   { active: false, time: 0.25, feedback: 0.2, mix: 0.15 },
            reverb:  { active: false, decay: 1.5, mix: 0.10 },
            widener: { active: false, width: 1.2 },
            saturation: { active: false, drive: 0.15, mix: 0.3 },
            gate:    { active: false, threshold: -50, attack: 0.002, release: 0.05 },
            chorus:  { active: false, rate: 0.8, depth: 0.003, mix: 0.10 },
            ...state
        };
        this.buildNode();
    }

    _generateImpulse(decay) {
        const sr = this.ctx.sampleRate;
        const len = sr * Math.max(0.1, decay);
        const buf = this.ctx.createBuffer(2, len, sr);
        for (let ch = 0; ch < 2; ch++) {
            const d = buf.getChannelData(ch);
            for (let i = 0; i < len; i++) {
                d[i] = (Math.random() * 2 - 1) * Math.pow(1 - i / len, 2);
            }
        }
        this.convolver.buffer = buf;
    }

    _updateSatCurve(drive) {
        const k = drive * 100;
        const samples = 256;
        const curve = new Float32Array(samples);
        for (let i = 0; i < samples; i++) {
            const x = (i / (samples - 1)) * 2 - 1;
            curve[i] = ((1 + k) * x) / (1 + k * Math.abs(x));
        }
        this.waveshaper.curve = curve;
    }

    buildNode() {
        const ctx = this.ctx;
        
        // -- Saturation --
        this.satDry = ctx.createGain();
        this.satWet = ctx.createGain();
        this.waveshaper = ctx.createWaveShaper();
        this.waveshaper.oversample = '4x';
        this.satOut = ctx.createGain();

        // -- Widener (True M/S Processing) --
        this.widenerIn = ctx.createGain();
        this.widenerOut = ctx.createGain();
        this.splitter = ctx.createChannelSplitter(2);
        this.merger = ctx.createChannelMerger(2);
        
        this.midGain = ctx.createGain(); this.midGain.gain.value = 0.5;
        this.sideGain = ctx.createGain(); this.sideGain.gain.value = 0.5;
        this.sideInvert = ctx.createGain(); this.sideInvert.gain.value = -1;
        this.midLevel = ctx.createGain(); 
        this.sideLevel = ctx.createGain();
        this.sideDecodeInvert = ctx.createGain(); this.sideDecodeInvert.gain.value = -1;

        // -- Chorus --
        this.chorusDry = ctx.createGain();
        this.chorusWet = ctx.createGain();
        this.chorusOut = ctx.createGain();
        this.chorusDelay = ctx.createDelay(0.1); 
        this.chorusLFO = ctx.createOscillator(); this.chorusLFO.type = 'sine';
        this.chorusLFOGain = ctx.createGain();
        
        // -- Delay --
        this.delayDry = ctx.createGain();
        this.delayWet = ctx.createGain();
        this.delayNode = ctx.createDelay(5.0);
        this.delayFeedback = ctx.createGain();
        this.delayOut = ctx.createGain();

        // -- Reverb --
        this.reverbDry = ctx.createGain();
        this.reverbWet = ctx.createGain();
        this.convolver = ctx.createConvolver();
        this.reverbOut = ctx.createGain();

        // WIRING
        // Input -> Saturation
        this.mainGain.connect(this.satDry);
        this.mainGain.connect(this.waveshaper);
        this.waveshaper.connect(this.satWet);
        this.satDry.connect(this.satOut);
        this.satWet.connect(this.satOut);

        // Saturation -> Widener
        this.satOut.connect(this.widenerIn);
        this.widenerIn.connect(this.splitter);
        
        this.splitter.connect(this.midGain, 0); this.splitter.connect(this.midGain, 1);
        this.splitter.connect(this.sideGain, 0); this.splitter.connect(this.sideInvert, 1); this.sideInvert.connect(this.sideGain);
        this.midGain.connect(this.midLevel); this.sideGain.connect(this.sideLevel);
        
        this.midLevel.connect(this.merger, 0, 0); this.sideLevel.connect(this.merger, 0, 0);
        this.sideLevel.connect(this.sideDecodeInvert); this.midLevel.connect(this.merger, 0, 1); this.sideDecodeInvert.connect(this.merger, 0, 1);
        this.merger.connect(this.widenerOut);

        // Widener -> Chorus
        this.widenerOut.connect(this.chorusDry); this.widenerOut.connect(this.chorusDelay);
        this.chorusLFO.connect(this.chorusLFOGain); this.chorusLFOGain.connect(this.chorusDelay.delayTime);
        this.chorusLFO.start(0);
        this.chorusDelay.connect(this.chorusWet); 
        this.chorusDry.connect(this.chorusOut); 
        this.chorusWet.connect(this.chorusOut);

        // Chorus -> Delay
        this.chorusOut.connect(this.delayDry); this.chorusOut.connect(this.delayNode);
        this.delayNode.connect(this.delayFeedback); this.delayFeedback.connect(this.delayNode);
        this.delayNode.connect(this.delayWet); 
        this.delayDry.connect(this.delayOut); 
        this.delayWet.connect(this.delayOut);

        // Delay -> Reverb
        this.delayOut.connect(this.reverbDry); this.delayOut.connect(this.convolver);
        this.convolver.connect(this.reverbWet); 
        this.reverbDry.connect(this.reverbOut); 
        this.reverbWet.connect(this.reverbOut);

        // Reverb -> Output
        this.reverbOut.connect(this.output);
        
        this.applyState();
        // SINKRONISASI BYPASS AWAL: Pastikan rute kabel fisik sesuai dengan state preset
        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }

    }
    
    update(newState) {
        if (!newState) return;
        for (const name of Object.keys(newState)) {
            if (this.state[name]) {
                this.state[name] = { ...this.state[name], ...newState[name] };
            }
        }
        this.applyState();
    }
    
    applyState() {
        if (!this.satDry) return;
        const now = this.ctx.currentTime;
        const rampTime = 0.01; // 10ms crossfade untuk semua gain changes
        
        // Helper: smooth gain change dengan ramp
        const rampGain = (param, value) => {
            param.setValueAtTime(param.value, now);
            param.linearRampToValueAtTime(value, now + rampTime);
        };
        
        // Saturation — gain compensation ×0.85 pada wet path karena waveshaper menambah level
        rampGain(this.satDry.gain, 1); // PARALLEL MODE: Dry sinyal dikunci 100%
        rampGain(this.satWet.gain, this.state.saturation.active ? this.state.saturation.mix * 0.85 : 0);
        this._updateSatCurve(this.state.saturation.drive);
        
        // Widener
        rampGain(this.midLevel.gain, 1);
        rampGain(this.sideLevel.gain, this.state.widener.active ? this.state.widener.width : 1.0);
        
        // Chorus
        rampGain(this.chorusDry.gain, 1); // PARALLEL MODE: Dry sinyal dikunci 100%
        rampGain(this.chorusWet.gain, this.state.chorus.active ? this.state.chorus.mix : 0);
        this.chorusDelay.delayTime.value = 0.015;
        this.chorusLFO.frequency.value = this.state.chorus.rate;
        this.chorusLFOGain.gain.value = this.state.chorus.depth;
        
        // Delay
        rampGain(this.delayDry.gain, 1); // PARALLEL MODE: Dry sinyal dikunci 100%
        rampGain(this.delayWet.gain, this.state.delay.active ? this.state.delay.mix : 0);
        this.delayNode.delayTime.value = this.state.delay.time;
        rampGain(this.delayFeedback.gain, this.state.delay.active ? this.state.delay.feedback : 0);
        
        // Reverb
        rampGain(this.reverbDry.gain, 1); // PARALLEL MODE: Dry sinyal dikunci 100%
        rampGain(this.reverbWet.gain, this.state.reverb.active ? this.state.reverb.mix : 0);
        
        if (this.state.reverb.active) {
            // Re-generate impulse if necessary, but we avoid excessive re-generation here.
            // Ideally, only regenerate when decay changes, which is handled externally.
        }
    }
    
    updateReverbDecay(decay) {
        this.state.reverb.decay = decay;
        this._generateImpulse(decay);
    }
}
