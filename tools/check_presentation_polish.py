"""Exercise T041B against the configured local preview; no external traffic."""
import json
from urllib.parse import urlencode, urlsplit, urljoin

from criclytics_app.paths import PROJECT_ROOT


def main():
    from playwright.sync_api import sync_playwright
    base = 'http://127.0.0.1:5050'
    output = PROJECT_ROOT/'build/t041b-browser'
    output.mkdir(parents=True, exist_ok=True)
    cases = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel='chrome', headless=True)
        try:
            for width in (375,1440):
                context = browser.new_context(viewport={'width':width,'height':900})
                context.route('**/*',lambda route: route.continue_() if route.request.url.startswith(base+'/') else route.abort())
                # Keep this presentation audit out of private issued-forecast writes.
                context.route('**/api/v1/workspaces',lambda route: route.fulfill(json={'workspaces':[]}))
                page = context.new_page()
                errors = []
                page.on('pageerror',lambda error: errors.append(str(error)))
                def visit(path):
                    page.goto(base+'/'+path,wait_until='networkidle')
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth + 2'), path
                def click_surface(card, selector):
                    destination=urljoin(base+'/',card.locator('.ui-card-primary').get_attribute('href'))
                    card.locator(selector).first.scroll_into_view_if_needed()
                    box = card.locator(selector).first.bounding_box()
                    page.mouse.click(box['x']+box['width']/2,box['y']+box['height']/2)
                    page.wait_for_url(destination)
                    page.wait_for_load_state('networkidle')
                visit('index.html')
                assert page.locator('.ui-hero .ui-coverage').count()==0
                assert 'Experimental' not in page.locator('.ui-hero').inner_text()
                footer=page.locator('.ui-footer')
                for href in ('about.html','data-sources.html','disclaimer.html','https://kryzect.vercel.app/'):
                    assert footer.locator('a[href="'+href+'"]').count()==1
                assert footer.locator('.ui-coverage').count()==1
                footer.screenshot(path=str(output/f'footer-{width}.png'))
                cases.append({'width':width,'check':'footer links, ownership, coverage and home heading','passed':True})
                visit('players.html')
                card=page.locator('.ui-player-card').first
                expected=card.locator('.ui-card-primary').get_attribute('href')
                click_surface(card,'.ui-card-stats')
                assert urlsplit(page.url).path.endswith('player-profile.html')
                assert urlsplit(page.url).query==urlsplit(expected).query
                page.get_by_role('tab',name='ML Insights',exact=True).click()
                page.get_by_text('The story behind next-ball estimates',exact=True).wait_for()
                text=page.get_by_role('tabpanel',name='ML Insights',exact=True).inner_text()
                for raw in ('held-out','SHA-256','189,168','log loss'):
                    assert raw not in text, raw
                cases.append({'width':width,'check':'player card surface and plain-language ML insights','passed':True})
                for listing,profile in (('teams','team-profile'),('venues','venue-profile')):
                    visit(listing+'.html')
                    click_surface(page.locator('.ui-click-card').first,'small')
                    assert urlsplit(page.url).path.endswith(profile+'.html')
                visit('matches.html')
                click_surface(page.locator('.ui-match-card').first,'.ui-match-venue')
                assert urlsplit(page.url).path.endswith(('match-detail.html','match-upcoming.html'))
                cases.append({'width':width,'check':'team, venue and match card surfaces','passed':True})
                visit('players.html')
                page.locator('.ui-card-actions a').first.click()
                page.wait_for_url('**/compare.html?**')
                visit('compare.html?'+urlencode({'a':'V Kohli','b':'Babar Azam'}))
                page.locator('.ui-player-probabilities').nth(1).wait_for()
                labels=page.locator('.ui-player-probabilities h2').all_text_contents()
                assert len(set(labels))==2 and all('Probability insights' in label for label in labels)
                assert any('Kohli' in label for label in labels) and any('Babar' in label for label in labels)
                cases.append({'width':width,'check':'secondary compare action and named probability panels','passed':True})
                visit('search.html?q=Kohli')
                assert page.locator('#app table').count()>0
                assert 'No records available' not in page.locator('#app').inner_text()
                visit('search.html?q=zzzz_no_cricket_result_zzzz')
                assert page.locator('#app .ui-state').count()==1
                assert 'No results found' in page.locator('#app').inner_text()
                cases.append({'width':width,'check':'populated search and single genuine empty state','passed':True})
                visit('scouting.html')
                buttons=page.locator('.ui-scouting-actions button')
                a,b=buttons.nth(0).bounding_box(),buttons.nth(1).bounding_box()
                assert b['x']>=a['x']+a['width']+8 or b['y']>=a['y']+a['height']+8
                cases.append({'width':width,'check':'scouting export action spacing','passed':True})
                visit('workspace.html?view=scenario')
                selectors=page.locator('.ui-scenario-selectors .ui-picker')
                selectors.nth(0).locator('.ui-picker-option').first.click()
                first_id=selectors.nth(0).locator('.ui-picker-option[aria-pressed="true"]').get_attribute('data-key')
                options=selectors.nth(1).locator('.ui-picker-option')
                for i in range(options.count()):
                    if options.nth(i).get_attribute('data-key')!=first_id:
                        options.nth(i).click()
                        break
                selectors.nth(2).locator('.ui-picker-option').first.click()
                page.get_by_role('button',name='Calculate scenario probabilities',exact=True).click()
                page.get_by_text('Next-attempt model probabilities',exact=True).wait_for()
                joint=page.locator('details').filter(has=page.locator('summary')).filter(has_text='Full coherent joint distribution')
                joint.locator('summary').click()
                text=joint.inner_text()
                assert 'batter_runs' not in text and '"extras"' not in text
                assert 'Dot ball' in text
                cases.append({'width':width,'check':'actual scenario calculation with readable delivery outcomes','passed':True})
                page.screenshot(path=str(output/f'scenario-{width}.png'),full_page=True)
                assert not errors,errors
                context.close()
        finally:
            browser.close()
    (output/'results.json').write_text(json.dumps(cases,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'checks':len(cases),'passed':True}))


if __name__=='__main__':
    main()
