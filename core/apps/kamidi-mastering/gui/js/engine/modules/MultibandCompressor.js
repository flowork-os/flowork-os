import { DSPNode } from './DSPNode.js';

export class MultibandCompressor extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            active: true,
            lowMidFreq: 250, midHighFreq: 4000,
            low: { threshold: -24, ratio: 2, knee: 6, attack: 0.03, release: 0.2, makeupGain: 0, mix: 1.0, width: 1.0 },
            mid: { threshold: -24, ratio: 2, knee: 6, attack: 0.02, release: 0.15, makeupGain: 0, mix: 1.0, width: 1.0 },
            high: { threshold: -24, ratio: 2, knee: 6, attack: 0.01, release: 0.1, makeupGain: 0, mix: 1.0, width: 1.0 },
            ...state
        };
        this._reduction = { low: 0, mid: 0, high: 0 };
        this.buildNode();
    }

    buildNode() {
        this.mainGain.connect(this.output);
        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }
    }

    initWorklet() {
        try { this.mainGain.disconnect(this.output); } catch(e) {}

        this.workletNode = new AudioWorkletNode(this.ctx, 'multiband-processor', {
            numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2]
        });

        this.workletNode.port.onmessage = (event) => {
            if (event.data.type === 'reduction') this._reduction = event.data.value;
        };

        this.mainGain.connect(this.workletNode);
        this.workletNode.connect(this.output);
        this._sendStateToWorklet();
        if (!this.state.active) this.setBypass(true);
    }

    _sendStateToWorklet() {
        if (!this.workletNode) return;
        this.workletNode.port.postMessage({
            type: 'update',
            lowMidFreq: this.state.lowMidFreq, midHighFreq: this.state.midHighFreq,
            low: { ...this.state.low }, mid: { ...this.state.mid }, high: { ...this.state.high }
        });
        this.workletNode.port.postMessage({ type: 'bypass', value: !this.state.active });
    }

    update(newState) {
        if (newState.active !== undefined) this.state.active = newState.active;
        if (newState.lowMidFreq !== undefined) this.state.lowMidFreq = newState.lowMidFreq;
        if (newState.midHighFreq !== undefined) this.state.midHighFreq = newState.midHighFreq;
        if (newState.low) this.state.low = { ...this.state.low, ...newState.low };
        if (newState.mid) this.state.mid = { ...this.state.mid, ...newState.mid };
        if (newState.high) this.state.high = { ...this.state.high, ...newState.high };
        if (newState.active !== undefined) this.setBypass(!this.state.active);
        this._sendStateToWorklet();
    }

    applyState() { this._sendStateToWorklet(); }

    getReduction() {
        if (!this.state.active) return { low: 0, mid: 0, high: 0 };
        return this._reduction;
    }
}
