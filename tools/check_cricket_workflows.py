"""Real local T033 interactions; optional single live-provider embed check."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:5050')
    parser.add_argument('--live-widget', action='store_true')
    parser.add_argument('--report', type=Path, required=True)
    args = parser.parse_args()
    if urlsplit(args.base).hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Use a local preview')
    output = Path('build/t033-preview')
    output.mkdir(exist_ok=True)
    cases = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        for width in (375, 1440):
            page = browser.new_page(viewport={'width':width, 'height':960}, reduced_motion='reduce')
            errors, external = [], []
            page.on('pageerror', lambda error:errors.append(str(error)))
            page.on('request', lambda req:external.append(urlsplit(req.url).hostname)
                    if not req.url.startswith(args.base) else None)
            page.goto(args.base, wait_until='networkidle')
            assert not external, external
            assert page.get_by_role('link', name='Open prediction centre', exact=False).count() == 1
            page.screenshot(path=str(output/f'home-{width}.png'), full_page=True)
            page.goto(args.base+'/players.html', wait_until='networkidle')
            assert page.locator('.ui-player-card').count() == 24
            page.get_by_label('Player name', exact=True).fill('Kohli')
            page.wait_for_function("() => document.querySelectorAll('.ui-player-card').length === 1")
            page.locator('.ui-player-card-title').click()
            page.get_by_role('tab', name='ODI', exact=True).click()
            for name in ('Career stats', 'vs Teams', 'At Venues', 'Probability Insights', 'ML Insights', 'Overview'):
                page.get_by_role('tab', name=name, exact=True).click()
                page.wait_for_timeout(100)
            page.get_by_role('tab', name='Probability Insights', exact=True).click()
            assert page.locator('meter').count() == 3
            assert 'not next-ball' in page.locator('#app').inner_text()
            page.get_by_role('tab', name='ML Insights', exact=True).click()
            page.get_by_text(re.compile(r'^(Calibrated|Contextual) CPU learner$')).wait_for()
            assert page.locator('meter').count() == 3
            page.screenshot(path=str(output/f'profile-ml-{width}.png'), full_page=True)
            page.goto(args.base+'/compare.html', wait_until='networkidle')
            assert page.locator('.ui-picker-option').count() == 24
            assert not page.locator('#app select').count()
            page.locator('.ui-picker').first.locator('.ui-picker-option').first.click()
            page.locator('.ui-picker').last.get_by_role('searchbox').fill('Babar')
            page.locator('.ui-picker').last.get_by_role('button', name='Babar Azam', exact=False).click()
            page.locator('caption').filter(has_text='ODI observed batting comparison').wait_for()
            assert page.locator('.ui-probability-card').count() == 6
            page.screenshot(path=str(output/f'compare-selected-{width}.png'), full_page=True)
            page.locator('.ui-picker').last.get_by_role('searchbox').fill('Kohli')
            page.locator('.ui-picker').last.get_by_role('button', name='Virat Kohli', exact=False).click()
            assert page.get_by_role('button', name='Compare selected', exact=True).is_disabled()
            assert not page.locator('table').count()
            page.get_by_role('button', name='Teams', exact=True).click()
            for index, name in enumerate(('India', 'Pakistan')):
                picker = page.locator('.ui-picker').nth(index)
                picker.get_by_role('searchbox').fill(name)
                picker.get_by_role('button', name=name+' International team', exact=False).click()
            page.locator('caption').filter(has_text='ODI team comparison').wait_for()
            page.goto(args.base+'/records.html', wait_until='networkidle')
            assert not page.locator('#app select').count()
            page.get_by_role('button', name='ODI', exact=True).click()
            page.get_by_role('button', name='Most wickets', exact=True).click()
            page.wait_for_function("() => document.querySelector('caption') && document.querySelector('table').textContent.includes('WICKETS') || document.querySelector('table') && document.querySelector('table').textContent.includes('Wickets')")
            page.goto(args.base+'/rankings.html', wait_until='networkidle')
            assert 'not official ICC ratings' in page.locator('#app').inner_text()
            page.get_by_role('button', name='Bowling leaders', exact=True).click()
            page.locator('caption').filter(has_text='T20I bowling leaders').wait_for()
            page.get_by_role('button', name='ICC snapshots', exact=True).click()
            page.get_by_role('link', name='View current official ICC rankings', exact=False).wait_for()
            assert page.get_by_role('link', name='View current official ICC rankings', exact=False).count() == 1
            page.wait_for_function("() => !document.querySelector('[aria-busy=true]')")
            assert ('ICC snapshot' in page.locator('#app').inner_text() or 'Official rankings are unavailable' in page.locator('#app').inner_text())
            page.goto(args.base+'/workspace.html', wait_until='networkidle')
            assert page.locator('.ui-session-card').count() > 0
            assert 'Past issued probabilities' in page.locator('#app').inner_text()
            assert page.locator('.ui-outcome-list meter').count() > 0
            assert not page.get_by_label('Advanced session identifier', exact=True).is_visible()
            assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth+2')
            page.screenshot(path=str(output/f'predictions-{width}.png'), full_page=True)
            page.goto(args.base+'/matches.html?status=completed', wait_until='networkidle')
            page.locator('.ui-match-card h3 a').first.click()
            page.get_by_role('tab', name='Scorecard', exact=True).click()
            assert page.locator('caption').filter(has_text='Innings totals').count() == 1
            page.get_by_role('tab', name='ML Insights', exact=True).click()
            page.get_by_text(re.compile(r'^(Calibrated|Contextual) CPU learner$')).wait_for()
            assert not errors, errors
            assert not external, external
            cases.append({'width':width, 'passed':True, 'application_errors':errors,
                          'external_requests_before_opt_in':external,
                          'flows':['player cards/search/all profile tabs','empirical probabilities/model evidence',
                                   'comparison player/team selection/same-identity prevention',
                                   'record/leaderboard buttons','session discovery/past joint probabilities',
                                   'match overview/scorecard/model evidence']})
            page.close()
        if args.live_widget:
            page = browser.new_page(viewport={'width':375,'height':960})
            page.goto(args.base, wait_until='networkidle')
            page.get_by_role('button', name='Load live scores', exact=True).click()
            frame = page.frame_locator('iframe.ui-live-widget-frame')
            frame.get_by_text('CRICTIMES EMBED', exact=False).wait_for(timeout=30000)
            body = frame.locator('body').inner_text()
            assert 'LIVE' in body and 'RECENT' in body
            privacy = frame.locator('body').evaluate("() => {try {void parent.document.body;return false;}catch(_){return true;}}")
            assert privacy
            page.screenshot(path=str(output/'live-widget-375.png'), full_page=True)
            page.get_by_role('button', name='Close live scores', exact=True).click()
            assert not page.locator('iframe').count()
            cases.append({'case':'actual external widget', 'loaded':True, 'parent_access_blocked':True,
                          'closed':True, 'prediction_input':False, 'latency_validation':None})
            page.close()
        browser.close()
    args.report.write_text(json.dumps({'cases':cases, 'limitations':'Local Chrome; no current next-delivery external feed, coach validation or live latency guarantee.'},indent=2)+'\n',encoding='utf-8')
    print('Cricket workflow checks passed')


if __name__ == '__main__':
    main()
