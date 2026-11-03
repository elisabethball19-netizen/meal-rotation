"""Existing meal editor returns to its source page/tab without losing edit semantics."""
from playwright.sync_api import sync_playwright
import scheduled_linked_slots_browser as fixture
from scheduled_linked_slots_browser import state,definitions,compose
fixture.HOOK+='''window.editorReturnTest={
 prepare:(page,plan,tabs)=>{if(plan!==activePlanId)loadMealPlan(plan);showMealPlanTabs=tabs;showTop=page!=='groups';allMealsActive=page==='all';groceryTabActive=page==='grocery';setMasterCategoriesView(!showTop);masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));render()},
 ui:()=>({...appViewSnapshot(),scroll:scrollY,editing:editId,tabs:showMealPlanTabs,expanded:[...masterExpandedCategories],viewer:recipeViewer?.mealId}),
 menu:()=>{const meal=meals.find(m=>m.id===1);openTopMealActionMenu(null,meal.cat,meal)},
 plan:id=>loadMealPlan(id)
};'''
def ui(p):return p.evaluate('editorReturnTest.ui()')
def confirm(p,save):
 panel=p.get_by_text('Save meal changes before closing?',exact=True).locator('..');assert panel.is_visible();panel.get_by_role('button',name='Yes' if save else 'No',exact=True).tap()
def open_from_page(p,page):
 if page=='top':p.locator('[data-weekday=Tuesday]+.top-recipe-wrap .mealname').first.tap()
 elif page=='groups':p.locator('#list .master-category-meal[data-meal-id="1"] .master-category-meal-name').first.tap()
 else:p.evaluate('editorReturnTest.menu()')
 menu=p.locator('[role=dialog]').filter(has=p.get_by_role('button',name='Edit meal',exact=True));origin=ui(p);menu.get_by_role('button',name='Edit meal',exact=True).tap();return origin

def run(browser,filename,width,page,plan,tabs,action):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.set_viewport_size({'width':width,'height':640});p.set_default_timeout(8000)
 p.evaluate('([page,plan,tabs])=>editorReturnTest.prepare(page,plan,tabs)',[page,plan,tabs]);p.evaluate('window.scrollTo(0,110)');p.wait_for_timeout(60)
 before=state(p);scheduled=compose(p);origin=open_from_page(p,page);id=ui(p)['editing'];original=next(m['name'] for m in before['meals'] if m['id']==id)
 assert ui(p)['view']=='groups' and p.locator('#editor .editor').is_visible()
 changed=action in ['save','cancel','outside-save','outside-discard'];new=original+' updated'
 if changed:p.locator('#name').fill(new)
 if action=='save':p.locator('#save').tap()
 elif action=='cancel':p.locator('#cancel').tap()
 else:
  p.touchscreen.tap(1,110)
  if action=='outside-save':confirm(p,True)
  elif action=='outside-discard':confirm(p,False)
 p.wait_for_timeout(200);after=ui(p)
 assert after['editing'] is None and after['view']==origin['view'] and after['planId']==origin['planId'] and after['tabs']==origin['tabs'],(origin,after)
 assert not p.locator('#editor .editor').count()
 assert abs(after['scroll']-min(origin['scroll'],p.evaluate('document.documentElement.scrollHeight-innerHeight')))<=2,(origin,after)
 saved=action in ['save','outside-save'];assert next(m['name'] for m in state(p)['meals'] if m['id']==id)==(new if saved else original)
 assert compose(p)==scheduled and before['sessions']==state(p)['sessions'] and before['scales']==state(p)['scales'] and before['prefs']==state(p)['prefs']
 if not saved:assert definitions(before)==definitions(state(p))
 if saved:assert new in p.locator('#list').inner_text()
 if page=='groups':assert set(after['expanded'])==set(origin['expanded'])
 if page=='top':assert p.locator('.rotation-compact-header').is_visible()
 if filename.startswith('meal-') and width==360 and page=='top' and plan=='lunch' and action=='save':p.screenshot(path='/tmp/editor-return-my-rotation.png')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors
 print('PASS',filename,width,page,plan,tabs,action,'original page/tab/scroll, updated or discarded name, unchanged schedule/progress/scaling/settings',flush=True);ctx.close()

def viewer(browser,filename,width,action):
 ctx,p,errors,_=fixture.setup(browser,filename,width,linked=True,duplicate=True,multi=True);p.set_viewport_size({'width':width,'height':640});p.evaluate('editorReturnTest.prepare("top","lunch",true)');p.evaluate('window.scrollTo(0,80)')
 p.locator('[data-weekday=Tuesday]+.top-recipe-wrap .mealname').first.tap();p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Open recipe',exact=True).tap();origin=ui(p);id=origin['viewer'];p.get_by_role('button',name='Edit Recipe',exact=True).tap()
 if action=='save':p.locator('#name').fill('Viewer edited name')
 p.locator('#save' if action=='save' else '#cancel').tap();p.wait_for_timeout(100)
 assert ui(p)['viewer']==id and ui(p)['view']=='top' and ui(p)['planId']=='lunch'
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(100);assert ui(p)['view']=='top' and ui(p)['planId']=='lunch' and not p.locator('#recipeViewer').count()
 assert not errors,errors;print('PASS',filename,width,'recipe viewer',action,'returns to viewer and correct underlying page/tab',flush=True);ctx.close()

def invalid_and_navigation(browser,filename,width):
 ctx,p,errors,_=fixture.setup(browser,filename,width,linked=True,multi=True);p.set_viewport_size({'width':width,'height':640});p.evaluate('editorReturnTest.prepare("top","original",true)');origin=open_from_page(p,'top');p.locator('#prep').fill('not a time');p.locator('#save').tap();p.get_by_role('button',name='OK',exact=True).tap()
 assert p.locator('#editor .editor').is_visible() and ui(p)['editing'] is not None
 p.locator('#cancel').tap();p.wait_for_timeout(100);assert ui(p)['view']==origin['view']
 # Closing the editor must not swallow an available outside Search action.
 origin=open_from_page(p,'top');p.locator('#name').fill('discard this draft');p.locator('#search').tap();confirm(p,False);p.wait_for_timeout(150)
 assert ui(p)['planId']=='original' and ui(p)['view']=='top' and ui(p)['editing'] is None
 assert p.get_by_role('dialog',name='Search meals',exact=True).is_visible()
 assert not errors,errors;print('PASS',filename,width,'invalid save retains editor/origin; outside Search still performs its intended action',flush=True);ctx.close()

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for page in ['top','groups']:
     for plan in ['original','lunch']:
      for action in ['save','cancel','outside-clean','outside-save','outside-discard']:run(b,filename,width,page,plan,True,action)
    for page in ['top','groups']:
     for action in ['save','cancel']:run(b,filename,width,page,'lunch',False,action)
    for page in ['all','grocery']:run(b,filename,width,page,'lunch',False,'cancel')
    for action in ['save','cancel']:viewer(b,filename,width,action)
    invalid_and_navigation(b,filename,width)
  b.close()
