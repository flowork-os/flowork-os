import { DSPNode } from './DSPNode.js';

export class Compressor extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            threshold: -24, ratio: 4, knee: 6, attack: 0.05, release: 0.25,
            makeupGain: 0, active: true, mix: 1.0,
            ...state
        };
        this._reduction = 0;
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

        this.workletNode = new AudioWorkletNode(this.ctx, 'compressor-processor', {
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
            threshold: this.state.threshold, ratio: this.state.ratio, knee: this.state.knee,
            attack: this.state.attack, release: this.state.release,
            makeupGain: this.state.makeupGain, mix: this.state.mix
        });
        this.workletNode.port.postMessage({ type: 'bypass', value: !this.state.active });
    }

    update(newState) {
        this.state = { ...this.state, ...newState };
        if (newState.active !== undefined) this.setBypass(!this.state.active);
        this._sendStateToWorklet();
    }

    applyState() { this._sendStateToWorklet(); }
    getReduction() { return this._reduction; }
}
