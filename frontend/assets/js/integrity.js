/* ─────────────────────────────────────────────
   integrity.js — Full Anti-Cheating Monitor
   Tab Switch, Camera Exit, Window Move/Focus, Fullscreen Exit
   ───────────────────────────────────────────── */

let tabSwitchCount = 0;
let cameraExitCount = 0;
let windowMoveCount = 0;
let multipleFacesCount = 0;
let additionalPersonCount = 0;
let phoneDetectedCount = 0;
let fullscreenExitCount = 0;
let totalViolations = 0;
let lastViolationTime = 0;

/**
 * Terminates the interview session due to integrity violations.
 */
function terminateInterview(reason) {
  if (Integrity.terminated) return;
  Integrity.terminated = true;
  Integrity.stop();

  console.log("[Integrity] Termination Triggered:", reason);

  // Stop interview processes
  if (typeof timerInterval !== 'undefined' && timerInterval) clearInterval(timerInterval);
  if (typeof Emotion !== 'undefined' && Emotion.stop) Emotion.stop();
  if (typeof Voice !== 'undefined' && Voice._stop) Voice._stop();

  // Stop camera and microphone
  if (window.pageStream) {
    window.pageStream.getTracks().forEach(track => {
        track.stop();
        track.enabled = false;
    });
  }

  // Disable inputs and interactions
  const toDisable = ["answer-text", "submit-btn", "mic-btn", "btn-skip"];
  toDisable.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
        el.disabled = true;
        el.style.opacity = "0.5";
        el.style.pointerEvents = "none";
    }
  });

  // Show fullscreen overlay with reason
  const overlay = document.getElementById("terminate-overlay");
  if (overlay) {
    const msgEl = overlay.querySelector(".term-msg");
    if (msgEl) msgEl.textContent = reason;
    overlay.classList.add("show");
  }

  // Auto redirect to report after 5 seconds
  setTimeout(() => {
    if (typeof goToReport === 'function') goToReport();
    else window.location.href = "/report";
  }, 5000);
}

const Integrity = {
  terminated: false,
  _winTimer: null,
  _camCheckTimer: null,
  _lastX: window.screenX,
  _lastY: window.screenY,
  _faceAbsent: 0,
  _noFaceEventTriggered: false,
  _fullscreenArmed: false,

  start() {
    console.log("[Integrity] Monitor Active");

    // 1. Tab Switching (document.visibilitychange)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        this._handleViolation("tab_switch");
      }
    });

    // 2. Window Focus Loss (window.blur)
    window.addEventListener("blur", () => {
      this._handleViolation("window_move");
    });

    // 3. Window Move Detection (polling)
    this._winTimer = setInterval(() => {
      const nx = window.screenX, ny = window.screenY;
      if (Math.abs(nx - this._lastX) > 50 || Math.abs(ny - this._lastY) > 50) {
        this._lastX = nx; this._lastY = ny;
        this._handleViolation("window_move");
      }
    }, 2000);

    // 4. Camera Status Check
    this._camCheckTimer = setInterval(() => {
        this._checkCamera();
    }, 4000);

    // 5. Fullscreen Exit
    document.addEventListener("fullscreenchange", () => {
        if (document.fullscreenElement) {
            this._fullscreenArmed = true;
        } else if (this._fullscreenArmed) {
            this._fullscreenArmed = false;
            this._handleViolation("fullscreen_exit");
        }
    });
  },

  stop() {
    clearInterval(this._winTimer);
    clearInterval(this._camCheckTimer);
  },

  _checkCamera() {
      if (!window.pageStream) return;
      const videoTrack = window.pageStream.getVideoTracks()[0];
      if (!videoTrack || !videoTrack.enabled || videoTrack.readyState === 'ended') {
          this._handleViolation("camera_exit");
      }
  },

  reportCameraExit() {
      if (this._noFaceEventTriggered) {
          return;
      }
      const NO_FACE_CONFIRMATION_FRAMES = 10;
      this._faceAbsent++;
      if (this._faceAbsent >= NO_FACE_CONFIRMATION_FRAMES) {
          this._faceAbsent = 0;
          this._noFaceEventTriggered = true;
          this._handleViolation("camera_exit");
      }
  },

  resetFaceCounter() {
      this._faceAbsent = 0;
      this._noFaceEventTriggered = false;
  },

  async _handleViolation(type) {
    if (this.terminated) return;

    // Cooldown to prevent duplicate counting for single physical Alt+Tab
    const now = Date.now();
    if (now - lastViolationTime < 1500) {
        return;
    }
    lastViolationTime = now;

    try {

        const data = await apiPost("/api/integrity/violation", {
            session_id: Session.id,
            type: type
        });

        if (data.counts) {
            tabSwitchCount = data.counts.tab_switch || 0;
            cameraExitCount = data.counts.camera_exit || 0;
            windowMoveCount = data.counts.window_move || 0;
            multipleFacesCount = data.counts.multiple_faces || 0;
            additionalPersonCount = data.counts.additional_person || 0;
            phoneDetectedCount = data.counts.phone_detected || 0;
            fullscreenExitCount = data.counts.fullscreen_exit || 0;
            totalViolations = data.violations || 0;
        }

        this._updateUI();

        if (totalViolations >= 3) {
            terminateInterview(data.warning || "Interview Terminated: Excessive Integrity Violations");
            return;
        }

        if (data.warning && totalViolations < 3) {
            this._showBanner(data.warning, data.warning_level);
        }

    } catch (e) {
        console.warn("[Integrity] Sync failed:", e);
        if (type === "tab_switch") tabSwitchCount++;
        else if (type === "camera_exit") cameraExitCount++;
        else if (type === "window_move") windowMoveCount++;
        else if (type === "multiple_faces") multipleFacesCount++;
        else if (type === "additional_person") additionalPersonCount++;
        else if (type === "phone_detected") phoneDetectedCount++;
        else if (type === "fullscreen_exit") fullscreenExitCount++;
        totalViolations = tabSwitchCount + cameraExitCount + windowMoveCount + multipleFacesCount + additionalPersonCount + phoneDetectedCount + fullscreenExitCount;

        this._updateUI();
        if (totalViolations >= 3) {
            terminateInterview("Interview Terminated: Excessive Violations");
        } else {
            this._showBanner(`Warning ${totalViolations}/3`, "warning");
        }
    }
  },

  _updateUI() {
    const tabEl = document.getElementById("tab-switch-count");
    const camEl = document.getElementById("camera-exit-count");
    const winEl = document.getElementById("window-move-count");
    const multiEl = document.getElementById("multiple-faces-count");
    const addPersonEl = document.getElementById("additional-person-count");
    const phoneEl = document.getElementById("phone-detected-count");
    const fullEl = document.getElementById("fullscreen-exit-count");

    if (tabEl) tabEl.innerHTML = `Tab Switch <span>${tabSwitchCount} / 3</span>`;
    if (camEl) camEl.innerHTML = `Camera Exit <span>${cameraExitCount} / 3</span>`;
    if (winEl) winEl.innerHTML = `Window Move <span>${windowMoveCount} / 3</span>`;
    if (multiEl) multiEl.innerHTML = `Multiple Faces <span>${multipleFacesCount} / 3</span>`;
    if (addPersonEl) addPersonEl.innerHTML = `Additional Person <span>${additionalPersonCount} / 3</span>`;
    if (phoneEl) phoneEl.innerHTML = `Phone Detected <span>${phoneDetectedCount} / 3</span>`;
    if (fullEl) fullEl.innerHTML = `Fullscreen Exit <span>${fullscreenExitCount} / 3</span>`;

    tabEl?.classList.toggle("active", tabSwitchCount > 0);
    camEl?.classList.toggle("active", cameraExitCount > 0);
    winEl?.classList.toggle("active", windowMoveCount > 0);
    multiEl?.classList.toggle("active", multipleFacesCount > 0);
    addPersonEl?.classList.toggle("active", additionalPersonCount > 0);
    phoneEl?.classList.toggle("active", phoneDetectedCount > 0);
    fullEl?.classList.toggle("active", fullscreenExitCount > 0);

    this._updateBadge("tab", tabSwitchCount);
    this._updateBadge("cam", cameraExitCount);
    this._updateBadge("win", windowMoveCount);
    this._updateBadge("multi", multipleFacesCount);
    this._updateBadge("phone", phoneDetectedCount);
    this._updateBadge("full", fullscreenExitCount);
  },


  _updateBadge(type, count) {
      const badge = document.getElementById(`vbadge-${type}`);
      const dot = document.getElementById(`vdot-${type}`);
      if (badge) badge.classList.toggle("hit", count > 0);
      if (dot) dot.classList.toggle("on", count > 0);
  },

  _showBanner(msg, level) {
    const el = document.getElementById("warn-banner");
    if (!el) return;
    el.textContent = msg;
    el.className = "warn-banner show" + (level === "critical" ? " critical" : "");
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove("show"), 4000);
  }
};
