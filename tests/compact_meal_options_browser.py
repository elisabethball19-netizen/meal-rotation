"""Focused compact menus, slot-local selection, alignment and auto-population."""
from playwright.sync_api import sync_playwright
import weekday_group_selection_browser as g
f=g.f
f.EXTRA+='''window.compactTest={
 seed:()=>{groupPickerTest.seed();setDayCategories('Saturday',['Weekend','Breakfast','Lunch']);renderList()},
 menu:cat=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat===cat);openTopMealActionMenu(x.day,x.cat,x.meal)},
 once:()=>saveOneTimeMeal('Saturday','Breakfast','A very long one-time breakfast with pancakes and bacon and fruit'),
 rows:()=>getDisplayedWeekdayMeals().map(x=>[x.day,x.cat,String(x.meal.id),x.meal.name]),
 library:()=>JSON.stringify(meals),
 enable:()=>{for(const m of meals)if(m.cat==='Breakfast')m.rotation=true;persist();renderList()},
 autoFixture:()=>{groupPickerTest.seed();setDayCategories('Saturday',['Weekend','Breakfast','Lunch']);setDayCategories('Sunday',['Breakfast']);for(const m of meals)if(m.cat==='Breakfast')m.rotation=true;meals.find(m=>m.id===4).favorite=true;persist();renderList();leaveWeekEmpty('Saturday','Breakfast')},
 linked:()=>{compactTest.seed();const m=meals.find(m=>m.id===3);m.rotation=true;m.linkedMealIds=[5];persist();renderList();leaveWeekEmpty('Saturday','Breakfast')},
 candidate:()=>emptySlotAutomaticCandidate('Saturday','Breakfast')?.id,
 excluded:()=>{const plan=mealPlans.find(p=>p.id===activePlanId);plan.cycleSlotChoices['Saturday::Breakfast']={empty:true,skipReplacement:true,excludedMealIds:['3','4']};saveActiveMealPlan();persist();renderList()},
 validate:()=>promotionTest.validate(),
 long:()=>{meals.find(m=>m.cat==='Weekend').name='A very long regular meal with an exceptionally long title that wraps on a phone';persist();renderList()},
 skip:()=>{groupPickerTest.seed();renderList()},
 plan:()=>mealPlans.find(p=>p.id===activePlanId),
 single:()=>{setDayCategories('Thursday',['Lunch']);renderList()}
};'''

def aligned(p):
 tags=p.locator('[data-schedule-day=Saturday] .top-meal-inline-category')
 edges=[x.bounding_box()['x']+x.bounding_box()['width'] for x in tags.all()]
 assert len(edges)==3 and max(edges)-min(edges)<3,edges
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')

def centered(dialog):
 for b in dialog.locator('.meal-full-action').all():
  assert b.evaluate('(e)=>getComputedStyle(e).textAlign')=='center'
  assert b.bounding_box()['height']>=44
 assert dialog.bounding_box()['height']<=680

def run(browser,filename,width):
 c,p,errors,prefix=f.setup(browser,filename,width);p.evaluate('compactTest.seed();compactTest.long()');aligned(p)
 original=p.evaluate('compactTest.library()');before=p.evaluate('compactTest.rows()')
 blank=p.locator('.empty-weekday-meal[data-category=Breakfast] .mealname');blank.tap();d=p.get_by_role('dialog',name='Empty group options')
 assert d.get_by_role('button',name='Select Meal',exact=True).count()==1
 assert not d.get_by_role('button',name='Auto-Populate Meal',exact=True).count()
 assert not d.get_by_role('button',name='Add One-Time Meal',exact=True).count()
 centered(d);d.get_by_role('button',name='Select Meal',exact=True).tap()
 chooser=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True)
 assert chooser.get_by_role('button',name='Create New Recipe',exact=True).count()==1
 assert not chooser.get_by_role('button',name='Add One-Time Meal',exact=True).count()
 assert chooser.get_by_role('button',name='Create New Recipe',exact=True).locator('svg').count()==1
 chooser.get_by_role('button',name='Search recipes',exact=True).tap();chooser.get_by_role('searchbox',name='Search recipes').fill('Lunch meal 1')
 chooser.locator('[data-meal-id="5"]').tap();chooser.get_by_role('button',name='Save',exact=True).tap()
 now=p.evaluate('compactTest.rows()');assert next(r for r in now if r[1]=='Breakfast')[2]=='5'
 assert next(r for r in now if r[1]=='Weekend')==next(r for r in before if r[1]=='Weekend')
 assert p.evaluate('compactTest.library()')==original
 p.reload();p.evaluate('promotionTest.my()');aligned(p);p.evaluate('compactTest.validate()')
 p.evaluate("compactTest.menu('Weekend')");d=p.get_by_role('dialog',name='Meal options for Saturday',exact=True)
 assert d.locator('.meal-quick-actions button').all_text_contents()==['Select','Skip','Edit']
 assert d.locator('.meal-full-action').all_text_contents()==['Open recipe','Leave Saturday weekend empty','Edit grocery list']
 assert d.locator('.meal-options-last-cooked').count()==1;centered(d)
 for b in d.locator('.meal-quick-actions button').all():assert b.bounding_box()['height']>=44
 before=p.evaluate('compactTest.rows()');d.get_by_role('button',name='Select',exact=True).tap();assert p.evaluate('compactTest.rows()')==before
 p.get_by_role('dialog',name="Choose Saturday's meal",exact=True).get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('compactTest.once()');aligned(p);p.evaluate("compactTest.menu('Breakfast')")
 d=p.get_by_role('dialog',name='One-time meal options',exact=True)
 assert d.locator('.meal-quick-actions button').all_text_contents()==['Select','Edit']
 assert d.locator('.meal-full-action').all_text_contents()==['Leave Saturday breakfast empty','Resume planned meal'];centered(d)
 assert not d.locator('.meal-options-last-cooked').count()
 d.get_by_role('button',name='Edit',exact=True).tap();editor=p.get_by_role('dialog',name='Edit one-time meal',exact=True)
 editor.get_by_role('textbox',name='One-time meal name',exact=True).fill('Sandwiches');editor.get_by_role('button',name='Save one-time meal',exact=True).tap()
 p.reload();p.evaluate('promotionTest.my()');assert any(r[3]=='Sandwiches' for r in p.evaluate('compactTest.rows()'))
 p.evaluate("compactTest.menu('Breakfast')");p.get_by_role('button',name='Resume planned meal',exact=True).tap();assert not any(r[3]=='Sandwiches' for r in p.evaluate('compactTest.rows()'))
 # No planned recipe in a truly empty group: omit Resume and recipe-only options.
 p.evaluate('compactTest.seed();compactTest.once()');p.evaluate("compactTest.menu('Breakfast')");d=p.get_by_role('dialog',name='One-time meal options',exact=True)
 assert d.locator('.meal-full-action').all_text_contents()==['Leave Saturday breakfast empty'];d.get_by_role('button',name='Close',exact=True).tap()
 # Automatic fill uses ranked candidates while keeping all other slots and the queue exact.
 p.evaluate('compactTest.autoFixture()');before=p.evaluate('compactTest.rows()');library=p.evaluate('compactTest.library()');candidate=str(p.evaluate('compactTest.candidate()'));assert candidate=='4',candidate
 p.locator('.empty-weekday-meal[data-category=Breakfast] .mealname').tap();d=p.get_by_role('dialog',name='Empty meal options',exact=True)
 assert d.get_by_role('button',name='Auto-Populate Meal',exact=True).count()==1
 d.get_by_role('button',name='Auto-Populate Meal',exact=True).tap()
 now=p.evaluate('compactTest.rows()');assert next(r for r in now if r[:2]==['Saturday','Breakfast'])[2]==candidate
 assert [r for r in now if r[:2]!=['Saturday','Breakfast']]==before
 assert p.evaluate('compactTest.library()')==library
 assert not p.evaluate("compactTest.plan().cycleSlotChoices['Saturday::Breakfast'].substitution")
 assert len({r[2] for r in now if r[1]=='Breakfast'})==2
 p.reload();p.evaluate('promotionTest.my()');assert p.evaluate('compactTest.rows()')==now
 p.evaluate('compactTest.excluded()');assert p.evaluate('compactTest.candidate()') is None
 p.locator('.empty-weekday-meal[data-category=Breakfast] .mealname').tap();assert not p.get_by_role('button',name='Auto-Populate Meal',exact=True).count();p.get_by_role('button',name='Leave Saturday breakfast empty',exact=True).tap()
 p.evaluate('compactTest.single()');p.locator('.empty-weekday-meal[data-schedule-day=Thursday] .mealname').tap();p.get_by_role('button',name='Leave Thursday empty',exact=True).tap()
 assert p.locator('.empty-weekday-meal[data-schedule-day=Thursday] .mealname').inner_text()=='—'
 p.evaluate('compactTest.skip()');p.evaluate("compactTest.menu('Weekend')");p.get_by_role('button',name='Skip',exact=True).tap();assert next(r for r in p.evaluate('compactTest.rows()') if r[1]=='Weekend')[2]=='2'
 p.evaluate('compactTest.linked()');library=p.evaluate('compactTest.library()');p.locator('.empty-weekday-meal[data-category=Breakfast] .mealname').tap();p.get_by_role('button',name='Auto-Populate Meal',exact=True).tap();assert any(r[1]=='Lunch' and r[2]=='5' for r in p.evaluate('compactTest.rows()'));assert p.evaluate('compactTest.library()')==library
 p.evaluate('compactTest.validate()');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',filename,width,'alignment, compact menus, chooser/search/cross-group slot, one-time controls, auto/favorites/exclusions/duplicates, reload, skip, backup, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
