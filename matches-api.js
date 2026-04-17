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

function getTeamInitials(teamName) {
  if (!teamName) return '?';
  const words = teamName.split(/\s+/).filter(Boolean);
  if (words.length === 0) return '?';
  if (words.length === 1) return words[0][0].toUpperCase();
  if (words.length === 2) return (words[0][0] + words[1][0]).toUpperCase();
  return (words[0][0] + words[1][0] + words[2][0]).toUpperCase();
}

function flagCircle(teamName, size) {
  size = size || 28;
  const iso = guessIso(teamName);
  if (!iso) return '<span style="font-size:' + Math.round(size*0.55) + 'px;font-weight:700;color:var(--accent);">' + getTeamInitials(teamName) + '</span>';
  return '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(teamName) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

function classifyMatch(match) {
  if (!match) return 'upcoming';
  if (match.matchEnded === true) return 'completed';
  if (match.matchStarted === true) return 'live';
  var status = (match.status || '').toLowerCase();
  if (/won by|beat|draw|tie|no result|abandoned|match ended|completed|declared/.test(status)) return 'completed';
  if (/innings break|stumps|tea|day \d|live|needs|need|requires|after lunch|after tea|session/.test(status)) return 'live';
  return 'upcoming';
}

function parseMatchNameTeams(match) {
  if (!match || !match.name) return ['', ''];
  var parts = match.name.split(/\s+vs\s+|\s+v\s+|\s+versus\s+/i);
  if (parts.length < 2) return ['', ''];
  var left = parts[0].trim();
  var right = parts[1].trim().split(/,|\(|–|-/)[0].trim();
  return [left, right];
}

function getMatchTeamName(match, index) {
  if (!match) return '';
  var fallback = (Array.isArray(match.teams) ? match.teams[index] : '') || (match.teamInfo && match.teamInfo[index] && match.teamInfo[index].name) || '';
  if (index === 0) {
    return match.t1 || match.team1 || fallback || parseMatchNameTeams(match)[0] || '';
  }
  return match.t2 || match.team2 || fallback || parseMatchNameTeams(match)[1] || '';
}

function formatScoreObject(score) {
  if (!score || score.r == null) return '';
  var wickets = score.w != null ? '/' + score.w : '';
  var overs = score.o != null ? ' (' + score.o + 'o)' : '';
  return String(score.r) + wickets + overs;
}

function normalizeTeamName(name) {
  return String(name || '').toLowerCase().replace(/women|men|'s/g, ' ').replace(/\s+/g, ' ').trim();
}

function looksLikeScore(value) {
  return /\d+\s*\/\s*\d+|\d+\s*\(\s*\d+(?:\.\d+)?o?\s*\)/.test(String(value || ''));
}

function getMatchScore(match, index) {
  if (match && Array.isArray(match.score) && match.score.length) {
    var team = getMatchTeamName(match, index);
    var hasInningLabels = match.score.some(function(s) {
      return s && String(s.inning || '').trim().length > 0;
    });

    if (team) {
      var teamClean = normalizeTeamName(team);
      for (var i = 0; i < match.score.length; i++) {
        var score = match.score[i];
        if (score && score.r != null) {
          var inningTeamRaw = String(score.inning || '').split(/\s+Inning/i)[0].trim();
          var inningClean = normalizeTeamName(inningTeamRaw);
          if (inningClean === teamClean || inningClean.includes(teamClean) || teamClean.includes(inningClean)) {
            return formatScoreObject(score);
          }
        }
      }
    }

    // If innings labels exist and no team match was found, do not guess by index.
    // This prevents mirrored scores in edge-case API payloads.
    if (hasInningLabels) {
      return '';
    }

    // Fallback by index only when that innings index exists.
    if (index < match.score.length && match.score[index] && match.score[index].r != null) {
      return formatScoreObject(match.score[index]);
    }
  }

  var s1 = match && match.t1s ? String(match.t1s) : '';
  var s2 = match && match.t2s ? String(match.t2s) : '';

  if (index === 0) {
    return looksLikeScore(s1) ? s1 : '';
  }

  // Guard against occasional API duplication where both fallbacks mirror innings 1.
  if (looksLikeScore(s2) && s2 !== s1) {
    return s2;
  }
  return '';
}

// ── Build a single match row card ─────────────────────────────────────────────
function buildMatchCard(match, statusClass, delay) {
  delay = delay || '';
  const id     = match.id || match.unique_id || '';
  const t1     = getMatchTeamName(match, 0) || 'TBA';
  const t2     = getMatchTeamName(match, 1) || 'TBA';
  const score1 = getMatchScore(match, 0);
  const score2 = getMatchScore(match, 1);
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

  var dp='match-detail';
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
  let matches = (data && data.data) ? data.data : [];

  const liveGroup = document.getElementById('group-live');
  if (!liveGroup) return;

  const liveTab = document.querySelector('.status-tab.live-tab');
  const liveCountPill = liveTab && liveTab.querySelector('.count-pill');

  matches = matches.filter(function(m) { return classifyMatch(m) === 'live'; });

  if (!matches.length) {
    const upcomingData = await apiFetch('/api/matches');
    const allMatches = (upcomingData && upcomingData.data) ? upcomingData.data : [];
    matches = allMatches.filter(function(m) { return classifyMatch(m) === 'upcoming'; }).slice(0, 6);
  }

  if (!matches.length) {
    // Fallback dummy match
    matches = [{
      id: 'dummy1',
      name: 'India vs Australia, 1st Test, Border-Gavaskar Trophy 2026',
      matchType: 'test',
      status: 'Match starts at Apr 15, 09:30 GMT',
      venue: 'MA Chidambaram Stadium, Chennai',
      date: '2026-04-15',
      dateTimeGMT: '2026-04-15T09:30:00',
      teams: ['India', 'Australia'],
      teamInfo: [
        {name: 'India', shortname: 'IND', img: 'https://g.cricapi.com/iapi/6-637877074931980375.webp?w=48'},
        {name: 'Australia', shortname: 'AUS', img: 'https://g.cricapi.com/iapi/4-637877074931980375.webp?w=48'}
      ],
      series_id: 'dummy',
      matchStarted: false,
      matchEnded: false
    }];
  }

  if (!matches.length) {
    const label = liveGroup.querySelector('.match-group-label');
    const labelHtml = label ? label.outerHTML : '';
    liveGroup.innerHTML = labelHtml + '<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.88rem;background:var(--surface-1);border:1px solid var(--border);border-radius:var(--radius-lg);">'
      + '<i class="fa fa-satellite-dish" style="font-size:1.5rem;display:block;margin-bottom:0.75rem;opacity:0.4;"></i>'
      + 'No live matches right now. Check back later for live coverage.</div>';
    if (liveCountPill) liveCountPill.textContent = '0';
    _allMatches['group-live'] = [];
    return;
  }

  _allMatches['group-live'] = matches.slice(0, 6);
  injectCards('group-live', _allMatches['group-live'], 'is-live', 'No live matches available right now.');
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
    _allMatches['group-upcoming'] = [];
    _allMatches['group-completed'] = [];
    // Show fallback message in upcoming and completed groups
    ['group-upcoming','group-completed'].forEach(function(id) {
      const g = document.getElementById(id);
      if (!g) return;
      const label = g.querySelector('.match-group-label');
      const labelHtml = label ? label.outerHTML : '';
      if (g.style.display === 'none') return; // skip hidden groups
      g.innerHTML = labelHtml + '<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.88rem;background:var(--surface-1);border:1px solid var(--border);border-radius:var(--radius-lg);">'
        + '<i class="fa fa-calendar-xmark" style="font-size:1.5rem;display:block;margin-bottom:0.75rem;opacity:0.4;"></i>'
        + 'Match data is unavailable. Run <code>python app.py</code> to start the server.</div>';
    });
    return;
  }

  const allMatches = data.data;

  if (!allMatches.length) {
    // Fallback dummy matches
    const dummyMatches = [{
      id: 'dummy2',
      name: 'England vs South Africa, 1st ODI, England tour of South Africa 2026',
      matchType: 'odi',
      status: 'Match starts at Apr 20, 10:00 GMT',
      venue: 'Newlands, Cape Town',
      date: '2026-04-20',
      dateTimeGMT: '2026-04-20T10:00:00',
      teams: ['England', 'South Africa'],
      teamInfo: [
        {name: 'England', shortname: 'ENG', img: 'https://g.cricapi.com/iapi/1-637877074931980375.webp?w=48'},
        {name: 'South Africa', shortname: 'SA', img: 'https://g.cricapi.com/iapi/3-637877074931980375.webp?w=48'}
      ],
      series_id: 'dummy2',
      matchStarted: false,
      matchEnded: false
    }];
    _allMatches['group-upcoming'] = dummyMatches;
    _allMatches['group-completed'] = [];
    injectCards('group-upcoming', _allMatches['group-upcoming'], 'is-upcoming', 'No upcoming matches.');
    injectCards('group-completed', _allMatches['group-completed'], 'is-completed', 'No completed matches.');
    return;
  }

  const upcoming  = allMatches.filter(function(m) { return classifyMatch(m) === 'upcoming'; });
  const completed = allMatches.filter(function(m) { return classifyMatch(m) === 'completed'; });
  const live      = allMatches.filter(function(m) { return classifyMatch(m) === 'live'; });

  _allMatches['group-upcoming'] = upcoming;
  _allMatches['group-completed'] = completed;
  if (live.length) _allMatches['group-live'] = live.slice(0, 6);

  // Update count pills on status tabs
  const upcomingPill = document.querySelector('.status-tab[data-status="upcoming"] .count-pill');
  const completedPill = document.querySelector('.status-tab[data-status="completed"] .count-pill');
  if (upcomingPill)  upcomingPill.textContent  = upcoming.length;
  if (completedPill) completedPill.textContent = completed.length;

  if (upcoming.length)  injectCards('group-upcoming',  _allMatches['group-upcoming'], 'is-upcoming',  'No upcoming matches scheduled.');
  else                  injectCards('group-upcoming',  [], 'is-upcoming', 'No upcoming matches found.');

  if (completed.length) injectCards('group-completed', _allMatches['group-completed'], 'is-completed', 'No recent results.');
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

// ── Store matches for filtering/sorting ──────────────────────────────────────
var _allMatches = { 'group-live': [], 'group-upcoming': [], 'group-completed': [] };

// ── Apply all active filters ──────────────────────────────────────────────────
function applyFilters() {
  var activeFormat = document.querySelector('.filter-chip[data-format].active');
  var fmt = activeFormat ? (activeFormat.dataset.format || 'all').toLowerCase() : 'all';
  
  // Get team and sort values from selects
  var teamVal = '';
  var sortVal = '';
  document.querySelectorAll('.filter-select').forEach(function(sel) {
    var firstOpt = sel.querySelector('option:first-child');
    if (firstOpt && firstOpt.textContent.includes('All Teams')) {
      teamVal = (sel.value || '').toLowerCase();
    } else if (firstOpt && firstOpt.textContent.includes('Sort')) {
      sortVal = sel.value.toLowerCase();
    }
  });

  // For each group, apply filters
  ['group-live', 'group-upcoming', 'group-completed'].forEach(function(groupId) {
    var allMatches = _allMatches[groupId] || [];
    var filtered = allMatches.slice();

    // Apply format filter (FIXED: T20I vs IPL separation)
    filtered = filtered.filter(function(m) {
      if (fmt === 'all') return true;
      var mFmt = (m.matchType || m.type || '').toLowerCase();
      var haystack = ((m.name || '') + ' ' + (m.series || '') + ' ' + (m.series_id || '')).toLowerCase();
      var isIpl = mFmt.includes('ipl') || haystack.includes(' indian premier league') || /\bipl\b/.test(haystack);
      if (fmt === 'ipl') return isIpl;                     // IPL by type OR series/name
      if (fmt === 't20') return mFmt.includes('t20');      // Keep IPL visible in T20 as requested
      if (fmt === 'odi') return mFmt === 'odi';
      if (fmt === 'test') return mFmt === 'test';
      return true;
    });

    // Apply team filter
    if (teamVal && teamVal !== '') {
      filtered = filtered.filter(function(m) {
        var t1 = (getMatchTeamName(m, 0) || '').toLowerCase();
        var t2 = (getMatchTeamName(m, 1) || '').toLowerCase();
        // Check if team name includes the filter value, or if removing "women" from team name matches
        var t1Base = t1.replace(/women|men|'s/g, ' ').trim();
        var t2Base = t2.replace(/women|men|'s/g, ' ').trim();
        var valClean = teamVal.replace(/women|men|'s/g, ' ').trim();
        return t1.includes(teamVal) || t2.includes(teamVal) || 
               t1Base.includes(valClean) || t2Base.includes(valClean) ||
               valClean.includes(t1Base.split(' ')[0]) || valClean.includes(t2Base.split(' ')[0]);
      });
    }

    // Apply sort
    if (sortVal && sortVal.includes('oldest')) {
      filtered.sort(function(a, b) {
        var dateA = new Date(a.date || a.dateTimeGMT || 0);
        var dateB = new Date(b.date || b.dateTimeGMT || 0);
        return dateA - dateB;
      });
    } else if (sortVal && sortVal.includes('format')) {
      filtered.sort(function(a, b) {
        var fmtOrder = { 'test': 1, 'odi': 2, 't20': 3, 't20i': 3, 'ipl': 4 };
        var fmtA = (a.matchType || a.type || '').toLowerCase();
        var fmtB = (b.matchType || b.type || '').toLowerCase();
        var ordA = fmtOrder[fmtA] || 99;
        var ordB = fmtOrder[fmtB] || 99;
        return ordA - ordB;
      });
    } else {
      // Default: newest first
      filtered.sort(function(a, b) {
        var dateA = new Date(a.date || a.dateTimeGMT || 0);
        var dateB = new Date(b.date || b.dateTimeGMT || 0);
        return dateB - dateA;
      });
    }

    // Inject filtered matches
    injectCards(groupId, filtered, groupId.includes('live') ? 'is-live' : (groupId.includes('completed') ? 'is-completed' : 'is-upcoming'), 'No matches.');
  });
}

// ── Format filter chips ───────────────────────────────────────────────────────
function initFormatFilter() {
  // Format chips (data-format)
  document.querySelectorAll('.filter-chip[data-format]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      document.querySelectorAll('.filter-chip[data-format]').forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active');
      applyFilters();
    });
  });

  // Filter selects (Team + Sort dropdowns in filter bar)
  document.querySelectorAll('.filter-select').forEach(function(sel) {
    sel.addEventListener('change', function() {
      applyFilters();
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
