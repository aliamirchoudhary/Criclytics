"""Frozen independent matchup-family experiment; no production selection or external calls."""
import json
from pathlib import Path
import numpy as np
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.pipeline.features import export
from criclytics_app.pipeline.events import encoded
from criclytics_app.pipeline.artifacts import digest
from criclytics_app.ml.baseline import fit,load_model,read_rows,matrix,probabilities,cluster_interval


def main():
    root=PROJECT_ROOT/'build/context-ablation-v1';root.mkdir(exist_ok=True)
    full=root/'features-full';without=root/'features-without-matchup'
    manifest=export(PROJECT_ROOT/'build/events-context-v1.sqlite3',full)
    without.mkdir()
    with (full/'rows.jsonl').open() as source,(without/'rows.jsonl').open('w',newline='\n') as destination:
        for line in source:
            row=json.loads(line)
            for name in ('prior_matchup_samples','prior_matchup_wicket_rate'):row['features'][name]=None
            destination.write(encoded(row)+'\n')
    modified={**manifest,'rows_sha256':digest(without/'rows.jsonl'),'ablation':'matchup history columns absent before all preprocessing'}
    (without/'manifest.json').write_text(json.dumps(modified,indent=2)+'\n')
    protocol='docs/CONTEXT_ABLATION_PROTOCOL.md frozen in e050a22; fresh2019?2021 window'
    full_report=fit(full,root/'model-full',protocol=protocol)
    without_report=fit(without,root/'model-without-matchup',protocol=protocol)
    full_model=load_model(root/'model-full/model.json',full_report['model_id'])
    without_model=load_model(root/'model-without-matchup/model.json',without_report['model_id'])
    test=read_rows(full,{'test'});ablated=read_rows(without,{'test'})
    # Vocabulary is training-derived and identical when only feature columns differ.
    assert full_model['labels']==without_model['labels']
    mapping={value:i for i,value in enumerate(full_model['labels'])};y=np.array([mapping.get(r['label'],0) for r in test])
    p=probabilities(full_model,matrix(test));reference=probabilities(without_model,matrix(ablated))
    interval=cluster_interval(test,y,p,reference)
    result={'protocol':protocol,'feature_manifest':manifest,'full_test_metrics':full_report['test_metrics'],
            'without_matchup_test_metrics':without_report['test_metrics'],'full_vs_without_matchup':interval,
            'full_model_id':full_report['model_id'],'without_model_id':without_report['model_id'],
            'lineup_pitch_home_families':{'eligible_as_issued_records':0,'included':False,'benefit':None},
            'source_availability':'unknown historical publication precision; not prospective proof','promoted':False,
            'decision':'Matchup feature remains experimental; no automatic inclusion/promotion. XI/pitch/home features excluded without eligible timestamped sources.'}
    (PROJECT_ROOT/'docs/audit/context-ablation-2026-10-28.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__=='__main__':main()
