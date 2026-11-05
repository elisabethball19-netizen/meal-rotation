"""Touch gestures, mixed moves and parent-deletion safety on real legacy-shaped records."""
import copy,json
from playwright.sync_api import sync_playwright
import meal_groups_bulk_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.bulkSafety={
 parent:()=>{meals.find(m=>m.id===1).linkedMealIds=[21];meals.find(m=>m.id===21).makeAheadTasks=[{id:'prep',description:'Prepare side',daysBefore:1}];persist();saveActiveMealPlan();renderList();slotTest.seed();promotionTest.check();const prep=scheduledMakeAheadTasks().find(x=>x.entry.meal.id===21&&x.entry.day==='Saturday');if(prep){prep.plan.makeAheadChecks={[prep.key]:true};saveActiveMealPlan()}},
 prep:()=>scheduledMakeAheadTasks().map(x=>({id:x.entry.meal.id,day:x.entry.day,complete:x.complete})),
 timer:id=>{const m=meals.find(m=>m.id===id),entry=getDisplayedWeekdayMeals().find(x=>x.meal.id===id);cookingTimer={version:1,id:'bulk-test-clock',recipeId:String(id),recipeName:m.name,stepToken:cookingItemTokens(m).steps[0].token,stepText:'Cook.',status:'paused',remaining:120000,context:entry?cookingContext(activePlanId,entry.day,entry.cat,m,entry.linkedTo):null};saveCookingTimer();syncCookingTimer()},clock:()=>cookingTimer,
 empties:()=>{weekdayCategories.Monday=['Sides'];for(const m of meals)if(m.cat==='Sides')m.rotation=false;saveWeekdayCategories();persist();renderList()},
 exactLabels:()=>{meals.find(m=>m.id===1).labels=[' Family ','family','Quick'];persist()},
 back:rotateAllBack
};'''
def linked_parent(b,name):
 c,p,errors,prefix=t.setup(b,name,360,'linked-slot');p.evaluate('bulkSafety.parent()');p.evaluate('bulkTest.makeHistory()');p.evaluate('bulkSafety.timer(21)');before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);timer=p.evaluate('bulkSafety.clock()');old=json.dumps(['original','Saturday','21','1'],separators=(',',':'));new=json.dumps(['original','Saturday','21',''],separators=(',',':'));assert old in before['sessions']['occurrences']
 p.evaluate('bulkTest.apply([1],{delete:true})');after=state(p);child=next(x for x in compose(p) if x[:3]==('original','Saturday','Sides'));assert child[3:]==(21,'')
 assert after['sessions']['occurrences'][new]['ingredients']==before['sessions']['occurrences'][old]['ingredients'] and after['sessions']['occurrences'][new]['steps']==before['sessions']['occurrences'][old]['steps'];assert after['scales']['occurrences'][new]['multiplier']==before['scales']['occurrences'][old]['multiplier'];assert old not in after['sessions']['occurrences'];assert next(x for x in p.evaluate('bulkSafety.prep()') if x['id']==21)['complete']
 now=p.evaluate('bulkSafety.clock()');assert now['id']==timer['id'] and now['remaining']==timer['remaining'] and now['context']['parentId']==''
 for id,source in f.sources(p).items():assert source['checked']==(groceries[id]['checked'] if id in groceries else False)
 p.evaluate('bulkTest.undo()');assert compose(p)==schedule and state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales']
 p.evaluate('bulkTest.apply([1],{delete:true})');p.evaluate('bulkSafety.back()');assert all(m['id']!=1 for m in state(p)['meals']) and any(m['id']==21 for m in state(p)['meals'])
 assert not errors,errors;print('PASS',name,'deleted parent leaves independent linked side, progress/scaling/reminder checks/groceries/timer intact; Undo restores occurrence and Cycle Back never resurrects deleted parent',flush=True);c.close()
def move_and_failure(b,name):
 c,p,errors,_=t.setup(b,name,320);p.evaluate('bulkTest.select([1,10])');before=copy.deepcopy(state(p));schedule=compose(p);storage=p.evaluate('bulkTest.snapshot()')
 p.get_by_role('button',name='Move selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Move 2 recipes',exact=True);assert d.get_by_role('combobox').count()==0;t.choose_bulk_value(p,d,'Meal group','Sides');t.choose_bulk_value(p,d,'Rotation status','Ideas');assert 'Scheduled selections will be replaced' in d.inner_text();d.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert p.evaluate('bulkTest.snapshot()')==storage
 p.get_by_role('button',name='Move selected recipes',exact=True).tap();d=p.get_by_role('dialog',name='Move 2 recipes',exact=True);t.choose_bulk_value(p,d,'Meal group','Sides');t.choose_bulk_value(p,d,'Rotation status','Ideas');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();after=state(p);t.stable(before,after,('cat','rotation'));assert all(m['cat']=='Sides' and not m['rotation'] for m in after['meals'] if m['id'] in [1,10]);assert all(x[3] not in [1,10] for x in compose(p));p.evaluate('bulkTest.undo()');assert compose(p)==schedule and state(p)['meals']==before['meals']
 # A failure while committing an earlier dependent key rolls back every value as well.
 for target in ['mealRotationPlansV1','mealRotationDataV1']:
  before=copy.deepcopy(state(p));saved=p.evaluate('bulkTest.snapshot()');p.evaluate('bulkSafety.timer(1)');saved=p.evaluate('bulkTest.snapshot()');p.evaluate('target=>bulkTest.fail(target)',target)
  try:p.evaluate('bulkTest.apply([1],{delete:true})');raise AssertionError('expected save failure')
  except Exception as e:assert 'simulated storage failure' in str(e),str(e)
  assert state(p)==before and p.evaluate('bulkTest.snapshot()')==saved and p.evaluate('bulkSafety.clock().id')=='bulk-test-clock';p.evaluate('restoreBulkNativeStorage()')
 assert not errors,errors;print('PASS',name,'Move dialog handles mixed groups/status together, Cancel is exact, primary/dependent-key failure preserves all data and active timer',flush=True);c.close()
def touch_and_scopes(b,name):
 c,p,errors,_=t.setup(b,name,320);client=c.new_cdp_session(p);r=t.reveal(p,1);r.scroll_into_view_if_needed();box=r.locator('.master-category-meal-name').first.bounding_box();point={'x':box['x']+10,'y':box['y']+12,'id':1}
 client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});p.wait_for_timeout(650);assert p.evaluate('bulkTest.selected()')==['1'];client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(80);assert p.evaluate('bulkTest.selected()')==['1'] and not p.locator('#recipeViewer').count()
 p.get_by_role('button',name='Select all / Deselect all',exact=True).tap();p.get_by_role('button',name='Select Weekend · In Rotation',exact=False).tap();assert set(p.evaluate('bulkTest.selected()'))=={'1','2','3','4'}
 t.reveal(p,10).locator('input[type=checkbox]').check();p.locator('[data-category="Weekend"] [aria-controls^="master-section-"]').first.tap();p.get_by_role('button',name='Select all / Deselect all',exact=True).tap();p.get_by_role('button',name='Select all in Weekend',exact=False).tap();assert {'1','2','3','4','5','6','10'}==set(p.evaluate('bulkTest.selected()'))
 p.set_viewport_size({'width':740,'height':360});p.screenshot(path='/tmp/bulk-selection-'+name+'-landscape.png');bar=p.locator('#recipeBulkToolbar').bounding_box();assert bar['y']+bar['height']<=360;p.get_by_role('button',name='Exit selection mode',exact=True).tap();assert not p.locator('.recipe-bulk-check').count()
 p.set_viewport_size({'width':320,'height':800});r=t.reveal(p,2);r.scroll_into_view_if_needed();box=r.locator('.master-category-meal-name').first.bounding_box();point={'x':box['x']+10,'y':box['y']+12,'id':1};client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});p.wait_for_timeout(80);client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**point,'y':point['y']+45}]});p.wait_for_timeout(600);client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert not p.evaluate('bulkTest.selected()') and not p.locator('#recipeViewer').count()
 assert not errors,errors;print('PASS',name,'CDP Android-style touch long press/scroll cancellation, section/group scopes preserve cross-group IDs and landscape toolbar remains accessible',flush=True);c.close()
def empty_and_labels(b,name):
 c,p,errors,_=t.setup(b,name,360);p.evaluate('bulkSafety.empties()');before=compose(p);p.evaluate('bulkTest.apply([20],{rotation:true})');assert compose(p)==before
 p.evaluate('bulkSafety.exactLabels()');p.evaluate('bulkTest.apply([1],{addLabels:["family","Spicy"]})');assert next(m for m in state(p)['meals'] if m['id']==1)['labels']==[' Family ','family','Quick','Spicy']
 original=p.evaluate('bulkTest.snapshot()')
 try:p.evaluate('bulkTest.apply([1],{addLabels:["Quick"],removeLabels:["quick"]})');raise AssertionError('Expected conflict')
 except Exception as e:assert 'added and removed' in str(e)
 assert p.evaluate('bulkTest.snapshot()')==original and not errors,errors;print('PASS',name,'bulk promotion leaves empty weekdays unchanged; labels preserve individual spelling/duplicates and conflicting edits are atomic',flush=True);c.close()
def persistence(b,name):
 for patch in [{'category':'Mains'},{'rotation':False},{'delete':True}]:
  c,p,errors,_=t.setup(b,name,360);p.evaluate('bulkSafety.timer(1)');p.evaluate('patch=>bulkTest.apply([1,2],patch)',patch);expected=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);backup=p.evaluate('bulkTest.snapshot()')
  if patch.get('delete'):assert p.evaluate('bulkSafety.clock()') is None
  p.reload();assert state(p)==expected and compose(p)==schedule and f.sources(p)==groceries
  p.evaluate('bulkTest.apply([10],{favorite:true})');p.evaluate('b=>bulkTest.restore(b)',backup);p.reload();assert state(p)==expected and compose(p)==schedule and f.sources(p)==groceries and not errors,errors;c.close()
 print('PASS',name,'group moves, demotions and deletion persist after reload and complete backup restore; deleting timer owner removes its timer',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   linked_parent(b,name);move_and_failure(b,name);touch_and_scopes(b,name);empty_and_labels(b,name);persistence(b,name)
  b.close()
