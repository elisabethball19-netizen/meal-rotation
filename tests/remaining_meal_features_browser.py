"""Scoped side restoration, occurrence groceries, full shared creation and popup favorites."""
from playwright.sync_api import sync_playwright
import same_day_group_assignment_browser as base
f=base.f
f.EXTRA+='''window.remainingTest={
 seed:()=>{sameDay.seed(false);const selected=Object.fromEntries(meals.map(m=>[m.id,m.ingredients]));localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));groceryOccurrenceChecks={version:1,checks:{}};checkedIngredients.clear();persist();promotionTest.my()},
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 check:(day,cat)=>{for(const s of getGroceryContributions(true))if(s.day===day&&s.cat===cat)groceryOccurrenceChecks.checks[s.id]=true;saveGroceryOccurrenceChecks()},
 legacyOrder:()=>{const plan=mealPlans[0];weekdayMealOverrides['Saturday::Lunch']='537';plan.weekdayMealOverrides={...weekdayMealOverrides};plan.cycleSlotChoices['Saturday::Lunch']={mealId:'537',substitution:true};plan.cycleSlotChoices['Saturday::Weekend'].retain=true;delete plan.weekSchedule.slots['Saturday::Lunch'];plan.weekSchedule.order.Saturday=['["Lunch"]','["Weekend"]','["Breakfast"]'];saveActiveMealPlan();renderList()},
 legacy:()=>{const s=getGroceryContributions(true).find(s=>s.mealId===537);groceryOccurrenceChecks={version:1,checks:{[s.legacyId]:true}};saveGroceryOccurrenceChecks()},
 duplicate:()=>applyManualWeekdayMeal('Saturday','Lunch',meals.find(m=>m.id===537)),
 sunday:()=>{setDayCategories('Sunday',['Weekend']);applyManualWeekdayMeal('Sunday','Weekend',meals.find(m=>m.id===537))},
 anotherTab:()=>{const plan={id:'second',name:'Other',weekdayCategories:{},weekdayMealOverrides:{},cycleSlotChoices:{},cycleRetainedSlots:{},weekdayRecipeFilters:{},pinnedCats:[]};mealPlans.push(plan);withSchedulingPlan('second',()=>{setDayCategories('Sunday',['Weekend']);applyManualWeekdayMeal('Sunday','Weekend',meals.find(m=>m.id===537))});saveActiveMealPlan();persist()},
 clear:()=>leaveWeekEmpty('Saturday','Lunch'),
 sides:assigned=>{remainingTest.seed();const p=meals.find(m=>m.id===537);p.name='Pernil';p.linkedMealIds=[25,26,25];meals.find(m=>m.id===25).name='Pernil rice ala Moi';meals.find(m=>m.id===25).ingredients=['2 cups rice'];meals.push({id:26,cat:'Bread',name:'Extra linked side',rotation:false,keepAsIdea:true,ingredients:['1 cup beans']});if(assigned)setDayCategories('Saturday',['Weekend','Bread']);setDayCategories('Sunday',['Weekend']);applyManualWeekdayMeal('Sunday','Weekend',p);localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));persist();promotionTest.my()},
 legacyHeld:()=>{remainingTest.sides(true);remainingTest.check('Saturday','Bread');remainingTest.hide();const plan=mealPlans[0],slot=plan.weekSchedule.slots['Saturday::Bread'];slot.groceryChecks=Object.fromEntries(Object.entries(slot.groceryChecks).map(([id,checked])=>{const key=JSON.parse(id);key[0]=JSON.stringify(JSON.parse(key[0]).slice(0,4));return [JSON.stringify(key),checked]}));delete plan.weekSchedule.linkedGroceryChecks;localStorage.removeItem('mealRotationLastRotationBeforeV1');saveActiveMealPlan()},
 legacyHide:()=>{remainingTest.sides(true);remainingTest.check('Saturday','Bread');const state=JSON.parse(captureState());state.groceryOccurrenceChecks.checks=Object.fromEntries(Object.entries(state.groceryOccurrenceChecks.checks).map(([id,value])=>{const source=JSON.parse(id);source[0]=JSON.stringify(JSON.parse(source[0]).slice(0,4));return [JSON.stringify(source),value]}));state.cookingCycledContexts=[{planId:'original',day:'Saturday',cat:'Bread',mealId:'25',parentId:'537',exact:true}];remainingTest.hide();const plan=mealPlans[0];delete plan.weekSchedule.linkedGroceryChecks;delete plan.weekSchedule.slots['Saturday::Bread'].groceryChecks;localStorage.setItem('mealRotationLastRotationBeforeV1',JSON.stringify(state));saveActiveMealPlan()},
 savedLibrary:()=>JSON.parse(localStorage.getItem('mealRotationDataV1')).meals,
 hide:()=>leaveWeekEmpty('Saturday','Bread'),
 menu:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Weekend');openTopMealActionMenu(x.day,x.cat,x.meal)},
 rows:()=>getDisplayedWeekdayMeals().map(x=>[x.day,x.cat,String(x.meal.id)]),
 addSideIngredient:()=>{meals.find(m=>m.id===25).ingredients.push('3 cups broth');const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1'));selected['25'].push('3 cups broth');localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));persist()},
 creator:()=>sameDay.chooser('Lunch'),
 recipes:()=>meals.filter(m=>!m._scheduledEditorDraft),
 editTemp:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Lunch');openOneTimeMealEditor(x.day,x.cat,x.meal)},
 longName:()=>{meals.find(m=>m.id===537).name='Korean Slow-Cooker Beef Bowls with a very long descriptive meal title that wraps naturally';persist()},
 favorite:()=>meals.find(m=>m.id===537).favorite===true,
 libraryIds:()=>meals.filter(m=>!m._scheduledEditorDraft).map(m=>m.id),
 temp:()=>getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Lunch')?.meal,
 prefs:()=>({history:localStorage.getItem('mealRotationLastRotationBeforeV1'),order:mealPlans[0].weekSchedule.order})
};'''

def reveal(p,selector):
 p.locator(selector).evaluate('(e)=>{for(let a=e.parentElement;a;a=a.parentElement)if(a.tagName==="DETAILS")a.open=true}')
 button={'#ingredients':'#toggleIngredients','#recipeInstructions':'#toggleInstructions','#recipeNotes':'#toggleRecipeNotes'}.get(selector)
 if button and p.locator(button).is_visible():p.locator(button).click()

def create(p,once,name):
 p.evaluate('combinedTest.viewport();remainingTest.creator()');chooser=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True)
 assert not chooser.get_by_role('button',name='Add One-Time Meal',exact=True).count()
 chooser.get_by_role('button',name='Create New Meal',exact=True).tap()
 d=p.get_by_role('dialog',name='Create New Meal',exact=True);assert d.locator('#editor').evaluate('(e)=>e.scrollWidth<=e.clientWidth');assert p.locator('#recipeInstructions').count()==1 and p.locator('#recipeNotes').count()==1
 assert p.locator('#scheduledOneTime').is_checked() is False
 assert not any(m.get('_scheduledEditorDraft') for m in p.evaluate('remainingTest.savedLibrary()'))
 p.locator('#name').fill(name)
 reveal(p,'#prep');p.locator('#prep').fill('15 min');p.locator('#totaltime').fill('45 min')
 reveal(p,'#ingredients');p.locator('#ingredients').fill('2 cups rice\n1 cup beans')
 reveal(p,'#recipeInstructions');p.locator('#recipeInstructions').fill('Simmer for 30 minutes.')
 reveal(p,'#recipeNotes');p.locator('#recipeNotes').fill('Remember the sauce.')
 reveal(p,'#url');p.locator('#url').fill('https://example.test/recipe')
 if once:p.locator('#scheduledOneTime').check()
 page_y=p.evaluate('scrollY');p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(60);p.locator('#save').scroll_into_view_if_needed();button=p.locator('#save').bounding_box();assert button['y']+button['height']<=360;assert p.evaluate('scrollY')==page_y
 p.locator('#save').click();p.wait_for_timeout(80);p.evaluate('combinedTest.resize(800,0)')
 assert not p.get_by_role('alertdialog').count(),p.locator('body').inner_text()[-2000:]
 assert not p.locator('#editor .editor').count()
 return p.evaluate('remainingTest.temp()')

def run(browser,name,width):
 c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('remainingTest.seed();remainingTest.legacy()')
 first=p.evaluate('remainingTest.sources()');assert len(first)==1 and first[0]['checked'] is True
 p.evaluate('remainingTest.duplicate()');sources=p.evaluate('remainingTest.sources()');assert len(sources)==2
 assert next(s for s in sources if s['cat']=='Weekend')['checked'] is True and next(s for s in sources if s['cat']=='Lunch')['checked'] is False
 assert len({s['id'] for s in sources})==2
 assert sum(item['quantity']['lo'] for item in p.evaluate('promotionTest.groceries()') if item['quantity'] and 'rice' in item['line'])==2
 p.evaluate('remainingTest.sunday();remainingTest.anotherTab()');sources=p.evaluate('remainingTest.sources()');assert len(sources)==4 and sum(s['checked'] for s in sources)==1
 p.evaluate('remainingTest.clear()');sources=p.evaluate('remainingTest.sources()');assert len(sources)==3 and sum(s['checked'] for s in sources)==1
 p.reload();p.evaluate('promotionTest.my()');sources=p.evaluate('remainingTest.sources()');assert len(sources)==3 and sum(s['checked'] for s in sources)==1
 p.evaluate('promotionTest.validate()')
 p.evaluate('remainingTest.seed();remainingTest.legacy();remainingTest.legacyOrder()');old=p.evaluate('remainingTest.sources()');assert next(s for s in old if s['cat']=='Weekend')['checked'] is True and next(s for s in old if s['cat']=='Lunch')['checked'] is False
 # Inline sides sharing one group restore independently and retain the other occurrence.
 p.evaluate('remainingTest.sides(false);remainingTest.check("Saturday","Bread");remainingTest.hide()')
 assert not any(r[0]=='Saturday' and r[2] in ['25','26'] for r in p.evaluate('remainingTest.rows()'))
 p.reload();p.evaluate('promotionTest.my();remainingTest.addSideIngredient();remainingTest.menu()');d=p.get_by_role('dialog',name='Meal options for Saturday',exact=True)
 assert d.get_by_role('button',name='Restore Pernil rice ala Moi',exact=True).count()==1 and d.get_by_role('button',name='Restore Extra linked side',exact=True).count()==1
 d.get_by_role('button',name='Restore Pernil rice ala Moi',exact=True).tap();rows=p.evaluate('remainingTest.rows()');assert any(r[0]=='Saturday' and r[2]=='25' for r in rows) and not any(r[0]=='Saturday' and r[2]=='26' for r in rows)
 sources=p.evaluate('remainingTest.sources()');rice=[s for s in sources if s['day']=='Saturday' and str(s['mealId'])=='25'];assert next(s for s in rice if s['line']=='2 cups rice')['checked'] is True and next(s for s in rice if s['line']=='3 cups broth')['checked'] is False
 assert len([r for r in rows if r[0]=='Sunday' and r[2] in ['25','26']])==2
 p.evaluate('remainingTest.menu()');p.get_by_role('button',name='Restore Extra linked side',exact=True).tap();assert any(r[0]=='Saturday' and r[2]=='26' for r in p.evaluate('remainingTest.rows()'))
 p.evaluate('remainingTest.sides(true);remainingTest.hide();remainingTest.menu()');p.get_by_role('button',name='Restore Pernil rice ala Moi',exact=True).tap();assert any(r[0]=='Saturday' and r[1]=='Bread' and r[2]=='25' for r in p.evaluate('remainingTest.rows()'))
 p.evaluate('remainingTest.legacyHide();remainingTest.menu()');p.get_by_role('button',name='Restore Pernil rice ala Moi',exact=True).tap();assert all(s['checked'] for s in p.evaluate('remainingTest.sources()') if s['day']=='Saturday' and str(s['mealId'])=='25')
 p.evaluate('remainingTest.legacyHeld();remainingTest.menu()');p.get_by_role('button',name='Restore Pernil rice ala Moi',exact=True).tap();assert all(s['checked'] for s in p.evaluate('remainingTest.sources()') if s['day']=='Saturday' and str(s['mealId'])=='25')
 # Favorite heart remains inside popup and does not change assignments/queues/history.
 before=p.evaluate('remainingTest.rows()');ids=p.evaluate('remainingTest.libraryIds()');prefs=p.evaluate('remainingTest.prefs()');p.evaluate('remainingTest.menu()');d=p.get_by_role('dialog',name='Meal options for Saturday',exact=True);heart=d.locator('[data-recipe-favorite]');heart.tap();assert d.is_visible() and p.evaluate('remainingTest.favorite()') is True
 assert p.evaluate('remainingTest.rows()')==before and p.evaluate('remainingTest.libraryIds()')==ids and p.evaluate('remainingTest.prefs()')==prefs
 d.get_by_role('button',name='Close meal options',exact=True).tap();p.reload();p.evaluate('promotionTest.my();remainingTest.longName();remainingTest.menu()');d=p.get_by_role('dialog',name='Meal options for Saturday',exact=True);title=d.locator('h3').bounding_box();heart=d.locator('[data-recipe-favorite]').bounding_box();close=d.get_by_role('button',name='Close meal options',exact=True).bounding_box();assert title['x']+title['width']<=heart['x']+1 and heart['x']+heart['width']<=close['x']+1;assert d.locator('[data-recipe-favorite]').get_attribute('aria-pressed')=='true';d.locator('[data-recipe-favorite]').tap();assert p.evaluate('remainingTest.favorite()') is False;d.get_by_role('button',name='Close meal options',exact=True).tap()
 # Full-editor cancellation keeps saved data and returns to the selector.
 p.evaluate('remainingTest.seed();remainingTest.creator()');ids=p.evaluate('remainingTest.libraryIds()');chooser=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True);chooser.get_by_role('button',name='Create New Meal',exact=True).tap();p.locator('#name').fill('Canceled draft');p.locator('#scheduledOneTime').check();p.locator('#cancel').click();assert chooser.is_visible() and p.evaluate('remainingTest.libraryIds()')==ids;chooser.get_by_role('button',name='Cancel',exact=True).tap()
 # Full editor creates permanent and rich temporary meals with the same controls.
 p.evaluate('remainingTest.seed()');ids=p.evaluate('remainingTest.libraryIds()');meal=create(p,False,'Full saved meal');assert meal['name']=='Full saved meal' and meal['prep']=='15' and meal['total']=='45' and meal['notes']=='Remember the sauce.' and meal['url']=='https://example.test/recipe'
 assert len(p.evaluate('remainingTest.libraryIds()'))==len(ids)+1
 p.evaluate('remainingTest.seed()');ids=p.evaluate('remainingTest.libraryIds()');meal=create(p,True,'Rich one-time meal');assert meal['temporaryMeal'] is True and meal['rotation'] is False and meal['notes']=='Remember the sauce.' and meal['instructions']
 assert p.evaluate('remainingTest.libraryIds()')==ids
 p.reload();p.evaluate('promotionTest.my()');assert p.evaluate('remainingTest.temp().url')=='https://example.test/recipe'
 p.evaluate('remainingTest.editTemp()');reveal(p,'#recipeInstructions');assert p.locator('#recipeInstructions').input_value()=='Simmer for 30 minutes.';reveal(p,'#recipeNotes');p.locator('#recipeNotes').fill('Edited temporary notes');p.locator('#save').click();assert p.evaluate('remainingTest.temp().notes')=='Edited temporary notes';assert p.evaluate('remainingTest.temp().url')=='https://example.test/recipe'
 p.evaluate('sameDay.forward()');assert not any(r[0]=='Saturday' and r[1]=='Lunch' for r in p.evaluate('remainingTest.rows()'));p.evaluate('sameDay.back()');assert p.evaluate('remainingTest.temp().notes')=='Edited temporary notes'
 p.evaluate('promotionTest.validate()');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'legacy/scoped duplicate groceries, hidden-side restore/checks, assigned/inline sides, favorite persistence, shared full permanent/temporary editor, reload/backup, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
