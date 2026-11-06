"""Optional image failures must not prevent recipe use, recovery or old backups."""
import copy,json,base64
from pathlib import Path
from playwright.sync_api import sync_playwright
import phase2_stage5_photos_browser as f
f.t.stage.f.HOOK += '''window.photoSafety={
 compress:file=>recipePhotoStorage.compress(file),
 cancelWrite:()=>{const native=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){const r=native.apply(this,args);if(this.name==='photos')setTimeout(()=>document.querySelector('[data-photo-editor] button:last-child')?.click(),0);return r};window.restorePhotoWrites=()=>{IDBObjectStore.prototype.put=native}},
 delayWrite:()=>{const native=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){const r=native.apply(this,args);if(this.name==='photos'){window.photoWriteObserved=true;const tx=this.transaction,done=tx.oncomplete;tx.oncomplete=e=>setTimeout(()=>done?.(e),600)}return r};window.restorePhotoWrites=()=>{IDBObjectStore.prototype.put=native}},
 failWrite:mode=>{const native=IDBObjectStore.prototype.put;IDBObjectStore.prototype.put=function(...args){if(this.name==='photos'){if(mode==='abort'){const r=native.apply(this,args);this.transaction.abort();return r}throw new DOMException('Synthetic photo quota','QuotaExceededError')}return native.apply(this,args)};window.restorePhotoWrites=()=>{IDBObjectStore.prototype.put=native}},
 deny:()=>{Object.defineProperty(window,'indexedDB',{configurable:true,get(){throw new Error('Synthetic unavailable photo database')}})},
 urls:()=>recipePhotoURLs.size,
 reference:(id,ref)=>{meals.find(m=>m.id===id).recipePhotoId=ref;persist()},
 late:()=>{meals.find(m=>m.id===1).notes='Later recipe edit';stage4Final.late();persist()},
 raw:id=>new Promise((resolve,reject)=>{const r=indexedDB.open(recipePhotoStorage.name,1);r.onsuccess=()=>{const db=r.result,tx=db.transaction('photos','readonly'),q=tx.objectStore('photos').get(id);q.onsuccess=()=>resolve(!!q.result);q.onerror=reject;tx.oncomplete=()=>db.close()};r.onerror=reject})
};'''
def assert_clean(p,before):
 actual=f.without_photos(f.state(p));expected=f.without_photos(before)
 assert actual==expected,{k:{'before':expected[k],'after':actual[k]} for k in actual if actual[k]!=expected[k]}
def cancel_dialog(p):p.get_by_role('dialog',name='Recipe photo',exact=True).get_by_role('button',name='Cancel photo change',exact=True).click()
def recover_download(p):
 with p.expect_download() as dl:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 return json.loads(Path(dl.value.path()).read_text())
def failures(b,name):
 c,p,e,prefix=f.setup(b,name,280);f.open_view(p);f.upload(p);old=f.refs(p)[1];before=f.state(p)
 for mode in ['quota','abort']:
  p.evaluate('photoSafety.failWrite',mode);f.upload(p,f.B,False);assert f.refs(p)[1]==old;assert_clean(p,before);p.evaluate('restorePhotoWrites()');cancel_dialog(p);assert p.evaluate('photoTest.image',old)
 # A committed blob with a delayed acknowledgement must not publish after Cancel.
 p.evaluate('photoSafety.delayWrite()');d=f.photo_dialog(p);d.locator('input[type=file]').set_input_files(str(f.B));p.wait_for_function('window.photoWriteObserved');d.get_by_role('button',name='Cancel photo change',exact=True).click();p.wait_for_timeout(750);p.evaluate('restorePhotoWrites()');assert f.refs(p)[1]==old;assert_clean(p,before)
 # Reload after a real image transaction starts must also leave the original reference.
 p.evaluate('window.photoWriteObserved=false;photoSafety.delayWrite()');d=f.photo_dialog(p);d.locator('input[type=file]').set_input_files(str(f.B));p.wait_for_function('window.photoWriteObserved');p.reload();assert f.refs(p)[1]==old;assert_clean(p,before);f.open_view(p)
 # LocalStorage failure after the image is durable retains the old core and exports the proposal.
 native=f.safety.native(p,prefix);f.safety.fail_writes(p,['mealRotationDataV1']);f.upload(p,f.B,False);assert f.refs(p)[1]==old;assert f.safety.native(p,prefix)==native;assert p.locator('#mealSaveWarning').is_visible();recovery=recover_download(p);assert len(recovery['photos']['items'])==2;assert recovery['failedTransactions'];assert any(tx['kind']=='recipe-photo' for tx in recovery['failedTransactions']);p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('!document.querySelector("[data-photo-editor]")');new=f.refs(p)[1];assert new!=old;assert_clean(p,before)
 # Removal also uses the existing recoverable core transaction.
 f.safety.fail_writes(p,['mealRotationDataV1']);d=f.photo_dialog(p);d.get_by_role('button',name='Remove photo',exact=True).click();assert f.refs(p)[1]==new;assert p.locator('#mealSaveWarning').is_visible();p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert f.refs(p)[1] is None;assert_clean(p,before)
 # Photo-only Undo preserves later shopping, cooking, scales and recipe definitions.
 f.close_view(p);p.evaluate('photoSafety.late();stage3Test.grocery()');checkbox=p.locator('.master-grocery-item input[type=checkbox]').first;checkbox.set_checked(not checkbox.is_checked());late=f.state(p);p.locator('#undo').click();assert f.refs(p)[1]==new;assert_clean(p,late);p.locator('#redo').click();assert f.refs(p)[1] is None;assert_clean(p,late);p.locator('#undo').click();assert f.refs(p)[1]==new;assert_clean(p,late);f.safety.fail_writes(p,['mealRotationDataV1']);p.locator('#redo').click();assert f.refs(p)[1]==new;assert_clean(p,late);assert p.locator('#mealSaveWarning').is_visible();p.evaluate('restoreSafetyWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();assert f.refs(p)[1] is None;assert_clean(p,late);p.locator('#undo').click();assert f.refs(p)[1]==new;p.reload();assert f.refs(p)[1]==new;assert_clean(p,late);assert not e,e;c.close();print('PASS',name,'quota/aborted/interrupted writes, Cancel, durable reference rollback, recovery photos, Retry attachment/removal and scoped Undo after later edits',flush=True)
def unavailable(b,name):
 c,p,e,_=f.setup(b,name,280);before=f.state(p);p.evaluate('photoSafety.deny()');f.open_view(p);f.upload(p,success=False);assert f.refs(p)[1] is None;assert f.state(p)==before;cancel_dialog(p)
 # Ordinary lightweight editing and core exports remain available without IndexedDB.
 p.get_by_role('button',name='Edit Recipe',exact=True).click();d=p.get_by_role('dialog',name='Edit Recipe',exact=True);d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Ordinary save without photos');d.get_by_role('button',name='Save recipe',exact=True).click();assert next(m for m in f.state(p)['meals'] if m['id']==1)['notes']=='Ordinary save without photos';data=f.backup_ui(p);assert 'photos' not in data
 # Restore a valid photo-less v2 backup while storage is denied.
 f.restore_ui(p,data);assert next(m for m in f.state(p)['meals'] if m['id']==1)['notes']=='Ordinary save without photos'
 f.open_view(p);f.upload(p);ref=f.refs(p)[1];saved=f.state(p);p.evaluate('photoTest.clear()');p.add_init_script("Object.defineProperty(window,'indexedDB',{configurable:true,get(){throw Error('Unavailable photo storage after reload')}})");p.reload();f.open_view(p);assert p.locator('.recipe-photo-placeholder').is_visible();p.evaluate('photoSafety.deny()');data=f.backup_ui(p);assert data['photos']['missing']==[ref] and not data['photos']['items'];assert f.state(p)==saved
 # Clearing the optional reference needs no photo database.
 p.locator('#settingsPanel').evaluate('(e)=>e.classList.add("hidden")');f.open_view(p);d=f.photo_dialog(p);d.get_by_role('button',name='Remove photo',exact=True).click();assert f.refs(p)[1] is None;assert_clean(p,saved);assert not e,e;c.close();print('PASS',name,'unavailable IndexedDB, ordinary editor saves/core backups/legacy-compatible v2 restore, missing placeholders, removal without storage',flush=True)
def malformed(b,name):
 c,p,e,_=f.setup(b,name);f.open_view(p);f.upload(p);data=f.backup_ui(p);ref=f.refs(p)[1];expected=f.state(p);p.evaluate('photoTest.clear()')
 variants=[None,{'version':99,'items':[]},{'version':1,'items':[dict(data['photos']['items'][0],data='AAAA')]},{'version':1,'items':[dict(data['photos']['items'][0],data='A'*350000)]},{'version':1,'items':[dict(data['photos']['items'][0],type='image/png')]}]
 for manifest in variants:
  candidate=copy.deepcopy(data)
  if manifest is None:candidate.pop('photos')
  else:candidate['photos']=manifest
  warnings=p.evaluate('photoTest.restore',candidate);assert warnings and f.state(p)==expected;assert p.evaluate('photoTest.image',ref) is None
 # Invalid core must be rejected before any optional image staging.
 bad=copy.deepcopy(data);bad['meals']='invalid';bad['storage']['mealRotationDataV1']=json.dumps({'cats':[],'meals':'invalid'})
 try:p.evaluate('photoTest.stage',bad);raise AssertionError('Invalid core accepted')
 except Exception as err:assert 'Invalid core accepted' not in str(err)
 assert p.evaluate('photoTest.image',ref) is None
 # Old backups have no images: explicit v1 and ordinary version2 still restore.
 legacy={'version':1,'cats':['Old'],'active':'Old','meals':[{'id':100,'name':'Legacy recipe','cat':'Old','rotation':False,'ingredients':['1 apple'],'notes':'Legacy note'}]};f.restore_ui(p,legacy);assert any(m['id']==100 and m['notes']=='Legacy note' and not m['rotation'] for m in f.state(p)['meals']);assert not e,e;c.close();print('PASS',name,'missing/malformed/oversize optional manifests preserve exact core, invalid core cannot stage photos, legacy v1 restore',flush=True)
def restore_failure(b,name):
 c,p,e,prefix=f.setup(b,name);f.open_view(p);f.upload(p);one=f.refs(p)[1];data=f.backup_ui(p);p.locator('#settingsPanel').evaluate('(e)=>e.classList.add("hidden")');f.open_view(p);f.upload(p,f.B);two=f.refs(p)[1];f.close_view(p);before=f.state(p);native=f.safety.native(p,prefix);f.safety.fail_writes(p,['mealRotationDataV1']);p.get_by_role('button',name='Settings and backups',exact=True).click()
 p.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true')
 with p.expect_file_chooser() as fc:p.get_by_role('button',name='Restore backup',exact=True).click()
 fc.value.set_files({'name':'restore.json','mimeType':'application/json','buffer':json.dumps(data).encode()});p.wait_for_function('document.querySelector("#mealSaveWarning")');assert f.state(p)==before;assert f.safety.native(p,prefix)==native;assert p.evaluate('photoTest.image',one) and p.evaluate('photoTest.image',two);p.evaluate('restoreSafetyWrites()')
 with p.expect_navigation(wait_until='load'):p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click()
 assert f.refs(p)[1]==one;assert p.evaluate('photoTest.image',one);assert not e,e;c.close();print('PASS',name,'failed photo-bearing backup restore keeps old core and both blobs, Retry Save restores original reference',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for fn in [failures,unavailable,malformed,restore_failure]:fn(b,name)
  b.close()
