"""Immediate weekday multi-group/filter saves with a compact, scrollable popup."""
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import state,definitions
fixture.HOOK+='''window.weekPopup={tabs:value=>{showMealPlanTabs=value;render();window.scrollTo(0,0)},many:()=>{for(let i=0;i<30;i++)cats.push('Extra accompaniment group '+i);persist();renderList()},labels:()=>{meals.find(m=>m.id===1).labels=['Fast','Weeknight'];persist()},filters:()=>weekdayRecipeFilters};'''
def dialog(p):return p.get_by_role('dialog',name='Select a group',exact=True)
def run(browser,filename,width,tabs,long):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,duplicate=True,multi=True);p.set_default_timeout(8000)
 if long:p.evaluate('weekPopup.many()')
 p.evaluate('weekPopup.labels()');p.evaluate('weekPopup.tabs',tabs);before=state(p);saved=p.evaluate('slotTest.storage()')
 h=p.locator('button.weekday-heading[data-weekday=Tuesday]');r=h.bounding_box();h.tap(position={'x':r['width']-5,'y':r['height']/2});d=dialog(p)
 assert d.get_by_role('heading').inner_text()=='Select a group'
 assert d.get_by_role('button').count()==1 and d.get_by_role('button',name='Close',exact=True).is_visible()
 assert d.get_by_role('button',name='Save meal groups').count()==0 and d.get_by_role('button',name='Cancel',exact=True).count()==0
 rice=d.locator('input[data-group-choice][value=Rice]');sides=d.locator('input[data-group-choice][value=Sides]');sauce=d.locator('input[data-group-choice][value=Sauces]')
 assert rice.is_checked() and sides.is_checked() and not sauce.is_checked()
 row=rice.locator('..').bounding_box();assert 36<=row['height']<44,row
 assert d.bounding_box()['height']<=520 and d.bounding_box()['width']<=width-30
 if long:
  body=d.locator('.weekday-group-picker-body');head=d.get_by_role('heading').bounding_box();close=d.get_by_role('button').bounding_box();r=body.bounding_box()
  cdp=ctx.new_cdp_session(p)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':r['x']+r['width']/2,'y':r['y']+r['height']-30}]})
  for i in range(1,9):cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':r['x']+r['width']/2,'y':r['y']+r['height']-30-i*25}]})
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(250)
  assert body.evaluate('(e)=>e.scrollTop')>0
  assert d.get_by_role('heading').bounding_box()==head and d.get_by_role('button').bounding_box()==close
  p.wait_for_timeout(600);body.evaluate('(e)=>e.scrollTop=0');p.wait_for_timeout(150)
 if filename.startswith('meal-') and width==360 and tabs:p.screenshot(path='/tmp/compact-group-popup-'+str(long)+'.png')
 d.get_by_role('button',name='Close',exact=True).tap();d.wait_for(state='detached');assert p.evaluate('slotTest.storage()')==saved
 h.tap();d=dialog(p);d.locator('input[data-group-choice][value=Sauces]').check()
 assert set(state(p)['plans'][0]['weekdayCategories']['Tuesday'])=={'Rice','Sides','Sauces'} and d.is_visible()
 d.get_by_role('checkbox',name='Fast',exact=True).check();assert p.evaluate('weekPopup.filters()')["Tuesday::Rice"]==['Fast']
 assert state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'];d.get_by_role('button',name='Close',exact=True).tap();p.reload();h=p.locator('button.weekday-heading[data-weekday=Tuesday]');h.tap();d=dialog(p)
 assert d.locator('input[data-group-choice][value=Sauces]').is_checked() and d.get_by_role('checkbox',name='Fast',exact=True).is_checked()
 d.locator('input[data-group-choice][value=Sides]').uncheck();assert set(state(p)['plans'][0]['weekdayCategories']['Tuesday'])=={'Rice','Sauces'}
 # Removing a group clears its filters using the existing setter; reselection stays possible.
 d.locator('input[data-group-choice][value=Rice]').uncheck();assert 'Tuesday::Rice' not in p.evaluate('weekPopup.filters()')
 d.locator('input[data-group-choice][value=Sauces]').uncheck();assert not d.locator('input[data-group-choice]:checked').count()
 d.get_by_role('button',name='Close',exact=True).tap();p.reload();h=p.locator('button.weekday-heading[data-weekday=Tuesday]');h.tap();d=dialog(p)
 assert not d.locator('input[data-group-choice]:checked').count()
 d.locator('input[data-group-choice][value=Rice]').check();d.locator('input[data-group-choice][value=Sides]').check();d.get_by_role('button',name='Close',exact=True).tap()
 after=state(p);assert definitions(before)==definitions(after) and before['plans'][1]==after['plans'][1]
 for field in ['sessions','scales']:
  for key,value in before[field]['occurrences'].items():
   if 'Friday' in key or 'lunch' in key:assert after[field]['occurrences'][key]==value,(field,key)
 assert before['prefs']==after['prefs']
 p.locator('.mealname').first.tap();menu=p.get_by_role('dialog',name='Meal options for Tuesday');assert menu.is_visible() and menu.get_by_role('button',name='Change meal',exact=True).is_visible();assert not dialog(p).count()
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors
 print('PASS',filename,width,tabs,long,'compact title/rows; X only; touch scroll; immediate groups/filters; close/reload/clear/re-add; links/progress/settings/storage isolation',flush=True);ctx.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [True,False]:
     for long in [False,True]:run(b,filename,width,tabs,long)
  b.close()
