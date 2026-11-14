"""Focused rotation/interface checks in disposable contexts for both existing apps."""
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as f
f.HOOK+='''window.interfaceTest={
 tabs:value=>{showTop=true;showMealPlanTabs=value;render()},
 order:start=>{startWeekday=start;const plan={id:'order-test',weekdayCategories:{Monday:['Meals'],Tuesday:['Reference'],Wednesday:['Other']},weekdayMealOverrides:{}};return {days:orderedDays(),entries:displayedRotationSelectionEntries(plan).map(e=>({day:e.day,empty:e.emptyAssigned}))}},
 complete:value=>{const item=scheduledMakeAheadTasks()[0];setMakeAheadComplete(item,value);return scheduledMakeAheadTasks().map(x=>({key:x.key,due:x.due,scheduled:x.scheduled,complete:x.complete}))},
 prep:()=>{const item=scheduledMakeAheadTasks()[0];return {before:JSON.stringify(item),text:makeAheadReminderRow(item,true).textContent,after:JSON.stringify(item)}},
 groups:()=>chooseBulkGroups(null,change=>window.pendingGroupChange=change),
 many:()=>{for(let n=0;n<75;n++)cats.push('Destination '+n);recipeBulkSourceGroup='Meals';chooseBulkGroups(null,change=>window.pendingGroupChange=change)},
 unassigned:()=>{recipeBulkSourceGroup='';chooseBulkGroups(null,()=>{})},
 selected:()=>[...recipeBulkIds],raw:()=>JSON.stringify({meals,mealPlans}),
 task:()=>makeAheadTaskDescription({task:{description:'Defrost steak'},entry:{day:'Friday',meal:{name:'Carne Asada'}},plan:mealPlans[0],scheduled:cookingLocalDate(new Date())})
};'''
def run(b,name):
 c,p,errors,prefix=f.setup(b,name,320)
 pin=f.row(p,2).get_by_role('button',name='Unpin recipe',exact=True);assert pin.locator('svg').get_attribute('fill')=='currentColor';assert pin.get_attribute('title')=='Unpin recipe';assert f.row(p,4).get_by_role('button',name='Pin recipe',exact=True).locator('svg').get_attribute('fill')=='none';p.screenshot(path='/tmp/interface-pins-'+name+'.png')
 for start in ['Monday','Saturday']:
  result=p.evaluate('s=>interfaceTest.order(s)',start);days=result['days'];entries=result['entries'];assert [days.index(e['day']) for e in entries]==sorted(days.index(e['day']) for e in entries);assert any(e['day']=='Tuesday' and e.get('empty') for e in entries)
 assert p.evaluate('interfaceTest.task()')=='Defrost steak for Friday’s dinner'
 prep=p.evaluate('interfaceTest.prep()');assert prep['before']==prep['after'] and ' · ' not in prep['text'] and 'dinner' in prep['text'] and 'meal tab' not in prep['text']
 before_dates=p.evaluate('interfaceTest.complete(false)');checked=p.evaluate('interfaceTest.complete(true)');assert checked[0]['complete'];assert [{k:v for k,v in x.items() if k!='complete'} for x in before_dates]==[{k:v for k,v in x.items() if k!='complete'} for x in checked];p.evaluate('interfaceTest.complete(false)')
 for visible in [True,False]:
  p.evaluate('v=>interfaceTest.tabs(v)',visible)
  assert p.locator('.meal-plan-add').count()==int(visible)
  assert not p.locator('[data-add-meal-tab]').count()
  if visible:
   p.locator('.meal-plan-add').tap();assert p.get_by_role('dialog',name='Add Meal Tab',exact=True).count();p.get_by_role('dialog',name='Add Meal Tab',exact=True).get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('interfaceTest.tabs(true)');p.locator('#settings').tap();p.locator('[data-settings-group=display]>summary').tap();tabs=p.get_by_role('checkbox',name='Show meal tabs',exact=True);tabs.uncheck();assert not p.locator('.meal-plan-add').count();tabs.check();assert p.locator('.meal-plan-add').count()==1
 p.evaluate('batch1.groups()');before=f.get(p,'records()');p.evaluate('batch1.select([2,3])')
 outer=p.get_by_role('dialog',name='Edit recipes',exact=True)
 assert outer.locator('.recipe-bulk-picker').count()==2
 assert outer.locator('.recipe-bulk-picker').first.evaluate('(e)=>getComputedStyle(e,"::after").borderRightStyle')=='solid'
 outer.get_by_role('button',name='Meal groups',exact=True).tap();d=p.get_by_role('dialog',name='Meal groups',exact=True)
 assert d.locator('.bulk-group-actions label').all_text_contents()==['Remove from Meals','Add to groups']
 d.get_by_role('checkbox',name='Remove from Meals',exact=True).check();assert not d.get_by_role('checkbox',name='Add to groups',exact=True).is_checked()
 d.get_by_role('checkbox',name='Add to groups',exact=True).check();assert d.get_by_role('button',name='Confirm meal groups',exact=True).is_disabled()
 d.get_by_role('button',name='New group',exact=True).tap();d.get_by_role('textbox',name='New group',exact=True).fill('Pending destination');d.get_by_role('button',name='Create group',exact=True).tap()
 assert d.get_by_role('checkbox',name='Pending destination',exact=True).is_checked()
 d.get_by_role('button',name='Confirm meal groups',exact=True).tap();assert f.get(p,'records()')==before
 outer.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert f.get(p,'records()')==before
 # Commit a pending group only at the outer confirmation.
 p.evaluate('batch1.select([2,3])');outer=p.get_by_role('dialog',name='Edit recipes',exact=True);outer.get_by_role('button',name='Meal groups',exact=True).tap();d=p.get_by_role('dialog',name='Meal groups',exact=True)
 d.get_by_role('checkbox',name='Add to groups',exact=True).check();d.get_by_role('button',name='New group',exact=True).tap();d.get_by_role('textbox',name='New group',exact=True).fill('Saved destination');d.get_by_role('button',name='Create group',exact=True).tap();d.get_by_role('button',name='Confirm meal groups',exact=True).tap();outer.get_by_role('button',name='Apply to selected recipes',exact=True).tap()
 assert len([m for m in f.get(p,'records()') if m['cat']=='Saved destination'])==2
 p.evaluate('interfaceTest.unassigned()');d=p.get_by_role('dialog',name='Meal groups',exact=True);assert d.locator('.bulk-group-actions label').all_text_contents()==['Add to groups'];d.get_by_role('button',name='Cancel meal groups',exact=True).tap()
 for w,h in [(320,800),(360,420),(740,360)]:
  p.set_viewport_size({'width':w,'height':h});p.evaluate('interfaceTest.many()');d=p.get_by_role('dialog',name='Meal groups',exact=True);d.get_by_role('checkbox',name='Add to groups',exact=True).check();scroll=d.locator('.bulk-group-destinations');assert scroll.evaluate('(e)=>e.scrollHeight>e.clientHeight');before=d.locator('.bulk-group-actions').bounding_box();scroll.evaluate('(e)=>e.scrollTop=e.scrollHeight');assert before==d.locator('.bulk-group-actions').bounding_box()
  for loc in [d.locator('strong'),d.locator('.bulk-group-actions'),d.get_by_role('button',name='Confirm meal groups',exact=True)]:
   box=loc.bounding_box();assert box['y']>=0 and box['y']+box['height']<=h,(w,h,box)
  assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.screenshot(path='/tmp/interface-bulk-'+name+'-'+str(w)+'.png');d.get_by_role('button',name='Cancel meal groups',exact=True).tap()
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close();print('PASS',name,'weekday order/empty day, task wording/identity, add-tab access, bulk order/validation/staging/save/cancel, mobile/keyboard scrolling',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
