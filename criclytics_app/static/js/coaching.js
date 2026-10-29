/* Private plans live in this page's memory; no note upload or browser persistence. */
(function () {
  'use strict';
  function validatePlan(value) {
    if (!value || Array.isArray(value) || Object.keys(value).sort().join(',') !== 'assumptions,evidence,notes,roster,schema_version,selectors' || value.schema_version !== 1) throw new Error('Unsupported private plan');
    for (const key of ['notes','roster','assumptions']) if (typeof value[key] !== 'string' || value[key].length > ({notes:12000,roster:4000,assumptions:6000})[key]) throw new Error('Plan field exceeds its limit');
    if (!value.selectors || Object.keys(value.selectors).sort().join(',') !== 'bowler,format,opponent,player,venue') throw new Error('Invalid selectors');
    for (const text of Object.values(value.selectors)) if (typeof text !== 'string' || text.length > 200 || /[\x00-\x1f\x7f]/.test(text)) throw new Error('Invalid selector');
    if (!['T20I','ODI','Test'].includes(value.selectors.format)) throw new Error('Unsupported format');
    if (value.evidence !== null && (typeof value.evidence !== 'object' || Array.isArray(value.evidence))) throw new Error('Invalid evidence');
    if (new TextEncoder().encode(JSON.stringify(value)).byteLength > 131072) throw new Error('Plan file too large');
    return value;
  }
  function init(ui) {
    const {app,query,node,field,formats,table,metrics,panel,button,request,state,link} = ui;
    const controls = {player:field('Batter name or source ID', null, query.get('player') || ''), bowler:field('Bowler name or source ID (optional)',null,''),format:formats('T20I'),opponent:field('Opponent source name (optional)',null,''),venue:field('Venue source name (optional)',null,'')};
    const form=node('form',null,'ui-filters'),results=node('section'),privatePanel=panel('Private preparation plan');
    Object.values(controls).forEach(control=>form.append(control.wrap));
    const submit=node('button','Prepare evidence');submit.type='submit';form.append(submit);
    app.replaceChildren(form,results,privatePanel);
    privatePanel.append(node('p','Notes stay in this page only. Navigation, refresh or closing the page loses them. Export your plan to keep it; anyone with that file can read it. No server upload or browser autosave.','ui-notice'));
    const privateFields={};
    for (const [key,label,max] of [['notes','Private tactical notes',12000],['roster','Private roster',4000],['assumptions','What-if assumptions',6000]]) {
      const wrap=node('div',null,'ui-field'),input=node('textarea');input.id='coach-'+key;input.maxLength=max;input.rows=4;
      const text=node('label',label);text.htmlFor=input.id;wrap.append(text,input);privatePanel.append(wrap);privateFields[key]=input;
    }
    privatePanel.append(node('p','What-if assumptions are planning notes. Changing a selected opponent or venue shows descriptive evidence, not a proven causal advantage or an adjusted probability.'));
    const notice=node('p');notice.setAttribute('role','status');privatePanel.append(notice);
    let evidence=null,generation=0;
    function selectors() {return Object.fromEntries(Object.entries(controls).map(([key,c])=>[key,c.input.value.trim()]));}
    function download(value,filename) {
      const text=JSON.stringify(value,null,2);
      const url=URL.createObjectURL(new Blob([text],{type:'application/json'})),anchor=node('a','Download');anchor.href=url;anchor.download=filename;
      document.body.append(anchor);anchor.click();anchor.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);
    }
    const exportActions=node('div',null,'ui-scouting-actions');
    exportActions.append(button('Export private plan',()=>{
      try {
        const value=validatePlan({schema_version:1,selectors:selectors(),notes:privateFields.notes.value,roster:privateFields.roster.value,assumptions:privateFields.assumptions.value,evidence});
        download(value,'criclytics-private-plan.json');notice.textContent='Private plan exported to a local file. Keep it private.';
      } catch (_) {notice.textContent='Plan could not be exported. Check field and file limits.';}
    }),button('Export public evidence',()=>{if(evidence){download(evidence,'criclytics-scouting-evidence.json');notice.textContent='Public source evidence exported without private notes.';}else notice.textContent='Prepare evidence first.';}));
    privatePanel.append(exportActions);
    const importLabel=node('label','Import private plan from a local file'),file=node('input');file.type='file';file.accept='.json,application/json';file.id='coach-import';importLabel.htmlFor=file.id;privatePanel.append(importLabel,file);
    file.addEventListener('change',async()=>{
      try {
        const selected=file.files[0];if(!selected)return;if(selected.size>131072)throw new Error('File too large');
        const plan=validatePlan(JSON.parse(await selected.text()));
        generation++;
        for(const [key,control] of Object.entries(controls))control.input.value=plan.selectors[key];
        for(const [key,input] of Object.entries(privateFields))input.value=plan[key];
        evidence=null;results.replaceChildren(node('p','Plan imported locally. Prepare evidence to verify its current source records.','ui-state'));
        notice.textContent='Plan restored in this page. Imported evidence is unverified until refreshed. Nothing uploaded.';
      } catch (_) {notice.textContent='Invalid or oversized plan. Existing private fields were preserved.';}
      file.value='';
    });
    function deliveryRows(value){return value ? Object.entries(value).map(([key,n])=>[key.replaceAll('_',' '),n]) : [];}
    async function run() {
      const current=++generation;const selected=selectors();evidence=null;
      if(!selected.player){results.replaceChildren(node('p','Choose a player from the identity directory or enter a unique name.', 'ui-state'),link('Find players','players'));return;}
      state(results,'loading');
      try {
        const report=await request('/api/v1/scouting?'+new URLSearchParams(selected));if(current!==generation)return;
        for (const [fieldName,optionName] of [['opponent','opponents'],['venue','venues']]) {
          const id='scouting-'+optionName;let list=document.getElementById(id);
          if(!list){list=node('datalist');list.id=id;form.append(list);controls[fieldName].input.setAttribute('list',id);}
          list.replaceChildren(...((report.options||{})[optionName]||[]).map(value=>{const option=node('option');option.value=value;return option;}));
        }
        evidence=report;results.replaceChildren(node('h2',report.player.name+' · '+report.format),node('p',report.assumptions,'ui-notice'));
        if(report.batting)results.append(metrics([['Batting matches',report.batting.matches],['Innings',report.batting.innings],['Runs',report.batting.runs],['Average',report.batting.average],['Strike rate',report.batting.strike_rate]]));
        else results.append(node('p','No scored batting innings available for this format.','ui-state'));
        results.append(table('Selected opponent evidence',['Metric','Observed value'],deliveryRows(report.against_opponent)),table('Selected venue evidence',['Metric','Observed value'],deliveryRows(report.at_venue)),
          table('Selected bowler format evidence',['Metric','Observed value'],deliveryRows(report.bowling)),table('Batter versus selected bowler · separate archive',['Metric','Observed value'],deliveryRows(report.matchup)),
          table('Batter phases · separate T20I archive',['Phase','Attempts','Batter runs','Batter balls','Striker dismissals','Bowler credited wickets'],Object.entries(report.phases).filter(([,v])=>v).map(([phase,v])=>[phase,v.attempts,v.batter_runs,v.batter_balls,v.striker_dismissals,v.bowler_credited_wickets])),
          table('Recent observed innings · all formats',['Runs'],report.recent_innings_all_formats.map(r=>[r])));
        if(report.delivery_sample)results.append(node('p','Separate delivery archive: '+report.delivery_sample.matches+' matches, '+report.delivery_sample.first_match_date+' to '+report.delivery_sample.last_match_date+'. '+report.delivery_sample.scope));
        else results.append(node('p','Matchup and phase archive unavailable. Missing evidence is not zero performance.','ui-notice'));
        results.append(node('p','Main coverage: '+report.coverage.first_match_date+' to '+report.coverage.last_match_date+'; '+report.coverage.accepted_matches+' matches. Cutoff is match date, not publication availability.'),
          node('p','Missing context: '+report.missing_context.join(', ')),node('p',report.attribution),node('p','Dataset: '+report.dataset_id),node('p','Report: '+report.report_id));
        results.setAttribute('aria-busy','false');
      }catch(error){if(current===generation)state(results,error.kind||'error',run);}
    }
    form.addEventListener('submit',event=>{event.preventDefault();run();});run();
    Object.values(controls).forEach(control=>control.input.addEventListener('input',()=>{
      generation++;evidence=null;results.replaceChildren(node('p','Selections changed. Prepare evidence for these assumptions.','ui-state'));
    }));
  }
  window.CriclyticsCoach=Object.freeze({init,validatePlan});
}());
