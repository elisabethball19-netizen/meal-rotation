"""Bulk grocery checks against the unchanged single-row semantics and existing history controls."""
import json,copy
from playwright.sync_api import sync_playwright
import grocery_bulk_performance_browser as perf
perf.fixture.HOOK+='''window.groceryBulkSpec={
 setup:()=>{
  const sources=getGroceryContributions(true,'both');
  for(const [i,source]of sources.entries())if(i%7===0){delete groceryOccurrenceChecks.checks[source.id];delete groceryOccurrenceChecks.quantities[source.id];checkedIngredients.add(source.baseKey)}
  const visible=getGroceryContributions(false,'both'),source=visible.find(s=>s.quantity&&s.mealId===visible[0].mealId);groceryOccurrenceChecks.checks[source.id]=false;groceryOccurrenceChecks.quantities[source.id]={lo:source.quantity.lo*.4,hi:source.quantity.hi*.4};
  const meal=meals.find(m=>m.id===source.mealId),plan=mealPlans.find(p=>p.id===source.planId),entry=getDisplayedWeekdayMealsForPlan(plan).find(e=>e.day===source.day&&e.meal.id===source.mealId),context=cookingContext(plan.id,entry.day,entry.cat,meal,entry.linkedTo),tokens=cookingItemTokens(meal),key=cookingOccurrenceKey(context);
  cookingSessions.occurrences[key]={id:'bulk-progress',context,ingredients:[tokens.ingredients[0].token],steps:[tokens.steps[0].token],autoIngredients:[],ingredientOverrides:{}};occurrenceScales.occurrences[key]={context,multiplier:2};writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales);
  saveGroceryOccurrenceChecks();localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));
  const line=[...getMasterGroceryItems().values()][0];localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify({[groceryTextKey(line)]:'Edited shopping wording kept'}));persist();renderList();
 },
 expected:checked=>{
  const items=getMasterGroceryItems(),sources=getGroceryContributions(true,'both'),savedLedger=groceryOccurrenceChecks,savedLegacy=checkedIngredients,capture=captureGroceryCheckStates,save=saveGroceryOccurrenceChecks;
  groceryOccurrenceChecks=JSON.parse(JSON.stringify(savedLedger));checkedIngredients=new Set(savedLegacy);
  // The old single-row operation re-captures current check values on every item.
  // Reuse the fixed scheduled source universe here to keep the reference fixture fast.
  captureGroceryCheckStates=()=>new Map(sources.map(source=>[source.id,{source,checked:grocerySourceChecked(source),amount:groceryCheckedAmount(source)}]));saveGroceryOccurrenceChecks=()=>true;
  try{for(const [key,item]of items)setGroceryItemChecked(key,item,checked);return JSON.parse(JSON.stringify({ledger:groceryOccurrenceChecks,legacy:[...checkedIngredients].sort(),rows:[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,checked:groceryItemChecked(key,item)}))}))}
  finally{groceryOccurrenceChecks=savedLedger;checkedIngredients=savedLegacy;captureGroceryCheckStates=capture;saveGroceryOccurrenceChecks=save}
 },
 checks:()=>JSON.parse(JSON.stringify({ledger:groceryOccurrenceChecks,legacy:[...checkedIngredients].sort(),rows:[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,checked:groceryItemChecked(key,item)}))})),
 hide:value=>{localStorage.setItem('mealRotationHideCheckedGroceriesV1',String(value));renderList()},
 excludeMeal:()=>{const source=getGroceryContributions(false,'both').find(s=>s.planId==='original');masterGroceryExcludedMealKeys.add(groceryMealKey(mealPlans.find(p=>p.id===source.planId),meals.find(m=>m.id===source.mealId)));saveMasterGroceryMealExclusions();renderList()},
 undo:()=>document.getElementById('undo').onclick(),redo:()=>document.getElementById('redo').onclick(),cleanup:()=>advanceWholeGroceryWeek(true,false)
};'''

def run(browser,name):
 c,p,errors,prefix=perf.setup(browser,name,55,8);p.evaluate('groceryBulkSpec.setup()');p.evaluate('groceryBulkSpec.excludeMeal()');p.evaluate('groceryPerf.profile()')
 for period in ['current','next','both','none']:
  p.evaluate('value=>groceryPerf.period(value)',period)
  for checked in [True,False]:
   p.evaluate('value=>groceryBulkSpec.hide(value)',not checked)
   before=p.evaluate('groceryPerf.allSources()');stable=p.evaluate('groceryPerf.stable()');manual=p.evaluate('groceryPerf.manual()');initial=p.evaluate('groceryBulkSpec.checks()')
   target={s['id'] for row in p.evaluate('groceryPerf.rows()') for s in row['sources']}
   expected=p.evaluate('checked=>groceryBulkSpec.expected(checked)',checked);result=p.evaluate('checked=>groceryPerf.action(checked)',checked)
   assert result['counts'].get('saveChecks',0)<=1 and result['counts']['generateList']==2 and result['counts'].get('captureChecks',0)<=4,result
   assert p.evaluate('groceryBulkSpec.checks()')==expected,(name,period,checked)
   after={s['id']:s for s in p.evaluate('groceryPerf.allSources()')}
   for source in before:
    if source['id'] not in target:assert after[source['id']]['checked']==source['checked'] and after[source['id']]['amount']==source['amount'],(period,source)
   assert all(item['checked']==checked for item in p.evaluate('groceryPerf.manual()'))
   assert p.evaluate('groceryPerf.stable()')==stable
   # Existing Undo/Redo handlers also restore the action's manual-item checks.
   p.evaluate('groceryBulkSpec.undo()');assert p.evaluate('groceryBulkSpec.checks()')==initial and p.evaluate('groceryPerf.manual()')==manual
   p.evaluate('groceryBulkSpec.redo()');assert p.evaluate('groceryBulkSpec.checks()')==expected and all(x['checked']==checked for x in p.evaluate('groceryPerf.manual()'))
  print('PASS',name,period,'Select/Deselect scope, scalar-equivalent amounts/order, excluded checks, manual items, Undo/Redo and one ledger save',flush=True)
 p.evaluate("groceryPerf.period('both')");p.evaluate('groceryPerf.action(true)');expected=p.evaluate('groceryBulkSpec.checks()');manual=p.evaluate('groceryPerf.manual()');p.reload();assert p.evaluate('groceryBulkSpec.checks()')==expected and p.evaluate('groceryPerf.manual()')==manual
 before=p.evaluate('groceryPerf.manual()');assert before and all(x['checked']for x in before);p.evaluate('groceryBulkSpec.cleanup()');assert p.evaluate('groceryPerf.manual()')==[];p.evaluate('groceryBulkSpec.undo()');assert p.evaluate('groceryPerf.manual()')==before
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;c.close();print('PASS',name,'bulk checks reload and whole-week manual cleanup/Undo without storage crossover',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(browser,name)
  browser.close()
