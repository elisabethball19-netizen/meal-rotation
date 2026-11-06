"""Real/stale editor ownership, chooser return context and always-on linked tabs."""
from playwright.sync_api import sync_playwright
import unified_meal_creation_browser as k
import recipe_tabs_browser as tabs
f=k.f
f.EXTRA+=tabs.HOOK
f.EXTRA+='''window.guardTest={
 restoreDraft:()=>{const before=JSON.parse(captureState());addRecipeToGroup('Weekend');const draft=newRecipeDraftId;restoreState(before);return {draft,editId,newRecipeDraftId,editor:!!document.querySelector('#editor .editor')}},
 stale:()=>{editId=999999;newRecipeDraftId=999998},
 open:()=>openCreateScheduledRecipe({planId:activePlanId,day:'Saturday',category:'Lunch',occasional:false}),
 add:()=>addRecipeToGroup('Weekend'),
 tabsFixture:()=>{sameDay.seed(false);meals.find(m=>m.id===537).linkedMealIds=[22,25];for(const m of meals){m.ingredients=Array.from({length:50},(_,i)=>(i+1)+' cups ingredient '+i);m.instructions=Array.from({length:50},(_,i)=>'Step '+i+': Stir carefully for a long time. '.repeat(4))}saveActiveMealPlan();persist();localStorage.setItem('mealRotationRecipeViewPrefsV1',JSON.stringify({mode:'split',ratio:.4,landscapeRatio:.5,syncIngredients:false,autoCompleteIngredients:false,keepScreenAwake:false,autoOpenLinkedRecipes:false,timerAlarmVolume:.6}))},
 prefs:()=>recipeViewPrefs,
 storedPrefs:()=>JSON.parse(localStorage.getItem('mealRotationRecipeViewPrefsV1')),
 settings:()=>renderTabs()
};'''

def chooser(p):
 p.evaluate("sameDay.chooser('Lunch')");return p.get_by_role('dialog',name="Choose Saturday's meal",exact=True)

def run(browser,name,width):
 c,p,errors,prefix=f.setup(browser,name,width);p.evaluate('sameDay.seed()')
 result=p.evaluate('guardTest.restoreDraft()');p.evaluate('promotionTest.my()');assert result['draft'] is not None and result['newRecipeDraftId'] is None and result['editId'] is None and not result['editor']
 # The defensive guard also permits an orphaned scalar ID without altering recipes.
 before=p.evaluate('sameDay.library()');p.evaluate('guardTest.stale()');d=chooser(p)
 assert d.get_by_role('button',name='Create New Recipe',exact=True).locator('svg').count()==1
 assert not d.get_by_role('button',name='Create New Recipe',exact=True).text_content()
 assert not d.get_by_role('button',name='Favorites only',exact=True).count()
 once=d.get_by_role('button',name='Add One-Time Meal',exact=True);assert once.count()==1 and once.evaluate('(e)=>getComputedStyle(e).textAlign')=='center'
 d.get_by_role('button',name='Search recipes',exact=True).tap();d.get_by_role('searchbox').fill('Tortilla Soup');d.locator('[data-meal-id="23"]').tap()
 state=p.evaluate('sameDay.state()');d.get_by_role('button',name='Create New Recipe',exact=True).tap();editor=p.get_by_role('dialog',name='Create New Recipe',exact=True)
 editor.get_by_role('textbox',name='Meal name',exact=True).fill('Canceled dish');editor.get_by_role('button',name='Cancel',exact=True).tap()
 assert d.is_visible() and d.get_by_role('searchbox').input_value()=='Tortilla Soup';assert d.locator('[data-meal-id="23"]').get_attribute('aria-pressed')=='true'
 assert p.evaluate('sameDay.state()')==state and p.evaluate('sameDay.library()')==before
 d.get_by_role('button',name='Create New Recipe',exact=True).tap();editor=p.get_by_role('dialog',name='Create New Recipe',exact=True);editor.get_by_role('textbox',name='Meal name',exact=True).fill('New Lunch Recipe');editor.get_by_role('button',name='Save recipe and schedule',exact=True).tap()
 assert not p.get_by_role('dialog').count();assert p.evaluate('creationTest.one().meal.name')=='New Lunch Recipe'
 assert p.evaluate('sameDay.displayed()')==['Weekend','Breakfast','Lunch']
 d=chooser(p);d.get_by_role('button',name='Add One-Time Meal',exact=True).tap();editor=p.get_by_role('dialog',name='Add One-Time Meal',exact=True);editor.get_by_role('textbox',name='One-time meal name',exact=True).fill('Potluck');editor.get_by_role('button',name='Save one-time meal',exact=True).tap();assert p.evaluate('creationTest.one().meal.temporaryMeal') is True
 # Protect a real unsaved recipe editor, rather than ignoring all guards.
 p.evaluate('promotionTest.editor(537)');p.locator('#name').fill('Keep this unsaved title');p.evaluate('guardTest.open()')
 warning=p.get_by_role('alertdialog').filter(has_text='Save or cancel the open recipe first.');assert warning.is_visible();warning.get_by_role('button',name='OK',exact=True).tap();assert p.locator('#name').input_value()=='Keep this unsaved title';assert not p.get_by_role('dialog',name='Create New Recipe',exact=True).count();p.locator('#cancel').click()
 count=len(p.evaluate('creationTest.recipes()'));p.evaluate('guardTest.add()');assert p.locator('#editor .editor').count()==1;p.locator('#cancel').click();assert len(p.evaluate('creationTest.recipes()'))==count
 # Old stored false is accepted but cannot disable linked tabs. Other preferences survive.
 p.evaluate('guardTest.tabsFixture()');p.reload();p.evaluate('promotionTest.my()');assert p.evaluate('guardTest.prefs().autoOpenLinkedRecipes') is True
 old=p.evaluate('guardTest.storedPrefs()');assert old['autoOpenLinkedRecipes'] is False
 p.evaluate('tabTest.open(537,"Saturday")');strip=p.locator('#recipeViewer .recipe-tab-strip');assert strip.get_by_role('tab').count()==3
 def select(name):strip.get_by_role('tab',name=name,exact=True).click();p.wait_for_timeout(100)
 def set_scroll(a,b):
  p.locator('.recipe-ingredients-pane').evaluate('(e,n)=>e.scrollTop=n',a);p.locator('.recipe-instructions-pane').evaluate('(e,n)=>e.scrollTop=n',b)
 def scrolls():return p.locator('#recipeViewer .recipe-pane').evaluate_all('(es)=>es.map(e=>e.scrollTop)')
 set_scroll(80,150);main=scrolls();select('Spaghetti');set_scroll(140,230);side=scrolls();select('Korean Slow-Cooker Beef Bowls');assert scrolls()==main;select('Spaghetti');assert scrolls()==side
 p.get_by_role('button',name='Close Garlic Bread tab',exact=True).click();p.get_by_role('button',name='Close Spaghetti tab',exact=True).click();assert strip.evaluate('(e)=>e.hidden')
 assert p.evaluate('tabTest.state().meals.find(m=>m.id===537).linkedMealIds')==[22,25]
 p.get_by_role('button',name='Close recipe',exact=True).click();p.evaluate('guardTest.settings()');assert not p.locator('#autoOpenLinkedRecipeTabs').count();assert p.locator('#mealTextSizeSelect').count()==1
 current=p.evaluate('guardTest.storedPrefs()');assert {a:b for a,b in current.items() if a!='autoOpenLinkedRecipes'}=={a:b for a,b in old.items() if a!='autoOpenLinkedRecipes'}
 p.evaluate('promotionTest.validate()');assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'restore/stale/real editor guard, plus/one-time toolbar, cancel context, slot save, group creation, legacy-false linked tabs/scroll/close/settings, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
