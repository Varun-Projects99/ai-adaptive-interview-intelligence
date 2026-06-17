/* ─────────────────────────────────────────────
   integrity.js — Full Anti-Cheating Monitor
   Tab Switch, Camera Exit, Window Move/Focus
   ───────────────────────────────────────────── */

let tabSwitchCount = 0;
let cameraExitCount = 0;
let windowMoveCount = 0;
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

  // Called by external modules (like emotion detector) if they detect face exit
  reportCameraExit() {
      this._faceAbsent++;
      if (this._faceAbsent >= 3) { // Multiple consecutive absences
          this._faceAbsent = 0;
          this._handleViolation("camera_exit");
      }
  },

  resetFaceCounter() { this._faceAbsent = 0; },

  async _handleViolation(type) {
    if (this.terminated) return;

    // Cooldown to prevent duplicate counting (e.g. visibilitychange + blur)
    const now = Date.now();
    if (now - lastViolationTime < 1500) {
        return;
    }
    lastViolationTime = now;

    // Sync with backend
    try {
        const data = await apiPost("/api/integrity/violation", { 
            session_id: Session.id, 
            type: type 
        });
        
        // Update local counts from backend (source of truth)
        if (data.counts) {
            tabSwitchCount = data.counts.tab_switch || 0;
            cameraExitCount = data.counts.camera_exit || 0;
            windowMoveCount = data.counts.window_move || 0;
            totalViolations = data.violations || 0;
        }

        // Update UI counters
        this._updateUI();

        // 🚨 STRICT TERMINATION TRIGGER (Goal: only at 3/3)
        if (totalViolations >= 3) {
            terminateInterview(data.warning || "Interview Terminated: Excessive Integrity Violations");
            return;
        }

        // Show warning banner for 1/3 and 2/3
        if (data.warning && totalViolations < 3) {
            this._showBanner(data.warning, data.warning_level);
        }

    } catch (e) { 
        console.warn("[Integrity] Sync failed:", e);
        // Fallback to local increments if backend fails
        if (type === "tab_switch") tabSwitchCount++;
        else if (type === "camera_exit") cameraExitCount++;
        else if (type === "window_move") windowMoveCount++;
        totalViolations = tabSwitchCount + cameraExitCount + windowMoveCount;
        
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

    if (tabEl) tabEl.innerHTML = `Tab Switch <span>${tabSwitchCount} / 3</span>`;
    if (camEl) camEl.innerHTML = `Camera Exit <span>${cameraExitCount} / 3</span>`;
    if (winEl) winEl.innerHTML = `Window Move <span>${windowMoveCount} / 3</span>`;

    // Highlight rows if violations exist
    tabEl?.classList.toggle("active", tabSwitchCount > 0);
    camEl?.classList.toggle("active", cameraExitCount > 0);
    winEl?.classList.toggle("active", windowMoveCount > 0);

    // Update topbar badges
    this._updateBadge("tab", tabSwitchCount);
    this._updateBadge("cam", cameraExitCount);
    this._updateBadge("win", windowMoveCount);
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
