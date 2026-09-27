/* ─────────────────────────────────────────────
   emotion.js — Webcam frame analysis
   Sends frames to /api/emotion/analyze
   ───────────────────────────────────────────── */

const Emotion = {
  _video: null,
  _timer: null,
  _interval: 3000, // Every 3 seconds

  // Per-violation-type state (was a single shared flag/timer before -- a
  // camera_exit countdown in progress could silently swallow a distinct
  // multiple_faces episode, or vice versa. Each strike-eligible type now
  // gets its own independent timer/flag, same 5-second debounce as before).
  _violationTimers: {},
  _activeStatus: {},
  _strikeTriggered: {},

  start(videoEl) {
    console.log("[Emotion] Analysis started");
    this._video = videoEl;
    // Delay first analysis to allow camera to warm up
    setTimeout(() => {
        this._timer = setInterval(() => this.analyze(), this._interval);
    }, 2000);
  },

  stop() {
    console.log("[Emotion] Analysis stopped");
    clearInterval(this._timer);
  },

  async analyze() {
    if (!this._video || this._video.paused || this._video.ended) return;
    if (!this._video.videoWidth || !this._video.videoHeight || this._video.readyState < 2) {
        console.warn("[Emotion] Webcam is not fully initialized or ready yet.");
        return;
    }

    // Capture frame from video
    const canvas = document.createElement("canvas");
    canvas.width = 320; // 320x240 for reliable detection
    canvas.height = 240;
    const ctx = canvas.getContext("2d");

    try {
        ctx.drawImage(this._video, 0, 0, canvas.width, canvas.height);
        const frame = canvas.toDataURL("image/jpeg", 0.6);

        const data = await apiPost("/api/emotion/analyze", {
            session_id: Session.id,
            frame: frame
        });

        console.log("[CAMERA] API result:", data);
        console.log("[CAMERA] face_detected:", data.face_detected);
        console.log("[CAMERA] status:", data.status);
        console.log("[CAMERA] UI state:", data.face_detected ? "face_present" : data.status);

        // New Tier-1/2 telemetry (quality/position/head-pose/phone). These
        // are purely informational/warning-tier and are handled completely
        // separately from the strike path below -- see
        // backend/modules/integrity_config.py for why (low light, blur,
        // face position, and sustained head-turn must NEVER strike).
        this._renderQuality(data);
        this._handleNewEvents(data);
        this._handlePhoneStrike(data);

        if (data.face_detected) {
            this._clearViolationTimer("camera_exit");
            this._clearViolationTimer("multiple_faces");
            Integrity.resetFaceCounter();
            this._updateFaceStatus("face_present");
            this._updateUI(data);
        } else if (data.status === "low_light") {
            // Low light must NEVER contribute to a strike (fixed: this used
            // to fall into the generic "else" branch below and, after 5
            // continuous seconds, count as a camera_exit strike). It is
            // still shown to the candidate and still logged server-side as
            // a structured, non-strike event (see /api/emotion/analyze).
            this._updateFaceStatus("low_light");
            this._clearViolationTimer("camera_exit");
        } else {
            // "no_face", "multiple_faces", "eyes_not_visible" -- unchanged,
            // still strike-eligible via the same 5-second debounce.
            this._updateFaceStatus(data.status);
            this._handleProctoringViolation(data.status);
        }
    } catch (e) {
        console.warn("[Emotion] Analysis failed:", e);
    }
  },

  _handleProctoringViolation(status) {
      const vtype = status === "multiple_faces" ? "multiple_faces" : "camera_exit";

      if (this._strikeTriggered[vtype]) {
          return;
      }

      if (this._violationTimers[vtype]) {
          if (this._activeStatus[vtype] === status) {
              return; // Keep existing timer running
          } else {
              clearTimeout(this._violationTimers[vtype]);
          }
      }

      this._activeStatus[vtype] = status;
      console.log(`[CAMERA] Starting 5-second countdown for strike due to ${status}`);

      this._violationTimers[vtype] = setTimeout(async () => {
          console.log(`[CAMERA] 5 seconds expired. Submitting strike for ${status}`);
          this._strikeTriggered[vtype] = true;
          delete this._violationTimers[vtype];
          try {
              // Multiple people in frame is a distinct signal from the
              // candidate simply being away/unclear (no_face, eyes_not_
              // visible all still fold into "camera_exit"), so it gets its
              // own tracked violation type -- see /api/integrity/violation
              // and the "Multiple Faces" counter in interview.html. Still
              // goes through the same 5-second debounce above and the same
              // 3-strike rule, just counted and reported separately.
              await Integrity._handleViolation(vtype);
          } catch (e) {
              console.error("[CAMERA] Violation reporting failed:", e);
          }
      }, 5000);
  },

  _clearViolationTimer(vtype) {
      if (this._violationTimers[vtype]) {
          clearTimeout(this._violationTimers[vtype]);
          delete this._violationTimers[vtype];
      }
      this._activeStatus[vtype] = null;
      this._strikeTriggered[vtype] = false;
  },

  // ── New Tier-1/2 telemetry (non-strike) ──────────────────────────────

  _renderQuality(data) {
      const el = document.getElementById("cam-quality");
      if (!el) return;

      if (!data.face_detected) { el.style.display = "none"; return; }

      const msgs = [];
      if (data.quality && data.quality.blurry) msgs.push("Camera image looks blurry");
      if (data.face_position === "too_far") msgs.push("Move closer to the camera");
      else if (data.face_position === "too_close") msgs.push("Move back from the camera a little");
      else if (data.face_position === "partially_visible") msgs.push("Keep your full face inside the frame");
      if (data.head_pose && data.head_pose.direction && !["center", "unknown"].includes(data.head_pose.direction)) {
          msgs.push("Please face the camera");
      }
      if (data.phone && data.phone.detected) msgs.push("Possible phone-like object in view");

      if (msgs.length === 0) { el.style.display = "none"; return; }
      el.textContent = "ℹ " + msgs[0];
      el.style.display = "block";
  },

  _newEventLabels: {
      BLURRY_IMAGE: "Image quality: camera feed looks blurry",
      LOW_LIGHT: "Room lighting looks low",
      FACE_TOO_FAR: "Please move closer to the camera",
      FACE_TOO_CLOSE: "Please move back from the camera",
      FACE_PARTIALLY_VISIBLE: "Please keep your full face in the frame",
      HEAD_LEFT: "Please face the camera",
      HEAD_RIGHT: "Please face the camera",
      HEAD_UP: "Please face the camera",
      HEAD_DOWN: "Please face the camera",
      PHONE_DETECTED: "Potential integrity concern: phone-like object detected"
  },

  _handleNewEvents(data) {
      if (!data.new_events || !data.new_events.length) return;
      data.new_events.forEach((evt) => {
          const msg = this._newEventLabels[evt] || evt;
          if (typeof showToast === "function") {
              showToast("ℹ " + msg, evt === "PHONE_DETECTED" ? "err" : "warn");
          }
      });
  },

  _handlePhoneStrike(data) {
      // Server-confirmed, sustained phone detection (see
      // modules/emotion_detector.py's PHONE_CONFIRM_SECONDS window and
      // PHONE_MIN_CONFIDENCE floor) -- reported once, edge-triggered, and
      // routed through the EXACT same violation pipeline every other
      // strike-eligible type already uses (same 3-strike rule, same UI).
      // Per spec, a confirmed phone is treated as a potential integrity
      // concern, never as proof of cheating.
      if (data.phone && data.phone.confirmed_strike) {
          Integrity._handleViolation("phone_detected");
      }
  },

  _updateUI(data) {
    // Update dominant emotion badge
    const badge = document.getElementById("cam-emotion");
    if (badge) {
        const emo = data.dominant_emotion || "neutral";
        badge.textContent = emo.toUpperCase();
        badge.className = "cam-emotion emotion-badge " + emo;
    }

    // Update live meters
    const score = data.interview_score || 65;
    const bar = document.getElementById("emot-bar");
    const val = document.getElementById("emot-val");
    if (bar) bar.style.width = score + "%";
    if (val) val.textContent = score + "%";

    // Add dot to timeline
    const history = document.getElementById("emot-history");
    if (history) {
        const dot = document.createElement("div");
        dot.className = "emot-dot " + (data.dominant_emotion || "neutral");
        dot.title = data.dominant_emotion;
        history.appendChild(dot);
        // Keep only last 15 dots
        if (history.children.length > 15) history.removeChild(history.firstChild);
    }
  },

  _updateFaceStatus(status) {
      const el = document.getElementById("cam-face");
      if (!el) return;

      if (status === true || status === "face_present") {
          el.textContent = "● FACE DETECTED";
          el.className = "cam-face-status ok";
      } else if (status === "low_light") {
          el.textContent = "⚠ LOW LIGHTING DETECTED";
          el.className = "cam-face-status warn";
          if (typeof showToast === "function") showToast("⚠ Room lighting is too low! Please increase room lighting.", "err");
      } else if (status === "multiple_faces") {
          el.textContent = "⚠ MULTIPLE FACES DETECTED";
          el.className = "cam-face-status gone";
          if (typeof showToast === "function") showToast("⚠ Multiple faces detected in camera frame!", "err");
      } else if (status === "eyes_not_visible" || status === "eye_contact_lost") {
          el.textContent = "⚠ EYES NOT VISIBLE / LOOK AT CAMERA";
          el.className = "cam-face-status warn";
          if (typeof showToast === "function") showToast("⚠ Eye contact lost or eyes not visible! Please look directly at the camera.", "err");
      } else {
          el.textContent = "⚠ NO FACE DETECTED";
          el.className = "cam-face-status gone";
          if (typeof showToast === "function") showToast("⚠ No face detected in camera frame! Please face the camera.", "err");
      }
  }
};
