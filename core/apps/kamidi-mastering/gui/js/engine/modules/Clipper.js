import { DSPNode } from './DSPNode.js';

export class Clipper extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = { active: true, threshold: 0, ...state };
        this._reduction = 0;
        this.buildNode();
    }

    buildNode() {
        this.preClipAnalyser = this.ctx.createAnalyser();
        this.preClipAnalyser.fftSize = 2048;

        this.mainGain.connect(this.preClipAnalyser);
        this.preClipAnalyser.connect(this.output);

        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }
    }

    initWorklet() {
        try { this.preClipAnalyser.disconnect(this.output); } catch(e) {}

        this.workletNode = new AudioWorkletNode(this.ctx, 'clipper-processor', {
            numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2]
        });

        this.workletNode.port.onmessage = (event) => {
            if (event.data.type === 'reduction') this._reduction = event.data.value;
        };

        this.preClipAnalyser.connect(this.workletNode);
        this.workletNode.connect(this.output);
        this._sendStateToWorklet();
        if (!this.state.active) this.setBypass(true);
    }

    _sendStateToWorklet() {
        if (!this.workletNode) return;
        this.workletNode.port.postMessage({ type: 'update', threshold: this.state.threshold });
        this.workletNode.port.postMessage({ type: 'bypass', value: !this.state.active });
    }

    update(newState) {
        this.state = { ...this.state, ...newState };
        if (newState.active !== undefined) this.setBypass(!this.state.active);
        this._sendStateToWorklet();
    }

    applyState() { this._sendStateToWorklet(); }

    getReduction() {
        if (!this.state.active) return 0;
        return this._reduction;
    }
}
