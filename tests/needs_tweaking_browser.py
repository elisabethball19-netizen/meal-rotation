"""Needs Adjusting status-only marking, read popups, shared removal confirmation and persistence."""
import copy,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,rows,compose
from section_visibility_fixture import reveal_recipe
f.EXTRA+='''window.tweakTest={
 viewer:(id,day='Saturday')=>{const meal=meals.find(m=>m.id===id),entry=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.meal.id===id);openRecipeViewer(meal,entry?cookingContext(activePlanId,entry.day,entry.cat,meal,entry.linkedTo):null)},
 closeViewer:()=>{finishRecipeViewerClose();window.history.replaceState({},'')},
 context:()=>recipeViewer?.context,
 instructions:()=>recipeViewer?.cover.querySelector('.recipe-instructions-pane').innerText,
 flag:id=>{const m=meals.find(x=>x.id===id);m.needsTweaking=true;m.needsTweakingNote='Seeded tweak';persist();renderList()},
 direct:(id)=>openNeedsTweaking(meals.find(m=>m.id===id)),
 setup:()=>{const m=meals.find(m=>m.id===1);m.notes='Keep my original recipe notes.';m.lastCooked='2026-10-27T12:00:00.000Z';m.labels=['Favorite'];m.linkedMealIds=[20];persist();renderList()},
 attachProgress:()=>{const m=meals.find(m=>m.id===20),item=cookingItemTokens(m),c=cookingContext(activePlanId,'Saturday','Sides',m);m.ingredientStepLinks=[{step:item.steps[0].token,ingredients:[item.ingredients[0].token]}];persist()},
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true},
 corruptGroceries:()=>{groceryCheckStorageInvalid=true},
 mode:mode=>{recipeViewPrefs.mode=mode;saveRecipeViewPrefs();renderRecipeViewer()}
};'''

def meal(p,id):return next(m for m in state(p)['meals'] if m['id']==id)
def check(c,p,errors,prefix):
 assert not errors,errors
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()
def dialog(p):
 d=p.locator('#needsTweakingDialog')
 if d.count() and p.locator('#recipeViewer').count():
  assert p.evaluate('Number(getComputedStyle(document.querySelector("#needsTweakingDialog")).zIndex)>Number(getComputedStyle(document.querySelector("#recipeViewer")).zIndex)'), 'Dialog must be painted above the recipe viewer'
 return d
def save(p,note=None):
 d=dialog(p)
 if not d.get_by_role('button',name='Save Needs Adjusting',exact=True).count():d.get_by_role('button',name='Edit note',exact=True).tap()
 if note is not None:d.get_by_role('textbox',name='What would you change? (optional)',exact=True).fill(note)
 d.get_by_role('button',name='Save Needs Adjusting',exact=True).tap()
 assert not d.count()
def icon(p,id,where='#list'):
 return p.locator(where+' [data-meal-id="'+str(id)+'"] .needs-tweaking-icon').first

def removal(p,confirm):
 d=p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True)
 d.wait_for(state='visible')
 assert d.get_by_text('This will remove the warning and its note. The recipe and its place in your rotation will not change.',exact=True).count()==1
 actions=d.locator('.meal-unified-actions');assert actions.get_by_role('button').count()==2
 for label in ['Confirm removal','Cancel removal']:
  button=actions.get_by_role('button',name=label,exact=True)
  assert button.inner_text()=='' and button.locator('svg').count()==1
  assert button.get_attribute('title')==label
  box=button.bounding_box();assert box['width']>=44 and box['height']>=44
 assert actions.get_by_role('button').nth(0).bounding_box()['x']<actions.get_by_role('button').nth(1).bounding_box()['x']
 actions.get_by_role('button',name='Confirm removal' if confirm else 'Cancel removal',exact=True).tap()
 d.wait_for(state='hidden');p.wait_for_timeout(50)

def unchanged(p,before,schedule,groceries,skip=1):
 after=state(p)
 assert compose(p)==schedule
 assert f.sources(p)==groceries
 assert after['sessions']==before['sessions'] and after['scales']==before['scales'] and after['prefs']==before['prefs']
 for old in before['meals']:
  new=meal(p,old['id']);omit={'needsTweaking','needsTweakingNote'} if old['id']==skip else set()
  assert {k:v for k,v in old.items() if k not in omit}=={k:v for k,v in new.items() if k not in omit},old['id']
 assert [m['id'] for m in before['meals']]==[m['id'] for m in after['meals']]

def scheduled(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('tweakTest.setup()');p.evaluate('tweakTest.viewer(1)')
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);storage=p.evaluate('tweakTest.backup()')
 action=p.get_by_role('button',name='Needs Adjusting',exact=True)
 assert action.count()==1 and action.locator('svg').count()==0
 action.tap();dialog(p).get_by_role('textbox').fill('Discard draft');dialog(p).get_by_role('button',name='Cancel Needs Adjusting',exact=True).tap()
 assert state(p)==before
 action.tap();save(p)
 assert meal(p,1)['needsTweaking'] and meal(p,1)['needsTweakingNote']=='' and meal(p,1)['rotation']
 unchanged(p,before,schedule,groceries)
 after_storage=p.evaluate('tweakTest.backup()');assert {k:v for k,v in after_storage.items() if k!='mealRotationDataV1'}=={k:v for k,v in storage.items() if k!='mealRotationDataV1'}
 status=p.locator('#recipeViewer .recipe-tweaking-status')
 assert status.count()==1 and status.locator('.recipe-tweaking-heading svg').count()==1
 assert status.locator('.recipe-tweaking-header > .recipe-tweaking-trash').count()==1
 assert not status.locator('.recipe-tweaking-note').count() and not action.count()
 assert status.get_by_role('button',name='Remove Needs Adjusting',exact=True).inner_text()==''
 # Viewer editor edits the note without changing occurrences, progress, scaling or dates.
 status.get_by_role('button',name='Edit note',exact=True).tap();save(p,'Try more seasoning.\nUse a different cooking method.')
 assert status.locator('.recipe-tweaking-note').inner_text()==meal(p,1)['needsTweakingNote']
 unchanged(p,before,schedule,groceries)
 status.get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();removal(p,False)
 assert meal(p,1)['needsTweaking'];unchanged(p,before,schedule,groceries)
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.groups()');reveal_recipe(p,1)
 assert icon(p,1).count()==1 and 'Try more seasoning' not in p.locator('#list [data-meal-id="1"]').inner_text()
 icon(p,1).tap();d=dialog(p)
 assert d.locator('textarea,input').count()==0
 assert d.locator('.recipe-tweaking-heading svg').count()==1 and d.get_by_text('Pernil',exact=True).count()==1
 assert d.locator('.recipe-tweaking-note').inner_text()==meal(p,1)['needsTweakingNote']
 assert d.get_by_role('button',name='Edit note',exact=True).locator('svg').count()==1
 d.get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();removal(p,False)
 assert d.is_visible() and meal(p,1)['needsTweaking']
 d.get_by_role('button',name='Edit note',exact=True).tap();save(p,'Read and edit from a card.')
 unchanged(p,before,schedule,groceries)
 # Rotation card icon and chooser icon never trigger their parent row action/selection.
 p.evaluate('promotionTest.my()');icon(p,1).tap();assert dialog(p).locator('textarea').count()==0
 assert not p.get_by_role('dialog',name='Meal options for Saturday',exact=True).count()
 dialog(p).get_by_role('button',name='Close Needs Adjusting',exact=True).tap()
 p.evaluate("promotionTest.chooser('Sunday','Weekend')");choice=p.locator('.weekday-meal-picker [data-meal-id="1"]')
 choice.locator('.needs-tweaking-icon').tap();assert dialog(p).locator('textarea').count()==0
 dialog(p).get_by_role('button',name='Close Needs Adjusting',exact=True).tap()
 assert choice.locator('.weekday-meal-choice-name').get_attribute('aria-pressed')=='false'
 p.locator('.weekday-meal-picker').get_by_role('button',name='Cancel',exact=True).tap()
 unchanged(p,before,schedule,groceries)
 saved=p.evaluate('tweakTest.backup()');p.reload();assert meal(p,1)['needsTweakingNote']=='Read and edit from a card.'
 p.evaluate('promotionTest.groups()');reveal_recipe(p,1);icon(p,1).tap();dialog(p).get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();removal(p,True)
 assert not dialog(p).count() and 'needsTweaking' not in meal(p,1) and 'needsTweakingNote' not in meal(p,1)
 assert not icon(p,1).count();unchanged(p,before,schedule,groceries)
 p.evaluate('(s)=>tweakTest.restore(s)',saved);p.reload();assert meal(p,1)['needsTweakingNote']=='Read and edit from a card.'
 p.evaluate('tweakTest.viewer(1)');p.locator('#recipeViewer .recipe-tweaking-status').get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();removal(p,True)
 assert meal(p,1)['rotation'] and 'needsTweaking' not in meal(p,1)
 assert p.get_by_role('button',name='Needs Adjusting',exact=True).count()==1
 unchanged(p,before,schedule,groceries)
 check(c,p,errors,prefix);print('PASS',name,width,'status-only mark/edit/cancel/confirmed remove; read-only card popup; viewer/cards/chooser; exact schedule/grocery/progress/scale/date/order/history preservation; reload/backup',flush=True)

def cycling(b,name):
 results=[]
 for marked in [False,True]:
  c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('tweakTest.setup()')
  if marked:p.evaluate('tweakTest.direct(1)');save(p,'Still cook this normally.')
  trace=[]
  for _ in range(4):
   p.evaluate('promotionTest.full()');trace.append(compose(p))
   if marked:assert meal(p,1)['needsTweakingNote']=='Still cook this normally.' and meal(p,1)['rotation']
  history=p.evaluate('tweakTest.backup()').get('mealRotationLastRotationBeforeV1');assert history
  current_schedule=compose(p);current_groceries=f.sources(p)
  p.evaluate('tweakTest.direct(1)');save(p,'Saved after cycling.')
  assert p.evaluate('tweakTest.backup()').get('mealRotationLastRotationBeforeV1')==history
  assert compose(p)==current_schedule and f.sources(p)==current_groceries
  if marked:
   p.evaluate('slotTest.back()');assert meal(p,1)['needsTweakingNote']=='Saved after cycling.'
   # Moving to Ideas is explicitly separate; warning survives both arrows.
   p.evaluate('promotionTest.groups()');reveal_recipe(p,1).locator('.recipe-section-move').tap()
   assert not meal(p,1)['rotation'] and meal(p,1)['needsTweaking']
   reveal_recipe(p,1).locator('.recipe-section-move').tap();assert meal(p,1)['rotation'] and meal(p,1)['needsTweaking']
  results.append(trace);check(c,p,errors,prefix)
 assert results[0]==results[1]
 print('PASS',name,'flagged/unflagged four-cycle schedules identical; status survives cycling, Cycle Back and separate Ideas/Rotation moves',flush=True)

def scheduled_variants(b,name):
 for variant in ['manual','linked']:
  c,p,errors,prefix=f.setup(b,name,360,'cross-group' if variant=='manual' else 'linked-slot');p.evaluate('tweakTest.setup()')
  if variant=='manual':
   target=3;p.evaluate("tweakTest.viewer(3,'Wednesday')")
  else:
   target=20;p.evaluate('tweakTest.attachProgress()');p.evaluate('tweakTest.viewer(1)');p.locator('#recipeViewer .recipe-linked-link').filter(has_text='Current side').tap()
  before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
  p.get_by_role('button',name='Needs Adjusting',exact=True).tap();save(p,'Status only.')
  assert meal(p,target)['needsTweaking'];unchanged(p,before,schedule,groceries,skip=target)
  p.locator('#recipeViewer .recipe-tweaking-status').get_by_role('button',name='Remove Needs Adjusting',exact=True).tap();removal(p,True)
  assert 'needsTweaking' not in meal(p,target);unchanged(p,before,schedule,groceries,skip=target)
  check(c,p,errors,prefix)
 print('PASS',name,'manual out-of-group occurrence and linked-side tab keep exact schedules, ingredient associations, occurrence progress/scales and groceries through mark/remove',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:scheduled(b,name,width)
   cycling(b,name);scheduled_variants(b,name)
  b.close()
