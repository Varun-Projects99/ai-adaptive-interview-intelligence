"""
test_face_detector.py — Verification script for face detection (Image & Webcam modes)
InterviewIQ AI Adaptive Interview Intelligence System - Part 2
"""

import sys
import os
import argparse
import time
import cv2

# Add backend to path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
sys.path.insert(0, project_root)

from backend.modules.integrity_monitor.face_detector import FaceDetector, FaceDetectorStabilizer


def test_image(image_path):
    print(f"=== Testing Image: {image_path} ===")
    if not os.path.exists(image_path):
        print(f"[ERROR] Image path does not exist: {image_path}")
        return

    detector = FaceDetector()
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[ERROR] Failed to read image: {image_path}")
        return

    res = detector.detect(frame, confidence_threshold=0.35)
    print(f"Raw Detections Count: {res['count']}")

    for idx, face in enumerate(res['faces']):
        bbox = face['bbox']
        conf = face['confidence']
        print(f" Face #{idx+1}: Box={bbox}, Conf={conf}")
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)
        cv2.putText(frame, f"Face {conf:.2f}", (bbox[0], max(15, bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    status_text = f"Faces: {res['count']} | Multi: {res['is_multi_face']}"
    cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255) if res['is_multi_face'] else (0, 255, 0), 2)

    out_path = os.path.join(script_dir, "test_output.jpg")
    cv2.imwrite(out_path, frame)
    print(f"Output annotated image saved to: {out_path}")


def test_webcam():
    print("=== Testing Webcam Mode (Press 'q' to exit) ===")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam camera index 0.")
        return

    detector = FaceDetector()
    stabilizer = FaceDetectorStabilizer(confirm_frames=3)

    prev_time = time.time()
    fps = 0.0

    while True:
        ret, frame = cap.read()
        if not ret or frame is None:
            print("[WARN] Failed to grab webcam frame.")
            break

        curr_time = time.time()
        fps = 1.0 / max(1e-5, (curr_time - prev_time))
        prev_time = curr_time

        raw_res = detector.detect(frame, confidence_threshold=0.35)
        stab_res = stabilizer.update(raw_res)

        count = stab_res['confirmed_count']
        status = stab_res['status']

        # Choose UI color based on status
        if status == "NORMAL_SINGLE_FACE":
            color = (0, 255, 0) # Green
        elif status == "NO_FACE_DETECTED":
            color = (0, 165, 255) # Orange
        else:
            color = (0, 0, 255) # Red (Multiple faces)

        # Draw raw face bounding boxes
        for face in raw_res['faces']:
            bbox = face['bbox']
            conf = face['confidence']
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(frame, f"Face: {conf:.2f}", (bbox[0], max(15, bbox[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

        # Draw HUD info
        cv2.putText(frame, f"Status: {status}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"Confirmed Faces: {count}", (20, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        if stab_res['person_entered']:
            cv2.putText(frame, "ALERT: PERSON ENTERED", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        elif stab_res['person_left']:
            cv2.putText(frame, "ALERT: PERSON LEFT", (20, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)

        cv2.imshow("InterviewIQ - Face Detection Integrity Monitor", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Test Face Detector Model")
    parser.add_argument("--image", type=str, help="Path to test image")
    parser.add_argument("--webcam", action="store_true", help="Test live webcam stream")
    args = parser.parse_args()

    if args.image:
        test_image(args.image)
    elif args.webcam:
        test_webcam()
    else:
        print("Please specify --image <path> or --webcam")


if __name__ == "__main__":
    main()
