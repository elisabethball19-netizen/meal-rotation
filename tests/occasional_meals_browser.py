"""One-time weekdays, compact chooser and menu order, isolated mobile storage."""
import json
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import rows,state,compose,definitions,context_key
fixture.HOOK+='''window.occasionalTest={
 prepare:tabs=>{showMealPlanTabs=tabs;meals.find(m=>m.id===2).name='Occasional curry';meals.find(m=>m.id===2).rotation=false;meals.find(m=>m.id===12).rotation=false;for(const m of meals)m.ingredients=['1 cup rice','Salt to taste'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));persist();render();for(const s of getGroceryContributions(true)){checkedIngredients.add(s.baseKey);groceryOccurrenceChecks.checks[s.id]=true}saveGroceryOccurrenceChecks();localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))},
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 checkMonday:()=>{for(const s of getGroceryContributions(true))if(s.day==='Monday'&&s.planId===activePlanId)groceryOccurrenceChecks.checks[s.id]=s.mealId===2;saveGroceryOccurrenceChecks()},
 overview:()=>{allMealsActive=true;groceryTabActive=false;renderList()},my:()=>{allMealsActive=false;groceryTabActive=false;renderList()},
 full:()=>moveDisplayedMealsToBottom(),groceries:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,checked:groceryItemChecked(key,item),quantity:item.quantity})),
 groups:(day,groups)=>setDayCategories(day,groups),tabs:value=>{showMealPlanTabs=value;render()},
 settings:()=>{settings.click()},draft:()=>{settingsBaseline=captureSettingsDraft()},cancelDraft:()=>{restoreSettingsDraft(settingsBaseline);settingsBaseline=null;render()},
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))}
};'''
def source_states(p):return {s['id']:(s['checked'],s['line']) for s in p.evaluate('occasionalTest.sources()')}
def meal(p,day='Monday',plan='original'):return [r for r in rows(p) if r['day']==day and r['planId']==plan]
def h(p,day='Monday'):return p.locator(f'button.weekday-heading[data-weekday={day}]')
def plan(p,day='Monday'):
 h(p,day).tap();return p.get_by_role('dialog',name=f"Plan {day}'s meal",exact=True)
def choose(p,id=2,day='Monday',decision=None):
 d=plan(p,day);d.get_by_role('button',name='Choose a meal',exact=True).tap();c=p.get_by_role('dialog',name=f"Choose {day}'s meal",exact=True)
 c.get_by_role('button',name='Search recipes',exact=True).tap();c.get_by_role('searchbox').fill('Occasional curry' if id==2 else 'Thai Garlic Pork');c.locator(f'[data-meal-id="{id}"]').tap();c.get_by_role('button',name='Save',exact=True).tap()
 if decision:
  d=p.get_by_role('dialog',name=('Occasional curry' if id==2 else 'Thai Garlic Pork')+' is already planned',exact=True)
  if d.get_by_role('combobox').count():d.get_by_role('combobox').select_option(label='Tuesday · Rice')
  d.get_by_role('button',name=decision,exact=True).tap()
 return c

def run(browser,filename,width,tabs):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.set_default_timeout(8000);p.evaluate('occasionalTest.prepare',tabs);p.evaluate('slotTest.seed()');base=state(p);scheduled=compose(p);before=source_states(p);saved=p.evaluate('slotTest.storage()')
 # Both empty heading and message, and the full blank area, offer exactly the two actions.
 for target in [h(p),p.locator('[data-weekday=Monday]+.empty-weekday-meal')]:
  target.tap();d=p.get_by_role('dialog',name="Plan Monday's meal",exact=True);assert d.get_by_role('button').all_text_contents()[1:]==['Choose a meal','Choose meal groups'];d.get_by_role('button',name='Close',exact=True).tap();assert p.evaluate('slotTest.storage()')==saved
 d=plan(p,'Wednesday');d.get_by_role('button',name='Close',exact=True).tap()
 choose(p);assert {r['id'] for r in meal(p)}=={2,12}
 assert state(p)['plans'][0]['weekdayCategories']==base['plans'][0]['weekdayCategories'];assert definitions(state(p))==definitions(base)
 assert p.locator('[data-weekday=Monday]+.empty-weekday-meal').count()==0
 added=source_states(p)
 for id,entry in added.items():assert entry==before[id] if id in before else entry[0] is False
 p.evaluate('slotTest.seed()');p.evaluate('occasionalTest.checkMonday()');monday={k:v for k,v in source_states(p).items() if json.loads(json.loads(k)[0])[1]=='Monday'};cooking=state(p)
 # Background and heading open planning, but the recipe name opens its normal options.
 wrap=p.locator('[data-weekday=Monday]+.top-recipe-wrap');r=wrap.bounding_box();wrap.tap(position={'x':r['width']-3,'y':r['height']-3});d=p.get_by_role('dialog',name="Plan Monday's meal",exact=True);d.get_by_role('button',name='Close',exact=True).tap()
 p.locator('[data-weekday=Monday]+.top-recipe-wrap .mealname').tap();menu=p.get_by_role('dialog',name='Meal options for Monday',exact=True)
 assert menu.get_by_role('button').all_text_contents()[1:]==['Open recipe','Change meal','Edit meal','Edit grocery list','Edit last cooked date']
 menu.get_by_role('button',name='Change meal',exact=True).tap();c=p.get_by_role('dialog',name="Choose Monday's meal",exact=True);assert c.get_by_role('button',name='Remove one-time meal',exact=True).is_visible();c.get_by_role('button',name='Cancel',exact=True).tap()
 # Regular assigned day retains direct heading/group behavior and compact chooser styling.
 h(p,'Tuesday').tap();p.get_by_role('dialog',name="Choose Tuesday's meal groups",exact=True).get_by_role('button',name='Close',exact=True).tap()
 p.locator('[data-weekday=Tuesday]+.top-recipe-wrap .mealname').tap();p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Change meal',exact=True).tap();c=p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True)
 assert c.locator('.master-category-title').first.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(245, 245, 245)'
 item=c.locator('.weekday-meal-choice').first;assert item.bounding_box()['height']>=44 and item.evaluate('(e)=>getComputedStyle(e).marginTop')=='0px'
 assert item.evaluate('(e)=>getComputedStyle(e).borderBottomColor')=='rgb(238, 238, 238)'
 if filename.startswith('meal-') and width==360 and tabs:p.screenshot(path='/tmp/occasional-chooser.png')
 c.get_by_role('button',name='Cancel',exact=True).tap()
 # One-time meals are excluded from Cycle Meals and survive normal/full cycles and Cycle Back.
 p.evaluate('slotTest.open()');d=p.get_by_role('heading',name='Select meals to rotate out').locator('..');assert 'Occasional curry' not in d.inner_text();d.get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('slotTest.cycle(["Tuesday::Rice"])');assert {r['id'] for r in meal(p)}=={2,12}
 for k,v in monday.items():assert source_states(p)[k]==v
 for r in meal(p):
  key=context_key(r);assert state(p)['sessions']['occurrences'][key]==cooking['sessions']['occurrences'][key] and state(p)['scales']['occurrences'][key]==cooking['scales']['occurrences'][key]
 p.evaluate('slotTest.back()');assert {r['id'] for r in meal(p)}=={2,12}
 p.evaluate('occasionalTest.full()');assert {r['id'] for r in meal(p)}=={2,12};p.evaluate('slotTest.back()')
 p.reload();assert {r['id'] for r in meal(p)}=={2,12}
 for k,v in monday.items():assert source_states(p)[k]==v
 p.evaluate('occasionalTest.overview()');assert 'Occasional curry' in p.locator('#list').inner_text();p.evaluate('occasionalTest.my()')
 assert any(r['checked'] for r in p.evaluate('occasionalTest.groceries()')) and any(not r['checked'] for r in p.evaluate('occasionalTest.groceries()'))
 # Complete backup roundtrip preserves occasional scheduling and occurrence checks.
 storage=p.evaluate('slotTest.storage()');backup={**json.loads(storage['mealRotationDataV1']),'version':2,'storage':storage};p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload();assert {r['id'] for r in meal(p)}=={2,12}
 for k,v in monday.items():assert source_states(p)[k]==v
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',filename,width,tabs,'menu order, compact chooser, empty/card/name taps, one-time links/Ideas/progress/scaling, regular cycles/back, overview/groceries/reload/backup',flush=True);ctx.close()

def assignment(browser,filename,width,group):
 ctx,p,errors,_=fixture.setup(browser,filename,width,linked=True,multi=True);p.evaluate('occasionalTest.prepare',True);choose(p);p.evaluate('slotTest.seed()');p.evaluate('occasionalTest.checkMonday()');old=source_states(p);before=state(p)
 d=plan(p);d.get_by_role('button',name='Choose meal groups',exact=True).tap();d=p.get_by_role('dialog',name="Choose Monday's meal groups",exact=True);d.locator(f'input[data-group-choice][value="{group}"]').check();d.get_by_role('button',name='Close',exact=True).tap()
 assert next(r for r in meal(p) if r['cat']==group)['id']==(12 if group=='Sides' else 2)
 assert state(p)['plans'][0]['weekdayCategories']['Monday']==[group] 
 if group=='Sides':assert {r['id'] for r in meal(p)}=={2,12} and state(p)['plans'][0]['occasionalMeals']['Monday']=='2'
 else:assert state(p)['plans'][0]['occasionalMeals']['Monday']=='2'
 for source in p.evaluate('occasionalTest.sources()'):
  token=json.loads(source['id']);match=next((v for k,v in old.items() if json.loads(json.loads(k)[0])[:3]==json.loads(token[0])[:3] and json.loads(k)[1:]==token[1:]),None)
  if match:assert (source['checked'],source['line'])==match
 for r in meal(p):
  if r['id']==2:key=context_key(r);assert state(p)['sessions']['occurrences'][key]==before['sessions']['occurrences'][key]
 p.evaluate('occasionalTest.full()');assert any(r['id']==2 for r in meal(p));p.evaluate('slotTest.back()')
 p.reload();assert next(r for r in meal(p) if r['cat']==group)['id']==(12 if group=='Sides' else 2)
 h(p).tap();assert p.get_by_role('dialog',name="Choose Monday's meal groups",exact=True).is_visible()
 assert not errors,errors
 print('PASS',filename,width,'assign permanent',group,'keeps planned substitution, progress and grocery checks',flush=True);ctx.close()

def remove(browser,filename,width):
 ctx,p,errors,_=fixture.setup(browser,filename,width,linked=True,multi=True);p.evaluate('occasionalTest.prepare',True);choose(p);d=plan(p);d.get_by_role('button',name='Choose a meal',exact=True).tap();c=p.get_by_role('dialog',name="Choose Monday's meal",exact=True);c.get_by_role('button',name='Remove one-time meal',exact=True).tap();p.get_by_role('button',name='Yes',exact=True).tap()
 assert not meal(p) and not state(p)['plans'][0]['weekdayCategories'].get('Monday') and next(m for m in state(p)['meals'] if m['id']==2)['rotation'] is False
 assert not errors,errors
 print('PASS',filename,width,'manual removal leaves recipe definitions and weekday assignments intact',flush=True);ctx.close()

def duplicates(browser,filename,width,choice,from_occasional=False):
 ctx,p,errors,_=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.evaluate('occasionalTest.prepare',True)
 if from_occasional:choose(p);p.evaluate('occasionalTest.checkMonday()')
 old=p.evaluate('occasionalTest.sources()');before=compose(p);assigned=state(p)['plans'][0]['weekdayCategories'];storage=p.evaluate('slotTest.storage()');day='Wednesday' if from_occasional else 'Monday';source_day='Monday' if from_occasional else 'Tuesday'
 decision='Close' if choice=='cancel' else ('No — Keep both meals' if choice=='no' else "Yes — Replace "+source_day+"'s meal")
 choose(p,2 if from_occasional else 1,day,decision)
 if choice=='cancel':assert compose(p)==before and p.evaluate('slotTest.storage()')==storage
 else:
  id=2 if from_occasional else 1;assert any(r['id']==id for r in meal(p,day))
  if choice=='no':assert any(r['id']==id for r in meal(p,source_day))
  elif from_occasional:assert not meal(p,source_day)
  else:assert all(r['id']!=1 for r in meal(p,'Tuesday','original'))
  for source in p.evaluate('occasionalTest.sources()'):
   if source['day']==day and source['planId']=='original':
    if choice=='no':assert source['checked'] is False
    else:
     token=json.loads(source['id']);previous=next(s for s in old if s['day']==source_day and s['planId']=='original' and s['mealId']==source['mealId'] and json.loads(s['id'])[1:]==token[1:]);assert source['checked']==(False if source['mealId']!=id and previous['cat'] in assigned.get(source_day,[]) else previous['checked'])
  if choice=='yes' and not from_occasional:p.evaluate('slotTest.back()');assert compose(p)==before
  p.reload()
 assert not errors,errors;ctx.close();print('PASS',filename,width,'duplicate',choice,'occasional source' if from_occasional else 'assigned source','occurrence groceries and history',flush=True)

def cancel_settings(browser,filename):
 ctx,p,errors,_=fixture.setup(browser,filename,320,linked=True,multi=True);p.evaluate('occasionalTest.prepare',True);choose(p);p.evaluate('occasionalTest.checkMonday()');before=source_states(p);schedule=compose(p);recipes=definitions(state(p))
 p.evaluate('occasionalTest.draft()');p.evaluate("occasionalTest.groups('Monday',['Sides'])");p.evaluate('occasionalTest.cancelDraft()')
 assert compose(p)==schedule and source_states(p)==before and definitions(state(p))==recipes and not errors,errors
 print('PASS',filename,'Settings Cancel restores occasional plan/checks without changing recipe rotation flags',flush=True);ctx.close()

def transitions(browser,filename,width):
 ctx,p,errors,_=fixture.setup(browser,filename,width,linked=True,multi=True);p.evaluate('occasionalTest.prepare',True);choose(p);p.evaluate('slotTest.seed()');p.evaluate('occasionalTest.checkMonday()');old=source_states(p);recipes=definitions(state(p))
 for groups in [['Rice'],['Rice','Sides'],['Sides'],[]]:
  p.evaluate('(groups)=>occasionalTest.groups("Monday",groups)',groups)
  assert {r['id'] for r in meal(p)}=={2,12}
  assert definitions(state(p))==recipes
  for source in p.evaluate('occasionalTest.sources()'):
   token=json.loads(source['id']);match=next((v for k,v in old.items() if json.loads(json.loads(k)[0])[:3]==json.loads(token[0])[:3] and json.loads(k)[1:]==token[1:]),None)
   assert match and (source['checked'],source['line'])==match
 p.evaluate('occasionalTest.groups("Monday",["Rice"])')
 # A protected occurrence with an assigned group still uses the existing duplicate replacement path.
 schedule=compose(p);choose(p,2,'Wednesday',"Yes — Replace Monday's meal");assert any(r['id']==2 for r in meal(p,'Wednesday')) and all(r['id']!=2 for r in meal(p,'Monday'))
 p.evaluate('slotTest.back()');assert compose(p)==schedule
 # Change, cycle and remove the protected assigned-slot meal without altering recipe definitions.
 p.locator('[data-weekday=Monday]+.top-recipe-wrap .mealname').tap();p.get_by_role('dialog',name='Meal options for Monday',exact=True).get_by_role('button',name='Change meal',exact=True).tap();d=p.get_by_role('dialog',name="Choose Monday's meal",exact=True)
 d.locator('[data-meal-id="3"]').tap();d.get_by_role('button',name='Save',exact=True).tap();assert any(r['id']==3 for r in meal(p))
 p.evaluate('occasionalTest.full()');assert any(r['id']==3 for r in meal(p))
 p.locator('[data-weekday=Monday]+.top-recipe-wrap .mealname').tap();p.get_by_role('dialog',name='Meal options for Monday',exact=True).get_by_role('button',name='Change meal',exact=True).tap();p.get_by_role('button',name='Remove one-time meal',exact=True).tap();p.get_by_role('button',name='Yes',exact=True).tap()
 assert 'Monday' not in state(p)['plans'][0].get('occasionalMeals',{}) and state(p)['plans'][0]['weekdayCategories']['Monday']==['Rice']
 # Malformed optional plan records are rejected before any saved data is written.
 saved=p.evaluate('slotTest.storage()');backup={**json.loads(saved['mealRotationDataV1']),'version':2,'storage':dict(saved)};plans=json.loads(saved['mealRotationPlansV1']);plans['plans'][0]['occasionalMeals']=[];backup['storage']['mealRotationPlansV1']=json.dumps(plans)
 error=p.evaluate('(b)=>{try{slotTest.restore(b);return ""}catch(e){return e.message}}',backup);assert 'Invalid one-time meals' in error and p.evaluate('slotTest.storage()')==saved
 assert not errors,errors;print('PASS',filename,width,'successive group assignments/unassignment, protected duplicate move/back, change/cycle/removal, malformed-backup rejection',flush=True);ctx.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for tabs in [True,False]:run(b,filename,width,tabs)
    for group in ['Rice','Sauces','Sides']:assignment(b,filename,width,group)
    remove(b,filename,width)
    transitions(b,filename,width)
    for origin in [False,True]:
     for choice in ['yes','no','cancel']:duplicates(b,filename,width,choice,origin)
   cancel_settings(b,filename)
  b.close()
