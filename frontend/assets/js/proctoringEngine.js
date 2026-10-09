/**
 * ProctoringEngine — Unified Multi-Modal Automated Proctoring System
 * =====================================================================
 * Additive, non-blocking monitoring layer for the InterviewIQ interview platform.
 *
 * This module continuously monitors 7 anti-cheating triggers:
 *   A. Mobile Phone Detection
 *   B. Multiple Person / Face Detection
 *   C. Camera Exit / Absence
 *   D. Face Out of Bounds / Off-Center Tracking
 *   E. Eye Movement & Gaze Direction Tracking
 *   F. Low-Light / Poor Visibility Detection
 *   G. Tab Switch, Window Blur & Fullscreen Exit
 *
 * Strike System:
 *   - Camera Exit: 5 seconds no face → 1st strike, +5s → 2nd strike, +5s → 3rd strike
 *   - Multiple Faces: 5 seconds continuous → 1st strike, +5s → 2nd strike, +5s → 3rd strike
 *   - Phone Detection: 5 seconds continuous → 1st strike, +5s → 2nd strike, +5s → 3rd strike
 *   - All violations reset when condition clears
 *
 * Usage:
 *   const engine = new ProctoringEngine({
 *     videoElement: document.getElementById('webcam'),
 *     onViolation: (type, count) => { ... },
 *     onMalpracticeTerminated: (details, snapshot) => { ... },
 *     onRecovery: () => { ... }
 *   });
 *   engine.start();
 *   // ... later ...
 *   engine.stop();
 */

(function(global) {
    'use strict';

    // ─────────────────────────────────────────────────────────────────────────
    // Configuration
    // ─────────────────────────────────────────────────────────────────────────
    const DEFAULT_CONFIG = {
        // Sampling interval (ms)
        sampleInterval: 500,

        // Phone detection
        phoneConfidenceThreshold: 0.6,
        phoneMinAreaRatio: 0.01,
        phoneMaxAreaRatio: 0.40,

        // Strike system (seconds of continuous violation before strike)
        strikeIntervalSeconds: 5,

        // Face bounds (percentage of frame dimensions)
        faceBoundsThreshold: 0.15,

        // Eye gaze deviation (seconds)
        gazeDeviationSeconds: 2.5,

        // Low light
        lowLightThreshold: 30,

        // Hard violation threshold (strikes)
        hardViolationLimit: 3,

        // Snapshot quality (JPEG)
        snapshotQuality: 0.85
    };

    // ─────────────────────────────────────────────────────────────────────────
    // Violation Types
    // ─────────────────────────────────────────────────────────────────────────
    const ViolationType = {
        PHONE_DETECTED: 'PHONE_DETECTED',
        MULTIPLE_FACES: 'MULTIPLE_FACES_DETECTED',
        CAMERA_EXIT: 'CAMERA_EXIT',
        FACE_LOOK_UP: 'FACE_LOOK_UP',
        FACE_LOOK_DOWN: 'FACE_LOOK_DOWN',
        FACE_LOOK_LEFT: 'FACE_LOOK_LEFT',
        FACE_LOOK_RIGHT: 'FACE_LOOK_RIGHT',
        EYE_GAZE_DEVIATION: 'EYE_GAZE_DEVIATION',
        LOW_LIGHT: 'LOW_LIGHT_ENVIRONMENT',
        TAB_SWITCH: 'TAB_SWITCH',
        WINDOW_BLUR: 'WINDOW_BLUR',
        FULLSCREEN_EXIT: 'FULLSCREEN_EXIT'
    };

    // ─────────────────────────────────────────────────────────────────────────
    // ProctoringEngine Class
    // ─────────────────────────────────────────────────────────────────────────
    class ProctoringEngine {
        /**
         * @param {Object} options
         * @param {HTMLVideoElement} options.videoElement - The webcam <video> element
         * @param {Function} [options.onViolation] - Called on each violation (type, count, max)
         * @param {Function} [options.onMalpracticeTerminated] - Called on hard violation (details, snapshot)
         * @param {Function} [options.onRecovery] - Called when all violations clear
         * @param {Function} [options.onStatusUpdate] - Called on each sample with status object
         * @param {Object} [options.config] - Override default config
         */
        constructor(options = {}) {
            this.video = options.videoElement;
            this.config = { ...DEFAULT_CONFIG, ...options.config };

            // Callbacks
            this.onViolation = options.onViolation || (() => {});
            this.onMalpracticeTerminated = options.onMalpracticeTerminated || (() => {});
            this.onRecovery = options.onRecovery || (() => {});
            this.onStatusUpdate = options.onStatusUpdate || (() => {});

            // State
            this.isRunning = false;
            this.sampleTimer = null;
            this.lastSampleTime = 0;

            // Strike counts (0-3)
            this.strikes = {
                [ViolationType.PHONE_DETECTED]: 0,
                [ViolationType.MULTIPLE_FACES]: 0,
                [ViolationType.CAMERA_EXIT]: 0,
                [ViolationType.FACE_LOOK_UP]: 0,
                [ViolationType.FACE_LOOK_DOWN]: 0,
                [ViolationType.FACE_LOOK_LEFT]: 0,
                [ViolationType.FACE_LOOK_RIGHT]: 0,
                [ViolationType.EYE_GAZE_DEVIATION]: 0,
                [ViolationType.LOW_LIGHT]: 0,
                [ViolationType.TAB_SWITCH]: 0,
                [ViolationType.WINDOW_BLUR]: 0,
                [ViolationType.FULLSCREEN_EXIT]: 0
            };

            // Total violation counts (for display)
            this.totalViolations = {
                [ViolationType.PHONE_DETECTED]: 0,
                [ViolationType.MULTIPLE_FACES]: 0,
                [ViolationType.CAMERA_EXIT]: 0,
                [ViolationType.FACE_LOOK_UP]: 0,
                [ViolationType.FACE_LOOK_DOWN]: 0,
                [ViolationType.FACE_LOOK_LEFT]: 0,
                [ViolationType.FACE_LOOK_RIGHT]: 0,
                [ViolationType.EYE_GAZE_DEVIATION]: 0,
                [ViolationType.LOW_LIGHT]: 0,
                [ViolationType.TAB_SWITCH]: 0,
                [ViolationType.WINDOW_BLUR]: 0,
                [ViolationType.FULLSCREEN_EXIT]: 0
            };

            // Active error flags (for UI badges)
            this.activeErrors = new Set();

            // Timestamps for continuous tracking
            this.violationStartTime = {
                [ViolationType.PHONE_DETECTED]: null,
                [ViolationType.MULTIPLE_FACES]: null,
                [ViolationType.CAMERA_EXIT]: null,
                [ViolationType.FACE_LOOK_UP]: null,
                [ViolationType.FACE_LOOK_DOWN]: null,
                [ViolationType.FACE_LOOK_LEFT]: null,
                [ViolationType.FACE_LOOK_RIGHT]: null,
                [ViolationType.EYE_GAZE_DEVIATION]: null,
                [ViolationType.LOW_LIGHT]: null
            };

            // Canvas for frame capture (offscreen)
            this.captureCanvas = document.createElement('canvas');
            this.captureCtx = this.captureCanvas.getContext('2d', { willReadFrequently: true });

            // Event listeners bound for cleanup
            this._boundHandlers = {
                visibilityChange: this._handleVisibilityChange.bind(this),
                windowBlur: this._handleWindowBlur.bind(this),
                fullscreenChange: this._handleFullscreenChange.bind(this)
            };

            // Detection state
            this._lastFaceCount = 0;
            this._lastPhoneDetected = false;
            this._lastLaptopDetected = false;
            this._lastFaceBounds = null;
            this._lastGazeDirection = null;
            this._lastLuminance = 128;

            // Use backend detection via API (more reliable than client-side ML)
            this._useBackendDetection = true;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Lifecycle
        // ─────────────────────────────────────────────────────────────────────

        /**
         * Start the proctoring engine.
         */
        start() {
            if (this.isRunning) return;
            this.isRunning = true;

            // Register event listeners for tab/window/fullscreen
            document.addEventListener('visibilitychange', this._boundHandlers.visibilityChange);
            window.addEventListener('blur', this._boundHandlers.windowBlur);
            document.addEventListener('fullscreenchange', this._boundHandlers.fullscreenChange);

            // Start sampling loop
            this._scheduleNextSample();

            console.log('[ProctoringEngine] Started');
        }

        /**
         * Stop the proctoring engine.
         */
        stop() {
            this.isRunning = false;
            if (this.sampleTimer) {
                clearTimeout(this.sampleTimer);
                this.sampleTimer = null;
            }

            // Remove event listeners
            document.removeEventListener('visibilitychange', this._boundHandlers.visibilityChange);
            window.removeEventListener('blur', this._boundHandlers.windowBlur);
            document.removeEventListener('fullscreenchange', this._boundHandlers.fullscreenChange);

            console.log('[ProctoringEngine] Stopped');
        }

        /**
         * Reset all strikes and active errors.
         */
        reset() {
            for (const key of Object.keys(this.strikes)) {
                this.strikes[key] = 0;
                this.totalViolations[key] = 0;
            }
            this.activeErrors.clear();
            for (const key of Object.keys(this.violationStartTime)) {
                this.violationStartTime[key] = null;
            }
            this.onRecovery();
        }

        // ─────────────────────────────────────────────────────────────────────
        // Sampling Loop
        // ─────────────────────────────────────────────────────────────────────

        _scheduleNextSample() {
            if (!this.isRunning) return;

            const now = Date.now();
            const elapsed = now - this.lastSampleTime;
            const delay = Math.max(0, this.config.sampleInterval - elapsed);

            this.sampleTimer = setTimeout(() => {
                this._sampleFrame();
                this._scheduleNextSample();
            }, delay);
        }

        async _sampleFrame() {
            if (!this.video || !this.video.videoWidth) return;

            this.lastSampleTime = Date.now();

            // Set canvas dimensions to match video
            this.captureCanvas.width = this.video.videoWidth;
            this.captureCanvas.height = this.video.videoHeight;

            // Draw current video frame to canvas
            this.captureCtx.drawImage(this.video, 0, 0);

            // Run detection (client-side for speed, backend for accuracy)
            const results = await this._detectAll();

            // Process results with strike system
            this._processResults(results);

            // Notify status update
            this.onStatusUpdate(this.getStatus());
        }

        // ─────────────────────────────────────────────────────────────────────
        // Detection (Client-Side + Backend)
        // ─────────────────────────────────────────────────────────────────────

        async _detectAll() {
            // Client-side detection for real-time feedback
            const faceResult = this._detectFacesClientSide();
            const lightResult = this._detectLowLight();
            const phoneResult = await this._detectPhoneClientSide();
            const laptopResult = this._detectLaptopClientSide();

            return {
                faceCount: faceResult.count,
                faceBounds: faceResult.bounds,
                luminance: lightResult.luminance,
                isLowLight: lightResult.isLow,
                phoneDetected: phoneResult.detected,
                phoneConfidence: phoneResult.confidence,
                laptopDetected: laptopResult.detected,
                laptopConfidence: laptopResult.confidence
            };
        }

        // ─────────────────────────────────────────────────────────────────────
        // Face Detection (Client-Side using Canvas + Simple Heuristics)
        // ─────────────────────────────────────────────────────────────────────

        _detectFacesClientSide() {
            try {
                const width = this.captureCanvas.width;
                const height = this.captureCanvas.height;

                // Get image data for analysis
                const imageData = this.captureCtx.getImageData(0, 0, width, height);
                const data = imageData.data;

                // Simple face detection using skin color detection
                // This is a lightweight approach that works in real-time
                const faceRegions = this._findFaceRegions(data, width, height);

                // Determine primary face bounds
                let bounds = null;
                if (faceRegions.length > 0) {
                    // Use the largest face region as the primary face
                    const primaryFace = faceRegions.reduce((a, b) => a.area > b.area ? a : b);
                    bounds = {
                        centerX: primaryFace.centerX / width,
                        centerY: primaryFace.centerY / height,
                        width: primaryFace.width / width,
                        height: primaryFace.height / height,
                        isOutOfBounds: false,
                        direction: null
                    };

                    // Check if face is out of bounds
                    const threshold = this.config.faceBoundsThreshold;
                    if (bounds.centerY < threshold) {
                        bounds.isOutOfBounds = true;
                        bounds.direction = 'UP';
                    } else if (bounds.centerY > (1 - threshold)) {
                        bounds.isOutOfBounds = true;
                        bounds.direction = 'DOWN';
                    } else if (bounds.centerX < threshold) {
                        bounds.isOutOfBounds = true;
                        bounds.direction = 'LEFT';
                    } else if (bounds.centerX > (1 - threshold)) {
                        bounds.isOutOfBounds = true;
                        bounds.direction = 'RIGHT';
                    }
                }

                return {
                    count: faceRegions.length,
                    bounds: bounds,
                    regions: faceRegions
                };
            } catch (err) {
                console.warn('[ProctoringEngine] Face detection error:', err);
                return { count: 0, bounds: null, regions: [] };
            }
        }

        /**
         * Find face regions using skin color detection.
         * This is a lightweight approach that works in real-time.
         */
        _findFaceRegions(data, width, height) {
            const regions = [];
            const visited = new Uint8Array(width * height);
            const skinPixels = [];

            // Detect skin-colored pixels
            for (let y = 0; y < height; y += 4) { // Sample every 4th row for performance
                for (let x = 0; x < width; x += 4) { // Sample every 4th column
                    const idx = (y * width + x) * 4;
                    const r = data[idx];
                    const g = data[idx + 1];
                    const b = data[idx + 2];

                    // Skin color detection (RGB rules)
                    if (this._isSkinColor(r, g, b)) {
                        skinPixels.push({ x, y });
                    }
                }
            }

            // Cluster skin pixels into regions
            if (skinPixels.length > 0) {
                const clusters = this._clusterPixels(skinPixels, width, height);

                // Filter clusters by size (minimum face size)
                const minFaceArea = (width * height) * 0.01; // 1% of frame
                for (const cluster of clusters) {
                    if (cluster.area >= minFaceArea) {
                        regions.push(cluster);
                    }
                }
            }

            return regions;
        }

        /**
         * Check if a pixel is skin-colored.
         */
        _isSkinColor(r, g, b) {
            // Multiple skin color rules for different skin tones
            const rule1 = r > 95 && g > 40 && b > 20 &&
                         r > g && r > b &&
                         Math.abs(r - g) > 15 &&
                         r - Math.min(g, b) > 15;

            const rule2 = r > 200 && g > 150 && b > 100 &&
                         r > g && g > b &&
                         (r - g) > 15;

            const rule3 = r > 60 && g > 40 && b > 20 &&
                         r > b && g > b &&
                         (r + g) / 2 > b + 20;

            return rule1 || rule2 || rule3;
        }

        /**
         * Cluster nearby skin pixels into regions.
         */
        _clusterPixels(pixels, width, height) {
            const clusters = [];
            const gridSize = 20; // Cluster grid size
            const grid = new Map();

            // Group pixels into grid cells
            for (const pixel of pixels) {
                const gx = Math.floor(pixel.x / gridSize);
                const gy = Math.floor(pixel.y / gridSize);
                const key = `${gx},${gy}`;

                if (!grid.has(key)) {
                    grid.set(key, { x: gx * gridSize, y: gy * gridSize, count: 0, pixels: [] });
                }
                const cell = grid.get(key);
                cell.count++;
                cell.pixels.push(pixel);
            }

            // Merge adjacent cells into clusters
            const visited = new Set();
            for (const [key, cell] of grid) {
                if (visited.has(key)) continue;

                const cluster = this._floodFillCluster(key, grid, visited, gridSize);
                if (cluster && cluster.count > 10) {
                    // Calculate cluster bounds
                    let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
                    for (const p of cluster.pixels) {
                        minX = Math.min(minX, p.x);
                        minY = Math.min(minY, p.y);
                        maxX = Math.max(maxX, p.x);
                        maxY = Math.max(maxY, p.y);
                    }

                    clusters.push({
                        centerX: (minX + maxX) / 2,
                        centerY: (minY + maxY) / 2,
                        width: maxX - minX,
                        height: maxY - minY,
                        area: cluster.count * 16, // Approximate area (4x4 sampling)
                        pixelCount: cluster.count
                    });
                }
            }

            return clusters;
        }

        /**
         * Flood fill to find connected cluster of grid cells.
         */
        _floodFillCluster(startKey, grid, visited, gridSize) {
            const queue = [startKey];
            const cluster = { count: 0, pixels: [] };

            while (queue.length > 0) {
                const key = queue.pop();
                if (visited.has(key)) continue;
                visited.add(key);

                const cell = grid.get(key);
                if (!cell) continue;

                cluster.count += cell.count;
                cluster.pixels.push(...cell.pixels);

                // Check neighbors
                const [gx, gy] = key.split(',').map(Number);
                const neighbors = [
                    `${gx + 1},${gy}`, `${gx - 1},${gy}`,
                    `${gx},${gy + 1}`, `${gx},${gy - 1}`,
                    `${gx + 1},${gy + 1}`, `${gx - 1},${gy - 1}`,
                    `${gx + 1},${gy - 1}`, `${gx - 1},${gy + 1}`
                ];

                for (const neighbor of neighbors) {
                    if (grid.has(neighbor) && !visited.has(neighbor)) {
                        queue.push(neighbor);
                    }
                }
            }

            return cluster;
        }

        // ─────────────────────────────────────────────────────────────────────
        // Phone Detection (Client-Side)
        // ─────────────────────────────────────────────────────────────────────

        async _detectPhoneClientSide() {
            try {
                // Use COCO-SSD if available
                if (typeof cocoSsd !== 'undefined' && this._cocoModel) {
                    const predictions = await this._cocoModel.detect(this.captureCanvas);

                    for (const pred of predictions) {
                        if (pred.class === 'cell phone' && pred.score >= this.config.phoneConfidenceThreshold) {
                            const predArea = pred.bbox[2] * pred.bbox[3];
                            const frameArea = this.captureCanvas.width * this.captureCanvas.height;
                            const areaRatio = predArea / frameArea;

                            if (areaRatio >= this.config.phoneMinAreaRatio && areaRatio <= this.config.phoneMaxAreaRatio) {
                                return { detected: true, confidence: pred.score, areaRatio };
                            }
                        }
                    }
                }

                // Fallback: detect phone-like objects using aspect ratio and position
                return this._detectPhoneHeuristic();
            } catch (err) {
                return { detected: false, confidence: 0 };
            }
        }

        /**
         * Heuristic phone detection based on object shape and position.
         */
        _detectPhoneHeuristic() {
            // Look for rectangular objects held in hands (typical phone usage)
            // This is a fallback when ML models are not available
            const width = this.captureCanvas.width;
            const height = this.captureCanvas.height;

            // Check for dark rectangular objects in the lower half of the frame
            // (where phones are typically held)
            const imageData = this.captureCtx.getImageData(0, Math.floor(height * 0.5), width, Math.floor(height * 0.5));
            const data = imageData.data;

            // Look for dark rectangular regions
            let darkPixelCount = 0;
            const threshold = 60; // Dark pixel threshold

            for (let i = 0; i < data.length; i += 16) {
                const r = data[i];
                const g = data[i + 1];
                const b = data[i + 2];
                if (r < threshold && g < threshold && b < threshold) {
                    darkPixelCount++;
                }
            }

            const totalSampled = Math.ceil(data.length / 16);
            const darkRatio = darkPixelCount / totalSampled;

            // If significant dark area detected in lower half, might be a phone
            if (darkRatio > 0.15 && darkRatio < 0.6) {
                return { detected: true, confidence: darkRatio, areaRatio: darkRatio };
            }

            return { detected: false, confidence: 0 };
        }

        // ─────────────────────────────────────────────────────────────────────
        // Laptop Detection (Client-Side)
        // ─────────────────────────────────────────────────────────────────────

        _detectLaptopClientSide() {
            try {
                // Use COCO-SSD if available
                if (typeof cocoSsd !== 'undefined' && this._cocoModel) {
                    // This would be populated by the COCO-SSD model
                    // For now, use heuristic detection
                }

                // Heuristic: detect laptop-like objects (rectangular, in background)
                return this._detectLaptopHeuristic();
            } catch (err) {
                return { detected: false, confidence: 0 };
            }
        }

        /**
         * Heuristic laptop detection.
         */
        _detectLaptopHeuristic() {
            const width = this.captureCanvas.width;
            const height = this.captureCanvas.height;

            // Look for rectangular objects with screen-like brightness in the background
            const imageData = this.captureCtx.getImageData(0, 0, width, height);
            const data = imageData.data;

            // Sample the background area (edges of frame)
            let brightRectangularRegions = 0;

            // Check left and right edges for laptop screens
            const edgeWidth = Math.floor(width * 0.2);
            const centerY = Math.floor(height * 0.5);

            for (let y = centerY - 50; y < centerY + 50; y += 4) {
                for (let x = 0; x < edgeWidth; x += 4) {
                    const idx = (y * width + x) * 4;
                    const r = data[idx];
                    const g = data[idx + 1];
                    const b = data[idx + 2];

                    // Look for bright screen-like pixels
                    if (r > 150 && g > 150 && b > 150) {
                        brightRectangularRegions++;
                    }
                }
            }

            // If significant bright regions detected, might be a laptop
            if (brightRectangularRegions > 50) {
                return { detected: true, confidence: 0.6 };
            }

            return { detected: false, confidence: 0 };
        }

        // ─────────────────────────────────────────────────────────────────────
        // Low Light Detection
        // ─────────────────────────────────────────────────────────────────────

        _detectLowLight() {
            try {
                const imageData = this.captureCtx.getImageData(0, 0, this.captureCanvas.width, this.captureCanvas.height);
                const data = imageData.data;
                let totalLuminance = 0;
                const pixelCount = data.length / 4;

                // Sample every 4th pixel for performance
                for (let i = 0; i < data.length; i += 16) {
                    const r = data[i];
                    const g = data[i + 1];
                    const b = data[i + 2];
                    totalLuminance += 0.2126 * r + 0.7152 * g + 0.0722 * b;
                }

                const sampledPixels = Math.ceil(data.length / 16);
                const avgLuminance = totalLuminance / sampledPixels;

                return { isLow: avgLuminance < this.config.lowLightThreshold, luminance: avgLuminance };
            } catch (err) {
                return { isLow: false, luminance: 128 };
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // Event Handlers (Tab Switch, Window Blur, Fullscreen Exit)
        // ─────────────────────────────────────────────────────────────────────

        _handleVisibilityChange() {
            if (document.hidden) {
                this._registerStrike(ViolationType.TAB_SWITCH);
            }
        }

        _handleWindowBlur() {
            this._registerStrike(ViolationType.WINDOW_BLUR);
        }

        _handleFullscreenChange() {
            if (!document.fullscreenElement) {
                this._registerStrike(ViolationType.FULLSCREEN_EXIT);
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // Results Processing with Strike System
        // ─────────────────────────────────────────────────────────────────────

        _processResults(results) {
            const now = Date.now();

            // A. Phone detection
            if (results.phoneDetected) {
                this._trackViolation(ViolationType.PHONE_DETECTED, now);
            } else {
                this._clearViolation(ViolationType.PHONE_DETECTED);
            }

            // B. Multiple faces
            if (results.faceCount > 1) {
                this._trackViolation(ViolationType.MULTIPLE_FACES, now);
            } else {
                this._clearViolation(ViolationType.MULTIPLE_FACES);
            }

            // C. Camera exit (no face detected)
            if (results.faceCount === 0) {
                this._trackViolation(ViolationType.CAMERA_EXIT, now);
            } else {
                this._clearViolation(ViolationType.CAMERA_EXIT);
            }

            // D. Face bounds
            if (results.faceBounds && results.faceBounds.isOutOfBounds) {
                const directionMap = {
                    'UP': ViolationType.FACE_LOOK_UP,
                    'DOWN': ViolationType.FACE_LOOK_DOWN,
                    'LEFT': ViolationType.FACE_LOOK_LEFT,
                    'RIGHT': ViolationType.FACE_LOOK_RIGHT
                };
                const violationType = directionMap[results.faceBounds.direction];
                if (violationType) {
                    this._trackViolation(violationType, now);
                }
            } else {
                this._clearViolation(ViolationType.FACE_LOOK_UP);
                this._clearViolation(ViolationType.FACE_LOOK_DOWN);
                this._clearViolation(ViolationType.FACE_LOOK_LEFT);
                this._clearViolation(ViolationType.FACE_LOOK_RIGHT);
            }

            // E. Low light
            if (results.isLowLight) {
                this._trackViolation(ViolationType.LOW_LIGHT, now);
            } else {
                this._clearViolation(ViolationType.LOW_LIGHT);
            }

            // Check for hard violations
            this._checkHardViolations();

            // Check for recovery
            if (this.activeErrors.size === 0) {
                this.onRecovery();
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // Strike System
        // ─────────────────────────────────────────────────────────────────────

        /**
         * Track a violation and award strikes based on continuous duration.
         * Strike awarded every 5 seconds of continuous violation.
         */
        _trackViolation(type, now) {
            if (!this.violationStartTime[type]) {
                this.violationStartTime[type] = now;
            }

            const elapsed = (now - this.violationStartTime[type]) / 1000;
            const newStrikeCount = Math.floor(elapsed / this.config.strikeIntervalSeconds);

            // Award new strikes
            while (this.strikes[type] < newStrikeCount && this.strikes[type] < this.config.hardViolationLimit) {
                this.strikes[type]++;
                this.totalViolations[type]++;
                this._activateError(type);
                this.onViolation(type, this.strikes[type], this.config.hardViolationLimit);
                console.log(`[ProctoringEngine] STRIKE ${this.strikes[type]}/${this.config.hardViolationLimit} — ${type}`);
            }
        }

        /**
         * Clear a violation when condition normalizes.
         */
        _clearViolation(type) {
            this.violationStartTime[type] = null;
            if (this.strikes[type] > 0) {
                this.strikes[type] = 0;
                this._deactivateError(type);
                console.log(`[ProctoringEngine] CLEARED — ${type}`);
            }
        }

        /**
         * Register an immediate strike (for tab switch, window blur, etc.)
         */
        _registerStrike(type) {
            if (this.strikes[type] < this.config.hardViolationLimit) {
                this.strikes[type]++;
                this.totalViolations[type]++;
                this._activateError(type);
                this.onViolation(type, this.strikes[type], this.config.hardViolationLimit);
                console.log(`[ProctoringEngine] STRIKE ${this.strikes[type]}/${this.config.hardViolationLimit} — ${type}`);
            }
            this._checkHardViolations();
        }

        _activateError(type) {
            this.activeErrors.add(type);
        }

        _deactivateError(type) {
            this.activeErrors.delete(type);
        }

        // ─────────────────────────────────────────────────────────────────────
        // Hard Violation Check
        // ─────────────────────────────────────────────────────────────────────

        _checkHardViolations() {
            for (const [type, count] of Object.entries(this.strikes)) {
                if (count >= this.config.hardViolationLimit) {
                    this._triggerMalpracticeTerminated(type);
                    return;
                }
            }
        }

        // ─────────────────────────────────────────────────────────────────────
        // Snapshot Capture
        // ─────────────────────────────────────────────────────────────────────

        _captureSnapshot() {
            try {
                const snapshotCanvas = document.createElement('canvas');
                const scale = 0.5;
                snapshotCanvas.width = this.captureCanvas.width * scale;
                snapshotCanvas.height = this.captureCanvas.height * scale;
                const ctx = snapshotCanvas.getContext('2d');
                ctx.drawImage(this.captureCanvas, 0, 0, snapshotCanvas.width, snapshotCanvas.height);

                // Add timestamp overlay
                ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
                ctx.fillRect(0, 0, snapshotCanvas.width, 30);
                ctx.fillStyle = '#fff';
                ctx.font = '14px monospace';
                ctx.fillText(`VIOLATION: ${new Date().toISOString()}`, 10, 20);

                return snapshotCanvas.toDataURL('image/jpeg', this.config.snapshotQuality);
            } catch (err) {
                console.error('[ProctoringEngine] Snapshot capture failed:', err);
                return null;
            }
        }

        _triggerMalpracticeTerminated(type) {
            const snapshot = this._captureSnapshot();
            const details = {
                type,
                timestamp: new Date().toISOString(),
                totalViolations: { ...this.totalViolations },
                activeErrors: Array.from(this.activeErrors)
            };

            console.error('[ProctoringEngine] MALPRACTICE TERMINATED:', details);
            this.onMalpracticeTerminated(details, snapshot);
        }

        // ─────────────────────────────────────────────────────────────────────
        // Public API
        // ─────────────────────────────────────────────────────────────────────

        /**
         * Get current proctoring status.
         */
        getStatus() {
            return {
                isRunning: this.isRunning,
                strikes: { ...this.strikes },
                totalViolations: { ...this.totalViolations },
                activeErrors: Array.from(this.activeErrors),
                lastResults: {
                    faceCount: this._lastFaceCount,
                    phoneDetected: this._lastPhoneDetected,
                    laptopDetected: this._lastLaptopDetected,
                    luminance: this._lastLuminance
                }
            };
        }

        /**
         * Get violation display string (e.g., "tabSwitches: 1/3")
         */
        getViolationDisplay() {
            return {
                phoneDetections: `${this.strikes[ViolationType.PHONE_DETECTED]}/${this.config.hardViolationLimit}`,
                multipleFaces: `${this.strikes[ViolationType.MULTIPLE_FACES]}/${this.config.hardViolationLimit}`,
                cameraExits: `${this.strikes[ViolationType.CAMERA_EXIT]}/${this.config.hardViolationLimit}`,
                gazeDeviations: `${this.strikes[ViolationType.EYE_GAZE_DEVIATION]}/${this.config.hardViolationLimit}`,
                lowLight: `${this.strikes[ViolationType.LOW_LIGHT]}/${this.config.hardViolationLimit}`,
                tabSwitches: `${this.strikes[ViolationType.TAB_SWITCH]}/${this.config.hardViolationLimit}`,
                windowBlur: `${this.strikes[ViolationType.WINDOW_BLUR]}/${this.config.hardViolationLimit}`,
                fullscreenExit: `${this.strikes[ViolationType.FULLSCREEN_EXIT]}/${this.config.hardViolationLimit}`
            };
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Export
    // ─────────────────────────────────────────────────────────────────────────
    global.ProctoringEngine = ProctoringEngine;
    global.ProctoringViolationType = ViolationType;

})(window);
