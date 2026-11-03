"""Compare highlighted-only insets and unchanged row geometry against prior source."""
import subprocess,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from section_visibility_fixture import expand_recipe_sections
import promotion_schedule_browser as f
f.EXTRA+='''window.paddingTest={manual:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()}};'''
ROOT=Path(__file__).resolve().parents[1]
def snapshot(b,name,width,tabs,manual):
 c,p,e,prefix=f.setup(b,name,width,'cross-group',tabs);p.evaluate('paddingTest.manual',manual);p.evaluate('promotionTest.groups()');expand_recipe_sections(p)
 def data(selector):return p.locator(selector).evaluate_all('''rows=>rows.map(e=>{const s=getComputedStyle(e),r=e.getBoundingClientRect();return {id:e.dataset.mealId,h:r.height,color:s.backgroundColor,radius:s.borderRadius,top:s.paddingTop,bottom:s.paddingBottom,left:s.paddingLeft,right:s.paddingRight,border:s.borderBottomWidth,days:e.querySelector('.master-meal-weekdays')?.textContent||'',dayRight:e.querySelector('.master-meal-weekdays')?getComputedStyle(e.querySelector('.master-meal-weekdays')).marginRight:null}})''')
 group=data('#list .master-category-meal');p.evaluate("promotionTest.chooser('Saturday','Weekend')");chooser=data('.weekday-meal-choice');assert not e,e
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close();return group,chooser
if __name__=='__main__':
 with tempfile.TemporaryDirectory() as tmp,sync_playwright() as pw:
  for name in ['index.html','meal-rotation-test.html']:Path(tmp,name).write_text(subprocess.check_output(['git','show','HEAD:'+name],cwd=ROOT,text=True))
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [False,True]:
     for manual in [False,True]:
      f.ROOT=Path(tmp);old=snapshot(b,name,width,tabs,manual);f.ROOT=ROOT;new=snapshot(b,name,width,tabs,manual)
      for section,(prior,current) in enumerate(zip(old,new)):
       assert len(prior)==len(current)
       for a,z in zip(prior,current):
        expected='13px' if z['days'] else ('0px' if section==0 else '8px')
        assert z['left']==expected,(section,z)
        assert {k:v for k,v in a.items() if k!='left'}=={k:v for k,v in z.items() if k!='left'},(section,a,z)
      print('PASS',name,width,'tabs',tabs,'manual',manual,'highlighted left inset only; same unhighlighted padding, heights, colors, rounding, borders and weekday right inset',flush=True)
  b.close()
