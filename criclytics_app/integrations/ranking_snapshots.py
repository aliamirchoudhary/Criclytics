"""Offline personal ICC HTML import. No fetching, hidden endpoints or public licence."""
import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from bs4 import BeautifulSoup

FORMATS = {'Test':'test','ODI':'odi','T20I':'t20i'}
CATEGORIES = {'batting':'batting','bowling':'bowling','allrounder':'all-rounder','teams':'team-rankings'}
TERMS = 'https://www.icc-cricket.com/news/icc-website-terms-of-use'


def source_url(category, fmt):
    return f'https://www.icc-cricket.com/rankings/{CATEGORIES[category]}/mens/{FORMATS[fmt]}'


def private_path(path):
    from ..paths import PACKAGE_ROOT, PROJECT_ROOT
    path = Path(path).resolve()
    if any(path == root or path.is_relative_to(root) for root in (PACKAGE_ROOT/'static',PROJECT_ROOT/'dist')):
        raise ValueError('Personal ranking evidence must remain outside public output')
    return path


def parse(html, category, fmt, fetched_at):
    if category not in CATEGORIES or fmt not in FORMATS or len(html.encode('utf-8')) > 5*1024*1024:
        raise ValueError('Unsupported or oversized ranking source')
    stamp = datetime.fromisoformat(fetched_at.replace('Z','+00:00'))
    if stamp.tzinfo is None or stamp > datetime.now(timezone.utc):
        raise ValueError('Observation requires a nonfuture timezone-aware timestamp')
    stamp = stamp.astimezone(timezone.utc)
    soup = BeautifulSoup(html,'html.parser')
    heading = ' '.join(h.get_text(' ',strip=True) for h in soup.find_all('h2')).lower()
    category_title = 'team' if category=='teams' else CATEGORIES[category]
    if "men's" not in heading or fmt.lower() not in heading or category_title not in heading or "women's" in heading:
        raise ValueError('Ranking page scope differs from requested category/format')
    match = re.search(r'Rank date\s*-\s*(\d{1,2}\s+[A-Za-z]+\s+\d{4})',soup.get_text(' ',strip=True))
    if not match:
        raise ValueError('Official ranking effective date missing')
    effective = datetime.strptime(match[1],'%d %B %Y').date()
    if effective > stamp.date():
        raise ValueError('Ranking date follows observation')
    tables = soup.find_all('table')
    if len(tables) != 1:
        raise ValueError('Expected exactly one ranking table')
    table = tables[0]
    headings = [h.get_text(' ',strip=True).lower() for h in table.select('thead th')]
    expected = ['pos','team','matches','pts','rating'] if category=='teams' else ['pos','team','player','rating','career best rating']
    if headings != expected:
        raise ValueError('Ranking table columns changed')
    rows, identities, previous_rank, previous_rating = [], set(), 0, 1501
    for index, tr in enumerate(table.select('tbody tr'),1):
        cells = tr.find_all('td',recursive=False)
        if len(cells) != 5:
            raise ValueError('Incomplete ranking row')
        position = cells[0].find('span')
        position = (position or cells[0]).get_text(' ',strip=True)
        rank = previous_rank if position in ('0=','=') else int(position)
        name_cell = cells[1] if category=='teams' else cells[2]
        anchor = name_cell.find('a')
        name = (anchor or name_cell).get_text(' ',strip=True)
        rating = int(cells[4 if category=='teams' else 3].get_text(' ',strip=True))
        country = cells[1].get_text(' ',strip=True)
        if not 1 <= rank <= index or rank < previous_rank or not 0 <= rating <= 1500 or rating > previous_rating:
            raise ValueError('Invalid rank/rating order')
        if rank == previous_rank and rating != previous_rating:
            raise ValueError('Tied rank with unequal rating')
        if not name or len(name)>160 or name.casefold() in identities or len(country)>100:
            raise ValueError('Invalid/duplicate ranking identity')
        row = {'rank':rank,'rating':rating,'player':name,'country':country,'source_position':position}
        if category=='teams':
            row['team'] = name
            row['matches'], row['points'] = [int(c.get_text('',strip=True).replace(',','')) for c in cells[2:4]]
            if not 0 <= row['matches'] <= 10000 or not 0 <= row['points'] <= 10000000:
                raise ValueError('Invalid team totals')
        else:
            row['career_best'] = cells[4].get_text(' ',strip=True)[:250]
        identities.add(name.casefold());rows.append(row)
        previous_rank, previous_rating = rank, rating
    if not 10 <= len(rows) <= 100:
        raise ValueError('Ranking table incomplete or unbounded')
    return {'schema_version':1,'source':'icc_personal_extract','source_url':source_url(category,fmt),
        'terms_url':TERMS,'rights_scope':'local_personal_only','public_reuse_approved':False,
        'category':category,'format':fmt,'effective_date':effective.isoformat(),
        'fetched_at':stamp.isoformat(),'source_sha256':hashlib.sha256(html.encode('utf-8')).hexdigest(),
        'rankings':rows,'fallback':False}


def publish(store, html, category, fmt, fetched_at):
    snapshot = parse(html,category,fmt,fetched_at)  # validate before opening/writing
    store = private_path(store)
    store.parent.mkdir(parents=True,exist_ok=True)
    payload = json.dumps(snapshot,ensure_ascii=False,separators=(',',':'))
    checksum = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    with closing(sqlite3.connect(store,timeout=2)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS snapshots(category TEXT,format TEXT,slot INTEGER,payload TEXT,sha256 TEXT,raw_html TEXT,PRIMARY KEY(category,format,slot))')
        current = db.execute('SELECT payload,sha256,raw_html FROM snapshots WHERE category=? AND format=? AND slot=0',(category,fmt)).fetchone()
        if current and hashlib.sha256(current[0].encode('utf-8')).hexdigest()==current[1]:
            old = json.loads(current[0])
            if snapshot['effective_date'] < old['effective_date'] or snapshot['fetched_at'] < old['fetched_at']:
                raise ValueError('Refusing ranking date regression')
            if old['source_sha256'] == snapshot['source_sha256']:
                db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?,?)',(category,fmt,1,*current))
                return old  # unchanged evidence must not be restamped
            db.execute('INSERT OR REPLACE INTO snapshots VALUES(?,?,?,?,?,?)',(category,fmt,1,*current))
        db.execute('INSERT OR REPLACE INTO snapshots VALUES(?,?,?,?,?,?)',(category,fmt,0,payload,checksum,html))
        db.execute('INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?,?)',(category,fmt,1,payload,checksum,html))
    return snapshot


def read(store, category, fmt):
    store = private_path(store)
    if not store.is_file():
        return None
    with closing(sqlite3.connect(store.as_uri()+'?mode=ro',uri=True,timeout=.25)) as db:
        rows = db.execute('SELECT slot,payload,sha256 FROM snapshots WHERE category=? AND format=? ORDER BY slot',(category,fmt)).fetchall()
    for slot,payload,checksum in rows:
        if len(payload)>1024*1024 or hashlib.sha256(payload.encode('utf-8')).hexdigest()!=checksum:
            continue
        result = json.loads(payload)
        result['backup_used'] = bool(slot)
        result['fallback'] = bool(slot)
        return result
    return None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--html',type=Path,required=True)
    parser.add_argument('--store',type=Path,required=True)
    parser.add_argument('--category',choices=CATEGORIES,required=True)
    parser.add_argument('--format',choices=FORMATS,required=True)
    parser.add_argument('--observed-at',required=True)
    args = parser.parse_args()
    source = private_path(args.html)
    if source.stat().st_size > 5*1024*1024:
        raise ValueError('Oversized HTML')
    result = publish(args.store,source.read_text(encoding='utf-8'),args.category,args.format,args.observed_at)
    print(json.dumps({'rows':len(result['rankings']),'effective_date':result['effective_date'],
                      'source_sha256':result['source_sha256'],'rights_scope':result['rights_scope']}))


if __name__=='__main__':main()
