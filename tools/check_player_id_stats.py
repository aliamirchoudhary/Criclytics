"""Full local candidate/API/browser verification; no promotion or network feed."""
import argparse
from collections import Counter
import json
from pathlib import Path
import threading
from werkzeug.serving import make_server
from criclytics_app import create_app
from criclytics_app.paths import PROJECT_ROOT
from criclytics_app.services.json_io import read_json
from criclytics_app.pipeline.artifacts import digest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    args = parser.parse_args()
    registry = PROJECT_ROOT/'build/identities-v1-final.json'
    app = create_app({'PROCESSED_DIR': PROJECT_ROOT/'build/data-v3-manifest-final',
                      'IDENTITY_REGISTRY': registry, 'IDENTITY_PLAYER_STORE': args.candidate,
                      'LIVE_DIR': PROJECT_ROOT/'build/t017a-live', 'REDIS_URL': '', 'LIVE_FETCH_ENABLED': False})
    client, store = app.test_client(), app.extensions['player_id_store']
    sums = Counter(); count = 0
    with store.connect() as db:
        rows = db.execute('SELECT profile FROM players')
        for row in rows:
            p = json.loads(row[0]); count += 1
            assert p['country'] is None
            for fmt, stats in p['batting'].items():
                sums['batting_runs'] += stats['runs']; sums['batting_innings'] += stats['innings']
                for group in ('yearly', 'vs_opp', 'at_venues'):
                    assert sum(s['runs'] for s in p[group][fmt].values()) == stats['runs']
                    assert sum(s['innings'] for s in p[group][fmt].values()) == stats['innings']
            for stats in p['bowling'].values():
                sums['bowling_wickets'] += stats['wickets']; sums['bowling_innings'] += stats['innings']
    for key, total in sums.items(): assert total == store.manifest['totals'][key]
    cook = client.get('/api/players/SC%20Cook').json
    assert cook['batting']['Test']['highest'] == 117
    assert cook['batting']['Test']['innings'] == 19
    assert client.get('/api/players/A%20Ali').status_code == 409
    choices = client.get('/api/players?search=A%20Ali&limit=500').json['players']
    assert len(choices) > 1 and all(p['identity_id'] for p in choices)
    assert client.get('/api/search?q=SC%20Cook').json['players'][0]['identity_id'] == cook['identity_id']
    for formats in store.records().values():
        for fmt, records in formats.items():
            for row in records:
                profile = store.profile(row['identity_id'])
                kind = 'bowling' if 'wickets' in row else 'batting'
                for key in ('runs', 'wickets', 'innings', 'matches', 'hundreds', 'highest', 'average'):
                    if key in row: assert row[key] == profile[kind][fmt][key]
    from playwright.sync_api import sync_playwright
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    browser_results = []
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(channel='chrome', headless=True)
            for width in (375, 1440):
                page = browser.new_page(viewport={'width': width, 'height': 900})
                errors = []; page.on('pageerror', lambda error: errors.append(str(error)))
                base = 'http://127.0.0.1:'+str(server.server_port)
                page.goto(base+'/players.html?search=A%20Ali')
                page.wait_for_function("() => document.querySelector('#app a[href*=\"player%3Acricsheet\"]') !== null")
                assert 'Observed teams' in page.locator('#app').inner_text()
                page.locator('#app a[href*="player%3Acricsheet"]').first.click()
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('Nationality is not inferred')")
                page.goto(base+'/player-profile.html?name=A%20Ali')
                page.get_by_role('link', name='Choose player', exact=True).wait_for()
                page.goto(base+'/player-profile.html?name=SC%20Cook')
                page.wait_for_function("() => document.querySelector('#app').textContent.includes('Nationality is not inferred')")
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                assert not errors, errors
                browser_results.append({'width': width, 'directory_id_link': True, 'ambiguous_name_recovery': True,
                                        'profile': True, 'overflow': False, 'page_errors': errors})
                page.close()
            browser.close()
    finally:
        server.shutdown(); thread.join(timeout=5); server.server_close()
    report = {'candidate': str(args.candidate), 'manifest_sha256': digest(args.candidate/'manifest.json'),
              'manifest': store.manifest, 'profiles_checked': count, 'profile_totals': dict(sums),
              'all_player_context_totals_reconcile': True, 'records_reconcile': True,
              'cook_test_highest': 117, 'cook_test_innings': 19, 'browser': browser_results,
              'limitations': 'Local opt-in only; no default promotion, deployment, complete-career or nationality claim.'}
    (PROJECT_ROOT/'docs/audit/player-id-aggregates-2026-10-28.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'profiles_checked': count, 'totals': dict(sums), 'browser': browser_results}))


if __name__ == '__main__': main()
