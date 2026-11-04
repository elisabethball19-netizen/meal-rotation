"""Read-only tracking UI and staged recipe editing, with no scheduling side effects."""
import copy
from playwright.sync_api import sync_playwright
import needs_tweaking_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.tweakRefine={
 seed:()=>{const m=meals.find(m=>m.id===1);m.prep='15';m.cook='45';m.total='60';m.marinate='120';m.linkGroup='';m.ingredientImportUrl='';persist();renderList()},
 copy:()=>{const m=meals.find(m=>m.id===1);m.linkGroup='same-source';meals.push({...m,id:30,cat:'Sides',rotation:true,ingredients:[...m.ingredients]});persist();renderList()},
 dirty:()=>editorHasPendingChanges(),history:()=>localStorage.getItem(ROTATION_BACK_KEY)
};'''
def status(p):return p.locator('#recipeViewer .recipe-tweaking-status')
def mark_control(p):return p.get_by_role('checkbox',name='Needs Adjusting',exact=True)
def note_control(p):return p.get_by_role('textbox',name='What would you change? (optional)',exact=True)
def editor(p):
 p.get_by_role('button',name='Edit Recipe',exact=True).tap();assert p.locator('#editor .editor').is_visible()
def save_editor(p):
 p.wait_for_timeout(850);p.locator('#save').tap();p.wait_for_timeout(80);assert not p.locator('#editor .editor').count()
def cancel_editor(p):
 p.wait_for_timeout(850);p.locator('#cancel').tap();p.wait_for_timeout(80);assert not p.locator('#editor .editor').count()
def viewer(b,name,width,mode):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakTest.viewer(1)');p.evaluate('(m)=>tweakTest.mode(m)',mode)
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 p.get_by_role('button',name='Needs Adjusting',exact=True).tap();t.save(p,'Try more seasoning.')
 assert status(p).evaluate('(e)=>e.previousElementSibling.classList.contains("recipe-header")')
 assert not p.get_by_role('button',name='Needs Adjusting',exact=True).count()
 head=status(p).locator('.recipe-tweaking-header');trash=head.get_by_role('button',name='Remove Needs Adjusting',exact=True)
 assert trash.inner_text()=='' and trash.locator('svg').count()==1
 geometry=trash.evaluate('(e)=>({right:e.getBoundingClientRect().right,header:e.parentElement.getBoundingClientRect().right})');assert abs(geometry['right']-geometry['header'])<1
 shape=trash.locator('svg').inner_html()
 assert status(p).get_by_role('button',name='Edit note',exact=True).locator('svg').count()==1
 # Same shared heading, trash shape, and confirmation in the readonly popup.
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.groups()');t.icon(p,1).tap()
 d=t.dialog(p);assert d.locator('textarea,input').count()==0
 assert d.get_by_role('button',name='Remove Needs Adjusting',exact=True).locator('svg').inner_html()==shape
 d.get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();t.removal(p,False)
 assert d.is_visible() and d.get_by_text('Try more seasoning.',exact=True).count()==1
 d.get_by_role('button',name='Close Needs Adjusting',exact=True).tap();p.evaluate('tweakTest.viewer(1)')
 status(p).get_by_role('button',name='Edit note',exact=True).tap();t.save(p,'Try a different method.\n'*100)
 p.set_viewport_size({'width':640,'height':360});p.wait_for_timeout(100)
 assert status(p).locator('.recipe-tweaking-note').bounding_box()['height']<=70
 if mode=='split':assert p.locator('#recipeViewer .recipe-panes').bounding_box()['height']>40
 p.set_viewport_size({'width':width,'height':800});p.wait_for_timeout(100)
 t.unchanged(p,before,schedule,groceries)
 # Cancelling does not close the recipe or alter its note; confirmation paints above it.
 status(p).get_by_role('button',name='Remove Needs Adjusting',exact=True).tap()
 assert p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True).evaluate('(e)=>Number(getComputedStyle(e).zIndex)>Number(getComputedStyle(document.querySelector("#recipeViewer")).zIndex)')
 t.removal(p,False);assert t.meal(p,1)['needsTweaking']
 status(p).get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();t.removal(p,True)
 assert not status(p).count();t.unchanged(p,before,schedule,groceries)
 t.check(c,p,errors,prefix);print('PASS',name,width,mode,'compact read popup/top note, shared trash style/placement, pencil edit, long-note landscape, confirmation paint/cancel/remove; unchanged schedule/groceries/progress',flush=True)

def recipe_editor(b,name,width,copies=False):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakRefine.seed()')
 if copies:p.evaluate('tweakRefine.copy()')
 p.evaluate('tweakTest.viewer(1)');before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);history=p.evaluate('tweakRefine.history()')
 editor(p);assert not mark_control(p).is_checked();assert p.locator('#rotation').is_checked()
 mark_control(p).check();note_control(p).fill('Discard draft');assert p.locator('#rotation').is_checked()
 cancel_editor(p);assert state(p)['meals']==before['meals']
 editor(p);mark_control(p).check();assert p.locator('#rotation').is_checked();save_editor(p)
 assert t.meal(p,1)['needsTweaking'] and t.meal(p,1)['rotation'] and t.meal(p,1)['needsTweakingNote']==''
 t.unchanged(p,before,schedule,groceries);assert p.evaluate('tweakRefine.history()')==history
 if copies:assert not t.meal(p,30).get('needsTweaking') and t.meal(p,30)['rotation']
 editor(p);note_control(p).fill('Edit Recipe note.');assert p.evaluate('tweakRefine.dirty()');save_editor(p)
 assert t.meal(p,1)['needsTweakingNote']=='Edit Recipe note.';t.unchanged(p,before,schedule,groceries)
 # Trash and checkbox removals share the exact same confirmation, and remain staged.
 editor(p);p.locator('#editorNeedsTweaking').get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();t.removal(p,False)
 assert mark_control(p).is_checked() and note_control(p).input_value()=='Edit Recipe note.'
 mark_control(p).uncheck();t.removal(p,False);assert mark_control(p).is_checked()
 p.locator('#editorNeedsTweaking').get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();t.removal(p,True)
 assert not mark_control(p).is_checked() and t.meal(p,1)['needsTweaking'];cancel_editor(p)
 assert t.meal(p,1)['needsTweakingNote']=='Edit Recipe note.'
 editor(p);mark_control(p).uncheck();t.removal(p,True);save_editor(p)
 assert 'needsTweaking' not in t.meal(p,1) and 'needsTweakingNote' not in t.meal(p,1)
 t.unchanged(p,before,schedule,groceries);assert p.evaluate('tweakRefine.history()')==history
 t.check(c,p,errors,prefix);print('PASS',name,width,'copies' if copies else 'editor','mark without changing rotation, optional/edit note, shared confirm for trash/uncheck, cancel/staged save, exact data/schedule/grocery/progress/history preservation',flush=True)

def outside_editor_icon(b,name):
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakRefine.seed()');p.evaluate('tweakTest.flag(1)');p.evaluate('promotionTest.groups()')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 p.evaluate('promotionTest.editor(2)');t.icon(p,1).tap()
 d=t.dialog(p);assert d.locator('textarea').count()==0 and not p.locator('#editor .editor').count()
 d.get_by_role('button',name='Edit note',exact=True).tap();t.save(p,'Edited after closing another editor.')
 assert t.meal(p,1)['needsTweakingNote']=='Edited after closing another editor.'
 t.unchanged(p,before,schedule,groceries)
 # A replayed stale warning must not re-open marking after an editor saved removal.
 p.evaluate('promotionTest.editor(1)');mark_control(p).uncheck();t.removal(p,True)
 t.icon(p,1).tap();question=p.get_by_text('Save meal changes before closing?',exact=True).locator('..');question.get_by_role('button',name='Yes',exact=True).tap();p.wait_for_timeout(80)
 assert 'needsTweaking' not in t.meal(p,1) and not t.dialog(p).count()
 t.unchanged(p,before,schedule,groceries)
 t.check(c,p,errors,prefix);print('PASS',name,'warning taps resolve current records after editor rollback and never re-mark a cleared recipe after an outside-save replay',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for mode in ['full','split']:viewer(b,name,width,mode)
    recipe_editor(b,name,width)
   recipe_editor(b,name,360,True);outside_editor_icon(b,name)
  b.close()
