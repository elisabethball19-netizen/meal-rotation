"""Read-only grocery source navigation using saved ingredient tokens and explicit step links."""
import copy,json
from playwright.sync_api import sync_playwright
import grocery_bulk_performance_browser as perf
perf.fixture.HOOK+='''window.sourceSpec={
 seed:()=>{
  const current=getGroceryContributions(false,'current').find(s=>s.planId==='original'&&!s.parentId),upcoming=getGroceryContributions(false,'next').find(s=>s.planId==='original'&&!s.parentId);
  const currentMeal=meals.find(m=>m.id===current.mealId),futureMeal=meals.find(m=>m.id===upcoming.mealId);
  for(const meal of [currentMeal,futureMeal]){
   meal.ingredients=Array.from({length:96},(_,i)=>i===80?'1 cup fresh cilantro':'1 cup navigation vegetable '+i);
   meal.instructions=Array.from({length:50},(_,i)=>({type:'step',text:i===40?'Chop and add fresh cilantro.':'Instruction '+i+': cook carefully and continue stirring the prepared food until ready. '+('Continue following the recipe carefully. '.repeat(3))}));
   const items=cookingItemTokens(meal);meal.ingredientStepLinks=[{step:items.steps[35].token,ingredients:[items.ingredients[70].token]},{step:items.steps[30].token,ingredients:[items.ingredients[70].token]},{step:items.steps[0].token,ingredients:items.ingredients.slice(0,60).map(i=>i.token)}];
  }
  const child=meals.find(m=>m.id===55);child.cat='Reference';cats.push('Reference');child.rotation=false;child.recipeStatus='up-next';child.upNextStar=false;currentMeal.linkedMealIds=[child.id];
  localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));
  const plan=mealPlans.find(p=>p.id===current.planId),entry=recipePlanEntries(plan.id).find(e=>e.day===current.day&&String(e.meal.id)===String(currentMeal.id)),context=cookingContext(plan.id,entry.day,entry.cat,currentMeal,entry.linkedTo),key=cookingOccurrenceKey(context),items=cookingItemTokens(currentMeal);
  occurrenceScales.occurrences[key]={context,multiplier:3};writeOccurrenceScales(occurrenceScales);cookingSessions.occurrences[key]={id:'navigation-progress',context,ingredients:[items.ingredients[2].token],steps:[items.steps[1].token],autoIngredients:[],ingredientOverrides:{}};writeCookingSessions(cookingSessions);persist();renderList();
  const all=getGroceryContributions(true,'both');for(const [i,s]of all.entries()){groceryOccurrenceChecks.checks[s.id]=i%2===0;if(s.quantity)groceryOccurrenceChecks.quantities[s.id]={lo:i%2===0?s.quantity.lo:0,hi:i%2===0?s.quantity.hi:0}}saveGroceryOccurrenceChecks();
  const line=[...getMasterGroceryItems().values()].find(item=>item.contributions.some(s=>s.mealId===currentMeal.id&&s.ingredientToken===items.ingredients[70].token));localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify({[groceryTextKey(line)]:'Edited shopping label unrelated to recipe'}));
  window.navigationFixture={currentId:currentMeal.id,futureId:futureMeal.id,childId:child.id,day:current.day};renderList();
 },
 mode:mode=>{recipeViewPrefs.mode=mode;recipeViewPrefs.ratio=.43;recipeViewPrefs.syncIngredients=true;recipeViewPrefs.autoCompleteIngredients=true;saveRecipeViewPrefs()},
 period:value=>groceryPerf.period(value),
 source:(period,index)=>{const id=period==='next'?navigationFixture.futureId:navigationFixture.currentId,meal=meals.find(m=>m.id===id),token=cookingItemTokens(meal).ingredients[index].token;return getGroceryContributions(false,period).find(s=>String(s.mealId)===String(id)&&s.ingredientToken===token)},
 tokens:(id,index)=>{const m=meals.find(m=>m.id===id),items=cookingItemTokens(m);return {ingredient:items.ingredients[index].token,firstStep:items.steps[30].token,lateStep:items.steps[35].token,inferred:recipeIngredientMatches(m).get(items.steps[40].token)?.includes(items.ingredients[80].token),rawIngredients:items.ingredients.map(i=>i.token)}},
 open:openGroceryRecipeSource,normal:()=>openSavedMealRecipe(meals.find(m=>m.id===navigationFixture.currentId),cookingContext('original',navigationFixture.day,'Batch',meals.find(m=>m.id===navigationFixture.currentId))),
 state:()=>JSON.stringify({meals,plans:mealPlans,sessions:cookingSessions,scales:occurrenceScales,ledger:groceryOccurrenceChecks,legacy:[...checkedIngredients],manual:manualGroceryItems(),selected:localStorage.getItem('mealRotationSelectedIngredientsV1'),text:localStorage.getItem(GROCERY_TEXT_OVERRIDES_KEY),prefs:localStorage.getItem(RECIPE_VIEW_PREFS_KEY)}),
 viewer:()=>{const v=recipeViewer;return {mealId:v.mealId,context:v.context,scale:v.context?occurrenceMultiplier(v.context):v.previewScale,mode:recipeViewingMode(),tabs:v.tabs.map(t=>({id:t.mealId,context:t.context})),target:v.activeTab.sourceNavigation,applied:v.activeTab.sourceNavigationApplied,scroll:[v.cover.scrollTop,...v.content.querySelectorAll('.recipe-pane')].map(x=>typeof x==='number'?x:x.scrollTop)}},
 close:closeRecipeViewer,tab:id=>switchRecipeTab(recipeViewer.tabs.find(t=>String(t.mealId)===String(id))),
 geometry:token=>{const v=recipeViewer,button=[...v.content.querySelectorAll('[data-cooking-token]')].find(b=>b.dataset.cookingToken===token),pane=recipeViewingMode()==='split'?button.closest('.recipe-pane'):v.cover,b=button.getBoundingClientRect(),p=pane.getBoundingClientRect();return {top:b.top,bottom:b.bottom,paneTop:p.top,paneBottom:p.bottom,scroll:pane.scrollTop,pressed:button.getAttribute('aria-pressed'),selected:button.classList.contains('recipe-link-selected'),ingredientOrder:[...v.content.querySelectorAll('.recipe-ingredients-pane [data-cooking-token]')].map(b=>b.dataset.cookingToken)} }
};'''

def setup(browser,name,mode):
 c,p,errors,prefix=perf.setup(browser,name,55,8);p.evaluate('sourceSpec.seed()');p.evaluate('mode=>sourceSpec.mode(mode)',mode);p.set_default_timeout(8000);return c,p,errors,prefix

def wait_target(p):p.wait_for_function('window.sourceSpec&&sourceSpec.viewer().applied===true',timeout=8000)
def assert_visible(p,token):
 box=p.evaluate('token=>sourceSpec.geometry(token)',token);assert box['bottom']>box['paneTop'] and box['top']<box['paneBottom'],box;return box

def run(browser,name,mode):
 c,p,errors,prefix=setup(browser,name,mode)
 for period in ['current','next']:
  p.evaluate('period=>sourceSpec.period(period)',period)
  for index in [70,80,90]:
   source=p.evaluate('args=>sourceSpec.source(...args)',[period,index]);assert source
   tokens=p.evaluate('args=>sourceSpec.tokens(...args)',[source['mealId'],index]);before=p.evaluate('sourceSpec.state()')
   if index==70:
    # Exercise a real expanded source button on the existing grocery row, including edited text.
    p.locator('.grocery-recipe-link').evaluate_all('(links,id)=>{for(const link of links)if(link.dataset.grocerySourceId===id)link.dataset.fixtureTarget="true"}',source['id'])
    link=p.locator('[data-fixture-target="true"]');assert link.count()==1
    row=link.locator('..').locator('..').locator('..')
    if period=='current':assert row.locator('.grocery-ingredient-name').inner_text()=='Edited shopping label unrelated to recipe'
    row.locator('.grocery-ingredient-name').tap();link.tap()
   else:p.evaluate('source=>sourceSpec.open(source)',source)
   wait_target(p);view=p.evaluate('sourceSpec.viewer()');assert view['mealId']==str(source['mealId']) and view['mode']==mode
   assert view['target']['ingredientToken']==tokens['ingredient'] and view['target']['scheduledDate']==source['scheduledDate']
   if period=='current':assert view['context']['planId']==source['planId'] and view['context']['day']==source['day'] and view['scale']==3
   else:assert view['context'] is None and view['scale']==1
   geometry=assert_visible(p,tokens['ingredient'])
   if index==70:
    assert view['target']['stepToken']==tokens['firstStep'] and view['target']['stepToken']!=tokens['lateStep']
    assert geometry['ingredientOrder'].index(tokens['ingredient'])!=tokens['rawIngredients'].index(tokens['ingredient'])
    step=p.evaluate('token=>sourceSpec.geometry(token)',tokens['firstStep']);assert step['selected'] and step['pressed']=='false'
    if mode=='split':assert_visible(p,tokens['firstStep']);assert view['scroll'][1]>0 and view['scroll'][2]>0
    else:assert view['scroll'][0]>0 and step['top']>step['paneBottom']
   else:
    assert view['target']['stepToken'] is None
    if index==80:assert tokens['inferred'] is True
    if mode=='split':assert view['scroll'][2]==0
   initial=p.evaluate('sourceSpec.viewer().scroll');p.wait_for_timeout(500);assert p.evaluate('sourceSpec.viewer().scroll')==initial,'delayed scroll jump'
   assert p.evaluate('sourceSpec.state()')==before,'navigation changed saved state'
   if index==70 and period=='current':
    child=p.evaluate('navigationFixture.childId');assert str(child) in [t['id']for t in view['tabs']]
    p.evaluate('id=>sourceSpec.tab(id)',child);p.evaluate('id=>sourceSpec.tab(id)',source['mealId']);p.wait_for_timeout(100);assert_visible(p,tokens['ingredient']);assert p.evaluate('sourceSpec.state()')==before
   p.evaluate('sourceSpec.close()');p.wait_for_timeout(30)
  print('PASS',name,mode,period,'linked/unlinked/inferred-only ingredients, first explicit step, edited wording/scaling, reordered display, stable panes/tabs and no saved-state changes',flush=True)
 # Bad identities or stale occurrences fall back to ordinary recipe opening, never a guessed target.
 source=p.evaluate("sourceSpec.source('current',70)")
 for bad in [{**source,'ingredientToken':'not-a-saved-token'},{**source,'scheduledDate':'1900-01-01'}]:
  before=p.evaluate('sourceSpec.state()');p.evaluate('source=>sourceSpec.open(source)',bad);p.wait_for_timeout(120);view=p.evaluate('sourceSpec.viewer()');assert not view.get('target') and not view.get('applied');assert p.evaluate('sourceSpec.state()')==before;p.evaluate('sourceSpec.close()');p.wait_for_timeout(30)
 before=p.evaluate('sourceSpec.state()');p.evaluate('sourceSpec.normal()');p.wait_for_timeout(120);assert not p.evaluate('sourceSpec.viewer()').get('target') and p.locator('.recipe-link-selected').count()==0;assert p.evaluate('sourceSpec.state()')==before;p.evaluate('sourceSpec.close()')
 assert p.locator('.manual-grocery-item .grocery-recipe-link').count()==0
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;c.close();print('PASS',name,mode,'unresolvable source fallback, unchanged ordinary opening and manual groceries, isolated storage/runtime',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for mode in ['split','full']:run(browser,name,mode)
  browser.close()
