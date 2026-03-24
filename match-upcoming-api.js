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

  var t1 = match.t1 || match.team1 || '';
  var t2 = match.t2 || match.team2 || '';
  var iso1 = COUNTRY_ISO[t1] || '';
  var iso2 = COUNTRY_ISO[t2] || '';

  // Page title + breadcrumb
  var name = match.name || (t1 + ' vs ' + t2);
  document.title = name + ' · Criclytics';
  var bc = document.getElementById('breadcrumbName');
  if (bc) bc.textContent = name;

  // Team names + flags
  var n1 = document.getElementById('team1Name'); if (n1) n1.textContent = t1;
  var n2 = document.getElementById('team2Name'); if (n2) n2.textContent = t2;

  var f1 = document.getElementById('team1Flag');
  var f2 = document.getElementById('team2Flag');
  if (f1 && iso1) f1.innerHTML = '<img src="'+FLAG_CDN+iso1+'.svg" style="width:100%;height:100%;object-fit:cover;">';
  if (f2 && iso2) f2.innerHTML = '<img src="'+FLAG_CDN+iso2+'.svg" style="width:100%;height:100%;object-fit:cover;">';

  // Scores (if any)
  var s1el = document.getElementById('team1Score'); if (s1el && match.t1s) s1el.textContent = match.t1s;
  var s2el = document.getElementById('team2Score'); if (s2el && match.t2s) s2el.textContent = match.t2s;

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
