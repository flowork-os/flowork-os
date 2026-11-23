import { DSPNode } from './DSPNode.js';

export class NoiseReduction extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            active: true,
            threshold: -60,
            amount: 0.5,
            ...state
        };
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
        this.workletNode = new AudioWorkletNode(this.ctx, 'noisegate-processor', {
            numberOfInputs: 1, numberOfOutputs: 1, outputChannelCount: [2]
        });
        
        this.mainGain.connect(this.workletNode);
        this.workletNode.connect(this.output);
        this.applyState();
    }
    
    update(newState) {
        this.state = { ...this.state, ...newState };
        if (newState.active !== undefined) {
            this.setBypass(!this.state.active);
        }
        this.applyState();
    }
    
    setBypass(bypassed) {
        this.isBypassed = bypassed;
        if (this.workletNode) {
            this.workletNode.port.postMessage({ type: 'bypass', value: bypassed });
        }
    }

    applyState() {
        if (!this.workletNode) return;
        this.workletNode.port.postMessage({
            type: 'update',
            threshold: this.state.threshold,
            amount: this.state.amount
        });
    }
}
