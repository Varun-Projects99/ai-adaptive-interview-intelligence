/* ─────────────────────────────────────────────
   interview.js — Core interview flow
   Questions, answers, timer, recording, meters
   ───────────────────────────────────────────── */

let currentQuestion = null;
let techScores      = [];
let timerSec        = 0;
let timerInterval   = null;
let pageStream      = null;     // shared media stream (video + mic)
let mediaRecorder   = null;
let recChunks       = [];

/* ════════════════════════════════════════════
   INIT — called on page load
   ════════════════════════════════════════════ */
async function initInterview() {
  if (!Session.id) {
    window.location.href = "/";
    return;
  }

  // Warm up TTS voices immediately
  if (window.speechSynthesis) {
    const initV = window.speechSynthesis.getVoices();
    console.log("[AI TTS] Available voices on load:", initV.map(v => `${v.name} (${v.lang})`));
    
    window.speechSynthesis.onvoiceschanged = () => {
      const vlist = window.speechSynthesis.getVoices();
      console.log("[AI TTS] Available voices changed:", vlist.map(v => `${v.name} (${v.lang})`));
    };
  }
}

async function submitConsents() {
  const camCheck = document.getElementById("consent-camera").checked;
  const micCheck = document.getElementById("consent-mic").checked;
  const recCheck = document.getElementById("consent-recording").checked;

  const errConsent = document.getElementById("consent-error");
  const errMedia = document.getElementById("media-error");

  errConsent.style.display = "none";
  errMedia.style.display = "none";

  if (!camCheck || !micCheck || !recCheck) {
    errConsent.style.display = "block";
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    pageStream = stream;
    window.pageStream = pageStream;

    const v = document.getElementById("webcam");
    if (v) v.srcObject = stream;
    console.log("[Webcam] Started via Consent Approval");

    // Submit consent statuses to backend
    const consentRes = await fetch("/api/session/consent", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: Session.id,
        camera: true,
        microphone: true,
        recording: true
      })
    });

    if (!consentRes.ok) {
      console.warn("[Consent] Backend registration response error:", consentRes.status);
    }

    // Hide overlay
    document.getElementById("consent-overlay").style.display = "none";

    // Trigger live recording status on screen
    const recIndicator = document.createElement("div");
    recIndicator.id = "rec-indicator";
    recIndicator.style = "display: flex; align-items: center; gap: 6px; background: rgba(255, 61, 90, 0.15); border: 1px solid var(--danger); padding: 4px 8px; border-radius: 4px; font-family: var(--fm); font-size: 10px; font-weight: 700; color: var(--danger); animation: blinker 1s linear infinite; line-height: 1;";
    recIndicator.innerHTML = '<span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: var(--danger);"></span> 🔴 RECORDING';

    const keyframesStyle = document.createElement("style");
    keyframesStyle.innerHTML = "@keyframes blinker { 50% { opacity: 0.4; } }";
    document.head.appendChild(keyframesStyle);

    const recContainer = document.getElementById("rec-container");
    if (recContainer) recContainer.appendChild(recIndicator);

    // Initialize the rest of the interview
    startTimer();
    startPageRecording(pageStream);
    Emotion.start(document.getElementById("webcam"));
    Integrity.start(onViolation, onTerminate);
    await loadNextQuestion();

  } catch (err) {
    console.error("[Consent Media Error]", err);
    errMedia.style.display = "block";
  }
}

/* ── WEBCAM ─────────────────────────────────── */
async function startWebcam() {
  try {
    const s = await navigator.mediaDevices.getUserMedia({ video: true, audio: true });
    const v = document.getElementById("webcam");
    if (v) v.srcObject = s;
    console.log("[Webcam] Started");
    return s;
  } catch(e) {
    showToast("Webcam/mic not available: " + e.message, "err");
    console.error("[Webcam]", e);
    return null;
  }
}

/* ── SESSION RECORDING ──────────────────────── */
function startPageRecording(stream) {
  if (!stream) return;
  try {
    mediaRecorder = new MediaRecorder(stream, { mimeType: "video/webm;codecs=vp8,opus" });
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) recChunks.push(e.data); };
    mediaRecorder.start(1000);
    console.log("[Recording] Session recording started");
  } catch(e) {
    console.warn("[Recording] Not available:", e.message);
  }
}

async function saveRecording() {
  if (!mediaRecorder || mediaRecorder.state === "inactive") return;
  
  const recIndicator = document.getElementById("rec-indicator");
  if (recIndicator) {
    recIndicator.innerHTML = '<span style="display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: #888;"></span> Recording stopped.';
    recIndicator.style.background = "rgba(255, 255, 255, 0.1)";
    recIndicator.style.borderColor = "var(--border)";
    recIndicator.style.color = "var(--text-muted)";
    recIndicator.style.animation = "none";
  }

  return new Promise(resolve => {
    mediaRecorder.onstop = async () => {
      const blob = new Blob(recChunks, { type: "video/webm" });
      const form = new FormData();
      form.append("session_id", Session.id);
      form.append("recording", blob, "interview.webm");
      try {
        await fetch(API + "/api/recording/save", { method:"POST", body: form });
        console.log("[Recording] Saved");
      } catch(e) { console.warn("[Recording] Save failed:", e); }
      resolve();
    };
    mediaRecorder.stop();
  });
}

/* ── TIMER ──────────────────────────────────── */
function startTimer() {
  timerInterval = setInterval(() => {
    timerSec++;
    const m  = String(Math.floor(timerSec/60)).padStart(2,"0");
    const s  = String(timerSec%60).padStart(2,"0");
    const el = document.getElementById("timer");
    if (el) el.textContent = m + ":" + s;

    // 1.3 hours maximum duration limit (4680 seconds)
    if (timerSec >= 4680) {
      showToast("Maximum time limit reached (1.3 hours). Submitting your interview...", "warn");
      endInterview();
    }
  }, 1000);
}

/* ── AI VOICE & AVATAR STATE MANAGEMENT ────────────────── */
let nextQuestionPayload = null;
let interviewDone = false;

const AI_VOICE = {
  speaking: false,
  utterance: null,
  
  speak(text, language, onStart, onEnd) {
      if (!window.speechSynthesis) {
          console.warn("[AI TTS] Speech synthesis not supported by this browser.");
          if (onEnd) onEnd();
          return;
      }

      let langCode = "en-IN";
      if (language === "hi") langCode = "hi-IN";
      else if (language === "kn") langCode = "kn-IN";

      console.log(`[AI TTS] Language: ${language === "kn" ? "Kannada" : language === "hi" ? "Hindi" : "English"}`);
      console.log(`[AI TTS] Text: ${text}`);
      console.log(`[AI TTS] Voice language: ${langCode}`);

      const voices = window.speechSynthesis.getVoices();
      console.log("[AI TTS] Available voices:", voices.map(v => `${v.name} (${v.lang})`));
      
      let bestVoice = voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith(langCode.toLowerCase()));
      
      // Fallback for English: search for any "en" voice if en-IN is not found
      if (!bestVoice && language === "en") {
          bestVoice = voices.find(v => v.lang.toLowerCase().replace('_', '-').startsWith("en"));
      }

      if (!bestVoice) {
          const langName = language === "kn" ? "Kannada" : language === "hi" ? "Hindi" : "English";
          const warnMsg = `${langName} voice is not available on this device. Please install/enable a ${langName} speech voice or switch language.`;
          console.error(`[AI TTS] ${warnMsg}`);
          showToast(warnMsg, "err");
          
          // Trigger the state transitions so candidate is not locked/stuck
          if (onStart) onStart();
          setTimeout(() => {
              if (onEnd) onEnd();
          }, 1500);
          return;
      }

      console.log(`[AI TTS] Selected voice: ${bestVoice.name} (${bestVoice.lang})`);

      this.utterance = new SpeechSynthesisUtterance(text);
      this.utterance.lang = bestVoice.lang;
      this.utterance.voice = bestVoice;
      this.utterance.rate = 0.95; // slightly slower for better comprehensibility
      
      this.utterance.onstart = () => {
          this.speaking = true;
          console.log("[AI TTS] Speaking started");
          if (onStart) onStart();
      };
      
      this.utterance.onend = () => {
          this.speaking = false;
          console.log("[AI TTS] Speaking finished");
          if (onEnd) onEnd();
      };

      this.utterance.onerror = (e) => {
          console.error("[AI TTS] Speech error:", e);
          this.speaking = false;
          if (onEnd) onEnd();
      };

      window.speechSynthesis.speak(this.utterance);
  },

  stop() {
      if (window.speechSynthesis) {
          console.log("[AI TTS] Cancelling active speech synthesis.");
          window.speechSynthesis.cancel();
      }
      this.speaking = false;
  }
};

function setAvatarState(state, text) {
  const avatar = document.getElementById("ai-avatar");
  const status = document.getElementById("ai-status");
  const speechText = document.getElementById("ai-speech-text");
  
  if (avatar) {
    avatar.className = "avatar-core " + state;
  }
  if (status) {
    status.textContent = "AI INTERVIEWER - " + state.toUpperCase();
    if (state === "speaking") {
      status.style.color = "var(--success)";
    } else if (state === "listening") {
      status.style.color = "var(--warn)";
    } else {
      status.style.color = "var(--accent)";
    }
  }
  if (speechText && text) {
    speechText.textContent = text;
  }
}

/* ── QUESTIONS ──────────────────────────────── */
async function loadNextQuestion() {
  setAvatarState("thinking", "Generating question...");
  AI_VOICE.stop();

  try {
    let data;
    if (nextQuestionPayload) {
      data = nextQuestionPayload;
      nextQuestionPayload = null;
    } else {
      data = await apiPost("/api/questions/next", { session_id: Session.id });
    }

    if (data.done || interviewDone) {
      // 40 minutes minimum duration limit (2400 seconds)
      if (timerSec < 2400) {
        showToast("Minimum interview duration is 40 minutes. Please take your time to elaborate.", "warn");
        const submitBtn = document.getElementById("submit-btn");
        if (submitBtn) {
          submitBtn.disabled = true;
          submitBtn.textContent = "Please wait (40m min)";
        }
        const checkInterval = setInterval(async () => {
          if (timerSec >= 2400) {
            clearInterval(checkInterval);
            await endInterview();
          } else {
            const remainingMin = Math.ceil((2400 - timerSec) / 60);
            showToast(`Please wait ${remainingMin} more minutes to complete the minimum 40-minute duration.`, "info");
          }
        }, 15000);
      } else {
        await endInterview();
      }
      return;
    }

    currentQuestion = data.question;
    const total     = data.total || Session.total;
    const idx       = (data.index || 0) + 1;
    const diff      = data.difficulty || "easy";

    /* Update question card */
    setText("q-text",  currentQuestion.question || "");
    setText("q-skill", currentQuestion.skill    ? "Skill: " + currentQuestion.skill : "");
    setText("q-index", `Question ${idx} / ${total}`);
    setWidth("q-bar",  (idx / Math.max(total,1)) * 100);

    const diffEl = document.getElementById("q-diff");
    if (diffEl) {
      diffEl.textContent = diff.toUpperCase();
      diffEl.className   = "diff-badge " + diff;
    }

    // Update avatar personality badge
    const pers = localStorage.getItem("personality") || "professional";
    setText("ai-personality-badge", "Personality: " + pers.charAt(0).toUpperCase() + pers.slice(1));

    // Compile text to speak
    const speechText = currentQuestion.question || "";
    const lang = localStorage.getItem("language") || "en";

    console.log("[AI TTS] Selected language:", lang);
    console.log("[AI TTS] Speech text:", speechText);

    // Play TTS directly in the configured language
    setAvatarState("speaking", speechText);
    
    AI_VOICE.speak(speechText, lang,
        () => {
            const langLabel = lang === "kn" ? "Kannada" : lang === "hi" ? "Hindi" : "English";
            setAvatarState("speaking", `Speaking (${langLabel}): ` + speechText);
        },
        () => {
            setAvatarState("listening", "Waiting for candidate's response...");
            
            // Auto transition to voice tab / trigger mic if appropriate
            const isVoice = document.getElementById("tab-voice")?.classList.contains("active");
            if (isVoice && typeof Voice !== "undefined" && !Voice.recording) {
                Voice.toggle();
            }
        }
    );

    /* Clear previous answer */
    const ta = document.getElementById("answer-text");
    if (ta) ta.value = "";
    setText("voice-transcript", "Your spoken answer will appear here...");

  } catch(e) {
    setAvatarState("idle", "Error loading question.");
    setText("q-text", "Error loading question. Check server connection.");
    console.error("[Question]", e);
  }
}

/* ── SUBMIT ANSWER ──────────────────────────── */
async function submitAnswer() {
  AI_VOICE.stop();
  const isText = document.getElementById("tab-text")?.classList.contains("active");
  const answer = isText
    ? (document.getElementById("answer-text")?.value.trim() || "")
    : Voice.getTranscript();

  if (!answer) {
    showToast("Please type or speak your answer first.", "warn");
    return;
  }

  const btn = document.getElementById("submit-btn");
  if (btn) { btn.classList.add("loading"); btn.disabled = true; }
  setAvatarState("thinking", "AI is evaluating your response...");

  try {
    const data = await apiPost("/api/answer/submit", {
      session_id: Session.id,
      question:   currentQuestion?.question || "",
      answer
    });
    
    // Save next payloads
    techScores.push(data.score);
    updateTechMeter();
    
    nextQuestionPayload = data.next_question;
    interviewDone = data.done;

    showFeedback(data);
  } catch(e) {
    showToast("Submission failed. Please try again.", "err");
    console.error("[Submit]", e);
    setAvatarState("idle", "Submission failed.");
  } finally {
    if (btn) { btn.classList.remove("loading"); btn.disabled = false; }
  }
}

async function skipQuestion() {
  AI_VOICE.stop();
  try {
    const data = await apiPost("/api/answer/submit", {
      session_id: Session.id,
      question:   currentQuestion?.question || "",
      answer:     "[SKIPPED]"
    });
    nextQuestionPayload = data.next_question;
    interviewDone = data.done;
  } catch(e) { /* ignore */ }
  await loadNextQuestion();
}

/* ── FEEDBACK POPUP ─────────────────────────── */
function showFeedback(data) {
  const score  = data.score || 0;
  const scoreEl = document.getElementById("fb-score");
  if (scoreEl) {
    scoreEl.textContent = score;
    scoreEl.className   = "score-val " + scoreClass(score);
    scoreEl.style.fontSize = "52px";
  }

  setText("fb-feedback", data.feedback || "");

  // Populate dynamic evaluation dimensions grid and details explanation
  const labelMap = {
    "technical_correctness": "Technical Correctness",
    "relevance": "Relevance",
    "depth": "Depth",
    "clarity": "Clarity",
    "problem_solving": "Problem Solving",
    "communication": "Communication",
    "completeness": "Completeness"
  };
  const getConfClass = (c) => c === "HIGH" ? "success" : c === "LOW" ? "danger" : "warn";

  const dimsGrid = document.getElementById("fb-dimensions-grid");
  const dimsDetails = document.getElementById("fb-dimensions-details");
  
  if (dimsGrid && data.dimensions) {
    let gridHtml = "";
    let detailsHtml = "";
    
    Object.entries(data.dimensions).forEach(([key, val]) => {
      const label = labelMap[key] || key;
      const scoreStr = val.score !== null ? `${val.score}%` : "N/A";
      const conf = val.confidence || "MEDIUM";
      const confClass = getConfClass(conf);
      
      // Grid item
      gridHtml += `
        <div class="flex justify-between items-center" style="background: var(--surface2); padding: 8px 12px; border: 1px solid var(--border); font-size: 12px">
          <span style="color: var(--text-muted)">${label}</span>
          <div class="flex items-center gap-8">
            <span style="font-weight: 700; color: ${val.score !== null ? 'var(--text)' : 'var(--text-muted)'}">${scoreStr}</span>
            <span class="chip ${confClass}" style="font-size: 8px; padding: 2px 6px; letter-spacing: 0.05em; transform: scale(0.95)">${conf}</span>
          </div>
        </div>
      `;
      
      // Expandable details item
      if (val.reason || (val.evidence && val.evidence.length)) {
        const evidenceStr = val.evidence && val.evidence.length 
          ? val.evidence.map(e => `<li style="margin-left: 12px; font-size: 11px; list-style-type: circle; color: var(--text-muted)">"${e}"</li>`).join("")
          : "";
          
        detailsHtml += `
          <div style="border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 6px">
            <div style="font-size: 12px; font-weight: 700; display: flex; justify-content: space-between; align-items: center; color: var(--accent2)">
              <span>${label} — ${scoreStr}</span>
              <span class="chip ${confClass}" style="font-size: 8px; padding: 2px 6px; scale: 0.9">${conf} Confidence</span>
            </div>
            <div style="font-size: 11px; color: var(--text); margin-top: 4px; line-height: 1.4">${val.reason || 'No details provided.'}</div>
            ${evidenceStr ? `<div style="margin-top: 4px"><span style="font-size: 10px; text-transform: uppercase; color: var(--text-muted); font-family: var(--fm)">Evidence:</span><ul style="margin-top: 2px">${evidenceStr}</ul></div>` : ""}
          </div>
        `;
      }
    });
    
    dimsGrid.innerHTML = gridHtml;
    dimsDetails.innerHTML = detailsHtml || `<div style="font-size: 11px; color: var(--text-muted)">No details.</div>`;
  }

  const strEl = document.getElementById("fb-strengths");
  if (strEl) strEl.innerHTML =
    (data.strengths || []).map(s => `<div class="fb-list-item strength">✓ ${s}</div>`).join("");

  const impEl = document.getElementById("fb-improvements");
  if (impEl) impEl.innerHTML =
    (data.improvements || []).map(s => `<div class="fb-list-item improve">→ ${s}</div>`).join("");

  const nd    = data.next_difficulty || "easy";
  const ndEl  = document.getElementById("fb-next-diff");
  if (ndEl) {
    ndEl.textContent = "Next difficulty: " + nd.toUpperCase();
    ndEl.className   = "chip " + (nd==="hard"?"danger": nd==="medium"?"warn":"success");
  }

  const ov = document.getElementById("feedback-overlay");
  if (ov) ov.classList.add("show");
}

async function closeFeedback() {
  const ov = document.getElementById("feedback-overlay");
  if (ov) ov.classList.remove("show");
  
  if (interviewDone) {
    await endInterview();
  } else {
    await loadNextQuestion();
  }
}

/* ── METERS ─────────────────────────────────── */
function updateTechMeter() {
  if (!techScores.length) return;
  const avg = Math.round(techScores.reduce((a,b)=>a+b,0) / techScores.length);
  setWidth("tech-bar", avg);
  setText("tech-val", avg + "%");
}

/* ── TAB SWITCHING ──────────────────────────── */
function switchTab(tab) {
  const isText = tab === "text";
  document.getElementById("tab-text") ?.classList.toggle("active", isText);
  document.getElementById("tab-voice")?.classList.toggle("active", !isText);
  const pt = document.getElementById("panel-text");
  const pv = document.getElementById("panel-voice");
  if (pt) pt.style.display = isText ? "flex" : "none";
  if (pv) pv.style.display = isText ? "none"  : "flex";
}

/* ── INTEGRITY CALLBACKS ────────────────────── */
function onViolation(data) { /* UI updated by Integrity module */ }

function onTerminate() {
  clearInterval(timerInterval);
  Emotion.stop();
  const ov = document.getElementById("terminate-overlay");
  if (ov) ov.classList.add("show");
}

/* ── END INTERVIEW ──────────────────────────── */
async function endInterview() {
  clearInterval(timerInterval);
  Emotion.stop();
  Integrity.stop();
  await saveRecording();
  window.location.href = "/report?session_id=" + Session.id;
}

function goToReport() {
  Integrity.stop();
  clearInterval(timerInterval);
  saveRecording().then(() => { window.location.href = "/report?session_id=" + Session.id; });
}

/* ── DOM HELPERS ────────────────────────────── */
function setText(id, val)  { const el=document.getElementById(id); if(el) el.textContent=val; }
function setWidth(id, pct) { const el=document.getElementById(id); if(el) el.style.width=pct+"%"; }
