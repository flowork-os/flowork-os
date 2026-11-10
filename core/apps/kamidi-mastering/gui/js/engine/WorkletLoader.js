/**
 * WorkletLoader.js — Memuat semua AudioWorklet processors sebagai inline Blob.
 * 
 * Mengapa Blob URL?
 * - Tauri menggunakan URL scheme custom (tauri://localhost) yang tidak selalu
 *   kompatibel dengan audioWorklet.addModule() untuk file terpisah.
 * - Blob URL dijamin berhasil di semua browser dan di Tauri karena
 *   kode worklet di-embed langsung sebagai string JavaScript.
 * 
 * Cara pakai:
 *   const loader = new WorkletLoader(audioContext);
 *   await loader.loadAll();
 *   // Setelah ini semua processor terdaftar dan bisa digunakan.
 */

// ===================== INLINE WORKLET SOURCE CODE =====================

const NOISEGATE_SOURCE = `
class NoiseGateProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bypassed = false;
        this.threshold = -60;
        this.amount = 0.5;
        this.envDB = -100;
        
        this.s_thresh = this.threshold;
        this.s_amount = this.amount;
        
        this.port.onmessage = (event) => {
            const d = event.data;
            if (d.type === 'update') {
                if (d.threshold !== undefined) this.threshold = d.threshold;
                if (d.amount !== undefined) this.amount = d.amount;
            } else if (d.type === 'bypass') { this.bypassed = d.value; }
        };
    }
    process(inputs, outputs) {
        const input = inputs[0], output = outputs[0];
        if (!input || !input[0] || !output || !output[0]) return true;
        const bs = input[0].length, numCh = Math.min(input.length, output.length);
        
        const attackC = Math.exp(-1 / (0.005 * sampleRate)); // 5ms attack
        const releaseC = Math.exp(-1 / (0.100 * sampleRate)); // 100ms release
        const paramSmooth = Math.exp(-1 / (0.03 * sampleRate)); // 30ms param smooth
        
        for (let s = 0; s < bs; s++) {
            this.s_thresh = paramSmooth * this.s_thresh + (1 - paramSmooth) * this.threshold;
            this.s_amount = paramSmooth * this.s_amount + (1 - paramSmooth) * this.amount;
            
            let sumSq = 0;
            for (let ch = 0; ch < numCh; ch++) {
                sumSq += input[ch][s] * input[ch][s];
            }
            const rms = Math.sqrt(sumSq / numCh);
            const db = 20 * Math.log10(rms + 1e-30);
            
            if (db > this.envDB) {
                this.envDB = attackC * this.envDB + (1 - attackC) * db;
            } else {
                this.envDB = releaseC * this.envDB + (1 - releaseC) * db;
            }
            
            let gainDB = 0;
            if (this.envDB < this.s_thresh && this.s_amount > 0.01) {
                const diff = this.s_thresh - this.envDB;
                // Maximum reduction scales with amount: 0.5 = -40dB, 1.0 = -80dB
                const maxRange = this.s_amount * 80; 
                // Ratio/Slope scales with amount: 0.5 = 2.5:1, 1.0 = 5:1 slope
                const slope = this.s_amount * 5; 
                gainDB = -Math.min(diff * slope, maxRange);
            }
            
            const gainLin = this.bypassed ? 1.0 : Math.pow(10, gainDB / 20);
            
            for (let ch = 0; ch < numCh; ch++) {
                output[ch][s] = input[ch][s] * gainLin;
            }
        }
        return true;
    }
}
registerProcessor('noisegate-processor', NoiseGateProcessor);
`;

const DYNAMIC_EQ_SOURCE = `
class DynamicEQProcessor extends AudioWorkletProcessor {
    static get parameterDescriptors() { return []; }
    constructor(options) {
        super();
        this.sampleRate = sampleRate;
        this.bypassed = false;
        this.reductions = [0, 0, 0, 0];
        this.bands = [
            { freq: 100, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 },
            { freq: 400, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 },
            { freq: 3000, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 },
            { freq: 8000, q: 2, thresh: -8, ratio: 2, attack: 0.02, release: 0.1 }
        ];
        this.bandStates = this.bands.map(() => ({
            envLevel: 0,
            filterState: [
                { x1: 0, x2: 0, y1: 0, y2: 0 },
                { x1: 0, x2: 0, y1: 0, y2: 0 }
            ],
            detectorState: { x1: 0, x2: 0, y1: 0, y2: 0 },
            currentGainDB: 0,
            peakCoeffs: { b0: 0, b1: 0, b2: 0, a1: 0, a2: 0 },
            detCoeffs: { b0: 0, b1: 0, b2: 0, a1: 0, a2: 0 }
        }));
        this.port.onmessage = (event) => {
            const data = event.data;
            if (data.type === 'updateBands') {
                for (let i = 0; i < 4; i++) {
                    if (data.bands[i]) Object.assign(this.bands[i], data.bands[i]);
                }
            } else if (data.type === 'bypass') {
                this.bypassed = data.value;
            }
        };
    }
    computePeakingCoeffs(freq, q, gainDB, out) {
        const w0 = 2 * Math.PI * freq / this.sampleRate;
        const cosw0 = Math.cos(w0); const sinw0 = Math.sin(w0);
        const alpha = sinw0 / (2 * q);
        const A = Math.pow(10, gainDB / 40);
        const b0 = 1 + alpha * A; const b1 = -2 * cosw0; const b2 = 1 - alpha * A;
        const a0 = 1 + alpha / A; const a1 = -2 * cosw0; const a2 = 1 - alpha / A;
        out.b0 = b0/a0; out.b1 = b1/a0; out.b2 = b2/a0; out.a1 = a1/a0; out.a2 = a2/a0;
    }
    computeBandpassCoeffs(freq, q, out) {
        const w0 = 2 * Math.PI * freq / this.sampleRate;
        const cosw0 = Math.cos(w0); const sinw0 = Math.sin(w0);
        const alpha = sinw0 / (2 * q);
        const a0 = 1 + alpha;
        out.b0 = alpha/a0; out.b1 = 0; out.b2 = -alpha/a0; out.a1 = (-2*cosw0)/a0; out.a2 = (1-alpha)/a0;
    }
    processBiquad(c, s, input) {
        const out = c.b0*input + c.b1*s.x1 + c.b2*s.x2 - c.a1*s.y1 - c.a2*s.y2;
        s.x2=s.x1; s.x1=input; s.y2=s.y1; s.y1=out;
        return out;
    }
    process(inputs, outputs) {
        const input = inputs[0]; const output = outputs[0];
        if (!input || !input[0] || !output || !output[0]) return true;
        const numCh = Math.min(input.length, output.length);
        const blockSize = input[0].length;
        // HAPUS bypass internal: biarkan memproses silence agar filter IIR tidak membeku (freeze state).
        for (let ch=0;ch<numCh;ch++) output[ch].set(input[ch]);
    for (let b = 0; b < 4; b++) {
            const band = this.bands[b]; const bs = this.bandStates[b];
            this.computeBandpassCoeffs(band.freq, band.q, bs.detCoeffs);
            const attackCoeff = Math.exp(-1 / (band.attack * this.sampleRate));
            const releaseCoeff = Math.exp(-1 / (band.release * this.sampleRate));
            const gainSmooth = Math.exp(-1 / (0.005 * this.sampleRate));
            const threshLin = Math.pow(10, band.thresh / 20);
            let maxReduction = 0;
            for (let s = 0; s < blockSize; s++) {
                let monoIn = 0;
                for (let ch=0;ch<numCh;ch++) monoIn += output[ch][s];
                monoIn /= numCh;
                const detected = this.processBiquad(bs.detCoeffs, bs.detectorState, monoIn);
                const absDetected = Math.abs(detected);
                if (absDetected > bs.envLevel) bs.envLevel = attackCoeff * bs.envLevel + (1-attackCoeff) * absDetected;
                else bs.envLevel = releaseCoeff * bs.envLevel + (1-releaseCoeff) * absDetected;
                
                let targetGainDB = 0;
                const envDB = 20 * Math.log10(bs.envLevel + 1e-30);
                const overDB = envDB - band.thresh;
                if (overDB > 0) {
                    targetGainDB = -(overDB - overDB / band.ratio);
                }
                
                bs.currentGainDB = gainSmooth * bs.currentGainDB + (1 - gainSmooth) * targetGainDB;
                if (bs.currentGainDB < maxReduction) maxReduction = bs.currentGainDB;
                
                this.computePeakingCoeffs(band.freq, band.q, bs.currentGainDB, bs.peakCoeffs);
                for (let ch=0;ch<numCh;ch++) output[ch][s] = this.processBiquad(bs.peakCoeffs, bs.filterState[ch], output[ch][s]);
            }
            this.reductions[b] = maxReduction;
        }
        if (this._fc === undefined) this._fc = 0;
        this._fc++;
        if (this._fc % 8 === 0) this.port.postMessage({ type: 'reduction', values: [...this.reductions] });
        return true;
    }
}
registerProcessor('dynamic-eq-processor', DynamicEQProcessor);
`;

const COMPRESSOR_SOURCE = `
class CompressorProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bypassed = false;
        this.threshold = -24; this.ratio = 4; this.knee = 6;
        this.attack = 0.05; this.release = 0.25; this.makeupGain = 0; this.mix = 1.0;
        this.envDB = -100; this.reduction = 0;
        
        // Parameter Smoothing States
        this.s_thresh = this.threshold;
        this.s_ratio = this.ratio;
        this.s_knee = this.knee;
        this.s_makeupLin = 1.0;
        this.s_mix = this.mix;

        // Sidechain HPF (approx 130Hz) to prevent bass from pumping the compressor
        this.scHpfAlpha = 1.0 / (1.0 + (2.0 * Math.PI * 130.0) / sampleRate);
        this.scHpfPrevX = [0, 0];
        this.scHpfPrevY = [0, 0];

        this.port.onmessage = (event) => {
            const d = event.data;
            if (d.type === 'update') {
                if (d.threshold !== undefined) this.threshold = d.threshold;
                if (d.ratio !== undefined) this.ratio = d.ratio;
                if (d.knee !== undefined) this.knee = d.knee;
                if (d.attack !== undefined) this.attack = d.attack;
                if (d.release !== undefined) this.release = d.release;
                if (d.makeupGain !== undefined) this.makeupGain = d.makeupGain;
                if (d.mix !== undefined) this.mix = d.mix;
            } else if (d.type === 'bypass') { this.bypassed = d.value; }
        };
    }
    computeGain(inputDB) {
        const T=this.s_thresh, R=this.s_ratio, W=this.s_knee;
        let outputDB;
        if (W > 0) {
            const hk = W/2;
            if (inputDB < T-hk) outputDB = inputDB;
            else if (inputDB > T+hk) outputDB = T + (inputDB-T)/R;
            else { const x = inputDB-T+hk; outputDB = inputDB + ((1/R-1)*x*x)/(2*W); }
        } else {
            outputDB = inputDB < T ? inputDB : T + (inputDB-T)/R;
        }
        return outputDB - inputDB;
    }
    process(inputs, outputs) {
        const input=inputs[0], output=outputs[0];
        if (!input||!input[0]||!output||!output[0]) return true;
        const numCh = Math.min(input.length, output.length);
        const blockSize = input[0].length;
        // HAPUS bypass internal: biarkan memproses silence agar filter IIR tidak membeku (freeze state).
        const attackCoeff = Math.exp(-1/(this.attack*sampleRate));
        const releaseCoeff = Math.exp(-1/(this.release*sampleRate));
        
        const target_makeupLin = Math.pow(10, this.makeupGain/20);
        const paramSmooth = Math.exp(-1/(0.03*sampleRate));

        let maxReduction = 0;
        for (let s=0; s<blockSize; s++) {
            this.s_thresh = paramSmooth * this.s_thresh + (1 - paramSmooth) * this.threshold;
            this.s_ratio = paramSmooth * this.s_ratio + (1 - paramSmooth) * this.ratio;
            this.s_knee = paramSmooth * this.s_knee + (1 - paramSmooth) * this.knee;
            this.s_makeupLin = paramSmooth * this.s_makeupLin + (1 - paramSmooth) * target_makeupLin;
            this.s_mix = paramSmooth * this.s_mix + (1 - paramSmooth) * this.mix;
            
            const wetMix=this.s_mix, dryMix=1-this.s_mix;

            let sumSq=0;
            for(let ch=0;ch<numCh;ch++) {
                // Apply Sidechain HPF for detector only
                const scOut = this.scHpfAlpha * (this.scHpfPrevY[ch] + input[ch][s] - this.scHpfPrevX[ch]);
                this.scHpfPrevX[ch] = input[ch][s];
                this.scHpfPrevY[ch] = scOut;
                sumSq += scOut * scOut;
            }
            
            const rms = Math.sqrt(sumSq/numCh);
            const inputDB = 20*Math.log10(rms+1e-30);
            if (inputDB > this.envDB) this.envDB = attackCoeff*this.envDB + (1-attackCoeff)*inputDB;
            else this.envDB = releaseCoeff*this.envDB + (1-releaseCoeff)*inputDB;
            const grDB = this.computeGain(this.envDB);
            if (grDB < maxReduction) maxReduction = grDB;
            const gainLin = Math.pow(10, grDB/20) * this.s_makeupLin;
            for(let ch=0;ch<numCh;ch++) {
                output[ch][s] = input[ch][s]*gainLin*wetMix + input[ch][s]*dryMix;
            }
        }
        this.reduction = maxReduction;
        if (this._fc === undefined) this._fc = 0;
        this._fc++;
        if (this._fc % 8 === 0) this.port.postMessage({ type: 'reduction', value: this.reduction });
        return true;
    }
}
registerProcessor('compressor-processor', CompressorProcessor);
`;

const MULTIBAND_SOURCE = `
class MultibandProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bypassed = false;
        this.lowMidFreq = 250; this.midHighFreq = 4000;
        this.bands = {
            low:  { threshold:-24,ratio:2,knee:6,attack:0.03,release:0.2,makeupGain:0,mix:1,width:1 },
            mid:  { threshold:-24,ratio:2,knee:6,attack:0.02,release:0.15,makeupGain:0,mix:1,width:1 },
            high: { threshold:-24,ratio:2,knee:6,attack:0.01,release:0.1,makeupGain:0,mix:1,width:1 }
        };
        this.filters = {}; this._initFilters();
        this._filtersDirty = true;
        this.cachedCoeffs = {};
        this.envDB = { low:-100, mid:-100, high:-100 };
        this.reduction = { low:0, mid:0, high:0 };
        this.outLo = { l:0, r:0, g:0 };
        this.outMo = { l:0, r:0, g:0 };
        this.outHo = { l:0, r:0, g:0 };
        this.port.onmessage = (event) => {
            const d = event.data;
            if (d.type === 'update') {
                if (d.lowMidFreq !== undefined) { this.lowMidFreq = d.lowMidFreq; this._filtersDirty = true; }
                if (d.midHighFreq !== undefined) { this.midHighFreq = d.midHighFreq; this._filtersDirty = true; }
                if (d.low) Object.assign(this.bands.low, d.low);
                if (d.mid) Object.assign(this.bands.mid, d.mid);
                if (d.high) Object.assign(this.bands.high, d.high);
            } else if (d.type === 'bypass') { this.bypassed = d.value; }
        };
    }
    _initFilters() {
        const ms = () => [{ x1:0,x2:0,y1:0,y2:0 },{ x1:0,x2:0,y1:0,y2:0 }];
        this.filters = {
            lowLP1:ms(),lowLP2:ms(),lowAP1:ms(),lowAP2:ms(),
            midHP1:ms(),midHP2:ms(),midLP1:ms(),midLP2:ms(),
            highAP1:ms(),highAP2:ms(),highHP1:ms(),highHP2:ms()
        };
    }
    _bq(type, freq) {
        const w0=2*Math.PI*freq/sampleRate, c=Math.cos(w0), s=Math.sin(w0), a=s/(2*Math.SQRT1_2), a0=1+a;
        if (type==='lp') return {b0:(1-c)/2/a0,b1:(1-c)/a0,b2:(1-c)/2/a0,a1:-2*c/a0,a2:(1-a)/a0};
        if (type==='hp') return {b0:(1+c)/2/a0,b1:-(1+c)/a0,b2:(1+c)/2/a0,a1:-2*c/a0,a2:(1-a)/a0};
        return {b0:(1-a)/a0,b1:-2*c/a0,b2:(1+a)/a0,a1:-2*c/a0,a2:(1-a)/a0};
    }
    _pb(c,s,i) { const o=c.b0*i+c.b1*s.x1+c.b2*s.x2-c.a1*s.y1-c.a2*s.y2; s.x2=s.x1;s.x1=i;s.y2=s.y1;s.y1=o; return o; }
    _cg(db,b) {
        const T=b.threshold,R=b.ratio,W=b.knee;
        if (W>0) { const h=W/2; if(db<T-h)return 0; if(db>T+h)return -(db-T)*(1-1/R); const x=db-T+h; return -((1-1/R)*x*x)/(2*W); }
        return db<T?0:-(db-T)*(1-1/R);
    }
    process(inputs, outputs) {
        const input=inputs[0],output=outputs[0];
        if(!input||!input[0]||!output||!output[0]) return true;
        const bs=input[0].length, hr=input.length>1&&output.length>1;
        // HAPUS bypass internal: biarkan memproses silence agar filter IIR tidak membeku (freeze state).
        if (this._filtersDirty) {
            this.cachedCoeffs = {
                lp1: this._bq('lp', this.lowMidFreq), hp1: this._bq('hp', this.lowMidFreq),
                lp2: this._bq('lp', this.midHighFreq), hp2: this._bq('hp', this.midHighFreq),
                ap_high: this._bq('ap', this.midHighFreq),
                ap_low: this._bq('ap', this.lowMidFreq)
            };
            this._filtersDirty = false;
        }
        const { lp1, hp1, lp2, hp2, ap_high, ap_low } = this.cachedCoeffs;
        const bn=['low','mid','high'],tc={};
        for(const n of bn){const b=this.bands[n];tc[n]={ac:Math.exp(-1/(b.attack*sampleRate)),rc:Math.exp(-1/(b.release*sampleRate)),ml:Math.pow(10,b.makeupGain/20)};}
        let rl=0,rm=0,rh=0;
        for(let s=0;s<bs;s++){
            const iL=input[0][s],iR=hr?input[1][s]:iL;
            let ll=this._pb(lp1,this.filters.lowLP1[0],iL);ll=this._pb(lp1,this.filters.lowLP2[0],ll);ll=this._pb(ap_high,this.filters.lowAP1[0],ll);ll=this._pb(ap_high,this.filters.lowAP2[0],ll);
            let lr=this._pb(lp1,this.filters.lowLP1[1],iR);lr=this._pb(lp1,this.filters.lowLP2[1],lr);lr=this._pb(ap_high,this.filters.lowAP1[1],lr);lr=this._pb(ap_high,this.filters.lowAP2[1],lr);
            let ml=this._pb(hp1,this.filters.midHP1[0],iL);ml=this._pb(hp1,this.filters.midHP2[0],ml);ml=this._pb(lp2,this.filters.midLP1[0],ml);ml=this._pb(lp2,this.filters.midLP2[0],ml);
            let mr=this._pb(hp1,this.filters.midHP1[1],iR);mr=this._pb(hp1,this.filters.midHP2[1],mr);mr=this._pb(lp2,this.filters.midLP1[1],mr);mr=this._pb(lp2,this.filters.midLP2[1],mr);
            let hl=this._pb(ap_low,this.filters.highAP1[0],iL);hl=this._pb(ap_low,this.filters.highAP2[0],hl);hl=this._pb(hp2,this.filters.highHP1[0],hl);hl=this._pb(hp2,this.filters.highHP2[0],hl);
            let hhr=this._pb(ap_low,this.filters.highAP1[1],iR);hhr=this._pb(ap_low,this.filters.highAP2[1],hhr);hhr=this._pb(hp2,this.filters.highHP1[1],hhr);hhr=this._pb(hp2,this.filters.highHP2[1],hhr);
            const pb=(l,r,n,out)=>{const b=this.bands[n],t=tc[n];const rms=Math.sqrt((l*l+r*r)*0.5);const db=20*Math.log10(rms+1e-30);
                if(db>this.envDB[n])this.envDB[n]=t.ac*this.envDB[n]+(1-t.ac)*db;else this.envDB[n]=t.rc*this.envDB[n]+(1-t.rc)*db;
                const gr=this._cg(this.envDB[n],b);const gl=Math.pow(10,gr/20)*t.ml;
                const mix=b.mix!==undefined?b.mix:1.0;
                let oL=l*gl*mix+l*(1-mix),oR=r*gl*mix+r*(1-mix);const mid=(oL+oR)*0.5,side=(oL-oR)*0.5;
                out.l=mid+side*b.width;out.r=mid-side*b.width;out.g=gr;};
            pb(ll,lr,'low',this.outLo);pb(ml,mr,'mid',this.outMo);pb(hl,hhr,'high',this.outHo);
            if(this.outLo.g<rl)rl=this.outLo.g;if(this.outMo.g<rm)rm=this.outMo.g;if(this.outHo.g<rh)rh=this.outHo.g;
            output[0][s]=this.outLo.l+this.outMo.l+this.outHo.l; if(hr) output[1][s]=this.outLo.r+this.outMo.r+this.outHo.r;
        }
        this.reduction={low:rl,mid:rm,high:rh};
        if(this._fc===undefined)this._fc=0;this._fc++;
        if(this._fc%8===0)this.port.postMessage({type:'reduction',value:this.reduction});
        return true;
    }
}
registerProcessor('multiband-processor', MultibandProcessor);
`;

const CLIPPER_SOURCE = `
class ClipperProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bypassed = false; this.threshold = 0; this.reduction = 0;
        this.s_thr = 1.0;
        this.port.onmessage = (event) => {
            const d = event.data;
            if (d.type === 'update') { if (d.threshold !== undefined) this.threshold = d.threshold; }
            else if (d.type === 'bypass') { this.bypassed = d.value; }
        };
    }
    softClip(sample, thr) {
        if (thr > 1.0 || thr <= 0.001) return sample;
        return Math.tanh(sample / thr) * thr;
    }
    process(inputs, outputs) {
        const input=inputs[0],output=outputs[0];
        if(!input||!input[0]||!output||!output[0]) return true;
        const numCh=Math.min(input.length,output.length),bs=input[0].length;
        // HAPUS bypass internal: biarkan memproses silence agar filter IIR tidak membeku (freeze state).
        
        const target_thr = Math.pow(10, this.threshold/20);
        const paramSmooth = Math.exp(-1/(0.03*sampleRate));
        
        let maxRed=0;
        if(!this._prev || this._prev.length < numCh) this._prev=new Float32Array(numCh);
        for(let s=0;s<bs;s++){
            this.s_thr = paramSmooth * this.s_thr + (1 - paramSmooth) * target_thr;
            let pb=0,pa=0;
            for(let ch=0;ch<numCh;ch++){
                const i=input[ch][s]; const ai=Math.abs(i); if(ai>pb)pb=ai;
                const mid=(this._prev[ch]+i)*0.5;
                const cm=this.softClip(mid,this.s_thr), cc=this.softClip(i,this.s_thr);
                output[ch][s]=(cm+cc)*0.5;
                this._prev[ch]=i;
                const ao=Math.abs(output[ch][s]); if(ao>pa)pa=ao;
            }
            if(pb>this.s_thr&&pb>0){const r=20*Math.log10(pa/pb+1e-30);if(r<maxRed)maxRed=r;}
        }
        this.reduction=maxRed;
        if(this._fc===undefined)this._fc=0;this._fc++;
        if(this._fc%8===0)this.port.postMessage({type:'reduction',value:this.reduction});
        return true;
    }
}
registerProcessor('clipper-processor', ClipperProcessor);
`;

const LIMITER_SOURCE = `
class LimiterProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bypassed = false;
        this.ceiling=-0.3; this.thresh=-3.0; this.release=0.1; this.knee=0; this.autoRelease=false;
        this.gainDB=0; this.reduction=0;
        this.lookaheadSamples = Math.ceil(0.005*sampleRate);
        this.bufferL = new Float32Array(this.lookaheadSamples);
        this.bufferR = new Float32Array(this.lookaheadSamples);
        this.bufferIndex = 0;
        
        // Parameter Smoothing States
        this.s_cLin = Math.pow(10, this.ceiling/20);
        this.s_makeupLin = 1.0;
        this.s_kneeLin = 0;
        
        // PDR Envelope State
        this.slowEnv = 0;

        // Sidechain HPF — membuat detector mengabaikan sub-bass peaks
        // 1st-order HPF ~80Hz (6dB/oct). Sub-bass tetap lewat di audio,
        // tapi TIDAK memicu gain reduction. Standar limiter profesional.
        this.scHpfAlpha = 1.0 / (1.0 + (2.0 * Math.PI * 80.0) / sampleRate);
        this.scHpfPrevX = [0, 0]; // Previous input [L, R]
        this.scHpfPrevY = [0, 0]; // Previous output [L, R]

        this.port.onmessage = (event) => {
            const d = event.data;
            if (d.type === 'update') {
                if(d.ceiling!==undefined)this.ceiling=d.ceiling;
                if(d.thresh!==undefined)this.thresh=d.thresh;
                if(d.release!==undefined)this.release=d.release;
                if(d.knee!==undefined)this.knee=d.knee;
                if(d.autoRelease!==undefined)this.autoRelease=d.autoRelease;
            } else if (d.type === 'bypass') { this.bypassed = d.value; }
        };
    }
    softClip(sample, ceiling, kneeLin) {
        if (kneeLin <= 0.001) {
            // Soft-clip via tanh: pembulatan halus pada 10% teratas headroom
            // menggantikan hard-clip yang menciptakan harmonik sember.
            const margin = ceiling * 0.1;
            const limit = ceiling - margin;
            const absSample = Math.abs(sample);
            if (absSample <= limit) return sample;
            const over = absSample - limit;
            const shaped = limit + (margin * Math.tanh(over / margin));
            return sample > 0 ? shaped : -shaped;
        }
        const absSample = Math.abs(sample);
        const threshold = ceiling - kneeLin;
        if (absSample <= threshold) return sample;
        const over = absSample - threshold;
        const shaped = threshold + (kneeLin * Math.tanh(over / kneeLin));
        return sample > 0 ? shaped : -shaped;
    }
    process(inputs, outputs) {
        const input=inputs[0],output=outputs[0];
        if(!input||!input[0]||!output||!output[0]) return true;
        const bs=input[0].length, hr=input.length>1&&output.length>1;
        // HAPUS bypass internal: biarkan memproses silence agar filter IIR tidak membeku (freeze state).
        
        const target_cLin=Math.pow(10,this.ceiling/20);
        const target_makeupLin = 1.0; // Auto-makeup dihapus — limiter hanya menurunkan, tidak menaikkan
        const target_kneeLin = target_cLin * (1 - Math.pow(10, -this.knee/20));
        
        const slowAttC = Math.exp(-1/(0.3 * sampleRate));  // 300ms attack for slow envelope
        const slowRelC = Math.exp(-1/(1.0 * sampleRate));  // 1000ms release for slow envelope
        const attC=Math.exp(-1/(0.005*sampleRate)); // Match lookahead (5ms) to prevent pre-echo clicks
        
        const paramSmooth = Math.exp(-1/(0.03*sampleRate)); // 30ms parameter smoothing
        
        // PDR constants
        const PDR_FAST = 0.03;  // 30ms  - transient (drum/snare)
        const PDR_SLOW = 0.25;  // 250ms - sustain (bass/vocal)
        
        let maxRed=0;
        for(let s=0;s<bs;s++){
            this.s_cLin = paramSmooth * this.s_cLin + (1 - paramSmooth) * target_cLin;
            this.s_makeupLin = paramSmooth * this.s_makeupLin + (1 - paramSmooth) * target_makeupLin;
            this.s_kneeLin = paramSmooth * this.s_kneeLin + (1 - paramSmooth) * target_kneeLin;
            
            const rawL=input[0][s], rawR=hr?input[1][s]:rawL;
            const iL=rawL * this.s_makeupLin, iR=rawR * this.s_makeupLin;
            const dL=this.bufferL[this.bufferIndex], dR=this.bufferR[this.bufferIndex];
            this.bufferL[this.bufferIndex]=iL; this.bufferR[this.bufferIndex]=iR;
            this.bufferIndex=(this.bufferIndex+1)%this.lookaheadSamples;
            // Sidechain HPF: sub-bass melewati audio TANPA TERSENTUH,
            // tapi detector MENGABAIKAN sub-bass saat menghitung peak.
            // Ini mencegah pumping/kumur-kumur pada vocal saat bass menghentak.
            const scL = this.scHpfAlpha * (this.scHpfPrevY[0] + iL - this.scHpfPrevX[0]);
            this.scHpfPrevX[0] = iL; this.scHpfPrevY[0] = scL;
            const scR = hr ? (this.scHpfAlpha * (this.scHpfPrevY[1] + iR - this.scHpfPrevX[1])) : scL;
            if (hr) { this.scHpfPrevX[1] = iR; this.scHpfPrevY[1] = scR; }
            const peak = Math.max(Math.abs(scL), hr ? Math.abs(scR) : 0);
            
            // PDR (Program Dependent Release) - Track Average Sustain Energy
            if (peak > this.slowEnv) this.slowEnv = slowAttC * this.slowEnv + (1-slowAttC) * peak;
            else this.slowEnv = slowRelC * this.slowEnv + (1-slowRelC) * peak;

            let tg=0;
            if(peak>this.s_cLin&&this.s_cLin>0){tg=20*Math.log10(this.s_cLin/(peak+1e-30));}
            
            let currentRelC;
            if (this.autoRelease) {
                // Smooth interpolation: ratio of peak to slow envelope
                // ratio = 1.0 (peak == slowEnv) → full sustain release (150ms)
                // ratio >= 2.0 (peak is 2x slowEnv) → full transient release (30ms)
                const ratio = (this.slowEnv > 1e-10) ? (peak / this.slowEnv) : 1.0;
                const t = Math.max(0, Math.min(1, (ratio - 1.0)));  // 0..1 smooth blend
                const adaptiveT = PDR_SLOW + t * (PDR_FAST - PDR_SLOW); // lerp: 150ms → 30ms
                currentRelC = Math.exp(-1/(adaptiveT * sampleRate));
            } else {
                currentRelC = Math.exp(-1/(this.release * sampleRate));
            }

            if(tg<this.gainDB)this.gainDB=attC*this.gainDB+(1-attC)*tg;
            else this.gainDB=currentRelC*this.gainDB+(1-currentRelC)*tg;
            if(this.gainDB<maxRed)maxRed=this.gainDB;
            const gl=Math.pow(10,this.gainDB/20);
            let oL=dL*gl, oR=dR*gl;
            oL = this.softClip(oL, this.s_cLin, this.s_kneeLin);
            if (hr) oR = this.softClip(oR, this.s_cLin, this.s_kneeLin);
            output[0][s]=oL; if(hr)output[1][s]=oR;
        }
        this.reduction=maxRed;
        if(this._fc===undefined)this._fc=0;this._fc++;
        if(this._fc%8===0)this.port.postMessage({type:'reduction',value:this.reduction});
        return true;
    }
}
registerProcessor('limiter-processor', LimiterProcessor);
`;

const SUBBASS_SOURCE = `
class SubBassProcessor extends AudioWorkletProcessor {
    constructor() {
        super();
        this.bypassed = false;
        // Params
        this.freq = 50;
        this.drive = 30; // 0 to 100
        this.mix = 50;   // 0 to 100
        this.sub = 20;   // 0 to 100
        this.clean = 40; // 0 to 100
        
        // Smoothing states
        this.s_freq = this.freq;
        this.s_drive = this.drive;
        this.s_mix = this.mix;
        this.s_sub = this.sub;
        this.s_clean = this.clean;

        // Filter states
        const ms = () => [{ x1:0,x2:0,y1:0,y2:0 }, { x1:0,x2:0,y1:0,y2:0 }];
        this.preLpf = ms();
        this.preLpf2 = ms();
        this.postLpf = ms();
        this.postLpf2 = ms();
        this.mudCutFilter = ms(); // For clean slider
        this.subHpf = ms(); // Subsonic HPF stage 1 (Linkwitz-Riley)
        this.subHpf2 = ms(); // Subsonic HPF stage 2 (Linkwitz-Riley)
        
        // DC Blocker states
        this.dcState = [0, 0];
        this.prevPost = [0, 0];
        
        // Ducking states
        this.envFast = [0, 0];
        this.envSlow = [0, 0];
        this.duckGain = [1, 1];
        
        // Dynamic Limiter states
        this.limiterEnv = [0, 0];

        this._filtersDirty = true;
        this.cachedCoeffs = {};

        this.port.onmessage = (event) => {
            const d = event.data;
            if (d.type === 'update') {
                if (d.freq !== undefined) { this.freq = d.freq; this._filtersDirty = true; }
                if (d.drive !== undefined) this.drive = d.drive;
                if (d.mix !== undefined) this.mix = d.mix;
                if (d.sub !== undefined) this.sub = d.sub;
                if (d.clean !== undefined) this.clean = d.clean;
            } else if (d.type === 'bypass') {
                this.bypassed = d.value;
            }
        };
    }

    _bq(type, freq, q = Math.SQRT1_2) {
        const w0 = 2 * Math.PI * freq / sampleRate;
        const c = Math.cos(w0);
        const s = Math.sin(w0);
        const alpha = s / (2 * q);
        const a0 = 1 + alpha;
        if (type === 'lp') return { b0:(1-c)/2/a0, b1:(1-c)/a0, b2:(1-c)/2/a0, a1:-2*c/a0, a2:(1-alpha)/a0 };
        if (type === 'hp') return { b0:(1+c)/2/a0, b1:-(1+c)/a0, b2:(1+c)/2/a0, a1:-2*c/a0, a2:(1-alpha)/a0 };
        return {b0:1,b1:0,b2:0,a1:0,a2:0}; 
    }

    _bq_peak(freq, q, gainDB) {
        const w0 = 2 * Math.PI * freq / sampleRate;
        const c = Math.cos(w0);
        const s = Math.sin(w0);
        const alpha = s / (2 * q);
        const A = Math.pow(10, gainDB / 40);
        const b0 = 1 + alpha * A; const b1 = -2 * c; const b2 = 1 - alpha * A;
        const a0 = 1 + alpha / A; const a1 = -2 * c; const a2 = 1 - alpha / A;
        return { b0: b0/a0, b1: b1/a0, b2: b2/a0, a1: a1/a0, a2: a2/a0 };
    }

    _pb(c, s, i) { 
        const o = c.b0*i + c.b1*s.x1 + c.b2*s.x2 - c.a1*s.y1 - c.a2*s.y2; 
        s.x2 = s.x1; s.x1 = i; s.y2 = s.y1; s.y1 = o; 
        return o; 
    }

    process(inputs, outputs) {
        const input = inputs[0], output = outputs[0];
        if (!input || !input[0] || !output || !output[0]) return true;
        const numCh = Math.min(input.length, output.length);
        const bs = input[0].length;
        
        // HAPUS bypass internal: membiarkan worklet tetap memproses sinyal (walaupun 0/silence)
        // mencegah filter IIR dan DC Blocker membeku (freeze state),
        // yang menyebabkan suara menjadi aneh/berbeda saat dinyalakan kembali.
        
        if (this._filtersDirty) {
            // PRE-FILTER: Isolasi frekuensi kick drum (misal 120Hz) untuk memastikan punch masuk ke saturator
            this.cachedCoeffs.pre = this._bq('lp', 120, Math.SQRT1_2);
            // POST-FILTER: Potong hasil saturasi tajam di frekuensi target (this.freq) agar murni sub
            this.cachedCoeffs.post = this._bq('lp', this.freq, Math.SQRT1_2);
            // SUBSONIC-FILTER: Linkwitz-Riley 24dB/oct (Q=0.5 per tahap, tanpa resonansi)
            this.cachedCoeffs.subsonic = this._bq('hp', 30, 0.5);
            this._filtersDirty = false;
        }

        const paramSmooth = Math.exp(-1/(0.03*sampleRate));
        const blockSmooth = Math.exp(-bs / (0.03 * sampleRate));
        const dcR = 0.9995; // Cutoff ~3.5Hz at 44.1kHz (was 0.995 which killed 35Hz!) 

        // Ducking / Sidechain constants
        const duckAttack = Math.exp(-1 / (0.005 * sampleRate)); // 5ms
        const duckRelease = Math.exp(-1 / (0.120 * sampleRate)); // 120ms (Bouncy/Empuk)
        const fastRel = Math.exp(-1 / (0.030 * sampleRate)); // 30ms release for peak detector
        const slowAtt = Math.exp(-1 / (0.080 * sampleRate)); // 80ms SMOOTHED attack for average detector
        const slowRel = Math.exp(-1 / (0.150 * sampleRate)); // 150ms release for average detector
        
        // Limiter constants
        const limAtt = Math.exp(-1 / (0.005 * sampleRate)); // 5ms
        const limRel = Math.exp(-1 / (0.060 * sampleRate)); // 60ms (Anti mendem)
        const limCeiling = 1.0;

        // Block-Rate Smoothing untuk parameter Clean (Mud Cut)
        this.s_clean = blockSmooth * this.s_clean + (1 - blockSmooth) * this.clean;
        const mudCutDB = -(this.s_clean / 100) * 10.0;
        const mudCoeffs = this._bq_peak(150, 0.6, mudCutDB); // Turun ke 150Hz Q 0.6

        for (let s = 0; s < bs; s++) {
            this.s_drive = paramSmooth * this.s_drive + (1 - paramSmooth) * this.drive;
            this.s_mix = paramSmooth * this.s_mix + (1 - paramSmooth) * this.mix;
            this.s_sub = paramSmooth * this.s_sub + (1 - paramSmooth) * this.sub;

            // Naikkan sensitivitas Wet Mix agar lebih terdengar
            const wetMix = (this.s_mix / 100) * 2.0;
            const dryMix = 1.0;
            
            // Perbaiki: driveMul mengontrol saturasi (distorsi), subGain mengontrol VOLUME akhir sub-bass
            const subGain = (this.s_sub / 100) * 4.0; // Maksimum +12dB murni

            // ═══ MONO SUM untuk sub-bass (standar industri mastering) ═══
            // Frekuensi < 80Hz tidak bisa dilokalisasi oleh telinga manusia,
            // jadi sub-bass HARUS identik di kiri & kanan.
            let xMono = 0;
            for (let ch = 0; ch < numCh; ch++) xMono += input[ch][s];
            xMono /= numCh;
            
            // ═══ JALUR SIDECHAIN (Deteksi Transien) — MONO ═══
            let pre = this._pb(this.cachedCoeffs.pre, this.preLpf[0], xMono);
            pre = this._pb(this.cachedCoeffs.pre, this.preLpf2[0], pre);
            let absPre = Math.abs(pre);
            
            // TRUE PEAK DETECTOR (Instant attack, smooth release)
            if (absPre > this.envFast[0]) this.envFast[0] = absPre;
            else this.envFast[0] = fastRel * this.envFast[0] + (1 - fastRel) * absPre;

            // envSlow: SMOOTHED AVERAGE (80ms attack, 150ms release)
            const slowCoeff = absPre > this.envSlow[0] ? slowAtt : slowRel;
            this.envSlow[0] = slowCoeff * this.envSlow[0] + (1 - slowCoeff) * absPre;

            let isTransient = this.envFast[0] > (this.envSlow[0] * 1.5 + 0.001);
            let targetDuck = isTransient ? 0.3 : 1.0;
            
            // Smooth duck gain
            if (targetDuck < this.duckGain[0]) {
                this.duckGain[0] = duckAttack * this.duckGain[0] + (1 - duckAttack) * targetDuck;
            } else {
                this.duckGain[0] = duckRelease * this.duckGain[0] + (1 - duckRelease) * targetDuck;
            }
            
            // ═══ JALUR WET (Sub-Bass Processing) — MONO ═══
            // Mud Cut pada jalur WET saja (sinyal DRY tidak disentuh)
            let preMud = this._pb(mudCoeffs, this.mudCutFilter[0], pre);
            
            // SATURASI: harmonik genap untuk kehangatan sub bass
            const driveMul = 1.0 + (this.s_drive / 100) * 3.0; // Maks 4.0
            let driveVal = preMud * driveMul;
            let sat = Math.tanh(driveVal + 0.25 * driveVal * driveVal);
            let post = this._pb(this.cachedCoeffs.post, this.postLpf[0], sat);
            post = this._pb(this.cachedCoeffs.post, this.postLpf2[0], post);
            
            // Subsonic HPF: Linkwitz-Riley 24dB/oct (Q=0.5, tanpa resonansi)
            post = this._pb(this.cachedCoeffs.subsonic, this.subHpf[0], post);
            post = this._pb(this.cachedCoeffs.subsonic, this.subHpf2[0], post);
            
            // DC Blocker
            this.dcState[0] = post - this.prevPost[0] + dcR * this.dcState[0];
            this.prevPost[0] = post;
            
            // Wet signal dengan SEMUA gain staging diterapkan
            let wetFull = this.dcState[0] * subGain * this.duckGain[0] * wetMix;
            
            // LIMITER: setelah semua gain staging
            let absWet = Math.abs(wetFull);
            if (absWet > this.limiterEnv[0]) {
                this.limiterEnv[0] = limAtt * this.limiterEnv[0] + (1 - limAtt) * absWet;
            } else {
                this.limiterEnv[0] = limRel * this.limiterEnv[0] + (1 - limRel) * absWet;
            }
            
            let limGain = 1.0;
            if (this.limiterEnv[0] > limCeiling) {
                limGain = limCeiling / this.limiterEnv[0];
            }
            
            // Sub-bass MONO yang sudah di-limit
            let wet = wetFull * limGain;
            
            // ═══ DISTRIBUSI: DRY stereo (utuh) + WET mono (identik L/R) ═══
            for (let ch = 0; ch < numCh; ch++) {
                output[ch][s] = (input[ch][s] * dryMix) + wet;
            }
        }

        return true;
    }
}
registerProcessor('subbass-processor', SubBassProcessor);
`;

// ===================== LOADER CLASS =====================

export class WorkletLoader {
    constructor(audioContext) {
        this.ctx = audioContext;
        this._loaded = false;
    }

    _createBlobURL(source) {
        const blob = new Blob([source], { type: 'application/javascript' });
        return URL.createObjectURL(blob);
    }

    async loadAll() {
        if (this._loaded) return;

        const sources = [
            NOISEGATE_SOURCE,
            DYNAMIC_EQ_SOURCE,
            COMPRESSOR_SOURCE,
            MULTIBAND_SOURCE,
            CLIPPER_SOURCE,
            LIMITER_SOURCE,
            SUBBASS_SOURCE
        ];

        const names = [
            'NoiseGate',
            'DynamicEQ', 'Compressor', 'Multiband', 'Clipper', 'Limiter', 'SubBass'];

        for (let i = 0; i < sources.length; i++) {
            try {
                const url = this._createBlobURL(sources[i]);
                await this.ctx.audioWorklet.addModule(url);
                // setTimeout(() => URL.revokeObjectURL(url), 5000); // Dinonaktifkan sementara karena DevTools sering lambat fetch source-map sehingga muncul ERR_FILE_NOT_FOUND
                console.log(`[WorkletLoader] ✅ ${names[i]} processor loaded.`);
            } catch (e) {
                console.error(`[WorkletLoader] ❌ ${names[i]} processor GAGAL:`, e);
            }
        }

        this._loaded = true;
        console.log('[WorkletLoader] Semua AudioWorklet processor berhasil dimuat.');
    }
}
