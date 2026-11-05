"""One unchanged meal editor, four independent collapsible groups, no lost drafts."""
import copy
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
from editor_sections_fixture import open_editor_section as section,expand_editor_sections
f.EXTRA+='''window.compactEditorTest={
 seed:()=>{const m=meals.find(m=>m.id===1);m.notes='Keep regular notes';m.needsTweaking=true;m.needsTweakingNote='Less salt next time';m.favorite=true;m.makeAheadTasks=[{id:'thaw',description:'Thaw pork',daysBefore:1}];m.linkedMealIds=[20];m.labels=['Original'];recipeLabelCatalog=['Original','Added'];saveRecipeLabelCatalog();m.instructions=[{type:'step',text:'Cook for 15 minutes.'}];const items=recipeAssociationItems(m);m.ingredientStepLinks=[{step:items.steps[0].token,ingredients:[items.ingredients[0].token]}];persist();renderList()},
 pending:editorHasPendingChanges,
 long:()=>{const m=meals.find(m=>m.id===1);m.name='A very long recipe name with multiple lines and linked side descriptions';m.labels=['Extremely_long_unbroken_recipe_label_for_mobile_layout_testing'];persist()},
 shared:()=>{const m=meals.find(m=>m.id===1);m.linkGroup='shared-test';meals.push({...JSON.parse(JSON.stringify(m)),id:30,cat:'Mains'});persist()},
 open:id=>openEditor(id),backup:()=>slotBackup.capture()
};'''
def setup(b,name,w=320):
 c,p,e,pr=f.setup(b,name,w,'linked-slot');p.evaluate('compactEditorTest.seed()');return c,p,e,pr
def open_edit(p,id=1):p.evaluate('id=>compactEditorTest.open(id)',id);p.wait_for_timeout(850)
def nested(p,button,panel):
 if p.locator(panel).is_hidden():p.locator(button).tap()
def run(b,name,width):
 c,p,e,prefix=setup(b,name,width);before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);open_edit(p)
 assert p.locator('#name').is_visible() and p.locator('#cat').is_visible() and p.get_by_role('checkbox',name='In rotation',exact=True).is_visible();assert p.locator('#editor [data-editor-section]').count()==4 and not p.locator('#editor [data-editor-section][open]').count()
 assert p.locator('#editor .meal-editor-section>summary').all_text_contents()==['Timing','Organization','Recipe','Notes & Reminders'];assert p.locator('#editor #rotation').count()==1 and p.locator('#editor .actions button').count()==3
 assigned={'timing':['prep','totaltime','marinate'],'organization':['recipeLabels','editLinkedMeals','editorAdditionalGroups'],'recipe':['editorIngredientsSection','editorInstructionsSection','recipeIngredientLinks','url'],'notes':['editorNeedsTweaking','recipeMakeAhead','editorNotesSection']}
 for key,ids in assigned.items():
  for id in ids:assert p.locator('#'+id).evaluate('(e)=>e.closest("[data-editor-section]").dataset.editorSection')==key
 assert not p.evaluate('compactEditorTest.pending()');section(p,'timing');boxes=[p.locator('#'+id).bounding_box() for id in ['prep','totaltime','marinate']];assert max(x['y'] for x in boxes)-min(x['y'] for x in boxes)<1
 p.locator('#prep').fill('17');p.locator('#totaltime').fill('50');p.locator('#marinate').fill('2 hr');section(p,'recipe');assert p.locator('[data-editor-section="timing"]').get_attribute('open') is not None
 nested(p,'#toggleInstructions','#instructionsPanel');nested(p,'#toggleIngredients','#ingredientsPanel');assert p.locator('#ingredients').is_visible() and p.locator('#recipeInstructions').is_visible();assert p.locator('#instructionGalleryInput').get_attribute('accept')=='image/*' and p.locator('#instructionCameraInput').get_attribute('capture')=='environment';assert p.locator('#ingredientCameraInput').get_attribute('capture')=='environment'
 p.locator('#url').fill('https://example.com/kept-recipe');p.locator('#recipeIngredientLinks>summary').tap();p.get_by_role('combobox',name='Instruction step for ingredient links',exact=True).wait_for(state='visible')
 section(p,'organization');assert p.get_by_role('combobox',name='Choose an additional meal group',exact=True).is_visible();p.locator('#recipeLabels').tap();labelDialog=p.locator('[role=dialog]').last;labelDialog.get_by_text('Added',exact=True).locator('..').get_by_role('checkbox').tap();labelDialog.get_by_role('button',name='OK',exact=True).tap();assert 'Added' in p.locator('#recipeLabels').inner_text()
 section(p,'notes');p.locator('#recipeMakeAhead>summary').tap();p.get_by_role('textbox',name='Preparation task',exact=True).fill('Thaw pork slowly');p.locator('#recipeMakeAhead').get_by_role('button',name='Add preparation task',exact=True).tap();p.get_by_role('textbox',name='Preparation task',exact=True).last.fill('Chop vegetables');p.get_by_role('combobox',name='Preparation timing',exact=True).last.select_option('2');nested(p,'#toggleRecipeNotes','#recipeNotesPanel');p.locator('#recipeNotes').fill('Keep regular notes, edited');p.locator('#editNeedsTweakingNote').fill('Less salt and more herbs')
 # Collapse all sections; drafts remain in the same controls and Save still reads them.
 for key in assigned:p.locator('[data-editor-section="'+key+'"]>summary').tap()
 assert not p.locator('#editor [data-editor-section][open]').count();assert p.locator('#prep').input_value()=='17' and p.locator('#recipeNotes').input_value()=='Keep regular notes, edited';assert p.evaluate('compactEditorTest.pending()');p.screenshot(path='/tmp/compact-editor-'+name+'-'+str(width)+'.png');p.locator('#save').tap()
 after=state(p);m=next(m for m in after['meals'] if m['id']==1);original=next(m for m in before['meals'] if m['id']==1)
 assert m['prep']=='17' and m['total']=='50' and m['marinate']=='2 hr' and m['url']=='https://example.com/kept-recipe';assert m['notes']=='Keep regular notes, edited' and m['needsTweakingNote']=='Less salt and more herbs';assert set(m['labels'])=={'Original','Added'} and m['makeAheadTasks'][0]['id']=='thaw' and m['makeAheadTasks'][0]['description']=='Thaw pork slowly' and m['makeAheadTasks'][-1]['daysBefore']==2
 for key in ['id','ingredients','instructions','ingredientStepLinks','linkedMealIds','favorite','lastCooked','rotation','cat']:assert m.get(key)==original.get(key),(key,m.get(key),original.get(key))
 assert compose(p)==schedule and f.sources(p)==groceries and after['sessions']==before['sessions'] and after['scales']==before['scales']
 open_edit(p);assert not p.locator('#editor [data-editor-section][open]').count();expand_editor_sections(p);nested(p,'#toggleInstructions','#instructionsPanel');p.locator('#recipeInstructions').fill('Discard this draft.');nested(p,'#toggleIngredients','#ingredientsPanel');p.locator('#ingredients').fill('99 cups discarded');nested(p,'#toggleRecipeNotes','#recipeNotesPanel');p.locator('#recipeNotes').fill('Discard notes');p.locator('#cat').select_option('Mains');p.locator('#cancel').tap();assert state(p)['meals']==after['meals'] and compose(p)==schedule
 p.reload();assert state(p)['meals']==after['meals'];assert not e,e
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'four collapsed defaults, compact timing/visible fields, existing nested editors/photos/links/labels/tasks/notes; independent sections retain drafts, Save and Cancel/reload preserve IDs/associations/links/status/schedule/progress/groceries',flush=True);c.close()
def groups_and_validation(b,name):
 c,p,e,_=setup(b,name,360);p.evaluate('compactEditorTest.shared()');open_edit(p,30);assert p.locator('#cat').input_value()=='Mains';section(p,'organization');assert p.get_by_role('combobox',name='Additional group',exact=True).input_value()=='Weekend';p.locator('#cancel').tap()
 # Clear the current primary membership and choose a replacement using the existing draft logic.
 open_edit(p,6);section(p,'organization');p.get_by_role('combobox',name='Choose an additional meal group',exact=True).select_option('Mains');assert p.get_by_role('combobox',name='Additional group',exact=True).input_value()=='Mains';p.get_by_role('button',name='Remove meal from Weekend',exact=True).tap();assert p.locator('#cat').input_value()=='';p.get_by_role('button',name='Remove meal from Mains',exact=True).tap();assert p.locator('#cat').input_value()=='' and p.locator('#cat').is_visible();p.locator('#cat').select_option('Sides');p.locator('#save').tap();assert next(m for m in state(p)['meals'] if m['id']==6)['cat']=='Sides'
 before=copy.deepcopy(state(p));open_edit(p);section(p,'timing');p.locator('#prep').fill('not a duration');p.locator('[data-editor-section="timing"]>summary').tap();p.locator('#save').tap();p.get_by_role('button',name='OK',exact=True).tap();assert p.locator('#prep').is_visible() and p.locator('#prep').evaluate('(e)=>e===document.activeElement');assert state(p)['meals']==before['meals'];p.locator('#cancel').tap()
 # Removing Needs Adjusting still uses the existing confirmation; Cancel keeps the note.
 open_edit(p);section(p,'notes');p.locator('#editNeedsTweaking').uncheck();d=p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True);d.get_by_role('button',name='Cancel removal',exact=True).tap();assert p.locator('#editNeedsTweaking').is_checked() and p.locator('#editNeedsTweakingNote').input_value()=='Less salt next time';p.locator('#cancel').tap();assert state(p)['meals']==before['meals'] and not e,e
 print('PASS',name,'primary Group reflects edited shared copy, additional groups/clearing retain existing semantics, hidden timing validation reveals field, status removal confirmation and overall Cancel preserve data',flush=True);c.close()
def long_layout(b,name):
 c,p,e,_=setup(b,name,320);p.evaluate('compactEditorTest.long()');open_edit(p)
 for size in [{'width':320,'height':800},{'width':740,'height':360}]:
  p.set_viewport_size(size);expand_editor_sections(p);p.locator('#recipeMakeAhead>summary').tap() if p.locator('#recipeMakeAhead').get_attribute('open') is None else None;nested(p,'#toggleRecipeNotes','#recipeNotesPanel');p.locator('#recipeNotes').fill('Preserve the same draft across rotation');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert p.locator('#recipeLabels').evaluate('(e)=>e.scrollWidth<=e.clientWidth+1');assert all(h>=44 for h in p.locator('.meal-editor-section>summary').evaluate_all('(es)=>es.map(e=>e.getBoundingClientRect().height)'));p.locator('#save').scroll_into_view_if_needed();assert p.locator('#save').is_visible();p.screenshot(path='/tmp/editor-expanded-'+name+'-'+str(size['width'])+'.png')
 p.locator('#cancel').tap();assert not e,e;c.close();print('PASS',name,'long names/unbroken labels, expanded sections and bottom icons remain usable in narrow portrait and short landscape; no horizontal overflow',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   groups_and_validation(b,name);long_layout(b,name)
   for width in [320,360]:run(b,name,width)
  b.close()
