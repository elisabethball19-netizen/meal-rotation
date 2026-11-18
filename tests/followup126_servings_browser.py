"""Composite side saves, recurring groups, legacy transition, current/next ownership."""
from playwright.sync_api import sync_playwright
import followup126_browser as f126
from datetime import datetime,timezone
import followup126_browser as base
fixture=base.fixture
fixture.HOOK+='''window.serving126={
 sourceIds:()=>getGroceryContributions(true,'current').map(s=>s.id).sort(),
 futureSides:()=>{const s=previewMealPlanAdvance(),e=s.entries.find(e=>!e.linkedTo&&!e.servingParentId);return servingSides(s.plan,e,s.entries)},
 rules:id=>JSON.parse(JSON.stringify(meals.find(m=>m.id===id))),
 repeat:()=>{for(const m of meals)if(m.cat==='Rice'&&m.id!==2)m.rotation=false;const p=mealPlans[0];delete p.weekdayMealOverrides['Tuesday::Rice'];delete p.cycleSlotChoices['Tuesday::Rice'];weekdayMealOverrides={...p.weekdayMealOverrides};const m=meals.find(m=>m.id===2);m.serveWithEntriesV1=[{id:'rotate',type:'rotating',groupIds:[groupIdentity('Vegetables',true),groupIdentity('Potatoes',true)],always:true}];saveActiveMealPlan();persist();follow126.home()},
 sides:week=>{const source=week?previewMealPlanAdvance():{plan:mealPlans[0],entries:getDisplayedWeekdayMealsForPlan(mealPlans[0])},parent=source.entries.find(e=>!e.linkedTo&&!e.servingParentId);return {parent:parent.meal.id,sides:servingSides(source.plan,parent,source.entries)}},
 save:(sides,week=0)=>{const source=week?previewMealPlanAdvance():{plan:mealPlans[0],entries:getDisplayedWeekdayMealsForPlan(mealPlans[0])},parent=source.entries.find(e=>!e.linkedTo&&!e.servingParentId);saveServingSession(servingTarget(source.plan,parent,week),sides,JSON.stringify(servingSides(source.plan,parent,source.entries)));follow126.home(week)},
 raw:()=>JSON.stringify({meals,mealPlans,scales:occurrenceScales,progress:cookingSessions,checks:groceryOccurrenceChecks}),
 weekday:()=>openRecurringDayEditor('Tuesday'),groups:()=>{showTop=false;groceryTabActive=false;allMealsActive=false;masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(cat=>masterExpandedCategories.add(cat));renderList({readOnly:true})},
 cooked:()=>editMealCookedDate(meals.find(m=>m.id===2)),
 favorite:()=>{meals.find(m=>m.id===1).favorite=true;for(const p of mealPlans)for(const choice of Object.values(p.cycleSlotChoices||{}))choice.retain=false;follow126.home()},
 rotation:()=>JSON.parse(JSON.stringify(mealPlans[0].sideRuleStateV1||{})),assignments:()=>JSON.parse(JSON.stringify(mealPlans[0].weekdayCategories)),
 settings:()=>{showTop=true;topSettingsOpen=true;renderMenu()},scaleMain:()=>{const e=getDisplayedWeekdayMealsForPlan(mealPlans[0])[0];openSavedMealRecipe(e.meal,cookingContext(activePlanId,e.day,e.cat,e.meal,e.linkedTo));setViewedRecipeScale(2);closeRecipeViewer()},
 currentScale:()=>{const e=getDisplayedWeekdayMealsForPlan(mealPlans[0])[0];return occurrenceMultiplier(cookingContext(activePlanId,e.day,e.cat,e.meal,e.linkedTo))},
 carry:()=>advanceMealPlanWeek(new Set()),
 pendingRecipe:()=>{const p=mealPlans[0];p.pendingNextWeekV1={version:1,week:'2026-11-24',choices:{[pendingChoiceKey('Tuesday','Rice')]:{day:'Tuesday',groupId:groupIdentity('Rice',true),mealId:'2',provenance:'manual'}}};saveActiveMealPlan()}
};'''

def setup(browser,name):
 c,p,errors,prefix=fixture.setup(browser,name,navigation_timeout=30000);p.context.new_cdp_session(p).send('Emulation.setTimezoneOverride',{'timezoneId':'America/Los_Angeles'});p.clock.set_fixed_time(datetime(2026,11,16,20,tzinfo=timezone.utc));p.evaluate('follow126.seed()');return c,p,errors,prefix

def run(browser,name):
 c,p,errors,prefix=setup(browser,name)
 # Simple current-only UI Save: single input replaces its display name; no recipe default write.
 before=p.evaluate('serving126.rules(2)');card=p.locator('.plan-meal-card[data-meal-id="2"]');card.locator('.meal-actions-toggle').click();f126.open_sides(card);f126.add_simple(p,card,'Rice');card.get_by_role('switch').uncheck();card.locator('.serving-icon-action[aria-label="Edit groceries"]').click();card.get_by_role('textbox',name='Side ingredients',exact=True).fill('1 cup jasmine rice');base.shot(p,name,'simple-current-keyboard');card.get_by_role('button',name='Close sides',exact=True).click();p.wait_for_timeout(150);after={k:v for k,v in p.evaluate('serving126.rules(2)').items() if v!=[]};assert after==before,after;assert p.evaluate('follow126.sides()[0].name')=='Rice';assert p.evaluate('follow126.sides()[0].always') is False
 p.reload();p.evaluate('follow126.home()');assert p.evaluate('follow126.sides()[0].name')=='Rice'
 # A fixed Always side creates a real link. An occurrence override changes only its serving.
 p.evaluate("serving126.save([{id:'fixed',type:'fixed',recipeId:'10',mealId:'10',always:true}])");assert 10 in p.evaluate('serving126.rules(2).linkedMealIds')
 assert any(e['id']==10 and str(e['parent'])=='2' for e in p.evaluate('follow126.current()'))
 p.evaluate('follow126.undo()');assert 10 not in p.evaluate('serving126.rules(2).linkedMealIds||[]');p.evaluate('follow126.redo()');assert 10 in p.evaluate('serving126.rules(2).linkedMealIds')
 # OFF removes the future default but retains this serving; no recipe is deleted.
 p.evaluate("serving126.save([{id:'fixed',type:'fixed',recipeId:'10',mealId:'10',always:false}])");assert 10 not in p.evaluate('serving126.rules(2).linkedMealIds');assert any(e['id']==10 for e in p.evaluate('follow126.current()'))
 # Future-only side save via actual child picker/outer check leaves the current occurrence untouched.
 current=p.evaluate('follow126.current()');assert not p.get_by_role('alertdialog').count(),p.get_by_role('alertdialog').inner_text();p.evaluate('follow126.home(1)');future=p.locator('.preview-plan-card[data-meal-id="3"]');future.locator('.meal-actions-toggle').click();assert future.locator('.shared-meal-action-grid button').count()==4;base.shot(p,name,'next-expanded');f126.open_sides(future);f126.add_recipe(p,future,'Green',12);future.get_by_role('switch').uncheck();future.get_by_role('button',name='Close sides',exact=True).click();p.wait_for_timeout(150);assert p.evaluate('follow126.current()')==current;assert any(s.get('mealId')=='12' for s in p.evaluate('serving126.futureSides()'));p.reload();p.evaluate('follow126.home(1)');assert any(s.get('mealId')=='12' for s in p.evaluate('serving126.futureSides()'))
 # Repeated parent servings alternate group, rotate inside group, never consume turns on view.
 p.evaluate('follow126.seed();serving126.repeat()');assert p.evaluate('serving126.sides(0).sides[0].mealId')=='12';state=p.evaluate('serving126.raw()');assert p.evaluate('serving126.sides(1).sides[0].mealId')=='10';assert p.evaluate('serving126.raw()')==state
 p.evaluate('follow126.advance()');assert p.evaluate('serving126.sides(0).sides[0].mealId')=='10';p.evaluate('follow126.undo()');assert p.evaluate('serving126.sides(0).sides[0].mealId')=='12';p.evaluate('follow126.redo()');assert p.evaluate('serving126.sides(0).sides[0].mealId')=='10'
 p.evaluate('follow126.advance();follow126.advance()');assert p.evaluate('serving126.sides(0).sides[0].mealId')=='11'
 # Legacy multi-main assignment: review required; cancel exact; confirmed migration keeps source identities.
 p.evaluate('follow126.seed();follow126.legacy()');ids=p.evaluate('serving126.sourceIds()');state=p.evaluate('serving126.raw()');p.evaluate('serving126.weekday()');d=p.get_by_role('dialog',name='Choose Tuesday’s meal groups',exact=True);d.get_by_role('button',name='Save meal groups',exact=True).click();assert 'Choose the main dish' in d.inner_text();assert p.evaluate('serving126.raw()')==state;base.shot(p,name,'legacy-review');d.get_by_role('button',name='Cancel meal groups',exact=True).click()
 p.evaluate('serving126.weekday()');d=p.get_by_role('dialog',name='Choose Tuesday’s meal groups',exact=True);d.get_by_role('radio',name='Main dish Chili-Garlic Broth Bowls',exact=True).check();d.get_by_role('checkbox',name='Keep other listed dishes as sides for this serving',exact=True).check();d.get_by_role('button',name='Save meal groups',exact=True).click();p.wait_for_timeout(150);assert not d.count(),d.inner_text();assert p.locator('.plan-meal-card[data-meal-id="10"]').count()==0;assert p.evaluate('serving126.sourceIds()')==ids;assert p.evaluate('serving126.assignments().Tuesday')==['Rice'];p.evaluate('follow126.undo()');assert p.evaluate('serving126.assignments().Tuesday')==['Rice','Potatoes'];p.evaluate('follow126.redo()')
 # Settings entry opens the same pending editor; Back cancels.
 p.evaluate('serving126.weekday()');d=p.get_by_role('dialog',name='Choose Tuesday’s meal groups',exact=True);state=p.evaluate('serving126.raw()');d.get_by_role('checkbox',name='Vegetables',exact=True).check();p.go_back();p.wait_for_timeout(150);assert not d.count();assert p.evaluate('serving126.raw()')==state
 # Actual cooked-date edits change eligible automatic queue; favorites and manual selections remain explicit.
 p.evaluate('follow126.seed();serving126.cooked()');d=p.get_by_role('dialog',name='Edit last cooked date',exact=True);d.get_by_label('Choose last cooked date',exact=True).fill('2026-11-16');d.get_by_role('button',name='Save',exact=True).click();assert p.evaluate('follow126.current()[0].id')==3
 p.evaluate('follow126.seed();serving126.favorite()');assert p.evaluate('follow126.pool()[0]')==1;p.evaluate('follow126.manual()');assert p.evaluate('follow126.current()[0].id')==3
 assert p.evaluate('follow126.backup()');assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'follow126 simple/fixed/rotating side saves, current/next isolation, defaults/removal, reload/Undo, safe legacy review, weekday Back, actual date/favorite/manual safeguards',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
