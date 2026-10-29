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
  function picker(label,kind,onSelect,initial) {
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
          const data=await request('/api/players?'+new URLSearchParams({search:input.value.trim(),limit:12,offset}));values=data.players||[];total=data.total;
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
    const launch=node('a','Open next-delivery prediction centre →');launch.href='workspace.html';launch.className='ui-action-primary';content.append(launch);return content;
  }
  async function research(target){
    target.append(node('h2','ML insights'),node('p','Experimental next-delivery model · male international T20I. A trained model exists; current coaching deployment remains unvalidated.','ui-notice'));
    try{
      evidence=evidence||fetch('/static/data/model-evidence.json',{credentials:'omit'}).then(r=>{if(!r.ok)throw Error();return r.json();});
      const data=await evidence;
      target.append(node('p',`${data.training_matches} training matches · ${data.calibration_matches} calibration · ${data.test_matches} held-out matches (${data.test_rows.toLocaleString()} attempts). Test period: ${data.test_period}.`));
      const grid=node('div',null,'ui-probability-grid');
      data.metrics.forEach(row=>{const card=node('div',null,'ui-probability-card'), meter=node('meter');meter.min=0;meter.max=2;meter.value=row.log_loss;meter.setAttribute('aria-label',row.name+' log loss');card.append(node('h3',row.name),node('strong',row.log_loss.toFixed(4)),meter,node('small','Held-out log loss · lower is better'));grid.append(card);});target.append(grid,node('p','The learner did not beat the stronger phase baseline in this evaluation. Historical testing is not prospective live validation.','ui-notice'));
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
  window.CriclyticsExperience=Object.freeze({segments,formats,picker,playerCard,empirical,research,name,teams,liveWidget});
}());
