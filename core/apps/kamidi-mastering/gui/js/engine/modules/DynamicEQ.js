import { DSPNode } from './DSPNode.js';

export class DynamicEQ extends DSPNode {
    constructor(ctx, state = {}) {
        super(ctx);
        this.state = {
            active: true,
            bands: [
                { freq: 100, q: 2, thresh: -20, ratio: 3, attack: 0.02, release: 0.1 },
                { freq: 500, q: 2, thresh: -20, ratio: 3, attack: 0.02, release: 0.1 },
                { freq: 2000, q: 2, thresh: -20, ratio: 3, attack: 0.02, release: 0.1 },
                { freq: 8000, q: 2, thresh: -20, ratio: 3, attack: 0.02, release: 0.1 }
            ],
            ...state
        };
        this._reduction = [0, 0, 0, 0];
        this.buildNode();
    }

    buildNode() {
        this.mainGain.connect(this.output);
        if (this.state && this.state.active !== undefined) {
            this.setBypass(!this.state.active);
        }
    }

    /**
     * Dipanggil oleh AudioEngine setelah WorkletLoader.loadAll() selesai.
     */
    initWorklet() {
        try {
            this.mainGain.disconnect(this.output);
        } catch(e) {}

        this.workletNode = new AudioWorkletNode(this.ctx, 'dynamic-eq-processor', {
            numberOfInputs: 1,
            numberOfOutputs: 1,
            outputChannelCount: [2]
        });

        this.workletNode.port.onmessage = (event) => {
            if (event.data.type === 'reduction') {
                this._reduction = event.data.values;
            }
        };

        this.mainGain.connect(this.workletNode);
        this.workletNode.connect(this.output);
        this._sendStateToWorklet();

        if (!this.state.active) {
            this.setBypass(true);
        }
    }

    _sendStateToWorklet() {
        if (!this.workletNode) return;
        this.workletNode.port.postMessage({ type: 'updateBands', bands: this.state.bands });
        this.workletNode.port.postMessage({ type: 'bypass', value: !this.state.active });
    }

    update(newState) {
        if (newState.active !== undefined) this.state.active = newState.active;
        if (newState.bands) {
            for (let i = 0; i < 4; i++) {
                if (newState.bands[i]) {
                    this.state.bands[i] = { ...this.state.bands[i], ...newState.bands[i] };
                }
            }
        }
        if (newState.active !== undefined) {
            this.setBypass(!this.state.active);
        }
        this._sendStateToWorklet();
    }

    applyState() { this._sendStateToWorklet(); }

    getReduction() { return this._reduction; }
}
