# backend/models/ — Model Provenance & Limitations

This project uses **no custom-trained models**. Everything here is classical
computer vision (OpenCV Haar cascades) or a small, pretrained, publicly
published model used as-is. Nothing in this folder was trained on this
project's own data, and no accuracy figure below is a claim about this
project's own testing — they are the publishers' own published numbers,
included so limitations are documented honestly instead of guessed at.

| File | Purpose | Size | Source | License |
|---|---|---|---|---|
| `haarcascade_frontalface_default.xml` | Face detection | ~930 KB | OpenCV core (bundled with `opencv-python`) | Intel/OpenCV |
| `haarcascade_eye.xml` | Eye detection | ~341 KB | OpenCV core (bundled with `opencv-python`) | Intel/OpenCV |
| `face_detection_yunet_2023mar.onnx` | Face landmark detector, used only to derive an **approximate head-pose** signal | 232,589 bytes (227.1 KB) | [opencv/opencv_zoo](https://github.com/opencv/opencv_zoo/tree/main/models/face_detection_yunet), official OpenCV org repo | Apache-2.0 |
| `object_detection_nanodet_2022nov.onnx` | General-purpose COCO (80-class) object detector, used only to check for a **possible phone-like object** in frame | 3,800,954 bytes (3.63 MB) | [opencv/opencv_zoo](https://github.com/opencv/opencv_zoo/tree/main/models/object_detection_nanodet) (NanoDet-Plus-m-1.5x, 416×416 input), official OpenCV org repo | Apache-2.0 |

SHA-256 checksums (verified against the official OpenCV Zoo git-lfs objects
at the time these were added):
```
face_detection_yunet_2023mar.onnx:
  8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4
object_detection_nanodet_2022nov.onnx:
  4b82da9944b88577175ee23a459dce2e26e6e4be573def65b1055dc2d9720186
```

Both files load and run through `cv2.dnn` / `cv2.FaceDetectorYN`, which are
part of the **core** `opencv-python` package already pinned in
`requirements.txt` (`opencv-python==4.9.0.80`) -- confirmed by loading and
running inference with both files against that exact pinned version.
**No new pip dependency was added for either capability.**

## Known limitations (read before trusting these signals)

- **Head pose (yaw/pitch/direction)** is estimated with `cv2.solvePnP`
  against a generic, textbook 3D face model -- it is **not calibrated to
  any individual candidate's real face geometry**. Treat `head_pose.yaw_deg`
  / `pitch_deg` as an approximate signal, not a precise measurement. It has
  not been validated against a labeled dataset of real interview footage
  (none was available in the development environment); only synthetic-image
  and single-photo smoke tests were possible. It is used only to derive a
  coarse center/left/right/up/down direction, and only after a **6-second
  sustained** reading in one non-center direction -- a brief natural glance
  never produces a warning.

- **Phone detection** uses NanoDet-Plus's own published accuracy for the
  COCO "cell phone" class: **AP50 = 33.7%, mAP = 22.8%** (COCO2017val, as
  published in the model's own `README.md` in opencv_zoo). This is a
  **general-purpose object detector, not trained or fine-tuned for
  interview-desk conditions**. It will legitimately miss some real phones
  and can occasionally score a phone-shaped object above the confidence
  floor. Mitigations in place: a confidence floor (`PHONE_MIN_CONFIDENCE =
  0.50`, see `backend/modules/integrity_config.py`) and a 6-second sustained
  detection requirement before it is ever reported as an event or
  contributes to a strike -- but this does **not** make it accurate, only
  more conservative about false alarms. A confirmed phone is reported as a
  "potential integrity concern," never as proof of cheating.

- **Face detection itself** (the pre-existing, unchanged Haar-cascade
  pipeline) is classical computer vision, not a trained classifier, and its
  known limitations (lighting sensitivity, profile-angle sensitivity, no
  real "identity" concept) are unchanged by this work.

- **No live-webcam empirical validation was possible in the development
  sandbox** (no real camera feed available there). All new logic was
  validated with: (a) unit tests against synthetic frames and a mocked
  clock (`backend/tests/test_integrity_events.py`), and (b) a smoke test
  against one real photograph. Real-world calibration of the thresholds in
  `integrity_config.py` (especially `PHONE_MIN_CONFIDENCE` and the
  `HEAD_POSE_*_CENTER_DEG` values) is expected once this runs against real
  interview sessions, and should be adjusted from that one centralized file
  rather than anywhere else in the code.
