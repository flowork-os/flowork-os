/**
 * Smart Logic - Cross-Module Intelligence Middleware
 * Handles automatic parameter compensation to maintain tonal balance and dynamics.
 */
export class SmartLogic {
    /**
     * @param {Object} audioEngine - Reference to the AudioEngine instance
     */
    constructor(audioEngine) {
        this.engine = audioEngine;
    }

    /**
     * Called when the Sub Bass Drive fader changes
     * @param {number} val - The new Sub Bass Drive value
     */
    onSubBassDriveChange(val) {
        // 1. Set Base Value
        if (typeof this.engine.setSubBassDrive === 'function') {
            this.engine.setSubBassDrive(val);
        }

        // 2. Kalkulasi Offset untuk Mud Cut (Target: Clean parameter internal)
        // Semakin besar drive, semakin besar Clean offset
        const cleanOffset = (val / 100) * 30; // Max +30 tambahan Clean
        if (typeof this.engine.setSubBassCleanOffset === 'function') {
            this.engine.setSubBassCleanOffset(cleanOffset);
        }

        // 3. Kalkulasi Offset untuk Gain Compensation (via Limiter Threshold atau internal SubBass mix)
        const gainCompOffset = -(val * 0.15); // Turunkan gain
        if (typeof this.engine.setSubBassGainOffset === 'function') {
            this.engine.setSubBassGainOffset(gainCompOffset);
        }
    }

    /**
     * Called when the EQ High Gain fader changes
     * @param {number} val - The new EQ High Gain value
     */
    onEQHighChange(val) {
        if (typeof this.engine.setEQHigh === 'function') {
            this.engine.setEQHigh(val); // Update Base
        }
        
        // Kompensasi Threshold Adaptif (Reverse Math) untuk Dynamic EQ band 4 kHz
        // Mencegah Acoustic Over-Compression saat sinyal High di-boost ekstrem.
        if (typeof this.engine.setDynEqThreshOffset === 'function') {
            if (val > 2) {
                const dynOffset = (val / 12) * 6; // Positif: Naikkan Threshold maksimal +6 dB
                this.engine.setDynEqThreshOffset(2, dynOffset); // Band 2 (index 2 = 3kHz-4kHz)
            } else {
                this.engine.setDynEqThreshOffset(2, 0);
            }
        }
    }
    
    /**
     * Called by the controller after a preset is loaded
     * Recalculates all offsets based on the baseSettings
     */
    recalculateAll() {
        if (typeof this.engine.getCurrentSettings !== 'function') return;
        
        // Ambil Base Value terbaru dari AudioEngine
        const base = this.engine.getCurrentSettings(); // getCurrentSettings mengembalikan baseSettings
        
        if (base && base.subBass && typeof base.subBass.drive !== 'undefined') {
            this.onSubBassDriveChange(base.subBass.drive);
        }
        
        if (base && typeof base.high !== 'undefined') {
            this.onEQHighChange(base.high);
        }
    }
}
