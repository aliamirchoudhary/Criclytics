/**
 * ml-widgets.js
 * ==============
 * Reusable ML prediction widgets for displaying probability insights
 * Used on: player-profile, venue-profile, match-detail, etc.
 */

// ── Load predictions for a player ────────────────────────────────────────────
async function loadPlayerProbabilities(playerName, format = 'ODI') {
  try {
    const resp = await fetch(`/api/predict/player/${encodeURIComponent(playerName)}/all?format=${encodeURIComponent(format)}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.error('Error loading player probabilities:', e);
    return null;
  }
}

// ── Load team match prediction ───────────────────────────────────────────────
async function loadTeamMatchPrediction(teamA, teamB, format = 'ODI', venue = null) {
  try {
    const resp = await fetch('/api/predict/team_match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        team_a: teamA,
        team_b: teamB,
        format: format,
        venue: venue
      })
    });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.error('Error loading team prediction:', e);
    return null;
  }
}

// ── Load venue performance bias ──────────────────────────────────────────────
async function loadVenuePerformanceBias(venueName, team = null, format = 'ODI') {
  try {
    const params = new URLSearchParams({ format });
    if (team) params.append('team', team);
    const resp = await fetch(`/api/predict/venue/${encodeURIComponent(venueName)}?${params}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.error('Error loading venue bias:', e);
    return null;
  }
}

// ── Load prediction leaderboard ──────────────────────────────────────────────
async function loadPredictionLeaderboard(metric = '50', format = 'ODI', limit = 10) {
  try {
    const resp = await fetch(`/api/predict/leaderboard?metric=${encodeURIComponent(metric)}&format=${encodeURIComponent(format)}&limit=${limit}`);
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (e) {
    console.error('Error loading leaderboard:', e);
    return null;
  }
}

// ── Render probability insight card ──────────────────────────────────────────
function renderProbabilityCard(prediction, metric) {
  const prob = prediction.probability || 0;
  const conf = prediction.confidence || 0;
  const form = prediction.recent_form || 'unknown';
  const icon = getMetricIcon(metric);
  const label = getMetricLabel(metric);
  
  // Color coding based on probability
  let probColor = 'var(--text-muted)';
  if (prob > 0.7) probColor = 'var(--success)';
  else if (prob > 0.5) probColor = 'var(--accent)';
  else if (prob > 0.3) probColor = 'var(--warning)';
  else probColor = 'var(--danger)';
  
  // Confidence indicator
  const confBars = Math.round(conf * 5);
  const confIndicator = Array(confBars).fill('█').join('') + Array(5 - confBars).fill('░').join('');
  
  return `
    <div class="ml-insight-card anim-up">
      <div class="ml-icon-box">${icon}</div>
      <div class="ml-body">
        <div class="ml-title">${label}</div>
        <div class="ml-desc">
          Recent form: <strong>${form}</strong>
          <br>Confidence: <span style="font-family:monospace;font-size:0.85rem;">${confIndicator}</span> ${Math.round(conf * 100)}%
        </div>
      </div>
      <div class="ml-prob" style="color:${probColor};">${(prob * 100).toFixed(0)}%</div>
    </div>
  `;
}

// ── Render all player predictions for a tab ──────────────────────────────────
async function renderPlayerPredictionsTab(playerName, format = 'ODI', containerId = 'panel-ml') {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Show loading state
  container.innerHTML = `
    <div class="disclaimer-banner mb-2">
      <span class="icon">⏳</span>
      Loading probability insights...
    </div>
  `;
  
  // Load predictions
  const data = await loadPlayerProbabilities(playerName, format);
  
  if (!data || data.error) {
    container.innerHTML = `
      <div class="disclaimer-banner mb-2">
        <span class="icon">ℹ</span>
        Probability insights not available for this player or format.
      </div>
    `;
    return;
  }
  
  if (!data.predictions) {
    container.innerHTML = `
      <div class="disclaimer-banner mb-2">
        <span class="icon">ℹ</span>
        No prediction data available.
      </div>
    `;
    return;
  }
  
  // Build HTML from predictions
  const metricsKeys = Object.keys(data.predictions);
  if (metricsKeys.length === 0) {
    container.innerHTML = `
      <div class="disclaimer-banner mb-2">
        <span class="icon">ℹ</span>
        No metrics available for this player.
      </div>
    `;
    return;
  }
  
  let html = `
    <div class="disclaimer-banner mb-2">
      <span class="icon">💡</span>
      Probability predictions based on recent performance data (${format} format).
    </div>
  `;
  
  for (const metric of metricsKeys) {
    const pred = data.predictions[metric];
    if (pred && !pred.error) {
      html += renderProbabilityCard(pred, metric);
    }
  }
  
  container.innerHTML = html;
}

// ── Render player probability tab ────────────────────────────────────────────
async function renderPlayerProbabilityTab(playerName, format = 'ODI', containerId = 'panel-probability') {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Show loading state
  container.innerHTML = `
    <div class="disclaimer-banner mb-2">
      <span class="icon">⏳</span>
      Loading probability insights...
    </div>
  `;
  
  // Load predictions
  const data = await loadPlayerProbabilities(playerName, format);
  
  if (!data || data.error) {
    container.innerHTML = `
      <div class="disclaimer-banner mb-2">
        <span class="icon">ℹ</span>
        Probability insights not available for this player or format.
      </div>
    `;
    return;
  }
  
  if (!data.predictions) {
    container.innerHTML = `
      <div class="disclaimer-banner mb-2">
        <span class="icon">ℹ</span>
        No prediction data available.
      </div>
    `;
    return;
  }
  
  // Build HTML from predictions
  const metricsKeys = Object.keys(data.predictions);
  if (metricsKeys.length === 0) {
    container.innerHTML = `
      <div class="disclaimer-banner mb-2">
        <span class="icon">ℹ</span>
        No metrics available for this player.
      </div>
    `;
    return;
  }
  
  let html = `
    <div class="disclaimer-banner mb-2">
      <span class="icon">💡</span>
      Probability predictions based on recent performance data (${format} format).
    </div>
  `;
  
  // Group predictions by category
  const milestonePreds = metricsKeys.filter(k => k.includes('score') || k.includes('milestone'));
  const venuePreds = metricsKeys.filter(k => k.includes('venue'));
  const opponentPreds = metricsKeys.filter(k => k.includes('opponent') || k.includes('vs'));
  
  // Milestone probabilities
  if (milestonePreds.length > 0) {
    html += `
      <div class="prob-block">
        <div class="prob-header">
          <span class="prob-icon">🏏</span>
          <span class="prob-label">Milestone Probabilities — ${format}</span>
        </div>
        <div class="prob-bar-wrap">
    `;
    
    for (const metric of milestonePreds.slice(0, 3)) {  // Limit to 3
      const pred = data.predictions[metric];
      if (pred && !pred.error) {
        const prob = Math.round((pred.probability || 0) * 100);
        const label = metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `
          <div class="prob-row">
            <div class="prob-row-header">
              <span class="prob-row-name">${label}</span>
              <span class="prob-row-val">${prob}%</span>
            </div>
            <div class="prob-bar">
              <div class="prob-bar-fill" style="width:${prob}%"></div>
            </div>
          </div>
        `;
      }
    }
    
    html += `
        </div>
        <div class="prob-disclaimer">Based on recent performance patterns.</div>
      </div>
    `;
  }
  
  // Venue probabilities
  if (venuePreds.length > 0) {
    html += `
      <div class="prob-block">
        <div class="prob-header">
          <span class="prob-icon">📍</span>
          <span class="prob-label">Venue Performance</span>
        </div>
        <div class="prob-bar-wrap">
    `;
    
    for (const metric of venuePreds.slice(0, 3)) {
      const pred = data.predictions[metric];
      if (pred && !pred.error) {
        const prob = Math.round((pred.probability || 0) * 100);
        const label = metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `
          <div class="prob-row">
            <div class="prob-row-header">
              <span class="prob-row-name">${label}</span>
              <span class="prob-row-val">${prob}%</span>
            </div>
            <div class="prob-bar">
              <div class="prob-bar-fill" style="width:${prob}%"></div>
            </div>
          </div>
        `;
      }
    }
    
    html += `
        </div>
        <div class="prob-disclaimer">Venue-specific performance analysis.</div>
      </div>
    `;
  }
  
  // Opponent probabilities
  if (opponentPreds.length > 0) {
    html += `
      <div class="prob-block">
        <div class="prob-header">
          <span class="prob-icon">🎯</span>
          <span class="prob-label">Opponent Probabilities</span>
        </div>
        <div class="prob-bar-wrap">
    `;
    
    for (const metric of opponentPreds.slice(0, 3)) {
      const pred = data.predictions[metric];
      if (pred && !pred.error) {
        const prob = Math.round((pred.probability || 0) * 100);
        const label = metric.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
        html += `
          <div class="prob-row">
            <div class="prob-row-header">
              <span class="prob-row-name">${label}</span>
              <span class="prob-row-val">${prob}%</span>
            </div>
            <div class="prob-bar">
              <div class="prob-bar-fill" style="width:${prob}%"></div>
            </div>
          </div>
        `;
      }
    }
    
    html += `
        </div>
        <div class="prob-disclaimer">Opponent-specific performance analysis.</div>
      </div>
    `;
  }
  
  container.innerHTML = html;
}

// ── Render team match prediction ─────────────────────────────────────────────
async function renderTeamMatchPrediction(teamA, teamB, format = 'ODI', venue = null, containerId) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  // Show loading state
  container.innerHTML = '<p style="text-align:center;color:var(--text-muted);">Loading match prediction...</p>';
  
  const data = await loadTeamMatchPrediction(teamA, teamB, format, venue);
  
  if (!data || data.error) {
    container.innerHTML = '<p style="text-align:center;color:var(--danger);">Prediction unavailable</p>';
    return;
  }
  
  const teamAData = data.team_a || {};
  const teamBData = data.team_b || {};
  const probA = (teamAData.win_probability || 0.5) * 100;
  const probB = (teamBData.win_probability || 0.5) * 100;
  
  const prediction = data.prediction || 'Too Close';
  const confidence = data.prediction_confidence || 0;
  
  html = `
    <div class="prediction-container">
      <div class="prediction-header">
        <div class="pred-title">Match Outcome Prediction</div>
        <div class="pred-meta">Prediction: <strong>${prediction}</strong> | Confidence: ${Math.round(confidence * 100)}%</div>
      </div>
      
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;margin-top:1.5rem;">
        <!-- Team A -->
        <div style="background:var(--surface-2);border-radius:var(--radius-md);padding:1.2rem;border-left:4px solid var(--accent);">
          <div style="font-weight:600;font-size:1rem;margin-bottom:0.5rem;">${teamAData.name || teamA}</div>
          <div style="font-size:2.2rem;font-weight:700;color:var(--accent);">${probA.toFixed(1)}%</div>
          <div style="font-size:0.85rem;color:var(--text-muted);margin-top:0.5rem;">Form: ${teamAData.recent_form || 'unknown'}</div>
        </div>
        
        <!-- Team B -->
        <div style="background:var(--surface-2);border-radius:var(--radius-md);padding:1.2rem;border-left:4px solid var(--warning);">
          <div style="font-weight:600;font-size:1rem;margin-bottom:0.5rem;">${teamBData.name || teamB}</div>
          <div style="font-size:2.2rem;font-weight:700;color:var(--warning);">${probB.toFixed(1)}%</div>
          <div style="font-size:0.85rem;color:var(--text-muted);margin-top:0.5rem;">Form: ${teamBData.recent_form || 'unknown'}</div>
        </div>
      </div>
      
      ${venue ? `<div style="font-size:0.85rem;color:var(--text-muted);margin-top:1rem;text-align:center;">Venue: ${venue}</div>` : ''}
    </div>
  `;
  
  container.innerHTML = html;
}

// ── Metric utilities ─────────────────────────────────────────────────────────
function getMetricIcon(metric) {
  switch (metric) {
    case '50': return '📊';
    case '100': return '🏆';
    case 'wicket_maiden': return '🎳';
    case 'strike_rate>140': return '⚡';
    case 'avg>50': return '⭐';
    default: return '📈';
  }
}

function getMetricLabel(metric) {
  switch (metric) {
    case '50': return 'Scoring 50+ Runs';
    case '100': return 'Scoring 100+ (Century)';
    case 'wicket_maiden': return 'Taking 1+ Wickets';
    case 'strike_rate>140': return 'Strike Rate > 140';
    case 'avg>50': return 'Maintaining Avg > 50';
    default: return 'Performance Metric';
  }
}

// ── Helper: Format comparison percentage bar ─────────────────────────────────
function renderPercentageBar(percent, width = '100%') {
  const clamped = Math.max(0, Math.min(percent, 100));
  let color = 'var(--danger)';
  if (clamped > 70) color = 'var(--success)';
  else if (clamped > 50) color = 'var(--accent)';
  else if (clamped > 30) color = 'var(--warning)';
  
  return `
    <div style="width:${width};height:6px;background:var(--border);border-radius:2px;overflow:hidden;">
      <div style="height:100%;width:${clamped}%;background:${color};transition:width 0.3s ease;"></div>
    </div>
  `;
}
