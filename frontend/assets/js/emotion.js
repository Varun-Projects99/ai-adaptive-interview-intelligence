/* ─────────────────────────────────────────────
   emotion.js — Webcam frame analysis
   Sends frames to /api/emotion/analyze
   ───────────────────────────────────────────── */

const Emotion = {
  _video: null,
  _timer: null,
  _interval: 3000, // Every 3 seconds

  // Wall-clock state tracking for camera incident confirmation & debouncing
  _noFaceFirstSeen: null,
  _noFaceIncidentActive: false,

  _multiFaceFirstSeen: null,
  _multiFaceIncidentActive: false,

  _lowLightFirstSeen: null,
  _lowLightIncidentActive: false,

  _phoneIncidentActive: false,

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
    canvas.width = 640;
    canvas.height = 480;
    const ctx = canvas.getContext("2d");

    try {
        ctx.drawImage(this._video, 0, 0, canvas.width, canvas.height);
        const frame = canvas.toDataURL("image/jpeg", 0.75);

        const data = await apiPost("/api/emotion/analyze", {
            session_id: Session.id,
            frame: frame
        });

        console.log("[CAMERA] API result:", data);

        this._renderQuality(data);
        this._handleNewEvents(data);
        this._drawDetectionBoxes(data);

        const now = Date.now();
        const faceCount = data.face_count || (data.face_detected ? 1 : 0);

        // 1. Process No Face state (0 faces)
        if (!data.face_detected && (data.status === "no_face" || data.status === "multiple_people_no_face")) {
            this._updateFaceStatus(data.status);

            this._multiFaceFirstSeen = null;
            this._lowLightFirstSeen = null;

            if (this._noFaceFirstSeen === null) {
                this._noFaceFirstSeen = now;
            }

            if (!this._noFaceIncidentActive) {
                const elapsedSec = (now - this._noFaceFirstSeen) / 1000;
                if (elapsedSec >= 2.0) {
                    this._noFaceIncidentActive = true;
                    console.log("[INTEGRITY] No face confirmed for 2+ seconds continuous -> 1 Camera Exit strike");
                    Integrity.registerIntegrityEvent("camera_exit");
                }
            }
        }

        // 2. Process Multiple Faces / Additional Person state (2+ faces)
        else if (data.status === "multiple_faces" || data.status === "additional_person_detected" || faceCount >= 2) {
            this._updateFaceStatus("multiple_faces");

            this._noFaceFirstSeen = null;
            this._lowLightFirstSeen = null;

            if (this._multiFaceFirstSeen === null) {
                this._multiFaceFirstSeen = now;
            }

            if (!this._multiFaceIncidentActive) {
                const elapsedSec = (now - this._multiFaceFirstSeen) / 1000;
                if (elapsedSec >= 2.0) {
                    this._multiFaceIncidentActive = true;
                    console.log("[INTEGRITY] Multiple faces confirmed for 2+ seconds continuous -> 1 Multiple Faces strike");
                    Integrity.registerIntegrityEvent("multiple_faces");
                }
            }
        }

        // 3. Process Low Light state
        else if (data.status === "low_light") {
            this._updateFaceStatus("low_light");

            this._noFaceFirstSeen = null;
            this._multiFaceFirstSeen = null;

            if (this._lowLightFirstSeen === null) {
                this._lowLightFirstSeen = now;
            }

            if (!this._lowLightIncidentActive) {
                const elapsedSec = (now - this._lowLightFirstSeen) / 1000;
                if (elapsedSec >= 5.0) {
                    this._lowLightIncidentActive = true;
                    console.log("[INTEGRITY] Low light confirmed for 5+ seconds continuous");
                    Integrity.registerIntegrityEvent("low_light");
                }
            }
        }

        // 4. Process Normal Single Candidate Face state (1 face, OK)
        else if (data.face_detected && faceCount === 1) {
            this._noFaceFirstSeen = null;
            this._noFaceIncidentActive = false;

            this._multiFaceFirstSeen = null;
            this._multiFaceIncidentActive = false;

            this._lowLightFirstSeen = null;
            this._lowLightIncidentActive = false;

            this._updateFaceStatus(data.status);
            this._updateUI(data);
        }

        // 5. Handle Phone detection UI indicator and strike confirmation
        if (data.phone) {
            const badge = document.getElementById("vbadge-phone");
            const dot = document.getElementById("vdot-phone");
            
            if (data.phone.detected) {
                console.log(`[PHONE DETECTED] class=cell phone confidence=${data.phone.confidence} boxes=`, data.phone.boxes);
                if (badge) badge.classList.add("hit");
                if (dot) dot.classList.add("on");

                if (data.phone.confirmed_strike) {
                    if (!this._phoneIncidentActive) {
                        this._phoneIncidentActive = true;
                        console.log("[INTEGRITY] Phone detection confirmed by backend telemetry -> 1 Phone strike");
                        Integrity.registerIntegrityEvent("phone_detected");
                    }
                }
            } else {
                this._phoneIncidentActive = false;
                if (typeof Integrity !== 'undefined' && (!Integrity.state || Integrity.state.phone_detected === 0)) {
                    if (badge) badge.classList.remove("hit");
                    if (dot) dot.classList.remove("on");
                }
            }
        }

        // Handle additional person confirmed strike from backend person_summary
        if (data.person_summary && data.person_summary.confirmed_strike) {
            if (!this._multiFaceIncidentActive) {
                this._multiFaceIncidentActive = true;
                console.log("[INTEGRITY] Additional person confirmed by backend telemetry -> 1 Additional Person strike");
                Integrity.registerIntegrityEvent("additional_person");
            }
        }
    } catch (e) {
        console.warn("[Emotion] Analysis failed:", e);
    }
  },

  _handlePhoneStrike(data) {
      if (data.phone && data.phone.confirmed_strike) {
          console.log("[INTEGRITY] Phone detection confirmed by backend telemetry");
          Integrity.registerIntegrityEvent("phone_detected");
      }
  },

  _handleAdditionalPersonStrike(data) {
      if (data.person_summary && data.person_summary.confirmed_strike) {
          console.log("[INTEGRITY] Additional person confirmed by backend telemetry");
          Integrity.registerIntegrityEvent("additional_person");
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

