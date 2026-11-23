import { DSPNode } from './DSPNode.js';

export class SubBass808 extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            active: true,
            freq: 50, drive: 0, sub: 20, mix: 50, clean: 40,
            ...state
        };
        this.buildNode();
    }

    buildNode() {
        const ctx = this.ctx;
        
        // WAVEFORM ANALYZER FOR SUBBASS (tetap di main thread)
        this.waveformLPF = ctx.createBiquadFilter();
        this.waveformLPF.type = 'lowpass';
        this.waveformLPF.frequency.value = 120;
        this.waveformLPF.Q.value = 0.5;

        this.waveformAnalyser = ctx.createAnalyser();
        this.waveformAnalyser.fftSize = 2048;
        this.waveformAnalyser.smoothingTimeConstant = 0; 

        // Placeholder routing before worklet loads
        this.mainGain.connect(this.output);
        this.output.connect(this.waveformLPF);
        this.waveformLPF.connect(this.waveformAnalyser);

        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }
    }

    initWorklet() {
        try { this.mainGain.disconnect(this.output); } catch(e) {}

        this.workletNode = new AudioWorkletNode(this.ctx, 'subbass-processor', {
            numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2]
        });

        this.mainGain.connect(this.workletNode);
        this.workletNode.connect(this.output);
        
        this._sendStateToWorklet();
        if (!this.state.active) this.setBypass(true);
    }

    _sendStateToWorklet() {
        if (!this.workletNode) return;
        
        const payload = {
            type: 'update',
            freq: this.state.freq,
            drive: this.state.drive,
            mix: this.state.mix,
            sub: this.state.sub,
            clean: this.state.clean
        };
        
        this.workletNode.port.postMessage(payload);
        this.workletNode.port.postMessage({ type: 'bypass', value: !this.state.active });
    }

    update(newState) {
        if (newState) this.state = { ...this.state, ...newState };
        if (newState && newState.active !== undefined) {
            this.setBypass(!this.state.active);
        }
        this._sendStateToWorklet();
    }

    applyState() {
        this._sendStateToWorklet();
    }

    getWaveformData() {
        if (!this.waveformAnalyser) return new Float32Array(0);
        const data = new Float32Array(this.waveformAnalyser.fftSize);
        this.waveformAnalyser.getFloatTimeDomainData(data);
        return data;
    }
}
