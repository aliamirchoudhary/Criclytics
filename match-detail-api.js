/**
 * match-detail-api.js
 * ===================
 * Reads ?id= from URL.
 * When no id: clears ALL hardcoded content, shows team names from URL params if available,
 * puts — in all score/stat fields. Zero hardcoded India/Australia content survives.
 * When id provided: loads from /api/matches/{id} and fills in real data.
 */

function guessIso(name) {
  var keys = Object.keys(COUNTRY_ISO);
  for (var i = 0; i < keys.length; i++) {
    if ((name || '').toLowerCase().includes(keys[i].toLowerCase())) return COUNTRY_ISO[keys[i]];
  }
  return '';
}

function flagCircle(name, size) {
  size = size || 44;
  var iso = COUNTRY_ISO[name] || guessIso(name);
  if (!iso) return '<span style="font-size:' + Math.round(size * 0.45) + 'px;font-weight:700;color:var(--accent);">' + esc((name || '?')[0]) + '</span>';
  return '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(name) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:50%;" onerror="this.style.display=\'none\'">';
}

function flInline(name, size) {
  size = size || 16;
  var iso = COUNTRY_ISO[name] || guessIso(name);
  if (!iso) return '';
  return '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(name) + '" style="width:' + size + 'px;height:' + size + 'px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;" onerror="this.style.display=\'none\'">';
}

function d(v) { return (v == null || v === '' || v === 0) ? '—' : v; }

// ── Clear ALL hardcoded content, replace with — ───────────────────────────────
function wipePage(t1, t2) {
  t1 = t1 || ''; t2 = t2 || '';
  var dash = '—';

  // Breadcrumb last span
  var bc = document.querySelector('.breadcrumb span:last-child');
  if (bc) bc.textContent = t1 && t2 ? t1 + ' vs ' + t2 : 'Match Detail';

  // Team names
  var n1 = document.getElementById('team1Name'); if (n1) n1.textContent = t1 || dash;
  var n2 = document.getElementById('team2Name'); if (n2) n2.textContent = t2 || dash;

  // Scores
  var s1 = document.getElementById('team1Score'); if (s1) s1.textContent = dash;
  var s2 = document.getElementById('team2Score'); if (s2) s2.textContent = dash;

  // Overs + CRR under each team
  document.querySelectorAll('.scoreboard-overs').forEach(function(el){ el.textContent = dash; });
  document.querySelectorAll('.scoreboard-crr').forEach(function(el){ el.textContent = dash; });

  // Target box value + RRR value
  var targetVal = document.querySelector('.target-box .value');
  if (targetVal) targetVal.textContent = dash;
  var rrrVal = document.querySelector('.run-rate-box .value');
  if (rrrVal) rrrVal.textContent = dash;

  // Flags
  var flags = document.querySelectorAll('.scoreboard-flag');
  if (flags[0]) flags[0].innerHTML = t1 ? flagCircle(t1, 44) : '';
  if (flags[1]) flags[1].innerHTML = t2 ? flagCircle(t2, 44) : '';

  // Status badge
  var statusEl = document.querySelector('.match-status-live');
  if (statusEl) {
    statusEl.innerHTML = '<span class="live-dot"></span> ' + (t1 && t2 ? t1 + ' vs ' + t2 : 'Match Detail');
  }

  // Chase bar
  var chaseLabels = document.querySelectorAll('.chase-bar-labels span');
  if (chaseLabels[0]) chaseLabels[0].textContent = t2 || dash;
  if (chaseLabels[1]) chaseLabels[1].textContent = dash;
  if (chaseLabels[2]) chaseLabels[2].textContent = dash;
  var chaseFill = document.querySelector('.chase-bar-fill');
  if (chaseFill) chaseFill.style.width = '0%';

  // Meta strip
  var metaItems = document.querySelectorAll('.match-meta-item');
  var icons = ['fa-location-dot','fa-calendar','fa-trophy','fa-circle-dot','fa-user'];
  metaItems.forEach(function(el, i) {
    el.innerHTML = '<i class="fa ' + (icons[i]||'fa-circle') + '"></i> ' + dash;
  });

  // Overview stats (Live Snapshot section)
  document.querySelectorAll('.overview-stat-value').forEach(function(el){ el.textContent = dash; });
  document.querySelectorAll('.overview-stat-sub').forEach(function(el){ el.textContent = dash; });

  // At Crease player names and numbers
  document.querySelectorAll('.at-crease-name').forEach(function(el){
    var link = el.querySelector('a');
    if (link) link.textContent = dash; else el.textContent = dash;
  });
  document.querySelectorAll('.at-crease-num').forEach(function(el){ el.textContent = dash; });

  // Recent deliveries card body
  document.querySelectorAll('.section-card').forEach(function(card) {
    var title = (card.querySelector('.section-card-title')||{}).textContent || '';
    if (title.includes('Recent Deliveries')) {
      var hdr = card.querySelector('.section-card-header');
      card.innerHTML = (hdr ? hdr.outerHTML : '') + '<div style="padding:1rem;color:var(--text-muted);font-size:.8rem;">' + dash + '</div>';
    }
  });

  // Match information info-rows
  document.querySelectorAll('.info-row .info-row-value').forEach(function(el){ el.textContent = dash; });

  // Win probability team names + percentages
  document.querySelectorAll('.win-prob-team').forEach(function(el, i) {
    var team = i === 0 ? (t1||dash) : (t2||dash);
    el.innerHTML = (team !== dash && team) ? flInline(team, 16) + esc(team) : dash;
  });
  document.querySelectorAll('.win-prob-pct').forEach(function(el){ el.textContent = dash; });
  document.querySelectorAll('.win-prob-fill-ind, .win-prob-fill-aus').forEach(function(b){ b.style.width = '50%'; });

  // Partnerships
  document.querySelectorAll('.partnership-wkt').forEach(function(el){ el.textContent = dash; });
  document.querySelectorAll('.partnership-names').forEach(function(el){ el.textContent = dash; });
  document.querySelectorAll('.partnership-runs').forEach(function(el){ el.textContent = dash; });

  // Partnerships sidebar title
  document.querySelectorAll('.sidebar-card').forEach(function(card) {
    var titleEl = card.querySelector('.sidebar-card-title');
    if (titleEl && titleEl.textContent.includes('Partnership')) {
      titleEl.textContent = 'Partnerships';
    }
  });

  // Series status scores
  document.querySelectorAll('.series-team-name').forEach(function(el, i) {
    var team = i === 0 ? (t1||dash) : (t2||dash);
    el.innerHTML = (team !== dash) ? flInline(team, 16) + esc(team) : dash;
  });
  document.querySelectorAll('.series-score, .series-val, .score-box').forEach(function(el){ el.textContent = dash; });

  // Scorecard tables - clear all tbody rows
  document.querySelectorAll('.scorecard-table tbody, .data-table tbody').forEach(function(tbody){
    tbody.innerHTML = '<tr><td colspan="10" style="text-align:center;padding:1.2rem;color:var(--text-muted);">' + dash + '</td></tr>';
  });

  // innings-label-text: [0]=team1 batting, [1]=team2 bowling, [2]=team2 batting, [3]=team1 bowling
  var labelTexts = document.querySelectorAll('.innings-label-text');
  var inningsLabels = [
    [t1, '1st Innings'], [t2, 'Bowling'], [t2, '2nd Innings'], [t1, 'Bowling']
  ];
  labelTexts.forEach(function(el, i) {
    var pair = inningsLabels[i] || [dash, dash];
    var team = pair[0]; var type = pair[1];
    if (team && team !== dash) {
      el.innerHTML = flInline(team, 16) + esc(team) + ' — ' + type;
    } else {
      el.textContent = dash;
    }
  });

  // innings-total scores ("187 / 4  (18.2 ov)")
  document.querySelectorAll('.innings-total').forEach(function(el){ el.textContent = dash; });

  // extras-row and total-row inside scorecard tables
  document.querySelectorAll('.extras-row td:last-child, .extras-row td[colspan]').forEach(function(el){
    if (el.textContent.trim() !== 'Extras') el.textContent = dash;
  });
  document.querySelectorAll('.extras-row').forEach(function(row){
    row.querySelectorAll('td').forEach(function(td){ td.textContent = dash; });
  });
  document.querySelectorAll('.total-row').forEach(function(row){
    row.querySelectorAll('td').forEach(function(td){ td.textContent = dash; });
  });

  // Fall of wickets
  document.querySelectorAll('.fow-items').forEach(function(el){ el.innerHTML = ''; });
  document.querySelectorAll('.fow-strip').forEach(function(el){
    var lbl = el.querySelector('.fow-label');
    if (lbl) el.innerHTML = lbl.outerHTML + '<div class="fow-items"><span style="color:var(--text-muted);">' + dash + '</span></div>';
  });

  // Insights tab — win probability large numbers
  document.querySelectorAll('.win-prob-num').forEach(function(el){ el.textContent = dash; });
  document.querySelectorAll('.win-team-name').forEach(function(el, i){
    var team = i === 0 ? (t1||dash) : (t2||dash);
    el.innerHTML = (team !== dash) ? flInline(team, 14) + esc(team) : dash;
  });

  // ── Sidebar Match Stats card ──────────────────────────────────────────────
  document.querySelectorAll('.sidebar-stat-value').forEach(function(el) {
    el.textContent = '—';
  });
  document.querySelectorAll('.sidebar-stat-label').forEach(function(el) {
    var txt = el.textContent;
    // Update team references in labels (IND → t1, AUS → t2)
    if (t1 && t2) {
      el.textContent = txt
        .replace(/\(IND\)/g, '(' + t1 + ')')
        .replace(/\(AUS\)/g, '(' + t2 + ')');
    }
  });

  // ── Series Status sidebar card ─────────────────────────────────────────────
  var seriesCards = document.querySelectorAll('.sidebar-card');
  seriesCards.forEach(function(card) {
    var title = (card.querySelector('.sidebar-card-title') || {}).textContent || '';
    if (title.includes('Series Status')) {
      // Replace hardcoded India 2-0 Australia
      var hdr = card.querySelector('.sidebar-card-header');
      card.innerHTML = (hdr ? hdr.outerHTML : '<div class="sidebar-card-header"><div class="sidebar-card-title"><i class="fa fa-trophy"></i> Series Status</div></div>')
        + '<div style="padding:1rem 1.1rem;text-align:center;color:var(--text-muted);font-size:.83rem;">—</div>';
    }
  });

  // ── Context Insights hardcoded titles ──────────────────────────────────────
  document.querySelectorAll('.insight-card-title').forEach(function(el) {
    var txt = el.textContent;
    if (txt.includes('Wankhede') || txt.includes('H2H') || txt.includes('Head-to-Head')) {
      // Will be updated by updateH2H and updateVenueContext
    }
  });

  // Page title
  document.title = (t1 && t2 ? t1 + ' vs ' + t2 + ' — ' : '') + 'Match Detail · Criclytics';
}

// ── Update scoreboard with real data ─────────────────────────────────────────
function updateScoreboard(match) {
  var t1 = match.t1 || match.team1 || '';
  var t2 = match.t2 || match.team2 || '';
  var s1 = match.t1s || ''; var s2 = match.t2s || '';

  var n1 = document.getElementById('team1Name'); if (n1) n1.textContent = t1;
  var n2 = document.getElementById('team2Name'); if (n2) n2.textContent = t2;
  var sc1 = document.getElementById('team1Score'); if (sc1) sc1.textContent = s1 || '—';
  var sc2 = document.getElementById('team2Score'); if (sc2) sc2.textContent = s2 || '—';

  var flags = document.querySelectorAll('.scoreboard-flag');
  if (flags[0]) flags[0].innerHTML = flagCircle(t1, 44);
  if (flags[1]) flags[1].innerHTML = flagCircle(t2, 44);

  var statusEl = document.querySelector('.match-status-live');
  if (statusEl && match.status) statusEl.textContent = match.status;

  var metaItems = document.querySelectorAll('.match-meta-item');
  var metaData = [
    match.venue   ? '<i class="fa fa-location-dot"></i> ' + esc(match.venue) : null,
    match.date    ? '<i class="fa fa-calendar"></i> ' + esc(match.date) : null,
    match.series  ? '<i class="fa fa-trophy"></i> ' + esc(match.series) : null,
    match.matchType ? '<i class="fa fa-circle-dot" style="color:var(--green-live);"></i> ' + esc(match.matchType) : null,
    match.toss    ? '<i class="fa fa-user"></i> Toss: ' + esc(match.toss) : null,
  ];
  metaItems.forEach(function(el, i) {
    if (metaData[i]) el.innerHTML = metaData[i];
  });

  // Match Information card info-rows
  var infoMap = {
    'Series':       match.series,
    'Match':        match.name || match.matchType,
    'Venue':        match.venue,
    'Date & Time':  match.date,
    'Toss':         match.toss,
    'Series Score': match.status,
  };
  document.querySelectorAll('.info-row').forEach(function(row) {
    var lbl = ((row.querySelector('.info-row-label') || {}).textContent || '').trim();
    var valEl = row.querySelector('.info-row-value');
    if (valEl && infoMap[lbl] != null) valEl.textContent = infoMap[lbl];
  });

  // Win probability team names
  document.querySelectorAll('.win-prob-team').forEach(function(el, i) {
    el.innerHTML = flInline(i === 0 ? t1 : t2, 16) + esc(i === 0 ? t1 : t2);
  });
  document.querySelectorAll('.series-team-name').forEach(function(el, i) {
    el.innerHTML = flInline(i === 0 ? t1 : t2, 16) + esc(i === 0 ? t1 : t2);
  });

  // Partnerships header
  var pTitle = document.querySelector('.sidebar-card-title');
  document.querySelectorAll('.sidebar-card').forEach(function(card) {
    var title = (card.querySelector('.sidebar-card-title') || {}).textContent || '';
    if (title.includes('Partnership')) {
      var titleEl = card.querySelector('.sidebar-card-title');
      if (titleEl) titleEl.innerHTML = '<i class="fa fa-handshake"></i> Partnerships (' + esc(t1) + ')';
    }
  });

  if (t1 && t2) {
    document.title = t1 + ' vs ' + t2 + ' — Match Detail · Criclytics';
    // Update sidebar stat labels to show real team names
    document.querySelectorAll('.sidebar-stat-label').forEach(function(el) {
      var txt = el.textContent;
      el.textContent = txt.replace('(IND)', '(' + t1 + ')').replace('(AUS)', '(' + t2 + ')');
    });
  }

  var totals=document.querySelectorAll('.innings-total');
  if(totals[0]&&s1)totals[0].textContent=s1;
  if(totals[1]&&s2)totals[1].textContent=s2;
  if(s1){var rm=s1.match(/(\d+)/);if(rm){var tEl=document.querySelector('.target-box .value');if(tEl)tEl.textContent=parseInt(rm[1])+1;}}
  if(match.name){var bc=document.querySelector('.breadcrumb span:last-child');if(bc)bc.textContent=match.name;document.title=match.name+' · Criclytics';}
  if(match.matchEnded)document.querySelectorAll('.scoreboard-crr').forEach(function(el){el.textContent='Final';});
}

// ── Batting scorecard ─────────────────────────────────────────────────────────
function updateBattingScorecard(innings, id) {
  var tbody = document.querySelector('#' + id + ' tbody') || document.querySelector('[data-innings="' + id + '"] tbody');
  if (!tbody) return;
  if (!innings || !innings.length) {
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:1rem;color:var(--text-muted);">—</td></tr>';
    return;
  }
  tbody.innerHTML = innings.map(function(b) {
    var name = b.batsman || b.batter || b.name || '—';
    return '<tr>'
      + '<td><a href="player-profile.html?name=' + encodeURIComponent(name) + '" style="font-weight:600;color:var(--text-primary);text-decoration:none;">' + esc(name) + '</a>'
      + '<div style="font-size:.7rem;color:var(--text-muted)">' + esc(b.dismissal || b.wicket || 'not out') + '</div></td>'
      + '<td class="mono">' + d(b.r || b.runs) + '</td>'
      + '<td class="mono">' + d(b.b || b.balls) + '</td>'
      + '<td class="mono">' + d(b['4s'] || b.fours) + '</td>'
      + '<td class="mono">' + d(b['6s'] || b.sixes) + '</td>'
      + '<td class="mono" style="color:var(--accent)">' + d(b.sr || b.strike_rate) + '</td>'
    + '</tr>';
  }).join('');
}

// ── Bowling scorecard ─────────────────────────────────────────────────────────
function updateBowlingScorecard(bowling, id) {
  var tbody = document.querySelector('#' + id + ' tbody') || document.querySelector('[data-innings="' + id + '"] tbody');
  if (!tbody) return;
  if (!bowling || !bowling.length) {
    tbody.innerHTML = '<tr><td colspan="8" style="text-align:center;padding:1rem;color:var(--text-muted);">—</td></tr>';
    return;
  }
  tbody.innerHTML = bowling.map(function(b) {
    var name = b.bowler || b.name || '—';
    return '<tr>'
      + '<td><a href="player-profile.html?name=' + encodeURIComponent(name) + '" style="font-weight:600;color:var(--text-primary);text-decoration:none;">' + esc(name) + '</a></td>'
      + '<td class="mono">' + d(b.o || b.overs)   + '</td>'
      + '<td class="mono">' + d(b.m || b.maidens)  + '</td>'
      + '<td class="mono">' + d(b.r || b.runs)     + '</td>'
      + '<td class="mono" style="color:var(--accent)">' + d(b.w || b.wickets) + '</td>'
      + '<td class="mono">' + d(b.eco || b.economy) + '</td>'
      + '<td class="mono">' + d(b.wd || b.wides)   + '</td>'
      + '<td class="mono">' + d(b.nb || b.noballs)  + '</td>'
    + '</tr>';
  }).join('');
}

// ── H2H ───────────────────────────────────────────────────────────────────────
async function updateH2H(t1, t2) {
  var data = await apiFetch('/api/h2h?team_a=' + encodeURIComponent(t1) + '&team_b=' + encodeURIComponent(t2) + '&format=T20I');
  if (!data) return;
  var r = Object.values(data)[0];
  if (!r) return;

  var h2hNames = document.querySelectorAll('.h2h-team-name');
  if (h2hNames[0]) h2hNames[0].innerHTML = flInline(t1, 16) + esc(t1);
  if (h2hNames[1]) h2hNames[1].innerHTML = flInline(t2, 16) + esc(t2);

  var h2hWins = document.querySelectorAll('.h2h-wins');
  if (h2hWins[0]) h2hWins[0].textContent = r.team_a_wins || r.won || 0;
  if (h2hWins[1]) h2hWins[1].textContent = r.team_b_wins || r.lost || 0;

  var total = r.matches || 1;
  var pA = Math.round(((r.team_a_wins || r.won || 0) / total) * 100);
  var pB = Math.round(((r.team_b_wins || r.lost || 0) / total) * 100);
  var bars = document.querySelectorAll('.h2h-bar-fill, .h2h-fill');
  if (bars[0]) bars[0].style.width = pA + '%';
  if (bars[1]) bars[1].style.width = pB + '%';

  var totalEl = document.querySelector('.h2h-total, .h2h-matches');
  if (totalEl) totalEl.textContent = total + ' T20I matches';
}

// ── Venue context ─────────────────────────────────────────────────────────────
async function updateVenueContext(venue) {
  var data = await apiFetch('/api/venues/' + encodeURIComponent(venue));
  if (!data) return;
  var t20 = data.t20i || {};
  var map = {
    'Avg 1st Innings': t20.avg_1st_innings ? Math.round(t20.avg_1st_innings) : null,
    'Chase Win %':     data.chase_win_pct ? data.chase_win_pct + '%' : null,
    'Highest Total':   t20.highest || null,
    'Avg Powerplay':   t20.avg_powerplay ? Math.round(t20.avg_powerplay) : null,
  };
  document.querySelectorAll('.venue-stat-row, .venue-context-stat').forEach(function(row) {
    var lbl = ((row.querySelector('.venue-stat-label, label') || {}).textContent || '').trim();
    var valEl = row.querySelector('.venue-stat-val, .val');
    if (valEl && map[lbl] != null) valEl.textContent = map[lbl];
  });
}

// ── Main loader ───────────────────────────────────────────────────────────────
async function loadMatchDetail() {
  var matchId = getParam('id');

  // ALWAYS wipe hardcoded content first
  wipePage();

  if (!matchId) {
    var ma=document.getElementById('panel-overview')||document.querySelector('.tab-panels');
    if(ma)ma.innerHTML='<div style="text-align:center;padding:4rem 2rem;color:var(--text-muted);"><i class="fa fa-cricket-bat-ball" style="font-size:3rem;display:block;margin-bottom:1.5rem;opacity:0.25;"></i><div style="font-size:1.1rem;font-weight:600;margin-bottom:0.5rem;color:var(--text-primary);">No match selected</div><div style="margin-bottom:1.5rem;font-size:.9rem;">Browse matches to view scorecard.</div><a href="matches.html" class="btn btn-primary"><i class="fa fa-arrow-left"></i> Browse Matches</a></div>';
    return;
  }

  // Try to find match in cached matches list first (fastest, most reliable)
  var match = null;
  var allData = await apiFetch('/api/matches');
  if (allData && allData.data) {
    match = allData.data.find(function(m) {
      return String(m.id || m.unique_id || '') === String(matchId);
    }) || null;
  }

  // Also try live endpoint
  if (!match) {
    var liveData = await apiFetch('/api/live');
    if (liveData && liveData.data) {
      match = liveData.data.find(function(m) {
        return String(m.id || m.unique_id || '') === String(matchId);
      }) || null;
    }
  }

  // Try CricAPI direct endpoints (works when API is accessible)
  if (!match) {
    var scoreData = await apiFetch('/api/matches/' + matchId + '/score');
    if (scoreData && scoreData.data && Object.keys(scoreData.data).length) {
      match = scoreData.data;
    }
  }
  if (!match) {
    var matchData = await apiFetch('/api/matches/' + matchId);
    if (matchData && matchData.data && Object.keys(matchData.data).length) {
      match = matchData.data;
    }
  }

  var t1 = (match && (match.t1 || match.team1)) || '';
  var t2 = (match && (match.t2 || match.team2)) || '';

  // Re-wipe with team names (shows flags + names even when no scorecard)
  wipePage(t1, t2);

  if (!match) {
    var statusEl2 = document.querySelector('.match-status-live');
    if (statusEl2) {
      statusEl2.innerHTML = 'Live data unavailable · <a href="matches.html" style="color:var(--accent);text-decoration:none;">← Back to Matches</a>';
      statusEl2.style.fontSize = '0.78rem';
    }
    return;
  }

  // We have at least basic match info — fill in what we have
  updateScoreboard(match);

  // COMPLETED: hide live-only sections, change badge
  if (match.matchEnded) {
    document.querySelectorAll('.section-card').forEach(function(card) {
      var t=((card.querySelector('.section-card-title')||{}).textContent||'');
      if(t.includes('Live Snapshot')||t.includes('At the Crease')||t.includes('Current Bowler')||t.includes('Recent Deliveries'))card.style.display='none';
    });
    document.querySelectorAll('.status-badge.status-live').forEach(function(el){el.textContent='Completed';el.className='status-badge status-completed';});
  }

  // UPCOMING: hide scorecard + live sections
  if (!match.matchStarted && !match.matchEnded) {
    var sp=document.getElementById('panel-scorecard');
    if(sp)sp.innerHTML='<div style="text-align:center;padding:3rem 2rem;color:var(--text-muted);"><i class="fa fa-clock" style="font-size:2.5rem;display:block;margin-bottom:1rem;opacity:0.3;"></i><div style="font-size:1rem;font-weight:600;">Match not started</div><div style="font-size:.85rem;margin-top:.3rem;">Scorecard available once match begins.</div></div>';
    document.querySelectorAll('.section-card').forEach(function(card){
      var t=((card.querySelector('.section-card-title')||{}).textContent||'');
      if(t.includes('Live Snapshot')||t.includes('At the Crease')||t.includes('Current Bowler')||t.includes('Recent Deliveries'))card.style.display='none';
    });
    document.querySelectorAll('.innings-total,.scoreboard-crr').forEach(function(el){el.textContent='';});
  }

  // Innings labels (always set even if no scorecard data)
  document.querySelectorAll('.innings-label-text').forEach(function(el, i) {
    var team = i === 0 ? t1 : (i === 1 ? t2 : (i === 2 ? t2 : t1));
    var suffix = (i === 0) ? '1st Innings' : (i === 1 ? 'Bowling' : (i === 2 ? '2nd Innings' : 'Bowling'));
    el.innerHTML = flInline(team, 16) + esc(team) + ' — ' + suffix;
  });

  // Innings scorecards — only if ball-by-ball data available (CricAPI live)
  var innings = match.score || match.innings || [];
  if (innings.length && innings[0] && innings[0].batting) {
    updateBattingScorecard(innings[0].batting, 'innings1-batting');
    updateBowlingScorecard(innings[0].bowling, 'innings1-bowling');
  }
  if (innings.length > 1 && innings[1] && innings[1].batting) {
    updateBattingScorecard(innings[1].batting, 'innings2-batting');
    updateBowlingScorecard(innings[1].bowling, 'innings2-bowling');
  }

  // Score from simple score array (CricAPI format: [{r,w,o,inning}])
  var simpleScores = match.score;
  if (simpleScores && simpleScores.length && !simpleScores[0].batting) {
    // Simple score objects, not full innings
    var totals = document.querySelectorAll('.innings-total');
    if (simpleScores[0] && totals[0]) {
      var s0 = simpleScores[0];
      totals[0].textContent = s0.r + '/' + s0.w + ' (' + s0.o + 'ov)';
    }
    if (simpleScores[1] && totals[1]) {
      var s1 = simpleScores[1];
      totals[1].textContent = s1.r + '/' + s1.w + ' (' + s1.o + 'ov)';
    }
  }

  if (t1 && t2) updateH2H(t1, t2);
  if (match.venue) updateVenueContext(match.venue);
}

document.addEventListener('DOMContentLoaded', loadMatchDetail);
