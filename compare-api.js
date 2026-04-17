/**
 * compare-api.js — complete rewrite
 * Intercepts selectItem/showResults from compare.html inline script.
 * Populates selectors with real player data, runs /api/compare/players,
 * updates every cell, bar, attribute row, probability block, summary.
 */

// ── State ─────────────────────────────────────────────────────────────────────
var selectedA = { name: 'V Kohli',   country: 'India',     mode: 'player' };
var selectedB = { name: 'S Smith',   country: 'Australia', mode: 'player' };
var compareMode = 'player'; // 'player' | 'team'
var activeFormatFilter = 'All Formats';

// ── Helpers ───────────────────────────────────────────────────────────────────
function flCircle2(country, size) {
  var code = COUNTRY_ISO[country] || '';
  if (!code) return '<div style="width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:var(--surface-2);display:flex;align-items:center;justify-content:center;font-size:0.7rem;font-weight:700;color:var(--accent);">' + (country||'?').slice(0,2) + '</div>';
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;vertical-align:middle;" onerror="this.style.display=\'none\'">';
}

// ── Override inline selectItem ────────────────────────────────────────────────
window.selectItem = function(side, el, name, flag, meta) {
  var list = document.getElementById('list-' + side);
  if (list) list.querySelectorAll('.selector-item').forEach(function(i) { i.classList.remove('selected'); });
  el.classList.add('selected');

  // Extract country from meta string like "India · Batsman"
  var parts = (meta || '').split('·');
  var country = parts[0].trim();
  var role    = (parts[1] || '').trim();

  // Update preview
  var preview = document.getElementById('preview-' + side);
  if (preview) {
    preview.innerHTML = '<div class="selected-preview-avatar" style="overflow:hidden;">' + flCircle2(country, 52) + '</div><span>' + esc(name) + '</span>';
  }

  // Store selection
  if (side === 'a') { selectedA = { name: name, country: country, role: role, mode: compareMode }; }
  else              { selectedB = { name: name, country: country, role: role, mode: compareMode }; }
};

// ── Override inline showResults ───────────────────────────────────────────────
window.showResults = function() {
  var r = document.getElementById('compare-results');
  if (r) { r.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
  if (compareMode === 'team') runTeamComparison();
  else                        runPlayerComparison();
};

// ── Override setTab to track active format ────────────────────────────────────
window.setTab = function(btn) {
  btn.closest('.tabs').querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
  btn.classList.add('active');
  activeFormatFilter = btn.textContent.trim();
};

// ── Override switchMode ───────────────────────────────────────────────────────
window.switchMode = function(mode, btn) {
  document.querySelectorAll('.type-btn').forEach(function(b) { b.classList.remove('active'); });
  btn.classList.add('active');
  compareMode = mode;

  var isTeam = (mode === 'team');
  document.querySelectorAll('.selector-label span').forEach(function(el, i) {
    el.textContent = isTeam ? (i === 0 ? 'Team A' : 'Team B') : (i === 0 ? 'Player A' : 'Player B');
  });

  var listA = document.getElementById('list-a');
  var listB = document.getElementById('list-b');
  if (!listA || !listB) return;

  if (isTeam) {
    // Populate with teams from API
    apiFetch('/api/teams').then(function(data) {
      if (!data) return;
      var teams = Object.keys(data).sort();
      var html = teams.map(function(t, i) {
        var iso = COUNTRY_ISO[t] || '';
        var flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(t) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' : '';
        return '<div class="selector-item' + (i === 0 ? ' selected' : i === 1 ? ' selected' : '') + '" onclick="selectItem(\'' + (listA === document.getElementById('list-a') ? 'a' : 'b') + '\', this, \'' + esc(t) + '\', \'\', \'' + esc(t) + ' ·\')">'
          + '<div class="selector-item-avatar" style="overflow:hidden;">' + flagHtml + '</div>'
          + '<div class="selector-item-info"><div class="selector-item-name">' + esc(t) + '</div><div class="selector-item-meta">International Team</div></div>'
          + '<div class="selector-item-check"><i class="fa-solid fa-check"></i></div>'
        + '</div>';
      }).join('');
      listA.innerHTML = html;
      listB.innerHTML = html;
      // Reset onclick with correct side
      listA.querySelectorAll('.selector-item').forEach(function(item, i) {
        var tname = teams[i];
        item.onclick = function() { window.selectItem('a', item, tname, '', tname + ' ·'); };
      });
      listB.querySelectorAll('.selector-item').forEach(function(item, i) {
        var tname = teams[i];
        item.onclick = function() { window.selectItem('b', item, tname, '', tname + ' ·'); };
      });
      if (teams[0]) selectedA = { name: teams[0], country: teams[0], mode: 'team' };
      if (teams[1]) selectedB = { name: teams[1], country: teams[1], mode: 'team' };
    });
  } else {
    // Restore player list from API
    populatePlayerSelectors();
  }
};

// ── Populate player selectors from API ────────────────────────────────────────
async function populatePlayerSelectors() {
  var data = await apiFetch('/api/players?limit=100&sort=runs');
  if (!data || !data.players) return;

  var players = data.players.slice(0, 30);
  var html = players.map(function(p) {
    var country = p.country || '';
    var iso = COUNTRY_ISO[country] || '';
    var flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(country) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' : '';
    var metaStr = esc(country) + ' ·';
    return '<div class="selector-item" data-name="' + esc(p.name) + '" data-country="' + esc(country) + '">'
      + '<div class="selector-item-avatar" style="overflow:hidden;">' + flagHtml + '</div>'
      + '<div class="selector-item-info"><div class="selector-item-name">' + esc(p.name) + '</div><div class="selector-item-meta">' + esc(country) + '</div></div>'
      + '<div class="selector-item-check"><i class="fa-solid fa-check"></i></div>'
    + '</div>';
  }).join('');

  ['a','b'].forEach(function(side) {
    var list = document.getElementById('list-' + side);
    if (!list) return;
    list.innerHTML = html;

    // Wire clicks
    list.querySelectorAll('.selector-item').forEach(function(item) {
      var pname   = item.dataset.name;
      var country = item.dataset.country;
      item.addEventListener('click', function() {
        window.selectItem(side, item, pname, '', country + ' ·');
      });
    });

    // Wire search
    var card = list.closest('.selector-card');
    var searchInput = card && card.querySelector('.search-input');
    if (searchInput) {
      searchInput.addEventListener('input', function() {
        var q = this.value.toLowerCase();
        list.querySelectorAll('.selector-item').forEach(function(item) {
          var name = (item.dataset.name || '').toLowerCase();
          item.style.display = (!q || name.includes(q)) ? '' : 'none';
        });
      });
    }
  });

  // Set defaults from existing selectedA/B state
  setDefaultSelected('a', selectedA.name);
  setDefaultSelected('b', selectedB.name);
}

function setDefaultSelected(side, name) {
  var list = document.getElementById('list-' + side);
  if (!list) return;
  var found = false;
  list.querySelectorAll('.selector-item').forEach(function(item) {
    item.classList.remove('selected');
    if (!found && item.dataset.name && item.dataset.name.toLowerCase().includes(name.toLowerCase().split(' ').pop())) {
      item.classList.add('selected');
      found = true;
    }
  });
}

// ── Player comparison ─────────────────────────────────────────────────────────
async function runPlayerComparison() {
  if (!selectedA.name || !selectedB.name) return;

  // Loading state
  var grid = document.querySelector('.compare-stat-grid');
  if (grid) grid.style.opacity = '0.5';

  var data = await apiFetch('/api/compare/players?player_a=' + encodeURIComponent(selectedA.name) + '&player_b=' + encodeURIComponent(selectedB.name));

  if (grid) grid.style.opacity = '1';
  if (!data) return;

  var a = data.player_a || {};
  var b = data.player_b || {};

  // ── Update panel headers ──────────────────────────────────────────────────
  var names   = document.querySelectorAll('.cph-name');
  var metas   = document.querySelectorAll('.cph-meta');
  var avatars = document.querySelectorAll('.cph-avatar');
  if (names[0])   names[0].textContent   = selectedA.name;
  if (names[1])   names[1].textContent   = selectedB.name;
  if (metas[0])   metas[0].textContent   = selectedA.country + (selectedA.role ? ' · ' + selectedA.role : '');
  if (metas[1])   metas[1].textContent   = selectedB.country + (selectedB.role ? ' · ' + selectedB.role : '');
  if (avatars[0]) { avatars[0].innerHTML = flCircle2(selectedA.country, 52); }
  if (avatars[1]) { avatars[1].innerHTML = flCircle2(selectedB.country, 52); }

  // ── Aggregate stats ───────────────────────────────────────────────────────
  var fmt = activeFormatFilter === 'All Formats' ? null
          : activeFormatFilter === 'Test'  ? 'Test'
          : activeFormatFilter === 'ODI'   ? 'ODI'
          : 'T20I';

  function aggBat(p) {
    var out = { runs:0, innings:0, not_outs:0, hundreds:0, fifties:0, matches:0, highest:'', avg:0, sr:0 };
    var fmts = fmt ? [fmt] : ['Test','ODI','T20I'];
    fmts.forEach(function(f) {
      var s = (p.batting||{})[f] || {};
      out.runs     += s.runs      || 0;
      out.innings  += s.innings   || 0;
      out.not_outs += s.not_outs  || 0;
      out.hundreds += s.hundreds  || 0;
      out.fifties  += s.fifties   || 0;
      out.matches  += s.matches   || 0;
      if (!out.highest || (s.highest && String(s.highest).replace('*','') > String(out.highest).replace('*',''))) out.highest = s.highest || '';
    });
    var dis = out.innings - out.not_outs;
    out.avg = dis > 0 ? (out.runs / dis).toFixed(1) : '—';
    // SR from ODI
    out.sr = ((p.batting||{})[fmt||'ODI']||{}).strike_rate || '—';
    return out;
  }

  var aAgg = aggBat(a); var bAgg = aggBat(b);
  var aTest = (a.batting||{})['Test']||{}; var bTest = (b.batting||{})['Test']||{};
  var aODI  = (a.batting||{})['ODI'] ||{}; var bODI  = (b.batting||{})['ODI'] ||{};
  var aT20  = (a.batting||{})['T20I']||{}; var bT20  = (b.batting||{})['T20I']||{};

  // ── Update flat grid cells ────────────────────────────────────────────────
  var statMap = {
    'Matches':       [aAgg.matches, bAgg.matches],
    'Innings':       [aAgg.innings, bAgg.innings],
    'Runs':          [aAgg.runs,    bAgg.runs],
    'Batting Avg':   [aAgg.avg,     bAgg.avg],
    'Strike Rate':   [aAgg.sr,      bAgg.sr],
    '100s / 50s':    [aAgg.hundreds + ' / ' + aAgg.fifties, bAgg.hundreds + ' / ' + bAgg.fifties],
    'Highest Score': [aAgg.highest || '—', bAgg.highest || '—'],
    'Not Outs':      [aAgg.not_outs, bAgg.not_outs],
    'Test Avg':      [aTest.average ? Number(aTest.average).toFixed(1) : '—', bTest.average ? Number(bTest.average).toFixed(1) : '—'],
    'Test Runs':     [aTest.runs || '—', bTest.runs || '—'],
    'Test 100s':     [aTest.hundreds || '—', bTest.hundreds || '—'],
    'ODI Avg':       [aODI.average  ? Number(aODI.average).toFixed(1)  : '—', bODI.average  ? Number(bODI.average).toFixed(1)  : '—'],
    'ODI Runs':      [aODI.runs  || '—', bODI.runs  || '—'],
    'ODI 100s':      [aODI.hundreds || '—', bODI.hundreds || '—'],
    'T20I Avg':      [aT20.average  ? Number(aT20.average).toFixed(1)  : '—', bT20.average  ? Number(bT20.average).toFixed(1)  : '—'],
    'T20I SR':       [aT20.strike_rate ? Number(aT20.strike_rate).toFixed(1) : '—', bT20.strike_rate ? Number(bT20.strike_rate).toFixed(1) : '—'],
    'T20I Runs':     [aT20.runs || '—', bT20.runs || '—'],
  };

  if (grid) {
    var children = Array.from(grid.children);
    var i = 0;
    while (i < children.length) {
      var el = children[i];
      if (el.classList.contains('compare-section-row')) { i++; continue; }
      if (el.classList.contains('compare-row-label')) {
        var label = el.textContent.trim();
        var vals  = statMap[label];
        var cellA = children[i+1];
        var cellB = children[i+2];
        if (vals && cellA && cellB) {
          var nA = parseFloat(String(vals[0]).replace(/[^0-9.]/g,''));
          var nB = parseFloat(String(vals[1]).replace(/[^0-9.]/g,''));
          var aW = !isNaN(nA) && !isNaN(nB) && nA > nB;
          var bW = !isNaN(nA) && !isNaN(nB) && nB > nA;
          cellA.textContent = vals[0] == null || vals[0] === '' ? '—' : String(vals[0]);
          cellB.textContent = vals[1] == null || vals[1] === '' ? '—' : String(vals[1]);
          cellA.className = 'compare-cell' + (aW ? ' winner' : bW ? ' loser' : '');
          cellB.className = 'compare-cell' + (bW ? ' winner' : aW ? ' loser' : '');
        }
        i += 3;
      } else { i++; }
    }
  }

  // ── Bar rows ──────────────────────────────────────────────────────────────
  var barData = [
    { aVal: parseFloat(aAgg.avg)||0,     bVal: parseFloat(bAgg.avg)||0,     max: 80  },
    { aVal: parseFloat(aT20.strike_rate)||0, bVal: parseFloat(bT20.strike_rate)||0, max: 180 },
    { aVal: aAgg.hundreds,                bVal: bAgg.hundreds,               max: 100 },
    { aVal: parseFloat(aODI.average)||0,  bVal: parseFloat(bODI.average)||0, max: 80  },
    { aVal: parseFloat(aTest.average)||0, bVal: parseFloat(bTest.average)||0, max: 80  },
  ];
  document.querySelectorAll('.bar-compare-row').forEach(function(row, i) {
    if (!barData[i]) return;
    var bd = barData[i];
    var fillA = row.querySelector('.bar-fill-a,.bar-compare-fill.bar-fill-a');
    var fillB = row.querySelector('.bar-fill-b,.bar-compare-fill.bar-fill-b');
    var spans = row.querySelectorAll('[style*="color"]');
    var pA = bd.max > 0 ? Math.min(Math.round((bd.aVal/bd.max)*100), 100) : 0;
    var pB = bd.max > 0 ? Math.min(Math.round((bd.bVal/bd.max)*100), 100) : 0;
    if (fillA) fillA.style.width = pA + '%';
    if (fillB) fillB.style.width = pB + '%';
    if (spans[0]) spans[0].textContent = bd.aVal || '—';
    if (spans[1]) spans[1].textContent = bd.bVal || '—';
  });

  // ── Attribute breakdown ───────────────────────────────────────────────────
  var attrData = [
    { name:'ODI Form',    aScore: aODI.average ? Math.min(99, Math.round(aODI.average * 1.5)) : 0,    bScore: bODI.average ? Math.min(99, Math.round(bODI.average * 1.5)) : 0 },
    { name:'Test Form',   aScore: aTest.average ? Math.min(99, Math.round(aTest.average * 1.4)) : 0,  bScore: bTest.average ? Math.min(99, Math.round(bTest.average * 1.4)) : 0 },
    { name:'T20 Form',    aScore: aT20.average ? Math.min(99, Math.round(aT20.average * 2)) : 0,      bScore: bT20.average ? Math.min(99, Math.round(bT20.average * 2)) : 0 },
    { name:'Consistency', aScore: aAgg.avg !== '—' ? Math.min(99, Math.round(parseFloat(aAgg.avg))) : 0, bScore: bAgg.avg !== '—' ? Math.min(99, Math.round(parseFloat(bAgg.avg))) : 0 },
    { name:'Big Match',   aScore: aODI.hundreds ? Math.min(99, aODI.hundreds * 2 + 40) : 40,         bScore: bODI.hundreds ? Math.min(99, bODI.hundreds * 2 + 40) : 40 },
    { name:'Away Record', aScore: Math.min(99, Math.round((aAgg.runs || 0) / 150) + 30),              bScore: Math.min(99, Math.round((bAgg.runs || 0) / 150) + 30) },
  ];

  document.querySelectorAll('.radar-attr-row').forEach(function(row, i) {
    if (!attrData[i]) return;
    var ad = attrData[i];
    var valA = row.querySelector('.radar-val-a');
    var valB = row.querySelector('.radar-val-b');
    var fillA = row.querySelector('.radar-fill-a');
    var fillB = row.querySelector('.radar-fill-b');
    if (valA)  valA.textContent  = ad.aScore + '/100';
    if (valB)  valB.textContent  = ad.bScore + '/100';
    if (fillA) fillA.style.width = ad.aScore + '%';
    if (fillB) fillB.style.width = ad.bScore + '%';
  });

  // ── Probability Insights ──────────────────────────────────────────────────
  var probBlocks = document.querySelectorAll('.prob-block');
  if (probBlocks[0] && probBlocks[1]) {
    // Block A
    var aInnings = aAgg.innings || 1;
    var aProbs = [
      { name:'Scoring 50+ in ODIs',  pct: aODI.fifties  ? Math.min(80, Math.round((aODI.fifties + (aODI.hundreds||0)) / Math.max(aODI.innings||1, 1) * 100)) : 30 },
      { name:'Scoring 30+ in T20Is', pct: aT20.fifties  ? Math.min(75, Math.round(aT20.fifties / Math.max(aT20.innings||1, 1) * 100 + 30)) : 35 },
      { name:'Century in Tests',     pct: aTest.hundreds ? Math.min(50, Math.round(aTest.hundreds / Math.max(aTest.innings||1, 1) * 100)) : 15 },
      { name:'Top scorer in match',  pct: Math.min(55, Math.round(((aAgg.hundreds || 0) + (aAgg.fifties || 0)) / Math.max(aInnings, 1) * 150)) },
    ];
    updateProbBlock(probBlocks[0], selectedA.name, selectedA.country, aProbs);

    // Block B
    var bInnings = bAgg.innings || 1;
    var bProbs = [
      { name:'Scoring 50+ in ODIs',  pct: bODI.fifties  ? Math.min(80, Math.round((bODI.fifties + (bODI.hundreds||0)) / Math.max(bODI.innings||1, 1) * 100)) : 30 },
      { name:'Scoring 30+ in T20Is', pct: bT20.fifties  ? Math.min(75, Math.round(bT20.fifties / Math.max(bT20.innings||1, 1) * 100 + 30)) : 35 },
      { name:'Century in Tests',     pct: bTest.hundreds ? Math.min(50, Math.round(bTest.hundreds / Math.max(bTest.innings||1, 1) * 100)) : 15 },
      { name:'Top scorer in match',  pct: Math.min(55, Math.round(((bAgg.hundreds || 0) + (bAgg.fifties || 0)) / Math.max(bInnings, 1) * 150)) },
    ];
    updateProbBlock(probBlocks[1], selectedB.name, selectedB.country, bProbs, true);
  }

  // ── Attribute breakdown legend names (two places: selector panel + radar section) ──
  var legendA = document.getElementById('legend-a-label');
  var legendB = document.getElementById('legend-b-label');
  if (legendA) legendA.textContent = selectedA.name;
  if (legendB) legendB.textContent = selectedB.name;

  // The radar section has a separate set of legend-item divs with hardcoded text nodes
  var radarLegendItems = document.querySelectorAll('.radar-section .legend-item');
  if (radarLegendItems[0]) {
    var dotA = radarLegendItems[0].querySelector('.legend-dot');
    radarLegendItems[0].innerHTML = (dotA ? dotA.outerHTML : '<div class="legend-dot legend-dot-a"></div>') + ' ' + esc(selectedA.name);
  }
  if (radarLegendItems[1]) {
    var dotB = radarLegendItems[1].querySelector('.legend-dot');
    radarLegendItems[1].innerHTML = (dotB ? dotB.outerHTML : '<div class="legend-dot legend-dot-b"></div>') + ' ' + esc(selectedB.name);
  }

  // ── Summary card ──────────────────────────────────────────────────────────
  var summaryTitle   = document.querySelector('.summary-title');
  var summaryText    = document.querySelector('.summary-text');
  var summaryVerdict = document.querySelector('.summary-verdict');
  if (summaryTitle)   summaryTitle.textContent   = selectedA.name + ' vs ' + selectedB.name;
  var aRunsTotal = aAgg.runs || 0;
  var bRunsTotal = bAgg.runs || 0;
  var aAvgNum = parseFloat(aAgg.avg) || 0;
  var bAvgNum = parseFloat(bAgg.avg) || 0;
  var aWins   = aAvgNum > bAvgNum;
  if (summaryText) {
    summaryText.textContent = 'Comparing '
      + (fmt || 'all formats') + '. '
      + selectedA.name + ' has ' + aRunsTotal.toLocaleString() + ' runs (avg ' + aAgg.avg + ') vs '
      + selectedB.name + '\'s ' + bRunsTotal.toLocaleString() + ' runs (avg ' + bAgg.avg + ').';
  }
  if (summaryVerdict) {
    summaryVerdict.textContent = aWins ? selectedA.name + ' edges overall' : selectedB.name + ' edges overall';
    summaryVerdict.className = 'summary-verdict ' + (aWins ? 'verdict-a' : 'verdict-b');
  }
}

function updateProbBlock(block, name, country, probs, isB) {
  var headerIcon = block.querySelector('.prob-icon');
  var headerLabel = block.querySelector('.prob-label');
  if (headerIcon) headerIcon.innerHTML = flCircle2(country, 28);
  if (headerLabel) {
    headerLabel.textContent = name + ' — Likelihoods';
    if (isB) headerLabel.style.color = '#FF7043';
  }
  var probRows = block.querySelectorAll('.prob-row');
  probs.forEach(function(p, i) {
    var row = probRows[i];
    if (!row) return;
    var nameEl = row.querySelector('.prob-row-name');
    var valEl  = row.querySelector('.prob-row-val');
    var fillEl = row.querySelector('.prob-bar-fill');
    if (nameEl) nameEl.textContent = p.name;
    if (valEl)  { valEl.textContent = p.pct + '%'; if (isB) valEl.style.color = '#FF7043'; }
    if (fillEl) fillEl.style.width = p.pct + '%';
  });
  var disclaimer = block.querySelector('.prob-disclaimer');
  if (disclaimer) disclaimer.textContent = 'Based on career data. Statistical likelihood from historical performance patterns.';
}

// ── Team comparison ───────────────────────────────────────────────────────────
async function runTeamComparison() {
  var nameA = selectedA.name; var nameB = selectedB.name;
  if (!nameA || !nameB) return;

  var dataA = await apiFetch('/api/teams/' + encodeURIComponent(nameA));
  var dataB = await apiFetch('/api/teams/' + encodeURIComponent(nameB));
  if (!dataA || !dataB) return;

  var fmt = activeFormatFilter === 'All Formats' ? 'T20I' : activeFormatFilter;
  var sA = (dataA.format_stats || {})[fmt] || {};
  var sB = (dataB.format_stats || {})[fmt] || {};

  // ── Headers ───────────────────────────────────────────────────────────────
  var names   = document.querySelectorAll('.cph-name');
  var metas   = document.querySelectorAll('.cph-meta');
  var avatars = document.querySelectorAll('.cph-avatar');
  if (names[0])   names[0].textContent   = nameA;
  if (names[1])   names[1].textContent   = nameB;
  if (metas[0])   metas[0].textContent   = nameA + ' · International Cricket';
  if (metas[1])   metas[1].textContent   = nameB + ' · International Cricket';
  if (avatars[0]) avatars[0].innerHTML   = flCircle2(nameA, 52);
  if (avatars[1]) avatars[1].innerHTML   = flCircle2(nameB, 52);

  // ── Legend labels (Attribute Breakdown section) ───────────────────────────
  var legendA = document.getElementById('legend-a-label');
  var legendB = document.getElementById('legend-b-label');
  if (legendA) legendA.textContent = nameA;
  if (legendB) legendB.textContent = nameB;

  // Radar section separate legend-item divs (hardcoded text nodes)
  var radarLegendItems = document.querySelectorAll('.radar-section .legend-item');
  if (radarLegendItems[0]) {
    var dotA = radarLegendItems[0].querySelector('.legend-dot');
    radarLegendItems[0].innerHTML = (dotA ? dotA.outerHTML : '<div class="legend-dot legend-dot-a"></div>') + ' ' + esc(nameA);
  }
  if (radarLegendItems[1]) {
    var dotB = radarLegendItems[1].querySelector('.legend-dot');
    radarLegendItems[1].innerHTML = (dotB ? dotB.outerHTML : '<div class="legend-dot legend-dot-b"></div>') + ' ' + esc(nameB);
  }

  // ── Stat grid (reuse row labels, put team stats in) ───────────────────────
  var statMap = {
    'Matches':       [sA.matches||'—',  sB.matches||'—'],
    'Innings':       [sA.matches||'—',  sB.matches||'—'],
    'Runs':          ['—',              '—'],
    'Batting Avg':   [sA.win_pct ? sA.win_pct+'% wins' : '—', sB.win_pct ? sB.win_pct+'% wins' : '—'],
    'Strike Rate':   ['—',              '—'],
    '100s / 50s':    ['—',              '—'],
    'Highest Score': ['—',              '—'],
    'Not Outs':      ['—',              '—'],
    'Test Avg':      [(dataA.format_stats||{})['Test'] ? ((dataA.format_stats['Test'].win_pct||0)+'% wins') : '—',
                     (dataB.format_stats||{})['Test'] ? ((dataB.format_stats['Test'].win_pct||0)+'% wins') : '—'],
    'Test Runs':     [(dataA.format_stats||{})['Test'] ? ((dataA.format_stats['Test'].matches||0)+' matches') : '—',
                     (dataB.format_stats||{})['Test'] ? ((dataB.format_stats['Test'].matches||0)+' matches') : '—'],
    'Test 100s':     ['—','—'],
    'ODI Avg':       [(dataA.format_stats||{})['ODI'] ? ((dataA.format_stats['ODI'].win_pct||0)+'% wins') : '—',
                     (dataB.format_stats||{})['ODI'] ? ((dataB.format_stats['ODI'].win_pct||0)+'% wins') : '—'],
    'ODI Runs':      [(dataA.format_stats||{})['ODI'] ? ((dataA.format_stats['ODI'].matches||0)+' matches') : '—',
                     (dataB.format_stats||{})['ODI'] ? ((dataB.format_stats['ODI'].matches||0)+' matches') : '—'],
    'ODI 100s':      ['—','—'],
    'T20I Avg':      [(dataA.format_stats||{})['T20I'] ? ((dataA.format_stats['T20I'].win_pct||0)+'% wins') : '—',
                     (dataB.format_stats||{})['T20I'] ? ((dataB.format_stats['T20I'].win_pct||0)+'% wins') : '—'],
    'T20I SR':       ['—','—'],
    'T20I Runs':     [(dataA.format_stats||{})['T20I'] ? ((dataA.format_stats['T20I'].matches||0)+' matches') : '—',
                     (dataB.format_stats||{})['T20I'] ? ((dataB.format_stats['T20I'].matches||0)+' matches') : '—'],
  };

  var grid = document.querySelector('.compare-stat-grid');
  if (grid) {
    var children = Array.from(grid.children);
    var i = 0;
    while (i < children.length) {
      var el = children[i];
      if (el.classList.contains('compare-section-row')) { i++; continue; }
      if (el.classList.contains('compare-row-label')) {
        var label = el.textContent.trim();
        var vals  = statMap[label];
        var cellA = children[i+1]; var cellB = children[i+2];
        if (vals && cellA && cellB) {
          cellA.textContent = String(vals[0]); cellA.className = 'compare-cell';
          cellB.textContent = String(vals[1]); cellB.className = 'compare-cell';
        }
        i += 3;
      } else { i++; }
    }
  }

  // ── Bar rows — show win % as bars ─────────────────────────────────────────
  var aWinPct = sA.win_pct || 0;
  var bWinPct = sB.win_pct || 0;
  var barDataTeam = [
    { aVal: aWinPct, bVal: bWinPct, max: 100 },
    { aVal: (dataA.format_stats||{})['T20I'] ? ((dataA.format_stats['T20I'].win_pct)||0) : 0,
      bVal: (dataB.format_stats||{})['T20I'] ? ((dataB.format_stats['T20I'].win_pct)||0) : 0, max: 100 },
    { aVal: sA.matches||0, bVal: sB.matches||0, max: Math.max(sA.matches||1, sB.matches||1, 1)*1.2 },
    { aVal: (dataA.format_stats||{})['ODI'] ? ((dataA.format_stats['ODI'].win_pct)||0) : 0,
      bVal: (dataB.format_stats||{})['ODI'] ? ((dataB.format_stats['ODI'].win_pct)||0) : 0, max: 100 },
    { aVal: (dataA.format_stats||{})['Test'] ? ((dataA.format_stats['Test'].win_pct)||0) : 0,
      bVal: (dataB.format_stats||{})['Test'] ? ((dataB.format_stats['Test'].win_pct)||0) : 0, max: 100 },
  ];
  document.querySelectorAll('.bar-compare-row').forEach(function(row, i) {
    if (!barDataTeam[i]) return;
    var bd = barDataTeam[i];
    var fillA = row.querySelector('.bar-fill-a,.bar-compare-fill.bar-fill-a');
    var fillB = row.querySelector('.bar-fill-b,.bar-compare-fill.bar-fill-b');
    var spans = row.querySelectorAll('[style*="color"]');
    var pA = bd.max > 0 ? Math.min(Math.round((bd.aVal/bd.max)*100),100) : 0;
    var pB = bd.max > 0 ? Math.min(Math.round((bd.bVal/bd.max)*100),100) : 0;
    if (fillA) fillA.style.width = pA + '%';
    if (fillB) fillB.style.width = pB + '%';
    if (spans[0]) spans[0].textContent = bd.aVal ? (Math.round(bd.aVal*10)/10) : '—';
    if (spans[1]) spans[1].textContent = bd.bVal ? (Math.round(bd.bVal*10)/10) : '—';
  });

  // ── Attribute breakdown bars ──────────────────────────────────────────────
  var attrTeam = [
    { aScore: aWinPct, bScore: bWinPct },
    { aScore: (dataA.format_stats||{})['Test'] ? ((dataA.format_stats['Test'].win_pct)||0) : 0,
      bScore: (dataB.format_stats||{})['Test'] ? ((dataB.format_stats['Test'].win_pct)||0) : 0 },
    { aScore: (dataA.format_stats||{})['T20I'] ? ((dataA.format_stats['T20I'].win_pct)||0) : 0,
      bScore: (dataB.format_stats||{})['T20I'] ? ((dataB.format_stats['T20I'].win_pct)||0) : 0 },
    { aScore: Math.min(99, (sA.matches||0)/2), bScore: Math.min(99, (sB.matches||0)/2) },
    { aScore: aWinPct * 0.9, bScore: bWinPct * 0.9 },
    { aScore: aWinPct * 0.8, bScore: bWinPct * 0.8 },
  ];
  document.querySelectorAll('.radar-attr-row').forEach(function(row, i) {
    if (!attrTeam[i]) return;
    var ad = attrTeam[i];
    var aS = Math.round(ad.aScore); var bS = Math.round(ad.bScore);
    var valA = row.querySelector('.radar-val-a'); var valB = row.querySelector('.radar-val-b');
    var fillA = row.querySelector('.radar-fill-a'); var fillB = row.querySelector('.radar-fill-b');
    if (valA)  valA.textContent  = aS + '/100';
    if (valB)  valB.textContent  = bS + '/100';
    if (fillA) fillA.style.width = aS + '%';
    if (fillB) fillB.style.width = bS + '%';
  });

  // ── Probability blocks — update headers with team names ───────────────────
  var probBlocks = document.querySelectorAll('.prob-block');
  if (probBlocks[0]) {
    var hdrA = probBlocks[0].querySelector('.prob-icon');
    var lblA = probBlocks[0].querySelector('.prob-label');
    if (hdrA) hdrA.innerHTML = flCircle2(nameA, 28);
    if (lblA) { lblA.textContent = nameA + ' — Likelihoods'; lblA.style.color = ''; }
    var probRowsA = probBlocks[0].querySelectorAll('.prob-row');
    var teamProbs = [
      { name: 'Winning at home', pct: Math.min(85, (aWinPct||50)+15) },
      { name: 'Winning in ' + fmt, pct: aWinPct||50 },
      { name: 'Winning away',      pct: Math.max(15, (aWinPct||50)-15) },
      { name: 'Top T20I team',     pct: Math.min(90, aWinPct||50) },
    ];
    probRowsA.forEach(function(row, i) {
      if (!teamProbs[i]) return;
      var nameEl = row.querySelector('.prob-row-name'); var valEl = row.querySelector('.prob-row-val'); var fillEl = row.querySelector('.prob-bar-fill');
      if (nameEl) nameEl.textContent = teamProbs[i].name;
      if (valEl)  valEl.textContent  = teamProbs[i].pct + '%';
      if (fillEl) fillEl.style.width = teamProbs[i].pct + '%';
    });
    var discA = probBlocks[0].querySelector('.prob-disclaimer');
    if (discA) discA.textContent = 'Based on Cricsheet historical data.';
  }
  if (probBlocks[1]) {
    var hdrB = probBlocks[1].querySelector('.prob-icon');
    var lblB = probBlocks[1].querySelector('.prob-label');
    if (hdrB) hdrB.innerHTML = flCircle2(nameB, 28);
    if (lblB) { lblB.textContent = nameB + ' — Likelihoods'; lblB.style.color = '#FF7043'; }
    var probRowsB = probBlocks[1].querySelectorAll('.prob-row');
    var teamProbsB = [
      { name: 'Winning at home', pct: Math.min(85, (bWinPct||50)+15) },
      { name: 'Winning in ' + fmt, pct: bWinPct||50 },
      { name: 'Winning away',      pct: Math.max(15, (bWinPct||50)-15) },
      { name: 'Top T20I team',     pct: Math.min(90, bWinPct||50) },
    ];
    probRowsB.forEach(function(row, i) {
      if (!teamProbsB[i]) return;
      var nameEl = row.querySelector('.prob-row-name'); var valEl = row.querySelector('.prob-row-val'); var fillEl = row.querySelector('.prob-bar-fill');
      if (nameEl) nameEl.textContent = teamProbsB[i].name;
      if (valEl)  { valEl.textContent = teamProbsB[i].pct + '%'; valEl.style.color = '#FF7043'; }
      if (fillEl) { fillEl.style.width = teamProbsB[i].pct + '%'; fillEl.style.background = 'linear-gradient(90deg,#FF7043,#FFB347)'; }
    });
    var discB = probBlocks[1].querySelector('.prob-disclaimer');
    if (discB) discB.textContent = 'Based on Cricsheet historical data.';
  }

  // ── Summary card ──────────────────────────────────────────────────────────
  var summaryTitle   = document.querySelector('.summary-title');
  var summaryText    = document.querySelector('.summary-text');
  var summaryVerdict = document.querySelector('.summary-verdict');
  if (summaryTitle)   summaryTitle.textContent = nameA + ' vs ' + nameB;
  if (summaryText)    summaryText.textContent  = fmt + ' record comparison. '
    + nameA + ': ' + (sA.matches||0) + ' matches, ' + (sA.win_pct||0) + '% wins. '
    + nameB + ': ' + (sB.matches||0) + ' matches, ' + (sB.win_pct||0) + '% wins.';
  if (summaryVerdict) {
    var aWins = (sA.win_pct||0) >= (sB.win_pct||0);
    summaryVerdict.textContent = aWins ? nameA + ' leads in ' + fmt : nameB + ' leads in ' + fmt;
    summaryVerdict.className = 'summary-verdict ' + (aWins ? 'verdict-a' : 'verdict-b');
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  populatePlayerSelectors();
});
