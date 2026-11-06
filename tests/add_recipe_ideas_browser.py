"""Mobile Add Recipe: reveal Ideas/editor, single-flight creation and draft rollback."""
import copy
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
from section_visibility_fixture import reveal_recipe
f.EXTRA+='''window.addRecipeTest={
 ui:()=>({editing:editId,draft:newRecipeDraftId,creating:addingGroupRecipe,parents:[...masterExpandedCategories],sections:Object.fromEntries(cats.map(cat=>[cat,{rotation:masterRecipeSectionOpen(cat,true),ideas:masterRecipeSectionOpen(cat,false)}]))}),
 prepare:long=>{if(long){for(let n=0;n<12;n++){const cat='Extra group '+n;cats.push(cat);for(let j=0;j<5;j++)meals.push({id:id++,cat,name:'Recipe '+j,rotation:true,ingredients:[],url:''})}cats.push('Bottom group');for(let n=0;n<30;n++)meals.push({id:id++,cat:'Bottom group',name:'Existing idea '+n,rotation:false,ingredients:[],url:''})}meals.push({id:id++,cat:'Weekend',name:'',rotation:false,ingredients:[],url:'',notes:'Old existing empty recipe: preserve'});masterExpansionInitialized=true;masterExpandedCategories.clear();for(const cat of cats)if(cat!=='Bottom group')masterExpandedCategories.add(cat);setMasterRecipeSectionOpen('Mains',true,false);setMasterRecipeSectionOpen('Mains',false,true);setMasterRecipeSectionOpen('Weekend',true,true);setMasterRecipeSectionOpen('Weekend',false,false);showTop=false;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(true);persist();renderList()},
 open:id=>openEditor(id),storage:()=>slotBackup.capture(),
 rapid:cat=>addRecipeToGroup(cat),
 existingEmpty:()=>meals.find(m=>m.notes==='Old existing empty recipe: preserve').id
};'''

def ui(p):return p.evaluate('addRecipeTest.ui()')
def current(p):return next(m for m in state(p)['meals'] if m['id']==ui(p)['editing'])
def plus(p,cat):return p.get_by_role('button',name='Add meal to '+cat,exact=True)
def untouched(before,after,cat):
 assert set(after['parents'])==set(before['parents'])|{cat}
 for group,sections in before['sections'].items():
  if group!=cat:assert after['sections'][group]==sections,(group,sections,after['sections'][group])
 assert after['sections'][cat]=={'rotation':False,'ideas':True}

def run(b,name,width,long):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('(long)=>addRecipeTest.prepare(long)',long)
 cat='Bottom group' if long else 'Weekend'
 before=copy.deepcopy(state(p));schedule=compose(p);grocery=f.sources(p);old_ui=ui(p)
 button=plus(p,cat);button.scroll_into_view_if_needed()
 if long:assert p.evaluate('scrollY')>1000
 # Keep detached handlers to exercise reentrant/repeated taps even across redraws.
 button.evaluate('(e)=>window.savedAdd=e.onclick')
 button.tap();p.wait_for_timeout(90)
 opened=ui(p);new=current(p)
 assert len(state(p)['meals'])==len(before['meals'])+1
 assert new['cat']==cat and new['rotation'] is False and new['name']==''
 untouched(old_ui,opened,cat)
 row=p.locator('#list [data-meal-id="'+str(new['id'])+'"]')
 assert row.is_visible() and p.locator('#editor .editor').is_visible()
 assert p.locator('#editor').evaluate('(e)=>e.closest("[data-recipe-section]").dataset.recipeSection')=='ideas'
 bounds=row.bounding_box();assert 0<=bounds['y']<p.evaluate('innerHeight')-50,bounds
 assert p.locator('#name').evaluate('(e)=>document.activeElement===e')
 # Native current controls are disabled; detached handlers/direct reentry also no-op.
 assert plus(p,cat).is_disabled()
 p.evaluate('()=>{for(let n=0;n<20;n++)window.savedAdd();for(let n=0;n<20;n++)addRecipeTest.rapid("Mains")}')
 plus(p,cat).evaluate('(e)=>e.click()')
 assert len(state(p)['meals'])==len(before['meals'])+1 and ui(p)['editing']==new['id']
 assert not p.get_by_role('dialog').count()
 # Simulate the smaller viewport left by an Android keyboard.
 p.set_viewport_size({'width':width,'height':500});p.wait_for_timeout(100)
 assert p.locator('#name').is_visible()
 p.wait_for_timeout(800)
 plus(p,cat).scroll_into_view_if_needed();plus(p,cat).evaluate('(e)=>window.scrollBy(0,e.closest(".master-category-card").getBoundingClientRect().top-100)');p.wait_for_timeout(50)
 hit=plus(p,cat).bounding_box()
 target=plus(p,cat).evaluate('(e)=>{const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {same:e===hit||e.contains(hit),tag:hit?.outerHTML.slice(0,250),x:r.x,y:r.y,pointer:getComputedStyle(e).pointerEvents}}')
 assert target['same'],target
 p.touchscreen.tap(hit['x']+hit['width']/2,hit['y']+hit['height']/2)
 assert ui(p)['editing']==new['id'] and len(state(p)['meals'])==len(before['meals'])+1

 p.locator('#cancel').tap();p.wait_for_timeout(100)
 assert ui(p)['editing'] is None and ui(p)['draft'] is None
 assert state(p)['meals']==before['meals'],[(a,b) for a,b in zip(before['meals'],state(p)['meals']) if a!=b]
 assert compose(p)==schedule,('schedule',schedule,compose(p))
 assert f.sources(p)==grocery,('groceries',grocery,f.sources(p))
 untouched(old_ui,ui(p),cat)
 assert plus(p,cat).is_enabled()
 assert not p.get_by_role('dialog').count()
 # Save creates exactly one named Idea, and another creation can start afterwards.
 p.set_viewport_size({'width':width,'height':800});plus(p,cat).tap();p.locator('#name').fill('A new mobile recipe');assert p.locator('#rotation').is_checked();p.locator('#rotation').uncheck()
 p.wait_for_timeout(850);p.locator('#save').tap();p.wait_for_timeout(100)
 saved=[m for m in state(p)['meals'] if m['name']=='A new mobile recipe'];assert len(saved)==1 and saved[0]['cat']==cat and not saved[0]['rotation']
 assert ui(p)['draft'] is None and ui(p)['editing'] is None
 assert compose(p)==schedule and f.sources(p)==grocery
 p.reload();p.evaluate('promotionTest.groups()')
 assert ui(p)['sections'][cat]=={'rotation':False,'ideas':True}
 # Cancel a named unsaved draft: existing cancel semantics discard its edits, no blank left.
 plus(p,cat).tap();p.locator('#name').fill('Discard this unsaved recipe');p.wait_for_timeout(850);p.locator('#cancel').tap()
 assert not any(m['name']=='Discard this unsaved recipe' for m in state(p)['meals'])
 assert len(state(p)['meals'])==len(before['meals'])+1
 # Existing empty recipes must not be mistaken for newly created drafts.
 empty=p.evaluate('addRecipeTest.existingEmpty()');reveal_recipe(p,empty);p.evaluate('(id)=>addRecipeTest.open(id)',empty);p.wait_for_timeout(850);p.locator('#cancel').tap()
 assert any(m['id']==empty for m in state(p)['meals'])
 # Untouched new draft closes with an outside tap, no extra confirmation or empty entry.
 plus(p,cat).tap();count=len(state(p)['meals']);p.wait_for_timeout(850);p.touchscreen.tap(1,150);p.wait_for_timeout(100)
 assert ui(p)['editing'] is None and len(state(p)['meals'])==count-1 and not p.get_by_role('dialog').count()
 assert state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'] and state(p)['prefs']==before['prefs']
 assert compose(p)==schedule and f.sources(p)==grocery
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors
 c.close();print('PASS',name,width,'bottom group' if long else 'normal group','Ideas/editor/scroll/focus, reentry guard, keyboard resize, cancel/outside discard, save/reload, existing empty recipe and unrelated state preservation',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for long in [False,True]:run(b,name,width,long)
  b.close()

