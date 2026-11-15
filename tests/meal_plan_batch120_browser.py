"""Issue #120: disposable browser checks for both existing storage namespaces."""
import json
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as base
base.HOOK+='''window.plan120={
 historyLength:()=>history.length,dialog:(all=false)=>openRotateOptions(all),emptyPlan:()=>{const plan=mealPlans.find(p=>p.id===activePlanId);weekdayCategories={};weekdayMealOverrides={};plan.weekdayCategories={};plan.weekdayMealOverrides={};plan.occasionalMeals={};plan.weekSchedule={version:1,slots:{},order:{}};plan.cycleRetainedSlots={};plan.cycleSlotChoices={}},
 home:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;render()},
 tabs:value=>{showMealPlanTabs=value;renderList({readOnly:true})},
 raw:()=>JSON.stringify(Object.fromEntries(Array.from({length:localStorage.length},(_,i)=>{const key=localStorage.key(i);return [key,localStorage.getItem(key)]}).filter(([key])=>key!=='mealRotationRecipeViewPrefsV1'))),
 state:()=>JSON.stringify({meals,mealPlans,sessions:cookingSessions,scales:occurrenceScales,manual:manualGroceryItems(),grocery:groceryOccurrenceChecks,checked:[...checkedIngredients]}),
 seed:()=>{meals.push({id:70,cat:'Meals',name:'Next recipe',rotation:true,ingredients:['2 cups beans'],instructions:['Cook beans.']});meals.push({id:71,cat:'Meals',name:'Retained Wednesday',rotation:true,ingredients:['rice'],instructions:['Cook.']},{id:72,cat:'Meals',name:'Another alternative',rotation:true,ingredients:['beans'],instructions:['Cook.']});weekdayCategories.Wednesday=['Meals'];weekdayMealOverrides['Wednesday::Meals']='71';showMealPlanTabs=true;saveActiveMealPlan();batch1.seedProgress();const task=scheduledMakeAheadTasks()[0];if(task)setMakeAheadComplete(task,true);saveManualGroceryItems([{id:'done',text:'Done grocery',checked:true},{id:'keep',text:'Keep grocery',checked:false}]);render()},
 viewer:()=>openSavedMealRecipe(meals.find(m=>m.id===1)),awake:()=>({enabled:recipeViewPrefs.keepScreenAwake,wake:!!recipeViewer?.wake}),
 bulk:value=>document.body.classList.toggle('recipe-bulk-select',value),
 longSlots:()=>{mealPlans.push({id:'long',name:'Extra long custom meal slot for Sunday dessert',weekdayCategories:{},weekdayMealOverrides:{}});renderList({readOnly:true})}
};'''

def assert_state(actual,expected):
 a,b=json.loads(actual),json.loads(expected)
 if a!=b:
  for key in b:
   if a.get(key)!=b[key]:print('DIFF',key,json.dumps(b[key]),json.dumps(a.get(key)),flush=True)
 assert a==b

def run(browser,name):
 c,p,errors,prefix=base.setup(browser,name,360)
 p.clock.set_fixed_time(datetime(2026,11,15,12,tzinfo=timezone.utc))
 p.evaluate('plan120.home()');p.evaluate('plan120.seed()')
 assert p.get_by_role('heading',name='My Meal Plan',exact=True).count()==1
 assert p.locator('#mealBottomNav button').all_text_contents()==['Meals','Week','Groceries','Meal Groups']
 assert not p.get_by_role('button',name='Rotate Back',exact=True).count()
 assert p.get_by_role('button',name='Next week',exact=True).count()==1
 # Preview tabs never persist or consume scheduling, progress or grocery state.
 before=p.evaluate('plan120.raw()')
 p.get_by_role('button',name='Next week',exact=True).tap()
 preview=p.locator('.all-meals-day').first.get_attribute('data-date')
 assert p.evaluate('plan120.raw()')==before
 p.get_by_role('button',name='This week',exact=True).tap()
 assert p.evaluate('plan120.raw()')==before
 dates=p.locator('.weekday-date');assert dates.count()==7 and all(' · ' in text for text in dates.all_text_contents())
 assert preview=='2026-11-16';assert p.locator('.weekday-date').first.text_content()==' · Nov 9'
 # Compact card exposes the existing direct operations, no intermediate modal.
 toggle=p.get_by_role('button',name='Meal actions for Active',exact=True);toggle.tap()
 card=toggle.locator('xpath=ancestor::div[contains(@class,"mealbody")]').locator(':scope > .expanded-meal-actions')
 assert card.locator('.meal-inline-action').all_text_contents()==['Use next recipe','Choose a different meal','Leave this meal empty','Edit recipe','Edit groceries','Add or edit sides']
 assert card.locator('.meal-inline-action svg').evaluate_all('(xs)=>xs.every(x=>!x.innerHTML.includes("undefined"))')
 card.get_by_role('button',name='Choose a different meal',exact=True).tap()
 assert p.get_by_role('dialog',name="Choose Monday's meal",exact=True).is_visible()
 assert p.locator('#mealBottomNav').is_hidden()
 p.get_by_role('button',name='Cancel',exact=True).last.tap()
 assert p.locator('#mealBottomNav').is_visible()
 # Cancel and empty selection do not change anything, including cooked preference.
 baseline=p.evaluate('plan120.state()');raw=p.evaluate('plan120.raw()')
 p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True)
 assert d.get_by_text("Unselected meals will be reused in next week's meal plan.",exact=True).is_visible()
 assert d.locator('.start-week-checklist input').evaluate_all('(xs)=>xs.length>0&&xs.every(x=>x.checked)')
 assert p.locator('#mealBottomNav').is_hidden()
 d.get_by_role('checkbox',name='Mark replaced meals as cooked',exact=True).check();d.get_by_role('button',name='Close Start next week',exact=True).tap()
 assert p.evaluate('plan120.raw()')==raw
 p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True)
 d.locator('.start-week-checklist input').evaluate_all('(xs)=>xs.forEach(x=>x.checked=false)');d.get_by_role('button',name='Start next week →',exact=True).tap()
 assert p.evaluate('plan120.state()')==baseline
 # Replace only Monday; Wednesday is unchecked and carries forward. Undo/Redo includes
 # cooking progress/scales, cooked dates, reminder checks and checked manual cleanup.
 p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True)
 d.locator('.start-week-checklist input').evaluate_all('(xs)=>xs.forEach((x,i)=>x.checked=i===0)');d.get_by_role('checkbox',name='Mark replaced meals as cooked',exact=True).check()
 d.get_by_role('button',name='Start next week →',exact=True).tap()
 after=p.evaluate('plan120.state()');assert after!=baseline
 data=json.loads(after);assert [m['id'] for m in data['manual']]==['keep']
 assert any(m.get('lastCooked') for m in data['meals'] if m['id']==1)
 assert any(e[1]=='Friday' and e[3]==5 for e in base.get(p,'schedule()'));assert any(e[1]=='Wednesday' and e[3]==71 for e in base.get(p,'schedule()'))
 p.locator('#undo').tap();
 assert_state(p.evaluate('plan120.state()'),baseline)
 p.locator('#redo').tap();assert p.evaluate('plan120.state()')==after
 p.locator('#undo').tap()
 # The all-selected path uses the original whole-week operation exactly once.
 count=p.evaluate('plan120.historyLength()');p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True)
 d.get_by_role('button',name='Start next week →',exact=True).evaluate('(button)=>{button.click();button.click()}')
 assert p.evaluate('plan120.historyLength()')==count+1
 assert p.locator('.weekday-date').first.text_content()==' · Nov 16'
 p.locator('#undo').tap();assert_state(p.evaluate('plan120.state()'),baseline)
 # Hidden slots keep their identities/data and grocery scope; restore navigation.
 plans=base.get(p,'plans()');p.evaluate('plan120.tabs(false)')
 assert not p.locator('.meal-plan-tabs').count() and p.locator('#mealBottomNav button').all_text_contents()==['Meals','Groceries','Meal Groups']
 assert base.get(p,'plans()')==plans
 p.evaluate('plan120.tabs(true)');assert base.get(p,'plans()')==plans
 p.evaluate('plan120.longSlots()');bar=p.locator('.meal-plan-tabs');assert bar.evaluate('(x)=>x.scrollWidth>x.clientWidth')
 bar.evaluate('(x)=>x.scrollLeft=x.scrollWidth');assert p.locator('.meal-plan-add').bounding_box()['x']<360
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 # Nav stays fixed and yields to keyboard and group selection actions.
 p.evaluate('scrollTo(0,document.body.scrollHeight)');nav=p.locator('#mealBottomNav').bounding_box();assert nav['y']+nav['height']==800
 p.evaluate('plan120.bulk(true)');assert p.locator('#mealBottomNav').is_hidden();p.evaluate('plan120.bulk(false)')
 p.evaluate("const input=document.createElement('input');input.id='keyboardProbe';document.body.append(input);input.focus()")
 assert p.locator('#mealBottomNav').is_hidden();p.evaluate("document.getElementById('keyboardProbe').remove()")
 p.wait_for_function("!document.body.classList.contains('meal-keyboard-open')")
 # Legacy global choice migrates even without mode/ratio; no duplicate checkbox.
 p.evaluate('batch1.editor(1)');p.locator('#cancel').tap();p.evaluate('plan120.home()')
 p.locator('.mealname').filter(has_text='Active').first.tap()
 awake=p.locator('.recipe-keep-awake');assert awake.get_attribute('aria-pressed')=='false'
 assert not p.get_by_role('checkbox',name='Keep Screen Awake',exact=True).count()
 awake.tap();assert awake.get_attribute('aria-pressed')=='true';assert awake.get_attribute('data-state')=='unavailable'
 p.screenshot(path='/workspace/work/meal-plan-120-'+name+'.png')
 # Close the existing viewer through its standard close control.
 p.get_by_role('button',name='Close recipe',exact=True).tap()
 assert not p.locator('#recipeViewer').count()
 p.reload();p.wait_for_function('window.plan120!==undefined');p.evaluate('plan120.home()');assert p.evaluate('plan120.awake().enabled')
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert p.evaluate("localStorage.getItem('unrelated-sentinel')")=='keep'
 c.close();print('PASS',name,'preview, dates, direct actions, cancellation, carry-over, cooked/manual/progress Undo/Redo, slots/nav, wake preference, isolation',flush=True)

def wake_lifecycle(browser,name):
 c,p,errors,prefix=base.setup(browser,name)
 p.evaluate("""window.wakeProbe={requests:0,releases:0,locks:[]};Object.defineProperty(navigator,'wakeLock',{configurable:true,value:{request:async()=>{wakeProbe.requests++;if(wakeProbe.deny)throw Error('denied');if(wakeProbe.defer)await new Promise(resolve=>wakeProbe.resolve=resolve);const lock=new EventTarget();lock.released=false;lock.release=async()=>{if(lock.released)return;lock.released=true;wakeProbe.releases++;lock.dispatchEvent(new Event('release'))};wakeProbe.locks.push(lock);return lock}}});plan120.home();plan120.viewer()""")
 awake=p.locator('.recipe-keep-awake');assert awake.get_attribute('aria-pressed')=='false'
 awake.tap();p.wait_for_function("document.querySelector('.recipe-keep-awake').dataset.state==='active'")
 assert p.evaluate('wakeProbe.requests')==1
 p.evaluate("Object.defineProperty(document,'visibilityState',{configurable:true,value:'hidden'});document.dispatchEvent(new Event('visibilitychange'))")
 assert p.evaluate('wakeProbe.releases')==1 and awake.get_attribute('data-state')=='inactive'
 p.evaluate("Object.defineProperty(document,'visibilityState',{configurable:true,value:'visible'});document.dispatchEvent(new Event('visibilitychange'))")
 p.wait_for_function('wakeProbe.requests===2&&!!recipeViewer.wake') if name=='index.html' else p.wait_for_function("document.querySelector('.recipe-keep-awake').dataset.state==='active'")
 awake.tap();assert p.evaluate('wakeProbe.releases')==2 and awake.get_attribute('data-state')=='off'
 p.get_by_role('button',name='Close recipe',exact=True).tap();assert p.evaluate('wakeProbe.releases')==2
 p.evaluate('plan120.viewer();wakeProbe.deny=true')
 awake=p.locator('.recipe-keep-awake');assert p.evaluate('wakeProbe.requests')==2
 awake.tap();p.wait_for_function("document.querySelector('.recipe-keep-awake').dataset.state==='unavailable'")
 assert not awake.evaluate("x=>x.classList.contains('active')")
 awake.tap();p.evaluate('wakeProbe.deny=false;wakeProbe.defer=true');awake.tap();p.wait_for_function('!!wakeProbe.resolve')
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.evaluate('wakeProbe.resolve()');p.wait_for_function('wakeProbe.releases===3')
 assert not p.locator('#recipeViewer').count() and not errors,errors
 c.close();print('PASS',name,'supported, denied, hidden/foreground, off, close and pending wake-lock lifecycle',flush=True)

def direct_actions(browser,name):
 c,p,errors,prefix=base.setup(browser,name);p.evaluate('plan120.home();plan120.seed()')
 initial=p.evaluate('plan120.state()')
 def actions(title='Active'):
  toggle=p.get_by_role('button',name='Meal actions for '+title,exact=True)
  if toggle.get_attribute('aria-expanded')=='false':toggle.tap()
  return toggle.locator('xpath=..').locator('xpath=..').locator(':scope > .expanded-meal-actions')
 # Grocery and sides open their existing staged editors; cancel is read-only.
 actions().get_by_role('button',name='Edit groceries',exact=True).tap()
 assert p.get_by_role('dialog',name='Edit groceries',exact=True).is_visible() and p.locator('#mealBottomNav').is_hidden()
 p.get_by_role('dialog',name='Edit groceries',exact=True).get_by_role('button',name='Cancel',exact=True).tap()
 assert_state(p.evaluate('plan120.state()'),initial)
 actions().get_by_role('button',name='Add or edit sides',exact=True).tap()
 p.get_by_role('dialog',name='Sides for Active',exact=True).get_by_role('button',name='Close sides',exact=True).tap()
 assert_state(p.evaluate('plan120.state()'),initial)
 actions().get_by_role('button',name='Edit recipe',exact=True).tap();assert p.locator('#mealName').count() or p.locator('#name').count();p.locator('#cancel').tap()
 assert_state(p.evaluate('plan120.state()'),initial)
 actions().get_by_role('button',name='Use next recipe',exact=True).tap()
 assert not any(e[0]=='original' and e[1]=='Monday' and e[3]==1 for e in base.get(p,'schedule()'))
 p.locator('#undo').tap();assert_state(p.evaluate('plan120.state()'),initial)
 actions().get_by_role('button',name='Leave this meal empty',exact=True).tap()
 assert not any(e[0]=='original' and e[1]=='Monday' and e[3]==1 for e in base.get(p,'schedule()'))
 p.locator('.empty-weekday-meal[data-schedule-day=Monday]').tap()
 d=p.get_by_role('dialog',name='Empty meal options',exact=True);d.get_by_role('button',name='Resume planned meal',exact=True).tap()
 assert any(e[0]=='original' and e[1]=='Monday' and e[3]==1 for e in base.get(p,'schedule()'))
 # Linked side has its own chevron and chooser; no independent-group turn is invented.
 before=p.evaluate('plan120.state()')
 actions('Linked side').get_by_role('button',name='Choose a different meal',exact=True).tap()
 p.get_by_role('dialog',name="Choose Monday's meal",exact=True).get_by_role('button',name='Cancel',exact=True).tap()
 assert_state(p.evaluate('plan120.state()'),before)
 actions('Linked side').get_by_role('button',name='Use next recipe',exact=True).tap()
 assert p.get_by_text('This meal has no independent assigned group. Change the one-time meal or skip its parent meal instead.',exact=True).is_visible()
 p.get_by_role('button',name='OK',exact=True).tap();assert_state(p.evaluate('plan120.state()'),before)
 assert not errors,errors
 p.set_viewport_size({'width':320,'height':420});p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True)
 for control in [d.get_by_role('button',name='Close Start next week',exact=True),d.get_by_role('button',name='Start next week →',exact=True)]:
  box=control.bounding_box();assert box['y']>=0 and box['y']+box['height']<=420
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 d.get_by_role('button',name='Close Start next week',exact=True).tap()
 p.evaluate('plan120.emptyPlan()');raw=p.evaluate('plan120.raw()');p.evaluate('plan120.dialog()');d=p.get_by_role('dialog',name='Start next week',exact=True)
 assert d.get_by_role('button',name='Start next week →',exact=True).is_disabled()
 assert d.get_by_text('No scheduled meals are ready to replace.',exact=True).is_visible()
 d.get_by_role('button',name='Close Start next week',exact=True).tap();assert p.evaluate('plan120.raw()')==raw
 c.close();print('PASS',name,'six direct actions, staged cancellation, skip/empty/resume, linked protections and short viewport dialog',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   run(browser,name);wake_lifecycle(browser,name);direct_actions(browser,name)
  browser.close()
