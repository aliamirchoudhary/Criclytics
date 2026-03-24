/**
 * index-api.js
 * ============
 * API wiring for index.html (Home page)
 * Loads: live matches, upcoming fixtures, trending players, rankings
 */

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';

const COUNTRY_ISO_MAP = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

function fl(country, size=20) {
  const code = COUNTRY_ISO_MAP[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${country}" style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;" onerror="this.style.display='none'">`;
}

function flCircle(country, size=44) {
  const code = COUNTRY_ISO_MAP[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${country}" style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;" onerror="this.style.display='none'">`;
}

// ── Live ticker ───────────────────────────────────────────────────────────────
async function loadLiveTicker() {
  const data = await apiFetch('/api/live');
  if (!data || !data.data || !data.data.length) return; // keep dummy ticker

  const matches = data.data.slice(0, 3);
  const inner = document.querySelector('.live-ticker-inner');
  if (!inner) return;

  const items = matches.map(m => {
    const t1 = m.t1 || m.team1 || '';
    const t2 = m.t2 || m.team2 || '';
    const score = m.t1s || m.score || '';
    return `<span class="ticker-item"><strong>${t1} vs ${t2}</strong> ${score} <span class="ticker-sep">|</span></span>`;
  });

  // Duplicate for seamless scroll
  const html = `<span class="ticker-label">Live</span>${items.join('')}<span class="ticker-label">Live</span>${items.join('')}`;
  inner.innerHTML = html;
}

// ── Upcoming fixtures ─────────────────────────────────────────────────────────
async function loadUpcoming() {
  const data = await apiFetch('/api/matches');
  if (!data || !data.data || !data.data.length) return;

  const upcoming = data.data.filter(m => m.ms === 'upcoming' || m.matchStarted === false).slice(0, 5);
  if (!upcoming.length) return;

  const container = document.querySelector('[data-upcoming]');
  if (!container) return;

  container.innerHTML = upcoming.map((m, i) => {
    const t1 = m.t1 || m.team1 || 'TBA';
    const t2 = m.t2 || m.team2 || 'TBA';
    const venue = m.venue || '';
    const date  = m.date || m.dateTimeGMT || '';
    const fmt   = m.matchType || '';
    const t1country = t1.split(' ')[0];
    return `
      <a href="match-detail.html?id=${m.id || ''}" class="upcoming-row anim-up delay-${i+1}">
        <div class="team-flag" style="width:36px;height:36px;">${flCircle(t1, 36)}</div>
        <div style="flex:1">
          <div class="upcoming-teams">${esc(t1)} vs ${esc(t2)}</div>
          <div class="upcoming-meta"><i class="fa fa-location-dot"></i> ${esc(venue)} <span class="match-format-badge">${esc(fmt)}</span></div>
        </div>
        <div class="upcoming-time">${esc(date)}</div>
        <i class="fa fa-chevron-right" style="color:var(--text-muted);font-size:0.75rem;"></i>
      </a>`;
  }).join('');
}

// ── Trending players ──────────────────────────────────────────────────────────
async function loadTrendingPlayers() {
  const data = await apiFetch('/api/players?limit=4&sort=runs');
  if (!data || !data.players || !data.players.length) return;

  const container = document.querySelector('[data-trending-players]');
  if (!container) return;

  const delays = ['delay-1','delay-2','delay-3','delay-4'];
  const meta = await apiFetch('/api/meta/players') || {};

  container.innerHTML = data.players.map((p, i) => {
    const name = p.name || '';
    // Find country from meta or batting formats
    const playerMeta = Object.entries(meta).find(([k]) => k.toLowerCase().includes(name.toLowerCase().split(' ').pop()))?.[1] || {};
    const country = playerMeta.country || '';
    const isoCode = COUNTRY_ISO_MAP[country] || '';
    const photoUrl = playerMeta.image_url || '';

    // Stats — pick best format
    const bat = p.batting || {};
    const bowl = p.bowling || {};
    const fmts = ['ODI','T20I','Test'];
    const bestBat = fmts.map(f => bat[f]).find(s => s && s.innings > 5);
    const bestBowl = fmts.map(f => bowl[f]).find(s => s && s.wickets > 5);

    const avatarHtml = photoUrl
      ? `<img src="${photoUrl}" alt="${esc(name)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;" onerror="this.textContent='${name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()}'"/>`
      : `<span style="font-size:1.1rem;font-weight:700;color:var(--accent);">${name.split(' ').map(w=>w[0]).join('').slice(0,2).toUpperCase()}</span>`;

    const statsHtml = bestBat ? `
      <div class="player-stat"><div class="player-stat-val">${bestBat.average||'—'}</div><div class="player-stat-label">Avg</div></div>
      <div class="player-stat"><div class="player-stat-val">${bestBat.strike_rate||'—'}</div><div class="player-stat-label">SR</div></div>
      <div class="player-stat"><div class="player-stat-val">${bestBat.hundreds||'—'}</div><div class="player-stat-label">100s</div></div>
    ` : bestBowl ? `
      <div class="player-stat"><div class="player-stat-val">${bestBowl.average||'—'}</div><div class="player-stat-label">Avg</div></div>
      <div class="player-stat"><div class="player-stat-val">${bestBowl.economy||'—'}</div><div class="player-stat-label">Econ</div></div>
      <div class="player-stat"><div class="player-stat-val">${bestBowl.wickets||'—'}</div><div class="player-stat-label">Wkts</div></div>
    ` : '';

    return `
      <div class="card player-card anim-up ${delays[i]}">
        <div class="player-avatar" style="overflow:hidden;">${avatarHtml}</div>
        <div class="player-name">${esc(name)}</div>
        <div class="player-meta">${country ? `${fl(country,14)} ${esc(country)}` : ''}<span>·</span> ${p.batting ? 'Batsman' : 'Bowler'}</div>
        <div class="player-stat-row">${statsHtml}</div>
        <a href="player-profile.html?name=${encodeURIComponent(name)}" class="btn btn-secondary btn-sm" style="width:100%;justify-content:center;margin-top:0.3rem;">View Profile</a>
      </div>`;
  }).join('');
}

// ── Mini rankings ─────────────────────────────────────────────────────────────
async function loadMiniRankings() {
  const data = await apiFetch('/api/icc-rankings?category=teams&format=T20I');
  if (!data || !data.rankings || !data.rankings.length) return;

  const tbody = document.querySelector('.rankings-mini tbody');
  if (!tbody) return;

  const rankClass = ['rank-1','rank-2','rank-3'];
  tbody.innerHTML = data.rankings.slice(0, 6).map((r, i) => {
    const rc = rankClass[i] || '';
    const change = r.change || '—';
    const changeClass = change.includes('+') || change.includes('▲') ? 'rank-up' : change.includes('-') || change.includes('▼') ? 'rank-down' : 'rank-same';
    return `
      <tr>
        <td><span class="rank-num ${rc}">${r.rank}</span></td>
        <td class="bold">${fl(r.team,20)} ${esc(r.team)}</td>
        <td class="mono">${r.rating||'—'}</td>
        <td class="mono">${r.points||'—'}</td>
        <td><span class="rank-change ${changeClass}">${esc(change)}</span></td>
      </tr>`;
  }).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadLiveTicker();
  loadUpcoming();
  loadTrendingPlayers();
  loadMiniRankings();
});
