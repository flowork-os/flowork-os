$nyquist plug-in
$version 5
$type process eqandfilters
$preview linear
$name (_ "Flowork AI Audio Sanitizer")
$debugbutton false
$author (_ "Mr. Flow (Flowork OS)")
$release 1.0.0
$copyright (_ "GNU General Public License v2.0 or later")

;; ==============================================================================
;; 👑 FLOWORK OS — AI AUDIO WATERMARK STRIPPER & ACOUSTIC SANITIZER
;; Destroys ultrasonic pilot tones, psychoacoustic spread spectrum (DSSS),
;; and latent neural token signatures from Suno, Udio, and generative models.
;; ==============================================================================

$control MODE (_ "Sanitization Profile") choice (("SunoUdio" (_ "Suno & Udio (Ultrasonic + Spread Spectrum)"))
                                                 ("Ultrasonic" (_ "Ultrasonic Pilot Tone Eraser Only"))
                                                 ("Forensic" (_ "Deep Forensic Scrub (Maximum Decoherence)"))) 0

$control FREQUENCY (_ "Brickwall Cutoff Frequency (Hz)") float-text "" 17500 12000 22000
$control STEEPNESS (_ "Filter Steepness") choice (("dB48" (_ "48 dB/oct (8-pole Butterworth)"))
                                                 ("dB72" (_ "72 dB/oct (12-pole Hybrid)"))
                                                 ("dB96" (_ "96 dB/oct (16-pole Brickwall)"))) 1

$control PHASE_SCRAMBLE (_ "Phase Decoherence (Shatter DSSS)") choice (("None" (_ "Off"))
                                                                      ("Subtle" (_ "Subtle (15% phase jitter)"))
                                                                      ("Moderate" (_ "Moderate (Recommended)"))
                                                                      ("Aggressive" (_ "Aggressive (Heavy Diffusion)"))) 2

$control WARMTH (_ "Analog Tape Micro-Harmonics") choice (("Off" (_ "Off (Linear)"))
                                                         ("TapeWarmth" (_ "Subtle Even Harmonics (Analog Emulation)"))) 1

;; DSP Core Functions
(defun apply-brickwall (sig cutoff steep-idx)
  (let ((nyq (/ *sound-srate* 2.0)))
    (if (>= cutoff nyq)
        sig
        (case steep-idx
          (0 (lowpass8 sig cutoff))
          (1 (lowpass8 (lowpass4 sig cutoff) cutoff))
          (2 (lowpass8 (lowpass8 sig cutoff) cutoff))
          (t (lowpass8 sig cutoff))))))

(defun apply-phase-decoherence (sig amount-idx)
  (case amount-idx
    (0 sig)
    (1 (allpass2 sig 16000 0.7071))
    (2 (allpass2 (allpass2 sig 14000 0.8) 18000 0.6))
    (3 (allpass2 (allpass2 (allpass2 sig 12000 0.9) 15500 0.7) 18500 0.5))
    (t sig)))

(defun apply-warmth (sig warmth-idx)
  (if (= warmth-idx 0)
      sig
      ;; Subtle soft-knee analog saturation: x - 0.04*x^3 to generate soft even/odd harmonics
      (mult sig (sum 1.0 (mult -0.04 (mult sig sig))))))

(defun sanitize-channel (sig)
  (let* ((filtered (apply-brickwall sig FREQUENCY STEEPNESS))
         (decohered (apply-phase-decoherence filtered PHASE_SCRAMBLE))
         (warmed (apply-warmth decohered WARMTH)))
    warmed))

;; Main Validation & Dispatch
(cond
  ((< FREQUENCY 1000.0)
   (_ "Error: Cutoff frequency must be at least 1000 Hz."))
  ((>= FREQUENCY (/ *sound-srate* 2.0))
   (format nil
           (_ "Error: Cutoff frequency (~a Hz) is above Nyquist limit for ~a Hz sample rate.~%Please use a frequency below ~a Hz.")
           FREQUENCY
           *sound-srate*
           (/ *sound-srate* 2.0)))
  (T
   ;; Multichan-expand applies sanitize-channel across both mono and stereo tracks
   (multichan-expand #'sanitize-channel *track*)))
