/**
 * index-api.js
 * ============
 * Wires index.html (home page) to real API data.
 * Replaces ALL hardcoded sections: stat bar, live ticker, live matches,
 * quick insights, upcoming matches, trending players, team rankings, recent results.
 */

function fl(country, size) {
  size = size || 20;
  var code = COUNTRY_ISO[country] || '';
  if (!code) return '';
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:' + Math.round(size*0.25) + 'px;" '
    + 'onerror="this.style.display=\'none\'">';
}

function flCircle(country, size) {
  size = size || 36;
  var code = COUNTRY_ISO[country] || '';
  if (!code) return '<div style="width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:var(--surface-2);display:flex;align-items:center;justify-content:center;font-size:' + Math.round(size*0.4) + 'px;color:var(--accent);">' + (country||'?')[0] + '</div>';
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;flex-shrink:0;" '
    + 'onerror="this.style.display=\'none\'">';
}

// ─── Stat Bar ──────────────────────────────────────────────────────────────────
async function loadStatBar() {
  var data = await apiFetch('/api/players?limit=1');
  var venueData = await apiFetch('/api/venues');
  var teamData  = await apiFetch('/api/teams');

  var totalPlayers = data && data.total ? data.total : null;
  var totalVenues  = venueData ? Object.keys(venueData).length : null;
  var totalTeams   = teamData  ? Object.keys(teamData).length  : null;

  var statItems = document.querySelectorAll('.stat-item');
  var statValues = document.querySelectorAll('.stat-value');
  // stat items: Matches, Players, Venues, Teams, Formats
  if (statValues[1] && totalPlayers) statValues[1].textContent = totalPlayers.toLocaleString() + '+';
  if (statValues[2] && totalVenues)  statValues[2].textContent = totalVenues + '+';
  if (statValues[3] && totalTeams)   statValues[3].textContent = totalTeams;
}

// ─── Live Ticker ──────────────────────────────────────────────────────────────
async function loadLiveTicker() {
  var inner = document.querySelector('.live-ticker-inner');
  if (!inner) return;

  // Try live matches first
  var liveData = await apiFetch('/api/live');
  var tickerMatches = (liveData && liveData.data) ? liveData.data : [];

  // Fall back to upcoming from /api/matches when no live
  if (!tickerMatches.length) {
    var allData = await apiFetch('/api/matches');
    var allMatches = (allData && allData.data) ? allData.data : [];
    tickerMatches = allMatches.filter(function(m) { return !m.matchEnded; }).slice(0, 5);
  }

  if (!tickerMatches.length) {
    // No data at all — hide ticker
    var ticker = inner.closest('.live-ticker');
    if (ticker) ticker.style.display = 'none';
    return;
  }

  var isAnyLive = tickerMatches.some(function(m) { return m.matchStarted && !m.matchEnded; });
  var labelType = isAnyLive ? 'Live' : 'Upcoming';

  var items = tickerMatches.map(function(m) {
    var t1 = m.t1 || m.team1 || '';
    var t2 = m.t2 || m.team2 || '';
    var score = m.t1s || '';
    var liveMarker = (m.matchStarted && !m.matchEnded) ? '<span style="color:var(--green-live);margin-right:3px;">●</span>' : '';
    return '<span class="ticker-item">' + liveMarker + '<strong>' + esc(t1) + '</strong> ' + esc(score ? score + ' · ' : '') + 'vs <strong>' + esc(t2) + '</strong> <span class="ticker-sep">|</span></span>';
  });

  inner.innerHTML = '<span class="ticker-label">' + labelType + '</span>' + items.join('')
    + '<span class="ticker-label">' + labelType + '</span>' + items.join('');
  // Ensure ticker is visible
  var ticker = inner.closest('.live-ticker');
  if (ticker) ticker.style.display = '';
}

// ─── Live Matches section — shows live or upcoming matches ────────────────────
async function loadLiveMatches() {
  var liveData = await apiFetch('/api/live');
  var matches = (liveData && liveData.data) ? liveData.data : [];
  var isLive = matches.length > 0;

  // Fall back to upcoming matches when no live
  if (!matches.length) {
    var allData = await apiFetch('/api/matches');
    var allMatches = (allData && allData.data) ? allData.data : [];
    matches = allMatches.filter(function(m) { return !m.matchEnded; }).slice(0, 3);
  }

  // Update section header
  var sectionTitle = document.querySelector('#right-now-section .section-title, .section-title');
  // Try to find the "Live Matches" title and update it
  document.querySelectorAll('.section-title').forEach(function(el) {
    if (el.textContent.includes('Live Matches') && !isLive && matches.length) {
      el.innerHTML = '<span class="icon">📅</span> Upcoming Matches';
    }
  });

  // Featured match card
  var featured = document.querySelector('.featured-match');
  if (featured) {
    if (!matches.length) {
      featured.innerHTML = '<div style="text-align:center;padding:2rem;color:var(--text-muted);">'
        + '<i class="fa fa-calendar" style="font-size:2rem;display:block;margin-bottom:1rem;opacity:0.3;"></i>'
        + '<div style="font-size:.9rem;">No matches scheduled right now.</div>'
        + '<a href="matches.html" class="btn btn-ghost" style="margin-top:1rem;font-size:.8rem;">Browse all matches</a>'
      + '</div>';
    } else {
      var m = matches[0];
      var t1 = m.t1 || m.team1 || ''; var t2 = m.t2 || m.team2 || '';
      var s1 = isLive ? (m.t1s || '—') : (m.date || 'Upcoming'); var s2 = isLive ? (m.t2s || '—') : '';
      var iso1 = COUNTRY_ISO[t1] || ''; var iso2 = COUNTRY_ISO[t2] || '';
      var f1Html = iso1 ? '<img src="' + FLAG_CDN + iso1 + '.svg" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' : '';
      var f2Html = iso2 ? '<img src="' + FLAG_CDN + iso2 + '.svg" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' : '';
      var badgeHtml = isLive
        ? '<span class="status-badge status-live">Live</span>'
        : '<span class="status-badge" style="background:rgba(94,184,255,0.1);color:var(--accent);border:1px solid rgba(94,184,255,0.2);">Upcoming</span>';
      var centerText = isLive ? '● In Progress' : (m.date || 'Scheduled');
      featured.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem;">'
        + badgeHtml
        + '<span class="match-format-badge">' + esc(m.matchType||'') + '</span>'
        + '<span style="font-size:0.75rem;color:var(--text-muted)">' + esc(m.status || m.series || '') + '</span>'
      + '</div>'
      + '<div class="featured-match-body">'
        + '<div class="featured-team"><div class="featured-flag">' + f1Html + '</div><div>'
          + '<div class="featured-team-name">' + esc(t1) + '</div>'
          + '<div class="featured-team-score">' + esc(s1) + '</div></div></div>'
        + '<div class="featured-center"><div class="featured-vs">vs</div><div class="featured-status-text">' + esc(centerText) + '</div></div>'
        + '<div class="featured-team right"><div class="featured-flag">' + f2Html + '</div><div style="text-align:right">'
          + '<div class="featured-team-name">' + esc(t2) + '</div>'
          + '<div class="featured-team-score">' + esc(s2) + '</div></div></div>'
      + '</div>'
      + '<div class="featured-footer"><div class="featured-venue"><i class="fa fa-location-dot"></i> ' + esc(m.venue||'—') + '</div>'
      + '<a href="match-detail.html?id=' + esc(m.id||'') + '" class="btn btn-secondary btn-sm">Details <i class="fa fa-arrow-right"></i></a></div>';
    }
  }

  // Two small live cards (grid-2)
  var smallGrid = document.querySelector('.featured-match + .grid-2, .live-small-grid');
  if (smallGrid) {
    if (matches.length < 2) {
      smallGrid.innerHTML = '';
    } else {
      smallGrid.innerHTML = matches.slice(1, 3).map(function(m) {
        var t1 = m.t1||m.team1||''; var t2 = m.t2||m.team2||'';
        var s1 = m.t1s||'—'; var s2 = m.t2s||'—';
        var iso1 = COUNTRY_ISO[t1]||''; var iso2 = COUNTRY_ISO[t2]||'';
        return '<a href="match-detail.html?id=' + esc(m.id||'') + '" class="card match-card anim-up">'
          + '<div class="match-card-header"><span class="status-badge status-live">Live</span><span class="match-format-badge">' + esc(m.matchType||'') + '</span></div>'
          + '<div class="match-teams">'
            + '<div class="match-team"><div class="team-flag">' + (iso1?'<img src="'+FLAG_CDN+iso1+'.svg" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">':'') + '</div><div class="team-name">' + esc(t1) + '</div><div class="team-score">' + esc(s1) + '</div></div>'
            + '<div class="match-vs">vs</div>'
            + '<div class="match-team"><div class="team-flag">' + (iso2?'<img src="'+FLAG_CDN+iso2+'.svg" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">':'') + '</div><div class="team-name">' + esc(t2) + '</div><div class="team-score">' + esc(s2) + '</div></div>'
          + '</div>'
          + '<div class="match-venue"><i class="fa fa-location-dot"></i> ' + esc(m.venue||'—') + '</div>'
        + '</a>';
      }).join('');
    }
  }
}

// ─── Quick Insights (from Cricsheet records) ──────────────────────────────────
async function loadQuickInsights() {
  var data = await apiFetch('/api/records');
  if (!data) return;
  var strip = document.querySelector('.insight-strip');
  if (!strip) return;

  var testTop  = data.most_runs   && data.most_runs.Test  && data.most_runs.Test[0];
  var odiTop   = data.most_runs   && data.most_runs.ODI   && data.most_runs.ODI[0];
  var t20Top   = data.most_wickets && data.most_wickets.T20I && data.most_wickets.T20I[0];
  var testWkt  = data.most_wickets && data.most_wickets.Test && data.most_wickets.Test[0];

  var insights = [];
  if (testTop) insights.push({
    icon: 'fa-cricket-bat-ball',
    title: esc(testTop.player) + ' — Test Runs',
    text: 'Career leader with ' + (testTop.runs||0).toLocaleString() + ' runs @ avg ' + (testTop.average||'—'),
    prob: ''
  });
  if (odiTop) insights.push({
    icon: 'fa-circle-dot',
    title: esc(odiTop.player) + ' — ODI Runs',
    text: 'Most ODI runs: ' + (odiTop.runs||0).toLocaleString() + ' in ' + (odiTop.matches||'—') + ' matches',
    prob: ''
  });
  if (t20Top) insights.push({
    icon: 'fa-bolt',
    title: esc(t20Top.player) + ' — T20I Wickets',
    text: t20Top.wickets + ' wickets @ ' + (t20Top.average||'—') + ' avg in T20Is',
    prob: ''
  });
  if (testWkt) insights.push({
    icon: 'fa-star',
    title: esc(testWkt.player) + ' — Test Wickets',
    text: 'Career Test wickets: ' + testWkt.wickets + ' in ' + (testWkt.matches||'—') + ' matches',
    prob: ''
  });

  if (!insights.length) return;
  strip.innerHTML = insights.slice(0,3).map(function(ins) {
    return '<div class="insight-card" style="padding:0">'
      + '<div class="insight-icon-wrap"><i class="fa ' + ins.icon + '" style="font-size:1.1rem;color:var(--accent);"></i></div>'
      + '<div class="insight-body"><div class="insight-title">' + ins.title + '</div><div class="insight-text">' + ins.text + '</div></div>'
      + (ins.prob ? '<div class="insight-prob">' + ins.prob + '</div>' : '')
    + '</div>';
  }).join('');
}

// ─── Upcoming Matches ─────────────────────────────────────────────────────────
async function loadUpcoming() {
  var data = await apiFetch('/api/matches');
  var allMatches = (data && data.data) ? data.data : [];
  var upcoming = allMatches.filter(function(m) { return !m.matchEnded; }).slice(0,5);

  var container = document.querySelector('[data-upcoming]');
  if (!container) return;

  if (!upcoming.length) {
    // Hide the upcoming section gracefully rather than showing a technical error
    var section = container.closest('section') || container.closest('.card');
    if (section) section.style.display = 'none';
    return;
  }

  container.innerHTML = upcoming.map(function(m, i) {
    var t1 = m.t1||m.team1||'TBA'; var t2 = m.t2||m.team2||'TBA';
    var venue = m.venue||''; var date = m.date||m.dateTimeGMT||'';
    var fmt = m.matchType||m.type||'';
    var isLive = m.matchStarted && !m.matchEnded;
    var delays = ['delay-1','delay-2','delay-3','delay-4','delay-5'];
    return '<a href="match-detail.html?id=' + esc(m.id||'') + '" class="upcoming-row anim-up ' + delays[i] + '">'
      + '<div class="team-flag" style="width:36px;height:36px;">' + flCircle(t1, 36) + '</div>'
      + '<div style="flex:1">'
        + '<div class="upcoming-teams">' + esc(t1) + ' vs ' + esc(t2) + '</div>'
        + '<div class="upcoming-meta"><i class="fa fa-location-dot"></i> ' + esc(venue) + ' <span class="match-format-badge">' + esc(fmt) + '</span></div>'
      + '</div>'
      + '<div class="upcoming-time">' + esc(date) + '</div>'
      + (isLive ? '<span class="status-badge status-live" style="font-size:.6rem;">Live</span>' : '')
    + '</a>';
  }).join('');
}

// ─── Format filter for upcoming ───────────────────────────────────────────────
function wireUpcomingFilter() {
  document.querySelectorAll('.filter-bar .filter-chip').forEach(function(chip) {
    chip.addEventListener('click', function() {
      chip.closest('.filter-bar').querySelectorAll('.filter-chip').forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active');
      var fmtText = chip.textContent.trim().toUpperCase();
      document.querySelectorAll('[data-upcoming] .upcoming-row').forEach(function(row) {
        if (fmtText === 'ALL') { row.style.display = ''; return; }
        var badge = (row.querySelector('.match-format-badge') || {}).textContent || '';
        row.style.display = badge.toUpperCase().includes(fmtText) ? '' : 'none';
      });
    });
  });
}

// ─── Trending Players ─────────────────────────────────────────────────────────
async function loadTrendingPlayers() {
  var data = await apiFetch('/api/players?limit=4&sort=runs');
  if (!data || !data.players || !data.players.length) return;
  var meta = await apiFetch('/api/meta/players') || {};
  var container = document.querySelector('[data-trending-players]');
  if (!container) return;

  var delays = ['delay-1','delay-2','delay-3','delay-4'];
  container.innerHTML = data.players.map(function(p, i) {
    var name    = p.name || '';
    var country = p.country || (meta[name] && meta[name].country) || '';
    var bat     = p.batting || {};
    var fmts    = ['ODI','T20I','Test'];
    var bestBat = null;
    for (var fi = 0; fi < fmts.length; fi++) {
      if (bat[fmts[fi]] && (bat[fmts[fi]].innings||0) > 5) { bestBat = bat[fmts[fi]]; break; }
    }
    var bowl = p.bowling || {};
    var bestBowl = null;
    for (var fj = 0; fj < fmts.length; fj++) {
      if (bowl[fmts[fj]] && (bowl[fmts[fj]].wickets||0) > 5) { bestBowl = bowl[fmts[fj]]; break; }
    }
    var initials = name.split(' ').map(function(w){return w[0]||'';}).join('').slice(0,2).toUpperCase();
    var statsHtml = bestBat
      ? '<div class="pcard-stat"><div class="pcard-stat-val">' + (bestBat.average||'—') + '</div><div class="pcard-stat-lbl">Avg</div></div>'
        + '<div class="pcard-stat"><div class="pcard-stat-val">' + (bestBat.strike_rate||'—') + '</div><div class="pcard-stat-lbl">SR</div></div>'
        + '<div class="pcard-stat"><div class="pcard-stat-val">' + (bestBat.hundreds||'—') + '</div><div class="pcard-stat-lbl">100s</div></div>'
      : bestBowl
      ? '<div class="pcard-stat"><div class="pcard-stat-val">' + (bestBowl.average||'—') + '</div><div class="pcard-stat-lbl">Avg</div></div>'
        + '<div class="pcard-stat"><div class="pcard-stat-val">' + (bestBowl.economy||'—') + '</div><div class="pcard-stat-lbl">Econ</div></div>'
        + '<div class="pcard-stat"><div class="pcard-stat-val">' + (bestBowl.wickets||'—') + '</div><div class="pcard-stat-lbl">Wkts</div></div>'
      : '';

    return '<div class="card player-card anim-up ' + delays[i] + '">'
      + '<div class="player-avatar" style="position:relative;overflow:hidden;">'
        + '<span style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-size:1.4rem;font-weight:700;color:var(--accent);">' + initials + '</span>'
        + (country ? '<img src="' + FLAG_CDN + (COUNTRY_ISO[country]||country) + '.svg" style="position:absolute;bottom:2px;right:2px;width:20px;height:20px;border-radius:50%;border:1.5px solid var(--surface-1);object-fit:cover;" onerror="this.style.display=\'none\'">' : '')
      + '</div>'
      + '<div class="player-name">' + esc(name) + '</div>'
      + '<div class="player-meta">' + (country ? fl(country,14) + esc(country) : '—') + '</div>'
      + '<div class="player-stat-row" style="display:grid;grid-template-columns:repeat(3,1fr);gap:.4rem;">' + statsHtml + '</div>'
      + '<a href="player-profile.html?name=' + encodeURIComponent(name) + '" class="btn btn-secondary btn-sm" style="width:100%;justify-content:center;margin-top:0.3rem;">View Profile</a>'
    + '</div>';
  }).join('');
}

// ─── Team Rankings mini table ─────────────────────────────────────────────────
async function loadMiniRankings() {
  var data = await apiFetch('/api/icc-rankings?category=teams&format=T20I');
  if (!data || !data.rankings || !data.rankings.length) return;
  var tbody = document.querySelector('.rankings-mini tbody');
  if (!tbody) return;

  var rankClass = ['rank-1','rank-2','rank-3'];
  tbody.innerHTML = data.rankings.slice(0, 6).map(function(r, i) {
    var rc  = rankClass[i] || '';
    var ch  = String(r.change || '—');
    var chC = ch.startsWith('+') || ch.includes('▲') ? 'rank-up'
            : ch.startsWith('-') || ch.includes('▼') ? 'rank-down'
            : 'rank-same';
    return '<tr>'
      + '<td><span class="rank-num ' + rc + '">' + (r.rank||i+1) + '</span></td>'
      + '<td class="bold">' + fl(r.team, 20) + esc(r.team) + '</td>'
      + '<td class="mono">' + (r.rating||'—') + '</td>'
      + '<td class="mono">' + (r.points||'—') + '</td>'
      + '<td><span class="rank-change ' + chC + '">' + esc(ch) + '</span></td>'
    + '</tr>';
  }).join('');
}

// ─── Recent Results ──────────────────────────────────────────────────────────
async function loadRecentResults() {
  var data = await apiFetch('/api/matches');
  var allMatches = (data && data.data) ? data.data : [];
  var completed = allMatches.filter(function(m){ return m.matchEnded; }).slice(0,4);

  // Find recent results container
  var recentEl = null;
  document.querySelectorAll('[style*="flex-direction:column"]').forEach(function(el) {
    if (el.querySelector('a.upcoming-row') && !recentEl) {
      var section = el.closest('section');
      if (section && (section.querySelector('.section-title')||{}).textContent.toLowerCase().includes('recent')) {
        recentEl = el;
      }
    }
  });
  if (!recentEl) return;

  if (!completed.length) {
    recentEl.closest('section') && (recentEl.closest('section').style.display = 'none');
    return;
  }

  recentEl.innerHTML = completed.map(function(m) {
    var t1 = m.t1||m.team1||''; var t2 = m.t2||m.team2||'';
    return '<a href="match-detail.html?id=' + esc(m.id||'') + '" class="upcoming-row" style="padding:0.75rem 1rem;">'
      + '<div style="flex:1">'
        + '<div style="font-size:.88rem;font-weight:600;color:var(--text-primary)">' + esc(m.status || (t1+' vs '+t2)) + '</div>'
        + '<div class="upcoming-meta"><span class="match-format-badge">' + esc(m.matchType||'') + '</span> ' + esc(m.venue||'') + '</div>'
      + '</div>'
      + '<span class="status-badge status-completed" style="font-size:.6rem;">Done</span>'
    + '</a>';
  }).join('');
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  loadStatBar();
  loadLiveTicker();
  loadLiveMatches();
  loadQuickInsights();
  loadUpcoming();
  loadTrendingPlayers();
  loadMiniRankings();
  loadRecentResults();
  wireUpcomingFilter();
});
