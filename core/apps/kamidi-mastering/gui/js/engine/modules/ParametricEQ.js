import { DSPNode } from './DSPNode.js';

export class ParametricEQ extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            hpf: { freq: 20, active: true },
            low: { gain: 0, freq: 250, active: true },
            mid: { gain: 0, freq: 1000, q: 1, active: true },
            high: { gain: 0, freq: 4000, active: true },
            ...state
        };
        this.buildNode();
    }

    buildNode() {
        const ctx = this.ctx;
        
        this.hpfEQ = ctx.createBiquadFilter();
        this.hpfEQ.type = 'highpass'; 
        
        this.lowEQ = ctx.createBiquadFilter();
        this.lowEQ.type = 'lowshelf'; 
        
        this.midEQ = ctx.createBiquadFilter();
        this.midEQ.type = 'peaking'; 
        
        this.highEQ = ctx.createBiquadFilter();
        this.highEQ.type = 'highshelf'; 
        
        this.applyState();
        // SINKRONISASI BYPASS AWAL: Pastikan rute kabel fisik sesuai dengan state preset
        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }


        this.mainGain.connect(this.hpfEQ);
        this.hpfEQ.connect(this.lowEQ);
        this.lowEQ.connect(this.midEQ);
        this.midEQ.connect(this.highEQ);
        this.highEQ.connect(this.output);
    }
    
    update(newState) {
        // Deep merge for EQ state
        if (newState.hpf) this.state.hpf = { ...this.state.hpf, ...newState.hpf };
        if (newState.low) this.state.low = { ...this.state.low, ...newState.low };
        if (newState.mid) this.state.mid = { ...this.state.mid, ...newState.mid };
        if (newState.high) this.state.high = { ...this.state.high, ...newState.high };
        
        this.applyState();
    }
    
    applyState() {
        if (!this.hpfEQ) return;
        
        this.hpfEQ.frequency.value = this.state.hpf.active ? this.state.hpf.freq : 10;
        
        this.lowEQ.frequency.value = this.state.low.freq;
        this.lowEQ.gain.value = this.state.low.active ? this.state.low.gain : 0;
        
        this.midEQ.frequency.value = this.state.mid.freq;
        this.midEQ.Q.value = this.state.mid.q;
        this.midEQ.gain.value = this.state.mid.active ? this.state.mid.gain : 0;
        
        this.highEQ.frequency.value = this.state.high.freq;
        this.highEQ.gain.value = this.state.high.active ? this.state.high.gain : 0;
    }
}
