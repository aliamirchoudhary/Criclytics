/**
 * ml-wiring-addon.js
 * ==================
 * Shared ML endpoint wiring functions for all pages
 * Provides fallback rendering when endpoints are unavailable
 */

// ── Render venue ML predictions ──────────────────────────────────────────────
async function renderVeneMLPredictions(venueName, format = 'ODI', containerId = 'panel-probability-insights') {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = '<div class="disclaimer-banner mb-2"><span class="icon">⏳</span> Loading venue insights...</div>';
  
  try {
    const data = await loadVenuePerformanceBias(venueName, null, format);
    
    let html = '<div class="disclaimer-banner mb-2"><span class="icon">💡</span> Venue-specific performance insights based on historical data.</div>';
    
    if (data && !data.error) {
      const bias_score = data.bias_score || 0;
      const chasing_bias = data.chasing_bias || 'Neutral';
      const chasing_avg = data.chasing_average || 0;
      const defending_avg = data.defending_average || 0;
      
      const basPct = Math.round(chasing_bias === 'Chasing' ? 60 : chasing_bias === 'Defending' ? 40 : 50);
      
      html += `
        <div class="prob-2col">
          <div class="prob-block">
            <div class="prob-header"><span class="prob-icon">🏃</span><span class="prob-label">Chasing Advantage</span></div>
            <div class="prob-row">
              <div class="prob-row-header"><span class="prob-row-name">Avg Chase Score</span><span class="prob-row-val">${chasing_avg || '—'}</span></div>
              <div class="prob-bar">${renderPercentageBar(basPct)}</div>
            </div>
          </div>
          <div class="prob-block">
            <div class="prob-header"><span class="prob-icon">🎯</span><span class="prob-label">Defending Advantage</span></div>
            <div class="prob-row">
              <div class="prob-row-header"><span class="prob-row-name">Avg Defend Score</span><span class="prob-row-val">${defending_avg || '—'}</span></div>
              <div class="prob-bar">${renderPercentageBar(100 - basPct)}</div>
            </div>
          </div>
        </div>
        <p style="font-size:0.75rem;color:var(--text-muted);margin-top:0.8rem;"><strong>Bias:</strong> ${chasing_bias}</p>
      `;
    } else {
      html += '<div class="disclaimer-banner" style="background:rgba(255,82,82,0.05);border-color:rgba(255,82,82,.2);"><span class="icon">ℹ</span> Predictions unavailable for this venue.</div>';
    }
    
    container.innerHTML = html;
  } catch (e) {
    console.warn('Venue predictions unavailable:', e && e.message ? e.message : e);
    container.innerHTML = '<div class="disclaimer-banner"><span class="icon">ℹ</span> Unable to load venue insights at this moment.</div>';
  }
}

// ── Render match prediction context ──────────────────────────────────────────
async function renderMatchContextInsight(teamA, teamB, venue = null, containerId = 'panel-context') {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = '<div class="disclaimer-banner mb-2"><span class="icon">⏳</span> Loading match context...</div>';
  
  try {
    const prediction = await loadTeamMatchPrediction(teamA, teamB, 'ODI', venue);
    
    let html = '<div class="disclaimer-banner mb-2"><span class="icon">⚡</span> Match prediction based on team form and head-to-head data.</div>';
    
    if (prediction && !prediction.error) {
      const probA = Math.round((prediction.team_a?.win_probability || 0.5) * 100);
      const probB = Math.round((prediction.team_b?.win_probability || 0.5) * 100);
      const pred = prediction.prediction || 'Too Close';
      const conf = Math.round((prediction.prediction_confidence || 0) * 100);
      
      html += `
        <div style="background:var(--surface-1);border-radius:var(--radius-lg);padding:1.2rem;margin-top:0.8rem;">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:0.8rem;">
            <div style="background:var(--surface-2);padding:0.8rem;border-radius:var(--radius-md);border-left:4px solid var(--accent);">
              <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.3rem;">🏏 ${teamA}</div>
              <div style="font-size:1.8rem;font-weight:700;color:var(--accent);">${probA}%</div>
            </div>
            <div style="background:var(--surface-2);padding:0.8rem;border-radius:var(--radius-md);border-left:4px solid var(--warning);">
              <div style="font-size:0.75rem;color:var(--text-muted);margin-bottom:0.3rem;">🏏 ${teamB}</div>
              <div style="font-size:1.8rem;font-weight:700;color:var(--warning);">${probB}%</div>
            </div>
          </div>
          <div style="background:var(--surface-2);padding:0.6rem;border-radius:var(--radius-md);text-align:center;font-size:0.8rem;">
            <strong>Prediction:</strong> ${pred} | <strong>Confidence:</strong> ${conf}%
          </div>
        </div>
      `;
    } else {
      html += '<div class="disclaimer-banner" style="background:rgba(255,82,82,0.05);border-color:rgba(255,82,82,.2);"><span class="icon">ℹ</span> Match prediction unavailable.</div>';
    }
    
    container.innerHTML = html;
  } catch (e) {
    console.warn('Match context unavailable:', e && e.message ? e.message : e);
  }
}

// ── Render player leaderboard predictions ────────────────────────────────────
async function renderPredictionLeaderboardCards(metric = '50', format = 'ODI', limit = 10, containerId = 'panel-leaderboard') {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = '<div class="disclaimer-banner mb-2"><span class="icon">⏳</span> Loading top performers...</div>';
  
  try {
    const data = await loadPredictionLeaderboard(metric, format, limit);
    
    if (data && data.predictions && data.predictions.length > 0) {
      let html = '<div class="disclaimer-banner mb-2"><span class="icon">⭐</span> Top players predicted to achieve this metric.</div>';
      
      for (const pred of data.predictions.slice(0, limit)) {
        const prob = Math.round((pred.probability || 0) * 100);
        const player = pred.player || '—';
        
        html += `
          <div class="ml-card" style="margin-bottom:0.6rem;">
            <div class="ml-icon">📊</div>
            <div class="ml-body" style="flex:1;">
              <div class="ml-title" style="font-size:0.9rem;">${player}</div>
              <div class="ml-desc" style="font-size:0.75rem;color:var(--text-muted);">${pred.recent_form || 'Recent'} form</div>
            </div>
            <div class="ml-val" style="font-size:1.4rem;">${prob}%</div>
          </div>
        `;
      }
      
      container.innerHTML = html;
    } else {
      container.innerHTML = '<div class="disclaimer-banner"><span class="icon">ℹ</span> No prediction data available for this metric.</div>';
    }
  } catch (e) {
    console.warn('Leaderboard unavailable:', e && e.message ? e.message : e);
    container.innerHTML = '<div class="disclaimer-banner"><span class="icon">ℹ</span> Unable to load predictions.</div>';
  }
}
