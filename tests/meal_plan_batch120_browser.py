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

base.HOOK+='''window.review120={
 seed:()=>{plan120.home();plan120.seed();const m=meals.find(m=>m.id===1);m.prep=10;m.total=40;m.marinate='2 hrs';m.lastCooked='2026-11-10T12:00:00.000Z';m.needsTweaking=true;m.needsTweakingNote='Less salt next time.';const saturday=meals.find(m=>m.id===70);saturday.name='Slow-Cooker Italian Beef Sandwiches';weekdayCategories.Saturday=['Meals'];weekdayMealOverrides['Saturday::Meals']='70';saveActiveMealPlan();persist();renderList()},
 prefs:value=>{timeDisplayPrefs.top.cooking=value;timeDisplayPrefs.top.marinate=value;showLastCooked=value;makeAheadDisplayPrefs.showMakeAheadReminders=value;renderList({readOnly:true})},
 groups:()=>mealPlans.map(p=>({id:p.id,name:p.name})),
 manage:id=>openMealSlotManager(id),longSlots:()=>{for(let n=0;n<7;n++)mealPlans.push({id:'custom'+n,name:'Extra long custom meal '+n,weekdayCategories:{},weekdayMealOverrides:{}});renderList({readOnly:true})},
 future:()=>{const plan=mealPlans.find(p=>p.id===activePlanId),key=rotationOccurrenceKey({...getDisplayedWeekdayMeals().find(e=>e.day==='Monday'),planId:plan.id});plan.rotationCalendar.occurrences[key]='2026-11-16';saveActiveMealPlan(false);renderList({readOnly:true})},
 mixed:()=>{meals.push({id:73,name:'Other alternative',cat:'Other',rotation:true,ingredients:['bread'],url:''});weekdayCategories.Tuesday=['Other'];weekdayMealOverrides['Tuesday::Other']='73';saveActiveMealPlan();const plan=mealPlans.find(p=>p.id===activePlanId);for(const [day,date]of [['Monday','2026-11-16'],['Tuesday','2026-11-17'],['Wednesday','2026-11-18'],['Saturday','2026-11-14']]){for(const e of getDisplayedWeekdayMeals().filter(e=>e.day===day)){const key=rotationOccurrenceKey({...e,planId:plan.id});plan.rotationCalendar.occurrences[key]=date;plan.rotationCalendar.assignedOn[key]='2026-11-09';plan.rotationCalendar.assignedAt[key]='2026-11-09T20:00:00.000Z'}}plan.rotationCalendar=rotationCalendarForPlan(plan,getDisplayedWeekdayMeals());saveActiveMealPlan(false);renderList({readOnly:true})},
 preview:slots=>previewMealPlanAdvance(slots?new Set(slots):null).entries.map(e=>[e.day,e.cat,String(e.meal.id),String(e.linkedTo||'')]),
 actual:()=>getDisplayedWeekdayMeals().map(e=>[e.day,e.cat,String(e.meal.id),String(e.linkedTo||'')]),
 partial:slots=>moveDisplayedMealsToBottom(new Set(slots)),
 viewer:id=>openSavedMealRecipe(meals.find(m=>m.id===id)),
 note:id=>{const m=meals.find(m=>m.id===id);m.needsTweaking=true;m.needsTweakingNote='Stable note '+id;persist()},
 longRecipe:()=>{const m=meals.find(m=>m.id===1);m.instructions=Array.from({length:24},(_,i)=>'Step '+(i+1)+': Mix the ingredients carefully and cook until tender.');persist()},
 scale:factor=>{mealTextSize=factor;applyMealTextSize()},
 aggregate:view=>{showTop=true;allMealsActive=view==='week';groceryTabActive=view==='grocery';render()},
 grocery:()=>JSON.stringify({checks:groceryOccurrenceChecks,selected:localStorage.getItem('mealRotationSelectedIngredientsV1'),excludedPlans:[...masterGroceryExcludedPlanIds],excludedMeals:[...masterGroceryExcludedMealKeys]}),
 independent:()=>{weekdayCategories.Monday=['Meals','Reference'];weekdayMealOverrides['Monday::Reference']='8';meals.find(m=>m.id===8).rotation=true;meals.find(m=>m.id===8).recipeStatus='rotation';saveActiveMealPlan();persist();renderList()},footer:()=>{const m=meals.find(m=>m.id===71);m.url='https://example.test/source';m.linkedMealIds=[8];openSavedMealRecipe(m)},
 overviewTask:()=>{meals.find(m=>m.id===14).makeAheadTasks=[{id:'defrost',description:'Defrost steak',daysBefore:0}];persist();overviewWeekOffset=1;showTop=true;allMealsActive=true;groceryTabActive=false;renderList({readOnly:true})},
 rawPrefs:()=>localStorage.getItem(RECIPE_VIEW_PREFS_KEY)
};'''

def setup_review(browser,name,width=360):
 c,p,errors,prefix=base.setup(browser,name,width);p.clock.set_fixed_time(datetime(2026,11,15,12,tzinfo=timezone.utc));p.evaluate('review120.seed()');return c,p,errors,prefix

def card(p,day='Monday'):
 return p.locator('.plan-meal-card[data-schedule-day="'+day+'"]').first

def expand(p,day='Monday'):
 row=card(p,day);button=row.locator(':scope>.meal-actions-toggle')
 if button.get_attribute('aria-expanded')=='false':button.tap()
 return row.locator('.expanded-meal-actions')

def layout_and_actions(browser,name):
 c,p,errors,prefix=setup_review(browser,name,320)
 title=p.get_by_role('heading',name='My Meal Plan',exact=True).bounding_box();tabs=p.locator('.meal-plan-tabs').bounding_box();controls=p.locator('.rotation-week-controls').bounding_box();first=card(p).bounding_box()
 assert title['y']<tabs['y']<controls['y']<first['y']
 controls=p.locator('.rotation-week-controls button').evaluate_all('(xs)=>xs.map(x=>{const b=x.getBoundingClientRect();return {x:b.x,y:b.y,r:b.right,w:b.width,h:b.height}})')
 assert len(controls)==3 and len(set(x['y'] for x in controls))==1 and all(x['h']>=44 and x['r']<=320 for x in controls)
 assert controls[0]['w']<100 and controls[1]['w']<100 and controls[2]['x']>=controls[1]['r']
 assert not p.locator('.plan-meal-card [data-recipe-favorite]:visible').count()
 assert not card(p).locator('.plan-linked-names .meal-actions-toggle').count()
 for row in p.locator('.plan-meal-card').all():
  box=row.bounding_box();stamp=row.locator('.plan-date').bounding_box();body=row.locator('.plan-card-content').bounding_box();arrow=row.locator(':scope>.meal-actions-toggle').bounding_box()
  assert body['x']>=stamp['x']+stamp['width'] and abs(body['y']-stamp['y'])<2
  assert arrow['x']>=body['x']+body['width']-6 and box['height']>=72
 assert card(p,'Saturday').locator('.mealname').inner_text()=='Slow-Cooker Italian Beef Sandwiches'
 p.screenshot(path='/workspace/work/review120/'+name+'-cards-320.png',full_page=True)
 empty=expand(p,'Tuesday');assert empty.locator('button').all_text_contents()==['Choose a meal'];empty.get_by_role('button',name='Choose a meal',exact=True).tap();p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True).get_by_role('button',name='Cancel',exact=True).tap()
 # Display off moves information into the expanded card; on does not duplicate it.
 p.evaluate('review120.prefs(false)');assert card(p).locator('.plan-detail:visible').count()==0
 panel=expand(p);assert card(p).locator('.plan-cooking-detail').is_visible() and card(p).locator('.plan-marinate-detail').is_visible()
 assert panel.locator('.meal-inline-action').all_text_contents()==['Use next recipe','Choose a different meal','Leave this meal empty','Edit recipe','Edit groceries','Add or edit sides']
 assert panel.locator('[data-recipe-favorite]').count()==1 and card(p).locator('.plan-cooked-detail').is_hidden()
 grid=panel.locator('.meal-action-group').bounding_box() if panel.locator('.meal-action-group').count()==1 else None
 groups=panel.locator('.meal-action-group').all();assert groups[0].bounding_box()['x']<groups[1].bounding_box()['x']
 for a,b in zip(groups[0].locator('button').all(),groups[1].locator('button').all()):assert abs(a.bounding_box()['y']-b.bounding_box()['y'])<2
 p.screenshot(path='/workspace/work/review120/'+name+'-expanded-320.png',full_page=True)
 baseline=p.evaluate('plan120.state()');panel.get_by_role('button',name='Choose a different meal',exact=True).tap();p.get_by_role('dialog',name="Choose Monday's meal",exact=True).get_by_role('button',name='Cancel',exact=True).tap();assert_state(p.evaluate('plan120.state()'),baseline)
 expand(p).get_by_role('button',name='Edit groceries',exact=True).tap();p.get_by_role('dialog',name='Edit groceries',exact=True).get_by_role('button',name='Cancel',exact=True).tap();assert_state(p.evaluate('plan120.state()'),baseline)
 expand(p).get_by_role('button',name='Add or edit sides',exact=True).tap();p.get_by_role('button',name='Close sides',exact=True).tap();assert_state(p.evaluate('plan120.state()'),baseline)
 expand(p).get_by_role('button',name='Edit recipe',exact=True).tap();p.locator('#cancel').tap();assert_state(p.evaluate('plan120.state()'),baseline)
 expand(p).get_by_role('button',name='Use next recipe',exact=True).tap();assert not any(e[0]=='Monday' and e[2]=='1' for e in p.evaluate('review120.actual()'));p.locator('#undo').tap();assert_state(p.evaluate('plan120.state()'),baseline)
 expand(p).get_by_role('button',name='Leave this meal empty',exact=True).tap();panel=expand(p)
 assert panel.locator('button').all_text_contents()==['Choose a meal','Resume planned meal'] and not p.get_by_role('dialog').count()
 p.screenshot(path='/workspace/work/review120/'+name+'-empty.png');panel.get_by_role('button',name='Resume planned meal',exact=True).tap()
 card(p).locator('.plan-linked-names button').tap();assert p.locator('#recipeViewer').is_visible();p.get_by_role('button',name='Close recipe',exact=True).tap()
 p.evaluate('review120.prefs(true)');panel=expand(p);assert card(p).locator('.plan-cooked-detail').is_hidden() and panel.locator('[data-recipe-favorite]').count()==1
 heart=panel.locator('[data-recipe-favorite]');heart.tap();assert expand(p).locator('[data-recipe-favorite]').get_attribute('aria-pressed')=='false'
 p.evaluate('review120.prefs(false)');p.locator('#settings').tap();p.locator('[data-settings-group=display]>summary').tap();assert p.get_by_text('Show on collapsed meal cards',exact=True).is_visible();assert p.get_by_role('switch',name='Show cooking times',exact=True).count()==1
 p.get_by_role('button',name='Cancel settings',exact=True).tap()
 p.evaluate('plan120.tabs(false)');assert not p.locator('.meal-plan-tabs').count() and p.locator('#mealBottomNav button').count()==3
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close();print('PASS',name,'mobile header/date/cards, details, two-column actions, one expanded heart, linked/empty actions and staged cancellation',flush=True)

def weeks_and_dialog(browser,name):
 c,p,errors,prefix=setup_review(browser,name)
 p.evaluate('review120.mixed()');before=p.evaluate('plan120.raw()');dates=p.locator('.plan-meal-card').evaluate_all('(xs)=>xs.map(x=>x.dataset.date)')
 assert dates[0]=='2026-11-16' and dates[1]=='2026-11-17' and dates[2]=='2026-11-18' and dates[3]=='2026-11-12' and dates[5]=='2026-11-14'
 predicted=p.evaluate('review120.preview()');p.get_by_role('button',name='Next week',exact=True).tap();assert p.evaluate('plan120.raw()')==before
 assert not p.locator('.plan-meal-card .meal-actions-toggle').count() and not p.locator('.meal-plan-title ~ .meal-plan-title').count()
 assert p.locator('.rotation-week-controls .start-week-text').is_visible()
 p.screenshot(path='/workspace/work/review120/'+name+'-preview.png',full_page=True)
 p.get_by_role('button',name='This week',exact=True).tap();assert p.evaluate('plan120.raw()')==before
 baseline=p.evaluate('plan120.state()');raw=p.evaluate('plan120.raw()')
 p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True)
 assert d.locator('.start-week-choice input').evaluate_all('(xs)=>xs.length>0&&xs.every(x=>x.checked)')
 for row in d.locator('.start-week-choice').all():
  check=row.locator('input').bounding_box();day=row.locator('.start-week-choice-day').bounding_box();recipe=row.locator('span').first.bounding_box();assert check['x']<recipe['x']<day['x']
 assert d.get_by_role('switch',name='Mark replaced meals as cooked',exact=True).count()==1
 d.get_by_role('switch',name='Mark replaced meals as cooked',exact=True).check();p.screenshot(path='/workspace/work/review120/'+name+'-dialog.png');d.get_by_role('button',name='Close Start next week',exact=True).tap();assert p.evaluate('plan120.raw()')==raw
 # Same all-selected default: preview and the actual operation agree despite mixed saved dates.
 count=p.evaluate('plan120.historyLength()');p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True);d.get_by_role('button',name='Start next week →',exact=True).evaluate('(button)=>{button.click();button.click()}')
 assert p.evaluate('plan120.historyLength()')==count+1 and p.evaluate('review120.actual()')==predicted
 after=p.evaluate('plan120.state()');p.locator('#undo').tap();assert_state(p.evaluate('plan120.state()'),baseline);p.locator('#redo').tap();assert_state(p.evaluate('plan120.state()'),after);p.locator('#undo').tap()
 # Selective replacement uses the same preview operation, retaining explicit unchecked meals.
 partial=p.evaluate("review120.preview(['Monday::Meals'])");p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True);d.locator('.start-week-choice input').evaluate_all('(xs)=>xs.forEach((x,i)=>x.checked=i===0)');d.get_by_role('switch',name='Mark replaced meals as cooked',exact=True).check();d.get_by_role('button',name='Start next week →',exact=True).tap();assert p.evaluate('review120.actual()')==partial
 assert [m['id'] for m in json.loads(p.evaluate('plan120.state()'))['manual']]==['keep']
 p.locator('#undo').tap();assert_state(p.evaluate('plan120.state()'),baseline)
 p.get_by_role('button',name='Start next week',exact=True).tap();d=p.get_by_role('dialog',name='Start next week',exact=True);d.locator('.start-week-choice input').evaluate_all('(xs)=>xs.forEach(x=>x.checked=false)');d.get_by_role('button',name='Start next week →',exact=True).tap();assert_state(p.evaluate('plan120.state()'),baseline)
 assert not errors,errors;c.close();print('PASS',name,'mixed occurrence dates preserved, mutation-free preview/default and partial parity, colored rows/switch/cancel, single dispatch and complete Undo/Redo',flush=True)


def slot_management(browser,name):
 c,p,errors,prefix=setup_review(browser,name,320)
 p.get_by_role('tab',name='Lunch',exact=True).tap();assert p.get_by_role('tab',name='Lunch',exact=True).get_attribute('aria-selected')=='true';p.get_by_role('tab',name='Dinner',exact=True).tap()
 before=p.evaluate('plan120.state()');tabs=p.locator('.meal-plan-tabs');first=p.get_by_role('tab',name='Dinner',exact=True)
 # A hold opens only on release; rename/reorder drafts cancel together.
 box=first.bounding_box();p.mouse.move(box['x']+20,box['y']+20);p.mouse.down();p.wait_for_timeout(620);assert not p.get_by_role('dialog',name='Rename meal slot',exact=True).count();p.mouse.up()
 d=p.get_by_role('dialog',name='Rename meal slot',exact=True);d.wait_for(state='visible');bounds=d.locator(':scope>div').bounding_box();assert d.locator('.meal-unified-actions button').evaluate_all('(xs)=>xs.every(x=>x.getBoundingClientRect().width>=44)');assert all(button.bounding_box()['x']>=bounds['x'] and button.bounding_box()['x']+button.bounding_box()['width']<=bounds['x']+bounds['width'] for button in d.locator('.meal-unified-actions button').all());assert d.get_by_role('button',name='Delete meal slot',exact=True).is_visible();d.get_by_role('textbox',name='Meal slot name',exact=True).fill('Changed');d.get_by_role('button',name='Move slot right',exact=True).tap();d.get_by_role('button',name='Cancel meal slot changes',exact=True).tap();assert_state(p.evaluate('plan120.state()'),before)
 # Accessible ordering shares stable IDs; saving rename does not change schedules.
 first=p.get_by_role('tab',name='Dinner',exact=True);first.focus();p.keyboard.press('Alt+ArrowRight');assert p.evaluate('review120.groups()')[1]['id']=='original';p.locator('#undo').tap();assert_state(p.evaluate('plan120.state()'),before)
 p.evaluate("review120.manage('original')");d=p.get_by_role('dialog',name='Rename meal slot',exact=True);d.get_by_role('textbox',name='Meal slot name',exact=True).fill('Evening');d.get_by_role('button',name='Save meal slot',exact=True).tap();assert p.get_by_role('tab',name='Evening',exact=True).get_attribute('aria-selected')=='true'
 # Horizontal hold/drag changes only display order and does not open rename.
 p.evaluate('review120.longSlots()');initial=p.evaluate('review120.groups()');button=p.get_by_role('tab',name='Evening',exact=True);box=button.bounding_box();bar=tabs.bounding_box();p.mouse.move(box['x']+20,box['y']+20);p.mouse.down();p.wait_for_timeout(620);p.mouse.move(bar['x']+bar['width']-4,box['y']+20,steps=10);p.wait_for_timeout(350);p.mouse.up();assert not p.get_by_role('dialog',name='Rename meal slot',exact=True).count();assert p.evaluate('review120.groups()')!=initial
 assert p.evaluate("review120.groups().some(p=>p.id==='original'&&p.name==='Evening')")
 tabs.evaluate('(x)=>x.scrollLeft=x.scrollWidth');assert p.locator('.meal-plan-add').bounding_box()['x']<360
 p.reload();p.wait_for_function('window.review120!==undefined');p.evaluate('plan120.home()');assert p.evaluate("review120.groups().some(p=>p.id==='original'&&p.name==='Evening')")
 assert not errors,errors;c.close();print('PASS',name,'hold-release manager, cancel, keyboard/drag ordering with edge scroll, stable selected IDs and reload',flush=True)


def aggregates(browser,name):
 c,p,errors,prefix=setup_review(browser,name);p.evaluate("review120.aggregate('week')")
 assert not p.locator('.meal-plan-tabs,.meal-plan-add').count()
 assert p.locator('.week-selector button').first.bounding_box()['width']<100
 p.evaluate('review120.overviewTask()');task=p.locator('.all-meals-day .make-ahead-reminder').first;assert task.is_visible();row=task.bounding_box();text=task.locator('.make-ahead-task-link').bounding_box();check=task.locator('input').bounding_box();assert row['height']<=max(text['height'],check['height'])+8;parent=task.locator('xpath=..').bounding_box();assert parent['y']+parent['height']-(row['y']+row['height'])<=16
 p.screenshot(path='/workspace/work/review120/'+name+'-overview.png',full_page=True)
 p.evaluate("review120.aggregate('grocery')");assert not p.locator('.meal-plan-tabs,.meal-plan-add,.grocery-week-options').count();checks=p.evaluate('review120.grocery()')
 p.get_by_role('button',name='Choose meals',exact=True).tap();d=p.get_by_role('dialog',name='Choose Meals',exact=True)
 assert d.get_by_role('checkbox',name='This week',exact=True).is_checked();d.get_by_role('checkbox',name='Next week',exact=True).check();p.get_by_role('button',name='Cancel',exact=True).tap();assert p.locator('.grocery-week-summary').inner_text()=='Both weeks'
 # Week choices preserve their previous immediate preference semantics; meal choices cancel.
 assert p.evaluate('review120.grocery()')==checks
 p.get_by_role('button',name='Choose meals',exact=True).tap();d=p.get_by_role('dialog',name='Choose Meals',exact=True);d.get_by_role('checkbox',name='This week',exact=True).uncheck();d.get_by_role('checkbox',name='Next week',exact=True).uncheck();d.get_by_role('button',name='Save meal selections',exact=True).tap();assert p.locator('.grocery-week-summary').inner_text()=='No weeks selected'
 p.get_by_role('button',name='Choose meals',exact=True).tap();d=p.get_by_role('dialog',name='Choose Meals',exact=True);d.get_by_role('checkbox',name='This week',exact=True).check();d.get_by_role('checkbox',name='Next week',exact=True).check();p.screenshot(path='/workspace/work/review120/'+name+'-grocery-filter.png');d.get_by_role('button',name='Save meal selections',exact=True).tap()
 p.reload();p.wait_for_function('window.review120!==undefined');p.evaluate("review120.aggregate('grocery')");assert p.locator('.grocery-week-summary').inner_text()=='Both weeks' and p.evaluate('review120.grocery()')==checks
 assert not errors,errors;c.close();print('PASS',name,'aggregate selectors removed, compact overview, grocery popup weeks/summary/none/both/reload and check preservation',flush=True)


def recipe_review(browser,name):
 c,p,errors,prefix=setup_review(browser,name);p.evaluate('review120.note(8);review120.longRecipe();review120.viewer(1)')
 assert p.get_by_role('button',name='Keep screen awake',exact=True).is_visible();assert p.locator('.recipe-keep-awake svg path').get_attribute('d').startswith('M9 17')
 p.get_by_role('button',name='Collapse Needs Adjusting note',exact=True).tap();assert p.locator('.recipe-tweaking-note').is_hidden()
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.evaluate('review120.viewer(1)');assert p.locator('.recipe-tweaking-note').is_hidden()
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.evaluate('review120.viewer(8)');assert p.locator('.recipe-tweaking-note').is_visible()
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.reload();p.wait_for_function('window.review120!==undefined');p.evaluate('review120.viewer(1)');assert p.locator('.recipe-tweaking-note').is_hidden()
 # Jump occupies an actual toolbar grid row, above all panes in every geometry.
 for width,height in [(320,800),(740,360)]:
  p.set_viewport_size({'width':width,'height':height})
  for size in ['normal','extra']:
   p.evaluate('s=>review120.scale(s)',size)
   for split in [False,True]:
    mode=p.locator('.recipe-view-mode')
    is_split=p.locator('#recipeViewer').evaluate("x=>x.classList.contains('recipe-split')")
    if is_split!=split:mode.tap()
    p.evaluate('()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');p.wait_for_timeout(100)
    if split:p.locator('.recipe-instructions-pane').evaluate('(pane)=>pane.scrollTop=pane.scrollHeight')
    else:p.locator('#recipeViewer').evaluate('(view)=>view.scrollTop=view.scrollHeight')
    p.locator('.recipe-current-step').wait_for(state='visible')
    rect=p.locator('.recipe-current-step').bounding_box();bar=p.locator('.recipe-viewer-bar').bounding_box();panes=p.locator('.recipe-panes').bounding_box()
    assert rect['y']>=bar['y'] and rect['y']+rect['height']<=bar['y']+bar['height']+1,(width,height,size,split,rect,panes)
    assert p.locator('.recipe-current-step').evaluate('(b)=>getComputedStyle(b).position')=='static'
    if split:assert bar['y']+bar['height']<=panes['y']+1
    assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
    p.screenshot(path='/workspace/work/review120/'+name+'-viewer-'+str(width)+'-'+size+'-'+str(split)+'.png')
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.evaluate('review120.viewer(8)')
 assert p.locator('.recipe-original svg').count()==1
 assert not errors,errors;c.close();print('PASS',name,'lightbulb, stable per-ID note collapse/reload and nonoverlapping jump in full/split portrait/landscape with large text',flush=True)

def touch_slots(browser,name):
 c,p,errors,prefix=setup_review(browser,name);p.evaluate('review120.longSlots()');cdp=c.new_cdp_session(p)
 def touch(kind,x=0,y=0):cdp.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y,'id':1}]})
 bar=p.locator('.meal-plan-tabs');box=p.get_by_role('tab',name='Dinner',exact=True).bounding_box();bounds=bar.bounding_box();before=p.evaluate('review120.groups()')
 touch('touchStart',box['x']+20,box['y']+20);p.wait_for_timeout(620)
 for i in range(1,11):touch('touchMove',box['x']+20+(bounds['x']+bounds['width']-5-box['x']-20)*i/10,box['y']+20);p.wait_for_timeout(16)
 p.wait_for_timeout(250);touch('touchEnd');assert p.evaluate('review120.groups()')!=before and not p.get_by_role('dialog',name='Rename meal slot',exact=True).count()
 # Cancelling a real held touch restores saved order and never opens rename.
 before=p.evaluate('review120.groups()');box=p.get_by_role('tab',name='Dinner',exact=True).bounding_box();touch('touchStart',box['x']+20,box['y']+20);p.wait_for_timeout(620);touch('touchMove',max(bounds['x']+5,box['x']-40),box['y']+20);touch('touchCancel');assert p.evaluate('review120.groups()')==before and not p.get_by_role('dialog',name='Rename meal slot',exact=True).count()
 p.get_by_role('tab',name='Dinner',exact=True).scroll_into_view_if_needed();p.evaluate('()=>new Promise(requestAnimationFrame)');box=p.get_by_role('tab',name='Dinner',exact=True).bounding_box();touch('touchStart',box['x']+20,box['y']+20);p.wait_for_timeout(620);assert not p.get_by_role('dialog',name='Rename meal slot',exact=True).count();touch('touchEnd');p.get_by_role('dialog',name='Rename meal slot',exact=True).get_by_role('button',name='Cancel meal slot changes',exact=True).tap()
 assert not errors,errors;c.close();print('PASS',name,'real touch hold/drag, edge scroll, cancelled drag and no rename/drop activation',flush=True)

def accompaniments_and_footer(browser,name):
 c,p,errors,prefix=setup_review(browser,name)
 assert not p.locator('.plan-meal-card[data-meal-id="8"]').count()
 p.evaluate('review120.independent()');side=p.locator('.plan-meal-card[data-meal-id="8"]');assert side.count()==1 and side.locator(':scope>.meal-actions-toggle').count()==1
 assert not card(p).locator('.plan-linked-names').count()
 baseline=p.evaluate('plan120.state()');side.locator(':scope>.meal-actions-toggle').tap();assert side.locator('.meal-inline-action').count()==6
 side.get_by_role('button',name='Edit recipe',exact=True).tap();p.locator('#cancel').tap();assert_state(p.evaluate('plan120.state()'),baseline)
 p.evaluate('review120.footer()');assert p.locator('.recipe-footer-linked svg').count()==1 and p.locator('.recipe-original svg').count()==1
 assert p.locator('.recipe-needs-tweaking').evaluate('(x)=>getComputedStyle(x).borderTopWidth')=='0px'
 assert p.locator('.recipe-footer-linked').evaluate('(x)=>getComputedStyle(x).textDecorationLine')=='none'
 p.screenshot(path='/workspace/work/review120/'+name+'-footer.png');assert not errors,errors;c.close();print('PASS',name,'linked accompaniment versus independent side controls, occurrence data preservation and compact footer actions',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   layout_and_actions(browser,name);weeks_and_dialog(browser,name);slot_management(browser,name);touch_slots(browser,name);aggregates(browser,name);accompaniments_and_footer(browser,name);recipe_review(browser,name);wake_lifecycle(browser,name)
  browser.close()
