"""Image-bearing startup recovery, offline storage failure, and recipe selection UI."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
import phase2_stage5_photo_safety_browser as f
p5=f.f
p5.t.stage.f.HOOK += '''window.photoUI={search:()=>openMealSearch(),chooser:()=>weekTest.chooser()};'''
def recovery(b,name):
 c,p,e,_=p5.setup(b,name);p5.open_view(p);p5.upload(p);data=p5.backup_ui(p);ref=p5.refs(p)[1];c.close()
 for denied in [False,True]:
  c,p,e,prefix,_=p5.safety.bare(b,name,{'mealRotationDataV1':'{broken'})
  if denied:p.evaluate("Object.defineProperty(window,'indexedDB',{configurable:true,get(){throw Error('Unavailable optional photos')}})")
  with p.expect_file_chooser() as fc:p.locator('#mealDataRecovery').get_by_role('button',name='Restore Backup',exact=True).click()
  fc.value.set_files({'name':'photos.json','mimeType':'application/json','buffer':json.dumps(data).encode()});p.wait_for_function('!document.querySelector("#mealDataRecovery")');core=json.loads(p.evaluate('k=>localStorage.getItem(k)',prefix+'mealRotationDataV1'));assert core['meals']==data['meals'];assert core['meals'][0]['recipePhotoId']==ref
  if not denied:
   assert p.evaluate('''({name,id})=>new Promise(resolve=>{const r=indexedDB.open(name);r.onsuccess=()=>{const db=r.result,q=db.transaction('photos').objectStore('photos').get(id);q.onsuccess=()=>{resolve(q.result instanceof Blob);db.close()}}})''',{'name':'mealRotationTestRecipePhotosV1' if prefix else 'mealRotationRecipePhotosV1','id':ref})
  else:p.wait_for_function('document.body.textContent.includes("Optional photo storage is unavailable")')
  assert p.evaluate('localStorage.getItem("unrelated-user-setting")')=='keep'
  if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='PRODUCTION SENTINEL'
  assert not e,e;c.close()
 print('PASS',name,'startup Phase 1 recovery restores photo-bearing core with working or unavailable IDB; original journal protection and test isolation retained',flush=True)
def selection(b,name):
 c,p,e,_=p5.setup(b,name,320);p5.open_view(p);p5.upload(p);main=p5.refs(p)[1];before=p5.state(p);p.get_by_role('button',name='Open recipes',exact=True).click();d=p.get_by_role('dialog',name='Open Recipes',exact=True);d.locator('[data-meal-id="1"] img').wait_for(state='visible');d.get_by_role('searchbox',name='Search all recipes',exact=True).fill('Thai');d.locator('[data-meal-id="1"] img').wait_for(state='visible');d.get_by_role('button',name='Close open recipes',exact=True).click()
 p.evaluate('stage3Test.tab(20)');assert p.locator('[data-photo-manage="20"]').count();p5.upload(p,p5.B);assert p5.refs(p)[1]==main and p5.refs(p)[20]!=main;assert str(p.evaluate('stage3Test.state().id'))=='20';f.assert_clean(p,before);p5.close_view(p)
 p.evaluate('photoUI.chooser()');d=p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True);d.locator('[data-meal-id="1"] img').wait_for(state='visible');d.get_by_role('button',name='Cancel',exact=True).click();assert p5.refs(p)[1]==main
 p.evaluate('photoUI.search()');d=p.get_by_role('dialog',name='Search meals',exact=True);d.get_by_role('searchbox').fill('Thai');d.locator('img').first.wait_for(state='visible');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not e,e;c.close();print('PASS',name,'Open Recipes, Change Meal and global search thumbnails; serving-linked photo independence and active recipe tab preservation',flush=True)
def timeout(b,name):
 c,p,e,_=p5.setup(b,name);before=p5.state(p);p.evaluate("Object.defineProperty(window,'indexedDB',{configurable:true,value:{open:()=>({})}})");p5.open_view(p);p5.upload(p,success=False);assert p5.state(p)==before;assert 'respond' in p.locator('[data-photo-editor] [role=status]').inner_text();f.cancel_dialog(p);assert p5.backup_ui(p)['meals']==before['meals'];assert not e,e;c.close();print('PASS',name,'nonresponding IndexedDB times out and leaves recipes and core exports usable',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for fn in [recovery,selection,timeout]:fn(b,name)
  b.close()
