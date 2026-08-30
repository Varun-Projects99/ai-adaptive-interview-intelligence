/* ─────────────────────────────────────────────
   report.js — Fetch /api/report/generate and render full dashboard
   ───────────────────────────────────────────── */

async function loadReport() {
  const urlParams = new URLSearchParams(window.location.search);
  const urlSessionId = urlParams.get("session_id");
  const sid = urlSessionId || Session.id;

  if (!sid) {
    renderError("No active session found. Please start a new interview.");
    return;
  }

  try {
    const endpoint = urlSessionId ? `/api/report/view/${urlSessionId}` : "/api/report/generate";
    const data = await apiPost(endpoint, { session_id: sid });
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
    <div class="report-container fade-up">
      
      ${d.terminated ? `
      <div style="background:rgba(255,61,90,.08);border:1px solid rgba(255,61,90,.4);
        padding:14px 20px;color:var(--danger);font-size:14px;
        display:flex;align-items:center;gap:12px;margin-bottom:12px;border-radius:8px">
        <span style="font-size:20px">🚫</span>
        <span>This interview was <strong>terminated</strong> due to repeated integrity violations.</span>
      </div>` : ""}

      <!-- HERO HEADER -->
      <div class="report-header">
        <div class="header-left">
          <span class="report-badge">Performance Evaluation Report</span>
          <h1 class="report-title">Your Interview Results</h1>
          <p class="report-meta">Session: <span class="mono">${d.session_id}</span> | Evaluated: ${d.date || 'Just now'}</p>
        </div>
        <div class="header-right">
          <div class="summary-stat">
            <span class="stat-num">${summary.total_questions||0}</span>
            <span class="stat-label">Questions</span>
          </div>
          <div class="summary-stat" style="margin-left:24px">
            <span class="stat-num">${(summary.skills_covered||[]).length}</span>
            <span class="stat-label">Skills Tested</span>
          </div>
          <div style="margin-left:24px">
            <span class="status-badge ${d.terminated ? 'status-terminated' : 'status-completed'}">
              ${d.terminated ? 'TERMINATED' : 'COMPLETED'}
            </span>
          </div>
        </div>
      </div>

      <!-- PRIMARY DASHBOARD PANEL -->
      <div class="dashboard-primary">
        <!-- Readiness Ring Card -->
        <div class="readiness-card">
          <h3 class="card-title">Overall Readiness</h3>
          <div class="radial-progress-wrapper">
            <svg class="radial-progress" viewBox="0 0 100 100">
              <circle class="bg" cx="50" cy="50" r="40"></circle>
              <circle class="fg ${scoreClass(rScore)}" cx="50" cy="50" r="40" 
                      style="stroke-dasharray: 251.2; stroke-dashoffset: ${251.2 - (251.2 * rScore / 100)}"></circle>
            </svg>
            <div class="radial-center">
              <span class="percentage">${rScore}%</span>
              <span class="rating-label">${scores.readiness_label || "Early Stage"}</span>
            </div>
          </div>
          <p class="card-desc">An aggregate score estimating your overall readiness based on technical correctness, pacing, and focus.</p>
        </div>

        <!-- Scores Details Grid -->
        <div class="metrics-grid">
          <div class="metric-item tech">
            <div class="metric-header">
              <span class="metric-icon">💻</span>
              <span class="metric-title">Technical Competency</span>
            </div>
            <div class="metric-body">
              <div class="score-display">
                <span class="score-num">${tScore}%</span>
                <span class="score-status ${scoreClass(tScore)}">
                  ${tScore >= 75 ? 'Strong' : tScore >= 50 ? 'Developing' : 'Needs Practice'}
                </span>
              </div>
              <div class="progress-track">
                <div class="progress-bar-fill ${scoreClass(tScore)}" style="width:${tScore}%"></div>
              </div>
              <p class="metric-desc">Evaluates the depth, accuracy, correctness, and reasoning of your responses.</p>
            </div>
          </div>

          <div class="metric-item conf">
            <div class="metric-header">
              <span class="metric-icon">🎙️</span>
              <span class="metric-title">Voice Confidence & Pacing</span>
            </div>
            <div class="metric-body">
              <div class="score-display">
                <span class="score-num">${cScore}%</span>
                <span class="score-status ${scoreClass(cScore)}">
                  ${cScore >= 75 ? 'Confident' : cScore >= 55 ? 'Moderate' : 'Nervous'}
                </span>
              </div>
              <div class="progress-track">
                <div class="progress-bar-fill ${scoreClass(cScore)}" style="width:${cScore}%"></div>
              </div>
              <p class="metric-desc">Measures speaking rate (WPM), voice tone variation, and avoidance of filler words.</p>
            </div>
          </div>

          <div class="metric-item emot">
            <div class="metric-header">
              <span class="metric-icon">😊</span>
              <span class="metric-title">Emotion & Composure</span>
            </div>
            <div class="metric-body">
              <div class="score-display">
                <span class="score-num">${scores.emotion_stability || "—"}</span>
                <span class="score-status ${emotionClass(scores.emotion_stability)}">Webcam Analysis</span>
              </div>
              <div class="progress-track">
                <div class="progress-bar-fill ${emotionClass(scores.emotion_stability)}" 
                     style="width:${scores.emotion_stability === 'Excellent' ? 100 : scores.emotion_stability === 'Good' ? 75 : scores.emotion_stability === 'Moderate' ? 50 : 25}%"></div>
              </div>
              <p class="metric-desc">Assesses body language, camera focus consistency, and facial expression poise.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- SECONDARY ROWS (BREAKDOWN & COMPLIANCE) -->
      <div class="dashboard-secondary">
        
        <!-- Left Column: Composure & Progression -->
        <div class="sec-col-left">
          
          <!-- Composure Breakdown -->
          <div class="detail-card">
            <h3 class="card-title">Emotional Composure Breakdown</h3>
            <div class="emots-list">
              ${Object.entries(emots).length
                ? Object.entries(emots).map(([k,v]) => `
                    <div class="emot-row">
                      <span class="emot-label">${k}</span>
                      <div class="emot-bar-track">
                        <div class="emot-bar-fill ${k}" style="width:${v}%"></div>
                      </div>
                      <span class="emot-percentage">${v}%</span>
                    </div>`).join("")
                : `<div class="empty-state">No facial expressions data was recorded.</div>`}
            </div>
          </div>

          <!-- Difficulty Progression -->
          <div class="detail-card">
            <h3 class="card-title">Adaptive Difficulty Path</h3>
            <div class="progression-path">
              ${prog.length ? `
                <div class="path-timeline">
                  ${prog.map((d, idx) => `
                    <div class="path-node ${d}">
                      <span class="node-dot"></span>
                      <span class="node-label">Q${idx+1}</span>
                      <span class="node-tooltip">${d.toUpperCase()}</span>
                    </div>`).join("")}
                </div>
              ` : `<div class="empty-state">No difficulty tracking history.</div>`}
              <div class="path-legend">
                <span class="legend-item"><span class="legend-dot easy"></span> Easy</span>
                <span class="legend-item"><span class="legend-dot medium"></span> Medium</span>
                <span class="legend-item"><span class="legend-dot hard"></span> Hard</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Right Column: Integrity Compliance & Tips -->
        <div class="sec-col-right">
          
          <!-- Integrity Monitor -->
          <div class="detail-card">
            <h3 class="card-title">Integrity Summary</h3>
            <div class="integrity-grid">
              <div class="integrity-stat ${(viols.tab_switch||0)>0 ? 'viol-warning' : 'viol-ok'}">
                <span class="stat-count">${viols.tab_switch||0}</span>
                <span class="stat-desc">Tab Switches</span>
              </div>
              <div class="integrity-stat ${(viols.camera_exit||0)>0 ? 'viol-warning' : 'viol-ok'}">
                <span class="stat-count">${viols.camera_exit||0}</span>
                <span class="stat-desc">Camera Exits</span>
              </div>
              <div class="integrity-stat ${(viols.window_move||0)>0 ? 'viol-warning' : 'viol-ok'}">
                <span class="stat-count">${viols.window_move||0}</span>
                <span class="stat-desc">Window Moves</span>
              </div>
            </div>
            <div class="integrity-status-banner ${d.terminated ? 'banner-red' : (viols.tab_switch || viols.camera_exit || viols.window_move) ? 'banner-yellow' : 'banner-green'}">
              ${d.terminated
                ? '⚠️ Session auto-terminated due to multiple strikes.'
                : (viols.tab_switch || viols.camera_exit || viols.window_move)
                  ? '⚠️ Disruptions or tab focus switches detected during evaluation.'
                  : '✓ Full Compliance: Excellent focus and webcam integrity maintained.'}
            </div>
          </div>

          <!-- Recommendations -->
          <div class="detail-card">
            <h3 class="card-title">Key Action Recommendations</h3>
            <div class="reccos-list">
              ${reccos.length ? reccos.map(r => `
                <div class="recco-item-card">
                  <span class="recco-bullet">💡</span>
                  <span class="recco-text">${r}</span>
                </div>`).join("")
              : `<div class="recco-item-card"><span class="recco-text">Continue standard mock interview practices.</span></div>`}
            </div>
          </div>
        </div>
      </div>

      <!-- DETAILED ANSWER REVIEW -->
      <div class="answer-review-section">
        <h2 class="section-heading">Detailed Question Review</h2>
        <div class="answers-list">
          ${answers.length ? answers.map((a,i) => `
            <div class="answer-review-card">
              <div class="arc-header">
                <div class="arc-qinfo">
                  <span class="arc-num">Question ${i+1}</span>
                  <span class="arc-difficulty ${a.difficulty||'easy'}">${(a.difficulty||"easy").toUpperCase()}</span>
                </div>
                <div class="arc-score">
                  <span class="arc-score-label">Score</span>
                  <span class="arc-score-num ${scoreClass(a.score||0)}">${a.score||0}/100</span>
                </div>
              </div>
              <div class="arc-body">
                <p class="arc-question-text">${a.question}</p>
                <div class="arc-response">
                  <span class="arc-label">Your Response</span>
                  <div class="arc-response-content">
                    ${a.answer && a.answer !== "[SKIPPED]"
                      ? a.answer
                      : '<span class="skipped-label">This question was skipped.</span>'}
                  </div>
                </div>
                ${a.feedback ? `
                  <div class="arc-feedback">
                    <span class="arc-label">AI Assessment Feedback</span>
                    <p class="arc-feedback-text">${a.feedback}</p>
                  </div>` : ""}
              </div>
            </div>`).join("")
          : `<div class="empty-state">No question attempts recorded during this session.</div>`}
        </div>
      </div>

      <!-- ACTION BUTTONS -->
      <div class="report-actions">
        <button class="btn btn-outline" onclick="window.print()">
          🖨️ Print Report
        </button>
        <button class="btn btn-primary" onclick="Session.clear(); window.location.href='/dashboard'">
          🔄 Start New Interview
        </button>
      </div>

    </div>
  `;
}

function scoreClass(score) {
  if (score >= 75) return "great";
  if (score >= 50) return "ok";
  return "poor";
}

function emotionClass(stability) {
  if (stability === "Excellent" || stability === "Good") return "great";
  if (stability === "Moderate") return "ok";
  return "poor";
}

function renderError(msg) {
  document.getElementById("report-body").innerHTML = `
    <div class="loading-state">
      <div style="font-size:48px">⚠️</div>
      <div class="font-mono" style="color:var(--danger);font-size:13px;text-align:center;margin-bottom:16px">${msg}</div>
      <button class="btn btn-primary" onclick="window.location.href='/dashboard'">← Go Back</button>
    </div>`;
}

/* Auto-run on page load */
loadReport();
