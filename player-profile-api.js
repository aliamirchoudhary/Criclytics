/**
 * player-profile-api.js
 * =====================
 * API wiring for player-profile.html
 * Reads ?name= from URL, loads full player profile from API,
 * populates all sections: hero, bio, stats, vs teams, venues, form.
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

function fl(country, size=16) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}" style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;" onerror="this.style.display='none'">`;
}

function flCircle(country, size=20) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${esc(country)}" style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;vertical-align:middle;" onerror="this.style.display='none'">`;
}

function dash(v) { return (v == null || v === 0 || v === '') ? '—' : v; }
function fmt1(v) { return (v == null || v === 0) ? '—' : Number(v).toFixed(1); }
function fmt2(v) { return (v == null || v === 0) ? '—' : Number(v).toFixed(2); }

// ── Load and render full profile ──────────────────────────────────────────────
async function loadProfile() {
  const playerName = getParam('name');
  if (!playerName) return; // show static default (Virat Kohli)

  // Load stats from Cricsheet pipeline
  const stats = await apiFetch(`/api/players/${encodeURIComponent(playerName)}`);

  // Load static meta (DOB, photo, country etc.)
  const allMeta  = await apiFetch('/api/meta/players') || {};
  // Find meta by matching name or Cricsheet key
  const meta = allMeta[playerName] ||
    Object.values(allMeta).find(m => m.full_name?.toLowerCase() === playerName.toLowerCase()) || {};

  if (!stats && !meta.full_name) return; // nothing found, keep static

  const displayName = meta.full_name || playerName;
  const country     = meta.country   || '';
  const isoCode     = COUNTRY_ISO[country] || '';
  const photoUrl    = meta.image_url || '';
  const initials    = displayName.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();

  // ── Update page title
  document.title = `${displayName} — Player Profile · Criclytics`;

  // ── Breadcrumb + name
  const nameEl = document.getElementById('profileName');
  const breadEl = document.getElementById('breadcrumbName');
  if (nameEl) nameEl.textContent = displayName;
  if (breadEl) breadEl.textContent = displayName;

  // ── Hero avatar: photo > initials + flag badge
  const initialsEl = document.getElementById('profileInitials');
  const photoEl    = document.getElementById('profilePhoto');
  const flagEl     = document.getElementById('profileFlag');
  const activeDot  = document.getElementById('activeDot');

  if (initialsEl) initialsEl.textContent = initials;

  if (photoUrl && photoEl) {
    photoEl.src = photoUrl;
    photoEl.alt = displayName;
    photoEl.style.display = 'block';
    photoEl.onload = () => { if (initialsEl) initialsEl.style.display = 'none'; };
    photoEl.onerror = () => { photoEl.style.display = 'none'; };
  }

  if (isoCode && flagEl) {
    flagEl.src = `${FLAG_BASE}${isoCode}.svg`;
    flagEl.alt = country;
    flagEl.style.display = 'block';
  }

  // ── Full name / bio line
  const fullNameEl = document.getElementById('profileFullName');
  if (fullNameEl && meta) {
    const dob = meta.dob ? new Date(meta.dob).toLocaleDateString('en-GB', {year:'numeric',month:'long',day:'numeric'}) : '';
    const birthplace = meta.birthplace || '';
    let parts = [displayName];
    if (dob) parts.push(`Born: ${dob}`);
    if (birthplace) parts.push(birthplace);
    fullNameEl.textContent = parts.join(' · ');
  }

  // ── Profile tags — country flag
  const tagsEl = document.querySelector('.profile-tags');
  if (tagsEl && country) {
    const countryTag = tagsEl.querySelector('.ptag:first-child');
    if (countryTag) {
      countryTag.innerHTML = `${fl(country, 12)} ${esc(country)}`;
    }
  }

  // ── Active dot
  if (activeDot && stats) {
    const isActive = (stats.recent_form || []).length > 0;
    activeDot.style.display = isActive ? 'block' : 'none';
  }

  if (!stats) return; // meta-only, no cricket stats available

  // ── Quick stats strip
  const allBat = stats.batting || {};
  const totalRuns = Object.values(allBat).reduce((s, f) => s + (f.runs || 0), 0);
  const totalHundreds = Object.values(allBat).reduce((s, f) => s + (f.hundreds || 0), 0);
  const totalFifties = Object.values(allBat).reduce((s, f) => s + (f.fifties || 0), 0);
  const totalMatches = Object.values(allBat).reduce((s, f) => s + (f.matches || 0), 0);
  const odiAvg = allBat['ODI']?.average || '—';
  const t20Sr  = allBat['T20I']?.strike_rate || '—';

  const qsVals = document.querySelectorAll('.qs-val');
  const qsLbls = document.querySelectorAll('.qs-lbl');
  if (qsVals.length >= 6) {
    qsVals[0].textContent = totalRuns.toLocaleString();
    qsVals[1].textContent = fmt1(odiAvg);
    qsVals[2].textContent = totalHundreds;
    qsVals[3].textContent = fmt1(t20Sr);
    qsVals[4].textContent = totalMatches;
    qsVals[5].textContent = totalFifties;
  }

  // ── Bio grid
  setBioValue('Full Name', displayName);
  if (meta.dob) {
    const age = meta.age || Math.floor((Date.now() - new Date(meta.dob)) / (365.25*24*3600*1000));
    setBioValue('Date of Birth', `${new Date(meta.dob).toLocaleDateString('en-GB',{year:'numeric',month:'long',day:'numeric'})} (Age ${age})`);
  }
  if (meta.birthplace) setBioValue('Birthplace', meta.birthplace);
  if (meta.batting_style) setBioValue('Batting Style', meta.batting_style);
  if (meta.bowling_style) setBioValue('Bowling Style', meta.bowling_style);
  if (meta.role) setBioValue('Role', meta.role);
  if (meta.ipl_team) setBioValue('Team', `${country}, ${meta.ipl_team} (IPL)`);
  if (meta.debut_test) setBioValue('Debut (Test)', meta.debut_test);
  if (meta.debut_odi)  setBioValue('Debut (ODI)',  meta.debut_odi);
  if (meta.debut_t20i) setBioValue('Debut (T20I)', meta.debut_t20i);

  // ── Nationality flag in bio
  if (country) {
    const bioNat = document.getElementById('bioNationality');
    if (bioNat) {
      const bioFlag = document.getElementById('bioFlag');
      if (bioFlag) {
        bioFlag.src = `${FLAG_BASE}${isoCode}.svg`;
        bioFlag.alt = country;
      }
      const textNode = bioNat.childNodes[bioNat.childNodes.length - 1];
      if (textNode && textNode.nodeType === 3) textNode.textContent = ` ${meta.nationality || country}`;
    }
  }

  // ── Recent form
  const form = stats.recent_form || [];
  if (form.length > 0) {
    const formStrip = document.querySelector('.form-strip');
    if (formStrip) {
      formStrip.innerHTML = form.slice(-10).map(score => {
        const cls = score >= 50 ? 'form-good' : score >= 20 ? 'form-ok' : 'form-poor';
        return `<div class="form-badge ${cls}" title="${score} runs">${score}</div>`;
      }).join('');
    }
  }

  // ── Format summary table
  renderFormatSummary(stats);

  // ── Career stats (format sub-tabs)
  renderCareerStats(stats);

  // ── Vs Teams table
  renderVsTeams(stats);

  // ── At Venues table
  renderVenues(stats);

  // ── Sidebar milestones
  renderMilestones(stats);

  // ── Sidebar vs opposition
  renderSidebarVsOpp(stats);
}

function setBioValue(label, value) {
  const bioRows = document.querySelectorAll('.bio-row');
  bioRows.forEach(row => {
    const labelEl = row.querySelector('.bio-label');
    const valueEl = row.querySelector('.bio-value');
    if (labelEl && labelEl.textContent.trim() === label && valueEl) {
      valueEl.textContent = value;
    }
  });
}

function renderFormatSummary(stats) {
  const tbody = document.querySelector('#panel-overview .data-table tbody');
  if (!tbody) return;
  const bat = stats.batting || {};
  const rows = ['Test','ODI','T20I'].map(fmt => {
    const s = bat[fmt];
    if (!s) return '';
    return `<tr>
      <td class="bold">${fmt}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono">${dash(s.innings)}</td>
      <td class="mono" style="color:var(--accent)">${dash(s.runs)}</td>
      <td class="mono">${dash(s.highest)}</td>
      <td class="mono">${fmt1(s.average)}</td>
      <td class="mono">${fmt1(s.strike_rate)}</td>
      <td class="mono">${dash(s.hundreds)}</td>
      <td class="mono">${dash(s.fifties)}</td>
    </tr>`;
  }).join('');
  tbody.innerHTML = rows || '<tr><td colspan="9" style="text-align:center;color:var(--text-muted)">No batting data</td></tr>';
}

function renderCareerStats(stats) {
  const bat = stats.batting || {};
  // Wire format sub-tabs
  document.querySelectorAll('.fmt-tab').forEach(tab => {
    tab.addEventListener('click', () => {
      document.querySelectorAll('.fmt-tab').forEach(t => t.classList.remove('active'));
      tab.classList.add('active');
      const fmt = tab.dataset.fmt.toUpperCase().replace('T20','T20I');
      updateCareerPanel(bat[fmt], fmt);
    });
  });
  // Show ODI by default
  updateCareerPanel(bat['ODI'], 'ODI');
}

function updateCareerPanel(s, fmt) {
  if (!s) return;
  const boxes = document.querySelectorAll('#fmt-odi .stat-box-val');
  if (!boxes.length) return;
  boxes[0].textContent = (s.runs || 0).toLocaleString();
  boxes[1].textContent = fmt1(s.average);
  boxes[2].textContent = fmt1(s.strike_rate);
  boxes[3].textContent = dash(s.highest);
  boxes[4].textContent = dash(s.hundreds);
  boxes[5].textContent = dash(s.fifties);
  boxes[6].textContent = dash(s.matches);
  if (boxes[7]) boxes[7].textContent = dash(s.not_outs);

  // Year table
  const yearData = stats?.yearly?.[getParam('name')] || {};
  const fmtYears = yearData[fmt] || {};
  const tbody = document.querySelector('#fmt-odi .data-table tbody');
  if (!tbody) return;
  const years = Object.keys(fmtYears).sort((a,b) => b-a).slice(0, 8);
  tbody.innerHTML = years.map(yr => {
    const y = fmtYears[yr];
    return `<tr>
      <td>${yr}</td>
      <td class="mono">${dash(y.matches)}</td>
      <td class="mono">${dash(y.innings)}</td>
      <td class="mono" style="color:var(--accent)">${dash(y.runs)}</td>
      <td class="mono">${fmt1(y.average)}</td>
      <td class="mono">${fmt1(y.strike_rate)}</td>
      <td class="mono">${dash(y.hundreds)}</td>
      <td class="mono">${dash(y.fifties)}</td>
    </tr>`;
  }).join('') || '<tr><td colspan="8" style="text-align:center;color:var(--text-muted)">No yearly data</td></tr>';
}

function renderVsTeams(stats) {
  const vsOpp = stats?.vs_opp || {};
  const tbody = document.querySelector('#panel-vs-teams .data-table tbody');
  if (!tbody) return;
  // Get ODI data
  const odiVs = vsOpp['ODI'] || {};
  const sorted = Object.entries(odiVs).sort((a,b) => (b[1].runs||0) - (a[1].runs||0));
  if (!sorted.length) return;
  tbody.innerHTML = sorted.slice(0, 10).map(([opp, s]) => {
    return `<tr>
      <td class="bold">${fl(opp, 18)}${esc(opp)}</td>
      <td class="mono">${dash(s.innings)}</td>
      <td class="mono">${dash(s.innings)}</td>
      <td class="mono" style="color:var(--accent)">${dash(s.runs)}</td>
      <td class="mono">${fmt1(s.average)}</td>
      <td class="mono">${fmt1(s.strike_rate)}</td>
      <td class="mono">${dash(s.highest)}</td>
      <td class="mono">${dash(s.hundreds)}</td>
      <td class="mono">${dash(s.fifties)}</td>
    </tr>`;
  }).join('');
}

function renderVenues(stats) {
  const atVenues = stats?.at_venues || {};
  const tbody = document.querySelector('#panel-venues .data-table tbody');
  if (!tbody) return;
  const odiVenues = atVenues['ODI'] || {};
  const sorted = Object.entries(odiVenues).sort((a,b) => (b[1].runs||0) - (a[1].runs||0));
  if (!sorted.length) return;
  tbody.innerHTML = sorted.slice(0, 8).map(([venue, s]) => {
    return `<tr>
      <td class="bold">${esc(venue)}</td>
      <td class="mono">${dash(s.innings)}</td>
      <td class="mono" style="color:var(--accent)">${dash(s.runs)}</td>
      <td class="mono">${fmt1(s.average)}</td>
      <td class="mono">${fmt1(s.strike_rate)}</td>
      <td class="mono">${dash(s.highest)}</td>
      <td class="mono">${dash(s.hundreds)}</td>
    </tr>`;
  }).join('');
}

function renderMilestones(stats) {
  const bat = stats.batting || {};
  const totalRuns = Object.values(bat).reduce((s, f) => s + (f.runs||0), 0);
  const totalHundreds = Object.values(bat).reduce((s, f) => s + (f.hundreds||0), 0);
  const totalFifties = Object.values(bat).reduce((s, f) => s + (f.fifties||0), 0);
  const highest = Math.max(...Object.values(bat).map(f => f.highest || 0));

  const milestoneRows = document.querySelectorAll('.aside-card:nth-child(2) .aside-stat-row');
  if (milestoneRows.length >= 5) {
    milestoneRows[0].querySelector('.aside-stat-val').textContent = totalHundreds;
    milestoneRows[1].querySelector('.aside-stat-val').textContent = totalFifties;
    milestoneRows[2].querySelector('.aside-stat-val').textContent = totalRuns.toLocaleString();
    milestoneRows[3].querySelector('.aside-stat-val').textContent = (bat['ODI']?.runs || 0).toLocaleString();
    milestoneRows[4].querySelector('.aside-stat-val').textContent = highest;
  }
}

function renderSidebarVsOpp(stats) {
  const vsOpp = stats?.vs_opp?.['ODI'] || {};
  const sorted = Object.entries(vsOpp)
    .filter(([,s]) => s.innings >= 3)
    .sort((a,b) => (b[1].average||0) - (a[1].average||0))
    .slice(0, 5);

  const h2hBody = document.querySelector('.aside-card:nth-child(3) .aside-card-body');
  if (!h2hBody || !sorted.length) return;

  h2hBody.innerHTML = sorted.map(([opp, s]) => `
    <div class="head2head-row">
      <span class="h2h-flag">${flCircle(opp, 20)}</span>
      <span class="h2h-name">${esc(opp)}</span>
      <span class="h2h-avg">${fmt1(s.average)}</span>
    </div>`).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadProfile);
