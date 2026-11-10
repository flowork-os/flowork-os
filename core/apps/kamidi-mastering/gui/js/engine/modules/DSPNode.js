export class DSPNode {
    constructor(ctx) {
        this.ctx = ctx;
        this.input = ctx.createGain();
        this.output = ctx.createGain();
        this.bypassGain = ctx.createGain();
        this.bypassGain.gain.value = 0; // 1 when bypassed
        this.mainGain = ctx.createGain();
        this.mainGain.gain.value = 1; // 0 when bypassed
        
        this.input.connect(this.mainGain);
        this.input.connect(this.bypassGain);
        this.bypassGain.connect(this.output);
        
        this.isBypassed = false;
    }
    
    connect(target) {
        if (target.input) {
            this.output.connect(target.input);
        } else {
            this.output.connect(target);
        }
    }
    
    disconnect() {
        this.output.disconnect();
    }
    
    setBypass(bypassed) {
        this.isBypassed = bypassed;
        const now = this.ctx.currentTime;
        const rampTime = 0.005; // 5ms crossfade — cukup cepat tapi tanpa klik/pop
        
        try {
            this.bypassGain.gain.cancelScheduledValues(0);
            this.mainGain.gain.cancelScheduledValues(0);
        } catch(e) {}

        this.bypassGain.gain.setValueAtTime(this.bypassGain.gain.value, now);
        this.mainGain.gain.setValueAtTime(this.mainGain.gain.value, now);
        this.bypassGain.gain.linearRampToValueAtTime(bypassed ? 1 : 0, now + rampTime);
        this.mainGain.gain.linearRampToValueAtTime(bypassed ? 0 : 1, now + rampTime);
    }
}
