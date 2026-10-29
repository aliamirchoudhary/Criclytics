/* Data-driven application UI. Provider strings are rendered as text, never HTML. */
(function () {
  'use strict';
  if (document.documentElement.dataset.criclyticsInitialized) return;
  document.documentElement.dataset.criclyticsInitialized = 'true';
  const {node, display} = window.CriclyticsDOM;
  const {request} = window.CriclyticsAPI;
  const media = window.CriclyticsMedia;
  const ux = window.CriclyticsExperience;
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
  function recordDetails(title,headers,rows) {
    const details=node('details',null,'ui-record-details'), summary=node('summary');
    summary.append(node('span',title),node('span',rows.length+' records','ui-record-count'));
    details.append(summary,table(title,headers,rows)); return details;
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
    form.addEventListener('change',event=>{if(event.target.dataset.autosubmit)run();});
    run(); return {run, results, form};
  }
  function pager(total, offset, limit, change) {
    const area = node('nav', null, 'ui-pager'); area.setAttribute('aria-label', 'Result pages');
    const before = button('Previous page', () => change(offset - limit)); before.disabled = offset === 0;
    const after = button('Next page', () => change(offset + limit)); after.disabled = offset + limit >= total;
    area.append(before, node('span', total ? `${offset + 1}–${Math.min(offset + limit, total)} of ${total}` : '0 results'), after); return area;
  }
  function avatar(name) {
    const item = media.flag(name); item.id = 'teamCrest'; item.classList.add('ui-team-crest');
    return item;
  }
  function teamLink(name) {
    const item = link('', 'team-profile', {name}); item.className = 'ui-team-link';
    item.append(media.flag(name), node('span', name)); return item;
  }
  function playerLink(player) {
    const item = link('', 'player-profile', {name:player.identity_id || player.name}); item.className = 'ui-player-link';
    const photo=media.portraits[player.identity_id];
    const label = node('span',photo ? photo.name : player.name); label.append(node('small',(player.formats || []).join(' / ')));
    item.append(media.portrait(player),label); return item;
  }
  function comparisonHeader(first,second,teams) {
    const grid=node('div',null,'ui-grid ui-comparison-header');
    [first,second].forEach(value=>{
      const card=node('article',null,'ui-card');
      card.append(teams ? teamLink(value.name) : playerLink(value));
      if(!teams) { const credit=media.credit(value.identity_id); if(credit) card.append(credit); }
      grid.append(card);
    }); return grid;
  }
  function fixtureCards(matches) {
    const grid = node('div', null, 'ui-grid');
    if (!matches.length) return node('p', 'No cached fixtures or results match this selection.', 'ui-state');
    matches.forEach(match => {
      const card = node('article', null, 'ui-card ui-match-card');
      const names = match.teams || [match.t1, match.t2];
      const title = match.name || names.filter(Boolean).join(' vs ');
      const heading = node('h3'); heading.append(link(title || 'Match details', match.matchEnded ? 'match-detail' : 'match-upcoming', {id: match.id || match.unique_id}));
      const meta = node('div',null,'ui-match-meta'); meta.append(node('span',match.matchType || 'International','ui-badge'),node('span',match.date ? String(match.date).slice(0,10) : 'Date unavailable'));
      card.append(meta,heading);
      names.filter(Boolean).slice(0,2).forEach((name,index) => {
        const row = node('div',null,'ui-match-team');
        const score = (match.score || []).find(s => (s.inning || s.team || '').startsWith(name));
        const value = index === 0 ? match.t1s : match.t2s;
        row.append(teamLink(name),node('strong',value || (score ? `${score.r}/${score.w} (${score.o})` : '—'))); card.append(row);
      });
      card.append(node('p',match.venue || 'Venue unavailable','ui-match-venue'),node('p',match.matchEnded ? (match.status || 'Completed') : 'Cached · '+(match.status || 'Live status unverified'),'ui-match-result'));
      grid.append(card);
    }); return grid;
  }
  async function scoreSnapshots(target){
    state(target,'loading');
    try{
      const data=await request('/api/matches?status=live&limit=2'), items=data.data||[], header=node('div',null,'ui-section-heading');
      header.append(node('h2','Match score centre'),link('All matches →','matches',{status:'live'}));
      const refresh=button('Refresh scores',()=>scoreSnapshots(target));refresh.className='ui-secondary';
      const source=data.provenance||{}, date=source.fetched_at || source.observed_at;
      const freshness=node('p',date?'Source updated: '+date+' · cached score snapshot, not a guaranteed real-time feed.':'Source freshness unavailable. Stored scores are not labelled live.','ui-score-freshness');
      target.replaceChildren(header,freshness,items.length?fixtureCards(items):node('p','No active score snapshot is available. Browse completed matches or open a local replay in the prediction centre.','ui-state'),refresh);
    }catch(error){state(target,error.kind||'error',()=>scoreSnapshots(target));}
    finally{target.setAttribute('aria-busy','false');}
  }
  async function home(){
    const content=node('div'),hero=node('section',null,'ui-hero'),copy=node('div',null,'ui-hero-copy');
    const heading=document.querySelector('.ui-main h1'),eyebrow=document.querySelector('.ui-main>.ui-eyebrow'),coverage=document.querySelector('.ui-coverage');
    if(eyebrow)copy.append(eyebrow);if(heading)copy.append(heading);
    copy.append(node('p','Cricket intelligence for the next delivery. Explore player matchups, understand the ground and inspect the evidence behind every probability.'));
    const actions=node('div',null,'ui-hero-actions'),primary=link('Open prediction centre →','workspace');primary.className='ui-action-primary';actions.append(primary,link('Explore players','players'));copy.append(actions);
    if(coverage)copy.append(coverage);
    const desk=node('aside',null,'ui-intelligence-desk');desk.append(node('p','NEXT-DELIVERY INTELLIGENCE','ui-eyebrow'),node('h2','Every ball has a context.'));
    [['01','Confirm the match','Score, striker, bowler and source freshness.'],['02','Inspect probabilities','Coherent outcomes from the experimental CPU model.'],['03','Review the evidence','Context coverage, held-out results and issued history.']].forEach(([number,title,description])=>{const row=node('div');row.append(node('span',number),node('strong',title),node('p',description));desk.append(row);});
    desk.append(node('p','Experimental · historical replay / manual scoring','ui-badge'));hero.append(copy,desk);content.append(hero);
    const quick=node('div',null,'ui-quick-grid');
    [['◉','Match centre','Scores & scorecards','matches'],['♙','Players','Profiles & matchups','players'],['↔','Compare','Choose players or teams','compare'],['◈','Predictions','Probability & ML insights','workspace'],['⌖','Venues','Scoring & chase records','venues'],['≡','Records','Format leaders','records'],['↗','Rankings','Dataset leaderboards','rankings'],['▤','Scouting','Prepare your match plan','scouting']].forEach(([icon,title,description,path])=>{const tile=link('',path);tile.append(node('span',icon),node('strong',title),node('small',description));quick.append(tile);});
    content.append(node('h2','Explore Criclytics'),quick,ux.liveWidget());
    const scores=node('section'),players=node('section'),recent=node('section');content.append(scores,players,recent);app.replaceChildren(content);
    const tasks=[scoreSnapshots(scores),(async()=>{try{const data=await request('/api/players?limit=4'),head=node('div',null,'ui-section-heading'),grid=node('div',null,'ui-player-grid');head.append(node('h2','Players to explore'),link('All players →','players'));(data.players||[]).forEach(player=>grid.append(ux.playerCard(player,'')));players.replaceChildren(head,grid);}catch(_){players.replaceChildren(node('p','Player discovery is temporarily unavailable.','ui-state'));}})(),(async()=>{try{const data=await request('/api/matches?status=completed&limit=4'),head=node('div',null,'ui-section-heading');head.append(node('h2','Recent results'),link('All results →','matches'));recent.replaceChildren(head,fixtureCards(data.data||[]));}catch(error){state(recent,error.kind||'error',home);}})()];await Promise.all(tasks);
  }
  function matches() {
    const status = ux.segments('Match status', [['live', 'Score centre'], ['upcoming', 'Upcoming'], ['completed', 'Results'], ['all', 'All matches']], query.get('status') || 'completed');
    const fmt = ux.formats('', true), team = field('Team name', null, ''), sort = field('Order', [['newest', 'Newest first'], ['oldest', 'Oldest first']], 'newest');
    let offset = 0, active = '';
    const surface = filters([status, fmt, team, sort], async () => {
      const signature = [status.input.value, fmt.input.value, team.input.value, sort.input.value].join('|');
      if (signature !== active) { offset = 0; active = signature; }
      const params = new URLSearchParams({status: status.input.value, sort: sort.input.value, limit: 20, offset});
      if (fmt.input.value) params.set('format', fmt.input.value);
      if (team.input.value.trim()) params.set('team', team.input.value.trim());
      const data = await request('/api/matches?' + params), content = node('div');
      if(status.input.value==='live')content.append(ux.liveWidget());
      content.append(provenance(data.provenance, 'Fixtures'), fixtureCards(data.data || []),
        pager(data.pagination.total, offset, 20, next => { offset = next; surface.run(); }));
      return content;
    });
  }
  function players() {
    const search=field('Player name',null,query.get('search') || ''), fmt=ux.formats('',true), country=field('Observed team',null,'');
    const role=ux.segments('Records',[['all','All players'],['bat','Batting'],['bowl','Bowling']],'all');
    const sort=field('Sort players by',[['runs','Most runs'],['wickets','Most wickets'],['avg','Batting average'],['sr','Strike rate']],'runs');
    const view=ux.segments('View',[['cards','Player cards'],['table','Table']],'cards');
    let offset=0,active='',timer;
    const surface=filters([search,fmt,country,role,sort,view],async()=>{
      const signature=[search.input.value,fmt.input.value,country.input.value,role.input.value,sort.input.value].join('|');
      if(signature!==active){offset=0;active=signature;}
      const params=new URLSearchParams({search:search.input.value.trim(),country:country.input.value.trim(),role:role.input.value,sort:sort.input.value,limit:24,offset});
      if(fmt.input.value)params.set('format',fmt.input.value);
      const data=await request('/api/players?'+params),content=node('div'),heading=node('div',null,'ui-section-heading');
      heading.append(node('h2',data.total.toLocaleString()+' players in the dataset'),node('span','Available-match records','ui-card-scope'));content.append(heading);
      if(view.input.value==='cards'){
        const grid=node('div',null,'ui-player-grid');(data.players||[]).forEach(p=>grid.append(ux.playerCard(p,fmt.input.value)));
        content.append(grid.childNodes.length?grid:node('p','No records available for this selection.','ui-state'));
      }else content.append(table('Players in available matches',['Player','Observed teams','Formats'],(data.players||[]).map(p=>[playerLink(p),ux.teams(p).join(', '),(p.formats||[]).join(', ')])));
      content.append(pager(data.total,offset,24,next=>{offset=next;surface.run();}));return content;
    });
    search.input.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(surface.run,300);});
  }
  function entities(kind) {
    const search = field(kind === 'teams' ? 'Team name' : 'Venue name', null, ''), fmt = formats('', true);
    filters([search, fmt], async () => {
      const data = await request('/api/' + kind), rows = Object.entries(data).filter(([name, stats]) =>
        name.toLowerCase().includes(search.input.value.trim().toLowerCase()) && (!fmt.input.value ||
          (kind === 'teams' ? !!stats[fmt.input.value] : (stats.formats || []).includes(fmt.input.value))));
      return table(kind === 'teams' ? 'Teams' : 'Venues', ['Name', 'Available formats'], rows.map(([name, stats]) =>
        [kind === 'teams' ? teamLink(name) : link(name,'venue-profile',{name}), (kind === 'teams' ? Object.keys(stats) : stats.formats || []).join(', ')]));
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
    if(kind === 'player' && media.portraits[data.identity_id]) document.querySelector('h1').textContent=media.portraits[data.identity_id].name;
    const content = node('div');
    if (kind === 'team') content.append(avatar(name));
    if (kind === 'player') {
      const identity = node('div',null,'ui-profile-identity'), description=node('div');
      const portrait = media.portrait(data,true);
      description.append(node('p','PLAYER PROFILE','ui-eyebrow'),node('h2',data.name));
      const credit=media.credit(data.identity_id); if(credit) description.append(credit);
      else description.append(node('small','Portrait not available for this player.','ui-photo-credit'));
      identity.append(portrait,description); content.append(identity);
      content.append(link('Prepare scouting plan', 'scouting', {player:data.identity_id || data.name}));
      content.append(node('p', data.observed_teams ? 'Observed teams: ' + data.observed_teams.map(t => t.team_name + ' (' + t.first_date + ' to ' + t.last_date + ')').join('; ') + '. Nationality is not inferred.' : data.country || 'Country unavailable'));
      const available=['T20I','ODI','Test'].filter(fmt=>(data.batting||{})[fmt] || (data.bowling||{})[fmt]);
      tabs(content,available.concat(['T20I','ODI','Test'].filter(fmt=>!available.includes(fmt))).map(fmt=>[fmt,fmt]),(target,fmt)=>{
        function stats(area){
          if(data.batting && data.batting[fmt]){area.append(node('h2','Batting'));batting(area,data.batting[fmt]);}
          if(data.bowling && data.bowling[fmt]){const s=data.bowling[fmt];area.append(node('h2','Bowling'),metrics([['Innings',s.innings],['Wickets',s.wickets],['Conceded runs',s.runs],['Legal balls',s.balls],['Economy',s.economy],['Average',s.average]]));}
          if(!area.childNodes.length)state(area,'empty');
        }
        tabs(target,[['overview','Overview'],['career','Career stats'],['opposition','vs Teams'],['venues','At Venues'],['probability','Probability Insights'],['ml','ML Insights']],(area,view)=>{
          if(view==='overview')stats(area);
          if(view==='career'){
            stats(area);area.append(recordDetails('Year-by-year batting',['Year','Matches','Innings','Runs','Average'],Object.entries((data.yearly||{})[fmt]||{}).sort().reverse().map(([year,s])=>[year,s.matches,s.innings,s.runs,s.average])));
          }
          if(view==='opposition')area.append(table('Batting by opposition',['Opponent','Innings','Runs','Average'],Object.entries((data.vs_opp||{})[fmt]||{}).map(([name,s])=>[teamLink(name),s.innings,s.runs,s.average])));
          if(view==='venues')area.append(table('Batting by venue',['Venue','Innings','Runs','Average'],Object.entries((data.at_venues||{})[fmt]||{}).map(([name,s])=>[link(name,'venue-profile',{name}),s.innings,s.runs,s.average])));
          if(view==='probability')area.append(ux.empirical(data,fmt));
          if(view==='ml')ux.research(area);
        });
      });
      const form=panel('Recent observed innings'),scores=node('ol',null,'ui-form-scores');
      (data.recent_form||[]).forEach((score,index)=>{const value=node('li',display(score));value.setAttribute('aria-label','Observed innings '+(index+1)+': '+display(score)+' runs');scores.append(value);});
      form.append(node('p','Across available formats, in chronological order.','ui-form-caption'),scores.childNodes.length?scores:node('p','No recent innings available.','ui-state'));content.append(form);
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
    app.replaceChildren(content);
  }
  async function detail() {
    const id = query.get('id');
    if (!id) { app.replaceChildren(node('p', 'Select a match to view its details.', 'ui-state'), link('Browse matches', 'matches')); return; }
    const payload = await request('/api/matches/' + encodeURIComponent(id));
    const match = payload.data || payload;
    if (!match || Array.isArray(match)) throw new Error('Invalid match');
    const content = node('div'); document.querySelector('h1').textContent = match.name || (match.teams || []).join(' vs ');
    const sides=node('div',null,'ui-match-sides'); (match.teams || []).forEach(name=>sides.append(teamLink(name))); content.append(sides);
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
    const views=node('div');
    tabs(views,[['overview','Overview'],['scorecard','Scorecard'],['probability','Probability Insights'],['ml','ML Insights']],(area,view)=>{
      if(view==='overview')area.append(fixtureCards([match]),node('p','Open the scorecard for innings and player figures.','ui-notice'));
      if(view==='scorecard')area.append(content);
      if(view==='probability'){area.append(node('h2','Next-delivery probabilities'),node('p','Forecasts require a fresh confirmed scoring session. A historical scorecard alone is not a live prediction input.','ui-notice'),link('Choose a scoring session →','workspace'));}
      if(view==='ml')ux.research(area);
    });
    app.replaceChildren(views);
  }
  function rankings() {
    const fmt=ux.formats('T20I',false),category=ux.segments('Rankings',[['batting','Batting leaders'],['bowling','Bowling leaders'],['archive','ICC archive']],'batting');
    filters([fmt,category],async()=>{
      const content=node('div');
      if(category.input.value==='archive'){
        const official=node('a','View current official ICC rankings ↗');official.href='https://www.icc-cricket.com/rankings';official.className='ui-action-primary';
        content.append(node('p','This archive is not current ICC ranking evidence. Live ICC updates require an approved source; old default ratings are not displayed as current.','ui-notice'),official);
        return content;
      }
      const data=await request('/api/rankings?'+new URLSearchParams({format:fmt.input.value,type:category.input.value,limit:30}));
      const bowling=category.input.value==='bowling';
      content.append(node('p','Statistical leaders from the selected historical dataset, not official ICC ratings. Minimum: '+(bowling?'five wickets':'five innings')+'.','ui-notice'));
      content.append(table(fmt.input.value+' '+(bowling?'bowling':'batting')+' leaders',bowling?['Rank','Player','Wickets','Average','Economy']:['Rank','Player','Runs','Average','Strike rate'],(data.results||[]).map((r,index)=>[index+1,playerLink({name:r.player,identity_id:r.identity_id}),bowling?r.wickets:r.runs,r.average,bowling?r.economy:r.strike_rate])));return content;
    });
  }
  function records() {
    const fmt=ux.formats('Test',false),category=ux.segments('Records',[['most_runs','Most runs'],['most_wickets','Most wickets'],['best_averages','Best averages'],['most_hundreds','Most hundreds']],'most_runs');
    filters([fmt,category],async()=>{
      const data=await request('/api/records'),rows=(data[category.input.value]||{})[fmt.input.value]||[],content=node('div');
      const isBowling=category.input.value==='most_wickets';
      const heading=node('div',null,'ui-section-heading');heading.append(node('h2',category.wrap.querySelector('[aria-pressed=true]').textContent+' · '+fmt.input.value),node('span','Available matches · not complete careers','ui-card-scope'));content.append(heading);
      content.append(table('Records from available matches',isBowling?['Rank','Player','Wickets','Average','Economy']:['Rank','Player','Runs','Average','Hundreds','Highest innings'],rows.map((r,index)=>isBowling?[index+1,playerLink({name:r.player,identity_id:r.identity_id}),r.wickets,r.average,r.economy]:[index+1,playerLink({name:r.player,identity_id:r.identity_id}),r.runs,r.average,r.hundreds,r.highest])));return content;
    });
  }
  function search() {
    const term = field('Search players, teams, venues or matches', null, query.get('q') || '');
    filters([term], async () => {
      const content = node('div');
      if (!term.input.value.trim()) { content.append(node('p', 'Enter a name, venue or match to search.', 'ui-state')); return content; }
      const data = await request('/api/search?' + new URLSearchParams({q: term.input.value.trim(), limit:20}));
      for (const [key, target] of [['players', 'player-profile'], ['teams', 'team-profile'], ['venues', 'venue-profile']]) {
        content.append(table(key[0].toUpperCase() + key.slice(1), ['Name'], (data[key] || []).map(r => [key === 'players' ? playerLink(r) : key === 'teams' ? teamLink(r.name) : link(r.name,target,{name:r.name})])));
      }
      content.append(node('h2', 'Matching fixtures and results'), fixtureCards(data.matches || [])); return content;
    });
  }
  function compare() {
    app.replaceChildren();const content=node('div'), selectors=node('div',null,'ui-compare-selectors'), results=node('section'), actions=node('div',null,'ui-compare-actions');
    let kind='players',first,second,generation=0;
    const mode=ux.segments('Compare',[['players','Players'],['teams','Teams']],'players',value=>{kind=value;build();});
    const fmt=ux.formats('ODI',false,()=>render());
    const submit=button('Compare selected',render);submit.disabled=true;
    content.append(mode.wrap,selectors,fmt.wrap,actions,results);actions.append(submit);app.append(content);
    function changed(){
      submit.disabled=!first.selected || !second.selected || (first.selected.identity_id||first.selected.name)===(second.selected.identity_id||second.selected.name);
      if(!submit.disabled)render();
      else if(first.selected && second.selected){generation++;results.replaceChildren(node('p','Choose two different identities.','ui-state'));results.setAttribute('aria-busy','false');}
    }
    function build(){
      generation++;results.replaceChildren(node('p','Choose a player or team on each side. Search is optional; browse the choices below.','ui-state'));
      first=ux.picker(kind==='players'?'Player A':'Team A',kind,()=>changed(),query.get('a'));
      second=ux.picker(kind==='players'?'Player B':'Team B',kind,()=>changed(),query.get('b'));
      selectors.replaceChildren(first.wrap,second.wrap);submit.disabled=true;
    }
    async function render(){
      if(!first.selected || !second.selected)return;
      if((first.selected.identity_id||first.selected.name)===(second.selected.identity_id||second.selected.name)){results.replaceChildren(node('p','Choose two different identities.','ui-state'));return;}
      const current=++generation,a=first.selected,b=second.selected,format=fmt.input.value;state(results,'loading');
      try{
        const area=node('div');
        if(kind==='teams'){
          const [left,right]=await Promise.all([request('/api/teams/'+encodeURIComponent(a.name)),request('/api/teams/'+encodeURIComponent(b.name))]);
          const x=(left.format_stats||{})[format],y=(right.format_stats||{})[format];
          if(!x||!y){state(area,'empty');}else area.append(comparisonHeader(left,right,true),table(format+' team comparison',['Metric',left.name,right.name],[['Matches','matches'],['Won','won'],['Lost','lost'],['Win %','win_pct']].map(([label,key])=>[label,x[key],y[key]])));
        }else{
          const data=await request('/api/compare/players?'+new URLSearchParams({player_a:a.identity_id||a.name,player_b:b.identity_id||b.name}));
          const left=data.player_a,right=data.player_b;area.append(comparisonHeader(left,right,false));
          const x=(left.batting||{})[format],y=(right.batting||{})[format];
          if(x&&y){area.append(table(format+' observed batting comparison',['Metric',ux.name(left),ux.name(right)],[['Matches','matches'],['Innings','innings'],['Runs','runs'],['Average','average'],['Strike rate','strike_rate'],['Highest innings','highest'],['Hundreds','hundreds']].map(([label,key])=>[label,x[key],y[key]])),ux.empirical(left,format),ux.empirical(right,format));}
          else area.append(node('p','One or both players have no batting sample in this format.','ui-state'));
          const bx=(left.bowling||{})[format],by=(right.bowling||{})[format];
          if(bx&&by)area.append(table(format+' observed bowling comparison',['Metric',ux.name(left),ux.name(right)],[['Innings','innings'],['Wickets','wickets'],['Average','average'],['Economy','economy']].map(([label,key])=>[label,bx[key],by[key]])));
        }
        if(current===generation){results.replaceChildren(area);results.setAttribute('aria-busy','false');}
      }catch(error){if(current===generation)state(results,error.kind||'error',render);}
    }
    build();
  }
  function information() {
    const content = panel(page === 'about' ? 'Built for match preparation and review' : page === 'data-sources' ? 'Traceable sources, clear limits' : 'What these records mean');
    if (page === 'about') content.append(node('p', 'Criclytics brings historical player, team, venue and match records into one place. The current dataset is a subset of men’s internationals, with coverage gaps and statistical revisions still under review.'));
    else if (page === 'data-sources') {
      content.append(node('p', 'Historical delivery data is provided by Cricsheet under the Open Data Commons Attribution License 1.0. Aggregates are derived from that dataset and may change as scoring contracts are corrected.'));
      const source = node('a', 'Cricsheet data and licensing'); source.href = 'https://cricsheet.org/licensing/'; content.append(source);
      content.append(node('p', 'Fixture and ranking snapshots may be cached or historical fallbacks. Their source and observation dates are displayed where available. Unknown timestamps do not imply fresh data.'));
      content.append(node('h2','Photography & flags'),node('p','Player photographs are locally hosted, licensed editorial portraits. Crops are for display. Availability is limited to the curated identities below; initials are used elsewhere. No endorsement is implied.'));
      Object.entries(media.portraits).forEach(([id,p])=>{const row=node('p',p.name+' — ');row.append(media.credit(id));content.append(row);});
      const flags=node('a','Flag icons: Panayiotis Lipiridis and contributors · MIT license');flags.href='/static/images/flags/LICENSE.txt';content.append(flags);
    } else content.append(node('p', 'Historical counts describe observed matches, not complete careers or guarantees about future performance. Missing values are displayed as unavailable. A snapshot of an in-progress match is not a verified real-time feed.'));
    prediction(content); app.replaceChildren(content);
  }
  async function workspace() {
    let sessions={workspaces:[]};
    try{sessions=await request('/api/v1/workspaces');}catch(_){/* Existing hosts may not expose local sessions. */}
    const identifier=field('Advanced session identifier',null,query.get('id') || ((sessions.workspaces||[])[0]||{}).id || '');
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
    function distribution(record,title){
      const area=panel(title);area.append(node('p','Issued: '+record.issued_at+' · '+(record.content.mode||'historical/manual')+' · inspect the full joint distribution below.','ui-card-scope'));
      const grid=node('div',null,'ui-outcome-list');
      Object.entries(record.content.distribution||{}).sort((a,b)=>b[1]-a[1]).slice(0,6).forEach(([label,p])=>{
        const row=node('div'),meter=node('meter');meter.min=0;meter.max=1;meter.value=p;meter.setAttribute('aria-label',jointLabel(label));row.append(node('span',jointLabel(label)),node('strong',(100*p).toFixed(2)+'%'),meter);grid.append(row);
      });area.append(grid,node('p','Top six joint outcomes shown. OTHER retains unknown runs and dismissals; no exact wicket or runs marginal is inferred.','ui-notice'));return area;
    }
    const surface = filters([identifier], async () => {
      clearTimeout(expiry);
      const content = node('div');
      content.append(node('p', 'Experimental shadow workspace. No validated current coaching prediction is released.', 'ui-prediction'),
        node('p', 'Manual refresh only. A source confirmation can expire before the actual ball is observed.'));
      const id = identifier.input.value.trim();
      if (!id) { content.append(node('p', 'No scoring session is connected. Select a local replay or manual session when available. Public next-ball predictions need an approved timely feed.', 'ui-state'),link('Browse match scorecards','matches')); return content; }
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
      const diagnostics=node('details',null,'ui-record-details');diagnostics.append(node('summary','Source, context and model details'));
      if (core) {
        const score = core.innings.find(inn => inn.innings === core.active_innings);
        content.append(metrics([['Runs',score.runs],['Wickets',score.wickets],['Overs',Math.floor(score.legal_balls/6)+'.'+score.legal_balls%6],['Source age (seconds)',Number.isFinite(data.source_age_seconds)?data.source_age_seconds.toFixed(1):null]]));
        diagnostics.append(
          node('p', 'Source cutoff: ' + core.source_cutoff + ' · status: ' + core.source_status),
          node('p', 'Source revision: ' + core.source_revision_counter + ' · state: ' + data.state_id));
        if (core.next_context) diagnostics.append(table('Announced next-attempt participants', ['Striker','Non-striker','Bowler'], [[core.next_context.striker,core.next_context.non_striker,core.next_context.bowler]]));
        diagnostics.append(node('p', 'History: ' + core.history_scope),
          table('Context coverage in model', ['Context', 'Availability'], Object.entries(core.context_coverage).map(([key,value]) => [key.replaceAll('_',' '),value.replaceAll('_',' ')])));
      }
      if (data.model) {
        diagnostics.append(node('p', data.model.limitations), node('p', 'Model ' + data.model.model_id + ' · calibration through ' + data.model.calibration_last_date));
        const samples = (data.model.training_coverage || {}).matches;
        if (samples) diagnostics.append(table('Historical model sample', ['Partition','Matches'], Object.entries(samples)));
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
      if(data.forecast && data.forecast_allowed)current.append(distribution(data.forecast,'Current experimental next-attempt probabilities'));
      content.append(current,diagnostics);
      if(!data.forecast_allowed && records.length)content.append(distribution(records[0],'Past issued probabilities · not a current forecast'));
      content.append(node('h2','Issued history · past entries are not current forecasts'));
      if (historyUnavailable) content.append(node('p', 'Full history is unavailable. The returned issued entry is retained below.', 'ui-error'));
      records.forEach(record => content.append(issuedPanel(record)));
      if (!records.length) content.append(node('p', 'No issued entries available.', 'ui-state'));
      return content;
    });
    surface.form.querySelector('button[type=submit]').textContent = 'Refresh probabilities';
    const advanced=node('details',null,'ui-record-details');advanced.append(node('summary','Advanced: open a known session'),identifier.wrap);surface.form.prepend(advanced);
    const intro=panel('Prediction & probability centre');intro.append(node('p','Choose a scoring session, inspect next-delivery outcomes and review the model evidence. Replay is explicitly historical; experimental output is not validated coaching advice.'));
    const choices=node('div',null,'ui-session-grid');
    (sessions.workspaces||[]).forEach(session=>{const choose=button((session.teams||[]).join(' vs ')+' · '+session.format+' · '+(session.dates||[]).join(', ')+' · '+session.mode,()=>{identifier.input.value=session.id;surface.run();});choose.className='ui-session-card';choices.append(choose);});
    if(!choices.childNodes.length)choices.append(node('p',sessions.reason || 'No local scoring sessions are configured.','ui-state'));
    intro.append(choices);const research=panel();ux.research(research);app.prepend(intro);app.append(research);
  }
  async function loadCoverage() {
    try {
      const data = await request('/api/coverage');
      if (!data.available) return;
      const target = document.querySelector('.ui-coverage');
      target.textContent = data.scope + ' · ' + Number(data.accepted_matches).toLocaleString() +
        ' matches · ' + data.first_match_date + ' — ' + data.last_match_date +
        '. Available-match statistics, not complete career totals. Cricsheet (ODC-BY-1.0).';
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
  media.initialize().finally(init);
}());
