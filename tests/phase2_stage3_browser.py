"""Stage 3: viewer editing, grocery navigation, and new-only defaults. Synthetic data."""
import copy,json
from playwright.sync_api import sync_playwright,expect
import phase2_stage2_browser as s2
stage=s2.stage
stage.f.HOOK += '''window.stage3Test={
 open:(id=1,preview=false)=>{const meal=meals.find(m=>m.id===id),entry=getDisplayedWeekdayMeals().find(e=>e.meal.id===id);openSavedMealRecipe(meal,preview?null:entry?cookingContext(activePlanId,entry.day,entry.cat,meal,entry.linkedTo):null)},
 state:()=>({id:recipeViewer?.mealId,context:recipeViewer?.context,tab:recipeViewer?.activeTab.key,tabs:recipeViewer?.tabs.map(t=>t.key),previewScale:recipeViewer?.previewScale,mode:recipeViewer&&recipeViewingMode(),ratio:recipeViewer?.activeTab.ratio,scroll:recipeViewer?.cover.scrollTop,panes:recipeViewer?[...recipeViewer.content.querySelectorAll('.recipe-pane')].map(p=>p.scrollTop):[],progress:cookingSessions,scales:occurrenceScales}),
 sameNames:()=>{for(const m of meals)m.name='Same display name';persist()},
 groceryLong:()=>{const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const m of meals){m.ingredients.push(...Array.from({length:30},(_,i)=>(m.id+1)+' tbsp pantry item '+i));selected[String(m.id)]=[...m.ingredients]}localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));masterGroceryExcludedMealKeys.add(groceryMealKey(mealPlans[0],meals.find(m=>m.id===20)));saveMasterGroceryMealExclusions();persist()},
 grocery:()=>{showTop=true;allMealsActive=false;groceryTabActive=true;render()},
 long:()=>{for(const m of meals){m.ingredients.push(...Array.from({length:45},(_,i)=>(i+1)+' tbsp ingredient '+m.id+' '+i));m.instructions.push(...Array.from({length:35},(_,i)=>({type:'step',text:'Cook ingredient '+i+' for 10 minutes. '+('Stir carefully. '.repeat(8))})))}persist();render()},
 tab:id=>switchRecipeTab(recipeViewer.tabs.find(t=>t.mealId===String(id))),
 add:()=>{openMasterCategories('Sauces');addRecipeToGroup('Sauces')},
 import:(idea=false)=>showRecipeImportSelection([{'@type':'Recipe',name:'Imported new recipe',identifier:'stage3-new',recipeIngredient:['2 cups rice','3 apples'],recipeInstructions:'Simmer for 15 minutes.',recipeCategory:'Sauces'},{'@type':'Recipe',name:'Existing duplicate',identifier:'existing-stage3',recipeIngredient:['9 cups rice'],recipeInstructions:'New imported directions.'}], 'stage3.json'),
 legacy:()=>{const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selected['1']=[];delete selected['3'];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));meals.find(m=>m.id===2).importSourceId='existing-stage3';persist()},
 related:()=>{const target=meals.find(m=>m.id===2);target.recipeImportReferences=[{name:'New related recipe',url:'https://recipes.test/stage3-related'}];importIngredientsFromWebsite=async()=>{const lines=['2 cups rice','3 apples'];lines.recipeDetails={name:'New related recipe',ingredients:[...lines],instructions:[{type:'step',text:'Simmer for 15 minutes.'}]};return lines};openRecipeImportReview([target],false)},
 shared:()=>{const main=meals.find(m=>m.id===1),peer=meals.find(m=>m.id===3);main.linkGroup=peer.linkGroup='stage3-shared';peer.cat='Sauces';peer.favorite=true;persist();stage3Test.open()},
 rawSelections:()=>JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}'),
 schedule:id=>scheduleMealFromGroups(id,{planId:activePlanId,day:'Sunday',category:null,occasional:true}),
 defaultSources:id=>getGroceryContributions(true).filter(s=>String(s.mealId)===String(id)),
 chooser:id=>openTopIngredientChooser(meals.find(m=>m.id===id)),
 exclude:id=>{const meal=meals.find(m=>m.id===id),selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selections[String(id)]=[meal.ingredients[1]];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));persist();render()},
 preview:()=>recipeViewer.previewProgress
};'''

def setup(b,name,width=360):return s2.setup(b,name,width,multi=True)
def view(p):return p.evaluate('stage3Test.state()')
def editor(p):p.get_by_role('button',name='Edit Recipe',exact=True).click();return p.get_by_role('dialog',name='Edit Recipe',exact=True)
def clean(errors):assert not errors,errors

def viewer_edit(b,name,width):
 c,p,errors,_=setup(b,name,width);p.evaluate('stage3Test.long();weekTest.check();stage3Test.open()');p.wait_for_timeout(150);before=view(p);definitions=stage.state(p)['meals'];rows=stage.rows(p);checks=s2.prior.progress(p)
 # Use a linked tab; preserve its scroll and all other tabs' state.
 p.evaluate('stage3Test.tab(20)');p.locator('.recipe-instructions-pane').evaluate('(e)=>e.scrollTop=250');p.wait_for_timeout(120);before=view(p)
 d=editor(p);p.screenshot(path='/tmp/stage3-editor-'+name+'-'+str(width)+'.png');assert p.locator('#recipeViewer').is_visible() and not p.locator('#editor .editor').count();d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Canceled note');d.get_by_role('button',name='Cancel',exact=True).click();assert stage.state(p)['meals']==definitions and view(p)['id']==before['id']
 d=editor(p);d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Edited from viewer\nKeep Unicode: café');d.get_by_role('textbox',name='Recipe source link',exact=True).fill('https://recipes.test/new?x=1&y=2');d.get_by_role('button',name='Save recipe',exact=True).click();assert not d.count();after=view(p)
 assert after['tab']==before['tab'] and after['tabs']==before['tabs'] and after['mode']==before['mode'] and after['ratio']==before['ratio'];assert after['progress']==before['progress'] and after['scales']==before['scales'];assert all(abs(a-b)<=3 for a,b in zip(after['panes'],before['panes']))
 saved=next(m for m in stage.state(p)['meals'] if m['id']==20);assert saved['notes']=='Edited from viewer\nKeep Unicode: café' and saved['originalRecipeUrl']=='https://recipes.test/new?x=1&y=2';assert stage.rows(p)==rows and s2.prior.progress(p)==checks
 # Content changes preserve unchanged completion tokens and scale, and leave advanced fields alone.
 d=editor(p);ing=d.get_by_role('textbox',name='Ingredients and quantities',exact=True);ing.fill(ing.input_value()+'\n2 lemons');instructions=d.get_by_role('textbox',name='Cooking instructions',exact=True);instructions.fill(instructions.input_value()+'\n\nServe warm.');d.get_by_role('button',name='Save recipe',exact=True).click();assert view(p)['progress']==before['progress'] and view(p)['scales']==before['scales'];record=next(m for m in stage.state(p)['meals'] if m['id']==20);assert record['ingredients'][-1]=='2 lemons' and record['instructions'][-1]['text']=='Serve warm.'
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.get_by_role('button',name='Close recipe',exact=True).click();p.reload();assert next(m for m in stage.state(p)['meals'] if m['id']==20)['notes']==saved['notes'];clean(errors);c.close();print('PASS',name,width,'viewer edit Cancel/content/notes/source; linked active tab, progress, scale, split scroll and reload',flush=True)

def groceries(b,name,width,same_names=False):
 c,p,errors,_=setup(b,name,width)
 if same_names:p.evaluate('stage3Test.sameNames()')
 p.evaluate('stage3Test.groceryLong();weekTest.check();stage3Test.grocery()');before=p.evaluate('weekTest.storage()');checks=s2.prior.progress(p);rows=stage.rows(p)
 names=p.locator('.grocery-ingredient-name');assert names.count()>20;names.nth(15).click();links=p.locator('.grocery-recipe-source:not([hidden]) .grocery-recipe-link');assert links.count()>=2
 for index in range(min(5,links.count())):
  link=links.nth(index);label=link.inner_text();expected_id=link.get_attribute('data-meal-id');expected_plan=link.get_attribute('data-plan-id');expected_day=link.get_attribute('data-day');link.scroll_into_view_if_needed();scroll=p.evaluate('scrollY');assert scroll>100;link.click();assert p.locator('#recipeViewer').is_visible();id=int(view(p)['id']);assert str(id)==expected_id and view(p)['context']['planId']==expected_plan and view(p)['context']['day']==expected_day;record=next(m for m in stage.state(p)['meals'] if m['id']==id);assert label.startswith(record['name']+' (');p.get_by_role('button',name='Close recipe',exact=True).click();p.wait_for_timeout(60);assert abs(p.evaluate('scrollY')-scroll)<=3;assert s2.prior.progress(p)==checks and stage.rows(p)==rows
 assert p.evaluate('weekTest.storage()')==before;clean(errors);c.close();print('PASS',name,width,'shared grocery contributors open exact recipe/context and restore scroll/checks/quantities/filters/storage',flush=True)

def defaults(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage3Test.legacy()');before=stage.state(p)['meals'];selected=p.evaluate('stage3Test.rawSelections()');p.evaluate('stage3Test.add()');assert p.locator('#rotation').is_checked();p.locator('#name').fill('Full editor new default');p.locator('#editor [data-editor-section=recipe] > summary').click();p.locator('#toggleIngredients').click();p.locator('#ingredients').fill('2 cups rice\n3 apples');p.locator('#save').click();p.wait_for_function('!document.querySelector("#editor .editor")');record=next(m for m in stage.state(p)['meals'] if m['name']=='Full editor new default');assert record['rotation'] is True and record['groceryDefaultAll'] is True
 p.evaluate('stage3Test.schedule',record['id']);assert len(p.evaluate('stage3Test.defaultSources',record['id']))==2;p.evaluate('stage3Test.chooser',record['id']);chooser=p.locator('[data-recipe-edit-draft]').filter(has=p.get_by_text('Add ingredients to grocery list',exact=True));assert chooser.get_by_role('checkbox',name='2 cups rice',exact=True).is_checked();chooser.get_by_role('checkbox',name='2 cups rice',exact=True).uncheck();chooser.get_by_role('button',name='Save',exact=True).click();assert len(p.evaluate('stage3Test.defaultSources',record['id']))==1
 # Imported duplicates retain their original status and selections; only new imports get defaults.
 p.evaluate('stage3Test.import()');d=p.get_by_role('dialog',name='Choose meal groups',exact=True);assert d.get_by_role('checkbox',name='Add imported recipes to rotation',exact=True).is_checked();d.get_by_role('button',name='Import recipes',exact=True).click();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click()
 imported=next(m for m in stage.state(p)['meals'] if m['name']=='Imported new recipe');assert imported['rotation'] and imported['groceryDefaultAll'];assert next(m for m in stage.state(p)['meals'] if m['id']==2)['rotation']==next(m for m in before if m['id']==2)['rotation']
 assert all(p.evaluate('stage3Test.rawSelections()').get(k)==v for k,v in selected.items());assert not p.evaluate('stage3Test.defaultSources',1)
 p.evaluate('stage3Test.schedule',imported['id']);assert len(p.evaluate('stage3Test.defaultSources',imported['id']))==2
 backup=p.evaluate('weekTest.storage()');p.reload();assert len(p.evaluate('stage3Test.defaultSources',imported['id']))==2;p.evaluate('weekTest.restore',backup);p.reload();assert len(p.evaluate('stage3Test.defaultSources',imported['id']))==2;clean(errors);c.close();print('PASS',name,'new full-editor/import defaults, explicit exclusions, existing exclusions/status, reload and backup',flush=True)

def failed_save(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage3Test.open()');before=stage.state(p)['meals'];rows=stage.rows(p);d=editor(p);d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Failed draft')
 p.evaluate('''()=>{window.stage3Set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationDataV1'))throw Error('synthetic quota');return stage3Set.call(this,k,v)}}''');d.get_by_role('button',name='Save recipe',exact=True).click();expect(d.get_by_role('status')).to_contain_text('draft is still open');assert stage.state(p)['meals']==before and stage.rows(p)==rows
 d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Latest retry edits');p.evaluate('()=>Storage.prototype.setItem=stage3Set');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('!document.querySelector("[data-viewer-recipe-draft]")');assert next(m for m in stage.state(p)['meals'] if m['id']==1)['notes']=='Latest retry edits';assert p.locator('#recipeViewer').is_visible();p.get_by_role('button',name='Close recipe',exact=True).click();p.reload();assert next(m for m in stage.state(p)['meals'] if m['id']==1)['notes']=='Latest retry edits';clean(errors);c.close();print('PASS',name,'viewer save atomic rollback, retained latest draft, Retry Save and reload',flush=True)

def defaults_options(b,name):
 c,p,errors,_=setup(b,name)
 target={'planId':'original','day':'Tuesday','category':'Rice','occasional':False};d=s2.create_dialog(p,target)
 assert d.get_by_role('checkbox',name='Add to rotation',exact=True).is_checked() and d.get_by_role('checkbox',name='Include these ingredients in groceries',exact=True).is_checked()
 d.get_by_role('textbox',name='Recipe name',exact=True).fill('Scheduled with new defaults');d.get_by_role('textbox',name='Ingredients',exact=True).fill('4 carrots\n2 cups rice');d.get_by_role('button',name='Save recipe and schedule',exact=True).click();created=next(m for m in stage.state(p)['meals'] if m['name']=='Scheduled with new defaults');assert created['rotation'] and len(p.evaluate('stage3Test.defaultSources',created['id']))==2
 d=s2.create_dialog(p,target);s2.fill_recipe(d,'Explicit scheduled Idea',rotation=False,groceries=False);d.get_by_role('button',name='Save recipe and schedule',exact=True).click();idea=next(m for m in stage.state(p)['meals'] if m['name']=='Explicit scheduled Idea');assert not idea['rotation'] and not p.evaluate('stage3Test.defaultSources',idea['id'])
 p.evaluate('stage3Test.import()');d=p.get_by_role('dialog',name='Choose meal groups',exact=True);d.get_by_role('checkbox',name='Add imported recipes to rotation',exact=True).uncheck();d.get_by_role('button',name='Import recipes',exact=True).click();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();imported=next(m for m in stage.state(p)['meals'] if m['name']=='Imported new recipe');assert imported['rotation'] is False;p.evaluate('stage3Test.schedule',imported['id']);assert len(p.evaluate('stage3Test.defaultSources',imported['id']))==2
 p.reload();assert not next(m for m in stage.state(p)['meals'] if m['id']==idea['id'])['rotation'];assert not p.evaluate('stage3Test.defaultSources',idea['id']);clean(errors);c.close();print('PASS',name,'Change Meal defaults and explicit Ideas/grocery opt-out; imported Ideas still include groceries when scheduled',flush=True)

def editor_accessibility_and_preview(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage3Test.open(3,true)');p.get_by_role('button',name='Scale Recipe',exact=True).click();p.get_by_role('menuitemradio',name='2×',exact=True).click();p.locator('.recipe-ingredients-pane .cooking-item').first.click();before=copy.deepcopy(view(p));progress=p.evaluate('stage3Test.preview()')
 d=editor(p);d.get_by_role('textbox',name='Ingredients and quantities',exact=True).focus();p.keyboard.press('Tab');assert d.get_by_role('textbox',name='Cooking instructions',exact=True).evaluate('(e)=>e===document.activeElement');d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Preview note');p.go_back();assert d.is_visible() and p.locator('#recipeViewer').is_visible();d.get_by_role('button',name='Save recipe',exact=True).click();assert view(p)['tab']==before['tab'] and view(p)['previewScale']==2 and p.evaluate('stage3Test.preview()')==progress;assert p.locator('.recipe-ingredients-pane .cooking-item').first.get_attribute('aria-pressed')=='true'
 d=editor(p);d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Discard via Escape');p.keyboard.press('Escape');assert not d.count() and next(m for m in stage.state(p)['meals'] if m['id']==3)['notes']=='Preview note'
 clean(errors);c.close();print('PASS',name,'viewer keyboard focus/Escape, Back retains open draft, preview completion and 2x scaling',flush=True)

def quantity_and_failure_cancel(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('weekTest.check();stage3Test.open()');d=editor(p);field=d.get_by_role('textbox',name='Ingredients and quantities',exact=True);field.fill(field.input_value().replace('1 cups rice','3 cups rice'));d.get_by_role('button',name='Save recipe',exact=True).click();assert any(s['original']=='3 cups rice' for s in p.evaluate('stage3Test.defaultSources',1));assert next(m for m in stage.state(p)['meals'] if m['id']==1)['ingredients'][0]=='3 cups rice'
 before=p.evaluate('weekTest.storage()');definitions=copy.deepcopy(stage.state(p)['meals']);d=editor(p);d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Cancel failed proposal');field=d.get_by_role('textbox',name='Ingredients and quantities',exact=True);field.fill(field.input_value().replace('3 cups rice','5 cups rice'));p.evaluate('''()=>{window.stage3Set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationSelectedIngredientsV1'))throw Error('synthetic selection failure');return stage3Set.call(this,k,v)}}''');d.get_by_role('button',name='Save recipe',exact=True).click();expect(d.get_by_role('status')).to_contain_text('draft is still open');assert stage.state(p)['meals']==definitions
 with p.expect_download() as download:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 assert 'Cancel failed proposal' in open(download.value.path()).read();p.evaluate('()=>Storage.prototype.setItem=stage3Set');d.get_by_role('button',name='Cancel',exact=True).click();assert not p.locator('#mealSaveWarning').count();assert p.evaluate('weekTest.storage()')==before;clean(errors);c.close();print('PASS',name,'quantity edits retain selection; selection-write rollback, draft export and cancellation preserve durable data',flush=True)

def related_import_defaults(b,name,ideas=False):
 c,p,errors,_=setup(b,name)
 p.evaluate('stage3Test.related')
 d=p.get_by_role('dialog',name='Review related recipes',exact=True);rotation=d.get_by_role('checkbox',name='Add newly imported related recipes to rotation',exact=True);assert rotation.is_checked();rotation.set_checked(not ideas);d.get_by_role('checkbox',name='Link New related recipe',exact=True).check();d.get_by_role('button',name='Save reviewed recipe changes',exact=True).click();p.wait_for_function('!document.querySelector("#recipeImportReview")')
 record=next(m for m in stage.state(p)['meals'] if m['name']=='New related recipe');assert record['rotation'] is (not ideas) and record['groceryDefaultAll'] is True;assert record['id'] in next(m for m in stage.state(p)['meals'] if m['id']==2)['linkedMealIds']
 p.evaluate('stage3Test.schedule',2);assert len(p.evaluate('stage3Test.defaultSources',record['id']))==2;p.reload();assert next(m for m in stage.state(p)['meals'] if m['id']==record['id'])['rotation'] is (not ideas);clean(errors);c.close();print('PASS',name,'related recipe import defaults/Ideas',ideas,'and selected linked groceries',flush=True)

def shared_content(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage3Test.shared');before=copy.deepcopy(stage.state(p)['meals']);rows=stage.rows(p);d=editor(p);d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Shared viewer note');d.get_by_role('button',name='Save recipe',exact=True).click();after=stage.state(p)['meals'];assert [dict(m,notes=next(old['notes'] for old in before if old['id']==m['id'])) for m in after]==before;assert all(m['notes']=='Shared viewer note' for m in after if m['id'] in [1,3]);assert stage.rows(p)==rows;clean(errors);c.close();print('PASS',name,'shared recipe content propagates while membership, Favorites, statuses and schedules stay intact',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:viewer_edit(b,name,width);groceries(b,name,width)
   groceries(b,name,320,True);defaults(b,name);failed_save(b,name);defaults_options(b,name);editor_accessibility_and_preview(b,name);quantity_and_failure_cancel(b,name);related_import_defaults(b,name);related_import_defaults(b,name,True);shared_content(b,name)
  b.close()
