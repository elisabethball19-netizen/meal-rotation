"""Permanent Stage 1 correction regressions; synthetic, disposable browser storage.

MEAL_STAGE1_EXPECT_FAILURES=1 reproduces the review findings before correction.
MEAL_CORRECTION_SOURCE_ROOT selects an unchanged HTML checkout for that probe.
"""
import copy
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright
import phase2_stage1_browser as stage
import occasional_meals_browser as legacy

if os.environ.get('MEAL_CORRECTION_SOURCE_ROOT'):
 stage.f.ROOT=Path(os.environ['MEAL_CORRECTION_SOURCE_ROOT'])

stage.f.HOOK += '''window.correctionTest={
 select:(day,cat,id,occasional=false,replacing=null)=>applyManualWeekdayMeal(day,cat,meals.find(m=>m.id===id),replacing,occasional),
 edit:id=>{const meal=meals.find(m=>m.id===id);Object.assign(meal,{notes:'Unrelated recipe edit after scheduling',ingredients:['7 cups rice'],instructions:'Updated instructions after scheduling.',url:'https://recipes.test/updated'});const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selected[String(id)]=['7 cups rice'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));persist()},
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 mark:(id,value=true)=>{for(const s of getGroceryContributions(true))if(String(s.mealId)===String(id))groceryOccurrenceChecks.checks[s.id]=value;saveGroceryOccurrenceChecks()},
 scale:id=>{for(const e of getDisplayedWeekdayMeals())if(String(e.meal.id)===String(id)){const context=cookingContext(activePlanId,e.day,e.cat,e.meal,e.linkedTo);occurrenceScales.occurrences[cookingOccurrenceKey(context)]={context,multiplier:3}}writeOccurrenceScales(occurrenceScales)},
 legacy:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;setDayCategories('Monday',['Sides']);renderList()},
 anotherLegacy:()=>{const p=mealPlans.find(p=>p.id===activePlanId);p.occasionalMeals={...p.occasionalMeals,Wednesday:'2'};setDayCategories('Wednesday',['Sides']);renderList()},
 open:(day,cat,id)=>openTopMealActionMenu(day,cat,getDisplayedWeekdayMeals().find(e=>e.day===day&&String(e.meal.id)===String(id)).meal),
 checks:()=>groceryOccurrenceChecks,
 edits:()=>JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}'),
 idea:()=>{meals.find(m=>m.id===3).rotation=false;meals.find(m=>m.id===3).linkedMealIds=[12];meals.find(m=>m.id===12).rotation=false;persist();renderList()},
 single:()=>{meals=meals.filter(m=>[1,10,20].includes(m.id));meals.find(m=>m.id===1).linkedMealIds=[20];mealPlans=mealPlans.filter(p=>p.id===activePlanId);weekdayCategories={Tuesday:['Rice','Sides']};weekdayMealOverrides={};const p=mealPlans[0];p.weekdayCategories=weekdayCategories;p.weekdayMealOverrides={};p.cycleSlotChoices={};p.cycleRetainedSlots={};saveActiveMealPlan();persist();renderList()},
 exclude:()=>{meals.find(m=>m.id===1).ingredients.push('Salt to taste');persist()},
 aggregates:()=>[...getMasterGroceryItems().values()].map(item=>({quantity:item.quantity,checked:item.contributions.every(s=>grocerySourceChecked(s)),sources:item.contributions})),
 redo:()=>document.getElementById('redo').click(),
 rotateMain:()=>moveDisplayedMealsToBottom(new Set(['Tuesday::Rice']),false,false,new Set(['Tuesday::Sides']))
};'''

def setup(browser,name,**kw):return stage.setup(browser,name,**kw)
def sources(p):return {s['id']:s for s in p.evaluate('correctionTest.sources()')}
def progress(p):return {key:(s['checked'],s['line']) for key,s in sources(p).items()}
def clean(errors):assert not errors,errors

def undo_temporary(browser,name,kind):
 c,p,errors,_=setup(browser,name,multi=True)
 if kind=='once':p.evaluate('weekTest.once();weekTest.check()')
 else:p.evaluate('weekTest.check();weekTest.empty()')
 before=copy.deepcopy(stage.plan(p)['weekSchedule']);before_rows=stage.rows(p);before_checks=progress(p)
 p.evaluate('weekTest.manual();weekTest.undo()')
 assert stage.plan(p)['weekSchedule']==before,'Undo must recover the intact temporary descriptor and stable ID'
 assert stage.rows(p)==before_rows and progress(p)==before_checks,'Undo must recover groceries/quantities/checks and unrelated occurrences'
 clean(errors);c.close()

def choose_recipe(p,day,id):
 dialog=p.get_by_role('dialog',name=f"Choose {day}'s meal",exact=True)
 dialog.get_by_role('button',name='Search recipes',exact=True).click();dialog.get_by_role('searchbox').fill('Third Main')
 dialog.locator(f'[data-meal-id="{id}"]').click();dialog.get_by_role('button',name='Save',exact=True).click()

def unconfigured(browser,name):
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.once(null,"Sunday");weekTest.my()')
 once=next(e for e in stage.rows(p) if e['day']=='Sunday');before=copy.deepcopy(stage.plan(p));queue=stage.queues(p)
 p.evaluate('e=>correctionTest.open(e.day,e.cat,e.id)',once)
 p.get_by_role('dialog',name='One-time meal options').get_by_role('button',name='Change meal',exact=True).click();choose_recipe(p,'Sunday',3)
 assert any(e['day']=='Sunday' and e['id']==3 for e in stage.rows(p)),'Unconfigured weekday must display the selected reusable recipe'
 assert any(s['day']=='Sunday' and s['mealId']==3 for s in sources(p).values())
 assert not stage.plan(p)['weekdayCategories'].get('Sunday') and stage.queues(p)==queue
 for field in ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices']:assert 'Sunday::@day' not in stage.plan(p).get(field,{})
 p.reload();backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload()
 assert any(e['day']=='Sunday' and e['id']==3 for e in stage.rows(p))
 # Undo itself is intentionally in-memory; exercise a fresh transition after reload.
 p.evaluate('weekTest.once(null,"Sunday");correctionTest.select("Sunday",null,3,true);weekTest.undo()')
 assert any(e['day']=='Sunday' and str(e['id']).startswith('once-') for e in stage.rows(p))
 clean(errors);c.close()

def legacy_reorder(browser,name,mode,width=320):
 c,p,errors,_=setup(browser,name,width=width,linked=True,multi=True)
 p.evaluate('occasionalTest.prepare(true)');legacy.choose(p);p.evaluate('correctionTest.legacy()')
 def ids():return p.locator('.top-recipe-wrap[data-schedule-day=Monday] .meal').evaluate_all('(rows)=>rows.map(row=>row.dataset.mealId)')
 before=ids();assert before==['12','2'],before
 handle=p.get_by_role('button',name='Reorder Occasional curry within Monday',exact=True)
 if mode=='keyboard':handle.focus();p.keyboard.press('ArrowUp')
 else:
  start=handle.bounding_box();target=p.locator('.top-recipe-wrap[data-schedule-day=Monday]').first.bounding_box()
  p.mouse.move(start['x']+start['width']/2,start['y']+start['height']/2);p.mouse.down();p.wait_for_timeout(500)
  p.mouse.move(target['x']+target['width']-4,target['y']+2,steps=8);p.mouse.up()
 assert ids()==['2','12'],'Legacy occasional identity must match rendering, pointer and keyboard keys'
 p.reload();p.evaluate('weekTest.my()');assert ids()==['2','12']
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();p.evaluate('weekTest.my()');assert ids()==['2','12']
 clean(errors);c.close()

def undo_preserves_edits(browser,name):
 for kind in ['once','empty']:
  c,p,errors,_=setup(browser,name,multi=True)
  p.evaluate('weekTest.check();weekTest.'+('once()' if kind=='once' else 'empty()'))
  old=copy.deepcopy(stage.plan(p)['weekSchedule']);p.evaluate('weekTest.manual();correctionTest.edit(2);correctionTest.mark(10,false);correctionTest.scale(10)')
  definitions=stage.definitions(p);selections=p.evaluate('correctionTest.edits()');unrelated={key:value for key,value in progress(p).items() if sources(p)[key]['mealId']==10}
  p.locator('#undo').click()
  assert stage.plan(p)['weekSchedule']==old and stage.definitions(p)==definitions and p.evaluate('correctionTest.edits()')==selections
  for key,value in unrelated.items():assert progress(p)[key]==value
  if kind=='empty':p.evaluate('weekTest.resume()');assert all(s['checked'] for s in sources(p).values() if s['mealId'] in [1,20])
  clean(errors);c.close()
 # Real Redo must also retain live recipe edits instead of old definitions.
 c,p,errors,_=setup(browser,name);p.evaluate('weekTest.once();weekTest.manual();correctionTest.edit(2)');p.locator('#undo').click();p.evaluate('correctionTest.edit(3)');expected=stage.definitions(p);p.locator('#redo').click();assert stage.definitions(p)==expected;assert any(e['id']==3 and e['cat']=='Rice' for e in stage.rows(p));clean(errors);c.close()

def unconfigured_idea_and_duplicates(browser,name):
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('correctionTest.idea();weekTest.once(null,"Sunday");weekTest.my()');definitions=stage.definitions(p)
 once=next(e for e in stage.rows(p) if e['day']=='Sunday');p.evaluate('e=>correctionTest.open(e.day,e.cat,e.id)',once);p.get_by_role('dialog',name='One-time meal options').get_by_role('button',name='Change meal',exact=True).click();choose_recipe(p,'Sunday',3)
 assert {e['id'] for e in stage.rows(p) if e['day']=='Sunday'}=={3,12};assert stage.definitions(p)==definitions
 assert {s['mealId'] for s in sources(p).values() if s['day']=='Sunday'}=={3,12}
 p.reload();backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();assert stage.definitions(p)==definitions;assert {e['id'] for e in stage.rows(p) if e['day']=='Sunday'}=={3,12};clean(errors);c.close()
 for decision,single in [('cancel',False),('no',False),('yes',False),('yes',True)]:
  c,p,errors,_=setup(browser,name,multi=True)
  if single:p.evaluate('correctionTest.single()')
  p.evaluate('weekTest.once(null,"Sunday");weekTest.check();weekTest.my()');before=copy.deepcopy(stage.plan(p)['weekSchedule']);checks=progress(p)
  once=next(e for e in stage.rows(p) if e['day']=='Sunday');p.evaluate('e=>correctionTest.open(e.day,e.cat,e.id)',once);p.get_by_role('dialog',name='One-time meal options').get_by_role('button',name='Change meal',exact=True).click()
  d=p.get_by_role('dialog',name="Choose Sunday's meal",exact=True);d.get_by_role('button',name='Search recipes',exact=True).click();d.get_by_role('searchbox').fill('Thai Garlic Pork');d.locator('[data-meal-id="1"]').click();d.get_by_role('button',name='Save',exact=True).click()
  confirm=p.get_by_role('dialog',name='Thai Garlic Pork is already planned',exact=True)
  label={'cancel':'Close','no':'No — Keep both meals','yes':"Yes — Replace Tuesday's meal"}[decision];confirm.get_by_role('button',name=label,exact=True).click()
  if decision=='cancel':assert stage.plan(p)['weekSchedule']==before and progress(p)==checks
  else:
   assert any(e['day']=='Sunday' and e['id']==1 for e in stage.rows(p));assert not stage.plan(p)['weekdayCategories'].get('Sunday')
   for field in ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices']:assert 'Sunday::@day' not in stage.plan(p).get(field,{})
   p.locator('#undo').click();assert stage.plan(p)['weekSchedule']==before and progress(p)==checks
  clean(errors);c.close()

def assert_aggregation(p):
 for row in p.evaluate('correctionTest.aggregates()'):
  if row['quantity']:assert abs(row['quantity']['lo']-sum(s['quantity']['lo'] for s in row['sources']))<1e-8
  assert row['checked']==all(sources(p)[s['id']]['checked'] for s in row['sources'])

def grocery_cycles(browser,name):
 # Hidden multipliers and linked checks survive reload and a whole-backup restore.
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.check();correctionTest.scale(1);correctionTest.scale(20);correctionTest.exclude()');before=progress(p);selected=p.evaluate('correctionTest.edits()')
 p.evaluate('weekTest.empty()');assert not any(s['mealId'] in [1,20] and s['planId']=='original' for s in sources(p).values())
 p.reload();backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();p.evaluate('weekTest.resume()');assert progress(p)==before
 assert p.evaluate('correctionTest.edits()')==selected;assert_aggregation(p)
 # Two hidden groups: rotate only Rice, keep Side's temporary shopping progress.
 p.evaluate('weekTest.empty();weekTest.empty("Sides");weekTest.rotate(["Tuesday::Rice"])')
 assert all(not s['checked'] for s in sources(p).values() if s['planId']=='original' and s['mealId'] in [1,20])
 assert 'Tuesday::Sides' in stage.plan(p)['weekSchedule']['slots'];p.reload();p.evaluate('weekTest.resume("Sides")')
 assert all(s['checked'] for s in sources(p).values() if s['mealId']==10)
 assert p.evaluate('correctionTest.edits()')==selected;assert_aggregation(p);clean(errors);c.close()
 # Rotation of a different group must leave a hidden main and its attachment alone.
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.check();correctionTest.scale(1);correctionTest.scale(20)');before=progress(p)
 p.evaluate('weekTest.empty();weekTest.rotate(["Tuesday::Sides"])');p.reload();p.evaluate('weekTest.resume()')
 for key,value in before.items():
  if json.loads(json.loads(key)[0])[2] in ['1','20']:assert progress(p)[key]==value
 assert all(not s['checked'] for s in sources(p).values() if s['planId']=='original' and s['cat']=='Sides')
 assert_aggregation(p);clean(errors);c.close()
 # Even a one-recipe pool returning the exact same ID is a new unchecked cycle.
 c,p,errors,_=setup(browser,name);p.evaluate('correctionTest.single();weekTest.check();weekTest.empty();weekTest.rotate()')
 assert sources(p) and all(not s['checked'] for s in sources(p).values());p.evaluate('weekTest.check();weekTest.rotate()');assert all(not s['checked'] for s in sources(p).values());clean(errors);c.close()
 # A recipe returning after other recipes must not revive an old check ledger.
 c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.check()');unchanged={key:value for key,value in progress(p).items() if sources(p)[key]['planId']!='original' or sources(p)[key]['cat']=='Sides'}
 returned=False
 for i in range(10):
  p.evaluate('correctionTest.rotateMain()')
  if any(e['planId']=='original' and e['cat']=='Rice' and e['id']==1 for e in stage.rows(p)):
   assert all(not s['checked'] for s in sources(p).values() if s['planId']=='original' and s['mealId']==1);returned=True;break
  for key,value in unchanged.items():assert progress(p)[key]==value
  # Check only the newly scheduled main; existing shared contributions stay exact.
  main=next(e for e in stage.rows(p) if e['planId']=='original' and e['cat']=='Rice');p.evaluate('id=>correctionTest.mark(id)',main['id'])
 assert returned,'Fixture must actually exercise a returning recipe';assert_aggregation(p);clean(errors);c.close()

def storage_and_validation(browser,name):
 c,p,errors,prefix=setup(browser,name,multi=True);p.evaluate('weekTest.check();correctionTest.scale(1)');expected=progress(p);durable=p.evaluate('prefix=>window.localStorage.getItem(prefix+"mealRotationPlansV1")',prefix)
 p.evaluate('''()=>{window.correctionNativeSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).startsWith('mealRotation'))throw Error('synthetic quota');return correctionNativeSet.call(this,k,v)}}''')
 p.evaluate('weekTest.empty()');assert p.locator('#mealSaveWarning').is_visible();assert p.evaluate('prefix=>window.localStorage.getItem(prefix+"mealRotationPlansV1")',prefix)==durable
 with p.expect_download() as download:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 payload=Path(download.value.path()).read_text();assert 'groceryChecks' in payload
 p.evaluate('()=>{Storage.prototype.setItem=correctionNativeSet}');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.reload();p.evaluate('weekTest.resume()');assert progress(p)==expected
 p.evaluate('weekTest.empty()');before=p.evaluate('weekTest.storage()');bad=copy.deepcopy(before);plans=json.loads(bad['mealRotationPlansV1']);plans['plans'][0]['weekSchedule']['slots']['Tuesday::Rice']['groceryChecks']={'not a source':True};bad['mealRotationPlansV1']=json.dumps(plans)
 try:p.evaluate('weekTest.validate',bad);raise AssertionError('malformed hidden checks accepted')
 except Exception as error:assert 'Invalid grocery source' in str(error),error
 assert p.evaluate('weekTest.storage()')==before
 # Deletion cleanup removes obsolete cached checks without resurrecting recipes.
 p.evaluate('weekTest.remove(1)');assert all(m['id']!=1 for m in stage.state(p)['meals'])
 assert all(json.loads(json.loads(key)[0])[2]!='1' for slot in stage.plan(p)['weekSchedule']['slots'].values() for key in slot.get('groceryChecks',{}))
 p.reload();assert all(m['id']!=1 for m in stage.state(p)['meals']);clean(errors);c.close()

def legacy_focus(browser,name):
 c,p,errors,_=setup(browser,name,linked=True,multi=True);p.evaluate('occasionalTest.prepare(true)');legacy.choose(p);p.evaluate('correctionTest.legacy();correctionTest.anotherLegacy()')
 handle=p.get_by_role('button',name='Reorder Occasional curry within Wednesday',exact=True);handle.focus();p.keyboard.press('ArrowUp')
 assert p.evaluate('document.activeElement.closest(".top-recipe-wrap").dataset.scheduleDay')=='Wednesday'
 assert p.locator('.top-recipe-wrap[data-schedule-day=Wednesday] .meal').first.get_attribute('data-meal-id')=='2'
 clean(errors);c.close()

def hide_resume(browser,name):
 c,p,errors,_=setup(browser,name,multi=True)
 p.evaluate('weekTest.check();correctionTest.scale(1);correctionTest.scale(20)');before=progress(p);selections=p.evaluate('correctionTest.edits()')
 p.evaluate('weekTest.empty();weekTest.resume()')
 assert progress(p)==before,'Same-cycle Resume must retain hidden main/linked checks and scaled quantities'
 assert p.evaluate('correctionTest.edits()')==selections
 clean(errors);c.close()

if __name__=='__main__':
 reproduce=os.environ.get('MEAL_STAGE1_EXPECT_FAILURES')=='1'
 cases=[('R1 one-time Undo',lambda b,n:undo_temporary(b,n,'once')),('R1 empty Undo',lambda b,n:undo_temporary(b,n,'empty')),('R2 unconfigured Change Meal',unconfigured),('R3 keyboard',lambda b,n:legacy_reorder(b,n,'keyboard')),('R3 pointer',lambda b,n:legacy_reorder(b,n,'pointer')),('R4 same-cycle grocery Resume',hide_resume)]
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for label,case in cases:
    try:case(browser,name)
    except AssertionError as error:
     if not reproduce:raise
     print('EXPECTED FAIL',name,label,str(error),flush=True)
    else:
     assert not reproduce,f'Expected unchanged source to reproduce {name}: {label}'
     print('PASS',name,label,flush=True)
   if not reproduce:
    for label,case in [('Undo preserves recipe edits and later checks',undo_preserves_edits),('Unconfigured Ideas, links and duplicate decisions',unconfigured_idea_and_duplicates),('Same-cycle holds vs full/selected/future rotations',grocery_cycles),('Hidden-check save failure, backup validation and deletion safety',storage_and_validation),('Legacy reorder identity remains scoped to its weekday',legacy_focus)]:
     case(browser,name);print('PASS',name,label,flush=True)
    for mode in ['keyboard','pointer']:legacy_reorder(browser,name,mode,360)
    print('PASS',name,'legacy reorder at 360px',flush=True)
  browser.close()
