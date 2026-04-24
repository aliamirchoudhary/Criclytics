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

function initialsFromName(name) {
  var parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return 'NA';
  var first = parts[0][0] || '';
  var second = (parts[1] && parts[1][0]) || '';
  return (first + second).toUpperCase() || 'NA';
}

function flCircle(country, size, fallbackLabel) {
  size = size || 40;
  const code = COUNTRY_ISO[country] || guessIso(country) || '';
  if (!code) {
    return '<span style="width:' + size + 'px;height:' + size + 'px;display:inline-flex;align-items:center;justify-content:center;border-radius:50%;background:var(--surface-2);font-size:' + Math.round(size*0.34) + 'px;font-weight:700;color:var(--accent);">' + esc(initialsFromName(fallbackLabel || country)) + '</span>';
  }
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

function buildPlayerAvatar(r, size) {
  size = size || 44;
  var imageUrl = r.photo || r.image || r.img || r.avatar || '';
  if (imageUrl) {
    return '<img src="' + esc(imageUrl) + '" alt="' + esc(r.name || 'Player') + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\';this.insertAdjacentHTML(\'afterend\',\'<span style=\\\"position:absolute;inset:0;display:flex;align-items:center;justify-content:center;border-radius:50%;background:var(--surface-2);font-size:' + Math.round(size*0.34) + 'px;font-weight:700;color:var(--accent);\\\">' + esc(initialsFromName(r.name)) + '</span>\');">';
  }
  return flCircle(r.country || '', size, r.name || '');
}

// ── Build result cards by type ────────────────────────────────────────────────
function buildPlayerCard(r) {
  var country = r.country || '';
  var formats = (r.formats || []).join(',');
  return '<a href="player-profile.html?name=' + encodeURIComponent(r.name) + '" class="result-row" data-country="' + esc(country.toLowerCase()) + '" data-formats="' + esc(formats) + '">'
    + '<div class="result-avatar" style="overflow:hidden;position:relative;">' + buildPlayerAvatar(r, 44) + '</div>'
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
    + '<div class="result-avatar rect" style="overflow:hidden;">' + flCircle(r.name, 44, r.name) + '</div>'
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
  const scoreText = r.scoreText || r.finalScore || '';
  return '<a href="match-detail.html?id=' + esc(r.id||'') + '" class="result-row">'
    + '<div class="result-avatar" style="overflow:hidden;display:flex;align-items:center;justify-content:center;gap:2px;background:var(--surface-2);">'
      + (iso1 ? '<img src="' + FLAG_CDN + iso1 + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;">' : '')
      + (iso2 ? '<img src="' + FLAG_CDN + iso2 + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;">' : '')
    + '</div>'
    + '<div class="result-info">'
      + '<div class="result-name">' + esc(t1) + ' vs ' + esc(t2) + '</div>'
      + '<div class="result-meta">' + esc(r.matchType||'') + (r.date ? ' · ' + esc(r.date) : '')
        + (scoreText ? ' · <span class="result-tag">' + esc(scoreText) + '</span>' : '')
        + (r.status ? ' <span class="result-tag">' + esc(r.status) + '</span>' : '') + '</div>'
    + '</div>'
    + '<span class="result-arrow"><i class="fa-solid fa-chevron-right"></i></span>'
  + '</a>';
}

  const MATCH_PAGE_SIZE = 10;
  let currentResults = {};
  let activeFilter = 'all';
  let currentQuery = '';
  let currentMatchPage = 1;

  function getMatchPageInfo(matches) {
    matches = Array.isArray(matches) ? matches : [];
    var totalPages = Math.max(1, Math.ceil(matches.length / MATCH_PAGE_SIZE));
    if (currentMatchPage > totalPages) currentMatchPage = totalPages;
    if (currentMatchPage < 1) currentMatchPage = 1;
    var start = (currentMatchPage - 1) * MATCH_PAGE_SIZE;
    var rows = matches.slice(start, start + MATCH_PAGE_SIZE);
    return { totalPages: totalPages, rows: rows, start: start + 1, end: start + rows.length };
  }

  function buildMatchPager(totalPages, currentPage) {
    if (totalPages <= 1) return '';
    var buttons = [];
    var start = Math.max(1, currentPage - 2);
    var end = Math.min(totalPages, start + 4);
    start = Math.max(1, end - 4);

    buttons.push('<button type="button" class="pager-btn" style="padding:0.45rem 0.7rem;border:1px solid var(--border);background:var(--surface-2);color:var(--text-muted);border-radius:999px;cursor:pointer;" data-match-page="' + (currentPage - 1) + '" ' + (currentPage === 1 ? 'disabled' : '') + '><i class="fa fa-chevron-left"></i></button>');
    for (var page = start; page <= end; page++) {
      buttons.push('<button type="button" class="pager-btn ' + (page === currentPage ? 'active' : '') + '" style="padding:0.45rem 0.75rem;border:1px solid ' + (page === currentPage ? 'rgba(94,184,255,0.45)' : 'var(--border)') + ';background:' + (page === currentPage ? 'rgba(94,184,255,0.14)' : 'var(--surface-2)') + ';color:' + (page === currentPage ? 'var(--accent)' : 'var(--text-muted)') + ';border-radius:999px;cursor:pointer;font-weight:700;" data-match-page="' + page + '">' + page + '</button>');
    }
    buttons.push('<button type="button" class="pager-btn" style="padding:0.45rem 0.7rem;border:1px solid var(--border);background:var(--surface-2);color:var(--text-muted);border-radius:999px;cursor:pointer;" data-match-page="' + (currentPage + 1) + '" ' + (currentPage === totalPages ? 'disabled' : '') + '><i class="fa fa-chevron-right"></i></button>');
    return '<div class="result-pager" style="display:flex;gap:0.45rem;justify-content:center;flex-wrap:wrap;margin-top:0.9rem;">' + buttons.join('') + '</div>';
  }

  function renderMatchGroup(matches) {
    matches = Array.isArray(matches) ? matches : [];
    if (!matches.length) return '';
    var page = getMatchPageInfo(matches);
    var rowsHtml = page.rows.map(buildMatchCard).join('');
    return '<div class="result-group anim-up delay-3" id="group-matches">'
      + '<div class="result-group-header"><div class="result-group-title"><div class="result-group-icon icon-match"><i class="fa fa-calendar"></i></div> Matches</div>'
      + '<span class="result-group-count">' + matches.length + ' result' + (matches.length !== 1 ? 's' : '') + ' · ' + page.start + '-' + page.end + ' of ' + matches.length + '</span></div>'
      + rowsHtml
      + buildMatchPager(page.totalPages, currentMatchPage)
    + '</div>';
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
  const matches = Array.isArray(results.matches) ? results.matches : [];
  const mCount = matches.length;
  const total  = pCount + tCount + vCount + mCount;

  currentQuery = query;
  if (results !== currentResults) currentMatchPage = 1;

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
  html += renderMatchGroup(matches);

  container.innerHTML = html;
  // Preserve insertion order so "Relevance" can restore the original listing.
  Array.from(container.querySelectorAll('.result-group .result-row, .result-group .result-match')).forEach(function(row, idx) {
    row.dataset.order = String(idx);
  });
  currentResults = results;
  // Reapply active filter if not 'all'
  if (activeFilter && activeFilter !== 'all') applyFilter(activeFilter);
  applySidebarFilters();
}

// ── Filter ────────────────────────────────────────────────────────────────────

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

function getActiveSidebarLabels(blockTitle) {
  var labels = [];
  document.querySelectorAll('.search-sidebar .sidebar-block').forEach(function(block) {
    var header = (block.querySelector('.sidebar-block-header') || {}).textContent || '';
    if (!header.toLowerCase().includes(blockTitle)) return;
    block.querySelectorAll('.sidebar-option.active').forEach(function(opt) {
      var txt = ((opt.querySelector('.sidebar-option-left') || {}).textContent || '').replace(/\s+/g, ' ').trim();
      if (txt) labels.push(txt);
    });
  });
  return labels;
}

function applySidebarFilters() {
  var container = document.getElementById('results-container') || document.querySelector('.search-results-main');
  if (!container) return;

  var formatFilters = getActiveSidebarLabels('format').filter(function(t) { return !t.toLowerCase().includes('all format'); });
  var countryFilters = getActiveSidebarLabels('country').filter(function(t) { return !t.toLowerCase().includes('all countr'); });
  var sortLabel = (getActiveSidebarLabels('sort by')[0] || 'relevance').toLowerCase();

  function textHasAny(text, needles) {
    if (!needles.length) return true;
    var hay = String(text || '').toLowerCase();
    return needles.some(function(n) { return hay.includes(String(n || '').toLowerCase()); });
  }

  function countryFromTeamName(name) {
    return (COUNTRY_ISO[name] ? name : '').toLowerCase();
  }

  function normalizeLabel(v) {
    return String(v || '').replace(/[^a-zA-Z0-9\s]/g, ' ').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function readCountryFromMeta(row) {
    var meta = ((row.querySelector('.result-meta') || {}).textContent || '');
    return normalizeLabel(meta.split('·')[0]);
  }

  function readFormatsFromRow(row) {
    var fromData = normalizeLabel((row.dataset.formats || '').replace(/,/g, ' '));
    var fromMeta = normalizeLabel((row.querySelector('.result-meta,.match-mini-sub') || {}).textContent || '');
    return (fromData + ' ' + fromMeta).trim();
  }

  function readNameForSort(row) {
    return (((row.querySelector('.result-name,.match-mini-title') || {}).textContent || '').trim());
  }

  function readNumericScore(row) {
    var txt = (row.textContent || '');
    var nums = txt.match(/\d+(?:\.\d+)?/g) || [];
    if (!nums.length) return 0;
    return Math.max.apply(null, nums.map(function(n) { return parseFloat(n) || 0; }));
  }

  var formatNeedles = formatFilters.map(normalizeLabel);
  var countryNeedles = countryFilters.map(normalizeLabel);

  container.querySelectorAll('.result-group').forEach(function(group) {
    var gid = group.id || '';
    var rows = gid === 'group-matches'
      ? Array.from(group.querySelectorAll('.result-row,.result-match'))
      : Array.from(group.querySelectorAll('.result-row'));

    rows.forEach(function(row) {
      var passFormat = true;
      var passCountry = true;

      if (gid === 'group-players') {
        var playerFormats = readFormatsFromRow(row);
        var playerCountry = normalizeLabel((row.dataset.country || '')) || readCountryFromMeta(row);
        passFormat = !formatNeedles.length || textHasAny(playerFormats, formatNeedles);
        passCountry = !countryNeedles.length || textHasAny(playerCountry, countryNeedles);
      } else if (gid === 'group-teams') {
        var meta = readFormatsFromRow(row);
        var name = ((row.querySelector('.result-name') || {}).textContent || '').trim();
        passFormat = !formatNeedles.length || textHasAny(meta, formatNeedles);
        passCountry = !countryNeedles.length || textHasAny(countryFromTeamName(name), countryNeedles);
      } else if (gid === 'group-venues') {
        var venueMeta = normalizeLabel((row.querySelector('.result-meta') || {}).textContent || '');
        passCountry = !countryNeedles.length || textHasAny(venueMeta, countryNeedles);
      } else if (gid === 'group-matches') {
        var matchMeta = readFormatsFromRow(row);
        passFormat = !formatNeedles.length || textHasAny(matchMeta, formatNeedles);
      }

      row.style.display = (passFormat && passCountry) ? '' : 'none';
    });

    var visibleRows = rows.filter(function(r) { return r.style.display !== 'none'; }).length;
    if (visibleRows === 0) {
      group.style.display = 'none';
    } else if (activeFilter === 'all') {
      group.style.display = '';
    }

    if (visibleRows > 1) {
      var rowSelector = gid === 'group-matches' ? '.result-row,.result-match' : '.result-row';
      var sortableRows = Array.from(group.querySelectorAll(rowSelector));
      if (sortLabel.includes('alphabet')) {
        sortableRows.sort(function(a, b) { return readNameForSort(a).localeCompare(readNameForSort(b)); });
      } else if (sortLabel.includes('most match') || sortLabel.includes('highest rated')) {
        sortableRows.sort(function(a, b) { return readNumericScore(b) - readNumericScore(a); });
      } else {
        sortableRows.sort(function(a, b) {
          var ao = parseInt(a.dataset.order || '0', 10);
          var bo = parseInt(b.dataset.order || '0', 10);
          return ao - bo;
        });
      }
      sortableRows.forEach(function(row) { group.appendChild(row); });
    }
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
    applySidebarFilters();
    applyFilter(cat);
  };

  document.addEventListener('click', function(e) {
    var button = e.target.closest && e.target.closest('[data-match-page]');
    if (!button) return;
    var page = parseInt(button.getAttribute('data-match-page'), 10);
    if (!page || page < 1) return;
    var totalPages = Math.max(1, Math.ceil(((currentResults.matches || []).length || 0) / MATCH_PAGE_SIZE));
    if (page > totalPages) return;
    currentMatchPage = page;
    if (currentQuery) renderResults(currentResults, currentQuery);
  });

  function resetSidebarFiltersInitial() {
    document.querySelectorAll('.search-sidebar .sidebar-block').forEach(function(block) {
      var header = ((block.querySelector('.sidebar-block-header') || {}).textContent || '').toLowerCase();
      var opts = Array.from(block.querySelectorAll('.sidebar-option'));
      if (!opts.length) return;

      if (header.includes('sort')) {
        opts.forEach(function(o) { o.classList.remove('active'); });
        var relevance = opts.find(function(o) {
          return ((o.querySelector('.sidebar-option-left') || {}).textContent || '').toLowerCase().includes('relevance');
        });
        (relevance || opts[0]).classList.add('active');
      } else {
        opts.forEach(function(o) { o.classList.remove('active'); });
      }
    });
  }

  // Override toggleFilter from search.html — sidebar format/country checkboxes
  window.toggleFilter = function(opt) {
    var block = opt.closest('.sidebar-block');
    var header = (block && block.querySelector('.sidebar-block-header')) || {};
    var headerText = (header.textContent || '').toLowerCase().trim();

    // Sort By is single-select; Format/Country remain multi-select.
    if (headerText.includes('sort')) {
      (block ? block.querySelectorAll('.sidebar-option') : []).forEach(function(o) { o.classList.remove('active'); });
      opt.classList.add('active');
    } else {
      opt.classList.toggle('active');
    }

    if (!currentResults) return;
    applySidebarFilters();
    if (activeFilter && activeFilter !== 'all') applyFilter(activeFilter);
  };

  // Initial state: no active sidebar filters except Sort by default.
  resetSidebarFiltersInitial();

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
