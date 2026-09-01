let isGenerating = false;
let pollingInterval = null;
let pollStartTime = 0;

async function loadReport() {
  if (isGenerating) {
    console.log("[Report] Already generating report, skipping duplicate request.");
    return;
  }

  const urlParams = new URLSearchParams(window.location.search);
  const urlSessionId = urlParams.get("session_id");
  const sid = urlSessionId || Session.id;

  if (!sid) {
    renderError("No active session found. Please start a new interview.");
    return;
  }

  isGenerating = true;
  pollStartTime = Date.now();
  
  // Render animated progress indicator layout
  renderLoadingState("Preparing evaluation...");
  
  // Start polling status
  if (pollingInterval) clearInterval(pollingInterval);
  
  // First check immediately
  await pollStatus(sid);
  
  // If not completed yet, start periodic checks
  if (isGenerating) {
    pollingInterval = setInterval(() => pollStatus(sid), 1500);
  }
}

async function pollStatus(sid) {
  const elapsed = Date.now() - pollStartTime;
  
  // Rotate stages representation messages
  let statusText = "Preparing evaluation...";
  if (elapsed > 12000) {
    statusText = "Finalizing report...";
  } else if (elapsed > 8000) {
    statusText = "Calculating performance...";
  } else if (elapsed > 4000) {
    statusText = "Analyzing answers...";
  }
  
  renderLoadingState(statusText);

  // Enforce maximum 25-second timeout limit to avoid blocking indefinitely
  if (elapsed > 25000) {
    stopPolling();
    renderTimeoutError();
    return;
  }

  try {
    const response = await fetch(`/api/report/status/${sid}`, {
      method: "GET",
      headers: { "Content-Type": "application/json" }
    });

    if (!response.ok) {
      if (response.status === 404) {
        console.log("[Report] Status endpoint returned 404, triggering generate POST.");
        await fetch("/api/report/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ session_id: sid })
        });
        return;
      }
      throw new Error(`HTTP ${response.status} Error`);
    }

    const data = await response.json();
    if (data.status === "completed") {
      stopPolling();
      renderReportReadyMessage(() => {
        renderReport(data.report);
      });
    } else if (data.status === "failed") {
      stopPolling();
      renderError("Report generation failed: " + (data.message || "Unknown error"));
    }
  } catch (err) {
    console.error("[Report Status Check Error]", err);
  }
}

function stopPolling() {
  isGenerating = false;
  if (pollingInterval) {
    clearInterval(pollingInterval);
    pollingInterval = null;
  }
}

function renderLoadingState(msg) {
  const container = document.getElementById("report-body");
  if (!container) return;
  
  let spin = container.querySelector(".load-spin");
  let label = container.querySelector(".load-msg");
  
  if (spin && label) {
    label.textContent = msg;
  } else {
    container.innerHTML = `
      <div class="loading-state">
        <div class="load-spin"></div>
        <div class="load-msg">${msg}</div>
        <div class="progress-bar-container" style="width:260px;height:4px;background:var(--border);border-radius:2px;margin-top:16px;overflow:hidden">
          <div class="progress-bar-value" style="width:40%;height:100%;background:var(--accent2);animation:load-indet 1.8s infinite ease-in-out"></div>
        </div>
      </div>
    `;
  }
}

function renderReportReadyMessage(callback) {
  const container = document.getElementById("report-body");
  if (!container) return;
  
  container.innerHTML = `
    <div class="loading-state fade-up">
      <div style="font-size:48px;margin-bottom:16px;color:var(--success)">✓</div>
      <div class="load-msg" style="color:var(--success)">Report ready ✓</div>
      <div style="font-size:12px;color:var(--text-muted);margin-top:8px">Loading dashboard...</div>
    </div>
  `;
  setTimeout(callback, 800);
}

function renderTimeoutError() {
  document.getElementById("report-body").innerHTML = `
    <div class="loading-state">
      <div style="font-size:48px;margin-bottom:16px">⏳</div>
      <div class="font-mono" style="color:var(--warn);font-size:14px;text-align:center;margin-bottom:20px;max-width:400px;line-height:1.6">
        Unable to generate the report right now. Please retry.
      </div>
      <button class="btn btn-primary" onclick="loadReport()">
        🔄 Retry Report
      </button>
    </div>`;
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
  const eScore  = scores.emotion_score !== undefined ? scores.emotion_score : (scores.emotion_stability === "Excellent" ? 90 : scores.emotion_stability === "Good" ? 75 : scores.emotion_stability === "Moderate" ? 50 : 30);
  const eLabel  = scores.emotion_stability || "Good";
  const rScore  = scores.readiness_index || 0;

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
                <span class="score-num">${eScore}%</span>
                <span class="score-status ${scoreClass(eScore)}">${eLabel}</span>
              </div>
              <div class="progress-track">
                <div class="progress-bar-fill ${scoreClass(eScore)}" 
                     style="width:${eScore}%"></div>
              </div>
              <p class="metric-desc">Assesses body language, camera focus consistency, and facial expression poise.</p>
            </div>
          </div>
        </div>
      </div>

      <!-- SKILLS & CANDIDATE INTELLIGENCE MAP -->
      <div class="detail-card" style="margin-top: 10px">
        <h3 class="card-title">Skills & Candidate Intelligence Map</h3>
        
        <div style="display: flex; flex-direction: column; gap: 20px">
          <!-- Skills Table -->
          <div style="overflow-x: auto">
            <table style="width: 100%; border-collapse: collapse; text-align: left; font-size: 13px">
              <thead>
                <tr style="border-bottom: 2px solid var(--border); color: var(--text-muted)">
                  <th style="padding: 10px 8px">Skill</th>
                  <th style="padding: 10px 8px; text-align: center">Questions Asked</th>
                  <th style="padding: 10px 8px; text-align: center">Avg Score</th>
                  <th style="padding: 10px 8px; text-align: center">Knowledge Depth</th>
                  <th style="padding: 10px 8px; text-align: center">Consistency</th>
                  <th style="padding: 10px 8px; text-align: center">Evidence Confidence</th>
                </tr>
              </thead>
              <tbody>
                ${Object.entries((d.candidate_profile && d.candidate_profile.skills) || d.skill_scores || {}).map(([skillName, skObj]) => {
                  const hasFullProfile = typeof skObj === "object";
                  const count = hasFullProfile ? (skObj.evidence_count || 0) : "—";
                  const avg = hasFullProfile ? (skObj.score || 0) : skObj;
                  const depth = hasFullProfile ? (skObj.depth || "Basic") : "Basic";
                  const consistency = hasFullProfile ? (skObj.consistency || "High") : "—";
                  const confidenceVal = hasFullProfile ? (skObj.confidence || 0) : "—";
                  
                  const depthClass = depth === "Advanced" ? "danger" : depth === "Intermediate" ? "warn" : "success";
                  const consistencyClass = consistency === "High" ? "success" : consistency === "Low" ? "danger" : "warn";
                  const confidenceText = typeof confidenceVal === "number" ? `${confidenceVal}%` : "—";
                  const confidenceClass = typeof confidenceVal === "number" ? (confidenceVal >= 75 ? "success" : confidenceVal >= 45 ? "warn" : "danger") : "warn";
                  
                  return `
                    <tr style="border-bottom: 1px solid var(--border); background: var(--surface2)">
                      <td style="padding: 12px 8px; font-weight: 700; color: var(--accent2)">${skillName}</td>
                      <td style="padding: 12px 8px; text-align: center">${count}</td>
                      <td style="padding: 12px 8px; text-align: center; font-weight: 700; color: ${avg >= 75 ? 'var(--success)' : avg >= 50 ? 'var(--warn)' : 'var(--danger)'}">${avg}%</td>
                      <td style="padding: 12px 8px; text-align: center">
                        <span class="chip ${depthClass}" style="font-size: 9px; padding: 2px 8px">${depth.toUpperCase()}</span>
                      </td>
                      <td style="padding: 12px 8px; text-align: center">
                        <span class="chip ${consistencyClass}" style="font-size: 9px; padding: 2px 8px">${consistency.toUpperCase()}</span>
                      </td>
                      <td style="padding: 12px 8px; text-align: center">
                        <span class="chip ${confidenceClass}" style="font-size: 9px; padding: 2px 8px">${confidenceText}</span>
                      </td>
                    </tr>
                  `;
                }).join("")}
              </tbody>
            </table>
          </div>
          
          <!-- Strong / Weak Areas -->
          <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px">
            <div style="background: rgba(16, 245, 154, 0.04); border: 1px solid rgba(16, 245, 154, 0.2); padding: 16px">
              <div class="font-mono text-success" style="font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px">
                ✓ Strong Technical Areas
              </div>
              <div class="flex-col gap-6">
                ${(d.strong_areas || []).length 
                  ? (d.strong_areas || []).map(sa => `<div style="font-size: 13px; color: var(--text)">• ${sa}</div>`).join("")
                  : `<div style="font-size: 12px; color: var(--text-muted)">No technical strong areas identified yet.</div>`}
              </div>
            </div>
            
            <div style="background: rgba(255, 61, 90, 0.04); border: 1px solid rgba(255, 61, 90, 0.2); padding: 16px">
              <div class="font-mono text-danger" style="font-size: 11px; letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px">
                → Areas Requiring Attention
              </div>
              <div class="flex-col gap-6">
                ${(d.weak_areas || []).length 
                  ? (d.weak_areas || []).map(wa => `<div style="font-size: 13px; color: var(--text)">• ${wa}</div>`).join("")
                  : `<div style="font-size: 12px; color: var(--text-muted)">No weaknesses identified yet.</div>`}
              </div>
            </div>
          </div>
          
          <!-- Contradictions & Corrections -->
          ${(d.candidate_profile && ((d.candidate_profile.contradictions && d.candidate_profile.contradictions.length > 0) || (d.candidate_profile.self_corrections && d.candidate_profile.self_corrections.length > 0))) ? `
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 16px; border-top: 1px solid var(--border); padding-top: 16px">
              <div>
                <div class="font-mono" style="font-size: 10px; color: var(--warn); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px">
                  ⚠️ Logical Contradictions Detected
                </div>
                <div class="flex-col gap-8">
                  ${d.candidate_profile.contradictions.map(c => `
                    <div style="background: var(--surface2); border: 1px solid var(--border); padding: 10px; font-size: 12px; border-left: 2px solid var(--warn)">
                      <div style="font-weight: 700; color: var(--accent2); margin-bottom: 4px">${c.skill} Question</div>
                      <div style="color: var(--text-muted)">${c.explanation}</div>
                    </div>
                  `).join("")}
                </div>
              </div>
              <div>
                <div class="font-mono" style="font-size: 10px; color: var(--success); letter-spacing: 0.1em; text-transform: uppercase; margin-bottom: 8px">
                  ✓ Self-Corrections Logged
                </div>
                <div class="flex-col gap-8">
                  ${d.candidate_profile.self_corrections.map(sc => `
                    <div style="background: var(--surface2); border: 1px solid var(--border); padding: 10px; font-size: 12px; border-left: 2px solid var(--success)">
                      <div style="font-weight: 700; color: var(--accent2); margin-bottom: 4px">${sc.skill} Question</div>
                      <div style="text-decoration: line-through; color: var(--danger)">${sc.original}</div>
                      <div style="color: var(--success); margin-top: 4px">Corrected: ${sc.corrected}</div>
                    </div>
                  `).join("")}
                </div>
              </div>
            </div>
          ` : ""}
        </div>
      </div>

      <!-- SECONDARY ROWS (BREAKDOWN & COMPLIANCE) -->
      <div class="dashboard-secondary" style="margin-top: 20px">
        
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
      <div class="answer-review-section" style="margin-top: 24px">
        <h2 class="section-heading">Detailed Question Review</h2>
        <div class="answers-list" style="display: flex; flex-direction: column; gap: 16px">
          ${answers.length ? answers.map((a,i) => `
            <div class="answer-review-card" style="background: var(--surface); border: 1px solid var(--border); padding: 20px">
              <div class="arc-header" style="display: flex; justify-content: space-between; align-items: center">
                <div class="arc-qinfo">
                  <span class="arc-num" style="font-weight: 700; color: var(--accent2)">Question ${i+1}</span>
                  <span class="arc-difficulty ${a.difficulty||'easy'}" style="margin-left: 8px">${(a.difficulty||"easy").toUpperCase()}</span>
                  <span class="chip accent" style="margin-left: 8px; scale: 0.85">${a.skill || 'General'}</span>
                </div>
                <div class="arc-score">
                  <span class="arc-score-label" style="font-size: 11px; color: var(--text-muted)">Score</span>
                  <span class="arc-score-num ${scoreClass(a.score||0)}" style="font-weight: 800; font-size: 18px; margin-left: 6px">${a.score||0}/100</span>
                </div>
              </div>
              <div class="arc-body" style="margin-top: 12px">
                <p class="arc-question-text" style="font-size: 14px; font-weight: 600; line-height: 1.5; color: #fff">${a.question}</p>
                <div class="arc-response" style="margin-top: 8px">
                  <span class="arc-label" style="font-size: 10px; font-family: var(--fm); text-transform: uppercase; color: var(--text-muted)">Your Response</span>
                  <div class="arc-response-content" style="font-size: 13px; color: var(--text-muted); border-left: 2px solid var(--border2); padding-left: 12px; margin-top: 4px; line-height: 1.6">
                    ${a.answer && a.answer !== "[SKIPPED]"
                      ? a.answer
                      : '<span class="skipped-label" style="color: var(--danger)">This question was skipped.</span>'}
                  </div>
                </div>
                ${a.feedback ? `
                  <div class="arc-feedback" style="margin-top: 10px; background: var(--surface2); padding: 10px; border: 1px solid var(--border)">
                    <span class="arc-label" style="font-size: 10px; font-family: var(--fm); text-transform: uppercase; color: var(--accent)">AI Assessment Feedback</span>
                    <p class="arc-feedback-text" style="font-size: 12px; line-height: 1.5; color: var(--text); margin-top: 4px">${a.feedback}</p>
                  </div>` : ""}
                  
                <!-- Multi-Dimensional Score Breakdown -->
                ${a.evaluation ? `
                  <div style="margin-top: 14px; border-top: 1px solid var(--border); padding-top: 12px">
                    <span style="font-size: 10px; font-family: var(--fm); text-transform: uppercase; color: var(--text-muted)">Dimensional Scores Breakdown</span>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-top: 6px">
                      ${Object.entries(a.evaluation).map(([dimKey, dimScore]) => {
                        const dimLabel = labelMap[dimKey] || dimKey;
                        const dimScoreStr = dimScore !== null ? `${dimScore}%` : "N/A";
                        const dimConf = (a.confidence && a.confidence[dimKey]) || "MEDIUM";
                        const confClass = getConfClass(dimConf);
                        return `
                          <div class="flex justify-between items-center" style="background: var(--surface2); padding: 6px 10px; font-size: 11px; border: 1px solid var(--border)">
                            <span style="color: var(--text-muted)">${dimLabel}</span>
                            <div class="flex items-center gap-8">
                              <span style="font-weight: 700; color: var(--text)">${dimScoreStr}</span>
                              <span class="chip ${confClass}" style="font-size: 7px; padding: 1px 4px; scale: 0.95">${dimConf}</span>
                            </div>
                          </div>
                        `;
                      }).join("")}
                    </div>
                    
                    <details style="margin-top: 10px; cursor: pointer">
                      <summary class="font-mono" style="font-size: 10px; color: var(--accent2); outline: none; user-select: none">
                        ▶ VIEW DIMENSIONAL REASONS & EVIDENCE
                      </summary>
                      <div style="margin-top: 8px; padding: 10px; background: var(--surface2); border: 1px solid var(--border); font-size: 11px">
                        ${Object.entries(a.evaluation).map(([dimKey, dimScore]) => {
                          const dimLabel = labelMap[dimKey] || dimKey;
                          const dimScoreStr = dimScore !== null ? `${dimScore}%` : "N/A";
                          const dimReason = (a.reasons && a.reasons[dimKey]) || "No detail provided.";
                          const dimConf = (a.confidence && a.confidence[dimKey]) || "MEDIUM";
                          const confClass = getConfClass(dimConf);
                          return `
                            <div style="margin-bottom: 8px">
                              <div style="font-weight: 700; color: var(--accent2); display:flex; justify-content:space-between">
                                <span>${dimLabel} (${dimScoreStr})</span>
                                <span class="chip ${confClass}" style="scale: 0.85">${dimConf} Confidence</span>
                              </div>
                              <div style="color: var(--text); margin-top: 2px">${dimReason}</div>
                            </div>
                          `;
                        }).join("")}
                        ${a.evidence && a.evidence.length ? `
                          <div style="margin-top: 8px; border-top: 1px solid var(--border); padding-top: 6px">
                            <span style="font-family: var(--fm); font-size: 9px; text-transform: uppercase; color: var(--text-muted)">CITED EVIDENCE FROM TRANSCRIPT:</span>
                            <ul style="margin-top: 2px; padding-left: 14px">
                              ${a.evidence.map(evStr => `<li style="list-style-type: circle; color: var(--text-muted); margin-bottom: 2px">"${evStr}"</li>`).join("")}
                            </ul>
                          </div>
                        ` : ""}
                      </div>
                    </details>
                  </div>
                ` : ""}
              </div>
            </div>`).join("") : '<div class="empty-state">No question attempts recorded during this session.</div>' }
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
