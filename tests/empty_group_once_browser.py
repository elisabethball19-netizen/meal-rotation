"""Empty group alignment and existing one-time schedule lifecycle, isolated fixtures."""
from playwright.sync_api import sync_playwright
import weekday_group_selection_browser as g
f=g.f
f.EXTRA+='''window.emptyOnce={
 assign:()=>{setDayCategories('Saturday',['Weekend','Breakfast','Lunch']);renderList()},
 data:()=>JSON.stringify(meals),
 slots:()=>weekSchedule(mealPlans.find(p=>p.id===activePlanId)).slots,
 rows:()=>getDisplayedWeekdayMeals().filter(x=>x.day==='Saturday').map(x=>[x.cat,x.meal.name]),
 overview:()=>{const list=document.createElement('div');renderAllMealsOverview(list);return list.textContent},
 back:()=>rotateAllBack(),
 menu:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.cat==='Breakfast');openTopMealActionMenu(x.day,x.cat,x.meal)},
 enable:()=>{for(const m of meals)if(m.cat==='Breakfast')m.rotation=true;persist();renderList()}
};'''

def run(browser,filename,width):
 c,p,errors,prefix=f.setup(browser,filename,width);p.evaluate('groupPickerTest.seed();emptyOnce.assign()')
 original=p.evaluate('emptyOnce.data()');checks=p.evaluate('groupPickerTest.selected()')
 blank=p.locator('.empty-weekday-meal[data-category=Breakfast]')
 assert blank.locator('.mealname').inner_text()=='Move a meal into rotation to display it here.'
 tag=blank.locator('.top-meal-inline-category');assert tag.text_content()=='Breakfast'
 assert tag.bounding_box()['x']>blank.locator('.mealname').bounding_box()['x']
 weekend=p.locator('.top-recipe-wrap[data-schedule-day=Saturday] .top-meal-inline-category').bounding_box()
 box=tag.bounding_box();assert abs(box['x']+box['width']-weekend['x']-weekend['width'])<=3
 blank.locator('.mealname').tap();dialog=p.get_by_role('dialog',name='Empty group options')
 assert dialog.get_by_role('button',name='Choose Meal',exact=True).count()==1
 dialog.get_by_role('button',name='Choose Meal',exact=True).tap()
 p.get_by_role('button',name='Add One-Time Meal',exact=True).tap()
 editor=p.get_by_role('dialog',name='Add One-Time Meal',exact=True)
 editor.get_by_role('textbox',name='One-time meal name',exact=True).fill('Pancakes and Bacon')
 editor.get_by_role('button',name='Save one-time meal',exact=True).tap()
 assert ['Breakfast','Pancakes and Bacon'] in p.evaluate('emptyOnce.rows()')
 assert 'Pancakes and Bacon' in p.evaluate('emptyOnce.overview()')
 assert p.evaluate('emptyOnce.data()')==original
 p.reload();p.evaluate('promotionTest.my()');assert ['Breakfast','Pancakes and Bacon'] in p.evaluate('emptyOnce.rows()')
 p.evaluate('promotionTest.validate()')
 p.evaluate('emptyOnce.menu()');p.get_by_role('button',name='Edit',exact=True).tap()
 editor=p.get_by_role('dialog',name='Edit one-time meal',exact=True);editor.get_by_role('textbox',name='One-time meal name',exact=True).fill('Sandwiches');editor.get_by_role('button',name='Save one-time meal',exact=True).tap()
 assert ['Breakfast','Sandwiches'] in p.evaluate('emptyOnce.rows()')
 p.evaluate('emptyOnce.menu()');assert p.get_by_role('button',name='Select',exact=True).count()==1
 assert not p.get_by_role('button',name='Resume planned meal',exact=True).count()
 p.get_by_role('button',name='Leave Saturday breakfast empty',exact=True).tap();assert p.evaluate("emptyOnce.slots()['Saturday::Breakfast'].kind")=='empty'
 p.locator('.empty-weekday-meal[data-category=Breakfast] .mealname').tap();p.get_by_role('button',name='Choose Meal',exact=True).tap();p.get_by_role('button',name='Add One-Time Meal',exact=True).tap()
 p.get_by_role('textbox',name='One-time meal name',exact=True).fill('Sandwiches');p.get_by_role('button',name='Save one-time meal',exact=True).tap()
 p.evaluate('emptyOnce.enable()');order=p.evaluate("promotionTest.order('Breakfast')")
 p.evaluate('promotionTest.full()');assert not p.evaluate('emptyOnce.slots()');assert p.evaluate("promotionTest.order('Breakfast')")==order
 assert ['Breakfast','Breakfast meal 1'] in p.evaluate('emptyOnce.rows()')
 p.evaluate('emptyOnce.back()');p.reload();p.evaluate('promotionTest.my()');assert ['Breakfast','Sandwiches'] in p.evaluate('emptyOnce.rows()')
 p.evaluate('promotionTest.full()');assert ['Breakfast','Breakfast meal 1'] in p.evaluate('emptyOnce.rows()')
 assert p.evaluate('groupPickerTest.selected()')==checks
 p.locator('.empty-weekday-meal[data-category=Lunch] .top-meal-inline-category').tap()
 assert p.locator('.master-category-card').count()>0
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors
 print('PASS',filename,width,'alignment, popup, one-time add/edit/remove, persistence, backup validation, queue preservation, repeated Back/forward, groceries, navigation, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,390]:run(b,name,width)
  b.close()
