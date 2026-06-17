/* ─────────────────────────────────────────────
   emotion.js — Webcam frame analysis
   Sends frames to /api/emotion/analyze
   ───────────────────────────────────────────── */

const Emotion = {
  _video: null,
  _timer: null,
  _interval: 3000, // Every 3 seconds

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

    // Capture frame from video
    const canvas = document.createElement("canvas");
    canvas.width = 160; // Low res for speed
    canvas.height = 120;
    const ctx = canvas.getContext("2d");
    
    try {
        ctx.drawImage(this._video, 0, 0, canvas.width, canvas.height);
        const frame = canvas.toDataURL("image/jpeg", 0.6);

        const data = await apiPost("/api/emotion/analyze", {
            session_id: Session.id,
            frame: frame
        });

        if (data.face_detected) {
            Integrity.resetFaceCounter();
            this._updateUI(data);
        } else {
            // Report to integrity monitor if face is missing
            Integrity.reportCameraExit();
            this._updateFaceStatus(false);
        }
    } catch (e) {
        console.warn("[Emotion] Analysis failed:", e);
    }
  },

  _updateUI(data) {
    this._updateFaceStatus(true);

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

  _updateFaceStatus(detected) {
      const el = document.getElementById("cam-face");
      if (!el) return;
      if (detected) {
          el.textContent = "● FACE OK";
          el.className = "cam-face-status ok";
      } else {
          el.textContent = "○ NO FACE";
          el.className = "cam-face-status warn";
      }
  }
};
