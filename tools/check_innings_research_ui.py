from pathlib import Path
import argparse
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright
import json
parser=argparse.ArgumentParser(description='Local longer-horizon research UI audit')
parser.add_argument('--base',default='http://127.0.0.1:5050')
parser.add_argument('--report',type=Path,required=True)
args=parser.parse_args()
if urlsplit(args.base).hostname not in ('127.0.0.1','localhost','::1'):raise ValueError('Local preview only')
out=Path('build/t039-ui');out.mkdir(exist_ok=True)
cases=[]
with sync_playwright() as p:
 b=p.chromium.launch(channel='chrome',headless=True)
 for width in (375,1440):
  page=b.new_page(viewport={'width':width,'height':960});errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  page.goto(args.base+'/workspace.html',wait_until='networkidle')
  page.get_by_role('button',name='Model evidence',exact=True).click()
  page.get_by_role('heading',name='Innings & match research',exact=True).wait_for()
  page.get_by_text('Inspect longer-horizon evaluation',exact=True).click()
  assert page.locator('caption').filter(has_text='Terminal batter-score bins').is_visible()
  assert page.locator('caption').filter(has_text='Joint match result').is_visible()
  assert 'calibration worsened' in page.locator('#app').inner_text()
  assert page.evaluate('() => document.documentElement.scrollWidth <= innerWidth+2')
  assert not errors,errors
  page.screenshot(path=str(out/f'evidence-{width}.png'),full_page=True)
  cases.append({'width':width,'passed':True,'actual_evaluation_tables_visible':True,'no_promotion_claim':True,'errors':errors})
  page.close()
 b.close()
args.report.write_text(json.dumps({'cases':cases,'scope':'Local retrospective reports; no live forecasts or coach review.'},indent=2)+'\n',encoding='utf-8')
print('Innings research UI passed')
