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
 scoped:()=>{meals.find(m=>m.id===5).name='Scoped new roast';meals.find(m=>m.id===6).name='Scoped second roast';meals.find(m=>m.id===5).linkedMealIds=[21];persist()},
 long:()=>{for(let n=100;n<220;n++)meals.push({id:n,cat:'Weekend',name:'Extra mobile recipe '+n,rotation:false,ingredients:['1 cup rice'],instructions:'Cook rice.'});persist()},
 originPlan:()=>loadMealPlan('lunch',false),
 weekly:()=>{allMealsActive=true;showTop=true;groceryTabActive=false;renderList()}
};'''
def dialog(p):return p.get_by_role('dialog',name='Open Recipes',exact=True)
def open_picker(p):p.locator('#recipeViewer .recipe-open-recipes').tap();return dialog(p)
def deck(p):return p.evaluate('openRecipesTest.deck()')
def box(d,id):return d.locator('[data-meal-id="'+str(id)+'"] input[type=checkbox]')
def apply(d):d.get_by_role('button',name='Open selected recipes',exact=True).tap()
def choose(p,id,query):
 d=open_picker(p);d.get_by_role('searchbox',name='Search all recipes',exact=True).fill(query);box(d,id).check();assert d.is_visible();apply(d)
def ids(p):return [x['id'] for x in deck(p)['tabs']]
def run(b,name,w,mode,linked):
 c,p,errors,prefix=f.setup(b,name,w,'multiple');p.evaluate('on=>openRecipesTest.seed(on)',linked);p.evaluate('promotionTest.check()');p.evaluate('openRecipesTest.open()');p.evaluate('mode=>openRecipesTest.mode(mode)',mode)
 p.locator('.recipe-step-timer').first.tap();p.get_by_role('button',name='Pause timer',exact=True).tap();timer=t.timer(p)
 p.locator('.recipe-viewer-ingredients .cooking-item').first.tap();p.locator('.recipe-viewer-steps .cooking-item').first.tap()
 if mode=='split':p.locator('.recipe-ingredients-pane').evaluate('(e)=>e.scrollTop=180');p.locator('.recipe-instructions-pane').evaluate('(e)=>e.scrollTop=360')
 else:p.locator('#recipeViewer').evaluate('(e)=>e.scrollTop=520')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);old=deck(p)
 # All scheduled and existing tabs are checked. Selection is a draft until confirmation.
 d=open_picker(p);assert not d.get_by_role('button',name='Open all',exact=False).count() and not d.get_by_role('button',name='Choose another recipe',exact=True).count();assert 'Already open' not in d.inner_text() and 'Open in a tab' not in d.inner_text()
 for id in [1,11,20]:assert box(d,id).is_checked()
 assert box(d,1).is_disabled() and 'Primary recipe · stays open' in d.inner_text();box(d,11).uncheck();d.get_by_role('searchbox').fill('roast mississippi');box(d,5).check();assert deck(p)==old
 d.get_by_role('button',name='Close open recipes',exact=True).tap();assert deck(p)==old
 d=open_picker(p);apply(d);now=deck(p);assert {'1','11','20'}.issubset(ids(p)) and len(ids(p))==len(set(ids(p))) and ('22' in ids(p))==linked
 assert now['active']==old['active'] and now['anchor']==old['anchor'] and now['cover']==old['cover'] and now['panes']==old['panes'];assert not p.locator('.recipe-tab-anchor .recipe-tab-close').count()
 d=open_picker(p);apply(d);assert deck(p)==now
 choose(p,5,'roast mississippi');after=deck(p);assert after['active']==old['active'] and len(after['tabs'])==len(now['tabs'])+1;assert next(x for x in after['tabs'] if x['id']=='5')['context'] is None
 d=open_picker(p);d.get_by_role('searchbox').fill('mississippi roast');assert box(d,5).is_checked();box(d,5).uncheck();d.get_by_role('button',name='Cancel open recipes',exact=True).tap();assert deck(p)==after
 d=open_picker(p);box(d,5).uncheck();apply(d);assert '5' not in ids(p)
 assert state(p)==before and compose(p)==schedule and f.sources(p)==groceries and t.timer(p)==timer
 p.locator('.recipe-tab-strip').get_by_role('tab',name='Next main',exact=True).tap();ctx=p.evaluate('openRecipesTest.context()');assert ctx['day']=='Saturday' and ctx['planId']=='original' and ctx['mealId']=='11'
 # Explicitly removing the active tab returns to the required anchor, restoring its scroll.
 d=open_picker(p);box(d,11).uncheck();apply(d);assert '11' not in ids(p) and deck(p)['active']==old['anchor'];assert deck(p)['panes']==old['panes'] and deck(p)['cover']==old['cover']
 assert state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'] and not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,w,mode,'linked',linked,'checked scheduled defaults, draft/top-X/bottom-X Cancel, multiword collection search, confirm/idempotence/remove-active, primary protection, exact tab/scroll/progress/timer/schedule/grocery preservation',flush=True);c.close()
def individual_and_origin(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('openRecipesTest.seed(false)');p.evaluate('openRecipesTest.open()');old=deck(p)
 d=open_picker(p);box(d,20).uncheck();apply(d);assert ids(p)==['1','11'] and deck(p)['active']==old['active']
 p.evaluate('openRecipesTest.originPlan()');d=open_picker(p);assert box(d,11).is_checked() and box(d,20).is_checked();assert not d.locator('[data-meal-id="4"]').count();d.get_by_role('button',name='Close open recipes',exact=True).tap();p.evaluate('timerTest.close()')
 p.evaluate("openRecipesTest.open(4,'Friday','lunch')");d=open_picker(p);assert d.locator('.recipe-open-choice').count()==1 and box(d,4).is_checked();assert not d.get_by_role('button',name='Select all',exact=True).is_visible();d.get_by_role('button',name='Close open recipes',exact=True).tap();p.evaluate('timerTest.close()')
 p.evaluate('openRecipesTest.open(1,null)');d=open_picker(p);assert d.locator('.recipe-open-choice').count()==1;d.get_by_role('searchbox').fill('Next main');box(d,11).check();d.get_by_role('searchbox').fill('mississippi roast');box(d,5).check();d.get_by_role('searchbox').fill('');assert box(d,11).is_checked() and box(d,5).is_checked();apply(d);assert ids(p)==['1','11','5'] and all(x['context'] is None for x in deck(p)['tabs'])
 # Closed preview tabs retain their independent in-memory progress and scroll cache.
 p.locator('.recipe-tab-strip').get_by_role('tab',name='Mississippi Pot Roast',exact=True).tap();p.locator('.recipe-viewer-ingredients .cooking-item').first.tap();p.locator('.recipe-instructions-pane').evaluate('(e)=>e.scrollTop=330');cached=deck(p);choose(p,6,'new roast');assert deck(p)['active']==cached['active'] and deck(p)['panes']==cached['panes']
 d=open_picker(p);box(d,5).uncheck();apply(d);choose(p,5,'mississippi roast');p.locator('.recipe-tab-strip').get_by_role('tab',name='Mississippi Pot Roast',exact=True).tap();assert deck(p)['panes']==cached['panes'] and next(x for x in deck(p)['tabs'] if x['id']=='5')['preview']==next(x for x in cached['tabs'] if x['id']=='5')['preview']
 assert not errors,errors;print('PASS',name,'exact Dinner/Lunch origin, one-row hidden scopes, collection origin never guesses, several searches retain selections, closed preview cache restores progress/scroll',flush=True);c.close()
def scopes_links_and_layout(b,name):
 c,p,errors,_=f.setup(b,name,320,'multiple');p.evaluate('openRecipesTest.seed(true)');p.evaluate('openRecipesTest.open()')
 # Explicitly unchecked links override the automatic setting in this action.
 d=open_picker(p);box(d,20).uncheck();box(d,22).uncheck();apply(d);assert '20' not in ids(p) and '22' not in ids(p)
 # Scope buttons affect displayed search results only, leaving hidden existing choices alone.
 p.evaluate('openRecipesTest.scoped()')
 d=open_picker(p);d.get_by_role('searchbox').fill('scoped');assert d.locator('.recipe-open-choice').count()==2;d.get_by_role('button',name='Select all',exact=True).tap();assert box(d,5).is_checked() and box(d,6).is_checked();d.get_by_role('searchbox').fill('Linked replacement');assert not box(d,21).is_checked();d.get_by_role('searchbox').fill('scoped');d.get_by_role('button',name='Deselect all',exact=True).tap();assert not box(d,5).is_checked() and not box(d,6).is_checked();d.get_by_role('searchbox').fill('');assert box(d,1).is_checked() and box(d,11).is_checked();d.get_by_role('button',name='Cancel open recipes',exact=True).tap()
 # Individual selection reflects automatic links as draft checkboxes, then honors unchecking.
 d=open_picker(p);d.get_by_role('searchbox').fill('scoped new');box(d,5).check();d.get_by_role('searchbox').fill('Linked replacement');assert box(d,21).is_checked();box(d,21).uncheck();apply(d);assert '5' in ids(p) and '21' not in ids(p) and len(ids(p))==len(set(ids(p)))
 d=open_picker(p);box(d,5).uncheck();apply(d);choose(p,5,'scoped new');assert '21' in ids(p) and len(ids(p))==len(set(ids(p)))
 p.evaluate('openRecipesTest.long()')
 for size in [{'width':320,'height':800},{'width':740,'height':360}]:
  p.set_viewport_size(size);d=open_picker(p);d.get_by_role('searchbox').fill('extra mobile');assert d.locator('.recipe-open-choice').count()==120;d.get_by_role('button',name='Select all',exact=True).tap();assert d.locator('input[type=checkbox]:checked').count()==120;d.get_by_role('button',name='Deselect all',exact=True).tap();box(d,100).check();box(d,219).check();list=d.locator('.recipe-open-list');list.evaluate('(e)=>e.scrollTop=e.scrollHeight');panel=d.locator(':scope > div');rect=panel.bounding_box();assert rect['height']<=size['height']*.86 and rect['x']>=17;assert d.get_by_role('searchbox').is_visible() and d.get_by_role('button',name='Open selected recipes',exact=True).is_visible();assert d.locator('.recipe-open-choice').first.evaluate('(e)=>e.getBoundingClientRect().height')>=44
  p.screenshot(path='/tmp/open-checklist-'+name+'-'+str(size['width'])+'.png');d.get_by_role('searchbox').fill('');assert box(d,100).is_checked() and box(d,219).is_checked();d.get_by_role('button',name='Cancel open recipes',exact=True).tap();assert '100' not in ids(p)
 assert not errors,errors;print('PASS',name,'explicit linked unchecks, displayed-result scope isolation, auto-linked draft state, primary protection, 120-row list and fixed compact header/search/footer in portrait/landscape',flush=True);c.close()
def legacy_origin_and_editor(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('openRecipesTest.seed(false)');before=copy.deepcopy(state(p));p.evaluate('openRecipesTest.legacyOrigin()');assert p.evaluate('openRecipesTest.context()') is None
 p.locator('.recipe-viewer-ingredients .cooking-item').first.tap();preview=deck(p)['tabs'][0]['preview'];d=open_picker(p);apply(d);assert len([x for x in deck(p)['tabs'] if x['id']=='1'])==1 and deck(p)['tabs'][0]['preview']==preview and state(p)['sessions']==before['sessions']
 choose(p,5,'mississippi roast');p.locator('.recipe-tab-strip').get_by_role('tab',name='Mississippi Pot Roast',exact=True).tap();p.get_by_role('button',name='Edit Recipe',exact=True).tap();p.wait_for_timeout(850);p.locator('#cancel').tap();p.wait_for_timeout(80)
 assert deck(p)['tabs'][0]['preview']==preview;d=open_picker(p);assert box(d,11).is_checked();d.get_by_role('button',name='Close open recipes',exact=True).tap()
 assert state(p)['meals']==before['meals'] and state(p)['sessions']==before['sessions'] and not errors,errors
 print('PASS',name,'verified origin survives untrusted legacy parent and editor return; no progress borrowing or duplicate tabs',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   individual_and_origin(b,name);scopes_links_and_layout(b,name);legacy_origin_and_editor(b,name)
   for width in [320,360]:
    for mode in ['full','split']:
     for linked in [False,True]:run(b,name,width,mode,linked)
  b.close()
