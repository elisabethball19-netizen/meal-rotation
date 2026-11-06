"""Phase 1 regressions. Synthetic data and disposable browser contexts only."""
import copy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import scheduled_linked_slots_browser as f

ROOT=Path(__file__).resolve().parents[1]
f.HOOK+='''window.safetyTest={
 edit:()=>{const m=meals.find(m=>m.id===1);Object.assign(m,{name:'Edited after cycling',ingredients:['3 cups brown rice'],instructions:[{type:'step',text:'New instructions.'}],notes:'New notes',custom:{keep:'new'},url:'https://new.test/recipe',favorite:true,serveWith:['Rice'],makeAheadTasks:[{id:'new',description:'Prepare',daysBefore:1}]});const child=meals.find(m=>m.id===20);child.name='Edited linked sauce';child.notes='New linked notes';child.ingredients=['2 tbsp new sauce'];child.instructions='New sauce method.';const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1'));selections['1']=['3 cups brown rice'];selections['20']=['2 tbsp new sauce'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));persist()},
 add:()=>{meals.push({id:99,name:'Added after cycling',cat:'Sauces',rotation:true,ingredients:['1 tsp salt'],instructions:'Stir.',url:'',custom:{added:true}});id=100;persist()},
 links:()=>{meals.find(m=>m.id===1).linkedMealIds=[21];persist()},
 swipe:id=>openMealSwipeMenu(meals.find(m=>m.id===id)),
 remove:id=>applyRecipeBulk([String(id)],{delete:true}),
 persist:()=>{persist();saveActiveMealPlan()},
 plans:()=>mealPlans,
 preferences:()=>{mealTextSize='large';localStorage.setItem('mealRotationTextSizeV1','large');applyMealTextSize()},
 scale:()=>{const x=getDisplayedWeekdayMeals()[0],c=cookingContext(activePlanId,x.day,x.cat,x.meal,x.linkedTo);const next=JSON.parse(JSON.stringify(occurrenceScales));next.occurrences[cookingOccurrenceKey(c)]={context:c,multiplier:3};writeOccurrenceScales(next)},
 checks:()=>{const [key,item]=[...getMasterGroceryItems()][0];setGroceryItemChecked(key,item,true)},
 editor:()=>openEditor(1),
 stopTimer:()=>cancelCookingTimer(),
 timer:()=>{cookingTimer={version:1,id:'safety-clock',recipeId:'1',recipeName:'Thai Garlic Pork',stepToken:'step',stepText:'Cook.',status:'paused',remaining:120000};saveCookingTimer()},
 rename:()=>{meals.find(m=>m.id===1).name='Unsaved recipe name';persist()},
 bulk:()=>applyRecipeBulk(['1'],{favorite:true}),
 storage:()=>captureBackupStorage()
};'''

def native(page,prefix=''):
 return page.evaluate('prefix=>Object.fromEntries(Object.entries(window.localStorage).filter(([k])=>k.startsWith(prefix+"mealRotation")&&(!prefix?!k.startsWith("mealRotationTestSandboxV1:"):true)))',prefix)

def fail_writes(page,targets=None,once=False):
 page.evaluate('''({targets,once})=>{window.safetyNativeSet=Storage.prototype.setItem;window.safetyNativeRemove=Storage.prototype.removeItem;let failed=false;const blocked=key=>(!targets||targets.some(x=>key.endsWith(x)))&&(!once||!failed);Storage.prototype.setItem=function(k,v){if(blocked(k)){failed=true;throw new DOMException('Injected quota failure','QuotaExceededError')}return safetyNativeSet.call(this,k,v)};Storage.prototype.removeItem=function(k){if(blocked(k)){failed=true;throw new Error('Injected remove failure')}return safetyNativeRemove.call(this,k)};window.restoreSafetyWrites=()=>{Storage.prototype.setItem=safetyNativeSet;Storage.prototype.removeItem=safetyNativeRemove}}''',dict(targets=targets,once=once))

def schedule_edits(browser,name,partial):
 c,p,errors,prefix=f.setup(browser,name,360,linked=True)
 before=f.compose(p);p.evaluate("slotTest.cycle(['Tuesday::Rice','Tuesday::Sides'])")
 p.evaluate('safetyTest.edit();safetyTest.add()');expected=f.definitions(f.state(p));selected=p.evaluate('safetyTest.storage()')['mealRotationSelectedIngredientsV1']
 if partial:p.evaluate("slotTest.partial(['original||Tuesday::Rice'])")
 else:p.evaluate('slotTest.back()')
 assert f.definitions(f.state(p))==expected
 assert p.evaluate('safetyTest.storage()')['mealRotationSelectedIngredientsV1']==selected
 assert f.slot(f.rows(p),'Rice')['id']==1
 if not partial:assert f.compose(p)==before
 p.reload();assert f.definitions(f.state(p))==expected and not errors,errors
 print('PASS',name,'selected' if partial else 'all','Cycle Back preserves current recipe/linked content, additions, selections, and reload',flush=True);c.close()

def schedule_links_and_deletions(browser,name):
 for partial in [False,True]:
  c,p,errors,prefix=f.setup(browser,name,360,linked=True);p.evaluate("slotTest.cycle(['Tuesday::Rice','Tuesday::Sides'])");p.evaluate('safetyTest.links()');expected=f.definitions(f.state(p));p.evaluate("slotTest.partial(['original||Tuesday::Rice'])" if partial else 'slotTest.back()');assert f.definitions(f.state(p))==expected
  rs=f.rows(p);assert any(x['id']==21 and x['parent']=='1' for x in rs) and not any(x['id']==20 and x['parent']=='1' for x in rs),rs
  assert not errors,errors;c.close()
 for partial in [False,True]:
  for deleted in [1,10,20]:
   c,p,errors,prefix=f.setup(browser,name,360,linked=True);p.evaluate("slotTest.cycle(['Tuesday::Rice','Tuesday::Sides'])");p.evaluate('safetyTest.remove',deleted);expected=f.definitions(f.state(p));p.evaluate("slotTest.partial(['original||Tuesday::Rice','original||Tuesday::Sides'])" if partial else 'slotTest.back()');assert f.definitions(f.state(p))==expected and all(x['id']!=deleted for x in f.rows(p));p.reload();assert f.definitions(f.state(p))==expected;assert not errors,errors;c.close()
 print('PASS',name,'both Back modes retain edited links; main/side/attachment deletions never resurrect',flush=True)

def swipe(browser,name):
 c,p,errors,prefix=f.setup(browser,name,360,linked=True);p.evaluate("slotTest.cycle(['Tuesday::Rice','Tuesday::Sides'])");before=copy.deepcopy(f.state(p));p.evaluate('safetyTest.swipe(1)');p.locator('#mealSwipeMenu').get_by_role('button',name='Delete recipe',exact=True).click();assert all(m['id']!=1 for m in f.state(p)['meals']);assert '"mealId":"1"' not in json.dumps(p.evaluate('slotTest.history()'),separators=(',',':'));p.locator('#undo').click();assert f.definitions(f.state(p))==f.definitions(before)
 p.evaluate('safetyTest.swipe(1)');p.locator('#mealSwipeMenu').get_by_role('button',name='Delete recipe',exact=True).click();p.evaluate('slotTest.back()');assert all(m['id']!=1 for m in f.state(p)['meals']);assert not errors,errors
 print('PASS',name,'swipe uses dependency-aware deletion/history pruning; Undo works; Back cannot resurrect',flush=True);c.close()

def bare(browser,name,data,read_failure=False):
 prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
 seed={prefix+k:v for k,v in data.items()};seed['unrelated-user-setting']='keep'
 if prefix:seed['mealRotationDataV1']='PRODUCTION SENTINEL'
 c=browser.new_context(viewport={'width':320,'height':720},accept_downloads=True);p=c.new_page();p.set_default_timeout(5000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.add_init_script('if(!sessionStorage.safetySeed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.safetySeed="yes"}')
 if read_failure:p.add_init_script('window.originalSafetyGet=Storage.prototype.getItem;Storage.prototype.getItem=function(k){if(k.endsWith("mealRotationDataV1"))throw new Error("Injected read failure");return originalSafetyGet.call(this,k)}')
 source=(ROOT/name).read_text();p.route('http://safety.test/**',lambda r:r.fulfill(content_type='text/html',body=source) if r.request.url.endswith(name) else r.fulfill(body=''));p.goto('http://safety.test/'+name)
 return c,p,errors,prefix,seed

CORE={'cats':['Legacy'],'active':'Legacy','meals':[{'id':1,'cat':'Legacy','name':'Preserved legacy meal','rotation':True,'ingredients':['1 cup rice'],'url':'','custom':{'keep':True}}]}

def recovery(browser,name):
 invalids=[{'mealRotationDataV1':'{broken'}, {'mealRotationDataV1':'null'}, {'mealRotationDataV1':json.dumps({**CORE,'meals':[None]})}, {'mealRotationDataV1':json.dumps(CORE),'mealRotationPlansV1':'not-json'}, {'mealRotationDataV1':json.dumps(CORE),'mealRotationSelectedIngredientsV1':'[]'}, {'mealRotationDataV1':json.dumps(CORE),'mealRotationCookingSessionsV1':'{"version":1,"occurrences":null}'}]
 for data in invalids:
  c,p,errors,prefix,seed=bare(browser,name,data);cover=p.locator('#mealDataRecovery');assert cover.is_visible();assert not p.locator('.meal').count();p.wait_for_timeout(100);assert native(p,prefix)=={k:v for k,v in seed.items() if k.startswith(prefix+'mealRotation') and (prefix or not k.startswith('mealRotationTestSandboxV1:'))}
  with p.expect_download() as dl:cover.get_by_role('button',name='Export Data for Recovery',exact=True).click()
  exported=json.loads(Path(dl.value.path()).read_text());assert exported['storage']==data
  cover.get_by_role('button',name='Start Fresh',exact=True).click();assert native(p,prefix)=={k:v for k,v in seed.items() if k.startswith(prefix+'mealRotation') and (prefix or not k.startswith('mealRotationTestSandboxV1:'))};cover.get_by_role('button',name='Cancel Start Fresh',exact=True).click();assert not p.locator('[data-start-fresh-confirm]').count()
  assert not errors,errors;c.close()
 # Legacy data remains usable and custom fields are retained.
 for legacy in [CORE,{'cats':[],'active':'','meals':[]}]:
  c,p,errors,prefix,_=bare(browser,name,{'mealRotationDataV1':json.dumps(legacy)});assert not p.locator('#mealDataRecovery').count();saved=json.loads(p.evaluate('k=>window.localStorage.getItem(k)',prefix+'mealRotationDataV1'));assert saved['meals']==legacy['meals'];assert not errors,errors;c.close()
 # A denied read must never turn into a new installation or overwrite any key.
 c,p,errors,prefix,seed=bare(browser,name,{'mealRotationDataV1':json.dumps(CORE)},True);assert p.locator('#mealDataRecovery').is_visible();assert p.evaluate('k=>originalSafetyGet.call(window.localStorage,k)',prefix+'mealRotationDataV1')==json.dumps(CORE);assert not errors,errors;c.close()
 print('PASS',name,'malformed/invalid primary and dependent data freeze writes, exact raw export, cancelled reset, denied reads, legacy compatibility',flush=True)

def recovery_actions(browser,name):
 for version in [1,2]:
  c,p,errors,prefix,seed=bare(browser,name,{'mealRotationDataV1':'{broken','mealRotationSelectedIngredientsV1':'{also broken'})
  cover=p.locator('#mealDataRecovery');before=native(p,prefix)
  with p.expect_file_chooser() as fc:cover.get_by_role('button',name='Restore Backup',exact=True).click()
  fc.value.set_files({'name':'bad.json','mimeType':'application/json','buffer':b'{"cats":[],"meals":null}'})
  expect(cover.get_by_role('status')).to_contain_text('not restored')
  assert native(p,prefix)==before
  backup={'version':version,**CORE}
  if version==2:backup['storage']={'mealRotationDataV1':json.dumps(CORE),'mealRotationSelectedIngredientsV1':'{"1":["1 cup rice"]}'}
  with p.expect_file_chooser() as fc:cover.get_by_role('button',name='Restore Backup',exact=True).click()
  fc.value.set_files({'name':'valid.json','mimeType':'application/json','buffer':json.dumps(backup).encode()});p.wait_for_function('!document.getElementById("mealDataRecovery")');saved=json.loads(p.evaluate('k=>window.localStorage.getItem(k)',prefix+'mealRotationDataV1'));assert saved['meals']==CORE['meals'];assert p.evaluate('localStorage.getItem("unrelated-user-setting")')=='keep'
  if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='PRODUCTION SENTINEL'
  assert not errors,errors;c.close()
 c,p,errors,prefix,_=bare(browser,name,{'mealRotationDataV1':'{broken'});cover=p.locator('#mealDataRecovery');cover.get_by_role('button',name='Start Fresh',exact=True).click();cover.get_by_role('button',name='Confirm Start Fresh',exact=True).click();p.wait_for_function('!document.getElementById("mealDataRecovery")');assert json.loads(p.evaluate('k=>window.localStorage.getItem(k)',prefix+'mealRotationDataV1'))['meals']==[];assert p.evaluate('localStorage.getItem("unrelated-user-setting")')=='keep'
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='PRODUCTION SENTINEL'
 assert not errors,errors;c.close()
 print('PASS',name,'invalid backup rejected unchanged, V1/V2 recovery restore, explicit Start Fresh, unrelated/test namespace preserved',flush=True)

def failures(browser,name):
 for action in ['rename','preferences','scale','checks','timer']:
  c,p,errors,prefix=f.setup(browser,name,360);before=native(p,prefix);fail_writes(p)
  p.evaluate('safetyTest.'+action+'()');assert p.locator('#mealSaveWarning').is_visible();assert native(p,prefix)==before
  with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
  exported=json.loads(Path(dl.value.path()).read_text());assert exported['unsaved']
  p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert p.locator('#mealSaveWarning').is_visible() and native(p,prefix)==before
  p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert not p.locator('#mealSaveWarning').count();after=native(p,prefix);assert after!=before
  p.reload();assert not p.locator('#mealDataRecovery,#mealSaveWarning').count();assert not errors,errors;c.close()
 # Strict bulk failure rolls back instead of leaving a partial commit; explicit retry commits the whole proposal.
 c,p,errors,prefix=f.setup(browser,name,360);before=native(p,prefix);fail_writes(p,['mealRotationDataV1'],True)
 try:p.evaluate('safetyTest.bulk()');raise AssertionError('Expected transactional write failure')
 except Exception as e:assert 'Injected quota failure' in str(e),e
 assert native(p,prefix)==before and not next(m for m in f.state(p)['meals'] if m['id']==1).get('favorite');assert p.locator('#mealSaveWarning').is_visible();p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('window.safetyTest && !document.getElementById("mealSaveWarning")');assert next(m for m in f.state(p)['meals'] if m['id']==1)['favorite'];assert not errors,errors;c.close()
 print('PASS',name,'quota failures preserve durable data, retain pending recipe/preferences/scales/checks/timer, export/retry/reload; strict bulk rollback/retry',flush=True)

def failed_editor_and_recovery(browser,name):
 c,p,errors,prefix=f.setup(browser,name,320);p.evaluate('safetyTest.editor()');p.locator('#name').fill('Draft retained after save failure');before=native(p,prefix);fail_writes(p,['mealRotationDataV1'],True);p.locator('#save').click();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();assert p.locator('#name').input_value()=='Draft retained after save failure' and native(p,prefix)==before
 p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('window.safetyTest && !document.getElementById("mealSaveWarning")');assert next(m for m in f.state(p)['meals'] if m['id']==1)['name']=='Draft retained after save failure';assert not errors,errors;c.close()
 # Removal failures also retain the desired state for Retry Save.
 c,p,errors,prefix=f.setup(browser,name,320);p.evaluate('safetyTest.timer()');before=native(p,prefix);fail_writes(p,['mealRotationCookingTimerV1']);p.evaluate('safetyTest.stopTimer()');assert native(p,prefix)==before and p.locator('#mealSaveWarning').is_visible();p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert not p.locator('#mealSaveWarning').count();assert not errors,errors;c.close()
 # A failed recovery restore must leave the raw originals available and allow retry.
 c,p,errors,prefix,_=bare(browser,name,{'mealRotationDataV1':'{broken'});before=native(p,prefix);fail_writes(p,['mealRotationDataV1'],True);backup={'version':2,**CORE,'storage':{'mealRotationDataV1':json.dumps(CORE),'mealRotationSelectedIngredientsV1':'{}'}}
 with p.expect_file_chooser() as fc:p.locator('#mealDataRecovery').get_by_role('button',name='Restore Backup',exact=True).click()
 fc.value.set_files({'name':'valid.json','mimeType':'application/json','buffer':json.dumps(backup).encode()});p.wait_for_function('document.getElementById("mealRecoveryStatus").textContent.includes("not restored")');assert {k:v for k,v in native(p,prefix).items() if not k.endswith('mealRotationRecoveryJournalV1')}==before;assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1');p.evaluate('restoreSafetyWrites()')
 with p.expect_file_chooser() as fc:p.locator('#mealDataRecovery').get_by_role('button',name='Restore Backup',exact=True).click()
 fc.value.set_files({'name':'valid.json','mimeType':'application/json','buffer':json.dumps(backup).encode()});p.wait_for_function('!document.getElementById("mealDataRecovery")');assert not errors,errors;c.close()
 print('PASS',name,'real editor failed Save retains draft; banner Retry saves without outside-close prompts; remove failures; recovery rollback and retry',flush=True)

def assert_shared_code():
 production=(ROOT/'index.html').read_text();sandbox=(ROOT/'meal-rotation-test.html').read_text()
 marker='/* Shared inline in both apps:'
 def shared(source):return source[source.index(marker):source.index('</script><script>',source.index(marker))]
 expected=shared(production).replace('()=>window.localStorage','()=>testStorage').replace('const localStorage=bulkRecipeStorageBridge','const testStorage=bulkRecipeStorageBridge').replace('localStorage.','testStorage.')
 assert shared(sandbox)==expected
 assert "const TEST_PREFIX='mealRotationTestSandboxV1:'" in sandbox and 'Reset Test App' in sandbox
 print('PASS shared application code synchronized; isolated test wrapper retained',flush=True)

def run_all():
 assert_shared_code()
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   schedule_edits(b,name,False);schedule_edits(b,name,True);schedule_links_and_deletions(b,name);swipe(b,name);recovery(b,name);recovery_actions(b,name);failures(b,name);failed_editor_and_recovery(b,name)
  b.close()
if __name__=='__main__':run_all()

