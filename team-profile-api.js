/**
 * team-profile-api.js
 * ===================
 * API wiring for team-profile.html
 * Reads ?name= from URL, loads full team profile from API,
 * populates hero, stats strip, format breakdown, H2H, venue stats.
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

function fl(country, size=18) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:5px;"
    onerror="this.style.display='none'">`;
}
function flCircle(country, size=24) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;vertical-align:middle;"
    onerror="this.style.display='none'">`;
}

function dash(v) { return (v == null || v === 0 || v === '') ? '—' : v; }
function fmt1(v) { return (!v) ? '—' : Number(v).toFixed(1); }

const CONF = {
  'India':'Asia','Pakistan':'Asia','Sri Lanka':'Asia','Bangladesh':'Asia','Afghanistan':'Asia',
  'Australia':'Pacific','New Zealand':'Pacific',
  'England':'Europe','Ireland':'Europe',
  'South Africa':'Africa','Zimbabwe':'Africa',
  'West Indies':'Americas',
};

// ── Load and render ───────────────────────────────────────────────────────────
async function loadTeamProfile() {
  const teamName = getParam('name');
  if (!teamName) return; // show static India default

  // Update page title
  document.title = `${teamName} — Team Profile · Criclytics`;

  // Update name elements
  const nameEl = document.getElementById('teamName');
  const breadEl = document.getElementById('breadcrumbTeam');
  if (nameEl) nameEl.textContent = teamName;
  if (breadEl) breadEl.textContent = teamName;

  // Update team crest flag
  const iso = COUNTRY_ISO[teamName];
  if (iso) {
    const crestImg = document.getElementById('teamCrestImg');
    if (crestImg) {
      crestImg.src = `${FLAG_BASE}${iso}.svg`;
      crestImg.alt = teamName;
    }
  }

  // Update compare link
  const compareBtn = document.getElementById('compareBtn');
  if (compareBtn) compareBtn.href = `compare.html?team_a=${encodeURIComponent(teamName)}`;

  // Load stats data
  const [teamData, metaData, rankingsData] = await Promise.all([
    apiFetch(`/api/teams/${encodeURIComponent(teamName)}`),
    apiFetch('/api/meta/teams'),
    apiFetch('/api/icc-rankings?category=teams&format=T20I'),
  ]);

  const meta   = metaData?.[teamName] || {};
  const stats  = teamData?.format_stats || {};
  const h2h    = teamData?.head_to_head || {};
  const venueStats = teamData?.venue_stats || {};

  // ── Full name / board info
  const fullNameEl = document.getElementById('teamFullName');
  if (fullNameEl && meta.board) {
    const founded = meta.founded ? ` · Founded: ${meta.founded}` : '';
    fullNameEl.textContent = `${meta.board}${founded}`;
  }

  // ── Profile tags — update confederation and ranking
  const tagsEl = document.querySelector('.team-hero-tags');
  if (tagsEl) {
    const confTag = tagsEl.querySelector('.ptag:first-child');
    const conf = CONF[teamName] || meta.confederation || '';
    if (confTag && conf) confTag.innerHTML = `<i class="fa fa-globe" style="font-size:.65rem"></i> ${conf}`;

    // Find rank from rankings
    const rankings = rankingsData?.rankings || [];
    const rank = rankings.find(r => r.team === teamName);
    if (rank) {
      const rankTag = tagsEl.querySelector('[style*="FFD700"]');
      if (rankTag) rankTag.innerHTML = `<i class="fa fa-trophy" style="font-size:.65rem"></i> ICC #${rank.rank} T20I`;
    }

    // WC trophies
    if (meta.icc_trophies !== undefined) {
      const trophyTag = tagsEl.querySelector('.ptag:last-child');
    }
  }

  // ── Stats strip
  const totalMatches = Object.values(stats).reduce((s, f) => s + (f.matches || 0), 0);
  const t20WinPct  = stats['T20I']?.win_pct || '—';
  const odiWinPct  = stats['ODI']?.win_pct  || '—';
  const testWinPct = stats['Test']?.win_pct  || '—';

  // Find ICC T20I rating
  const rankingsAll = await apiFetch('/api/icc-rankings?category=teams&format=T20I');
  const teamRank = rankingsAll?.rankings?.find(r => r.team === teamName);
  const iccRating = teamRank?.rating || '—';
  const iccTrophies = meta.icc_trophies ?? '—';

  const tssVals = document.querySelectorAll('.tss-val');
  if (tssVals.length >= 6) {
    tssVals[0].textContent = totalMatches || '—';
    tssVals[1].textContent = t20WinPct !== '—' ? t20WinPct + '%' : '—';
    tssVals[2].textContent = odiWinPct !== '—' ? odiWinPct + '%' : '—';
    tssVals[3].textContent = testWinPct !== '—' ? testWinPct + '%' : '—';
    tssVals[4].textContent = iccRating;
    tssVals[5].textContent = iccTrophies;
  }

  // ── Format breakdown table (Overview tab)
  renderFormatBreakdown(stats);

  // ── H2H table
  renderH2H(h2h);

  // ── Venue performance
  renderVenueStats(venueStats);

  // ── Sidebar rivals update
  renderRivals(h2h);

  // ── Recent results (from CricAPI)
  renderRecentResults(teamName);
}

function renderFormatBreakdown(stats) {
  const tbody = document.querySelector('#panel-overview .data-table tbody');
  if (!tbody) return;
  const rows = ['T20I','ODI','Test'].map(fmt => {
    const s = stats[fmt];
    if (!s || !s.matches) return '';
    return `<tr>
      <td class="bold">${fmt}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono">${dash(s.won)}</td>
      <td class="mono">${dash(s.lost)}</td>
      <td class="mono">${dash(s.tied)}</td>
      <td class="mono">${dash(s.no_result)}</td>
      <td class="mono" style="color:var(--accent)">${s.win_pct ? s.win_pct + '%' : '—'}</td>
      <td class="mono">${fmt1(s.avg_score)}</td>
      <td class="mono">${fmt1(s.avg_wickets)}</td>
    </tr>`;
  }).filter(Boolean).join('');
  if (rows) tbody.innerHTML = rows;
}

function renderH2H(h2h) {
  const tbody = document.querySelector('#panel-h2h .data-table tbody');
  if (!tbody || !Object.keys(h2h).length) return;

  // Flatten: h2h is {opponent: {T20I: {...}, ODI: {...}}}
  // Show T20I by default
  const rows = Object.entries(h2h).map(([opp, fmts]) => {
    const s = fmts['T20I'] || fmts['ODI'] || Object.values(fmts)[0];
    if (!s) return '';
    return `<tr>
      <td class="bold">${fl(opp, 18)}${esc(opp)}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono" style="color:var(--green-live)">${dash(s.won)}</td>
      <td class="mono" style="color:var(--red)">${dash(s.lost)}</td>
      <td class="mono">${dash(s.tied)}</td>
      <td class="mono">${dash(s.no_result)}</td>
      <td class="mono" style="color:var(--accent)">${s.win_pct ? s.win_pct + '%' : '—'}</td>
      <td class="mono">${esc(s.last_result || '—')}</td>
    </tr>`;
  }).filter(Boolean).join('');
  if (rows) tbody.innerHTML = rows;
}

function renderVenueStats(venueStats) {
  // venueStats is {format: {venue: {...}}}
  const tbody = document.querySelector('#panel-venues .data-table tbody');
  if (!tbody) return;
  const t20Venues = venueStats['T20I'] || {};
  const sorted = Object.entries(t20Venues)
    .filter(([,s]) => s.matches >= 2)
    .sort((a,b) => (b[1].matches||0) - (a[1].matches||0))
    .slice(0, 8);
  if (!sorted.length) return;
  tbody.innerHTML = sorted.map(([venue, s]) => `
    <tr>
      <td class="bold">${esc(venue)}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono" style="color:var(--green-live)">${dash(s.won)}</td>
      <td class="mono" style="color:var(--red)">${dash(s.lost)}</td>
      <td class="mono" style="color:var(--accent)">${s.win_pct ? s.win_pct + '%' : '—'}</td>
      <td class="mono">${fmt1(s.avg_score)}</td>
      <td class="mono">${dash(s.highest)}</td>
    </tr>`).join('');
}

function renderRivals(h2h) {
  // Update sidebar rival cards if they exist
  const rivalCards = document.querySelectorAll('.rival-card');
  if (!rivalCards.length) return;
  const rivals = Object.entries(h2h)
    .map(([opp, fmts]) => {
      const s = fmts['T20I'] || fmts['ODI'] || Object.values(fmts)[0] || {};
      return { opp, ...s };
    })
    .sort((a,b) => (b.matches||0) - (a.matches||0))
    .slice(0, rivalCards.length);

  rivals.forEach((r, i) => {
    const card = rivalCards[i];
    if (!card) return;
    const flagEl = card.querySelector('.rival-flag');
    const nameEl = card.querySelector('.rival-name');
    const statsEl = card.querySelector('.rival-stats');
    if (flagEl) flagEl.innerHTML = flCircle(r.opp, 24);
    if (nameEl) nameEl.textContent = r.opp;
    if (statsEl) statsEl.textContent = `${r.matches||0} matches · ${r.won||0}W ${r.lost||0}L`;
  });
}

async function renderRecentResults(teamName) {
  const data = await apiFetch('/api/matches');
  if (!data?.data?.length) return;

  const completed = data.data
    .filter(m => m.matchEnded && (
      (m.t1||'').includes(teamName) || (m.t2||'').includes(teamName) ||
      (m.team1||'').includes(teamName) || (m.team2||'').includes(teamName)
    ))
    .slice(0, 4);

  if (!completed.length) return;

  const recentEl = document.querySelector('#panel-overview [data-recent-results]');
  if (!recentEl) return;

  recentEl.innerHTML = completed.map(m => {
    const t1 = m.t1 || m.team1 || '';
    const t2 = m.t2 || m.team2 || '';
    const winner = m.status || '';
    return `
      <a href="match-detail.html?id=${esc(m.id||'')}" class="upcoming-row" style="padding:.75rem 1rem;">
        <div style="flex:1">
          <div style="font-size:.88rem;font-weight:600;color:var(--text-primary)">${esc(t1)} vs ${esc(t2)}</div>
          <div class="upcoming-meta"><span class="match-format-badge">${esc(m.matchType||'')}</span> ${esc(m.venue||'')} · ${esc(m.date||'')}</div>
        </div>
        <span class="status-badge status-completed">Completed</span>
      </a>`;
  }).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadTeamProfile);
