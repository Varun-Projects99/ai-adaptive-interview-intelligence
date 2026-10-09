/**
 * useProctoring.ts — React Hook for Mobile Phone Object Detection Proctoring
 * InterviewIQ AI Adaptive Interview Intelligence System
 *
 * Integrates TensorFlow.js COCO-SSD object detection for real-time video monitoring.
 */

import { useEffect, useRef, useState, useCallback, RefObject } from 'react';
import * as tf from '@tensorflow/tfjs';
import * as cocoSsd from '@tensorflow-models/coco-ssd';

export interface UseProctoringOptions {
  sampleInterval?: number;       // Sampling interval in ms (default: 800ms)
  minConfidence?: number;        // Detection score threshold (default: 0.65)
  requiredDetections?: number;   // Consecutive positive detections required for violation (default: 3)
  targetClass?: string;          // Target COCO-SSD class label (default: 'cell phone')
  onViolationDetected?: (data: ViolationPayload) => void;
  onDetectionUpdate?: (data: DetectionUpdatePayload) => void;
  onModelLoaded?: () => void;
  onModelError?: (error: Error) => void;
}

export interface ViolationPayload {
  type: string;
  consecutiveDetections: number;
  confidence: number;
  bbox: number[] | null;
  timestamp: number;
}

export interface DetectionUpdatePayload {
  isDetected: boolean;
  consecutiveDetections: number;
  requiredDetections: number;
  confidence: number;
  predictions: cocoSsd.DetectedObject[];
}

export function useProctoring(
  videoRef: RefObject<HTMLVideoElement | null>,
  options: UseProctoringOptions = {}
) {
  const {
    sampleInterval = 800,
    minConfidence = 0.65,
    requiredDetections = 2,
    targetClass = 'cell phone',
    onViolationDetected,
    onDetectionUpdate,
    onModelLoaded,
    onModelError
  } = options;

  const [isReady, setIsReady] = useState<boolean>(false);
  const [isDetecting, setIsDetecting] = useState<boolean>(false);
  const [error, setError] = useState<Error | null>(null);
  const [consecutiveCount, setConsecutiveCount] = useState<number>(0);

  const modelRef = useRef<cocoSsd.ObjectDetection | null>(null);
  const isRunningRef = useRef<boolean>(false);
  const consecutiveRef = useRef<number>(0);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const isProcessingRef = useRef<boolean>(false);

  // Load TensorFlow.js COCO-SSD Model
  useEffect(() => {
    let isMounted = true;

    async function loadModel() {
      try {
        await tf.ready();
        const loadedModel = await cocoSsd.load({
          base: 'lite_mobilenet_v2'
        });

        if (isMounted) {
          modelRef.current = loadedModel;
          setIsReady(true);
          onModelLoaded?.();
        }
      } catch (err) {
        if (isMounted) {
          const errorObj = err instanceof Error ? err : new Error(String(err));
          setError(errorObj);
          onModelError?.(errorObj);
        }
      }
    }

    loadModel();

    return () => {
      isMounted = false;
      if (timerRef.current) clearTimeout(timerRef.current);
      modelRef.current = null;
    };
  }, [onModelLoaded, onModelError]);

  // Frame processing function
  const processFrame = useCallback(async () => {
    const video = videoRef.current;
    const model = modelRef.current;

    if (!isRunningRef.current || !model || !video) return;

    if (video.paused || video.ended || video.readyState < 2 || !video.videoWidth) {
      return;
    }

    if (isProcessingRef.current) return;
    isProcessingRef.current = true;

    try {
      const predictions = await model.detect(video);

      const phoneDetections = predictions.filter(
        (pred) =>
          pred.class.toLowerCase() === targetClass.toLowerCase() &&
          pred.score >= minConfidence
      );

      const isDetected = phoneDetections.length > 0;
      const topDetection = isDetected ? phoneDetections[0] : null;

      // Detection buffer logic: increment on match, decrement when clear
      if (isDetected) {
        consecutiveRef.current += 1;
      } else {
        consecutiveRef.current = Math.max(0, consecutiveRef.current - 1);
      }

      setConsecutiveCount(consecutiveRef.current);

      onDetectionUpdate?.({
        isDetected,
        consecutiveDetections: consecutiveRef.current,
        requiredDetections,
        confidence: topDetection ? topDetection.score : 0,
        predictions
      });

      if (consecutiveRef.current >= requiredDetections) {
        onViolationDetected?.({
          type: 'phone_detected',
          consecutiveDetections: consecutiveRef.current,
          confidence: topDetection ? topDetection.score : 0,
          bbox: topDetection ? topDetection.bbox : null,
          timestamp: Date.now()
        });

        consecutiveRef.current = 0;
      }
    } catch (err) {
      console.error('[useProctoring] Frame processing error:', err);
    } finally {
      isProcessingRef.current = false;
    }
  }, [videoRef, targetClass, minConfidence, requiredDetections, onDetectionUpdate, onViolationDetected]);

  // Start continuous sampling loop
  const start = useCallback(() => {
    if (isRunningRef.current) return;
    isRunningRef.current = true;
    setIsDetecting(true);
    consecutiveRef.current = 0;
    setConsecutiveCount(0);

    const loop = async () => {
      if (!isRunningRef.current) return;
      await processFrame();
      if (isRunningRef.current) {
        timerRef.current = setTimeout(loop, sampleInterval);
      }
    };

    loop();
  }, [processFrame, sampleInterval]);

  // Stop sampling loop
  const stop = useCallback(() => {
    isRunningRef.current = false;
    setIsDetecting(false);
    if (timerRef.current) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    consecutiveRef.current = 0;
    setConsecutiveCount(0);
  }, []);

  // Auto-start when model is ready and video element is attached
  useEffect(() => {
    if (isReady && videoRef.current) {
      start();
    }
    return () => {
      stop();
    };
  }, [isReady, videoRef, start, stop]);

  return {
    isReady,
    isDetecting,
    error,
    consecutiveCount,
    start,
    stop
  };
}
