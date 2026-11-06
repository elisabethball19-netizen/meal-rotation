"""Independent-review reproductions; disposable Chromium contexts and synthetic data.

MEAL_SAFETY_SOURCE_ROOT points these tests at the pre-correction source for red/green verification.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import phase1_data_safety_browser as t

ROOT=Path(os.environ.get('MEAL_SAFETY_SOURCE_ROOT',Path(__file__).resolve().parents[1]))
t.ROOT=ROOT
t.f.ROOT=ROOT
t.f.HOOK+='''window.correctionTest={adjust:()=>{meals.find(m=>m.id===1).needsTweaking=true;persist()},links:()=>{const meal=meals.find(m=>m.id===1);openRecipeViewer(meal);beginRecipeLinkEdit(recipeViewer,cookingItemTokens(meal).steps[0].token)}};'''


def failed_editor(browser,name):
 c,p,errors,prefix=t.f.setup(browser,name,320)
 p.evaluate('safetyTest.editor()')
 p.locator('#name').fill('First failed draft')
 t.fail_writes(p,['mealRotationDataV1'],True)
 p.locator('#save').click()
 p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click()
 expect(p.locator('#mealSaveWarning')).to_be_visible()
 return c,p,errors,prefix


def unsafe_backup(browser,name):
 c,p,errors,prefix,_=t.bare(browser,name,{'mealRotationDataV1':'{original unreadable','mealRotationSelectedIngredientsV1':'{recoverable original selections'})
 before=t.native(p,prefix)
 backup={'version':2,**t.CORE,'storage':{'mealRotationDataV1':json.dumps(t.CORE),'mealRotationSelectedIngredientsV1':'[]'}}
 with p.expect_file_chooser() as fc:p.locator('#mealDataRecovery').get_by_role('button',name='Restore Backup',exact=True).click()
 fc.value.set_files({'name':'invalid-selection-backup.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
 p.wait_for_function('''({key,original})=>document.getElementById('mealRecoveryStatus')?.textContent.includes('not restored')||localStorage.getItem(key)!==original''',arg={'key':prefix+'mealRotationDataV1','original':'{original unreadable'})
 assert t.native(p,prefix)==before,'invalid replacement overwrote original raw records'
 expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored')
 assert not errors,errors
 c.close()


def latest_editor_retry(browser,name):
 c,p,errors,prefix=failed_editor(browser,name)
 p.locator('#name').fill('LATEST unsaved draft');p.evaluate('window.retryNavigationSentinel=42')
 p.evaluate('restoreSafetyWrites()')
 p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click()
 p.wait_for_function('''key=>!document.querySelector('#editor .editor')||JSON.parse(localStorage.getItem(key)).meals.some(m=>m.id===1&&m.name==='LATEST unsaved draft')''',arg=prefix+'mealRotationDataV1')
 saved=json.loads(p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationDataV1'))
 assert next(m for m in saved['meals'] if m['id']==1)['name']=='LATEST unsaved draft','Retry Save committed stale editor data'
 assert p.evaluate('window.retryNavigationSentinel')==42,'editor retry must not reload'
 assert not errors,errors
 c.close()


def complete_export(browser,name):
 c,p,errors,prefix=failed_editor(browser,name)
 p.locator('#name').fill('LATEST export draft')
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 exported=json.loads(Path(dl.value.path()).read_text())
 text=json.dumps(exported)
 assert 'First failed draft' in text,'failed transaction proposal is absent from recovery export'
 assert 'LATEST export draft' in text,'current editor draft is absent from recovery export'
 assert exported['failedTransactions'] and exported['editorDrafts']
 saved=json.loads(exported['storage']['mealRotationDataV1'])
 assert next(m for m in saved['meals'] if m['id']==1)['name']!='First failed draft'
 assert p.locator('#name').input_value()=='LATEST export draft' and not errors,errors
 c.close()


def background_warning(browser,name):
 c,p,errors,prefix=failed_editor(browser,name)
 p.evaluate('restoreSafetyWrites();window.dispatchEvent(new Event("pagehide"))')
 expect(p.locator('#mealSaveWarning')).to_be_visible()
 assert p.locator('#name').input_value()=='First failed draft'
 assert p.evaluate('''()=>{const event=new Event('beforeunload',{cancelable:true});window.dispatchEvent(event);return event.defaultPrevented}'''),'unresolved failure lost close protection'
 assert not errors,errors
 c.close()


def weekday_colors(browser,name):
 original='not-json'
 c,p,errors,prefix,_=t.bare(browser,name,{'mealRotationDataV1':json.dumps(t.CORE),'mealRotationWeekdayColorsV1':original})
 expect(p.locator('#mealDataRecovery')).to_be_visible()
 assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationWeekdayColorsV1')==original
 assert not errors,errors
 c.close()



def structured_registry(browser,name):
 invalid={
  'mealRotationCategoryColorsV1':'false','mealRotationTimeVisibilityV1':'not-json',
  'mealRotationRecipeViewPrefsV1':'[]','mealRotationEditorSectionsV1':'false',
  'mealRotationMakeAheadDisplayV1':'{"showMakeAheadReminders":"true"}',
  'mealRotationGroupSectionExpansionV1':'{"version":1,"groups":[]}',
  'mealRotationMasterGroceryExcludedPlansV1':'{}','mealRotationMasterGroceryExcludedMealsV1':'false',
  'mealRotationLastTopMealIdsV1:original':'{}','mealRotationWeekdayColorsV1':'{"Monday":false}',
  'mealRotationCookingTimerV1':'{"version":1,"status":"running","deadline":"bad"}',
  'mealRotationWeekdayRecipeFiltersV1':'{"Monday::Legacy":"tag"}',
 }
 for key,value in invalid.items():
  c,p,errors,prefix,_=t.bare(browser,name,{'mealRotationDataV1':json.dumps(t.CORE),key:value})
  expect(p.locator('#mealDataRecovery')).to_be_visible()
  assert p.evaluate('k=>localStorage.getItem(k)',prefix+key)==value and not errors,errors
  c.close()
 valid={'mealRotationDataV1':json.dumps(t.CORE),'mealRotationWeekdayCategoriesV1':'{"Monday":"Legacy"}','mealRotationTopCountsV1':'{"Legacy":"2"}','mealRotationTimeVisibilityV1':'null','mealRotationMasterGroceryExcludedPlansV1':'[2,"legacy-plan"]','mealRotationRecipeViewPrefsV1':'null','mealRotationEditorSectionsV1':'null','mealRotationCookingTimerV1':'null','mealRotationGroupSectionExpansionV1':'null','mealRotationTextSizeV1':'large','mealRotationShowLastCookedV1':'false','mealRotationShowPlanTabsV1':'true','mealRotationStartWeekdayV1':'Sunday','mealRotationCustomSettingV9':'{opaque extension value'}
 c,p,errors,prefix,_=t.bare(browser,name,valid)
 assert not p.locator('#mealDataRecovery').count(),p.locator('body').inner_text()
 for key in ['mealRotationTextSizeV1','mealRotationShowLastCookedV1','mealRotationShowPlanTabsV1','mealRotationStartWeekdayV1','mealRotationCustomSettingV9']:assert p.evaluate('k=>localStorage.getItem(k)',prefix+key)==valid[key]
 assert not errors,errors
 c.close()


def upload_backup(p,backup):
 # Native file pickers require the recovery page to own browser focus.
 p.bring_to_front()
 with p.expect_file_chooser() as fc:p.locator('#mealDataRecovery').get_by_role('button',name='Restore Backup',exact=True).click()
 fc.value.set_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})


def recovery_journal(browser,name):
 originals={'mealRotationDataV1':'{original corrupt','mealRotationSelectedIngredientsV1':'{original selection'}
 backup={'version':2,**t.CORE,'storage':{'mealRotationDataV1':json.dumps(t.CORE),'mealRotationSelectedIngredientsV1':'{}'}}
 # Failure to secure a journal must precede all replacement mutations.
 c,p,errors,prefix,_=t.bare(browser,name,originals)
 before=t.native(p,prefix);t.fail_writes(p,['mealRotationRecoveryJournalV1'],True);upload_backup(p,backup)
 expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored')
 assert t.native(p,prefix)==before
 p.evaluate('restoreSafetyWrites()');c.close()
 # Retain the journal across an injected interruption after writing, before reload.
 c,p,errors,prefix,_=t.bare(browser,name,originals)
 source=(ROOT/name).read_text().replace('  reload();\n }\n function finishStartup()', '  window.replacementWritten=true;\n }\n function finishStartup()',1)
 assert 'window.replacementWritten=true' in source
 route='http://safety.test/**'
 p.unroute(route);p.route(route,lambda r:r.fulfill(content_type='text/html',body=source) if r.request.url.endswith(name) else r.fulfill(body=''))
 p.reload();upload_backup(p,backup);p.wait_for_function('window.replacementWritten===true')
 journal=json.loads(p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1'))
 assert journal['originalStorage']==originals
 # Simulate a startup error: old bytes must still be exportable after navigation.
 broken=(ROOT/name).read_text().replace('const mealBulkStorageBase=mealPersistence.storage;',"mealPersistence.finishStartup=()=>{throw Error('Injected startup interruption')};const mealBulkStorageBase=mealPersistence.storage;",1)
 p.unroute(route);p.route(route,lambda r:r.fulfill(content_type='text/html',body=broken) if r.request.url.endswith(name) else r.fulfill(body=''))
 p.reload();expect(p.locator('#mealDataRecovery')).to_be_visible()
 with p.expect_download() as dl:p.locator('#mealDataRecovery').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 exported=json.loads(Path(dl.value.path()).read_text());assert exported['originalStorage']==originals
 assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1')
 normal=(ROOT/name).read_text();p.unroute(route);p.route(route,lambda r:r.fulfill(content_type='text/html',body=normal) if r.request.url.endswith(name) else r.fulfill(body=''))
 p.reload();assert not p.locator('#mealDataRecovery').count();assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1') is None
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='PRODUCTION SENTINEL'
 assert not errors,errors
 c.close()


def cancellation_and_supersession(browser,name):
 c,p,errors,prefix=failed_editor(browser,name)
 p.locator('#name').fill('LATEST directly saved draft');p.evaluate('restoreSafetyWrites();window.dispatchEvent(new Event("pagehide"))')
 expect(p.locator('#mealSaveWarning')).to_be_visible()
 p.locator('#save').click();expect(p.locator('#mealSaveWarning')).to_have_count(0)
 assert next(m for m in t.f.state(p)['meals'] if m['id']==1)['name']=='LATEST directly saved draft' and not errors,errors
 c.close()
 c,p,errors,prefix=failed_editor(browser,name);p.evaluate('restoreSafetyWrites()');p.locator('#cancel').click()
 expect(p.locator('#mealSaveWarning')).to_have_count(0)
 assert next(m for m in t.f.state(p)['meals'] if m['id']==1)['name']!='First failed draft'
 p.evaluate('window.dispatchEvent(new Event("pagehide"))');assert not p.locator('#mealSaveWarning').count() and not errors,errors
 c.close()


def bulk_and_open_drafts(browser,name):
 c,p,errors,prefix=t.f.setup(browser,name,320);t.fail_writes(p,['mealRotationDataV1'],True)
 try:p.evaluate('safetyTest.bulk()');raise AssertionError('Expected injected bulk failure')
 except Exception as e:assert 'Injected quota failure' in str(e),e
 p.evaluate('restoreSafetyWrites();window.dispatchEvent(new Event("pagehide"))');expect(p.locator('#mealSaveWarning')).to_be_visible()
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 export=json.loads(Path(dl.value.path()).read_text());proposal=export['failedTransactions'][0]['proposals'][-1]['storage'];assert next(m for m in json.loads(proposal['mealRotationDataV1'])['meals'] if m['id']==1)['favorite']
 p.evaluate('safetyTest.editor()');p.locator('#name').fill('New work must not be discarded')
 saved=t.native(p,prefix);p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_contain_text('editor');assert p.locator('#name').input_value()=='New work must not be discarded' and t.native(p,prefix)==saved
 p.locator('#cancel').click();p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_have_count(0)
 assert next(m for m in t.f.state(p)['meals'] if m['id']==1)['favorite'] and not errors,errors
 c.close()


def multiple_pending_and_nested_export(browser,name):
 c,p,errors,prefix=failed_editor(browser,name)
 p.locator('#name').fill('Newer export draft');p.get_by_text('Timing',exact=True).click();p.locator('#prep').fill('invalid raw time')
 p.evaluate('restoreSafetyWrites()')
 # A different failed ordinary save must not hide the failed transaction.
 t.fail_writes(p,['mealRotationTextSizeV1']);p.evaluate('safetyTest.preferences()');p.evaluate('restoreSafetyWrites()')
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 exported=json.loads(Path(dl.value.path()).read_text());assert exported['unsaved']['mealRotationTextSizeV1']=='large';assert 'invalid raw time' in json.dumps(exported['editorDrafts']) and 'First failed draft' in json.dumps(exported['failedTransactions'])
 p.locator('#cancel').click();expect(p.locator('#mealSaveWarning')).to_be_visible()
 p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_have_count(0)
 assert not errors,errors;c.close()



def interrupted_retry_and_rollback(browser,name):
 c,p,errors,prefix=t.f.setup(browser,name,320);t.fail_writes(p);p.evaluate('safetyTest.preferences();mealBulkStorageBase.setItem("mealRotationTextSizeV1","extra");mealBulkStorageBase.setItem("mealRotationShowLastCookedV1","false")');p.evaluate('restoreSafetyWrites()');t.fail_writes(p,['mealRotationShowLastCookedV1'],True)
 p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_be_visible()
 assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationTextSizeV1')=='extra'
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 export=json.loads(Path(dl.value.path()).read_text());assert export['storage']['mealRotationTextSizeV1']=='extra' and export['unsaved']['mealRotationShowLastCookedV1']=='false'
 p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_have_count(0)
 assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationShowLastCookedV1')=='false' and not errors,errors;c.close()
 # Fail the primary commit and then its rollback writes, leaving dependent keys partially persisted.
 c,p,errors,prefix=t.f.setup(browser,name,320);p.evaluate('safetyTest.editor()');p.locator('#name').fill('Failed rollback draft');p.locator('#rotation').uncheck();before=t.native(p,prefix)
 p.evaluate('''()=>{const native=Storage.prototype.setItem;let rollback=false;Storage.prototype.setItem=function(k,v){if(k.endsWith('mealRotationDataV1'))rollback=true;if(rollback)throw Error('Injected commit and rollback failure');return native.call(this,k,v)};window.restoreRollbackWrites=()=>{Storage.prototype.setItem=native}}''')
 p.locator('#save').click();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();expect(p.locator('#mealSaveWarning')).to_be_visible()
 p.locator('#name').fill('LATEST after rollback failure')
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 export=json.loads(Path(dl.value.path()).read_text());assert export['failedTransactions'] and export['unsaved'];assert export['originalStorage']['mealRotationDataV1']==before[prefix+'mealRotationDataV1'];assert 'LATEST after rollback failure' in json.dumps(export['editorDrafts'])
 p.evaluate('restoreRollbackWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_have_count(0)
 record=next(m for m in t.f.state(p)['meals'] if m['id']==1);assert record['name']=='LATEST after rollback failure' and record['rotation'] is False and not errors,errors;c.close()


def partial_read_and_nested_drafts(browser,name):
 c,p,errors,prefix,_=t.bare(browser,name,{'mealRotationDataV1':json.dumps(t.CORE),'mealRotationTextSizeV1':'large'},True)
 with p.expect_download() as dl:p.locator('#mealDataRecovery').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 export=json.loads(Path(dl.value.path()).read_text());assert export['storage']['mealRotationTextSizeV1']=='large' and 'mealRotationDataV1' in export['unreadableKeys'];assert export['readError'] and not errors,errors;c.close()
 c,p,errors,prefix=failed_editor(browser,name);p.get_by_text('Organization',exact=True).click();p.locator('#serveWith').click();dialog=p.get_by_role('dialog',name='Serve with',exact=True);dialog.get_by_label('Custom Serve with keyword').fill('UNSAVED nested term')
 # The nested modal owns focus; invoke the existing warning handlers to check their safeguards and snapshot coverage.
 p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).evaluate('(b)=>b.onclick()');expect(p.locator('#mealSaveWarning')).to_contain_text('open dialog');assert p.locator('#name').input_value()=='First failed draft'
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).evaluate('(b)=>b.onclick()')
 export=json.loads(Path(dl.value.path()).read_text());assert 'UNSAVED nested term' in json.dumps(export['editorDrafts']) and 'First failed draft' in json.dumps(export['failedTransactions'])
 dialog.get_by_role('button',name='Cancel Serve with',exact=True).click();p.locator('#cancel').click();assert not errors,errors;c.close()


def confirmation_and_live_recovery(browser,name):
 c,p,errors,prefix=t.f.setup(browser,name,320);p.evaluate('correctionTest.adjust();safetyTest.editor()');p.locator('#name').fill('Before confirmation');p.get_by_text('Notes & Reminders',exact=True).click();p.locator('#editNeedsTweaking').evaluate('(el)=>el.checked=false');p.locator('#save').click()
 dialog=p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True);expect(dialog).to_be_visible();p.locator('#name').evaluate("el=>{el.value='LATEST during confirmation';el.dispatchEvent(new Event('input',{bubbles:true}))}");dialog.get_by_role('button',name='Confirm removal',exact=True).click()
 expect(p.get_by_role('alertdialog')).to_contain_text('draft changed');p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();assert p.locator('#name').input_value()=='LATEST during confirmation'
 p.locator('#save').click();expect(p.locator('#editor .editor')).to_have_count(0);assert next(m for m in t.f.state(p)['meals'] if m['id']==1)['name']=='LATEST during confirmation' and not errors,errors;c.close()
 # A read failure with a live draft must not allow replacement until explicit draft cancellation.
 c,p,errors,prefix=failed_editor(browser,name);p.locator('#name').fill('LATEST before live recovery');p.evaluate('restoreSafetyWrites()');before=t.native(p,prefix)
 p.evaluate("""()=>{const get=Storage.prototype.getItem;window.restoreLiveReads=()=>{Storage.prototype.getItem=get};Storage.prototype.getItem=function(k){if(k.endsWith('mealRotationWeekdayColorsV1'))throw Error('Injected live read failure');return get.call(this,k)};mealBulkStorageBase.getItem('mealRotationWeekdayColorsV1')}""")
 expect(p.locator('#mealDataRecovery')).to_be_visible();p.evaluate('restoreLiveReads()')
 with p.expect_download() as dl:p.locator('#mealDataRecovery').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 assert 'LATEST before live recovery' in Path(dl.value.path()).read_text()
 backup={'version':2,**t.CORE,'storage':{'mealRotationDataV1':json.dumps(t.CORE)}};upload_backup(p,backup);expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored');assert t.native(p,prefix)==before
 p.locator('#mealDataRecovery').get_by_role('button',name='Cancel Open Drafts',exact=True).click();p.get_by_role('button',name='Keep Open Drafts',exact=True).click();assert p.locator('#editor .editor').count()
 p.locator('#mealDataRecovery').get_by_role('button',name='Cancel Open Drafts',exact=True).click();p.get_by_role('button',name='Confirm Cancel Drafts',exact=True).click();assert not p.locator('#editor .editor').count() and t.native(p,prefix)==before
 upload_backup(p,backup);p.wait_for_function('!document.getElementById("mealDataRecovery")');assert not errors,errors;c.close()
 # Link-edit selection uses a Set in memory; recovery export must serialize its tokens.
 c,p,errors,prefix=t.f.setup(browser,name,320);t.fail_writes(p);p.evaluate('safetyTest.preferences();correctionTest.links()')
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).evaluate('(b)=>b.onclick()')
 export=json.loads(Path(dl.value.path()).read_text());view=next(d for d in export['editorDrafts'] if d['kind']=='recipe-viewer');assert isinstance(view['data']['ingredientLinkDraft']['selected'],list) and view['data']['ingredientLinkDraft']['step']
 assert not errors,errors;c.close()

EXTRA_CASES=[structured_registry,recovery_journal,cancellation_and_supersession,bulk_and_open_drafts,multiple_pending_and_nested_export,interrupted_retry_and_rollback,partial_read_and_nested_drafts,confirmation_and_live_recovery]

REPRODUCTIONS=[unsafe_backup,latest_editor_retry,complete_export,background_warning,weekday_colors]


def run_all():
 failures=[]
 baseline=os.environ.get('MEAL_SAFETY_EXPECT_BASELINE_FAILURES')=='1'
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for case in REPRODUCTIONS:
    try:case(b,name)
    except Exception as error:
     failures.append((name,case.__name__))
     print(('EXPECTED BASELINE FAILURE' if baseline else 'FAIL'),name,case.__name__,str(error).splitlines()[0],flush=True)
     if not baseline:raise
    else:
     print('PASS',name,case.__name__,flush=True)
   if not baseline:
    for case in EXTRA_CASES:
     case(b,name);print('PASS',name,case.__name__,flush=True)
   # Each failed case has an isolated profile; release it before the next app.
   for context in b.contexts:context.close()
  b.close()
 if baseline:assert len(failures)==10,failures
 else:assert not failures,failures
if __name__=='__main__':run_all()

