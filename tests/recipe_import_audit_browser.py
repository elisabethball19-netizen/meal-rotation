"""Instruction extraction and reviewed URL repairs, using synthetic recipes/storage."""
import copy,csv,gzip,io,json,tempfile,zipfile
from urllib.parse import unquote
from playwright.sync_api import sync_playwright
import instruction_repair_browser as fixture
SAGE=fixture.SAGE
SOURCE='https://android.recipesage.com/api/share/recipe/'+SAGE
SAGE2='32345678-1234-1234-1234-123456789abc'
BOILER=['Create an account or login to save this recipe to your collection.','Register/Login to Save','Created 5/5/2026, 11:05 PM','Last edited 6/16/2026, 11:13 PM','Last made 5/26/2026']
STEPS=['Brown the roast in a pan with vegetable oil.','Add the broth and roast to a covered slow cooker.','Slow cook on low for 8 hours, then serve.']
READER='Title: French Dip\nURL Source: '+SOURCE+'\nMarkdown Content:\n'+'\n\n'.join('**'+str(i)+'**'+text for i,text in enumerate(STEPS,1))
COOK=[{'type':'section','text':'Pork'},{'type':'step','text':'Roast 2 lb pork at 350°F for 4 hours.'},{'type':'section','text':'Finish'},{'type':'step','text':'Rest for 20 minutes and serve with 1½ cups rice.'}]
fixture.HOOK+='''window.auditTest={complete:completeRecipeFields,items:recipeImportItems,html:recipeImportHtml,extract:(raw,url='',name='')=>extractCompleteRecipe(raw,url,name),cleanup:cleanupRecipeInstructions,read:recipeImportReadFile,web:(url,name='French Dip')=>importIngredientsFromWebsite(url,null,name).then(lines=>({lines:[...lines],details:lines.recipeDetails})),audit:()=>meals.map(m=>({id:m.id,...recipeInstructionAudit(m)})),
 seed:()=>{const m=meals.find(m=>m.id===2),t=cookingItemTokens(m);m.ingredientStepLinks=[{step:t.steps.find(s=>s.text.startsWith('Roast')).token,ingredients:[t.ingredients[0].token]}];const c=cookingContext('original','Tuesday',m.cat,m);cookingSessions.occurrences[cookingOccurrenceKey(c)]={id:'pernil',context:c,ingredients:[t.ingredients[0].token],steps:[t.steps.find(s=>s.text.startsWith('Roast')).token],autoIngredients:[],ingredientOverrides:{}};writeCookingSessions(cookingSessions);persist()},
 viewer:()=>openRecipeViewer(meals.find(m=>m.id===2),cookingContext('original','Tuesday','Fish',meals.find(m=>m.id===2))),closeViewer:()=>closeRecipeViewer()};'''
def library():
 dirty=[COOK[0],COOK[1],*[{'type':'step','text':text} for text in BOILER],*COOK[2:]]
 return [fixture.meal(1,SAGE,name='French Dip',instructions=[],originalRecipeUrl=SOURCE,url=SOURCE,linkGroup='shared'),fixture.meal(10,SAGE,name='My renamed dip',cat='Dinner',instructions=[],originalRecipeUrl=SOURCE,url=SOURCE,linkGroup='shared'),fixture.meal(2,SAGE2,name='Pernil',rotation=True,instructions=dirty,url='https://android.recipesage.com/api/share/recipe/'+SAGE2,notes='My handwritten note: keep 2 tbsp juices.\n'+ '\n'.join(BOILER)),fixture.meal(3,'valid',name='Already correct',instructions='Cook at 180°C for 25 minutes. Keep my edited instruction.'),fixture.meal(4,'offline',name='Unavailable',instructions=[],url='https://recipes.test/unavailable',originalRecipeUrl='https://recipes.test/unavailable'),fixture.meal(7,'associations',name='Missing with saved links',instructions=[],ingredientStepLinks=[{'step':'old-step','ingredients':['old-ingredient']}],url=SOURCE,originalRecipeUrl=SOURCE),fixture.meal(8,'web',name='Other imported website',url='https://recipes.test/other',originalRecipeUrl='https://recipes.test/other',instructions=[{'type':'step','text':'Boil water for 10 minutes.'},*({'type':'step','text':text} for text in BOILER)],importSourceId='',recipeSageId='',sourceUrl=''),fixture.meal(50,'side',name='Side',cat='Sides',instructions='Cook rice for 15 minutes.')]

def parse_tests(browser,filename,width):
 ctx,p,errors,_=fixture.setup(browser,filename,width,library=library(),seed_progress=False)
 def extract(raw,url='',name=''):return p.evaluate('([raw,url,name])=>auditTest.extract(raw,url,name)',[raw,url,name])
 def complete(record):return p.evaluate('(r)=>auditTest.complete(r)',record)
 found=extract(READER,SOURCE,'French Dip');assert len(found['instructions'])==3 and all(text in '\n'.join(b['text'] for b in found['instructions']) for text in STEPS)
 assert extract(READER,'https://unrelated.test/other','French Dip') is None
 structured={'@type':'Recipe','name':'Pernil','recipeIngredient':['2 lb pork'],'recipeInstructions':[{'@type':'HowToSection','name':'Roast','itemListElement':[{'@type':'ListItem','position':1,'item':{'@type':'HowToStep','text':{'@value':'Bake at 350°F for 4 hours.'}}},{'@type':'HowToStep','text':'Rest for 20 minutes.'},*({'@type':'HowToStep','text':text} for text in BOILER)]}],'url':'https://recipes.test/pernil','notes':'A real recipe note.'}
 result=complete(structured);texts='\n'.join(b['text'] for b in result['instructions']);assert '350°F' in texts and '4 hours' in texts and 'Roast' in texts and not any(b in texts for b in BOILER)
 for record in [dict(structured,recipeInstructions=[],directions='Cook at 200°C for 30 minutes.'),dict(structured,recipeInstructions='Register/Login to Save',directions='Cook at 200°C for 30 minutes.')]:assert complete(record)['instructions'][0]['text']=='Cook at 200°C for 30 minutes.'
 assert complete(dict(structured,recipeInstructions={'@type':'HowToStep','itemListElement':[],'text':'Cook for 15 minutes.'}))['instructions'][0]['text']=='Cook for 15 minutes.'
 graph={'@graph':[{'@type':'Recipe','name':'Graph recipe','recipeIngredient':['1 carrot'],'recipeInstructions':[{'@id':'#section'}]},{'@id':'#section','@type':'HowToSection','name':'Vegetables','itemListElement':[{'@id':'#step'}]},{'@id':'#step','@type':'HowToStep','text':'Roast carrots for 25 minutes.'}]}
 for data in [extract(json.dumps(graph)),complete(p.evaluate('(r)=>auditTest.items(r)[0]',graph))]:assert [b['text'] for b in data['instructions']]==['Vegetables','Roast carrots for 25 minutes.']
 # An incomplete JSON-LD record must not hide the visible recipe card; complete structured instructions win.
 card='<div class="wprm-recipe-container"><h2 class="wprm-recipe-name">Pernil</h2><ul><li class="wprm-recipe-ingredient">2 lb pork</li></ul><div class="wprm-recipe-instructions-container"><h3>Roast</h3><ol><li>Cook at 325°F for 5 hours.</li><li>Rest for 10 minutes.</li></ol><nav>Home</nav><div class="advertisement">Unrelated ad</div></div></div>'
 partial=dict(structured,recipeInstructions=[])
 for method in ['extract','html']:
  html='<script type="application/ld+json">'+json.dumps(partial)+'</script>'+card
  value=extract(html,'https://recipes.test/pernil','Pernil') if method=='extract' else complete(p.evaluate('(raw)=>auditTest.html(raw)[0]',html))
  assert '325°F' in str(value['instructions']) and 'Unrelated ad' not in str(value['instructions'])
 metadata_only=dict(structured,recipeInstructions='Register/Login to Save')
 assert '325°F' in str(extract('<script type="application/ld+json">'+json.dumps(metadata_only)+'</script>'+card,'https://recipes.test/pernil','Pernil')['instructions'])
 html='<script type="application/ld+json">'+json.dumps(structured)+'</script>'+card
 assert '350°F' in str(extract(html,'https://recipes.test/pernil','Pernil')['instructions']) and '325°F' not in str(extract(html,'https://recipes.test/pernil','Pernil')['instructions'])
 micro='<article itemscope itemtype="https://schema.org/Recipe"><h1 itemprop="name">Micro recipe</h1><div itemprop="recipeIngredient">1 carrot</div><p itemprop="recipeInstructions">Chop carrots.</p><p itemprop="recipeInstructions">Cook carrots for 10 minutes.</p></article>'
 assert len(extract(micro)['instructions'])==2
 ambiguous=json.dumps([dict(structured,name='Recipe A',url='https://recipes.test/a'),dict(structured,name='Recipe B',url='https://recipes.test/b')]);assert extract(ambiguous,'https://recipes.test/unknown','Custom title')['instructions']==[]
 good='Created a smooth dough and rest 30 minutes.\nLog in your cooking journal when the dough doubles.\n350°F for 30 minutes\n2.5 cups broth\nA discount may be available from your butcher.'
 assert '\n'.join(b['text'] for b in p.evaluate('(raw)=>auditTest.cleanup(raw)',good)['instructions'])==good
 note='Keep these useful pork juices.\nLinked Recipes\n![Image 2](https://recipesage.com/app/assets/imgs/logo_green_padded.png)\n## Rice With Beans\n'+'\n'.join(BOILER)
 cleaned=complete(dict(structured,url=SOURCE,notes=note));assert cleaned['notes']=='Keep these useful pork juices.' and cleaned['recipeImportReferences'][0]['name']=='Rice With Beans'
 # All structured file paths share the instruction parser/cleaner.
 buff=io.StringIO();writer=csv.writer(buff);writer.writerow(['name','instructions']);writer.writerow(['Pernil','Cook for 4 hours.\n'+'\n'.join(BOILER)])
 for name,raw in [('fixture.json',json.dumps(structured)),('fixture.jsonld',json.dumps(graph)),('fixture.html',html),('fixture.csv',buff.getvalue())]:
  result=p.evaluate('([name,raw])=>auditTest.read(new File([raw],name)).then(records=>records.map(auditTest.complete))',[name,raw]);assert result and all(not any(b in str(r['instructions']) for b in BOILER) for r in result)
 # Archive/Paprika/Mela and Trello paths must use the same cleanup logic.
 archive=io.BytesIO()
 paprika={'name':'Paprika roast','ingredients':'2 lb pork','directions':'Roast for 4 hours.\n'+'\n'.join(BOILER),'uid':'audit-paprika'}
 mela={'title':'Mela roast','ingredients':['2 lb pork'],'instructions':'Roast for 4 hours.\n'+'\n'.join(BOILER),'id':'audit-mela'}
 with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_STORED) as z:
  z.writestr('recipe.json',json.dumps(structured));z.writestr('recipe.html',html);z.writestr('recipe.csv',buff.getvalue());z.writestr('recipe.paprikarecipe',gzip.compress(json.dumps(paprika).encode()));z.writestr('recipe.melarecipe',json.dumps(mela))
 for name,data,count in [('recipes.zip',archive.getvalue(),5),('recipe.paprikarecipe',gzip.compress(json.dumps(paprika).encode()),1),('recipe.melarecipe',json.dumps(mela).encode(),1)]:
  result=p.evaluate('([name,data])=>auditTest.read(new File([new Uint8Array(data)],name)).then(records=>records.map(auditTest.complete))',[name,list(data)])
  assert len(result)==count and all(r['instructions'] and not any(b in str(r['instructions']) for b in BOILER) for r in result),(name,result)
 board={'lists':[{'id':'l','name':'Dinner'}],'cards':[{'id':'c','name':'Trello roast','idList':'l','desc':'Ingredients\n- 2 lb pork\nInstructions\n1. Roast for 4 hours.\n'+ '\n'.join(BOILER)}]}
 result=p.evaluate('(board)=>auditTest.items(board).map(auditTest.complete)',board)
 assert len(result)==1 and 'Roast for 4 hours.' in str(result[0]['instructions']) and not any(b in str(result[0]['instructions']) for b in BOILER)
 assert not errors,errors;ctx.close();print('PASS',filename,width,'numbered RecipeSage, nested/graph/alias/schema/cards/microdata, structured precedence, ambiguity, metadata cleanup, legitimate wording, JSON/HTML/CSV/ZIP/Paprika/Mela/Trello',flush=True)

def repair_tests(browser,filename,width):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,library=library(),seed_progress=True);p.evaluate('auditTest.seed()');p.set_default_timeout(12000);requests=[]
 def request(route):
  url=unquote(route.request.url);requests.append(url)
  if 'unavailable' in url:route.fulfill(status=404,body='Unavailable');return
  if 'r.jina.ai' in url:body=READER;kind='text/plain'
  else:body=json.dumps({'@type':'Recipe','name':'French Dip','recipeIngredient':['3 lb beef'],'url':SOURCE});kind='application/json'
  route.fulfill(status=200,content_type=kind,headers={'Access-Control-Allow-Origin':'*'},body=body)
 p.route('https://**/*',request)
 # Legacy viewer cannot silently write a retry into a previously saved blank recipe.
 before=copy.deepcopy(p.evaluate('repairTest.state()'));saved=p.evaluate('repairTest.storage()');p.evaluate('repairTest.show()');p.wait_for_timeout(80);assert not requests and p.evaluate('repairTest.storage()')==saved;p.evaluate('auditTest.closeViewer()');p.wait_for_timeout(80)
 p.evaluate('repairTest.open()');d=p.locator('#recipeInstructionRepair');d.get_by_role('button',name='Preview saved recipe cleanup',exact=True).click();assert p.evaluate('repairTest.storage()')==saved
 for detail in d.locator('details').all():detail.evaluate('(e)=>e.open=true')
 assert d.get_by_role('button',name='Retry instructions for French Dip (ID 1)',exact=True).is_visible()
 d.get_by_role('button',name='Retry missing instructions from saved URLs',exact=True).click();p.wait_for_function("document.querySelector('#recipeInstructionRepair').textContent.includes('Saved URL retry (review only)')")
 assert p.evaluate('repairTest.storage()')==saved and p.evaluate('repairTest.state()')==before
 assert 'unavailable' in d.inner_text().lower() and 'manual correction' in d.inner_text()
 for detail in d.locator('details').all():detail.evaluate('(e)=>e.open=true')
 for check in d.get_by_role('checkbox').all():check.uncheck()
 for id,name in [(1,'French Dip'),(10,'My renamed dip'),(2,'Pernil'),(8,'Other imported website')]:d.get_by_role('checkbox',name=f'Apply repair to {name} (ID {id})',exact=True).check()
 assert d.get_by_role('button',name='Apply selected repairs',exact=True).is_disabled()
 if filename.startswith('meal-') and width==360:p.screenshot(path='/tmp/import-audit-repair-preview.png')
 with tempfile.TemporaryDirectory() as tmp:
  backup=fixture.verified_backup(p,tmp);assert backup['storage']==saved
  d.get_by_role('button',name='Apply selected repairs',exact=True).click();assert 'Only previewed instructions/notes were changed' in d.inner_text()
 after=p.evaluate('repairTest.state()');storage=p.evaluate('repairTest.storage()')
 for old,new in zip(before['meals'],after['meals']):
  expected=copy.deepcopy(old)
  if old['id'] in [1,10]:expected['instructions']=[{'type':'step','text':t} for t in STEPS]
  if old['id']==2:expected['instructions']=COOK;expected['notes']='My handwritten note: keep 2 tbsp juices.\n'
  if old['id']==8:expected['instructions']=[{'type':'step','text':'Boil water for 10 minutes.'}]
  assert new==expected,(old['id'],new,expected)
 assert before['sessions']==after['sessions'] and before['scales']==after['scales'] and before['prefs']==after['prefs']
 for key,value in saved.items():
  if key!='mealRotationDataV1':assert storage[key]==value,key
 assert sum(url==SOURCE for url in requests)==1,requests
 assert next(m for m in after['meals'] if m['id']==7)['instructions']==[]
 d.get_by_role('button',name='Close',exact=True).click();p.reload();p.evaluate('auditTest.viewer()');assert 'Create an account' not in p.locator('#recipeViewer').inner_text();assert 'Roast 2 lb pork' in p.locator('#recipeViewer').inner_text();p.evaluate('auditTest.closeViewer()');p.wait_for_timeout(100)
 # A second cleanup is idempotent.
 assert not any(row['id'] in [1,2,8,10] and row['ready'] for row in p.evaluate('repairTest.plan([])'))
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING APP SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',filename,width,'URL retry beyond ingredients-only, unavailable source, preview/backup/apply, exact field preservation, progress/links/scales/settings, no duplicates, viewer and idempotence',flush=True)

def failure_tests(browser,filename):
 ctx,p,errors,_=fixture.setup(browser,filename,360,library=library(),seed_progress=False)
 before=p.evaluate('repairTest.storage()');state=p.evaluate('repairTest.state()');pending=[]
 p.route('https://**/*',lambda route:pending.append(route))
 p.evaluate('repairTest.open()');d=p.locator('#recipeInstructionRepair');d.get_by_role('button',name='Retry missing instructions from saved URLs',exact=True).click();p.wait_for_timeout(100)
 assert pending
 d.get_by_role('button',name='Cancel',exact=True).click();p.wait_for_timeout(100)
 for route in pending:
  try:route.abort()
  except Exception:pass
 assert p.evaluate('repairTest.storage()')==before and p.evaluate('repairTest.state()')==state
 p.unroute('https://**/*')
 p.route('https://**/*',lambda route:route.fulfill(status=200,content_type='text/plain',body=READER))
 def preview():
  p.evaluate('repairTest.open()');dialog=p.locator('#recipeInstructionRepair');dialog.get_by_role('button',name='Retry missing instructions from saved URLs',exact=True).click();p.wait_for_function("document.querySelector('#recipeInstructionRepair').textContent.includes('Saved URL retry (review only)')");return dialog
 d=preview()
 with tempfile.TemporaryDirectory() as tmp:
  fixture.verified_backup(p,tmp);p.evaluate('repairTest.fail()');d.get_by_role('button',name='Apply selected repairs',exact=True).click()
  assert 'could not be saved' in d.inner_text() and p.evaluate('repairTest.storage()')==before and p.evaluate('repairTest.state()')==state
  p.evaluate('repairRestoreWrite()')
 d.get_by_role('button',name='Cancel',exact=True).click();d=preview()
 with tempfile.TemporaryDirectory() as tmp:
  fixture.verified_backup(p,tmp);p.evaluate('repairTest.mutate()');changed=p.evaluate('repairTest.storage()');d.get_by_role('button',name='Apply selected repairs',exact=True).click()
  assert 'Saved data changed' in d.inner_text() and p.evaluate('repairTest.storage()')==changed
 assert not errors,errors;ctx.close();print('PASS',filename,'URL cancellation, quota failure, stale-data guard, no partial writes',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:parse_tests(b,filename,width);repair_tests(b,filename,width)
   failure_tests(b,filename)
  b.close()
