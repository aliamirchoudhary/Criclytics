/**
 * matches-api.js
 * ==============
 * API wiring for matches.html
 * Loads live, upcoming and completed matches from CricAPI.
 * Falls back to static dummy data gracefully.
 *
 * Actual HTML IDs:
 *   #group-live       — live matches container
 *   #group-upcoming   — upcoming matches container
 *   #group-completed  — completed matches container
 *   .filter-chip[data-format] — format filter chips (all/t20/odi/test)
 *   .sidebar-series-item — series sidebar rows
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
  'Netherlands':'NL','Scotland':'GB-SCT','Nepal':'NP','UAE':'AE','Oman':'OM',
};

function guessIso(teamName) {
  if (!teamName) return '';
  for (const [c, code] of Object.entries(COUNTRY_ISO))
    if (teamName.toLowerCase().includes(c.toLowerCase())) return code;
  return '';
}

function flagCircle(teamName, size) {
  size = size || 28;
  const iso = guessIso(teamName);
  if (!iso) return '<span style="font-size:' + Math.round(size*0.55) + 'px;font-weight:700;color:var(--accent);">' + (teamName||'?')[0] + '</span>';
  return '<img src="' + FLAG_BASE + iso + '.svg" alt="' + esc(teamName) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

// ── Build a single match row card ─────────────────────────────────────────────
function buildMatchCard(match, statusClass, delay) {
  delay = delay || '';
  const id     = match.id || match.unique_id || '';
  const t1     = match.t1 || match.team1 || 'TBA';
  const t2     = match.t2 || match.team2 || 'TBA';
  const score1 = match.t1s || '';
  const score2 = match.t2s || '';
  const fmt    = match.matchType || match.type || '';
  const venue  = match.venue || '';
  const date   = match.date || match.dateTimeGMT || '';
  const status = match.status || '';
  const series = match.series || match.series_id || '';

  const isLive      = statusClass === 'is-live';
  const isCompleted = statusClass === 'is-completed';

  let badge;
  if (isLive) {
    badge = '<span class="status-badge status-live">Live</span>';
  } else if (isCompleted) {
    badge = '<span class="status-badge status-completed">Completed</span>';
  } else {
    badge = '<span class="status-badge" style="background:rgba(94,184,255,0.1);color:var(--accent);border:1px solid rgba(94,184,255,0.2);">Upcoming</span>';
  }

  let infoLine;
  if (isLive) {
    infoLine = '<div style="font-size:0.75rem;color:var(--green-live);font-weight:600;">' + esc(status) + '</div>';
  } else if (isCompleted) {
    infoLine = '<div style="font-size:0.75rem;color:var(--text-muted);">' + esc(status) + '</div>';
  } else {
    infoLine = '<div style="font-size:0.75rem;color:var(--accent-warm);font-weight:600;">' + esc(date) + '</div>';
  }

  const s1html = score1 ? '<span class="match-row-score">' + esc(score1) + '</span>' : '';
  const s2html = score2 ? '<span class="match-row-score">' + esc(score2) + '</span>' : '';

  return '<a href="match-detail.html?id=' + esc(id) + '" class="match-row-card ' + statusClass + ' anim-up ' + delay + '">'
    + '<div class="match-row-badges">' + badge + '<span class="match-format-badge">' + esc(fmt) + '</span></div>'
    + '<div class="match-row-teams">'
      + '<div class="match-row-team">'
        + '<span class="match-row-flag" style="width:28px;height:28px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:var(--surface-2);flex-shrink:0;">' + flagCircle(t1,28) + '</span>'
        + '<span class="match-row-team-name">' + esc(t1) + '</span>'
        + s1html
      + '</div>'
      + '<div class="match-row-divider"></div>'
      + '<div class="match-row-team">'
        + '<span class="match-row-flag" style="width:28px;height:28px;border-radius:50%;overflow:hidden;display:flex;align-items:center;justify-content:center;background:var(--surface-2);flex-shrink:0;">' + flagCircle(t2,28) + '</span>'
        + '<span class="match-row-team-name">' + esc(t2) + '</span>'
        + s2html
      + '</div>'
    + '</div>'
    + '<div class="match-row-info">'
      + '<div class="match-row-venue"><i class="fa fa-location-dot"></i> ' + esc(venue) + '</div>'
      + '<div class="match-row-series">' + esc(series) + '</div>'
      + infoLine
    + '</div>'
    + '<i class="fa fa-chevron-right match-row-arrow"></i>'
  + '</a>';
}

// ── Inject cards into a group, preserving the label header ───────────────────
function injectCards(groupId, matches, statusClass, emptyMsg) {
  const group = document.getElementById(groupId);
  if (!group) return;

  const label = group.querySelector('.match-group-label');
  const labelHtml = label ? label.outerHTML : '';

  if (!matches.length) {
    group.innerHTML = labelHtml + '<div style="padding:2rem;text-align:center;color:var(--text-muted);font-size:0.88rem;">' + emptyMsg + '</div>';
    return;
  }

  const delays = ['','delay-1','delay-2','delay-3','delay-4','delay-5'];
  group.innerHTML = labelHtml + matches.map(function(m, i) {
    return buildMatchCard(m, statusClass, delays[i % delays.length]);
  }).join('');
}

// ── Load live matches ─────────────────────────────────────────────────────────
async function loadLive() {
  const data = await apiFetch('/api/live');
  const matches = (data && data.data) ? data.data : [];
  if (!matches.length) return;

  injectCards('group-live', matches.slice(0,6), 'is-live', 'No live matches right now.');

  const liveLabel = document.querySelector('#group-live .match-group-date');
  if (liveLabel) {
    liveLabel.innerHTML = '<span style="width:7px;height:7px;background:var(--green-live);border-radius:50%;display:inline-block;margin-right:6px;"></span>Live Now (' + matches.length + ')';
  }
}

// ── Load upcoming + completed ─────────────────────────────────────────────────
async function loadFixtures() {
  const data = await apiFetch('/api/matches');
  if (!data || !data.data || !data.data.length) return;

  const upcoming  = data.data.filter(function(m) { return !m.matchStarted && !m.matchEnded; });
  const completed = data.data.filter(function(m) { return m.matchEnded; });

  if (upcoming.length)  injectCards('group-upcoming',  upcoming.slice(0,12),  'is-upcoming',  'No upcoming matches.');
  if (completed.length) injectCards('group-completed', completed.slice(0,12), 'is-completed', 'No recent results.');
}

// ── Load series sidebar ───────────────────────────────────────────────────────
async function loadSeries() {
  const data = await apiFetch('/api/series');
  if (!data || !data.data || !data.data.length) return;

  const firstItem = document.querySelector('.sidebar-series-item');
  if (!firstItem) return;
  const container = firstItem.parentElement;
  if (!container) return;

  const head = container.querySelector('.sidebar-card-header');
  const headHtml = head ? head.outerHTML : '';

  container.innerHTML = headHtml + data.data.slice(0,6).map(function(s) {
    return '<a href="#" class="sidebar-series-item">'
      + '<div class="series-name">' + esc(s.name || s.series || '—') + '</div>'
      + '<div class="series-meta">'
        + '<span class="match-format-badge" style="font-size:0.62rem;">' + esc(s.matchType || '') + '</span> '
        + esc(s.status || 'Active')
      + '</div>'
    + '</a>';
  }).join('');
}

// ── Format filter chips ───────────────────────────────────────────────────────
function initFormatFilter() {
  document.querySelectorAll('.filter-chip[data-format]').forEach(function(chip) {
    chip.addEventListener('click', function() {
      document.querySelectorAll('.filter-chip[data-format]').forEach(function(c) { c.classList.remove('active'); });
      chip.classList.add('active');

      const fmt = chip.dataset.format.toLowerCase();
      document.querySelectorAll('.match-row-card').forEach(function(card) {
        if (fmt === 'all') { card.style.display = ''; return; }
        const cardFmt = (card.querySelector('.match-format-badge') ? card.querySelector('.match-format-badge').textContent.trim().toLowerCase() : '');
        const hit = fmt === 't20' ? cardFmt.includes('t20')
                  : fmt === 'odi' ? cardFmt === 'odi'
                  : fmt === 'test'? cardFmt === 'test'
                  : cardFmt.includes(fmt);
        card.style.display = hit ? '' : 'none';
      });
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  loadLive();
  loadFixtures();
  loadSeries();
  initFormatFilter();
});
