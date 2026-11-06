"""Saturday multi-group ordering, same-day duplicate decisions and independent edits."""
import json
from playwright.sync_api import sync_playwright
import combined_weekday_ui_browser as k
f=k.f
f.EXTRA+='''window.sameDay={
 seed:(once=true)=>{cats=['Weekend','Breakfast','Lunch','Bread'];meals=[{id:537,cat:'Weekend',name:'Korean Slow-Cooker Beef Bowls',rotation:true,ingredients:['1 cup rice']},{id:535,cat:'Weekend',name:'Mississippi-Style Pot Roast',rotation:true,ingredients:[]},{id:22,cat:'Weekend',name:'Spaghetti',rotation:true,ingredients:['1 cup rice']},{id:23,cat:'Weekend',name:'Tortilla Soup',rotation:true,ingredients:[]},{id:24,cat:'Breakfast',name:'Sandwiches',rotation:false,ingredients:[]},{id:25,cat:'Bread',name:'Garlic Bread',rotation:false,keepAsIdea:true,ingredients:[]}];id=538;mealPlans=[{id:'original',name:'Dinner',weekdayCategories:{Saturday:['Weekend','Breakfast','Lunch']},weekdayMealOverrides:{'Saturday::Weekend':'537','Saturday::Breakfast':'24'},cycleRetainedSlots:{'Saturday::Weekend':'537','Saturday::Breakfast':'24'},cycleSlotChoices:{'Saturday::Weekend':{mealId:'537',parentId:''},'Saturday::Breakfast':{mealId:'24',parentId:'',substitution:true,retain:true}},weekdayRecipeFilters:{},pinnedCats:[],weekSchedule:{version:1,slots:{'Saturday::Lunch':{kind:'empty'},...(once?{'Saturday::Breakfast':{kind:'once',meal:{id:'once-sandwiches',name:'Sandwiches',cat:'Breakfast',rotation:false,temporaryMeal:true,ingredients:[]}}}:{})},order:{Saturday:['["Weekend"]','["Breakfast"]','["Lunch"]']}}}];activePlanId='original';weekdayCategories={Saturday:['Weekend','Breakfast','Lunch']};weekdayMealOverrides={...mealPlans[0].weekdayMealOverrides};weekdayRecipeFilters={};previouslyActiveLinkedIds=new Set();saveActiveMealPlan();persist();promotionTest.my()},
 chooser:cat=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat===cat);openWeekdayMealChooser('Saturday',cat,x?.meal)},
 rows:()=>getDisplayedWeekdayMeals().filter(x=>x.day==='Saturday').map(x=>[x.cat,String(x.meal.id)]),
 displayed:()=>[...document.querySelectorAll('[data-week-row][data-schedule-day="Saturday"]')].map(e=>JSON.parse(e.dataset.displayKey)[0]),
 library:()=>JSON.stringify(meals.map(({id,cat,name,rotation,ingredients})=>({id,cat,name,rotation,ingredients}))),
 state:()=>JSON.stringify({mealPlans,meals,weekdayCategories,weekdayMealOverrides,lastBack:localStorage.getItem('mealRotationLastRotationBeforeV1')}),
 clear:()=>leaveWeekEmpty('Saturday','Lunch'),
 legacyOrder:()=>{editableWeekSchedule(mealPlans[0]).order.Saturday=['["Weekend"]'];saveActiveMealPlan();renderList()},
 linked:()=>{meals.find(m=>m.id===537).linkedMealIds=[25];persist();renderList()},
 plan:()=>mealPlans[0],
 forward:()=>moveDisplayedMealsToBottom(),back:()=>rotateAllBack(),
 restore:()=>{const saved=captureBackupStorage();restoreBackupStorage(saved);loadMealPlan('original')}
};'''

def choose(p,cat,id):
 p.evaluate('sameDay.chooser',cat);d=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True)
 d.get_by_role('button',name='Search recipes',exact=True).tap();d.get_by_role('searchbox').fill({537:'Korean Slow-Cooker Beef Bowls',22:'Spaghetti',23:'Tortilla Soup'}[id]);d.locator(f'[data-meal-id="{id}"]').tap();d.get_by_role('button',name='Save',exact=True).tap();return d

def picks(p):return dict(p.evaluate('sameDay.rows()'))
def order(p):assert p.evaluate('sameDay.displayed()')==['Weekend','Breakfast','Lunch']

def run(browser,name,width):
 c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('sameDay.seed()');library=p.evaluate('sameDay.library()');order(p)
 choose(p,'Lunch',23);assert picks(p)=={'Weekend':'537','Breakfast':'once-sandwiches','Lunch':'23'};order(p)
 p.evaluate('sameDay.clear()');before=p.evaluate('sameDay.state()');d=choose(p,'Lunch',537)
 confirm=p.get_by_role('dialog',name='Korean Slow-Cooker Beef Bowls is already planned',exact=True);assert confirm.is_visible()
 assert p.evaluate('sameDay.state()')==before
 confirm.get_by_role('button',name='Close',exact=True).tap();assert p.evaluate('sameDay.state()')==before
 d.get_by_role('button',name='Cancel',exact=True).tap();choose(p,'Weekend',22)
 assert picks(p)=={'Weekend':'22','Breakfast':'once-sandwiches'};order(p)
 assert p.evaluate('sameDay.library()')==library
 p.reload();p.evaluate('promotionTest.my()');assert picks(p)=={'Weekend':'22','Breakfast':'once-sandwiches'};order(p)
 for once in [True,False]:
  # Same-day keep-both is an intentional duplicate in two independent slots.
  p.evaluate('sameDay.seed',once);d=choose(p,'Lunch',537);confirm=p.get_by_role('dialog',name='Korean Slow-Cooker Beef Bowls is already planned',exact=True)
  confirm.get_by_role('button',name='No — Keep both meals',exact=True).tap();assert picks(p)['Weekend']==picks(p)['Lunch']=='537';order(p)
  p.reload();p.evaluate('promotionTest.my()');assert picks(p)['Weekend']==picks(p)['Lunch']=='537';order(p)
  choose(p,'Weekend',22);assert picks(p)['Lunch']=='537' and picks(p)['Weekend']=='22';order(p)
  assert p.evaluate('sameDay.library()')==library
  # Explicit same-day move leaves the source slot empty without rotating its queue.
  p.evaluate('sameDay.seed',once);d=choose(p,'Lunch',537);confirm=p.get_by_role('dialog',name='Korean Slow-Cooker Beef Bowls is already planned',exact=True)
  confirm.get_by_role('button',name='Yes — Move meal',exact=True).tap();assert 'Weekend' not in picks(p) and picks(p)['Lunch']=='537';order(p)
  assert p.evaluate("sameDay.plan().weekSchedule.slots['Saturday::Weekend'].kind")=='empty'
  assert p.evaluate('sameDay.library()')==library
  choose(p,'Weekend',22);assert picks(p)['Weekend']=='22' and picks(p)['Lunch']=='537';order(p)
  p.reload();p.evaluate('promotionTest.my()');assert picks(p)['Weekend']=='22' and picks(p)['Lunch']=='537';order(p)
 # Partially saved legacy order stays stable regardless of slot population and rotation.
 p.evaluate('sameDay.seed();sameDay.legacyOrder()');order(p);choose(p,'Lunch',23);order(p);p.evaluate('sameDay.clear()');order(p)
 p.evaluate('sameDay.forward()');order(p);p.reload();p.evaluate('promotionTest.my()');order(p);p.evaluate('sameDay.back()');order(p)
 p.evaluate('sameDay.restore()');p.reload();p.evaluate('promotionTest.my()');order(p)
 # Linked recipes stay attached to their original parent without displacing another group.
 p.evaluate('sameDay.seed();sameDay.linked()');choose(p,'Lunch',23);order(p);assert p.locator('.top-inline-linked').count()==1
 p.evaluate('sameDay.clear()');d=choose(p,'Lunch',537);confirm=p.get_by_role('dialog',name='Korean Slow-Cooker Beef Bowls is already planned',exact=True);confirm.press('Escape');d.get_by_role('button',name='Cancel',exact=True).tap()
 choose(p,'Weekend',22);assert 'Lunch' not in picks(p);order(p)
 p.evaluate('promotionTest.validate()');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'exact Saturday sequence, cancel/keep/move, no hidden writes, one-time/linked, stable order/queues, reload/rotation/back/restore, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
