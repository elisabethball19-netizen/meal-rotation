"""Disposable mobile import/settings fixtures for both existing apps."""
import base64,gzip,io,json,zipfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as fixture
SAGE='12345678-1234-4234-8234-123456789abc'
TEXT='Title: Roasted carrots\nIngredients\n- 2 carrots\n- 1 tbsp oil\nInstructions\nRoast the carrots for 20 minutes.\nNotes\nKeep these notes.'
RAW={'name':'Roasted carrots','recipeCategory':['Side dish'],'recipeIngredient':['2 carrots','1 tbsp oil'],'recipeInstructions':['Roast the carrots for 20 minutes.'],'notes':'Keep these notes.','url':'https://recipes.test/carrots'}
fixture.HOOK+='''window.spec123={
 import:openRecipeImportSourcePicker,bulk:items=>showRecipeImportSelection(recipeImportItems(items),'fixture.json'),read:async([name,b64])=>recipeImportReadFile(new File([Uint8Array.from(atob(b64),c=>c.charCodeAt(0))],name)),
 state:()=>JSON.stringify({meals:meals.filter(m=>m.id!==newRecipeDraftId),plans:mealPlans,checks:groceryOccurrenceChecks,scales:occurrenceScales}),
 storage:()=>captureBackupStorage(),records:()=>JSON.parse(JSON.stringify(meals)),
 undo:()=>{const v=JSON.parse(history.pop());redoHistory.push(captureHistoryCounterpart(v));restoreState(v)},redo:()=>{const v=JSON.parse(redoHistory.pop());history.push(captureHistoryCounterpart(v));restoreState(v)},
 refreshSeed:()=>{const m=meals.find(m=>m.id===1);m.recipeSageId='12345678-1234-4234-8234-123456789abc';m.importSourceId=m.recipeSageId;m.notes='Personal notes stay';persist()},
 ocr:()=>{ingredientPhotoIsBlank=async()=>false;recognizeIngredientPhoto=async()=>'''+json.dumps(TEXT)+'''},
 delayBackup:()=>{const original=storeRecipeSageSafetyBackup;storeRecipeSageSafetyBackup=(...args)=>new Promise(resolve=>{window.release123=()=>original(...args).then(resolve)});window.restore123=()=>{storeRecipeSageSafetyBackup=original}},
 normalized:records=>records.map(normalizeRecipeStatus),sideId:()=>groupIdentity(builtinSidesGroup()),validate:()=>validateBackupStorage(captureBackupStorage())
};'''
OUT=Path('/workspace/work/screenshots123');OUT.mkdir(exist_ok=True)
def close(p,title='Import recipes'):
 p.get_by_role('button',name='Close '+title.lower(),exact=True).click();p.wait_for_timeout(100)
def popup(p):return p.get_by_role('dialog',name='Import recipes',exact=True)
def review(p):popup(p).get_by_role('button',name='Review recipe',exact=True).click();p.locator('#name').wait_for()
def cancel_editor(p):p.locator('#cancel').click();p.wait_for_timeout(150)
def settings(p):
 if not p.locator('#settingsPanel:not(.hidden)').count():p.get_by_role('button',name='Settings and backups',exact=True).click()
 for key in ['display','recipes','backups']:p.locator('[data-settings-group="'+key+'"]').evaluate('(e)=>e.open=true')
def run(b,name):
 c,p,errors,prefix=fixture.setup(b,name);p.set_default_timeout(8000)
 settings(p)
 assert p.locator('[data-settings-group=recipes]').get_by_role('button').all_text_contents()==['Import recipes','Export recipes','Refresh from RecipeSage']
 assert p.locator('[data-settings-group=backups]').get_by_role('button').all_text_contents()==['Save backup','Restore backup']
 assert not p.locator('#recipeSageRefresh').count()
 columns=p.locator('#settingsPanel .settings-display-option').evaluate_all('(rows)=>rows.map(r=>[r.querySelector(".preference-switch-control").getBoundingClientRect().left,r.querySelector(".settings-display-option-copy").getBoundingClientRect().left])')
 assert len(set(tuple(round(x)for x in r)for r in columns))==1,columns
 p.screenshot(path=str(OUT/(name+'-display.png')),full_page=True)
 saved=p.evaluate('spec123.state()');p.get_by_role('button',name='Import recipes',exact=True).scroll_into_view_if_needed();return_scroll=p.evaluate('scrollY');p.get_by_role('button',name='Import recipes',exact=True).click()
 assert popup(p).get_by_role('radio').count()==5;return_scroll=p.evaluate('scrollY')
 for label in ['Website link','Photo or camera','Paste text','Recipe file','Trello board link']:
  popup(p).get_by_role('radio',name=label,exact=True).check();assert popup(p).locator('.recipe-import-method-body').count()==1
 p.screenshot(path=str(OUT/(name+'-import.png')))
 p.go_back();p.wait_for_timeout(150);assert not popup(p).count();assert p.evaluate('spec123.state()')==saved;assert abs(p.evaluate('scrollY')-return_scroll)<2,(return_scroll,p.evaluate('scrollY'))
 # Inline status stays pending, saves through the existing operation, Undo/Redo restores it.
 p.evaluate('batch1.editor(1)');p.locator('#recipeStatus input[value="up-next"]').check();assert p.evaluate('batch1.records().find(m=>m.id===1).rotation')
 p.locator('.meal-editor-fields').evaluate('(e)=>e.scrollTop=0');p.screenshot(path=str(OUT/(name+'-status.png')));cancel_editor(p);assert p.evaluate('batch1.records().find(m=>m.id===1).rotation')
 p.evaluate('batch1.editor(1)');p.locator('#recipeStatus input[value="up-next"]').check();p.locator('#save').click();assert not p.evaluate('batch1.records().find(m=>m.id===1).rotation');p.evaluate('spec123.undo()');assert p.evaluate('batch1.records().find(m=>m.id===1).rotation');p.evaluate('spec123.redo()');assert not p.evaluate('batch1.records().find(m=>m.id===1).rotation')
 p.evaluate('batch1.editor(1)');p.locator('#recipeStatus input[value="rotation"]').check();p.go_back();p.get_by_role('button',name='No',exact=True).click();p.wait_for_timeout(150);assert not p.evaluate('batch1.records().find(m=>m.id===1).rotation')
 # Text/photo/website use existing parsers and ordinary editor review, no save on Cancel.
 for method in ['text','photo','website']:
  before=p.evaluate('spec123.state()');p.evaluate('method=>spec123.import(method)',method)
  if method=='text':popup(p).get_by_role('textbox',name='Recipe text',exact=True).fill(TEXT)
  elif method=='photo':
   p.evaluate('spec123.ocr()');popup(p).locator('input[type=file]').first.set_input_files({'name':'recipe.png','mimeType':'image/png','buffer':b'fixture OCR'});popup(p).get_by_role('textbox',name='Recognized recipe text').wait_for();p.wait_for_function('document.querySelector(".recipe-import-method-body textarea").value.includes("carrots")')
  else:
   p.route('https://recipes.test/carrots',lambda route:route.fulfill(status=200,body='<script type="application/ld+json">'+json.dumps({'@type':'Recipe',**RAW})+'</script>'))
   popup(p).get_by_role('textbox',name='Website link',exact=True).fill('https://recipes.test/carrots')
  review(p);assert not any(r.get('url')==RAW['url'] for r in json.loads(p.evaluate('spec123.storage().mealRotationDataV1'))['meals']);assert p.locator('#ingredients').input_value().count('carrots')==1;assert 'Roast' in p.locator('#recipeInstructions').input_value();cancel_editor(p);assert p.evaluate('spec123.state()')==before
 before=p.evaluate('spec123.state()');p.evaluate("spec123.import('text')");popup(p).get_by_role('textbox',name='Recipe text').fill('Family recipe text without headings');review(p);assert p.locator('#recipeNotes').input_value()=='Family recipe text without headings';cancel_editor(p);assert p.evaluate('spec123.state()')==before
 # Representative file parser formats, including gzip Paprika and ZIP wrappers.
 raw=json.dumps({'@type':'Recipe',**RAW}).encode();files={'recipe.json':raw,'recipe.jsonld':raw,'recipe.melarecipe':raw,'recipe.paprikarecipe':gzip.compress(raw),'recipe.html':b'<script type="application/ld+json">'+raw+b'</script>','recipe.csv':b'name,ingredients,instructions\nCarrots,2 carrots,Roast carrots.\n'}
 for ext in ['zip','paprikarecipes','melarecipes']:
  buffer=io.BytesIO()
  with zipfile.ZipFile(buffer,'w',zipfile.ZIP_STORED)as archive:archive.writestr('recipe.json',raw)
  files['recipes.'+ext]=buffer.getvalue()
 for filename,data in files.items():assert p.evaluate('args=>spec123.read(args)',[filename,base64.b64encode(data).decode()]),filename
 # Single file -> editor -> opt-in Sides, Save/Undo/Redo without changing old records.
 p.evaluate("spec123.import('file')");popup(p).locator('input[type=file]').set_input_files({'name':'single.json','mimeType':'application/json','buffer':raw});popup(p).get_by_role('button',name='Read recipe file').click();p.locator('#name').wait_for()
 assert p.locator('#recipeStatus input[value=rotation]').is_disabled();side_id=p.evaluate('spec123.sideId()');p.get_by_role('checkbox',name='Add this recipe to Sides?',exact=True).check();p.get_by_role('button',name='Edit meal groups',exact=True).click();groups=p.get_by_role('dialog',name='Choose a group for your recipe',exact=True);groups.get_by_role('checkbox',name='Meals',exact=True).check();groups.get_by_role('button',name='Apply selected groups',exact=True).click();p.locator('#save').click();records=p.evaluate('spec123.records()');new=next(r for r in records if r.get('url')==RAW['url']);assert {r['cat']for r in records if r.get('url')==RAW['url']}=={'Sides','Meals'};assert new['cat']=='Sides' and new['notes']==RAW['notes'] and 'Roast' in str(new['instructions']);p.evaluate('spec123.validate()');p.evaluate('spec123.undo()');assert not any(r.get('url')==RAW['url']for r in p.evaluate('spec123.records()'));p.evaluate('spec123.redo()');assert any(r.get('url')==RAW['url']for r in p.evaluate('spec123.records()'));assert p.evaluate('spec123.sideId()')==side_id
 # Bulk keeps original group picker; likely-side choice is opt-in, uncertain metadata untouched.
 bulk=[{**RAW,'name':'Bulk side','identifier':'bulk-side','recipeCategory':['Side dish','Vegetables']},{**RAW,'name':'Roasted potatoes','identifier':'uncertain','recipeCategory':['Main dish']}]
 p.evaluate('items=>spec123.bulk(items)',bulk);d=p.get_by_role('dialog',name='Choose meal groups',exact=True);assert d.locator('.import-side-review input').count()==1 and not d.locator('.import-side-review input').is_checked();d.locator('.import-side-review input').check();p.screenshot(path=str(OUT/(name+'-bulk.png')));d.get_by_role('button',name='Import recipes',exact=True).click();p.get_by_role('button',name='OK',exact=True).click();records=p.evaluate('spec123.records()');assert next(r for r in records if r.get('importSourceId')=='bulk-side')['cat']=='Sides';assert next(r for r in records if r.get('importSourceId')=='uncertain')['cat']==''
 # Trello uses its existing board parser and bulk review, no records on Back.
 board={'lists':[{'id':'list','name':'Sides'}],'cards':[{'id':'a','name':'Board carrots','idList':'list','desc':'Ingredients\n- 2 carrots\nInstructions\nRoast carrots.'},{'id':'b','name':'Board rice','idList':'list','desc':'Ingredients\n- 1 cup rice'}]}
 p.route('https://trello.com/b/abcdef12.json',lambda route:route.fulfill(status=200,content_type='application/json',body=json.dumps(board)))
 p.evaluate("spec123.import('trello')");popup(p).get_by_role('textbox',name='Trello board link',exact=True).fill('https://trello.com/b/abcdef12');popup(p).get_by_role('button',name='Read board').click();d=p.get_by_role('dialog',name='Choose meal groups',exact=True);d.wait_for();p.go_back();p.wait_for_timeout(150);assert not d.count()
 # Refresh popup retains safety-backup logic and personal notes; cancellation and Undo.
 p.evaluate('spec123.refreshSeed()');settings(p);p.get_by_role('button',name='Refresh from RecipeSage',exact=True).click();d=p.get_by_role('dialog',name='Refresh from RecipeSage',exact=True);before=p.evaluate('spec123.state()');close(p,'Refresh from RecipeSage');assert p.evaluate('spec123.state()')==before
 p.get_by_role('button',name='Refresh from RecipeSage',exact=True).click();d=p.get_by_role('dialog',name='Refresh from RecipeSage',exact=True);d.locator('input[type=file]').set_input_files({'name':'sage.json','mimeType':'application/json','buffer':json.dumps([{**RAW,'identifier':SAGE,'recipeInstructions':['Updated cooking step.']}]).encode()});d.get_by_role('button',name='Refresh Recipes',exact=True).wait_for();p.wait_for_function('!document.querySelector("#recipeSageRefresh button:last-of-type").disabled')
 with p.expect_download()as download:d.get_by_role('button',name='Refresh Recipes',exact=True).click()
 assert 'before-recipesage-refresh' in download.value.suggested_filename
 p.wait_for_function('document.querySelector("#recipeSageRefresh [role=status]").textContent.includes("recipes refreshed")');assert p.evaluate('spec123.records().find(m=>m.id===1).notes')=='Personal notes stay';assert 'Updated cooking' in str(p.evaluate('spec123.records().find(m=>m.id===1).instructions'));close(p,'Refresh from RecipeSage');p.evaluate('spec123.undo()');assert 'Updated cooking' not in str(p.evaluate('spec123.records().find(m=>m.id===1).instructions'))
 # Closing during the awaited safety backup must prevent the refresh write.
 settings(p);p.get_by_role('button',name='Refresh from RecipeSage',exact=True).click();d=p.get_by_role('dialog',name='Refresh from RecipeSage',exact=True);before=p.evaluate('spec123.state()');p.evaluate('spec123.delayBackup()')
 d.locator('input[type=file]').set_input_files({'name':'sage.json','mimeType':'application/json','buffer':json.dumps([{**RAW,'identifier':SAGE,'recipeInstructions':['Must not save this step.']}]).encode()});p.wait_for_function('!document.querySelector("#recipeSageRefresh button:last-of-type").disabled');d.get_by_role('button',name='Refresh Recipes',exact=True).click();p.wait_for_function('typeof release123==="function"');close(p,'Refresh from RecipeSage');p.evaluate('release123()');p.evaluate('restore123()');assert p.evaluate('spec123.state()')==before
 # Real narrow/landscape and app extra-text layouts, plus keyboard-like reduced viewport.
 for width,height,suffix in [(320,640,'narrow'),(740,360,'landscape'),(360,360,'keyboard')]:
  p.set_viewport_size({'width':width,'height':height});p.evaluate("document.body.dataset.mealTextSize='extra';spec123.import('text')");popup(p).get_by_role('textbox',name='Recipe text').fill(TEXT);popup(p).locator('>div').evaluate('(e)=>e.scrollTop=e.scrollHeight');p.screenshot(path=str(OUT/(name+'-'+suffix+'.png')));assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');close(p)
 # Recipe export excludes full settings/storage; backup and Restore reuse existing data validation.
 p.set_viewport_size({'width':360,'height':800});settings(p)
 with p.expect_download()as download:p.locator('[data-settings-group=recipes]').get_by_role('button',name='Export recipes',exact=True).click()
 recipe_export=json.loads(Path(download.value.path()).read_text());assert 'meals'in recipe_export and 'storage'not in recipe_export
 with p.expect_download()as download:p.locator('[data-settings-group=backups]').get_by_role('button',name='Save backup',exact=True).click()
 backup=json.loads(Path(download.value.path()).read_text());assert 'storage'in backup and 'mealRotationDataV1'in backup['storage']
 saved_meals=p.evaluate('records=>spec123.normalized(records)',json.loads(backup['storage']['mealRotationDataV1'])['meals'])
 with p.expect_file_chooser()as chooser:p.locator('[data-settings-group=backups]').get_by_role('button',name='Restore backup',exact=True).click()
 with p.expect_navigation(wait_until='load'):chooser.value.set_files({'name':'backup.json','mimeType':'application/json','buffer':json.dumps(backup).encode()})
 assert p.evaluate('spec123.records()')==saved_meals,[(x,y)for x,y in zip(saved_meals,p.evaluate('spec123.records()'))if x!=y]
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;c.close();print('PASS',name,'unified methods/parsers, review, Sides, status, refresh safety, Undo/Redo, cancellation/Back, mobile geometry')
if __name__=='__main__':
 with sync_playwright()as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(browser,name)
  browser.close()
