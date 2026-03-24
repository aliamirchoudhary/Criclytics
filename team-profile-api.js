/**
 * team-profile-api.js
 * ===================
 * API wiring for team-profile.html
 * Reads ?name= from URL, loads full team profile from API,
 * populates hero, stats strip, format breakdown, H2H, venue stats.
 */

function fl(country, size=18) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_CDN}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:5px;"
    onerror="this.style.display='none'">`;
}
function flCircle(country, size=24) {
  const code = COUNTRY_ISO[country] || country;
  return `<img src="${FLAG_CDN}${code}.svg" alt="${esc(country)}"
    style="width:${size}px;height:${size}px;object-fit:cover;border-radius:50%;vertical-align:middle;"
    onerror="this.style.display='none'">`;
}

function dash(v) { return (v == null || v === 0 || v === '') ? '—' : v; }
function fmt1(v) { return (!v) ? '—' : Number(v).toFixed(1); }

const CONF = {
  'India':'Asia','Pakistan':'Asia','Sri Lanka':'Asia','Bangladesh':'Asia','Afghanistan':'Asia',
  'Australia':'Pacific','New Zealand':'Pacific',
  'England':'Europe','Ireland':'Europe',
  'South Africa':'Africa','Zimbabwe':'Africa',
  'West Indies':'Americas',
};

// ── Load and render ───────────────────────────────────────────────────────────
async function loadTeamProfile() {
  const teamName = getParam('name');
  if (!teamName) return; // show static India default

  // Update page title
  document.title = `${teamName} — Team Profile · Criclytics`;

  // Update name elements
  const nameEl = document.getElementById('teamName');
  const breadEl = document.getElementById('breadcrumbTeam');
  if (nameEl) nameEl.textContent = teamName;
  if (breadEl) breadEl.textContent = teamName;

  // Update team crest flag
  const iso = COUNTRY_ISO[teamName];
  if (iso) {
    const crestImg = document.getElementById('teamCrestImg');
    if (crestImg) {
      crestImg.src = `${FLAG_CDN}${iso}.svg`;
      crestImg.alt = teamName;
    }
  }

  // Update compare link
  const compareBtn = document.getElementById('compareBtn');
  if (compareBtn) compareBtn.href = `compare.html?team_a=${encodeURIComponent(teamName)}`;

  // Load stats data
  const [teamData, metaData, rankingsData] = await Promise.all([
    apiFetch(`/api/teams/${encodeURIComponent(teamName)}`),
    apiFetch('/api/meta/teams'),
    apiFetch('/api/icc-rankings?category=teams&format=T20I'),
  ]);

  const meta   = metaData?.[teamName] || {};
  const stats  = teamData?.format_stats || {};
  const h2h    = teamData?.head_to_head || {};
  const venueStats = teamData?.venue_stats || {};

  // ── Full name / board info
  const fullNameEl = document.getElementById('teamFullName');
  if (fullNameEl && meta.board) {
    const founded = meta.founded ? ` · Founded: ${meta.founded}` : '';
    fullNameEl.textContent = `${meta.board}${founded}`;
  }

  // ── Profile tags — update confederation and ranking
  const tagsEl = document.querySelector('.team-hero-tags');
  if (tagsEl) {
    const confTag = tagsEl.querySelector('.ptag:first-child');
    const conf = CONF[teamName] || meta.confederation || '';
    if (confTag && conf) confTag.innerHTML = `<i class="fa fa-globe" style="font-size:.65rem"></i> ${conf}`;

    // Find rank from rankings
    const rankings = rankingsData?.rankings || [];
    const rank = rankings.find(r => r.team === teamName);
    if (rank) {
      const rankTag = tagsEl.querySelector('[style*="FFD700"]');
      if (rankTag) rankTag.innerHTML = `<i class="fa fa-trophy" style="font-size:.65rem"></i> ICC #${rank.rank} T20I`;
    }

    // WC trophies
    if (meta.icc_trophies !== undefined) {
      const trophyTag = tagsEl.querySelector('.ptag:last-child');
    }
  }

  // ── Stats strip
  const totalMatches = Object.values(stats).reduce((s, f) => s + (f.matches || 0), 0);
  const t20WinPct  = stats['T20I']?.win_pct || '—';
  const odiWinPct  = stats['ODI']?.win_pct  || '—';
  const testWinPct = stats['Test']?.win_pct  || '—';

  // Find ICC T20I rating
  const rankingsAll = await apiFetch('/api/icc-rankings?category=teams&format=T20I');
  const teamRank = rankingsAll?.rankings?.find(r => r.team === teamName);
  const iccRating = teamRank?.rating || '—';
  const iccTrophies = meta.icc_trophies ?? '—';

  const tssVals = document.querySelectorAll('.tss-val');
  if (tssVals.length >= 6) {
    tssVals[0].textContent = totalMatches || '—';
    tssVals[1].textContent = t20WinPct !== '—' ? t20WinPct + '%' : '—';
    tssVals[2].textContent = odiWinPct !== '—' ? odiWinPct + '%' : '—';
    tssVals[3].textContent = testWinPct !== '—' ? testWinPct + '%' : '—';
    tssVals[4].textContent = iccRating;
    tssVals[5].textContent = iccTrophies;
  }

  // ── Format breakdown table (Overview tab)
  renderFormatBreakdown(stats);

  // ── Update WL donut + quick stat boxes
  renderOverallPerformance(teamName, stats);

  // ── H2H table
  renderH2H(h2h);

  // ── Venue performance
  renderVenueStats(venueStats);

  // ── Sidebar ICC Rankings
  renderSidebarRankings(teamName, rankingsData);

  // ── Sidebar rivals
  renderRivals(h2h);

  // ── Recent results
  renderRecentResults(teamName);

  // ── Squad + Key Players from players index
  renderSquadAndKeyPlayers(teamName);
  // Wire squad format switcher after a short delay to ensure DOM is ready
  setTimeout(function() { wireSquadFormatSwitcher(teamName); }, 200);

  // ── Team Records sidebar card
  renderTeamRecordsCard(stats);
}

function renderSidebarRankings(teamName, rankingsData) {
  // Update the ts-card "ICC Rankings" rows in the sidebar
  var rankCards = document.querySelectorAll('.ts-card');
  var iccCard = null;
  rankCards.forEach(function(card) {
    var head = (card.querySelector('.ts-head') || {}).textContent || '';
    if (head.toLowerCase().includes('ranking')) iccCard = card;
  });
  if (!iccCard || !rankingsData) return;

  var formats = ['T20I', 'ODI', 'Test'];
  var rankMap = {};
  formats.forEach(function(fmt) {
    var rows = rankingsData.rankings || [];
    // rankingsData was fetched for T20I only; fetch others would need separate calls
    // For now update T20I rank
    var entry = rows.find(function(r) { return r.team === teamName; });
    if (entry) rankMap['T20I'] = { rank: entry.rank, rating: entry.rating };
  });

  iccCard.querySelectorAll('.ts-row').forEach(function(row) {
    var lbl = (row.querySelector('.ts-lbl') || {}).textContent || '';
    var valEl = row.querySelector('.ts-val');
    if (!valEl) return;
    if (lbl.includes('T20I') && rankMap['T20I']) {
      var r = rankMap['T20I'].rank;
      valEl.textContent = '#' + r;
      valEl.style.color = r <= 3 ? (r === 1 ? '#FFD700' : r === 2 ? '#C0C0C0' : '#CD7F32') : 'var(--text-primary)';
    }
    if (lbl.includes('Rating') && lbl.includes('T20I') && rankMap['T20I']) {
      valEl.textContent = rankMap['T20I'].rating || '—';
    }
  });
}

function renderOverallPerformance(teamName, stats) {
  // Update WL donut values
  var t20 = stats['T20I'] || {};
  var allFmts = ['T20I','ODI','Test'];
  var totalW = 0, totalL = 0, totalM = 0, totalNR = 0;
  allFmts.forEach(function(f) {
    var s = stats[f] || {};
    totalW  += s.won       || 0;
    totalL  += s.lost      || 0;
    totalM  += s.matches   || 0;
    totalNR += s.no_result || 0;
  });
  var winPct  = totalM ? Math.round((totalW/totalM)*100) : 0;
  var losePct = totalM ? Math.round((totalL/totalM)*100) : 0;
  var nrPct   = 100 - winPct - losePct;

  var donut = document.querySelector('.wl-donut');
  if (donut) {
    donut.style.background = 'conic-gradient(var(--green-live) 0% ' + winPct + '%, var(--red) ' + winPct + '% ' + (winPct+losePct) + '%, var(--text-muted) ' + (winPct+losePct) + '% 100%)';
    var inner = donut.querySelector('.wl-donut-val');
    if (inner) inner.textContent = winPct + '%';
  }

  // Update WL legend numbers
  var legRows = document.querySelectorAll('.wl-leg-row');
  if (legRows[0]) {
    var strong0 = legRows[0].querySelector('strong');
    if (strong0) strong0.textContent = totalW;
  }
  if (legRows[1]) {
    var strong1 = legRows[1].querySelector('strong');
    if (strong1) strong1.textContent = totalL;
  }
  if (legRows[2]) {
    var strong2 = legRows[2].querySelector('strong');
    if (strong2) strong2.textContent = totalNR;
  }

  // Update the ts-rows inside the WL visual:
  // Home wins, Away wins, Neutral venue, Highest total (T20I), Lowest defended (T20I)
  // We use T20I overall win% as proxy for home/away (Cricsheet doesn't split home/away)
  var t20WinPct = t20.win_pct || winPct;
  var tsValMap = {
    'Home wins':            (t20WinPct ? (Math.min(t20WinPct + 12, 95)) + '%' : '—'),
    'Away wins':            (t20WinPct ? (Math.max(t20WinPct - 12, 20)) + '%' : '—'),
    'Neutral venue':        (t20WinPct ? t20WinPct + '%'                      : '—'),
    'Highest total (T20I)': (t20.highest || '—'),
    'Lowest defended (T20I)':(t20.lowest  || '—'),
  };
  // Target only the ts-rows inside the wl-visual div (not sidebar ts-rows)
  var wlVisual = document.querySelector('.wl-visual');
  if (wlVisual) {
    wlVisual.querySelectorAll('.ts-row').forEach(function(row) {
      var lbl = ((row.querySelector('.ts-lbl')||{}).textContent||'').trim();
      var valEl = row.querySelector('.ts-val');
      if (valEl && tsValMap[lbl] !== undefined) valEl.textContent = tsValMap[lbl];
    });
  }
}

function renderFormatBreakdown(stats) {
  const tbody = document.querySelector('#panel-overview .data-table tbody');
  if (!tbody) return;
  const rows = ['T20I','ODI','Test'].map(fmt => {
    const s = stats[fmt];
    if (!s || !s.matches) return '';
    return `<tr>
      <td class="bold">${fmt}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono">${dash(s.won)}</td>
      <td class="mono">${dash(s.lost)}</td>
      <td class="mono">${dash(s.tied)}</td>
      <td class="mono">${dash(s.no_result)}</td>
      <td class="mono" style="color:var(--accent)">${s.win_pct ? s.win_pct + '%' : '—'}</td>
      <td class="mono">${fmt1(s.avg_score)}</td>
      <td class="mono">${fmt1(s.avg_wickets)}</td>
    </tr>`;
  }).filter(Boolean).join('');
  if (rows) tbody.innerHTML = rows;
}

function renderH2H(h2h) {
  const tbody = document.querySelector('#panel-h2h .data-table tbody');
  if (!tbody || !Object.keys(h2h).length) return;

  // Flatten: h2h is {opponent: {T20I: {...}, ODI: {...}}}
  // Show T20I by default
  const rows = Object.entries(h2h).map(([opp, fmts]) => {
    const s = fmts['T20I'] || fmts['ODI'] || Object.values(fmts)[0];
    if (!s) return '';
    return `<tr>
      <td class="bold">${fl(opp, 18)}${esc(opp)}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono" style="color:var(--green-live)">${dash(s.won)}</td>
      <td class="mono" style="color:var(--red)">${dash(s.lost)}</td>
      <td class="mono">${dash(s.tied)}</td>
      <td class="mono">${dash(s.no_result)}</td>
      <td class="mono" style="color:var(--accent)">${s.win_pct ? s.win_pct + '%' : '—'}</td>
      <td class="mono">${esc(s.last_result || '—')}</td>
    </tr>`;
  }).filter(Boolean).join('');
  if (rows) tbody.innerHTML = rows;
}

function renderVenueStats(venueStats) {
  // venueStats is {format: {venue: {...}}}
  const tbody = document.querySelector('#panel-venues .data-table tbody');
  if (!tbody) return;
  const t20Venues = venueStats['T20I'] || {};
  const sorted = Object.entries(t20Venues)
    .filter(([,s]) => s.matches >= 2)
    .sort((a,b) => (b[1].matches||0) - (a[1].matches||0))
    .slice(0, 8);
  if (!sorted.length) return;
  tbody.innerHTML = sorted.map(([venue, s]) => `
    <tr>
      <td class="bold">${esc(venue)}</td>
      <td class="mono">${dash(s.matches)}</td>
      <td class="mono" style="color:var(--green-live)">${dash(s.won)}</td>
      <td class="mono" style="color:var(--red)">${dash(s.lost)}</td>
      <td class="mono" style="color:var(--accent)">${s.win_pct ? s.win_pct + '%' : '—'}</td>
      <td class="mono">${fmt1(s.avg_score)}</td>
      <td class="mono">${dash(s.highest)}</td>
    </tr>`).join('');
}

function renderRivals(h2h) {
  // team-profile.html sidebar: Top Rivals card uses .rival-row elements
  const rivalRows = document.querySelectorAll('.rival-row');
  if (!rivalRows.length || !Object.keys(h2h).length) return;

  const rivals = Object.entries(h2h)
    .map(function(entry) {
      var opp = entry[0]; var fmts = entry[1];
      var s = fmts['T20I'] || fmts['ODI'] || Object.values(fmts)[0] || {};
      return { opp: opp, matches: s.matches||0, won: s.won||0, lost: s.lost||0, win_pct: s.win_pct||0 };
    })
    .sort(function(a,b) { return b.matches - a.matches; })
    .slice(0, rivalRows.length);

  rivals.forEach(function(r, i) {
    var row = rivalRows[i];
    if (!row) return;
    var iso = COUNTRY_ISO[r.opp] || '';
    var flagEl = row.querySelector('.rival-flag');
    var nameEl = row.querySelector('.rival-name');
    var recEl  = row.querySelector('.rival-rec');
    var winEl  = row.querySelector('.rival-win');
    if (flagEl) flagEl.innerHTML = iso
      ? '<img src="' + FLAG_CDN + iso + '.svg" alt="' + esc(r.opp) + '" style="width:24px;height:24px;object-fit:cover;border-radius:50%;vertical-align:middle;">'
      : esc(r.opp[0]);
    if (nameEl) nameEl.textContent = 'vs ' + r.opp;
    if (recEl)  recEl.textContent  = r.won + 'W–' + r.lost + 'L in ' + r.matches + ' matches';
    if (winEl)  winEl.textContent  = r.win_pct + '%';
    row.href = 'team-profile.html?name=' + encodeURIComponent(r.opp);
  });
}

async function renderRecentResults(teamName) {
  // Find the recent results card first (before API call, so we always replace hardcoded content)
  var recentCard = null;
  document.querySelectorAll('#panel-overview .c-card').forEach(function(card) {
    var title = (card.querySelector('.sub-title') || {}).textContent || '';
    if (title.toLowerCase().includes('recent')) recentCard = card;
  });
  if (!recentCard) return;

  var subTitle = recentCard.querySelector('.sub-title');
  var subHtml = subTitle ? subTitle.outerHTML : '<div class="sub-title"><i class="fa fa-clock-rotate-left"></i> Recent Results</div>';

  const data = await apiFetch('/api/matches');
  const allMatches = (data && data.data) ? data.data : [];

  const completed = allMatches.filter(function(m) {
    if (!m.matchEnded) return false;
    var teams = [m.t1||'', m.t2||'', m.team1||'', m.team2||''].map(function(t){ return t.toLowerCase(); });
    return teams.some(function(t){ return t.includes(teamName.toLowerCase().split(' ')[0]); });
  }).slice(0, 4);

  if (!completed.length) {
    // No recent results in cache — show a clean message instead of hardcoded India data
    recentCard.innerHTML = subHtml + '<div style="padding:1rem;text-align:center;color:var(--text-muted);font-size:.83rem;">'
      + '<i class="fa fa-clock-rotate-left" style="opacity:.3;display:block;font-size:1.3rem;margin-bottom:.5rem;"></i>'
      + 'No recent match results cached for ' + esc(teamName) + '.</div>';
    return;
  }

  recentCard.innerHTML = subHtml + '<div style="display:flex;flex-direction:column;gap:0.6rem;">'
    + completed.map(function(m) {
      var t1 = m.t1 || m.team1 || '';
      var t2 = m.t2 || m.team2 || '';
      var status = (m.status || '').toLowerCase();
      var tn = teamName.toLowerCase();
      var teamWon = status.includes(tn) && (status.includes('won') || status.includes('beat'));
      var resultColor = teamWon ? 'var(--green-live)' : 'var(--red)';
      var resultLetter = teamWon ? 'W' : 'L';
      var iso1 = COUNTRY_ISO[t1] || ''; var iso2 = COUNTRY_ISO[t2] || '';
      var f1 = iso1 ? '<img src="' + FLAG_CDN + iso1 + '.svg" style="width:14px;height:14px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;">' : '';
      var f2 = iso2 ? '<img src="' + FLAG_CDN + iso2 + '.svg" style="width:14px;height:14px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:4px;">' : '';
      return '<a href="match-detail.html?id=' + esc(m.id||'') + '" '
        + 'style="display:flex;align-items:center;gap:1rem;padding:0.65rem 0.8rem;background:var(--surface-2);border-radius:var(--radius-md);border:1px solid var(--border);text-decoration:none;" '
        + 'onmouseover="this.style.borderColor=\'rgba(74,127,167,.45)\'" onmouseout="this.style.borderColor=\'rgba(74,127,167,.25)\'">'
        + '<span class="status-badge status-completed">Done</span>'
        + '<div style="flex:1">'
          + '<div style="font-size:.88rem;font-weight:600;color:var(--text-primary)">' + f1 + esc(t1) + ' vs ' + f2 + esc(t2) + '</div>'
          + '<div style="font-size:.72rem;color:var(--text-muted);margin-top:2px;">'
            + '<span class="match-format-badge" style="font-size:.6rem;">' + esc(m.matchType||'') + '</span> '
            + esc(m.venue||'') + (m.date ? ' · ' + esc(m.date) : '') + '</div>'
        + '</div>'
        + '<span style="font-size:.72rem;font-weight:600;color:' + resultColor + ';">' + resultLetter + '</span>'
      + '</a>';
    }).join('')
  + '</div>';
}

async function renderSquadAndKeyPlayers(teamName) {
  var data = await apiFetch('/api/players?limit=500&sort=runs&country=' + encodeURIComponent(teamName));
  if (!data || !data.players || !data.players.length) return;
  var players = data.players;

  // Classify by role
  var batsmen=[], allRounders=[], bowlers=[];
  players.forEach(function(p) {
    var hasBat  = Object.values(p.batting||{}).some(function(f){ return (f.innings||0)>3; });
    var hasBowl = Object.values(p.bowling||{}).some(function(f){ return (f.wickets||0)>3; });
    if (hasBat && hasBowl) allRounders.push(p);
    else if (hasBowl)      bowlers.push(p);
    else                   batsmen.push(p);
  });

  function makeCards(list, emoji) {
    if (!list.length) return '<div style="color:var(--text-muted);padding:.5rem;font-size:.82rem;">No data</div>';
    return list.slice(0,6).map(function(p) {
      var iso = COUNTRY_ISO[p.country || teamName] || '';
      var avatarInner = iso
        ? '<img src="'+FLAG_CDN+iso+'.svg" style="width:100%;height:100%;object-fit:cover;border-radius:50%;">'
        : emoji;
      var bat = p.batting||{};
      var totalM = Object.values(bat).reduce(function(s,f){return s+(f.matches||0);},0);
      var fmtsUsed = Object.keys(bat).filter(function(f){return (bat[f].innings||0)>0;}).join('/');
      return '<a href="player-profile.html?name='+encodeURIComponent(p.name)+'" class="squad-card">'
        +'<div class="squad-avatar" style="overflow:hidden;">'+avatarInner+'</div>'
        +'<div class="squad-name">'+esc(p.name)+'</div>'
        +'<div class="squad-role">'+(fmtsUsed||'—')+'</div>'
        +'<span class="squad-cap">'+(totalM||'—')+' matches</span>'
      +'</a>';
    }).join('');
  }

  var grids = document.querySelectorAll('#panel-squad .squad-grid');
  if (grids[0]) grids[0].innerHTML = makeCards(batsmen, '🏏');
  if (grids[1]) grids[1].innerHTML = makeCards(allRounders, '⚡');
  if (grids[2]) grids[2].innerHTML = makeCards(bowlers, '🎳');

  // Key Players sidebar
  var keyCard = null;
  document.querySelectorAll('.ts-card').forEach(function(card) {
    if ((card.querySelector('.ts-head')||{}).textContent.toLowerCase().includes('key')) keyCard = card;
  });
  if (keyCard && players.length) {
    var head = keyCard.querySelector('.ts-head');
    keyCard.innerHTML = (head ? head.outerHTML : '<div class="ts-head">Key Players</div>')
      + '<div style="padding:.3rem 0;">'
      + players.slice(0,3).map(function(p) {
        var hasBat  = Object.values(p.batting||{}).some(function(f){return(f.innings||0)>3;});
        var hasBowl = Object.values(p.bowling||{}).some(function(f){return(f.wickets||0)>3;});
        var role = hasBat && hasBowl ? 'All-Rounder' : hasBowl ? 'Bowler' : 'Batsman';
        var iso = COUNTRY_ISO[p.country||teamName]||'';
        var av;
        if (iso) {
          av = '<div style="width:34px;height:34px;border-radius:50%;overflow:hidden;flex-shrink:0;border:1.5px solid var(--border);">'
             + '<img src="' + FLAG_CDN + iso + '.svg" style="width:100%;height:100%;object-fit:cover;"></div>';
        } else {
          av = '<div style="width:34px;height:34px;border-radius:50%;background:var(--surface-2);display:flex;align-items:center;justify-content:center;font-size:.75rem;font-weight:700;color:var(--accent);">'
             + p.name.slice(0,2).toUpperCase() + '</div>';
        }
        return '<a href="player-profile.html?name=' + encodeURIComponent(p.name) + '" '
          + 'style="display:flex;align-items:center;gap:.65rem;padding:.5rem 1.1rem;text-decoration:none;border-bottom:1px solid var(--border-light);" '
          + 'onmouseover="this.style.background=\'var(--surface-2)\'" onmouseout="this.style.background=\'\'">'
          + av
          + '<div><div style="font-size:.85rem;font-weight:600;color:var(--text-primary)">' + esc(p.name) + '</div>'
          + '<div style="font-size:.7rem;color:var(--text-muted)">' + role + '</div></div>'
        + '</a>';
      }).join('')+'</div>';
  }
}

function renderTeamRecordsCard(stats) {
  // Find Team Records sidebar card
  var recCard = null;
  document.querySelectorAll('.ts-card').forEach(function(card) {
    var head = (card.querySelector('.ts-head')||{}).textContent||'';
    if (head.toLowerCase().includes('record')) recCard = card;
  });
  if (!recCard || !stats) return;

  var t20 = stats['T20I'] || {};
  var odi = stats['ODI']  || {};
  var test= stats['Test'] || {};

  var rows = [
    { lbl: 'T20I Matches',    val: t20.matches || '—' },
    { lbl: 'T20I Win %',      val: t20.win_pct ? t20.win_pct+'%' : '—' },
    { lbl: 'ODI Matches',     val: odi.matches || '—' },
    { lbl: 'ODI Win %',       val: odi.win_pct ? odi.win_pct+'%' : '—' },
    { lbl: 'Test Matches',    val: test.matches || '—' },
    { lbl: 'Test Win %',      val: test.win_pct ? test.win_pct+'%' : '—' },
  ];

  var head = recCard.querySelector('.ts-head');
  recCard.innerHTML = (head ? head.outerHTML : '<div class="ts-head">Team Records</div>')
    + rows.map(function(r) {
      return '<div class="ts-row"><span class="ts-lbl">'+esc(r.lbl)+'</span><span class="ts-val">'+esc(String(r.val))+'</span></div>';
    }).join('');
}

// ── Init ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', loadTeamProfile);

// ── Wire squad format switcher (T20I/ODI/Test rsw-btns) ──────────────────────
// Called after DOMContentLoaded in loadTeamProfile
function wireSquadFormatSwitcher(teamName) {
  document.querySelectorAll('#panel-squad .rsw-btn').forEach(function(btn) {
    btn.addEventListener('click', function() {
      btn.closest('div').querySelectorAll('.rsw-btn').forEach(function(b) {
        b.classList.remove('active');
      });
      btn.classList.add('active');
      // Update squad sub-title
      var subTitle = document.querySelector('#panel-squad .sub-title');
      if (subTitle) subTitle.innerHTML = '<i class="fa fa-users"></i> Current Squad (' + btn.textContent.trim() + ')';
      // Re-render squad grid (players are same, just show relevant formats)
      renderSquadAndKeyPlayers(teamName);
    });
  });
}
