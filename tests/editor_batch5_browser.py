"""One card-backed draft, linked picker reset and Recipe adjustment-note choices."""
from playwright.sync_api import sync_playwright
import editor_batch4_browser as base
f=base.f
f.EXTRA+='''window.batch5={
 add:()=>addRecipeToGroup('Weekend'),
 seed:()=>{batch4.seed(true,'Less salt');const m=meals.find(m=>m.id===537);m.prep='10';m.cook='40';m.total='50';m.marinate='2 h';persist();promotionTest.groups()},
 meal:()=>meals.find(m=>m.id===537),open:()=>openEditor(537),
 warning:()=>document.querySelectorAll('#list .needs-tweaking-icon').length,
 other:()=>JSON.stringify(meals.filter(m=>m.id!==537)),
 emptyAdjust:()=>{const m=meals.find(m=>m.id===537);m.needsTweaking=true;m.needsTweakingNote='';m.ingredients=[];m.instructions='';m.url='';m.notes='';m.makeAheadTasks=[];persist()},
 prefs:()=>captureBackupStorage(),restore:s=>restoreBackupStorage(s)
};'''

def expand(p,selector):base.expand(p,selector)
def field(p,label,id,value):
 p.get_by_role('button',name='Edit '+label,exact=True).click();assert p.locator('#'+id).is_visible();p.locator('#'+id).fill(value)
 if id=='prep' and value=='15 min':
  p.locator('#timeKeyboardMode').click();assert p.locator('#prep').is_visible() and p.locator('#prep').input_value()==value;p.locator('#timeKeyboardMode').click()
 p.locator('#'+id).press('Enter')

def linked(p):
 d=p.locator('#mealCardLinkedPicker');expand(p,'#mealCardLinkedPicker');return d

def fit(p):
 p.wait_for_timeout(60);assert p.locator('.meal-editor-fields').evaluate('(e)=>e.scrollWidth<=e.clientWidth')

def adjust(p):
 expand(p,'[data-editor-section="recipe"]');return p.get_by_role('checkbox',name='Needs Adjusting',exact=True)

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport();batch5.seed()')
 # Normal cards keep their action popup; no editing input exists before Edit.
 normal=p.locator('#list .master-category-meal[data-meal-id="537"]');normal.locator('.master-category-meal-name').first.click();assert p.get_by_role('dialog',name='Meal options').is_visible();assert not p.locator('#editor #name').count();p.get_by_role('button',name='Close meal options',exact=True).click()
 p.evaluate('batch5.open()');p.wait_for_timeout(850);original=p.evaluate('batch5.meal()');other=p.evaluate('batch5.other()')
 card=p.locator('#editor .meal-card-edit-mode');assert card.count()==1 and card.get_attribute('data-meal-id')=='537'
 assert p.locator('[data-editor-section]').evaluate_all('(es)=>es.map(e=>e.dataset.editorSection)')==['serve','recipe','notes']
 assert not p.locator('#editor details[open]').count();assert not p.locator('#name').is_visible()
 for id in ['name','prep','totaltime','marinate']:assert p.locator('#'+id).count()==1 and card.locator('#'+id).count()==1
 p.get_by_role('button',name='Edit meal name',exact=True).click();assert p.locator('#name').evaluate('(e)=>e.selectionStart===0&&e.selectionEnd===e.value.length');p.locator('#name').fill('Draft meal title');p.locator('#name').press('Enter')
 total_before=p.locator('#totaltime').input_value();field(p,'prep time','prep','15 min');assert p.locator('#totaltime').input_value()==total_before and p.locator('#marinate').input_value()=='2 h'
 field(p,'total time','totaltime','65 min');field(p,'marinate time','marinate','');assert p.evaluate('batch3.dirty()') is True and p.evaluate('batch5.meal()')==original
 d=linked(p);groups=d.locator('.meal-editor-group-heading');assert all(v=='false' for v in groups.evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-expanded"))'))
 search=d.get_by_role('searchbox');search.fill('roast mississippi');d.locator('label:visible').filter(has_text='Mississippi-Style Pot Roast').get_by_role('checkbox').check();assert p.evaluate('batch5.meal().linkedMealIds')==[25]
 d.locator(':scope>summary').click();p.wait_for_timeout(40);assert all(v=='false' for v in groups.evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-expanded"))'));linked(p);assert all(v=='false' for v in groups.evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-expanded"))'))
 search.fill('');assert d.locator('label:visible').filter(has_text='Mississippi-Style Pot Roast').count()==1
 # Neutral hierarchy and left/right chevron placement.
 expand(p,'[data-editor-section="recipe"]');expand(p,'#editorIngredientsSection');fit(p)
 main=p.locator('[data-editor-section="recipe"]>summary');assert main.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(234, 234, 234)'
 assert p.locator('#editorIngredientsSection>summary').evaluate('(e)=>e.firstElementChild.classList.contains("settings-chevron")') or p.locator('#editorIngredientsSection>summary .settings-chevron').evaluate('(e)=>getComputedStyle(e).order')=='-1'
 expand(p,'[data-editor-section="notes"]');expand(p,'#recipeMakeAhead');chosen=p.locator('#recipeMakeAhead [data-lead-unit][aria-pressed="true"]').first;assert chosen.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)' and chosen.evaluate('(e)=>getComputedStyle(e).boxShadow')!='none'
 assert all(v=='-1' for v in p.locator('#editor .meal-editor-subsection>summary>.settings-chevron').evaluate_all('(es)=>es.map(e=>getComputedStyle(e).order)'))
 assert p.locator('[data-editor-section="recipe"] #editNeedsTweaking').count()==1 and not p.locator('[data-editor-section="notes"] #editNeedsTweaking').count()
 # Keep/Delete/dismiss remain draft-only. Chevron does not alter checkbox.
 mark=adjust(p);assert mark.is_checked() and p.locator('#editNeedsTweakingNote').is_visible();p.get_by_role('button',name='Expand or collapse adjustment note').click();assert not p.locator('#editNeedsTweakingNote').is_visible() and mark.is_checked();p.get_by_role('button',name='Expand or collapse adjustment note').click()
 mark.click();confirm=p.get_by_role('dialog',name='Uncheck Needs Adjusting?');assert mark.is_checked();assert confirm.get_by_role('button',name='Keep note').evaluate('(e)=>e===document.activeElement');confirm.get_by_role('button',name='Close adjustment confirmation').click();assert mark.is_checked() and p.locator('#editNeedsTweakingNote').input_value()=='Less salt'
 mark.click();p.get_by_role('button',name='Keep note',exact=True).click();assert not mark.is_checked() and not p.locator('#editNeedsTweakingNote').is_visible();assert p.locator('#editNeedsTweakingNote').input_value()=='Less salt' and not p.locator('.meal-card-adjusting-warning').is_visible()
 mark.check();assert p.locator('#editNeedsTweakingNote').is_visible();mark.click();p.get_by_role('button',name='Delete note',exact=True).click();assert p.locator('#editNeedsTweakingNote').input_value()==''
 p.locator('#cancel').click();assert p.evaluate('batch5.meal()')==original and p.evaluate('batch5.other()')==other
 # Commit all card/editor changes as one existing save, then restore/reload.
 p.evaluate('batch5.open()');field(p,'meal name','name','Saved card meal');field(p,'prep time','prep','12 min');field(p,'total time','totaltime','60');field(p,'marinate time','marinate','3 h')
 d=linked(p);d.get_by_role('searchbox').fill('roast mississippi');d.locator('label:visible').filter(has_text='Mississippi-Style Pot Roast').get_by_role('checkbox').check();mark=adjust(p);mark.click();p.get_by_role('button',name='Keep note',exact=True).click();p.locator('#save').click();m=p.evaluate('batch5.meal()');assert m['name']=='Saved card meal' and m['prep']=='12' and m['total']=='60' and m['marinate']=='3 h' and set(m['linkedMealIds'])=={25,535} and not m.get('needsTweaking') and m['needsTweakingNote']=='Less salt',m
 assert not p.locator('#list .master-category-meal[data-meal-id="537"] .needs-tweaking-icon').count();assert p.evaluate('batch5.other()')==other
 saved=p.evaluate('batch5.prefs()');p.evaluate('batch3.valid()');p.evaluate('batch5.restore',saved);p.reload();p.evaluate('combinedTest.viewport();promotionTest.my();batch5.open()');assert p.locator('#name').input_value()=='Saved card meal' and '12' in p.locator('#prep').input_value()
 assert p.locator('[data-editor-summary="recipe"]').inner_text()=='Added'
 mark=adjust(p);assert not mark.is_checked();mark.check();assert p.locator('#editNeedsTweakingNote').input_value()=='Less salt';p.locator('#cancel').click()
 p.evaluate('batch5.open()');field(p,'prep time','prep','');field(p,'marinate time','marinate','');p.locator('#save').click();assert p.evaluate('batch5.meal().prep')=='' and p.evaluate('batch5.meal().marinate')=='' and p.evaluate('batch5.meal().total')=='60'
 # Empty adjustment state moves indicators only into Recipe, and needs no confirmation.
 p.evaluate('batch5.emptyAdjust();batch5.open()');mark=adjust(p);mark.click();assert not p.get_by_role('dialog',name='Uncheck Needs Adjusting?').count();assert p.locator('[data-editor-summary="recipe"]').inner_text()=='' and p.locator('[data-editor-summary="notes"]').inner_text()==''
 mark.check();p.locator('#editNeedsTweakingNote').fill('Recipe-only note');assert p.locator('[data-editor-summary="recipe"]').inner_text()=='Added' and p.locator('[data-editor-summary="notes"]').inner_text()=='';p.locator('#cancel').click()
 # Card text input participates in existing keyboard handling and validation.
 p.evaluate('batch5.open()');p.get_by_role('button',name='Edit prep time').click();p.locator('#prep').fill('invalid');p.locator('#prep').press('Enter');p.locator('#save').click();p.get_by_role('alertdialog').get_by_role('button',name='OK').click();assert p.locator('#prep').is_visible();p.locator('#prep').fill('');p.locator('#prep').press('Enter')
 p.get_by_role('button',name='Edit meal name').click();p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(90);assert not p.locator('#save').is_visible();fit(p);p.evaluate('combinedTest.resize(800,0)');p.wait_for_timeout(80);p.locator('#cancel').click()
 p.evaluate('batch5.open()');field(p,'meal name','name','Discard via outside warning');p.locator('#list .master-category-meal[data-meal-id="22"] .master-category-meal-name').first.click();assert p.get_by_text('Save meal changes before closing?',exact=True).is_visible();p.get_by_role('button',name='No',exact=True).click();p.get_by_role('button',name='Close meal options',exact=True).click();assert p.evaluate('batch5.meal().name')=='Saved card meal'
 p.evaluate('batch5.add()');p.wait_for_timeout(100);assert p.locator('#name').is_visible();p.locator('#name').fill('Created with card');p.locator('#name').press('Enter');p.locator('#save').click();assert any(m['name']=='Created with card' for m in p.evaluate('remainingTest.recipes()'))
 # One-time modal shares the same controls and single draft.
 p.evaluate('batch3.once()');assert p.locator('#name').is_visible();p.locator('#name').fill('Card temporary');p.locator('#name').press('Enter');p.locator('#scheduledOneTime').check();field(p,'prep time','prep','5 min');fit(p);p.locator('#save').click();assert p.evaluate('remainingTest.temp().name')=='Card temporary' and p.evaluate('remainingTest.temp().prep')=='5'
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'one card draft, normal actions, independent times/name/links, picker collapse reset, no duplicate fields, adjusting confirmations/indicators/warnings, save/cancel/reload/backup, validation/keyboard/one-time; no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
