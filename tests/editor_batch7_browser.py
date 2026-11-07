"""Photo-free UI, legacy photo backups, compact draft card and retained OCR import paths."""
import base64,json
from pathlib import Path
from PIL import Image,ImageDraw
from playwright.sync_api import sync_playwright
import editor_batch6_browser as base
f=base.f
PHOTO=Path('/tmp/b7-legacy.jpg');im=Image.new('RGB',(600,400),'white');draw=ImageDraw.Draw(im);draw.rectangle((30,30,500,80),fill='black');draw.text((30,100),'1 cup rice\n2 cups broth',fill='black');im.save(PHOTO,'JPEG')
f.EXTRA+='''window.batch7={
 seed:async bytes=>{batch5.seed();const blob=new Blob([Uint8Array.from(atob(bytes),c=>c.charCodeAt(0))],{type:'image/jpeg'}),id=await recipePhotoStorage.idFor(blob);await recipePhotoStorage.put([{id,blob}]);meals.find(m=>m.id===537).recipePhotoId=id;persist();promotionTest.groups();return id},
 read:id=>recipePhotoStorage.read(id).then(b=>!!b),
 open:()=>openRecipeViewer(meals.find(m=>m.id===537)),
 bundle:()=>recipePhotoStorage.appendBackup({version:2,cats,active,meals,weekdayCategories,weekdayMealOverrides,mealPlans:{plans:mealPlans,activeId:activePlanId},storage:captureBackupStorage()}),
 restore:async d=>{validateBackupCore(startupCore(d));const normalized=normalizeImportedBackup(d);validateBackupStorage(normalized);const warnings=await recipePhotoStorage.restore(d);restoreBackupStorage(normalized);backupRestoreReloadPending=true;return warnings},
 mutate:()=>{meals.find(m=>m.id===537).name='Changed fixture';persist()},
 scan:text=>{window.Tesseract={recognize:async()=>({data:{text}})}},
 undo:()=>restoreState({recipePhotoUndo:{refs:{'537':{present:true,value:meals.find(m=>m.id===537).recipePhotoId}}}})
};'''

def clean(p):assert p.locator('[class*="recipe-photo"],[data-photo-manage],[data-photo-editor]').count()==0

def settings(p):
 if p.locator('#settingsPanel').is_hidden():p.get_by_role('button',name='Settings and backups',exact=True).click()
 p.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true')

def backup_ui(p):
 settings(p)
 with p.expect_download() as dl:p.get_by_role('button',name='Export backup',exact=True).click()
 return json.loads(Path(dl.value.path()).read_text())

def restore_ui(p,data):
 settings(p)
 with p.expect_file_chooser() as fc:p.get_by_role('button',name='Restore backup',exact=True).click()
 if data.get('version',1)>=2:
  with p.expect_navigation(wait_until='load'):fc.value.set_files({'name':'legacy-photo-backup.json','mimeType':'application/json','buffer':json.dumps(data).encode()})
  p.wait_for_function('window.batch7')
 else:
  fc.value.set_files({'name':'legacy-photo-backup.json','mimeType':'application/json','buffer':json.dumps(data).encode()});p.wait_for_function('batch5.meal().name!=="Changed fixture"')

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport()');ref=p.evaluate('batch7.seed',base64.b64encode(PHOTO.read_bytes()).decode());clean(p)
 assert p.evaluate('batch5.meal().recipePhotoId')==ref and p.evaluate('batch7.read',ref)
 p.evaluate('promotionTest.my()');clean(p);p.evaluate('remainingTest.menu()');assert p.get_by_role('dialog',name='Meal options').is_visible();p.get_by_role('button',name='Close meal options',exact=True).click()
 p.evaluate('batch7.open()');clean(p);assert p.locator('#recipeViewer').is_visible();p.get_by_role('button',name='Close recipe',exact=True).click()
 p.evaluate('batch5.open()');p.wait_for_timeout(850);clean(p);card=p.locator('.meal-card-edit-mode');button=p.get_by_role('button',name='Edit meal name',exact=True)
 assert abs(button.bounding_box()['width']-card.locator('.meal-card-name-field').bounding_box()['width'])<1
 assert card.evaluate('(e)=>getComputedStyle(e).boxShadow')=='none' and card.evaluate('(e)=>getComputedStyle(e).borderBottomWidth')=='0px'
 assert card.evaluate('(e)=>parseFloat(getComputedStyle(e).outlineWidth)')<=1
 assert button.locator('svg').count()==0 and button.evaluate('(e)=>getComputedStyle(e).boxShadow')=='none'
 base.base.field(p,'meal name','name','Discard photo-free edit');base.base.field(p,'prep time','prep','15 min');base.base.linked(p);base.base.fit(p);p.locator('#cancel').click();assert p.evaluate('batch5.meal().name')!='Discard photo-free edit'
 p.evaluate('batch5.open()');p.wait_for_timeout(700);base.base.field(p,'meal name','name','Photo-free saved meal');p.locator('#save').click();assert p.evaluate('batch5.meal().name')=='Photo-free saved meal' and p.evaluate('batch5.meal().recipePhotoId')==ref
 # Existing camera/gallery controls still run preprocessing, OCR result review and draft application.
 # Only the external OCR recognizer is synthetic; real camera capture and text recognition need a device check.
 p.evaluate('batch5.open()');p.wait_for_timeout(700);base.base.expand(p,'[data-editor-section=recipe]');base.base.expand(p,'#editorIngredientsSection')
 for id,button_id in [('ingredientGalleryInput','ingredientPhotoButton'),('ingredientCameraInput','ingredientCameraButton')]:
  p.evaluate('batch7.scan','Ingredients\n1 cup rice\n2 cups broth')
  with p.expect_file_chooser() as fc:p.locator('#'+button_id).click()
  fc.value.set_files(str(PHOTO));d=p.get_by_role('dialog',name='Review photo ingredients',exact=True);d.get_by_role('button',name='Add ingredients',exact=True).click();assert 'rice' in p.locator('#ingredients').input_value()
 base.base.expand(p,'#editorInstructionsSection')
 for id,button_id in [('instructionGalleryInput','instructionPhotoButton'),('instructionCameraInput','instructionCameraButton')]:
  p.locator('#recipeInstructions').fill('');p.evaluate('batch7.scan','Instructions\n1. Stir the rice into the broth.\n2. Cook for 20 minutes.')
  with p.expect_file_chooser() as fc:p.locator('#'+button_id).click()
  fc.value.set_files(str(PHOTO));d=p.get_by_role('dialog',name='Review photo cooking instructions',exact=True);d.get_by_role('button',name='Use instructions',exact=True).click();assert 'Stir' in p.locator('#recipeInstructions').input_value()
 p.locator('#cancel').click()
 data=backup_ui(p);assert any(x['id']==ref for x in data['photos']['items']);p.evaluate('batch7.mutate()');restore_ui(p,data);assert p.evaluate('batch5.meal().name')=='Photo-free saved meal';assert p.evaluate('batch7.read',ref);clean(p)
 # Version-1 backups with optional photos use the legacy UI restore path too.
 legacy={k:v for k,v in data.items() if k!='storage'};legacy['version']=1;p.evaluate('batch7.mutate()');restore_ui(p,legacy);assert p.evaluate('batch5.meal().recipePhotoId')==ref;assert p.evaluate('batch7.read',ref)
 # Missing or malformed optional photos cannot block recipe-content restoration.
 invalid=json.loads(json.dumps(data));invalid['photos']={'version':999,'items':[]};warnings=p.evaluate('batch7.restore',invalid);assert warnings;p.reload();p.wait_for_function('window.batch7');assert p.evaluate('batch5.meal().recipePhotoId')==ref and p.evaluate('batch7.read',ref);p.evaluate('batch7.undo()');clean(p)
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'photo-free cards/lists/viewer, full-width draft name/soft edges, Save/Cancel/links, legacy refs/v1+v2 photo backup UI roundtrip/invalid optional data, retained IDB and camera/gallery OCR pipeline (synthetic recognizer); no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
