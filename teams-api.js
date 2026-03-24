/**
 * teams-api.js
 * ============
 * API wiring for teams.html
 * Loads ICC rankings, team stats, and upcoming fixtures.
 * All team links pass ?name= to team-profile.html
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

function fl(country, size=28) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;vertical-align:middle;"
    onerror="this.style.display='none'">`;
}

function flInline(country, size=18) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;"
    onerror="this.style.display='none'">`;
}

const posClass = ['pos-1','pos-2','pos-3'];
const delays = ['','delay-1','delay-2','delay-3','delay-4','delay-5','','delay-1','delay-2','delay-3','delay-4','delay-5'];

// ── Render rankings table ─────────────────────────────────────────────────────
function renderRankings(teams, fmt) {
  const wrap = document.querySelector('.rank-table-wrap');
  if (!wrap) return;

  // Update section title
  const title = document.querySelector('#view-rankings .section-title');
  if (title) title.innerHTML = `<span class="icon"><i class="fa fa-trophy" style="color:var(--accent-warm);"></i></span> ${fmt} Team Rankings`;

  // Keep header row
  const header = wrap.querySelector('[style*="grid-template-columns"]');
  const headerHtml = header ? header.outerHTML : '';

  if (!teams.length) return;

  wrap.innerHTML = headerHtml + teams.map((t, i) => {
    const pos = i < 3 ? posClass[i] : '';
    const delay = delays[i];
    const change = t.change || '—';
    const changeClass = change.includes('+') || change.includes('▲') ? 'rank-up'
                      : change.includes('-') || change.includes('▼') ? 'rank-down' : 'rank-same';
    const teamName = t.team || t.name || '';

    return `
      <a href="team-profile.html?name=${encodeURIComponent(teamName)}" class="rank-row ${pos} anim-up ${delay}">
        <span class="rank-pos">${t.rank || i+1}</span>
        <div class="rank-flag-big" style="overflow:hidden;">${fl(teamName, 42)}</div>
        <div class="rank-team-info">
          <div class="rank-team-name">${esc(teamName)}</div>
          <div class="rank-team-sub">${esc(CONF[teamName] || '')} · Full Member</div>
        </div>
        <div class="rank-stat">
          <div class="rank-stat-val">${t.rating || '—'}</div>
          <div class="rank-stat-lbl">Rating</div>
        </div>
        <div class="rank-stat">
          <div class="rank-stat-val">${t.points || '—'}</div>
          <div class="rank-stat-lbl">Points</div>
        </div>
        <div class="rank-stat">
          <div class="rank-stat-val">—</div>
          <div class="rank-stat-lbl">Win Rate</div>
        </div>
        <div class="rank-change-col">
          <span class="rank-change ${changeClass}">${esc(change)}</span>
        </div>
      </a>`;
  }).join('');

  // Enrich with win rates from team stats
  enrichWinRates(teams, fmt);
}

// ── Enrich ranking rows with real win rates from Cricsheet ────────────────────
async function enrichWinRates(teams, fmt) {
  const statsData = await apiFetch('/api/teams');
  if (!statsData) return;

  teams.forEach((t, i) => {
    const teamName = t.team || t.name || '';
    const fmtMap = {'T20I':'T20I','ODI':'ODI','Test':'Test'};
    const fmtKey = fmtMap[fmt] || fmt;
    const s = statsData[teamName]?.[fmtKey];
    if (!s) return;

    const row = document.querySelectorAll('.rank-row')[i];
    if (!row) return;
    const winPct = s.win_pct ? `${s.win_pct}%` : '—';
    const statVals = row.querySelectorAll('.rank-stat-val');
    if (statVals[2]) statVals[2].textContent = winPct;
  });
}

// ── Confederation map ─────────────────────────────────────────────────────────
const CONF = {
  'India':'Asia','Pakistan':'Asia','Sri Lanka':'Asia','Bangladesh':'Asia','Afghanistan':'Asia',
  'Australia':'Pacific','New Zealand':'Pacific',
  'England':'Europe','Ireland':'Europe','Scotland':'Europe','Netherlands':'Europe',
  'South Africa':'Africa','Zimbabwe':'Africa','Kenya':'Africa','Namibia':'Africa',
  'West Indies':'Americas','USA':'Americas','Canada':'Americas',
};

// ── Render team cards ─────────────────────────────────────────────────────────
async function renderTeamCards() {
  const statsData = await apiFetch('/api/teams') || {};
  const rankData  = await apiFetch('/api/icc-rankings?category=teams&format=T20I') || {};
  const rankings  = rankData.rankings || [];

  // Build rank lookup
  const rankMap = {};
  rankings.forEach(r => { rankMap[r.team] = r.rank; });

  const grid = document.getElementById('view-cards')?.querySelector('.teams-grid');
  if (!grid) return;

  const teams = Object.keys(statsData);
  if (!teams.length) return;

  grid.innerHTML = teams.map((team, i) => {
    const s = statsData[team] || {};
    const t20 = s['T20I'] || {};
    const conf = CONF[team] || '';
    const code = COUNTRY_ISO[team] || '';
    const rank = rankMap[team] || '—';
    const totalMatches = Object.values(s).reduce((sum, f) => sum + (f.matches || 0), 0);
    const formats = Object.keys(s).filter(f => s[f].matches > 0);
    const delay = delays[i % delays.length];

    return `
      <a href="team-profile.html?name=${encodeURIComponent(team)}" class="team-card anim-up ${delay}">
        <div class="team-card-banner" style="background:transparent;">
          <div class="team-card-flag-wrap" style="overflow:hidden;">
            ${code ? `<img src="${FLAG_BASE}${code}.svg" alt="${esc(team)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">` : esc(team[0])}
          </div>
        </div>
        <div class="team-card-body">
          <div>
            <div class="team-card-name">${esc(team)}</div>
            <div class="team-card-abbr">${conf ? `${conf}` : ''}</div>
          </div>
          <div class="team-card-stats">
            <div class="tcs">
              <div class="tcs-val">${rank !== '—' ? '#' + rank : '—'}</div>
              <div class="tcs-lbl">T20I</div>
            </div>
            <div class="tcs">
              <div class="tcs-val">${t20.win_pct ? t20.win_pct + '%' : '—'}</div>
              <div class="tcs-lbl">Win%</div>
            </div>
            <div class="tcs">
              <div class="tcs-val">${t20.matches || '—'}</div>
              <div class="tcs-lbl">T20Is</div>
            </div>
          </div>
          <div class="team-card-formats">
            ${formats.map(f => `<span class="pcard-fmt">${f}</span>`).join('')}
          </div>
        </div>
        <div class="team-card-footer">
          <span>${totalMatches ? totalMatches + ' intl matches' : '—'}</span>
          <span style="color:var(--green-live);font-weight:600;font-size:0.68rem;">● Active</span>
        </div>
      </a>`;
  }).join('');
}

// ── Render win rates sidebar ──────────────────────────────────────────────────
async function renderWinRatesSidebar() {
  const statsData = await apiFetch('/api/teams') || {};

  const teams = Object.entries(statsData)
    .map(([team, s]) => ({ team, win_pct: s['T20I']?.win_pct || 0 }))
    .filter(t => t.win_pct > 0)
    .sort((a, b) => b.win_pct - a.win_pct)
    .slice(0, 6);

  const sbWinrate = document.querySelector('.sb-card:first-child');
  if (!sbWinrate || !teams.length) return;

  const head = sbWinrate.querySelector('.sb-head');
  const disclaimer = sbWinrate.querySelector('.disclaimer-banner')?.parentElement?.outerHTML || '';

  sbWinrate.innerHTML = (head?.outerHTML || '<div class="sb-head"><i class="fa fa-chart-bar"></i> Top T20I Win Rates</div>') +
    teams.map(t => `
      <a href="team-profile.html?name=${encodeURIComponent(t.team)}" class="winrate-row">
        <span class="winrate-flag">${fl(t.team, 28)}</span>
        <div class="winrate-info">
          <div class="winrate-name">${esc(t.team)}</div>
          <div class="winrate-bar-wrap">
            <div class="winrate-bar-fill" style="width:${Math.min(t.win_pct, 100)}%"></div>
          </div>
        </div>
        <span class="winrate-pct">${t.win_pct}%</span>
      </a>`).join('') +
    `<div style="padding:0.55rem 1.1rem;border-top:1px solid var(--border-light);">
       <div class="disclaimer-banner" style="padding:0.45rem 0.7rem;">
         <span class="icon">⚠</span> Historical data only.
       </div>
     </div>`;
}

// ── Render upcoming fixtures ──────────────────────────────────────────────────
async function renderFixtures() {
  const data = await apiFetch('/api/matches');
  if (!data?.data?.length) return;

  const upcoming = data.data.filter(m => !m.matchStarted).slice(0, 4);
  if (!upcoming.length) return;

  const fixtureCard = document.querySelectorAll('.sb-card')[1];
  if (!fixtureCard) return;

  const head = fixtureCard.querySelector('.sb-head');
  fixtureCard.innerHTML = (head?.outerHTML || '<div class="sb-head"><i class="fa fa-calendar"></i> Upcoming Fixtures</div>') +
    upcoming.map(m => {
      const t1 = m.t1 || m.team1 || '';
      const t2 = m.t2 || m.team2 || '';
      return `
        <a href="match-detail.html?id=${esc(m.id||'')}" class="fixture-item">
          <div class="fixture-teams">${esc(t1)} vs ${esc(t2)}</div>
          <div class="fixture-meta">
            <span class="match-format-badge" style="font-size:.6rem">${esc(m.matchType||'')}</span>
            ${esc(m.venue||'')} · ${esc(m.date||'')}
          </div>
        </a>`;
    }).join('');
}

// ── Format switcher for rankings ──────────────────────────────────────────────
let rankingsCache = {};

async function switchRankingsFormat(fmt) {
  if (!rankingsCache[fmt]) {
    const data = await apiFetch(`/api/icc-rankings?category=teams&format=${fmt}`);
    rankingsCache[fmt] = data?.rankings || [];
  }
  renderRankings(rankingsCache[fmt], fmt);
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Load T20I rankings by default
  await switchRankingsFormat('T20I');

  // Wire format rank tabs
  document.querySelectorAll('[data-fmt-rank]').forEach(btn => {
    btn.addEventListener('click', () => {
      btn.closest('div').querySelectorAll('[data-fmt-rank]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const fmt = btn.dataset.fmtRank.toUpperCase();
      switchRankingsFormat(fmt);
    });
  });

  // Load other sections
  renderWinRatesSidebar();
  renderFixtures();

  // Load team cards when "All Teams" view is activated
  document.querySelectorAll('#rankSwitcher .rsw-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      if (btn.dataset.view === 'cards') renderTeamCards();
    });
  });
});
