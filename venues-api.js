/**
 * venues-api.js
 * =============
 * API wiring for venues.html
 * Loads venue stats from /api/venues + static meta, renders cards
 * grouped by country with real flags and links.
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
  'UAE':'AE','Netherlands':'NL','Scotland':'GB-SCT',
};

function fl(country, size=20) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:6px;"
    onerror="this.style.display='none'">`;
}
function flCircle(country, size=22) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;vertical-align:middle;"
    onerror="this.style.display='none'">`;
}

// ── Pitch label from avg score ────────────────────────────────────────────────
function pitchLabel(avgT20) {
  if (!avgT20 || avgT20 === 0) return 'Balanced';
  if (avgT20 >= 185) return 'Flat · Very high-scoring';
  if (avgT20 >= 170) return 'Flat · High-scoring';
  if (avgT20 >= 155) return 'Batting friendly';
  if (avgT20 >= 140) return 'Balanced';
  return 'Bowling friendly';
}

// ── Render venue card ─────────────────────────────────────────────────────────
function renderVenueCard(venueName, stats, meta, delay='') {
  const country = meta?.country || guessCountry(venueName);
  const iso = COUNTRY_ISO[country] || '';
  const capacity = meta?.capacity ? meta.capacity.toLocaleString() : '—';
  const pitch = meta?.pitch?.surface || pitchLabel(stats?.t20i?.avg_1st_innings);
  const avgT20 = stats?.t20i?.avg_1st_innings ? Math.round(stats.t20i.avg_1st_innings) : '—';
  const avgOdi = stats?.odi?.avg_1st_innings ? Math.round(stats.odi.avg_1st_innings) : '—';
  const chasePct = stats?.chase_win_pct ? `${stats.chase_win_pct}%` : '—';
  const batFriendly = stats?.t20i?.avg_1st_innings
    ? Math.min(Math.round(stats.t20i.avg_1st_innings / 2), 85)
    : 50;
  const city = meta?.city || '';
  const location = [city, country].filter(Boolean).join(', ');

  return `
    <a href="venue-profile.html?name=${encodeURIComponent(venueName)}" class="venue-card anim-up ${delay}">
      <div class="venue-card-visual">
        <span class="venue-card-visual-icon"><i class="fa fa-building" style="font-size:1.8rem;color:rgba(255,255,255,0.4);"></i></span>
        <span class="venue-country-flag" style="overflow:hidden;">${iso ? flCircle(country, 22) : ''}</span>
        <span class="venue-capacity-badge"><i class="fa fa-users"></i> ${capacity}</span>
        <span class="venue-pitch-badge">${esc(pitch)}</span>
      </div>
      <div class="venue-card-body">
        <div class="venue-card-name">${esc(venueName)}</div>
        <div class="venue-card-location"><i class="fa fa-location-dot"></i> ${esc(location)}</div>
        <div class="venue-mini-stats">
          <div class="venue-mini-stat"><span class="venue-mini-stat-val">${avgT20}</span><span class="venue-mini-stat-label">Avg T20</span></div>
          <div class="venue-mini-stat"><span class="venue-mini-stat-val">${avgOdi}</span><span class="venue-mini-stat-label">Avg ODI</span></div>
          <div class="venue-mini-stat"><span class="venue-mini-stat-val">${chasePct}</span><span class="venue-mini-stat-label">Chase wins</span></div>
        </div>
      </div>
      <div class="venue-card-footer">
        <div class="bias-indicator">
          <span>Bat</span>
          <div class="bias-bar"><div class="bias-fill-bat" style="width:${batFriendly}%"></div></div>
          <span>${batFriendly}%</span>
        </div>
        <i class="fa fa-chevron-right venue-card-arrow"></i>
      </div>
    </a>`;
}

// ── Guess country from venue name ─────────────────────────────────────────────
function guessCountry(name) {
  const n = name.toLowerCase();
  if (n.includes('mumbai')||n.includes('delhi')||n.includes('kolkata')||
      n.includes('chennai')||n.includes('bengaluru')||n.includes('hyderabad')||
      n.includes('ahmedabad')||n.includes('pune')||n.includes('mohali')) return 'India';
  if (n.includes('melbourne')||n.includes('sydney')||n.includes('brisbane')||
      n.includes('adelaide')||n.includes('perth')||n.includes('woolloongabba')) return 'Australia';
  if (n.includes('lord')||n.includes('oval')||n.includes('edgbaston')||
      n.includes('headingley')||n.includes('trent')||n.includes('old trafford')) return 'England';
  if (n.includes('karachi')||n.includes('lahore')||n.includes('rawalpindi')||
      n.includes('multan')||n.includes('faisalabad')||n.includes('gaddafi')) return 'Pakistan';
  if (n.includes('newlands')||n.includes('wanderers')||n.includes('centurion')||
      n.includes('durban')||n.includes('port elizabeth')) return 'South Africa';
  if (n.includes('eden park')||n.includes('basin')||n.includes('hagley')||
      n.includes('seddon')||n.includes('university oval')) return 'New Zealand';
  if (n.includes('kensington')||n.includes('sabina')||n.includes('providence')) return 'West Indies';
  if (n.includes('colombo')||n.includes('galle')||n.includes('kandy')) return 'Sri Lanka';
  if (n.includes('dhaka')||n.includes('chittagong')||n.includes('sher-e-bangla')) return 'Bangladesh';
  if (n.includes('sharjah')||n.includes('dubai')||n.includes('abu dhabi')) return 'UAE';
  return '';
}

// ── Load and render all venues ────────────────────────────────────────────────
async function loadVenues() {
  const [venueStats, venueMeta] = await Promise.all([
    apiFetch('/api/venues'),
    apiFetch('/api/meta/venues'),
  ]);

  if (!venueStats || !Object.keys(venueStats).length) return;

  // Group venues by country
  const byCountry = {};
  Object.entries(venueStats).forEach(([name, stats]) => {
    const meta = venueMeta?.[name];
    const country = meta?.country || guessCountry(name);
    if (!country) return;
    if (!byCountry[country]) byCountry[country] = [];
    byCountry[country].push({ name, stats, meta });
  });

  // Sort countries by number of venues
  const sorted = Object.entries(byCountry).sort((a,b) => b[1].length - a[1].length);

  // Find the venues grid container
  const container = document.querySelector('.venue-groups');
  if (!container || !sorted.length) return;

  const delays = ['','delay-1','delay-2','delay-3','delay-4','delay-5'];
  const iso_map = COUNTRY_ISO;

  container.innerHTML = sorted.map(([country, venues]) => {
    const iso = iso_map[country] || '';
    const flagHtml = iso
      ? `<img src="${FLAG_BASE}${iso}.svg" alt="${country}" style="width:20px;height:20px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:6px;" onerror="this.style.display='none'">`
      : '';
    const cards = venues
      .sort((a,b) => (b.stats?.matches||0) - (a.stats?.matches||0))
      .slice(0, 6)
      .map((v, i) => renderVenueCard(v.name, v.stats, v.meta, delays[i % delays.length]))
      .join('');
    return `
      <div class="venue-group">
        <div class="venue-group-header">
          <span class="region-group-title">${flagHtml}${esc(country)}</span>
          <span style="font-size:0.75rem;color:var(--text-muted)">${venues.length} venues</span>
        </div>
        <div class="venue-cards-grid">${cards}</div>
      </div>`;
  }).join('');

  // Update hero count
  const totalVenues = Object.keys(venueStats).length;
  const heroCount = document.querySelector('.venues-hero p');
  if (heroCount) {
    heroCount.textContent = `Browse ${totalVenues}+ international venues with scoring stats, pitch profiles, and probability insights.`;
  }

  // Update sidebar
  renderSidebarStats(venueStats, venueMeta);
}

// ── Sidebar: most active + highest scoring venues ────────────────────────────
function renderSidebarStats(venueStats, venueMeta) {
  // Most active venues
  const mostActive = Object.entries(venueStats)
    .sort((a,b) => (b[1].matches||0) - (a[1].matches||0))
    .slice(0, 5);

  const activeEl = document.getElementById('mostActiveCard');
  if (activeEl) {
    activeEl.innerHTML = mostActive.map(([name, stats]) => {
      const meta = venueMeta?.[name] || {};
      const country = meta.country || guessCountry(name);
      return `
        <a href="venue-profile.html?name=${encodeURIComponent(name)}" class="svr-row">
          <span class="svr-flag">${flCircle(country, 22)}</span>
          <div class="svr-info">
            <div class="svr-name">${esc(name)}</div>
            <div class="svr-sub">${esc(country)} · ${stats.matches||0} matches</div>
          </div>
          <span class="svr-val">${stats.matches||0}</span>
        </a>`;
    }).join('');
  }

  // Highest avg T20 score venues
  const highestScoring = Object.entries(venueStats)
    .filter(([,s]) => s.t20i?.avg_1st_innings > 0)
    .sort((a,b) => (b[1].t20i?.avg_1st_innings||0) - (a[1].t20i?.avg_1st_innings||0))
    .slice(0, 5);

  const scoringEl = document.getElementById('highestScoringCard');
  if (scoringEl) {
    scoringEl.innerHTML = highestScoring.map(([name, stats]) => {
      const meta = venueMeta?.[name] || {};
      const country = meta.country || guessCountry(name);
      const avg = Math.round(stats.t20i.avg_1st_innings);
      return `
        <a href="venue-profile.html?name=${encodeURIComponent(name)}" class="svr-row">
          <span class="svr-flag">${flCircle(country, 22)}</span>
          <div class="svr-info">
            <div class="svr-name">${esc(name)}</div>
            <div class="svr-sub">${esc(country)}</div>
          </div>
          <span class="svr-val">${avg}</span>
        </a>`;
    }).join('');
  }
}

// ── Filter by search ──────────────────────────────────────────────────────────
function initSearch() {
  const searchEl = document.querySelector('.hero-search, .search-input');
  if (!searchEl) return;
  searchEl.addEventListener('input', e => {
    const q = e.target.value.toLowerCase().trim();
    document.querySelectorAll('.venue-card').forEach(card => {
      const name = card.querySelector('.venue-card-name')?.textContent?.toLowerCase() || '';
      const loc  = card.querySelector('.venue-card-location')?.textContent?.toLowerCase() || '';
      card.style.display = (!q || name.includes(q) || loc.includes(q)) ? '' : 'none';
    });
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadVenues();
  initSearch();
});
