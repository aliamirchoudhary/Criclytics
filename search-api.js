/**
 * search-api.js
 * =============
 * API wiring for search.html
 * Reads ?q= from URL, calls /api/search, renders results by type.
 *
 * HTML structure:
 *   #searchInput            — main search input
 *   #searchQuery            — query display span
 *   #resultsCount           — count display
 *   .results-section        — main results container
 *   .filter-chip[data-type] — type filter chips (all/players/teams/venues/matches)
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
  if (!code) return '<span style="font-size:' + Math.round(size*0.45) + 'px;font-weight:700;color:var(--accent);">' + (country||'?')[0] + '</span>';
  return '<img src="' + FLAG_BASE + code + '.svg" alt="' + esc(country) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

// ── Build result cards by type ────────────────────────────────────────────────
function buildPlayerCard(r) {
  const country = r.country || '';
  return '<a href="player-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-card">'
    + '<div class="result-avatar" style="overflow:hidden;">' + flCircle(country, 44) + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(r.name) + '</div>'
      + '<div class="result-meta">' + esc(country) + (r.role ? ' · ' + esc(r.role) : '') + '</div>'
      + (r.runs ? '<div class="result-stats"><span class="result-stat">' + r.runs + ' runs</span>'
          + (r.average ? '<span class="result-stat">Avg ' + Number(r.average).toFixed(1) + '</span>' : '')
        + '</div>' : '')
    + '</div>'
    + '<span class="result-type-badge">Player</span>'
    + '<i class="fa fa-chevron-right result-arrow"></i>'
  + '</a>';
}

function buildTeamCard(r) {
  return '<a href="team-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-card">'
    + '<div class="result-avatar rect" style="overflow:hidden;">' + flCircle(r.name, 44) + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(r.name) + '</div>'
      + '<div class="result-meta">International Cricket Team</div>'
    + '</div>'
    + '<span class="result-type-badge">Team</span>'
    + '<i class="fa fa-chevron-right result-arrow"></i>'
  + '</a>';
}

function buildVenueCard(r) {
  const country = r.country || '';
  const iso = COUNTRY_ISO[country] || '';
  const flagHtml = iso ? '<img src="' + FLAG_BASE + iso + '.svg" alt="' + esc(country) + '" style="width:44px;height:44px;object-fit:cover;border-radius:8px;">' : '<i class="fa fa-building" style="font-size:1.5rem;color:var(--accent);"></i>';
  return '<a href="venue-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-card">'
    + '<div class="result-avatar rect" style="overflow:hidden;background:var(--surface-2);display:flex;align-items:center;justify-content:center;">' + flagHtml + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(r.name) + '</div>'
      + '<div class="result-meta">' + esc(country) + (r.city ? ' · ' + esc(r.city) : '') + '</div>'
      + (r.matches ? '<div class="result-stats"><span class="result-stat">' + r.matches + ' matches</span></div>' : '')
    + '</div>'
    + '<span class="result-type-badge">Venue</span>'
    + '<i class="fa fa-chevron-right result-arrow"></i>'
  + '</a>';
}

function buildMatchCard(r) {
  const t1 = r.t1 || r.team1 || '';
  const t2 = r.t2 || r.team2 || '';
  const iso1 = guessIso(t1); const iso2 = guessIso(t2);
  return '<a href="match-detail.html?id=' + esc(r.id||'') + '" class="result-card">'
    + '<div class="result-avatar" style="overflow:hidden;display:flex;align-items:center;justify-content:center;gap:2px;background:var(--surface-2);">'
      + (iso1 ? '<img src="' + FLAG_BASE + iso1 + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;">' : '')
      + (iso2 ? '<img src="' + FLAG_BASE + iso2 + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;">' : '')
    + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(t1) + ' vs ' + esc(t2) + '</div>'
      + '<div class="result-meta">' + esc(r.matchType||'') + (r.date ? ' · ' + esc(r.date) : '') + '</div>'
      + (r.status ? '<div class="result-stats"><span class="result-stat">' + esc(r.status) + '</span></div>' : '')
    + '</div>'
    + '<span class="result-type-badge">Match</span>'
    + '<i class="fa fa-chevron-right result-arrow"></i>'
  + '</a>';
}

// ── Render all results ────────────────────────────────────────────────────────
function renderResults(results, query) {
  const container = document.querySelector('.results-section, #resultsContainer, .search-results');
  const countEl   = document.getElementById('resultsCount') || document.querySelector('.results-count');
  const queryEl   = document.getElementById('searchQuery')  || document.querySelector('.search-query-display');

  if (queryEl) queryEl.textContent = query;

  const total = (results.players||[]).length + (results.teams||[]).length
              + (results.venues||[]).length + (results.matches||[]).length;

  if (countEl) countEl.textContent = total + ' result' + (total !== 1 ? 's' : '') + ' for "' + query + '"';

  if (!container) return;

  if (!total) {
    container.innerHTML = '<div style="text-align:center;padding:4rem 2rem;color:var(--text-muted);">'
      + '<i class="fa fa-magnifying-glass" style="font-size:2.5rem;margin-bottom:1rem;display:block;opacity:0.4;"></i>'
      + '<div style="font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;">No results found</div>'
      + '<div>Try a different spelling or search for a team, venue, or match.</div>'
    + '</div>';
    return;
  }

  let html = '';

  if ((results.players||[]).length) {
    html += '<div class="results-group">'
      + '<div class="results-group-label"><i class="fa fa-user"></i> Players (' + results.players.length + ')</div>'
      + results.players.slice(0,10).map(buildPlayerCard).join('')
    + '</div>';
  }
  if ((results.teams||[]).length) {
    html += '<div class="results-group">'
      + '<div class="results-group-label"><i class="fa fa-shield-halved"></i> Teams (' + results.teams.length + ')</div>'
      + results.teams.slice(0,5).map(buildTeamCard).join('')
    + '</div>';
  }
  if ((results.venues||[]).length) {
    html += '<div class="results-group">'
      + '<div class="results-group-label"><i class="fa fa-building"></i> Venues (' + results.venues.length + ')</div>'
      + results.venues.slice(0,5).map(buildVenueCard).join('')
    + '</div>';
  }
  if ((results.matches||[]).length) {
    html += '<div class="results-group">'
      + '<div class="results-group-label"><i class="fa fa-calendar"></i> Matches (' + results.matches.length + ')</div>'
      + results.matches.slice(0,5).map(buildMatchCard).join('')
    + '</div>';
  }

  container.innerHTML = html;
  currentResults = results;
  applyFilter(activeFilter);
}

// ── Filter ────────────────────────────────────────────────────────────────────
let currentResults = {};
let activeFilter = 'all';

function applyFilter(type) {
  activeFilter = type;
  document.querySelectorAll('.results-group').forEach(function(group) {
    if (type === 'all') { group.style.display = ''; return; }
    const label = (group.querySelector('.results-group-label')?.textContent || '').toLowerCase();
    group.style.display = label.includes(type) ? '' : 'none';
  });
}

// ── Main search ───────────────────────────────────────────────────────────────
async function doSearch(query) {
  if (!query || !query.trim()) return;
  query = query.trim();

  // Update URL
  const url = new URL(window.location.href);
  url.searchParams.set('q', query);
  window.history.replaceState({}, '', url);

  // Update input
  const input = document.getElementById('searchInput') || document.querySelector('.hero-search, .search-hero-input');
  if (input) input.value = query;

  // Show loading
  const container = document.querySelector('.results-section, #resultsContainer, .search-results');
  if (container) container.innerHTML = '<div style="text-align:center;padding:3rem;color:var(--text-muted);"><i class="fa fa-spinner fa-spin" style="font-size:2rem;"></i></div>';

  const data = await apiFetch('/api/search?q=' + encodeURIComponent(query) + '&limit=20');
  if (data) {
    renderResults(data, query);
  } else {
    renderResults({}, query);
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  // Run search from URL param
  const q = getParam('q');
  if (q) doSearch(q);

  // Wire search input
  const input = document.getElementById('searchInput') || document.querySelector('.hero-search, .search-hero-input, input[type="search"]');
  if (input) {
    if (q) input.value = q;
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && this.value.trim()) doSearch(this.value.trim());
    });
    // Also wire search button if present
    const btn = document.querySelector('.search-btn, .hero-search-btn, [onclick*="search"]');
    if (btn) btn.addEventListener('click', function() { if (input.value.trim()) doSearch(input.value.trim()); });
  }

  // Wire filter chips
  document.querySelectorAll('.filter-chip[data-type]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      document.querySelectorAll('.filter-chip[data-type]').forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active');
      applyFilter(chip.dataset.type);
    });
  });

  // Wire trending/popular search buttons
  document.querySelectorAll('.trending-tag, .popular-search').forEach(function(tag) {
    tag.addEventListener('click', function() {
      const text = this.textContent.replace(/[🇮🇳🇦🇺🏴󠁧󠁢󠁥󠁮󠁧󠁿🇵🇰🇳🇿🇿🇦]/g, '').trim();
      if (text) doSearch(text);
    });
  });
});
