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
  _activeCameraWarning: null,

  start(videoEl) {
    console.log("[Emotion] Analysis started");
    this._video = videoEl;
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

    const canvas = document.createElement("canvas");
    canvas.width = 320;
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

        this._renderQuality(data);
        this._handleNewEvents(data);
        this._handlePhoneStrike(data);
        this._handleAdditionalPersonStrike(data);
        this._drawDetectionBoxes(data);

        if (data.face_detected) {
            this._clearViolationTimer("camera_exit");
            this._clearViolationTimer("multiple_faces");
            Integrity.resetFaceCounter();
            this._updateFaceStatus("face_present");
            this._updateUI(data);
        } else if (data.status === "low_light") {
            this._updateFaceStatus("low_light");
            this._clearViolationTimer("camera_exit");
        } else {
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
              return;
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

  _handlePhoneStrike(data) {
      if (data.phone && data.phone.confirmed_strike) {
          Integrity._handleViolation("phone_detected");
      }
  },

  _handleAdditionalPersonStrike(data) {
      if (data.person_summary && data.person_summary.confirmed_strike) {
          Integrity._handleViolation("additional_person");
      }
  },

  _drawDetectionBoxes(data) {
      const canvas = document.getElementById("detection-canvas");
      if (!canvas || !this._video) return;
      const ctx = canvas.getContext("2d");
      const w = canvas.width = this._video.videoWidth || 320;
      const h = canvas.height = this._video.videoHeight || 240;

      ctx.clearRect(0, 0, w, h);

      if (data.person_summary && data.person_summary.boxes) {
          data.person_summary.boxes.forEach((box, idx) => {
              ctx.strokeStyle = idx === 0 ? "#10f59a" : "#ff3d5a";
              ctx.lineWidth = 2;
              ctx.strokeRect(box.x, box.y, box.w, box.h);

              ctx.fillStyle = idx === 0 ? "#10f59a" : "#ff3d5a";
              ctx.font = "10px monospace";
              ctx.fillText(idx === 0 ? "CANDIDATE" : "ADDITIONAL PERSON", box.x + 4, Math.max(12, box.y - 4));
          });
      }
  },


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
      if (data.person_summary && data.person_summary.detected) msgs.push("Additional person detected in camera frame");

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
      PHONE_DETECTED: "Potential integrity concern: phone-like object detected",
      ADDITIONAL_PERSON: "Integrity alert: additional person detected in camera frame"
  },

  _handleNewEvents(data) {
      if (!data.new_events || !data.new_events.length) return;
      data.new_events.forEach((evt) => {
          const msg = this._newEventLabels[evt] || evt;
          if (typeof showToast === "function") {
              showToast("ℹ " + msg, (evt === "PHONE_DETECTED" || evt === "ADDITIONAL_PERSON") ? "err" : "warn");
          }
      });
  },

  _updateUI(data) {
    const badge = document.getElementById("cam-emotion");
    if (badge) {
        const emo = data.dominant_emotion || "neutral";
        badge.textContent = emo.toUpperCase();
        badge.className = "cam-emotion emotion-badge " + emo;
    }

    const score = data.interview_score || 65;
    const bar = document.getElementById("emot-bar");
    const val = document.getElementById("emot-val");
    if (bar) bar.style.width = score + "%";
    if (val) val.textContent = score + "%";

    const history = document.getElementById("emot-history");
    if (history) {
        const dot = document.createElement("div");
        dot.className = "emot-dot " + (data.dominant_emotion || "neutral");
        dot.title = data.dominant_emotion;
        history.appendChild(dot);
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
      } else if (status === "multiple_faces") {
          el.textContent = "⚠ MULTIPLE FACES DETECTED";
          el.className = "cam-face-status gone";
      } else if (status === "additional_person_detected") {
          el.textContent = "⚠ ADDITIONAL PERSON DETECTED";
          el.className = "cam-face-status gone";
      } else if (status === "multiple_people_no_face") {
          el.textContent = "⚠ MULTIPLE PEOPLE (NO FACE)";
          el.className = "cam-face-status gone";
      } else if (status === "eyes_not_visible" || status === "eye_contact_lost") {
          el.textContent = "⚠ EYES NOT VISIBLE / LOOK AT CAMERA";
          el.className = "cam-face-status warn";
      } else {
          el.textContent = "⚠ NO FACE DETECTED";
          el.className = "cam-face-status gone";
      }
  }
};

