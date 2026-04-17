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

  // Update sidebar bests
  updateSidebarBests(data);
  updateSidebarCountryLeaders(data);
  updateSidebarRecentlyBroken(data);
}

function updateSidebarBests(data) {
  var card = findSidebarCardByTitle('all-time bests');
  if (!card) return;
  var head = card.querySelector('.sidebar-card-header');

  var testRuns = data.most_runs && data.most_runs.Test && data.most_runs.Test[0];
  var testWkts = data.most_wickets && data.most_wickets.Test && data.most_wickets.Test[0];
  var testAvg = data.best_averages && data.best_averages.Test && data.best_averages.Test[0];
  var odiRuns = data.most_runs && data.most_runs.ODI && data.most_runs.ODI[0];
  var odiHundreds = data.most_hundreds && data.most_hundreds.ODI && data.most_hundreds.ODI[0];

  var rows = [];
  if (testRuns) {
    rows.push(buildSidebarRecordRow({
      name: testRuns.player,
      country: detectCountry(testRuns),
      sub: 'Most Test runs ever',
      val: (testRuns.runs || 0).toLocaleString(),
      href: 'player-profile.html?name=' + encodeURIComponent(testRuns.player)
    }));
  }
  if (testWkts) {
    rows.push(buildSidebarRecordRow({
      name: testWkts.player,
      country: detectCountry(testWkts),
      sub: 'Most Test wickets',
      val: testWkts.wickets || '—',
      href: 'player-profile.html?name=' + encodeURIComponent(testWkts.player)
    }));
  }
  if (testAvg) {
    rows.push(buildSidebarRecordRow({
      name: testAvg.player,
      country: detectCountry(testAvg),
      sub: 'Highest Test avg',
      val: testAvg.average || '—',
      href: 'player-profile.html?name=' + encodeURIComponent(testAvg.player)
    }));
  }
  if (odiRuns) {
    rows.push(buildSidebarRecordRow({
      name: odiRuns.player,
      country: detectCountry(odiRuns),
      sub: 'Most ODI runs',
      val: (odiRuns.runs || 0).toLocaleString(),
      href: 'player-profile.html?name=' + encodeURIComponent(odiRuns.player)
    }));
  }
  if (odiHundreds) {
    rows.push(buildSidebarRecordRow({
      name: odiHundreds.player,
      country: detectCountry(odiHundreds),
      sub: 'Most ODI centuries',
      val: odiHundreds.hundreds || '—',
      href: 'player-profile.html?name=' + encodeURIComponent(odiHundreds.player)
    }));
  }

  if (!rows.length) {
    card.innerHTML = (head ? head.outerHTML : '')
      + '<div style="padding:0.8rem 1.1rem;color:var(--text-muted);font-size:0.76rem;">No all-time records available.</div>';
    return;
  }

  card.innerHTML = (head ? head.outerHTML : '') + rows.join('');
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

function detectCountry(entry) {
  if (!entry) return '';
  return entry.country || guessCountry(entry.player || entry.team || '');
}

function buildSidebarRecordRow(opts) {
  var name = opts.name || '—';
  var sub = opts.sub || '';
  var val = opts.val == null ? '—' : String(opts.val);
  var href = opts.href || '#';
  var country = opts.country || '';
  var code = COUNTRY_ISO[country] || '';
  var flag = code
    ? '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;">'
    : '<span style="width:24px;height:24px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:var(--surface-2);font-size:0.7rem;color:var(--text-muted);font-weight:700;">' + esc(name.slice(0, 1).toUpperCase()) + '</span>';

  return '<a href="' + href + '" class="sidebar-rec-row">'
    + '<span class="srec-flag">' + flag + '</span>'
    + '<div class="srec-info">'
      + '<div class="srec-name">' + esc(name) + '</div>'
      + '<div class="srec-sub">' + esc(sub) + '</div>'
    + '</div>'
    + '<span class="srec-val" style="color:var(--accent);">' + esc(val) + '</span>'
  + '</a>';
}

function updateSidebarCountryLeaders(data) {
  var card = findSidebarCardByTitle('records by country');
  if (!card) return;
  var head = card.querySelector('.sidebar-card-header');

  var counts = {};
  Object.keys(data || {}).forEach(function(key) {
    var byFmt = data[key];
    if (!byFmt || typeof byFmt !== 'object') return;
    Object.keys(byFmt).forEach(function(fmt) {
      var rows = byFmt[fmt];
      if (!Array.isArray(rows)) return;
      rows.slice(0, 10).forEach(function(entry) {
        var country = detectCountry(entry);
        if (!country) return;
        counts[country] = (counts[country] || 0) + 1;
      });
    });
  });

  var leaders = Object.keys(counts)
    .map(function(country) { return { country: country, count: counts[country] }; })
    .sort(function(a, b) { return b.count - a.count; })
    .slice(0, 5);

  if (!leaders.length) {
    card.innerHTML = (head ? head.outerHTML : '')
      + '<div style="padding:0.8rem 1.1rem;color:var(--text-muted);font-size:0.76rem;">No country record stats available.</div>';
    return;
  }

  card.innerHTML = (head ? head.outerHTML : '') + leaders.map(function(item) {
    return buildSidebarRecordRow({
      name: item.country,
      country: item.country,
      sub: item.count + ' top-record entries',
      val: item.count,
      href: 'team-profile.html?name=' + encodeURIComponent(item.country)
    });
  }).join('');
}

function updateSidebarRecentlyBroken(data) {
  var card = findSidebarCardByTitle('recently broken');
  if (!card) return;
  var head = card.querySelector('.sidebar-card-header');

  var items = [];
  var odiHundreds = data.most_hundreds && data.most_hundreds.ODI && data.most_hundreds.ODI[0];
  var testWkts = data.most_wickets && data.most_wickets.Test && data.most_wickets.Test[0];
  var t20Runs = data.most_runs && data.most_runs.T20I && data.most_runs.T20I[0];

  if (odiHundreds) {
    items.push({
      name: odiHundreds.player,
      country: detectCountry(odiHundreds),
      sub: 'Current ODI centuries benchmark',
      val: odiHundreds.hundreds || '—',
      href: 'player-profile.html?name=' + encodeURIComponent(odiHundreds.player)
    });
  }
  if (testWkts) {
    items.push({
      name: testWkts.player,
      country: detectCountry(testWkts),
      sub: 'Current Test wickets benchmark',
      val: testWkts.wickets || '—',
      href: 'player-profile.html?name=' + encodeURIComponent(testWkts.player)
    });
  }
  if (t20Runs) {
    items.push({
      name: t20Runs.player,
      country: detectCountry(t20Runs),
      sub: 'Current T20I runs benchmark',
      val: (t20Runs.runs || 0).toLocaleString(),
      href: 'player-profile.html?name=' + encodeURIComponent(t20Runs.player)
    });
  }

  if (!items.length) {
    card.innerHTML = (head ? head.outerHTML : '')
      + '<div style="padding:0.8rem 1.1rem;color:var(--text-muted);font-size:0.76rem;">No recent benchmark updates available.</div>';
    return;
  }

  card.innerHTML = (head ? head.outerHTML : '') + items.slice(0, 3).map(function(item) {
    return '<a href="' + item.href + '" class="sidebar-rec-row">'
      + '<span class="srec-flag">' + flagImg(item.country, 24) + '</span>'
      + '<div class="srec-info">'
        + '<div class="srec-name">' + esc(item.name) + '</div>'
        + '<div class="srec-sub">' + esc(item.sub) + '</div>'
      + '</div>'
      + '<span class="srec-val" style="color:var(--green-live);">' + esc(String(item.val)) + '</span>'
    + '</a>';
  }).join('');
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
