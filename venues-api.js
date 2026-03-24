/**
 * venues-api.js
 * =============
 * API wiring for venues.html
 * Loads venue stats from /api/venues + static meta, renders cards
 * grouped by country with real flags and links.
 * Depends on cricklytics.js globals: FLAG_CDN, COUNTRY_ISO, apiFetch, esc, getParam
 */

function fl(country, size) {
  size = size || 20;
  var code = COUNTRY_ISO[country] || country;
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:6px;" '
    + 'onerror="this.style.display=\'none\'">';
}
function flCircle(country, size) {
  size = size || 22;
  var code = COUNTRY_ISO[country] || country;
  return '<img src="' + FLAG_CDN + code + '.svg" alt="' + esc(country) + '" '
    + 'style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;vertical-align:middle;" '
    + 'onerror="this.style.display=\'none\'">';
}

function pitchLabel(avgT20) {
  if (!avgT20) return 'Balanced';
  if (avgT20 >= 185) return 'Flat · Very high-scoring';
  if (avgT20 >= 170) return 'Flat · High-scoring';
  if (avgT20 >= 155) return 'Batting friendly';
  if (avgT20 >= 140) return 'Balanced';
  return 'Bowling friendly';
}

function guessCountry(name) {
  var n = (name || '').toLowerCase();
  if (n.includes('mumbai')||n.includes('wankhede')||n.includes('delhi')||n.includes('kolkata')||
      n.includes('eden')||n.includes('chennai')||n.includes('bengaluru')||n.includes('chinnaswamy')||
      n.includes('hyderabad')||n.includes('rajiv')||n.includes('ahmedabad')||n.includes('modi')||
      n.includes('pune')||n.includes('mohali')||n.includes('dharamsala')||n.includes('ranchi')||
      n.includes('nagpur')||n.includes('indore')) return 'India';
  if (n.includes('melbourne')||n.includes('mcg')||n.includes('sydney')||n.includes('scg')||
      n.includes('brisbane')||n.includes('gabba')||n.includes('adelaide')||n.includes('perth')||
      n.includes('waca')||n.includes('optus')) return 'Australia';
  if (n.includes("lord's")||n.includes('lords')||n.includes('oval')||n.includes('edgbaston')||
      n.includes('headingley')||n.includes('trent')||n.includes('old trafford')||
      n.includes('chester')||n.includes('rose bowl')||n.includes("riverside")) return 'England';
  if (n.includes('karachi')||n.includes('lahore')||n.includes('gaddafi')||n.includes('rawalpindi')||
      n.includes('multan')||n.includes('faisalabad')||n.includes('iqbal')) return 'Pakistan';
  if (n.includes('newlands')||n.includes('wanderers')||n.includes('centurion')||
      n.includes('durban')||n.includes('kingsmead')||n.includes('port elizabeth')||
      n.includes('st george')) return 'South Africa';
  if (n.includes('eden park')||n.includes('basin')||n.includes('hagley')||
      n.includes('seddon')||n.includes('mclean')||n.includes('university oval')) return 'New Zealand';
  if (n.includes('kensington')||n.includes('sabina')||n.includes('providence')||
      n.includes('queen\'s park')||n.includes('warner park')) return 'West Indies';
  if (n.includes('colombo')||n.includes('galle')||n.includes('kandy')||
      n.includes('pallekele')||n.includes('premadasa')) return 'Sri Lanka';
  if (n.includes('dhaka')||n.includes('chittagong')||n.includes('sher-e-bangla')||
      n.includes('sylhet')||n.includes('mirpur')) return 'Bangladesh';
  if (n.includes('sharjah')||n.includes('dubai')||n.includes('abu dhabi')) return 'UAE';
  if (n.includes('harare')||n.includes('bulawayo')||n.includes('queens')) return 'Zimbabwe';
  return '';
}

// Region → countries mapping for filter chips
var REGION_COUNTRIES = {
  'all':  null,
  'asia': ['India','Pakistan','Sri Lanka','Bangladesh','Afghanistan','UAE'],
  'aus':  ['Australia'],
  'eng':  ['England'],
  'sa':   ['South Africa','Zimbabwe'],
  'wi':   ['West Indies'],
  'nz':   ['New Zealand'],
};

function renderVenueCard(venueName, stats, meta, delay) {
  delay = delay || '';
  var country  = (meta && meta.country) || guessCountry(venueName);
  var iso      = COUNTRY_ISO[country] || '';
  var capacity = (meta && meta.capacity) ? Number(meta.capacity).toLocaleString() : '—';
  var t20i     = (stats && stats.t20i) || {};
  var odi      = (stats && stats.odi)  || {};
  var pitch    = (meta && meta.pitch && meta.pitch.surface) || pitchLabel(t20i.avg_1st_innings);
  var avgT20   = t20i.avg_1st_innings ? Math.round(t20i.avg_1st_innings) : '—';
  var avgOdi   = odi.avg_1st_innings  ? Math.round(odi.avg_1st_innings)  : '—';
  var chasePct = stats && stats.chase_win_pct ? stats.chase_win_pct + '%' : '—';
  var batFriendly = t20i.avg_1st_innings ? Math.min(Math.round(t20i.avg_1st_innings / 2), 85) : 50;
  var city     = (meta && meta.city) || '';
  var location = [city, country].filter(Boolean).join(', ');

  return '<a href="venue-profile.html?name=' + encodeURIComponent(venueName) + '" class="venue-card anim-up ' + delay + '">'
    + '<div class="venue-card-visual">'
      + '<span class="venue-card-visual-icon"><i class="fa fa-building" style="font-size:1.8rem;color:rgba(255,255,255,0.4);"></i></span>'
      + '<span class="venue-country-flag" style="overflow:hidden;">' + (iso ? flCircle(country, 22) : '') + '</span>'
      + '<span class="venue-capacity-badge"><i class="fa fa-users"></i> ' + esc(capacity) + '</span>'
      + '<span class="venue-pitch-badge">' + esc(pitch) + '</span>'
    + '</div>'
    + '<div class="venue-card-body">'
      + '<div class="venue-card-name">' + esc(venueName) + '</div>'
      + '<div class="venue-card-location"><i class="fa fa-location-dot"></i> ' + esc(location) + '</div>'
      + '<div class="venue-mini-stats">'
        + '<div class="venue-mini-stat"><span class="venue-mini-stat-val">' + avgT20 + '</span><span class="venue-mini-stat-label">Avg T20</span></div>'
        + '<div class="venue-mini-stat"><span class="venue-mini-stat-val">' + avgOdi + '</span><span class="venue-mini-stat-label">Avg ODI</span></div>'
        + '<div class="venue-mini-stat"><span class="venue-mini-stat-val">' + chasePct + '</span><span class="venue-mini-stat-label">Chase wins</span></div>'
      + '</div>'
    + '</div>'
    + '<div class="venue-card-footer">'
      + '<div class="bias-indicator"><span>Bat</span>'
        + '<div class="bias-bar"><div class="bias-fill-bat" style="width:' + batFriendly + '%"></div></div>'
        + '<span>' + batFriendly + '%</span>'
      + '</div>'
      + '<i class="fa fa-chevron-right venue-card-arrow"></i>'
    + '</div>'
  + '</a>';
}

// ── All data stored here for filtering ───────────────────────────────────────
var _allVenueData = []; // [{country, name, stats, meta}]

function buildGroups(venueList) {
  // Group by country
  var byCountry = {};
  venueList.forEach(function(v) {
    if (!byCountry[v.country]) byCountry[v.country] = [];
    byCountry[v.country].push(v);
  });

  var sorted = Object.keys(byCountry).sort(function(a,b) {
    return byCountry[b].length - byCountry[a].length;
  });

  var delays = ['','delay-1','delay-2','delay-3','delay-4','delay-5'];

  return sorted.map(function(country) {
    var venues = byCountry[country];
    var iso = COUNTRY_ISO[country] || '';
    var flagHtml = iso
      ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(country) + '" style="width:20px;height:20px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:6px;" onerror="this.style.display=\'none\'">'
      : '';
    var cards = venues
      .sort(function(a,b){ return (b.stats&&b.stats.matches||0)-(a.stats&&a.stats.matches||0); })
      .slice(0, 6)
      .map(function(v, i){ return renderVenueCard(v.name, v.stats, v.meta, delays[i%delays.length]); })
      .join('');
    return '<div class="region-group" data-country="' + esc(country) + '">'
      + '<div class="region-group-label">'
        + '<span class="region-group-title">' + flagHtml + esc(country) + '</span>'
        + '<div class="region-group-line"></div>'
      + '</div>'
      + '<div class="venues-grid">' + cards + '</div>'
    + '</div>';
  }).join('');
}

function applyVenueFilters(searchQ, region) {
  var container = document.getElementById('venueGroups') || document.querySelector('.venue-groups');
  if (!container) return;

  var filtered = _allVenueData.slice();

  // Region filter
  if (region && region !== 'all') {
    var allowed = REGION_COUNTRIES[region];
    if (allowed) filtered = filtered.filter(function(v){ return allowed.indexOf(v.country) !== -1; });
  }

  // Text search
  if (searchQ) {
    var q = searchQ.toLowerCase();
    filtered = filtered.filter(function(v){
      return v.name.toLowerCase().includes(q)
        || (v.country||'').toLowerCase().includes(q)
        || ((v.meta&&v.meta.city)||'').toLowerCase().includes(q);
    });
  }

  if (!filtered.length) {
    container.innerHTML = '<div style="padding:3rem;text-align:center;color:var(--text-muted);">'
      + '<i class="fa fa-magnifying-glass" style="font-size:2rem;display:block;margin-bottom:1rem;opacity:0.4;"></i>'
      + '<div>No venues found matching your search.</div></div>';
    return;
  }

  container.innerHTML = buildGroups(filtered);
}

// ── Load and render all venues ────────────────────────────────────────────────
async function loadVenues() {
  var venueStats = await apiFetch('/api/venues');
  var venueMeta  = await apiFetch('/api/meta/venues');

  if (!venueStats || !Object.keys(venueStats).length) return;

  // Build flat list
  _allVenueData = Object.keys(venueStats).map(function(name) {
    var meta    = (venueMeta && venueMeta[name]) || {};
    var country = meta.country || guessCountry(name);
    return { name: name, stats: venueStats[name], meta: meta, country: country };
  }).filter(function(v){ return v.country; });

  var container = document.getElementById('venueGroups') || document.querySelector('.venue-groups');
  if (container) container.innerHTML = buildGroups(_allVenueData);

  // Update hero stat pills
  var totalVenues = Object.keys(venueStats).length;
  var heroP = document.querySelector('.venues-hero p');
  if (heroP) heroP.textContent = 'Explore ' + totalVenues + '+ international venues with scoring stats, pitch profiles, and probability insights.';

  // Update sidebar
  renderSidebarStats(venueStats, venueMeta);
}

// ── Sidebar: most active + highest scoring venues ─────────────────────────────
function renderSidebarStats(venueStats, venueMeta) {
  var mostActive = Object.entries(venueStats)
    .sort(function(a,b){ return (b[1].matches||0)-(a[1].matches||0); })
    .slice(0,5);

  var activeEl = document.getElementById('mostActiveCard');
  if (activeEl && mostActive.length) {
    var head = activeEl.querySelector('.sidebar-card-header');
    activeEl.innerHTML = (head ? head.outerHTML : '<div class="sidebar-card-header"><div class="sidebar-card-title"><i class="fa fa-fire"></i> Most Active</div></div>')
      + mostActive.map(function(e){
          var name=e[0]; var s=e[1];
          var meta=(venueMeta&&venueMeta[name])||{};
          var country=meta.country||guessCountry(name);
          return '<a href="venue-profile.html?name='+encodeURIComponent(name)+'" class="sidebar-venue-row">'
            +'<span class="svr-flag">'+flCircle(country,22)+'</span>'
            +'<div class="svr-info"><div class="svr-name">'+esc(name)+'</div><div class="svr-meta">'+esc(country)+' · '+(s.matches||0)+' matches</div></div>'
            +'<span class="svr-stat">'+(s.matches||0)+'</span></a>';
        }).join('');
  }

  var highestScoring = Object.entries(venueStats)
    .filter(function(e){ return e[1].t20i&&e[1].t20i.avg_1st_innings>0; })
    .sort(function(a,b){ return (b[1].t20i.avg_1st_innings||0)-(a[1].t20i.avg_1st_innings||0); })
    .slice(0,5);

  var scoringEl = document.getElementById('highestScoringCard');
  if (scoringEl && highestScoring.length) {
    var head2 = scoringEl.querySelector('.sidebar-card-header');
    scoringEl.innerHTML = (head2 ? head2.outerHTML : '<div class="sidebar-card-header"><div class="sidebar-card-title"><i class="fa fa-chart-simple"></i> Highest Avg T20 Score</div></div>')
      + highestScoring.map(function(e){
          var name=e[0]; var s=e[1];
          var meta=(venueMeta&&venueMeta[name])||{};
          var country=meta.country||guessCountry(name);
          var avg=Math.round(s.t20i.avg_1st_innings);
          return '<a href="venue-profile.html?name='+encodeURIComponent(name)+'" class="sidebar-venue-row">'
            +'<span class="svr-flag">'+flCircle(country,22)+'</span>'
            +'<div class="svr-info"><div class="svr-name">'+esc(name)+'</div><div class="svr-meta">'+esc(country)+'</div></div>'
            +'<span class="svr-stat">'+avg+'</span></a>';
        }).join('');
  }
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', function() {
  loadVenues();

  var activeRegion = 'all';
  var searchTimer = null;

  // Search input (filter bar uses .nav-search not #heroSearch on venues page)
  var searchEl = document.querySelector('.filter-sticky .nav-search');
  if (searchEl) {
    searchEl.addEventListener('input', function() {
      clearTimeout(searchTimer);
      var q = this.value.trim();
      searchTimer = setTimeout(function(){ applyVenueFilters(q, activeRegion); }, 200);
    });
  }

  // Region filter chips
  document.querySelectorAll('[data-region]').forEach(function(btn) {
    btn.addEventListener('click', function() {
      document.querySelectorAll('[data-region]').forEach(function(b){ b.classList.remove('active'); });
      btn.classList.add('active');
      activeRegion = btn.dataset.region || 'all';
      var q = searchEl ? searchEl.value.trim() : '';
      applyVenueFilters(q, activeRegion);
    });
  });

  // Sort dropdown
  var sortEl = document.querySelector('.filter-sticky .filter-select');
  if (sortEl) {
    sortEl.addEventListener('change', function() {
      if (!_allVenueData.length) return; // data not loaded yet
      var val = this.value.toLowerCase();
      if (val.includes('capacity')) {
        _allVenueData.sort(function(a, b) {
          return ((b.meta && b.meta.capacity) || 0) - ((a.meta && a.meta.capacity) || 0);
        });
      } else if (val.includes('alpha')) {
        _allVenueData.sort(function(a, b) { return a.name.localeCompare(b.name); });
      } else {
        // Default: matches hosted
        _allVenueData.sort(function(a, b) {
          return ((b.stats && b.stats.matches) || 0) - ((a.stats && a.stats.matches) || 0);
        });
      }
      var q = _venueSearchEl ? _venueSearchEl.value.trim() : '';
      applyVenueFilters(q, _activeVenueRegion);
    });
  }
});
