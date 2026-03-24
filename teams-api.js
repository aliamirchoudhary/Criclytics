/**
 * teams-api.js
 * ============
 * API wiring for teams.html
 * Loads ICC rankings, team stats, and upcoming fixtures.
 * All team links pass ?name= to team-profile.html
 */

function fl(country, size=28) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_CDN}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;vertical-align:middle;"
    onerror="this.style.display='none'">`;
}

function flInline(country, size=18) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_CDN}${code}.svg" alt="${esc(country)}"
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
    const rankNum = parseInt(t.rank) || (i+1);
    const pos = rankNum === 1 ? posClass[0] : rankNum === 2 ? posClass[1] : rankNum === 3 ? posClass[2] : '';
    const delay = delays[i];
    const change = t.change || '—';
    const ch = String(change);
    const changeClass = ch.startsWith('+') ? 'rank-up' : ch.startsWith('-') ? 'rank-down' : 'rank-same';
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

  // Re-apply any active region/search filter after rebuild
  if (_activeTeamRegion || _teamSearch) filterRankingRows();
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

// ── Filter displayed ranking rows by region/search ────────────────────────────
function filterRankingRows() {
  document.querySelectorAll('.rank-table-wrap .rank-row:not([style*="grid"])').forEach(function(row) {
    if (row.classList.contains('rank-row-header')) return;
    var nameEl = row.querySelector('.rank-team-name, [data-team]');
    var teamName = (nameEl ? nameEl.textContent : '') || (row.dataset.team || '');
    teamName = teamName.trim();
    var conf = CONF[teamName] || '';

    var regionOk = !_activeTeamRegion || (REGION_TEAMS[_activeTeamRegion] || []).indexOf(teamName) !== -1;
    var searchOk = !_teamSearch || teamName.toLowerCase().includes(_teamSearch);
    row.style.display = (regionOk && searchOk) ? '' : 'none';
  });
}

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
            ${code ? `<img src="${FLAG_CDN}${code}.svg" alt="${esc(team)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">` : esc(team[0])}
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
  var fixtureCard = document.querySelectorAll('.sb-card')[1];
  if (!fixtureCard) return;
  var head = fixtureCard.querySelector('.sb-head');
  var headHtml = head ? head.outerHTML : '<div class="sb-head"><i class="fa fa-calendar"></i> Upcoming Fixtures</div>';

  var data = await apiFetch('/api/matches');
  var upcoming = (data && data.data) ? data.data.filter(function(m){ return !m.matchStarted; }).slice(0,4) : [];

  if (!upcoming.length) {
    fixtureCard.innerHTML = headHtml
      + '<div style="padding:1rem 1.1rem;font-size:0.78rem;color:var(--text-muted);">'
      + '<i class="fa fa-calendar-xmark" style="display:block;font-size:1.2rem;margin-bottom:.5rem;opacity:.4;"></i>'
      + 'No upcoming fixtures cached. Run <code>fetch_live.py</code> when connected to a network.'
      + '</div>';
    return;
  }

  fixtureCard.innerHTML = headHtml + upcoming.map(function(m) {
    var t1 = m.t1 || m.team1 || '';
    var t2 = m.t2 || m.team2 || '';
    var iso1 = COUNTRY_ISO[t1] || ''; var iso2 = COUNTRY_ISO[t2] || '';
    var f1 = iso1 ? '<img src="' + FLAG_CDN + iso1 + '.svg" style="width:14px;height:14px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:3px;">' : '';
    var f2 = iso2 ? '<img src="' + FLAG_CDN + iso2 + '.svg" style="width:14px;height:14px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:3px;">' : '';
    return '<a href="match-detail.html?id=' + esc(m.id||'') + '" class="fixture-item">'
      + '<div class="fixture-teams">' + f1 + esc(t1) + ' vs ' + f2 + esc(t2) + '</div>'
      + '<div class="fixture-meta"><span class="match-format-badge" style="font-size:.6rem">' + esc(m.matchType||'') + '</span> '
      + esc(m.venue||'') + ' · ' + esc(m.date||'') + '</div>'
    + '</a>';
  }).join('');
}

// ── Format switcher for rankings ──────────────────────────────────────────────
// Clear cache on page load so fresh data is fetched each visit
var rankingsCache = {};

async function switchRankingsFormat(fmt) {
  if (!rankingsCache[fmt]) {
    var data = await apiFetch('/api/icc-rankings?category=teams&format=' + fmt);
    rankingsCache[fmt] = (data && data.rankings) ? data.rankings : [];
  }
  renderRankings(rankingsCache[fmt], fmt);
}

// ── State for filtering ───────────────────────────────────────────────────────
var _activeTeamFmt    = 'T20I';
var _activeTeamRegion = '';
var _teamSearch       = '';

var CONF = {
  'India':'Asia','Pakistan':'Asia','Sri Lanka':'Asia','Bangladesh':'Asia','Afghanistan':'Asia',
  'Australia':'Pacific','New Zealand':'Pacific',
  'England':'Europe','Ireland':'Europe','Scotland':'Europe','Netherlands':'Europe',
  'South Africa':'Africa','Zimbabwe':'Africa','Kenya':'Africa','Namibia':'Africa',
  'West Indies':'Americas','USA':'Americas','Canada':'Americas',
};

var REGION_TEAMS = {
  'asia':     ['India','Pakistan','Sri Lanka','Bangladesh','Afghanistan'],
  'europe':   ['England','Ireland','Scotland','Netherlands'],
  'pacific':  ['Australia','New Zealand'],
  'africa':   ['South Africa','Zimbabwe','Namibia'],
  'americas': ['West Indies','USA','Canada'],
};

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // Load T20I rankings by default
  await switchRankingsFormat('T20I');

  // Format filter chips (data-fmt="t20i"/"odi"/"test")
  document.querySelectorAll('.filter-chip[data-fmt]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-chip[data-fmt]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const raw = btn.dataset.fmt.toLowerCase();
      _activeTeamFmt = raw === 't20i' ? 'T20I' : raw === 'odi' ? 'ODI' : 'Test';
      switchRankingsFormat(_activeTeamFmt);
    });
  });

  // Region filter chips (data-region)
  document.querySelectorAll('.filter-chip[data-region]').forEach(btn => {
    btn.addEventListener('click', () => {
      // Toggle
      const wasActive = btn.classList.contains('active');
      document.querySelectorAll('.filter-chip[data-region]').forEach(b => b.classList.remove('active'));
      if (!wasActive) {
        btn.classList.add('active');
        _activeTeamRegion = btn.dataset.region;
      } else {
        _activeTeamRegion = '';
      }
      filterRankingRows();
    });
  });

  // Search input
  const searchInput = document.querySelector('.filter-sticky .search-input');
  if (searchInput) {
    searchInput.addEventListener('input', () => {
      _teamSearch = searchInput.value.trim().toLowerCase();
      filterRankingRows();
    });
  }

  // Wire format rank sub-tabs inside the table header
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
