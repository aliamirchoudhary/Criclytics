/* Cricket workflows: visible choices, safe text rendering and source-labelled evidence. */
(function () {
  'use strict';
  const {node,display}=window.CriclyticsDOM;
  const {request}=window.CriclyticsAPI;
  const media=window.CriclyticsMedia;
  let uid=0, evidence;
  function segments(label,choices,value,change) {
    const wrap=node('fieldset',null,'ui-segments'), input=node('input');
    input.type='hidden';input.value=value;input.dataset.autosubmit='true';
    wrap.append(node('legend',label),input);
    const buttons=choices.map(([key,title])=>{
      const button=node('button',title);button.type='button';button.dataset.value=key;
      button.addEventListener('click',()=>{
        input.value=key;sync();input.dispatchEvent(new Event('change',{bubbles:true}));if(change)change(key);
      });wrap.append(button);return button;
    });
    function sync(){buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.value===input.value)));}
    sync();return {wrap,input};
  }
  function formats(value,all,change) {
    return segments('Format',(all?[['','All formats']]:[]).concat([['T20I','T20I'],['ODI','ODI'],['Test','Test']]),value,change);
  }
  function name(player){return (media.portraits[player.identity_id]||{}).name || player.full_name || player.name;}
  function teams(player){return (player.observed_teams || []).map(t=>t.team_name).concat(player.observed_teams?[]:[player.country]).filter(Boolean);}
  function picker(label,kind,onSelect,initial,options={}) {
    const wrap=node('section',null,'ui-picker'), heading=node('h2',label), selected=node('div','Choose from the list below','ui-picker-selected');
    const input=node('input'), id='picker-'+(++uid), inputLabel=node('label','Search '+(kind==='players'?'players':'teams'));
    input.id=id;input.type='search';input.maxLength=200;input.placeholder=kind==='players'?'Name or observed team':'Team name';inputLabel.htmlFor=id;
    const list=node('div',null,'ui-picker-list'), status=node('p',null,'ui-picker-status');status.setAttribute('role','status');
    let chosen=null,generation=0,timer,offset=0;
    list.setAttribute('role','group');list.setAttribute('aria-label',label+' choices');
    const more=node('button','More choices');more.type='button';
    more.addEventListener('click',()=>{offset+=12;load();});
    wrap.append(heading,selected,inputLabel,input,status,list,more);
    function choose(value){chosen=value;selected.replaceChildren();selected.append(kind==='players'?media.portrait(value):media.flag(value.name),node('strong',name(value)));sync();onSelect(value);}
    function sync(){list.querySelectorAll('button').forEach(b=>b.setAttribute('aria-pressed',String(chosen && b.dataset.key===(chosen.identity_id||chosen.name))));}
    async function load(){
      const ticket=++generation;status.textContent='Loading choices…';more.disabled=true;
      try{
        let values,total;
        if(kind==='players'){
          const params=new URLSearchParams({search:input.value.trim(),limit:12,offset,role:options.role||'all',sort:options.role==='bowl'?'wickets':'runs'});
          if(options.format)params.set('format',options.format);
          const data=await request('/api/players?'+params);values=data.players||[];total=data.total;
        }else{
          const data=await request('/api/teams');values=Object.keys(data).filter(n=>n.toLowerCase().includes(input.value.trim().toLowerCase())).map(name=>({name}));total=values.length;values=values.slice(offset,offset+12);
        }
        if(ticket!==generation)return;
        list.replaceChildren();
        values.forEach(value=>{
          const button=node('button',null,'ui-picker-option');button.type='button';button.dataset.key=value.identity_id||value.name;
          const description=node('span');description.append(node('strong',name(value)),node('small',teams(value).join(' · ') || (kind==='teams'?'International team':'Observed player')));
          button.append(kind==='players'?media.portrait(value):media.flag(value.name),description);button.addEventListener('click',()=>choose(value));list.append(button);
        });
        status.textContent=total?`${offset+1}–${Math.min(offset+12,total)} of ${total} choices`:'No matching choices.';more.disabled=offset+12>=total;sync();
        if(!chosen && initial){const profile=await request('/api/'+kind+'/'+encodeURIComponent(initial));if(profile.name)choose(profile);initial=null;}
      }catch(_){if(ticket===generation){status.textContent='Choices unavailable. Search again to retry.';list.replaceChildren();}}
    }
    input.addEventListener('input',()=>{clearTimeout(timer);offset=0;timer=setTimeout(load,250);});load();
    return {wrap,get selected(){return chosen;}};
  }
  function playerCard(player,format){
    const card=node('article',null,'ui-player-card'), title=node('a');title.href='player-profile.html?'+new URLSearchParams({name:player.identity_id||player.name});
    title.className='ui-player-card-title';title.append(media.portrait(player),node('h2',name(player)));card.append(title);
    const memberships=node('div',null,'ui-card-memberships');teams(player).slice(0,3).forEach(team=>{const row=node('span');row.append(media.flag(team),document.createTextNode(team));memberships.append(row);});card.append(memberships);
    const available=player.formats||[], chosen=format || (available.includes('T20I')?'T20I':available[0]);
    const stats=(player.batting||{})[chosen], bowling=(player.bowling||{})[chosen], values=stats?[['Runs',stats.runs],['Average',stats.average],['Strike rate',stats.strike_rate]]:bowling?[['Wickets',bowling.wickets],['Economy',bowling.economy],['Average',bowling.average]]:[];
    const metrics=node('dl',null,'ui-card-stats');values.forEach(([label,value])=>{const item=node('div');item.append(node('dt',label),node('dd',display(value)));metrics.append(item);});card.append(metrics);
    const badges=node('p',null,'ui-format-badges');available.forEach(fmt=>badges.append(node('span',fmt)));card.append(badges,node('small',chosen?chosen+' · available-match figures':'Statistics unavailable','ui-card-scope'));
    const actions=node('div',null,'ui-card-actions'), compare=node('a','Compare +'), scouting=node('a','Scout ↗');
    compare.href='compare.html?'+new URLSearchParams({a:player.identity_id||player.name});scouting.href='scouting.html?'+new URLSearchParams({player:player.identity_id||player.name});actions.append(compare,scouting);card.append(actions);return card;
  }
  function empirical(player,format){
    const content=node('section',null,'ui-panel');content.append(node('h2','Probability insights'),node('p','Observed innings frequencies · '+format+'. These describe the selected historical sample; they are not next-ball or future-match predictions.','ui-notice'));
    const stats=(player.batting||{})[format], grid=node('div',null,'ui-probability-grid');
    if(stats && Number.isInteger(stats.innings) && stats.innings>0){
      [['50+ runs',(stats.fifties??NaN)+(stats.hundreds??NaN)],['100+ runs',stats.hundreds],['Not out',stats.not_outs]].forEach(([label,count])=>{
        const card=node('div',null,'ui-probability-card');card.append(node('h3',label));
        if(Number.isInteger(count)&&count>=0&&count<=stats.innings){const meter=node('meter');meter.min=0;meter.max=1;meter.value=count/stats.innings;meter.setAttribute('aria-label',label+' observed innings share');card.append(node('strong',(100*count/stats.innings).toFixed(1)+'%'),meter,node('small',count+' of '+stats.innings+' observed innings'));}
        else card.append(node('p','Unavailable'));
        grid.append(card);
      });content.append(grid);
    }else content.append(node('p','No eligible innings sample in this format.','ui-state'));
    const launch=node('a','Explore a player/bowler/venue scenario →');launch.href='workspace.html?'+new URLSearchParams({view:'scenario',a:player.identity_id||player.name});launch.className='ui-action-primary';content.append(launch);return content;
  }
  async function research(target){
    target.append(node('h2','ML insights'),node('p','Experimental next-delivery model · male international T20I. A trained model exists; current coaching deployment remains unvalidated.','ui-notice'));
    try{
      evidence=evidence||(async()=>{
        const contextual=await request('/api/v1/scenarios/catalog').catch(()=>({available:false}));
        if(contextual.available)return {training_matches:contextual.matches.train,calibration_matches:contextual.matches.calibration,test_matches:contextual.matches.test,test_rows:contextual.metrics.contextual.rows,test_period:contextual.test_period,evaluation_sha256:contextual.evaluation_sha256,feature_families:['innings/phase','batter/bowler records','exact player matchup','venue and team rivalry','last five prior observed matches by role'],metrics:[{name:'Global baseline',...contextual.metrics.global},{name:'Phase baseline',...contextual.metrics.phase},{name:'Contextual CPU learner',...contextual.metrics.contextual}]};
        const result=await fetch('/static/data/model-evidence.json',{credentials:'omit'});if(!result.ok)throw Error();return result.json();
      })();
      const data=await evidence;
      target.append(node('p',`${data.training_matches} training matches · ${data.calibration_matches} calibration · ${data.test_matches} held-out matches (${data.test_rows.toLocaleString()} attempts). Test period: ${data.test_period}.`));
      const grid=node('div',null,'ui-probability-grid');
      data.metrics.forEach(row=>{const card=node('div',null,'ui-probability-card'), meter=node('meter');meter.min=0;meter.max=2;meter.value=row.log_loss;meter.setAttribute('aria-label',row.name+' log loss');card.append(node('h3',row.name),node('strong',row.log_loss.toFixed(4)),meter,node('small','Held-out log loss · lower is better'));grid.append(card);});target.append(grid,node('p',(data.metrics[2].log_loss<data.metrics[1].log_loss?'This candidate improved held-out log loss over the phase reference. ':'This candidate did not improve held-out log loss over the phase reference. ')+'Historical testing is not prospective live validation.','ui-notice'));
      const details=node('details',null,'ui-record-details');details.append(node('summary','Model inputs and evaluation details'));
      details.append(node('p','Inputs: '+data.feature_families.join('; ')),node('p','Optional weather, pitch, crowd and media signals are excluded until independently validated.'),node('p','Evaluation SHA-256: '+data.evaluation_sha256));target.append(details);
    }catch(_){evidence=null;target.append(node('p','Model evaluation report unavailable. No performance values are substituted.','ui-state'));}
  }
  function liveWidget(){
    const panel=node('section',null,'ui-panel ui-live-widget'), controls=node('div',null,'ui-hero-actions'), slot=node('div');
    const load=node('button','Load live scores'),stop=node('button','Close live scores');load.type=stop.type='button';stop.hidden=true;
    const source=node('a','Live scores by CricTimes ↗');source.href='https://crictimes.org/live-cricket-score-widget';
    panel.append(node('h2','Live scores'),node('p','Free external CricTimes score panel. Opens on request without an API key or account credits. Provider latency and completeness are unverified; these scores are not prediction inputs.','ui-score-freshness'));
    load.addEventListener('click',()=>{
      const frame=node('iframe');frame.title='CricTimes live cricket scores (external)';frame.className='ui-live-widget-frame';
      // Different provider origin: it cannot read the application or private plans.
      frame.setAttribute('sandbox','allow-scripts allow-same-origin');frame.referrerPolicy='no-referrer';frame.setAttribute('allow',"camera 'none'; microphone 'none'; geolocation 'none'");
      frame.src='https://cwidget.crictimes.org/?b=091a31&sb=142d4b&c=e8f0fa&a=102440&bo=263e5d&dc=061729&db=61bbff';slot.replaceChildren(frame);load.hidden=true;stop.hidden=false;
    });
    stop.addEventListener('click',()=>{slot.replaceChildren();load.hidden=false;stop.hidden=true;});
    controls.append(load,stop,source);panel.append(controls,slot);return panel;
  }
  function localChoices(label,values,onSelect){
    const wrap=node('section',null,'ui-picker'),input=node('input'),id='local-choices-'+(++uid),inputLabel=node('label','Search '+label.toLowerCase()),list=node('div',null,'ui-picker-list');
    let chosen='';input.type='search';input.id=id;input.maxLength=200;inputLabel.htmlFor=id;list.setAttribute('role','group');list.setAttribute('aria-label',label+' choices');
    const selected=node('p','Choose from the list below','ui-picker-status');wrap.append(node('h2',label),selected,inputLabel,input,list);
    function render(){list.replaceChildren();const matches=values.filter(v=>v.toLowerCase().includes(input.value.trim().toLowerCase()));matches.slice(0,20).forEach(value=>{
      const button=node('button',value,'ui-picker-option');button.type='button';button.setAttribute('aria-pressed',String(chosen===value));button.addEventListener('click',()=>{chosen=value;selected.textContent=value;render();onSelect(value);});list.append(button);
    });if(!matches.length)list.append(node('p','No matching choices.','ui-state'));}
    input.addEventListener('input',render);render();return {wrap,get selected(){return chosen;}};
  }
  async function scenarioExplorer(target,query){
    target.setAttribute('aria-busy','true');
    try{
      const catalog=await request('/api/v1/scenarios/catalog');
      target.replaceChildren(node('h2','What if these players faced each other?'),node('p','Experimental male international T20I · choose a batter, bowler and ground. This is a hypothetical next-attempt distribution, not a live forecast.','ui-notice'));
      if(!catalog.available){target.append(node('p',catalog.reason || 'Contextual model unavailable.','ui-state'));return;}
      target.append(node('p','Source through '+catalog.data_asof+' · model history through '+catalog.training_last_date+'. Recent form means the latest five observed matches, not unobserved current performance.','ui-card-scope'));
      const selectors=node('div',null,'ui-scenario-selectors'),results=node('section'),controls=node('div',null,'ui-panel');
      const submit=node('button','Calculate scenario probabilities');submit.type='button';submit.disabled=true;
      let batter,bowler,venue,left,right,generation=0,last=null;
      const changed=()=>{
        generation++;
        const a=batter?.selected?.identity_id,b=bowler?.selected?.identity_id;
        const teamMismatch=Boolean(left?.selected)!==Boolean(right?.selected) || Boolean(left?.selected && left.selected===right?.selected);
        submit.disabled=!a || !b || !venue?.selected || a===b || teamMismatch;last=null;results.replaceChildren();
      };
      batter=picker('Batter','players',changed,query.get('a'),{format:'T20I',role:'bat'});
      bowler=picker('Bowler','players',changed,query.get('b'),{format:'T20I',role:'bowl'});
      venue=localChoices('Ground',catalog.venues,changed);selectors.append(batter.wrap,bowler.wrap,venue.wrap);
      const phase=segments('Match phase',[['0','Powerplay'],['1','Middle overs'],['2','Death overs']],'0',changed),innings=segments('Innings',[['1','First innings'],['2','Chase']],'1',changed);
      const details=node('details',null,'ui-record-details');details.append(node('summary','Add team rivalry context (optional)'));
      const sides=node('div',null,'ui-compare-selectors');left=localChoices('Team A',catalog.teams,changed);right=localChoices('Team B',catalog.teams,changed);sides.append(left.wrap,right.wrap);details.append(sides);
      const dateLabel=node('label','Scenario date'),dateInput=node('input'),dateId='scenario-date-'+(++uid);dateInput.id=dateId;dateInput.type='date';dateInput.min=catalog.data_asof;dateInput.value=new Date().toISOString().slice(0,10);dateLabel.htmlFor=dateId;dateInput.addEventListener('change',changed);
      const pov=segments('Perspective',[['batter','Batter view'],['bowler','Bowler view']],'batter',()=>{if(last)render(last);});
      controls.append(phase.wrap,innings.wrap,dateLabel,dateInput,details,submit);target.append(selectors,controls,pov.wrap,results);
      function render(data){
        results.replaceChildren(node('h2','Next-attempt model probabilities'));
        const card=node('div',null,'ui-probability-grid');
        const labels=pov.input.value==='batter'?[['six','Six'],['four','Four'],['scoreless_attempt','No total runs']]:[['bowler_credited_wicket','Bowler-credited wicket'],['any_wicket','Any wicket on the attempt'],['legal_delivery','Legal delivery']];
        labels.forEach(([key,label])=>{const value=data.events[key],box=node('div',null,'ui-probability-card'),meter=node('meter');meter.min=0;meter.max=1;meter.value=value.lower;meter.setAttribute('aria-label',label+' known model probability mass');box.append(node('h3',label),node('strong','≈'+(100*value.lower).toFixed(1)+'%'),meter,node('small','Model bounds: '+(100*value.lower).toFixed(3)+'–'+(100*value.upper).toFixed(3)+'%'));card.append(box);});results.append(card);
        results.append(node('p','Both perspectives use the same joint distribution. Event ranges represent unresolved OTHER mass, not confidence intervals; events can overlap.','ui-notice'));
        if(data.cold_start)results.append(node('p','Personal history is missing for at least one role. Backoff priors and observed recent form are used; this is not a fully personalized estimate.','ui-notice'));
        const coverage=node('div',null,'ui-grid');Object.entries(data.recent_form).forEach(([role,row])=>{const box=node('section',null,'ui-card');box.append(node('h3',role+' recent form'),node('p',row.matches+' observed matches · last '+(row.last_observed_date||'unknown')),node('p',row.age_days===null?'Age unavailable':row.age_days+' days old at the scenario date'));coverage.append(box);});results.append(coverage);
        const samples=node('details',null,'ui-record-details');samples.append(node('summary','Context sample sizes and learned mixture weights'));
        Object.entries(data.component_samples).forEach(([family,count])=>samples.append(node('p',family.replaceAll('_',' ')+': '+count.toLocaleString()+' training/history attempts · mixture weight '+(100*data.mixture_weights[family]).toFixed(1)+'%')));results.append(samples,node('p','Not modelled: '+data.unsupported_context.join('; ')+'.','ui-notice'));
        const joint=node('details',null,'ui-record-details');joint.append(node('summary','Full coherent joint distribution · '+(100*data.unknown_mass).toFixed(3)+'% OTHER'));
        Object.entries(data.distribution).sort((a,b)=>b[1]-a[1]).forEach(([label,p])=>joint.append(node('p',label+' → '+(100*p).toFixed(3)+'%')));results.append(joint);
      }
      submit.addEventListener('click',async()=>{
        const current=++generation;submit.disabled=true;results.replaceChildren(node('p','Calculating contextual probabilities…','ui-state'));
        const params=new URLSearchParams({batter:batter.selected.identity_id,bowler:bowler.selected.identity_id,venue:venue.selected,innings:innings.input.value,phase:phase.input.value,as_of:dateInput.value});
        if(left.selected)params.set('team_a',left.selected);if(right.selected)params.set('team_b',right.selected);
        try{const data=await request('/api/v1/scenarios?'+params);if(current===generation){last=data;render(data);}}
        catch(_){if(current===generation)results.replaceChildren(node('p','Scenario unavailable. Choose two different players, a ground, a valid date and either both teams or neither.','ui-error'));}
        finally{if(current===generation)submit.disabled=false;}
      });
    }catch(_){target.replaceChildren(node('p','Scenario model unavailable. Retry the prediction centre when the API is ready.','ui-state'));}
    finally{target.setAttribute('aria-busy','false');}
  }
  window.CriclyticsExperience=Object.freeze({segments,formats,picker,playerCard,empirical,research,name,teams,liveWidget,scenarioExplorer});
}());
