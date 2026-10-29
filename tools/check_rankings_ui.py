"""Actual local personal snapshot and unavailable-category interactions."""
import argparse
import json
from pathlib import Path
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',default='http://127.0.0.1:5050')
    parser.add_argument('--report',type=Path,required=True)
    args = parser.parse_args()
    if urlsplit(args.base).hostname not in ('127.0.0.1','localhost','::1'):
        raise ValueError('Local preview only')
    out = Path('build/t036-ui');out.mkdir(exist_ok=True)
    cases = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome',headless=True)
        for width in (375,1440):
            page = browser.new_page(viewport={'width':width,'height':960})
            errors = [];page.on('pageerror',lambda e:errors.append(str(e)))
            expected = page.request.get(args.base+'/api/icc-rankings?category=batting&format=T20I').json()
            teams = page.request.get(args.base+'/api/icc-rankings?category=teams&format=T20I').json()
            assert expected['available'] and teams['available']
            page.goto(args.base+'/rankings.html',wait_until='networkidle')
            page.get_by_role('button',name='ICC snapshots',exact=True).click()
            page.locator('caption').filter(has_text='ICC T20I batting').wait_for()
            assert 'ranking date '+expected['effective_date'] in page.locator('#app').inner_text()
            assert page.locator('tbody tr').count()==len(expected['rankings'])
            page.screenshot(path=str(out/f'batting-{width}.png'),full_page=True)
            page.get_by_role('button',name='Teams',exact=True).last.click()
            page.locator('caption').filter(has_text='ICC T20I teams').wait_for()
            assert page.locator('tbody tr').count()==len(teams['rankings'])
            assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth+2')
            page.get_by_role('button',name='Bowling',exact=True).click()
            page.get_by_text('Official rankings are unavailable here.',exact=False).wait_for()
            assert not page.locator('table').count()
            assert not page.locator('#app select').count()
            assert not errors, errors
            cases.append({'width':width,'passed':True,'batting_rows':len(expected['rankings']),'team_rows':len(teams['rankings']),
                'source_date_displayed':True,'missing_category_unavailable':True,'errors':errors})
            page.close()
        browser.close()
    args.report.write_text(json.dumps({'cases':cases,'scope':'Local personal extract only; no public reuse or automated refresh approved.'},indent=2)+'\n',encoding='utf-8')
    print('Ranking UI checks passed')


if __name__=='__main__':main()
