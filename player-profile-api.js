/**
 * player-profile-api.js
 * =====================
 * Reads ?name= from URL, loads player from /api/players/<name>
 * which returns: {name, batting:{ODI:{},Test:{},T20I:{}}, bowling:{},
 *                formats[], yearly:{}, vs_opp:{}, at_venues:{}}
 */

function dash(v) { return (v==null||v===0||v==='') ? '—' : v; }
function fmt1(v) { return (!v) ? '—' : Number(v).toFixed(1); }

// ── Main loader ───────────────────────────────────────────────────────────────
async function loadProfile() {
  const playerName = getParam('name');
  if (!playerName) return;

  document.title = playerName + ' — Player Profile · Criclytics';

  // Update name immediately
  const nameEl  = document.getElementById('profileName');
  const breadEl = document.getElementById('breadcrumbName');
  if (nameEl)  nameEl.textContent  = playerName;
  if (breadEl) breadEl.textContent = playerName;

  // Fetch stats (includes yearly, vs_opp, at_venues)
  const stats = await apiFetch('/api/players/' + encodeURIComponent(playerName));
  
  // Fetch static meta (photo, DOB, country)
  const allMeta = await apiFetch('/api/meta/players') || {};
  const meta = allMeta[playerName]
    || Object.values(allMeta).find(function(m){ return (m.full_name||'').toLowerCase() === playerName.toLowerCase(); })
    || {};

  if (!stats) {
    // Player not found in Cricsheet data - show name at least
    if (nameEl) nameEl.textContent = playerName;
    if (breadEl) breadEl.textContent = playerName;
    document.title = playerName + ' — Player Profile · Criclytics';
    // Update initials
    var ini = playerName.split(' ').map(function(w){return w[0]||'';}).join('').slice(0,2).toUpperCase();
    var initialsEl2 = document.getElementById('profileInitials');
    if (initialsEl2) initialsEl2.textContent = ini;
    return;
  }

  // ── Display name & hero ───────────────────────────────────────────────────
  const displayName = meta.full_name || playerName;
  // country: meta has it for featured players; stats.country from Cricsheet for everyone else
  const country     = meta.country || stats.country || '';
  // Use stats.country from players_index (covers ALL players, not just 70 in meta)
  const isoCode     = meta.iso_code || stats.iso_code || COUNTRY_ISO[country] || COUNTRY_ISO[stats.country || ''] || '';
  const photoUrl    = meta.image_url || '';
  const initials    = displayName.split(' ').map(function(w){return w[0];}).join('').slice(0,2).toUpperCase();

  if (nameEl)  nameEl.textContent  = displayName;
  if (breadEl) breadEl.textContent = displayName;
  document.title = displayName + ' — Player Profile · Criclytics';

  var initialsEl = document.getElementById('profileInitials');
  var photoEl    = document.getElementById('profilePhoto');
  var flagEl     = document.getElementById('profileFlag');
  var activeDot  = document.getElementById('activeDot');

  if (initialsEl) initialsEl.textContent = initials;

  if (photoUrl && photoUrl.length > 0 && photoEl) {
    photoEl.src = photoUrl; photoEl.alt = displayName; photoEl.style.display = 'block';
    photoEl.onload  = function(){ if(initialsEl) initialsEl.style.display='none'; };
    photoEl.onerror = function(){ photoEl.style.display='none'; };
  }

  if (isoCode && flagEl) {
    flagEl.src = FLAG_CDN + isoCode + '.svg';
    flagEl.alt = country; flagEl.style.display = 'block';
  }

  // Full name line
  var fullNameEl = document.getElementById('profileFullName');
  if (fullNameEl) {
    var parts = [displayName];
    if (meta.dob) parts.push('Born: ' + meta.dob);
    if (meta.birthplace) parts.push(meta.birthplace);
    fullNameEl.textContent = parts.join(' · ');
  }

  // Country tag
  if (country) {
    var countryTag = document.querySelector('.profile-tags .ptag:first-child');
    if (countryTag) countryTag.innerHTML = '<i class="fa fa-flag" style="font-size:.65rem"></i> ' + country;
  }

  if (activeDot) activeDot.style.display = 'block';

  // ── Quick stats strip ─────────────────────────────────────────────────────
  var bat = stats.batting || {};
  var totalRuns = Object.values(bat).reduce(function(s,f){return s+(f.runs||0);},0);
  var totalHundreds = Object.values(bat).reduce(function(s,f){return s+(f.hundreds||0);},0);
  var totalFifties = Object.values(bat).reduce(function(s,f){return s+(f.fifties||0);},0);
  var totalMatches = Object.values(bat).reduce(function(s,f){return s+(f.matches||0);},0);
  var odiAvg = (bat['ODI'] || {}).average || 0;
  var t20Sr  = (bat['T20I'] || {}).strike_rate || 0;

  var qsVals = document.querySelectorAll('.qs-val');
  if (qsVals.length >= 6) {
    qsVals[0].textContent = totalRuns.toLocaleString();
    qsVals[1].textContent = fmt1(odiAvg);
    qsVals[2].textContent = totalHundreds;
    qsVals[3].textContent = fmt1(t20Sr);
    qsVals[4].textContent = totalMatches;
    qsVals[5].textContent = totalFifties;
  }

  // ── Bio grid ──────────────────────────────────────────────────────────────
  // Country comes from meta OR from stats.country (Cricsheet field)
  var bioCountry = country || stats.country || '';
  var bioIso = COUNTRY_ISO[bioCountry] || '';
  setBioValue('Full Name', displayName);
  if (meta.dob) setBioValue('Date of Birth', meta.dob + (meta.age ? ' (Age ' + meta.age + ')' : ''));
  if (meta.birthplace) setBioValue('Birthplace', meta.birthplace);
  if (meta.batting_style) setBioValue('Batting Style', meta.batting_style);
  if (meta.bowling_style) setBioValue('Bowling Style', meta.bowling_style);
  if (meta.role) setBioValue('Role', meta.role);
  if (meta.debut_test) setBioValue('Debut (Test)', meta.debut_test);
  if (meta.debut_odi)  setBioValue('Debut (ODI)',  meta.debut_odi);
  if (meta.debut_t20i) setBioValue('Debut (T20I)', meta.debut_t20i);

  // Nationality — always set, use stats.country if meta missing
  if (bioCountry) {
    var natEl = document.getElementById('bioNationality');
    if (natEl) {
      natEl.innerHTML = (bioIso
        ? '<img src="' + FLAG_CDN + bioIso + '.svg" alt="' + esc(bioCountry) + '" style="width:16px;height:16px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;" onerror="this.style.display=\'none\'">'
        : '')
        + esc(bioCountry);
    } else {
      setBioValue('Nationality', bioCountry);
    }
  }

  // Team (League) — set from meta.team, or national team, or dash
  var teamVal = meta.team || (country ? country : null);
  setBioValue('Team', teamVal || '—');

  // ── Recent form badges ────────────────────────────────────────────────────
  var form = stats.recent_form || [];
  if (form.length > 0) {
    var formStrip = document.querySelector('.form-strip');
    if (formStrip) {
      formStrip.innerHTML = form.slice(-10).map(function(score) {
        var cls = score >= 50 ? 'form-good' : score >= 20 ? 'form-ok' : 'form-poor';
        return '<div class="form-badge ' + cls + '" title="' + score + ' runs">' + score + '</div>';
      }).join('');
    }
  }

  // ── Format summary table ──────────────────────────────────────────────────
  var tbody = document.querySelector('#panel-overview .data-table tbody');
  if (tbody) {
    var rows = ['Test','ODI','T20I'].map(function(fmt) {
      var s = bat[fmt]; if (!s || !s.innings) return '';
      return '<tr><td class="bold">' + fmt + '</td>'
        + '<td class="mono">' + dash(s.matches) + '</td>'
        + '<td class="mono">' + dash(s.innings) + '</td>'
        + '<td class="mono" style="color:var(--accent)">' + dash(s.runs) + '</td>'
        + '<td class="mono">' + dash(s.highest) + '</td>'
        + '<td class="mono">' + fmt1(s.average) + '</td>'
        + '<td class="mono">' + fmt1(s.strike_rate) + '</td>'
        + '<td class="mono">' + dash(s.hundreds) + '</td>'
        + '<td class="mono">' + dash(s.fifties) + '</td></tr>';
    }).filter(Boolean).join('');
    if (rows) tbody.innerHTML = rows;
  }

  // ── Career stats with yearly data ─────────────────────────────────────────
  var yearly = stats.yearly || {};
  renderCareerTab(bat, yearly, 'ODI');  // default tab

  document.querySelectorAll('.fmt-tab').forEach(function(tab) {
    tab.addEventListener('click', function() {
      document.querySelectorAll('.fmt-tab').forEach(function(t){t.classList.remove('active');});
      tab.classList.add('active');
      // HTML data-fmt values: 'odi', 'test', 't20' (NOT t20i)
      var rawFmt = (tab.dataset.fmt || '').toLowerCase();
      var fmtKey = rawFmt === 't20' ? 'T20I' : rawFmt === 'test' ? 'Test' : 'ODI';
      // There is only one panel (fmt-odi) — we replace its content for each format
      renderCareerTab(bat, yearly, fmtKey);
      // Also update vs-teams and at-venues tables
      renderVsTeams(vsOpp, fmtKey);
      renderAtVenues(atVenues, fmtKey);
    });
  });

  // ── Vs Teams & At Venues — stored for format switching ───────────────────
  var vsOpp    = stats.vs_opp    || {};
  var atVenues = stats.at_venues || {};
  renderVsTeams(vsOpp, 'ODI');
  renderAtVenues(atVenues, 'ODI');

  // Inject format switcher into vs-teams and venues panels
  injectFmtSwitcher('#panel-vs-teams', function(fmtKey) {
    renderVsTeams(vsOpp, fmtKey);
    // Update section title
    var titleEl = document.querySelector('#panel-vs-teams .section-title-sm');
    if (titleEl) titleEl.innerHTML = '<i class="fa fa-shield-halved"></i> Performance vs Opposition (' + fmtKey + ')';
  });
  injectFmtSwitcher('#panel-venues', function(fmtKey) {
    renderAtVenues(atVenues, fmtKey);
    var titleEl = document.querySelector('#panel-venues .section-title-sm');
    if (titleEl) titleEl.innerHTML = '<i class="fa fa-location-dot"></i> Performance at Venues (' + fmtKey + ')';
  });

  // ── Sidebar milestones ────────────────────────────────────────────────────
  var totalRunsAll = Object.values(bat).reduce(function(s,f){return s+(f.runs||0);},0);
  var milRows = document.querySelectorAll('.aside-card:nth-child(2) .aside-stat-row');
  if (milRows.length >= 4) {
    milRows[0].querySelector('.aside-stat-val').textContent = totalHundreds;
    milRows[1].querySelector('.aside-stat-val').textContent = totalFifties;
    milRows[2].querySelector('.aside-stat-val').textContent = totalRunsAll.toLocaleString();
    milRows[3].querySelector('.aside-stat-val').textContent = ((bat['ODI']||{}).runs||0).toLocaleString();
  }

  // ── Sidebar vs opposition ─────────────────────────────────────────────────
  var vsOdiSorted = Object.entries(vsOpp['ODI']||{})
    .filter(function(e){return (e[1].innings||0)>=3;})
    .sort(function(a,b){return (b[1].average||0)-(a[1].average||0);})
    .slice(0,5);
  var h2hBody = document.querySelector('.aside-card:nth-child(3) .aside-card-body');
  if (h2hBody && vsOdiSorted.length) {
    h2hBody.innerHTML = vsOdiSorted.map(function(entry) {
      var opp = entry[0], s = entry[1];
      var iso = COUNTRY_ISO[opp] || '';
      var flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" style="width:20px;height:20px;object-fit:cover;border-radius:50%;vertical-align:middle;">' : '';
      return '<div class="head2head-row">'
        + '<span class="h2h-flag">' + flagHtml + '</span>'
        + '<span class="h2h-name">' + opp + '</span>'
        + '<span class="h2h-avg">' + fmt1(s.average) + '</span></div>';
    }).join('');
  }

  // ── ICC Rankings sidebar card ─────────────────────────────────────────────
  renderPlayerRankingsSidebar(displayName, country);

  // ── Similar Players sidebar card ──────────────────────────────────────────
  renderSimilarPlayersSidebar(displayName, country, stats);
}

function setBioValue(label, value) {
  document.querySelectorAll('.bio-row').forEach(function(row) {
    var lbl = row.querySelector('.bio-label');
    var val = row.querySelector('.bio-value');
    if (lbl && val && lbl.textContent.trim() === label) val.textContent = value;
  });
}

// ── Inject a format switcher bar into a panel ────────────────────────────────
function injectFmtSwitcher(panelSelector, onChange) {
  var panel = document.querySelector(panelSelector);
  if (!panel) return;
  // Don't double-inject
  if (panel.querySelector('.pp-fmt-switcher')) return;

  var switcher = document.createElement('div');
  switcher.className = 'pp-fmt-switcher';
  switcher.style.cssText = 'display:flex;gap:4px;margin-bottom:1rem;';

  var fmts = [
    { key: 'ODI',  label: 'ODI',  active: true },
    { key: 'Test', label: 'Test', active: false },
    { key: 'T20I', label: 'T20I', active: false },
  ];

  fmts.forEach(function(f) {
    var btn = document.createElement('button');
    btn.textContent = f.label;
    btn.dataset.fmt = f.key;
    btn.style.cssText = 'padding:4px 14px;border-radius:20px;border:1px solid var(--border);background:' + (f.active ? 'var(--accent)' : 'var(--surface-2)') + ';color:' + (f.active ? '#fff' : 'var(--text-secondary)') + ';font-size:.78rem;font-weight:600;cursor:pointer;transition:all .15s;';
    btn.addEventListener('click', function() {
      switcher.querySelectorAll('button').forEach(function(b) {
        b.style.background = 'var(--surface-2)';
        b.style.color = 'var(--text-secondary)';
      });
      btn.style.background = 'var(--accent)';
      btn.style.color = '#fff';
      onChange(f.key);
    });
    switcher.appendChild(btn);
  });

  // Insert before the first child of the panel
  panel.insertBefore(switcher, panel.firstChild);
}

function renderVsTeams(vsOpp, fmt) {
  var tbody = document.querySelector('#panel-vs-teams .data-table tbody');
  if (!tbody) return;
  var fmtData = vsOpp[fmt] || vsOpp['ODI'] || {};
  var sorted = Object.entries(fmtData).sort(function(a,b){return (b[1].runs||0)-(a[1].runs||0);});
  if (!sorted.length) return;
  tbody.innerHTML = sorted.slice(0,10).map(function(entry) {
    var opp = entry[0], s = entry[1];
    var iso = COUNTRY_ISO[opp] || '';
    var flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" style="width:16px;height:16px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:5px;" onerror="this.style.display=\'none\'">' : '';
    return '<tr><td class="bold">' + flagHtml + esc(opp) + '</td>'
      + '<td class="mono">' + dash(s.matches) + '</td>'
      + '<td class="mono">' + dash(s.innings) + '</td>'
      + '<td class="mono" style="color:var(--accent)">' + dash(s.runs) + '</td>'
      + '<td class="mono">' + fmt1(s.average) + '</td>'
      + '<td class="mono">' + fmt1(s.strike_rate) + '</td>'
      + '<td class="mono">' + dash(s.highest) + '</td>'
      + '<td class="mono">' + dash(s.hundreds) + '</td>'
      + '<td class="mono">' + dash(s.fifties) + '</td></tr>';
  }).join('');
}

function renderAtVenues(atVenues, fmt) {
  var tbody = document.querySelector('#panel-venues .data-table tbody');
  if (!tbody) return;
  var fmtData = atVenues[fmt] || atVenues['ODI'] || {};
  var sortedV = Object.entries(fmtData).sort(function(a,b){return (b[1].runs||0)-(a[1].runs||0);});
  if (!sortedV.length) return;
  tbody.innerHTML = sortedV.slice(0,8).map(function(entry) {
    var venue = entry[0], s = entry[1];
    return '<tr><td class="bold">' + esc(venue) + '</td>'
      + '<td class="mono">' + dash(s.innings) + '</td>'
      + '<td class="mono" style="color:var(--accent)">' + dash(s.runs) + '</td>'
      + '<td class="mono">' + fmt1(s.average) + '</td>'
      + '<td class="mono">' + fmt1(s.strike_rate) + '</td>'
      + '<td class="mono">' + dash(s.highest) + '</td>'
      + '<td class="mono">' + dash(s.hundreds) + '</td></tr>';
  }).join('');
}

function renderCareerTab(bat, yearly, fmt) {
  var s = bat[fmt];
  var panel = document.getElementById('fmt-odi') || document.querySelector('.fmt-panel');
  if (!panel) return;

  var boxes = panel.querySelectorAll('.stat-box-val');
  if (boxes.length >= 6) {
    boxes[0].textContent = s ? (s.runs||0).toLocaleString() : '—';
    boxes[1].textContent = s ? fmt1(s.average)    : '—';
    boxes[2].textContent = s ? fmt1(s.strike_rate) : '—';
    boxes[3].textContent = s ? dash(s.highest)    : '—';
    boxes[4].textContent = s ? dash(s.hundreds)   : '—';
    boxes[5].textContent = s ? dash(s.fifties)    : '—';
    if (boxes[6]) boxes[6].textContent = s ? dash(s.matches)   : '—';
    if (boxes[7]) boxes[7].textContent = s ? dash(s.not_outs)  : '—';
  }

  // Update "Year-by-Year (ODI Runs)" section title to reflect current format
  panel.querySelectorAll('.section-title-sm').forEach(function(el) {
    if (el.textContent.includes('Year')) el.textContent = 'Year-by-Year (' + fmt + ' Runs)';
  });
  // Update vs opposition and at venues section titles
  var vsEl = document.querySelector('#panel-vs-teams .section-title-sm');
  if (vsEl) vsEl.textContent = 'Performance vs Opposition (' + fmt + ')';
  var venueEl = document.querySelector('#panel-venues .section-title-sm');
  if (venueEl) venueEl.textContent = 'Performance at Venues (' + fmt + ')';

  var yearData = yearly[fmt] || {};
  var tbody = panel.querySelector('.data-table tbody');
  if (!tbody) return;
  var years = Object.keys(yearData).sort(function(a,b){return b-a;}).slice(0,8);
  if (!years.length) { tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;color:var(--text-muted);padding:1rem;">No ' + fmt + ' data available</td></tr>'; return; }
  tbody.innerHTML = years.map(function(yr) {
    var y = yearData[yr];
    return '<tr><td>' + yr + '</td>'
      + '<td class="mono">' + dash(y.matches)      + '</td>'
      + '<td class="mono">' + dash(y.innings)      + '</td>'
      + '<td class="mono" style="color:var(--accent)">' + dash(y.runs) + '</td>'
      + '<td class="mono">' + fmt1(y.average)      + '</td>'
      + '<td class="mono">' + fmt1(y.strike_rate)  + '</td>'
      + '<td class="mono">' + dash(y.hundreds)     + '</td>'
      + '<td class="mono">' + dash(y.fifties)      + '</td></tr>';
  }).join('');
}

async function renderPlayerRankingsSidebar(playerName, country) {
  // Find the ICC Rankings aside-card (first aside-card)
  var rankCard = document.querySelector('.aside-card:first-child');
  if (!rankCard) return;
  var head = rankCard.querySelector('.aside-card-head');
  if (!head || !head.textContent.toLowerCase().includes('rank')) return;

  var formats = ['T20I','ODI','Test'];
  var cats    = ['batting','bowling'];
  var results = [];

  for (var fi = 0; fi < formats.length; fi++) {
    for (var ci = 0; ci < cats.length; ci++) {
      var fmt = formats[fi];
      var cat = cats[ci];
      var fmtParam = fmt === 'T20I' ? 'T20I' : fmt;
      var data = await apiFetch('/api/icc-rankings?category=' + cat + '&format=' + fmtParam);
      if (!data || !data.rankings) continue;
      // Search for this player by abbreviated name match
      var entry = data.rankings.find(function(r) {
        var rname = (r.player||r.name||'').toLowerCase();
        var pparts = playerName.toLowerCase().split(' ');
        return pparts.some(function(part){ return part.length > 2 && rname.includes(part); });
      });
      if (entry) {
        results.push({ fmt: fmt, cat: cat, rank: entry.rank, rating: entry.rating });
      }
    }
  }

  if (!results.length) {
    // Player not found in rankings — replace hardcoded values with —
    var body0 = rankCard.querySelector('.aside-card-body');
    if (body0) {
      body0.innerHTML = ['ODI Batting','Test Batting','T20I Batting','All-Rounder'].map(function(lbl) {
        return '<div class="aside-stat-row"><span class="aside-stat-label">' + lbl + '</span><span class="aside-stat-val" style="color:var(--text-muted);">—</span></div>';
      }).join('');
    }
    return;
  }

  var body = rankCard.querySelector('.aside-card-body');
  if (!body) return;
  body.innerHTML = results.map(function(r) {
    var rankNum = parseInt(r.rank) || 0;
    var color = rankNum === 1 ? '#FFD700' : rankNum <= 3 ? '#C0C0C0' : 'var(--accent)';
    return '<div class="aside-stat-row">'
      + '<span class="aside-stat-label">' + esc(r.fmt) + ' ' + r.cat.charAt(0).toUpperCase() + r.cat.slice(1) + '</span>'
      + '<span class="aside-stat-val" style="color:' + color + ';">#' + esc(String(r.rank)) + ' <span style="font-size:0.7rem;color:var(--text-muted);">(' + esc(String(r.rating)) + ')</span></span>'
    + '</div>';
  }).join('');
}

async function renderSimilarPlayersSidebar(playerName, country, stats) {
  // Find Similar Players aside-card (last aside-card)
  var cards = document.querySelectorAll('.aside-card');
  var simCard = cards[cards.length - 1];
  if (!simCard) return;
  var head = simCard.querySelector('.aside-card-head');
  if (!head || !head.textContent.toLowerCase().includes('similar')) return;

  // Fetch players from same country with similar batting average
  var bat = stats.batting || {};
  var odiAvg = (bat['ODI'] || {}).average || 0;

  var data = await apiFetch('/api/players?limit=200&sort=runs');
  if (!data || !data.players) return;

  var similar = data.players.filter(function(p) {
    if (p.name === playerName) return false;
    // Same country (from country field added by process_cricsheet)
    if (p.country && country && p.country !== country) return false;
    // Similar batting average
    var pOdiAvg = ((p.batting||{})['ODI']||{}).average || 0;
    return pOdiAvg > 0 && Math.abs(pOdiAvg - odiAvg) < 15;
  }).slice(0, 3);

  if (!similar.length) return;

  var body = simCard.querySelector('.aside-card-body');
  if (!body) return;

  body.style.display = 'flex';
  body.style.flexDirection = 'column';
  body.style.gap = '0.6rem';

  body.innerHTML = similar.map(function(p) {
    var pCountry = p.country || country || '';
    var iso = COUNTRY_ISO[pCountry] || '';
    var initials = p.name.split(' ').map(function(w){return w[0]||'';}).join('').slice(0,2).toUpperCase();
    var pOdiAvg = fmt1(((p.batting||{})['ODI']||{}).average);
    return '<a href="player-profile.html?name=' + encodeURIComponent(p.name) + '" '
      + 'style="display:flex;align-items:center;gap:0.7rem;text-decoration:none;padding:0.3rem 0;transition:opacity var(--transition);" '
      + 'onmouseover="this.style.opacity=\'.75\'" onmouseout="this.style.opacity=\'1\'">'
      + '<div style="width:34px;height:34px;border-radius:50%;background:var(--surface-2);display:flex;align-items:center;justify-content:center;font-size:0.75rem;font-weight:700;color:var(--accent);border:1.5px solid var(--border);overflow:hidden;">'
        + (iso ? '<img src="'+FLAG_CDN+iso+'.svg" alt="'+esc(pCountry)+'" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">' : initials)
      + '</div>'
      + '<div>'
        + '<div style="font-size:.85rem;font-weight:600;color:var(--text-primary)">'+esc(p.name)+'</div>'
        + '<div style="font-size:.72rem;color:var(--text-muted)">Avg '+pOdiAvg+' · Batsman</div>'
      + '</div>'
    + '</a>';
  }).join('');
}

document.addEventListener('DOMContentLoaded', loadProfile);
