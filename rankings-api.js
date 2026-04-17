/**
 * rankings-api.js
 * ===============
 * Wires rankings.html to /api/icc-rankings
 * Panel IDs: test-batting, test-bowling, test-allrounder, test-teams
 *            odi-batting,  odi-bowling,  odi-allrounder,  odi-teams
 *            t20-batting,  t20-bowling,  t20-allrounder,  t20-teams
 * Format tabs: data-fmt="test" / "odi" / "t20"
 * Category btns: data-cat="batting" / "bowling" / "allrounder" / "teams"
 */

function fl(country, size) {
  size = size || 28;
  var code = COUNTRY_ISO[country] || '';
  if (!code) return '<span style="width:' + size + 'px;height:' + size + 'px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:var(--surface-2);font-size:0.7rem;color:var(--text-muted);">' + (country||'?').slice(0,2) + '</span>';
  return '<span class="rank-flag" style="overflow:hidden;display:flex;align-items:center;justify-content:center;width:' + size + 'px;height:' + size + 'px;">'
    + '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:100%;height:100%;object-fit:cover;border-radius:50%;" '
    + 'onerror="this.style.display=\'none\'">'
    + '</span>';
}

var medalClass = ['gold','silver','bronze'];

// ── Build a player ranking row ────────────────────────────────────────────────
function buildPlayerRow(r, idx) {
  var medal = idx < 3 ? medalClass[idx] : '';
  var ch = String(r.change || '');
  var changeClass = ch.startsWith('+') ? 'up' : ch.startsWith('-') ? 'down' : 'same';
  var changeIcon  = changeClass === 'up' ? '<i class="fa fa-caret-up"></i>'
                  : changeClass === 'down' ? '<i class="fa fa-caret-down"></i>'
                  : '<i class="fa fa-minus"></i>';
  var rating   = r.rating || '—';
  var barWidth = rating !== '—' ? Math.min(Math.round((parseInt(String(rating)) / 1000) * 100), 100) : 0;
  var barClass = idx === 0 ? 'gold-bar' : idx === 1 ? 'silver-bar' : idx === 2 ? 'bronze-bar' : '';
  var stat2    = r.avg || r.econ || r.bat_avg || r.sr || '—';
  var name     = r.player || r.name || '—';
  var country  = r.country || '';
  var rank     = r.rank || (idx + 1);

  return '<a href="player-profile.html?name=' + encodeURIComponent(name) + '" class="rank-row">'
    + '<div class="rank-medal ' + medal + '">' + rank + '</div>'
    + fl(country, 28)
    + '<div class="rank-identity"><div>'
    +   '<div class="rank-name">' + esc(name) + '</div>'
    +   '<div class="rank-country">' + esc(country) + '</div>'
    + '</div></div>'
    + '<span class="rank-stat primary">' + esc(String(rating)) + '</span>'
    + '<span class="rank-stat">' + esc(String(stat2)) + '</span>'
    + '<span class="rank-move ' + changeClass + '">' + changeIcon + ' ' + esc(r.change || '—') + '</span>'
    + '<div class="rank-bar-wrap"><div class="rank-bar-bg"><div class="rank-bar-fill ' + barClass + '" style="width:' + barWidth + '%"></div></div></div>'
  + '</a>';
}

// ── Build a team ranking row ──────────────────────────────────────────────────
function buildTeamRow(r, idx) {
  var medal = idx < 3 ? medalClass[idx] : '';
  var ch2 = String(r.change || '');
  var cc2 = ch2.startsWith('+') ? 'up' : ch2.startsWith('-') ? 'down' : 'same';
  var ci2 = cc2 === 'up' ? '<i class="fa fa-caret-up"></i>' : cc2 === 'down' ? '<i class="fa fa-caret-down"></i>' : '<i class="fa fa-minus"></i>';
  var team   = r.team || r.name || '—';
  var rating = r.rating || '—';
  var points = r.points || '—';
  var barWidth = rating !== '—' ? Math.min(Math.round((parseInt(String(rating)) / 1000) * 100), 100) : 0;
  var rank = r.rank || (idx + 1);

  return '<a href="team-profile.html?name=' + encodeURIComponent(team) + '" class="rank-row">'
    + '<div class="rank-medal ' + medal + '">' + rank + '</div>'
    + fl(team, 28)
    + '<div class="rank-identity"><div>'
    +   '<div class="rank-name">' + esc(team) + '</div>'
    +   '<div class="rank-country">' + esc(points) + ' pts</div>'
    + '</div></div>'
    + '<span class="rank-stat primary">' + esc(String(rating)) + '</span>'
    + '<span class="rank-stat">' + esc(String(points)) + '</span>'
    + '<span class="rank-move ' + cc2 + '">' + ci2 + ' ' + esc(r.change || '—') + '</span>'
    + '<div class="rank-bar-wrap"><div class="rank-bar-bg"><div class="rank-bar-fill" style="width:' + barWidth + '%"></div></div></div>'
  + '</a>';
}

// ── Inject rows into a cat-panel's rank-card ──────────────────────────────────
function injectRankings(panelId, rows, isTeams) {
  var panel = document.getElementById(panelId);
  if (!panel) { console.warn('rankings-api: panel not found:', panelId); return; }
  var card = panel.querySelector('.rank-card');
  if (!card) { console.warn('rankings-api: .rank-card not found in', panelId); return; }
  if (!rows || !rows.length) { console.warn('rankings-api: no rows for', panelId); return; }

  // Preserve card header AND column header row exactly
  var cardHeader = card.querySelector('.rank-card-header');
  var rowHeader  = card.querySelector('.rank-row-header');
  var keepHtml   = (cardHeader ? cardHeader.outerHTML : '') + (rowHeader ? rowHeader.outerHTML : '');

  card.innerHTML = keepHtml + rows.slice(0, 15).map(function(r, i) {
    return isTeams ? buildTeamRow(r, i) : buildPlayerRow(r, i);
  }).join('');
}

// ── Fetch rankings from API (with cache) ──────────────────────────────────────
var rankCache = {};

async function fetchRankings(category, fmt) {
  // Normalise fmt: 'test'→'Test', 'odi'→'ODI', 't20'→'T20I', 'T20I'→'T20I'
  var fmtNorm = fmt === 'T20I' || fmt === 't20i' ? 'T20I'
              : fmt === 'ODI'  || fmt === 'odi'  ? 'ODI'
              : fmt === 'Test' || fmt === 'test' ? 'Test'
              : fmt === 't20' || fmt === 'T20' ? 'T20I'
              : fmt;

  var key = category + '_' + fmtNorm;
  if (rankCache[key]) return rankCache[key];

  var data = await apiFetch('/api/icc-rankings?category=' + encodeURIComponent(category) + '&format=' + encodeURIComponent(fmtNorm));
  if (!data) {
    console.warn('fetchRankings: API returned null for', category, fmtNorm);
    rankCache[key] = [];
    return [];
  }
  var rows = (Array.isArray(data.rankings)) ? data.rankings : [];
  rankCache[key] = rows;
  return rows;
}

// ── Load all 4 category panels for a format ───────────────────────────────────
async function loadFormatPanels(fmt) {
  // fmt is e.g. 'test', 'odi', 't20' from data-fmt attribute
  var cats = ['batting', 'bowling', 'allrounder', 'teams'];
  for (var i = 0; i < cats.length; i++) {
    var cat    = cats[i];
    var panelId = fmt + '-' + cat;          // e.g. 'test-batting'
    var rows   = await fetchRankings(cat, fmt); // fmt normalised inside fetchRankings
    injectRankings(panelId, rows, cat === 'teams');
  }
}

// ── Sidebar: Current No.1s ────────────────────────────────────────────────────
async function updateSidebarNo1s() {
  var srrRows = document.querySelectorAll('.sidebar-rank-row');
  if (!srrRows.length) return;

  var pairs = [
    ['T20I','batting'], ['T20I','bowling'],
    ['ODI','batting'],  ['ODI','bowling'],
    ['Test','batting'], ['Test','bowling'],
  ];

  for (var i = 0; i < pairs.length && i < srrRows.length; i++) {
    var fmt = pairs[i][0];
    var cat = pairs[i][1];
    var rows = await fetchRankings(cat, fmt);
    if (!rows.length) continue;
    var no1 = rows[0];
    var row = srrRows[i];
    var name    = no1.player || no1.team || no1.name || '—';
    var country = no1.country || (no1.team ? no1.team : '');
    var code    = COUNTRY_ISO[country] || '';
    var nameEl  = row.querySelector('.srr-name');
    var subEl   = row.querySelector('.srr-sub');
    var ptsEl   = row.querySelector('.srr-pts');
    var flagEl  = row.querySelector('.srr-flag');
    if (nameEl) nameEl.textContent = name;
    if (subEl)  subEl.textContent  = fmt + ' ' + cat.charAt(0).toUpperCase() + cat.slice(1) + ' · ' + (no1.rating || '—');
    if (ptsEl)  ptsEl.textContent  = no1.rating || '—';
    if (flagEl && code) {
      flagEl.innerHTML = '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">';
    }
    if (row.tagName === 'A') row.href = (no1.player ? 'player-profile.html?name=' : 'team-profile.html?name=') + encodeURIComponent(name);
  }
}

function parseRankChange(change) {
  var s = String(change || '').trim();
  var m = s.match(/[-+]?\d+/);
  return m ? parseInt(m[0], 10) : 0;
}

function findSidebarCardByTitle(text) {
  var target = String(text || '').toLowerCase();
  var found = null;
  document.querySelectorAll('.sidebar-card').forEach(function(card) {
    if (found) return;
    var title = ((card.querySelector('.sidebar-card-title') || {}).textContent || '').toLowerCase();
    if (title.includes(target)) found = card;
  });
  return found;
}

function buildMoverRow(item) {
  var delta = item.delta || 0;
  var cls = delta >= 0 ? 'up' : 'down';
  var icon = delta >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
  var sign = delta > 0 ? '+' : '';
  var hrefBase = item.kind === 'team' ? 'team-profile.html?name=' : 'player-profile.html?name=';
  var flag = fl(item.country || item.name || '', 28);
  return '<a href="' + hrefBase + encodeURIComponent(item.name) + '" class="mover-row">'
    + '<span style="font-size:1.2rem;width:28px;height:28px;display:inline-flex;align-items:center;justify-content:center;overflow:hidden;border-radius:50%;">' + flag + '</span>'
    + '<div class="mover-info">'
      + '<div class="mover-name">' + esc(item.name) + '</div>'
      + '<div class="mover-sub">' + esc(item.sub) + '</div>'
    + '</div>'
    + '<span class="mover-change ' + cls + '"><i class="fa ' + icon + '"></i> ' + sign + delta + '</span>'
  + '</a>';
}

function buildTopTeamRow(entry, fmt) {
  var team = entry.team || entry.name || '—';
  var rating = entry.rating || '—';
  return '<a href="team-profile.html?name=' + encodeURIComponent(team) + '" class="sidebar-rank-row">'
    + '<span class="srr-pos" style="color:#FFD700;">★</span>'
    + '<span class="srr-flag" style="overflow:hidden;display:flex;align-items:center;justify-content:center;">' + fl(team, 24) + '</span>'
    + '<div class="srr-info">'
      + '<div class="srr-name">' + esc(team) + '</div>'
      + '<div class="srr-sub">' + esc(fmt) + ' · ' + esc(String(rating)) + ' rating</div>'
    + '</div>'
    + '<span class="srr-pts">' + esc(String(rating)) + '</span>'
  + '</a>';
}

async function updateSidebarMovers() {
  var moversCard = findSidebarCardByTitle('biggest movers');
  if (!moversCard) return;

  var sources = [
    ['Test', 'batting'], ['Test', 'bowling'],
    ['ODI', 'batting'],  ['ODI', 'bowling'],
    ['T20I', 'batting'], ['T20I', 'bowling'],
    ['T20I', 'teams']
  ];

  var movers = [];
  for (var i = 0; i < sources.length; i++) {
    var fmt = sources[i][0];
    var cat = sources[i][1];
    var rows = await fetchRankings(cat, fmt);
    rows.forEach(function(r) {
      var delta = parseRankChange(r.change);
      if (!delta) return;
      var isTeam = cat === 'teams';
      movers.push({
        name: isTeam ? (r.team || r.name || '') : (r.player || r.name || ''),
        country: isTeam ? (r.team || r.name || '') : (r.country || ''),
        delta: delta,
        kind: isTeam ? 'team' : 'player',
        sub: fmt + ' ' + (cat === 'teams' ? 'Teams' : (cat.charAt(0).toUpperCase() + cat.slice(1)))
      });
    });
  }

  movers.sort(function(a, b) { return Math.abs(b.delta) - Math.abs(a.delta); });
  var top = movers.slice(0, 5);

  var head = moversCard.querySelector('.sidebar-card-header');
  if (!top.length) {
    moversCard.innerHTML = (head ? head.outerHTML : '')
      + '<div style="padding:0.8rem 1.1rem;color:var(--text-muted);font-size:0.76rem;">No ranking movement available.</div>';
    return;
  }

  moversCard.innerHTML = (head ? head.outerHTML : '') + top.map(buildMoverRow).join('');
}

async function updateSidebarTopTeams() {
  var topTeamsCard = findSidebarCardByTitle('top teams');
  if (!topTeamsCard) return;

  var defs = [['Test', 'Test'], ['ODI', 'ODI'], ['T20I', 'T20I']];
  var rows = [];
  for (var i = 0; i < defs.length; i++) {
    var fmt = defs[i][0];
    var label = defs[i][1];
    var teams = await fetchRankings('teams', fmt);
    if (teams && teams.length) rows.push(buildTopTeamRow(teams[0], label));
  }

  var head = topTeamsCard.querySelector('.sidebar-card-header');
  if (!rows.length) {
    topTeamsCard.innerHTML = (head ? head.outerHTML : '')
      + '<div style="padding:0.8rem 1.1rem;color:var(--text-muted);font-size:0.76rem;">No team rankings available.</div>';
    return;
  }

  topTeamsCard.innerHTML = (head ? head.outerHTML : '') + rows.join('');
}

// ── Tab switching ─────────────────────────────────────────────────────────────
var loadedFormats = {};

function initTabs() {
  // Format tabs
  document.querySelectorAll('.format-tab[data-fmt]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var fmt = btn.dataset.fmt;  // 'test', 'odi', or 't20'
      if (!fmt) { console.warn('format-tab missing data-fmt'); return; }
      
      // Update format tab active state
      document.querySelectorAll('.format-tab').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      
      // Show/hide format panels
      document.querySelectorAll('.fmt-panel').forEach(function(p) { p.classList.remove('active'); });
      var panel = document.getElementById('fmt-' + fmt);
      if (!panel) { console.warn('fmt-panel not found for format:', fmt); return; }
      panel.classList.add('active');
      
      // Ensure batting category is active for this format
      var battingPanel = panel.querySelector('#' + fmt + '-batting');
      if (battingPanel) {
        panel.querySelectorAll('.cat-panel').forEach(function(p) { p.classList.remove('active'); });
        battingPanel.classList.add('active');
        document.querySelectorAll('.cs-btn').forEach(function(b) { b.classList.remove('active'); });
        document.querySelector('.cs-btn[data-cat="batting"]').classList.add('active');
      }
      
      // Load data if not already loaded
      if (!loadedFormats[fmt]) {
        loadedFormats[fmt] = true;
        loadFormatPanels(fmt);
      }
    });
  });

  // Category buttons
  document.querySelectorAll('.cs-btn[data-cat]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var cat = btn.dataset.cat;
      if (!cat) { console.warn('cs-btn missing data-cat'); return; }
      
      // Update category button active state
      document.querySelectorAll('.cs-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      
      // Show/hide category panels in active format panel
      var activeFmt = document.querySelector('.fmt-panel.active');
      if (!activeFmt) { console.warn('no .fmt-panel.active found'); return; }
      
      activeFmt.querySelectorAll('.cat-panel').forEach(function(p) { p.classList.remove('active'); });
      var fmtPrefix = activeFmt.id.replace('fmt-','');  // e.g. 'test' → 'test', 'odi' → 'odi'
      var catPanel = activeFmt.querySelector('#' + fmtPrefix + '-' + cat);
      if (!catPanel) { console.warn('cat-panel not found:', fmtPrefix + '-' + cat); return; }
      catPanel.classList.add('active');
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initTabs();
  loadedFormats['test'] = true;
  loadFormatPanels('test');
  updateSidebarNo1s();
  updateSidebarMovers();
  updateSidebarTopTeams();

  // Wire nav search (missing from rankings.html inline script)
  var navSearch = document.querySelector('.nav-search');
  if (navSearch) {
    navSearch.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && this.value.trim()) {
        window.location.href = 'search.html?q=' + encodeURIComponent(this.value.trim());
      }
    });
  }
});
