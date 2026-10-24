/**
 * match-upcoming-api.js
 * =====================
 * Wires match-upcoming.html for upcoming fixtures.
 * Shows: fixture details, H2H, venue context, win probability.
 * No scorecard, no live snapshot.
 */

document.addEventListener('DOMContentLoaded', async function() {
  var matchId = getParam('id');

  if (!matchId) {
    document.getElementById('matchStatus').textContent = 'No match selected';
    return;
  }

  // Find match in /api/matches
  var match = null;
  var data = await apiFetch('/api/matches');
  if (data && data.data) {
    match = data.data.find(function(m) { return String(m.id) === String(matchId); });
  }
  if (!match) {
    var liveData = await apiFetch('/api/live');
    if (liveData && liveData.data) {
      match = liveData.data.find(function(m) { return String(m.id) === String(matchId); });
    }
  }

  if (!match) {
    document.getElementById('matchStatus').textContent = 'Match not found';
    return;
  }

  function getTeamInitials(name) {
    if (!name) return '?';
    var words = (name || '').split(/\s+/).filter(function(w){ return !!w; });
    if (words.length === 0) return '?';
    if (words.length === 1) return words[0][0].toUpperCase();
    if (words.length === 2) return (words[0][0] + words[1][0]).toUpperCase();
    return (words[0][0] + words[1][0] + words[2][0]).toUpperCase();
  }

  function parseNameTeams(name) {
    if (!name) return ['', ''];
    var parts = name.split(/\s+vs\s+|\s+v\s+|\s+versus\s+/i);
    if (parts.length < 2) return ['', ''];
    return [parts[0].trim(), parts[1].trim().split(/,|\(|–|-/)[0].trim()];
  }

  function normalizeTeamNameCandidate(value, index) {
    var raw = String(value || '').trim();
    if (!raw) return '';
    var parsed = parseNameTeams(raw);
    if (parsed[0] && parsed[1]) return index === 0 ? parsed[0] : parsed[1];
    return raw;
  }

  function resolveScoreboardIso(name) {
    var raw = String(name || '').trim();
    if (!raw) return '';

    if (COUNTRY_ISO[raw]) return COUNTRY_ISO[raw];

    var normalized = raw.replace(/\s*\([^)]*\)\s*/g, ' ').replace(/\s+/g, ' ').trim();
    if (COUNTRY_ISO[normalized]) return COUNTRY_ISO[normalized];

    var stripped = normalized
      .replace(/\s+(A|B|XI|W|Women|U-?19|U-?23)$/i, '')
      .replace(/\s+/g, ' ')
      .trim();
    if (COUNTRY_ISO[stripped]) return COUNTRY_ISO[stripped];

    var countries = Object.keys(COUNTRY_ISO).sort(function(a, b) { return b.length - a.length; });
    for (var i = 0; i < countries.length; i++) {
      var c = countries[i];
      if (normalized === c || normalized.indexOf(c + ' ') === 0) return COUNTRY_ISO[c];
    }
    return '';
  }

  function renderTeamFlag(el, teamName) {
    if (!el) return;
    var size = el.clientWidth || 72;
    var initials = esc(getTeamInitials(teamName));
    var iso = resolveScoreboardIso(teamName);

    if (!iso) {
      el.innerHTML = '<span style="display:flex;align-items:center;justify-content:center;width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:var(--surface-2);border:1px solid rgba(94,184,255,0.28);font-size:' + Math.round(size * 0.38) + 'px;font-weight:700;color:var(--accent);">' + initials + '</span>';
      return;
    }

    el.innerHTML = '<span style="position:relative;display:flex;align-items:center;justify-content:center;width:' + size + 'px;height:' + size + 'px;">'
      + '<img src="' + FLAG_CDN + iso + '.svg" alt="" style="position:absolute;inset:0;width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" '
      + 'onerror="this.style.display=\'none\'; if(this.nextElementSibling){this.nextElementSibling.style.display=\'flex\';}">'
      + '<span style="display:none;align-items:center;justify-content:center;width:' + size + 'px;height:' + size + 'px;border-radius:50%;background:var(--surface-2);border:1px solid rgba(94,184,255,0.28);font-size:' + Math.round(size * 0.38) + 'px;font-weight:700;color:var(--accent);">' + initials + '</span>'
      + '</span>';
  }

  function getMatchTeamName(match, index) {
    if (!match) return '';
    var fallback = (Array.isArray(match.teams) ? match.teams[index] : '')
      || (match.teamInfo && match.teamInfo[index] && match.teamInfo[index].name)
      || '';
    if (index === 0) {
      return normalizeTeamNameCandidate(match.t1 || match.team1 || fallback || parseNameTeams(match.name)[0] || '', 0);
    }
    return normalizeTeamNameCandidate(match.t2 || match.team2 || fallback || parseNameTeams(match.name)[1] || '', 1);
  }

  var t1 = getMatchTeamName(match, 0);
  var t2 = getMatchTeamName(match, 1);

  // Page title + breadcrumb
  var name = match.name || (t1 + ' vs ' + t2);
  document.title = name + ' · Criclytics';
  var bc = document.getElementById('breadcrumbName');
  if (bc) bc.textContent = name;

  // Team names + flags
  var n1 = document.getElementById('team1Name'); if (n1) n1.textContent = t1;
  var n2 = document.getElementById('team2Name'); if (n2) n2.textContent = t2;

  // Keep visual parity between left/right labels.
  if (n1) {
    n1.style.color = 'var(--text-primary)';
    n1.style.fontWeight = '700';
  }
  if (n2) {
    n2.style.color = 'var(--text-primary)';
    n2.style.fontWeight = '700';
  }

  var f1 = document.getElementById('team1Flag');
  var f2 = document.getElementById('team2Flag');
  renderTeamFlag(f1, t1);
  renderTeamFlag(f2, t2);

  // Scores (if any)
  var s1el = document.getElementById('team1Score'); if (s1el && match.t1s) s1el.textContent = match.t1s;
  var s2el = document.getElementById('team2Score'); if (s2el && match.t2s) s2el.textContent = match.t2s;
  if (s1el) {
    s1el.style.color = 'var(--text-muted)';
    s1el.style.fontWeight = '600';
  }
  if (s2el) {
    s2el.style.color = 'var(--text-muted)';
    s2el.style.fontWeight = '600';
  }

  // Status badge
  var statEl = document.getElementById('matchStatus');
  if (statEl) {
    if (match.matchStarted && !match.matchEnded) {
      statEl.textContent = 'LIVE';
      statEl.style.background = 'rgba(0,230,118,.15)';
      statEl.style.color = 'var(--green-live)';
      statEl.style.border = '1px solid rgba(0,230,118,.3)';
    } else if (match.matchEnded) {
      statEl.textContent = match.status || 'Completed';
      statEl.style.background = 'rgba(255,255,255,.06)';
      statEl.style.color = 'var(--text-secondary)';
    } else {
      statEl.textContent = 'Upcoming';
    }
  }

  // Date
  var dateEl = document.getElementById('matchDate');
  if (dateEl && match.date) dateEl.textContent = match.date;

  // Meta strip
  var v = document.getElementById('metaVenue');
  var d = document.getElementById('metaDate');
  var fmt = document.getElementById('metaFormat');
  var ser = document.getElementById('metaSeries');
  if (v && match.venue) v.innerHTML = '<i class="fa fa-location-dot"></i> ' + esc(match.venue);
  if (d && match.date) d.innerHTML = '<i class="fa fa-calendar"></i> ' + esc(match.date);
  if (fmt && match.matchType) fmt.innerHTML = '<i class="fa fa-circle-dot" style="color:var(--accent)"></i> ' + esc(match.matchType);
  if (ser && match.series_id) ser.innerHTML = '<i class="fa fa-trophy"></i> ' + esc(match.series_id.replace(/-/g,' ').replace(/\b\w/g,function(c){return c.toUpperCase();}));

  // Fixture details panel
  var fxFormat = document.getElementById('fxFormat'); if (fxFormat) fxFormat.textContent = match.matchType || '—';
  var fxDate   = document.getElementById('fxDate');   if (fxDate)   fxDate.textContent   = match.date || '—';
  var fxVenue  = document.getElementById('fxVenue');  if (fxVenue)  fxVenue.textContent  = match.venue || '—';
  var fxSeries = document.getElementById('fxSeries'); if (fxSeries) fxSeries.textContent = match.series_id || '—';

  // H2H
  var h2hEl = document.getElementById('h2hContent');
  if (h2hEl && t1 && t2) {
    var h2hData = await apiFetch('/api/h2h?team_a=' + encodeURIComponent(t1) + '&team_b=' + encodeURIComponent(t2) + '&format=' + (match.matchType || 'T20I'));
    if (h2hData) {
      var wins1 = h2hData.team_a_wins || 0;
      var wins2 = h2hData.team_b_wins || 0;
      var total = h2hData.matches || (wins1 + wins2);
      h2hEl.innerHTML =
        '<div style="display:flex;justify-content:space-between;align-items:center;gap:1rem;">'
        + '<div style="text-align:center;"><div style="font-size:1.8rem;font-weight:700;color:var(--accent)">'+wins1+'</div><div style="font-size:.75rem;color:var(--text-muted)">'+esc(t1)+' wins</div></div>'
        + '<div style="text-align:center;color:var(--text-muted);font-size:.8rem;">'+total+' matches played</div>'
        + '<div style="text-align:center;"><div style="font-size:1.8rem;font-weight:700;color:var(--accent)">'+wins2+'</div><div style="font-size:.75rem;color:var(--text-muted)">'+esc(t2)+' wins</div></div>'
        + '</div>';
      // Win probability from H2H
      if (total > 0) {
        var pct1 = Math.round((wins1/total)*100);
        var pct2 = 100 - pct1;
        var wp1 = document.getElementById('wpTeam1'); if (wp1) wp1.textContent = esc(t1);
        var wp2 = document.getElementById('wpTeam2'); if (wp2) wp2.textContent = esc(t2);
        var bar = document.getElementById('wpBar');   if (bar) bar.style.width = pct1 + '%';
        var p1 = document.getElementById('wpPct1');  if (p1) p1.textContent = pct1 + '%';
        var p2 = document.getElementById('wpPct2');  if (p2) p2.textContent = pct2 + '%';
      }
    } else {
      h2hEl.innerHTML = '<div style="color:var(--text-muted);font-size:.83rem;">No H2H data available.</div>';
    }
  }

  // Venue context
  var venueEl = document.getElementById('venueContent');
  if (venueEl && match.venue) {
    var vData = await apiFetch('/api/venues/' + encodeURIComponent(match.venue));
    if (vData) {
      var t20 = vData.t20i || {};
      var odi = vData.odi  || {};
      var fmt_key = match.matchType === 'T20I' ? t20 : odi;
      venueEl.innerHTML =
        '<div style="display:grid;grid-template-columns:1fr 1fr;gap:.6rem;">'
        + '<div><span style="color:var(--text-muted)">Avg 1st innings</span><br><strong>' + (fmt_key.avg_1st_innings ? Math.round(fmt_key.avg_1st_innings) : '—') + '</strong></div>'
        + '<div><span style="color:var(--text-muted)">Chase win%</span><br><strong>' + (vData.chase_win_pct ? vData.chase_win_pct+'%' : '—') + '</strong></div>'
        + '<div><span style="color:var(--text-muted)">Matches played</span><br><strong>' + (fmt_key.matches || '—') + '</strong></div>'
        + '<div><span style="color:var(--text-muted)">Toss advantage</span><br><strong>' + (fmt_key.toss_win_pct ? fmt_key.toss_win_pct+'%' : '—') + '</strong></div>'
        + '</div>';
    } else {
      venueEl.innerHTML = '<div style="color:var(--text-muted);font-size:.83rem;">No venue data available.</div>';
    }
  }

  // Nav search
  var navSearch = document.querySelector('.nav-search');
  if (navSearch) {
    navSearch.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && this.value.trim()) {
        window.location.href = 'search.html?q=' + encodeURIComponent(this.value.trim());
      }
    });
  }
});
