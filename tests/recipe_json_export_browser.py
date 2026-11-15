"""Recipe-only JSON download and unchanged full backup, in disposable app fixtures."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import simple_sides_browser as s
s.f.HOOK+='''window.exportTest={seed:()=>{meals[0].simpleSides=[{id:'side-export',name:'Rice',ingredients:[{id:'ingredient-export',text:'1 cup rice'}]}];persist()},records:()=>JSON.parse(JSON.stringify(meals)),groups:()=>[...cats],storage:()=>JSON.stringify(captureBackupStorage())};'''
with sync_playwright() as pw:
 b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for name in ['index.html','meal-rotation-test.html']:
  c,p,errors,prefix=s.setup(b,name);p.evaluate('exportTest.seed()');records=p.evaluate('exportTest.records()');groups=p.evaluate('exportTest.groups()')
  p.get_by_role('button',name='Settings and backups',exact=True).tap();p.locator('details[data-settings-group=backups]').evaluate('(e)=>e.open=true');before=p.evaluate('exportTest.storage()')
  with p.expect_download() as download:p.get_by_role('button',name='Export all recipes (.json)',exact=True).tap()
  file=download.value;assert file.suggested_filename=='meal-rotation-recipes.json';data=json.loads(Path(file.path()).read_text());assert data['meals']==records and data['cats']==groups;assert data['version']==2;assert 'mealPlans' not in data and 'storage' not in data;assert any(not m['rotation'] for m in data['meals']);assert any(m.get('linkedMealIds') for m in data['meals']);assert data['meals'][0]['simpleSides'][0]['name']=='Rice';assert p.evaluate('exportTest.storage()')==before
  with p.expect_download() as download:p.get_by_role('button',name='Export backup',exact=True).tap()
  file=download.value;assert file.suggested_filename=='meal-rotation-backup.json';backup=json.loads(Path(file.path()).read_text());assert backup['meals']==records and 'mealPlans' in backup and 'storage' in backup;assert not errors,errors
  if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
  c.close();print('PASS',name,'all recipe records/Ideas/links/side defaults, valid JSON, recipe-only contents, read-only export, original full backup and isolated storage',flush=True)
 b.close()
