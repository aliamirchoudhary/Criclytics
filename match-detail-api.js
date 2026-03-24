/**
 * match-detail-api.js
 * ===================
 * API wiring for match-detail.html
 * Reads ?id= from URL and loads full match scorecard from CricAPI.
 * Falls back to static dummy data when no id or API unavailable.
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

function guessIso(teamName) {
  for (const [c, code] of Object.entries(COUNTRY_ISO))
    if ((teamName||'').toLowerCase().includes(c.toLowerCase())) return code;
  return '';
}

function flagCircle(teamName, size=44) {
  const iso = guessIso(teamName);
  if (!iso) return `<span style="font-size:${Math.round(size*0.5)}px;font-weight:700;color:var(--accent);">${(teamName||'?')[0]}</span>`;
  return `<img src="${FLAG_BASE}${iso}.svg" alt="${esc(teamName)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;"
    onerror="this.style.display='none'">`;
}

function fl(teamName, size=16) {
  const iso = guessIso(teamName);
  if (!iso) return '';
  return `<img src="${FLAG_BASE}${iso}.svg" alt="${esc(teamName)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;"
    onerror="this.style.display='none'">`;
}

function dash(v) { return (v==null||v===''||v===0) ? '—' : v; }

// ── Update scoreboard hero ────────────────────────────────────────────────────
function updateScoreboard(match) {
  const t1 = match.t1 || match.team1 || '';
  const t2 = match.t2 || match.team2 || '';
  const s1 = match.t1s || '';
  const s2 = match.t2s || '';

  // Team names
  const n1 = document.getElementById('team1Name');
  const n2 = document.getElementById('team2Name');
  if (n1) n1.textContent = t1;
  if (n2) n2.textContent = t2;

  // Scores
  const sc1 = document.getElementById('team1Score');
  const sc2 = document.getElementById('team2Score');
  if (sc1) sc1.textContent = s1 || '—';
  if (sc2) sc2.textContent = s2 || '—';

  // Flags — update scoreboard-flag elements
  const flags = document.querySelectorAll('.scoreboard-flag');
  if (flags[0]) flags[0].innerHTML = flagCircle(t1, 44);
  if (flags[1]) flags[1].innerHTML = flagCircle(t2, 44);

  // Status
  const statusEl = document.querySelector('.match-status-live, .match-status-upcoming');
  if (statusEl && match.status) statusEl.textContent = match.status;

  // Meta strip
  const venueEl = document.querySelector('.match-meta-item:first-child');
  if (venueEl && match.venue) venueEl.innerHTML = `<i class="fa fa-location-dot"></i> ${esc(match.venue)}`;

  const dateEl = document.querySelector('.match-meta-item:nth-child(2)');
  if (dateEl && match.date) dateEl.innerHTML = `<i class="fa fa-calendar"></i> ${esc(match.date)}`;
}

// ── Update batting scorecard ──────────────────────────────────────────────────
function updateBattingScorecard(innings, tbodyId) {
  const tbody = document.querySelector(`#${tbodyId} tbody, .scorecard-batting-${tbodyId} tbody`);
  if (!tbody || !innings?.length) return;

  tbody.innerHTML = innings.map(b => `
    <tr>
      <td>
        <a href="player-profile.html?name=${encodeURIComponent(b.batsman||b.batter||'')}"
           style="font-weight:600;color:var(--text-primary);text-decoration:none;">
          ${esc(b.batsman||b.batter||'—')}
        </a>
        <div style="font-size:0.7rem;color:var(--text-muted);">${esc(b.dismissal||b.wicket||'not out')}</div>
      </td>
      <td class="mono">${dash(b.r||b.runs)}</td>
      <td class="mono">${dash(b.b||b.balls)}</td>
      <td class="mono">${dash(b['4s']||b.fours)}</td>
      <td class="mono">${dash(b['6s']||b.sixes)}</td>
      <td class="mono" style="color:var(--accent)">${dash(b.sr||b.strike_rate)}</td>
    </tr>`).join('');
}

// ── Update bowling scorecard ──────────────────────────────────────────────────
function updateBowlingScorecard(bowling, tbodyId) {
  const tbody = document.querySelector(`#${tbodyId} tbody, .scorecard-bowling-${tbodyId} tbody`);
  if (!tbody || !bowling?.length) return;

  tbody.innerHTML = bowling.map(b => `
    <tr>
      <td>
        <a href="player-profile.html?name=${encodeURIComponent(b.bowler||'')}"
           style="font-weight:600;color:var(--text-primary);text-decoration:none;">
          ${esc(b.bowler||'—')}
        </a>
      </td>
      <td class="mono">${dash(b.o||b.overs)}</td>
      <td class="mono">${dash(b.m||b.maidens)}</td>
      <td class="mono">${dash(b.r||b.runs)}</td>
      <td class="mono" style="color:var(--accent)">${dash(b.w||b.wickets)}</td>
      <td class="mono">${dash(b.eco||b.economy)}</td>
      <td class="mono">${dash(b.wd||b.wides)}</td>
      <td class="mono">${dash(b.nb||b.noballs)}</td>
    </tr>`).join('');
}

// ── Update H2H section ────────────────────────────────────────────────────────
async function updateH2H(t1, t2) {
  const data = await apiFetch(`/api/h2h?team_a=${encodeURIComponent(t1)}&team_b=${encodeURIComponent(t2)}&format=T20I`);
  if (!data) return;

  const fmts = Object.values(data);
  if (!fmts.length) return;

  const r = fmts[0]; // T20I H2H

  // Update H2H team names with flags
  const h2hNames = document.querySelectorAll('.h2h-team-name');
  if (h2hNames[0]) h2hNames[0].innerHTML = `${fl(t1,16)}${esc(t1)}`;
  if (h2hNames[1]) h2hNames[1].innerHTML = `${fl(t2,16)}${esc(t2)}`;

  // Update win counts
  const h2hWins = document.querySelectorAll('.h2h-wins');
  if (h2hWins[0]) h2hWins[0].textContent = r.team_a_wins || r.won || 0;
  if (h2hWins[1]) h2hWins[1].textContent = r.team_b_wins || r.lost || 0;

  // Update win bar widths
  const total = r.matches || 1;
  const t1Pct = Math.round(((r.team_a_wins||r.won||0) / total) * 100);
  const t2Pct = Math.round(((r.team_b_wins||r.lost||0) / total) * 100);

  const h2hBars = document.querySelectorAll('.h2h-bar-fill, .h2h-fill');
  if (h2hBars[0]) h2hBars[0].style.width = t1Pct + '%';
  if (h2hBars[1]) h2hBars[1].style.width = t2Pct + '%';

  // Total matches
  const h2hTotal = document.querySelector('.h2h-total, .h2h-matches');
  if (h2hTotal) h2hTotal.textContent = `${total} T20I matches`;
}

// ── Update venue context ──────────────────────────────────────────────────────
async function updateVenueContext(venueName) {
  if (!venueName) return;
  const data = await apiFetch(`/api/venues/${encodeURIComponent(venueName)}`);
  if (!data) return;

  const t20 = data.t20i || {};

  // Update venue stat values
  const venueStats = {
    'Avg 1st Innings': t20.avg_1st_innings ? Math.round(t20.avg_1st_innings) : null,
    'Chase Win %':     data.chase_win_pct ? data.chase_win_pct + '%' : null,
    'Highest Total':   t20.highest || null,
    'Avg Powerplay':   t20.avg_powerplay ? Math.round(t20.avg_powerplay) : null,
  };

  document.querySelectorAll('.venue-stat-row, .venue-context-stat').forEach(row => {
    const label = row.querySelector('.venue-stat-label, label')?.textContent?.trim();
    const valEl = row.querySelector('.venue-stat-val, .val');
    if (label && valEl && venueStats[label]) valEl.textContent = venueStats[label];
  });
}

// ── Load full match ───────────────────────────────────────────────────────────
async function loadMatchDetail() {
  const matchId = getParam('id');
  if (!matchId) return; // show static default

  // Load match score
  const scoreData = await apiFetch(`/api/matches/${matchId}/score`);
  const matchData = await apiFetch(`/api/matches/${matchId}`);

  const match = scoreData?.data || matchData?.data || {};
  if (!match || !Object.keys(match).length) return;

  // Update page title
  const t1 = match.t1 || match.team1 || '';
  const t2 = match.t2 || match.team2 || '';
  if (t1 && t2) document.title = `${t1} vs ${t2} — Match Detail · Criclytics`;

  // Update scoreboard
  updateScoreboard(match);

  // Update innings labels with flags
  document.querySelectorAll('.innings-label-text').forEach(el => {
    const text = el.textContent.trim();
    if (text.includes(t1)) el.innerHTML = `${fl(t1,16)}${esc(text.replace(t1,'').trim())} ${esc(t1)} — 1st Innings`;
    else if (text.includes(t2)) el.innerHTML = `${fl(t2,16)}${esc(text.replace(t2,'').trim())} ${esc(t2)} — 2nd Innings`;
  });

  // Update scorecard tables if available
  const innings = match.score || match.innings || [];
  if (innings.length > 0 && innings[0]?.batting) {
    updateBattingScorecard(innings[0].batting, 'innings1-batting');
    updateBowlingScorecard(innings[0].bowling, 'innings1-bowling');
  }
  if (innings.length > 1 && innings[1]?.batting) {
    updateBattingScorecard(innings[1].batting, 'innings2-batting');
    updateBowlingScorecard(innings[1].bowling, 'innings2-bowling');
  }

  // Update H2H
  if (t1 && t2) await updateH2H(t1, t2);

  // Update venue context
  const venue = match.venue || '';
  if (venue) await updateVenueContext(venue);

  // Update win prob team names
  const probTeams = document.querySelectorAll('.win-prob-team');
  if (probTeams[0]) probTeams[0].innerHTML = `${fl(t1,16)}${esc(t1)}`;
  if (probTeams[1]) probTeams[1].innerHTML = `${fl(t2,16)}${esc(t2)}`;
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadMatchDetail);
