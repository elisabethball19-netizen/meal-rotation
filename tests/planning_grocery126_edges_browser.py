"""Focused 126 preservation/edge fixtures, both isolated browser namespaces."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import planning_grocery126_browser as base
fixture=base.fixture
fixture.HOOK+='''window.edge126={
 rawManual:()=>JSON.stringify(manualGroceryItems()),manual:()=>{saveManualGroceryItems([{id:'oats',text:'7 cartons oat milk',checked:true}]);return JSON.stringify(manualGroceryItems())},quantity:()=>[...getMasterGroceryItems()].find(([,i])=>i.line.includes('fragrant rice'))?.[1].quantity.lo,
 autoDuplicate:()=>{const p=mealPlans[0],s=previewMealPlanAdvance(),e=s.entries.find(e=>e.day==='Monday');return {id:e.meal.id,provenance:futureDuplicateInfo(p,e.meal).map(x=>x.provenance)}},
 remember:(id,n,options)=>batch126.scale(id,n,options),
 sources:period=>getGroceryContributions(false,period).map(s=>({id:s.id,mealId:s.mealId,date:s.scheduledDate,text:groceryContributionText(s),multiplier:s.multiplier,checked:grocerySourceChecked(s)})),
 editAggregate:()=>{groceryPeriod='both';const item=[...getMasterGroceryItems()].find(([,i])=>i.contributions.length>1)[1];openGroceryTextEditor(item,()=>{})},
 emptyPool:()=>{const s=previewMealPlanAdvance(),entry=s.entries.find(e=>e.day==='Monday');for(const m of meals)if(m.cat===entry.cat&&m.id!==entry.meal.id){m.rotation=false;m.recipeStatus='up-next'}persist();return entry.meal.id},
 backup:()=>{const b=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(b);return b},legacy:()=>{const b=recipeBulkBackupAPI.capture();delete b.mealRotationOccurrenceScalesV1;recipeBulkBackupAPI.validate(b);return true},
 many:()=>{weekdays.forEach((day,i)=>{weekdayCategories[day]=['Meals'];weekdayMealOverrides[day+'::Meals']=i%2?'102':'101'});saveActiveMealPlan();persist();establishDatedFixtureSchedule();groceryPeriod='both';localStorage.setItem(GROCERY_PERIOD_KEY,'both');batch122.grocery()},
 onlyFuture:()=>{const p=mealPlans[0],e=getDisplayedWeekdayMealsForPlan(p)[0],date=n=>{const d=new Date();d.setDate(d.getDate()+n);return cookingLocalDate(d)};batch126.show();renderTodayTodo([{plan:p,entry:e,task:{id:'f',description:'Future only'},key:JSON.stringify([rotationOccurrenceKey({...e,planId:p.id}),date(2),'','f']),due:date(1),scheduled:date(2),complete:false}])},
 allComplete:()=>{const p=mealPlans[0],e=getDisplayedWeekdayMealsForPlan(p)[0],today=cookingLocalDate(new Date());makeAheadDisplayPrefs.showCompletedToday=true;batch126.show();renderTodayTodo([{plan:p,entry:e,task:{id:'c',description:'Complete'},key:JSON.stringify([rotationOccurrenceKey({...e,planId:p.id}),today,'','c']),due:today,scheduled:today,complete:true}])},
 };'''

def check(browser,name):
 c,p,errors,prefix=fixture.setup(browser,name,width=320,navigation_timeout=30000)
 p.evaluate('batch122.seed();batch126.add()')
 # Aggregate shopping wording scales canonical contributions, preserving manual source and recipes.
 p.evaluate('batch122.grocery()');rice=p.locator('.master-grocery-item').filter(has=p.locator('.grocery-ingredient-name',has_text='rice')).first;rice.locator('.grocery-expand').click();rice.locator('.grocery-contribution-edit').click();p.get_by_label('Grocery item',exact=True).fill('3 cups fragrant rice');p.get_by_role('button',name='Save grocery item',exact=True).click();recipes=p.evaluate('batch122.raw()');manual=p.evaluate('edge126.manual()')
 for scale,expected in [(2,6),(.5,1.5),(1,3)]:
  p.evaluate('n=>{batch122.scale(101,n);batch122.scale(102,n)}',scale);assert p.evaluate('edge126.quantity()')==expected
 assert p.evaluate('batch122.raw()')==recipes;assert p.evaluate('edge126.rawManual()')==manual
 p.evaluate('batch122.seed();batch126.add()')
 # Automatic cross-week duplicate replaced in same future group, atomically Undoable.
 info=p.evaluate('edge126.autoDuplicate()');print('automatic fixture',name,info,flush=True)
 assert info['provenance']==['automatic']
 old=p.evaluate('batch126.state()');p.evaluate('(id)=>batch126.select(id,"Monday",0)',info['id'])
 assert next(e for e in p.evaluate('batch126.preview().entries')if e['day']=='Monday')['id']!=info['id']
 p.evaluate('batch126.undo()');assert p.evaluate('batch126.plans()[0].weekdayMealOverrides["Monday::Meals"]')=='101'
 p.evaluate('batch126.redo()');assert p.evaluate('batch126.plans()[0].weekdayMealOverrides["Monday::Meals"]')==str(info['id'])
 # Manual pending choice remains if keep both; replacing it uses explicit protected decision.
 p.evaluate('batch122.seed();batch126.add();batch126.select(103)');p.evaluate('batch126.select(103,"Monday",0)');assert next(e for e in p.evaluate('batch126.preview().entries')if e['day']=='Monday')['id']==103
 p.evaluate('batch126.undo()');p.evaluate('batch126.select(103,"Monday",0,"Meals",{replaceFuture:true})');assert next(e for e in p.evaluate('batch126.preview().entries')if e['day']=='Monday')['id']!=103
 # No replacement: all state remains unchanged.
 p.evaluate('batch122.seed()');id=p.evaluate('edge126.emptyPool()');state=p.evaluate('batch126.state()')
 try:p.evaluate('(id)=>batch126.select(id,"Tuesday",0)',id)
 except Exception as e:assert 'No different eligible' in str(e)
 else:raise AssertionError('empty candidate pool must reject')
 assert p.evaluate('batch126.state()')==state
 # Sequence still advances with outgoing meal carried forward; Undo restores it.
 p.evaluate('batch122.seed();batch126.sequence();batch126.advance(["Tuesday::Meals"])')
 assert p.evaluate('batch126.plans()[0].alternatingGroupsV1.monday.position')==1
 assert any(e['day']=='Monday' and e['id']==101 for e in p.evaluate('batch126.preview().entries')) is False # next projection is another week
 assert p.evaluate('batch1.schedule().some(e=>e[1]==="Monday"&&e[3]===101)')
 p.evaluate('batch126.undo()');assert p.evaluate('batch126.plans()[0].alternatingGroupsV1.monday.position')==0
 # All scale toggle combinations, default reset, other scheduled copy, direct-only links.
 p.evaluate('batch122.seed();batch126.add();batch126.select(103,"Monday",0)')
 p.evaluate('batch126.scale(103,2,{remember:true,linked:false})');assert p.evaluate('batch126.scales().defaults["103"]')==2;assert p.evaluate('batch126.scales().defaults["104"]||1')==1
 p.evaluate('batch126.close();batch126.scale(103,.5,{remember:false,linked:true})');assert p.evaluate('batch126.scales().defaults["103"]')==2
 assert not p.evaluate('Object.values(batch126.scales().occurrences).some(e=>e.context.mealId==="105")')
 p.evaluate('batch126.close();batch126.scale(103,1,{remember:true,linked:true});batch126.close()');assert p.evaluate('batch126.scales().defaults["103"]')==1;assert p.evaluate('batch126.scales().defaults["104"]')==1
 p.evaluate('batch126.undo()');assert p.evaluate('batch126.scales().defaults["103"]')==2
 p.evaluate('batch126.redo()');assert p.evaluate('batch126.scales().defaults["103"]')==1
 assert p.evaluate('edge126.legacy()');backup=p.evaluate('edge126.backup()');assert backup
 # Narrow/large text grouped and combined views, aggregate editor and keyboard height.
 p.evaluate('batch122.seed();batch126.add();batch122.extras();batch122.grocery()');p.get_by_label('Grocery view',exact=True).select_option('meal');p.add_style_tag(content='html{font-size:20px}button,select{font-size:1rem}')
 p.screenshot(path='/workspace/work/screenshots/'+name+'-grouped-large126.png',full_page=True)
 p.get_by_label('Grocery view',exact=True).select_option('combined');rice=p.locator('.master-grocery-item').filter(has=p.locator('.grocery-ingredient-name',has_text='rice')).first;rice.locator('.grocery-expand').evaluate('(b)=>{if(b.getAttribute("aria-expanded")!=="true")b.click()}');rice.locator('.grocery-contribution input').first.check();p.screenshot(path='/workspace/work/screenshots/'+name+'-partial-large126.png',full_page=True)
 rice.locator('.grocery-contribution-edit').click();p.set_viewport_size({'width':320,'height':420});p.get_by_label('Grocery item',exact=True).fill('3 cups fragrant rice');p.screenshot(path='/workspace/work/screenshots/'+name+'-keyboard126.png');p.get_by_role('button',name='Cancel',exact=True).click()
 p.set_viewport_size({'width':320,'height':800});p.evaluate('edge126.many()');p.get_by_role('button',name='Choose meals',exact=True).click();dialog=p.get_by_role('dialog',name='Choose Meals',exact=True);p.screenshot(path='/workspace/work/screenshots/'+name+'-grocery-filter126.png');weekX=dialog.locator('.grocery-filter-weeks input').first.bounding_box()['x'];mealX=dialog.locator('section label input').last.bounding_box()['x'];assert abs(weekX-mealX)<2,(weekX,mealX);dialog.get_by_role('button',name='Cancel',exact=True).click();p.get_by_label('Grocery view',exact=True).select_option('meal');assert p.locator('.grocery-meal-section').count()>=12;p.screenshot(path='/workspace/work/screenshots/'+name+'-many-sections126.png');p.locator('.grocery-meal-section').last.scroll_into_view_if_needed();p.screenshot(path='/workspace/work/screenshots/'+name+'-many-sections-bottom126.png');p.evaluate('edge126.onlyFuture()');assert p.locator('#todaysTodo').count()==0
 p.evaluate('edge126.allComplete()');assert p.locator('#todaysTodo').count()==0
 assert not errors,errors
 c.close();print('PASS',name,'126 duplicate auto/manual/no replacement, carry sequence, scale toggle combinations/default reset, backup validation, narrow/large text/keyboard',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:check(b,name)
  b.close()
