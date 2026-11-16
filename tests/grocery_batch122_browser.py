"""Issue 122 disposable mobile fixtures; never touches a user's origin/storage."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as fixture
fixture.HOOK+='''window.batch122={
 seed:()=>{
 cats=['Bread','Meals','Sides'];active='Bread';meals=Array.from({length:57},(_,i)=>({id:i+1,name:i?'Bread idea '+i:'Easy Sourdough Bread',cat:'Bread',rotation:i===0,recipeStatus:i===0?'rotation':'up-next',ingredients:['1 cup rice'],instructions:[{type:'step',text:'Cook rice.'}]}));
 meals.push({id:101,name:'Easy Sourdough Bread',cat:'Meals',rotation:true,linkGroup:'bread',ingredients:['1 cup rice']});meals[0].linkGroup='bread';
 meals.push({id:102,name:'Garlic rice with an especially long recipe name for narrow screens',cat:'Meals',rotation:true,ingredients:['2 cups rice','2 cloves garlic, minced']});
 mealPlans=[{id:'original',name:'Dinner',weekdayCategories:{Monday:['Meals'],Tuesday:['Meals']},weekdayMealOverrides:{'Monday::Meals':'101','Tuesday::Meals':'102'},weekdayRecipeFilters:{},pinnedCats:[]}];activePlanId='original';weekdayCategories=JSON.parse(JSON.stringify(mealPlans[0].weekdayCategories));weekdayMealOverrides={...mealPlans[0].weekdayMealOverrides};weekdayRecipeFilters={};showMealPlanTabs=false;
 localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify({'101':['1 cup rice'],'102':['2 cups rice','2 cloves garlic, minced']}));
 cookingSessions={version:1,occurrences:{}};occurrenceScales={version:1,occurrences:{}};groceryOccurrenceChecks={version:1,checks:{},quantities:{}};checkedIngredients=new Set();saveGroceryOccurrenceChecks();groceryPeriod='current';localStorage.setItem(GROCERY_PERIOD_KEY,'current');persist();saveActiveMealPlan();establishDatedFixtureSchedule();batch1.groups();
 },
 settings:saveMealGroupSettings,raw:()=>JSON.stringify(meals),
 grocery:()=>{showTop=true;groceryTabActive=true;allMealsActive=false;renderList({readOnly:true})},
 sources:()=>getGroceryContributions(false,'current'),
 scale:(id,n,day=null)=>{const source=getGroceryContributions(false,'current').find(s=>s.mealId===id&&(!day||s.day===day)),m=meals.find(m=>m.id===id),ctx=cookingContext(source.planId,source.day,source.cat,m,source.parentId);occurrenceScales.occurrences[cookingOccurrenceKey(ctx)]={context:ctx,multiplier:n};writeOccurrenceScales(occurrenceScales);batch122.grocery()},
 undo:()=>{const state=history.pop();redoHistory.push(captureHistoryCounterpart(JSON.parse(state)));restoreState(JSON.parse(state))},redo:()=>{const state=redoHistory.pop();history.push(captureHistoryCounterpart(JSON.parse(state)));restoreState(JSON.parse(state))},
 rows:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,text:item.line,sources:item.contributions.map(s=>({id:s.id,checked:grocerySourceChecked(s),text:groceryContributionText(s)}))})),
 extras:()=>{
  weekdayCategories.Wednesday=['Meals'];weekdayMealOverrides['Wednesday::Meals']='101';saveActiveMealPlan();persist();
  const plan=mealPlans[0],entry=getDisplayedWeekdayMealsForPlan(plan).find(e=>e.day==='Monday');
  plan.simpleSideOccurrences={...(plan.simpleSideOccurrences||{}),[simpleSideOccurrenceKey(plan,entry)]:[{id:'peas',name:'Peas',ingredients:[{id:'peas-ingredient',text:'1 cup peas'}]}]};
  saveActiveMealPlan();persist();saveManualGroceryItems([{id:'manual',text:'Unrelated manual item',checked:true}]);batch122.grocery();
 },
 editSource:id=>{const source=getGroceryContributions(false,'current').find(s=>s.id===id);openGroceryTextEditor({line:groceryContributionText(source),contributions:[source]},()=>batch122.grocery())},
 legacy:(id,text)=>{localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify({[JSON.stringify([id])]:text}));batch122.grocery()},
 pin:id=>applyRecipeBulk([String(id)],{upNextStar:!meals.find(m=>m.id===id).upNextStar},{upNextFirst:String(id)})
};'''

def run(browser,name):
 c,p,errors,prefix=fixture.setup(browser,name)
 p.evaluate('batch122.seed()')
 before=p.evaluate('batch122.raw()')
 p.evaluate("batch122.settings('Bread','Bread',false)")
 assert p.locator('[data-category="Bread"] .master-category-meal').count()==57
 assert p.locator('[data-category="Bread"] .recipe-up-next-star').count()==57
 assert p.evaluate('batch122.raw()')==before
 p.locator('[data-category="Bread"] [data-meal-id="1"] .recipe-up-next-star').tap()
 assert p.locator('[data-category="Bread"] .master-category-meal').first.get_attribute('data-meal-id')=='1'
 p.evaluate('batch122.undo()');assert p.evaluate('batch122.raw()')==before
 p.evaluate('batch122.redo()');assert p.locator('[data-category="Bread"] [data-meal-id="1"] .recipe-up-next-star').get_attribute('aria-pressed')=='true'
 Path('/workspace/work/screenshots').mkdir(exist_ok=True)
 p.locator('[data-category="Bread"] [data-meal-id="1"]').scroll_into_view_if_needed();p.screenshot(path='/workspace/work/screenshots/'+name+'-pins.png')
 p.reload();p.evaluate('batch1.groups()');assert p.locator('[data-category="Bread"] .master-category-meal').count()==57
 p.evaluate("batch122.settings('Bread','Bread',true)");assert p.evaluate('batch1.records()').__len__()==59
 assert p.evaluate('batch1.records().find(m=>m.id===1).rotation') is True
 # Assigned group guard rejects without changing records; Cancel writes nothing.
 saved=p.evaluate('batch122.raw()');assert p.evaluate("(()=>{try{batch122.settings('Meals','Meals',false);return false}catch(e){return e.message.includes('assignments')}})()")
 p.evaluate("batch1.groupEdit('Meals')");p.get_by_role('dialog',name='Edit group',exact=True).get_by_role('button',name='Cancel group editing',exact=True).click();assert p.evaluate('batch122.raw()')==saved
 p.evaluate('batch122.grocery()')
 rice=p.locator('.master-grocery-item').filter(has=p.locator('.grocery-ingredient-name',has_text='3 cups rice'))
 assert rice.count()==1 and rice.locator('.grocery-ingredient-name').inner_text()=='3 cups rice (2)'
 assert p.locator('.grocery-expand').count()==2
 rice.locator('.grocery-ingredient-name').tap();assert rice.locator('.grocery-contribution').count()==2
 rice.locator('.grocery-contribution input').first.check();assert rice.locator('.grocery-checkbox-target input').evaluate('(x)=>x.indeterminate')
 assert rice.locator('.grocery-ingredient-name').inner_text()=='3 cups rice (2)'
 p.get_by_role('button',name='Hide checked groceries',exact=True).tap();assert rice.count()==1 and rice.locator('.grocery-contribution input').count()==2
 p.reload();p.evaluate('batch122.grocery()');assert rice.locator('.grocery-checkbox-target input').evaluate('(x)=>x.indeterminate')
 p.get_by_role('button',name='Show checked groceries',exact=True).tap()
 rice.locator('.grocery-checkbox-target input').check();assert all(s['checked']for s in p.evaluate('batch122.rows()')[0]['sources'])
 rice.locator('.grocery-checkbox-target input').uncheck();assert not any(s['checked']for r in p.evaluate('batch122.rows()')for s in r['sources'])
 garlic=p.locator('.master-grocery-item').filter(has=p.locator('.grocery-ingredient-name',has_text='garlic'))
 garlic.locator('.grocery-expand').tap();garlic.locator('.grocery-contribution-edit').tap()
 d=p.get_by_role('dialog',name='Edit grocery item',exact=True)
 assert d.get_by_text('Changes apply only to your grocery list. Quantities still update when you scale the recipe.',exact=True).count()==1
 d.get_by_role('textbox').fill('2 cloves garlic');d.get_by_role('button',name='Save grocery item',exact=True).tap()
 for n,text in [(2,'4 cloves garlic'),(.5,'1 cloves garlic'),(1,'2 cloves garlic')]:
  p.evaluate('n=>batch122.scale(102,n)',n);assert any(r['text']==text.replace('1 cloves','1 clove') for r in p.evaluate('batch122.rows()')),p.evaluate('batch122.rows()')
 assert p.evaluate('batch1.records().find(m=>m.id===102).ingredients[1]')=='2 cloves garlic, minced'
 p.reload();p.evaluate('batch122.grocery()');assert any(r['text']=='2 cloves garlic'for r in p.evaluate('batch122.rows()'))
 p.locator('.grocery-expand').first.tap();p.screenshot(path='/workspace/work/screenshots/'+name+'-groceries.png')
 p.set_viewport_size({'width':320,'height':640});p.evaluate("document.body.dataset.mealTextSize='extra'");p.screenshot(path='/workspace/work/screenshots/'+name+'-large.png');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 p.set_viewport_size({'width':740,'height':360});p.screenshot(path='/workspace/work/screenshots/'+name+'-landscape.png')
 # Same recipe on two days retains source identities; simple sides share only their occurrence scale.
 p.set_viewport_size({'width':360,'height':800});p.evaluate('batch122.extras()')
 sources=p.evaluate('batch122.sources()');rice=[s for s in sources if s['mealId']==101 and not s.get('simpleSideId')];assert len(rice)==2 and rice[0]['id']!=rice[1]['id']
 side=next(s for s in sources if s.get('simpleSideId'))
 p.evaluate('id=>batch122.editSource(id)',side['id']);d=p.get_by_role('dialog',name='Edit grocery item',exact=True);d.get_by_role('textbox').fill('1 cup garden peas');d.get_by_role('button',name='Save grocery item',exact=True).tap()
 p.evaluate("batch122.scale(101,2,'Monday')");rows=p.evaluate('batch122.rows()');assert any(r['text']=='2 cups garden peas'for r in rows)
 sources=p.evaluate('batch122.sources()');assert next(s for s in sources if s['mealId']==101 and s['day']=='Wednesday' and not s.get('simpleSideId'))['line']=='1 cup rice'
 monday=next(s for s in sources if s['mealId']==101 and s['day']=='Monday' and not s.get('simpleSideId'))
 p.evaluate('id=>batch122.editSource(id)',monday['id']);d=p.get_by_role('dialog',name='Edit grocery item',exact=True);d.get_by_role('textbox').fill('10 cups special rice');d.get_by_role('button',name='Save grocery item',exact=True).tap()
 p.evaluate("batch122.scale(101,.5,'Monday')");assert any(r['text']=='2½ cups special rice'for r in p.evaluate('batch122.rows()')),p.evaluate('batch122.rows()')
 assert any(r['text']=='3 cups rice'for r in p.evaluate('batch122.rows()'))
 # Cancel and text Undo/Redo preserve other source wording and manual checks.
 p.evaluate('id=>batch122.editSource(id)',monday['id']);d=p.get_by_role('dialog',name='Edit grocery item',exact=True);d.get_by_role('textbox').fill('Discard this');d.get_by_role('button',name='Cancel',exact=True).tap();assert not any('Discard' in r['text']for r in p.evaluate('batch122.rows()'))
 p.evaluate('batch122.undo()');assert not any('special rice' in r['text']for r in p.evaluate('batch122.rows()'))
 p.evaluate('batch122.redo()');assert any('special rice' in r['text']for r in p.evaluate('batch122.rows()'))
 assert p.locator('.manual-grocery-item input').is_checked()
 # An older unambiguous rename scales from recipe quantity; ambiguous quantities stay intact.
 garlic=next(s for s in p.evaluate('batch122.sources()')if 'garlic' in s['original'])
 p.evaluate('id=>batch122.legacy(id,"2 cloves garlic")',garlic['id']);p.evaluate('batch122.scale(102,2)');assert any(r['text']=='4 cloves garlic'for r in p.evaluate('batch122.rows()'))
 p.evaluate('id=>batch122.legacy(id,"7 cloves garlic")',garlic['id']);p.evaluate('batch122.scale(102,.5)');assert any(r['text']=='7 cloves garlic'for r in p.evaluate('batch122.rows()'))
 assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'57 mixed reference recipes, pins, guard/cancel, per-source checks, wording/scaling, reload, narrow/large/landscape')
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
