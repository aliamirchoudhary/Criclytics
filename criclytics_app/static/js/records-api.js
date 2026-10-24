/**
 * records-api.js
 * ==============
 * API wiring for records.html
 * Loads all-time records from /api/records (Cricsheet computed).
 *
 * HTML structure:
 *   .format-tab[data-fmt="test/odi/t20"]    — format switcher
 *   .cs-btn[data-cat="batting/bowling/team/partnership"] — category switcher
 *   #fmt-test, #fmt-odi, #fmt-t20           — format panels
 *   #test-batting, #odi-bowling etc.         — category panels
 *   .record-card inside each cat-panel       — each record table card
 */

function guessCountry(name) {
  // Try to match against known country names
  const n = (name || '').toLowerCase();
  for (const [country] of Object.entries(COUNTRY_ISO)) {
    if (n.includes(country.toLowerCase())) return country;
  }
  return '';
}

function flagImg(country, size) {
  size = size || 24;
  const code = COUNTRY_ISO[country] || country;
  if (!code) return '';
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;vertical-align:middle;" '
    + 'onerror="this.style.display=\'none\'">';
}

const medalClass = {1:'gold', 2:'silver', 3:'bronze'};

// ── Build player record row ───────────────────────────────────────────────────
function buildPlayerRow(entry, rank, stats) {
  var player  = entry.player || '—';
  var matches = entry.matches || '—';
  var medal   = medalClass[rank] || 'plain';
  // Country comes from entry.country if present (added by enrichment),
  // otherwise leave blank — never fall back to hardcoded 'IN'
  var country = entry.country || '';
  var code    = COUNTRY_ISO[country] || '';
  var flagHtml = code
    ? '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;" onerror="this.style.display=\'none\'">'
    : '<span style="width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:var(--surface-2);font-size:0.7rem;font-weight:700;color:var(--accent);">' + (player[0]||'?') + '</span>';

  var statsHtml = stats.map(function(s) {
    var cls = s.primary ? 'rec-stat primary' : s.green ? 'rec-stat green' : 'rec-stat';
    return '<span class="' + cls + '">' + esc(String(s.val == null ? '—' : s.val)) + '</span>';
  }).join('');

  return '<a href="player-profile.html?name=' + encodeURIComponent(player) + '" class="record-row">'
    + '<div class="rec-medal ' + medal + '">' + rank + '</div>'
    + '<span class="rec-flag">' + flagHtml + '</span>'
    + '<div class="rec-identity">'
      + '<div class="rec-name">' + esc(player) + '</div>'
      + '<div class="rec-sub">' + esc(String(matches)) + ' matches' + (country ? ' · ' + esc(country) : '') + '</div>'
    + '</div>'
    + statsHtml
  + '</a>';
}

// ── Build team record row ─────────────────────────────────────────────────────
function buildTeamRow(entry, rank, stats) {
  const team  = entry.player || entry.team || '—';
  const medal = medalClass[rank] || 'plain';
  const code  = COUNTRY_ISO[team] || '';

  const statsHtml = stats.map(function(s) {
    const cls = s.primary ? 'rec-stat primary' : s.green ? 'rec-stat green' : 'rec-stat';
    return '<span class="' + cls + '">' + esc(String(s.val || '—')) + '</span>';
  }).join('');

  return '<a href="team-profile.html?name=' + encodeURIComponent(team) + '" class="record-row">'
    + '<div class="rec-medal ' + medal + '">' + rank + '</div>'
    + '<span class="rec-flag">'
      + (code ? '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(team) + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;">' : '')
    + '</span>'
    + '<div class="rec-identity">'
      + '<div class="rec-name">' + esc(team) + '</div>'
    + '</div>'
    + statsHtml
  + '</a>';
}

// ── Inject into a record-card ─────────────────────────────────────────────────
function injectRecordCard(card, rows) {
  if (!card || !rows.length) return;
  const header = card.querySelector('.record-card-header');
  const rowHeader = card.querySelector('.record-row.header');
  const keepHtml = (header ? header.outerHTML : '') + (rowHeader ? rowHeader.outerHTML : '');
  card.innerHTML = keepHtml + rows.join('');
}

// ── Populate batting records ──────────────────────────────────────────────────
function populateBatting(panelId, data, fmtKey) {
  // fmtKey is the exact records.json key: 'Test', 'ODI', or 'T20I'
  // Derive it from panelId if not explicitly passed
  if (!fmtKey) {
    var p = panelId.split('-')[0]; // 'test', 'odi', or 't20'
    fmtKey = p === 't20' ? 'T20I' : p === 'test' ? 'Test' : 'ODI';
  }
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const cards = panel.querySelectorAll('.record-card');

  // Card 0: Most Runs
  const runsData = (data.most_runs && data.most_runs[fmtKey]) ? data.most_runs[fmtKey] : [];
  if (cards[0] && runsData.length) {
    const rows = runsData.slice(0,10).map(function(e, i) {
      return buildPlayerRow(e, i+1, [
        {val: e.runs, primary: true},
        {val: e.average},
        {val: e.hundreds, green: true}
      ]);
    });
    injectRecordCard(cards[0], rows);
  }

  // Card 1: Best Averages
  const avgData = (data.best_averages && data.best_averages[fmtKey]) ? data.best_averages[fmtKey] : [];
  if (cards[1] && avgData.length) {
    const rows = avgData.slice(0,10).map(function(e, i) {
      return buildPlayerRow(e, i+1, [
        {val: e.runs},
        {val: e.average, primary: true},
        {val: e.hundreds, green: true}
      ]);
    });
    injectRecordCard(cards[1], rows);
  }

  // Card 2: Most Centuries
  const hundredsData = (data.most_hundreds && data.most_hundreds[fmtKey]) ? data.most_hundreds[fmtKey] : [];
  if (cards[2] && hundredsData.length) {
    const rows = hundredsData.slice(0,10).map(function(e, i) {
      return buildPlayerRow(e, i+1, [
        {val: e.hundreds, primary: true},
        {val: e.fifties},
        {val: e.matches}
      ]);
    });
    injectRecordCard(cards[2], rows);
  }
}

// ── Populate bowling records ──────────────────────────────────────────────────
function populateBowling(panelId, data, fmtKey) {
  if (!fmtKey) {
    var p = panelId.split('-')[0];
    fmtKey = p === 't20' ? 'T20I' : p === 'test' ? 'Test' : 'ODI';
  }
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const cards = panel.querySelectorAll('.record-card');

  // Card 0: Most Wickets
  const wicketsData = (data.most_wickets && data.most_wickets[fmtKey]) ? data.most_wickets[fmtKey] : [];
  if (cards[0] && wicketsData.length) {
    const rows = wicketsData.slice(0,10).map(function(e, i) {
      return buildPlayerRow(e, i+1, [
        {val: e.wickets, primary: true},
        {val: e.average},
        {val: e.five_wkts, green: true}
      ]);
    });
    injectRecordCard(cards[0], rows);
  }
}

// ── Load all records ──────────────────────────────────────────────────────────
async function loadRecords() {
  const data = await apiFetch('/api/records');
  if (!data) return;

  // Populate all format panels
  // fmt is the HTML panel prefix: 'test', 'odi', 't20'
  // fmtKey is the exact key in records.json: 'Test', 'ODI', 'T20I'
  ['test','odi','t20'].forEach(function(fmt) {
    var fmtKey = fmt === 't20' ? 'T20I' : fmt === 'test' ? 'Test' : 'ODI';

    // Pass fmtKey (e.g. 'Test') as the data key — NOT fmt.toUpperCase() which gives 'TEST'/'T20'
    populateBatting(fmt + '-batting', {
      most_runs:     {[fmtKey]: data.most_runs?.[fmtKey]},
      best_averages: {[fmtKey]: data.best_averages?.[fmtKey]},
      most_hundreds: {[fmtKey]: data.most_hundreds?.[fmtKey]},
    });

    populateBowling(fmt + '-bowling', {
      most_wickets: {[fmtKey]: data.most_wickets?.[fmtKey]},
    });
  });

  // Update sidebar cards from explicit backend sidebar payload
  updateSidebarAllTimeBests(data);
  updateSidebarRecordsByCountry(data);
  updateSidebarRecentlyBroken(data);
}

function findSidebarCardByTitle(fragment) {
  var byId = {
    'all-time bests': 'records-all-time-bests',
    'records by country': 'records-by-country',
    'recently broken': 'records-recently-broken'
  };
  if (byId[fragment]) {
    var exact = document.getElementById(byId[fragment]);
    if (exact) return exact;
  }

  var cards = document.querySelectorAll('.sidebar-card');
  for (var i = 0; i < cards.length; i++) {
    var titleEl = cards[i].querySelector('.sidebar-card-title');
    var title = (titleEl ? titleEl.textContent : '').toLowerCase();
    if (title.indexOf(fragment.toLowerCase()) !== -1) return cards[i];
  }
  return null;
}

function sidebarRowHtml(opts) {
  var name = opts.name || '—';
  var sub = opts.sub || '—';
  var value = opts.value == null ? '—' : String(opts.value);
  var href = opts.href || '#';
  var country = opts.country || '';
  var valueColor = opts.valueColor || 'var(--accent)';
  var code = COUNTRY_ISO[country] || '';
  var fallbackInitial = (name[0] || '?').toUpperCase();
  var flag = code
    ? '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;">'
    : '<span style="width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:var(--surface-2);font-size:0.7rem;font-weight:700;color:var(--accent);">' + esc(fallbackInitial) + '</span>';

  return '<a href="' + href + '" class="sidebar-rec-row">'
    + '<span class="srec-flag">' + flag + '</span>'
    + '<div class="srec-info"><div class="srec-name">' + esc(name) + '</div><div class="srec-sub">' + esc(sub) + '</div></div>'
    + '<span class="srec-val" style="color:' + valueColor + ';">' + esc(value) + '</span>'
  + '</a>';
}

function updateSidebarAllTimeBests(data) {
  var card = findSidebarCardByTitle('all-time bests');
  if (!card) return;

  var header = card.querySelector('.sidebar-card-header');
  if (!header) return;

  var section = data.sidebar && Array.isArray(data.sidebar.all_time_bests) ? data.sidebar.all_time_bests : [];
  var rows = section.map(function(item) {
    var value = item && item.value;
    if (typeof value === 'number' && value >= 1000) value = value.toLocaleString();
    var name = (item && (item.name || item.player || item.country)) || '—';
    var isTeam = item && item.type === 'team';
    return sidebarRowHtml({
      name: name,
      sub: (item && (item.label || item.sub)) || '—',
      value: value,
      href: isTeam
        ? 'team-profile.html?name=' + encodeURIComponent(name)
        : 'player-profile.html?name=' + encodeURIComponent(name),
      country: (item && item.country) || ''
    });
  });

  if (!rows.length) {
    rows.push(sidebarRowHtml({ name: '—', sub: 'No records available', value: '—', href: '#', country: '' }));
  }
  card.innerHTML = header.outerHTML + rows.join('');
}

function updateSidebarRecordsByCountry(data) {
  var card = findSidebarCardByTitle('records by country');
  if (!card) return;

  var header = card.querySelector('.sidebar-card-header');
  if (!header) return;

  var section = data.sidebar && Array.isArray(data.sidebar.records_by_country) ? data.sidebar.records_by_country : [];
  var rows = section.map(function(item) {
    var country = (item && (item.country || item.name)) || '—';
    return sidebarRowHtml({
      name: country,
      sub: (item && (item.label || item.sub)) || '—',
      value: item && item.count,
      href: 'team-profile.html?name=' + encodeURIComponent(country),
      country: country
    });
  });

  if (!rows.length) {
    rows.push(sidebarRowHtml({ name: '—', sub: 'No country data available', value: '—', href: '#', country: '' }));
  }
  card.innerHTML = header.outerHTML + rows.join('');
}

function updateSidebarRecentlyBroken(data) {
  var card = findSidebarCardByTitle('recently broken');
  if (!card) return;

  var header = card.querySelector('.sidebar-card-header');
  if (!header) return;

  var section = data.sidebar && Array.isArray(data.sidebar.recently_broken) ? data.sidebar.recently_broken : [];
  var rows = section.map(function(item) {
    var name = (item && (item.name || item.player || item.country)) || '—';
    var isTeam = item && item.type === 'team';
    var value = item && item.value;
    if (typeof value === 'number' && value >= 1000) value = value.toLocaleString();
    return sidebarRowHtml({
      name: name,
      sub: (item && (item.label || item.sub)) || '—',
      value: value,
      href: isTeam
        ? 'team-profile.html?name=' + encodeURIComponent(name)
        : 'player-profile.html?name=' + encodeURIComponent(name),
      country: (item && item.country) || '',
      valueColor: 'var(--green-live)'
    });
  });

  if (!rows.length) {
    rows.push(sidebarRowHtml({ name: '—', sub: 'No recent updates available', value: '—', href: '#', country: '', valueColor: 'var(--green-live)' }));
  }
  card.innerHTML = header.outerHTML + rows.join('');
}

// ── Tab switching ─────────────────────────────────────────────────────────────
function initTabs() {
  document.querySelectorAll('.format-tab[data-fmt]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.format-tab').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      const fmt = btn.dataset.fmt;
      document.querySelectorAll('.fmt-panel').forEach(function(p) { p.classList.remove('active'); });
      const panel = document.getElementById('fmt-' + fmt);
      if (panel) panel.classList.add('active');
    });
  });

  document.querySelectorAll('.cs-btn[data-cat]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('.cs-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');
      const cat = btn.dataset.cat;
      const activeFmt = document.querySelector('.fmt-panel.active');
      if (!activeFmt) return;
      activeFmt.querySelectorAll('.cat-panel').forEach(function(p) { p.classList.remove('active'); });
      const catPanel = activeFmt.querySelector('.cat-panel[id$="-' + cat + '"]');
      if (catPanel) catPanel.classList.add('active');
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  initTabs();
  loadRecords();
});
