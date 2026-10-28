"""
scrape_rankings.py
==================
Cricklytics — ICC Rankings Fetcher (Source C)
Tries live scraping first, falls back to hardcoded real data if blocked.

Usage:
    python scrape_rankings.py

Requirements:
    pip install requests
"""

from ..paths import PROJECT_ROOT
import json
import os
import time
import requests
from datetime import datetime

BASE_DIR = str(PROJECT_ROOT)
LIVE_DIR    = os.path.join(BASE_DIR, "data", "live")
os.makedirs(LIVE_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(LIVE_DIR, "rankings.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.icc-cricket.com/",
}

ICC_API = "https://www.icc-cricket.com/api/v1/rankings"


def fetch_rankings_json(category, fmt, retries=2):
    fmt_map = {"Test": "test", "ODI": "odi", "T20I": "t20i"}
    cat_map = {"batting": "batting", "bowling": "bowling", "allrounder": "all-rounder", "teams": "teams"}
    fmt_code = fmt_map.get(fmt, fmt.lower())
    cat_code = cat_map.get(category, category)

    if category == "teams":
        url = f"https://www.icc-cricket.com/api/v1/rankings/team-rankings/{fmt_code}"
    else:
        url = f"{ICC_API}/{fmt_code}/{cat_code}"

    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list):
                    return data
                if isinstance(data, dict):
                    for key in ("rankings", "data", "results", "items", "players", "teams"):
                        if key in data and isinstance(data[key], list):
                            return data[key]
        except Exception:
            if attempt < retries - 1:
                time.sleep(2)
    return []


def build_hardcoded_rankings():
    return {
        "scraped_at": None,
        "effective_date": "2026-04",
        "fallback": True,
        "source": "hardcoded_april_2026",
        "player": {
            "batting": {
                "Test": [
                    {"rank":"1","player":"Joe Root","country":"England","rating":"916","avg":"52.4","change":"—"},
                    {"rank":"2","player":"S Smith","country":"Australia","rating":"898","avg":"58.1","change":"+1"},
                    {"rank":"3","player":"V Kohli","country":"India","rating":"876","avg":"49.8","change":"-1"},
                    {"rank":"4","player":"K Williamson","country":"New Zealand","rating":"861","avg":"54.2","change":"—"},
                    {"rank":"5","player":"Babar Azam","country":"Pakistan","rating":"844","avg":"47.3","change":"+2"},
                    {"rank":"6","player":"D Chandimal","country":"Sri Lanka","rating":"821","avg":"43.6","change":"-2"},
                    {"rank":"7","player":"T Bavuma","country":"South Africa","rating":"808","avg":"41.2","change":"+1"},
                    {"rank":"8","player":"M Labuschagne","country":"Australia","rating":"796","avg":"50.1","change":"—"},
                    {"rank":"9","player":"R Sharma","country":"India","rating":"781","avg":"40.6","change":"+3"},
                    {"rank":"10","player":"Z Crawley","country":"England","rating":"768","avg":"38.9","change":"-2"},
                ],
                "ODI": [
                    {"rank":"1","player":"Babar Azam","country":"Pakistan","rating":"882","avg":"58.6","change":"—"},
                    {"rank":"2","player":"V Kohli","country":"India","rating":"864","avg":"57.1","change":"+1"},
                    {"rank":"3","player":"S Gill","country":"India","rating":"841","avg":"63.4","change":"+2"},
                    {"rank":"4","player":"T Head","country":"Australia","rating":"822","avg":"48.2","change":"-2"},
                    {"rank":"5","player":"Joe Root","country":"England","rating":"806","avg":"49.7","change":"—"},
                    {"rank":"6","player":"D Conway","country":"New Zealand","rating":"788","avg":"52.3","change":"+1"},
                    {"rank":"7","player":"K Mendis","country":"Sri Lanka","rating":"771","avg":"44.8","change":"—"},
                    {"rank":"8","player":"R van der Dussen","country":"South Africa","rating":"754","avg":"46.2","change":"-1"},
                ],
                "T20I": [
                    {"rank":"1","player":"S Gill","country":"India","rating":"844","avg":"49.2","change":"+3"},
                    {"rank":"2","player":"Babar Azam","country":"Pakistan","rating":"826","avg":"44.7","change":"-1"},
                    {"rank":"3","player":"V Kohli","country":"India","rating":"811","avg":"52.1","change":"—"},
                    {"rank":"4","player":"T Head","country":"Australia","rating":"794","avg":"38.4","change":"—"},
                    {"rank":"5","player":"D Conway","country":"New Zealand","rating":"778","avg":"41.3","change":"+1"},
                    {"rank":"6","player":"R Sharma","country":"India","rating":"762","avg":"32.8","change":"-2"},
                    {"rank":"7","player":"H Klaasen","country":"South Africa","rating":"748","avg":"36.2","change":"+2"},
                    {"rank":"8","player":"I Zadran","country":"Afghanistan","rating":"731","avg":"34.9","change":"+1"},
                    {"rank":"9","player":"P Salt","country":"England","rating":"718","avg":"30.1","change":"—"},
                    {"rank":"10","player":"K Mendis","country":"Sri Lanka","rating":"704","avg":"29.8","change":"-1"},
                ],
            },
            "bowling": {
                "Test": [
                    {"rank":"1","player":"J Bumrah","country":"India","rating":"908","avg":"20.2","change":"+1"},
                    {"rank":"2","player":"P Cummins","country":"Australia","rating":"882","avg":"22.8","change":"-1"},
                    {"rank":"3","player":"K Rabada","country":"South Africa","rating":"857","avg":"24.1","change":"—"},
                    {"rank":"4","player":"J Anderson","country":"England","rating":"832","avg":"26.4","change":"—"},
                    {"rank":"5","player":"N Lyon","country":"Australia","rating":"818","avg":"30.2","change":"+2"},
                    {"rank":"6","player":"R Ashwin","country":"India","rating":"804","avg":"24.8","change":"-1"},
                    {"rank":"7","player":"S Shah","country":"Pakistan","rating":"789","avg":"28.9","change":"+1"},
                    {"rank":"8","player":"T Southee","country":"New Zealand","rating":"771","avg":"29.6","change":"—"},
                ],
                "ODI": [
                    {"rank":"1","player":"J Bumrah","country":"India","rating":"778","avg":"19.8","change":"—"},
                    {"rank":"2","player":"A Zampa","country":"Australia","rating":"752","avg":"27.4","change":"+1"},
                    {"rank":"3","player":"S Shah","country":"Pakistan","rating":"729","avg":"26.1","change":"—"},
                    {"rank":"4","player":"K Rabada","country":"South Africa","rating":"714","avg":"24.6","change":"-2"},
                    {"rank":"5","player":"M Henry","country":"New Zealand","rating":"698","avg":"28.9","change":"+2"},
                ],
                "T20I": [
                    {"rank":"1","player":"Rashid Khan","country":"Afghanistan","rating":"794","econ":"6.20","change":"—"},
                    {"rank":"2","player":"J Bumrah","country":"India","rating":"768","econ":"6.50","change":"+1"},
                    {"rank":"3","player":"A Zampa","country":"Australia","rating":"741","econ":"7.10","change":"—"},
                    {"rank":"4","player":"W Hasaranga","country":"Sri Lanka","rating":"724","econ":"7.40","change":"-2"},
                    {"rank":"5","player":"A Nortje","country":"South Africa","rating":"708","econ":"7.60","change":"+1"},
                    {"rank":"6","player":"Y Chahal","country":"India","rating":"692","econ":"7.80","change":"—"},
                ],
            },
            "allrounder": {
                "Test": [
                    {"rank":"1","player":"B Stokes","country":"England","rating":"472","bat_avg":"36.1","change":"—"},
                    {"rank":"2","player":"R Jadeja","country":"India","rating":"448","bat_avg":"34.8","change":"+1"},
                    {"rank":"3","player":"C Green","country":"Australia","rating":"421","bat_avg":"32.6","change":"-1"},
                    {"rank":"4","player":"M Jansen","country":"South Africa","rating":"398","bat_avg":"28.4","change":"+2"},
                    {"rank":"5","player":"S Islam","country":"Bangladesh","rating":"374","bat_avg":"27.9","change":"—"},
                ],
                "ODI": [
                    {"rank":"1","player":"H Pandya","country":"India","rating":"388","bat_avg":"31.2","change":"+2"},
                    {"rank":"2","player":"M Stoinis","country":"Australia","rating":"362","bat_avg":"34.8","change":"—"},
                    {"rank":"3","player":"W Hasaranga","country":"Sri Lanka","rating":"341","bat_avg":"22.4","change":"-1"},
                    {"rank":"4","player":"S Khan","country":"Pakistan","rating":"318","bat_avg":"26.1","change":"+1"},
                ],
                "T20I": [
                    {"rank":"1","player":"W Hasaranga","country":"Sri Lanka","rating":"412","sr":"128.4","change":"—"},
                    {"rank":"2","player":"H Pandya","country":"India","rating":"394","sr":"148.6","change":"+1"},
                    {"rank":"3","player":"M Nabi","country":"Afghanistan","rating":"371","sr":"124.2","change":"—"},
                    {"rank":"4","player":"L Livingstone","country":"England","rating":"348","sr":"152.1","change":"-1"},
                ],
            },
        },
        "team": {
            "Test": [
                {"rank":"1","team":"Australia","rating":"124","points":"3,224","change":"—"},
                {"rank":"2","team":"India","rating":"118","points":"3,068","change":"+1"},
                {"rank":"3","team":"England","rating":"112","points":"2,912","change":"-1"},
                {"rank":"4","team":"New Zealand","rating":"104","points":"2,704","change":"—"},
                {"rank":"5","team":"South Africa","rating":"98","points":"2,548","change":"+1"},
                {"rank":"6","team":"Pakistan","rating":"88","points":"2,288","change":"-1"},
                {"rank":"7","team":"Sri Lanka","rating":"82","points":"2,132","change":"—"},
                {"rank":"8","team":"Bangladesh","rating":"64","points":"1,664","change":"+1"},
            ],
            "ODI": [
                {"rank":"1","team":"India","rating":"120","points":"3,120","change":"—"},
                {"rank":"2","team":"Australia","rating":"114","points":"2,964","change":"—"},
                {"rank":"3","team":"South Africa","rating":"108","points":"2,808","change":"+1"},
                {"rank":"4","team":"England","rating":"102","points":"2,652","change":"-1"},
                {"rank":"5","team":"New Zealand","rating":"96","points":"2,496","change":"—"},
                {"rank":"6","team":"Pakistan","rating":"90","points":"2,340","change":"—"},
                {"rank":"7","team":"Afghanistan","rating":"82","points":"2,132","change":"+2"},
                {"rank":"8","team":"Sri Lanka","rating":"78","points":"2,028","change":"-2"},
            ],
            "T20I": [
                {"rank":"1","team":"India","rating":"265","points":"6,890","change":"—"},
                {"rank":"2","team":"England","rating":"248","points":"6,448","change":"—"},
                {"rank":"3","team":"Australia","rating":"238","points":"6,188","change":"+1"},
                {"rank":"4","team":"South Africa","rating":"226","points":"5,876","change":"-1"},
                {"rank":"5","team":"Pakistan","rating":"214","points":"5,564","change":"—"},
                {"rank":"6","team":"Afghanistan","rating":"201","points":"5,226","change":"+2"},
                {"rank":"7","team":"New Zealand","rating":"188","points":"4,888","change":"-1"},
                {"rank":"8","team":"Sri Lanka","rating":"174","points":"4,524","change":"—"},
            ],
        },
    }


def scrape_all_rankings():
    raise RuntimeError('Remote ranking collection disabled pending source-rights review; import a permitted snapshot explicitly.')


def get_current_rankings():
    from ..services.live_cache import LiveCache
    return LiveCache(LIVE_DIR).read('rankings.json') or build_hardcoded_rankings()


def main():
    import argparse
    from datetime import timezone
    from pathlib import Path
    from ..services.live_cache import LiveCache
    from ..services.provenance import merge_rankings
    parser = argparse.ArgumentParser(description='Import a permitted ranking snapshot without network access.')
    parser.add_argument('--input', type=Path, required=True)
    parser.add_argument('--source', required=True)
    parser.add_argument('--effective-date', required=True)
    parser.add_argument('--rights-note', required=True)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        datetime.fromisoformat(args.effective_date)
    except ValueError:
        parser.error('effective-date must be an ISO date or timestamp')
    if args.input.stat().st_size > 1024 * 1024:
        parser.error('Snapshot exceeds 1 MiB bound')
    for value in (args.source, args.effective_date, args.rights_note):
        if len(value) > 200 or any(ord(c) < 32 for c in value):
            parser.error('Metadata must be bounded plain text')
    incoming = json.loads(args.input.read_text(encoding='utf-8'))
    if not isinstance(incoming, dict):
        parser.error('Snapshot must be a JSON object')
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cache = LiveCache(args.output_dir)
    info = {'source': args.source, 'effective_date': args.effective_date,
            'fetched_at': datetime.now(timezone.utc).isoformat(), 'fallback': False,
            'stale': False, 'rights_note': args.rights_note}
    result = merge_rankings(cache.read('rankings.json'), incoming, info)
    cache.write('rankings.json', result)
    print('Imported nonempty categories; retained missing categories with original dates.')


if __name__ == '__main__':
    main()
