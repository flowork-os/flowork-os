import { DSPNode } from './DSPNode.js';

export class Limiter extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            active: true, ceiling: -0.3, thresh: -0.3,
            release: 0.1, knee: 0.0, autoRelease: false,
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

        this.workletNode = new AudioWorkletNode(this.ctx, 'limiter-processor', {
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
            ceiling: this.state.ceiling, thresh: this.state.thresh,
            release: this.state.release,
            knee: this.state.knee, autoRelease: this.state.autoRelease
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
