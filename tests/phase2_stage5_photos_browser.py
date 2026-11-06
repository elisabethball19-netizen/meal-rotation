"""Stage 5 optional photos: real files, UI, indexed blobs and data-safety fixtures."""
import base64,copy,hashlib,json,sys
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright
import phase2_stage4_final_browser as f
safety=f.safety
t=f.t
ROOT=Path(__file__).resolve().parents[1]
A=Path('/tmp/recipe-photo-a.png');B=Path('/tmp/recipe-photo-b.png')
Image.new('RGBA',(1800,1200),(190,30,40,255)).save(A)
Image.new('RGBA',(900,1500),(10,120,210,120)).save(B)
t.stage.f.HOOK += '''window.photoTest={
 state:()=>stage4Final.state(),
 db:()=>recipePhotoStorage.name,
 image:id=>recipePhotoStorage.read(id).then(async blob=>blob?{type:blob.type,size:blob.size,data:recipePhotoStorage.sha256(new Uint8Array(await blob.arrayBuffer())),bytes:Array.from(new Uint8Array(await blob.arrayBuffer()))}:null),
 bundle:()=>recipePhotoStorage.appendBackup({version:2,cats,active,meals,mealPlans:{plans:mealPlans,activeId:activePlanId},storage:captureBackupStorage()}),
 stage:async data=>{validateBackupCore(startupCore(data));const normalized=normalizeImportedBackup(data);validateBackupStorage(normalized);return recipePhotoStorage.restore(data)},
 restore:async data=>{validateBackupCore(startupCore(data));const normalized=normalizeImportedBackup(data);validateBackupStorage(normalized);const warnings=await recipePhotoStorage.restore(data);restoreBackupStorage(normalized);backupRestoreReloadPending=true;return warnings},
 refs:()=>meals.map(m=>({id:m.id,ref:m.recipePhotoId})),
 shared:()=>stage4Test.shared('Destination'),
 open:id=>stage3Test.open(id),groups:()=>stage4Test.groups(),
 clear:()=>new Promise((resolve,reject)=>{const r=indexedDB.open(recipePhotoStorage.name,1);r.onsuccess=()=>{const db=r.result,tx=db.transaction('photos','readwrite');tx.objectStore('photos').clear();tx.oncomplete=()=>{db.close();resolve()};tx.onerror=reject};r.onerror=reject}),
 preview:()=>({id:recipeViewer?.mealId,tab:recipeViewer?.activeTab.key,scroll:recipeViewer?.cover.scrollTop,panes:recipeViewer?[...recipeViewer.content.querySelectorAll('.recipe-pane')].map(p=>p.scrollTop):[]}),
 stacks:()=>({undo:history.length,redo:redoHistory.length}),
 photoUndo:()=>restoreState(JSON.parse(history.pop())),
 digest:text=>recipePhotoStorage.sha256(new TextEncoder().encode(text))
};'''
def setup(b,name,width=360):
 result=f.seeded(b,name,width);result[1].set_default_timeout(20000);return result
def state(p):return p.evaluate('photoTest.state()')
def refs(p):return {r['id']:r.get('ref') for r in p.evaluate('photoTest.refs()')}
def without_photos(data):
 data=copy.deepcopy(data)
 for meal in data['meals']:meal.pop('recipePhotoId',None)
 return data
def open_view(p,id=1):
 if p.locator('#recipeViewer').count():close_view(p)
 p.evaluate('photoTest.open',id);assert p.locator('#recipeViewer').is_visible()
def photo_dialog(p):
 p.locator('#recipeViewer [data-photo-manage]').click();return p.get_by_role('dialog',name='Recipe photo',exact=True)
def upload(p,path=A,success=True):
 d=photo_dialog(p);d.locator('input[type=file]').set_input_files(str(path))
 if success:
  try:p.wait_for_function('!document.querySelector("[data-photo-editor]")')
  except Exception as error:raise AssertionError('Photo upload did not finish: '+d.locator('[role=status]').inner_text()) from error
 else:p.wait_for_function('document.querySelector("[data-photo-editor] [role=status]")?.textContent.includes("not changed")')
 return d
def close_view(p):p.get_by_role('button',name='Close recipe',exact=True).click()
def backup_ui(p):
 close_view(p) if p.locator('#recipeViewer').count() else None
 if p.locator('#settingsPanel').is_hidden():p.get_by_role('button',name='Settings and backups',exact=True).click()
 p.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true')
 with p.expect_download() as dl:p.get_by_role('button',name='Export backup',exact=True).click()
 return json.loads(Path(dl.value.path()).read_text())
def restore_ui(p,data):
 if p.locator('#settingsPanel').is_hidden():p.get_by_role('button',name='Settings and backups',exact=True).click()
 p.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true')
 p.bring_to_front()
 with p.expect_file_chooser() as fc:p.get_by_role('button',name='Restore backup',exact=True).click()
 if data.get('version',1)>=2:
  with p.expect_navigation(wait_until='load'):fc.value.set_files({'name':'photos.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
  p.wait_for_function('window.photoTest')
 else:
  fc.value.set_files({'name':'photos.json','mimeType':'application/json','buffer':json.dumps(data).encode()});p.wait_for_function('(ids)=>JSON.stringify(photoTest.refs().map(r=>r.id))===JSON.stringify(ids)',arg=[m['id'] for m in data['meals']])

def basic(b,name,width):
 c,p,e,prefix=setup(b,name,width);p.evaluate('photoTest.shared()');open_view(p);before=state(p);assert p.locator('.recipe-photo-view .recipe-photo-placeholder').is_visible();assert p.evaluate('photoTest.digest', 'abc')==hashlib.sha256(b'abc').hexdigest();d=photo_dialog(p);p.keyboard.press('Escape');assert not d.count();assert state(p)==before
 upload(p);one=refs(p)[1];assert one and len(one)==68;assert all(r==one for id,r in refs(p).items() if id==1 or next(m for m in state(p)['meals'] if m['id']==id).get('linkGroup')=='stage4-family');assert refs(p)[20] is None;assert without_photos(state(p))==without_photos(before)
 image=p.evaluate('photoTest.image',one);assert image['type']=='image/jpeg' and image['size']<=256*1024 and one=='rp1-'+image['data'];assert hashlib.sha256(bytes(image['bytes'])).hexdigest()==image['data'];assert not any('data:image' in value for value in p.evaluate('weekTest.storage()').values());p.wait_for_function('document.querySelector(".recipe-photo-view img")?.naturalWidth>0');assert p.locator('.recipe-photo-large img').evaluate('(e)=>Math.max(e.naturalWidth,e.naturalHeight)<=1024');assert p.locator('[data-photo-manage]').evaluate('(e)=>e===document.activeElement')
 upload(p,B);two=refs(p)[1];assert two!=one and p.evaluate('photoTest.image',one);d=photo_dialog(p);d.get_by_role('button',name='Remove photo',exact=True).click();assert refs(p)[1] is None;assert p.locator('.recipe-photo-view .recipe-photo-placeholder').is_visible();close_view(p);p.locator('#undo').click();assert refs(p)[1]==two;p.locator('#redo').click();assert refs(p)[1] is None;p.locator('#undo').click();assert refs(p)[1]==two
 p.evaluate('photoTest.groups()');
 if not p.locator('.master-category-meal[data-meal-id="1"]').count():p.locator('.master-category-card[data-category=Rice] .master-category-title').click()
 assert p.locator('.master-category-meal-name .recipe-photo-thumb').count()>0;p.locator('.master-category-meal[data-meal-id="1"] img').wait_for(state='visible');p.evaluate('weekTest.my()');assert not p.locator('#list .recipe-photo-image').count();p.evaluate('weekTest.views()');assert not p.locator('#list .recipe-photo-image').count();p.reload();assert refs(p)[1]==two;open_view(p);p.wait_for_function('document.querySelector(".recipe-photo-view img")?.naturalWidth>0');assert without_photos(state(p))==without_photos(before);assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not e,e
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 print('PASS',name,width,'attach/replace/remove, compressed SHA JPEGs, shared refs, viewer/thumbnail/placeholders, scoped history, reload and compact schedules',flush=True);c.close()

def backups(b,name):
 c,p,e,_=setup(b,name);open_view(p);upload(p);ref=refs(p)[1];expected=state(p);data=backup_ui(p);assert data['version']==2 and data['photos']['version']==1 and data['photos']['items'][0]['id']==ref;assert not data['photos']['missing'];assert base64.b64decode(data['photos']['items'][0]['data'])[:2]==b'\xff\xd8';p.evaluate('photoTest.clear()');assert p.evaluate('photoTest.image',ref) is None
 restore_ui(p,data);assert refs(p)[1]==ref and p.evaluate('photoTest.image',ref);assert state(p)==expected;open_view(p);p.wait_for_function('document.querySelector(".recipe-photo-view img")?.naturalWidth>0');assert not e,e;c.close();print('PASS',name,'real backup export and file restore include immutable photos and exact recipe/schedule/cooking/grocery state',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [280,360]:basic(b,name,width)
   backups(b,name)
  b.close()
