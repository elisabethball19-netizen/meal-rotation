"""Issue 126: disposable real-browser occurrence, future-plan and control flows."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import grocery_batch122_browser as base
fixture=base.fixture
fixture.HOOK+='''window.batch126={
 state:()=>JSON.stringify({mealPlans,weekdayCategories,weekdayMealOverrides,scales:occurrenceScales,checks:groceryOccurrenceChecks,meals}),
 plans:()=>JSON.parse(JSON.stringify(mealPlans)),preview:()=>{const s=previewMealPlanAdvance();return {plan:s.plan,entries:s.entries.map(e=>({day:e.day,cat:e.cat,id:e.meal.id,date:cookingLocalDate(scheduledOccurrenceDate({...e,planId:s.plan.id},s.plan.rotationCalendar))}))}},
 show:(week=0)=>{showTop=true;groceryTabActive=false;allMealsActive=false;rotationWeekOffset=week;renderList({readOnly:true})},
 select:(id,day='Monday',week=1,cat='Meals',extra={})=>{rotationWeekOffset=week;applyRecipeBulk([String(id)],{},{mealSelection:{planId:activePlanId,week,day,category:cat,mealId:String(id),...extra}})},
 sequence:()=>{const p=mealPlans[0];p.alternatingGroupsV1={monday:{day:'Monday',groups:[groupIdentity('Meals',true),groupIdentity('Bread',true)],position:0}};saveActiveMealPlan()},
 advance:slots=>{rotationWeekOffset=0;advanceMealPlanWeek(slots?new Set(slots):null)},
 scale:(id,n,options={},future=false)=>{const source=future?previewMealPlanAdvance():{plan:mealPlans[0],entries:getDisplayedWeekdayMealsForPlan(mealPlans[0])},entry=source.entries.find(e=>String(e.meal.id)===String(id));openSavedMealRecipe(meals.find(m=>m.id===id),future?pendingContext(source.plan,entry):cookingContext(source.plan.id,entry.day,entry.cat,entry.meal,entry.linkedTo));return setViewedRecipeScale(n,options)},
 close:()=>closeRecipeViewer(),scales:()=>JSON.parse(JSON.stringify(occurrenceScales)),
 add:()=>{meals.push({id:103,name:'Lemon rice and chicken with a very long name for a family dinner',cat:'Meals',rotation:true,ingredients:['1 cup rice','1 lb chicken'],linkedMealIds:[104,104],makeAheadTasks:[{id:'prep',description:'Prepare dinner',daysBefore:1}]},{id:104,name:'Direct herb sauce',cat:'Sides',rotation:false,ingredients:['1 cup cream'],linkedMealIds:[105]},{id:105,name:'Second-level bread',cat:'Sides',rotation:false,ingredients:['1 cup flour']});const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selected['103']=['1 cup rice','1 lb chicken'];selected['104']=['1 cup cream'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));persist()},
 picker:()=>{const s=previewMealPlanAdvance(),e=s.entries.find(e=>e.day==='Monday');openWeekdayMealChooser(e.day,e.cat,e.meal,false,{futurePlan:s.plan,occurrenceKey:simpleSideOccurrenceKey(s.plan,e)})},
 assignment:()=>openDayCategoryPicker('Monday'),undo:()=>{const s=JSON.parse(history.pop());redoHistory.push(captureHistoryCounterpart(s));restoreState(s)},redo:()=>{const s=JSON.parse(redoHistory.pop());history.push(captureHistoryCounterpart(s));restoreState(s)},
 todo:()=>{const today=cookingLocalDate(new Date()),p=mealPlans[0],e=getDisplayedWeekdayMealsForPlan(p)[0],date=n=>{const d=new Date();d.setDate(d.getDate()+n);return cookingLocalDate(d)};batch126.show();renderTodayTodo([[-1,0,'Overdue'],[0,1,'Today'],[1,2,'Future']].map(([due,scheduled,name],i)=>({plan:p,entry:e,task:{id:'t'+i,description:name},key:JSON.stringify([rotationOccurrenceKey({...e,planId:p.id}),date(scheduled),'','t'+i]),due:date(due),scheduled:date(scheduled),complete:false})))},
 };'''

def check(browser,name):
 c,p,errors,prefix=fixture.setup(browser,name,navigation_timeout=30000)
 p.evaluate('batch122.seed();batch126.add()')
 p.evaluate('batch126.show()');nameButton=p.locator('.plan-meal-card .mealname').first
 nameButton.dispatch_event('pointerdown',{'button':0,'pointerType':'mouse','pointerId':1,'clientX':100,'clientY':200});p.wait_for_timeout(600);nameButton.dispatch_event('pointerup',{'button':0,'pointerType':'mouse','pointerId':1});assert not p.locator('.compact-meal-dialog').count()
 p.wait_for_timeout(750);nameButton.click();assert p.locator('#recipeViewer').count();p.evaluate('batch126.close()');p.wait_for_timeout(150)
 # Grouped checks use the same dated contribution store; reload and filters preserve partial.
 p.evaluate('batch122.grocery()');p.get_by_label('Grocery view',exact=True).select_option('meal')
 section=p.locator('.grocery-meal-section').first
 section.locator('.grocery-checkbox-target input').first.check()
 p.get_by_label('Grocery view',exact=True).select_option('combined')
 rice=p.locator('.master-grocery-item').filter(has=p.locator('.grocery-ingredient-name',has_text='rice')).first
 assert rice.locator('.grocery-checkbox-target input').evaluate('(x)=>x.indeterminate')
 rice.locator('.grocery-expand').click();assert rice.locator('.grocery-contribution-edit').count()==1
 assert rice.locator('.grocery-contribution-amount').count()==0
 p.reload();p.evaluate('batch122.grocery()');assert rice.locator('.grocery-checkbox-target input').evaluate('(x)=>x.indeterminate')
 # Future edit changes groceries immediately; current stays exact, cancel/Back do not write.
 current=p.evaluate('batch126.plans()[0].weekdayMealOverrides')
 p.evaluate('batch126.show(1);batch126.picker()');before=p.evaluate('batch126.state()');p.get_by_role('button',name='Cancel',exact=True).click();assert p.evaluate('batch126.state()')==before
 p.wait_for_timeout(400)
 p.evaluate('batch126.picker()');p.go_back();p.wait_for_timeout(200);assert not p.locator('.weekday-meal-picker').count()
 p.evaluate('batch126.show(1);batch126.picker()');picker=p.locator('.weekday-meal-picker');picker.locator('[data-meal-id="103"]').first.click();picker.get_by_role('button',name='Save',exact=True).click();p.wait_for_timeout(200);assert not picker.count();assert p.evaluate('batch126.plans()[0].weekdayMealOverrides')==current
 assert next(e for e in p.evaluate('batch126.preview().entries')if e['day']=='Monday')['id']==103
 p.reload();assert next(e for e in p.evaluate('batch126.preview().entries')if e['day']=='Monday')['id']==103
 p.evaluate('batch126.show(1)');p.locator('.preview-plan-card[data-meal-id="103"] .meal-actions-toggle').click();p.screenshot(path='/workspace/work/screenshots/'+name+'-future126.png')
 # Scaling direct links and future defaults; numeric 1x overrides saved default.
 p.evaluate('batch126.scale(103,2,{remember:true,linked:true},true)')
 scales=p.evaluate('batch126.scales()');assert scales['defaults']['103']==2 and scales['defaults']['104']==2 and '105' not in scales['defaults']
 p.evaluate('batch126.close();batch126.scale(103,1,{},true)');assert any(e['multiplier']==1 and e['context']['mealId']=='103' for e in p.evaluate('batch126.scales().occurrences').values())
 p.get_by_role('button',name='Scale Recipe',exact=True).click();assert not p.get_by_role('switch',name='Remember for this recipe').is_checked();assert not p.get_by_role('switch',name='Scale linked recipes too').is_checked()
 p.screenshot(path='/workspace/work/screenshots/'+name+'-scale126.png');p.keyboard.press('Escape');p.evaluate('batch126.close()')
 pending=p.evaluate('batch126.preview()');p.evaluate('batch126.advance()');assert p.evaluate('batch126.plans()[0].weekdayMealOverrides["Monday::Meals"]')=='103'
 assert not p.evaluate('batch126.plans()[0].pendingNextWeekV1||null')
 p.evaluate('batch126.undo()');assert p.evaluate('batch126.plans()[0].pendingNextWeekV1')
 p.evaluate('batch126.redo()');assert p.evaluate('batch126.plans()[0].weekdayMealOverrides["Monday::Meals"]')=='103'
 # Independent alternating position: preview/reload never advance; explicit advance/Undo does.
 p.evaluate('batch122.seed();batch126.add();batch126.sequence()');state=p.evaluate('batch126.state()');assert next(e for e in p.evaluate('batch126.preview().entries')if e['day']=='Monday')['cat']=='Bread';assert p.evaluate('batch126.state()')==state
 p.evaluate('batch126.show();batch126.assignment()');p.screenshot(path='/workspace/work/screenshots/'+name+'-sequence126.png');p.get_by_role('button',name='Close',exact=True).click()
 p.evaluate('batch126.advance()');assert p.evaluate('batch126.plans()[0].alternatingGroupsV1.monday.position')==1
 p.evaluate('batch126.undo()');assert p.evaluate('batch126.plans()[0].alternatingGroupsV1.monday.position')==0
 # Only due/eligible items keep Today alive; no future task.
 p.evaluate('batch126.todo()');assert 'Future' not in p.locator('#todaysTodo').inner_text();assert 'Today' in p.locator('#todaysTodo').inner_text()
 assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'126 grouped checks, future/cancel/Back/advance/Undo, direct scaling, sequence and due-only To-Do',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:check(b,name)
  b.close()
