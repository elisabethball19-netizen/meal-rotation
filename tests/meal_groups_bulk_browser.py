"""Isolated mobile selection, bulk metadata, schedule-aware moves/deletes and atomic saves."""
import copy,json
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.bulkTest={
 start:id=>beginRecipeBulk(meals.find(m=>m.id===id)),end:endRecipeBulk,selected:()=>[...recipeBulkIds],
 apply:(ids,patch)=>applyRecipeBulk(ids.map(String),patch),select:ids=>{recipeBulkMode=true;recipeBulkIds=new Set(ids.map(String));recipeBulkFocus={cat:meals.find(m=>String(m.id)===String(ids[0]))?.cat,rotation:true};updateRecipeBulkUI()},
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))},
 snapshot:()=>recipeBulkBackupAPI.capture(),restore:b=>{recipeBulkBackupAPI.restore(b);backupRestoreReloadPending=true},
 seed:()=>{for(const m of meals){m.labels=[m.id%2?'Family':'Quick'];m.custom={preserve:'custom-'+m.id}}const a=meals.find(m=>m.id===1);a.needsTweaking=true;a.needsTweakingNote='Keep my own note.  ';a.favorite=true;a.makeAheadTasks=[{id:'thaw',description:'Thaw pork',daysBefore:1}];meals.find(m=>m.id===2).needsTweakingNote='An individual legacy note';recipeLabelCatalog=['Family','Quick','Spicy'];saveRecipeLabelCatalog();persist();renderList()},
 linked:()=>{meals.find(m=>m.id===1).linkedMealIds=[20];meals.find(m=>m.id===10).linkedMealIds=[1];const plan=mealPlans.find(p=>p.id===activePlanId);weekdayCategories.Sunday.push('Sides');weekdayMealOverrides['Sunday::Sides']='20';plan.cycleRetainedSlots['Sunday::Sides']='20';plan.cycleSlotChoices['Sunday::Sides']={mealId:'20',parentId:'',substitution:true};saveWeekdayMealOverrides();persist();renderList();slotTest.seed();promotionTest.check()},
 shared:()=>{meals.find(m=>m.id===1).linkGroup='shared';meals.find(m=>m.id===5).linkGroup='shared';meals.find(m=>m.id===5).cat='Mains';persist();renderList()},
 history:()=>localStorage.getItem(ROTATION_BACK_KEY),makeHistory:()=>localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify({...JSON.parse(captureState()),rotationOccurrences:slotTest.rows().map(r=>({planId:r.planId,day:r.day,cat:r.cat,mealId:String(r.id),parentId:r.parent}))})),
 excluded:()=>{masterGroceryExcludedMealKeys.add('lunch::4');saveMasterGroceryMealExclusions()},
 labels:()=>allRecipeLabels(),layout:()=>({y:scrollY,width:document.documentElement.scrollWidth}),
 long:()=>{for(let n=50;n<150;n++)meals.push({id:n,name:'Long mobile recipe '+n,cat:'Weekend',rotation:n%2===0,ingredients:['1 cup rice'],instructions:'Cook 15 minutes.'});persist();renderList()},
 fail:(target='mealRotationDataV1')=>{const original=Storage.prototype.setItem;let thrown=false;Storage.prototype.setItem=function(key,value){if(key.endsWith(target)&&!thrown){thrown=true;throw Error('simulated storage failure')}return original.call(this,key,value)};window.restoreBulkNativeStorage=()=>{Storage.prototype.setItem=original}}
};'''
def setup(b,name,width=360,mode='multiple'):
 c,p,e,prefix=f.setup(b,name,width,mode);p.evaluate('bulkTest.seed()');p.evaluate('promotionTest.groups()');return c,p,e,prefix
def stable(before,after,allowed=()):
 assert {m['id'] for m in before['meals']}=={m['id'] for m in after['meals']}
 for old in before['meals']:
  new=next(m for m in after['meals'] if m['id']==old['id']);assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed},(old,new)
def row(p,id):return p.locator('.master-category-meal[data-meal-id="'+str(id)+'"]')
def reveal(p,id):
 r=row(p,id);section=r.locator('..');toggle=section.locator('xpath=preceding-sibling::button[1]')
 if section.is_hidden():toggle.tap()
 return r

def interaction(b,name,w):
 c,p,errors,prefix=setup(b,name,w);p.evaluate('bulkTest.long()');before=copy.deepcopy(state(p));schedule=compose(p)
 r=reveal(p,70);r.scroll_into_view_if_needed();old_y=p.evaluate('scrollY');name_button=r.locator('.master-category-meal-name').first;box=name_button.bounding_box();p.mouse.move(box['x']+15,box['y']+12);p.mouse.down();p.wait_for_timeout(650);assert p.evaluate('bulkTest.selected()')==['70'];p.mouse.up();p.wait_for_timeout(80)
 assert p.evaluate('bulkTest.selected()')==['70'] and not p.locator('#recipeViewer').count() and not p.get_by_role('dialog').count()
 assert p.locator('.recipe-bulk-check').count()==p.locator('.master-category-meal').count();assert abs(p.evaluate('scrollY')-old_y)<3
 r=reveal(p,72);r.locator('.master-category-meal-name').first.tap();assert set(p.evaluate('bulkTest.selected()'))=={'70','72'};r.locator('.master-category-meal-name').first.tap();assert p.evaluate('bulkTest.selected()')==['70']
 r.locator('input[type=checkbox]').check();assert set(p.evaluate('bulkTest.selected()'))=={'70','72'}
 # Parent and section collapse do not erase IDs, and new groups expand alongside existing ones.
 p.locator('[data-category="Weekend"] .master-category-title').tap();assert set(p.evaluate('bulkTest.selected()'))=={'70','72'}
 p.locator('[data-category="Mains"] .master-category-title').tap();p.locator('[data-category="Mains"] .master-category-title').tap();r=reveal(p,10);r.locator('input[type=checkbox]').check();assert '10' in p.evaluate('bulkTest.selected()')
 p.get_by_role('button',name='Select all / Deselect all',exact=True).tap();d=p.get_by_role('dialog',name='Select recipes',exact=True);d.get_by_role('button',name='Select expanded sections',exact=False).tap();assert {'70','72','10'}.issubset(p.evaluate('bulkTest.selected()'))
 p.get_by_role('button',name='Select all / Deselect all',exact=True).tap();p.get_by_role('button',name='Select all recipes across all groups',exact=False).tap();assert len(p.evaluate('bulkTest.selected()'))==len(state(p)['meals'])
 p.get_by_role('button',name='Select all / Deselect all',exact=True).tap();p.get_by_role('button',name='Deselect all',exact=True).tap();assert not p.evaluate('bulkTest.selected()');assert p.get_by_role('button',name='Edit selected recipes',exact=True).is_disabled()
 toolbar=p.locator('#recipeBulkToolbar');assert toolbar.is_visible();box=toolbar.bounding_box();assert box['y']+box['height']<=800
 for nav in p.locator('.unified-nav-fab').all():n=nav.bounding_box();assert n['y']+n['height']<=box['y']
 p.get_by_role('button',name='Exit selection mode',exact=True).tap();assert not p.locator('.recipe-bulk-check').count() and not toolbar.count();assert state(p)['meals']==before['meals'] and compose(p)==schedule
 r=reveal(p,10);r.locator('.master-category-meal-name').first.tap();assert p.get_by_role('dialog',name='Meal options',exact=True).is_visible()
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,w,'long press/no recipe action, checkbox and row taps, scroll/expansion/cross-group/scoped selections, toolbar/nav geometry, exit and normal tap, no recipe/schedule edits',flush=True);c.close()

def choose_bulk_value(p,d,label,value):
 d.get_by_role('button',name=label,exact=True).tap();picker=p.get_by_role('dialog',name=label,exact=True);picker.get_by_role('radio',name=value,exact=True).check();picker.get_by_role('button',name='Confirm '+label.lower(),exact=True).tap()

def edit(b,name,w):
 c,p,errors,prefix=setup(b,name,w);p.evaluate('bulkTest.select([1,2,5])');before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 p.get_by_role('button',name='Edit selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Edit 3 recipes',exact=True);assert d.get_by_role('button',name='Apply to selected recipes',exact=True).is_disabled()
 d.get_by_role('combobox',name='Family Favorites',exact=True).select_option('true');d.get_by_role('combobox',name='Needs Adjusting',exact=True).select_option('true');d.get_by_text('Add labels',exact=True).tap();d.get_by_role('checkbox',name='Spicy',exact=True).check();d.get_by_role('textbox',name='New label (optional)',exact=True).fill('New Label');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap()
 after=state(p);stable(before,after,('favorite','needsTweaking','labels'))
 for m in after['meals']:
  old=next(x for x in before['meals'] if x['id']==m['id'])
  if m['id'] in [1,2,5]:assert m['favorite'] and m['needsTweaking'] and {'Spicy','New Label',*old['labels']}.issubset(m['labels'])
  else:assert m==old
 assert compose(p)==schedule and f.sources(p)==groceries and after['sessions']==before['sessions'] and after['scales']==before['scales']
 # Successful edits exit selection; start a new selection before testing Cancel.
 assert not p.locator('#recipeBulkToolbar,.recipe-bulk-check').count();p.evaluate('bulkTest.select([1,2,5])')
 # Cancel a mixed edit; removal requires one explicit note-removal confirmation.
 p.get_by_role('button',name='Edit selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Edit 3 recipes',exact=True);choose_bulk_value(p,d,'Meal group','Mains');d.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert state(p)==after
 p.get_by_role('button',name='Edit selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Edit 3 recipes',exact=True);d.get_by_role('combobox',name='Needs Adjusting',exact=True).select_option('false');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();confirm=p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True);confirm.get_by_role('button',name='Cancel removal',exact=True).tap();assert state(p)==after
 d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True).get_by_role('button',name='Confirm removal',exact=True).tap();assert all(not m.get('needsTweaking') and 'needsTweakingNote' not in m for m in state(p)['meals'] if m['id'] in [1,2,5])
 p.evaluate('bulkTest.apply([1,2],{favorite:false,removeLabels:["Spicy"]})');assert all('Spicy' not in m['labels'] and not m.get('favorite') for m in state(p)['meals'] if m['id'] in [1,2]);assert compose(p)==schedule
 backup=p.evaluate('bulkTest.snapshot()');expected=copy.deepcopy(state(p));p.reload();assert state(p)==expected;p.evaluate('bulkTest.apply([1],{favorite:true})');p.evaluate('b=>bulkTest.restore(b)',backup);p.reload();assert state(p)==expected and not errors,errors
 print('PASS',name,w,'one bulk dialog, explicit-only mixed changes, additive/removal labels, favorites, preserved individual notes, confirmed status/note removal, Cancel/reload/backup and unchanged progress/groceries/schedule',flush=True);c.close()

def data_operations(b,name):
 for operation in ['group','promote','demote','delete','linked-delete','shared-delete','failure','collision']:
  mode='linked-slot' if operation=='linked-delete' else 'multiple';c,p,errors,prefix=setup(b,name,360,mode)
  if operation in ['collision','shared-delete']:p.evaluate('bulkTest.shared()')
  if operation=='linked-delete':p.evaluate('bulkTest.linked()')
  if operation in ['delete','linked-delete','shared-delete']:p.evaluate('bulkTest.makeHistory()');p.evaluate('bulkTest.excluded()')
  before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);storage=p.evaluate('bulkTest.snapshot()')
  if operation=='group':
   p.evaluate('bulkTest.apply([1,2],{category:"Mains"})');stable(before,state(p),('cat',));assert compose(p)==schedule and f.sources(p)==groceries and state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales']
  elif operation=='promote':
   p.evaluate('bulkTest.apply([5,6],{rotation:true})');stable(before,state(p),('rotation','rotationPromotionPriority'));assert [m['id'] for m in state(p)['meals'] if m['cat']=='Weekend' and m['rotation']][:2]==[5,6];assert compose(p)==schedule and f.sources(p)==groceries
  elif operation=='demote':
   p.evaluate('bulkTest.apply([1,2],{rotation:false})');after=state(p);stable(before,after,('rotation','rotationPromotionPriority'));assert not any(x[3] in [1,2] for x in compose(p));assert all(m['rotation'] is False for m in after['meals'] if m['id'] in [1,2]);assert all(m.get('lastCooked')==next(x for x in before['meals'] if x['id']==m['id']).get('lastCooked') for m in after['meals'])
  elif operation in ['delete','linked-delete','shared-delete']:
   deleted=[1] if operation=='shared-delete' else [1,5];p.evaluate('ids=>bulkTest.select(ids)',deleted);p.get_by_role('button',name='Delete selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Delete '+str(len(deleted))+' recipe'+('' if len(deleted)==1 else 's')+' from all groups?',exact=True);assert d.locator('button').count()==2;d.get_by_role('button',name='Cancel removal',exact=True).tap();assert p.evaluate('bulkTest.snapshot()')==storage
   p.get_by_role('button',name='Delete selected recipes',exact=True).tap();p.get_by_role('dialog',name='Delete '+str(len(deleted))+' recipe'+('' if len(deleted)==1 else 's')+' from all groups?',exact=True).get_by_role('button',name='Confirm removal',exact=True).tap();deleted=[1,5] if operation=='shared-delete' else deleted;after=state(p);assert {m['id'] for m in after['meals']}=={m['id'] for m in before['meals']}-set(deleted);assert not any(x[3] in deleted for x in compose(p));assert all(not (set(map(str,deleted))&{str(x) for x in m.get('linkedMealIds',[])}) for m in after['meals']);assert all(m['id'] in {x['id'] for x in after['meals']} for m in p.evaluate('JSON.parse(bulkTest.history()).meals'))
  elif operation in ['failure','collision']:
   if operation=='failure':p.evaluate('bulkTest.fail()')
   try:p.evaluate('bulkTest.apply([1,5],'+('{category:"Mains"}' if operation=='collision' else '{favorite:true,category:"Mains"}')+')');raise AssertionError('Expected operation rejection')
   except Exception as error:assert ('same group' in str(error) or 'simulated storage failure' in str(error)),str(error)
   assert state(p)==before and p.evaluate('bulkTest.snapshot()')==storage
   if operation=='failure':p.evaluate('restoreBulkNativeStorage()')
  if operation not in ['failure','collision']:
   for id,source in f.sources(p).items():assert source['checked']==(groceries[id]['checked'] if id in groceries else False),(operation,id,source)
   p.evaluate('bulkTest.undo()');assert compose(p)==schedule and state(p)['meals']==before['meals'] and state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales'] and f.sources(p)==groceries,(operation,state(p))
  assert not errors,errors
  if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
  print('PASS',name,operation,'IDs/metadata/schedules/linked references/groceries/history/Undo/atomic failure verified',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:interaction(b,name,width);edit(b,name,width)
   data_operations(b,name)
  b.close()
