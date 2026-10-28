/* Data-driven application UI. Provider strings are rendered as text, never HTML. */
(function () {
  'use strict';
  if (document.documentElement.dataset.criclyticsInitialized) return;
  document.documentElement.dataset.criclyticsInitialized = 'true';
  const {node, display} = window.CriclyticsDOM;
  const {request} = window.CriclyticsAPI;
  const page = document.body.dataset.page;
  const app = document.getElementById('app');
  const query = new URLSearchParams(location.search);
  const unavailable = 'Predictions unavailable. No chronologically evaluated and calibrated model is released.';
  let uid = 0;
  function link(title, target, values) {
    const item = node('a', title);
    item.href = target + '.html' + (values ? '?' + new URLSearchParams(values) : '');
    return item;
  }
  function panel(title) {
    const item = node('section', null, 'ui-panel');
    if (title) item.append(node('h2', title));
    return item;
  }
  function metrics(values) {
    const list = node('dl', null, 'ui-metrics');
    values.forEach(([label, value]) => { const item = node('div'); item.append(node('dt', label), node('dd', display(value))); list.append(item); });
    return list;
  }
  function table(title, headers, rows) {
    if (!rows.length) return node('p', 'No records available for this selection.', 'ui-state');
    const wrap = node('div', null, 'ui-table-wrap');
    wrap.tabIndex = 0; wrap.setAttribute('role', 'region'); wrap.setAttribute('aria-label', title + ', scrollable table');
    const grid = node('table', null, 'ui-table');
    grid.append(node('caption', title));
    const head = node('thead'), tr = node('tr'), body = node('tbody');
    headers.forEach(label => { const th = node('th', label); th.scope = 'col'; tr.append(th); });
    head.append(tr); grid.append(head);
    rows.forEach(values => { const row = node('tr'); values.forEach(value => {
      const cell = node('td'); cell.append(value instanceof Node ? value : document.createTextNode(display(value))); row.append(cell);
    }); body.append(row); });
    grid.append(body); wrap.append(grid); return wrap;
  }
  function field(label, values, value) {
    const id = 'ui-field-' + (++uid), wrap = node('div', null, 'ui-field');
    const name = node('label', label); name.htmlFor = id;
    const input = node(values ? 'select' : 'input'); input.id = id;
    if (values) values.forEach(([key, title]) => { const option = node('option', title); option.value = key; input.append(option); });
    else { input.type = 'search'; input.maxLength = 200; }
    if (value !== undefined && value !== null) input.value = value;
    wrap.append(name, input); return {wrap, input};
  }
  function formats(value, all) { return field('Format', (all ? [['', 'All formats']] : []).concat([['T20I', 'T20I'], ['ODI', 'ODI'], ['Test', 'Test']]), value); }
  function button(label, action) { const item = node('button', label); item.type = 'button'; item.addEventListener('click', action); return item; }
  function provenance(info, title) {
    if (!info) return node('p', 'Observation time and source freshness are unavailable.', 'ui-notice');
    return node('p', (title || 'Snapshot') + ': ' + (info.source || 'unknown source') +
      ' · Effective ' + (info.effective_date || 'unknown') + ' · Fetched ' + (info.fetched_at || 'unknown') +
      (info.fallback ? ' · Fallback' : '') + (info.stale ? ' · Stale or observation time unknown' : ''), 'ui-notice');
  }
  function prediction(target) { target.append(node('p', unavailable, 'ui-prediction')); }
  function state(target, kind, retry) {
    target.replaceChildren();
    const message = kind === 'loading' ? 'Loading records…' : kind === 'not-found' ? 'This record was not found. Choose another entity from search.' :
      kind === 'empty' ? 'No records match this selection.' : 'Records are unavailable. Please try again.';
    const item = node('p', message, 'ui-state' + (kind === 'error' ? ' ui-error' : ''));
    item.setAttribute('role', kind === 'error' ? 'alert' : 'status');
    target.append(item); target.setAttribute('aria-busy', String(kind === 'loading'));
    if (retry) target.append(button('Try again', retry));
  }
  function filters(fields, render) {
    const form = node('form', null, 'ui-filters'), results = node('div');
    fields.forEach(item => form.append(item.wrap));
    const submit = node('button', 'Apply filters'); submit.type = 'submit'; form.append(submit);
    app.replaceChildren(form, results);
    let generation = 0;
    async function run() {
      const current = ++generation;
      state(results, 'loading');
      try {
        const content = await render();
        if (current !== generation) return;
        results.replaceChildren(content); results.setAttribute('aria-busy', 'false');
      } catch (error) { if (current === generation) state(results, error.kind || 'error', run); }
    }
    form.addEventListener('submit', event => { event.preventDefault(); run(); });
    run(); return {run, results, form};
  }
  function pager(total, offset, limit, change) {
    const area = node('nav', null, 'ui-pager'); area.setAttribute('aria-label', 'Result pages');
    const before = button('Previous page', () => change(offset - limit)); before.disabled = offset === 0;
    const after = button('Next page', () => change(offset + limit)); after.disabled = offset + limit >= total;
    area.append(before, node('span', total ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total}` : '0 results'), after); return area;
  }
  function avatar(name) {
    const item = node('div', name.split(/\s+/).filter(Boolean).slice(0, 2).map(s => s[0]).join('').toUpperCase(), 'ui-avatar');
    item.id = 'teamCrest'; item.setAttribute('aria-label', name);
    const initials = item.textContent, url = ({India:'IN',Pakistan:'PK',Australia:'AU',England:'ENGLAND','South Africa':'ZA','New Zealand':'NZ','Sri Lanka':'LK',Bangladesh:'BD',Afghanistan:'AF'})[name];
    if (url) {
      const image = node('img'); image.src = 'https://cdn.jsdelivr.net/npm/country-flag-emoji-json@2.0.0/dist/images/' + url + '.svg'; image.alt = name;
      image.addEventListener('error', () => { item.textContent = initials; });
      item.replaceChildren(image);
    }
    return item;
  }
  function fixtureCards(matches) {
    const grid = node('div', null, 'ui-grid');
    if (!matches.length) return node('p', 'No cached fixtures or results match this selection.', 'ui-state');
    matches.forEach(match => {
      const card = node('article', null, 'ui-card');
      const names = match.teams || [match.t1, match.t2];
      const title = match.name || names.filter(Boolean).join(' vs ');
      const heading = node('h3'); heading.append(link(title || 'Match details', match.matchEnded ? 'match-detail' : 'match-upcoming', {id: match.id || match.unique_id}));
      card.append(heading, node('p', [match.matchType, match.date, match.venue].filter(Boolean).join(' · ')),
        node('p', match.matchEnded ? (match.status || 'Completed') : 'Cached · ' + (match.status || 'Live status unverified')));
      if (match.t1s || match.t2s) card.append(node('p', [match.t1s, match.t2s].filter(Boolean).join(' / ')));
      grid.append(card);
    }); return grid;
  }
  async function home() {
    const [recent, upcoming] = await Promise.all([request('/api/matches?status=completed&limit=4'), request('/api/matches?status=upcoming&sort=oldest&limit=4')]);
    const content = node('div'), hero = panel('Prepare with records. Review with context.');
    hero.append(node('p', 'Explore players, matchups, venues and results from the available historical matches. Missing data stays unavailable.'), link('Browse matches', 'matches'));
    prediction(hero); content.append(hero, provenance(upcoming.provenance, 'Fixtures'), node('h2', 'Recent results'), fixtureCards(recent.data || []), node('h2', 'Cached upcoming fixtures'), fixtureCards(upcoming.data || []));
    app.replaceChildren(content);
  }
  function matches() {
    const status = field('Match status', [['completed', 'Completed'], ['upcoming', 'Upcoming'], ['live', 'Cached in progress'], ['all', 'All']], query.get('status') || 'completed');
    const fmt = formats('', true), team = field('Team name', null, ''), sort = field('Order', [['newest', 'Newest first'], ['oldest', 'Oldest first']], 'newest');
    let offset = 0, active = '';
    const surface = filters([status, fmt, team, sort], async () => {
      const signature = [status.input.value, fmt.input.value, team.input.value, sort.input.value].join('|');
      if (signature !== active) { offset = 0; active = signature; }
      const params = new URLSearchParams({status: status.input.value, sort: sort.input.value, limit: 20, offset});
      if (fmt.input.value) params.set('format', fmt.input.value);
      if (team.input.value.trim()) params.set('team', team.input.value.trim());
      const data = await request('/api/matches?' + params), content = node('div');
      content.append(provenance(data.provenance, 'Fixtures'), fixtureCards(data.data || []),
        pager(data.pagination.total, offset, 20, next => { offset = next; surface.run(); }));
      return content;
    });
  }
  function players() {
    const search = field('Player name', null, query.get('search') || ''), fmt = formats('', true), country = field('Team or country', null, '');
    const role = field('Player role', [['all', 'All observed roles'], ['bat', 'Batting records'], ['bowl', 'Bowling records']], 'all');
    const sort = field('Sort players by', [['runs', 'Runs'], ['wickets', 'Wickets'], ['avg', 'Batting average'], ['sr', 'Strike rate']], 'runs');
    let offset = 0, active = '';
    const surface = filters([search, fmt, country, role, sort], async () => {
      const signature = [search.input.value, fmt.input.value, country.input.value, role.input.value, sort.input.value].join('|');
      if (signature !== active) { offset = 0; active = signature; }
      const params = new URLSearchParams({search: search.input.value, country: country.input.value, role: role.input.value, sort: sort.input.value, limit: 20, offset});
      if (fmt.input.value) params.set('format', fmt.input.value);
      const data = await request('/api/players?' + params), content = node('div');
      if (data.identity_correct) content.append(node('p', 'Teams are observed memberships, not nationality. Statistics cover available matches only.', 'ui-notice'));
      content.append(table('Players in available matches', ['Player', data.identity_correct ? 'Observed teams' : 'Country', 'Formats'], (data.players || []).map(p => [link(p.name, 'player-profile', {name: p.identity_id || p.name}), p.observed_teams ? p.observed_teams.map(t => t.team_name).join(', ') : p.country, (p.formats || []).join(', ')])),
        pager(data.total, offset, 20, next => { offset = next; surface.run(); })); return content;
    });
  }
  function entities(kind) {
    const search = field(kind === 'teams' ? 'Team name' : 'Venue name', null, ''), fmt = formats('', true);
    filters([search, fmt], async () => {
      const data = await request('/api/' + kind), rows = Object.entries(data).filter(([name, stats]) =>
        name.toLowerCase().includes(search.input.value.trim().toLowerCase()) && (!fmt.input.value ||
          (kind === 'teams' ? !!stats[fmt.input.value] : (stats.formats || []).includes(fmt.input.value))));
      return table(kind === 'teams' ? 'Teams' : 'Venues', ['Name', 'Available formats'], rows.map(([name, stats]) =>
        [link(name, kind === 'teams' ? 'team-profile' : 'venue-profile', {name}), (kind === 'teams' ? Object.keys(stats) : stats.formats || []).join(', ')]));
    });
  }
  function tabs(target, choices, render) {
    const bar = node('div', null, 'ui-tabs'), content = node('div');
    bar.setAttribute('role', 'tablist'); bar.setAttribute('aria-label', 'Record view');
    const id = 'ui-panel-' + (++uid); content.id = id; content.setAttribute('role', 'tabpanel'); content.tabIndex = 0;
    choices.forEach(([value, label], index) => {
      const tab = button(label, () => select(index)); tab.id = id + '-tab-' + index; tab.setAttribute('role', 'tab'); tab.setAttribute('aria-controls', id); tab.dataset.value = value; bar.append(tab);
    });
    function select(index) {
      [...bar.children].forEach((tab, i) => { tab.setAttribute('aria-selected', String(i === index)); tab.tabIndex = i === index ? 0 : -1; });
      content.setAttribute('aria-labelledby', bar.children[index].id); content.replaceChildren(); render(content, choices[index][0]);
    }
    bar.addEventListener('keydown', event => {
      const current = [...bar.children].indexOf(document.activeElement); if (current < 0) return;
      let index = current;
      if (event.key === 'ArrowRight') index = (current + 1) % choices.length;
      else if (event.key === 'ArrowLeft') index = (current + choices.length - 1) % choices.length;
      else if (event.key === 'Home') index = 0;
      else if (event.key === 'End') index = choices.length - 1;
      else return;
      event.preventDefault(); select(index); bar.children[index].focus();
    }); target.append(bar, content); select(0);
  }
  function batting(target, stats, title) {
    target.append(metrics([['Matches', stats.matches], ['Innings', stats.innings], ['Runs', stats.runs], ['Average', stats.average], ['Strike rate', stats.strike_rate], ['Highest innings', stats.highest], ['Fifties', stats.fifties], ['Hundreds', stats.hundreds], ['Not outs', stats.not_outs]]));
    target.append(node('p', title || 'Descriptive statistics from observed matches.', 'ui-notice'));
  }
  async function profile(kind) {
    const name = query.get('name');
    if (!name) { app.replaceChildren(node('p', 'Select a ' + kind + ' to view its records.', 'ui-state'), link('Find records', 'search')); return; }
    const route = kind === 'player' ? 'players' : kind === 'team' ? 'teams' : 'venues';
    let data;
    try { data = await request('/api/' + route + '/' + encodeURIComponent(name)); }
    catch (error) {
      if (kind === 'player' && error.status === 409) {
        app.replaceChildren(node('p', 'This name matches more than one player. Choose a player from the directory.', 'ui-state'), link('Choose player', 'players', {search:name})); return;
      }
      throw error;
    }
    document.querySelector('h1').textContent = data.name || data.venue || name;
    const content = node('div');
    if (kind === 'team') content.append(avatar(name));
    if (kind === 'player') {
      content.append(link('Prepare scouting plan', 'scouting', {player:data.identity_id || data.name}));
      content.append(node('p', data.observed_teams ? 'Observed teams: ' + data.observed_teams.map(t => t.team_name + ' (' + t.first_date + ' to ' + t.last_date + ')').join('; ') + '. Nationality is not inferred.' : data.country || 'Country unavailable'));
      const available = ['T20I', 'ODI', 'Test'].filter(fmt => (data.batting || {})[fmt] || (data.bowling || {})[fmt]);
      tabs(content, available.concat(['T20I', 'ODI', 'Test'].filter(fmt => !available.includes(fmt))).map(fmt => [fmt, fmt]), (target, fmt) => {
        if (data.batting && data.batting[fmt]) { target.append(node('h2', 'Batting')); batting(target, data.batting[fmt]); }
        if (data.bowling && data.bowling[fmt]) { const s = data.bowling[fmt]; target.append(node('h2', 'Bowling'), metrics([['Innings', s.innings], ['Wickets', s.wickets], ['Conceded runs', s.runs], ['Legal balls', s.balls], ['Economy', s.economy], ['Average', s.average], ['Maidens', s.maidens]])); }
        if (!target.childNodes.length) state(target, 'empty');
        target.append(table('Observed yearly batting', ['Year', 'Matches', 'Innings', 'Runs', 'Average'], Object.entries((data.yearly || {})[fmt] || {}).sort().map(([year,s]) => [year,s.matches,s.innings,s.runs,s.average])),
          table('Batting by opposition', ['Opponent', 'Innings', 'Runs', 'Average'], Object.entries((data.vs_opp || {})[fmt] || {}).map(([name,s]) => [link(name,'team-profile',{name}),s.innings,s.runs,s.average])),
          table('Batting by venue', ['Venue', 'Innings', 'Runs', 'Average'], Object.entries((data.at_venues || {})[fmt] || {}).map(([name,s]) => [link(name,'venue-profile',{name}),s.innings,s.runs,s.average])));
      });
      content.append(table('Recent observed innings (chronological)', ['Innings score'], (data.recent_form || []).map(score => [score])));
    } else if (kind === 'team') {
      tabs(content, ['T20I', 'ODI', 'Test'].map(fmt => [fmt, fmt]), (target, fmt) => {
        const s = (data.format_stats || {})[fmt]; if (!s) { state(target, 'empty'); return; }
        target.append(metrics([['Matches', s.matches], ['Won', s.won], ['Lost', s.lost], ['Drawn', s.drawn], ['Tied', s.tied], ['No result', s.no_result], ['Win %', s.win_pct]]));
        target.append(table('Head to head in available matches', ['Opponent', 'Matches', 'Won', 'Lost', 'Drawn', 'Tied', 'No result'], Object.entries(data.head_to_head || {}).filter(([,v]) => v[fmt]).map(([opponent, v]) =>
          [link(opponent, 'team-profile', {name: opponent}), v[fmt].matches, v[fmt].won, v[fmt].lost, v[fmt].drawn, v[fmt].tied, v[fmt].no_result])));
        target.append(table('Team venue records', ['Venue','Matches','Won','Lost','Average innings'], Object.entries((data.venue_stats || {})[fmt] || {}).map(([name,s]) => [link(name,'venue-profile',{name}),s.matches,s.won,s.lost,s.avg_score])));
      });
    } else {
      content.append(metrics([['Observed matches', data.matches]]));
      tabs(content, [['t20i', 'T20I'], ['odi', 'ODI'], ['test', 'Test']], (target, fmt) => {
        const s = data[fmt]; if (!s) { state(target, 'empty'); return; }
        target.append(metrics([['First innings average', s.avg_1st_innings], ['Second innings average', s.avg_2nd_innings], ['Highest', s.highest], ['Lowest', s.lowest], ['Chase win %', s.chase_win_pct], ['Chase samples', s.chase_samples]]));
      });
      content.append(node('p', data.player_leaderboard_scope || 'Venue leaderboards combine observed formats.'));
      content.append(table('Observed top batters at this venue', ['Player', 'Runs', 'Matches'], (data.top_batters || []).map(p => [link(p.player, 'player-profile', {name: p.identity_id || p.player}), p.runs, p.matches])));
      content.append(table('Observed top bowlers at this venue', ['Player','Wickets','Matches'], (data.top_bowlers || []).map(p => [link(p.player,'player-profile',{name:p.identity_id || p.player}),p.wickets,p.matches])));
    }
    prediction(content); app.replaceChildren(content);
  }
  async function detail() {
    const id = query.get('id');
    if (!id) { app.replaceChildren(node('p', 'Select a match to view its details.', 'ui-state'), link('Browse matches', 'matches')); return; }
    const payload = await request('/api/matches/' + encodeURIComponent(id));
    const match = payload.data || payload;
    if (!match || Array.isArray(match)) throw new Error('Invalid match');
    const content = node('div'); document.querySelector('h1').textContent = match.name || (match.teams || []).join(' vs ');
    content.append(node('p', [match.matchType, match.date, match.venue].filter(Boolean).join(' · ')), node('p', match.status || 'Status unavailable', 'ui-notice'));
    if (!match.matchEnded) content.append(node('p', 'Cached match information. Current live freshness has not been verified.', 'ui-notice'));
    content.append(table('Innings totals', ['Team', 'Runs', 'Wickets', 'Overs'], (match.score || []).map(s => [s.inning || s.team, s.r, s.w, s.o])));
    const innings = match.innings || [];
    if (innings.length) tabs(content, innings.map((inn, index) => [index, `${inn.team || 'Innings'} · ${index + 1}${inn.super_over ? ' (Super over)' : ''}`]), (target, index) => {
      const inn = innings[index];
      target.append(table('Batting scorecard', ['Batter', 'Dismissal', 'Runs', 'Balls', '4s', '6s'], (inn.batting || []).map(r => [link(r.batsman, 'player-profile', {name: r.batsman}), r.dismissal, r.r, r.b, r['4s'], r['6s']])),
        table('Bowling scorecard', ['Bowler', 'Overs', 'Maidens', 'Runs', 'Wickets'], (inn.bowling || []).map(r => [link(r.bowler, 'player-profile', {name: r.bowler}), r.o, r.m, r.r, r.w])));
      if ((inn.fall_of_wickets || []).length) { const list = node('ul'); inn.fall_of_wickets.forEach(value => list.append(node('li',value))); target.append(node('h2','Fall of wickets'),list); }
    });
    prediction(content); app.replaceChildren(content);
  }
  function rankings() {
    const fmt = formats('T20I'), category = field('Ranking category', [['teams', 'Teams'], ['batting', 'Batting'], ['bowling', 'Bowling'], ['allrounder', 'All-rounders']], 'teams');
    filters([fmt, category], async () => {
      const data = await request('/api/icc-rankings?' + new URLSearchParams({category: category.input.value, format: fmt.input.value})), content = node('div');
      content.append(provenance(data.provenance, 'Ranking snapshot'), table('Ranking snapshot', ['Rank', 'Name', 'Country', 'Rating'], (data.rankings || []).map(r => [r.rank, link(r.team || r.player || r.name, category.input.value === 'teams' ? 'team-profile' : 'player-profile', {name: r.team || r.player || r.name}), r.country, r.rating]))); return content;
    });
  }
  function records() {
    const fmt = formats('T20I'), category = field('Record', [['most_runs', 'Most runs'], ['most_wickets', 'Most wickets'], ['best_averages', 'Best batting averages'], ['most_hundreds', 'Most hundreds']], 'most_runs');
    filters([fmt, category], async () => {
      const data = await request('/api/records'), rows = (data[category.input.value] || {})[fmt.input.value] || [];
      return table('Records from available matches', ['Player', 'Runs', 'Wickets', 'Average', 'Hundreds'], rows.map(r => [link(r.player, 'player-profile', {name: r.identity_id || r.player}), r.runs, r.wickets, r.average, r.hundreds]));
    });
  }
  function search() {
    const term = field('Search players, teams, venues or matches', null, query.get('q') || '');
    filters([term], async () => {
      const content = node('div');
      if (!term.input.value.trim()) { content.append(node('p', 'Enter a name, venue or match to search.', 'ui-state')); return content; }
      const data = await request('/api/search?' + new URLSearchParams({q: term.input.value.trim(), limit:20}));
      for (const [key, target] of [['players', 'player-profile'], ['teams', 'team-profile'], ['venues', 'venue-profile']]) {
        content.append(table(key[0].toUpperCase() + key.slice(1), ['Name'], (data[key] || []).map(r => [link(r.name, target, {name:r.identity_id || r.name})])));
      }
      content.append(node('h2', 'Matching fixtures and results'), fixtureCards(data.matches || [])); return content;
    });
  }
  function compare() {
    const kind = field('Compare', [['players', 'Players'], ['teams', 'Teams']], 'players');
    const a = field('First recorded name', null, query.get('a') || ''), b = field('Second recorded name', null, query.get('b') || ''), fmt = formats('T20I');
    filters([kind, a, b, fmt], async () => {
      const content = node('div');
      if (!a.input.value.trim() || !b.input.value.trim()) { content.append(node('p', 'Choose two names. Use search to find their recorded names.', 'ui-state'), link('Find records', 'search')); return content; }
      if (kind.input.value === 'teams') {
        const [first, second] = await Promise.all([request('/api/teams/' + encodeURIComponent(a.input.value.trim())), request('/api/teams/' + encodeURIComponent(b.input.value.trim()))]);
        const s1 = (first.format_stats || {})[fmt.input.value], s2 = (second.format_stats || {})[fmt.input.value];
        if (!s1 || !s2) { state(content, 'empty'); return content; }
        content.append(table('Team records · ' + fmt.input.value, ['Metric', first.name, second.name],
          [['Matches','matches'],['Won','won'],['Lost','lost'],['Drawn','drawn'],['Tied','tied'],['No result','no_result'],['Win %','win_pct']].map(([label,key]) => [label, s1[key], s2[key]])));
        prediction(content); return content;
      }
      const data = await request('/api/compare/players?' + new URLSearchParams({player_a:a.input.value.trim(), player_b:b.input.value.trim()}));
      const first = (data.player_a.batting || {})[fmt.input.value], second = (data.player_b.batting || {})[fmt.input.value];
      if (!first || !second) { state(content, 'empty'); return content; }
      content.append(table('Descriptive batting comparison · ' + fmt.input.value, ['Metric', data.player_a.name, data.player_b.name], [['Matches','matches'],['Innings','innings'],['Runs','runs'],['Average','average'],['Strike rate','strike_rate'],['Highest innings','highest'],['Hundreds','hundreds']].map(([name,key]) => [name, first[key], second[key]])),
        node('p', 'Sample size and match context affect comparisons. No performance verdict is inferred.', 'ui-notice'));
      prediction(content); return content;
    });
  }
  function information() {
    const content = panel(page === 'about' ? 'Built for match preparation and review' : page === 'data-sources' ? 'Traceable sources, clear limits' : 'What these records mean');
    if (page === 'about') content.append(node('p', 'Criclytics brings historical player, team, venue and match records into one place. The current dataset is a subset of men’s internationals, with coverage gaps and statistical revisions still under review.'));
    else if (page === 'data-sources') {
      content.append(node('p', 'Historical delivery data is provided by Cricsheet under the Open Data Commons Attribution License 1.0. Aggregates are derived from that dataset and may change as scoring contracts are corrected.'));
      const source = node('a', 'Cricsheet data and licensing'); source.href = 'https://cricsheet.org/licensing/'; content.append(source);
      content.append(node('p', 'Fixture and ranking snapshots may be cached or historical fallbacks. Their source and observation dates are displayed where available. Unknown timestamps do not imply fresh data.'));
    } else content.append(node('p', 'Historical counts describe observed matches, not complete careers or guarantees about future performance. Missing values are displayed as unavailable. A snapshot of an in-progress match is not a verified real-time feed.'));
    prediction(content); app.replaceChildren(content);
  }
  function workspace() {
    const identifier = field('Workspace identifier', null, query.get('id') || '');
    let expiry;
    const reasons = values => (values || []).map(value => String(value).replaceAll('_', ' ')).join('; ');
    function jointLabel(label) {
      if (label === 'OTHER') return 'Other / unknown joint outcome';
      try {
        const value = JSON.parse(label), extras = Object.entries(value.extras).filter(([,n]) => n).map(([key,n]) => n + ' ' + key).join(', ');
        return 'Batter ' + value.batter_runs + (extras ? '; extras ' + extras : '; no extras') + '; ' + (value.dismissals.length ? value.dismissals.join(', ') : 'no dismissal') + '; ' + (value.legal ? 'legal' : 'illegal') + ' attempt';
      } catch (_) { return 'Unrecognized outcome'; }
    }
    function issuedPanel(record) {
      const detail = node('details'), content = record.content || {};
      detail.id = 'forecast-' + record.forecast_id;
      detail.append(node('summary', 'Issued ' + record.issued_at + ' · ' + record.forecast_id.slice(0,12)),
        node('p', 'Target attempt: ' + content.target_event_id), node('p', 'Source cutoff: ' + content.source_cutoff),
        node('p', 'Model: ' + content.model_id), node('p', 'Dataset: ' + content.dataset_id),
        node('p', 'Feature hash: ' + content.feature_hash), node('p', 'State: ' + content.state_id));
      if (record.replaces_forecast_id) detail.append(node('p', 'Replaces issued forecast ' + record.replaces_forecast_id));
      detail.append(table('Issued joint next-attempt distribution', ['Joint outcome', 'Probability'], Object.entries(content.distribution || {}).sort((a,b) => b[1]-a[1]).map(([label,p]) => [jointLabel(label), (p*100).toFixed(2) + '%'])),
        node('p', 'OTHER has unknown runs and dismissals. No exact wicket or runs marginal is claimed.'));
      return detail;
    }
    const surface = filters([identifier], async () => {
      clearTimeout(expiry);
      const content = node('div');
      content.append(node('p', 'Experimental shadow workspace. No validated current coaching prediction is released.', 'ui-prediction'),
        node('p', 'Manual refresh only. A source confirmation can expire before the actual ball is observed.'));
      const id = identifier.input.value.trim();
      if (!id) { content.append(node('p', 'Enter an existing local manual or replay workspace identifier. No public live feed is enabled.', 'ui-state')); return content; }
      const path = '/api/v1/workspaces/' + encodeURIComponent(id);
      const data = await request(path + '/forecast');
      const receivedAt = performance.now();
      let records = [], historyUnavailable = false;
      if (data.core) {
        try { const history = await request(path + '/history?limit=20'); records = history.forecasts || []; }
        catch (_) { historyUnavailable = true; }
      }
      const status = node('p', (data.mode === 'manual' ? 'Manual scoring' : data.mode === 'replay' ? 'Historical replay' : 'Source unavailable') +
        (data.forecast_allowed ? ' · confirmed source snapshot' : ' · forecast unavailable: ' + reasons(data.blocked_reasons)), 'ui-notice');
      status.setAttribute('role', 'status'); status.setAttribute('aria-live', 'polite'); content.append(status);
      const core = data.core;
      if (core) {
        const score = core.innings.find(inn => inn.innings === core.active_innings);
        content.append(metrics([['Runs',score.runs],['Wickets',score.wickets],['Legal balls',score.legal_balls],['Source age at refresh (seconds)',data.source_age_seconds],['Event lag (seconds)',data.event_lag_seconds]]),
          node('p', 'Source cutoff: ' + core.source_cutoff + ' · status: ' + core.source_status),
          node('p', 'Source revision: ' + core.source_revision_counter + ' · state: ' + data.state_id));
        if (core.next_context) content.append(table('Announced next-attempt participants', ['Striker','Non-striker','Bowler'], [[core.next_context.striker,core.next_context.non_striker,core.next_context.bowler]]));
        content.append(node('p', 'History: ' + core.history_scope),
          table('Context coverage in model', ['Context', 'Availability'], Object.entries(core.context_coverage).map(([key,value]) => [key.replaceAll('_',' '),value.replaceAll('_',' ')])));
      }
      if (data.model) {
        content.append(node('p', data.model.limitations), node('p', 'Model ' + data.model.model_id + ' · calibration through ' + data.model.calibration_last_date));
        const samples = (data.model.training_coverage || {}).matches;
        if (samples) content.append(table('Historical model sample', ['Partition','Matches'], Object.entries(samples)));
      }
      const current = panel('Current shadow forecast');
      if (data.forecast && data.forecast_allowed) {
        const record = data.forecast;
        const anchor = node('a', 'View issued forecast ' + record.forecast_id.slice(0,12)); anchor.href = '#forecast-' + encodeURIComponent(record.forecast_id);
        current.append(anchor, node('p', 'Unknown joint-outcome mass: ' + (record.content.unknown_mass*100).toFixed(2) + '%'));
        if (!records.some(r => r.forecast_id === record.forecast_id)) records.unshift(record);
        const remaining = Math.max(0, Number(data.eligibility_valid_for_seconds || 0) - (performance.now()-receivedAt)/1000);
        expiry = setTimeout(() => {
          current.replaceChildren(node('h2','Current shadow forecast'), node('p', 'Confirmation expired. Refresh to recheck the source; past entries remain in issued history.', 'ui-state'));
          status.textContent = 'Confirmation expired · current forecast unavailable';
        }, remaining*1000);
      } else current.append(node('p', 'No current forecast: ' + reasons(data.blocked_reasons), 'ui-state'));
      content.append(current, node('h2', 'Issued history · past entries are not current forecasts'));
      if (historyUnavailable) content.append(node('p', 'Full history is unavailable. The returned issued entry is retained below.', 'ui-error'));
      records.forEach(record => content.append(issuedPanel(record)));
      if (!records.length) content.append(node('p', 'No issued entries available.', 'ui-state'));
      return content;
    });
    surface.form.querySelector('button[type=submit]').textContent = 'Refresh workspace';
  }
  async function loadCoverage() {
    try {
      const data = await request('/api/coverage');
      if (!data.available) return;
      const target = document.querySelector('.ui-coverage');
      target.textContent = 'Name-keyed historical aggregates remain under review; ambiguous identities are unavailable. ' + data.scope + '. Matches: ' + data.accepted_matches +
        '. Coverage: ' + data.first_match_date + ' to ' + data.last_match_date +
        '. Cutoff is the latest match date, not proof of historical publication time. Derived from Cricsheet (ODC-BY-1.0).';
    } catch (_) { /* Keep the existing honest unknown-coverage notice. */ }
  }
  async function init() {
    const navigation = document.querySelector('.ui-navigation');
    if (matchMedia('(min-width:1100px)').matches) navigation.open = true;
    document.querySelectorAll('.ui-navigation a').forEach(item => { if (item.getAttribute('href') === page + '.html') item.setAttribute('aria-current', 'page'); });
    const handlers = {index:home, matches, players, teams:() => entities('teams'), venues:() => entities('venues'),
      'player-profile':() => profile('player'), 'team-profile':() => profile('team'), 'venue-profile':() => profile('venue'),
      'match-detail':detail, 'match-upcoming':detail, rankings, records, search, compare, workspace,
      scouting:() => window.CriclyticsCoach.init({app,query,node,field,formats,table,metrics,panel,button,request,state,link}),
      about:information, 'data-sources':information, disclaimer:information};
    try { await handlers[page](); } catch (error) { state(app, error.kind || 'error', init); }
    app.setAttribute('aria-busy', 'false');
  }
  loadCoverage();
  init();
}());
