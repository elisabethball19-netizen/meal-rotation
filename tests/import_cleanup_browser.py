"""Automatic conservative cleanup regressions; hooks are injected only in test pages."""
import csv,io,json
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SAUCE='https://recipes.test/green__sauce?amount=2&unit=cup#prepare'
DIRTY=f'''## Sauce
1. Mix onions at 180°C / 350°F for 10 minutes.
2. Add [green sauce]({SAUCE}) and rest for 5 minutes.
3. ![Photo](https://images.test/prep.jpg)
[photo]: https://images.test/plate.png
Create an account to save recipes
Log in
Created: 2026-10-15T10:30:00Z
Last edited: 2026-11-01T12:00:00Z
Advertisement
https://google-analytics.com/collect?tracking=1
## You might also like
- [Chocolate cake](https://recipes.test/cake)
- [More cookies](https://recipes.test/cookies)
## Finish
3. Serve with [rice](https://recipes.test/rice).
Dwell under the cloche until the aroma mellows.
## Linked recipes
[Spice blend](https://recipes.test/spices)
'''
CLEAN=[{'type':'section','text':'Aromatic finish'},{'type':'step','text':'Fold ½ cup herbs into 2.5 cups broth at 85°C for 7 minutes.'},{'type':'step','text':f'Use [green sauce]({SAUCE}) if desired.'},{'type':'step','text':'Create a smooth paste. Log the resting time in your cooking journal.'}]
HTML=f'<h2>Sauce</h2><p>Mix onions for 10 minutes.</p><p>Add <a href="{SAUCE}">green sauce</a> and rest.</p><p>Log in</p><h2>Finish</h2><p>Serve warm.</p>'
BASE=[dict(id=1,name='Imported main',cat='Main',rotation=True,importSourceId='source-main',url='https://recipes.test/main',originalRecipeUrl='https://original.test/main?source=kept#recipe',linkedMealIds=[2],ingredients=['2 onions','1 cup rice'],instructions=DIRTY,notes='Keep this note and its exact amount: ½ cup.',storedImportedSource={'raw':'Already saved source payload'}),dict(id=2,name='Intentional side',cat='Side',rotation=False,ingredients=['1 loaf bread'],instructions='Toast bread for 5 minutes.'),dict(id=3,name='Legacy HTML',cat='Other',rotation=True,recipeSageId='11111111-2222-4333-8444-555555555555',url='https://recipes.test/legacy',instructions=HTML,ingredients=['2 onions']),dict(id=4,name='Already clean',cat='Ideas',rotation=False,importSourceId='clean-source',instructions=CLEAN,ingredients=['1 cup herbs']),dict(id=5,name='Ambiguous context',cat='Ideas',rotation=False,importSourceId='ambiguous',instructions='## You might also like\n[suggested](https://recipes.test/suggested)\nDwell until the aroma mellows.',ingredients=['1 cup broth'])]
BASE.extend([dict(id=6,name='Storage failure',cat='Ideas',rotation=False,importSourceId='failure',instructions=DIRTY,ingredients=[]),dict(id=8,name='Structured links',cat='Ideas',rotation=False,importSourceId='structured',instructions=[{'type':'step','name':'Sauce component','text':HTML.split('<p>')[2].split('</p>')[0]}],ingredients=[]),dict(id=10,name='Empty HTML anchor',cat='Ideas',rotation=False,instructions='<p><a href="https://recipes.test/empty"></a></p>'+HTML,ingredients=[]),dict(id=9,name='Reference link',cat='Ideas',rotation=False,instructions='Use [the sauce][sauce].\n[sauce]: '+SAUCE,ingredients=[]),dict(id=7,name='Manual recipe',cat='Ideas',rotation=False,url='https://recipes.test/manual',instructions=DIRTY,ingredients=[])])
HOOK="""window.cleanupTest={link:(text)=>{const d=document.createElement('div');appendInstructionLinks(d,text,'https://recipes.test/main');return {html:d.innerHTML,text:d.textContent}},state:()=>({meals,sessions:cookingSessions,scales:occurrenceScales,prefs:recipeViewPrefs}),cleanup:cleanupRecipeInstructions,complete:completeRecipeFields,parse:importedInstructionBlocks,items:recipeImportItems,csv:recipeImportCsv,trello:recipeImportTrelloBoard,extract:extractCompleteRecipe,import:items=>showRecipeImportSelection(recipeImportItems(items),'fixture.json'),open:(id=1,day='Tuesday')=>{window.history.replaceState({},'');const m=meals.find(m=>m.id===id);openRecipeViewer(m,day?cookingContext('original',day,m.cat,m):null,true)},seed:()=>{for(const [id,days] of [[1,['Tuesday','Friday']],[3,['Monday']]]){const m=meals.find(m=>m.id===id),tokens=cookingItemTokens(m),steps=tokens.steps.filter(s=>s.token);for(const day of days){const c=cookingContext('original',day,m.cat,m);cookingSession(c,true);const session=cookingSession(c);session.steps=steps.slice(0,2).map(s=>s.token);session.ingredientOverrides={[tokens.ingredients[0].token]:true};session.autoIngredients=[];materializeIngredientChoices(session);const key=cookingOccurrenceKey(c);occurrenceScales.occurrences[key]={context:c,multiplier:day==='Tuesday'?2:1}}m.ingredientStepLinks=[{step:steps[0].token,ingredients:[tokens.ingredients[0].token]}]}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales);persist()},tokens:id=>cookingItemTokens(meals.find(m=>m.id===id)),raw:key=>localStorage.getItem(key),fail:()=>{const previous=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.endsWith('mealRotationDataV1')){window.failedWrites=(window.failedWrites||0)+1;throw Error('Quota')};return previous.call(this,k,v)}},edit:id=>openEditor(id)};"""

def run(browser,filename,width):
    ctx=browser.new_context(viewport={'width':width,'height':851 if width<600 else 900},is_mobile=width<600,has_touch=width<600)
    page=ctx.new_page();page.set_default_timeout(8000);errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    source=(ROOT/filename).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+HOOK+'})();').replace('function validateBackupCore(d){','window.cleanupBackup={capture:captureBackupStorage,validate:validateBackupStorage,restore:restoreBackupStorage};function validateBackupCore(d){')
    prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
    seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Main','Side','Other','Ideas'],active='Main',meals=BASE)),prefix+'mealRotationWeekdayCategoriesV1':json.dumps({'Tuesday':['Main'],'Friday':['Main'],'Monday':['Other']}),prefix+'mealRotationRecipeViewPrefsV1':json.dumps(dict(mode='split',ratio=.4,syncIngredients=False,autoCompleteIngredients=False,keepScreenAwake=False))}
    page.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1";}window.primaryWrites=0;const originalSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(k.endsWith("mealRotationDataV1"))primaryWrites++;return originalSet.call(this,k,v)};')
    page.route('http://meal.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=source) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''))
    fetched=[]
    def fetch(route):fetched.append(route.request.url);route.fulfill(status=200,content_type='text/html',body='<h1>Linked component recipe</h1>')
    ctx.route('https://**/*',fetch)
    page.goto('http://meal.test/'+filename)
    def state():return page.evaluate('cleanupTest.state()')
    def meal(i):return next(m for m in state()['meals'] if m['id']==i)
    def ev(name,value):return page.evaluate('(a)=>cleanupTest[a[0]](a[1])',[name,value])
    def op(i=1,day='Tuesday'):page.evaluate('(a)=>cleanupTest.open(...a)',[i,day])
    def close():page.get_by_role('button',name='Close recipe',exact=True).click();page.wait_for_selector('#recipeViewer',state='detached')
    def control(n):
        el=page.locator('.recipe-viewer-steps .cooking-item').nth(n)
        return el.locator('.recipe-step-toggle') if el.locator('.recipe-step-toggle').count() else el
    # Clean imports and unfamiliar directions remain unchanged; related links are not authorization.
    details=ev('complete',{'name':'Clean','recipeInstructions':CLEAN,'url':'https://original.test/clean','notes':'Unchanged note.'})
    assert details['instructions']==CLEAN and not details.get('instructionCleanupBackupV1'),details
    uncertain='Dwell under the cloche.\nCreate a smooth paste.\n## Related Recipes\n[Relevant dressing](https://recipes.test/dressing)\n## See also\nUse ⅓ cup to lacquer the surface.'
    cleaned=ev('cleanup',uncertain);assert not cleaned['removed'];assert 'https://recipes.test/dressing' in str(cleaned['instructions'])
    dirty=ev('complete',{'name':'Dirty','recipeInstructions':DIRTY,'recipeIngredient':['2 onions'],'url':'https://original.test/dirty','notes':'Keep notes.'})
    text='\n'.join(b['text'] for b in dirty['instructions'])
    for good in ['180°C / 350°F','10 minutes','Dwell under the cloche',SAUCE,'Linked recipes','https://recipes.test/spices']:assert good in text,good
    for bad in ['Create an account','Log in','Chocolate cake','More cookies','google-analytics','images.test','2026-','Advertisement']:assert bad not in text,bad
    for unknown in ['![Fold the dough as shown](https://images.test/fold.jpg)','[![Sauce picture](https://images.test/sauce.jpg)](https://recipes.test/sauce)','![Fold the dough][fold]\n[fold]: https://images.test/fold.jpg']:
        result=ev('cleanup',unknown);assert not result['removed'] and unknown.splitlines()[0] in str(result['instructions'])
    assert not ev('cleanup','[Sponsored](https://doubleclick.net/track?id=1)')['instructions']
    assert dirty['instructionCleanupBackupV1']['instructionsBeforeCleanup']==DIRTY
    assert dirty['originalRecipeUrl']=='https://original.test/dirty' and dirty['notes']=='Keep notes.'
    assert ev('cleanup',dirty['instructions'])['instructions']==dirty['instructions']
    html=ev('complete',{'name':'HTML','recipeInstructions':HTML,'url':'https://recipes.test/legacy'});assert SAUCE in str(html['instructions']),html
    preserved=ev('cleanup','<nav>Home | Recipes</nav><form>Whisk for 10 minutes.</form><footer>Rest for 5 minutes.</footer>')
    assert 'Whisk for 10 minutes.' in str(preserved['instructions']) and 'Rest for 5 minutes.' in str(preserved['instructions'])
    # Shared extraction covers structured website/RecipeSage/reader responses, CSV and Trello.
    structured={'@type':'Recipe','name':'Dirty','recipeInstructions':DIRTY,'recipeIngredient':['2 onions'],'url':'https://original.test/dirty'}
    for raw in [json.dumps(structured),'<script type="application/ld+json">'+json.dumps(structured)+'</script>',json.dumps({'contents':json.dumps(structured)})]:
        result=ev('extract',raw);assert result['instructions']==dirty['instructions']
    buff=io.StringIO();writer=csv.writer(buff);writer.writerow(['name','instructions']);writer.writerow(['CSV',DIRTY]);items=ev('csv',buff.getvalue());assert ev('complete',items[0])['instructions']==dirty['instructions']
    items=ev('trello',{'lists':[{'id':'L','name':'Ideas'}],'cards':[{'id':'T','idList':'L','name':'Trello','desc':'## Instructions\n'+DIRTY}]});assert 'Chocolate cake' not in str(ev('complete',items[0])['instructions'])
    # Existing imported recipe: one atomic write includes a recovery copy; saved cooking data is untouched.
    page.evaluate('cleanupTest.seed()');before=state();old=meal(1);page.evaluate('primaryWrites=0');op()
    assert page.evaluate('primaryWrites')==1
    after=meal(1);assert after['instructionCleanupBackupV1']['instructionsBeforeCleanup']==DIRTY
    for key in ['ingredients','notes','linkedMealIds','url','originalRecipeUrl','storedImportedSource','ingredientStepLinks']:assert after[key]==old[key],key
    assert state()['sessions']==before['sessions'] and state()['scales']==before['scales']
    assert not page.locator('#recipeImportReview').count();assert not page.get_by_role('alertdialog').count()
    page.get_by_role('button',name='Recipe settings',exact=True).click()
    assert not page.locator('#recipeViewerSettings').get_by_role('button',name='Review instruction cleanup / related recipes',exact=True).count()
    assert page.locator('#recipeViewerSettings').get_by_label('Keep Screen Awake',exact=True).count()==1
    box=page.locator('#recipeViewerSettings').bounding_box();assert box['x']>=0 and box['x']+box['width']<=width+1
    if filename=='index.html' and width==320:page.screenshot(path='/workspace/issue4-mobile-settings.png')
    page.get_by_role('button',name='Close settings',exact=True).click()
    # The legitimate sauce link opens safely and never completes the step or creates a linked meal.
    link=page.locator('.recipe-instruction-link').filter(has_text='green sauce');assert link.get_attribute('href')==SAUCE
    assert not page.locator('button a').count() and link.get_attribute('rel')=='noopener noreferrer'
    unchanged=state()['sessions']
    with ctx.expect_page() as popup:link.click()
    popup.value.wait_for_url(SAUCE);assert popup.value.url==SAUCE;popup.value.close()
    assert state()['sessions']==unchanged and meal(1)['linkedMealIds']==[2]
    assert page.get_by_role('link',name='View Original Recipe',exact=True).get_attribute('href')==old['originalRecipeUrl']
    # Native completion, keyboard completion, and long-press link editing still work on linked steps.
    control(1).click();assert control(1).get_attribute('aria-pressed')=='false'
    control(1).focus();control(1).press('Space');assert control(1).get_attribute('aria-pressed')=='true'
    saved=state()['sessions'];control(1).scroll_into_view_if_needed();box=control(1).bounding_box();page.mouse.move(box['x']+3,box['y']+3);page.mouse.down();page.wait_for_timeout(650);page.mouse.up()
    assert page.locator('.recipe-link-edit-bar').is_visible();page.get_by_role('button',name='Cancel ingredient links',exact=True).click();assert state()['sessions']==saved
    # Opening/closing repeatedly or reloading does not rewrite already processed recipes.
    close();page.evaluate('primaryWrites=0');op();close();op();assert page.evaluate('primaryWrites')==0
    close();page.reload();page.evaluate('primaryWrites=0');op();assert page.evaluate('primaryWrites')==0;close()
    # Clean recipes receive neither markers nor cleanup writes. Ambiguous token changes are skipped.
    clean_before=meal(4);page.evaluate('primaryWrites=0');op(4,None);assert meal(4)==clean_before and page.evaluate('primaryWrites')==0;close()
    ambiguous=meal(5);page.evaluate('primaryWrites=0');op(5,None);assert meal(5)==ambiguous and page.evaluate('primaryWrites')==0;close()
    # Legacy HTML links remain clickable, with original cooking tokens/progress preserved after cleanup and edit.
    previous=state()['sessions'];old_html=meal(3);op(3,'Monday');assert meal(3)['instructionCleanupBackupV1']['instructionsBeforeCleanup']==HTML
    assert state()['sessions']==previous and meal(3)['ingredientStepLinks']==old_html['ingredientStepLinks'];assert page.locator('.recipe-instruction-link').get_attribute('href')==SAUCE
    page.get_by_role('button',name='Edit Recipe',exact=True).click();field=page.locator('#recipeInstructions');assert '<a href=' in field.input_value() and SAUCE.replace('&','&amp;') in field.input_value()
    field.fill(field.input_value()+'\nNew step remains incomplete.');page.locator('#save').click();assert state()['sessions']==previous
    assert control(3).get_attribute('aria-pressed')=='false';assert page.locator('.recipe-instruction-link').get_attribute('href')==SAUCE;close()
    op(8,None);assert page.locator('.recipe-instruction-link').get_attribute('href')==SAUCE;close()
    op(10,None);assert 'Mix onions for 10 minutes.' in control(0).inner_text();assert page.locator('.recipe-instruction-link').get_attribute('href')==SAUCE;close()
    op(9,None);assert page.locator('.recipe-instruction-link').filter(has_text='the sauce').get_attribute('href')==SAUCE;close()
    # A normal explicit file import cleans automatically and shows no cleanup/related-selection flow.
    ev('import',[dict(structured,identifier='new-import',linkedRecipes=[{'name':'Suggestion','url':'https://recipes.test/suggestion'}])]);page.get_by_role('button',name='Import recipes',exact=True).click()
    assert not page.get_by_role('button',name='Review related recipes',exact=True).count()
    page.get_by_role('button',name='OK',exact=True).click();new=[m for m in state()['meals'] if m['name']=='Dirty'];assert len(new)==1 and not new[0]['rotation'] and not new[0].get('linkedMealIds')
    assert new[0]['instructions']==dirty['instructions'];assert not any(m['name']=='Suggestion' for m in state()['meals']);assert meal(1)['linkedMealIds']==[2]
    assert fetched==[SAUCE.split('#')[0]],fetched
    # V2 backups retain the recovery copy and restore through the existing storage validators.
    backup=page.evaluate('cleanupBackup.capture()');page.evaluate('(b)=>cleanupBackup.validate(b)',backup)
    raw=json.loads(backup['mealRotationDataV1']);assert next(m for m in raw['meals'] if m['id']==1)['instructionCleanupBackupV1']['instructionsBeforeCleanup']==DIRTY
    page.evaluate('(key)=>localStorage.setItem(key,JSON.stringify({version:1,occurrences:{}}))',prefix+'mealRotationCookingSessionsV1');page.evaluate('(b)=>cleanupBackup.restore(b)',backup)
    assert page.evaluate('cleanupBackup.capture()')==backup
    if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")') is None
    # No cleanup for recipes of unknown provenance, and failed backup writes never change a recipe.
    manual=meal(7);page.evaluate('primaryWrites=0');op(7,None);assert meal(7)==manual and page.evaluate('primaryWrites')==0;close()
    failure=meal(6);page.evaluate('cleanupTest.fail()');op(6,None);assert meal(6)==failure
    assert not page.get_by_role('alertdialog').count() and not page.locator('#recipeImportReview').count()
    close();op(6,None);assert meal(6)==failure and page.evaluate('failedWrites')==1
    # Unsafe link schemes stay inert; no nested links/buttons or script execution.
    unsafe=ev('link','[unsafe](javascript:window.hacked=1)')
    assert '<a' not in unsafe['html'] and 'unsafe' in unsafe['text'];assert page.evaluate('typeof window.hacked')=='undefined'
    assert not errors,errors
    print(f'PASS {filename} {width}px: conservative imports/formats, recoverable/idempotent existing cleanup, clickable safe links, no unsolicited links/UI, editor/progress/scaling/associations, backup restore, mobile settings; no JS errors',flush=True)
    ctx.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            for width in [320,360,1280]:run(browser,filename,width)
        browser.close()
