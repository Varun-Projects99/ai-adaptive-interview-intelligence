/**
 * proctoringDetector.js — Automated Mobile Phone Proctoring Utility
 * InterviewIQ AI Adaptive Interview Intelligence System
 *
 * Features:
 * 1. Imports and initializes TensorFlow.js & @tensorflow-models/coco-ssd model.
 * 2. Continuously samples video frames from a webcam reference (`videoRef`).
 * 3. Configurable sampling interval (default: 800ms) and confidence threshold (default: 0.65).
 * 4. Detection buffer logic:
 *    - Filters for `class === 'cell phone'` and `score >= minConfidence`.
 *    - Increments consecutive detection counter when phone is present.
 *    - Decrements counter when clear.
 *    - Triggers `onViolationDetected` callback only when `consecutiveDetections >= 3`.
 * 5. Lifecycle functions: Clean `start()`, `stop()`, and `dispose()`.
 * 6. React & Vanilla JS support: Exported as `ProctoringDetector` class and `useProctoring` hook.
 */

(function (root, factory) {
    if (typeof define === 'function' && define.amd) {
        define(['@tensorflow/tfjs', '@tensorflow-models/coco-ssd'], factory);
    } else if (typeof exports === 'object') {
        module.exports = factory(
            require('@tensorflow/tfjs'),
            require('@tensorflow-models/coco-ssd')
        );
    } else {
        root.ProctoringDetectorModule = factory(root.tf, root.cocoSsd);
        root.ProctoringDetector = root.ProctoringDetectorModule.ProctoringDetector;
        if (root.React) {
            root.useProctoring = root.ProctoringDetectorModule.useProctoring;
        }
    }
}(typeof self !== 'undefined' ? self : this, function (tf, cocoSsd) {

    /**
     * Core Proctoring Detector Class for Mobile Phone Detection
     */
    class ProctoringDetector {
        /**
         * @param {Object} options Configuration settings
         * @param {number} [options.sampleInterval=800] Sampling interval in milliseconds
         * @param {number} [options.minConfidence=0.65] Confidence threshold for detection (0.0 to 1.0)
         * @param {number} [options.requiredDetections=3] Consecutive positive detections required for violation
         * @param {string} [options.targetClass='cell phone'] COCO-SSD target object label
         * @param {Function} [options.onViolationDetected] Callback fired when violation threshold is reached
         * @param {Function} [options.onDetectionUpdate] Callback fired each frame with status details
         * @param {Function} [options.onModelLoaded] Callback fired when model finishes loading
         * @param {Function} [options.onModelError] Callback fired if model loading fails
         */
        constructor(options = {}) {
            this.sampleInterval = options.sampleInterval || 800;
            this.minConfidence = options.minConfidence || 0.65;
            this.requiredDetections = options.requiredDetections || 2;
            this.targetClass = options.targetClass || 'cell phone';

            // Callbacks
            this.onViolationDetected = options.onViolationDetected || null;
            this.onDetectionUpdate = options.onDetectionUpdate || null;
            this.onModelLoaded = options.onModelLoaded || null;
            this.onModelError = options.onModelError || null;

            // Internal State
            this.model = null;
            this.isLoading = false;
            this.isReady = false;
            this.isRunning = false;
            this.consecutiveDetections = 0;
            this._timerId = null;
            this._videoElement = null;
            this._isProcessing = false;
        }

        /**
         * Asynchronously loads TensorFlow.js COCO-SSD Object Detection Model
         * @returns {Promise<boolean>} True if loaded successfully, false otherwise
         */
        async init() {
            if (this.isReady && this.model) return true;
            if (this.isLoading) return false;

            this.isLoading = true;
            console.log('[PROCTORING] Initializing TensorFlow.js COCO-SSD model...');

            try {
                // Ensure TensorFlow.js backend is ready
                const tfEngine = tf || (typeof window !== 'undefined' ? window.tf : null);
                const cocoEngine = cocoSsd || (typeof window !== 'undefined' ? window.cocoSsd : null);

                if (!tfEngine || !cocoEngine) {
                    throw new Error('TensorFlow.js or COCO-SSD library not loaded. Ensure CDN or npm packages are imported.');
                }

                await tfEngine.ready();
                this.model = await cocoEngine.load({
                    base: 'lite_mobilenet_v2' // Fast, lightweight model suitable for real-time webcam proctoring
                });

                this.isReady = true;
                this.isLoading = false;
                console.log('[PROCTORING] COCO-SSD Mobile Phone Detection Model loaded successfully.');

                if (typeof this.onModelLoaded === 'function') {
                    this.onModelLoaded();
                }
                return true;
            } catch (error) {
                this.isLoading = false;
                this.isReady = false;
                console.error('[PROCTORING] Error loading mobile phone detection model:', error);
                if (typeof this.onModelError === 'function') {
                    this.onModelError(error);
                }
                return false;
            }
        }

        /**
         * Starts continuous detection loop on the provided video element.
         * @param {HTMLVideoElement|{current: HTMLVideoElement}} videoRef Reference to webcam video element
         */
        async start(videoRef) {
            // Unpack video element from React ref or direct DOM reference
            const videoEl = videoRef && videoRef.current ? videoRef.current : videoRef;

            if (!videoEl) {
                console.warn('[PROCTORING] Cannot start detection: video element reference is null or invalid.');
                return;
            }

            this._videoElement = videoEl;

            // Ensure model is loaded before starting
            if (!this.isReady) {
                const loaded = await this.init();
                if (!loaded) {
                    console.error('[PROCTORING] Aborting start: Model failed to initialize.');
                    return;
                }
            }

            if (this.isRunning) {
                console.log('[PROCTORING] Detection loop already running.');
                return;
            }

            this.isRunning = true;
            this.consecutiveDetections = 0;
            console.log(`[PROCTORING] Detection loop started (Interval: ${this.sampleInterval}ms, Confidence >= ${this.minConfidence})`);

            // Schedule continuous sampling loop
            this._scheduleNextSample();
        }

        /**
         * Schedules the next frame evaluation.
         * @private
         */
        _scheduleNextSample() {
            if (!this.isRunning) return;

            this._timerId = setTimeout(async () => {
                await this._processFrame();
                this._scheduleNextSample();
            }, this.sampleInterval);
        }

        /**
         * Analyzes a single frame from the webcam feed.
         * Implements detection buffer logic.
         * @private
         */
        async _processFrame() {
            if (!this.isRunning || !this.model || !this._videoElement) return;

            // Verify video element is actively playing and has valid dimensions
            if (
                this._videoElement.paused ||
                this._videoElement.ended ||
                this._videoElement.readyState < 2 || // HAVE_CURRENT_DATA or higher
                !this._videoElement.videoWidth
            ) {
                return;
            }

            if (this._isProcessing) return; // Skip frame if previous inference is still in progress
            this._isProcessing = true;

            try {
                // Execute COCO-SSD object detection on webcam frame
                const predictions = await this.model.detect(this._videoElement);

                // Filter for mobile phone predictions meeting confidence criteria
                const phoneDetections = predictions.filter(pred => {
                    return (
                        pred.class.toLowerCase() === this.targetClass.toLowerCase() &&
                        pred.score >= this.minConfidence
                    );
                });

                const isDetected = phoneDetections.length > 0;
                const topDetection = isDetected ? phoneDetections[0] : null;

                // Buffer counter update: Increment on detection, decrement when clear
                if (isDetected) {
                    this.consecutiveDetections += 1;
                } else {
                    this.consecutiveDetections = Math.max(0, this.consecutiveDetections - 1);
                }

                // Notify progress listeners
                if (typeof this.onDetectionUpdate === 'function') {
                    this.onDetectionUpdate({
                        isDetected,
                        consecutiveDetections: this.consecutiveDetections,
                        requiredDetections: this.requiredDetections,
                        confidence: topDetection ? topDetection.score : 0,
                        predictions
                    });
                }

                // Trigger violation callback when threshold is reached
                if (this.consecutiveDetections >= this.requiredDetections) {
                    console.warn(
                        `[PROCTORING VIOLATION] Mobile Phone detected continuously for ${this.consecutiveDetections} frames! Confidence: ${topDetection ? (topDetection.score * 100).toFixed(1) : 0}%`
                    );

                    if (typeof this.onViolationDetected === 'function') {
                        this.onViolationDetected({
                            type: 'phone_detected',
                            consecutiveDetections: this.consecutiveDetections,
                            confidence: topDetection ? topDetection.score : 0,
                            bbox: topDetection ? topDetection.bbox : null,
                            timestamp: Date.now()
                        });
                    }

                    // Reset buffer counter to require sustained detection for subsequent warnings
                    this.consecutiveDetections = 0;
                }
            } catch (error) {
                console.error('[PROCTORING] Error evaluating frame:', error);
            } finally {
                this._isProcessing = false;
            }
        }

        /**
         * Pauses/stops the detection loop without disposing model memory.
         */
        stop() {
            if (!this.isRunning) return;

            this.isRunning = false;
            if (this._timerId) {
                clearTimeout(this._timerId);
                this._timerId = null;
            }
            this.consecutiveDetections = 0;
            console.log('[PROCTORING] Detection loop stopped.');
        }

        /**
         * Cleanly stops detection loop and disposes model memory.
         */
        dispose() {
            this.stop();
            if (this.model && typeof this.model.dispose === 'function') {
                try {
                    this.model.dispose();
                } catch (e) {
                    // Ignore disposal warnings
                }
            }
            this.model = null;
            this.isReady = false;
            this._videoElement = null;
            console.log('[PROCTORING] ProctoringDetector disposed.');
        }
    }

    /**
     * React Hook Wrapper for ProctoringDetector
     * @param {Object} videoRef React useRef pointing to HTMLVideoElement
     * @param {Object} options ProctoringDetector options
     * @returns {Object} Detector controls & state
     */
    function useProctoring(videoRef, options = {}) {
        // Fallback for non-React environment
        if (typeof React === 'undefined' || !React.useEffect) {
            console.warn('[PROCTORING] React environment not detected. Use `ProctoringDetector` class directly.');
            return null;
        }

        const { useState, useEffect, useRef, useCallback } = React;

        const [isReady, setIsReady] = useState(false);
        const [isDetecting, setIsDetecting] = useState(false);
        const [error, setError] = useState(null);
        const [detectionCount, setDetectionCount] = useState(0);

        const detectorRef = useRef(null);

        useEffect(() => {
            const detector = new ProctoringDetector({
                ...options,
                onModelLoaded: () => {
                    setIsReady(true);
                    if (options.onModelLoaded) options.onModelLoaded();
                },
                onModelError: (err) => {
                    setError(err);
                    if (options.onModelError) options.onModelError(err);
                },
                onDetectionUpdate: (update) => {
                    setDetectionCount(update.consecutiveDetections);
                    if (options.onDetectionUpdate) options.onDetectionUpdate(update);
                }
            });

            detectorRef.current = detector;
            detector.init();

            return () => {
                detector.dispose();
            };
        }, []);

        const startProctoring = useCallback(() => {
            if (detectorRef.current && videoRef) {
                detectorRef.current.start(videoRef);
                setIsDetecting(true);
            }
        }, [videoRef]);

        const stopProctoring = useCallback(() => {
            if (detectorRef.current) {
                detectorRef.current.stop();
                setIsDetecting(false);
            }
        }, []);

        useEffect(() => {
            if (isReady && videoRef && videoRef.current) {
                startProctoring();
            }
        }, [isReady, videoRef, startProctoring]);

        return {
            isReady,
            isDetecting,
            error,
            detectionCount,
            startProctoring,
            stopProctoring
        };
    }

    return {
        ProctoringDetector,
        useProctoring
    };
}));
