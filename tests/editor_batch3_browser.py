"""Session-only sections, inline linking and existing automatic/manual step associations."""
from playwright.sync_api import sync_playwright
import remaining_meal_features_browser as base
f=base.f
f.EXTRA+='''window.batch3={
 seed:()=>{remainingTest.seed();const m=meals.find(m=>m.id===537);m.ingredients=['1 cup rice','2 onions','1 tsp salt'];m.instructions='Cook rice.\\nChop onions.';m.notes='Keep notes';m.serveWith=['Rice'];m.linkedMealIds=[25];m.makeAheadTasks=[{id:'a',description:'Thaw',daysBefore:2},{id:'b',description:'Marinate',daysBefore:0,hoursBefore:3}];localStorage.setItem(RECIPE_EDITOR_SECTIONS_KEY,JSON.stringify({ingredients:true,instructions:true,sections:{serve:true,linked:true,recipe:true,notes:true},subsections:{adjusting:true,ahead:true,notes:true}}));localStorage.setItem('mealRotationLinkedSearchAnyOrderV1','false');persist()},
 viewer:()=>{recipeViewPrefs.syncIngredients=true;recipeViewPrefs.autoCompleteIngredients=true;const m=meals.find(m=>m.id===537);openRecipeViewer(m,cookingContext('original','Saturday','Weekend',m))},
 open:()=>openEditor(537),meal:()=>meals.find(m=>m.id===537),storage:()=>captureBackupStorage(),valid:()=>validateBackupStorage(captureBackupStorage()),restore:s=>restoreBackupStorage(s),dirty:()=>editorHasPendingChanges(),
 links:()=>validRecipeIngredientLinks(meals.find(m=>m.id===537)),matches:()=>[...recipeIngredientMatches(meals.find(m=>m.id===537))].map(([step,ingredients])=>({step,ingredients})),once:()=>openCreateScheduledRecipe({planId:activePlanId,day:'Saturday',category:'Lunch'})
};'''

def expand(p,selector):
 e=p.locator(selector)
 if not e.evaluate('(e)=>e.open'):e.locator(':scope>summary').click();p.wait_for_timeout(30)

def ind(p,key):return p.locator('[data-editor-summary="'+key+'"]').inner_text()
def unit(p,index,label):p.locator('.make-ahead-task-editor').nth(index).get_by_role('button',name=label,exact=True).click()
def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport();batch3.seed();batch3.open()');p.wait_for_timeout(850)
 savedprefs=p.evaluate('batch3.storage().mealRotationEditorSectionsV1');assert p.locator('#editor details[open]').count()==0
 expand(p,'[data-editor-section="notes"]');expand(p,'#editorNeedsTweaking');expand(p,'#editorNotesSection');assert not p.locator('label[for="editNeedsTweakingNote"]').count() and not p.locator('#editorNotesSection label').count()
 assert p.locator('#recipeNotes').input_value()=='Keep notes';p.locator('#recipeNotes').fill('Draft notes')
 # Heading plus expands Make Ahead; each row's existing timing remains exact.
 ahead=p.locator('#recipeMakeAhead');assert not ahead.evaluate('(e)=>e.open');ahead.locator(':scope>summary').get_by_role('button',name='Add preparation task').click();assert ahead.evaluate('(e)=>e.open')
 rows=p.locator('.make-ahead-task-editor');assert rows.count()==3 and not ahead.get_by_role('combobox').count()
 assert rows.nth(0).get_by_role('button',name='Days',exact=True).get_attribute('aria-pressed')=='true' and rows.nth(1).get_by_role('button',name='Hours',exact=True).get_attribute('aria-pressed')=='true'
 rows.nth(2).get_by_role('textbox',name='Preparation task').fill('Custom preparation');rows.nth(2).get_by_role('spinbutton').fill('2.25');unit(p,2,'Hours')
 # Inline suggestions: no dialog, no duplicates, removal restores availability.
 expand(p,'[data-editor-section="serve"]');serve=p.locator('[data-editor-section="serve"]');assert serve.get_by_role('button',name='Remove Serve with Rice').count()==1
 assert not serve.locator('.meal-editor-suggestions').get_by_role('button',name='Rice',exact=True).count()
 serve.get_by_role('button',name='Remove Serve with Rice').click();assert ind(p,'serve')=='';serve.locator('.meal-editor-suggestions').get_by_role('button',name='Rice',exact=True).click();assert ind(p,'serve')=='Rice'
 custom=serve.get_by_role('textbox',name='Custom Serve with suggestion');custom.fill('Garlic bread');serve.get_by_role('button',name='Add custom Serve with suggestion').click();custom.fill('garlic BREAD');custom.press('Enter');assert len(p.locator('.meal-editor-chips button').all())==2
 # Inline linked picker uses AND search regardless of general saved setting.
 expand(p,'[data-editor-section="linked"]');linked=p.locator('[data-editor-section="linked"]');assert not linked.get_by_text('Match word order',exact=True).count()
 search=linked.get_by_role('searchbox',name='Search linked meals');search.fill('roast mississippi');option=linked.locator('label:visible').filter(has_text='Mississippi-Style Pot Roast');assert option.count()==1;option.get_by_role('checkbox').check();assert ind(p,'linked')=='2 linked'
 assert p.evaluate('batch3.dirty()') is True
 assert linked.locator('.meal-editor-group-heading').first.evaluate('(e)=>e.firstElementChild.textContent') in ['▸','▾']
 # Recipe controls retain import inputs and use independent collapsed subsections.
 expand(p,'[data-editor-section="recipe"]');assert p.locator('#editorIngredientsSection').evaluate('(e)=>e.open') is False and not p.locator('#editorInstructionsSection').evaluate('(e)=>e.open')
 expand(p,'#editorIngredientsSection');expand(p,'#editorInstructionsSection');assert p.locator('#ingredients').input_value()=='1 cup rice\n2 onions\n1 tsp salt'
 for id in ['ingredientPhotoButton','ingredientCameraButton','instructionPhotoButton','instructionCameraButton']:assert p.locator('#'+id).is_visible()
 for id in ['ingredientGalleryInput','ingredientCameraInput','instructionGalleryInput','instructionCameraInput']:assert p.locator('#'+id).count()==1
 expand(p,'#recipeIngredientLinks');links=p.locator('#recipeIngredientLinks');assert links.locator(':scope>summary').inner_text()=='Link Steps';assert not p.get_by_role('combobox',name='Ingredient matching',exact=True).count()
 selector=links.get_by_role('combobox',name='Instruction step for ingredient links');steps=selector.locator('option').evaluate_all('(es)=>es.map(e=>e.value)');assert len(steps)==2
 assert links.get_by_role('checkbox',name='1 cup rice',exact=True).is_checked();links.get_by_role('checkbox',name='1 tsp salt',exact=True).check();selector.select_option(steps[1]);assert links.get_by_role('checkbox',name='2 onions',exact=True).is_checked();links.get_by_role('checkbox',name='2 onions',exact=True).uncheck()
 selector.select_option(steps[0]);assert links.get_by_role('checkbox',name='1 tsp salt',exact=True).is_checked();assert links.get_by_role('button',name='Reset to automatic').is_visible()
 # Text updates leave the actual field/focus/scroll state intact.
 p.locator('#recipeInstructions').focus();before=p.locator('.meal-editor-fields').evaluate('(e)=>e.scrollTop');p.locator('#recipeInstructions').fill('Cook rice.\nChop onions.');assert p.evaluate('document.activeElement.id')=='recipeInstructions' and ind(p,'recipe')=='Added'
 p.locator('#save').click();m=p.evaluate('batch3.meal()');assert m['notes']=='Draft notes' and m['serveWith']==['Rice','Garlic bread'] and set(m['linkedMealIds'])=={25,535}
 assert m['makeAheadTasks'][:2]==[{'id':'a','description':'Thaw','daysBefore':2},{'id':'b','description':'Marinate','daysBefore':0,'hoursBefore':3}] and m['makeAheadTasks'][2]['hoursBefore']==2.25
 stored=p.evaluate('batch3.links()');assert len(stored)==2 and len(stored[0]['ingredients'])==2 and stored[1]['ingredients']==[]
 # Reopen ignores every saved expansion preference and preserves each step override.
 p.evaluate('batch3.open()');assert p.locator('#editor details[open]').count()==0
 expand(p,'[data-editor-section="recipe"]');expand(p,'#recipeIngredientLinks');selector=links.get_by_role('combobox');selector.select_option(steps[1]);assert not links.get_by_role('checkbox',name='2 onions',exact=True).is_checked()
 links.get_by_role('button',name='Reset to automatic').click();assert links.get_by_role('checkbox',name='2 onions',exact=True).is_checked();p.locator('#cancel').click();assert p.evaluate('batch3.links()')==stored
 p.evaluate('batch3.viewer()');p.locator('.recipe-viewer-steps .cooking-item').first.click();p.wait_for_timeout(100);checks=p.locator('.recipe-viewer-ingredients .cooking-item').evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-pressed"))');assert checks==['true','false','true'],checks;p.get_by_role('button',name='Close recipe',exact=True).click();p.wait_for_timeout(60)
 p.evaluate('batch3.valid()');saved=p.evaluate('batch3.storage()');assert saved['mealRotationEditorSectionsV1']==savedprefs and saved['mealRotationLinkedSearchAnyOrderV1']=='false'
 p.evaluate('batch3.restore',saved);p.reload();p.evaluate('combinedTest.viewport();promotionTest.my();batch3.open()');assert p.locator('#editor details[open]').count()==0
 p.locator('#cancel').click()
 # One-time uses the same structure, keyboard-sized viewport and sticky toolbar.
 p.evaluate('batch3.once()');assert not p.locator('#editor details[open]').count();p.locator('#name').fill('Batch three temporary');p.locator('#scheduledOneTime').check();expand(p,'[data-editor-section="notes"]');expand(p,'#editorNotesSection');p.locator('#recipeNotes').fill('Temporary notes');p.locator('#recipeNotes').focus();p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(90)
 assert p.locator('#editor .editor').evaluate('(e)=>e.scrollWidth<=e.clientWidth');box=p.locator('#save').bounding_box();assert box['y']+box['height']<=360
 p.locator('#save').click();p.evaluate('combinedTest.resize(800,0)');assert p.evaluate('remainingTest.temp().notes')=='Temporary notes'
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'collapsed sections, heading plus/segmented timing, inline suggestions/AND links, automatic/manual step associations/reset, imports retained, live indicators, save/cancel/reload/backup, one-time/mobile toolbar; no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
