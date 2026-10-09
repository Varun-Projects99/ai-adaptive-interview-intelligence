"""
test_phone_detector.py — Verification script for Part 1 V2 Phone Detector (Image & Webcam modes)
InterviewIQ AI Adaptive Interview Intelligence System (Part 1 V2)
"""

import sys
import os
import argparse
import time
import cv2

# Add project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))
sys.path.insert(0, project_root)

from backend.modules.integrity_monitor.phone_detector import PhoneDetector, PhoneDetectorStabilizer


def test_image(image_path):
    print(f"=== Testing Image: {image_path} ===")
    if not os.path.exists(image_path):
        print(f"[ERROR] Image path does not exist: {image_path}")
        return

    detector = PhoneDetector()
    frame = cv2.imread(image_path)
    if frame is None:
        print(f"[ERROR] Failed to read image: {image_path}")
        return

    res = detector.detect(frame, confidence_threshold=0.35)
    print(f"Detection Result: {res}")

    if res['detected'] and res['bbox']:
        bbox = res['bbox']
        conf = res['confidence']
        cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 0, 255), 2)
        cv2.putText(frame, f"PHONE: {conf:.2f}", (bbox[0], max(15, bbox[1] - 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

    status_text = f"Phone: {'DETECTED' if res['detected'] else 'NOT DETECTED'}"
    cv2.putText(frame, status_text, (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                (0, 0, 255) if res['detected'] else (0, 255, 0), 2)

    out_path = os.path.join(script_dir, "test_v2_output.jpg")
    cv2.imwrite(out_path, frame)
    print(f"Annotated test image saved to: {out_path}")


def test_webcam():
    print("=== Testing Webcam Mode (Press 'q' to exit) ===")
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam camera index 0.")
        return

    detector = PhoneDetector()
    stabilizer = PhoneDetectorStabilizer(confirm_frames=3, lost_frames=2, confidence_threshold=0.35)

    prev_time = time.time()

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

        confirmed = stab_res['confirmed']
        color = (0, 0, 255) if confirmed else (0, 255, 0)

        if raw_res['detected'] and raw_res['bbox']:
            bbox = raw_res['bbox']
            conf = raw_res['confidence']
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), color, 2)
            cv2.putText(frame, f"Phone: {conf:.2f}", (bbox[0], max(15, bbox[1] - 10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

        status_msg = "PERSISTENT_PHONE_DETECTED" if confirmed else "NORMAL_CLEAN_CANDIDATE"
        cv2.putText(frame, f"Status: {status_msg}", (20, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        cv2.putText(frame, f"FPS: {fps:.1f}", (20, 65), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)

        cv2.imshow("InterviewIQ - Part 1 V2 Phone Detector", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    parser = argparse.ArgumentParser(description="Test Part 1 V2 Phone Detector")
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
