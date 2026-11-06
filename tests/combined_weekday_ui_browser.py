"""Focused Android-style row dragging, empty-state safety, menus and keyboard geometry."""
from playwright.sync_api import sync_playwright
import compact_meal_options_browser as k
f=k.f
f.EXTRA+='''window.combinedTest={
 seed:()=>compactTest.seed(),
 stable:()=>JSON.stringify({meals,assignments:weekdayCategories,overrides:weekdayMealOverrides,choices:mealPlans.map(p=>p.cycleSlotChoices)}),
 rows:()=>[...document.querySelectorAll('[data-week-row][data-schedule-day="Saturday"]')].map(e=>JSON.parse(e.dataset.displayKey)[0]),
 bread:()=>{compactTest.seed();cats.push('Bread');meals.push({id:7,cat:'Bread',name:'Garlic Bread',rotation:false,keepAsIdea:true,ingredients:[]});meals.find(m=>m.id===2).linkedMealIds=[7];setDayCategories('Sunday',['Weekend']);persist();renderList()},
 whole:()=>leaveWeekEmpty('Sunday',null,true),
 legacy:()=>{editableWeekSchedule(mealPlans.find(p=>p.id===activePlanId)).slots['Sunday::Bread']={kind:'empty'};saveActiveMealPlan();renderList()},
 individual:()=>leaveWeekEmpty('Saturday','Breakfast'),
 slots:()=>weekSchedule(mealPlans.find(p=>p.id===activePlanId)).slots,
 viewport:()=>{const v=new EventTarget();Object.assign(v,{width:innerWidth,height:innerHeight,offsetTop:0,offsetLeft:0});Object.defineProperty(window,'visualViewport',{configurable:true,value:v})},
 resize:(height,top)=>{Object.assign(visualViewport,{height,offsetTop:top});visualViewport.dispatchEvent(new Event('resize'))},
 editor:()=>openOneTimeMealEditor('Saturday','Breakfast'),
 edit:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Breakfast');openOneTimeMealEditor(x.day,x.cat,x.meal)}
};'''

def touch(session,kind,x,y):
 session.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y}]})

def drag(p,session,source,target):
 p.locator('.weekday-heading[data-weekday=Saturday]').evaluate('(e)=>e.scrollIntoView({block:"start"})')
 a=source.bounding_box();b=target.bounding_box();x=a['x']+min(20,a['width']/2);y=a['y']+a['height']/2
 touch(session,'touchStart',x,y);p.wait_for_timeout(620)
 touch(session,'touchMove',x,b['y']+3);touch(session,'touchEnd',x,b['y']+3);p.wait_for_timeout(60)

def run(browser,name,width):
 c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('combinedTest.seed()');session=c.new_cdp_session(p)
 before=p.evaluate('combinedTest.stable()')
 drag(p,session,p.locator('.empty-weekday-meal[data-category=Lunch] .top-meal-inline-category'),p.locator('[data-week-row][data-schedule-day=Saturday]').first)
 assert p.evaluate('combinedTest.rows()')==['Lunch','Weekend','Breakfast']
 assert p.evaluate('combinedTest.stable()')==before
 p.reload();p.evaluate('promotionTest.my()');assert p.evaluate('combinedTest.rows()')==['Lunch','Weekend','Breakfast']
 # Intentionally empty rows also participate; dragging a regular group label works.
 p.evaluate('combinedTest.individual()');before=p.evaluate('combinedTest.stable()')
 drag(p,session,p.locator('.top-recipe-wrap[data-schedule-day=Saturday] .top-meal-inline-category'),p.locator('.empty-weekday-meal[data-category=Lunch]'))
 assert p.evaluate('combinedTest.rows()')==['Weekend','Lunch','Breakfast'];assert p.evaluate('combinedTest.stable()')==before
 for row in p.locator('.empty-weekday-meal').all():assert row.locator('.mealname').text_content()=='—'
 tail=p.locator('[data-week-row][data-schedule-day=Saturday]').last
 assert tail.evaluate('(e)=>getComputedStyle(e).borderBottomRightRadius')=='8px'
 assert tail.evaluate('(e)=>getComputedStyle(e).borderBottomLeftRadius')=='8px'
 heading=p.locator('.weekday-heading[data-weekday=Saturday]');assert heading.evaluate('(e)=>getComputedStyle(e).borderTopLeftRadius')=='8px'
 # Tap empty-row whitespace, not its dash, to open the appropriate menu.
 blank=p.locator('.empty-weekday-meal[data-category=Lunch]');b=blank.bounding_box();p.touchscreen.tap(b['x']+b['width']/2,b['y']+b['height']/2)
 d=p.get_by_role('dialog',name='Empty group options',exact=True);assert d.get_by_role('button',name='Select Meal',exact=True).count()==1
 assert not d.get_by_role('button',name='Add One-Time Meal',exact=True).count();d.get_by_role('button',name='Close',exact=True).tap()
 p.locator('.empty-weekday-meal[data-schedule-day=Monday]').tap();d=p.get_by_role('dialog',name="Plan Monday's meal",exact=True)
 assert d.get_by_role('button').all_text_contents()[1:]==['Select Meal','Choose Meal Groups']
 for b in d.locator('.smallbtn').all():assert b.evaluate('(e)=>getComputedStyle(e).textAlign')=='center'
 d.get_by_role('button',name='Close',exact=True).tap()
 # Header icon creates/selects a group without an extra full-width button or resume.
 p.evaluate('groupPickerTest.open()');d=p.get_by_role('dialog',name="Choose Saturday's meal groups",exact=True)
 plus=d.get_by_role('button',name='Create New Group',exact=True);assert plus.locator('svg').count()==1 and not plus.text_content()
 assert not d.get_by_role('button',name='Resume planned meals',exact=True).count()
 assert plus.bounding_box()['x']<d.get_by_role('button',name='Close',exact=True).bounding_box()['x']
 plus.tap();prompt=p.get_by_role('dialog').filter(has_text='New group name');prompt.get_by_role('textbox').fill('Quick meals');prompt.get_by_role('button',name='Save',exact=True).tap()
 assert d.locator('input[value="Quick meals"]').is_checked();d.get_by_role('button',name='Close',exact=True).tap()
 p.reload();p.evaluate('promotionTest.my()');assert 'Quick meals' in p.evaluate('groupPickerTest.assigned()')
 # Legacy whole-day conversion never materializes linked-only groups as assigned empty rows.
 p.evaluate('combinedTest.bread()');before=p.evaluate('combinedTest.stable()');p.evaluate('combinedTest.whole()')
 assert 'Sunday::Bread' not in p.evaluate('combinedTest.slots()')
 assert p.evaluate('combinedTest.stable()')==before
 p.evaluate('combinedTest.legacy()');assert not p.locator('.empty-weekday-meal[data-schedule-day=Sunday][data-category=Bread]').count()
 p.reload();p.evaluate('promotionTest.my()');assert not p.locator('.empty-weekday-meal[data-schedule-day=Sunday][data-category=Bread]').count()
 assert 'Sunday::Bread' in p.evaluate('combinedTest.slots()'),'Legacy data was deleted'
 p.evaluate('compactTest.validate()')
 # Muted compact quick actions, centered buttons, existing one-time editing.
 p.evaluate("compactTest.menu('Weekend')");d=p.get_by_role('dialog',name='Meal options for Saturday',exact=True)
 for b in d.locator('.meal-quick-actions button').all():
  assert b.evaluate('(e)=>getComputedStyle(e).textDecorationLine')=='none'
  assert b.evaluate('(e)=>getComputedStyle(e).color')=='rgb(112, 119, 130)'
 for b in d.locator('.meal-full-action').all():assert b.evaluate('(e)=>getComputedStyle(e).textAlign')=='center'
 assert not d.get_by_role('button',name='Leave Entire Day Empty This Week',exact=True).count();d.get_by_role('button',name='Close meal options',exact=True).tap()
 # Emulate visual-viewport keyboard shrink/restore, including scrolled action buttons.
 p.evaluate('combinedTest.viewport();combinedTest.editor();combinedTest.resize(300,30)');p.wait_for_timeout(80)
 editor=p.get_by_role('dialog',name='Add One-Time Meal',exact=True);box=editor.bounding_box();assert box['y']>=30 and box['y']+box['height']<=330
 editor.get_by_role('textbox',name='One-time meal name',exact=True).fill('Fish sticks')
 editor.get_by_role('textbox',name='Optional grocery items with quantities',exact=True).fill('1 bag fish sticks')
 save=editor.get_by_role('button',name='Save one-time meal',exact=True);save.scroll_into_view_if_needed();b=save.bounding_box();assert b['y']>=30 and b['y']+b['height']<=330
 p.evaluate('combinedTest.resize(800,0)');p.wait_for_timeout(60);assert editor.bounding_box()['height']>box['height'];save.tap()
 p.evaluate('combinedTest.edit();combinedTest.resize(280,0)');editor=p.get_by_role('dialog',name='Edit one-time meal',exact=True);cancel=editor.get_by_role('button',name='Cancel',exact=True);cancel.scroll_into_view_if_needed();cancel.tap()
 assert not p.get_by_role('dialog').count();assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'mixed/empty group label drag and reload, display-only state, dash/whole-row tap, corners, icon creation, legacy linked empties, compact styling, keyboard geometry, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
