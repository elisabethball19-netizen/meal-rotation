"""Needs Tweaking: viewer, section moves, independent occurrences, mobile and backups."""
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
 if note is not None:d.get_by_role('textbox',name='What would you change? (optional)',exact=True).fill(note)
 d.get_by_role('button',name='Save Needs Tweaking',exact=True).tap()
 assert not d.count()
def icon(p,id,where='#list'):
 return p.locator(where+' [data-meal-id="'+str(id)+'"] .needs-tweaking-icon').first

def scheduled(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.evaluate('tweakTest.setup()')
 before=copy.deepcopy(state(p));before_groceries=f.sources(p);original=meal(p,1);p.evaluate('tweakTest.viewer(1)')
 pane=p.locator('#recipeViewer .recipe-instructions-pane')
 assert pane.locator('.recipe-needs-tweaking').count()==1 and pane.locator('.recipe-needs-tweaking svg').count()==0
 assert pane.locator('.recipe-needs-tweaking').evaluate('(e)=>e.previousElementSibling.classList.contains("recipe-viewer-notes")')
 p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();d=dialog(p)
 assert d.is_visible() and d.get_by_role('textbox').input_value()==''
 d.get_by_role('textbox').fill('Less salt next time. Try a longer rest.')
 d.get_by_role('button',name='Cancel Needs Tweaking',exact=True).tap()
 assert state(p)==before
 # Save with the note blank: scheduled recipe demotes, linked definition remains intact.
 p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();save(p)
 current=meal(p,1);assert current['needsTweaking'] is True and current['needsTweakingNote']=='' and not current['rotation']
 assert {k:v for k,v in original.items() if k not in ['rotation','rotationPromotionPriority']}=={k:v for k,v in current.items() if k not in ['rotation','rotationPromotionPriority','needsTweaking','needsTweakingNote']}
 assert all(r['id']!=1 for r in rows(p))
 assert f.pick(p,'Saturday')['id']!=1 and f.pick(p,'Sunday')['id']==2
 # No stale context can recreate a removed scheduled session while viewer stays open.
 assert p.locator('#recipeViewer').is_visible() and p.evaluate('tweakTest.context()') is None
 assert p.locator('#recipeViewer .recipe-needs-tweaking').count()==0 and p.locator('#recipeViewer .recipe-tweaking-status').count()==1
 unchanged={k:v for k,v in before_groceries.items() if v['mealId'] not in [1,20]}
 for key,value in unchanged.items():
  assert f.sources(p).get(key)==value,(key,value,f.sources(p).get(key))
 assert not any(s['checked'] for key,s in f.sources(p).items() if key not in before_groceries)
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.groups()');r=reveal_recipe(p,1)
 assert r.locator('.needs-tweaking-icon').count()==1 and 'Less salt' not in r.inner_text()
 icon(p,1).tap();assert dialog(p).get_by_role('textbox').get_attribute('placeholder')=='Needs Tweaking'
 save(p,'Less salt next time.')
 assert meal(p,1)['needsTweakingNote']=='Less salt next time.' and not meal(p,1)['rotation']
 # Promotion leaves the status intact and uses established scheduling behavior.
 r=reveal_recipe(p,1);r.locator('.recipe-section-move').tap();assert meal(p,1)['rotation'] and meal(p,1)['needsTweaking']
 assert len([r for r in rows(p) if r['id']==1])==1
 # Icon on My Rotation never opens meal options; editing does not demote again.
 p.evaluate('promotionTest.my()');icon(p,1).tap()
 assert dialog(p).is_visible() and not p.get_by_role('dialog',name='Meal options for Saturday').count()
 save(p,'Add lemon.')
 assert meal(p,1)['rotation'] and meal(p,1)['needsTweakingNote']=='Add lemon.'
 # Chooser icon is a sibling control; its tap must not select a different meal.
 p.evaluate("promotionTest.chooser('Sunday','Weekend')")
 chooser=p.locator('.weekday-meal-picker');choice=chooser.locator('[data-meal-id="1"]')
 assert choice.locator('.needs-tweaking-icon').count()==1
 before_schedule=compose(p);chooser.get_by_role('button',name='Search recipes',exact=True).tap();chooser.get_by_role('searchbox',name='Search recipes',exact=True).fill('Pernil');choice.locator('.needs-tweaking-icon').tap()
 assert dialog(p).get_by_role('textbox').input_value()=='Add lemon.'
 save(p,'Try more lemon.')
 choice=chooser.locator('[data-meal-id="1"]')
 assert choice.locator('.weekday-meal-choice-name').get_attribute('aria-pressed')=='false'
 assert compose(p)==before_schedule
 # Selecting the flagged recipe still previews and Cancel discards that selection.
 choice.get_by_role('button',name='Pernil',exact=True).tap()
 assert chooser.locator('[data-meal-id="1"] .weekday-meal-choice-name').get_attribute('aria-pressed')=='true'
 chooser.get_by_role('button',name='Cancel',exact=True).tap();assert compose(p)==before_schedule
 # Full backups preserve fields; restoring also works without new schema requirements.
 stored=p.evaluate('tweakTest.backup()');p.reload();assert meal(p,1)['needsTweakingNote']=='Try more lemon.'
 p.evaluate('promotionTest.groups()');reveal_recipe(p,1);icon(p,1).tap()
 original_membership=meal(p,1)['rotation'];dialog(p).get_by_role('button',name='Remove Needs Tweaking',exact=True).tap()
 assert 'needsTweaking' not in meal(p,1) and 'needsTweakingNote' not in meal(p,1)
 assert meal(p,1)['rotation']==original_membership
 assert not icon(p,1).count()
 p.evaluate('(s)=>tweakTest.restore(s)',stored);p.reload();assert meal(p,1)['needsTweakingNote']=='Try more lemon.'
 p.evaluate('promotionTest.groups()');reveal_recipe(p,1)
 assert icon(p,1).count()==1
 check(c,p,errors,prefix);print('PASS',name,width,'scheduled demotion/replacement, blank note, edit/cancel, three views, click isolation, promotion, persistence/backup/restore/clear',flush=True)

def edge_cases(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'linked-slot');p.evaluate('tweakTest.setup()');p.evaluate('tweakTest.attachProgress()')
 original=meal(p,20);old=copy.deepcopy(state(p));p.evaluate('tweakTest.viewer(1)');p.locator('#recipeViewer .recipe-linked-link').filter(has_text='Current side').tap()
 p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();save(p,'Improve this linked side.')
 assert meal(p,20)['linkedMealIds']==original['linkedMealIds']
 assert meal(p,20)['ingredientStepLinks']==original['ingredientStepLinks']
 assert meal(p,1)['linkedMealIds']==[20]
 assert not meal(p,20)['rotation'] and not any(r['id']==20 for r in rows(p))
 # Unrelated recipe occurrence progress/scales survive as dictated by existing demotion.
 now=state(p)
 for key,session in old['sessions']['occurrences'].items():
  if session['context']['mealId'] not in ['20'] and not(session['context']['day']=='Saturday' and session['context']['cat']=='Sides'):
   assert now['sessions']['occurrences'].get(key)==session
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.groups()');reveal_recipe(p,20);icon(p,20).tap()
 dialog(p).get_by_role('button',name='Remove Needs Tweaking',exact=True).tap();assert not meal(p,20)['rotation']
 # New status on an unscheduled Ideas recipe is supported, with Full View too.
 p.evaluate('tweakTest.viewer(6)');p.evaluate('tweakTest.mode("full")')
 p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();save(p,'Improve the sear.')
 assert meal(p,6)['needsTweaking'] and not meal(p,6)['rotation']
 p.evaluate('tweakTest.closeViewer()');p.reload()
 assert meal(p,6)['needsTweakingNote']=='Improve the sear.'
 check(c,p,errors,prefix);print('PASS',name,width,'linked side removal, associations/links/progress, Ideas, Full View and clear membership',flush=True)

def repeated_and_cycle_back(b,name):
 c,p,errors,prefix=f.setup(b,name,360,'multiple');p.evaluate('tweakTest.setup()')
 assert not p.locator('.needs-tweaking-icon').count()
 p.evaluate("promotionTest.manual('Sunday','Weekend',1)")
 p.evaluate("promotionTest.plan('lunch')");p.evaluate("promotionTest.manual('Friday','Weekend',1)");p.evaluate("promotionTest.plan('original')")
 assert len([r for r in rows(p) if r['id']==1])==3
 p.evaluate('tweakTest.viewer(1)');p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();save(p,'Keep this note across weeks.')
 assert not any(r['id']==1 for r in rows(p))
 p.evaluate('tweakTest.closeViewer()');p.evaluate('promotionTest.promote(1)')
 assert meal(p,1)['needsTweakingNote']=='Keep this note across weeks.'
 # Cycling preserves status; changing it afterwards must survive old rotation snapshots.
 p.evaluate('promotionTest.full()');assert meal(p,1)['needsTweaking']
 p.evaluate('tweakTest.direct(1)');save(p,'Updated after cycling.')
 p.evaluate('slotTest.back()');assert meal(p,1)['needsTweakingNote']=='Updated after cycling.'
 # Clearing after a cycle must not be undone by Cycle Back either.
 p.evaluate('promotionTest.full()');p.evaluate('tweakTest.direct(1)')
 dialog(p).get_by_role('button',name='Remove Needs Tweaking',exact=True).tap()
 p.evaluate('slotTest.back()');assert 'needsTweaking' not in meal(p,1) and 'needsTweakingNote' not in meal(p,1)
 # A manually scheduled Ideas recipe must be removed using the same replacement logic.
 p.evaluate("promotionTest.manual('Wednesday','Mains',6)")
 assert any(r['id']==6 and r['day']=='Wednesday' for r in rows(p)) and not meal(p,6)['rotation']
 p.evaluate("tweakTest.viewer(6,'Wednesday')");p.get_by_role('button',name='Mark as Needs Tweaking',exact=True).tap();save(p)
 assert not any(r['id']==6 for r in rows(p)) and f.pick(p,'Wednesday','Mains')['id'] in [10,11,12]
 check(c,p,errors,prefix);print('PASS',name,'repeated occurrences across tabs, promotion/cycling, post-cycle edit/clear retained by Cycle Back, scheduled Ideas override',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for w in [320,360]:scheduled(b,name,w);edge_cases(b,name,w)
   repeated_and_cycle_back(b,name)
  b.close()
