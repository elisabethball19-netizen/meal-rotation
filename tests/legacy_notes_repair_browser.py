"""Legacy viewer clutter lives in notes too. Only synthetic fixtures are committed."""
import copy,json,tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
import instruction_repair_browser as base
TIP='Add 1 tsp sesame oil just before serving.'
FOOTER='Create an account or login to save this recipe to your collection.\n\n Register/Login to Save \n\n_Created 1/2/2025, 3:04 PM  \n Last edited 1/3/2025, 4:05 PM_'
LOGO='![Image 1](https://recipesage.com/app/assets/imgs/logo_green_padded.png)'
NOTES=TIP+'\n\n  \n\nLinked Recipes\n\n'+LOGO+'\n## Thai garlic pork\n\n  \n\n  \n\n'+FOOTER
STEPS=[{'type':'step','text':'Cook rice in broth for 15 minutes.'},{'type':'step','text':'Stir in the green onions and cilantro.'}]
base.HOOK+='''window.notesTest={plan:()=>recipeRepairPlan([],meals).rows.map(r=>({id:r.meal.id,ready:r.instructions!==null||r.notes!==null,instructions:r.instructions,notes:r.notes,reason:r.reason,uncertain:r.uncertain})),notes:(m,lib)=>recipeRepairLegacyNotes(m,lib),import:r=>completeRecipeFields(recipeImportItems([r])[0]),show:(id,day='Tuesday')=>{const m=meals.find(m=>m.id===id);openRecipeViewer(m,id===1?cookingContext('original',day,m.cat,m):null)},close:()=>closeRecipeViewer(),edit:id=>openEditor(id),tokens:id=>cookingItemTokens(meals.find(m=>m.id===id)),matches:id=>[...recipeIngredientMatches(meals.find(m=>m.id===id))],seed:()=>{const m=meals.find(m=>m.id===1),items=cookingItemTokens(m),step=items.steps.find(s=>s.token).token,ing=items.ingredients[0].token;m.ingredientStepLinks=[{step,ingredients:[ing]}];persist();const c=cookingContext('original','Tuesday',m.cat,m);cookingSession(c).steps=[step];writeCookingSessions(cookingSessions);const bad=meals.find(m=>m.id===71),b=cookingItemTokens(bad);bad.ingredientStepLinks=[{step:b.steps[0].token,ingredients:[b.ingredients[0].token]}];const imageMeal=meals.find(m=>m.id===75),im=cookingItemTokens(imageMeal);imageMeal.ingredientStepLinks=[{step:im.steps.find(s=>s.text.startsWith('![Image')).token,ingredients:[im.ingredients[0].token]}];persist()}};'''
def imported(i,notes,**extra):
    return base.meal(i,base.SAGE,name='Notes fixture '+str(i),instructions=copy.deepcopy(STEPS),notes=notes,**extra)
def run(browser,filename,width):
    library=[imported(1,NOTES,rotation=True,name_override='unused'),base.meal(3,base.SAGE2,instructions='My edited step. Keep overnight.'),base.meal(50,'side',cat='Sides',name='Side',instructions='Boil the side.',linkedMealIds=[]),base.meal(51,'pork',cat='Sides',name='Thai garlic pork',instructions='Fry pork.',linkedMealIds=[])]
    library[0]['name']='Garlic Jasmine Rice with Cauliflower';library[0].pop('name_override');library[0]['ingredients']=['1½ cups jasmine rice','1 tsp sesame oil']
    library += [imported(60,NOTES,importSourceId='',recipeSageId='',url='https://manual.test/recipe'),imported(61,'Linked Recipes\n[Side](https://recipes.test/side)\n![My icing diagram](https://images.test/diagram.png)'),imported(62,'Linked Recipes\n'+LOGO+'\n## Thai garlic pork\nServe with [Side](https://recipes.test/side).\nKeep chilled at 4°C.\n'+FOOTER),imported(63,NOTES,linkedMealIds=[51]),imported(64,'Created 1/2/2025, 3:04 PM\nLast edited 1/3/2025, 4:05 PM'),imported(65,'Linked Recipes\n![My saved layout](https://recipesage.com/app/assets/imgs/logo_green_padded.png)\n## Thai garlic pork\n'+FOOTER),imported(66,'Linked Recipes\n'+LOGO+'\nCreated with love on Grandma’s birthday.\nCreate an account or login to save this recipe to your collection.'),imported(67,TIP+'\n'+LOGO+'\n'+FOOTER),imported(68,NOTES,recipeSageId='',url='https://manual.test/recipe'),imported(70,'<div>Linked Recipes</div><p>'+LOGO+'</p><p>'+FOOTER.replace('\n','<br>')+'</p>'),imported(71,NOTES),imported(72,TIP+'\n![Image 1]\n'+FOOTER),imported(73,NOTES.replace('\n','\r\n'))]
    library[-3]['instructions']=[{'type':'step','text':'Create an account or login to save this recipe to your collection.'},{'type':'step','text':'Created 1/2/2025, 3:04 PM'}]
    for i in [74,75]:
        m=imported(i,TIP);m['instructions']=copy.deepcopy(STEPS)+[{'type':'step','text':line} for line in ('Linked Recipes\n'+LOGO+'\n## Thai garlic pork\n'+FOOTER).split('\n') if line.strip()];library.append(m)
    ctx,page,errors,prefix=base.setup(browser,filename,width,library=library)
    page.evaluate('notesTest.seed()')
    state=lambda:page.evaluate('repairTest.state()');storage=lambda:page.evaluate('repairTest.storage()')
    baseline=copy.deepcopy(state());saved=storage()
    # Reproduce the reported legacy viewer/editor mismatch before any cleanup.
    page.evaluate('notesTest.show(1)');notes=page.locator('.recipe-viewer-notes');assert all(t in notes.inner_text() for t in ['Linked Recipes','![Image 1]','Create an account','Last edited',TIP])
    page.evaluate('notesTest.close()');page.evaluate('notesTest.edit(1)')
    assert 'Linked Recipes' not in page.locator('#recipeInstructions').input_value()
    assert NOTES==page.locator('#recipeNotes').input_value()
    assert page.locator('#recipeNotesPanel').is_hidden()
    page.get_by_role('button',name='Cancel',exact=True).click()
    # Fresh import is clean, unlike the already-persisted legacy record.
    current=page.evaluate('(r)=>notesTest.import(r)',base.source(base.SAGE,name='Garlic Jasmine Rice with Cauliflower',instructions=STEPS)|{'notes':TIP})
    assert current['notes']==TIP and 'Linked Recipes' not in json.dumps(current)
    # Baseline after ordinary viewer/editor actions; the repair must not change it on preview.
    baseline=copy.deepcopy(state());saved=storage();tokens=page.evaluate('notesTest.tokens(1)');matches=page.evaluate('notesTest.matches(1)')
    plan={r['id']:r for r in page.evaluate('notesTest.plan()')}
    assert plan[1]['instructions'] is None and plan[1]['notes'].strip()==TIP
    for i in [60,61,64,66,68,70,75]:assert not plan[i]['ready'],(i,plan[i])
    for i in [62,63,65]:assert plan[i]['ready'] and plan[i]['uncertain']
    assert 'https://recipes.test/side' in plan[62]['notes'] and '4°C' in plan[62]['notes']
    assert 'Linked Recipes' in plan[63]['notes'] and 'Thai garlic pork' in plan[63]['notes']
    assert '![My saved layout]' in plan[65]['notes']
    assert plan[67]['notes'].strip()==TIP and plan[72]['notes'].strip()==TIP
    assert '\r\n' in plan[73]['notes'] and plan[73]['notes'].strip()==TIP
    assert plan[71]['ready'] and plan[71]['instructions'] is None and plan[71]['notes'].strip()==TIP
    assert plan[74]['instructions']==STEPS and plan[74]['notes'] is None
    opaque=page.evaluate('([m,lib])=>notesTest.notes(m,lib)',[imported(99,{'text':'keep'}),library]);assert opaque['notes'] is None and opaque['uncertain']
    # Preview and Cancel make no writes. Every changed field is explicitly identified.
    page.evaluate('repairTest.open()');page.get_by_role('button',name='Preview saved recipe cleanup',exact=True).click();dialog=page.locator('#recipeInstructionRepair')
    detail=dialog.locator('details').filter(has_text='(ID 1, Fish)');detail.locator('summary').click()
    assert 'Current saved notes' in detail.inner_text() and 'Proposed notes' in detail.inner_text() and TIP in detail.inner_text()
    assert 'Current saved instructions' not in detail.inner_text()
    assert not page.get_by_role('button',name='Apply selected repairs',exact=True).is_enabled()
    assert storage()==saved and state()==baseline
    page.get_by_role('button',name='Cancel',exact=True).click();assert storage()==saved
    page.evaluate('repairTest.open()');page.get_by_role('button',name='Preview saved recipe cleanup',exact=True).click()
    with tempfile.TemporaryDirectory() as tmp:
        backup=base.verified_backup(page,tmp);assert backup['storage']==saved
        # Read-back must preserve both the exact original contaminated notes and complete storage.
        assert next(m for m in backup['meals'] if m['id']==1)['notes']==NOTES
        # Quota failure has no partial instruction/notes/progress changes.
        page.evaluate('repairTest.fail()');page.get_by_role('button',name='Apply selected repairs',exact=True).click()
        assert 'could not be saved' in dialog.inner_text() and storage()==saved and state()==baseline
        page.evaluate('repairRestoreWrite()');base.verified_backup(page,tmp)
        page.get_by_role('button',name='Apply selected repairs',exact=True).click();after=state();after_storage=storage()
        for before,meal in zip(baseline['meals'],after['meals']):
            expected=copy.deepcopy(before)
            if plan[meal['id']]['notes'] is not None:expected['notes']=plan[meal['id']]['notes']
            if plan[meal['id']]['instructions'] is not None:expected['instructions']=plan[meal['id']]['instructions']
            assert meal==expected,meal['id']
        for k in baseline:
            if k!='meals':assert baseline[k]==after[k],k
        assert {k:v for k,v in saved.items() if k!='mealRotationDataV1'}=={k:v for k,v in after_storage.items() if k!='mealRotationDataV1'}
        assert page.evaluate('notesTest.tokens(1)')==tokens and page.evaluate('notesTest.matches(1)')==matches
        page.get_by_role('button',name='Close',exact=True).click()
        assert not any(r['ready'] for r in page.evaluate('notesTest.plan()'))
        page.evaluate('notesTest.show(1)');assert page.locator('.recipe-viewer-notes').inner_text()==TIP
        assert '3 cups jasmine rice' in page.locator('.recipe-viewer-ingredients').inner_text()
        assert 'Side' in page.locator('#recipeViewer').inner_text()
        assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
        if filename=='meal-rotation-test.html' and width==360:page.screenshot(path='/tmp/legacy-notes-repaired-360.png')
        page.set_viewport_size({'width':780,'height':width});page.wait_for_timeout(120);assert page.locator('.recipe-viewer-notes').inner_text()==TIP
        page.set_viewport_size({'width':width,'height':851});page.wait_for_timeout(120)
        page.evaluate('notesTest.close()');before_reload=storage();page.reload();assert storage()==before_reload
        assert page.evaluate('notesTest.tokens(1)')==tokens and page.evaluate('notesTest.matches(1)')==matches
        assert state()['sessions']==after['sessions'] and state()['scales']==after['scales']
        # Full pre-repair backup restores exact original notes and all stored data.
        page.evaluate('(b)=>repairTest.restore(b)',backup);assert storage()==saved
    if prefix:assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING APP SENTINEL'
    assert not errors,errors;ctx.close()
    print('PASS',filename,width,'legacy notes viewer/editor reproduction, clean-import comparison, conservative headings/images/URLs/user notes, backup readback/cancel/quota/restore, notes-only atomic writes, progress/links/scaling/groceries, idempotence/reload, portrait/landscape, test isolation; no JS errors',flush=True)
if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            for width in [320,360]:run(browser,filename,width)
        browser.close()
