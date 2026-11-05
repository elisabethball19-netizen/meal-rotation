"""All three meal lists consume the existing stable-ID timer and shared controls."""
import copy
from playwright.sync_api import sync_playwright
import timer_alarm_adjusting_browser as a
from scheduled_linked_slots_browser import state,compose
f=a.f;t=a.t
f.EXTRA+='''window.timerListTest={
 seed:()=>{const meal=meals.find(m=>m.id===3);meal.instructions=['Simmer for 15 minutes.'];meal.needsTweaking=true;meal.needsTweakingNote='Keep my note';meal.linkedMealIds=[20];meals.push({...meal,id:40,cat:'Sides',rotation:false,linkedMealIds:[],needsTweaking:false});persist();applyManualWeekdayMeal('Saturday','Weekend',meal);},
 page:view=>{showTop=view!=='groups';allMealsActive=view==='all';groceryTabActive=false;setMasterCategoriesView(!showTop);if(view==='groups'){masterExpansionInitialized=true;masterExpandedCategories.clear();for(const cat of cats){masterExpandedCategories.add(cat);setMasterRecipeSectionOpen(cat,true,true);setMasterRecipeSectionOpen(cat,false,true)}}render();},
 rename:name=>{meals.find(m=>m.id===3).name=name||'Lentils renamed';persist();renderList()},
 duplicate:()=>applyManualWeekdayMeal('Sunday','Weekend',meals.find(m=>m.id===3)),
 source:()=>({timer:cookingTimer,viewer:recipeViewer?.mealId}),
 cleanupAvailable:()=>typeof openRecipeImportReview==='function'&&typeof cleanupRecipeInstructions==='function'
};'''
def indicator(p,id=3):return p.locator('#list [data-recipe-timer-name="'+str(id)+'"] + .recipe-list-timer')
def popup(p):return p.get_by_role('dialog',name='Cooking timer',exact=True)
def page(p,view,status='paused'):
 p.evaluate('view=>timerListTest.page(view)',view)
 icons=indicator(p);assert icons.count()>=1 and icons.first.is_visible(),(view,icons.count())
 assert all(s==status for s in icons.evaluate_all('(els)=>els.map(e=>e.dataset.timerStatus)'))
 assert indicator(p,40).count()==0,'same title must not share another recipe ID timer'
 assert p.locator('#recipeViewer').count()==0
 return icons

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.clock.install();p.evaluate('timerListTest.seed()');p.evaluate('promotionTest.check()');p.evaluate('timerListTest.page("top")');t.mock_alerts(p,'denied')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 assert not p.locator('.recipe-list-timer').count()
 p.evaluate('timerTest.viewer(3)');t.icon(p).tap();first=t.timer(p);assert first['recipeId']=='3'
 p.get_by_role('button',name='Pause timer',exact=True).tap();p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(100)
 # The user's exact repro: paused timer in Lentils, viewer closed, visible in all three lists.
 for view in ['top','groups','all']:
  icons=page(p,view);icons.first.tap();d=popup(p);assert d.is_visible() and t.timer(p)['recipeId']=='3' and d.get_by_role('button',name='Resume timer',exact=True).is_visible()
  assert not p.locator('#recipeViewer').count() and p.get_by_role('dialog').count()==1
  if name.startswith('meal-') and width==360:p.screenshot(path='/tmp/timer-indicator-'+view+'.png')
  d.get_by_role('button',name='Hide timer controls',exact=True).tap();assert not popup(p).count() and t.timer(p)['id']==first['id']
 # Run, pause and countdown updates use the same state while no recipe is open.
 indicator(p).first.tap();popup(p).get_by_role('button',name='Resume timer',exact=True).tap();assert t.timer(p)['status']=='running'
 assert indicator(p).first.get_attribute('data-timer-status')=='running'
 p.clock.fast_forward(32000);assert '14:28' in popup(p).inner_text()
 popup(p).get_by_role('button',name='Pause timer',exact=True).tap();assert indicator(p).first.get_attribute('data-timer-status')=='paused'
 paused=t.timer(p)['remaining'];popup(p).get_by_role('button',name='Hide timer controls',exact=True).tap()
 p.reload();assert t.timer(p)['id']==first['id'] and t.timer(p)['status']=='paused' and t.timer(p)['remaining']==paused
 for view in ['top','groups','all']:page(p,view)
 # Cancellation unwraps the original names without resetting unrelated page state.
 indicator(p).first.scroll_into_view_if_needed();scroll=p.evaluate('scrollY');indicator(p).first.tap();popup(p).get_by_role('button',name='Delete timer',exact=True).tap()
 assert t.timer(p) is None and not popup(p).count() and not p.locator('.recipe-list-timer').count()
 assert abs(p.evaluate('scrollY')-min(scroll,p.evaluate('document.documentElement.scrollHeight-innerHeight')))<=2,(scroll,p.evaluate('scrollY'))
 for view in ['top','groups','all']:
  p.evaluate('view=>timerListTest.page(view)',view);assert not p.locator('.recipe-list-timer').count()
 # Finish while outside the viewer, retain icons until dismissal, including after reload.
 p.evaluate('timerTest.viewer(3)');t.icon(p).tap();p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(50)
 p.clock.fast_forward(900100);assert t.timer(p)['status']=='complete'
 for view in ['top','groups','all']:page(p,view,'complete')
 p.reload();assert t.timer(p)['status']=='complete'
 for view in ['top','groups','all']:page(p,view,'complete')
 p.wait_for_timeout(30);completion=p.get_by_role('alertdialog',name="Time's Up!",exact=True);assert completion.is_visible();completion.get_by_role('button',name='Acknowledge completed timer',exact=True).tap()
 assert t.timer(p) is None and not popup(p).count() and not p.locator('.recipe-list-timer').count()
 t.stable(p,before,schedule,groceries)
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'paused Lentils after viewer close in all 3 pages; shared popup event isolation/run/pause/cancel/finish/dismiss/reload; exact data/scroll preservation',flush=True);c.close()

def identity(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.clock.install();p.evaluate('timerListTest.seed()');p.evaluate('timerListTest.duplicate()');p.evaluate('timerTest.viewer(3)');t.icon(p).tap();p.get_by_role('button',name='Pause timer',exact=True).tap();p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(50)
 page(p,'top');assert indicator(p).count()==2
 p.evaluate('timerListTest.rename()');assert indicator(p).count()==2 and 'Lentils renamed' in indicator(p).first.get_attribute('aria-label')
 page(p,'groups');assert indicator(p).count()==1 and indicator(p,40).count()==0
 page(p,'all');assert indicator(p).count()==2
 indicator(p).first.tap();p.keyboard.press('Escape');assert not popup(p).count() and t.timer(p)['status']=='paused'
 p.set_viewport_size({'width':320,'height':640});p.evaluate('timerListTest.rename("Lentils with a very long recipe name and linked side descriptions for mobile layout")')
 for view in ['top','groups','all']:
  page(p,view);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 print('PASS',name,'stable IDs survive rename/duplicate weekdays; same-name different-ID excluded; Escape preserves timer',flush=True);c.close()

def linked(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.clock.install();p.evaluate('timerListTest.seed()');p.evaluate('promotionTest.check()');p.evaluate('timerTest.viewer(20)');t.icon(p).tap();p.get_by_role('button',name='Pause timer',exact=True).tap();p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(50)
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 for view in ['top','groups','all']:
  p.evaluate('view=>timerListTest.page(view)',view);assert indicator(p,20).first.is_visible() and indicator(p,3).count()==0
  indicator(p,20).first.tap();assert t.timer(p)['recipeId']=='20' and not p.locator('#recipeViewer').count();popup(p).get_by_role('button',name='Hide timer controls',exact=True).tap()
 indicator(p,20).first.tap();popup(p).get_by_role('button',name='Delete timer',exact=True).tap();assert not p.locator('.recipe-list-timer').count()
 t.stable(p,before,schedule,groceries);assert not errors,errors
 print('PASS',name,'linked recipe indicators and controls in all 3 views use child ID without parent actions or data changes',flush=True);c.close()

def settings(b,name,width,landscape):
 c,p,errors,_=f.setup(b,name,width,'multiple');p.clock.install();p.evaluate('timerTest.setup()');p.evaluate('timerTest.viewer()');t.mock_alerts(p)
 if landscape:p.set_viewport_size({'width':740,'height':360})
 panel=a.settings(p);assert not panel.get_by_role('button',name='Review instruction cleanup / related recipes',exact=True).count() and p.evaluate('timerListTest.cleanupAvailable()')
 assert not panel.get_by_text('Uses your device’s media volume. Preview stops after 3 seconds.',exact=True).count()
 slider=panel.get_by_role('slider',name='Timer alarm volume',exact=True);button=panel.get_by_role('button',name='Test alarm sound',exact=True)
 slider.scroll_into_view_if_needed();x=slider.bounding_box();y=button.bounding_box()
 assert y['x']>=x['x']+x['width'] and abs(y['y']+y['height']/2-x['y']-x['height']/2)<3,(x,y)
 assert button.inner_text()=='' and button.locator('svg').count()==1 and not panel.locator('.recipe-timer-volume .muted').count()
 a.volume(p,35);button.tap();assert a.sound(p)['kind']=='test' and p.evaluate('alertCalls.levels.at(-1)')==.35
 stop=panel.get_by_role('button',name='Stop test sound',exact=True);assert stop.inner_text()=='' and stop.locator('svg').count()==1
 stop.tap();assert a.sound(p) is None;button.tap();p.clock.fast_forward(3100);assert a.sound(p) is None
 a.close_settings(p);p.reload();p.evaluate('timerTest.viewer(20)');assert a.settings(p).get_by_role('slider').input_value()=='35'
 if name.startswith('meal-') and width==360:p.screenshot(path='/tmp/timer-settings-'+('landscape' if landscape else 'portrait')+'.png')
 assert not errors,errors
 print('PASS',name,width,landscape,'cleanup control only removed here; compact aligned icon/slider, preview stop/timeout and global/reloaded volume',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   identity(b,name)
   linked(b,name)
   for width in [320,360]:
    run(b,name,width)
    for landscape in [False,True]:settings(b,name,width,landscape)
  b.close()
