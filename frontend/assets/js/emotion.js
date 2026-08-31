/* ─────────────────────────────────────────────
   emotion.js — Webcam frame analysis
   Sends frames to /api/emotion/analyze
   ───────────────────────────────────────────── */

const Emotion = {
  _video: null,
  _timer: null,
  _interval: 3000, // Every 3 seconds
  _violationTimer: null,
  _activeViolationType: null,
  _strikeTriggered: false,

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

        if (data.face_detected) {
            this._clearViolationTimer();
            this._strikeTriggered = false;
            Integrity.resetFaceCounter();
            this._updateFaceStatus("face_present");
            this._updateUI(data);
        } else {
            // "low_light", "no_face", or "multiple_faces"
            this._updateFaceStatus(data.status);
            this._handleProctoringViolation(data.status);
        }
    } catch (e) {
        console.warn("[Emotion] Analysis failed:", e);
    }
  },

  _handleProctoringViolation(status) {
      if (this._strikeTriggered) {
          return;
      }
      
      if (this._violationTimer) {
          if (this._activeViolationType === status) {
              return; // Keep existing timer running
          } else {
              clearTimeout(this._violationTimer);
          }
      }

      this._activeViolationType = status;
      console.log(`[CAMERA] Starting 5-second countdown for strike due to ${status}`);
      
      this._violationTimer = setTimeout(async () => {
          console.log(`[CAMERA] 5 seconds expired. Submitting strike for ${status}`);
          this._strikeTriggered = true;
          this._violationTimer = null;
          try {
              // Trigger strike via Integrity monitor
              await Integrity._handleViolation("camera_exit");
          } catch (e) {
              console.error("[CAMERA] Violation reporting failed:", e);
          }
      }, 5000);
  },

  _clearViolationTimer() {
      if (this._violationTimer) {
          clearTimeout(this._violationTimer);
          this._violationTimer = null;
      }
      this._activeViolationType = null;
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
          el.textContent = "○ LOW LIGHT — Improve lighting";
          el.className = "cam-face-status gone";
      } else if (status === "multiple_faces") {
          el.textContent = "○ MULTIPLE FACES DETECTED";
          el.className = "cam-face-status gone";
      } else {
          el.textContent = "○ NO FACE DETECTED";
          el.className = "cam-face-status gone";
      }
  }
};
