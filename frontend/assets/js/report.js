/* ─────────────────────────────────────────────
   report.js — Fetch /api/report/generate and render full dashboard
   ───────────────────────────────────────────── */

async function loadReport() {
  if (!Session.id) {
    renderError("No active session found. Please start a new interview.");
    return;
  }

  try {
    const data = await apiPost("/api/report/generate", { session_id: Session.id });
    renderReport(data);
  } catch(e) {
    renderError("Could not load report: " + e.message);
    console.error("[Report]", e);
  }
}

function renderReport(d) {
  const scores  = d.scores   || {};
  const summary = d.summary  || {};
  const answers = d.answers  || [];
  const reccos  = d.recommendations || [];
  const emots   = d.emotion_breakdown || {};
  const viols   = summary.violations || {};
  const prog    = summary.difficulty_progression || [];

  const tScore  = scores.technical  || 0;
  const cScore  = scores.confidence || 0;
  const rScore  = scores.readiness_index || 0;

  document.getElementById("report-body").innerHTML = `

    ${d.terminated ? `
    <div style="background:rgba(255,61,90,.08);border:1px solid rgba(255,61,90,.4);
      padding:14px 20px;color:var(--danger);font-size:14px;
      display:flex;align-items:center;gap:12px;margin-bottom:28px">
      <span style="font-size:20px">🚫</span>
      <span>This interview was <strong>terminated</strong> due to repeated integrity violations.</span>
    </div>` : ""}

    <!-- HEADER -->
    <div class="flex justify-between items-center mb-32">
      <div>
        <div class="font-mono text-muted mb-8"
             style="font-size:10px;letter-spacing:.18em;text-transform:uppercase">
          Performance Report
        </div>
        <div class="font-heading"
             style="font-size:clamp(28px,5vw,52px);font-weight:800;letter-spacing:-2px;line-height:1">
          Your Interview<br>Results
        </div>
      </div>
      <div class="font-mono text-muted" style="font-size:12px;text-align:right;line-height:2.2">
        ${summary.total_questions||0} Questions Answered<br>
        ${(summary.skills_covered||[]).length} Skills Tested<br>
        ${d.terminated
          ? '<span style="color:var(--danger)">TERMINATED</span>'
          : '<span style="color:var(--success)">COMPLETED</span>'}
      </div>
    </div>

    <!-- SCORE GRID -->
    <div class="score-grid mb-32">
      <div class="score-card tech">
        <div class="sc-label">Technical Score</div>
        <div class="score-val ${scoreClass(tScore)}" style="font-size:44px">${tScore}%</div>
        <div class="sc-sub">Answer quality</div>
      </div>
      <div class="score-card conf">
        <div class="sc-label">Voice Confidence</div>
        <div class="score-val ${scoreClass(cScore)}" style="font-size:44px">${cScore}%</div>
        <div class="sc-sub">Speech analysis</div>
      </div>
      <div class="score-card emot">
        <div class="sc-label">Emotion Stability</div>
        <div class="font-heading"
             style="font-size:22px;font-weight:800;color:var(--warn);line-height:1.3;margin-top:4px">
          ${scores.emotion_stability || "—"}
        </div>
        <div class="sc-sub">Webcam analysis</div>
      </div>
      <div class="score-card read">
        <div class="sc-label">Readiness Index</div>
        <div class="score-val ${scoreClass(rScore)}" style="font-size:44px">${rScore}</div>
        <div class="sc-sub">${scores.readiness_label || "—"}</div>
      </div>
    </div>

    <!-- EMOTION BREAKDOWN -->
    <div class="mb-32">
      <div class="section-title">Emotion Breakdown</div>
      <div class="flex-col gap-12">
        ${Object.entries(emots).length
          ? Object.entries(emots).map(([k,v]) => `
              <div class="flex items-center gap-12">
                <div style="font-size:13px;min-width:90px;text-transform:capitalize">${k}</div>
                <div class="emot-bar-wrap">
                  <div class="emot-bar-fill ${k}" style="width:${v}%"></div>
                </div>
                <div class="font-mono text-muted" style="font-size:12px;min-width:44px;text-align:right">
                  ${v}%
                </div>
              </div>`).join("")
          : `<div class="text-muted" style="font-size:13px">No emotion data was recorded.</div>`}
      </div>
    </div>

    <!-- DIFFICULTY PROGRESSION -->
    <div class="mb-32">
      <div class="section-title">Difficulty Progression</div>
      <div class="diff-timeline mb-8">
        ${prog.map(d => `<div class="diff-dot ${d}" title="${d}"></div>`).join("")
          || `<div class="text-muted" style="font-size:13px">No data.</div>`}
      </div>
      <div class="flex gap-16" style="font-size:12px;color:var(--text-muted)">
        <div class="flex items-center gap-8"><div class="diff-dot easy"></div>Easy</div>
        <div class="flex items-center gap-8"><div class="diff-dot medium"></div>Medium</div>
        <div class="flex items-center gap-8"><div class="diff-dot hard"></div>Hard</div>
      </div>
    </div>

    <!-- INTEGRITY -->
    <div class="mb-32">
      <div class="section-title">Integrity Summary</div>
      <div class="viol-summary-grid">
        <div class="vs-card">
          <div class="vs-count ${(viols.tab_switch||0)>0?'hit':''}">${viols.tab_switch||0}</div>
          <div class="vs-label">Tab Switches</div>
        </div>
        <div class="vs-card">
          <div class="vs-count ${(viols.camera_exit||0)>0?'hit':''}">${viols.camera_exit||0}</div>
          <div class="vs-label">Camera Exits</div>
        </div>
        <div class="vs-card">
          <div class="vs-count ${(viols.window_move||0)>0?'hit':''}">${viols.window_move||0}</div>
          <div class="vs-label">Window Moves</div>
        </div>
      </div>
    </div>

    <!-- RECOMMENDATIONS -->
    <div class="mb-32">
      <div class="section-title">Recommendations</div>
      <div class="flex-col gap-8">
        ${reccos.map(r => `<div class="reco-item">→ ${r}</div>`).join("")}
      </div>
    </div>

    <!-- ANSWER REVIEW -->
    <div class="mb-32">
      <div class="section-title">Answer Review (${answers.length})</div>
      <div class="flex-col gap-8">
        ${answers.length ? answers.map((a,i) => `
          <div class="answer-item">
            <div class="ai-header">
              <div class="ai-question">
                <span class="font-mono text-muted" style="font-size:11px">Q${i+1}</span>
                <span class="diff-badge ${a.difficulty||'easy'}" style="margin-left:8px">
                  ${(a.difficulty||"easy").toUpperCase()}
                </span><br>
                ${a.question}
              </div>
              <div class="score-val ${scoreClass(a.score||0)}" style="font-size:28px;flex-shrink:0">
                ${a.score||0}
              </div>
            </div>
            ${a.answer && a.answer !== "[SKIPPED]"
              ? `<div class="ai-answer">${a.answer}</div>`
              : `<div class="ai-answer" style="color:var(--danger);font-style:italic">Skipped</div>`}
            ${a.feedback ? `<div class="ai-feedback">${a.feedback}</div>` : ""}
          </div>`).join("")
        : `<div class="text-muted" style="font-size:13px">No answers were recorded.</div>`}
      </div>
    </div>

    <!-- ACTIONS -->
    <div class="flex gap-12">
      <button class="btn btn-primary" style="flex:1"
              onclick="Session.clear(); window.location.href='/dashboard'">
        🔄 Start New Interview
      </button>
      <button class="btn btn-outline" style="flex:1" onclick="window.print()">
        🖨️ Print Report
      </button>
    </div>
  `;
}

function scoreClass(score) {
  if (score >= 75) return "great";
  if (score >= 50) return "ok";
  return "poor";
}

function renderError(msg) {
  document.getElementById("report-body").innerHTML = `
    <div class="loading-state">
      <div style="font-size:48px">⚠️</div>
      <div class="font-mono" style="color:var(--danger);font-size:13px;text-align:center">${msg}</div>
      <button class="btn btn-primary" onclick="window.location.href='/dashboard'">← Go Back</button>
    </div>`;
}

/* Auto-run on page load */
loadReport();
