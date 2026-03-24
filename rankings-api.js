/**
 * rankings-api.js
 * ===============
 * API wiring for rankings.html
 * Loads ICC rankings from /api/icc-rankings and populates all panels.
 *
 * HTML structure:
 *   .format-tab[data-fmt="test/odi/t20"]   — format switcher
 *   .cs-btn[data-cat="batting/bowling/allrounder/teams"] — category switcher
 *   #fmt-test, #fmt-odi, #fmt-t20          — format panels
 *   #test-batting, #odi-batting etc.        — category panels (data-rankings-panel)
 *   .rank-card inside each panel            — the card containing header + rows
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
  'Netherlands':'NL','Scotland':'GB-SCT',
};

function fl(country, size) {
  size = size || 28;
  const code = COUNTRY_ISO[country] || country;
  return '<span class="rank-flag" style="overflow:hidden;display:flex;align-items:center;justify-content:center;">'
    + '<img src="' + FLAG_BASE + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" '
    + 'onerror="this.style.display=\'none\'">'
    + '</span>';
}

const medalClass = ['gold','silver','bronze'];

// ── Build a player ranking row ────────────────────────────────────────────────
function buildPlayerRow(r, idx) {
  const medal = idx < 3 ? medalClass[idx] : '';
  const changeClass = (r.change||'').includes('+') || (r.change||'').includes('▲') ? 'up'
                    : (r.change||'').includes('-') || (r.change||'').includes('▼') ? 'down' : 'same';
  const changeIcon  = changeClass === 'up' ? '<i class="fa fa-caret-up"></i>'
                    : changeClass === 'down' ? '<i class="fa fa-caret-down"></i>'
                    : '<i class="fa fa-minus"></i>';
  const rating = r.rating || '—';
  const maxRating = 1000;
  const barWidth = rating !== '—' ? Math.round((parseInt(rating) / maxRating) * 100) : 0;
  const barClass = idx === 0 ? 'gold-bar' : idx === 1 ? 'silver-bar' : idx === 2 ? 'bronze-bar' : '';
  const stat2 = r.avg || r.econ || r.bat_avg || r.sr || '—';
  const playerName = r.player || r.name || '—';
  const country = r.country || '';

  return '<a href="player-profile.html?name=' + encodeURIComponent(playerName) + '" class="rank-row">'
    + '<div class="rank-medal ' + medal + '">' + (r.rank || idx+1) + '</div>'
    + fl(country, 28)
    + '<div class="rank-identity"><div>'
    +   '<div class="rank-name">' + esc(playerName) + '</div>'
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
  const medal = idx < 3 ? medalClass[idx] : '';
  const changeClass = (r.change||'').includes('+') ? 'up' : (r.change||'').includes('-') ? 'down' : 'same';
  const changeIcon  = changeClass === 'up' ? '<i class="fa fa-caret-up"></i>'
                    : changeClass === 'down' ? '<i class="fa fa-caret-down"></i>'
                    : '<i class="fa fa-minus"></i>';
  const rating = r.rating || '—';
  const barWidth = rating !== '—' ? Math.round((parseInt(rating) / 150) * 100) : 0;
  const barClass = idx === 0 ? 'gold-bar' : idx === 1 ? 'silver-bar' : idx === 2 ? 'bronze-bar' : '';
  const teamName = r.team || r.name || '—';

  return '<a href="team-profile.html?name=' + encodeURIComponent(teamName) + '" class="rank-row">'
    + '<div class="rank-medal ' + medal + '">' + (r.rank || idx+1) + '</div>'
    + fl(teamName, 28)
    + '<div class="rank-identity"><div>'
    +   '<div class="rank-name">' + esc(teamName) + '</div>'
    +   '<div class="rank-country">' + esc(r.points || '') + ' pts</div>'
    + '</div></div>'
    + '<span class="rank-stat primary">' + esc(String(rating)) + '</span>'
    + '<span class="rank-stat">' + esc(r.points || '—') + '</span>'
    + '<span class="rank-move ' + changeClass + '">' + changeIcon + ' ' + esc(r.change || '—') + '</span>'
    + '<div class="rank-bar-wrap"><div class="rank-bar-bg"><div class="rank-bar-fill ' + barClass + '" style="width:' + barWidth + '%"></div></div></div>'
  + '</a>';
}

// ── Inject rows into a panel ──────────────────────────────────────────────────
function injectRankings(panelId, rows, isTeams) {
  const panel = document.getElementById(panelId);
  if (!panel) return;
  const card = panel.querySelector('.rank-card');
  if (!card) return;

  // Keep card header, replace rows
  const header = card.querySelector('.rank-card-header');
  const rowHeader = card.querySelector('.rank-row-header');
  const keepHtml = (header ? header.outerHTML : '') + (rowHeader ? rowHeader.outerHTML : '');

  if (!rows || !rows.length) return;

  card.innerHTML = keepHtml + rows.map(function(r, i) {
    return isTeams ? buildTeamRow(r, i) : buildPlayerRow(r, i);
  }).join('');
}

// ── Cache to avoid re-fetching ────────────────────────────────────────────────
const rankCache = {};

async function fetchRankings(category, fmt) {
  const key = category + '_' + fmt;
  if (rankCache[key]) return rankCache[key];

  const apiCat = category === 'teams' ? 'teams' : category;
  const apiFmt = fmt.toUpperCase() === 'T20' ? 'T20I' : fmt.toUpperCase();
  const data = await apiFetch('/api/icc-rankings?category=' + apiCat + '&format=' + apiFmt);
  const rows = (data && data.rankings) ? data.rankings : [];
  rankCache[key] = rows;
  return rows;
}

// ── Load all panels for a given format ───────────────────────────────────────
async function loadFormatPanels(fmt) {
  const cats = ['batting','bowling','allrounder','teams'];
  for (const cat of cats) {
    const panelId = fmt + '-' + cat;
    const rows = await fetchRankings(cat, fmt);
    injectRankings(panelId, rows, cat === 'teams');
  }
}

// ── Update sidebar: Current No.1s ─────────────────────────────────────────────
async function updateSidebarNo1s() {
  const formats = ['T20I','ODI','Test'];
  const cats    = ['batting','bowling'];

  const srrContainer = document.querySelector('.sidebar-rank-rows, [class*="srr"]')?.parentElement;
  if (!srrContainer) return;

  let html = '';
  for (const fmt of formats) {
    for (const cat of cats) {
      const rows = await fetchRankings(cat, fmt);
      if (!rows.length) continue;
      const no1 = rows[0];
      const name = no1.player || no1.team || no1.name || '—';
      const country = no1.country || '';
      const code = COUNTRY_ISO[country] || '';
      html += '<div class="srr-row" style="display:flex;align-items:center;gap:0.7rem;padding:0.6rem 1rem;border-bottom:1px solid var(--border-light);">'
        + '<span style="color:#FFD700;font-size:0.9rem;">★</span>'
        + (code ? '<span class="srr-flag" style="overflow:hidden;width:28px;height:28px;display:flex;align-items:center;justify-content:center;border-radius:50%;">'
            + '<img src="' + FLAG_BASE + code + '.svg" alt="' + esc(country) + '" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
            + '</span>' : '')
        + '<div class="srr-info" style="flex:1;min-width:0;">'
          + '<div class="srr-name" style="font-size:0.85rem;font-weight:600;color:var(--text-primary);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + esc(name) + '</div>'
          + '<div class="srr-sub" style="font-size:0.7rem;color:var(--text-muted);">' + fmt + ' ' + cat.charAt(0).toUpperCase() + cat.slice(1) + '</div>'
        + '</div>'
        + '<span class="srr-rating" style="font-family:var(--font-mono);font-size:0.85rem;font-weight:700;color:var(--accent);">' + esc(no1.rating||'—') + '</span>'
      + '</div>';
    }
  }

  // Find existing srr-row elements and replace their parent content
  const firstSrr = document.querySelector('.srr-row, [class*="srr-row"]');
  if (firstSrr && firstSrr.parentElement) {
    const parent = firstSrr.parentElement;
    const head   = parent.querySelector('[class*="card-head"], [class*="sidebar-card-header"]');
    parent.innerHTML = (head ? head.outerHTML : '') + html;
  }
}

// ── Tab switching ─────────────────────────────────────────────────────────────
let loadedFormats = {};

function initTabs() {
  // Format tabs: test / odi / t20
  document.querySelectorAll('.format-tab[data-fmt]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const fmt = btn.dataset.fmt;
      document.querySelectorAll('.format-tab').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');

      document.querySelectorAll('.fmt-panel').forEach(function(p) { p.classList.remove('active'); });
      const panel = document.getElementById('fmt-' + fmt);
      if (panel) panel.classList.add('active');

      // Load this format's data if not yet loaded
      if (!loadedFormats[fmt]) {
        loadedFormats[fmt] = true;
        loadFormatPanels(fmt);
      }
    });
  });

  // Category tabs: batting / bowling / allrounder / teams
  document.querySelectorAll('.cs-btn[data-cat]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      const cat = btn.dataset.cat;
      document.querySelectorAll('.cs-btn').forEach(function(b) { b.classList.remove('active'); });
      btn.classList.add('active');

      // Show/hide cat-panels in the currently active fmt-panel
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
  // Load Test rankings on page load (default active tab)
  loadedFormats['test'] = true;
  loadFormatPanels('test');
  updateSidebarNo1s();
});
