"""Shared meal chooser toolbar, simplified creation, empty-row layout and keyboard fit."""
from playwright.sync_api import sync_playwright
import same_day_group_assignment_browser as k
f=k.f
f.EXTRA+='''window.creationTest={
 open:(day='Saturday',cat='Lunch')=>{const x=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat===cat);openWeekdayMealChooser(day,cat,x?.meal,!getDayCategories(day).length)},
 sunday:()=>{setDayCategories('Sunday',['Weekend','Breakfast','Lunch']);renderList()},
 recipes:()=>meals.map(m=>({id:m.id,name:m.name,cat:m.cat,ingredients:m.ingredients,rotation:m.rotation})),
 rows:()=>getDisplayedWeekdayMeals().map(x=>[x.day,x.cat,String(x.meal.id),x.meal.name]),
 empty:()=>leaveWeekEmpty('Sunday','Weekend'),
 edit:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Lunch');openOneTimeMealEditor(x.day,x.cat,x.meal)},
 one:()=>getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Lunch'),
 full:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Saturday'&&x.cat==='Lunch');openEditor(x.meal.id)},
 backup:()=>promotionTest.validate()
};'''

def open_create(p,day='Saturday',cat='Lunch'):

 for previous in p.locator('.weekday-meal-picker').all():previous.get_by_role('button',name='Cancel',exact=True).click()
 p.evaluate('([day,cat])=>creationTest.open(day,cat)',[day,cat]);d=p.get_by_role('dialog',name='Choose '+day+"'s meal",exact=True)
 assert d.get_by_role('button',name='Add One-Time Meal',exact=True).count()==1
 assert not d.get_by_role('button',name='Favorites only',exact=True).count()
 plus=d.get_by_role('button',name='Create New Recipe',exact=True);assert plus.locator('svg').count()==1 and not plus.text_content()
 assert d.get_by_role('button',name='Search recipes',exact=True).count()==1
 plus.tap();d=p.get_by_role('dialog',name='Create New Recipe',exact=True)
 assert not d.get_by_role('checkbox',name='One-time meal',exact=True).is_checked()
 assert d.get_by_role('combobox',name='Recipe Group',exact=True).is_visible()
 assert d.get_by_role('textbox').count()==2 and d.get_by_role('checkbox').count()==1
 assert not d.get_by_role('textbox',name='Instructions',exact=True).count()
 return d

def run(browser,name,width):
 c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('sameDay.seed();creationTest.sunday();creationTest.empty()')
 styles=p.locator('[data-week-row] .top-meal-inline-category').evaluate_all('(es)=>es.map(e=>{const s=getComputedStyle(e);return [s.fontSize,s.fontWeight,s.color,s.textTransform,s.textAlign]})')
 assert styles and all(s==['12px','400','rgb(102, 102, 102)','uppercase','right'] for s in styles),styles
 for row in p.locator('.empty-weekday-meal').all():
  box=row.bounding_box();dash=row.locator('.mealname').bounding_box();assert abs((dash['y']+dash['height']/2)-(box['y']+box['height']/2))<2
  assert box['height']<=44
 tail=p.locator('[data-week-row][data-schedule-day=Sunday]').last;assert tail.evaluate('(e)=>getComputedStyle(e).borderBottomRightRadius')=='8px'
 original=p.evaluate('sameDay.state()');d=open_create(p);d.get_by_role('checkbox',name='One-time meal',exact=True).check();d=p.get_by_role('dialog',name='Add One-Time Meal',exact=True);assert d.is_visible()
 assert not d.get_by_role('combobox',name='Recipe Group',exact=True).is_visible();d.get_by_role('button',name='Cancel',exact=True).tap();assert p.evaluate('sameDay.state()')==original
 # Permanent recipe creation uses existing atomic scheduling and ingredient selection.
 before=p.evaluate('creationTest.rows()');recipes=p.evaluate('creationTest.recipes()');d=open_create(p)
 d.get_by_role('textbox',name='Meal name',exact=True).fill('Pancakes and Bacon');d.get_by_role('combobox',name='Recipe Group',exact=True).select_option('Breakfast');d.get_by_role('textbox',name='Ingredients',exact=True).fill('2 cups flour\n1 cup milk')
 d.get_by_role('button',name='Save recipe and schedule',exact=True).tap()
 assert not p.get_by_role('dialog').count()
 now=p.evaluate('creationTest.rows()');added=next(x for x in now if x[:2]==['Saturday','Lunch']);assert added[3]=='Pancakes and Bacon'
 assert [r for r in now if r[:2]!=['Saturday','Lunch']]==before
 assert len(p.evaluate('creationTest.recipes()'))==len(recipes)+1
 created=next(x for x in p.evaluate('creationTest.recipes()') if str(x['id'])==added[2]);assert created['cat']=='Breakfast' and created['ingredients']==['2 cups flour','1 cup milk']
 assert len([s for s in p.evaluate('promotionTest.sources()') if str(s['mealId'])==added[2]])==2
 p.evaluate('creationTest.backup()');p.reload();p.evaluate('promotionTest.my()');assert next(x for x in p.evaluate('creationTest.rows()') if x[:2]==['Saturday','Lunch'])[3]=='Pancakes and Bacon'
 # Full editor remains available later; the initial editor did not remove its details.
 p.evaluate('creationTest.full()');assert p.locator('#recipeInstructions').count()==1;p.locator('#cancel').click();p.evaluate('promotionTest.my()')
 # Every source context opens the same toolbar/editor, with unchecked default.
 for day,cat in [('Saturday','Weekend'),('Sunday','Weekend'),('Monday',None)]:
  d=open_create(p,day,cat);d.get_by_role('button',name='Cancel',exact=True).tap()
 # Temporary creation, groceries, keyboard geometry and page scroll preservation.
 p.evaluate('sameDay.seed();combinedTest.viewport()');before=p.evaluate('creationTest.recipes()');p.locator('.weekday-heading[data-weekday=Saturday]').evaluate('(e)=>e.scrollIntoView({block:"start"})');d=open_create(p);p.wait_for_timeout(70);page_y=p.evaluate('scrollY')
 d.get_by_role('checkbox',name='One-time meal',exact=True).check();d=p.get_by_role('dialog',name='Add One-Time Meal',exact=True)
 d.get_by_role('textbox',name='Meal name',exact=True).fill('Fish sticks');d.get_by_role('textbox',name='Ingredients',exact=True).fill('2 bags fish sticks')
 p.evaluate('combinedTest.resize(300,20)');p.wait_for_timeout(70);box=d.locator(':scope > div').bounding_box();assert box['y']>=20 and box['y']+box['height']<=320
 save=d.get_by_role('button',name='Save one-time meal',exact=True);save.scroll_into_view_if_needed();b=save.bounding_box();assert b['y']>=20 and b['y']+b['height']<=320
 assert p.evaluate('scrollY')==page_y,{'before':page_y,'after':p.evaluate('scrollY')}
 p.evaluate('combinedTest.resize(800,0)');save.tap();assert p.evaluate('creationTest.recipes()')==before
 assert p.evaluate('creationTest.one().meal.temporaryMeal') is True
 assert any(s['line']=='2 bags fish sticks' for s in p.evaluate('promotionTest.sources()'))
 p.reload();p.evaluate('promotionTest.my()');assert p.evaluate('creationTest.one().meal.name')=='Fish sticks'
 p.evaluate('combinedTest.viewport();creationTest.edit();combinedTest.resize(280,0)');d=p.get_by_role('dialog',name='Edit one-time meal',exact=True);d.get_by_role('textbox',name='One-time meal name',exact=True).fill('Sandwiches');d.get_by_role('button',name='Save one-time meal',exact=True).tap();assert p.evaluate('creationTest.one().meal.name')=='Sandwiches'
 p.evaluate('sameDay.forward()');assert not any(r[1]=='Lunch' and r[3]=='Sandwiches' for r in p.evaluate('creationTest.rows()'));p.evaluate('sameDay.back()');assert p.evaluate('creationTest.one().meal.name')=='Sandwiches'
 p.evaluate('creationTest.backup()');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'consistent labels/centered dash, all chooser contexts, default/reset/cancel, permanent/temporary creation, groceries, full editor, reload/back, keyboard/page scroll, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
