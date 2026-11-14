"""Original app: duplicate confirmation, compact menu and direct occurrence sides."""
import copy,json
from playwright.sync_api import sync_playwright
import simple_sides_browser as s
f=s.f
f.HOOK+='''window.dialogTest={
 seed:()=>{const p=mealPlans[0];meals.find(m=>m.id===1).name='Chicken Curry';weekdayCategories.Monday=['Meals'];weekdayMealOverrides['Monday::Meals']='6';p.cycleRetainedSlots['Monday::Meals']='6';p.cycleSlotChoices['Monday::Meals']={mealId:'6',parentId:'',retain:true,substitution:true};saveActiveMealPlan();persist();render()},
 monday:()=>{const e=recipePlanEntries(activePlanId).find(e=>e.day==='Monday'&&e.cat==='Meals');openTopMealActionMenu(e.day,e.cat,e.meal)},
 tuesday:()=>simpleTest.menu(),
 side:()=>{const e=recipePlanEntries(activePlanId).find(e=>e.day==='Tuesday'&&e.cat==='Meals'&&!e.occasional);openOccurrenceServeWith(activePlanId,e)},
 rows:()=>correctionTest.rows(),
 saveTwice:()=>{const save=document.querySelector('.weekday-meal-picker [aria-label=Save]');window.oldPickerSave=save;save.onclick();save.onclick()},
 captureChoices:()=>{window.oldDuplicateButtons=[...document.querySelectorAll('[role=dialog]')].at(-1).querySelectorAll('button')},
 repeatChoices:()=>{for(const button of oldDuplicateButtons)button.onclick()},
 failChoice:()=>{const original=applyManualWeekdayMeal;applyManualWeekdayMeal=(...args)=>{applyManualWeekdayMeal=original;throw Error('injected choice failure')}},
 history:()=>history.length,
 seedProgress:()=>{const entry=recipePlanEntries('original').find(e=>e.day==='Tuesday'&&e.meal.id===1),context=cookingContext('original',entry.day,entry.cat,entry.meal,entry.linkedTo),session=cookingSession(context,true);session.ingredients=[cookingItemTokens(entry.meal).ingredients[0].token];writeCookingSessions(cookingSessions);const item=scheduledMakeAheadTasks().find(x=>x.plan.id==='original'&&x.entry.meal.id===1);mealPlans[0].makeAheadChecks={...(mealPlans[0].makeAheadChecks||{}),[item.key]:true};saveActiveMealPlan()},
 progress:()=>JSON.stringify({sessions:cookingSessions,scales:occurrenceScales,checks:mealPlans.map(p=>p.makeAheadChecks)}),
 onceTwice:()=>{const button=[...document.querySelectorAll('.occurrence-side-editor button')].find(button=>button.textContent==='This time only');button.onclick();button.onclick()},
 cancelAll:()=>document.querySelector('.occurrence-side-editor [aria-label="Cancel side edit"]').click(),
 expectedReplace:()=>{const entry=recipePlanEntries(activePlanId).find(e=>e.day==='Tuesday'&&e.cat==='Meals'&&!e.occasional);return automaticSlotCandidates(mealPlans[0],entry.day,entry.cat,meals,recipePlanEntries(activePlanId)).filter(m=>m.id!==1).map(m=>m.id)}
};'''
def setup(b,name):
 c,p,e,pr=s.setup(b,name);p.evaluate('dialogTest.seed()');return c,p,e,pr

def side(p):return p.get_by_role('dialog',name='Sides for Chicken Curry',exact=True)
def open_side(p):
 p.evaluate('dialogTest.tuesday()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Add or edit sides',exact=True).tap();side(p).wait_for()
def fill(p,name,ingredients=''):
 d=side(p);d.get_by_role('textbox',name='Side name',exact=True).fill(name)
 if ingredients:
  d.get_by_text('Ingredients (optional)',exact=True).tap();d.get_by_role('textbox',name='Side ingredients (optional)',exact=True).fill(ingredients)
def add_side(p,name,ingredients='',choice='This time only'):
 open_side(p);fill(p,name,ingredients);side(p).get_by_role('button',name=choice,exact=True).tap();assert not side(p).count();assert not p.locator('.compact-meal-dialog [role=dialog]').count()
def rows(p):return sorted(p.evaluate('dialogTest.rows()'),key=json.dumps)

def duplicate_cases(b,name):
 for decision in ['keep','replace','x']:
  c,p,e,pr=setup(b,name);add_side(p,'Rice','1 cup rice',choice='Always');baseline=rows(p);sides_before=copy.deepcopy(s.sides(p));progress=p.evaluate('dialogTest.progress()');p.evaluate('dialogTest.monday()');p.get_by_role('dialog',name='Meal options for Monday',exact=True).get_by_role('button',name='Change meal',exact=True).tap();picker=p.locator('.weekday-meal-picker');picker.locator('[data-meal-id="1"]').tap();p.evaluate('dialogTest.saveTwice()');d=p.get_by_role('dialog',name='Chicken Curry is already planned',exact=True);assert d.count()==1;assert picker.evaluate('(e)=>!!e.closest("[inert]")');p.evaluate('dialogTest.captureChoices()')
  if decision=='keep':
   button=d.get_by_role('button',name='No — Keep both meals',exact=True);box=button.bounding_box();p.touchscreen.tap(box['x']+20,box['y']+20);p.touchscreen.tap(box['x']+20,box['y']+20)
  elif decision=='replace':d.get_by_role('button',name="Yes — Replace Tuesday's meal",exact=True).tap()
  else:d.get_by_role('button',name='Close',exact=True).tap()
  p.evaluate('dialogTest.repeatChoices()');p.clock.run_for(450);assert not d.count();actual=rows(p)
  if decision=='x':
   assert actual==baseline and picker.count();assert not picker.get_by_role('button',name='Save',exact=True).is_disabled();picker.locator('[data-meal-id="2"]').tap();picker.get_by_role('button',name='Save',exact=True).tap();assert not picker.count();assert next(r for r in rows(p) if r['day']=='Monday' and r['planId']=='original')['id']==2
  else:
   assert not picker.count();assert any(r['day']=='Monday' and r['id']==1 and r['planId']=='original' for r in actual)
   if decision=='keep':assert s.sides(p)==sides_before and p.evaluate('dialogTest.progress()')==progress;assert any(r['day']=='Tuesday' and r['id']==1 and not r.get('linked') for r in actual)
   else:assert not any(r['day']=='Tuesday' and r['id']==1 and r['cat']=='Meals' for r in actual)
   assert [r for r in actual if r['day'] not in ['Monday','Tuesday']]==[r for r in baseline if r['day'] not in ['Monday','Tuesday']];p.locator('#undo').tap();assert rows(p)==baseline;p.locator('#redo').tap();assert rows(p)==actual
  assert not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('dialogTest.monday()');p.get_by_role('button',name='Change meal',exact=True).tap();picker=p.locator('.weekday-meal-picker');picker.locator('[data-meal-id="2"]').tap();p.evaluate('dialogTest.failChoice()');picker.get_by_role('button',name='Save',exact=True).tap();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).tap();assert not picker.get_by_role('button',name='Save',exact=True).is_disabled();picker.get_by_role('button',name='Save',exact=True).tap();assert not picker.count() and not e,e;c.close()
 print('PASS',name,'Replace/Keep both/X, pending guard, detached retaps, inert/focus recovery, existing replacement and Undo/Redo',flush=True)

def direct_side_cases(b,name):
 c,p,e,pr=setup(b,name);before=p.evaluate('simpleTest.snapshot()');open_side(p);d=side(p);assert d.get_by_role('textbox',name='Side name').is_visible();assert d.get_by_role('button',name='Always',exact=True).is_disabled();assert d.get_by_role('button',name='This time only',exact=True).is_disabled();assert not d.locator('details').get_attribute('open');assert not d.get_by_role('button',name='Add simple side',exact=True).count();fill(p,' Rice ');assert d.get_by_text('Always serve Rice with Chicken Curry?',exact=True).is_visible();d.get_by_role('button',name='Cancel side edit',exact=True).tap();assert p.evaluate('simpleTest.snapshot()')==before
 add_side(p,'Rice',choice='Always');assert [x['name'] for x in s.sides(p)]==['Rice'];assert not s.side_sources(p);assert s.record(p)['simpleSides'][0]['name']=='Rice';assert not s.sides(p,'lunch','Friday')
 add_side(p,'Peas','1 cup peas');assert len(s.sides(p))==2;assert len(s.record(p)['simpleSides'])==1;assert len(s.side_sources(p))==1
 open_side(p);d=side(p);d.get_by_role('button',name='Edit simple side Peas',exact=True).tap();assert not d.get_by_role('button',name='Always',exact=True).is_visible();assert d.get_by_role('button',name='Save side',exact=True).is_visible();d.get_by_role('textbox',name='Side name').fill('Garden peas');d.get_by_role('button',name='Save side',exact=True).tap();assert s.sides(p)[1]['name']=='Garden peas' and s.record(p)['simpleSides'][0]['name']=='Rice'
 open_side(p);side(p).get_by_role('button',name='Remove simple side Rice',exact=True).tap();side(p).get_by_role('button',name='Cancel side edit',exact=True).tap();assert len(s.sides(p))==2
 open_side(p);side(p).get_by_role('button',name='Remove simple side Rice',exact=True).tap();side(p).get_by_role('button',name='Remove side',exact=True).tap();assert [x['name'] for x in s.sides(p)]==['Garden peas'];p.locator('#undo').tap();assert len(s.sides(p))==2;p.locator('#redo').tap();assert len(s.sides(p))==1
 open_side(p);fill(p,'Sauce','2 tbsp oil');before=p.evaluate('simpleTest.snapshot()');p.evaluate('simpleTest.fail()');side(p).get_by_role('button',name='Always',exact=True).tap();assert 'draft is still here' in side(p).inner_text();assert p.evaluate('simpleTest.snapshot()')==before;assert side(p).get_by_role('textbox',name='Side name').input_value()=='Sauce';p.evaluate('restoreSimpleWrites()');side(p).get_by_role('button',name='Always',exact=True).tap();assert not side(p).count()
 open_side(p);fill(p,'Sauce','3 tbsp oil');side(p).get_by_role('button',name='Always',exact=True).tap();assert len([x for x in s.record(p)['simpleSides'] if x['name']=='Sauce'])==1
 p.reload();assert [x['name'] for x in s.sides(p)]==['Garden peas','Sauce'];p.evaluate('simpleTest.scale(2)');assert all(x['multiplier']==2 for x in s.side_sources(p));assert not any(x['simpleSideName']=='Garden peas' for x in s.side_sources(p,'next'));assert not s.sides(p,'lunch','Friday');assert s.record(p)['linkedMealIds']==[8]
 open_side(p);fill(p,'Bread');history=p.evaluate('dialogTest.history()');p.evaluate('dialogTest.onceTwice()');assert p.evaluate('dialogTest.history()')==history+1 and len(s.sides(p))==3
 assert not e,e;c.close();print('PASS',name,'one-editor Always/This time, blank/X, ingredients, edit/remove check, failure retry, duplicate reuse, sides/scaling/reload/isolation and single save',flush=True)

def menu_skip_layout(b,name):
 c,p,e,pr=setup(b,name);add_side(p,'Skip side','1 cup peas');p.evaluate('simpleTest.scale(2)');p.evaluate('ids=>simpleTest.check(ids)',[x['id'] for x in s.side_sources(p)]);p.evaluate('dialogTest.seedProgress()');baseline=rows(p);progress=p.evaluate('dialogTest.progress()');p.evaluate('dialogTest.tuesday()');d=p.get_by_role('dialog',name='Meal options for Tuesday',exact=True);p.screenshot(path='/tmp/compact-meal-options-'+name+'.png');assert d.locator('.meal-option-row').all_text_contents()==['Change meal','Add or edit sides','Edit recipe','Edit groceries','Skip this meal'];assert not d.get_by_role('button',name='Open recipe',exact=True).count();assert d.locator('.meal-options-last-cooked').bounding_box()['y']<d.locator('.meal-option-row').first.bounding_box()['y'];assert d.locator('.meal-option-row').evaluate_all('(xs)=>xs.every(e=>getComputedStyle(e).borderTopWidth==="0px"&&getComputedStyle(e).textAlign==="left")');d.get_by_role('button',name='Skip this meal',exact=True).tap();p.clock.run_for(450);actual=rows(p);assert not s.side_sources(p);assert any(r['id']==5 and r['day']=='Tuesday' for r in actual);assert any(r['id']==14 and r['day']=='Tuesday' for r in actual);assert not any(r['id']==1 and r['day']=='Tuesday' and r['planId']=='original' for r in actual);assert [r for r in actual if r['day']!='Tuesday']==[r for r in baseline if r['day']!='Tuesday'];p.locator('#undo').tap();assert rows(p)==baseline and p.evaluate('dialogTest.progress()')==progress
 p.evaluate('dialogTest.tuesday()');p.get_by_role('dialog',name='Meal options for Tuesday').get_by_role('button',name='Skip this meal').tap();p.clock.run_for(450);p.reload();assert any(r['id']==5 and r['day']=='Tuesday' for r in rows(p));s.t.hold(p,s.t.blank(p));p.get_by_role('button',name='Resume planned meal',exact=True).tap();p.clock.run_for(450);assert rows(p)==baseline and p.evaluate('dialogTest.progress()')==progress and all(x['checked'] for x in s.side_sources(p))
 open_side(p);fill(p,'Long side name that wraps in a narrow mobile editor','1 cup peas\n2 carrots');p.set_viewport_size({'width':320,'height':420});assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');d=side(p);assert d.get_by_role('button',name='Always').is_visible();assert d.get_by_role('button',name='This time only').is_visible();assert d.locator('.recipe-bulk-fields').evaluate('(e)=>getComputedStyle(e).overflowY==="auto"');p.screenshot(path='/tmp/direct-side-editor-'+name+'.png');d.get_by_role('button',name='Cancel side edit').tap();assert not e,e;c.close();print('PASS',name,'compact action rows, scoped Skip with two dishes in one group, Undo and narrow keyboard-height editor',flush=True)

def data_and_routes(b,name):
 c,p,e,pr=setup(b,name);add_side(p,'Peas','1 cup peas\n2 carrots',choice='Always');before=s.side_sources(p);p.evaluate('ids=>simpleTest.check(ids)',[x['id'] for x in before]);p.evaluate('simpleTest.scale(2)');p.evaluate('ids=>simpleTest.check(ids)',[x['id'] for x in s.side_sources(p)]);defaults=copy.deepcopy(s.record(p)['simpleSides']);open_side(p);side(p).get_by_role('button',name='Edit simple side Peas').tap();side(p).get_by_text('Ingredients (optional)',exact=True).tap();side(p).get_by_role('textbox',name='Side ingredients (optional)').fill('1 cup peas\n3 carrots');side(p).get_by_role('button',name='Save side').tap();sources=s.side_sources(p);assert next(x for x in sources if x['original']=='1 cup peas')['checked'];assert not next(x for x in sources if x['original']=='3 carrots')['checked'];assert s.record(p)['simpleSides']==defaults
 backup=p.evaluate('simpleTest.backup()');p.evaluate('simpleTest.removeParent()');assert not s.side_sources(p);p.evaluate('simpleTest.undo()');assert [x['id'] for x in s.side_sources(p)]==[x['id'] for x in sources];p.evaluate('storage=>simpleTest.restore(storage)',backup);p.reload();assert s.side_sources(p)==sources
 p.evaluate('dialogTest.tuesday()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Edit recipe').tap();assert p.locator('#name').input_value()=='Chicken Curry';assert p.locator('#editLinkedMeals').evaluate('(e)=>e.readDraft()')==[8];p.locator('#cancel').tap();assert s.record(p)['linkedMealIds']==[8]
 p.evaluate('dialogTest.tuesday()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Change meal').tap();assert p.get_by_role('button',name='Choose another rotation meal',exact=True).is_visible();p.locator('.weekday-meal-picker').get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('dialogTest.tuesday()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Edit groceries').tap();assert p.get_by_text('Add ingredients to grocery list',exact=True).is_visible();p.get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('simpleTest.futureLunch()');p.evaluate('simpleTest.open("lunch","Friday",1)');d=side(p);d.get_by_role('textbox',name='Side name').fill('Future bread');d.get_by_role('button',name='This time only',exact=True).tap();assert [x['name'] for x in s.sides(p)]==['Peas'] and any(x['name']=='Future bread' for x in s.sides(p,'lunch','Friday'));p.evaluate('simpleTest.preview()');s.t.hold(p,p.locator('.all-meals-day .mealname').first);assert not p.get_by_role('dialog',name='Next week meal options').get_by_role('button',name='Add or edit sides',exact=True).count();assert not e,e
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close();print('PASS',name,'grocery checks/scaling/defaults, backup/removal Undo, recipe/linked/grocery/auto-replacement routes and actual future isolation',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:duplicate_cases(b,name);direct_side_cases(b,name);menu_skip_layout(b,name);data_and_routes(b,name)
  b.close()
