import { DSPNode } from './DSPNode.js';

export class TransientShaper extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            active: true,
            attack: 0,
            sustain: 0,
            ...state
        };
        this.buildNode();
    }

    buildNode() {
        const ctx = this.ctx;
        this.tsIn = ctx.createGain();
        this.tsOut = ctx.createGain();
        this.tsRectifier = ctx.createWaveShaper();
        
        const rectCurve = new Float32Array(65536);
        for(let i=0; i<65536; i++) rectCurve[i] = Math.abs((i*2)/65536 - 1);
        this.tsRectifier.curve = rectCurve;
        
        this.tsFastLPF = ctx.createBiquadFilter();
        this.tsFastLPF.type = 'lowpass';
        this.tsFastLPF.frequency.value = 150; 
        
        this.tsSlowLPF = ctx.createBiquadFilter();
        this.tsSlowLPF.type = 'lowpass';
        this.tsSlowLPF.frequency.value = 20; 
        
        this.tsInvertSlow = ctx.createGain();
        this.tsInvertSlow.gain.value = -1;
        
        this.tsControlSum = ctx.createGain();
        
        // DC Blocker (highpass 2Hz) — mencegah AGC behavior dari rectified signal
        this.tsDCBlocker = ctx.createBiquadFilter();
        this.tsDCBlocker.type = 'highpass';
        this.tsDCBlocker.frequency.value = 2;
        this.tsDCBlocker.Q.value = 0.707;
        
        this.tsSensitivityGain = ctx.createGain();
        this.tsSensitivityGain.gain.value = 4; // Dikurangi dari 15 → 4 agar swing VCA terkontrol
        
        this.tsTransferCurve = ctx.createWaveShaper();
        
        // LPF 50Hz untuk memuluskan kontrol gain dan menghilangkan micro-clicks
        this.tsControlLPF = ctx.createBiquadFilter();
        this.tsControlLPF.type = 'lowpass';
        this.tsControlLPF.frequency.value = 50;
        this.tsControlLPF.Q.value = 0.5;
        
        this.tsVCA = ctx.createGain();
        this.tsVCA.gain.value = 1;

        // Control Path
        this.tsIn.connect(this.tsRectifier);
        this.tsRectifier.connect(this.tsFastLPF);
        this.tsRectifier.connect(this.tsSlowLPF);
        this.tsFastLPF.connect(this.tsControlSum);
        this.tsSlowLPF.connect(this.tsInvertSlow);
        this.tsInvertSlow.connect(this.tsControlSum);
        this.tsControlSum.connect(this.tsDCBlocker);
        this.tsDCBlocker.connect(this.tsSensitivityGain);
        this.tsSensitivityGain.connect(this.tsTransferCurve);
        this.tsTransferCurve.connect(this.tsControlLPF);
        this.tsControlLPF.connect(this.tsVCA.gain); 

        // Audio Path
        this.tsIn.connect(this.tsVCA);
        this.tsVCA.connect(this.tsOut);
        
        this.applyState();
        // SINKRONISASI BYPASS AWAL: Pastikan rute kabel fisik sesuai dengan state preset
        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }


        this.mainGain.connect(this.tsIn);
        this.tsOut.connect(this.output);
    }
    
    update(newState) {
        this.state = { ...this.state, ...newState };
        if (newState.active !== undefined) {
            this.setBypass(!this.state.active);
        }
        this.applyState();
    }
    
    applyState() {
        if (!this.tsTransferCurve) return;
        
        const attack = this.state.attack / 100;
        const sustain = this.state.sustain / 100;
        
        if (!this.state.active || (attack === 0 && sustain === 0)) {
            this.tsTransferCurve.curve = new Float32Array([0, 0]);
            return;
        }

        const curve = new Float32Array(65536);
        for (let i = 0; i < 65536; i++) {
            let x = (i * 2) / 65536 - 1; 
            let y = 0;
            
            if (x > 0) {
                let intensity = Math.pow(x, 0.5); 
                y = intensity * attack * 0.6; // Dikurangi dari 1.5 → 0.6
            } else {
                let intensity = Math.pow(Math.abs(x), 0.5);
                y = intensity * sustain * 0.6; // Dikurangi dari 1.5 → 0.6
            }
            
            if (y > 0.5) y = 0.5;   // max +3.5 dB (sebelumnya +9.5 dB)
            if (y < -0.3) y = -0.3; // max -3 dB (sebelumnya -20 dB)
            
            curve[i] = y;
        }
        this.tsTransferCurve.curve = curve;
    }
}
