/**
 * compare-api.js
 * ==============
 * API wiring for compare.html
 * Loads players/teams from API for selector lists,
 * then fetches comparison data on "Compare" click.
 *
 * HTML structure:
 *   #list-a, #list-b          — selector list containers
 *   #preview-a, #preview-b   — selected item previews
 *   .type-btn[data-mode]      — player/team mode toggle
 *   #compare-results          — results section
 *   .cph-name (×2)            — compare panel header names
 *   .cph-avatar (×2)          — compare panel header avatars
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

function guessIso(name) {
  for (const [c, code] of Object.entries(COUNTRY_ISO))
    if ((name||'').toLowerCase().includes(c.toLowerCase())) return code;
  return '';
}

function flCircle(country, size) {
  size = size || 40;
  const code = COUNTRY_ISO[country] || guessIso(country) || '';
  if (!code) return '<span style="font-size:1.4rem;font-weight:700;color:var(--accent);">' + (country||'?')[0] + '</span>';
  return '<img src="' + FLAG_BASE + code + '.svg" alt="' + esc(country) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

function dash(v) { return (v==null||v===0||v==='') ? '—' : v; }
function fmt1(v) { return (!v) ? '—' : Number(v).toFixed(1); }

// ── Populate selector lists from API ─────────────────────────────────────────
async function populateSelectors() {
  const [playersData, metaData] = await Promise.all([
    apiFetch('/api/players?limit=100&sort=runs'),
    apiFetch('/api/meta/players'),
  ]);

  if (!playersData?.players?.length) return;

  const players = playersData.players.slice(0, 30);
  const meta = metaData || {};

  function buildItem(p, side, i) {
    const playerMeta = meta[p.name] || {};
    const country = playerMeta.country || '';
    const iso = COUNTRY_ISO[country] || '';
    const role = playerMeta.role || '';
    const flagHtml = iso
      ? '<img src="' + FLAG_BASE + iso + '.svg" alt="' + esc(country) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
      : '<span style="font-size:1rem;font-weight:700;color:var(--accent);">' + (p.name||'?')[0] + '</span>';
    return '<div class="selector-item' + (i === 0 && side === 'a' ? ' selected' : (i === 1 && side === 'b' ? ' selected' : '')) + '" '
      + 'onclick="selectPlayerItem(\'' + side + '\', this, \'' + esc(p.name) + '\', \'' + esc(country) + '\', \'' + esc(role) + '\')">'
      + '<div class="selector-item-avatar" style="overflow:hidden;">' + flagHtml + '</div>'
      + '<div class="selector-item-info">'
        + '<div class="selector-item-name">' + esc(p.name) + '</div>'
        + '<div class="selector-item-meta">' + esc(country) + (role ? ' · ' + esc(role) : '') + '</div>'
      + '</div>'
      + '<div class="selector-item-check"><i class="fa-solid fa-check"></i></div>'
    + '</div>';
  }

  const listA = document.getElementById('list-a');
  const listB = document.getElementById('list-b');

  if (listA) listA.innerHTML = players.map((p, i) => buildItem(p, 'a', i)).join('');
  if (listB) listB.innerHTML = players.map((p, i) => buildItem(p, 'b', i)).join('');

  // Update previews with first two players
  if (players.length >= 2) {
    const p0meta = meta[players[0].name] || {};
    const p1meta = meta[players[1].name] || {};
    updatePreview('a', players[0].name, p0meta.country || '');
    updatePreview('b', players[1].name, p1meta.country || '');
    selectedA = { name: players[0].name, country: p0meta.country || '' };
    selectedB = { name: players[1].name, country: p1meta.country || '' };
  }
}

function updatePreview(side, name, country) {
  const el = document.getElementById('preview-' + side);
  if (!el) return;
  const iso = COUNTRY_ISO[country] || '';
  const flagHtml = iso
    ? '<img src="' + FLAG_BASE + iso + '.svg" alt="' + esc(country) + '" style="width:52px;height:52px;object-fit:cover;border-radius:50%;">'
    : '<span style="font-size:1.5rem;font-weight:700;color:var(--accent);">' + (name||'?')[0] + '</span>';
  el.innerHTML = '<div class="selected-preview-avatar" style="overflow:hidden;">' + flagHtml + '</div><span>' + esc(name) + '</span>';
}

// ── Track selections ──────────────────────────────────────────────────────────
let selectedA = { name: '', country: '' };
let selectedB = { name: '', country: '' };

window.selectPlayerItem = function(side, el, name, country, role) {
  const list = document.getElementById('list-' + side);
  if (list) list.querySelectorAll('.selector-item').forEach(function(i) { i.classList.remove('selected'); });
  el.classList.add('selected');
  updatePreview(side, name, country);
  if (side === 'a') selectedA = { name, country };
  else selectedB = { name, country };
};

// ── Run comparison ────────────────────────────────────────────────────────────
async function runComparison() {
  const nameA = selectedA.name;
  const nameB = selectedB.name;
  if (!nameA || !nameB) return;

  // Show loading state
  const resultsEl = document.getElementById('compare-results');
  if (resultsEl) {
    resultsEl.style.opacity = '0.5';
    resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  const data = await apiFetch('/api/compare/players?player_a=' + encodeURIComponent(nameA) + '&player_b=' + encodeURIComponent(nameB));

  if (resultsEl) resultsEl.style.opacity = '1';
  if (!data) return;

  const a = data.player_a || {};
  const b = data.player_b || {};

  // Update panel headers
  const names = document.querySelectorAll('.cph-name');
  const avatars = document.querySelectorAll('.cph-avatar');
  if (names[0]) names[0].textContent = nameA;
  if (names[1]) names[1].textContent = nameB;
  if (avatars[0]) { avatars[0].style.overflow = 'hidden'; avatars[0].innerHTML = flCircle(selectedA.country, 52); }
  if (avatars[1]) { avatars[1].style.overflow = 'hidden'; avatars[1].innerHTML = flCircle(selectedB.country, 52); }

  // Populate format stat tables for active tab
  populateCompareStats(a, b, 'ODI');
  populateCompareStats(a, b, 'T20I');
  populateCompareStats(a, b, 'Test');

  // Animate results in
  if (resultsEl) {
    resultsEl.style.animation = 'none';
    resultsEl.offsetHeight;
    resultsEl.style.animation = 'fadeSlideUp 0.5s ease both';
  }
}

function populateCompareStats(a, b, fmt) {
  const aBat = a.batting?.[fmt] || {};
  const bBat = b.batting?.[fmt] || {};
  const aBowl = a.bowling?.[fmt] || {};
  const bBowl = b.bowling?.[fmt] || {};

  const fmtKey = fmt.toLowerCase().replace('t20i','t20');

  // Batting comparison rows
  const statPairs = [
    { label:'Matches',      va: aBat.matches,      vb: bBat.matches },
    { label:'Runs',         va: aBat.runs,          vb: bBat.runs,     primary:true },
    { label:'Average',      va: fmt1(aBat.average), vb: fmt1(bBat.average) },
    { label:'Strike Rate',  va: fmt1(aBat.strike_rate), vb: fmt1(bBat.strike_rate) },
    { label:'Centuries',    va: aBat.hundreds,      vb: bBat.hundreds },
    { label:'Fifties',      va: aBat.fifties,       vb: bBat.fifties },
    { label:'Wickets',      va: aBowl.wickets,      vb: bBowl.wickets },
    { label:'Bowl Avg',     va: fmt1(aBowl.average), vb: fmt1(bBowl.average) },
    { label:'Economy',      va: fmt1(aBowl.economy), vb: fmt1(bBowl.economy) },
  ];

  // Find compare table for this format
  const table = document.querySelector('#compare-' + fmtKey + ' .compare-table, [data-fmt="' + fmtKey + '"] .compare-table');
  if (!table) return;

  const tbody = table.querySelector('tbody');
  if (!tbody) return;

  tbody.innerHTML = statPairs.map(function(row) {
    const va = dash(row.va);
    const vb = dash(row.vb);
    const aWins = parseFloat(va) > parseFloat(vb);
    const bWins = parseFloat(vb) > parseFloat(va);
    return '<tr>'
      + '<td class="mono' + (row.primary ? ' primary' : '') + (aWins ? ' winner' : '') + '">' + va + '</td>'
      + '<td class="stat-label">' + esc(row.label) + '</td>'
      + '<td class="mono' + (row.primary ? ' primary' : '') + (bWins ? ' winner' : '') + '">' + vb + '</td>'
    + '</tr>';
  }).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  populateSelectors();

  // Wire Compare button
  const compareBtn = document.querySelector('.compare-go-btn, [onclick="showResults()"]');
  if (compareBtn) {
    compareBtn.addEventListener('click', runComparison);
  }

  // Wire format sub-tabs in results
  document.querySelectorAll('.tab[data-fmt]').forEach(function(tab) {
    tab.addEventListener('click', function() {
      tab.closest('.tabs').querySelectorAll('.tab').forEach(function(t) { t.classList.remove('active'); });
      tab.classList.add('active');
      const fmt = tab.dataset.fmt;
      document.querySelectorAll('[id^="compare-"]').forEach(function(p) { p.style.display = 'none'; });
      const panel = document.getElementById('compare-' + fmt);
      if (panel) panel.style.display = '';
    });
  });
});
