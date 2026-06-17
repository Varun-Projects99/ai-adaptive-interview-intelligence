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

  pageStream = await startWebcam();
  window.pageStream = pageStream;
  startTimer();
  startPageRecording(pageStream);
  Emotion.start(document.getElementById("webcam"));
  Integrity.start(onViolation, onTerminate);
  await loadNextQuestion();
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
  }, 1000);
}

/* ── QUESTIONS ──────────────────────────────── */
async function loadNextQuestion() {
  try {
    const data = await apiPost("/api/questions/next", { session_id: Session.id });

    if (data.done) {
      await endInterview();
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

    /* Clear previous answer */
    const ta = document.getElementById("answer-text");
    if (ta) ta.value = "";
    setText("voice-transcript", "Your spoken answer will appear here...");

  } catch(e) {
    setText("q-text", "Error loading question. Check server connection.");
    console.error("[Question]", e);
  }
}

/* ── SUBMIT ANSWER ──────────────────────────── */
async function submitAnswer() {
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

  try {
    const data = await apiPost("/api/answer/submit", {
      session_id: Session.id,
      question:   currentQuestion?.question || "",
      answer
    });
    techScores.push(data.score);
    updateTechMeter();
    showFeedback(data);
  } catch(e) {
    showToast("Submission failed. Please try again.", "err");
    console.error("[Submit]", e);
  } finally {
    if (btn) { btn.classList.remove("loading"); btn.disabled = false; }
  }
}

async function skipQuestion() {
  try {
    await apiPost("/api/answer/submit", {
      session_id: Session.id,
      question:   currentQuestion?.question || "",
      answer:     "[SKIPPED]"
    });
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
  await loadNextQuestion();
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
  window.location.href = "/report";
}

function goToReport() {
  Integrity.stop();
  clearInterval(timerInterval);
  saveRecording().then(() => { window.location.href = "/report"; });
}

/* ── DOM HELPERS ────────────────────────────── */
function setText(id, val)  { const el=document.getElementById(id); if(el) el.textContent=val; }
function setWidth(id, pct) { const el=document.getElementById(id); if(el) el.style.width=pct+"%"; }
