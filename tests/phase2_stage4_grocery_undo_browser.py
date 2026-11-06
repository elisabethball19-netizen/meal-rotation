"""Occurrence-aware group Undo with real Grocery List shopping interactions."""
import copy,json,sys
from pathlib import Path
from playwright.sync_api import sync_playwright
import phase2_stage4_final_browser as f

t=f.t
f.t.stage.f.HOOK += '''window.groupShopping={
 prepare:(legacy=false)=>{const main=meals.find(m=>m.id===1);assignSharedRecipeFields(main,{ingredients:[...main.ingredients,'4 cloves garlic']});const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selections['1'].push('4 cloves garlic');localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));withSchedulingPlan('lunch',()=>{saveOneTimeMeal('Thursday','Sides','Unrelated errand',['7 apples','1 cup rice','2 plums']);saveOneTimeMeal('Wednesday',null,'Already bought',['5 pears'])});for(const source of getGroceryContributions(true))groceryOccurrenceChecks.checks[source.id]=source.original.includes('pears')||source.original.includes('plums');if(legacy){groceryOccurrenceChecks.checks={};for(const source of getGroceryContributions(true))if(source.original.includes('pears')||source.original.includes('plums'))checkedIngredients.add(source.baseKey)}saveGroceryOccurrenceChecks();localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));if(!legacy)masterGroceryExcludedMealKeys.add(groceryMealKey(mealPlans.find(p=>p.id==='lunch'),meals.find(m=>m.id===10)));saveMasterGroceryMealExclusions();persist();renderList()},
 state:()=>{const v=stage4Final.state();v.checked.sort();v.exclusions={plans:[...masterGroceryExcludedPlanIds].sort(),meals:[...masterGroceryExcludedMealKeys].sort()};return v},
 rows:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,baseKey:item.baseKey,quantity:item.quantity,checked:groceryItemChecked(key,item),ids:item.contributions.map(s=>s.id)})),
 view:()=>{showTop=true;groceryTabActive=true;allMealsActive=false;renderList()},
 stacks:()=>({undo:history.length,redo:redoHistory.length}),
 late:()=>{for(const [key,value]of Object.entries(cookingSessions.occurrences))if(value.context.planId==='lunch'&&value.context.day==='Tuesday'){value.ingredients=[];value.steps=[];value.autoIngredients=[];for(const token of Object.keys(value.ingredientOverrides))value.ingredientOverrides[token]=false;occurrenceScales.occurrences[key].multiplier=3}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales);persist()}
};'''
def state(p):return p.evaluate('groupShopping.state()')
def rows(p):return p.evaluate('groupShopping.rows()')
def toggle(p,word,value):
 entries=rows(p);matches=[(i,row) for i,row in enumerate(entries) if word in row['line'] and row['checked']!=value];assert len(matches)==1,(word,value,entries);i,row=matches[0];stacks=p.evaluate('groupShopping.stacks()');element=p.locator('.master-grocery-item').nth(i);assert element.locator('.grocery-ingredient-name').inner_text()==row['line'];element.get_by_role('checkbox').set_checked(value);assert p.evaluate('groupShopping.stacks()')==stacks,'Shopping checkbox must not create Undo';return row['ids']
def plan_filter(p,enabled):
 p.get_by_role('button',name='Choose Meals',exact=True).click();d=p.get_by_role('dialog',name='Choose Meals',exact=True);d.get_by_role('checkbox',name='Dinner',exact=True).set_checked(enabled);d.get_by_role('button',name='Save meal selections',exact=True).click()
def prepare(b,name,duplicate,legacy=False):
 c,p,e,prefix=f.seeded(b,name,duplicate=duplicate);p.evaluate('groupShopping.prepare',legacy);return c,p,e,prefix

def reproduce(b,name,duplicate):
 c,p,e,_=prepare(b,name,duplicate);f.move(p);p.evaluate('groupShopping.view()');ids=toggle(p,'apples',True);assert len(ids)==1;assert all(s['checked'] for s in state(p)['sources'] if s['id'] in ids);p.locator('#undo').click();assert all(not s['checked'] for s in state(p)['sources'] if s['id'] in ids);p.reload();assert all(not s['checked'] for s in state(p)['sources'] if s['id'] in ids);t.clean(e);c.close();print('REPRODUCED',name,'shared destination',duplicate,'actual Lunch/Thursday apples checkbox true -> false after group Undo and reload',flush=True)
def owned(id,duplicate):
 occurrence=json.loads(json.loads(id)[0]);return occurrence[:2]==['original','Tuesday'] and (duplicate or occurrence[2]=='1')
def expected_undo(before,late,duplicate):
 expected=copy.deepcopy(before);after_sources={s['id']:s for s in late['sources']}
 expected['sources']=[after_sources[s['id']] if not owned(s['id'],duplicate) else s for s in expected['sources']]
 expected['checks']['checks']={key:value for key,value in late['checks']['checks'].items() if not owned(key,duplicate)}
 expected['checks']['checks'].update({key:value for key,value in before['checks']['checks'].items() if owned(key,duplicate)})
 garlic=next(s for s in before['sources'] if 'garlic' in s['original']);keys={garlic['baseKey'],*garlic['checkKeys']};expected['checked']=sorted((set(late['checked'])-keys)|(set(before['checked'])&keys))
 # Preserve a restored unchecked source when the shared legacy rice flag is
 # retained for unrelated shopping; the exclusive garlic flag was restored.
 for source in before['sources']:
  if owned(source['id'],duplicate) and source['baseKey'] in expected['checked'] and not source['checked'] and source['id'] not in before['checks']['checks']:expected['checks']['checks'][source['id']]=False
 for field in ['sessions','scales']:
  for key,value in late[field]['occurrences'].items():
   if value['context']['planId']=='lunch':expected[field]['occurrences'][key]=value
 expected['exclusions']=late['exclusions'];return expected
def patch_shopping(expected,actual):
 result=copy.deepcopy(expected);current={s['id']:s for s in actual['sources']};result['sources']=[{**s,'checked':current[s['id']]['checked']} if s['planId']=='lunch' else s for s in result['sources']]
 for key,value in actual['checks']['checks'].items():
  if json.loads(json.loads(key)[0])[0]=='lunch':result['checks']['checks'][key]=value
 # Only the unrelated fruit flags were changed at this point in the UI.
 fruit_keys={s['baseKey'] for s in actual['sources'] if s['planId']=='lunch' and ('apples' in s['original'] or 'plums' in s['original'])};result['checked']=sorted((set(result['checked'])-fruit_keys)|(set(actual['checked'])&fruit_keys));return result

def visible(p,expected):
 groups={}
 for source in expected['sources']:
  if source['planId'] in expected['exclusions']['plans'] or str(source['planId'])+'::'+str(source['mealId']) in expected['exclusions']['meals']:continue
  key=(source['baseKey'],source['checked']);entry=groups.setdefault(key,{'ids':set(),'lo':0,'hi':0,'quantity':source['quantity']});entry['ids'].add(source['id'])
  if source['quantity']:entry['lo']+=source['quantity']['lo'];entry['hi']+=source['quantity']['hi']
 actual=rows(p);assert {(row['baseKey'],row['checked']) for row in actual}==set(groups)
 for i,row in enumerate(actual):
  want=groups[row['baseKey'],row['checked']];assert set(row['ids'])==want['ids'],'Visible contribution identities differ'
  if want['quantity']:assert row['quantity']['lo']==want['lo'] and row['quantity']['hi']==want['hi'] and row['quantity']['unit']==want['quantity']['unit']
  else:assert row['quantity'] is None
  element=p.locator('.master-grocery-item').nth(i);assert element.get_by_role('checkbox').is_checked()==row['checked'];assert element.locator('.grocery-ingredient-name').inner_text()==row['line']

def run(b,name,duplicate,fail='none',legacy=False):
 c,p,e,prefix=prepare(b,name,duplicate,legacy);before=state(p);native=f.safety.native(p,prefix)
 if fail=='move':f.safety.fail_writes(p,['mealRotationDataV1'])
 f.move(p)
 if fail=='move':
  assert state(p)==before and f.safety.native(p,prefix)==native;assert p.locator('#mealSaveWarning').is_visible();p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click()
 p.evaluate('groupShopping.late();groupShopping.view()');plan_filter(p,False);assert any(row['checked'] and 'pears' in row['line'] for row in rows(p));toggle(p,'apples',True);toggle(p,'plums',False);plan_filter(p,True);shared=toggle(p,'rice',True);assert any(json.loads(json.loads(id)[0])[0]=='lunch' for id in shared) and any(json.loads(json.loads(id)[0])[:2]==['original','Tuesday'] for id in shared);affected=toggle(p,'garlic',True);assert affected and all(json.loads(json.loads(id)[0])[:2]==['original','Tuesday'] for id in affected);late=state(p);expected=expected_undo(before,late,duplicate)
 key='mealRotationGroceryOccurrenceChecksV1' if fail=='undo_ledger' else 'mealRotationCheckedIngredientsV1'
 if fail.startswith('undo_'):f.safety.fail_writes(p,[key])
 p.locator('#undo').click();assert state(p)==expected,('Undo must retain all unrelated shopping and exact affected state',name,duplicate,fail,state(p),expected);visible(p,expected)
 if fail.startswith('undo_'):
  assert p.locator('#mealSaveWarning').is_visible()
  with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
  recovery=json.loads(Path(dl.value.path()).read_text());assert json.loads(recovery['unsaved'][key])==(expected['checks'] if fail=='undo_ledger' else expected['checked']);p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert not p.locator('#mealSaveWarning').count();assert state(p)==expected
 toggle(p,'apples',False);before_redo=state(p);expected_redo=patch_shopping(late,before_redo);p.locator('#redo').click();assert state(p)==expected_redo,'Redo reverted unrelated shopping or altered complete moved state';visible(p,expected_redo)
 toggle(p,'plums',True);expected_second=patch_shopping(before_redo,state(p));p.locator('#undo').click();assert state(p)==expected_second,'Second Undo reverted unrelated shopping or occurrence metadata';visible(p,expected_second);saved=t.storage(p);p.reload();assert state(p)==expected_second;p.evaluate('weekTest.restore',saved);p.reload();assert state(p)==expected_second
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 t.clean(e);c.close();print('PASS',name,'shared destination',duplicate,fail,'legacy',legacy,'real checkbox edits, shared/affected checks, complete Undo/Redo/Undo, cooking/scales/exclusions, reload and backup',flush=True)

if __name__=='__main__':
 if '--source-root' in sys.argv:t.stage.f.ROOT=Path(sys.argv[sys.argv.index('--source-root')+1])
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for duplicate in [False,True]:
    if '--reproduce' in sys.argv:reproduce(b,name,duplicate)
    else:
     for fail in ['none','move','undo_ledger','undo_legacy']:run(b,name,duplicate,fail)
     run(b,name,duplicate,legacy=True)
  b.close()
