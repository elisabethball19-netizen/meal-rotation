"""Shared editor structure, section preferences and bounded mobile action toolbar."""
from playwright.sync_api import sync_playwright
import remaining_meal_features_browser as base
f=base.f
f.EXTRA+='''window.editorBatch={open:()=>openEditor(537),openNew:()=>openEditor(meals.find(m=>m.name==='Batch one new meal').id),add:()=>addRecipeToGroup('Weekend'),meal:()=>meals.find(m=>m.id===537),prefs:()=>JSON.parse(localStorage.getItem(RECIPE_EDITOR_SECTIONS_KEY)),seed:()=>{remainingTest.seed();const m=meals.find(m=>m.id===537);m.serveWith=['Rice'];m.linkedMealIds=[25];m.notes='Saved notes';m.ingredients=['3 lb pork'];m.instructions='Cook slowly.';persist()},create:()=>openCreateScheduledRecipe({planId:activePlanId,day:'Saturday',category:'Lunch'}),validate:()=>{const s=captureBackupStorage();validateBackupStorage(s);return s},all:()=>meals.filter(m=>!m._scheduledEditorDraft)};'''

def visible_essentials(p):
 for sel in ['#name','#categoryRows','#rotation','#prep','#totaltime','#marinate']:
  assert p.locator(sel).is_visible(),sel
 assert not p.locator('[data-editor-section="timing"],[data-editor-section="organization"]').count()
 assert p.locator('[data-editor-section]').evaluate_all('(es)=>es.map(e=>e.dataset.editorSection)')==['serve','linked','recipe','notes']
 assert p.locator('#editor .editor').evaluate('(e)=>e.scrollWidth<=e.clientWidth')
 for id in ['save','delete','cancel','serveWith','editLinkedMeals','prep','totaltime','marinate']:assert p.locator('#'+id).count()==1

def toggle(p,key):
 p.locator('[data-editor-section="'+key+'"]>summary').click();p.wait_for_timeout(40)

def toolbar(p):
 for sel in ['#save','#delete','#cancel']:
  box=p.locator(sel).bounding_box();assert box and box['y']>=0 and box['y']+box['height']<=p.evaluate('window.visualViewport?.height||innerHeight')+2,(sel,box)


def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport();editorBatch.seed();editorBatch.open()');p.wait_for_timeout(850);visible_essentials(p);toolbar(p)
 assert p.locator('[data-editor-section][open]').count()==0
 assert p.locator('[data-editor-summary="serve"]').inner_text()=='Rice'
 assert p.locator('[data-editor-summary="linked"]').inner_text()=='1 linked'
 assert p.locator('[data-editor-summary="recipe"]').inner_text()=='Added'
 assert p.locator('[data-editor-summary="notes"]').inner_text()=='Added'
 for key in ['serve','linked','recipe','notes']:toggle(p,key)
 toggle(p,'notes');prefs=p.evaluate('editorBatch.prefs().sections');assert prefs=={'serve':True,'linked':True,'recipe':True,'notes':False},prefs
 # Existing selection dialogs still operate; cancel leaves the meal intact.
 p.locator('#serveWith').click();d=p.get_by_role('dialog',name='Serve with');assert d.is_visible();p.get_by_role('button',name='Cancel Serve with').click()
 p.locator('#editLinkedMeals').click();d=p.get_by_role('heading',name='Linked meals').locator('..');d.get_by_role('button',name='Cancel',exact=True).click()
 # Timing remains compact and editable; group assignment controls remain outside sections.
 p.locator('#prep').fill('15');p.locator('#totaltime').fill('45');p.locator('#marinate').fill('2 h')
 p.locator('[aria-label="Add group membership"]').click();selects=p.locator('#categoryRows select');assert selects.count()==2
 selects.last.select_option('Lunch');p.locator('#categoryRows button[aria-label^="Remove"]').last.click();assert p.locator('#categoryRows select').count()==1
 # Inline keyboard resizing keeps actions within the editor rather than page-fixed.
 p.evaluate('combinedTest.resize(360,0)');p.locator('#totaltime').focus();p.wait_for_timeout(80);toolbar(p);assert p.locator('#save').evaluate('(e)=>getComputedStyle(e.parentElement).position')=='sticky';p.evaluate('combinedTest.resize(800,0)');p.wait_for_timeout(60)
 # Long recipe content scrolls inside editor; toolbar never covers the scroll area.
 p.locator('#recipeInstructions').evaluate('(e)=>{e.value="Long instructions\\n".repeat(80)}')
 p.locator('.meal-editor-fields').evaluate('(e)=>e.scrollTop=e.scrollHeight');toolbar(p)
 bounds=p.locator('.meal-editor-fields').bounding_box();bar=p.locator('#save').bounding_box();assert bounds['y']+bounds['height']<=bar['y']
 p.locator('#save').click();m=p.evaluate('editorBatch.meal()');assert m['prep']=='15' and m['total']=='45' and m['marinate']=='2 h',m
 p.evaluate('editorBatch.open()');p.wait_for_timeout(850);assert p.locator('[data-editor-section="recipe"]').get_attribute('open') is not None and p.locator('[data-editor-section="notes"]').get_attribute('open') is None
 p.locator('#name').fill('Canceled change');p.locator('#cancel').click();assert p.evaluate('editorBatch.meal().name')=='Korean Slow-Cooker Beef Bowls'
 # New inline meals start with optional sections collapsed despite remembered expansion.
 p.evaluate('editorBatch.add()');visible_essentials(p);assert p.locator('[data-editor-section][open]').count()==0
 p.locator('#name').fill('Batch one new meal');p.locator('#save').click();assert any(m['name']=='Batch one new meal' for m in p.evaluate('editorBatch.all()'))
 # Delete still uses its existing confirmation.
 p.evaluate('editorBatch.openNew()');p.locator('#delete').click();p.get_by_role('button',name='Confirm removal',exact=True).click();assert not any(m['name']=='Batch one new meal' for m in p.evaluate('editorBatch.all()'))
 # Shared modal one-time creation and keyboard-height layout.
 p.evaluate('editorBatch.create()');visible_essentials(p);assert p.locator('#scheduledOneTime').is_visible() and not p.locator('#scheduledOneTime').is_checked()
 p.locator('#name').fill('Batch one temporary meal');p.locator('#scheduledOneTime').check();p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(80);toolbar(p)
 p.locator('#save').click();p.evaluate('combinedTest.resize(800,0)');assert p.evaluate('remainingTest.temp().temporaryMeal') is True
 # Existing section preferences survive reload and validate in an ordinary backup.
 p.evaluate('editorBatch.validate()');p.reload();p.evaluate('promotionTest.my();editorBatch.open()');assert p.locator('[data-editor-section="recipe"]').get_attribute('open') is not None
 p.locator('#cancel').click();assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'shared inline/modal layout, essentials/groups/timing, sections/preferences/summaries, dialogs, create/edit/once/save/delete/cancel, bounded toolbar/keyboard viewport, reload/backup, no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
