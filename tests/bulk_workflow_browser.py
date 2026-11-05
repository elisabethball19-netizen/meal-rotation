"""App-styled bulk selectors, inline group creation and success-only selection exit."""
import copy
from playwright.sync_api import sync_playwright
import meal_groups_bulk_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.bulkFlow={groups:()=>cats,selected:()=>[...recipeBulkIds],mode:()=>recipeBulkMode,long:()=>{for(let n=0;n<120;n++)cats.push('Long group '+n);persist();renderList()}};'''
def select_value(p,d,label,value,confirm=True):
 d.get_by_role('button',name=label,exact=True).tap();picker=p.get_by_role('dialog',name=label,exact=True);picker.get_by_role('radio',name=value,exact=True).check();picker.get_by_role('button',name=('Confirm ' if confirm else 'Cancel ')+label.lower(),exact=True).tap()
def move(p):p.get_by_role('button',name='Move selected recipes',exact=True).tap();return p.get_by_role('dialog',name='Move 2 recipes',exact=True)
def selector(p,d):d.get_by_role('button',name='Meal group',exact=True).tap();return p.get_by_role('dialog',name='Meal group',exact=True)
def create_prompt(p,picker):picker.get_by_role('button',name='+ New Group',exact=True).tap();return p.get_by_role('dialog',name='New group',exact=True)
def run(b,name,w):
 c,p,e,_=t.setup(b,name,w);p.evaluate('bulkTest.select([5,6])');before=copy.deepcopy(state(p));schedule=compose(p);d=move(p);assert not d.locator('select').count() and 'Unchanged leaves' not in d.inner_text()
 select_value(p,d,'Rotation status','Ideas');select_value(p,d,'Rotation status','In Rotation',False);assert d.get_by_role('button',name='Rotation status',exact=True).inner_text()=='Ideas'
 select_value(p,d,'Meal group','Mains',False);assert d.get_by_role('button',name='Meal group',exact=True).inner_text()=='Unchanged';select_value(p,d,'Meal group','Mains')
 picker=selector(p,d);assert picker.get_by_role('radio',name='Mains',exact=True).is_checked();prompt=create_prompt(p,picker);prompt.get_by_role('textbox',name='New group name',exact=True).fill('  Cooking Tests  ');prompt.get_by_role('button',name='Create group',exact=True).tap();assert not prompt.count() and not picker.count() and d.is_visible();assert d.get_by_role('button',name='Meal group',exact=True).inner_text()=='Cooking Tests' and d.get_by_role('button',name='Rotation status',exact=True).inner_text()=='Ideas';assert state(p)['meals']==before['meals'] and compose(p)==schedule and p.evaluate('bulkFlow.selected()')==['5','6'];assert p.evaluate('bulkFlow.groups().includes("Cooking Tests")')
 d.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert p.evaluate('bulkFlow.mode()') and p.evaluate('bulkFlow.selected()')==['5','6'] and state(p)['meals']==before['meals']
 d=move(p);select_value(p,d,'Meal group','Cooking Tests');select_value(p,d,'Rotation status','In Rotation');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();assert not p.get_by_role('dialog').count() and not p.locator('#recipeBulkToolbar,.recipe-bulk-check').count() and not p.evaluate('bulkFlow.mode()') and not p.evaluate('bulkFlow.selected()');assert all(m['cat']=='Cooking Tests' and m['rotation'] for m in state(p)['meals'] if m['id'] in [5,6]);assert compose(p)==schedule
 expected=copy.deepcopy(state(p));p.reload();assert state(p)==expected and p.evaluate('bulkFlow.groups().filter(c=>c==="Cooking Tests").length')==1 and not e,e
 print('PASS',name,w,'white custom Move selectors, remembered values/selector Cancel, explicit new group retains selections/status without moving, Move Cancel keeps group/selection, confirm moves and exits, reload',flush=True);c.close()
def validation_failure_and_layout(b,name):
 c,p,e,_=t.setup(b,name,320);p.evaluate('bulkTest.select([5,6])');d=move(p);picker=selector(p,d);prompt=create_prompt(p,picker);before=p.evaluate('bulkTest.snapshot()');prompt.get_by_role('button',name='Create group',exact=True).tap();assert 'Enter a group name' in prompt.inner_text();prompt.get_by_role('textbox').fill('wEeKeNd');prompt.get_by_role('button',name='Create group',exact=True).tap();assert 'already exists' in prompt.inner_text() and p.evaluate('bulkTest.snapshot()')==before
 prompt.get_by_role('textbox').fill('Failed new group');p.evaluate('bulkTest.fail()');prompt.get_by_role('button',name='Create group',exact=True).tap();assert 'simulated storage failure' in prompt.inner_text() and p.evaluate('bulkTest.snapshot()')==before;p.evaluate('restoreBulkNativeStorage()');prompt.get_by_role('button',name='Cancel new group',exact=True).tap();picker.get_by_role('button',name='Cancel meal group',exact=True).tap();assert p.evaluate('bulkFlow.mode()')
 select_value(p,d,'Meal group','Mains');before=p.evaluate('bulkTest.snapshot()');p.evaluate('bulkTest.fail()');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();p.get_by_role('button',name='OK',exact=True).tap();assert p.evaluate('bulkTest.snapshot()')==before and p.evaluate('bulkFlow.selected()')==['5','6'] and p.evaluate('bulkFlow.mode()') and d.is_visible();p.evaluate('restoreBulkNativeStorage()');d.get_by_role('button',name='Cancel bulk edit',exact=True).tap()
 p.evaluate('bulkFlow.long()')
 for size in [{'width':320,'height':800},{'width':740,'height':360}]:
  p.set_viewport_size(size);d=move(p);picker=selector(p,d);list=picker.locator('.recipe-bulk-choice-list');assert list.evaluate('(e)=>e.scrollHeight>e.clientHeight');list.evaluate('(e)=>e.scrollTop=e.scrollHeight');assert picker.get_by_role('button',name='Confirm meal group',exact=True).is_visible() and picker.get_by_role('button',name='Cancel meal group',exact=True).is_visible();assert picker.locator(':scope>div').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(255, 255, 255)';assert picker.locator(':scope>div').bounding_box()['height']<=size['height']*.86;p.screenshot(path='/tmp/bulk-custom-selector-'+name+'-'+str(size['width'])+'.png');picker.get_by_role('button',name='Cancel meal group',exact=True).tap();d.get_by_role('button',name='Cancel bulk edit',exact=True).tap()
 assert not e,e;print('PASS',name,'blank/duplicate/storage-failed new groups do not change data, failed Move retains selections and dialog, 120-group selectors scroll with visible icons in portrait/landscape',flush=True);c.close()
def edit_delete_exit(b,name):
 c,p,e,_=t.setup(b,name,360);p.evaluate('bulkTest.select([5,6])');before=copy.deepcopy(state(p));p.get_by_role('button',name='Edit selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Edit 2 recipes',exact=True);d.get_by_role('combobox',name='Family Favorites',exact=True).select_option('true');d.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert state(p)==before and p.evaluate('bulkFlow.mode()') and len(p.evaluate('bulkFlow.selected()'))==2
 p.get_by_role('button',name='Edit selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Edit 2 recipes',exact=True);d.get_by_role('combobox',name='Family Favorites',exact=True).select_option('true');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();assert not p.evaluate('bulkFlow.mode()') and not p.locator('#recipeBulkToolbar,.recipe-bulk-check').count()
 p.evaluate('bulkTest.select([5,6])');p.get_by_role('button',name='Delete selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Delete 2 recipes from all groups?',exact=True);d.get_by_role('button',name='Cancel removal',exact=True).tap();assert p.evaluate('bulkFlow.mode()') and len(p.evaluate('bulkFlow.selected()'))==2
 p.get_by_role('button',name='Delete selected recipes',exact=True).tap();p.get_by_role('dialog',name='Delete 2 recipes from all groups?',exact=True).get_by_role('button',name='Confirm removal',exact=True).tap();assert not p.locator('#recipeBulkToolbar,.recipe-bulk-check').count() and not p.evaluate('bulkFlow.mode()') and all(m['id'] not in [5,6] for m in state(p)['meals']) and not e,e
 print('PASS',name,'successful Bulk Edit/Delete close and exit selection; Edit/Delete Cancel preserve recipes and selections; count confirmation deletes selected recipes only',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   validation_failure_and_layout(b,name);edit_delete_exit(b,name)
   for w in [320,360]:run(b,name,w)
  b.close()
