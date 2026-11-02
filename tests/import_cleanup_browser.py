"""Import cleanup regressions in Chromium. Hooks are injected only into routed test pages."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SAGE='11111111-2222-4333-8444-555555555555'
DIRTY='''## Sauce
1. Preheat to 180°C / 350°F for 25 minutes.
2. Mix 2 tbsp oil and 1½ cups flour.
3. ![Photo](https://images.test/prep.jpg)
4. https://images.test/finished.png?width=800
5. ![Plate][photo]
[photo]: https://images.test/plate.webp
## Linked Recipes
- [Garlic Bread](https://recipes.test/bread)
- [New Sauce](https://recipes.test/new-sauce)
- Unavailable Dressing
Create an account
Log in
Created: 2026-10-15T10:30:00Z
Last edited: 2026-11-01T12:00:00Z
Privacy Policy
Powered by RecipeSage
## Finish
6. Bake for 25 minutes at 350°F.
An unusual family note that may be useful.
'''
BASE=[dict(id=1,name='Main recipe',cat='Dinner',rotation=True,url='https://recipes.test/main',originalRecipeUrl='https://original.test/main',ingredients=['2 tbsp oil','1½ cups flour'],instructions=DIRTY),dict(id=2,name='Garlic Bread',cat='Dinner',rotation=False,importSourceId='bread-id',url='https://recipes.test/bread',ingredients=['1 loaf bread'],instructions='Toast bread for 5 minutes.'),dict(id=3,name='Garlic Bread with Cheese',cat='Dinner',rotation=False,url='https://recipes.test/cheesy-bread',ingredients=['1 loaf bread','1 cup cheese'],instructions='Toast with cheese.')]
HOOK='''window.importTest={cleanup:cleanupRecipeInstructions,complete:completeRecipeFields,extract:extractCompleteRecipe,items:recipeImportItems,csv:recipeImportCsv,html:recipeImportHtml,trello:recipeImportTrelloBoard,read:recipeImportReadFile,match:(ref,lib)=>findRelatedImportedMeal(ref,lib||meals,meals.find(m=>m.id===1)),state:()=>({meals,cats,sessions:cookingSessions}),open:()=>openRecipeViewer(meals.find(m=>m.id===1),cookingContext('original','Monday','Dinner',meals.find(m=>m.id===1))),review:(ids=[1],preview=true)=>openRecipeImportReview(meals.filter(m=>ids.includes(m.id)),preview),importItems:items=>showRecipeImportSelection(recipeImportItems(items),'fixture.json'),backup:()=>{const d={cats,meals};window.importBackupTest.validate(d);return window.importBackupTest.normalize(d)},fill:(details)=>{const copy={...meals[0]};fillMissingRecipeContent(copy,details);return copy},failSave:()=>{const old=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.endsWith('mealRotationDataV1'))throw Error('Quota');return old.call(this,k,v)};return true}};'''

def run(browser,filename):
    context=browser.new_context(viewport={'width':393 if filename=='index.html' else 360,'height':851},is_mobile=True,has_touch=True)
    page=context.new_page();page.set_default_timeout(7000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    source=(ROOT/filename).read_text().replace('function validateBackupCore(d){','window.importBackupTest={validate:validateBackupCore,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK+'})();')
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Dinner'],active='Dinner',meals=BASE)),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Monday':['Dinner']})}
    page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}')
    page.route('http://meal.test/**',lambda route:route.fulfill(status=200,content_type='text/html',body=source) if route.request.url.endswith(filename) else route.fulfill(status=200,body=''))
    fetched=[]
    def request(route):
        fetched.append(route.request.url)
        if 'new-sauce' in route.request.url:
            body={'@type':'Recipe','name':'New Sauce','recipeIngredient':['1 cup tomatoes'],'recipeInstructions':'Simmer tomatoes for 20 minutes.\nCreate an account','url':'https://recipes.test/new-sauce'}
            route.fulfill(status=200,content_type='application/json',headers={'Access-Control-Allow-Origin':'*'},body=json.dumps(body))
        else:route.fulfill(status=200,content_type='text/html',headers={'Access-Control-Allow-Origin':'*'},body='<h1>Log in</h1>Create an account')
    page.route('https://**/*',request)
    page.goto('http://meal.test/'+filename)
    def state():return page.evaluate('importTest.state()')
    def evaluate(name,value):return page.evaluate('(arg)=>importTest[arg[0]](arg[1])',[name,value])
    # Pure parser checks use the actual DOM/Markdown parser in the browser.
    cleaned=evaluate('cleanup',DIRTY)
    texts='\n'.join(b['text'] for b in cleaned['instructions'])
    for good in ['180°C / 350°F','25 minutes','2 tbsp oil','1½ cups flour','Sauce','Finish','An unusual family note']:assert good in texts,good
    for bad in ['![','images.test','Linked Recipes','Create an account','Log in','2026-','Privacy Policy','Powered by']:assert bad not in texts,bad
    assert len(cleaned['related'])==3
    assert evaluate('cleanup','1. ![Photo](<https://images.test/a.png>)')['instructions']==[]
    inline=evaluate('cleanup','Stir for 2 minutes. ![Photo](https://images.test/a.png)')
    assert inline['instructions'][0]['text']=='Stir for 2 minutes.'
    for raw in ['Create an account to save this recipe','Sign in or create an account','**1** Linked Recipes\n[Garlic Bread](https://recipes.test/bread)']:
        assert evaluate('cleanup',raw)['instructions']==[],(raw,evaluate('cleanup',raw))
    assert evaluate('cleanup','## Related Recipes\nLeave for 20 minutes.\nFold in cheese.')['instructions']==[{'type':'step','text':'Leave for 20 minutes.'},{'type':'step','text':'Fold in cheese.'}]
    assert evaluate('cleanup','## Related Recipes\nGarlic Bread\nInstructions\nBake for 10 minutes.')['instructions'][-2:]==[{'type':'step','text':'Instructions'},{'type':'step','text':'Bake for 10 minutes.'}]

    assert all(b['text'].strip() not in ['3.','4.','5.'] for b in cleaned['instructions'])
    assert evaluate('cleanup',cleaned['instructions'])['instructions']==cleaned['instructions'],'cleanup must be idempotent'
    uncertain='Created a smooth dough and rest for 30 minutes.\nLog in your cooking journal the time the dough doubled.\n350°F for 30 minutes\n2.5 cups of broth\nA discount may be available from your local butcher.'
    assert '\n'.join(b['text'] for b in evaluate('cleanup',uncertain)['instructions'])==uncertain
    html='<h2>Sauce</h2><p>Mix 2 tbsp oil.</p><p>2. <img src="https://images.test/a.jpg"></p><h2>Related Recipes</h2><p><a href="https://recipes.test/bread">Garlic Bread</a></p><form>Create account</form><h2>Finish</h2><p>Bake at 180°C for 25 minutes.</p>'
    hc=evaluate('cleanup',html);assert hc['related'][0]['url']=='https://recipes.test/bread';assert [b['text'] for b in hc['instructions']]==['Sauce','Mix 2 tbsp oil.','Finish','Bake at 180°C for 25 minutes.']
    structured={'@type':'Recipe','name':'RecipeSage fixture','identifier':SAGE,'recipeIngredient':['1 cup flour'],'recipeInstructions':DIRTY,'url':'https://recipes.test/original','prepTime':'PT10M','cookTime':'PT25M','notes':'Keep this meaningful note.'}
    details=evaluate('complete',structured);assert details['prep']==10 and details['cook']==25 and details['originalRecipeUrl']==structured['url'];assert len(details['recipeImportReferences'])==3
    for raw in [json.dumps(structured),'<script type="application/ld+json">'+json.dumps(structured)+'</script>',json.dumps({'contents':json.dumps(structured)})]:
        extracted=evaluate('extract',raw);assert len(extracted['recipeImportReferences'])==3;assert not any('images.test' in b['text'] for b in extracted['instructions'])
    for shape in [DIRTY,{'markdown':DIRTY},[{'@type':'HowToStep','text':line} for line in DIRTY.splitlines()]]:
        assert len(evaluate('complete',dict(structured,recipeInstructions=shape))['recipeImportReferences'])==3
    csv='name,instructions\n"CSV recipe",'+json.dumps(DIRTY).replace('\\n','\n')
    # Actual CSV quoting with embedded newlines.
    import csv as csv_module,io
    buff=io.StringIO();writer=csv_module.writer(buff);writer.writerow(['name','instructions']);writer.writerow(['CSV recipe',DIRTY])
    cr=evaluate('csv',buff.getvalue());assert len(evaluate('complete',cr[0])['recipeImportReferences'])==3
    board={'lists':[{'id':'L','name':'Dinner'}],'cards':[{'id':'T','idList':'L','name':'Trello recipe','desc':'## Instructions\n'+DIRTY}]}
    tr=evaluate('trello',board);assert len(evaluate('complete',tr[0])['recipeImportReferences'])==3
    # File parsing preserves its structured source for the same cleanup pipeline.
    assert page.evaluate('(r)=>importTest.read(new File([JSON.stringify(r)],"fixture.json")).then(items=>importTest.complete(items[0]).recipeImportReferences.length)',structured)==3
    # Reliable IDs/URLs win; similar and ambiguous titles never match.
    assert evaluate('match',{'name':' GARLIC   BREAD '})['id']==2
    assert evaluate('match',{'name':'Garlic Bread','url':'https://different.test/bread'}) is None
    assert evaluate('match',{'name':'Garlic'}) is None
    assert page.evaluate('importTest.match({name:"Bread",url:"https://recipes.test/plain"},[{id:10,name:"Bread"}]).id')==10
    assert page.evaluate('importTest.match({name:"Bread"},[{id:10,name:"Bread"},{id:11,name:"Bread"}])') is None
    assert page.evaluate('importTest.match({sourceId:"bread-id"}).id')==2
    assert page.evaluate('(uuid)=>importTest.match({url:"https://recipesage.com/app/recipes/"+uuid},[{id:9,name:"Source recipe",recipeSageId:uuid,url:"https://original.test/recipe"}]).id',SAGE)==9
    original=state();assert original['meals'][0]['instructions']==DIRTY,'opening app must not rewrite existing recipes'
    # Existing-recipe review is accessible from Recipe settings, and Cancel saves nothing.
    page.evaluate('importTest.open()');page.locator('.recipe-viewer-steps .cooking-item').first.click();progress=state()['sessions']
    page.get_by_role('button',name='Recipe settings',exact=True).click();page.get_by_role('button',name='Review instruction cleanup / related recipes',exact=True).click()
    dialog=page.locator('#recipeImportReview');assert dialog.is_visible()
    assert dialog.locator('input:checked').count()==0
    assert 'Create an account' not in dialog.get_by_role('textbox').input_value()
    assert '350°F' in dialog.get_by_role('textbox').input_value()
    buttons=dialog.locator('.meal-unified-actions').bounding_box();assert buttons['y']+buttons['height']<=851
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if filename=='index.html':page.screenshot(path='/workspace/import-cleanup-review.png')
    dialog.get_by_role('button',name='Cancel recipe review').click();assert state()==dict(original,sessions=progress)
    page.evaluate('importTest.review()');page.get_by_role('button',name='Save reviewed recipe changes').click()
    assert state()['sessions']==progress;assert next(m for m in state()['meals'] if m['id']==1)['linkedMealIds']==[]
    assert len(state()['meals'])==3 and all(not m['rotation'] for m in state()['meals'][1:])
    assert next(m for m in state()['meals'] if m['id']==1)['originalRecipeUrl']=='https://original.test/main'
    page.evaluate('importTest.review()');page.get_by_role('checkbox',name='Link Garlic Bread',exact=True).check();page.get_by_role('button',name='Save reviewed recipe changes').click()
    assert next(m for m in state()['meals'] if m['id']==1)['linkedMealIds']==[2];assert len(state()['meals'])==3;assert not fetched
    page.evaluate('importTest.review()');assert page.get_by_role('checkbox',name='Link Garlic Bread',exact=True).is_checked();page.get_by_role('button',name='Cancel recipe review').click()
    # Reopening and backups retain metadata, ordinary linkedMealIds, and original URLs.
    assert page.evaluate('importTest.backup().mealRotationDataV1')
    page.get_by_role('button',name='Close recipe',exact=True).click();page.wait_for_timeout(100);page.reload()
    assert next(m for m in state()['meals'] if m['id']==1)['linkedMealIds']==[2];assert len(next(m for m in state()['meals'] if m['id']==1)['recipeImportReferences'])==3
    # A missing recipe is fetched only when selected, then reused for another parent.
    page.evaluate('importTest.review()');page.get_by_role('checkbox',name='Link New Sauce',exact=True).check();page.get_by_role('button',name='Save reviewed recipe changes').click()
    page.wait_for_function('!document.querySelector("#recipeImportReview")')
    sauce=[m for m in state()['meals'] if m['name']=='New Sauce'];assert len(sauce)==1 and not sauce[0]['rotation'];assert len(fetched)==1
    assert len(sauce[0]['ingredients'])==1;assert 'Create an account' not in str(sauce[0]['instructions'])
    page.evaluate('importTest.review()');page.get_by_role('button',name='Save reviewed recipe changes').click();assert len(state()['meals'])==4;assert len(fetched)==1
    page.evaluate("history.replaceState({},'')")
    page.goto('http://meal.test/'+filename)
    # Bulk imports clean automatically but do not create/schedule any mentioned targets.
    evaluate('importItems',[dict(structured,name='Another main',identifier='bulk-main')]);page.get_by_role('button',name='Import recipes',exact=True).click()
    page.get_by_role('button',name='Review related recipes',exact=True).click();assert page.locator('#recipeImportReview input:checked').count()==0
    before=state();page.get_by_role('checkbox',name='Link Garlic Bread',exact=True).check();page.get_by_role('checkbox',name='Link New Sauce',exact=True).check();page.get_by_role('button',name='Save reviewed recipe changes').click()
    bulk=[m for m in state()['meals'] if m['name']=='Another main'][0];assert len(bulk['linkedMealIds'])==2 and not bulk['rotation'];assert len(state()['meals'])==len(before['meals']);assert len(fetched)==1
    assert not any('images.test' in b['text'] for b in bulk['instructions'])
    alias=dict(structured,name='Alias references',identifier='alias-main',recipeInstructions='Cook for 5 minutes.',relatedRecipes=[{'name':'Garlic Bread','id':'bread-id'},{'name':'Garlic Bread','url':'https://recipes.test/bread'},{'name':'Alias references','id':'alias-main'}])
    evaluate('importItems',[alias]);page.get_by_role('button',name='Import recipes',exact=True).click();page.get_by_role('button',name='Review related recipes',exact=True).click()
    assert page.get_by_role('checkbox',name='Link Garlic Bread',exact=True).count()==1
    assert page.get_by_role('checkbox',name='Link Alias references',exact=True).is_disabled()
    page.get_by_role('checkbox',name='Link Garlic Bread',exact=True).check();page.get_by_role('button',name='Save reviewed recipe changes').click()
    assert [m for m in state()['meals'] if m['name']=='Alias references'][0]['linkedMealIds']==[2]
    # Empty/login-only source cannot produce an empty placeholder or partial saved changes.
    page.evaluate('importTest.review([1])');before=state();area=page.get_by_role('textbox');area.fill(area.input_value()+'\nKeep a reviewed addition.')
    # An unavailable source is tested with a synthetic import whose reference has a URL.
    page.get_by_role('button',name='Cancel recipe review').click()
    evaluate('importItems',[dict(structured,name='Failure main',identifier='failure-main',relatedRecipes=[{'name':'Missing dish','url':'https://recipes.test/missing'}])]);page.get_by_role('button',name='Import recipes',exact=True).click();page.get_by_role('button',name='Review related recipes',exact=True).click()
    before=state();page.get_by_role('checkbox',name='Link Missing dish',exact=True).check();page.get_by_role('button',name='Save reviewed recipe changes').click()
    page.wait_for_function('document.querySelector("#recipeImportReview [role=status]").textContent.includes("No changes")||document.querySelector("#recipeImportReview [role=status]").textContent.includes("could not")')
    assert state()==before;assert not any(m['name']=='Missing dish' for m in state()['meals']);page.get_by_role('button',name='Cancel recipe review').click()
    # Test storage remains isolated and save failure keeps the original recipe and open draft.
    if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")') is None
    page.evaluate('importTest.review([1])');page.get_by_role('textbox').fill('Changed only in preview.');before=state();page.evaluate('importTest.failSave()');page.get_by_role('button',name='Save reviewed recipe changes').click();assert state()==before;assert 'could not be saved' in page.locator('#recipeImportReview [role=status]').inner_text();page.get_by_role('button',name='Cancel recipe review').click()
    assert not errors,errors
    print('PASS',filename,'cleanup formats, preservation, preview/cancel, matching, opt-in linking, no duplicate/placeholder/schedule, source failure, save failure, backup, mobile UI; no JS errors',flush=True)
    context.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:run(browser,filename)
        browser.close()
