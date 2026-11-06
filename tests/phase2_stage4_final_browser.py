"""Focused final Stage 4 regressions. Synthetic state; real UI operations."""
import copy,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import phase2_stage4_corrections_browser as k
import phase1_data_safety_browser as safety
t=k.t

t.stage.f.HOOK += '''window.stage4Final={
 seed:()=>{writeMasterGroupOrder([...cats].reverse(),false);const main=meals.find(m=>m.id===1);assignSharedRecipeFields(main,{favorite:true,ingredients:[...main.ingredients,'3 carrots']});meals.find(m=>m.id===11).favorite=true;const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selected['3']=[];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));for(const plan of mealPlans)for(const cat of ['Rice','Sides'])advanceFavoriteRotation(plan,cat,meals.find(m=>m.cat===cat&&m.rotation));slotTest.seed();for(const value of Object.values(cookingSessions.occurrences)){const meal=meals.find(m=>String(m.id)===String(value.context.mealId)),tokens=cookingItemTokens(meal);value.ingredients=tokens.ingredients.map(i=>i.token);value.steps=tokens.steps.map(i=>i.token);value.autoIngredients=tokens.ingredients.map(i=>i.token);value.ingredientOverrides=Object.fromEntries(tokens.ingredients.map(i=>[i.token,true]))}writeCookingSessions(cookingSessions);for(const [i,source]of getGroceryContributions(true).entries())groceryOccurrenceChecks.checks[source.id]=i%2===0;saveGroceryOccurrenceChecks();persist();renderList()},
 state:()=>JSON.parse(JSON.stringify({meals,cats,display:{masterGroupOrder,pinnedCats,expandedCats,categoryColors,weekdayColors,topCounts,identities:readGroupIdentities()},plans:mealPlans,sessions:cookingSessions,scales:occurrenceScales,selected:JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}'),sources:getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),checks:groceryOccurrenceChecks,checked:[...checkedIngredients],history:localStorage.getItem(ROTATION_BACK_KEY)})),
 falseOverride:()=>{const value=Object.values(cookingSessions.occurrences).find(v=>v.context.planId==='original'&&v.context.day==='Tuesday'&&String(v.context.mealId)==='1'),token=Object.keys(value.ingredientOverrides).at(-1);value.ingredientOverrides[token]=false;value.ingredients=value.ingredients.filter(t=>t!==token);writeCookingSessions(cookingSessions)},
 late:()=>{for(const [key,value]of Object.entries(cookingSessions.occurrences))if(value.context.planId==='lunch'&&value.context.day==='Thursday'){value.ingredients=[];value.steps=[];value.autoIngredients=[];for(const token of Object.keys(value.ingredientOverrides))value.ingredientOverrides[token]=false;occurrenceScales.occurrences[key].multiplier=3}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales);persist()},
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))}
};'''
def state(p):return p.evaluate('stage4Final.state()')
def move(p):
 p.evaluate('stage4Test.del','Rice');d=p.get_by_role('dialog',name='Delete “Rice” group?',exact=True);d.get_by_role('button',name='Delete group, but keep recipes',exact=True).click();d.get_by_role('combobox',name='Move recipes to group',exact=True).select_option('Destination');d.get_by_role('button',name='Confirm moving recipes and deleting group',exact=True).click()
def seeded(b,name,width=360,duplicate=True):
 c,p,errors,prefix=t.setup(b,name,width);p.evaluate('stage4Test.destination()')
 if duplicate:p.evaluate('stage4Test.shared','Destination')
 p.evaluate('stage4Final.seed();stage4Test.groups()');return c,p,errors,prefix

def merge(b,name,duplicate=True,reproduce=False):
 c,p,errors,prefix=seeded(b,name,duplicate=duplicate);before=state(p);assert len(before['scales']['occurrences'])>=5;assert all(plan.get('favoriteRotationScores') for plan in before['plans']);assert before['selected']['3']==[];assert all(s['ingredients'] and s['steps'] and s['ingredientOverrides'] for s in before['sessions']['occurrences'].values());move(p);moved=state(p);p.locator('#undo').click();after=state(p)
 if reproduce:
  assert after['meals']==before['meals'];assert len(after['scales']['occurrences'])<len(before['scales']['occurrences']);assert len(after['sessions']['occurrences'])<len(before['sessions']['occurrences']);assert after['sources']!=before['sources'];print('REPRODUCED merge Undo state loss',name,'scales',len(before['scales']['occurrences']),len(after['scales']['occurrences']),'sessions',len(before['sessions']['occurrences']),len(after['sessions']['occurrences']),flush=True)
 else:
  assert after==before,('Complete Undo state differs',before,after)
  p.locator('#redo').click();assert state(p)==moved,'Redo must restore the complete moved state';p.locator('#undo').click();assert state(p)==before,'Second Undo must preserve all occurrence metadata'
  saved=t.storage(p);p.reload();assert state(p)==before,'Reload changed restored occurrence state';p.evaluate('weekTest.restore',saved);p.reload();assert state(p)==before,'Backup restoration changed complete restored state'
  if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
  # The moved state must also survive a reload and a complete backup restore.
  move(p);moved=state(p);saved=t.storage(p);p.reload();assert state(p)==moved;p.evaluate('weekTest.restore',saved);p.reload();assert state(p)==moved
  print('PASS',name,'merge',duplicate,'complete records/plans/selections/scales/cooking/groceries/checks Undo, reload and backup',flush=True)
 t.clean(errors);c.close()

def nested(b,name,width,reproduce=False,interaction='keyboard'):
 c,p,errors,_=t.setup(b,name,width);p.evaluate('weekTest.my()');head=p.locator('button.weekday-heading[data-weekday=Tuesday]');head.focus();p.keyboard.press('Enter');d=k.picker(p,'Tuesday');button=d.get_by_role('button',name='Side for Sides',exact=True);k.reach(p,button);p.keyboard.press('Enter');child=p.get_by_role('dialog',name='Side for Sides',exact=True);radio=child.get_by_role('radio',name='Independent',exact=True);k.reach(p,radio);p.keyboard.press('ArrowDown');assert child.get_by_role('radio',name='Dependent side for Rice',exact=True).is_checked();confirm=child.get_by_role('button',name='Confirm side for sides',exact=True);k.reach(p,confirm)
 if interaction=='touch':confirm.tap()
 elif interaction=='pointer':confirm.click()
 else:p.keyboard.press('Enter')
 if reproduce:
  assert p.evaluate('document.activeElement===document.body');p.keyboard.press('Escape');assert d.count();print('REPRODUCED nested confirmation BODY/immediate Escape ignored',name,width,flush=True)
 else:
  k.active(p,d);assert d.get_by_role('button',name='Side for Sides',exact=True).evaluate('(e)=>e===document.activeElement');p.keyboard.press('Escape');assert not d.count();k.restored(p,'Tuesday')
  # Confirm the reverse change and traverse both boundaries; then cancel a child.
  p.keyboard.press('Enter');d=k.picker(p,'Tuesday');button=d.get_by_role('button',name='Side for Sides',exact=True);k.reach(p,button);p.keyboard.press('Enter');child=p.get_by_role('dialog',name='Side for Sides',exact=True);radio=child.get_by_role('radio',name='Dependent side for Rice',exact=True);k.reach(p,radio);p.keyboard.press('ArrowUp');assert child.get_by_role('radio',name='Independent',exact=True).is_checked();k.reach(p,child.get_by_role('button',name='Confirm side for sides',exact=True));p.keyboard.press('Enter');k.active(p,d);k.ring(p,d);k.reach(p,d.get_by_role('button',name='Side for Sides',exact=True));p.keyboard.press('Enter');child=p.get_by_role('dialog',name='Side for Sides',exact=True);p.keyboard.press('Escape');k.active(p,d);p.keyboard.press('Escape');assert not d.count();k.restored(p,'Tuesday');print('PASS',name,width,interaction,'side confirmation both directions, immediate focus/Escape, parent trap and child Cancel',flush=True)
 t.clean(errors);c.close()

def failure(b,name,key,duplicate=True):
 c,p,errors,prefix=seeded(b,name,duplicate=duplicate);before=state(p);native=safety.native(p,prefix);safety.fail_writes(p,[key]);move(p);assert state(p)==before,'Failed group change leaked memory state';assert safety.native(p,prefix)==native,'Failed group change changed durable data';assert p.locator('#mealSaveWarning').is_visible();assert p.locator('#categoryDeleteDialog').count()==1
 # Existing failed-operation export retains the full proposal and old base.
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 exported=json.loads(Path(dl.value.path()).read_text());transactions=exported['failedTransactions'];assert any(x['kind']=='group-removal' for x in transactions);assert any('mealRotationCookingSessionsV1' in proposal['storage'] and 'mealRotationOccurrenceScalesV1' in proposal['storage'] for x in transactions for proposal in x['proposals'])
 p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert not p.locator('#mealSaveWarning').count();assert not p.locator('#categoryDeleteDialog').count();assert 'Rice' not in state(p)['cats'];p.locator('#undo').click();assert state(p)==before,'Retry followed by Undo must restore every occurrence and record';saved=t.storage(p);p.reload();assert state(p)==before;p.evaluate('weekTest.restore',saved);p.reload();assert state(p)==before
 t.clean(errors);c.close();print('PASS',name,key,'merge',duplicate,'atomic failed-save rollback, recovery proposal/export, Retry, exact Undo, reload and backup',flush=True)

def undo_failure(b,name,key):
 c,p,errors,prefix=seeded(b,name);before=state(p);move(p);safety.fail_writes(p,[key]);p.locator('#undo').click();assert p.locator('#mealSaveWarning').is_visible();assert state(p)==before,'Pending Undo must retain complete restored state in memory'
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 recovery=json.loads(Path(dl.value.path()).read_text());assert key in recovery['unsaved'];assert json.loads(recovery['unsaved'][key])==(before['scales'] if key=='mealRotationOccurrenceScalesV1' else before['display']['masterGroupOrder'] if key=='mealRotationGroupDisplayOrderV1' else before['sessions'])
 p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert not p.locator('#mealSaveWarning').count();assert state(p)==before;p.reload();assert state(p)==before;saved=t.storage(p);p.evaluate('weekTest.restore',saved);p.reload();assert state(p)==before;t.clean(errors);c.close();print('PASS',name,key,'failed Undo retains/export complete pending occurrence state; Retry, reload and backup',flush=True)

def retained_progress(b,name):
 c,p,errors,_=seeded(b,name);p.evaluate('stage4Final.falseOverride()');before=state(p);move(p);p.evaluate('stage4Final.late()');late=state(p);expected=copy.deepcopy(before)
 keys=[key for key,value in before['scales']['occurrences'].items() if value['context']['planId']=='lunch' and value['context']['day']=='Thursday'];assert keys
 for key in keys:
  expected['scales']['occurrences'][key]=late['scales']['occurrences'][key];expected['sessions']['occurrences'][key]=late['sessions']['occurrences'][key]
 changed={source['id']:source for source in late['sources'] if source['planId']=='lunch' and source['day']=='Thursday'};assert changed
 expected['sources']=[changed.get(source['id'],source) for source in expected['sources']]
 p.locator('#undo').click();assert state(p)==expected,'Undo must restore the merged contexts while keeping later unrelated cooking/scales';saved=t.storage(p);p.reload();assert state(p)==expected;p.evaluate('weekTest.restore',saved);p.reload();assert state(p)==expected;t.clean(errors);c.close();print('PASS',name,'false overrides and later unrelated cooking/scaling survive exact group Undo, reload and backup',flush=True)

if __name__=='__main__':
 reproduce='--reproduce' in sys.argv
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  if reproduce:
   for root in ['/tmp/stage4-before','/tmp/stage4-final-before']:
    t.stage.f.ROOT=Path(root)
    for name in ['index.html','meal-rotation-test.html']:merge(b,name,reproduce=True)
   t.stage.f.ROOT=Path('/tmp/stage4-final-before')
   for name in ['index.html','meal-rotation-test.html']:
    for width in [280,320,360]:nested(b,name,width,True)
  else:
   for name in ['index.html','meal-rotation-test.html']:
    for duplicate in [False,True]:merge(b,name,duplicate)
    retained_progress(b,name)
    for key in ['mealRotationCookingSessionsV1','mealRotationOccurrenceScalesV1','mealRotationDataV1']:failure(b,name,key)
    failure(b,name,'mealRotationDataV1',False)
    for key in ['mealRotationOccurrenceScalesV1','mealRotationCookingSessionsV1','mealRotationGroupDisplayOrderV1']:undo_failure(b,name,key)
    for width in [280,320,360]:nested(b,name,width)
    for interaction in ['pointer','touch']:nested(b,name,320,interaction=interaction)
  b.close()
