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
var activeCategory = 'batting';

function showCategoryForActiveFormat(cat) {
  var activeFmt = document.querySelector('.fmt-panel.active');
  if (!activeFmt) return;
  activeFmt.querySelectorAll('.cat-panel').forEach(function(p) { p.classList.remove('active'); });
  var fmtId = activeFmt.id.replace('fmt-', '');
  var catPanel = activeFmt.querySelector('#' + fmtId + '-' + cat);
  if (catPanel) catPanel.classList.add('active');
}

async function fetchRankings(category, fmt) {
  // Normalise fmt: 'test'→'Test', 'odi'→'ODI', 't20'→'T20I', 'T20I'→'T20I'
  var fmtNorm = fmt === 'T20I' || fmt === 't20i' ? 'T20I'
              : fmt === 'ODI'  || fmt === 'odi'  ? 'ODI'
              : fmt === 'Test' || fmt === 'test' ? 'Test'
              : fmt.toUpperCase() === 'T20' ? 'T20I' : fmt;

  var key = category + '_' + fmtNorm;
  if (rankCache[key]) return rankCache[key];

  var data = await apiFetch('/api/icc-rankings?category=' + category + '&format=' + fmtNorm);
  var rows = (data && Array.isArray(data.rankings)) ? data.rankings : [];
  rankCache[key] = rows;
  return rows;
}

// ── Load all 4 category panels for a format ───────────────────────────────────
async function loadFormatPanels(fmt) {
  // fmt is e.g. 'test', 'odi', 't20' from data-fmt attribute
  var cats = ['batting', 'bowling', 'allrounder', 'teams'];
  var tasks = cats.map(function(cat) {
    var panelId = fmt + '-' + cat;          // e.g. 'test-batting'
    return fetchRankings(cat, fmt).then(function(rows) {
      injectRankings(panelId, rows, cat === 'teams');
    });
  });
  await Promise.all(tasks);
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

async function updateSidebarTopTeams() {
  var teamRows = document.querySelectorAll('.sidebar-card');
  var teamCard = null;
  teamRows.forEach(function(card) {
    var title = (card.querySelector('.sidebar-card-title') || {}).textContent || '';
    if (title.toLowerCase().includes('top teams')) teamCard = card;
  });
  if (!teamCard) return;

  var fmts = ['Test', 'ODI', 'T20I'];
  var rows = [];
  for (var i = 0; i < fmts.length; i++) {
    var fmt = fmts[i];
    var data = await fetchRankings('teams', fmt);
    if (data && data.length) rows.push({ fmt: fmt, row: data[0] });
  }

  if (!rows.length) return;

  var header = teamCard.querySelector('.sidebar-card-header');
  teamCard.innerHTML = header ? header.outerHTML : '<div class="sidebar-card-header"><div class="sidebar-card-title"><i class="fa fa-shield-halved" style="color:#FFD700;"></i> Top Teams</div></div>';

  rows.forEach(function(entry) {
    var r = entry.row;
    var team = r.team || r.name || '—';
    var country = team;
    var code = COUNTRY_ISO[country] || '';
    var flag = code
      ? '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
      : '';
    var item = document.createElement('a');
    item.className = 'sidebar-rank-row';
    item.href = 'team-profile.html?name=' + encodeURIComponent(team);
    item.innerHTML = ''
      + '<span class="srr-pos" style="color:#FFD700;">★</span>'
      + '<span class="srr-flag" style="overflow:hidden;display:flex;align-items:center;justify-content:center;">' + flag + '</span>'
      + '<div class="srr-info">'
        + '<div class="srr-name">' + esc(team) + '</div>'
        + '<div class="srr-sub">' + esc(entry.fmt) + ' · ' + esc(String(r.rating || '—')) + ' rating</div>'
      + '</div>'
      + '<span class="srr-pts">' + esc(String(r.rating || '—')) + '</span>';
    teamCard.appendChild(item);
  });
}

function parseMovement(changeValue) {
  var raw = String(changeValue == null ? '' : changeValue).trim();
  var match = raw.match(/-?\d+/);
  if (!match) return { value: 0, text: '—' };
  var n = parseInt(match[0], 10);
  if (!Number.isFinite(n) || n === 0) return { value: 0, text: '—' };
  return { value: n, text: (n > 0 ? '+' : '') + n };
}

async function updateSidebarMovers() {
  var moverRows = document.querySelectorAll('.mover-row');
  if (!moverRows.length) return;

  var combos = [
    ['Test', 'batting'], ['Test', 'bowling'], ['Test', 'teams'],
    ['ODI', 'batting'],  ['ODI', 'bowling'],  ['ODI', 'teams'],
    ['T20I', 'batting'], ['T20I', 'bowling'], ['T20I', 'teams']
  ];

  var pool = [];
  for (var i = 0; i < combos.length; i++) {
    var fmt = combos[i][0];
    var cat = combos[i][1];
    var rows = await fetchRankings(cat, fmt);
    (rows || []).forEach(function(r) {
      var move = parseMovement(r.change);
      if (!move.value) return;
      var isTeam = cat === 'teams' || !!r.team;
      var name = isTeam ? (r.team || r.name || '') : (r.player || r.name || '');
      if (!name) return;
      pool.push({
        name: name,
        country: r.country || (isTeam ? name : ''),
        fmt: fmt,
        cat: cat,
        isTeam: isTeam,
        move: move,
      });
    });
  }

  pool.sort(function(a, b) {
    var ad = Math.abs(a.move.value);
    var bd = Math.abs(b.move.value);
    if (bd !== ad) return bd - ad;
    if ((a.move.value > 0) !== (b.move.value > 0)) return a.move.value > 0 ? -1 : 1;
    return a.name.localeCompare(b.name);
  });

  var seen = {};
  var movers = [];
  for (var j = 0; j < pool.length; j++) {
    var key = pool[j].name + '|' + pool[j].fmt + '|' + pool[j].cat;
    if (seen[key]) continue;
    seen[key] = true;
    movers.push(pool[j]);
    if (movers.length >= moverRows.length) break;
  }

  for (var k = 0; k < moverRows.length; k++) {
    var row = moverRows[k];
    var mover = movers[k];
    var nameEl = row.querySelector('.mover-name');
    var subEl = row.querySelector('.mover-sub');
    var changeEl = row.querySelector('.mover-change');
    var iconWrap = row.querySelector('span[style*="width:28px"]');

    if (!mover) {
      if (nameEl) nameEl.textContent = '—';
      if (subEl) subEl.textContent = '—';
      if (changeEl) {
        changeEl.className = 'mover-change';
        changeEl.innerHTML = '—';
      }
      row.href = '#';
      continue;
    }

    if (nameEl) nameEl.textContent = mover.name;
    if (subEl) subEl.textContent = mover.fmt + ' ' + (mover.cat === 'teams' ? 'Teams' : mover.cat.charAt(0).toUpperCase() + mover.cat.slice(1));

    if (changeEl) {
      var up = mover.move.value > 0;
      changeEl.className = 'mover-change ' + (up ? 'up' : 'down');
      changeEl.innerHTML = '<i class="fa ' + (up ? 'fa-arrow-up' : 'fa-arrow-down') + '"></i> ' + esc(mover.move.text);
    }

    var code = COUNTRY_ISO[mover.country] || '';
    if (iconWrap) {
      iconWrap.innerHTML = code
        ? '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(mover.country) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
        : '<span style="font-size:0.75rem;font-weight:700;color:var(--accent);">' + esc(mover.name.slice(0,2).toUpperCase()) + '</span>';
    }

    row.href = mover.isTeam
      ? 'team-profile.html?name=' + encodeURIComponent(mover.name)
      : 'player-profile.html?name=' + encodeURIComponent(mover.name);
  }
}

// ── Tab switching ─────────────────────────────────────────────────────────────
var loadedFormats = {};

function initTabs() {
  // Format tabs
  document.querySelectorAll('.format-tab[data-fmt]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      var fmt = btn.dataset.fmt;  // 'test', 'odi', or 't20'
      document.querySelectorAll('.format-tab').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      document.querySelectorAll('.fmt-panel').forEach(function(p) { p.classList.remove('active'); });
      var panel = document.getElementById('fmt-' + fmt);
      if (panel) panel.classList.add('active');
      showCategoryForActiveFormat(activeCategory);
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
      activeCategory = cat;
      document.querySelectorAll('.cs-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      showCategoryForActiveFormat(cat);
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initTabs();
  loadedFormats['test'] = true;
  loadedFormats['odi'] = true;
  loadedFormats['t20'] = true;
  Promise.all([
    loadFormatPanels('test'),
    loadFormatPanels('odi'),
    loadFormatPanels('t20'),
  ]);
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
