"""Actual contextual scenario choices and shared batter/bowler probability views."""
import argparse
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    output=Path('build/t034-ui');output.mkdir(exist_ok=True)
    cases=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(channel='chrome',headless=True)
        for width in (375,1440):
            page=browser.new_page(viewport={'width':width,'height':960},reduced_motion='reduce')
            errors=[];calls=[]
            page.on('pageerror',lambda e:errors.append(str(e)))
            page.on('request',lambda r:calls.append(r.url) if '/api/v1/scenarios?' in r.url else None)
            page.goto('http://127.0.0.1:5050/workspace.html?view=scenario',wait_until='networkidle')
            page.locator('.ui-scenario-selectors .ui-picker').nth(0).locator('.ui-picker-option').first.click()
            page.locator('.ui-scenario-selectors .ui-picker').nth(1).locator('.ui-picker-option').first.click()
            venue=page.locator('.ui-scenario-selectors .ui-picker').nth(2)
            venue.get_by_role('searchbox').fill('Lord')
            venue.locator('.ui-picker-option').first.click()
            page.get_by_role('button',name='Calculate scenario probabilities',exact=True).click()
            page.get_by_role('heading',name='Next-attempt model probabilities',exact=True).wait_for()
            assert len(calls)==1
            assert page.locator('.ui-probability-card:visible').count()==3
            assert 'not confidence intervals' in page.locator('#app').inner_text()
            page.get_by_role('button',name='Bowler view',exact=True).click()
            assert page.get_by_role('heading',name='Bowler-credited wicket',exact=True).count()==1
            assert len(calls)==1,'Perspective toggle must reuse one coherent distribution'
            assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth+2')
            page.screenshot(path=str(output/f'bowler-{width}.png'),full_page=True)
            page.get_by_role('button',name='Batter view',exact=True).click()
            assert page.get_by_role('heading',name='Six',exact=True).count()==1
            page.get_by_role('button',name='Death overs',exact=True).click()
            assert not page.get_by_role('heading',name='Next-attempt model probabilities',exact=True).count()
            page.get_by_role('button',name='Calculate scenario probabilities',exact=True).click()
            page.get_by_role('heading',name='Next-attempt model probabilities',exact=True).wait_for()
            assert len(calls)==2
            page.screenshot(path=str(output/f'batter-{width}.png'),full_page=True)
            assert not errors,errors
            cases.append({'width':width,'passed':True,'typed_ids':False,'scenario_calls':len(calls),
                'perspective_uses_shared_distribution':True,'changed_context_clears_previous_result':True,'errors':errors})
            page.close()
        browser.close()
    args.report.write_text(json.dumps({'cases':cases,'limits':'Local Chrome and hypothetical model only; no live source/promotion/psychology validation.'},indent=2)+'\n',encoding='utf-8')
    print('Scenario UI checks passed')


if __name__=='__main__':main()
