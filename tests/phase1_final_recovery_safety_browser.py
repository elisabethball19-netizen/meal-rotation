"""Final Phase 1 review regressions. Synthetic data; disposable Chromium profiles only.

MEAL_FINAL_SOURCE_ROOT selects the pre-fix apps for red/green verification.
MEAL_FINAL_EXPECT_FAILURES=1 expects all four review reproductions to fail per app.
"""
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import phase1_safety_corrections_browser as s

t=s.t
ROOT=Path(os.environ.get('MEAL_FINAL_SOURCE_ROOT',Path(__file__).resolve().parents[1]))
s.ROOT=ROOT;t.ROOT=ROOT;t.f.ROOT=ROOT
t.f.HOOK+='window.finalRecoveryTest={label:()=>applyRecipeBulk(["1"],{addLabels:["UNRELATED SUCCESS"]}),favorite:()=>applyRecipeBulk(["1"],{favorite:true})};'


def download_recovery(p):
 with p.expect_download() as dl:p.locator('#mealDataRecovery').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 return json.loads(Path(dl.value.path()).read_text())


def backup():
 return {'version':2,**t.CORE,'storage':{'mealRotationDataV1':json.dumps(t.CORE)}}


def unreadable_original(browser,name):
 originals={'mealRotationDataV1':json.dumps(t.CORE),'mealRotationTextSizeV1':'large'}
 c,p,errors,prefix,_=t.bare(browser,name,originals,True);before=t.native(p,prefix)
 s.upload_backup(p,backup());expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored')
 assert p.evaluate('k=>originalSafetyGet.call(localStorage,k)',prefix+'mealRotationDataV1')==originals['mealRotationDataV1'],'restore destroyed unreadable primary'
 assert t.native(p,prefix)==before,'replacement mutated storage without a complete original snapshot'
 assert 'Original records were restored' not in p.locator('#mealRecoveryStatus').inner_text()
 assert not errors,errors;c.close()


def incomplete_replacement(browser,name):
 old=json.dumps(t.CORE);replacement={**t.CORE,'meals':[{**t.CORE['meals'][0],'name':'BACKUP REPLACEMENT'}]}
 originals={'mealRotationDataV1':old,'mealRotationWeekdayColorsV1':'not-json','mealRotationSelectedIngredientsV1':'{"1":["ORIGINAL SELECTION"]}'}
 intended={'mealRotationDataV1':json.dumps(replacement),'mealRotationWeekdayColorsV1':'{"Monday":"#112233"}','mealRotationSelectedIngredientsV1':'{"1":["BACKUP SELECTION"]}'}
 journal={'version':1,'originalStorage':originals,'beforeReplacement':originals,'replacement':intended,'pendingWrites':{},'failedTransactions':[],'editorDrafts':[]}
 partial={**intended,'mealRotationDataV1':old,'mealRotationRecoveryJournalV1':json.dumps(journal)}
 c,p,errors,prefix,_=t.bare(browser,name,partial);expect(p.locator('#mealDataRecovery')).to_be_visible()
 assert t.native(p,prefix)=={prefix+k:v for k,v in partial.items()},'startup rewrote incomplete replacement or removed its journal'
 export=download_recovery(p);assert export['originalStorage']==originals and export['recoveryJournal']['replacement']==intended
 assert not errors,errors;c.close()


def repeated_recovery(browser,name):
 c,p,errors,prefix=t.f.setup(browser,name,320)
 t.fail_writes(p,['mealRotationTextSizeV1']);p.evaluate('mealBulkStorageBase.setItem("mealRotationTextSizeV1","UNIQUE_PENDING_REAL")');p.evaluate('restoreSafetyWrites()')
 p.evaluate('prefix=>{localStorage.setItem(prefix+"mealRotationWeekdayColorsV1","not-json");mealPersistence.failStartup(Error("Injected runtime invalid record"))}',prefix)
 t.fail_writes(p,['mealRotationDataV1'],True);s.upload_backup(p,backup());expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored');p.evaluate('restoreSafetyWrites()')
 journal_key=prefix+'mealRotationRecoveryJournalV1';first=p.evaluate('k=>localStorage.getItem(k)',journal_key);assert 'UNIQUE_PENDING_REAL' in first
 p.reload();expect(p.locator('#mealDataRecovery')).to_be_visible();assert p.evaluate('k=>localStorage.getItem(k)',journal_key)==first
 t.fail_writes(p,['mealRotationDataV1'],True);s.upload_backup(p,backup());expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored')
 export=download_recovery(p);assert 'UNIQUE_PENDING_REAL' in json.dumps(export),'second failed restore erased earlier pending changes'
 p.evaluate('restoreSafetyWrites()');p.reload();expect(p.locator('#mealDataRecovery')).to_be_visible();assert 'UNIQUE_PENDING_REAL' in json.dumps(download_recovery(p))
 assert not errors,errors;c.close()


def unrelated_operation(browser,name):
 c,p,errors,prefix=t.f.setup(browser,name,320);t.fail_writes(p,['mealRotationDataV1'],True)
 try:p.evaluate('safetyTest.bulk()');raise AssertionError('Expected injected failure')
 except Exception as e:assert 'Injected quota failure' in str(e),e
 p.evaluate('restoreSafetyWrites();finalRecoveryTest.label()')
 expect(p.locator('#mealSaveWarning')).to_be_visible()
 record=next(m for m in t.f.state(p)['meals'] if m['id']==1);assert not record.get('favorite') and 'UNRELATED SUCCESS' in record['labels']
 assert p.evaluate('mealPersistence.unsaved'),'unrelated success lost close protection'
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 export=json.loads(Path(dl.value.path()).read_text());assert export['failedTransactions']
 # Repeating the actual failed operation may resolve it, preserving the other change.
 p.evaluate('finalRecoveryTest.favorite()');expect(p.locator('#mealSaveWarning')).to_have_count(0)
 record=next(m for m in t.f.state(p)['meals'] if m['id']==1);assert record['favorite'] and 'UNRELATED SUCCESS' in record['labels']
 p.reload();assert next(m for m in t.f.state(p)['meals'] if m['id']==1)['favorite']
 assert not errors,errors;c.close()


def unreadable_snapshot_edges(browser,name):
 originals={'mealRotationDataV1':json.dumps(t.CORE),'mealRotationWeekdayColorsV1':'not-json','mealRotationSelectedIngredientsV1':'{}'}
 for blocked in ['mealRotationSelectedIngredientsV1','mealRotationRecoveryJournalV1','enumeration']:
  c,p,errors,prefix,_=t.bare(browser,name,originals);before=t.native(p,prefix)
  p.evaluate("""blocked=>{const get=Storage.prototype.getItem,key=Storage.prototype.key,wrapper=typeof testStorage==='undefined'?null:testStorage,wrapperKey=wrapper?.key;window.restoreFinalReads=()=>{Storage.prototype.getItem=get;Storage.prototype.key=key;if(wrapper)wrapper.key=wrapperKey};Storage.prototype.getItem=function(k){if(k.endsWith(blocked))throw Error('Injected required read failure');return get.call(this,k)};if(blocked==='enumeration'){const fail=()=>{throw Error('Injected enumeration failure')};if(wrapper)wrapper.key=fail;else Storage.prototype.key=fail}}""",blocked)
  s.upload_backup(p,backup());expect(p.locator('#mealRecoveryStatus')).to_contain_text('No replacement was attempted');assert t.native(p,prefix)==before
  p.locator('#mealDataRecovery').get_by_role('button',name='Start Fresh',exact=True).click();p.get_by_role('button',name='Confirm Start Fresh',exact=True).click();expect(p.locator('#mealRecoveryStatus')).to_contain_text('Start Fresh could not finish')
  # Explicit destruction no longer requires a readable snapshot. Enumeration fails before
  # deletion; denied verification reads may fail after deletion and must report that honestly.
  assert t.native(p,prefix)==(before if blocked=='enumeration' else {})
  p.evaluate('restoreFinalReads()');s.upload_backup(p,backup());p.wait_for_function('!document.getElementById("mealDataRecovery")');assert not errors,errors;c.close()
 # The journal must remain exportable even if a different app record is denied at startup.
 journal={'version':1,'originalStorage':{'mealRotationDataV1':'ORIGINAL JOURNALED BYTES'},'replacement':{},'editorDrafts':[{'raw':'EARLIER RAW DRAFT'}]}
 c,p,errors,prefix,_=t.bare(browser,name,{'mealRotationDataV1':json.dumps(t.CORE),'mealRotationRecoveryJournalV1':json.dumps(journal)},True)
 export=download_recovery(p);assert export['recoveryJournal']==journal and export['originalStorage']==journal['originalStorage'];assert not errors,errors;c.close()


def journal_history(browser,name):
 originals={'mealRotationDataV1':'{original corrupt'}
 first={'version':1,'originalStorage':originals,'replacement':{'mealRotationDataV1':json.dumps(t.CORE)},'pendingWrites':{'mealRotationTextSizeV1':'FIRST PENDING'},'failedTransactions':[{'proposal':'FIRST FAILED PROPOSAL'}],'editorDrafts':[{'raw':'FIRST RAW DRAFT'}]}
 second={**first,'pendingWrites':{'mealRotationTextSizeV1':'SECOND PENDING'},'editorDrafts':[{'raw':'SECOND RAW DRAFT'}],'previousAttempts':[first]}
 c,p,errors,prefix,_=t.bare(browser,name,{**originals,'mealRotationRecoveryJournalV1':json.dumps(second)})
 for count in range(2):
  t.fail_writes(p,['mealRotationDataV1'],True);s.upload_backup(p,backup());expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored');p.evaluate('restoreSafetyWrites()')
  export=download_recovery(p);history=export['recoveryJournal']['previousAttempts'];assert len(history)==count+2;assert history[0]==first
  text=json.dumps(export);assert all(marker in text for marker in ['FIRST PENDING','FIRST FAILED PROPOSAL','FIRST RAW DRAFT','SECOND PENDING','SECOND RAW DRAFT'])
  assert export['originalStorage']==originals
  p.reload();expect(p.locator('#mealDataRecovery')).to_be_visible()
 # Optional journaling retries once at quota rather than blocking a valid restore.
 t.fail_writes(p,['mealRotationRecoveryJournalV1'],True);s.upload_backup(p,backup());p.wait_for_function('!document.getElementById("mealDataRecovery")')
 assert json.loads(p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationDataV1'))['meals']==t.CORE['meals']
 assert not errors,errors;c.close()
 # Even malformed journal bytes are archived rather than replaced without a recovery copy.
 c,p,errors,prefix,_=t.bare(browser,name,{**originals,'mealRotationRecoveryJournalV1':'{UNREADABLE OLD JOURNAL'})
 t.fail_writes(p,['mealRotationDataV1'],True);s.upload_backup(p,backup());expect(p.locator('#mealRecoveryStatus')).to_contain_text('not restored')
 assert download_recovery(p)['recoveryJournal']['previousJournalRaw']=='{UNREADABLE OLD JOURNAL';assert not errors,errors;c.close()


def startup_commit_boundaries(browser,name):
 valid={'mealRotationDataV1':json.dumps(t.CORE)}
 # Equality must include removals: an obsolete record means replacement is incomplete.
 for intended,actual in [(valid,{**valid,'mealRotationTextSizeV1':'large'}),({},valid)]:
  journal={'version':1,'originalStorage':valid,'replacement':intended}
  records={**actual,'mealRotationRecoveryJournalV1':json.dumps(journal)}
  c,p,errors,prefix,_=t.bare(browser,name,records);expect(p.locator('#mealDataRecovery')).to_be_visible();assert t.native(p,prefix)=={prefix+k:v for k,v in records.items()};assert not errors,errors;c.close()
 # Complete replacements, including Start Fresh, are accepted before normal startup writes.
 for intended in [valid,{}]:
  journal={'version':1,'originalStorage':{'mealRotationDataV1':'{old corrupt'},'replacement':intended}
  c,p,errors,prefix,_=t.bare(browser,name,{**intended,'mealRotationRecoveryJournalV1':json.dumps(journal)})
  assert not p.locator('#mealDataRecovery').count();assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1') is None;assert not errors,errors;c.close()


def completion_marker_durability(browser,name):
 valid={'mealRotationDataV1':json.dumps(t.CORE)}
 journal={'version':1,'originalStorage':{'mealRotationDataV1':'{OLD RECOVERABLE'},'replacement':valid}
 for failure in ['marker-write','marker-readback','cleanup']:
  c,p,errors,prefix,_=t.bare(browser,name,{'mealRotationDataV1':'{initial corrupt'})
  p.evaluate('a=>{for(const[k,v]of Object.entries(a.records))localStorage.setItem(a.prefix+k,v)}',{'prefix':prefix,'records':{**valid,'mealRotationRecoveryJournalV1':json.dumps(journal)}})
  before=t.native(p,prefix)
  p.add_init_script("""(()=>{const failure="""+json.dumps(failure)+""",set=Storage.prototype.setItem,get=Storage.prototype.getItem,remove=Storage.prototype.removeItem;let journalReads=0;window.restoreCompletionStorage=()=>{Storage.prototype.setItem=set;Storage.prototype.getItem=get;Storage.prototype.removeItem=remove};Storage.prototype.setItem=function(k,v){if(failure==='marker-write'&&k.endsWith('mealRotationRecoveryJournalV1'))throw Error('Injected marker write failure');return set.call(this,k,v)};Storage.prototype.getItem=function(k){if(k.endsWith('mealRotationRecoveryJournalV1')&&++journalReads===2&&failure==='marker-readback')throw Error('Injected marker readback failure');return get.call(this,k)};Storage.prototype.removeItem=function(k){if(failure==='cleanup'&&k.endsWith('mealRotationRecoveryJournalV1'))throw Error('Injected cleanup failure');return remove.call(this,k)}})()""")
  p.reload()
  if failure=='cleanup':
   expect(p.locator('#mealSaveWarning')).to_be_visible();assert not p.locator('#mealDataRecovery').count()
   saved=p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1');assert json.loads(saved)['replacementCommitted'] is True
   # Normal startup has added records; a verified commit must still be recognized next launch.
   p.reload();expect(p.locator('#mealSaveWarning')).to_be_visible();assert not p.locator('#mealDataRecovery').count()
   p.evaluate('restoreCompletionStorage()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();expect(p.locator('#mealSaveWarning')).to_have_count(0);assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1') is None
  else:
   assert not p.locator('#mealDataRecovery').count()
   assert p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationRecoveryJournalV1') is None
   p.evaluate('restoreCompletionStorage()');p.reload();assert not p.locator('#mealDataRecovery').count()
  assert not errors,errors;c.close()


EXTRA_CASES=[unreadable_snapshot_edges,journal_history,startup_commit_boundaries,completion_marker_durability]


REPRODUCTIONS=[unreadable_original,incomplete_replacement,repeated_recovery,unrelated_operation]

if __name__=='__main__':
 expected=os.environ.get('MEAL_FINAL_EXPECT_FAILURES')=='1';failures=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for case in REPRODUCTIONS:
    try:case(b,name)
    except Exception as e:
     failures.append((name,case.__name__));print('EXPECTED FAILURE' if expected else 'FAIL',name,case.__name__,str(e).splitlines()[0],flush=True)
     if not expected:raise
    else:print('PASS',name,case.__name__,flush=True)
   if not expected:
    for case in EXTRA_CASES:
     case(b,name);print('PASS',name,case.__name__,flush=True)
   for context in b.contexts:context.close()
  b.close()
 assert len(failures)==8 if expected else not failures,failures
