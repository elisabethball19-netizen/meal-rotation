"""Per-occurrence grocery checks across rotation, using isolated synthetic data."""
import copy,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import rows,state,compose,context_key,definitions
fixture.HOOK+='''window.groceryTest={
 rows:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,quantity:item.quantity,checked:groceryItemChecked(key,item),sources:item.contributions.map(source=>({...source,checked:grocerySourceChecked(source)}))})),
 ledger:()=>groceryOccurrenceChecks,
 legacy:key=>{checkedIngredients.add(key);localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))},
 view:()=>{showTop=true;allMealsActive=false;groceryTabActive=true;renderList()},
 my:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;renderList()},
 all:all=>moveDisplayedMealsToBottom(null,all),
 check:(key,value)=>{const items=getMasterGroceryItems();setGroceryItemChecked(key,items.get(key),value);localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))},
 plan:id=>loadMealPlan(id),tabs:value=>{showMealPlanTabs=value;renderList()},
 breakfast:()=>{mealPlans.push({id:'breakfast',name:'Breakfast',weekdayCategories:{Thursday:['Sides']},weekdayMealOverrides:{'Thursday::Sides':'10'},cycleRetainedSlots:{'Thursday::Sides':'10'},weekdayRecipeFilters:{},pinnedCats:[]});saveActiveMealPlan();renderList()},
 exclude:value=>{if(value)masterGroceryExcludedPlanIds.add('lunch');else masterGroceryExcludedPlanIds.delete('lunch');saveMasterGroceryPlanExclusions();renderList()},
 edit:(id,line)=>{editTopRecipeIngredient(meals.find(m=>m.id===id),line)},
 renameGroup:()=>{renameCategoryDirect('Rice')},
 chooser:id=>openTopIngredientChooser(meals.find(m=>m.id===id)),
 undo:()=>{if(history.length){redoHistory.push(captureState());restoreState(JSON.parse(history.pop()))}},
 oldHistory:()=>{const old=readPreviousRotation();delete old.groceryOccurrenceChecks;localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify(old))},
 single:()=>{meals=meals.filter(m=>m.id===1);meals[0].linkedMealIds=[];cats=['Rice'];weekdayCategories={Tuesday:['Rice'],Friday:['Rice']};weekdayMealOverrides={};mealPlans=[{id:'original',name:'Dinner',weekdayCategories,weekdayMealOverrides:{},weekdayRecipeFilters:{},pinnedCats:[]}];activePlanId='original';saveActiveMealPlan();renderList()},
 extras:()=>{for(const m of meals){m.ingredients.push('Salt to taste');m.ingredients.push('1/2 cup beans')}const chosen=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const m of meals)chosen[m.id]=m.ingredients;localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(chosen));persist();renderList()}
};'''
BASE='quantity:["cup","rice"]'

def groceries(p):return p.evaluate('groceryTest.rows()')
def sources(p):return {s['id']:s for r in groceries(p) for s in r['sources']}
def total(p,checked=None,name='rice'):
 return sum(row['quantity']['lo'] for row in groceries(p) if row['quantity'] and row['quantity']['name']==name and (checked is None or row['checked']==checked))
def prepare(browser,filename,width,linked=True):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=linked,duplicate=True,multi=True);p.set_default_timeout(8000);p.evaluate('groceryTest.breakfast()');p.evaluate('slotTest.seed()');return ctx,p,errors,prefix

def apply(p,selected):
 p.get_by_role('button',name='Rotate Meals',exact=True).tap();p.get_by_role('button',name='Select recipes to rotate out',exact=True).tap();d=p.get_by_role('heading',name='Select meals to rotate out').locator('..');d.get_by_role('button',name='Deselect all',exact=True).tap()
 for name in selected:d.get_by_role('checkbox',name=name,exact=True).check()
 d.get_by_role('button',name='Move selected',exact=True).tap()

def unchanged_data(before,after,p,selection):
 assert definitions(before)==definitions(after) and before['prefs']==after['prefs']
 assert [x['weekdayCategories'] for x in before['plans']]==[x['weekdayCategories'] for x in after['plans']]
 assert p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']==selection

def compare_transition(before,after,reset_slots):
 for id,item in after.items():
  reset=(item['planId'],item['day'],item['cat']) in reset_slots
  if id in before and not reset:assert item['checked']==before[id]['checked'] and item['quantity']==before[id]['quantity'],('retained source changed',before[id],item)
  else:assert item['checked'] is False,('new source inherited checks',item)
 assert all(id in after for id,item in before.items() if (item['planId'],item['day'],item['cat']) not in reset_slots and item['planId']!='original')

def run(browser,filename,width):
 ctx,p,errors,prefix=prepare(browser,filename,width);p.evaluate('groceryTest.legacy',BASE)
 before=state(p);before_sources=sources(p);original=compose(p);selected=p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1'];assert all(s['checked'] for s in before_sources.values())
 apply(p,['Tuesday · Rice — Thai Garlic Pork']);after_sources=sources(p)
 compare_transition(before_sources,after_sources,{('original','Tuesday','Rice'),('original','Tuesday','Sauces')})
 retained=[s for id,s in after_sources.items() if id in before_sources];new=[s for id,s in after_sources.items() if id not in before_sources]
 assert new and retained and all(s['checked'] for s in retained) and all(not s['checked'] for s in new)
 assert len(groceries(p))==2 and total(p,True)==sum(s['quantity']['lo'] for s in retained) and total(p,False)==sum(s['quantity']['lo'] for s in new)
 assert next(s for s in retained if s['planId']=='original' and s['day']=='Friday' and s['mealId']==1)['checked']
 unchanged_data(before,state(p),p,selected)
 for r in rows(p):
  if r['planId']!='original' or r['day']!='Tuesday':
   key=context_key(r);assert state(p)['sessions']['occurrences'][key]==before['sessions']['occurrences'][key];assert state(p)['scales']['occurrences'][key]==before['scales']['occurrences'][key]
 expected=groceries(p);p.reload();assert groceries(p)==expected
 # Hidden/excluded tabs preserve their source state when later restored.
 p.evaluate('groceryTest.exclude(true)');p.evaluate('groceryTest.exclude(false)');assert groceries(p)==expected
 p.evaluate('groceryTest.tabs(false)');assert all(s['planId']=='original' for s in sources(p).values());p.evaluate('groceryTest.tabs(true)');assert groceries(p)==expected
 # Hide Selected removes only the checked portion, not the incoming quantity.
 p.evaluate('groceryTest.view()');assert p.locator('.master-grocery-item').count()==2
 p.get_by_role('button',name='Hide checked groceries',exact=True).tap();assert p.locator('.master-grocery-item').count()==1
 p.get_by_role('button',name='Show checked groceries',exact=True).tap();assert p.locator('.master-grocery-item').count()==2
 if filename=='meal-rotation-test.html' and width==360:p.screenshot(path='/tmp/grocery-preserve-split-test-360.png')
 # Checkbox toggles and Select All/Deselect All still operate on the shown quantities.
 p.locator('.master-grocery-item').filter(has=p.locator('input:not(:checked)')).get_by_role('checkbox').tap();assert len(groceries(p))==1 and all(s['checked'] for s in sources(p).values())
 p.get_by_role('button',name='Deselect all groceries',exact=True).tap();assert not any(s['checked'] for s in sources(p).values())
 p.get_by_role('button',name='Select all groceries',exact=True).tap();assert all(s['checked'] for s in sources(p).values())
 p.evaluate('groceryTest.undo()');assert not any(s['checked'] for s in sources(p).values())
 # Full Cycle Back restores the pre-rotation checks and exact schedule.
 p.evaluate('groceryTest.my()');p.evaluate('slotTest.back()');assert compose(p)==original,('schedule',compose(p),original)
 assert set(sources(p))==set(before_sources) and all(sources(p)[id]['checked']==old['checked'] for id,old in before_sources.items())
 # Original ingredient-key backups/snapshots remain compatible.
 p.evaluate('groceryTest.all(false)');p.evaluate('groceryTest.oldHistory()');p.evaluate('slotTest.back()');assert compose(p)==original and all(s['checked'] for s in sources(p).values())
 # Partial Cycle Back restores old selected checks and preserves newly edited retained checks.
 apply(p,['Tuesday · Rice — Thai Garlic Pork']);p.evaluate('groceryTest.view()');p.get_by_role('button',name='Deselect all groceries',exact=True).tap();p.evaluate('groceryTest.my()')
 p.evaluate('slotTest.partial(["original||Tuesday::Rice"])');assert next(s for s in sources(p).values() if s['planId']=='original' and s['day']=='Tuesday' and s['mealId']==1)['checked']
 assert not next(s for s in sources(p).values() if s['planId']=='breakfast')['checked']
 # Backup roundtrip retains both checked and unchecked portions.
 saved=p.evaluate('slotTest.storage()');backup={**json.loads(saved['mealRotationDataV1']),'version':2,'storage':saved};expected=groceries(p);p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload();assert groceries(p)==expected
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',filename,width,'partial legacy/shared checks, repeated/cross-plan retention, split quantities, hidden/excluded tabs, controls/Undo/history/partial+full Cycle Back, reload/backups/progress/settings',flush=True)


def full_and_repeat(browser,filename,width):
 ctx,p,errors,prefix=prepare(browser,filename,width);p.evaluate('groceryTest.extras()');p.evaluate('groceryTest.legacy',BASE);p.evaluate('groceryTest.legacy','unmeasured:salt to taste');p.evaluate('groceryTest.legacy','quantity:["cup","bean"]')
 before=sources(p);p.evaluate('groceryTest.all(false)');after=sources(p)
 assert all(not s['checked'] for s in after.values() if s['planId']=='original')
 assert all(s['checked']==before[id]['checked'] for id,s in after.items() if s['planId']!='original')
 assert any(r['quantity'] is None for r in groceries(p))
 p.evaluate('groceryTest.plan("lunch")');p.evaluate('groceryTest.all(false)');assert all(not s['checked'] for s in sources(p).values() if s['planId']=='lunch')
 p.evaluate('groceryTest.plan("breakfast")');p.evaluate('groceryTest.all(false)');assert all(not s['checked'] for s in sources(p).values() if s['planId']=='breakfast')
 # Explicit all-tab rotation resets every incoming source, including shared IDs.
 p.evaluate('groceryTest.view()');p.get_by_role('button',name='Select all groceries',exact=True).tap();p.evaluate('groceryTest.all(true)');assert not any(s['checked'] for s in sources(p).values())
 p.reload();assert not any(s['checked'] for s in sources(p).values());assert not errors,errors;ctx.close()
 ctx,p,errors,prefix=prepare(browser,filename,width,False);p.evaluate('groceryTest.single()');p.evaluate('slotTest.seed()');p.evaluate('groceryTest.legacy',BASE)
 initial=sources(p);apply(p,['Tuesday · Rice — Thai Garlic Pork']);now=sources(p);assert len(initial)==len(now)==2
 assert not next(s for s in now.values() if s['day']=='Tuesday')['checked'] and next(s for s in now.values() if s['day']=='Friday')['checked']
 assert len(groceries(p))==2
 p.evaluate('groceryTest.oldHistory()');p.evaluate('slotTest.partial(["original||Tuesday::Rice"])');assert all(s['checked'] for s in sources(p).values())
 p.evaluate('groceryTest.all(false)');assert not any(s['checked'] for s in sources(p).values());assert not errors,errors;ctx.close()
 print('PASS',filename,width,'full rotations, Breakfast/Lunch/Dinner/all-tabs, unmeasured/fraction ingredients, single-recipe repeats with independent checks',flush=True)


def edits_and_links(browser,filename,width):
 ctx,p,errors,prefix=prepare(browser,filename,width);p.evaluate('groceryTest.legacy',BASE)
 # Rotate both main and independently scheduled side: the new linked side wins unchecked.
 before=sources(p);apply(p,['Tuesday · Rice — Thai Garlic Pork','Tuesday · Sides — Garlic Jasmine Rice with Cauliflower']);now=sources(p)
 assert any(s['mealId']==12 and s['day']=='Tuesday' and not s['checked'] for s in now.values())
 assert all(s['checked'] for s in now.values() if s['planId']!='original' or s['day']=='Friday')
 # Rename an unchecked source to an existing checked ingredient; it must stay unchecked.
 p.evaluate('groceryTest.edit(2,"2 cups rice")');d=p.get_by_role('dialog',name='Edit ingredient');d.get_by_role('textbox',name='Ingredient').fill('3 cups rice');d.get_by_role('button',name='Save ingredient',exact=True).tap()
 assert all(not s['checked'] for s in sources(p).values() if s['mealId']==2 and s['day']=='Tuesday')
 # Quantity edits preserve checked state for every retained occurrence of that meal.
 p.evaluate('groceryTest.edit(10,"10 cups rice")');d=p.get_by_role('dialog',name='Edit ingredient');d.get_by_role('textbox',name='Ingredient').fill('15 cups rice');d.get_by_role('button',name='Save ingredient',exact=True).tap()
 assert all(s['checked'] for s in sources(p).values() if s['mealId']==10)
 # Grocery membership chooser Save/Cancel retains source states; reselected ingredients start unchecked.
 expected=groceries(p);p.evaluate('groceryTest.chooser(10)');p.get_by_role('button',name='Cancel',exact=True).tap();assert groceries(p)==expected
 p.evaluate('groceryTest.chooser(10)');d=p.get_by_role('heading',name='Add ingredients to grocery list').locator('..');d.get_by_role('button',name='Save',exact=True).tap();assert groceries(p)==expected
 p.evaluate('groceryTest.chooser(10)');d=p.get_by_role('heading',name='Add ingredients to grocery list').locator('..');d.get_by_role('checkbox').first.tap();d.get_by_role('checkbox').first.tap();d.get_by_role('button',name='Save',exact=True).tap()
 assert all(not s['checked'] for s in sources(p).values() if s['mealId']==10)
 expected=groceries(p);p.reload();assert groceries(p)==expected
 assert not errors,errors;ctx.close();print('PASS',filename,width,'linked priority/removal, retained repeated links, manual quantity edits/rename, grocery chooser Cancel, reload',flush=True)

def mixed_legacy_and_rename(browser,filename,width):
 ctx,p,errors,prefix=prepare(browser,filename,width);p.evaluate('groceryTest.legacy','10 cups rice');initial=sources(p)
 assert any(s['checked'] for s in initial.values()) and any(not s['checked'] for s in initial.values())
 apply(p,['Tuesday · Rice — Thai Garlic Pork']);after=sources(p);compare_transition(initial,after,{('original','Tuesday','Rice'),('original','Tuesday','Sauces')})
 p.evaluate('groceryTest.renameGroup()');d=p.get_by_role('dialog');d.get_by_role('textbox').fill('Rice renamed');d.get_by_role('button',name='Save',exact=True).tap();p.wait_for_timeout(50)
 assert {id:s['checked'] for id,s in sources(p).items()}=={id:s['checked'] for id,s in after.items()}
 # Invalid optional grocery metadata is rejected before changing storage.
 saved=p.evaluate('slotTest.storage()');bad={**json.loads(saved['mealRotationDataV1']),'version':2,'storage':dict(saved)}
 bad['storage']['mealRotationGroceryOccurrenceChecksV1']=json.dumps({'version':1,'checks':{'not a valid source':True}})
 rejected=False
 try:p.evaluate('(b)=>slotTest.restore(b)',bad)
 except Exception as error:rejected='Invalid grocery source' in str(error)
 assert rejected and p.evaluate('slotTest.storage()')==saved
 assert not errors,errors;ctx.close();print('PASS',filename,width,'mixed legacy line checks, retained unchecked portions, group rename stability, invalid-backup rejection without writes',flush=True)

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  # Verify isolated test app first, then regular app with the same fixtures.
  for filename in ['meal-rotation-test.html','index.html']:
   for width in [320,360]:
    run(b,filename,width);full_and_repeat(b,filename,width);edits_and_links(b,filename,width);mixed_legacy_and_rename(b,filename,width)
  b.close()

