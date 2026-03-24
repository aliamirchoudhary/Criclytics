/**
 * venue-profile-api.js
 * ====================
 * API wiring for venue-profile.html
 * Reads ?name= from URL, loads full venue profile from API,
 * populates hero, stats, pitch info, top batters/bowlers, recent matches.
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
  'UAE':'AE','Netherlands':'NL',
};

function fl(country, size=16) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;"
    onerror="this.style.display='none'">`;
}

function dash(v) { return (v==null||v===0||v==='') ? '—' : v; }
function fmt1(v) { return (!v) ? '—' : Number(v).toFixed(1); }
function pct(v)  { return (!v) ? '—' : v + '%'; }

// ── Load and render ───────────────────────────────────────────────────────────
async function loadVenueProfile() {
  const venueName = getParam('name');
  if (!venueName) return;

  document.title = `${venueName} — Venue Profile · Criclytics`;

  // Update name elements immediately
  const nameEl = document.getElementById('venueName');
  const breadEl = document.getElementById('breadcrumbVenue');
  if (nameEl) nameEl.textContent = venueName;
  if (breadEl) breadEl.textContent = venueName;

  // Load all data in parallel
  const [venueData, venueMeta, batters, bowlers] = await Promise.all([
    apiFetch(`/api/venues/${encodeURIComponent(venueName)}`),
    apiFetch('/api/meta/venues'),
    apiFetch('/api/venues/' + encodeURIComponent(venueName)),
    null,
  ]);

  if (!venueData) return;

  const meta    = venueMeta?.[venueName] || {};
  const t20     = venueData.t20i || {};
  const odi     = venueData.odi  || {};
  const test    = venueData.test || {};

  // ── Hero location flag
  const country = meta.country || '';
  const iso = COUNTRY_ISO[country] || '';
  const heroFlag = document.getElementById('heroFlag');
  if (heroFlag && iso) {
    heroFlag.innerHTML = `<img src="${FLAG_BASE}${iso}.svg" alt="${country}"
      style="width:20px;height:20px;object-fit:cover;border-radius:2px;vertical-align:middle;"
      onerror="this.style.display='none'">`;
  }

  // Hero location text
  const locationEl = document.querySelector('.venue-hero-location');
  if (locationEl && meta.city) {
    const city = meta.city || '';
    const countryText = meta.country || '';
    locationEl.innerHTML = `
      ${iso ? `<img src="${FLAG_BASE}${iso}.svg" alt="${countryText}" style="width:20px;height:20px;object-fit:cover;border-radius:2px;vertical-align:middle;">` : ''}
      <i class="fa fa-location-dot"></i>
      ${esc(city)}${countryText ? ', ' + esc(countryText) : ''}`;
  }

  // ── Venue quick stats (top strip)
  const qsVals = document.querySelectorAll('.venue-qs-val, .vqs-val');
  if (qsVals.length >= 4) {
    qsVals[0].textContent = t20.avg_1st_innings ? Math.round(t20.avg_1st_innings) : '—';
    qsVals[1].textContent = odi.avg_1st_innings ? Math.round(odi.avg_1st_innings) : '—';
    qsVals[2].textContent = pct(venueData.chase_win_pct);
    qsVals[3].textContent = t20.highest || '—';
  }

  // ── Stats section cards
  renderStatCards(venueData, meta);

  // ── Top batters table
  const topBatters = venueData.top_batters || [];
  renderTopBatters(topBatters);

  // ── Top bowlers table
  const topBowlers = venueData.top_bowlers || [];
  renderTopBowlers(topBowlers);

  // ── Pitch profile (from static meta)
  renderPitchProfile(meta.pitch || {});

  // ── Venue info sidebar
  renderVenueInfo(meta);

  // ── Team win % section
  renderTeamWinPct(venueData);

  // ── Recent matches from CricAPI
  renderRecentMatches(venueName);
}

function renderStatCards(data, meta) {
  // Update stats in the Overview scoring section
  const t20 = data.t20i || {};
  const odi = data.odi  || {};

  // Map stat labels to values
  const updates = {
    'Avg 1st Innings (T20I)':  t20.avg_1st_innings ? Math.round(t20.avg_1st_innings) : '—',
    'Avg 2nd Innings (T20I)':  t20.avg_2nd_innings ? Math.round(t20.avg_2nd_innings) : '—',
    'Avg 1st Innings (ODI)':   odi.avg_1st_innings ? Math.round(odi.avg_1st_innings) : '—',
    'Highest T20I Total':      dash(t20.highest),
    'Lowest T20I Total':       dash(t20.lowest),
    'Highest ODI Total':       dash(odi.highest),
    'Chase Win %':             pct(data.chase_win_pct),
    'Defend Win %':            pct(data.defend_win_pct),
    'Toss Winner Win %':       pct(data.toss_winner_win_pct),
    'Avg Powerplay (T20I)':    t20.avg_powerplay ? Math.round(t20.avg_powerplay) : '—',
    'Avg Death (T20I)':        t20.avg_death ? Math.round(t20.avg_death) : '—',
    'Total Matches':           dash(data.matches),
  };

  document.querySelectorAll('.stat-card, .score-stat-card, .venue-stat-box').forEach(card => {
    const label = card.querySelector('.stat-label, .score-stat-label, .venue-stat-label')?.textContent?.trim();
    const valEl = card.querySelector('.stat-val, .score-stat-val, .venue-stat-val');
    if (label && valEl && updates[label] !== undefined) {
      valEl.textContent = updates[label];
    }
  });

  // Update wicket type breakdown if present
  const wicketTypes = data.wicket_types || {};
  if (Object.keys(wicketTypes).length) {
    const wktMap = {
      'caught':  'Caught',
      'bowled':  'Bowled',
      'lbw':     'LBW',
      'run out': 'Run Out',
      'stumped': 'Stumped',
    };
    document.querySelectorAll('.wkt-type-row').forEach(row => {
      const label = row.querySelector('.wkt-type-label')?.textContent?.trim().toLowerCase();
      const valEl = row.querySelector('.wkt-type-val');
      if (label && valEl) {
        const key = Object.keys(wktMap).find(k => wktMap[k].toLowerCase() === label);
        if (key && wicketTypes[key] !== undefined) {
          valEl.textContent = wicketTypes[key] + '%';
          const bar = row.querySelector('.wkt-bar-fill');
          if (bar) bar.style.width = wicketTypes[key] + '%';
        }
      }
    });
  }
}

function renderTopBatters(batters) {
  const tbody = document.querySelector('#panel-batters .data-table tbody, [data-top-batters] tbody');
  if (!tbody || !batters.length) return;
  tbody.innerHTML = batters.slice(0, 10).map((b, i) => `
    <tr>
      <td class="mono" style="color:var(--text-muted)">${i+1}</td>
      <td>
        <a href="player-profile.html?name=${encodeURIComponent(b.player)}"
          style="font-weight:600;color:var(--text-primary);text-decoration:none;">
          ${esc(b.player)}
        </a>
      </td>
      <td class="mono">${dash(b.matches)}</td>
      <td class="mono" style="color:var(--accent)">${dash(b.runs)}</td>
      <td class="mono">${fmt1(b.average)}</td>
      <td class="mono">${fmt1(b.strike_rate)}</td>
      <td class="mono">${dash(b.highest)}</td>
      <td class="mono">${dash(b.hundreds)}</td>
    </tr>`).join('');
}

function renderTopBowlers(bowlers) {
  const tbody = document.querySelector('#panel-bowlers .data-table tbody, [data-top-bowlers] tbody');
  if (!tbody || !bowlers.length) return;
  tbody.innerHTML = bowlers.slice(0, 10).map((b, i) => `
    <tr>
      <td class="mono" style="color:var(--text-muted)">${i+1}</td>
      <td>
        <a href="player-profile.html?name=${encodeURIComponent(b.player)}"
          style="font-weight:600;color:var(--text-primary);text-decoration:none;">
          ${esc(b.player)}
        </a>
      </td>
      <td class="mono">${dash(b.matches)}</td>
      <td class="mono" style="color:var(--accent)">${dash(b.wickets)}</td>
      <td class="mono">${fmt1(b.average)}</td>
      <td class="mono">${fmt1(b.economy)}</td>
    </tr>`).join('');
}

function renderPitchProfile(pitch) {
  if (!pitch || !Object.keys(pitch).length) return;
  const map = {
    'surface':    '.pitch-surface-val',
    'pace_factor':'.pitch-pace-val',
    'spin_factor':'.pitch-spin-val',
    'dew_factor': '.pitch-dew-val',
    'bounce':     '.pitch-bounce-val',
    'best_toss':  '.pitch-toss-val',
  };
  Object.entries(map).forEach(([key, sel]) => {
    const el = document.querySelector(sel);
    if (el && pitch[key]) el.textContent = pitch[key];
  });
}

function renderVenueInfo(meta) {
  if (!meta || !Object.keys(meta).length) return;
  const updates = {
    'Capacity':      meta.capacity ? meta.capacity.toLocaleString() : null,
    'Established':   meta.established,
    'Managed By':    meta.managed_by,
    'Ends':          meta.ends ? meta.ends.join(' · ') : null,
    'Floodlights':   meta.floodlights !== undefined ? (meta.floodlights ? 'Yes' : 'No') : null,
    'Notable Events': meta.notable_events ? meta.notable_events.join(', ') : null,
  };
  document.querySelectorAll('.venue-info-row').forEach(row => {
    const label = row.querySelector('.venue-info-label')?.textContent?.trim();
    const valEl = row.querySelector('.venue-info-val');
    if (label && valEl && updates[label]) valEl.textContent = updates[label];
  });

  // Update sidebar country
  const countryEl = document.getElementById('sidebarCountry');
  if (countryEl && meta.country) {
    const iso = COUNTRY_ISO[meta.country] || '';
    countryEl.innerHTML = iso
      ? `<img src="${FLAG_BASE}${iso}.svg" alt="${meta.country}" style="width:16px;height:16px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;"> ${esc(meta.country)}`
      : esc(meta.country);
  }
}

function renderTeamWinPct(venueData) {
  // Team win % is not in current API but could be added
  // Leaving for future ML iteration
}

async function renderRecentMatches(venueName) {
  const data = await apiFetch('/api/matches');
  if (!data?.data?.length) return;

  const atVenue = data.data
    .filter(m => (m.venue||'').toLowerCase().includes(venueName.toLowerCase().slice(0,10)))
    .slice(0, 3);

  if (!atVenue.length) return;

  const recentEl = document.querySelector('[data-recent] .matches-at-venue, #panel-recent');
  if (!recentEl) return;

  // Just update the upcoming teams divs
  const upcomingDivs = recentEl.querySelectorAll('.upcoming-teams');
  atVenue.forEach((m, i) => {
    if (!upcomingDivs[i]) return;
    const t1 = m.t1 || m.team1 || '';
    const t2 = m.t2 || m.team2 || '';
    upcomingDivs[i].textContent = `${t1} vs ${t2}`;
  });
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadVenueProfile);
