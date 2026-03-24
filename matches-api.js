/**
 * matches-api.js
 * ==============
 * API wiring for matches.html
 * Loads live, upcoming and completed matches from CricAPI.
 * Falls back to static dummy data gracefully.
 *
 * Actual HTML IDs:
 *   #group-live       — live matches container
 *   #group-upcoming   — upcoming matches container
 *   #group-completed  — completed matches container
 *   .filter-chip[data-format] — format filter chips (all/t20/odi/test)
 *   .sidebar-series-item — series sidebar rows
 */

function guessIso(teamName) {
  if (!teamName) return '';
  for (const [c, code] of Object.entries(COUNTRY_ISO))
    if (teamName.toLowerCase().includes(c.toLowerCase())) return code;
  return '';
}

function flagCircle(teamName, size) {
  size = size || 28;
  const iso = guessIso(teamName);
  if (!iso) return '<span style="font-size:' + Math.round(size*0.55) + 'px;font-weight:700;color:var(--accent);">' + (teamName||'?')[0] + '</span>';
  return '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(teamName) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

// ── Build a single match row card ─────────────────────────────────────────────
function buildMatchCard(match, statusClass, delay) {
  delay = delay || '';
  const id     = match.id || match.unique_id || '';
  const t1     = match.t1 || match.team1 || 'TBA';
  const t2     = match.t2 || match.team2 || 'TBA';
  const score1 = match.t1s || '';
  const score2 = match.t2s || '';
  const fmt    = match.matchType || match.type || '';
  const venue  = match.venue || '';
  const date   = match.date || match.dateTimeGMT || '';
  const status = match.status || '';
  const series = match.series || match.series_id || '';

  const isLive      = statusClass === 'is-live';
  const isCompleted = statusClass === 'is-completed';

  let badge;
  if (isLive) {
    badge = '<span class="status-badge status-live">Live</span>';
  } else if (isCompleted) {
    badge = '<span class="status-badge status-completed">Completed</span>';
  } else {
    badge = '<span class="status-badge" style="background:rgba(94,184,255,0.1);color:var(--accent);border:1px solid rgba(94,184,255,0.2);">Upcoming</span>';
  }

  let infoLine;
  if (isLive) {
    infoLine = '<div style="font-size:0.75rem;color:var(--green-live);font-weight:600;">' + esc(status) + '</div>';
  } else if (isCompleted) {
    infoLine = '<div style="font-size:0.75rem;color:var(--text-muted);">' + esc(status) + '</div>';
  } else {
    infoLine = '<div style="font-size:0.75rem;color:var(--accent-warm);font-weight:600;">' + esc(date) + '</div>';
  }

  const s1html = score1 ? '<span class="match-row-score">' + esc(score1) + '</span>' : '';
  const s2html = score2 ? '<span class="match-row-score">' + esc(score2) + '</span>' : '';

  var dp=(statusClass==='is-upcoming')?'match-upcoming':'match-detail';
  return '<a href="'+dp+'.html?id=' + esc(id) + '" class="match-row-card ' + statusClass + ' anim-up ' + delay + '">'
    + '<div class="match-row-badges">' + badge + '<span class="match-format-badge">' + esc(fmt) + '</span></div>'
    + '<div class="match-row-teams">'
      + '<div class="match-row-team">'
        + '<span class="match-row-flag" style="width:28px;height:28px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:var(--surface-2);flex-shrink:0;">' + flagCircle(t1,28) + '</span>'
        + '<span class="match-row-team-name">' + esc(t1) + '</span>'
        + s1html
      + '</div>'
      + '<div class="match-row-divider"></div>'
      + '<div class="match-row-team">'
        + '<span class="match-row-flag" style="width:28px;height:28px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:var(--surface-2);flex-shrink:0;">' + flagCircle(t2,28) + '</span>'
        + '<span class="match-row-team-name">' + esc(t2) + '</span>'
        + s2html
      + '</div>'
    + '</div>'
    + '<div class="match-row-info">'
      + '<div class="match-row-venue"><i class="fa fa-location-dot"></i> ' + esc(venue) + '</div>'
      + '<div class="match-row-series">' + esc(series) + '</div>'
      + infoLine
    + '</div>'
    + '<i class="fa fa-chevron-right match-row-arrow"></i>'
  + '</a>';
}

// ── Inject cards into a group, preserving the label header ───────────────────
var _ms={},_ps={},_PSZ=10;
function injectCards(g,all,sc,msg){_ms[g]={matches:all,statusClass:sc,emptyMsg:msg};_ps[g]=1;_rg(g);}
function _rg(g){
  var grp=document.getElementById(g);if(!grp)return;
  var s=_ms[g]||{},all=s.matches||[],sc=s.statusClass||'',msg=s.emptyMsg||'No matches.';
  var pg=_ps[g]||1,lbl=grp.querySelector('.match-group-label'),lh=lbl?lbl.outerHTML:'';
  if(!all.length){grp.innerHTML=lh+'<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:.88rem;"><i class="fa fa-calendar-xmark" style="font-size:1.5rem;display:block;margin-bottom:.5rem;opacity:.4;"></i>'+esc(msg)+'</div>';return;}
  var tot=Math.ceil(all.length/_PSZ);pg=Math.max(1,Math.min(pg,tot));_ps[g]=pg;
  var dl=['','delay-1','delay-2','delay-3','delay-4','delay-5'];
  var sl=all.slice((pg-1)*_PSZ,pg*_PSZ);
  var cards=sl.map(function(m,i){return buildMatchCard(m,sc,dl[i%dl.length]);}).join('');
  var pag='';
  if(tot>1){
    var b='<button class="page-btn'+(pg===1?' disabled':'')+'" data-group="'+g+'" data-page="'+(pg-1)+'"><i class="fa fa-chevron-left"></i></button>';
    for(var p=1;p<=tot;p++){
      if(tot<=7||p===1||p===tot||Math.abs(p-pg)<=1)b+='<button class="page-btn'+(p===pg?' active':'')+'" data-group="'+g+'" data-page="'+p+'">'+p+'</button>';
      else if(Math.abs(p-pg)===2)b+='<button class="page-btn" style="pointer-events:none">…</button>';
    }
    b+='<button class="page-btn'+(pg===tot?' disabled':'')+'" data-group="'+g+'" data-page="'+(pg+1)+'"><i class="fa fa-chevron-right"></i></button>';
    pag='<div class="pagination">'+b+'</div>';
  }
  grp.innerHTML=lh+cards+pag;
}
document.addEventListener('click',function(e){
  var btn=e.target.closest&&e.target.closest('.page-btn');
  if(!btn||btn.classList.contains('disabled')||btn.style.pointerEvents==='none')return;
  var g=btn.dataset.group,p=parseInt(btn.dataset.page,10);
  if(!g||isNaN(p))return;
  _ps[g]=p;_rg(g);
  var el=document.getElementById(g);if(el)el.scrollIntoView({behavior:'smooth',block:'start'});
});

// ── Load live matches ─────────────────────────────────────────────────────────
async function loadLive() {
  const data = await apiFetch('/api/live');
  const matches = (data && data.data) ? data.data : [];

  const liveGroup = document.getElementById('group-live');
  if (!liveGroup) return;

  const liveTab = document.querySelector('.status-tab.live-tab');
  const liveCountPill = liveTab && liveTab.querySelector('.count-pill');

  if (!matches.length) {
    // Show "no live matches" message inside the live group
    const label = liveGroup.querySelector('.match-group-label');
    const labelHtml = label ? label.outerHTML : '';
    liveGroup.innerHTML = labelHtml + '<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.88rem;background:var(--surface-1);border:1px solid var(--border);border-radius:var(--radius-lg);">'
      + '<i class="fa fa-satellite-dish" style="font-size:1.5rem;display:block;margin-bottom:0.75rem;opacity:0.4;"></i>'
      + 'No live matches right now. Live data is unavailable — check back later.</div>';
    if (liveCountPill) liveCountPill.textContent = '0';
    return;
  }

  injectCards('group-live', matches.slice(0, 6), 'is-live', 'No live matches right now.');
  if (liveCountPill) liveCountPill.textContent = matches.length;

  const liveLabel = document.querySelector('#group-live .match-group-date');
  if (liveLabel) {
    liveLabel.innerHTML = '<span style="width:7px;height:7px;background:var(--green-live);border-radius:50%;display:inline-block;margin-right:6px;animation:pulse-dot 1.2s infinite;"></span>Live Now (' + matches.length + ')';
  }
}

// ── Load upcoming + completed ─────────────────────────────────────────────────
async function loadFixtures() {
  const data = await apiFetch('/api/matches');
  if (!data || !data.data || !data.data.length) {
    // Show fallback message in upcoming and completed groups
    ['group-upcoming','group-completed'].forEach(function(id) {
      const g = document.getElementById(id);
      if (!g) return;
      const label = g.querySelector('.match-group-label');
      const labelHtml = label ? label.outerHTML : '';
      if (g.style.display === 'none') return; // skip hidden groups
      g.innerHTML = labelHtml + '<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.88rem;background:var(--surface-1);border:1px solid var(--border);border-radius:var(--radius-lg);">'
        + '<i class="fa fa-calendar-xmark" style="font-size:1.5rem;display:block;margin-bottom:0.75rem;opacity:0.4;"></i>'
        + 'Match data is unavailable. Run <code>python fetch_live.py --fixtures</code> to cache fixtures.</div>';
    });
    return;
  }

  const allMatches = data.data;
  const upcoming  = allMatches.filter(function(m) { return !m.matchStarted && !m.matchEnded; });
  const completed = allMatches.filter(function(m) { return m.matchEnded; });
  const live      = allMatches.filter(function(m) { return m.matchStarted && !m.matchEnded; });

  // Update count pills on status tabs
  const upcomingPill = document.querySelector('.status-tab[data-status="upcoming"] .count-pill');
  const completedPill = document.querySelector('.status-tab[data-status="completed"] .count-pill');
  if (upcomingPill)  upcomingPill.textContent  = upcoming.length;
  if (completedPill) completedPill.textContent = completed.length;

  if (upcoming.length)  injectCards('group-upcoming',  upcoming, 'is-upcoming',  'No upcoming matches scheduled.');
  else                  injectCards('group-upcoming',  [], 'is-upcoming', 'No upcoming matches found.');

  if (completed.length) injectCards('group-completed', completed, 'is-completed', 'No recent results.');
  else                  injectCards('group-completed', [], 'is-completed', 'No recent results found.');
  // Also inject live if live group wasn't filled by loadLive
  if (live.length) {
    const liveGroup = document.getElementById('group-live');
    const liveLabel = liveGroup && liveGroup.querySelector('.match-group-date');
    if (liveLabel && liveLabel.textContent.includes('No live')) {
      injectCards('group-live', live.slice(0, 6), 'is-live', 'No live matches.');
    }
  }
}

// ── Load series sidebar ───────────────────────────────────────────────────────
async function loadSeries() {
  const data = await apiFetch('/api/series');
  // Normalize: our fixed Flask endpoint returns {data:[...]}
  const seriesList = (data && data.data) ? data.data : (data && data.series) ? data.series : [];
  if (!seriesList.length) return;

  const firstItem = document.querySelector('.sidebar-series-item');
  if (!firstItem) return;
  const container = firstItem.parentElement;
  if (!container) return;

  const head = container.querySelector('.sidebar-card-header');
  const headHtml = head ? head.outerHTML : '';

  container.innerHTML = headHtml + seriesList.slice(0, 6).map(function(s) {
    const name   = s.name || s.series || s.title || '—';
    const fmt    = s.matchType || s.type || '';
    const status = s.status || 'Active';
    const total  = s.total || s.totalMatches || 0;
    const current = s.current || s.currentMatch || 0;
    const progress = total > 0 ? Math.min(Math.round((current / total) * 100), 100) : 30;
    return '<a href="#" class="sidebar-series-item">'
      + '<div class="series-name">' + esc(name) + '</div>'
      + '<div class="series-meta">'
        + (fmt ? '<span class="match-format-badge" style="font-size:0.62rem;">' + esc(fmt) + '</span> ' : '')
        + esc(status)
      + '</div>'
      + '<div class="series-progress"><div class="series-progress-fill" style="width:' + progress + '%"></div></div>'
    + '</a>';
  }).join('');
}

// ── Format filter chips ───────────────────────────────────────────────────────
function initFormatFilter() {
  // Format chips (data-format)
  document.querySelectorAll('.filter-chip[data-format]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      document.querySelectorAll('.filter-chip[data-format]').forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active');
      var fmt = (chip.dataset.format || '').toLowerCase();
      document.querySelectorAll('.match-row-card').forEach(function(card) {
        if (fmt === 'all') { card.style.display = ''; return; }
        var cardFmt = (card.querySelector('.match-format-badge') || {}).textContent || '';
        cardFmt = cardFmt.trim().toLowerCase();
        var hit = fmt === 't20'  ? (cardFmt.includes('t20') || cardFmt.includes('ipl'))
                : fmt === 'odi'  ? cardFmt === 'odi'
                : fmt === 'test' ? cardFmt === 'test'
                : fmt === 'ipl'  ? (cardFmt.includes('ipl') || cardFmt.includes('t20'))
                : cardFmt.includes(fmt);
        card.style.display = hit ? '' : 'none';
      });
    });
  });

  // Filter selects (Sort + Region dropdowns in filter bar)
  document.querySelectorAll('.filter-select').forEach(function(sel) {
    sel.addEventListener('change', function() {
      var val = sel.value.toLowerCase();
      // Series/region filter
      if (val && val !== 'all matches' && !val.includes('series') && !val.includes('filter') && !val.includes('all')) {
        document.querySelectorAll('.match-row-card').forEach(function(card) {
          var series = (card.dataset.series || card.querySelector('.match-series') || {}).textContent || '';
          card.style.display = (!val || series.toLowerCase().includes(val)) ? '' : 'none';
        });
      } else {
        document.querySelectorAll('.match-row-card').forEach(function(card) { card.style.display = ''; });
      }
    });
  });
}

// Status tabs are handled by the inline script in matches.html

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  // Pre-clear ALL hardcoded match cards immediately — before async data arrives
  // This ensures the user never sees stale hardcoded content in any group
  ['group-live', 'group-upcoming', 'group-completed'].forEach(function(id) {
    var g = document.getElementById(id);
    if (!g) return;
    var label = g.querySelector('.match-group-label');
    var labelHtml = label ? label.outerHTML : '';
    g.innerHTML = labelHtml + '<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.88rem;opacity:0.5;">'
      + '<i class="fa fa-circle-notch fa-spin" style="font-size:1.2rem;display:block;margin-bottom:0.5rem;"></i>'
      + 'Loading…</div>';
  });

  loadLive();
  loadFixtures();
  loadSeries();
  initFormatFilter();
  loadMatchInsights();
});

// ── Match Insights sidebar (from Cricsheet records) ───────────────────────────
async function loadMatchInsights() {
  var data = await apiFetch('/api/records');
  if (!data) return;

  // Find the match insights sidebar card
  var insightCard = null;
  document.querySelectorAll('.sidebar-card').forEach(function(card) {
    var title = (card.querySelector('.sidebar-card-header, .sb-head') || {}).textContent || '';
    if (title.toLowerCase().includes('insight')) insightCard = card;
  });
  if (!insightCard) return;

  var head = insightCard.querySelector('.sidebar-card-header, .sb-head');
  var headHtml = head ? head.outerHTML : '<div class="sb-head"><i class="fa fa-brain"></i> Match Insights</div>';

  // Build insights from real records data
  var testRuns = data.most_runs && data.most_runs.Test && data.most_runs.Test[0];
  var odiWkts  = data.most_wickets && data.most_wickets.ODI && data.most_wickets.ODI[0];
  var t20Runs  = data.most_runs && data.most_runs.T20I && data.most_runs.T20I[0];

  var insights = [];
  if (testRuns) insights.push({ icon: 'fa-cricket-bat-ball', text: '<strong>' + esc(testRuns.player) + '</strong> leads Test run-scorers with ' + (testRuns.runs||0).toLocaleString() + ' runs' });
  if (odiWkts)  insights.push({ icon: 'fa-circle-dot', text: '<strong>' + esc(odiWkts.player) + '</strong> leads ODI wicket-takers with ' + (odiWkts.wickets||0) + ' wickets' });
  if (t20Runs)  insights.push({ icon: 'fa-bolt', text: '<strong>' + esc(t20Runs.player) + '</strong> has most T20I runs: ' + (t20Runs.runs||0).toLocaleString() });
  insights.push({ icon: 'fa-trophy', text: 'Browse <a href="records.html" style="color:var(--accent);">all-time records</a> across formats' });

  if (!insights.length) return;
  insightCard.innerHTML = headHtml + insights.map(function(ins) {
    return '<div class="sidebar-insight" style="padding:.65rem 1.1rem;border-bottom:1px solid var(--border-light);display:flex;gap:.6rem;align-items:center;">'
      + '<i class="fa ' + ins.icon + '" style="color:var(--accent);font-size:.9rem;flex-shrink:0;"></i>'
      + '<div style="font-size:.78rem;color:var(--text-muted);line-height:1.4;">' + ins.text + '</div>'
    + '</div>';
  }).join('');
}
