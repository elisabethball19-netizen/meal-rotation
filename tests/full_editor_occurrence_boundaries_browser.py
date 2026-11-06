"""Full-editor nested controls, multiple memberships, origin tab and draft isolation."""
from playwright.sync_api import sync_playwright
import remaining_meal_features_browser as t
f=t.f
f.EXTRA+='''window.editorBoundary={
 rotatingSide:()=>{remainingTest.sides(true);setDayCategories('Sunday',[EMPTY_DAY_ASSIGNMENT]);const side=meals.find(m=>m.id===25);side.rotation=true;side.keepAsIdea=false;meals.push({id:27,cat:'Bread',name:'Next side',rotation:true,ingredients:[]});const plan=mealPlans[0];plan.cycleSlotChoices['Saturday::Bread']={mealId:'27',blockedParents:['537']};weekdayMealOverrides['Saturday::Bread']='27';plan.weekdayMealOverrides={...weekdayMealOverrides};plan.cycleRetainedSlots['Saturday::Bread']='27';advanceDependentSource(plan,side);saveActiveMealPlan();persist();renderList()},
 breadQueue:()=>meals.filter(m=>m.cat==='Bread'&&m.rotation).map(m=>m.id),
 currentPlan:()=>activePlanId,
 second:()=>{remainingTest.seed();remainingTest.anotherTab();loadMealPlan('second');setDayCategories('Saturday',['Lunch']);promotionTest.my()},
 original:()=>getDisplayedWeekdayMealsForPlan(mealPlans.find(p=>p.id==='original')).map(x=>[x.day,x.cat,String(x.meal.id)]),
 addLinkIngredient:()=>{remainingTest.seed();meals.find(m=>m.id===25).ingredients=['2 cups rice'];const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1'));selected['25']=['2 cups rice'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));persist()},
 tempMenu:()=>openTopMealActionMenu('Saturday','Lunch',remainingTest.temp()),
 newName:name=>meals.filter(m=>m.name===name&&!m._scheduledEditorDraft),
 originalChecks:()=>Object.fromEntries(getGroceryContributions(true).map(s=>[s.id,grocerySourceChecked(s)]))
};'''

def open_editor(p):
 p.evaluate('remainingTest.creator()');p.get_by_role('dialog',name="Choose Saturday's meal",exact=True).get_by_role('button',name='Create New Meal',exact=True).tap()

def run(browser,name):
 c,p,errors,prefix=f.setup(browser,name,390);p.evaluate('editorBoundary.second()');original=p.evaluate('editorBoundary.original()');open_editor(p)
 p.locator('#name').fill('Meal with two memberships');p.locator('#rotation').uncheck();p.get_by_role('button',name='Add group membership',exact=True).tap();p.locator('#categoryRows select').nth(1).select_option('Breakfast');p.locator('#save').click()
 assert p.evaluate('editorBoundary.currentPlan()')=='second'
 records=p.evaluate('editorBoundary.newName("Meal with two memberships")');assert len(records)==2 and {m['cat'] for m in records}=={'Lunch','Breakfast'} and all(m['rotation'] is False for m in records)
 assert p.evaluate('editorBoundary.original()')==original
 assert p.evaluate('remainingTest.temp().name')=='Meal with two memberships'
 open_editor(p);p.locator('#name').fill('Normal rotating meal in second tab');p.locator('#save').click();assert p.evaluate('remainingTest.temp().name')=='Normal rotating meal in second tab';assert p.evaluate('editorBoundary.original()')==original
 p.evaluate('editorBoundary.rotatingSide()');queue=p.evaluate('editorBoundary.breadQueue()');p.evaluate('remainingTest.menu()');p.get_by_role('button',name='Restore Pernil rice ala Moi',exact=True).click();assert p.evaluate('editorBoundary.breadQueue()')==queue
 # Temporary full-editor links and memberships are edited by the same nested controls.
 p.evaluate('editorBoundary.addLinkIngredient()');original_ids=p.evaluate('remainingTest.libraryIds()');open_editor(p);p.locator('#name').fill('Linked temporary meal');p.locator('#scheduledOneTime').check();p.get_by_role('button',name='Add group membership',exact=True).tap();p.locator('#categoryRows select').nth(1).select_option('Breakfast')
 t.reveal(p,'#editLinkedMeals');p.locator('#editLinkedMeals').click()
 dialog=p.get_by_role('dialog').filter(has=p.get_by_role('heading',name='Linked meals',exact=True));dialog.get_by_role('searchbox',name='Search meals',exact=True).fill('Garlic Bread');dialog.locator('label').filter(has_text='Garlic Bread').locator('input[type=checkbox]').check();dialog.get_by_role('button',name='OK',exact=True).click();p.locator('#save').click()
 assert p.evaluate('remainingTest.libraryIds()')==original_ids
 assert p.evaluate('remainingTest.temp().linkedMealIds')==[25]
 assert len(p.evaluate('remainingTest.temp().mealGroups'))==2
 assert any(r[0]=='Saturday' and r[2]=='25' for r in p.evaluate('remainingTest.rows()'))
 p.evaluate('remainingTest.check("Saturday","Bread");remainingTest.hide();editorBoundary.tempMenu()');p.get_by_role('button',name='Restore Garlic Bread',exact=True).click();assert all(s['checked'] for s in p.evaluate('remainingTest.sources()') if s['day']=='Saturday' and str(s['mealId'])=='25')
 p.evaluate('remainingTest.editTemp()');assert p.locator('#categoryRows select').count()==2;p.locator('#save').click();assert len(p.evaluate('remainingTest.temp().mealGroups'))==2 and p.evaluate('remainingTest.temp().linkedMealIds')==[25]
 p.evaluate('sameDay.forward()');assert set(p.evaluate('remainingTest.libraryIds()'))==set(original_ids)
 p.evaluate('sameDay.back()');assert p.evaluate('remainingTest.temp().linkedMealIds')==[25]
 p.evaluate('promotionTest.validate()');assert not errors,errors
 print('PASS',name,'origin tab, full editor memberships/rotation, nested linked picker, rich temporary links/edit/restore/expiry/Back, no leaked drafts or JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:run(b,name)
  finally:b.close()
