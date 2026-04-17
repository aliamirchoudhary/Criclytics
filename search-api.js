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

function guessIso(name) {
  for (const [c, code] of Object.entries(COUNTRY_ISO))
    if ((name||'').toLowerCase().includes(c.toLowerCase())) return code;
  return '';
}

function flCircle(country, size) {
  size = size || 40;
  const code = COUNTRY_ISO[country] || guessIso(country) || '';
  if (!code) return '<span style="font-size:' + Math.round(size*0.45) + 'px;font-weight:700;color:var(--accent);">' + (country||'?')[0] + '</span>';
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

// ── Build result cards by type ────────────────────────────────────────────────
function buildPlayerCard(r) {
  var country = r.country || '';
  var formats = (r.formats || []).join(',');
  return '<a href="player-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-row" data-country="' + esc(country.toLowerCase()) + '" data-formats="' + esc(formats) + '">'
    + '<div class="result-avatar" style="overflow:hidden;">' + flCircle(country, 44) + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(r.name) + '</div>'
      + '<div class="result-meta">' + esc(country) + (r.role ? ' <span class="result-tag">' + esc(r.role) + '</span>' : '') + '</div>'
      + (r.runs || r.wickets ? '<div class="result-stats">'
          + (r.runs ? '<div class="result-stat"><div class="result-stat-val">' + r.runs + '</div><div class="result-stat-label">Runs</div></div>' : '')
          + (r.average ? '<div class="result-stat"><div class="result-stat-val">' + Number(r.average).toFixed(1) + '</div><div class="result-stat-label">Avg</div></div>' : '')
          + (r.wickets ? '<div class="result-stat"><div class="result-stat-val">' + r.wickets + '</div><div class="result-stat-label">Wickets</div></div>' : '')
        + '</div>' : '')
    + '</div>'
    + '<span class="result-arrow"><i class="fa-solid fa-chevron-right"></i></span>'
  + '</a>';
}

function buildTeamCard(r) {
  return '<a href="team-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-row">'
    + '<div class="result-avatar rect" style="overflow:hidden;">' + flCircle(r.name, 44) + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(r.name) + '</div>'
      + '<div class="result-meta">International Cricket Team'
        + (r.formats && r.formats.length ? ' · ' + r.formats.join(' / ') : '') + '</div>'
    + '</div>'
    + '<span class="result-arrow"><i class="fa-solid fa-chevron-right"></i></span>'
  + '</a>';
}

function buildVenueCard(r) {
  const country = r.country || '';
  const iso = COUNTRY_ISO[country] || '';
  const flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(country) + '" style="width:44px;height:44px;object-fit:cover;border-radius:8px;">' : '<i class="fa fa-building" style="font-size:1.5rem;color:var(--accent);"></i>';
  return '<a href="venue-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-row">'
    + '<div class="result-avatar rect" style="overflow:hidden;background:var(--surface-2);display:flex;align-items:center;justify-content:center;">' + flagHtml + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(r.name) + '</div>'
      + '<div class="result-meta">' + esc(country) + (r.city ? ' · ' + esc(r.city) : '')
        + (r.matches ? ' <span class="result-tag">' + r.matches + ' matches</span>' : '') + '</div>'
    + '</div>'
    + '<span class="result-arrow"><i class="fa-solid fa-chevron-right"></i></span>'
  + '</a>';
}

function buildMatchCard(r) {
  const t1 = r.t1 || r.team1 || '';
  const t2 = r.t2 || r.team2 || '';
  const iso1 = guessIso(t1); const iso2 = guessIso(t2);
  return '<a href="match-detail.html?id=' + esc(r.id||'') + '" class="result-row">'
    + '<div class="result-avatar" style="overflow:hidden;display:flex;align-items:center;justify-content:center;gap:2px;background:var(--surface-2);">'
      + (iso1 ? '<img src="' + FLAG_CDN + iso1 + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;">' : '')
      + (iso2 ? '<img src="' + FLAG_CDN + iso2 + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;">' : '')
    + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(t1) + ' vs ' + esc(t2) + '</div>'
      + '<div class="result-meta">' + esc(r.matchType||'') + (r.date ? ' · ' + esc(r.date) : '')
        + (r.status ? ' <span class="result-tag">' + esc(r.status) + '</span>' : '') + '</div>'
    + '</div>'
    + '<span class="result-arrow"><i class="fa-solid fa-chevron-right"></i></span>'
  + '</a>';
}

// ── Render all results ────────────────────────────────────────────────────────
function renderResults(results, query) {
  const container = document.getElementById('results-container') || document.querySelector('.search-results-main');
  const countEl   = document.getElementById('result-count') || document.getElementById('resultsCount') || document.querySelector('.results-count');
  const queryEl   = document.getElementById('searchQuery')  || document.querySelector('.search-query-display');

  if (queryEl) queryEl.textContent = query;

  const pCount = (results.players||[]).length;
  const tCount = (results.teams||[]).length;
  const vCount = (results.venues||[]).length;
  const mCount = (results.matches||[]).length;
  const total  = pCount + tCount + vCount + mCount;

  // Update cat-tab counts
  document.querySelectorAll('.cat-tab').forEach(function(tab) {
    var countBadge = tab.querySelector('.count');
    if (!countBadge) return;
    var onclick = tab.getAttribute('onclick') || '';
    if (onclick.includes("'all'"))      countBadge.textContent = total;
    else if (onclick.includes("'players'")) countBadge.textContent = pCount;
    else if (onclick.includes("'teams'"))   countBadge.textContent = tCount;
    else if (onclick.includes("'venues'"))  countBadge.textContent = vCount;
    else if (onclick.includes("'matches'")) countBadge.textContent = mCount;
  });

  if (countEl) {
    countEl.innerHTML = '<strong>' + total + '</strong> result' + (total !== 1 ? 's' : '') + ' for <strong>"' + esc(query) + '"</strong>';
  }

  if (!container) return;

  if (!total) {
    container.innerHTML = '<div style="text-align:center;padding:4rem 2rem;color:var(--text-muted);">'
      + '<i class="fa fa-magnifying-glass" style="font-size:2.5rem;margin-bottom:1rem;display:block;opacity:0.4;"></i>'
      + '<div style="font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;">No results found</div>'
      + '<div>Try a different spelling or search for a team, venue, or match.</div>'
    + '</div>';
    return;
  }

  var html = '';

  if (pCount) {
    html += '<div class="result-group anim-up" id="group-players">'
      + '<div class="result-group-header"><div class="result-group-title"><div class="result-group-icon icon-player"><i class="fa fa-user"></i></div> Players</div>'
      + '<span class="result-group-count">' + pCount + ' result' + (pCount !== 1 ? 's' : '') + '</span></div>'
      + results.players.slice(0,10).map(buildPlayerCard).join('')
    + '</div>';
  }
  if (tCount) {
    html += '<div class="result-group anim-up delay-1" id="group-teams">'
      + '<div class="result-group-header"><div class="result-group-title"><div class="result-group-icon icon-team"><i class="fa fa-shield-halved"></i></div> Teams</div>'
      + '<span class="result-group-count">' + tCount + ' result' + (tCount !== 1 ? 's' : '') + '</span></div>'
      + results.teams.slice(0,5).map(buildTeamCard).join('')
    + '</div>';
  }
  if (vCount) {
    html += '<div class="result-group anim-up delay-2" id="group-venues">'
      + '<div class="result-group-header"><div class="result-group-title"><div class="result-group-icon icon-venue"><i class="fa fa-building"></i></div> Venues</div>'
      + '<span class="result-group-count">' + vCount + ' result' + (vCount !== 1 ? 's' : '') + '</span></div>'
      + results.venues.slice(0,5).map(buildVenueCard).join('')
    + '</div>';
  }
  if (mCount) {
    html += '<div class="result-group anim-up delay-3" id="group-matches">'
      + '<div class="result-group-header"><div class="result-group-title"><div class="result-group-icon icon-match"><i class="fa fa-calendar"></i></div> Matches</div>'
      + '<span class="result-group-count">' + mCount + ' result' + (mCount !== 1 ? 's' : '') + '</span></div>'
      + results.matches.slice(0,5).map(buildMatchCard).join('')
    + '</div>';
  }

  container.innerHTML = html;
  currentResults = results;
  // Reapply active filter if not 'all'
  if (activeFilter && activeFilter !== 'all') applyFilter(activeFilter);
}

// ── Filter ────────────────────────────────────────────────────────────────────
let currentResults = {};
let activeFilter = 'all';

function applyFilter(type) {
  activeFilter = type;
  document.querySelectorAll('.result-group').forEach(function(group) {
    if (type === 'all') { group.style.display = ''; return; }
    const id = group.id || '';
    // id is like 'group-players', 'group-teams', 'group-venues', 'group-matches'
    const groupType = id.replace('group-', '').replace(/s$/, ''); // 'player','team','venue','match'
    group.style.display = (groupType === type || id.includes(type)) ? '' : 'none';
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
  const input = document.getElementById('main-search-input') || document.querySelector('.big-search-input');
  if (input) input.value = query;

  // Show loading
  const container = document.getElementById('results-container') || document.querySelector('.search-results-main');
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
  var q = getParam('q');
  if (q) doSearch(q);

  // Wire main search input
  var input = document.getElementById('main-search-input') || document.querySelector('.big-search-input');
  if (input) {
    if (q) input.value = q;
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && this.value.trim()) doSearch(this.value.trim());
    });
  }

  // Override the inline setCat() from search.html
  window.setCat = function(btn, cat) {
    document.querySelectorAll('.cat-tab').forEach(function(t) { t.classList.remove('active'); });
    btn.classList.add('active');
    activeFilter = cat;
    applyFilter(cat);
  };

  // Override toggleFilter from search.html — sidebar format/country checkboxes
  window.toggleFilter = function(opt) {
    var block = opt.closest('.sidebar-block');
    var header = (block && block.querySelector('.sidebar-block-header')) || {};
    var headerText = (header.textContent || '').toLowerCase().trim();

    // Toggle active state on clicked option
    opt.classList.toggle('active');

    // Get all active options in this block
    var activeOpts = block ? Array.from(block.querySelectorAll('.sidebar-option.active')) : [];
    var activeLabels = activeOpts.map(function(o) {
      return (o.querySelector('.sidebar-option-left') || {}).textContent || '';
    }).map(function(t) { return t.replace(/[\u0000-\u001F\u007F-\u009F]/g, '').trim(); });

    if (!currentResults) return;

    var container = document.getElementById('results-container') || document.querySelector('.search-results-main');
    if (!container) return;

    if (headerText.includes('format')) {
      // Filter player/team cards by format
      var allFormats = activeLabels.some(function(l) { return l.toLowerCase().includes('all'); });
      container.querySelectorAll('.result-group').forEach(function(group) {
        var groupId = group.id || '';
        if (groupId !== 'group-players') return;
        group.querySelectorAll('.result-row').forEach(function(row) {
          if (allFormats) { row.style.display = ''; return; }
          var rowFmts = (row.dataset.formats || '').split(',');
          var match = activeLabels.some(function(fmt) {
            return rowFmts.some(function(rf) { return rf.toUpperCase().includes(fmt.toUpperCase()); });
          });
          row.style.display = match ? '' : 'none';
        });
      });

    } else if (headerText.includes('country')) {
      // Filter player cards by country
      container.querySelectorAll('.result-group#group-players .result-row').forEach(function(row) {
        if (!activeLabels.length) { row.style.display = ''; return; }
        var rowCountry = (row.dataset.country || '').toLowerCase();
        var match = activeLabels.some(function(l) {
          var clean = l.replace(/[^\x00-\x7F]/g,'').trim().toLowerCase();
          return !clean || rowCountry.includes(clean);
        });
        row.style.display = match ? '' : 'none';
      });
    }
  };

  // Wire suggestion chips
  document.querySelectorAll('.suggestion-chip').forEach(function(chip) {
    chip.addEventListener('click', function() {
      var text = this.textContent.trim();
      if (text && input) input.value = text;
      if (text) doSearch(text);
    });
  });

  // Wire clear button
  var clearBtn = document.querySelector('.big-search-clear');
  if (clearBtn) {
    clearBtn.addEventListener('click', function() {
      if (input) { input.value = ''; input.focus(); }
      var container = document.getElementById('results-container') || document.querySelector('.search-results-main');
      if (container) container.innerHTML = '';
    });
  }
});
