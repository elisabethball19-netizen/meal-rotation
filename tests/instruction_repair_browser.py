"""Issue #5: isolated repair UI, safety and existing reimport audit. No real app data."""
import copy,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SAGE='12345678-1234-1234-1234-123456789abc'
SAGE2='22345678-1234-1234-1234-123456789abc'
STEPS=[{'@type':'HowToSection','name':'Fish','itemListElement':[{'@type':'HowToStep','text':'Preheat to 200°C / 390°F. Bake for 15 minutes.'},{'@type':'HowToStep','text':'Serve with [green sauce](https://recipes.test/sauce?amount=2&unit=cup#finish).'}]},{'@type':'HowToSection','name':'Finish','itemListElement':[{'@type':'HowToStep','text':'Rest for 5 minutes.'}]}]
def source(identifier,name='Crispy Fish Tacos',instructions=STEPS,ingredients=None,url=None):
    return {'@type':'Recipe','identifier':identifier,'name':name,'recipeIngredient':ingredients or ['2 fish fillets','1 cup flour'],'recipeInstructions':instructions,'notes':'Source notes must not replace my notes','prepTime':'PT25M','cookTime':'PT15M','url':url or 'https://recipesage.com/app/recipes/'+identifier,'recipeCategory':['New file group']}
def meal(i,identifier,name='Crispy Fish Tacos',**extra):
    m=dict(id=i,name=name,cat='Fish',rotation=False,importSourceId=identifier,recipeSageId=identifier if len(identifier)==36 else '',ingredients=['2 fish fillets','1 cup flour'],notes='My handwritten notes',url='https://recipesage.com/app/recipes/'+identifier,originalRecipeUrl='https://original.test/'+str(i),labels=['Favorite'],linkedMealIds=[50],prep=3,cook=4,total=7,image='keep-image',custom={'unknown':'keep'},ingredientStepLinks=[])
    m.update(extra);return m
MEALS=[meal(1,SAGE,rotation=True,linkGroup='original-fish'),meal(2,SAGE,cat='Dinner',instructions=None,linkGroup='original-fish'),meal(3,SAGE2,instructions='My edited step. Keep overnight.'),meal(4,'partial',instructions=['Heat oil.']),meal(5,'heading',instructions=[{'type':'section','text':'Sauce'}]),meal(6,'placeholder',instructions='Instructions unavailable.'),meal(7,'associations',instructions=[],ingredientStepLinks=[{'step':'old-token','ingredients':['old-ing']}]),meal(8,'progress',instructions=[]),meal(9,'ambiguous-title',name='Shared Title'),meal(10,'conflict',name='Conflicting source',recipeSageId='different-id'),meal(11,'empty-source'),meal(12,'duplicate-source'),meal(13,'duplicate-library'),meal(14,'duplicate-library'),meal(15,'renamed',name='My renamed fish'),meal(16,'no-corroboration',name='Changed title',ingredients=['1 carrot']),meal(17,'url-fallback',importSourceId='',recipeSageId='',sourceUrl='https://original.test/fallback',url='https://original.test/fallback'),meal(18,'unproven',importSourceId='',recipeSageId='',sourceUrl='',url='https://manual.test/recipe',instructions=''),meal(19,'missing-file'),meal(50,'side',name='Side',cat='Sides',rotation=False,instructions='Boil rice.'),meal(51,'same-title-other',name='Shared Title',instructions='Existing other recipe.')]
SOURCES=[source(SAGE),source(SAGE2),source('partial'),source('heading'),source('placeholder'),source('associations'),source('progress',instructions=[]),source('new-same-title','Shared Title'),source('other-same-title','Shared Title'),source('conflict','Conflicting source'),source('empty-source',instructions=[]),source('duplicate-source'),source('duplicate-source',instructions='Different source steps.'),source('duplicate-library'),source('renamed'),source('no-corroboration'),source('',url='https://original.test/fallback'),source('brand-new','A recipe absent from working data')]
HOOK="""window.repairTest={
 schedule:()=>({mealPlans,weekdayCategories,entries:mealPlans.map(p=>getDisplayedWeekdayMealsForPlan(p))}),open:()=>openRecipeInstructionRepair(repairBackup),
 items:r=>recipeImportItems(r),identity:r=>recipeImportIdentity(recipeImportItems([r])[0]),plan:(r,library=meals)=>recipeRepairPlan(recipeImportItems(r),library).rows.map(x=>({id:x.meal.id,match:x.match,ready:x.instructions!==null,reason:x.reason,instructions:x.instructions})),
 state:()=>({cats,active,meals,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs}),
 storage:()=>repairBackup.capture(),restore:b=>{repairBackup.restore(repairBackup.normalize(b));backupRestoreReloadPending=true},normal:r=>showRecipeImportSelection(recipeImportItems(r),'audit.json'),
 extract:(raw)=>extractCompleteRecipe(raw,'https://source.test/recipe','Fixture'),
 corruptProgress:()=>{const m=meals.find(m=>m.id===8),c=cookingContext('original','Tuesday',m.cat,m);cookingSessions.occurrences[cookingOccurrenceKey(c)]={id:'stale',context:c,ingredients:[],steps:['old-step']};localStorage.setItem(COOKING_SESSIONS_KEY,JSON.stringify(cookingSessions))},
 seedProgress:()=>{const edited=meals.find(m=>m.id===3),items=cookingItemTokens(edited);edited.ingredientStepLinks=[{step:items.steps.find(x=>x.token).token,ingredients:[items.ingredients[0].token]}];persist();for(const day of ['Tuesday','Friday']){const m=meals.find(m=>m.id===1),c=cookingContext('original',day,m.cat,m),ing=cookingItemTokens(m).ingredients[0].token;cookingSessions.occurrences[cookingOccurrenceKey(c)]={id:day,context:c,ingredients:day==='Tuesday'?[ing]:[],steps:[],autoIngredients:[],ingredientOverrides:{[ing]:day==='Tuesday'}};occurrenceScales.occurrences[cookingOccurrenceKey(c)]={context:c,multiplier:day==='Tuesday'?2:0.5}}localStorage.setItem(COOKING_SESSIONS_KEY,JSON.stringify(cookingSessions));localStorage.setItem(OCCURRENCE_SCALES_KEY,JSON.stringify(occurrenceScales))},
 show:(day='Tuesday')=>openRecipeViewer(meals.find(m=>m.id===1),cookingContext('original',day,meals.find(m=>m.id===1).cat,meals.find(m=>m.id===1))),persist:()=>persist(),
 fail:()=>{const original=localStorage.setItem.bind(localStorage);localStorage.setItem=(k,v)=>{if(k==='mealRotationDataV1')throw Error('QuotaExceededError');original(k,v)};window.repairRestoreWrite=()=>{localStorage.setItem=original}},
 saveProgress:()=>writeCookingSessions(cookingSessions),saveScales:()=>localStorage.setItem(OCCURRENCE_SCALES_KEY,JSON.stringify(occurrenceScales)),
 mutate:()=>{meals.find(m=>m.id===1).notes+=' changed';persist()}
};"""

def setup(browser,filename,width,library=None,seed_progress=True,weekdays=None):
    ctx=browser.new_context(viewport={'width':width,'height':851},is_mobile=width<600,has_touch=width<600,accept_downloads=True)
    page=ctx.new_page();page.set_default_timeout(10000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    storage='testStorage' if filename.startswith('meal-') else 'localStorage';prefix='mealRotationTestSandboxV1:' if storage=='testStorage' else ''
    src=(ROOT/filename).read_text().replace('function validateBackupCore(d){','window.repairBackup={capture:captureBackupStorage,validate:validateBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){')
    src=src.replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK.replace('localStorage',storage)+'})();')
    seed={prefix+'mealRotationDataV1':json.dumps({'cats':['Fish','Dinner','Sides'],'active':'Fish','meals':MEALS if library is None else library}),prefix+'mealRotationWeekdayCategoriesV1':json.dumps(weekdays or {'Tuesday':['Fish'],'Friday':['Fish']}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps({'mode':'split','ratio':.4,'syncIngredients':True,'autoCompleteIngredients':True,'keepScreenAwake':False}),prefix+'mealRotationSelectedIngredientsV1':json.dumps({'1':['2 fish fillets']}),prefix+'mealRotationCheckedIngredientsV1':json.dumps(['1 cup flour']),prefix+'mealRotationCustomSettingV9':'preserve-unknown-setting',prefix+'mealRotationTutorialStageV1':'done'}
    if prefix:seed['mealRotationDataV1']='WORKING APP SENTINEL';seed['mealRotationCookingSessionsV1']='WORKING PROGRESS SENTINEL'
    page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
    page.route('http://meal.test/**',lambda route:route.fulfill(status=200,content_type='text/html',body=src) if route.request.url.endswith(filename) else route.fulfill(status=200,body=''))
    page.route('https://**/*',lambda route:route.fulfill(status=200,body=''))
    page.goto('http://meal.test/'+filename)
    if seed_progress:page.evaluate('repairTest.seedProgress()')
    return ctx,page,errors,prefix

def upload(page,name,data,filename='recipesage.json'):
    with page.expect_file_chooser() as fc:page.get_by_role('button',name=name,exact=True).click()
    payload=data if isinstance(data,bytes) else json.dumps(data).encode()
    fc.value.set_files({'name':filename,'mimeType':'application/json','buffer':payload})
    page.wait_for_timeout(60)

def verified_backup(page,tmp):
    with page.expect_download() as event:page.get_by_role('button',name='Download complete backup',exact=True).click()
    target=Path(tmp)/'backup.json';event.value.save_as(target)
    upload(page,'Verify downloaded backup',target.read_bytes(),'backup.json')
    assert page.get_by_role('button',name='Apply instruction repair',exact=True).is_enabled()
    return json.loads(target.read_text())

def run(browser,filename,width):
    ctx,page,errors,prefix=setup(browser,filename,width)
    state=lambda:page.evaluate('repairTest.state()')
    storage=lambda:page.evaluate('repairTest.storage()')
    baseline=copy.deepcopy(state());saved=storage()
    # The settings entry itself is reachable; no automatic repair on load.
    assert next(m for m in baseline['meals'] if m['id']==1).get('instructions') is None
    page.get_by_role('button',name='Settings and backups',exact=True).click()
    page.locator('details[data-settings-group="backups"]').evaluate('(e)=>e.open=true')
    baseline=copy.deepcopy(state());saved=storage()
    page.get_by_role('button',name='Repair RecipeSage Imports',exact=True).click()
    assert page.locator('#recipeInstructionRepair').is_visible()
    assert storage()==saved and state()==baseline
    page.evaluate('repairTest.corruptProgress()'); plan=page.evaluate('(r)=>repairTest.plan(r)',SOURCES)
    page.evaluate('delete repairTest.state().sessions.occurrences[JSON.stringify(["original","Tuesday","8",""])];repairTest.saveProgress();repairTest.persist()')
    baseline=copy.deepcopy(state());saved=storage()
    ready=[r['id'] for r in plan if r['ready']];assert ready==[1,2,15,17],plan
    assert next(r for r in plan if r['id']==7)['reason'].startswith('Existing instruction associations')
    assert next(r for r in plan if r['id']==8)['reason'].startswith('Saved instruction progress')
    assert next(r for r in plan if r['id']==12)['reason'].startswith('Ambiguous')
    assert next(r for r in plan if r['id']==13)['reason'].startswith('Several unrelated')
    assert next(r for r in plan if r['id']==18)['reason'].startswith('No saved import provenance')
    assert not page.get_by_role('button',name='Apply instruction repair',exact=True).is_enabled()
    upload(page,'Choose RecipeSage file',SOURCES)
    dialog=page.locator('#recipeInstructionRepair');assert '4 empty records ready' in dialog.inner_text()
    dialog.locator('details').filter(has_text='(ID 1, Fish)').locator('summary').click()
    assert '200°C / 390°F' in dialog.inner_text() and '15 minutes' in dialog.inner_text()
    assert 'https://recipes.test/sauce?amount=2&unit=cup#finish' in dialog.inner_text()
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert storage()==saved and state()==baseline
    # Cancel preview and invalid files are write-free.
    page.get_by_role('button',name='Cancel',exact=True).click();assert storage()==saved
    page.evaluate('repairTest.open()');upload(page,'Choose RecipeSage file',b'{broken')
    assert 'No repair applied' in page.locator('#recipeInstructionRepair').inner_text();assert storage()==saved
    upload(page,'Choose RecipeSage file',[]);assert 'No recipes were found' in dialog.inner_text()
    upload(page,'Choose RecipeSage file',SOURCES)
    with tempfile.TemporaryDirectory() as tmp:
        backup=verified_backup(page,tmp);assert backup['version']==2 and backup['storage']==saved
        # A truncated/incomplete/old backup cannot authorize repairs.
        upload(page,'Verify downloaded backup',{'version':2,'storage':{'mealRotationDataV1':saved['mealRotationDataV1']}})
        assert page.get_by_role('button',name='Apply instruction repair',exact=True).is_disabled()
        verified_backup(page,tmp)
        # Storage failure leaves every key and every in-memory record untouched.
        page.evaluate('repairTest.fail()');page.get_by_role('button',name='Apply instruction repair',exact=True).click()
        assert 'No recipes were changed' in dialog.inner_text();assert storage()==saved and state()==baseline
        page.evaluate('repairRestoreWrite()');verified_backup(page,tmp)
        # Selecting another export invalidates previous verification.
        upload(page,'Choose RecipeSage file',SOURCES);assert page.get_by_role('button',name='Apply instruction repair',exact=True).is_disabled()
        verified_backup(page,tmp)
        if width==320:page.screenshot(path='/workspace/issue5-repair-preview-'+filename+'.png')
        page.get_by_role('button',name='Apply instruction repair',exact=True).click()
        assert 'Restored instructions for 4' in dialog.inner_text()
        after=state();after_storage=storage()
        assert set(after_storage)==set(saved)
        assert {k:v for k,v in after_storage.items() if k!='mealRotationDataV1'}=={k:v for k,v in saved.items() if k!='mealRotationDataV1'}
        assert {k:v for k,v in after.items() if k!='meals'}=={k:v for k,v in baseline.items() if k!='meals'}
        for old,new in zip(baseline['meals'],after['meals']):
            if old['id'] in ready:
                assert {k:v for k,v in old.items() if k!='instructions'}=={k:v for k,v in new.items() if k!='instructions'}
                assert 'Rest for 5 minutes.' in json.dumps(new['instructions'])
                assert 'https://recipes.test/sauce?amount=2&unit=cup#finish' in json.dumps(new['instructions'])
            else:assert old==new
        page.get_by_role('button',name='Close',exact=True).click()
        # Reconciliation/persist and a reload preserve all existing progress/scales.
        page.evaluate('repairTest.persist()');assert storage()==after_storage
        page.reload();assert storage()==after_storage, {k:(after_storage.get(k),storage().get(k)) for k in set(after_storage)|set(storage()) if after_storage.get(k)!=storage().get(k)}
        page.evaluate('repairTest.open()');upload(page,'Choose RecipeSage file',SOURCES)
        assert '0 empty records ready' in page.locator('#recipeInstructionRepair').inner_text()
        assert page.get_by_role('button',name='Download complete backup',exact=True).is_disabled()
        page.get_by_role('button',name='Cancel',exact=True).click()
        # Repaired viewer uses the old source URL, separate scales/progress and normal completion.
        page.evaluate('repairTest.show("Tuesday")')
        assert '4 fish fillets' in page.locator('.recipe-viewer-ingredients').inner_text()
        assert page.locator('.recipe-original').get_attribute('href')=='https://original.test/1'
        page.locator('.recipe-viewer-steps .cooking-item').first.click()
        sessions=state()['sessions']['occurrences'];assert len(sessions[json.dumps(['original','Tuesday','1',''],separators=(',',':'))]['steps'])==1
        assert sessions[json.dumps(['original','Friday','1',''],separators=(',',':'))]['steps']==[]
        page.get_by_role('button',name='Close recipe',exact=True).click()
        page.evaluate('repairTest.show("Friday")');assert '1 fish fillets' in page.locator('.recipe-viewer-ingredients').inner_text()
        page.get_by_role('button',name='Close recipe',exact=True).click()
        # Existing V2 restoration accepts and exactly restores the verified pre-repair backup.
        page.evaluate('(b)=>repairTest.restore(b)',backup);assert storage()==saved
        page.reload();assert page.evaluate('repairTest.state().meals.find(m=>m.id===1).instructions===undefined')
    if prefix:
        assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING APP SENTINEL'
        assert page.evaluate('localStorage.getItem("mealRotationCookingSessionsV1")')=='WORKING PROGRESS SENTINEL'
    assert not errors,errors
    ctx.close()
    # Stale preview/backup: actual memory or other-tab storage changes block apply.
    ctx,page,errors,_=setup(browser,filename,width)
    page.evaluate('repairTest.open()');upload(page,'Choose RecipeSage file',SOURCES)
    with tempfile.TemporaryDirectory() as tmp:
        verified_backup(page,tmp);page.evaluate('repairTest.mutate()');changed=page.evaluate('repairTest.storage()')
        page.get_by_role('button',name='Apply instruction repair',exact=True).click()
        assert 'Saved data changed' in page.locator('#recipeInstructionRepair').inner_text()
        assert page.evaluate('repairTest.storage()')==changed
    assert not errors,errors;ctx.close()
    print('PASS',filename,str(width)+'px: preview/matching, verified complete backup, failure/stale guards, instruction-only writes, idempotence, exact progress/settings preservation, backup restore, test isolation; no JS errors',flush=True)

def audit(browser,filename):
    ctx,page,errors,_=setup(browser,filename,360)
    before=page.evaluate('repairTest.state()')
    # Existing normal import: IDs deduplicate, broader missing fields and reference metadata fill.
    r=source(SAGE);r['linkedRecipes']=[{'name':'Reference metadata','url':'https://source.test/side'}]
    page.evaluate('(r)=>repairTest.normal([r])',r);page.locator('#recipeImportDialog').get_by_role('button',name='Import recipes',exact=True).click()
    after=page.evaluate('repairTest.state()');assert len(after['meals'])==len(before['meals'])
    assert next(m for m in after['meals'] if m['id']==1)['id']==1 and next(m for m in after['meals'] if m['id']==1)['ingredients']==next(m for m in before['meals'] if m['id']==1)['ingredients'] and next(m for m in after['meals'] if m['id']==1)['notes']==next(m for m in before['meals'] if m['id']==1)['notes']
    assert next(m for m in after['meals'] if m['id']==1)['instructions'] and next(m for m in after['meals'] if m['id']==1)['recipeImportReferences']
    assert next(m for m in after['meals'] if m['id']==3)==next(m for m in before['meals'] if m['id']==3)
    # A changed source identity is a new import, regardless of similar/exact title.
    page.get_by_role('button',name='OK',exact=True).click()
    page.evaluate('(r)=>repairTest.normal([r])',source('new-source-id'))
    page.locator('#recipeImportDialog').get_by_role('button',name='Import recipes',exact=True).click()
    after2=page.evaluate('repairTest.state()');assert len(after2['meals'])==len(before['meals'])+1 and not next(m for m in after2['meals'] if m['importSourceId']=='new-source-id')['rotation']
    assert next(m for m in after2['meals'] if m['importSourceId']=='new-source-id')['name']=='Crispy Fish Tacos'
    assert not errors,errors;ctx.close()
    print('PASS',filename,'normal reimport audit: same-ID enrich/deduplicate, existing edits retained, changed-ID duplicate confirmed',flush=True)


def extraction_and_matching(browser,filename):
    ctx,page,errors,_=setup(browser,filename,360)
    r=source('fixture','Fixture')
    for raw in [json.dumps(r),json.dumps({'data':{'recipes':[r]}}),'<script type="application/ld+json">'+json.dumps({'@type':'Organization','name':'Site'})+'</script><script type="application/ld+json">'+json.dumps({'@graph':[r]})+'</script>']:
        result=page.evaluate('(raw)=>repairTest.extract(raw)',raw)
        text=json.dumps(result['instructions']);assert 'Preheat to 200' in text and 'Rest for 5 minutes' in text and 'https://recipes.test/sauce?amount=2&unit=cup#finish' in text
        assert result['ingredients']==r['recipeIngredient']
    html='<article itemscope itemtype="https://schema.org/Recipe"><h1 itemprop="name">Fixture</h1><div itemprop="recipeIngredient">2 fish fillets</div><div itemprop="recipeInstructions"><h2>Fish</h2><p>Heat to 200°C.</p><p>Cook for 15 minutes.</p></div></article>'
    result=page.evaluate('(raw)=>repairTest.extract(raw)',html);assert [x['text'] for x in result['instructions']]==['Fish','Heat to 200°C.','Cook for 15 minutes.']
    for raw in ['', '<html><title>Access denied</title><body>Sign in</body></html>','<html><body><div id="app"></div><script>renderRecipe()</script></body></html>']:
        result=page.evaluate('(raw)=>repairTest.extract(raw)',raw);assert not result or not result['instructions']
    # Stable importer-generated IDs and namespaced aliases also require corroboration.
    no_id=source('','No ID Recipe',url='');no_id.pop('url')
    identity=page.evaluate('(r)=>repairTest.identity(r)',no_id)
    target=meal(80,identity,name='No ID Recipe',url='',recipeSageId='')
    assert page.evaluate('(a)=>repairTest.plan([a[0]],[a[1]])',[no_id,target])[0]['ready']
    target['name']='Different recipe';assert not page.evaluate('(a)=>repairTest.plan([a[0]],[a[1]])',[no_id,target])[0]['ready']
    alias={'title':'Namespaced','id':'42','ingredients':['2 fish fillets','1 cup flour'],'instructions':'Bake for 15 minutes.'}
    target=meal(81,'mela:42',name='Namespaced',url='',recipeSageId='')
    assert page.evaluate('(a)=>repairTest.plan([a[0]],[a[1]])',[alias,target])[0]['ready']
    # Preserve generic component references in repairs; recognized clutter still goes.
    r=source(SAGE,instructions='## Sauce\nMix 2 cups flour.\n[Green sauce](https://recipes.test/sauce)\n## Linked Recipes\n[Side](https://recipes.test/side)\n## Finish\nBake at 180°C for 20 minutes.\n![Image](https://images.test/a.jpg)\nCreate an account to save this recipe\nLast edited: 2026-10-01')
    row=page.evaluate('(r)=>repairTest.plan([r]).find(x=>x.id===1)',r);text=json.dumps(row['instructions'])
    assert 'https://recipes.test/side' in text and 'https://recipes.test/sauce' in text and '180' in text and '20 minutes' in text
    assert 'Create an account' not in text and 'images.test' not in text and 'Last edited' not in text
    r=source(SAGE,instructions='<h2>Sauce</h2><p>Mix flour.</p><footer>Rest for 12 minutes.</footer><form>Fold in cheese.</form><p>![Bake until golden](https://images.test/meaningful.jpg)</p>')
    row=page.evaluate('(r)=>repairTest.plan([r]).find(x=>x.id===1)',r);text=json.dumps(row['instructions'])
    assert 'Rest for 12 minutes' in text and 'Fold in cheese' in text and 'Bake until golden' in text and 'meaningful.jpg' in text
    r=source(SAGE,instructions=[{'@type':'HowToStep','text':'Serve with <a href="https://recipes.test/sauce?amount=2&amp;unit=cup#finish">green sauce</a>.'}])
    row=page.evaluate('(r)=>repairTest.plan([r]).find(x=>x.id===1)',r)
    assert 'https://recipes.test/sauce?amount=2&unit=cup#finish' in json.dumps(row['instructions'])
    assert not errors,errors;ctx.close()
    print('PASS',filename,'structured RecipeSage/JSON-LD/HTML extraction, unavailable pages, identity aliases, conservative repair references',flush=True)

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            extraction_and_matching(browser,filename)
            audit(browser,filename)
            for width in [320,360,1280]:run(browser,filename,width)
        browser.close()
