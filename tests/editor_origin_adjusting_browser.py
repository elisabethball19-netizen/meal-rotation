"""Explicit editor origin, independent sections, search resume and legacy status compatibility."""
from playwright.sync_api import sync_playwright
import editor_return_browser as e
from scheduled_linked_slots_browser import state,compose
e.fixture.HOOK+='''
window.originTest={
 sections:()=>Object.fromEntries(masterSectionExpansion),
 seed:()=>{setMasterRecipeSectionOpen('Rice',true,true);setMasterRecipeSectionOpen('Rice',false,false);setMasterRecipeSectionOpen('Sides',true,false);setMasterRecipeSectionOpen('Sides',false,true);render();},
 stale:()=>{showTop=true;groceryTabActive=false;allMealsActive=false},
 trace:()=>{window.returnRenders=[];const original=render;render=function(){returnRenders.push(appViewSnapshot().view);return original()};},
 search:()=>openMealSearch()
};'''
def run(b,name,width,page,via_viewer,save):
 c,p,errors,prefix=e.fixture.setup(b,name,width,linked=True,duplicate=True,multi=True)
 p.set_viewport_size({'width':width,'height':640})
 p.evaluate('page=>editorReturnTest.prepare(page,"lunch",true)',page);p.evaluate('originTest.seed()');p.evaluate('scrollTo(0,90)')
 before=state(p);schedule=compose(p);sections=p.evaluate('originTest.sections()');origin=e.ui(p)
 if via_viewer:
  p.evaluate('editorReturnTest.menu()');p.get_by_role('button',name='Open recipe',exact=True).tap()
  # Viewer retains its actual origin even if an asynchronous path changes page flags.
  if page=='groups':p.evaluate('originTest.stale()')
  p.get_by_role('button',name='Edit Recipe',exact=True).tap()
 else:e.open_from_page(p,page)
 p.wait_for_timeout(850)
 if save:p.locator('#name').fill('Saved origin test')
 p.evaluate('originTest.trace()');p.locator('#save' if save else '#cancel').tap();p.wait_for_timeout(150)
 assert e.ui(p)['view']==page and e.ui(p)['planId']=='lunch'
 assert all(x==page for x in p.evaluate('returnRenders')),p.evaluate('returnRenders')
 assert p.evaluate('originTest.sections()')==sections
 assert e.ui(p)['expanded']==origin['expanded']
 if via_viewer:
  assert p.locator('#recipeViewer').count()==1
  p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(100)
 assert e.ui(p)['view']==page
 assert abs(e.ui(p)['scroll']-min(origin['scroll'],p.evaluate('document.documentElement.scrollHeight-innerHeight')))<=2
 assert compose(p)==schedule and state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales']
 assert not errors,errors
 print('PASS',name,width,page,'viewer' if via_viewer else 'direct','save' if save else 'cancel','origin/sections/tab/scroll, no intermediate wrong-page render, unchanged schedule/progress',flush=True);c.close()
def browser_back(b,name):
 c,p,errors,_=e.fixture.setup(b,name,360,linked=True,duplicate=True,multi=True)
 p.evaluate('editorReturnTest.prepare("groups","lunch",true)');p.evaluate('originTest.seed()');sections=p.evaluate('originTest.sections()')
 p.evaluate('editorReturnTest.menu()');p.get_by_role('button',name='Open recipe',exact=True).tap();p.get_by_role('button',name='Edit Recipe',exact=True).tap();p.wait_for_timeout(850)
 p.go_back();p.wait_for_timeout(150)
 assert p.locator('#recipeViewer').is_visible() and e.ui(p)['view']=='groups' and p.evaluate('originTest.sections()')==sections
 p.get_by_role('button',name='Close recipe',exact=True).tap();p.wait_for_timeout(150)
 assert not p.locator('#recipeViewer').count() and e.ui(p)['view']=='groups'
 assert not errors,errors
 print('PASS',name,'Back closes viewer editor to original viewer/group context',flush=True);c.close()
def search(b,name):
 c,p,errors,_=e.fixture.setup(b,name,360,linked=True,duplicate=True,multi=True)
 p.evaluate('editorReturnTest.prepare("groups","lunch",true)');p.evaluate('originTest.seed()');sections=p.evaluate('originTest.sections()')
 p.evaluate('originTest.search()');d=p.get_by_role('dialog',name='Search meals',exact=True)
 d.get_by_role('searchbox',name='Search meal names',exact=True).fill('garlic')
 d.get_by_role('checkbox',name='Match word order').check()
 d.locator('[data-meal-id="1"]').tap();p.get_by_role('button',name='Edit meal',exact=True).tap();p.wait_for_timeout(850);p.locator('#cancel').tap()
 d=p.get_by_role('dialog',name='Search meals',exact=True)
 assert d.is_visible() and d.get_by_role('searchbox').input_value()=='garlic' and d.get_by_role('checkbox').is_checked()
 assert e.ui(p)['view']=='groups' and e.ui(p)['planId']=='lunch' and p.evaluate('originTest.sections()')==sections
 assert not errors,errors
 print('PASS',name,'Search dialog/query/checkbox restored after Edit Recipe',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for page in ['top','groups']:
    for via in [False,True]:
     for save in [False,True]:run(b,name,360,page,via,save)
   search(b,name)
   browser_back(b,name)
  b.close()
