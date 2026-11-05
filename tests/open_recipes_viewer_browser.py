"""Extend the existing viewer deck without changing schedules or occurrence progress."""
import copy
from playwright.sync_api import sync_playwright
import recipe_cooking_timer_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.openRecipesTest={
 seed:on=>{const plan=mealPlans.find(p=>p.id==='original');weekdayCategories.Saturday=['Weekend','Mains','Sides'];weekdayMealOverrides['Saturday::Mains']='11';weekdayMealOverrides['Saturday::Sides']='20';plan.cycleRetainedSlots={...plan.cycleRetainedSlots,'Saturday::Mains':'11','Saturday::Sides':'20'};plan.cycleSlotChoices={...plan.cycleSlotChoices,'Saturday::Mains':{mealId:'11',parentId:''},'Saturday::Sides':{mealId:'20',parentId:'',retain:true}};meals.find(m=>m.id===1).linkedMealIds=[20];meals.find(m=>m.id===20).linkedMealIds=[22];for(const m of meals){m.ingredients=Array.from({length:65},(_,i)=>(i+1)+' cups ingredient '+m.id+'-'+i);m.instructions=Array.from({length:45},(_,i)=>'Cook step '+i+' for 15 minutes. '+('Stir and taste carefully. '.repeat(4)))}recipeViewPrefs.autoOpenLinkedRecipes=on;saveRecipeViewPrefs();saveWeekdayMealOverrides();persist();renderList();slotTest.seed()},
 open:(id=1,day='Saturday',plan='original')=>{const m=meals.find(m=>m.id===id);openRecipeViewer(m,day?cookingContext(plan,day,m.cat,m):null)},
 deck:()=>({active:recipeViewer?.activeTab.key,anchor:recipeViewer?.anchorTab.key,tabs:recipeViewer?.tabs.map(t=>({id:t.mealId,key:t.key,context:t.context,preview:t.previewProgress})),cover:recipeViewer?.cover.scrollTop,panes:[...document.querySelectorAll('.recipe-pane')].map(p=>p.scrollTop)}),
 legacyOrigin:()=>{const m=meals.find(m=>m.id===1);openRecipeViewer(m,cookingContext('original','Saturday',m.cat,m,'999'))},
 context:()=>recipeViewer?.context,
 mode:mode=>{recipeViewer.activeTab.mode=mode;renderRecipeViewer()},
 originPlan:()=>loadMealPlan('lunch',false),
 weekly:()=>{allMealsActive=true;showTop=true;groceryTabActive=false;renderList()}
};'''
def dialog(p):return p.get_by_role('dialog',name='Open recipes',exact=True)
def open_picker(p):p.locator('#recipeViewer .recipe-open-recipes').tap();return dialog(p)
def deck(p):return p.evaluate('openRecipesTest.deck()')
def choose(p,id,query):
 d=open_picker(p);d.get_by_role('button',name='Choose another recipe',exact=True).tap();d.get_by_role('searchbox',name='Search all recipes',exact=True).fill(query);d.locator('[data-meal-id="'+str(id)+'"]').tap()
def run(b,name,w,mode,linked):
 c,p,errors,prefix=f.setup(b,name,w,'multiple');p.evaluate('on=>openRecipesTest.seed(on)',linked);p.evaluate('promotionTest.check()');p.evaluate('openRecipesTest.open()');p.evaluate('mode=>openRecipesTest.mode(mode)',mode)
 # A paused timer, current progress and nonzero independent scrolls must survive additions.
 p.locator('.recipe-step-timer').first.tap();p.get_by_role('button',name='Pause timer',exact=True).tap();timer=t.timer(p)
 p.locator('.recipe-viewer-ingredients .cooking-item').first.tap();p.locator('.recipe-viewer-steps .cooking-item').first.tap()
 if mode=='split':p.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop=180');p.locator('.recipe-instructions-pane').evaluate('(e)=>e.scrollTop=360')
 else:p.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=520')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);old=deck(p)
 d=open_picker(p);assert d.get_by_role('button',name='Open all Saturday dinner recipes',exact=True).is_visible();assert d.locator('[data-meal-id="1"]').is_disabled();assert 'Already open' in d.locator('[data-meal-id="1"]').inner_text()
 assert d.locator('[data-meal-id="11"]').count()==1 and d.locator('[data-meal-id="20"]').count()==1
 d.get_by_role('button',name='Open all Saturday dinner recipes',exact=True).tap();now=deck(p);ids=[x['id'] for x in now['tabs']];assert {'1','11','20'}.issubset(ids) and len(ids)==len(set(ids))
 assert ('22' in ids)==linked and now['active']==old['active'] and now['anchor']==old['anchor']
 assert now['cover']==old['cover'] and now['panes']==old['panes'],(old,now)
 assert not p.locator('.recipe-tab-anchor .recipe-tab-close').count()
 # Repeated Open All is idempotent, preserving tab order and active recipe.
 d=open_picker(p);d.get_by_role('button',name='Open all Saturday dinner recipes',exact=True).tap();assert deck(p)==now
 choose(p,5,'roast mississippi');after=deck(p);assert after['active']==old['active'] and len(after['tabs'])==len(ids)+1;preview=next(x for x in after['tabs'] if x['id']=='5');assert preview['context'] is None
 d=open_picker(p);d.get_by_role('button',name='Choose another recipe',exact=True).tap();d.get_by_role('searchbox').fill('mississippi roast');assert d.locator('[data-meal-id="5"]').is_disabled();d.get_by_role('button',name='Close open recipes',exact=True).tap()
 assert state(p)==before and compose(p)==schedule and f.sources(p)==groceries and t.timer(p)==timer
 # Switching explicitly uses the definite scheduled context; returning restores scroll/progress.
 p.locator('.recipe-tab-strip').get_by_role('tab',name='Next main',exact=True).tap();ctx=p.evaluate('openRecipesTest.context()');assert ctx['day']=='Saturday' and ctx['planId']=='original' and ctx['mealId']=='11'
 p.locator('.recipe-tab-strip').get_by_role('tab',name='Pernil',exact=True).tap();restored=deck(p);assert restored['panes']==old['panes'] and restored['cover']==old['cover']
 assert state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales']
 if w==320 and mode=='split':p.screenshot(path='/tmp/open-recipes-'+name+'-'+str(linked)+'.png')
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth') and not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,w,mode,'linked',linked,'correct day/plan, Open All/idempotence/search/preview, existing order/active/scroll/progress/scaling/timer/schedule/groceries preserved',flush=True);c.close()
def individual_and_origin(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('openRecipesTest.seed(false)');p.evaluate('openRecipesTest.open()');old=deck(p)
 d=open_picker(p);d.locator('[data-meal-id="11"]').tap();assert [x['id'] for x in deck(p)['tabs']]==['1','11'] and deck(p)['active']==old['active']
 # A different globally selected plan must not change the deck's origin.
 p.evaluate('openRecipesTest.originPlan()');d=open_picker(p);assert d.get_by_role('button',name='Open all Saturday dinner recipes',exact=True).is_visible();d.get_by_role('button',name='Close open recipes',exact=True).tap();p.evaluate('timerTest.close()')
 p.evaluate("openRecipesTest.open(4,'Friday','lunch')");d=open_picker(p);assert d.get_by_role('button',name='Open all Friday lunch recipes',exact=True).is_visible();assert d.locator('.recipe-open-choice').count()==1;d.get_by_role('button',name='Close open recipes',exact=True).tap();p.evaluate('timerTest.close()')
 # Direct collection entry never guesses a day, even for a currently scheduled recipe.
 p.evaluate('openRecipesTest.open(1,null)');d=open_picker(p);assert not d.get_by_role('button',name='Open all',exact=False).count() and not d.locator('.recipe-open-choice').count();d.get_by_role('button',name='Choose another recipe',exact=True).tap();d.get_by_role('searchbox').fill('Next main');d.locator('[data-meal-id="11"]').tap();assert all(x['context'] is None for x in deck(p)['tabs'])
 assert not errors,errors;print('PASS',name,'individual addition, Dinner/Lunch origin remains exact, unscheduled origin has no guessed day/progress',flush=True);c.close()
def landscape_and_long_list(b,name):
 c,p,errors,_=f.setup(b,name,320,'multiple');p.evaluate('openRecipesTest.seed(true)');p.evaluate('openRecipesTest.open()')
 for size in [{'width':320,'height':800},{'width':740,'height':360}]:
  p.set_viewport_size(size);d=open_picker(p);p.screenshot(path='/tmp/open-recipes-dialog-'+name+'-'+str(size['width'])+'.png');box=d.locator(':scope > div').bounding_box();assert box['height']<=size['height']*.86 and box['x']>=17
  d.get_by_role('button',name='Choose another recipe',exact=True).tap();d.get_by_role('searchbox').fill('');list=d.locator('.recipe-open-list');assert list.evaluate('(e)=>e.scrollHeight>=e.clientHeight');list.evaluate('(e)=>e.scrollTop=e.scrollHeight');assert d.get_by_role('button',name='Close open recipes',exact=True).is_visible();d.get_by_role('searchbox').fill('roast mississippi');d.locator('[data-meal-id="5"]').tap()
  # Already-open recipe remains disabled when the same search is repeated.
  d=open_picker(p);d.get_by_role('button',name='Choose another recipe',exact=True).tap();d.get_by_role('searchbox').fill('roast mississippi');assert d.locator('[data-meal-id="5"]').is_disabled();d.get_by_role('button',name='Close open recipes',exact=True).tap()
  p.get_by_role('button',name='Close Mississippi Pot Roast tab',exact=True).tap()
 assert not errors,errors;print('PASS',name,'portrait/landscape compact picker, independently scrolling collection, visible close/search, cached recipe reopening',flush=True);c.close()
def legacy_origin_and_editor(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('openRecipesTest.seed(false)');before=copy.deepcopy(state(p));p.evaluate('openRecipesTest.legacyOrigin()');assert p.evaluate('openRecipesTest.context()') is None
 p.locator('.recipe-viewer-ingredients .cooking-item').first.tap();preview=deck(p)['tabs'][0]['preview'];d=open_picker(p);d.get_by_role('button',name='Open all Saturday dinner recipes',exact=True).tap();now=deck(p);assert len([x for x in now['tabs'] if x['id']=='1'])==1 and now['tabs'][0]['preview']==preview and state(p)['sessions']==before['sessions']
 choose(p,5,'mississippi roast');p.locator('.recipe-tab-strip').get_by_role('tab',name='Mississippi Pot Roast',exact=True).tap();p.get_by_role('button',name='Edit Recipe',exact=True).tap();p.wait_for_timeout(850);p.locator('#cancel').tap();p.wait_for_timeout(80)
 assert deck(p)['tabs'][0]['preview']==preview;d=open_picker(p);assert d.get_by_role('button',name='Open all Saturday dinner recipes',exact=True).is_visible();d.get_by_role('button',name='Close open recipes',exact=True).tap()
 assert state(p)['meals']==before['meals'] and state(p)['sessions']==before['sessions'] and not errors,errors
 print('PASS',name,'verified scheduled origin survives untrusted legacy parent context and preview-tab editor round trip; no progress borrowing or duplicate tabs',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   individual_and_origin(b,name);landscape_and_long_list(b,name);legacy_origin_and_editor(b,name)
   for width in [320,360]:
    for mode in ['full','split']:
     for linked in [False,True]:run(b,name,width,mode,linked)
  b.close()
