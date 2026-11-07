"""Live draft summaries and compatible Notes & Reminders controls, isolated mobile fixtures."""
from playwright.sync_api import sync_playwright
import remaining_meal_features_browser as base
f=base.f
f.EXTRA+='''window.batch2={
 seed:(legacy=false)=>{remainingTest.seed();const m=meals.find(m=>m.id===537);m.ingredients=[];m.instructions='';m.url='';m.notes='Original notes';m.needsTweaking=true;m.needsTweakingNote=legacy?'':'Less salt';m.makeAheadTasks=[{id:'same',description:'Same-day task',daysBefore:0},{id:'custom',description:'Early task',daysBefore:5,custom:'keep'},{id:'decimal',description:'Fractional legacy',daysBefore:.75}];persist()},
 open:()=>openEditor(537),meal:()=>meals.find(m=>m.id===537),
 prefs:()=>recipeEditorSections,rows:()=>scheduledMakeAheadTasks().filter(x=>x.entry.meal.id===537).map(x=>({id:x.task.id,due:x.due,scheduled:x.scheduled})),
 validate:()=>{const s=captureBackupStorage();validateBackupStorage(s);return s},restore:s=>restoreBackupStorage(s),
 once:()=>openCreateScheduledRecipe({planId:activePlanId,day:'Saturday',category:'Lunch'}),
 unusual:()=>{const m=meals.find(m=>m.id===537);m.makeAheadTasks=[{id:'opaque',description:'Keep custom timing',daysBefore:'legacy-custom',custom:'keep'}];persist()},
 library:()=>JSON.stringify(meals.filter(m=>!m._scheduledEditorDraft))
};'''

def open_details(p,selector):
 d=p.locator(selector)
 if not d.evaluate('(e)=>e.open'):d.locator(':scope>summary').click();p.wait_for_timeout(30)

def indicator(p,key):return p.locator('[data-editor-summary="'+key+'"]').inner_text()
def row(p,index):return p.locator('.make-ahead-task-editor').nth(index)
def task(p,index):return row(p,index).get_by_role('textbox',name='Preparation task',exact=True)
def amount(p,index):return row(p,index).get_by_role('spinbutton',name='Preparation lead time',exact=True)
def unit(p,index):return row(p,index).get_by_role('combobox',name='Preparation lead time unit',exact=True)

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport();batch2.seed();batch2.open()');p.wait_for_timeout(850)
 assert not p.locator('[data-editor-subsection][open]').count()
 open_details(p,'[data-editor-section="notes"]')
 assert p.locator('[data-editor-subsection]').evaluate_all('(es)=>es.map(e=>e.dataset.editorSubsection)')==['adjusting','ahead','notes']
 for key in ['adjusting','ahead','notes']:open_details(p,'[data-editor-subsection="'+key+'"]')
 assert p.locator('#editNeedsTweaking').get_attribute('type')=='hidden'
 assert p.locator('#editNeedsTweakingNote').input_value()=='Less salt' and p.locator('#recipeNotes').input_value()=='Original notes'
 assert amount(p,0).input_value()=='0' and amount(p,1).input_value()=='5' and amount(p,2).input_value()=='0.75'
 # Only text indicators update: retain the actual textarea, focus, text and expanded sections.
 p.locator('#recipeNotes').fill('Draft notes');p.locator('#recipeNotes').focus();p.wait_for_timeout(80);before=p.locator('.meal-editor-fields').evaluate('(e)=>e.scrollTop');node=p.locator('#recipeNotes').element_handle()
 p.locator('#recipeNotes').fill('');assert indicator(p,'notes')=='Added' and p.evaluate('document.activeElement.id')=='recipeNotes' and node.evaluate('(e)=>e.isConnected') and p.locator('.meal-editor-fields').evaluate('(e)=>e.scrollTop')==before
 p.locator('#editorNeedsTweaking').get_by_role('button',name='Remove Needs Adjusting',exact=True).click()
 assert p.locator('#editNeedsTweakingNote').input_value()=='' and not p.evaluate('document.getElementById("editNeedsTweaking").checked')
 for _ in range(3):row(p,0).get_by_role('button',name='Remove preparation task').click()
 assert indicator(p,'notes')==''
 p.locator('#editNeedsTweakingNote').fill('More seasoning');assert indicator(p,'notes')=='Added'
 p.locator('#editNeedsTweakingNote').fill('');assert indicator(p,'notes')==''
 task(p,0).fill('Marinate');amount(p,0).fill('3');unit(p,0).select_option('hours');assert indicator(p,'notes')=='Added'
 p.locator('#recipeMakeAhead').get_by_role('button',name='Add preparation task',exact=True).click();task(p,1).fill('Thaw');amount(p,1).fill('2');unit(p,1).select_option('days')
 # Other section indicators reflect the current selection-dialog drafts.
 open_details(p,'[data-editor-section="serve"]');p.locator('#serveWith').click();d=p.get_by_role('dialog',name='Serve with');d.get_by_role('checkbox',name='Rice',exact=True).check();d.get_by_role('button',name='Save Serve with').click();assert indicator(p,'serve')=='Rice'
 p.locator('#serveWith').click();d=p.get_by_role('dialog',name='Serve with');d.get_by_role('checkbox',name='Rice',exact=True).uncheck();d.get_by_role('button',name='Save Serve with').click();assert indicator(p,'serve')==''
 open_details(p,'[data-editor-section="linked"]');p.locator('#editLinkedMeals').click();d=p.get_by_role('heading',name='Linked meals').locator('..');d.get_by_role('searchbox').fill('Garlic Bread');d.locator('label:visible').filter(has_text='Garlic Bread').get_by_role('checkbox').first.check();d.get_by_role('button',name='OK',exact=True).click();assert indicator(p,'linked')=='1 linked'
 p.locator('#editLinkedMeals').click();d=p.get_by_role('heading',name='Linked meals').locator('..');d.get_by_role('searchbox').fill('Garlic Bread');d.locator('label:visible').filter(has_text='Garlic Bread').get_by_role('checkbox').first.uncheck();d.get_by_role('button',name='OK',exact=True).click();assert indicator(p,'linked')==''
 open_details(p,'[data-editor-section="recipe"]');base.reveal(p,'#ingredients');p.locator('#ingredients').fill('1 cup rice');assert indicator(p,'recipe')=='Added';p.locator('#ingredients').fill('');assert indicator(p,'recipe')==''
 base.reveal(p,'#recipeInstructions');p.locator('#recipeInstructions').fill('Cook.');assert indicator(p,'recipe')=='Added';p.locator('#recipeInstructions').fill('');assert indicator(p,'recipe')==''
 p.locator('#url').fill('https://example.test/recipe');assert indicator(p,'recipe')=='Added';p.locator('#url').fill('');assert indicator(p,'recipe')==''
 # Cancel discards every recipe draft but retains display preferences.
 p.locator('#cancel').click();m=p.evaluate('batch2.meal()');assert m['notes']=='Original notes' and m['needsTweakingNote']=='Less salt' and len(m['makeAheadTasks'])==3
 p.evaluate('batch2.open()');p.wait_for_timeout(850);assert p.locator('[data-editor-subsection][open]').count()==3
 # Keep same-day/custom/fractional legacy data byte-for-byte while adding exact hours.
 open_details(p,'[data-editor-section="notes"]');p.locator('#recipeNotes').fill('Saved new notes');p.locator('#editNeedsTweakingNote').fill('Saved adjustment')
 p.locator('#recipeMakeAhead').get_by_role('button',name='Add preparation task',exact=True).click();task(p,3).fill('Three hours');amount(p,3).fill('3');unit(p,3).select_option('hours')
 amount(p,3).fill('-1');p.locator('#save').click();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();assert p.locator('#recipeMakeAhead').is_visible();amount(p,3).fill('3')
 p.locator('#recipeMakeAhead').get_by_role('button',name='Add preparation task',exact=True).click();task(p,4).fill('Twenty-seven hours');amount(p,4).fill('27');unit(p,4).select_option('hours')
 p.locator('#save').click();m=p.evaluate('batch2.meal()');assert m['notes']=='Saved new notes' and m['needsTweakingNote']=='Saved adjustment'
 assert m['makeAheadTasks'][:3]==[{'id':'same','description':'Same-day task','daysBefore':0},{'id':'custom','description':'Early task','daysBefore':5,'custom':'keep'},{'id':'decimal','description':'Fractional legacy','daysBefore':.75}]
 assert m['makeAheadTasks'][3]['hoursBefore']==3 and m['makeAheadTasks'][3]['daysBefore']==0
 rows=p.evaluate('batch2.rows()');h=next(x for x in rows if x['id']==m['makeAheadTasks'][4]['id']);assert h['due']<h['scheduled']
 saved=p.evaluate('batch2.validate()');p.evaluate('batch2.restore',saved);p.reload();p.evaluate('combinedTest.viewport();promotionTest.my();batch2.open()');p.wait_for_timeout(850)
 assert p.locator('#recipeNotes').input_value()=='Saved new notes' and unit(p,3).input_value()=='hours' and amount(p,3).input_value()=='3'
 p.locator('#cancel').click()
 # An opaque legacy lead time remains visible and survives an unrelated Save.
 p.evaluate('batch2.unusual();batch2.open()');open_details(p,'[data-editor-section="notes"]');open_details(p,'#recipeMakeAhead');assert p.get_by_text('Saved lead time: legacy-custom days (retained until edited).',exact=True).is_visible();p.locator('#save').click();assert p.evaluate('batch2.meal().makeAheadTasks[0]')=={'id':'opaque','description':'Keep custom timing','daysBefore':'legacy-custom','custom':'keep'}
 # Legacy marked-without-note status survives save, and explicit trash removes it.
 p.evaluate('batch2.seed(true);batch2.open()');open_details(p,'[data-editor-section="notes"]');open_details(p,'#editorNeedsTweaking');assert p.get_by_text('Marked for adjustment (no note).',exact=True).is_visible()
 p.locator('#save').click();assert p.evaluate('batch2.meal().needsTweaking') is True
 p.evaluate('batch2.open()');open_details(p,'[data-editor-section="notes"]');open_details(p,'#editorNeedsTweaking');p.locator('#editorNeedsTweaking').get_by_role('button',name='Remove Needs Adjusting').click();p.locator('#save').click();assert not p.evaluate('batch2.meal().needsTweaking||false')
 # Shared one-time editor keeps the toolbar accessible under a keyboard-sized viewport.
 p.evaluate('batch2.once()');p.locator('#name').fill('One time reminders');p.locator('#scheduledOneTime').check();open_details(p,'[data-editor-section="notes"]');open_details(p,'[data-editor-subsection="notes"]');p.locator('#recipeNotes').fill('Temporary note');p.locator('#recipeNotes').focus();p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(100)
 assert p.locator('#editor .editor').evaluate('(e)=>e.scrollWidth<=e.clientWidth');box=p.locator('#save').bounding_box();assert box['y']+box['height']<=360
 p.locator('#save').click();p.evaluate('combinedTest.resize(800,0)');assert p.evaluate('remainingTest.temp().notes')=='Temporary note'
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'live indicators, subsections/preferences, notes/adjusting/legacy status, task add/edit/delete/decimal days/hours, cancel/save/reload/backup, one-time/mobile toolbar, no JS errors',flush=True);c.close()

def linked_cancel(b,name):
 c,p,errors,prefix=f.setup(b,name,320);p.evaluate('batch2.seed();batch2.open()');open_details(p,'[data-editor-section="linked"]');p.locator('#editLinkedMeals').click();d=p.get_by_role('heading',name='Linked meals').locator('..');d.get_by_role('searchbox').fill('Garlic Bread');d.locator('label:visible').filter(has_text='Garlic Bread').get_by_role('checkbox').first.check();assert indicator(p,'linked')=='1 linked';d.get_by_role('button',name='Cancel',exact=True).click();assert indicator(p,'linked')=='';p.locator('#cancel').click();assert not errors,errors
 print('PASS',name,'linked checkbox updates indicator immediately; dialog Cancel restores it',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
    linked_cancel(b,name)
  finally:b.close()
