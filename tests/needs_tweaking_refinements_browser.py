"""Needs Tweaking paint stacking, conditional viewer status, and staged recipe editing."""
import copy
from playwright.sync_api import sync_playwright
import needs_tweaking_browser as t
from scheduled_linked_slots_browser import state,rows,compose
from section_visibility_fixture import reveal_recipe
f=t.f
f.EXTRA+='''window.tweakRefine={
 editor:()=>openViewedRecipeEditor(),dirty:()=>editorHasPendingChanges(),
 seed:()=>{const m=meals.find(m=>m.id===1);m.prep='15';m.cook='45';m.total='60';m.marinate='120';persist();renderList()},
 copy:()=>{const m=meals.find(m=>m.id===1);m.linkGroup='same-source';meals.push({...m,id:30,cat:'Sides',rotation:true,ingredients:[...m.ingredients]});persist();renderList()},
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))},
 mode:()=>recipeViewingMode()
};'''

def header_status(p):return p.locator('#recipeViewer .recipe-tweaking-status')
def mark(p,note=None):
 p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();t.save(p,note)
def editor(p):
 p.get_by_role('button',name='Edit Recipe',exact=True).tap();assert p.locator('#editor .editor').is_visible()
def mark_control(p):return p.get_by_role('checkbox',name='Needs Tweaking',exact=True)
def note_control(p):return p.get_by_role('textbox',name='What would you change? (optional)',exact=True)
def save_editor(p):
 p.wait_for_timeout(850);p.locator('#save').tap();p.wait_for_timeout(80)
 assert not p.locator('#editor .editor').count()
def cancel_editor(p):
 p.wait_for_timeout(850);p.locator('#cancel').tap();p.wait_for_timeout(80)
 assert not p.locator('#editor .editor').count()
def viewer(b,name,width,mode):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakTest.viewer(1)');p.evaluate('(m)=>tweakTest.mode(m)',mode)
 old=copy.deepcopy(state(p));before=t.meal(p,1)
 action=p.get_by_role('button',name='Mark as Needs Tweaking',exact=True)
 assert action.count()==1 and action.locator('svg').count()==0 and not header_status(p).count()
 action.tap();d=t.dialog(p);assert d.is_visible()
 assert p.evaluate('document.querySelector("#recipeViewer").inert')
 d.get_by_role('textbox').fill('Discard this note');d.get_by_role('button',name='Cancel Needs Tweaking',exact=True).tap()
 assert state(p)==old and not p.evaluate('document.querySelector("#recipeViewer").inert')
 mark(p)
 status=header_status(p);assert status.count()==1 and not status.locator('.recipe-tweaking-note').count()
 assert not p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).count()
 assert status.evaluate('(e)=>e.previousElementSibling.classList.contains("recipe-header")&&e.compareDocumentPosition(document.querySelector(".recipe-panes"))&Node.DOCUMENT_POSITION_FOLLOWING')
 assert p.locator('#recipeViewer .recipe-tweaking-heading svg').count()==1
 assert not t.meal(p,1)['rotation'] and t.meal(p,1)['notes']==before['notes'] and t.meal(p,1)['lastCooked']==before['lastCooked']
 status.get_by_role('button',name='Edit Note',exact=True).tap();assert t.dialog(p).get_by_role('button',name='Remove Needs Tweaking',exact=True).count()==1
 note='Try more seasoning.\nUse a different cooking method.'
 t.save(p,note);assert header_status(p).locator('.recipe-tweaking-note').inner_text()==note
 assert not p.locator('#recipeViewer .recipe-viewer-notes').inner_text()==note
 # A long note stays compact, before independently scrollable cooking panels.
 header_status(p).get_by_role('button',name='Edit Note',exact=True).tap();t.save(p,'Try seasoning.\n'*100)
 p.set_viewport_size({'width':640,'height':360});p.wait_for_timeout(120)
 assert p.locator('#recipeViewer .recipe-tweaking-note').bounding_box()['height']<=70
 if mode=='split':assert p.locator('#recipeViewer .recipe-panes').bounding_box()['height']>40
 p.set_viewport_size({'width':width,'height':800});p.wait_for_timeout(100)
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.promote(1)');assert t.meal(p,1)['needsTweaking'] and t.meal(p,1)['rotation']
 p.evaluate('tweakTest.viewer(1)');schedule=compose(p)
 header_status(p).get_by_role('button',name='Remove Needs Tweaking',exact=True).tap()
 assert 'needsTweaking' not in t.meal(p,1) and 'needsTweakingNote' not in t.meal(p,1)
 assert t.meal(p,1)['rotation'] and compose(p)==schedule
 assert not header_status(p).count() and p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).count()==1
 assert p.locator('#recipeViewer .recipe-needs-tweaking svg').count()==0
 t.check(c,p,errors,prefix);print('PASS',name,width,mode,'visible modal above viewer, unmarked text only, cancel/blank mark, top note/edit/remove, long-note landscape bounds, promotion and unchanged content/schedule',flush=True)

def recipe_editor(b,name,width,copies=False):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakRefine.seed()')
 if copies:
  p.evaluate('tweakRefine.copy()');p.evaluate("promotionTest.manual('Sunday','Weekend',1)");p.evaluate("promotionTest.plan('lunch')");p.evaluate("promotionTest.manual('Friday','Weekend',1)");p.evaluate("promotionTest.plan('original')")
 p.evaluate('tweakTest.viewer(1)');before=copy.deepcopy(state(p));grocery=f.sources(p)
 editor(p);assert not mark_control(p).is_checked() and not note_control(p).is_visible()
 mark_control(p).check();note_control(p).fill('My draft only');assert p.evaluate('tweakRefine.dirty()')
 assert not p.locator('#rotation').is_checked() and 'needsTweaking' not in t.meal(p,1)
 cancel_editor(p);assert state(p)['meals']==before['meals']
 # Optional blank note marks and uses the original outgoing schedule/grocery snapshot.
 editor(p);mark_control(p).check();save_editor(p)
 assert t.meal(p,1)['needsTweaking'] and t.meal(p,1)['needsTweakingNote']=='' and not t.meal(p,1)['rotation']
 assert not any(r['id']==1 for r in rows(p)) and f.pick(p,'Saturday')['id']!=1
 assert f.pick(p,'Sunday')['id']!=1 if copies else f.pick(p,'Sunday')['id']==2
 assert header_status(p).count()==1
 for old in before['meals']:
  now=t.meal(p,old['id'])
  for key in ['name','notes','ingredients','instructions','labels','linkedMealIds','lastCooked','prep','cook','total','marinate','ingredientStepLinks']:
   if key in old:assert now.get(key)==old[key],(key,old['id'],old.get(key),now.get(key))
 if copies:assert not t.meal(p,30).get('needsTweaking') and t.meal(p,30)['rotation']
 for key,value in grocery.items():
  if value['mealId'] not in [1,20]:assert f.sources(p).get(key)==value
 assert not any(v['checked'] for key,v in f.sources(p).items() if key not in grocery)
 # Promote and edit only the note: no new demotion or grocery reset.
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.promote(1)');p.evaluate('tweakTest.viewer(1)')
 schedule=compose(p);checked=f.sources(p)
 editor(p);assert mark_control(p).is_checked();note_control(p).fill('More seasoning from Edit Recipe.');assert p.evaluate('tweakRefine.dirty()');save_editor(p)
 assert t.meal(p,1)['rotation'] and compose(p)==schedule and f.sources(p)==checked
 assert header_status(p).locator('.recipe-tweaking-note').inner_text()=='More seasoning from Edit Recipe.'
 # Explicit Remove is staged. Cancel restores it; Save clears only tracking fields.
 editor(p);p.locator('#editor').get_by_role('button',name='Remove Needs Tweaking',exact=True).tap()
 assert not mark_control(p).is_checked() and t.meal(p,1)['needsTweaking'];cancel_editor(p)
 assert t.meal(p,1)['needsTweaking']
 editor(p);p.locator('#editor').get_by_role('button',name='Remove Needs Tweaking',exact=True).tap();save_editor(p)
 assert 'needsTweaking' not in t.meal(p,1) and 'needsTweakingNote' not in t.meal(p,1)
 assert t.meal(p,1)['rotation'] and compose(p)==schedule and f.sources(p)==checked
 # Checkbox unmarking has the same semantics; blank notes remain optional.
 editor(p);mark_control(p).check();save_editor(p);editor(p);mark_control(p).uncheck();save_editor(p)
 assert 'needsTweaking' not in t.meal(p,1) and 'needsTweakingNote' not in t.meal(p,1)
 t.check(c,p,errors,prefix);print('PASS',name,width,'shared copies' if copies else 'recipe editor','mark/blank note, staged cancel/remove/checkbox clear, note-only edit preserves rotation/groceries, source fields and linked copies preserved; returns to viewer',flush=True)

def undo_and_failed_save(b,name):
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakTest.viewer(1)')
 before=copy.deepcopy(state(p));schedule=compose(p);editor(p);mark_control(p).check();save_editor(p)
 p.evaluate('tweakTest.closeViewer()');p.get_by_role('button',name='Undo',exact=True).tap()
 assert not t.meal(p,1).get('needsTweaking') and t.meal(p,1)['rotation'] and compose(p)==schedule
 t.check(c,p,errors,prefix)
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakTest.viewer(1)');editor(p)
 mark_control(p).check();note_control(p).fill('Keep this draft for retry.')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 storage='testStorage' if prefix else 'localStorage'
 # Existing editor's primary-write rollback must also protect the new fields.
 p.evaluate('''()=>{const store=STORAGE,original=store.setItem.bind(store);window.restoreTweakWrite=()=>{store.setItem=original};store.setItem=(key,value)=>{if(key==='mealRotationDataV1')throw Error('Injected quota failure');original(key,value)}}'''.replace('STORAGE',storage))
 p.wait_for_timeout(850);p.locator('#save').tap()
 message=p.get_by_role('alertdialog').filter(has_text='Recipe could not be saved.')
 assert message.is_visible();message.get_by_role('button',name='OK',exact=True).tap()
 assert state(p)['meals']==before['meals'] and compose(p)==schedule and f.sources(p)==groceries
 assert mark_control(p).is_checked() and note_control(p).input_value()=='Keep this draft for retry.'
 p.evaluate('restoreTweakWrite()');cancel_editor(p)
 assert not t.meal(p,1).get('needsTweaking')
 t.check(c,p,errors,prefix);print('PASS',name,'single Undo restores marking/schedule; failed primary write preserves recipes/schedule/groceries and retryable editor draft',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for mode in ['full','split']:viewer(b,name,width,mode)
    recipe_editor(b,name,width)
   recipe_editor(b,name,360,True)
   undo_and_failed_save(b,name)
  b.close()
