/* ─────────────────────────────────────────────
   voice.js — Mic recording → /api/voice/analyze
   Waveform animation, transcript display, confidence meter
   Enhanced with real-time Speech-to-Text
   ───────────────────────────────────────────── */

const Voice = {
  _recorder:   null,
  _chunks:     [],
  _waveTimer:  null,
  _recognition: null,
  isRecording: false,
  scores:      [],
  _fullTranscript: "",

  /* Initialize Speech Recognition */
  _initRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.warn("[Voice] Speech Recognition not supported in this browser.");
      return null;
    }

    const recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = "en-US";

    recognition.onstart = () => {
      console.log("Voice recognition started");
    };

    recognition.onresult = (event) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      this._fullTranscript += finalTranscript;
      const transcript = this._fullTranscript + interimTranscript;
      
      console.log("Voice recognized:", transcript);
      this._updateTranscriptUI(transcript);
    };

    recognition.onerror = (event) => {
      console.error("[Voice] Recognition error:", event.error);
      if (event.error === 'not-allowed' || event.error === 'service-not-allowed') {
        if (typeof showToast === "function") showToast("Microphone permission denied or service unavailable.", "err");
        this.isRecording = false;
        this._setMicUI(false);
      }
    };

    recognition.onend = () => {
      console.log("Voice recognition stopped");
      // Automatically restart recognition if it stops unexpectedly while interview is active
      if (this.isRecording) {
        try {
          this._recognition.start();
        } catch (e) {
          console.error("[Voice] Error restarting recognition:", e);
        }
      }
    };

    return recognition;
  },

  /* Toggle start/stop */
  async toggle() {
    this.isRecording ? this._stop() : await this._start();
  },

  _initialText: "",

  async _start() {
    try {
      // Capture existing text to append to it
      const targetSelectors = ["textarea", "#answer", ".answer-input", "#answer-text"];
      this._initialText = "";
      for (const selector of targetSelectors) {
        const el = document.querySelector(selector);
        if (el && (el.tagName === "TEXTAREA" || el.tagName === "INPUT")) {
          this._initialText = el.value.trim();
          break;
        }
      }

      // Trigger microphone permission request automatically
      const stream    = await navigator.mediaDevices.getUserMedia({ audio: true });
      this._chunks    = [];
      this._recorder  = new MediaRecorder(stream);

      this._recorder.ondataavailable = e => this._chunks.push(e.data);
      this._recorder.onstop = async () => {
        const blob = new Blob(this._chunks, { type: "audio/webm" });
        stream.getTracks().forEach(t => t.stop());
        await this._analyze(blob);
      };

      // Live STT initialization
      if (!this._recognition) {
        this._recognition = this._initRecognition();
      }

      this.isRecording = true;
      if (this._recognition) {
        this._fullTranscript = ""; // Reset for new session
        try {
          this._recognition.start();
        } catch (e) {
          console.warn("[Voice] Recognition already started or error:", e);
        }
      } else {
        if (typeof showToast === "function") showToast("Speech recognition not supported in this browser. Falling back to audio recording only.", "warn");
      }

      this._recorder.start();
      this._setMicUI(true);
      this._animateWave(true);
      this._setStatus("🔴 Recording... click mic to stop");
    } catch(e) {
      if (typeof showToast === "function") showToast("Microphone access denied. Please allow mic permissions.", "err");
      console.error("[Voice]", e);
    }
  },

  _stop() {
    this.isRecording = false;

    if (this._recorder && this._recorder.state !== "inactive") {
      this._recorder.stop();
    }
    
    if (this._recognition) {
      try {
        this._recognition.stop();
      } catch (e) {
        console.warn("[Voice] Error stopping recognition:", e);
      }
    }

    this._setMicUI(false);
    this._animateWave(false);
    this._setStatus("Analysing your voice...");
  },

  _updateTranscriptUI(text) {
    /* Live display in the dedicated voice transcript area */
    const tEl = document.getElementById("voice-transcript");
    if (tEl) tEl.textContent = text || "Listening...";

    /* Live sync to the answer input/textarea */
    const targetSelectors = ["textarea", "#answer", ".answer-input", "#answer-text"];
    let inputFound = false;

    const fullText = (this._initialText ? this._initialText + " " : "") + text;

    for (const selector of targetSelectors) {
      const el = document.querySelector(selector);
      if (el && (el.tagName === "TEXTAREA" || el.tagName === "INPUT")) {
        el.value = fullText;
        inputFound = true;
        break;
      }
    }

    // Support for contenteditable divs if no standard input found
    if (!inputFound) {
      const editable = document.querySelector("[contenteditable='true']");
      if (editable) {
        editable.textContent = fullText;
      }
    }
  },

  async _analyze(blob) {
    if (typeof Session === "undefined" || !Session.id) return;

    const form = new FormData();
    form.append("session_id", Session.id);
    form.append("audio", blob, "answer.wav");

    try {
      const res  = await fetch((typeof API !== "undefined" ? API : "") + "/api/voice/analyze", { method:"POST", body: form });
      const data = await res.json();

      this.scores.push(data.confidence_score || 50);

      /* Status */
      this._setStatus(`${data.confidence_label || "Analyzed"} — ${data.confidence_score || 0}/100`);

      /* Confidence meter */
      const avg = this.avgScore();
      const bar = document.getElementById("conf-bar");
      const val = document.getElementById("conf-val");
      if (bar) bar.style.width = avg + "%";
      if (val) val.textContent = avg + "%";

      /* Final transcript sync if backend provides a better one */
      if (data.transcript) {
        this._updateTranscriptUI(data.transcript);
      }

    } catch(e) {
      this._setStatus("Voice analysis unavailable.");
      console.warn("[Voice]", e);
    }
  },

  _setMicUI(recording) {
    const btn = document.getElementById("mic-btn");
    if (!btn) return;
    btn.classList.toggle("recording", recording);
    btn.textContent = recording ? "⏹️" : "🎙️";
  },

  _setStatus(msg) {
    const el = document.getElementById("voice-status");
    if (el) el.textContent = msg;
  },

  _animateWave(active) {
    const bars = document.querySelectorAll(".wave-bar");
    if (active) {
      if (this._waveTimer) clearInterval(this._waveTimer);
      this._waveTimer = setInterval(() => {
        bars.forEach(b => {
          b.style.height = (5 + Math.random() * 26) + "px";
        });
      }, 90);
    } else {
      clearInterval(this._waveTimer);
      this._waveTimer = null;
      const defaults = [8,16,12,20,10,18,14,22];
      bars.forEach((b, i) => { b.style.height = (defaults[i] || 12) + "px"; });
    }
  },

  getTranscript() {
    const el = document.getElementById("voice-transcript");
    const t  = el ? el.textContent.trim() : "";
    return (t && t !== "Your spoken answer will appear here...") ? t : "";
  },

  avgScore() {
    if (!this.scores.length) return 0;
    return Math.round(this.scores.reduce((a,b) => a+b, 0) / this.scores.length);
  }
};
