/* ─────────────────────────────────────────────
   voice.js — Mic recording → /api/voice/analyze
   Waveform animation, transcript display, confidence meter
   Enhanced with real-time Speech-to-Text
   ───────────────────────────────────────────── */

const Voice = {
  _waveTimer:  null,
  _recognition: null,
  isRecording: false,
  scores:      [],
  _fullTranscript: "",
  _audioContext: null,
  _scriptProcessor: null,
  _audioSource: null,
  _leftchannel: [],
  _recordingLength: 0,
  _sampleRate: 0,
  _micStream: null,

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

      // Initialize AudioContext
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this._audioContext = new AudioContext();
      this._sampleRate = this._audioContext.sampleRate;

      // Get user audio stream
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this._audioSource = this._audioContext.createMediaStreamSource(stream);

      // Create a ScriptProcessorNode with bufferSize of 4096, 1 input channel, 1 output channel (mono)
      this._scriptProcessor = this._audioContext.createScriptProcessor(4096, 1, 1);

      this._leftchannel = [];
      this._recordingLength = 0;

      this._scriptProcessor.onaudioprocess = (e) => {
        if (!this.isRecording) return;
        const left = e.inputBuffer.getChannelData(0);
        this._leftchannel.push(new Float32Array(left));
        this._recordingLength += left.length;
      };

      // Connect nodes
      this._audioSource.connect(this._scriptProcessor);
      this._scriptProcessor.connect(this._audioContext.destination);

      // Save reference to stream to stop tracks later
      this._micStream = stream;

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

    // Disconnect and clean up Web Audio nodes
    if (this._scriptProcessor) {
      this._scriptProcessor.disconnect();
    }
    if (this._audioSource) {
      this._audioSource.disconnect();
    }
    if (this._audioContext) {
      this._audioContext.close();
    }

    // Stop microphone stream tracks
    if (this._micStream) {
      this._micStream.getTracks().forEach(t => t.stop());
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

    // Export audio to PCM WAV blob and send to backend
    const blob = this._exportWAV();
    this._analyze(blob);
  },

  _exportWAV() {
    const flatChannel = new Float32Array(this._recordingLength);
    let offset = 0;
    for (let i = 0; i < this._leftchannel.length; i++) {
      flatChannel.set(this._leftchannel[i], offset);
      offset += this._leftchannel[i].length;
    }

    const bufferArr = new ArrayBuffer(44 + flatChannel.length * 2);
    const view = new DataView(bufferArr);

    // RIFF identifier
    this._writeString(view, 0, 'RIFF');
    // file length
    view.setUint32(4, 36 + flatChannel.length * 2, true);
    // RIFF type
    this._writeString(view, 8, 'WAVE');
    // format chunk identifier
    this._writeString(view, 12, 'fmt ');
    // format chunk length
    view.setUint32(16, 16, true);
    // sample format (raw PCM)
    view.setUint16(20, 1, true);
    // channel count (1 channel, mono)
    view.setUint16(22, 1, true);
    // sample rate
    view.setUint32(24, this._sampleRate, true);
    // byte rate (sample rate * block align)
    view.setUint32(28, this._sampleRate * 2, true);
    // block align (1 channel * 2 bytes/sample)
    view.setUint16(32, 2, true);
    // bits per sample (16 bits)
    view.setUint16(34, 16, true);
    // data chunk identifier
    this._writeString(view, 36, 'data');
    // data chunk length
    view.setUint32(40, flatChannel.length * 2, true);

    // Write PCM audio samples
    let sampleOffset = 44;
    for (let i = 0; i < flatChannel.length; i++, sampleOffset += 2) {
      let s = Math.max(-1, Math.min(1, flatChannel[i]));
      view.setInt16(sampleOffset, s < 0 ? s * 0x8000 : s * 0x7FFF, true);
    }

    return new Blob([view], { type: 'audio/wav' });
  },

  _writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
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
