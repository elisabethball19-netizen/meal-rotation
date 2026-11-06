"""Deferred queue turns and My Rotation gestures, in isolated mobile Chromium."""
import copy
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.fixTest={
 prepare:favorite=>{for(const p of mealPlans){p.weekdayCategories={};p.weekdayMealOverrides={};p.cycleRetainedSlots={};p.cycleSlotChoices={};delete p.favoriteRotationScores}const p=mealPlans[0];p.weekdayCategories={Saturday:['Weekend'],Sunday:['Weekend']};p.weekdayMealOverrides={'Saturday::Weekend':'1','Sunday::Weekend':'2'};p.cycleRetainedSlots={...p.weekdayMealOverrides};p.cycleSlotChoices=Object.fromEntries(Object.entries(p.weekdayMealOverrides).map(([k,v])=>[k,{mealId:v,parentId:''}]));for(const m of meals){delete m.favorite;if(m.cat==='Weekend'){m.rotation=true;m.lastCooked='2020-01-01T12:00:00.000Z'}}meals.find(m=>m.id===1).name='Korean Beef Bowls';meals.find(m=>m.id===2).name='Pot Roast';meals.find(m=>m.id===3).name='Pernil';if(favorite)meals.find(m=>m.id===2).favorite=true;weekdayCategories=p.weekdayCategories;weekdayMealOverrides={...p.weekdayMealOverrides};saveActiveMealPlan();persist();promotionTest.my()},
 skip:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Sunday');return skipScheduledMeal(x.day,x.cat,x.meal)},
 gestures:()=>{weekdayCategories={Saturday:['Weekend','Mains','Sides']};weekdayMealOverrides={};const p=mealPlans[0];p.weekdayCategories=weekdayCategories;p.weekdayMealOverrides={};p.cycleSlotChoices={};p.cycleRetainedSlots={};saveActiveMealPlan();persist();promotionTest.my();window.recipeOpened=0;openSavedMealRecipe=()=>{recipeOpened++}},
 opened:()=>recipeOpened
};'''
def deferred(b,name,favorite):
 c,p,errors,_=f.setup(b,name,360);p.evaluate('fixTest.prepare',favorite)
 before=copy.deepcopy(state(p));p.evaluate("promotionTest.manual('Saturday','Weekend',3)");p.evaluate('fixTest.skip()')
 adjusted=compose(p);after=state(p)
 assert before['meals']==after['meals']
 assert before['plans'][0].get('favoriteRotationScores')==after['plans'][0].get('favoriteRotationScores'),'Skip consumed a weighted turn'
 p.evaluate('promotionTest.full()');now=compose(p)
 ids=[x[3] for x in now if x[0]=='original']
 assert set(ids)=={1,2},now
 p.reload();assert compose(p)==now
 p.evaluate('slotTest.back()');assert compose(p)==adjusted
 assert not errors,errors;c.close();print('PASS',name,'deferred meals, favorite=',favorite,flush=True)
def touch(p,session,kind,x,y):
 session.send('Input.dispatchTouchEvent',{'type':kind,'touchPoints':[] if kind in ['touchEnd','touchCancel'] else [{'x':x,'y':y}]})
def gestures(b,name):
 c,p,errors,_=f.setup(b,name,360);p.evaluate('fixTest.gestures()');session=c.new_cdp_session(p)
 assert p.locator('.week-reorder-handle').count()==0
 rows=p.locator('.top-recipe-wrap');before=rows.evaluate_all('(es)=>es.map(e=>e.dataset.displayKey)');box=rows.first.locator('.mealname').bounding_box();x=box['x']+20;y=box['y']+10
 # Tap still opens meal actions.
 p.locator('.top-recipe-wrap .mealname').first.tap();assert p.get_by_role('dialog',name='Meal options for Saturday',exact=True).count();p.get_by_role('dialog',name='Meal options for Saturday',exact=True).get_by_role('button',name='Close meal options',exact=True).click();box=rows.first.locator('.mealname').bounding_box();x=box['x']+20;y=box['y']+10
 # Mouse tap retains the same action; touch cancellation opens nothing.
 p.locator('.top-recipe-wrap .mealname').first.click();assert p.get_by_role('dialog',name='Meal options for Saturday',exact=True).count();p.get_by_role('button',name='Close meal options',exact=True).click()
 touch(p,session,'touchStart',x,y);p.wait_for_timeout(620);touch(p,session,'touchCancel',x,y);assert p.evaluate('fixTest.opened()')==0
 # Long hold + tiny jitter opens existing recipe options only on release.
 touch(p,session,'touchStart',x,y);p.wait_for_timeout(620);assert p.evaluate('fixTest.opened()')==0;touch(p,session,'touchMove',x+2,y+2);touch(p,session,'touchEnd',x,y);assert p.evaluate('fixTest.opened()')==1
 p.wait_for_timeout(750)
 target=rows.nth(2).bounding_box();touch(p,session,'touchStart',x,y);p.wait_for_timeout(620);touch(p,session,'touchMove',x,target['y']+target['height']-3);touch(p,session,'touchEnd',x,y)
 assert p.evaluate('fixTest.opened()')==1
 after=rows.evaluate_all('(es)=>es.map(e=>e.dataset.displayKey)');assert after==before[1:]+before[:1],(before,after)
 p.reload();p.evaluate('promotionTest.my()');assert rows.evaluate_all('(es)=>es.map(e=>e.dataset.displayKey)')==after
 # An ordinary vertical swipe must scroll and never reorder/open a menu.
 p.evaluate("document.body.style.paddingBottom='1600px';window.scrollTo(0,0)");box=rows.first.locator('.mealname').bounding_box();y=box['y']+12
 touch(p,session,'touchStart',x,y)
 for delta in [12,30,60,100]:touch(p,session,'touchMove',x,y-delta);p.wait_for_timeout(30)
 touch(p,session,'touchEnd',x,y-100);p.wait_for_timeout(200)
 assert p.evaluate('scrollY')>0
 assert rows.evaluate_all('(es)=>es.map(e=>e.dataset.displayKey)')==after
 assert p.get_by_role('dialog').count()==0
 assert not errors,errors;c.close();print('PASS',name,'mobile tap, hold/jitter/release, drag/reload, native scroll',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for favorite in [False,True]:deferred(b,name,favorite)
   gestures(b,name)
  b.close()
