"""Issue 19: rotate scheduled owners/occurrences, not linked recipe IDs. Synthetic data."""
import json,copy,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
def meal(id,name,cat,links=None,labels=None):
 return dict(id=id,name=name,cat=cat,rotation=True,ingredients=[str(id)+' cups rice'],instructions=[{'type':'step','text':'Cook rice for 15 minutes.'}],notes='Keep notes '+str(id),url='https://recipes.test/'+str(id),linkedMealIds=links or [],labels=labels or [],custom={'keep':id})
MEALS=[meal(1,'Crying Tiger','Mains',[10,20]),meal(2,'Next Main','Mains'),meal(3,'Other Parent','Other',[10]),meal(4,'Next Other','Other'),meal(10,'Roasted Garlic Rice','Rice',labels=['Only']),meal(11,'Plain Rice','Rice'),meal(12,'Other Rice','Rice'),meal(20,'Puerto Vallarta salsa roja','Salsa'),meal(21,'Other Salsa','Salsa')]
HOOK='''window.cycleTest={state:()=>({meals,plans:mealPlans,activePlanId,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs}),rows:()=>mealPlans.flatMap(plan=>getDisplayedWeekdayMealsForPlan(plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan).map(x=>({planId:plan.id,day:x.day,cat:x.cat,id:x.meal.id,parent:String(x.linkedTo??''),scheduled:rotationGroupScheduled(plan,x.day,x.cat)}))),chooser:(all=false)=>openMoveMealChooser(all),cycle:(keys=null,all=false,mark=false)=>moveDisplayedMealsToBottom(keys?new Set(keys):null,all,mark),back:()=>rotateAllBack(),partial:keys=>rotateSelectedBack(keys),backChooser:()=>openRotateBackChooser(),previous:()=>readPreviousRotation(),oldHistory:()=>{const p=readPreviousRotation();delete p.rotationOccurrences;localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify(p))},storage:()=>cycleBackup.capture(),groceries:()=>[...getMasterGroceryItems().values()],restore:b=>{cycleBackup.restore(cycleBackup.normalize(b));backupRestoreReloadPending=true},seed:()=>{for(const plan of mealPlans)for(const entry of getDisplayedWeekdayMealsForPlan(plan)){const c=cookingContext(plan.id,entry.day,entry.cat,entry.meal,entry.linkedTo),key=cookingOccurrenceKey(c),items=cookingItemTokens(entry.meal);cookingSessions.occurrences[key]={id:'session-'+key,context:c,ingredients:[items.ingredients[0].token],steps:[items.steps[0].token],autoIngredients:[],ingredientOverrides:{[items.ingredients[0].token]:true}};occurrenceScales.occurrences[key]={context:c,multiplier:2}}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales)},edit:()=>{meals.find(m=>m.id===2).notes='Edited after cycling';persist()}};'''
def setup(browser,filename,width,mode='simple'):
 assignments={'Tuesday':['Mains']};overrides={};plans=[]
 if mode in ['independent','shared','multi','replacement']:assignments['Friday']=['Rice']
 if mode=='shared':assignments['Tuesday']=['Mains','Other']
 if mode=='replacement':assignments={'Tuesday':['Mains','Rice']};overrides={'Tuesday::Rice':'11'}
 if mode=='same-day':assignments={'Tuesday':['Mains','Rice']}
 if mode in ['repeated','legacy-pin']:assignments={'Tuesday':['Mains'],'Thursday':['Mains'],'Friday':['Mains']}
 if mode=='legacy-pin':overrides={'Thursday':'1'}
 plans=[dict(id='original',name='Dinner',weekdayCategories=assignments,weekdayMealOverrides=overrides,weekdayRecipeFilters={},pinnedCats=[])]
 if mode=='multi':plans.append(dict(id='lunch',name='Lunch',weekdayCategories={'Friday':['Rice']},weekdayMealOverrides={},weekdayRecipeFilters={'Friday::Rice':['Only']},pinnedCats=[]))
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Mains','Other','Rice','Salsa'],active='Mains',meals=MEALS)),prefix+'mealRotationPlansV1':json.dumps(dict(plans=plans,activeId='original')),prefix+'mealRotationShowPlanTabsV1':'true',prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=True,autoCompleteIngredients=True,keepScreenAwake=False,autoOpenLinkedRecipes=True)),prefix+'mealRotationSelectedIngredientsV1':json.dumps({'1':['1 cups rice'],'10':['10 cups rice']}),prefix+'mealRotationCheckedIngredientsV1':json.dumps(['10 cups rice']),prefix+'mealRotationTutorialStageV1':'done'}
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL';seed['mealRotationCookingSessionsV1']='PROGRESS SENTINEL'
 ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,accept_downloads=True);page=ctx.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
 source=(ROOT/filename).read_text().replace('function validateBackupCore(d){','window.cycleBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){')
 source=source.replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
 page.route('http://cycle.test/**',lambda route:route.fulfill(status=200,content_type='text/html',body=source) if route.request.url.endswith(filename) else route.fulfill(status=200,body=''))
 page.route('https://**/*',lambda route:route.fulfill(status=200,body=''))
 page.goto('http://cycle.test/'+filename);page.evaluate('cycleTest.seed()');return ctx,page,errors,prefix

def state(page):return page.evaluate('cycleTest.state()')
def rows(page):return page.evaluate('cycleTest.rows()')
def key(row):return json.dumps([row['planId'],row['day'],str(row['id']),str(row['parent'])],separators=(',',':'))
def core(page):return sorted((r['planId'],r['day'],r['cat'],r['id'],str(r['parent'])) for r in rows(page))
def check_definitions(before,after):assert sorted(before['meals'],key=lambda m:m['id'])==sorted(after['meals'],key=lambda m:m['id'])
def open_chooser(page):
 page.get_by_role('button',name='Cycle Meals',exact=True).tap();page.get_by_role('button',name='Select recipes to rotate out',exact=True).tap()
 return page.locator('div').filter(has=page.get_by_role('heading',name='Select meals to rotate out',exact=True)).filter(has=page.get_by_role('button',name='Move selected',exact=True)).last

def run(browser,filename,width):
 # One visible parent; select/deselect/cancel, all vs explicit selection, history reload/undo.
 ctx,page,errors,prefix=setup(browser,filename,width);before=state(page);before_rows=core(page);storage=page.evaluate('cycleTest.storage()')
 open_chooser(page);labels=page.locator('label').filter(has=page.locator('input[type=checkbox]')).all_text_contents();assert page.get_by_role('heading',name='Select meals to rotate out').is_visible()
 # Scope to the overlay to exclude other page settings checkboxes.
 dialog=page.get_by_role('heading',name='Select meals to rotate out').locator('..');assert dialog.get_by_role('checkbox').count()==1
 assert 'Crying Tiger' in dialog.inner_text() and 'Roasted Garlic Rice' not in dialog.inner_text() and 'Puerto Vallarta' not in dialog.inner_text()
 dialog.get_by_role('button',name='Deselect all',exact=True).click();assert not dialog.get_by_role('checkbox').is_checked();dialog.get_by_role('button',name='Move selected',exact=True).click();assert page.evaluate('cycleTest.storage()')==storage
 open_chooser(page);dialog=page.get_by_role('heading',name='Select meals to rotate out').locator('..');dialog.get_by_role('button',name='Deselect all',exact=True).click();dialog.get_by_role('button',name='Select all',exact=True).click();assert dialog.get_by_role('checkbox').is_checked();dialog.get_by_role('button',name='Cancel',exact=True).click();assert page.evaluate('cycleTest.storage()')==storage
 open_chooser(page);page.get_by_role('button',name='Move selected',exact=True).click();assert [r['id'] for r in rows(page)]==[2],rows(page);check_definitions(before,state(page))
 previous=page.evaluate('cycleTest.previous()');assert len(previous['rotationOccurrences'])==3 and len(previous['cookingCycledContexts'])==3
 page.reload();page.evaluate('cycleTest.back()');assert core(page)==before_rows;check_definitions(before,state(page))
 page.evaluate('cycleTest.cycle()');page.get_by_role('button',name='Undo',exact=True).click();assert core(page)==before_rows
 assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if filename=='index.html' and width==360:
  open_chooser(page);page.screenshot(path='/tmp/issue19-cycle-chooser-360.png');page.get_by_role('button',name='Cancel',exact=True).tap()
 if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;ctx.close()
 for mode in ['independent','same-day','shared','replacement','multi','repeated','legacy-pin']:
  ctx,page,errors,prefix=setup(browser,filename,width,mode);before=state(page);before_rows=core(page);prior=rows(page);storage=page.evaluate('cycleTest.storage()');groceries=page.evaluate('cycleTest.groceries()')
  if mode=='legacy-pin':assert any(r['day']=='Thursday' and r['id']==2 for r in prior)
  page.evaluate('cycleTest.chooser(true)');dialog=page.get_by_role('heading',name='Select meals to rotate out').locator('..');expected=[r for r in prior if (r['parent']=='' or r.get('scheduled'))];assert dialog.get_by_role('checkbox').count()==len(expected),(mode,prior)
  # Only select Tuesday's main; every other top-level occurrence must stay.
  dialog.get_by_role('button',name='Deselect all',exact=True).click();dialog.get_by_role('checkbox').nth(next(i for i,r in enumerate(expected) if r['id']==1)).check();dialog.get_by_role('button',name='Move selected',exact=True).click()
  after=state(page);now=rows(page);check_definitions(before,after)
  for r in prior:
   if not (r['planId']=='original' and r['day']=='Tuesday' and (r['parent']=='1' or ((r['parent']=='' or r.get('scheduled')) and r['id']==1))):
    assert r in now,(mode,'independent occurrence moved',r,now)
    assert before['sessions']['occurrences'][key(r)]==after['sessions']['occurrences'][key(r)],(mode,'progress',r)
    assert before['scales']['occurrences'][key(r)]==after['scales']['occurrences'][key(r)],(mode,'scaling',r)
  if mode=='shared':assert any(r['id']==10 and r['parent']=='3' for r in now) and not any(r['id']==20 for r in now)
  if mode=='replacement':assert any(r['id']==10 and r.get('scheduled') for r in now),(mode,now)
  assert json.loads(page.evaluate('cycleTest.storage()')['mealRotationSelectedIngredientsV1'])==json.loads(storage['mealRotationSelectedIngredientsV1'])
  assert before['prefs']==after['prefs']
  # New history restores only the selected parent and implied children; later edits survive partial Back.
  page.evaluate('cycleTest.edit()');page.evaluate('cycleTest.backChooser()');back_dialog=page.get_by_role('heading',name='Select meals to rotate back').locator('..');assert all('Roasted Garlic Rice' not in t and 'Puerto Vallarta' not in t for t in back_dialog.get_by_role('checkbox').locator('..').all_text_contents())
  back_dialog.get_by_role('button',name='Cancel',exact=True).click();page.evaluate("cycleTest.partial(['original||Tuesday::Mains'])");assert core(page)==before_rows,(mode,'partial back',rows(page),before_rows)
  assert next(m for m in state(page)['meals'] if m['id']==2)['notes']=='Edited after cycling'
  # Legacy history without the occurrence extension uses the normal linked scheduler.
  page.evaluate("cycleTest.cycle(['Tuesday::Mains'])");page.evaluate('cycleTest.oldHistory()');page.evaluate("cycleTest.partial(['original||Tuesday::Mains'])");assert core(page)==before_rows,(mode,'legacy back',rows(page),before_rows)
  if mode=='shared':
   page.evaluate('cycleTest.seed()');shared_before=state(page);owned=[r for r in rows(page) if r['parent']=='1'];page.evaluate("cycleTest.cycle(['Tuesday::Other'])");shared_after=state(page)
   for r in owned:
    assert r in rows(page) and shared_before['sessions']['occurrences'][key(r)]==shared_after['sessions']['occurrences'][key(r)] and shared_before['scales']['occurrences'][key(r)]==shared_after['scales']['occurrences'][key(r)]
   page.evaluate('cycleTest.back()');assert core(page)==before_rows
  if mode=='multi':
   page.evaluate('cycleTest.chooser(true)');all_dialog=page.get_by_role('heading',name='Select meals to rotate out').locator('..');all_dialog.get_by_role('button',name='Deselect all',exact=True).tap();assert all_dialog.locator('input:checked').count()==0;all_dialog.get_by_role('button',name='Select all',exact=True).tap();assert all_dialog.locator('input:checked').count()==len([r for r in rows(page) if (r['parent']=='' or r.get('scheduled'))]);all_dialog.get_by_role('button',name='Move selected',exact=True).tap();page.evaluate('cycleTest.back()');assert core(page)==before_rows
  assert not errors,errors;ctx.close()
 # Explicit mark-cooked behavior and backup/history compatibility remain available.
 ctx,page,errors,prefix=setup(browser,filename,width,'independent');original_rows=core(page);page.evaluate("cycleTest.cycle(['Tuesday::Mains'],false,true)");marked=state(page)
 assert all(next(m for m in marked['meals'] if m['id']==id).get('lastCooked') for id in [1,10,20]);assert not next(m for m in marked['meals'] if m['id']==2).get('lastCooked')
 page.get_by_role('button',name='Settings and backups',exact=True).click();page.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true')
 with tempfile.TemporaryDirectory() as tmp:
  with page.expect_download() as dl:page.get_by_role('button',name='Export backup',exact=True).click()
  path=Path(tmp)/'backup.json';dl.value.save_as(path);backup=json.loads(path.read_text());saved=backup['storage'];assert 'rotationOccurrences' in json.loads(saved['mealRotationLastRotationBeforeV1'])
  page.evaluate('(b)=>cycleTest.restore(b)',backup);page.reload();page.evaluate('cycleTest.back()');assert core(page)==original_rows
 assert not errors,errors;ctx.close()
 print('PASS',filename,width,'parent-only choices, select/deselect/cancel/all/partial, independent same-day/different-day/cross-tab slots, shared owners, linked replacement, history/legacy fallback, Cycle Back/Undo, progress/scales/selection/settings preservation; no JS errors',flush=True)
if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for f in ['index.html','meal-rotation-test.html']:
   for w in [320,360]:run(b,f,w)
  b.close()
