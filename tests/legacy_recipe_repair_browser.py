"""Explicit legacy RecipeSage repair, synthetic storage only; regular/test app parity."""
import copy,json,tempfile
from playwright.sync_api import sync_playwright
import instruction_repair_browser as base
RICE='Garlic Jasmine Rice with Cauliflower'
CLUTTER=['1. Create an account or login to save this recipe to your collection.','2. [Register/Login to Save](https://recipesage.com/#/register)','3. _Created 5/5/2026, 11:05 PM','4. Last edited 7/22/2026, 11:42 PM_']
COOK=[{'type':'section','text':'Pork'},{'type':'step','text':'Fry 500 g pork at 180°C for 15 minutes.'},{'type':'step','text':'Serve with [rice](https://recipes.test/rice_with_cauliflower?amount=2&unit=cup#finish).'}]
def fixture(i,**kw):
    return base.meal(i,'legacy-'+str(i),name='Thai Garlic Pork '+str(i),instructions=copy.deepcopy(COOK)+[{'type':'section','text':RICE}]+CLUTTER,**kw)
def run(browser,filename,width):
    library=[fixture(60,linkedMealIds=[50],rotation=True),base.meal(50,'rice',name=RICE,cat='Sides',instructions='Boil rice.',linkedMealIds=[])]
    # Same-looking component headings with real directions, a URL, or no saved relation stay.
    library += [fixture(61,linkedMealIds=[50]),fixture(62,linkedMealIds=[50]),fixture(63,linkedMealIds=[])]
    library[2]['instructions'].append({'type':'step','text':'Boil 2 cups rice for 12 minutes.'})
    library[3]['instructions'][3]['text']='['+RICE+'](https://recipes.test/rice)'
    # Removing metadata embedded in one cooking block would change its token: skip.
    library += [fixture(64,linkedMealIds=[50])];library[-1]['instructions']=[{'type':'step','text':'Bake at 200°C for 20 minutes.\n'+CLUTTER[0]}]
    # Exact string/CRLF representation retained (individual array entries).
    library += [fixture(65,linkedMealIds=[50])];library[-1]['instructions']=['## Pork\r\n','Fry 500 g pork at 180°C for 15 minutes.\r\n','## '+RICE+'\r\n']+[x+'\r\n' for x in CLUTTER]
    # Meaningful captions/recipe links, mixed prompts and manual recipes retained.
    library += [fixture(66,linkedMealIds=[50])];library[-1]['instructions']=COOK+['Create an account or login to save this recipe to your collection. Then bake for 10 minutes.','[Register/Login to Save](https://recipes.test/component)','Created 5/5/2026 sauce starter: ferment for 2 days.']
    library += [fixture(67,linkedMealIds=[50])];library[-1].update(importSourceId='',recipeSageId='',url='https://manual.test/recipe')
    library += [fixture(68,linkedMealIds=[50]),fixture(69,linkedMealIds=[50],rotation=True,cat='Dinner')]
    # Metadata-only recipe can be restored from a confidently matched export.
    library += [fixture(70,linkedMealIds=[50])];library[-1]['instructions']=CLUTTER[:]
    # Unrecognized structured fields are preserved rather than flattened.
    library += [fixture(71,linkedMealIds=[50])];library[-1]['instructions']=[{'type':'step','text':'Created 5/5/2026','custom':'keep'},'Login to save this recipe.']
    library += [fixture(72,linkedMealIds=[50])];library[-1]['instructions']=COOK+['<p><a href="https://recipesage.com/#/login">Register/Login to Save</a></p>','Last edited: 2026-07-22T23:42:00Z']
    # Plain string suffix, exact screenshot without Markdown links.
    library += [fixture(73,linkedMealIds=[50])];library[-1]['instructions']='## Pork\r\nFry 500 g pork at 180°C for 15 minutes.\r\n\r\n## '+RICE+'\r\n'+'\r\n'.join(CLUTTER).replace('[Register/Login to Save](https://recipesage.com/#/register)','Register/Login to Save')
    library += [fixture(74,linkedMealIds=[50])];library[-1]['instructions']='\n'.join(CLUTTER)
    key='mealRotationDataV1'
    ctx,page,errors,prefix=base.setup(browser,filename,width,library=library,seed_progress=False,weekdays={'Tuesday':['Fish','Dinner'],'Friday':['Fish']})
    # Access internal helpers through the already-injected plan; token formulas are stable JSON.
    step=lambda section,text:json.dumps(['step',section,text],ensure_ascii=False,separators=(',',':'))+'#0'
    ing=json.dumps(['ingredient','','2 fish fillets'],separators=(',',':'))+'#0'
    page.evaluate('''([token,ing,bad])=>{const s=repairTest.state();s.sessions.occurrences={};s.scales.occurrences={};for(const id of [60,68,69]){const m=s.meals.find(m=>m.id===id);m.ingredientStepLinks=[{step:id===68?bad:token,ingredients:[ing]}]};for(const day of ['Tuesday','Friday']){const context={planId:'original',day,cat:'Fish',mealId:'60',parentId:''};s.sessions.occurrences[JSON.stringify(['original',day,'60',''])]={id:day,context,ingredients:day==='Tuesday'?[ing]:[],steps:day==='Tuesday'?[token]:[],autoIngredients:day==='Tuesday'?[ing]:[],ingredientOverrides:{}};s.scales.occurrences[JSON.stringify(['original',day,'60',''])]={context,multiplier:day==='Tuesday'?2:0.5}}s.sessions.occurrences[JSON.stringify(['original','Tuesday','69',''])]={id:'blocked',context:{planId:'original',day:'Tuesday',cat:'Dinner',mealId:'69',parentId:''},ingredients:[],steps:[bad]};repairTest.saveProgress();repairTest.saveScales();repairTest.persist()}''',[step('Pork','Fry 500 g pork at 180°C for 15 minutes.'),ing,step(RICE,CLUTTER[0][3:])])
    baseline=copy.deepcopy(page.evaluate('repairTest.state()'));saved=page.evaluate('repairTest.storage()')
    plan=page.evaluate('repairTest.plan([])');rows={r['id']:r for r in plan}
    assert rows[60]['ready'] and rows[60]['instructions']==COOK,rows[60]
    for i in [64,66,67,68,69]:assert not rows[i]['ready'],(i,rows[i])
    assert rows[61]['instructions'][3]['text']==RICE
    assert rows[62]['instructions'][3]['text'].startswith('[')
    assert rows[63]['instructions'][3]['text']==RICE
    assert rows[65]['instructions']==next(m for m in library if m['id']==65)['instructions'][:2]
    assert rows[73]['instructions']=='## Pork\r\nFry 500 g pork at 180°C for 15 minutes.\r\n\r\n',rows[73]
    assert rows[71]['instructions']==[{'type':'step','text':'Created 5/5/2026','custom':'keep'}]
    assert rows[72]['instructions']==COOK
    assert rows[74]['ready'] and rows[74]['instructions']==''
    # Open/preview/cancel cannot modify storage, including completed occurrences.
    page.evaluate('repairTest.open()');page.get_by_role('button',name='Preview saved instruction cleanup',exact=True).click()
    dialog=page.locator('#recipeInstructionRepair');assert 'saved lines to clean' in dialog.inner_text()
    row=dialog.locator('details').filter(has_text='(ID 60, Fish)');row.locator('summary').click()
    assert all(x in row.inner_text() for x in ['Current saved instructions','Proposed instructions','180°C','15 minutes','Recognized saved lines to remove','stray linked heading'])
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    if filename=='index.html' and width==360:page.screenshot(path='/tmp/legacy-repair-preview-360.png')
    assert page.evaluate('repairTest.storage()')==saved
    page.get_by_role('button',name='Cancel',exact=True).click();assert page.evaluate('repairTest.storage()')==saved
    # Deselect all then include only the screenshot fixture and raw CRLF variants.
    page.evaluate('repairTest.open()');page.get_by_role('button',name='Preview saved instruction cleanup',exact=True).click()
    for details in dialog.locator('details').all():details.evaluate('(e)=>e.open=true')
    for check in dialog.get_by_role('checkbox').all():check.uncheck()
    for i in [60,65,73,74]:dialog.get_by_role('checkbox',name=f'Apply repair to Thai Garlic Pork {i} (ID {i})',exact=True).check()
    with tempfile.TemporaryDirectory() as tmp:
        backup=base.verified_backup(page,tmp);assert backup['storage']==saved
        page.evaluate('repairTest.fail()');page.get_by_role('button',name='Apply instruction repair',exact=True).click()
        assert 'could not be saved' in dialog.inner_text() and page.evaluate('repairTest.storage()')==saved
        page.evaluate('repairRestoreWrite()');base.verified_backup(page,tmp)
        page.get_by_role('button',name='Apply instruction repair',exact=True).click()
        assert 'cleaned 4 recipes (19 saved lines)' in dialog.inner_text(),dialog.inner_text()[-600:]
        after=page.evaluate('repairTest.state()');storage=page.evaluate('repairTest.storage()')
        for before,m in zip(baseline['meals'],after['meals']):
            expected=copy.deepcopy(before)
            if m['id'] in [60,65,73,74]:expected['instructions']=rows[m['id']]['instructions']
            assert m==expected,(m['id'],m,expected)
        for field in baseline:
            if field!='meals':assert after[field]==baseline[field],field
        assert {k:v for k,v in storage.items() if k!=key}=={k:v for k,v in saved.items() if k!=key}
        page.get_by_role('button',name='Close',exact=True).click()
        # Reopening retains independent progress and the same associations without reconciliation.
        repeat={r['id']:r for r in page.evaluate('repairTest.plan([])')}
        assert not any(repeat[i]['ready'] for i in [60,65,73,74])
        page.evaluate('repairTest.persist()');page.reload()
        assert page.evaluate('repairTest.storage()')==storage,page.evaluate('repairTest.schedule()')
        assert page.evaluate('repairTest.state().sessions')==baseline['sessions']
        assert page.evaluate('repairTest.state().scales')==baseline['scales']
        # Combined source repair: metadata-only becomes real instructions, uncertain missing untouched.
        page.evaluate('repairTest.open()');src=base.source('legacy-70',name='Thai Garlic Pork 70')
        base.upload(page,'Choose RecipeSage file',[src])
        details=dialog.locator('details').filter(has_text='(ID 70, Fish)');details.locator('summary').click()
        assert 'Restore missing instructions and remove' in details.inner_text()
        for d in dialog.locator('details').all():d.evaluate('(e)=>e.open=true')
        for c in dialog.get_by_role('checkbox').all():c.uncheck()
        dialog.get_by_role('checkbox',name='Apply repair to Thai Garlic Pork 70 (ID 70)',exact=True).check()
        base.verified_backup(page,tmp);page.get_by_role('button',name='Apply instruction repair',exact=True).click()
        result=page.evaluate('repairTest.state()');assert len(result['meals'])==len(library)
        updated=next(m for m in result['meals'] if m['id']==70);assert '200°C' in json.dumps(updated['instructions'],ensure_ascii=False)
        assert {k:v for k,v in updated.items() if k!='instructions'}=={k:v for k,v in next(m for m in baseline['meals'] if m['id']==70).items() if k!='instructions'}
        page.evaluate('(b)=>repairTest.restore(b)',backup)
        assert page.evaluate('repairTest.storage()')==saved
    if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING APP SENTINEL'
    assert not errors,errors
    ctx.close();print('PASS',filename,width,'legacy screenshot, conservative removals, retained uncertain content, associations/progress guards, CRLF/raw structure, selection/cancel, quota safety, complete backup/restore, combined missing repair, idempotence, storage isolation')
if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            for width in [320,360]:run(browser,filename,width)
        browser.close()
