/**
 * players-api.js
 * ==============
 * API wiring for players.html
 * Loads players from /api/players, handles search, filters, pagination,
 * grid/list view rendering, and player photo loading.
 */

'use strict';

const FLAG_BASE = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';
const COUNTRY_ISO = {
  'India':'IN','Australia':'AU','England':'ENGLAND','Pakistan':'PK',
  'New Zealand':'NZ','South Africa':'ZA','West Indies':'WI','Sri Lanka':'LK',
  'Bangladesh':'BD','Afghanistan':'AF','Zimbabwe':'ZW','Ireland':'IE',
};

// ── State ─────────────────────────────────────────────────────────────────────
let allPlayers   = [];
let playersMeta  = {};
let currentPage  = 1;
const PAGE_SIZE  = 24;
let activeFormat = '';
let activeSearch = '';
let activeSort   = 'runs';
let activeLetter = 'all';

// ── Helpers ───────────────────────────────────────────────────────────────────
function fl(country, size = 16) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_BASE}${code}.svg" alt="${country}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;"
    onerror="this.style.display='none'">`;
}

function flCircle(iso, size = 18) {
  return `<img src="${FLAG_BASE}${iso}.svg"
    style="position:absolute;bottom:-2px;right:-2px;width:${size}px;height:${size}px;border-radius:50%;border:1.5px solid var(--surface-1);object-fit:cover;"
    onerror="this.style.display='none'">`;
}

function initials(name) {
  return (name || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
}

function getBestStats(player) {
  const bat = player.batting || {};
  const bowl = player.bowling || {};
  for (const fmt of ['T20I', 'ODI', 'Test']) {
    if (bat[fmt] && bat[fmt].innings >= 3) return { type: 'bat', s: bat[fmt], fmt };
  }
  for (const fmt of ['T20I', 'ODI', 'Test']) {
    if (bowl[fmt] && bowl[fmt].wickets >= 3) return { type: 'bowl', s: bowl[fmt], fmt };
  }
  return null;
}

function getCountry(player) {
  const meta = playersMeta[player.name] || {};
  return meta.country || '';
}

function getIso(player) {
  const country = getCountry(player);
  return COUNTRY_ISO[country] || '';
}

function getPhotoUrl(player) {
  const meta = playersMeta[player.name] || {};
  return meta.image_url || '';
}

// ── Avatar HTML ───────────────────────────────────────────────────────────────
function avatarHtml(player, size = 52) {
  const ini  = initials(player.name);
  const iso  = getIso(player);
  const photo = getPhotoUrl(player);
  const photoHtml = photo
    ? `<img src="${photo}" alt="${esc(player.name)}" style="width:100%;height:100%;object-fit:cover;border-radius:50%;position:absolute;inset:0;">`
    : '';
  const flagBadge = iso ? flCircle(iso, size > 40 ? 18 : 14) : '';
  return `
    <div style="position:relative;width:${size}px;height:${size}px;border-radius:50%;background:var(--surface-2);border:2px solid var(--border);flex-shrink:0;display:flex;align-items:center;justify-content:center;overflow:visible;">
      <span style="font-size:${Math.round(size*0.28)}px;font-weight:700;color:var(--accent);">${ini}</span>
      ${photoHtml}
      ${flagBadge}
    </div>`;
}

// ── Render grid card ──────────────────────────────────────────────────────────
function renderCard(player, delay = '') {
  const stats = getBestStats(player);
  const country = getCountry(player);
  const iso = getIso(player);
  const formats = player.formats || [];

  let statsHtml = '';
  if (stats && stats.type === 'bat') {
    statsHtml = `
      <div class="pcard-stat"><div class="pcard-stat-val">${stats.s.average || '—'}</div><div class="pcard-stat-lbl">Avg</div></div>
      <div class="pcard-stat"><div class="pcard-stat-val">${stats.s.strike_rate || '—'}</div><div class="pcard-stat-lbl">SR</div></div>
      <div class="pcard-stat"><div class="pcard-stat-val">${stats.s.hundreds || '0'}</div><div class="pcard-stat-lbl">100s</div></div>`;
  } else if (stats && stats.type === 'bowl') {
    statsHtml = `
      <div class="pcard-stat"><div class="pcard-stat-val">${stats.s.average || '—'}</div><div class="pcard-stat-lbl">Avg</div></div>
      <div class="pcard-stat"><div class="pcard-stat-val">${stats.s.economy || '—'}</div><div class="pcard-stat-lbl">Econ</div></div>
      <div class="pcard-stat"><div class="pcard-stat-val">${stats.s.wickets || '0'}</div><div class="pcard-stat-lbl">Wkts</div></div>`;
  }

  const fmtBadges = formats.map(f => `<span class="pcard-fmt">${f}</span>`).join('');
  const countryHtml = country ? `<div class="pcard-country">${fl(country, 16)} ${esc(country)}</div>` : '';

  return `
    <a href="player-profile.html?name=${encodeURIComponent(player.name)}" class="pcard anim-up ${delay}">
      <div class="pcard-stripe"></div>
      <div class="pcard-body">
        <div class="pcard-top">
          ${avatarHtml(player, 52)}
          <div class="pcard-info">
            <div class="pcard-name">${esc(player.name)}</div>
            <div class="pcard-role">${stats ? (stats.type === 'bat' ? 'Batsman' : 'Bowler') : 'All-Rounder'}</div>
          </div>
        </div>
        ${countryHtml}
        <div class="pcard-stats">${statsHtml}</div>
        <div class="pcard-formats">${fmtBadges}</div>
      </div>
      <div class="pcard-footer">
        <span class="pcard-rank">${esc(player.name)}</span>
      </div>
    </a>`;
}

// ── Render list row ───────────────────────────────────────────────────────────
function renderRow(player, idx) {
  const stats = getBestStats(player);
  const country = getCountry(player);

  const s1 = stats ? (stats.type === 'bat' ? stats.s.average : stats.s.average) || '—' : '—';
  const s2 = stats ? (stats.type === 'bat' ? stats.s.strike_rate : stats.s.economy) || '—' : '—';
  const s3 = stats ? (stats.type === 'bat' ? stats.s.hundreds : stats.s.wickets) || '—' : '—';
  const l2 = stats ? (stats.type === 'bat' ? 'SR' : 'Econ') : 'SR';
  const l3 = stats ? (stats.type === 'bat' ? '100s' : 'Wkts') : '—';

  return `
    <a href="player-profile.html?name=${encodeURIComponent(player.name)}" class="prow">
      <span class="prow-num">${idx}</span>
      ${avatarHtml(player, 38)}
      <div class="prow-info">
        <div class="prow-name">${esc(player.name)}</div>
        <div class="prow-sub">${esc(country)} · ${(player.formats||[]).join(' / ')}</div>
      </div>
      <div class="prow-stat"><div class="prow-stat-val">${s1}</div><div class="prow-stat-lbl">Avg</div></div>
      <div class="prow-stat"><div class="prow-stat-val">${s2}</div><div class="prow-stat-lbl">${l2}</div></div>
      <div class="prow-stat"><div class="prow-stat-val">${s3}</div><div class="prow-stat-lbl">${l3}</div></div>
      <i class="fa fa-chevron-right" style="color:var(--text-muted);font-size:0.72rem;"></i>
    </a>`;
}

// ── Filter + paginate ─────────────────────────────────────────────────────────
function getFiltered() {
  let players = [...allPlayers];

  if (activeSearch) {
    const q = activeSearch.toLowerCase();
    players = players.filter(p => p.name.toLowerCase().includes(q));
  }

  if (activeFormat) {
    players = players.filter(p => (p.formats || []).includes(activeFormat));
  }

  if (activeLetter !== 'all') {
    players = players.filter(p => p.name.toUpperCase().startsWith(activeLetter));
  }

  // Sort
  players.sort((a, b) => {
    const aStats = getBestStats(a);
    const bStats = getBestStats(b);
    const aVal = aStats ? (aStats.type === 'bat' ? (aStats.s.runs || 0) : (aStats.s.wickets || 0)) : 0;
    const bVal = bStats ? (bStats.type === 'bat' ? (bStats.s.runs || 0) : (bStats.s.wickets || 0)) : 0;
    return bVal - aVal;
  });

  return players;
}

// ── Render current page ───────────────────────────────────────────────────────
function renderPage() {
  const filtered = getFiltered();
  const total = filtered.length;
  const start = (currentPage - 1) * PAGE_SIZE;
  const page  = filtered.slice(start, start + PAGE_SIZE);

  const delays = ['delay-1','delay-2','delay-3','delay-4','','delay-1','delay-2','delay-3'];

  // Grid view
  const gridView = document.getElementById('gridView');
  if (gridView) {
    gridView.innerHTML = page.map((p, i) => renderCard(p, delays[i % delays.length])).join('');
  }

  // List view
  const listView = document.getElementById('listView');
  if (listView) {
    // Keep header row
    const header = listView.querySelector('[style*="grid-template-columns"]');
    const headerHtml = header ? header.outerHTML : '';
    listView.innerHTML = headerHtml + page.map((p, i) => renderRow(p, start + i + 1)).join('');
  }

  // Results count
  const countEl = document.querySelector('.results-count');
  if (countEl) {
    countEl.innerHTML = `Showing <strong>${Math.min(PAGE_SIZE, total - start)}</strong> of <strong>${total.toLocaleString()}</strong> players`;
  }

  // Hero search count
  const heroCount = document.querySelector('.hero-search-count');
  if (heroCount) heroCount.textContent = `${total.toLocaleString()} players`;

  renderPagination(total);
}

// ── Pagination ────────────────────────────────────────────────────────────────
function renderPagination(total) {
  const totalPages = Math.ceil(total / PAGE_SIZE);
  const pag = document.querySelector('.pagination');
  if (!pag) return;

  let html = `<button class="page-btn ${currentPage === 1 ? 'disabled' : ''}" onclick="changePage(${currentPage - 1})"><i class="fa fa-chevron-left"></i></button>`;

  const pages = [];
  if (totalPages <= 7) {
    for (let i = 1; i <= totalPages; i++) pages.push(i);
  } else {
    pages.push(1);
    if (currentPage > 3) pages.push('...');
    for (let i = Math.max(2, currentPage-1); i <= Math.min(totalPages-1, currentPage+1); i++) pages.push(i);
    if (currentPage < totalPages - 2) pages.push('...');
    pages.push(totalPages);
  }

  pages.forEach(p => {
    if (p === '...') {
      html += `<span style="color:var(--text-muted);font-size:.85rem;padding:0 .3rem">…</span>`;
    } else {
      html += `<button class="page-btn ${p === currentPage ? 'active' : ''}" onclick="changePage(${p})">${p}</button>`;
    }
  });

  html += `<button class="page-btn ${currentPage === totalPages ? 'disabled' : ''}" onclick="changePage(${currentPage + 1})"><i class="fa fa-chevron-right"></i></button>`;
  pag.innerHTML = html;
}

function changePage(page) {
  const filtered = getFiltered();
  const totalPages = Math.ceil(filtered.length / PAGE_SIZE);
  if (page < 1 || page > totalPages) return;
  currentPage = page;
  renderPage();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}
window.changePage = changePage;

// ── Load data ─────────────────────────────────────────────────────────────────
async function loadPlayers() {
  // Load players index
  const data = await apiFetch('/api/players?limit=500&sort=runs');
  if (data && data.players) {
    allPlayers = data.players;
  }

  // Load meta for photos + countries
  const meta = await apiFetch('/api/meta/players');
  if (meta) playersMeta = meta;

  renderPage();
  updateFacetCounts();
}

function updateFacetCounts() {
  const total = allPlayers.length;
  // Update total count in facets
  const allRolesOpt = document.querySelector('.facet-opt.active .facet-count');
  if (allRolesOpt) allRolesOpt.textContent = total.toLocaleString();
}

// ── Event wiring ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadPlayers();

  // Hero search
  const heroSearch = document.getElementById('heroSearch');
  if (heroSearch) {
    heroSearch.addEventListener('input', e => {
      activeSearch = e.target.value.trim();
      currentPage = 1;
      renderPage();
    });
  }

  // Sort chips
  document.querySelectorAll('[data-sort]').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('[data-sort]').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeSort = btn.dataset.sort;
      currentPage = 1;
      renderPage();
    });
  });

  // Format chips
  document.querySelectorAll('[data-fmt]').forEach(btn => {
    btn.addEventListener('click', () => {
      const fmt = btn.dataset.fmt.toUpperCase().replace('T20','T20I');
      if (activeFormat === fmt) {
        activeFormat = '';
        btn.classList.remove('active');
      } else {
        document.querySelectorAll('[data-fmt]').forEach(b => b.classList.remove('active'));
        activeFormat = fmt;
        btn.classList.add('active');
      }
      currentPage = 1;
      renderPage();
    });
  });

  // Alpha bar
  document.querySelectorAll('.alpha-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.alpha-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeLetter = btn.dataset.letter || 'all';
      currentPage = 1;
      renderPage();
    });
  });

  // View toggle
  const gridView = document.getElementById('gridView');
  const listView = document.getElementById('listView');
  document.getElementById('gridViewBtn')?.addEventListener('click', () => {
    gridView.style.display = '';
    listView.style.display = 'none';
    document.getElementById('gridViewBtn').classList.add('active');
    document.getElementById('listViewBtn').classList.remove('active');
  });
  document.getElementById('listViewBtn')?.addEventListener('click', () => {
    listView.style.display = '';
    gridView.style.display = 'none';
    document.getElementById('listViewBtn').classList.add('active');
    document.getElementById('gridViewBtn').classList.remove('active');
  });
});
