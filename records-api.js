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

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

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
  return '<img src="' + FLAG_BASE + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;vertical-align:middle;" '
    + 'onerror="this.style.display=\'none\'">';
}

const medalClass = {1:'gold', 2:'silver', 3:'bronze'};

// ── Build player record row ───────────────────────────────────────────────────
function buildPlayerRow(entry, rank, stats) {
  const player  = entry.player || '—';
  const matches = entry.matches || '—';
  const medal   = medalClass[rank] || 'plain';

  // stats is an array of {val, label} to show
  const statsHtml = stats.map(function(s) {
    const cls = s.primary ? 'rec-stat primary' : s.green ? 'rec-stat green' : 'rec-stat';
    return '<span class="' + cls + '">' + esc(String(s.val || '—')) + '</span>';
  }).join('');

  return '<a href="player-profile.html?name=' + encodeURIComponent(player) + '" class="record-row">'
    + '<div class="rec-medal ' + medal + '">' + rank + '</div>'
    + '<span class="rec-flag"><img src="' + FLAG_BASE + 'IN.svg" alt="" id="recflag-' + rank + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;"></span>'
    + '<div class="rec-identity">'
      + '<div class="rec-name">' + esc(player) + '</div>'
      + '<div class="rec-sub">' + esc(matches) + ' matches</div>'
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
      + (code ? '<img src="' + FLAG_BASE + code + '.svg" alt="' + esc(team) + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;">' : '')
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
function populateBatting(panelId, data) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const cards = panel.querySelectorAll('.record-card');

  // Card 0: Most Runs
  const runsData = data.most_runs ? data.most_runs[panelId.split('-')[0].toUpperCase()] || [] : [];
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
  const avgData = data.best_averages ? data.best_averages[panelId.split('-')[0].toUpperCase()] || [] : [];
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
  const hundredsData = data.most_hundreds ? data.most_hundreds[panelId.split('-')[0].toUpperCase()] || [] : [];
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
function populateBowling(panelId, data) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const cards = panel.querySelectorAll('.record-card');
  const fmt   = panelId.split('-')[0].toUpperCase();

  // Card 0: Most Wickets
  const wicketsData = data.most_wickets ? data.most_wickets[fmt] || [] : [];
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
  ['test','odi','t20'].forEach(function(fmt) {
    // Map t20 → T20I for the records data keys
    const fmtKey = fmt === 't20' ? 'T20I' : fmt.toUpperCase();
    const fmtData = {
      most_runs:     {[fmtKey]: data.most_runs?.[fmtKey]},
      best_averages: {[fmtKey]: data.best_averages?.[fmtKey]},
      most_hundreds: {[fmtKey]: data.most_hundreds?.[fmtKey]},
      most_wickets:  {[fmtKey]: data.most_wickets?.[fmtKey]},
    };

    populateBatting(fmt + '-batting', {
      most_runs:     {[fmt.toUpperCase()]: data.most_runs?.[fmtKey]},
      best_averages: {[fmt.toUpperCase()]: data.best_averages?.[fmtKey]},
      most_hundreds: {[fmt.toUpperCase()]: data.most_hundreds?.[fmtKey]},
    });

    populateBowling(fmt + '-bowling', {
      most_wickets: {[fmt.toUpperCase()]: data.most_wickets?.[fmtKey]},
    });
  });

  // Update sidebar bests
  updateSidebarBests(data);
}

// ── Update sidebar all-time bests ─────────────────────────────────────────────
function updateSidebarBests(data) {
  // Most Test runs: most_runs.Test[0]
  const testRuns = data.most_runs?.Test?.[0];
  const odiRuns  = data.most_runs?.ODI?.[0];
  const testWkts = data.most_wickets?.Test?.[0];

  const srecRows = document.querySelectorAll('.sidebar-rec-row');
  if (srecRows[0] && testRuns) {
    const flag = srecRows[0].querySelector('.srec-flag');
    const name = srecRows[0].querySelector('.srec-name');
    const val  = srecRows[0].querySelector('.srec-val');
    if (name) name.textContent = testRuns.player;
    if (val)  val.textContent  = (testRuns.runs||'').toLocaleString();
  }
  if (srecRows[1] && testWkts) {
    const name = srecRows[1].querySelector('.srec-name');
    const val  = srecRows[1].querySelector('.srec-val');
    if (name) name.textContent = testWkts.player;
    if (val)  val.textContent  = testWkts.wickets;
  }
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
