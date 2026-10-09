/* ─────────────────────────────────────────────
   integrity.js — Central Integrity Strike Manager
   Single source of truth for Anti-Cheating Telemetry & Strikes
   ───────────────────────────────────────────── */

// Maintain legacy global variables for backwards compatibility with any existing scripts,
// backed by Integrity.state.
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
 * Global entry point to terminate the interview session due to integrity violations.
 */
function terminateInterview(reason) {
  if (typeof Integrity !== 'undefined' && Integrity.terminateInterview) {
    Integrity.terminateInterview(reason);
  }
}

const Integrity = {
  active: false,
  terminated: false,
  fullscreenExitTerminated: false,
  _isTerminating: false,
  _winTimer: null,
  _camCheckTimer: null,
  _lastX: typeof window !== 'undefined' ? window.screenX : 0,
  _lastY: typeof window !== 'undefined' ? window.screenY : 0,
  _faceAbsent: 0,
  _noFaceEventTriggered: false,
  _fullscreenArmed: false,
  _lastEventTime: {},

  // Central Single Source of Truth for State
  state: {
    tab_switch: 0,
    camera_exit: 0,
    window_move: 0,
    multiple_faces: 0,
    additional_person: 0,
    phone_detected: 0,
    fullscreen_exit: 0,
    total: 0
  },

  _activeTabIncident: false,
  _tabIncidentStartTime: 0,
  _activeWindowMoveIncident: false,

  start() {
    console.log("[INTEGRITY] Central Strike Manager Active");
    this.active = true;

    // Fetch initial violation state from backend session if available
    this.syncInitialState();

    // 1. Tab Switching & Focus Correlation (document.visibilitychange + window.focus/blur)
    document.addEventListener("visibilitychange", () => {
      if (document.hidden && this.active && !this.terminated) {
        if (!this._activeTabIncident) {
          this._activeTabIncident = true;
          this._tabIncidentStartTime = Date.now();
          console.log("[INTEGRITY] event detected: tab_switch (document.hidden = true)");
          this.registerIntegrityEvent("tab_switch");
        }
      } else if (!document.hidden) {
        // Returned to tab - clear active incident state after brief settling delay
        setTimeout(() => {
          this._activeTabIncident = false;
          this._activeWindowMoveIncident = false;
        }, 1000);
      }
    });

    window.addEventListener("focus", () => {
      setTimeout(() => {
        this._activeTabIncident = false;
        this._activeWindowMoveIncident = false;
      }, 1000);
    });

    // 2. Window Focus Loss (window.blur) - Correlated to tab switch / ALT+TAB
    window.addEventListener("blur", () => {
      if (this.active && !this.terminated) {
        if (document.hidden || this._activeTabIncident || (Date.now() - this._tabIncidentStartTime) < 3000) {
          console.log("[INTEGRITY] window.blur correlated with tab_switch; ignoring duplicate window_move");
          return;
        }
        if (!this._activeWindowMoveIncident) {
          this._activeWindowMoveIncident = true;
          console.log("[INTEGRITY] event detected: window_move (window.blur)");
          this.registerIntegrityEvent("window_move");
        }
      }
    });

    // 3. Window Move Detection (polling screen position)
    this._winTimer = setInterval(() => {
      if (!this.active || this.terminated) return;
      if (document.hidden || this._activeTabIncident) return;
      const nx = window.screenX, ny = window.screenY;
      if (Math.abs(nx - this._lastX) > 50 || Math.abs(ny - this._lastY) > 50) {
        this._lastX = nx; this._lastY = ny;
        if (!this._activeWindowMoveIncident) {
          this._activeWindowMoveIncident = true;
          console.log("[INTEGRITY] event detected: window_move (position delta > 50px)");
          this.registerIntegrityEvent("window_move");
        }
      }
    }, 3000);

    // 4. Camera Status Check
    this._camCheckTimer = setInterval(() => {
      if (!this.active || this.terminated) return;
      this._checkCamera();
    }, 4000);

    // 5. Fullscreen Exit (Terminal Non-Strike Event)
    document.addEventListener("fullscreenchange", () => {
      if (document.fullscreenElement) {
        this._fullscreenArmed = true;
      } else if (this._fullscreenArmed && this.active && !this.terminated && !this.fullscreenExitTerminated && !this._isTerminating) {
        console.log("[INTEGRITY] event detected: fullscreen_exit (fullscreen disengaged)");
        this.registerIntegrityEvent("fullscreen_exit");
      }
    });
  },

  stop() {
    this.active = false;
    if (this._winTimer) clearInterval(this._winTimer);
    if (this._camCheckTimer) clearInterval(this._camCheckTimer);
  },

  async syncInitialState() {
    if (typeof Session === 'undefined' || !Session.id) return;
    try {
      const res = await fetch(`/api/session?session_id=${Session.id}`);
      if (res.ok) {
        const data = await res.json();
        if (data && data.violations) {
          this._applyStateFromBackend(data.violations);
          console.log("[INTEGRITY] Initial state synced from backend:", this.state);
        }
      }
    } catch (e) {
      console.warn("[INTEGRITY] Initial state sync warning:", e);
    }
  },

  _applyStateFromBackend(counts) {
    if (!counts) return;
    this.state.tab_switch = counts.tab_switch || 0;
    this.state.camera_exit = counts.camera_exit || 0;
    this.state.window_move = counts.window_move || 0;
    this.state.multiple_faces = counts.multiple_faces || 0;
    this.state.additional_person = counts.additional_person || 0;
    this.state.phone_detected = counts.phone_detected || 0;
    this.state.fullscreen_exit = counts.fullscreen_exit || 0;
    this.state.total = counts.total || (
      this.state.tab_switch + this.state.camera_exit + this.state.window_move +
      this.state.multiple_faces + this.state.additional_person + this.state.phone_detected
    );

    // Sync legacy variables
    tabSwitchCount = this.state.tab_switch;
    cameraExitCount = this.state.camera_exit;
    windowMoveCount = this.state.window_move;
    multipleFacesCount = this.state.multiple_faces;
    additionalPersonCount = this.state.additional_person;
    phoneDetectedCount = this.state.phone_detected;
    fullscreenExitCount = this.state.fullscreen_exit;
    totalViolations = this.state.total;

    this._updateUI();
  },

  /**
   * Central strike registration entry point.
   * Handles validation, temporal confirmation, cooldown, UI update,
   * backend persistence, and 3-strike / terminal conditions.
   */
  async registerIntegrityEvent(type, metadata = {}) {
    if (this.terminated || this.fullscreenExitTerminated) return;
    if (!this.active) {
      console.log(`[INTEGRITY] Event ${type} ignored: interview not active yet.`);
      return;
    }

    // SPECIAL HARD TERMINATION RULE: Fullscreen Exit
    if (type === "fullscreen_exit") {
      console.log("[INTEGRITY] event confirmed: FULLSCREEN_EXIT — triggering immediate hard termination");
      await this.terminateForFullscreenExit();
      return;
    }

    // Allowed 3-strike eligible event types
    const validTypes = ["tab_switch", "camera_exit", "window_move", "multiple_faces", "additional_person", "phone_detected"];
    if (validTypes.indexOf(type) === -1) {
      console.warn(`[INTEGRITY] Unknown event type '${type}' ignored.`);
      return;
    }

    // Cooldown check (2 seconds per event type to register strike fast on continuous incidents)
    const now = Date.now();
    const lastTime = this._lastEventTime[type] || 0;
    const COOLDOWN_MS = 2000;
    if (now - lastTime < COOLDOWN_MS) {
      console.log(`[INTEGRITY] event ${type} debounced (${now - lastTime}ms < ${COOLDOWN_MS}ms)`);
      return;
    }
    this._lastEventTime[type] = now;

    console.log(`[INTEGRITY] event confirmed: ${type}`);

    // Increment local state immediately
    this.state[type] = (this.state[type] || 0) + 1;
    this.state.total = (this.state.total || 0) + 1;
    const strikeNumber = this.state.total;
    console.log(`[INTEGRITY] strike registered: ${type} (Strike ${strikeNumber}/3)`);

    // Sync legacy vars
    this._applyStateFromBackend(this.state);

    // Update UI counters instantly
    this._updateUI();
    console.log(`[INTEGRITY] strike count updated UI: ${this.state.total}/3`);

    // Persist event/state to backend
    try {
      if (typeof apiPost === 'function' && typeof Session !== 'undefined' && Session.id) {
        const data = await apiPost("/api/integrity/violation", {
          session_id: Session.id,
          type: type,
          metadata: metadata
        });
        console.log("[INTEGRITY] event persisted to backend:", data);

        if (data && data.counts) {
          this._applyStateFromBackend(data.counts);
        }

        if (data && data.terminate) {
          this.terminateInterview(data.warning || "Interview Terminated: 3 Integrity Violations Reached");
          return;
        }

        if (data && data.warning) {
          this._showBanner(data.warning, data.warning_level);
        }
      }
    } catch (e) {
      console.warn("[INTEGRITY] Backend persistence failed:", e);
      if (this.state.total >= 3) {
        this.terminateInterview("Interview Terminated: 3 Integrity Violations Reached");
      } else {
        this._showBanner(`Warning: Strike ${this.state.total}/3 (${type.replace('_', ' ')})`, "warning");
      }
    }
  },

  // Legacy alias for compatibility with existing code calling Integrity._handleViolation
  _handleViolation(type) {
    return this.registerIntegrityEvent(type);
  },

  /**
   * Hard Fullscreen Exit Termination (1-strike terminal event).
   */
  async terminateForFullscreenExit() {
    if (this.terminated || this.fullscreenExitTerminated || this._isTerminating) return;
    this._isTerminating = true;
    this.terminated = true;
    this.fullscreenExitTerminated = true;
    this.stop();

    console.log("[INTEGRITY] Fullscreen Exit Terminal Event Executed");

    // 1. Show camera frame overlay warning immediately
    const camOverlay = document.getElementById("cam-fullscreen-overlay");
    if (camOverlay) {
        camOverlay.style.display = "flex";
    }

    // 2. Stop interview processes
    if (typeof timerInterval !== 'undefined' && timerInterval) clearInterval(timerInterval);
    if (typeof Emotion !== 'undefined' && Emotion.stop) Emotion.stop();
    if (typeof Voice !== 'undefined' && Voice._stop) Voice._stop();
    if (typeof AI_VOICE !== 'undefined' && AI_VOICE.stop) AI_VOICE.stop();

    // 3. Stop camera and microphone
    if (window.pageStream) {
      window.pageStream.getTracks().forEach(track => {
          track.stop();
          track.enabled = false;
      });
    }

    // 4. Disable all inputs and controls
    const toDisable = ["answer-text", "submit-btn", "mic-btn", "btn-skip", "tab-text", "tab-voice", "env-guidance-continue-btn"];
    toDisable.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
          el.disabled = true;
          el.style.opacity = "0.5";
          el.style.pointerEvents = "none";
      }
    });

    const ta = document.getElementById("answer-text");
    if (ta) ta.readOnly = true;

    // Update status text
    const statusEl = document.getElementById("ai-status");
    if (statusEl) {
        statusEl.textContent = "INTERVIEW TERMINATED — FULLSCREEN EXIT";
        statusEl.style.color = "var(--danger)";
    }

    // 5. Show terminate overlay with exact reason
    const overlay = document.getElementById("terminate-overlay");
    if (overlay) {
      const msgEl = overlay.querySelector(".term-msg");
      if (msgEl) msgEl.textContent = "Fullscreen exited during interview. The session has been automatically ended.";
      const titleEl = overlay.querySelector(".term-title");
      if (titleEl) titleEl.textContent = "Interview Terminated";
      overlay.classList.add("show");
    }

    this.state.fullscreen_exit = 1;
    this._updateUI();

    // 6. Save recording safely and persist termination to backend
    try {
      if (typeof saveRecording === 'function') {
        await saveRecording();
      }
    } catch (e) {
      console.warn("[INTEGRITY] Save recording failed on fullscreen termination:", e);
    }

    try {
      if (typeof apiPost === 'function' && typeof Session !== 'undefined' && Session.id) {
        await apiPost("/api/integrity/violation", {
          session_id: Session.id,
          type: "fullscreen_exit"
        });
      }
    } catch (e) {
      console.warn("[INTEGRITY] Terminal notification failed:", e);
    }

    // 7. Auto redirect to report page after flow completion
    setTimeout(() => {
      if (typeof goToReport === 'function') goToReport();
      else window.location.href = "/report?session_id=" + (typeof Session !== 'undefined' ? Session.id : "");
    }, 2500);
  },

  terminateInterview(reason) {
    if (this.terminated) return;
    this.terminated = true;
    this.stop();

    console.log("[INTEGRITY] 3-Strike Interview Termination Triggered:", reason);

    // Stop interview processes
    if (typeof timerInterval !== 'undefined' && timerInterval) clearInterval(timerInterval);
    if (typeof Emotion !== 'undefined' && Emotion.stop) Emotion.stop();
    if (typeof Voice !== 'undefined' && Voice._stop) Voice._stop();
    if (typeof AI_VOICE !== 'undefined' && AI_VOICE.stop) AI_VOICE.stop();

    // Stop camera and microphone
    if (window.pageStream) {
      window.pageStream.getTracks().forEach(track => {
          track.stop();
          track.enabled = false;
      });
    }

    // Disable all inputs and controls
    const toDisable = ["answer-text", "submit-btn", "mic-btn", "btn-skip", "tab-text", "tab-voice"];
    toDisable.forEach(id => {
      const el = document.getElementById(id);
      if (el) {
          el.disabled = true;
          el.style.opacity = "0.5";
          el.style.pointerEvents = "none";
      }
    });

    const ta = document.getElementById("answer-text");
    if (ta) ta.readOnly = true;

    // Show terminate overlay
    const overlay = document.getElementById("terminate-overlay");
    if (overlay) {
      const msgEl = overlay.querySelector(".term-msg");
      if (msgEl) msgEl.textContent = reason;
      overlay.classList.add("show");
    }
  },

  _checkCamera() {
    if (!window.pageStream) return;
    const videoTrack = window.pageStream.getVideoTracks()[0];
    if (!videoTrack || !videoTrack.enabled || videoTrack.readyState === 'ended') {
      console.log("[INTEGRITY] event detected: camera_exit (video track disabled or ended)");
      this.registerIntegrityEvent("camera_exit");
    }
  },

  reportCameraExit() {
    if (this._noFaceEventTriggered) return;
    const NO_FACE_CONFIRMATION_FRAMES = 5;
    this._faceAbsent++;
    if (this._faceAbsent >= NO_FACE_CONFIRMATION_FRAMES) {
      this._faceAbsent = 0;
      this._noFaceEventTriggered = true;
      console.log("[INTEGRITY] event detected: camera_exit (face absent for 5 frames / ~2 seconds)");
      this.registerIntegrityEvent("camera_exit");
    }
  },

  resetFaceCounter() {
    this._faceAbsent = 0;
    this._noFaceEventTriggered = false;
  },

  _updateUI() {
    const tabEl = document.getElementById("tab-switch-count");
    const camEl = document.getElementById("camera-exit-count");
    const winEl = document.getElementById("window-move-count");
    const multiEl = document.getElementById("multiple-faces-count");
    const addPersonEl = document.getElementById("additional-person-count");
    const phoneEl = document.getElementById("phone-detected-count");
    const fullEl = document.getElementById("fullscreen-exit-count");

    if (tabEl) tabEl.innerHTML = `Tab Switch <span>${this.state.tab_switch} / 3</span>`;
    if (camEl) camEl.innerHTML = `Camera Exit <span>${this.state.camera_exit} / 3</span>`;
    if (winEl) winEl.innerHTML = `Window Move <span>${this.state.window_move} / 3</span>`;
    if (multiEl) multiEl.innerHTML = `Multiple Faces <span>${this.state.multiple_faces} / 3</span>`;
    if (addPersonEl) addPersonEl.innerHTML = `Additional Person <span>${this.state.additional_person} / 3</span>`;
    if (phoneEl) phoneEl.innerHTML = `Phone Detected <span>${this.state.phone_detected} / 3</span>`;
    if (fullEl) fullEl.innerHTML = `Fullscreen Exit <span>${this.fullscreenExitTerminated ? "TERMINATED" : "Terminal"}</span>`;

    tabEl?.classList.toggle("active", this.state.tab_switch > 0);
    camEl?.classList.toggle("active", this.state.camera_exit > 0);
    winEl?.classList.toggle("active", this.state.window_move > 0);
    multiEl?.classList.toggle("active", this.state.multiple_faces > 0);
    addPersonEl?.classList.toggle("active", this.state.additional_person > 0);
    phoneEl?.classList.toggle("active", this.state.phone_detected > 0);
    fullEl?.classList.toggle("active", this.fullscreenExitTerminated);

    this._updateBadge("tab", this.state.tab_switch);
    this._updateBadge("cam", this.state.camera_exit);
    this._updateBadge("win", this.state.window_move);
    this._updateBadge("multi", this.state.multiple_faces);
    this._updateBadge("phone", this.state.phone_detected);
    this._updateBadge("full", this.fullscreenExitTerminated ? 1 : 0);
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
