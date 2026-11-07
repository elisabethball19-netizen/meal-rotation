"""Multiple unchecked groups: persisted slot cleanup, scope, reload and reassign."""
import json
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
f.EXTRA+='''window.groupRemoval={
 seed:(day,mode)=>{
  cats=['Weekend','Breakfast','Lunch','Sides'];meals=['Weekend','Breakfast','Lunch'].flatMap((cat,i)=>[0,1].map(n=>({id:i*2+n+1,cat,name:cat+' meal '+(n+1),rotation:true,ingredients:['1 cup rice'],instructions:'Cook.',notes:'Keep me'})));id=7;
  const plan=id=>({id,name:id==='original'?'Dinner':'Other tab',weekdayCategories:{Saturday:['Weekend','Breakfast','Lunch'],Sunday:['Weekend','Breakfast','Lunch']},weekdayMealOverrides:{},cycleRetainedSlots:{},cycleSlotChoices:{},weekdayRecipeFilters:{},pinnedCats:[],weekSchedule:{version:1,slots:{},order:{Saturday:['["Weekend"]','["Breakfast"]','["Lunch"]'],Sunday:['["Weekend"]','["Breakfast"]','["Lunch"]']}}});mealPlans=[plan('original'),plan('other')];
  for(const p of mealPlans)for(const d of ['Saturday','Sunday'])for(const [i,cat]of ['Weekend','Breakfast','Lunch'].entries()){const key=d+'::'+cat,value=String(i*2+(d==='Saturday'?1:2));p.weekdayMealOverrides[key]=value;p.cycleRetainedSlots[key]=value;p.cycleSlotChoices[key]={mealId:value,parentId:'',substitution:true,retain:true,blockedParents:[]}}
  const p=mealPlans[0];for(const d of ['Saturday','Sunday']){p.weekSchedule.slots[d+'::Breakfast']={kind:'once',meal:{id:'once-'+d,name:'Sandwiches',cat:'Breakfast',temporaryMeal:true,rotation:false,ingredients:['1 cup rice']}};p.weekSchedule.slots[d+'::Lunch']={kind:'empty'}}
  if(mode==='both_meals'){delete p.weekSchedule.slots[day+'::Breakfast'];delete p.weekSchedule.slots[day+'::Lunch']}
  if(mode==='adopted_meal'){delete p.weekSchedule.slots[day+'::Breakfast'];p.occasionalMeals={[day]:p.weekdayMealOverrides[day+'::Breakfast']};p.cycleSlotChoices[day+'::Breakfast'].occasional=true}
  if(mode==='both_empty')p.weekSchedule.slots[day+'::Breakfast']={kind:'empty'};
  mealPlans[1].weekSchedule.slots['Saturday::Breakfast']={kind:'once',meal:{id:'once-other-tab',name:'Untouched other tab meal',cat:'Breakfast',temporaryMeal:true,rotation:false,ingredients:[]}};
  activePlanId='original';weekdayCategories=JSON.parse(JSON.stringify(p.weekdayCategories));weekdayMealOverrides={...p.weekdayMealOverrides};weekdayRecipeFilters={};groceryOccurrenceChecks={version:1,checks:{}};checkedIngredients.clear();localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));localStorage.removeItem('mealRotationLastRotationBeforeV1');saveActiveMealPlan();persist();promotionTest.my();preserveOtherMealPlanChoices(null,null);saveActiveMealPlan();for(const s of getGroceryContributions(true))groceryOccurrenceChecks.checks[s.id]=s.day==='Sunday';saveGroceryOccurrenceChecks();localStorage.setItem('mealRotationLastRotationBeforeV1',captureState());
 },
 open:day=>openDayCategoryPicker(day),
 assigned:day=>getDayCategories(day),
 rows:day=>getDisplayedWeekdayMeals().filter(e=>e.day===day).map(e=>[e.cat,String(e.meal.id),!!e.meal.temporaryMeal]),
 weekend:day=>String(getDisplayedWeekdayMeals().find(e=>e.day===day&&e.cat==='Weekend')?.meal.id),
 visible:day=>[...document.querySelectorAll('[data-week-row][data-schedule-day="'+day+'"]')].map(e=>JSON.parse(e.dataset.displayKey)[0]),
 recipes:()=>JSON.stringify(meals),
 plan:()=>mealPlans[0],
 elsewhere:day=>{const p=mealPlans[0],other=day==='Saturday'?'Sunday':'Saturday',filter=map=>Object.fromEntries(Object.entries(map||{}).filter(([key])=>key.startsWith(other+'::')));return JSON.stringify({otherTab:mealPlans[1],otherAssignments:p.weekdayCategories[other],overrides:filter(p.weekdayMealOverrides),pins:filter(p.cycleRetainedSlots),choices:filter(p.cycleSlotChoices),weekSlots:filter(p.weekSchedule.slots),order:p.weekSchedule.order[other],checks:getGroceryContributions(true).filter(s=>s.planId!=='original'||s.day!==day).map(s=>[s.id,grocerySourceChecked(s)]),settings:localStorage.getItem('mealRotationCustomSettingV9'),ingredients:localStorage.getItem('mealRotationSelectedIngredientsV1'),history:localStorage.getItem('mealRotationLastRotationBeforeV1')})},
 otherRows:day=>mealPlans.flatMap(p=>getDisplayedWeekdayMealsForPlan(p).filter(e=>p.id!=='original'||e.day!==day).map(e=>[p.id,e.day,e.cat,String(e.meal.id)])),
 rotate:day=>moveDisplayedMealsToBottom(new Set([day+'::Breakfast'])),
 legacy:day=>{weekdayCategories[day]=['Weekend'];for(const c of ['Breakfast','Lunch']){const key=day+'::'+c;delete weekdayMealOverrides[key];delete mealPlans[0].cycleRetainedSlots[key];delete mealPlans[0].cycleSlotChoices[key]}saveActiveMealPlan();persist();renderList()},
 dayOnlyLibrary:day=>{mealPlans[0].occasionalMeals={[day]:'3'};saveActiveMealPlan();persist();renderList()},
 dayOnly:day=>saveOneTimeMeal(day,null,'Keep day-only meal',['1 cup beans']),
 hiddenSide:day=>{const parent=getDisplayedWeekdayMeals().find(e=>e.day===day&&e.cat==='Weekend').meal;meals.push({id:9,cat:'Sides',name:'Keep hidden side',rotation:false,keepAsIdea:true,ingredients:['1 cup beans']});parent.linkedMealIds=[9];persist();renderList();leaveWeekEmpty(day,'Sides')}
};'''

def dialog(p,day):
 p.evaluate('groupRemoval.open',day);return p.get_by_role('dialog',name='Choose '+day+"'s meal groups",exact=True)

def removed_state(p,day):
 assert p.evaluate('groupRemoval.assigned',day)==['Weekend']
 state=p.evaluate('groupRemoval.plan()')
 for cat in ['Breakfast','Lunch']:
  key=day+'::'+cat
  for field in ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices']:assert key not in state[field],(field,key,state[field])
  assert key not in state['weekSchedule']['slots'],state['weekSchedule']['slots']
 assert p.evaluate('groupRemoval.visible',day)==['Weekend']

def run(b,name,day,mode):
 c,p,errors,prefix=f.setup(b,name,360);p.evaluate('([d,m])=>groupRemoval.seed(d,m)',[day,mode]);p.reload();p.evaluate('promotionTest.my()')
 recipes=p.evaluate('groupRemoval.recipes()');elsewhere=p.evaluate('groupRemoval.elsewhere',day);weekend=p.evaluate('groupRemoval.weekend',day)
 d=dialog(p,day)
 for cat in ['Breakfast','Lunch']:d.locator('input[data-group-choice][value="'+cat+'"]').uncheck()
 d.get_by_role('button',name='Close',exact=True).click();removed_state(p,day)
 assert p.evaluate('groupRemoval.recipes()')==recipes and p.evaluate('groupRemoval.weekend',day)==weekend
 assert p.evaluate('groupRemoval.elsewhere',day)==elsewhere
 d=dialog(p,day)
 for cat in ['Breakfast','Lunch']:assert not d.locator('input[value="'+cat+'"]').is_checked()
 d.get_by_role('button',name='Close',exact=True).click();p.reload();p.evaluate('promotionTest.my()');removed_state(p,day)
 assert p.evaluate('groupRemoval.recipes()')==recipes and p.evaluate('groupRemoval.elsewhere',day)==elsewhere
 # Reassignment uses the normal queue, without reviving the removed one-time/empty state.
 d=dialog(p,day)
 for cat in ['Breakfast','Lunch']:d.locator('input[value="'+cat+'"]').check()
 d.get_by_role('button',name='Close',exact=True).click();assert p.evaluate('groupRemoval.assigned',day)==['Weekend','Breakfast','Lunch']
 rows=p.evaluate('groupRemoval.rows',day)
 assert {r[0] for r in rows}=={'Weekend','Breakfast','Lunch'} and not any(r[2] for r in rows)
 if mode=='occupied_empty' and day=='Saturday':
  current=next(r[1] for r in rows if r[0]=='Breakfast');chosen=4 if current=='3' else 3
  p.evaluate("promotionTest.chooser('Saturday','Breakfast')");picker=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True)
  picker.get_by_role('button',name='Search recipes',exact=True).click();picker.get_by_role('searchbox').fill('Breakfast meal '+str(chosen-2));picker.locator('[data-meal-id="'+str(chosen)+'"]').click();picker.get_by_role('button',name='Save',exact=True).click()
  keep=p.get_by_role('button',name='No — Keep both meals',exact=True)
  if keep.count():keep.click()
  assert next(r[1] for r in p.evaluate('groupRemoval.rows',day) if r[0]=='Breakfast')==str(chosen)
 old=p.evaluate('groupRemoval.otherRows',day);p.evaluate('groupRemoval.rotate',day);assert p.evaluate('groupRemoval.otherRows',day)==old
 assert p.evaluate('groupRemoval.visible',day)==['Weekend','Breakfast','Lunch']
 p.evaluate('promotionTest.validate()');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,day,mode,'two unchecks, saved slot cleanup, scope, reopen/reload, reassign/rotation, recipes/settings/history/other checks unchanged',flush=True);c.close()

def legacy(b,name,day):
 c,p,errors,prefix=f.setup(b,name,360);p.evaluate('([d,m])=>groupRemoval.seed(d,m)',[day,'occupied_empty']);p.evaluate('groupRemoval.legacy',day)
 assert 'Breakfast' in p.evaluate('groupRemoval.visible',day),'fixture must reproduce the old ghost meal'
 recipes=p.evaluate('groupRemoval.recipes()');elsewhere=p.evaluate('groupRemoval.elsewhere',day)
 d=dialog(p,day);assert not d.locator('input[value="Breakfast"]').is_checked();d.get_by_role('button',name='Close',exact=True).click();removed_state(p,day)
 assert p.evaluate('groupRemoval.recipes()')==recipes and p.evaluate('groupRemoval.elsewhere',day)==elsewhere
 p.reload();p.evaluate('promotionTest.my()');removed_state(p,day);assert not errors,errors
 print('PASS',name,day,'legacy already-unchecked one-time/empty slots reconciled on close without unrelated changes',flush=True);c.close()

def masks(b,name):
 for kind in ['dayOnly','hiddenSide','dayOnlyLibrary']:
  c,p,errors,prefix=f.setup(b,name,360);p.evaluate('groupRemoval.seed("Saturday","occupied_empty")');p.evaluate('groupRemoval.'+kind+'("Saturday")');d=dialog(p,'Saturday')
  for cat in ['Breakfast','Lunch']:d.locator('input[value="'+cat+'"]').uncheck()
  d.get_by_role('button',name='Close',exact=True).click();slots=p.evaluate('groupRemoval.plan().weekSchedule.slots')
  if kind=='dayOnlyLibrary':assert p.evaluate('groupRemoval.plan().occasionalMeals.Saturday')=='3' and p.evaluate('groupRemoval.weekend("Saturday")')=='1'
  else:assert ('Saturday::@day' if kind=='dayOnly' else 'Saturday::Sides') in slots
  assert 'Saturday::Breakfast' not in slots and 'Saturday::Lunch' not in slots
  assert p.evaluate('groupRemoval.assigned("Saturday")')==['Weekend']
  p.evaluate('promotionTest.validate()');assert not errors,errors
  print('PASS',name,kind,'preserved during group removal',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for day in ['Saturday','Sunday']:
     for mode in ['occupied_empty','both_meals','both_empty','adopted_meal']:run(b,name,day,mode)
     legacy(b,name,day)
    masks(b,name)
  finally:b.close()
