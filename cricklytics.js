/**
 * cricklytics.js
 * ==============
 * Shared utilities for all Cricklytics pages.
 * Handles: API calls, flag images, player photos, logo, nav search.
 *
 * Include in every page BEFORE page-specific scripts:
 *   <script src="cricklytics.js"></script>
 */

'use strict';

// ── API base URL ─────────────────────────────────────────────────────────────
const API = '';   // empty = same origin (Flask serves on localhost:5000)

// ── jsDelivr CDN flag base URL ────────────────────────────────────────────────
const FLAG_CDN = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/';

// ── Country name → ISO code map ───────────────────────────────────────────────
const COUNTRY_ISO = {
  'India':         'IN',
  'Australia':     'AU',
  'England':       'ENGLAND',
  'Pakistan':      'PK',
  'New Zealand':   'NZ',
  'South Africa':  'ZA',
  'West Indies':   'WI',
  'Sri Lanka':     'LK',
  'Bangladesh':    'BD',
  'Afghanistan':   'AF',
  'Zimbabwe':      'ZW',
  'Ireland':       'IE',
  'Netherlands':   'NL',
  'Scotland':      'GB-SCT',
  'Nepal':         'NP',
  'Oman':          'OM',
  'UAE':           'AE',
  'Papua New Guinea': 'PG',
  'Namibia':       'NA',
  'Canada':        'CA',
  'USA':           'US',
};

/**
 * Returns the jsDelivr SVG flag URL for a country name or ISO code.
 * Works on all browsers including Windows Chrome/Edge.
 * @param {string} countryOrCode - Country name (e.g. "India") or ISO code (e.g. "IN")
 * @returns {string} Full CDN URL to SVG flag image
 */
function flagUrl(countryOrCode) {
  const code = COUNTRY_ISO[countryOrCode] || countryOrCode;
  return `${FLAG_CDN}${code}.svg`;
}

/**
 * Creates a flag <img> element.
 * @param {string} country - Country name or ISO code
 * @param {number} size - Width/height in px (default 24)
 * @param {string} extraClass - Optional extra CSS class
 * @returns {HTMLImageElement}
 */
function flagImg(country, size = 24, extraClass = '') {
  const img = document.createElement('img');
  img.src = flagUrl(country);
  img.alt = country;
  img.width = size;
  img.height = size;
  img.style.cssText = `width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;flex-shrink:0;vertical-align:middle;`;
  if (extraClass) img.className = extraClass;
  // Fallback to emoji if CDN fails
  img.onerror = function() {
    const span = document.createElement('span');
    span.style.fontSize = `${Math.round(size * 0.8)}px`;
    span.style.lineHeight = '1';
    span.textContent = countryToEmoji(country);
    this.parentNode && this.parentNode.replaceChild(span, this);
  };
  return img;
}

/**
 * Replaces all elements with class 'flag-img' or data-flag attribute
 * with proper SVG flag images.
 * Call once after DOM is ready.
 */
function upgradeAllFlags() {
  // Replace emoji flags in elements with data-country or data-flag attribute
  document.querySelectorAll('[data-flag]').forEach(el => {
    const country = el.dataset.flag;
    const size = parseInt(el.dataset.flagSize || el.offsetWidth || 24);
    el.innerHTML = '';
    el.appendChild(flagImg(country, size));
  });

  // Also upgrade known flag container classes
  const flagSelectors = [
    '.team-flag',
    '.player-avatar',
    '.pcard-avatar',
    '.rank-flag',
    '.rank-flag-big',
    '.featured-flag',
    '.venue-country-flag',
    '.team-crest',
  ];

  flagSelectors.forEach(sel => {
    document.querySelectorAll(sel).forEach(el => {
      const text = el.textContent.trim();
      // Only replace if content is a single emoji flag (no other content)
      if (text && isEmojiFlag(text) && !el.querySelector('img')) {
        const country = emojiToCountry(text);
        if (country) {
          const size = sel.includes('big') || sel.includes('crest') || sel.includes('avatar') ? 44 : 24;
          const img = flagImg(country, size);
          img.style.borderRadius = '50%';
          el.textContent = '';
          el.appendChild(img);
        }
      }
    });
  });
}

/** Check if a string is purely a flag emoji */
function isEmojiFlag(str) {
  // Flag emojis are regional indicator pairs or tag sequences
  return /^\p{Regional_Indicator}{2}$/u.test(str.trim()) ||
         /^[\uD83C][\uDDE6-\uDDFF][\uD83C][\uDDE6-\uDDFF]$/.test(str.trim()) ||
         str.trim() === '🏴󠁧󠁢󠁥󠁮󠁧󠁿';  // England
}

/** Map flag emoji to country name */
function emojiToCountry(emoji) {
  const map = {
    '🇮🇳': 'India',
    '🇦🇺': 'Australia',
    '🏴󠁧󠁢󠁥󠁮󠁧󠁿': 'England',
    '🇵🇰': 'Pakistan',
    '🇳🇿': 'New Zealand',
    '🇿🇦': 'South Africa',
    '🇼🇸': 'West Indies',
    '🇱🇰': 'Sri Lanka',
    '🇧🇩': 'Bangladesh',
    '🇦🇫': 'Afghanistan',
    '🇿🇼': 'Zimbabwe',
    '🇮🇪': 'Ireland',
    '🇳🇱': 'Netherlands',
    '🇳🇵': 'Nepal',
    '🇦🇪': 'UAE',
  };
  return map[emoji] || null;
}

/** Fallback: country name to emoji */
function countryToEmoji(country) {
  const map = {
    'India':'🇮🇳','Australia':'🇦🇺','England':'🏴󠁧󠁢󠁥󠁮󠁧󠁿','Pakistan':'🇵🇰',
    'New Zealand':'🇳🇿','South Africa':'🇿🇦','West Indies':'🇼🇸','Sri Lanka':'🇱🇰',
    'Bangladesh':'🇧🇩','Afghanistan':'🇦🇫','Zimbabwe':'🇿🇼','Ireland':'🇮🇪',
  };
  return map[country] || '🏏';
}


// ── Player photos ─────────────────────────────────────────────────────────────

// Cache of player meta loaded from /api/meta/players
let _playersMeta = null;

async function getPlayersMeta() {
  if (_playersMeta) return _playersMeta;
  try {
    const res = await fetch(`${API}/api/meta/players`);
    if (res.ok) _playersMeta = await res.json();
  } catch (e) {}
  return _playersMeta || {};
}

/**
 * Returns the photo URL for a player from players_meta.json.
 * @param {string} cricsheetName - Cricsheet format name e.g. "V Kohli"
 * @returns {Promise<string>} image URL or empty string
 */
async function getPlayerPhotoUrl(cricsheetName) {
  const meta = await getPlayersMeta();
  return meta[cricsheetName]?.image_url || '';
}

/**
 * Creates a player avatar element: photo if available, initials fallback.
 * @param {string} playerName - Display name e.g. "Virat Kohli"
 * @param {string} cricsheetName - e.g. "V Kohli"
 * @param {string} country - Country name for flag fallback
 * @param {number} size - Size in px
 * @returns {HTMLElement}
 */
function playerAvatarEl(playerName, cricsheetName, country, size = 68) {
  const wrapper = document.createElement('div');
  wrapper.className = 'player-avatar-wrap';
  wrapper.style.cssText = `width:${size}px;height:${size}px;border-radius:50%;overflow:hidden;flex-shrink:0;position:relative;background:var(--surface-2);border:2px solid var(--border);display:flex;align-items:center;justify-content:center;`;

  // Show initials immediately
  const initials = (playerName || '?').split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
  wrapper.innerHTML = `<span style="font-size:${Math.round(size * 0.32)}px;font-weight:700;color:var(--accent);letter-spacing:0.05em;">${initials}</span>`;

  // Load photo asynchronously
  if (cricsheetName) {
    getPlayerPhotoUrl(cricsheetName).then(url => {
      if (url) {
        const img = document.createElement('img');
        img.src = url;
        img.alt = playerName;
        img.style.cssText = `width:100%;height:100%;object-fit:cover;border-radius:50%;`;
        img.onerror = () => {}; // keep initials on error
        img.onload = () => {
          wrapper.innerHTML = '';
          wrapper.appendChild(img);
        };
      }
    });
  }

  return wrapper;
}


// ── API helpers ───────────────────────────────────────────────────────────────

/**
 * Fetch from the Flask API with error handling.
 * @param {string} path - e.g. '/api/players?limit=24'
 * @returns {Promise<any>} parsed JSON or null on error
 */
async function apiFetch(path) {
  try {
    const res = await fetch(`${API}${path}`);
    if (!res.ok) {
      console.warn(`API ${path} returned ${res.status}`);
      return null;
    }
    return await res.json();
  } catch (e) {
    console.error(`API fetch failed: ${path}`, e);
    return null;
  }
}

/**
 * Get URL query parameter by name.
 * @param {string} name
 * @returns {string|null}
 */
function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

/**
 * Format a number with commas: 12345 → "12,345"
 */
function fmtNum(n) {
  if (n == null || n === '') return '—';
  return Number(n).toLocaleString();
}

/**
 * Format a stat value, showing '—' for zero/null/undefined
 */
function fmtStat(val, decimals = 1) {
  if (val == null || val === '' || val === 0) return '—';
  return typeof val === 'number' ? val.toFixed(decimals) : val;
}

/**
 * Build a flag + country name inline HTML string (safe, no XSS).
 * @param {string} country
 * @param {boolean} flagOnly - if true, only show flag image
 * @returns {string} HTML string
 */
function flagHtml(country, flagOnly = false) {
  const code = COUNTRY_ISO[country] || country;
  const url = `${FLAG_CDN}${code}.svg`;
  const imgHtml = `<img src="${url}" alt="${country}" style="width:18px;height:18px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;" onerror="this.style.display='none'">`;
  return flagOnly ? imgHtml : `${imgHtml}<span>${country}</span>`;
}

/**
 * Escape HTML to prevent XSS when inserting user/API data into innerHTML.
 */
function esc(str) {
  if (str == null) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}


// ── Navigation search ─────────────────────────────────────────────────────────

/**
 * Wire up the nav search bar to redirect to search.html on Enter.
 * Call once per page.
 */
function initNavSearch() {
  const input = document.querySelector('.nav-search');
  if (!input) return;
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && input.value.trim()) {
      window.location.href = `search.html?q=${encodeURIComponent(input.value.trim())}`;
    }
  });
}


// ── Logo upgrade ──────────────────────────────────────────────────────────────

/**
 * Replace the emoji/img1.png logo icons with logo.png.
 * Works for both navbar and footer.
 */
function upgradeLogo() {
  document.querySelectorAll('.nav-logo-icon').forEach(el => {
    el.innerHTML = `<img src="logo.png" alt="Cricklytics"
      style="height:32px;width:auto;max-width:120px;object-fit:contain;display:block;"
      onerror="this.style.display='none'">`;
    // Remove the background gradient since we have a real logo now
    el.style.background = 'transparent';
    el.style.boxShadow  = 'none';
    el.style.width      = 'auto';
    el.style.padding    = '0';
  });

  // Also hide the text "Cricklytics" next to logo since it's part of the image
  // Only hide if the logo image loaded successfully
  document.querySelectorAll('.nav-logo').forEach(logoLink => {
    const icon = logoLink.querySelector('.nav-logo-icon img');
    if (icon) {
      icon.addEventListener('load', () => {
        const textEl = logoLink.querySelector('.nav-logo-text');
        if (textEl) textEl.style.display = 'none';
      });
    }
  });
}


// ── WebCraft links fix ────────────────────────────────────────────────────────

/**
 * Update WebCraft watermark links to correct URLs.
 */
function fixWebcraftLinks() {
  const brand = document.querySelector('.webcraft-brand');
  if (brand) brand.href = 'https://webcraft-dev.vercel.app/';

  const contact = document.querySelector('.webcraft-contact');
  if (contact) contact.href = 'https://webcraft-dev.vercel.app/#contact';
}


// ── Mobile nav ────────────────────────────────────────────────────────────────

function toggleMobileNav() {
  const nav = document.getElementById('mobileNav');
  if (nav) nav.classList.toggle('open');
}


// ── Auto-init on DOM ready ────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', () => {
  initNavSearch();
  fixWebcraftLinks();
  upgradeLogo();
  // Flag upgrade is called per-page after dynamic content loads
});
