"""Import attributed local context revisions; no network or psychological coefficients."""
import argparse
import json
from pathlib import Path
from ..services.match_context import ContextLedger,validate
from .ranking_snapshots import private_path


def import_records(source,store):
    source = private_path(source)
    if source.stat().st_size>1024*1024:
        raise ValueError('Context import exceeds one MiB')
    records = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(records,list) or not 1<=len(records)<=64:
        raise ValueError('Import requires1..64attributed records')
    for record in records:
        validate(record)
        if record.get('rights_basis') not in ('own_observation','permitted_extract','licensed') or not record.get('rights_reference'):
            raise ValueError('Every imported observation requires a reuse basis/reference')
    ledger = ContextLedger(store)
    try:
        ledger.connection.execute('BEGIN IMMEDIATE')
        with ledger.connection:
            for record in records:ledger.add(record,commit=False)
    finally:
        ledger.close()
    return len(records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--file',type=Path,required=True)
    parser.add_argument('--ledger',type=Path,required=True)
    args = parser.parse_args()
    print(json.dumps({'imported_records':import_records(args.file,args.ledger),'model_effect':'none'}))


if __name__=='__main__':main()
