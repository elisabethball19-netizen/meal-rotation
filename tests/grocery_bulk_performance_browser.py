"""Disposable representative grocery fixture, actual toolbar timings and immediate call counts."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as fixture
ROOT=Path(__file__).resolve().parents[1]
fixture.HOOK+='''window.groceryPerf={
 seed:(recipeCount=55,ingredientCount=20)=>{
  cats=['Batch'];active='Batch';id=recipeCount+1;meals=Array.from({length:recipeCount},(_,i)=>({id:i+1,name:'Fixture recipe '+(i+1),cat:'Batch',rotation:true,ingredients:Array.from({length:ingredientCount},(_,j)=>'1 cup '+(j<4?'shared pantry '+j:'recipe '+(i+1)+' ingredient '+j)),instructions:[{type:'step',text:'Cook fixture ingredients.'}],notes:'Keep recipe notes '+i,makeAheadTasks:[{id:'prep',description:'Prepare fixture',daysBefore:1}]}));
  mealPlans=['original','lunch','excluded'].map((id,i)=>({id,name:['Dinner','Lunch','Excluded'][i],weekdayCategories:Object.fromEntries(weekdays.map(day=>[day,['Batch']])),weekdayMealOverrides:{},weekdayRecipeFilters:{},pinnedCats:[]}));activePlanId='original';weekdayCategories=JSON.parse(JSON.stringify(mealPlans[0].weekdayCategories));weekdayMealOverrides={};weekdayRecipeFilters={};showMealPlanTabs=true;localStorage.setItem('mealRotationShowPlanTabsV1','true');
  masterGroceryExcludedPlanIds=new Set(['excluded']);masterGroceryExcludedMealKeys=new Set();saveMasterGroceryPlanExclusions();saveMasterGroceryMealExclusions();
  localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));
  cookingSessions={version:1,occurrences:{}};occurrenceScales={version:1,occurrences:{}};groceryOccurrenceChecks={version:1,checks:{},quantities:{}};checkedIngredients=new Set();
  saveManualGroceryItems(Array.from({length:24},(_,i)=>({id:'manual-'+i,text:'Manual fixture item '+i,checked:i%3===0})));
  saveActiveMealPlan();persist();
  for(const plan of mealPlans){const entries=getDisplayedWeekdayMealsForPlan(plan),calendar=rotationCalendarForPlan(plan,entries),start=cookingPlanningWeekStart();for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:plan.id});calendar.occurrences[key]=cookingLocalDate(cookingDateInWeek(entry.day,start));calendar.assignedOn[key]=cookingLocalDate(start);calendar.assignedAt[key]=start.toISOString()}plan.rotationCalendar=calendar}
  localStorage.setItem(GROCERY_PERIOD_KEY,'both');groceryPeriod='both';saveActiveMealPlan();persist();
  const sources=getGroceryContributions(true,'both');for(const [i,source]of sources.entries()){groceryOccurrenceChecks.checks[source.id]=i%3===0;if(source.quantity)groceryOccurrenceChecks.quantities[source.id]={lo:i%3===0?source.quantity.lo:0,hi:i%3===0?source.quantity.hi:0}}
  saveGroceryOccurrenceChecks();showTop=true;groceryTabActive=true;allMealsActive=false;render();
 },
 metrics:()=>({recipes:meals.length,recipeIngredients:meals.reduce((n,m)=>n+m.ingredients.length,0),sources:getGroceryContributions(true,'both').length,visibleSources:getGroceryContributions(false,groceryPeriod).length,recipeRows:getMasterGroceryItems().size,manualItems:manualGroceryItems().length,period:groceryPeriod}),
 profile:()=>{
  const counts={},wrap=(name,original)=>function(...args){counts[name]=(counts[name]||0)+1;return original.apply(this,args)};
  getGroceryContributions=wrap('contributions',getGroceryContributions);captureGroceryCheckStates=wrap('captureChecks',captureGroceryCheckStates);saveGroceryOccurrenceChecks=wrap('saveChecks',saveGroceryOccurrenceChecks);getMasterGroceryItems=wrap('generateList',getMasterGroceryItems);renderList=wrap('renderList',renderList);previewNextWeekPlans=wrap('previewWeek',previewNextWeekPlans);saveActiveMealPlan=wrap('savePlan',saveActiveMealPlan);reconcileRotationCalendars=wrap('reconcileCalendar',reconcileRotationCalendars);
  window.groceryPerfCounts=counts;
 },
 action:checked=>{for(const key of Object.keys(window.groceryPerfCounts))delete window.groceryPerfCounts[key];const start=performance.now();document.querySelector('[aria-label="'+(checked?'Select all groceries':'Deselect all groceries')+'"]').onclick();return {checked,ms:performance.now()-start,counts:{...window.groceryPerfCounts}}},
 period:value=>{groceryPeriod=value;localStorage.setItem(GROCERY_PERIOD_KEY,value);renderList()},
 rows:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,checked:groceryItemChecked(key,item),sources:item.contributions})),
 allSources:()=>getGroceryContributions(true,'both').map(source=>({...source,checked:grocerySourceChecked(source),amount:groceryCheckedAmount(source)})),
 manual:manualGroceryItems,ledger:()=>groceryOccurrenceChecks,
 stable:()=>JSON.stringify({meals,plans:mealPlans,sessions:cookingSessions,scales:occurrenceScales,selected:localStorage.getItem('mealRotationSelectedIngredientsV1'),text:localStorage.getItem(GROCERY_TEXT_OVERRIDES_KEY)}),
 undo:()=>{redoHistory.push(captureState());restoreState(JSON.parse(history.pop()))},redo:()=>{history.push(captureState());restoreState(JSON.parse(redoHistory.pop()))}
};'''
def setup(browser,name,recipe_count=55,ingredient_count=20):
 c,p,errors,prefix=fixture.setup(browser,name);p.set_default_timeout(120000);p.clock.set_fixed_time(datetime(2026,11,10,12,tzinfo=timezone.utc));p.evaluate('args=>groceryPerf.seed(...args)',[recipe_count,ingredient_count]);return c,p,errors,prefix

def measure(browser,name,trials=1):
 c,p,errors,prefix=setup(browser,name);metrics=p.evaluate('groceryPerf.metrics()');p.evaluate('groceryPerf.profile()');results=[]
 for _ in range(trials):
  for checked in [True,False]:
   result=p.evaluate('checked=>groceryPerf.action(checked)',checked);results.append(result);print(json.dumps({'app':name,'metrics':metrics,'action':result}),flush=True)
 assert not errors,errors;c.close();return dict(app=name,metrics=metrics,results=results)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--output');parser.add_argument('--app',default='both');parser.add_argument('--trials',type=int,default=1);args=parser.parse_args()
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);results=[measure(browser,name,args.trials)for name in (['index.html','meal-rotation-test.html'] if args.app=='both' else [args.app])];browser.close()
 if args.output:Path(args.output).write_text(json.dumps(results,indent=2))
