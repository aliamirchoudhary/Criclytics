"""Optional authored-fixture proxy checks; never production pressure inference."""
from collections import Counter
import json
from criclytics_app.services.weather import utc
from criclytics_app.services.annotations import position
from criclytics_app.paths import PROJECT_ROOT

PROXIES={'audible_booing','audible_cheering','observed_on_field_incident','critical_headline_tone'}


def eligible(record,cutoff,before_event=None):
    allowed={'proxy','match_id','player_id','source','source_license','source_rights_verified','language','published_at','observed_at','event_id','occurred'}
    if set(record)-allowed or record.get('proxy') not in PROXIES:raise ValueError('Only observable proxy schema is supported')
    if record.get('source_rights_verified') is not True or not record.get('source_license') or not record.get('source'):return False
    if not str(record.get('player_id','')).startswith('player:'):return False
    if type(record.get('occurred')) not in (bool,type(None)):raise ValueError('Occurrence must be observed/unknown')
    if not record.get('published_at') or not record.get('observed_at') or not cutoff:return False
    when=utc(cutoff);published=utc(record['published_at'])
    if max(published,utc(record['observed_at']))>when:return False
    if record['proxy']=='critical_headline_tone':return 0<=(when-published).total_seconds()<=72*3600
    if not before_event or not record.get('event_id'):return False
    mid,innings,attempt=position(record['event_id']);target_mid,target_innings,target_attempt=position(before_event)
    return mid==target_mid==record['match_id'] and (innings,attempt)<(target_innings,target_attempt)


def agreement(first,second):
    if len(first)!=len(second):raise ValueError('Paired labels required')
    paired=[(a,b) for a,b in zip(first,second) if a is not None and b is not None]
    if not paired:return {'paired':0,'agreement':None,'kappa':None}
    if any(type(value) is not bool for pair in paired for value in pair):raise ValueError('Observable binary labels required')
    observed=sum(a==b for a,b in paired)/len(paired)
    a=Counter(pair[0] for pair in paired);b=Counter(pair[1] for pair in paired)
    expected=sum(a[value]/len(paired)*b[value]/len(paired) for value in (True,False))
    return {'paired':len(paired),'agreement':observed,'kappa':(observed-expected)/(1-expected) if expected<1 else None}


def main():
    record={'proxy':'audible_booing','match_id':'match:fictional','player_id':'player:fictional','source':'authored fixture',
            'source_license':'CC0 authored fixture','source_rights_verified':True,'language':'unknown',
            'published_at':'2020-01-01T10:00:00Z','observed_at':'2020-01-01T10:00:01Z',
            'event_id':'match:fictional#i1/d1','occurred':None}
    assert not eligible(record,'2020-01-01T10:00:00Z','match:fictional#i1/d2')
    assert eligible(record,'2020-01-01T10:01:00Z','match:fictional#i1/d2')
    assert not eligible(record,'2020-01-01T10:01:00Z','match:fictional#i1/d1')
    result={'protocol':'docs/MEDIA_RESEARCH_PROTOCOL.md preregistered ed4a874','decision':'excluded_optional_research',
            'external_calls':0,'real_match_events':0,'real_independent_raters':0,'actual_human_agreement':None,
            'actual_heldout_log_loss_delta':None,'actual_heldout_brier_delta':None,
            'fixture_math_only':agreement([True,True,False,False,None],[True,False,False,False,True]),
            'cutoff_checks':True,'production_feature_enabled':False,
            'limitations':'Fictional arrays test arithmetic only; no real human agreement, psychological ground truth or predictive signal claimed.'}
    (PROJECT_ROOT/'docs/audit/media-research-2026-10-28.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
