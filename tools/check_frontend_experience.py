"""Exercise the T032 visual flows against an already running local preview."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='http://127.0.0.1:5050')
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--screenshots', type=Path, default=Path('build/t032-preview'))
    args = parser.parse_args()
    if urlsplit(args.base).hostname not in ('localhost', '127.0.0.1', '::1'):
        raise ValueError('Use an existing local preview, never production')
    args.screenshots.mkdir(parents=True, exist_ok=True)
    cases = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        for width in (375, 1440):
            page = browser.new_page(viewport={'width': width, 'height': 960}, reduced_motion='reduce')
            errors, external = [], []
            page.on('pageerror', lambda error: errors.append(str(error)))
            page.on('request', lambda req: external.append(req.url) if not req.url.startswith(args.base) else None)
            page.goto(args.base, wait_until='networkidle')
            assert page.locator('.ui-hero-player img').count() == 4
            assert page.locator('.ui-hero h1').count() == 1
            if width < 1100:
                page.locator('.ui-navigation summary').click()
            page.get_by_role('navigation', name='Primary').get_by_role('link', name='Players', exact=True).click()
            page.get_by_label('Player name', exact=True).fill('Kohli')
            page.get_by_role('button', name='Apply filters').click()
            player = page.get_by_role('link', name='Virat Kohli', exact=False).first
            player.wait_for()
            assert 'player%3Acricsheet%3Aba607b88' in player.get_attribute('href')
            player.click()
            page.get_by_role('heading', name='Virat Kohli', exact=True).wait_for()
            assert page.locator('.ui-profile-identity img').count() == 1
            page.get_by_role('tab', name='ODI', exact=True).click()
            assert page.get_by_role('tab', name='ODI', exact=True).get_attribute('aria-selected') == 'true'
            assert page.locator('.ui-photo-credit a', has_text='Anand Anil').count() == 1
            assert page.locator('.ui-record-details').count() == 3
            assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth + 2')
            page.screenshot(path=str(args.screenshots/f'profile-{width}.png'), full_page=True)
            page.locator('.ui-record-details').last.locator('summary').click()
            assert page.locator('.ui-record-details').last.get_attribute('open') is not None
            assert page.locator('.ui-record-details').last.locator('table').is_visible()
            # A matching display name must never attach a portrait to a different identity.
            result = page.evaluate("""() => {
                const m=window.CriclyticsMedia;
                const wrong=m.portrait({name:'V Kohli',identity_id:'player:cricsheet:unknown'});
                const hostile=m.portrait({name:'<img src=x onerror=alert(1)>',identity_id:'unknown'});
                return {wrongImages:wrong.querySelectorAll('img').length,
                    hostileImages:hostile.querySelectorAll('img').length, label:wrong.getAttribute('aria-label')};
            }""")
            assert result['wrongImages'] == result['hostileImages'] == 0
            assert 'unavailable' in result['label']
            # Both photo and flag failure preserve visible, named fallbacks.
            page.route('**/static/images/players/*', lambda route: route.abort())
            page.route('**/static/images/flags/*', lambda route: route.abort())
            page.goto(args.base+'/player-profile.html?name=player%3Acricsheet%3Aba607b88', wait_until='networkidle')
            assert page.locator('.ui-profile-identity .ui-image-fallback').inner_text() == 'VK'
            page.goto(args.base+'/team-profile.html?name=India', wait_until='networkidle')
            assert page.locator('#teamCrest').inner_text() == 'I'
            page.unroute('**/static/images/players/*')
            page.unroute('**/static/images/flags/*')
            # An unavailable fixture service must not erase homepage discovery/results.
            page.route('**/api/matches?status=upcoming*', lambda route: route.fulfill(status=503, json={'error':'unavailable'}))
            page.goto(args.base, wait_until='networkidle')
            assert page.locator('.ui-discover-card').count() == 3
            assert page.locator('.ui-match-card').count() > 0
            assert page.get_by_role('button', name='Try again').count() == 1
            assert not errors, errors
            assert not external, external
            page.unroute('**/api/matches?status=upcoming*')
            for name, path in [('home','/'), ('players','/players.html'), ('matches','/matches.html')]:
                page.goto(args.base+path, wait_until='networkidle')
                page.screenshot(path=str(args.screenshots/f'{name}-{width}.png'), full_page=True)
            cases.append({'width':width, 'passed':True, 'flows':['menu/directory/filter/stable-profile',
                'profile format tab and expandable records', 'photo attribution', 'wrong-identity/hostile-name fallback',
                'denied portrait and flag', 'partial homepage API failure'], 'errors':errors, 'external_requests':external})
            page.close()
        browser.close()
    args.report.write_text(json.dumps({'cases':cases, 'limitations':'Local Chrome only; curated photo coverage is two players. No deployment or real-user acceptance.'}, indent=2)+'\n', encoding='utf-8')
    print('T032 focused flows passed at mobile and desktop widths')


if __name__ == '__main__':
    main()
