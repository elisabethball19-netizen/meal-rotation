"""Android editor widths, keyboard geometry, task layout and independent adjustment notes."""
from playwright.sync_api import sync_playwright
import editor_batch3_browser as base
f=base.f
f.EXTRA+='''window.batch4={
 seed:(marked=true,note='Less salt')=>{batch3.seed();const m=meals.find(m=>m.id===537);m.needsTweaking=marked;m.needsTweakingNote=note;meals.push({id:900,cat:'Bread',name:'',rotation:false,ingredients:[]},{id:901,cat:'Bread',name:'   ',rotation:false,ingredients:[]},{id:902,cat:'Bread',name:'A very long linked meal name with enough words to wrap naturally on a narrow screen',rotation:false,ingredients:[]});persist()},
 empty:()=>{batch4.seed(false,'');const m=meals.find(m=>m.id===537);m.notes='';m.makeAheadTasks=[];persist()},
 rows:()=>document.getElementById('recipeMakeAhead').readDraft(),
 outside:()=>({meals:meals.filter(m=>m.id!==537),plans:mealPlans}),prefs:()=>captureBackupStorage().mealRotationEditorSectionsV1
};'''

def expand(p,s):base.expand(p,s)
def fit(p):
 p.wait_for_timeout(80)
 r=p.locator('#editor .meal-editor-fields');assert r.evaluate('(e)=>e.scrollWidth<=e.clientWidth'),r.evaluate('(e)=>[e.scrollWidth,e.clientWidth]')
 bad=r.evaluate('''e=>{const edge=e.getBoundingClientRect();return [...e.querySelectorAll('summary,input:not([type=hidden]):not([type=file]),textarea,select,.make-ahead-lead')].filter(x=>x.getClientRects().length).filter(x=>{const r=x.getBoundingClientRect();return r.left<edge.left-1||r.right>edge.right+1}).map(x=>({id:x.id,tag:x.tagName,cls:x.className}))}''')
 assert not bad,bad

def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width);p.evaluate('combinedTest.viewport();batch4.seed(true,"Less salt");batch3.open()');p.wait_for_timeout(850)
 assert not p.locator('#editor details[open]').count()
 for key in ['serve','linked','recipe','notes']:expand(p,'[data-editor-section="'+key+'"]')
 for sel in ['#editorIngredientsSection','#editorInstructionsSection','#recipeIngredientLinks','#editorNeedsTweaking','#recipeMakeAhead','#editorNotesSection']:expand(p,sel)
 fit(p)
 headers=p.locator('#editorIngredientsSection>summary,#editorInstructionsSection>summary,#recipeIngredientLinks>summary');assert headers.all_inner_texts()==['Ingredients','Steps','Link Steps']
 rects=headers.evaluate_all('(es)=>es.map(e=>({x:e.getBoundingClientRect().left,right:e.getBoundingClientRect().right,font:getComputedStyle(e).fontSize,weight:getComputedStyle(e).fontWeight}))');assert all(x==rects[0] for x in rects)
 assert p.locator('[data-editor-section="recipe"]>summary').evaluate('(e)=>getComputedStyle(e).backgroundColor')!='rgba(0, 0, 0, 0)'
 assert p.locator('#editorInstructionsSection>summary').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgba(0, 0, 0, 0)'
 assert p.get_by_role('checkbox',name='Add to rotation',exact=True).is_checked()
 # Linked search keeps native clear behavior, uses standard SVG chevrons and excludes blank records.
 linked=p.locator('[data-editor-section="linked"]');search=linked.get_by_role('searchbox');assert search.evaluate('(e)=>getComputedStyle(e).borderRadius')=='8px'
 assert linked.locator('.meal-editor-group-heading svg').count()>0
 search.fill('screen narrow');assert linked.locator('label:visible').filter(has_text='A very long linked meal').count()==1;fit(p)
 search.fill('');assert not linked.locator('label:visible').evaluate_all('(es)=>es.some(e=>!e.textContent.trim())')
 heading=linked.locator('.meal-editor-group-heading').filter(has_text='Bread');
 if heading.get_attribute('aria-expanded')=='true':heading.click()
 heading.click();assert heading.get_attribute('aria-expanded')=='true';assert heading.locator('.expanded svg').count()==1
 heading.click();assert heading.get_attribute('aria-expanded')=='false'
 # Focus/hardware keyboard or browser chrome shrink alone must not hide actions.
 search.focus();p.wait_for_timeout(50);assert p.locator('#save').is_visible();p.evaluate('combinedTest.resize(740,0)');p.wait_for_timeout(80);assert p.locator('#save').is_visible()
 # Software keyboard shrink hides only editor actions; field/node/focus survive and search stays usable.
 handle=search.element_handle();p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(90);assert not p.locator('#save').is_visible() and p.evaluate('document.activeElement.getAttribute("aria-label")')=='Search linked meals';assert handle.evaluate('(e)=>e.isConnected')
 search.fill('roast mississippi');assert linked.locator('label:visible').filter(has_text='Mississippi-Style Pot Roast').count()==1;fit(p)
 p.evaluate('combinedTest.resize(800,0)');p.wait_for_timeout(90);assert p.locator('#save').is_visible()
 # Task row layout and local insertion/removal preserve identifiers and values.
 ahead=p.locator('#recipeMakeAhead');assert not ahead.locator(':scope>summary button').count();assert not ahead.get_by_text('0 days means same day.',exact=True).count()
 before=p.evaluate('batch4.rows()');rows=ahead.locator('.make-ahead-task-editor');first=rows.nth(0)
 text=first.get_by_role('textbox');trash=first.get_by_role('button',name='Remove preparation task');number=first.get_by_role('spinbutton');plus=first.get_by_role('button',name='Add preparation task')
 assert abs(text.bounding_box()['y']-trash.bounding_box()['y'])<5 and trash.bounding_box()['x']>text.bounding_box()['x']
 assert plus.bounding_box()['y']>text.bounding_box()['y'] and plus.bounding_box()['x']>number.bounding_box()['x']
 selected=first.get_by_role('button',name='Days',exact=True);neutral=first.get_by_role('button',name='Hours',exact=True);assert selected.get_attribute('aria-pressed')=='true';assert selected.evaluate('(e)=>getComputedStyle(e).backgroundColor')!=neutral.evaluate('(e)=>getComputedStyle(e).backgroundColor')
 plus.click();rows.nth(1).get_by_role('textbox').fill('Inserted task');rows.nth(1).get_by_role('spinbutton').fill('2.25');rows.nth(1).get_by_role('button',name='Hours',exact=True).click();draft=p.evaluate('batch4.rows()');assert [x['id'] for x in [draft[0],draft[2]]]==[x['id'] for x in before] and draft[1]['hoursBefore']==2.25
 rows.nth(1).get_by_role('button',name='Remove preparation task').click();assert p.evaluate('batch4.rows()')==before;fit(p)
 # Independent note/status: uncheck retains text and does not request removal confirmation.
 adjust=p.get_by_role('checkbox',name='Mark as needs adjusting');note=p.get_by_role('textbox',name='Needs Adjusting note');assert adjust.is_checked() and note.input_value()=='Less salt';assert not p.locator('#editorNeedsTweaking .recipe-tweaking-trash').count()
 adjust.uncheck();assert note.input_value()=='Less salt';note.fill('Unmarked saved note');assert p.evaluate('batch3.dirty()') is True
 p.locator('#save').click();assert not p.get_by_role('dialog',name='Remove Needs Adjusting?').count();m=p.evaluate('batch3.meal()');assert not m.get('needsTweaking') and m['needsTweakingNote']=='Unmarked saved note'
 p.evaluate('batch3.open()');assert not p.locator('#editor details[open]').count();expand(p,'[data-editor-section="notes"]');expand(p,'#editorNeedsTweaking');note=p.get_by_role('textbox',name='Needs Adjusting note');assert note.input_value()=='Unmarked saved note'
 adjust=p.get_by_role('checkbox',name='Mark as needs adjusting');adjust.check();note.fill('');assert adjust.is_checked();p.locator('#save').click();assert p.evaluate('batch3.meal().needsTweaking') is True and p.evaluate('batch3.meal().needsTweakingNote')==''
 p.evaluate('batch3.open()');expand(p,'[data-editor-section="notes"]');expand(p,'#editorNeedsTweaking');p.get_by_role('checkbox',name='Mark as needs adjusting').uncheck();p.get_by_role('textbox',name='Needs Adjusting note').fill('Discard this');p.locator('#cancel').click();assert p.evaluate('batch3.meal().needsTweaking') is True and p.evaluate('batch3.meal().needsTweakingNote')==''
 saved=p.evaluate('batch3.storage()');p.evaluate('batch3.valid()');p.evaluate('batch3.restore',saved);p.reload();p.evaluate('combinedTest.viewport();promotionTest.my();batch3.open()');expand(p,'[data-editor-section="notes"]');expand(p,'#editorNeedsTweaking');assert p.get_by_role('checkbox',name='Mark as needs adjusting').is_checked();p.locator('#cancel').click()
 p.evaluate('batch4.seed(true,"  Keep this spacing  ");batch3.open()');expand(p,'[data-editor-section="notes"]');expand(p,'#editorNeedsTweaking');p.get_by_role('checkbox',name='Mark as needs adjusting').uncheck();p.locator('#save').click();assert p.evaluate('batch3.meal().needsTweakingNote')=='  Keep this spacing  '
 p.evaluate('batch4.empty();batch3.open()');expand(p,'[data-editor-section="notes"]');expand(p,'#editorNeedsTweaking');indicator=p.locator('[data-editor-summary="notes"]');assert indicator.inner_text()=='';mark=p.get_by_role('checkbox',name='Mark as needs adjusting');mark.check();assert indicator.inner_text()=='Added';mark.uncheck();assert indicator.inner_text()=='';p.get_by_role('textbox',name='Needs Adjusting note').fill('Note only');assert indicator.inner_text()=='Added' and not mark.is_checked();p.get_by_role('textbox',name='Needs Adjusting note').fill('');assert indicator.inner_text()=='';p.locator('#cancel').click()
 # New one-time modal also hides/restores its toolbar on software-keyboard geometry.
 p.evaluate('batch3.once()');p.locator('#name').fill('Batch four once');p.locator('#scheduledOneTime').check();p.locator('#name').focus();p.evaluate('combinedTest.resize(360,0)');p.wait_for_timeout(90);assert not p.locator('#save').is_visible();fit(p);p.evaluate('combinedTest.resize(800,0)');p.wait_for_timeout(80);assert p.locator('#save').is_visible();p.locator('#save').click();assert p.evaluate('remainingTest.temp().name')=='Batch four once'
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'flat bounds/hierarchy, Steps, linked search/chevrons/no blanks, keyboard detection, task row ordering/exact timing, independent adjustment/legacy notes, save/cancel/reload/backup, one-time; no JS errors',flush=True);c.close()

if __name__=='__main__':
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  try:
   for name in ['index.html','meal-rotation-test.html']:
    for width in [320,390]:run(b,name,width)
  finally:b.close()
