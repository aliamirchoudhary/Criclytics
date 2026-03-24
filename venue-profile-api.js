/**
 * venue-profile-api.js — complete rewrite
 * Loads venue data from /api/venues/{name} and /api/meta/venues
 * Updates ALL hardcoded values on venue-profile.html
 */

var _venueData = null;
var _venueMeta = {};
var _activeFmt = 't20';

function d(v) { return (v == null || v === '' || v === 0) ? '—' : v; }
function f1(v) { return (!v && v !== 0) ? '—' : Number(v).toFixed(1); }

function flImg(country, size) {
  var code = COUNTRY_ISO[country] || '';
  if (!code) return '';
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:3px;" onerror="this.style.display=\'none\'">';
}

function guessCountry(name) {
  var n = (name || '').toLowerCase();
  if (/mumbai|wankhede|delhi|kolkata|eden|chennai|bengaluru|chinnaswamy|hyderabad|rajiv|ahmedabad|modi|pune|mohali|dharamsala|ranchi|nagpur|indore|chepauk|feroz/.test(n)) return 'India';
  if (/melbourne|mcg|sydney|scg|brisbane|gabba|adelaide|perth|waca|optus|manuka|bellerive/.test(n)) return 'Australia';
  if (/lord|oval|edgbaston|headingley|trent|old trafford|chester|rose bowl|riverside|hampshire/.test(n)) return 'England';
  if (/karachi|lahore|gaddafi|rawalpindi|multan|faisalabad|iqbal|niaz/.test(n)) return 'Pakistan';
  if (/newlands|wanderers|centurion|durban|kingsmead|port elizabeth|st george/.test(n)) return 'South Africa';
  if (/eden park|basin|hagley|seddon|mclean|university oval|bay oval/.test(n)) return 'New Zealand';
  if (/kensington|sabina|providence|queen.s park|warner/.test(n)) return 'West Indies';
  if (/colombo|galle|kandy|pallekele|premadasa/.test(n)) return 'Sri Lanka';
  if (/dhaka|chittagong|sher-e-bangla|sylhet|mirpur|zahur/.test(n)) return 'Bangladesh';
  if (/sharjah|dubai|abu dhabi|zayed/.test(n)) return 'UAE';
  if (/harare|bulawayo|queens/.test(n)) return 'Zimbabwe';
  if (/kabul|khost|jalalabad/.test(n)) return 'Afghanistan';
  return '';
}

// ─── Venue information card (info-row elements) ───────────────────────────────
function renderVenueInfoCard(name, data, meta) {
  var country = (meta && meta.country) || guessCountry(name);
  var city = meta && meta.city || '';
  var location = [city, country].filter(Boolean).join(', ');
  var map = {
    'Full name':       name,
    'Location':        location || country,
    'Established':     (meta && meta.established) ? String(meta.established) : null,
    'Capacity':        (meta && meta.capacity) ? Number(meta.capacity).toLocaleString() + ' (seated)' : null,
    'Managed by':      (meta && meta.managed_by) || null,
    'Ends':            (meta && meta.ends && meta.ends.join) ? meta.ends.join(' · ') : null,
    'Notable events':  (meta && meta.notable_events && meta.notable_events.join) ? meta.notable_events.join(' · ') : null,
    'Floodlights':     (meta && meta.floodlights !== undefined) ? (meta.floodlights ? 'Yes · Day/Night matches supported' : 'No') : null,
  };
  document.querySelectorAll('.info-row').forEach(function(row) {
    var lbl = ((row.querySelector('.info-row-label') || {}).textContent || '').trim();
    var valEl = row.querySelector('.info-row-value');
    if (valEl && map[lbl] != null) valEl.textContent = map[lbl];
  });
}

// ─── Hero quick-stat chips ────────────────────────────────────────────────────
function renderHeroStats(data, meta) {
  var t20 = data.t20i || {};
  var odi = data.odi  || {};
  var country = (meta && meta.country) || '';
  var iso = COUNTRY_ISO[country] || '';

  // Location line
  var locEl = document.querySelector('.venue-hero-location');
  if (locEl) {
    var city = (meta && meta.city) || '';
    var loc  = [city, country].filter(Boolean).join(', ');
    var flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(country) + '" style="width:20px;height:20px;object-fit:cover;border-radius:2px;vertical-align:middle;" onerror="this.style.display=\'none\'">' : '';
    locEl.innerHTML = '<span id="heroFlag">' + flagHtml + '</span> <i class="fa fa-location-dot"></i> ' + esc(loc || 'International Venue');
  }

  // Quick stat chips
  var chips = {
    'Capacity':      meta && meta.capacity ? Number(meta.capacity).toLocaleString() : null,
    'Est.':          meta && meta.established ? String(meta.established) : null,
    'Intl. Matches': data.matches ? String(data.matches) : null,
    'Avg T20 Score': t20.avg_1st_innings ? String(Math.round(t20.avg_1st_innings)) : null,
    'Avg ODI Score': odi.avg_1st_innings  ? String(Math.round(odi.avg_1st_innings))  : null,
    'Chase Win %':   data.chase_win_pct   ? data.chase_win_pct + '%'                 : null,
  };
  document.querySelectorAll('.venue-qs').forEach(function(chip) {
    var lbl = ((chip.querySelector('.venue-qs-label') || {}).textContent || '').trim();
    var valEl = chip.querySelector('.venue-qs-value');
    if (valEl && chips[lbl] != null) valEl.textContent = chips[lbl];
  });
}

// ─── Overview: scoring stat grid ─────────────────────────────────────────────
function renderOverviewStats(data) {
  var t20 = data.t20i || {};
  var odi = data.odi  || {};
  var map = {
    'Avg 1st Innings (T20)': t20.avg_1st_innings ? Math.round(t20.avg_1st_innings) : null,
    'Avg 2nd Innings (T20)': t20.avg_2nd_innings ? Math.round(t20.avg_2nd_innings) : null,
    'Highest T20 Total':     t20.highest || null,
    'Avg 1st Innings (ODI)': odi.avg_1st_innings ? Math.round(odi.avg_1st_innings) : null,
    'Avg Powerplay Score':   t20.avg_powerplay ? Math.round(t20.avg_powerplay) + '/2' : null,
    'Avg Death Score':       t20.avg_death     ? Math.round(t20.avg_death)     + '/2' : null,
  };
  document.querySelectorAll('.overview-stat').forEach(function(card) {
    var lbl = ((card.querySelector('.overview-stat-label') || {}).textContent || '').trim();
    var valEl = card.querySelector('.overview-stat-value');
    if (valEl && map[lbl] != null) valEl.textContent = map[lbl];
  });
}

// ─── Pitch profile ────────────────────────────────────────────────────────────
function renderPitchProfile(data, meta) {
  var t20 = data.t20i || {};
  var pitch = (meta && meta.pitch) || {};

  // Text rows
  var pitchMap = {
    'Surface type': pitch.surface || null,
    'Pace factor':  pitch.pace_factor || null,
    'Spin factor':  pitch.spin_factor || null,
    'Dew factor':   pitch.dew_factor || null,
    'Bounce':       pitch.bounce || null,
    'Best toss decision': pitch.toss_decision || null,
  };
  document.querySelectorAll('.pitch-detail-row').forEach(function(row) {
    var lbl = ((row.querySelector('.pitch-detail-label') || {}).textContent || '').trim();
    var valEl = row.querySelector('.pitch-detail-value');
    if (valEl && pitchMap[lbl] != null) valEl.textContent = pitchMap[lbl];
  });

  // Bat/bowl bias bar — computed from chase win %
  // If chasing wins 61%, batting is strong → bat-friendly = chase_win_pct (capped 30–85)
  var chasePct  = data.chase_win_pct || 50;
  var batFriendly  = Math.max(30, Math.min(85, chasePct));
  var bowlFriendly = 100 - batFriendly;
  var batFill  = document.querySelector('.bias-bat-fill');
  var bowlFill = document.querySelector('.bias-bowl-fill');
  if (batFill)  batFill.style.width  = batFriendly  + '%';
  if (bowlFill) bowlFill.style.width = bowlFriendly + '%';

  // Update the label text
  var labels = document.querySelectorAll('.bias-full-label span');
  if (labels[0]) labels[0].textContent = 'Batting-friendly (' + batFriendly + '%)';
  if (labels[1]) labels[1].textContent = 'Bowling-friendly (' + bowlFriendly + '%)';
}

// ─── Match Statistics tab — format switcher ───────────────────────────────────
function renderStatsForFmt(fmt) {
  if (!_venueData) return;
  var fmtKey = fmt === 'odi' ? 'odi' : fmt === 'test' ? 'test' : 't20i';
  var s = _venueData[fmtKey] || {};
  var fmtLabel = fmt === 'odi' ? 'ODI' : fmt === 'test' ? 'Test' : 'T20I';

  // Update section title
  var statsCard0 = document.querySelector('#panel-stats .section-card');
  var statsHeader = statsCard0 ? statsCard0.querySelector('.section-card-title') : null;
  if (statsHeader) statsHeader.innerHTML = '<i class="fa fa-chart-bar"></i> Scoring Statistics — ' + fmtLabel;

  var rowMap = {
    'Average 1st innings total':  s.avg_1st_innings ? Math.round(s.avg_1st_innings) : '—',
    'Average 2nd innings total':  s.avg_2nd_innings ? Math.round(s.avg_2nd_innings) : '—',
    'Highest total':              d(s.highest),
    'Lowest total':               d(s.lowest),
    'Average powerplay score':    s.avg_powerplay   ? Math.round(s.avg_powerplay) + ' / 2' : '—',
    'Average death-over score':   s.avg_death       ? Math.round(s.avg_death)     + ' / 2' : '—',
    'Batting first wins':         _venueData.defend_win_pct != null ? (100 - (_venueData.chase_win_pct || 0)) + '%' : '—',
    'Chasing wins':               _venueData.chase_win_pct  != null ? _venueData.chase_win_pct + '%' : '—',
    'Toss winner win %':          _venueData.toss_winner_win_pct != null ? _venueData.toss_winner_win_pct + '%' : '—',
  };

  // Use first .section-card inside #panel-stats (not :first-child which would match the switcher div)
  var statsCard = document.querySelector('#panel-stats .section-card');
  var statRows = statsCard ? statsCard.querySelectorAll('.stat-row') : [];
  Array.prototype.forEach.call(statRows, function(row) {
    var lbl = ((row.querySelector('.stat-row-label') || {}).textContent || '').trim();
    var valEl = row.querySelector('.stat-row-value');
    if (valEl && rowMap[lbl] !== undefined) valEl.textContent = rowMap[lbl];
  });

  // Update wicket breakdown bars
  var wickets = s.wicket_types || _venueData.wicket_types || {};
  var wktMap  = { 'Caught': 'caught', 'Bowled': 'bowled', 'LBW': 'lbw', 'Run Out': 'run out', 'Stumped': 'stumped' };
  // Second .section-card in #panel-stats contains wicket breakdown
  var statsCards = document.querySelectorAll('#panel-stats .section-card');
  var wktCard = statsCards && statsCards[1];
  var wktBlocks = wktCard ? wktCard.querySelectorAll('div > div') : [];
  Array.prototype.forEach.call(wktBlocks, function(block) {
    var spans = block.querySelectorAll('span');
    if (!spans.length) return;
    var labelText = (spans[0] || {}).textContent || '';
    var valSpan   = spans[1];
    var bar       = block.querySelector('[style*="width"]');
    var key = wktMap[labelText.trim()];
    if (key && wickets[key] != null && valSpan && bar) {
      valSpan.textContent = wickets[key] + '%';
      bar.style.width     = wickets[key] + '%';
    }
  });
}

// ─── Match Statistics tab — Recent Matches ────────────────────────────────────
async function renderRecentMatchesAtVenue(venueName) {
  var data = await apiFetch('/api/matches');
  var matches = (data && data.data) ? data.data : [];

  // Try to find matches at this venue by partial name match
  var nameParts = venueName.toLowerCase().split(' ').filter(function(p){ return p.length > 3; });
  var atVenue = matches.filter(function(m) {
    var v = (m.venue || '').toLowerCase();
    return nameParts.some(function(part){ return v.includes(part); });
  }).slice(0, 4);

  // If no venue-specific matches, show most recent completed matches anyway
  var toShow = atVenue.length ? atVenue : matches.filter(function(m){ return m.matchEnded; }).slice(0, 4);
  if (!toShow.length) toShow = matches.slice(0, 4); // fallback: any matches

  var recentCard = null;
  document.querySelectorAll('#panel-stats .section-card').forEach(function(card) {
    var title = (card.querySelector('.section-card-title') || {}).textContent || '';
    if (title.toLowerCase().includes('recent')) recentCard = card;
  });
  if (!recentCard) return;

  var hdr = recentCard.querySelector('.section-card-header');
  var hdrHtml = hdr ? hdr.outerHTML : '';

  if (!toShow.length) {
    recentCard.innerHTML = hdrHtml + '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:.83rem;">No match data available.</div>';
    return;
  }

  recentCard.innerHTML = hdrHtml + toShow.map(function(m) {
    var t1 = m.t1 || m.team1 || ''; var t2 = m.t2 || m.team2 || '';
    var iso1 = COUNTRY_ISO[t1] || ''; var iso2 = COUNTRY_ISO[t2] || '';
    var f1 = iso1 ? flImg(t1, 16) : ''; var f2 = iso2 ? flImg(t2, 16) : '';
    var fmt = m.matchType || ''; var dt = m.date || '';
    var status = m.matchEnded ? 'status-completed' : (m.matchStarted ? 'status-live' : 'status-upcoming');
    var statusLabel = m.matchEnded ? 'Done' : (m.matchStarted ? 'Live' : 'Soon');
    return '<a href="match-detail.html?id=' + esc(m.id || '') + '" class="match-at-venue">'
      + '<div class="mav-badge"><span class="status-badge ' + status + '">' + statusLabel + '</span><span class="match-format-badge">' + esc(fmt) + '</span></div>'
      + '<div class="mav-teams">'
        + '<div class="mav-team-line">' + f1 + esc(t1) + ' <span>' + esc(m.t1s || '') + '</span></div>'
        + '<div class="mav-team-line">' + f2 + esc(t2) + ' <span>' + esc(m.t2s || '') + '</span></div>'
        + '<div class="mav-result">' + esc(m.status || '') + '</div>'
      + '</div>'
      + '<div class="mav-date">' + esc(dt) + '</div>'
    + '</a>';
  }).join('');
}

// ─── Team bias tab ────────────────────────────────────────────────────────────
async function renderTeamBiasTab(venueName) {
  // Always find the section card first so we can replace hardcoded content
  var biasSection = document.querySelector('#panel-teambias .section-card');
  if (!biasSection) return;

  var hdr = biasSection.querySelector('.section-card-header');
  var hdrHtml = hdr ? hdr.outerHTML : '<div class="section-card-header"><div class="section-card-title"><i class="fa fa-shield-halved"></i> Team Win % at this Venue · T20I</div></div>';
  var colHdr = biasSection.querySelector('[style*="grid-template-columns"]');
  var colHtml = colHdr ? colHdr.outerHTML : '';

  var teamsData = await apiFetch('/api/teams');
  if (!teamsData) {
    biasSection.innerHTML = hdrHtml + '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:.83rem;">No team data available.</div>';
    return;
  }

  var biasRows = [];
  Object.keys(teamsData).forEach(function(team) {
    var ts = teamsData[team];
    // handle both {T20I:{...}} and direct format keys
    var t20 = ts['T20I'] || ts['t20i'] || ts['T20'] || {};
    var m = t20.matches || 0;
    if (m >= 3) {
      biasRows.push({ team: team, win_pct: t20.win_pct || 0, matches: m });
    }
  });
  biasRows.sort(function(a, b) { return b.win_pct - a.win_pct; });

  if (!biasRows.length) {
    biasSection.innerHTML = hdrHtml + '<div style="padding:1.5rem;text-align:center;color:var(--text-muted);font-size:.83rem;">No venue bias data available.</div>';
    return;
  }

  biasSection.innerHTML = hdrHtml + colHtml + biasRows.slice(0, 8).map(function(r) {
    var iso = COUNTRY_ISO[r.team] || '';
    var flagHtml = iso ? flImg(r.team, 16) : '';
    var wp = Math.round(r.win_pct * 10) / 10;
    return '<div class="team-bias-row">'
      + '<span class="team-bias-name">' + flagHtml + esc(r.team) + '</span>'
      + '<div class="team-bias-bar-wrap"><div class="team-bias-bar-bg">'
        + '<div class="team-bias-bar-fill" style="width:' + Math.min(wp, 100) + '%"></div>'
      + '</div></div>'
      + '<span class="team-bias-pct">' + wp + '%</span>'
    + '</div>';
  }).join('');
}

// ─── Sidebar: Quick Facts ─────────────────────────────────────────────────────
function renderSidebarFacts(venueName, data, meta) {
  var country = (meta && meta.country) || guessCountry(venueName);
  var iso     = COUNTRY_ISO[country] || '';
  var factMap = {
    'Country':      country,
    'City':         (meta && meta.city) || '',
    'Capacity':     (meta && meta.capacity) ? Number(meta.capacity).toLocaleString() : '',
    'Established':  (meta && meta.established) ? String(meta.established) : '',
    'Intl Matches': data.matches ? String(data.matches) : '',
    'Pitch Type':   (meta && meta.pitch && meta.pitch.surface) || '',
    'Dew Factor':   (meta && meta.pitch && meta.pitch.dew_factor) || '',
  };
  document.querySelectorAll('.sidebar-stat-row').forEach(function(row) {
    var lbl = ((row.querySelector('.sidebar-stat-label') || {}).textContent || '').trim();
    var valEl = row.querySelector('.sidebar-stat-value');
    if (!valEl) return;
    if (lbl === 'Country' && iso) {
      valEl.innerHTML = '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(country) + '" style="width:16px;height:16px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;" onerror="this.style.display=\'none\'"> ' + esc(country);
    } else if (factMap[lbl]) {
      valEl.textContent = factMap[lbl];
    }
  });
}

// ─── Sidebar: Key Insights ────────────────────────────────────────────────────
function renderKeyInsights(venueName, data) {
  var t20 = data.t20i || {};
  var insights = [
    { val: data.chase_win_pct ? data.chase_win_pct + '%' : '—',   text: 'Chasing teams win T20Is here' },
    { val: t20.avg_1st_innings ? Math.round(t20.avg_1st_innings) : '—', text: 'Average 1st innings T20 score' },
    { val: data.toss_winner_win_pct ? data.toss_winner_win_pct + '%' : '—', text: 'Toss winner wins the match (T20I)' },
    { val: data.matches ? String(data.matches) : '—',             text: 'International matches played here' },
  ];

  var insightRows = document.querySelectorAll('.sidebar-insight');
  insights.forEach(function(ins, i) {
    if (!insightRows[i]) return;
    var valEl  = insightRows[i].querySelector('.sidebar-insight-val');
    var textEl = insightRows[i].querySelector('.sidebar-insight-text');
    if (valEl)  valEl.textContent  = ins.val;
    if (textEl) {
      textEl.innerHTML = ins.text;
      // Bold first word for visual emphasis
      textEl.innerHTML = '<strong>' + ins.text.split(' ').slice(0,2).join(' ') + '</strong> ' + ins.text.split(' ').slice(2).join(' ');
    }
  });
}

// ─── Sidebar: Upcoming Here ───────────────────────────────────────────────────
async function renderUpcomingAtVenue(venueName) {
  var data = await apiFetch('/api/matches');
  var matches = (data && data.data) ? data.data : [];

  var upcoming = matches.filter(function(m) {
    if (m.matchEnded) return false;
    var v = (m.venue || '').toLowerCase();
    var n = venueName.toLowerCase();
    return v.includes(n.split(' ')[0]) || v.includes(n.split(',')[0]);
  }).slice(0, 3);

  var upcomingRows = document.querySelectorAll('.upcoming-match-row');
  if (!upcomingRows.length) return;

  if (!upcoming.length) {
    // Fall back to any upcoming matches from cache
    upcoming = matches.filter(function(m){ return !m.matchEnded; }).slice(0, 3);
  }
  if (!upcoming.length) {
    // Still nothing — show a clean message without technical jargon
    if (upcomingRows[0] && upcomingRows[0].parentElement) {
      var parent = upcomingRows[0].parentElement;
      var sideHead = parent.querySelector('.sidebar-card-header');
      var sideHtml = sideHead ? sideHead.outerHTML : '';
      parent.innerHTML = sideHtml + '<div style="padding:1rem 1.1rem;font-size:0.78rem;color:var(--text-muted);">No upcoming matches scheduled.</div>';
    }
    return;
  }

  upcoming.forEach(function(m, i) {
    var row = upcomingRows[i];
    if (!row) return;
    var t1 = m.t1 || m.team1 || 'TBA';
    var t2 = m.t2 || m.team2 || 'TBA';
    var fmt = m.matchType || '';
    var dt  = m.date || '';
    var iso1 = COUNTRY_ISO[t1] || ''; var iso2 = COUNTRY_ISO[t2] || '';
    var f1 = iso1 ? flImg(t1, 14) : ''; var f2 = iso2 ? flImg(t2, 14) : '';
    var teamsEl = row.querySelector('.upcoming-teams');
    var metaEl  = row.querySelector('.upcoming-meta');
    if (teamsEl) teamsEl.innerHTML = f1 + esc(t1) + ' vs ' + f2 + esc(t2);
    if (metaEl)  metaEl.innerHTML = '<span class="match-format-badge" style="font-size:0.6rem;">' + esc(fmt) + '</span><span>' + esc(dt) + '</span>';
  });
  // Hide extra hardcoded rows
  for (var i = upcoming.length; i < upcomingRows.length; i++) {
    upcomingRows[i].style.display = 'none';
  }
}

// ─── Sidebar: Similar Venues ──────────────────────────────────────────────────
async function renderSimilarVenues(venueName, avgT20) {
  var allStats = await apiFetch('/api/venues');
  var allMeta  = await apiFetch('/api/meta/venues');
  if (!allStats) return;

  var similar = Object.keys(allStats)
    .filter(function(n) {
      if (n === venueName) return false;
      var t = (allStats[n].t20i || {}).avg_1st_innings || 0;
      return avgT20 ? Math.abs(t - avgT20) < 25 && t > 0 : false;
    })
    .slice(0, 3);

  if (!similar.length) return;

  var simCard = null;
  document.querySelectorAll('.sidebar-card').forEach(function(card) {
    var title = (card.querySelector('.sidebar-card-title') || {}).textContent || '';
    if (title.toLowerCase().includes('similar')) simCard = card;
  });
  if (!simCard) return;

  var sideHead = simCard.querySelector('.sidebar-card-header');
  simCard.innerHTML = (sideHead ? sideHead.outerHTML : '<div class="sidebar-card-header"><div class="sidebar-card-title"><i class="fa fa-location-dot"></i> Similar Venues</div></div>')
    + similar.map(function(name) {
      var meta    = (allMeta && allMeta[name]) || {};
      var country = meta.country || guessCountry(name);
      var iso     = COUNTRY_ISO[country] || '';
      var avg     = (allStats[name].t20i || {}).avg_1st_innings ? Math.round(allStats[name].t20i.avg_1st_innings) : '—';
      var city    = meta.city || '';
      var flagHtml = iso ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(country) + '" style="width:28px;height:28px;object-fit:cover;border-radius:50%;vertical-align:middle;" onerror="this.style.display=\'none\'">' : '';
      return '<a href="venue-profile.html?name=' + encodeURIComponent(name) + '" style="display:flex;align-items:center;gap:0.7rem;padding:0.7rem 1.1rem;border-bottom:1px solid var(--border-light);text-decoration:none;transition:background var(--transition);" onmouseover="this.style.background=\'var(--surface-2)\'" onmouseout="this.style.background=\'\'">'
        + '<span>' + flagHtml + '</span>'
        + '<div><div style="font-size:0.82rem;font-weight:600;color:var(--text-primary);">' + esc(name) + '</div>'
        + '<div style="font-size:0.68rem;color:var(--text-muted);">' + (city ? esc(city) + ' · ' : '') + avg + ' avg</div></div>'
      + '</a>';
    }).join('');
}

// ─── Top Batters ──────────────────────────────────────────────────────────────
function renderTopBatters(batters) {
  var tables = document.querySelectorAll('#panel-players table');
  if (!tables[0] || !batters.length) return;
  var tbody = tables[0].querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = batters.slice(0, 10).map(function(b, i) {
    var iso = COUNTRY_ISO[b.country || ''] || '';
    var flagHtml = iso ? flImg(b.country, 14) : '';
    return '<tr style="border-bottom:1px solid var(--border-light);">'
      + '<td style="padding:0.65rem 1.2rem;color:' + (i === 0 ? 'var(--accent)' : 'var(--text-muted)') + ';font-family:var(--font-mono);font-weight:700;">' + (i+1) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;"><a href="player-profile.html?name=' + encodeURIComponent(b.player) + '" style="font-weight:600;color:var(--text-primary);text-decoration:none;">' + flagHtml + esc(b.player) + '</a></td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--text-secondary);">' + d(b.matches) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;font-family:var(--font-mono);font-weight:700;color:var(--frost);">' + (b.runs || 0).toLocaleString() + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--accent-warm);">' + f1(b.average) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--text-secondary);">' + d(b.highest) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--green-live);">' + d(b.hundreds) + '</td>'
    + '</tr>';
  }).join('');
}

// ─── Top Bowlers ──────────────────────────────────────────────────────────────
function renderTopBowlers(bowlers) {
  var tables = document.querySelectorAll('#panel-players table');
  if (!tables[1] || !bowlers.length) return;
  var tbody = tables[1].querySelector('tbody');
  if (!tbody) return;
  tbody.innerHTML = bowlers.slice(0, 10).map(function(b, i) {
    var iso = COUNTRY_ISO[b.country || ''] || '';
    var flagHtml = iso ? flImg(b.country, 14) : '';
    var best = (b.best_wkts && b.best_runs) ? b.best_wkts + '/' + b.best_runs : '—';
    return '<tr style="border-bottom:1px solid var(--border-light);">'
      + '<td style="padding:0.65rem 1.2rem;color:' + (i === 0 ? 'var(--accent)' : 'var(--text-muted)') + ';font-family:var(--font-mono);font-weight:700;">' + (i+1) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;"><a href="player-profile.html?name=' + encodeURIComponent(b.player) + '" style="font-weight:600;color:var(--text-primary);text-decoration:none;">' + flagHtml + esc(b.player) + '</a></td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--text-secondary);">' + d(b.matches) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;font-family:var(--font-mono);font-weight:700;color:var(--frost);">' + d(b.wickets) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--accent-warm);">' + f1(b.average) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--green-live);">' + f1(b.economy) + '</td>'
      + '<td style="padding:0.65rem 0.8rem;text-align:right;color:var(--text-secondary);">' + esc(best) + '</td>'
    + '</tr>';
  }).join('');
}

// ─── Probability Insights tab — computed from real data ───────────────────────
function renderProbabilityInsights(venueName, data) {
  var t20 = data.t20i || {};
  var chasePct  = data.chase_win_pct || 50;
  var defendPct = 100 - chasePct;
  var avgT20    = t20.avg_1st_innings || 160;
  var prob200   = Math.max(5, Math.min(60, Math.round((avgT20 - 150) * 1.2)));
  var tossWin   = data.toss_winner_win_pct || 50;
  var matchOver350 = Math.round(Math.max(5, Math.min(75, (((data.odi || {}).avg_1st_innings || 260) - 220) * 0.8)));

  // Update match outcome prob rows in panel-insights
  var probRows = document.querySelectorAll('#panel-insights .prob-row');
  var updates = [
    { label: /[Cc]hasing|chase/,   pct: chasePct },
    { label: /[Ii]ndia.*(home|T20I)|home.*win/i, pct: null }, // skip player-specific
    { label: /350.*ODI|ODI.*350/,  pct: matchOver350 },
    { label: /[Tt]oss winner/,     pct: tossWin },
    { label: /200.*T20|T20.*200/,  pct: prob200 },
    { label: /[Pp]owerplay.*55/,   pct: t20.avg_powerplay ? Math.round(t20.avg_powerplay / 55 * 44) : 40 },
  ];

  probRows.forEach(function(row) {
    var labelEl = row.querySelector('.prob-label');
    var pctEl   = row.querySelector('.prob-pct');
    var fillEl  = row.querySelector('.prob-bar-fill');
    if (!labelEl || !pctEl) return;
    var labelText = labelEl.textContent;

    updates.forEach(function(u) {
      if (!u.pct || !u.label.test(labelText)) return;
      pctEl.textContent = u.pct + '%';
      if (fillEl) fillEl.style.width = u.pct + '%';
    });
  });

  // Update venue name in probability titles
  document.querySelectorAll('#panel-insights .section-card-title').forEach(function(el) {
    if (el.textContent.includes('Wankhede') || el.textContent.includes('Probabilities at ')) {
      el.innerHTML = el.innerHTML.replace(/Wankhede|at [A-Z][^<]*/g, 'at ' + esc(venueName));
    }
  });
}

// ─── Main loader ──────────────────────────────────────────────────────────────
async function loadVenueProfile() {
  var venueName = getParam('name');
  if (!venueName) return;

  document.title = venueName + ' — Venue Profile · Criclytics';

  var nameEl  = document.getElementById('venueName');
  var breadEl = document.getElementById('breadcrumbVenue');
  if (nameEl)  nameEl.textContent  = venueName;
  if (breadEl) breadEl.textContent = venueName;

  // Replace "Wankhede" references in all title elements
  document.querySelectorAll('.section-card-title, .sidebar-card-title').forEach(function(el) {
    if (el.textContent.includes('Wankhede')) {
      el.innerHTML = el.innerHTML.replace(/Wankhede/g, esc(venueName));
    }
  });

  var venueData = await apiFetch('/api/venues/' + encodeURIComponent(venueName));
  var venueMeta = await apiFetch('/api/meta/venues');
  var meta = (venueMeta && venueMeta[venueName]) || null;

  // Try partial match in meta
  if (!meta && venueMeta) {
    Object.keys(venueMeta).forEach(function(k) {
      if (!meta && k.toLowerCase().includes(venueName.toLowerCase().split(' ')[0].toLowerCase())) {
        meta = venueMeta[k];
      }
    });
  }

  if (!venueData) {
    console.warn('venue-profile: no data for', venueName);
    return;
  }

  _venueData = venueData;
  _venueMeta = meta || {};

  renderHeroStats(venueData, meta || {});
  renderOverviewStats(venueData);
  renderPitchProfile(venueData, meta || {});
  renderVenueInfoCard(venueName, venueData, meta || {});
  renderStatsForFmt('t20');
  renderTeamBiasTab(venueName);
  renderTopBatters(venueData.top_batters || []);
  renderTopBowlers(venueData.top_bowlers || []);
  renderSidebarFacts(venueName, venueData, meta || {});
  renderKeyInsights(venueName, venueData);
  renderUpcomingAtVenue(venueName);
  renderRecentMatchesAtVenue(venueName);
  renderSimilarVenues(venueName, (venueData.t20i || {}).avg_1st_innings);
  renderProbabilityInsights(venueName, venueData);
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  loadVenueProfile();

  // Format switcher — the inline script in HTML only toggles active class
  // We need to also call renderStatsForFmt here
  document.querySelectorAll('.fs-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      _activeFmt = btn.dataset.fmt || 't20';
      renderStatsForFmt(_activeFmt);
    });
  });
});
