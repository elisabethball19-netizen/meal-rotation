"""Weekday group popup layout and distinct heading/recipe actions; synthetic data."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import state,definitions
fixture.HOOK+='''window.weekPopup={tabs:value=>{showMealPlanTabs=value;render();window.scrollTo(0,0)},many:()=>{for(let i=0;i<30;i++)cats.push('Extra accompaniment group '+i);persist();renderList()},labels:()=>{meals.find(m=>m.id===1).labels=['Fast','Weeknight'];meals.find(m=>m.id===10).labels=['Mild'];persist()},filters:()=>weekdayRecipeFilters};'''
TITLE="Select a group for Tuesday's dinner"
def popup(p):return p.get_by_role('dialog',name=TITLE,exact=True)
def heading(p):return p.locator('button.weekday-heading[data-weekday=Tuesday]')
def storage(p):return p.evaluate('slotTest.storage()')

def run(browser,filename,width,tabs,long=False,height=800):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.set_default_timeout(8000);p.set_viewport_size({'width':width,'height':height})
 if long:p.evaluate('weekPopup.many()')
 p.evaluate('weekPopup.tabs',tabs);before=state(p);saved=storage(p)
 h=heading(p);rect=h.bounding_box();assert rect['height']>=44 and rect['width']>=width-35
 # Blank space near the right edge, not weekday text, opens only group selection.
 h.tap(position={'x':rect['width']-5,'y':3});d=popup(p);assert d.is_visible()
 assert p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).count()==0
 assert d.get_by_role('heading').inner_text()==TITLE
 close=d.get_by_role('button',name='Close',exact=True);cr=close.bounding_box();hr=d.get_by_role('heading').bounding_box();box=d.bounding_box()
 assert cr['width']>=44 and cr['height']>=44 and cr['x']>=hr['x']+hr['width']+9
 assert close.evaluate('e=>getComputedStyle(e).borderTopWidth')=='0px'
 assert close.evaluate('e=>getComputedStyle(e).backgroundColor')=='rgba(0, 0, 0, 0)'
 assert close.locator('svg').bounding_box()['width']==25
 assert box['height']<=min(height*.65,520)+1 and box['x']>=17 and box['x']+box['width']<=width-17
 assert d.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
 assert d.get_by_role('checkbox',name='Rice',exact=True).is_checked() and d.get_by_role('checkbox',name='Sides',exact=True).is_checked()
 assert not d.get_by_role('checkbox',name='Sauces',exact=True).is_checked()
 assert d.get_by_role('button',name='Change meal',exact=True).count()==0
 body=d.locator('.weekday-group-picker-body');footer=d.get_by_role('button',name='Save meal groups',exact=True).bounding_box()
 if long:
  assert body.evaluate('(e)=>e.scrollHeight>e.clientHeight+100')
  r=body.bounding_box();x=r['x']+r['width']*.7;y=r['y']+r['height']*.85;cdp=ctx.new_cdp_session(p)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for n in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y-r['height']*.65*n/8}]});p.wait_for_timeout(20)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(150);assert body.evaluate('(e)=>e.scrollTop')>0
  assert abs(close.bounding_box()['y']-cr['y'])<1 and abs(d.get_by_role('button',name='Save meal groups').bounding_box()['y']-footer['y'])<1
  last=d.locator('input[data-group-choice]').last;last.scroll_into_view_if_needed();lr=last.bounding_box();assert lr['y']+lr['height']<footer['y']
 else:assert body.evaluate('(e)=>e.scrollHeight<=e.clientHeight+1')
 if filename=='meal-rotation-test.html' and width==360 and tabs:p.screenshot(path='/tmp/weekday-group-popup-'+('long' if long else 'short')+'.png')
 close.tap(position={'x':3,'y':3});assert storage(p)==saved
 # Draft changes are discarded by the new close control just like the existing Cancel.
 h.tap(position={'x':3,'y':3});d=popup(p);d.get_by_role('checkbox',name='Rice',exact=True).uncheck();d.get_by_role('checkbox',name='Sauces',exact=True).check();d.get_by_role('button',name='Close',exact=True).tap();assert storage(p)==saved
 # Existing label-filter drafts and multiple group selections still save correctly.
 p.evaluate('weekPopup.labels()');baseline=state(p);saved=storage(p);h.tap();d=popup(p)
 d.get_by_role('checkbox',name='Fast',exact=True).check();d.get_by_role('button',name='Close',exact=True).tap();assert storage(p)==saved
 h.tap();d=popup(p);d.get_by_role('checkbox',name='Fast',exact=True).check();d.get_by_role('checkbox',name='Sauces',exact=True).check();d.get_by_role('button',name='Save meal groups',exact=True).tap()
 assert state(p)['plans'][0]['weekdayCategories']['Tuesday']==['Rice','Sides','Sauces']
 assert p.evaluate('weekPopup.filters()')['Tuesday::Rice']==['Fast']
 assert definitions(state(p))==definitions(baseline)
 assert state(p)['plans'][1]==baseline['plans'][1]
 for key,entry in baseline['sessions']['occurrences'].items():
  if entry['context']['day']=='Friday':assert state(p)['sessions']['occurrences'][key]==entry and state(p)['scales']['occurrences'][key]==baseline['scales']['occurrences'][key]
 # Keyboard activation opens a single popup, and clearing/re-adding groups remains possible.
 heading(p).focus();p.keyboard.press('Enter');assert popup(p).count()==1;popup(p).get_by_role('button',name='Cancel',exact=True).tap()
 heading(p).focus();p.keyboard.press('Space');assert popup(p).count()==1;d=popup(p)
 d.get_by_role('checkbox',name='Rice',exact=True).uncheck();d.get_by_role('checkbox',name='Sides',exact=True).uncheck();d.get_by_role('checkbox',name='Sauces',exact=True).uncheck();d.get_by_role('button',name='Save meal groups',exact=True).tap()
 heading(p).tap();d=popup(p);assert not d.locator('input[data-group-choice]:checked').count();d.get_by_role('checkbox',name='Rice',exact=True).check();d.get_by_role('checkbox',name='Sides',exact=True).check();d.get_by_role('button',name='Save meal groups',exact=True).tap()
 p.reload();assert state(p)['plans'][0]['weekdayCategories']['Tuesday']==['Rice','Sides']
 # Recipe taps retain their own menu; Change meal opens the existing grouped chooser.
 p.locator('.mealname').filter(has_text='Thai Garlic Pork').first.tap();menu=p.get_by_role('dialog',name='Meal options for Tuesday',exact=True)
 assert menu.is_visible() and popup(p).count()==0
 assert menu.get_by_role('button',name='Change meal',exact=True).count()==1
 assert menu.get_by_role('button',name="Change Tuesday's meal",exact=True).count()==0
 assert menu.get_by_role('button',name='Save meal groups',exact=True).count()==0
 menu.get_by_role('button',name='Change meal',exact=True).tap();chooser=p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True);assert chooser.get_by_role('button',name='Search recipes').is_visible();chooser.get_by_role('button',name='Cancel',exact=True).tap()
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',filename,width,'tabs' if tabs else 'no tabs','long' if long else 'short','group list: full-area taps/keyboard, independent touch scroll, X/draft cancel, multiple groups/filters/save/reload/clear, separate recipe actions; no JS errors',flush=True)

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [True,False]:
     for long in [False,True]:run(b,filename,width,tabs,long)
  b.close()
