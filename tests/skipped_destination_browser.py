"""Persisted skipped Monday/Rice regression, driven through the rendered empty-slot UI."""
from playwright.sync_api import sync_playwright
import meal_dialog_corrections_browser as t
s=t.s
t.f.HOOK+='''window.riceFixture={
 seed:(mode='independent')=>{
  cats=cats.map(cat=>cat==='Meals'?'Rice':cat);for(const meal of meals)if(meal.cat==='Meals')meal.cat='Rice';renameGroupIdentity('Meals','Rice');
  for(const plan of mealPlans){for(const day of Object.keys(plan.weekdayCategories))plan.weekdayCategories[day]=plan.weekdayCategories[day].map(cat=>cat==='Meals'?'Rice':cat);for(const field of ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices'])plan[field]=Object.fromEntries(Object.entries(plan[field]||{}).map(([key,value])=>[key.replace('::Meals','::Rice'),value]));plan.rotationCalendar.slots=Object.fromEntries(Object.entries(plan.rotationCalendar.slots).map(([key,value])=>[key.replace('::Meals','::Rice'),value]))}
  const plan=mealPlans[0];weekdayCategories=JSON.parse(JSON.stringify(plan.weekdayCategories));weekdayMealOverrides={...plan.weekdayMealOverrides};
  if(mode==='independent'){delete weekdayCategories.Monday;for(const field of ['weekdayMealOverrides','cycleRetainedSlots','cycleSlotChoices'])delete plan[field]['Monday::Rice'];delete weekdayMealOverrides['Monday::Rice'];plan.occasionalMeals.Monday='6'}
  saveActiveMealPlan();leaveWeekEmpty('Monday',mode==='day'?null:'Rice');leaveWeekEmpty('Thursday','Rice');persist();render();
 },
 snapshot:()=>simpleTest.snapshot(),rows:()=>dialogTest.rows(),slots:()=>JSON.parse(JSON.stringify(mealPlans[0].weekSchedule.slots)),records:()=>simpleTest.records(),
 none:()=>{for(const meal of meals)if(meal.cat==='Rice'&&meal.id!==1)meal.rotation=false;persist();renderList()},
 noCandidates:()=>{for(const meal of meals)if(meal.cat==='Rice')meal.rotation=false;persist();renderList()},
 otherGroup:()=>{weekdayCategories.Monday=['Other'];weekdayMealOverrides['Monday::Other']='14';const plan=mealPlans[0];plan.cycleRetainedSlots['Monday::Other']='14';plan.cycleSlotChoices['Monday::Other']={mealId:'14',parentId:'',retain:true,substitution:true};saveActiveMealPlan();persist();renderList()},
 reference:()=>{localStorage.setItem(GROUP_ROTATION_KEY,JSON.stringify({[groupIdentity('Rice',true)]:false}));persist();renderList()},
 fail:()=>{const original=Storage.prototype.setItem;let thrown=false;Storage.prototype.setItem=function(key,value){if(key.endsWith('mealRotationPlansV1')&&!thrown){thrown=true;throw Error('injected scheduling save failure')}return original.call(this,key,value)};window.restoreRiceWrites=()=>{Storage.prototype.setItem=original}}
};'''

def setup(b,name,mode='independent'):
 c,p,e,pr=t.setup(b,name);p.evaluate('riceFixture.seed',mode);p.reload();assert not e,e
 assert p.locator('.empty-weekday-meal[data-schedule-day=Monday]').count()==1
 return c,p,e,pr

def open_picker(p):
 s.t.hold(p,p.locator('.empty-weekday-meal[data-schedule-day=Monday]'));d=p.get_by_role('dialog',name='Empty meal options',exact=True);d.get_by_role('button',name='Select Meal',exact=True).tap();return p.locator('.weekday-meal-picker')

def select(p,picker,id):
 if not picker.locator('[data-meal-id="'+str(id)+'"]').count():
  picker.get_by_role('button',name='Search recipes',exact=True).tap();picker.get_by_role('searchbox',name='Search recipes',exact=True).fill(next(x['name'] for x in p.evaluate('riceFixture.records()') if x['id']==id))
 picker.locator('[data-meal-id="'+str(id)+'"]').tap()

def rows(p):return sorted(p.evaluate('riceFixture.rows()'),key=str)
def slot(p):return p.evaluate('riceFixture.slots()')
def finish(p,picker,decision=None):
 picker.get_by_role('button',name='Save',exact=True).tap()
 if decision:
  d=p.get_by_role('dialog',name='Chicken Curry is already planned for Tuesday.',exact=True);assert d.get_by_role('button',name='Confirm meal choice').is_disabled();d.get_by_role('radio',name='Use a different meal on Tuesday' if decision=='replace' else 'Keep Chicken Curry on Tuesday too',exact=True).check();d.get_by_role('button',name='Confirm meal choice',exact=True).tap()
 p.clock.run_for(450)

def selections(b,name,mode='independent'):
 for choice,id in [('rotation',2),('ideas',4),('cross-group ideas',12),('replace',1),('keep',1),('next',None)]:
  c,p,e,pr=setup(b,name,mode);baseline=rows(p);before_slots=slot(p);before_records={m['id']:m for m in p.evaluate('riceFixture.records()')};picker=open_picker(p);assert picker.get_by_role('button',name='Use next recipe',exact=True).is_enabled()
  if choice=='next':picker.get_by_role('button',name='Use next recipe',exact=True).tap();p.clock.run_for(450)
  else:select(p,picker,id);finish(p,picker,choice if choice in ['replace','keep'] else None)
  assert not picker.count(),(name,mode,choice,p.get_by_role('alertdialog').all_text_contents())
  actual=rows(p);dest=[r for r in actual if r['planId']=='original' and r['day']=='Monday' and not r['linked']];assert len(dest)==1,(choice,dest)
  if id:assert dest[0]['id']==id,(choice,dest)
  assert p.locator('.top-recipe-wrap[data-schedule-day=Monday] .meal[data-meal-id="'+str(dest[0]['id'])+'"]').count()==1
  assert dest[0]['date']==before_slots['Monday::'+('@day' if mode=='day' else 'Rice')]['scheduledDate']
  assert 'Monday::'+('@day' if mode=='day' else 'Rice') not in slot(p)
  assert slot(p)['Thursday::Rice']==before_slots['Thursday::Rice']
  assert [r for r in actual if not(r['planId']=='original' and r['day'] in ['Monday','Tuesday'])]==[r for r in baseline if not(r['planId']=='original' and r['day'] in ['Monday','Tuesday'])]
  if choice!='replace':assert [r for r in actual if r['day']=='Tuesday']==[r for r in baseline if r['day']=='Tuesday']
  else:assert not any(r['planId']=='original' and r['day']=='Tuesday' and r['id']==1 for r in actual);assert any(r['day']=='Tuesday' and r['id']==5 for r in actual) and any(r['day']=='Tuesday' and r['id']==14 for r in actual)
  for meal in p.evaluate('riceFixture.records()'):assert (meal.get('rotation'),meal.get('lastCooked'))==(before_records[meal['id']].get('rotation'),before_records[meal['id']].get('lastCooked'))
  p.locator('#undo').tap();assert rows(p)==baseline and slot(p)==before_slots;p.locator('#redo').tap();assert rows(p)==actual;p.reload();assert rows(p)==actual and not p.locator('.empty-weekday-meal[data-schedule-day=Monday]').count();assert p.locator('.top-recipe-wrap[data-schedule-day=Monday] .meal[data-meal-id="'+str(dest[0]['id'])+'"]').count()==1;assert not e,e
  if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
  c.close()
 print('PASS',name,mode,'persisted UI Rotation/Ideas/cross-group/duplicate Replace+Keep/next, exact date/mask, other occurrences/status, Undo/Redo and reload',flush=True)

def cancellation_and_failures(b,name):
 for choice in ['outer','nested','unavailable','storage']:
  c,p,e,pr=setup(b,name)
  if choice=='unavailable':p.evaluate('riceFixture.none()');p.reload()
  before=p.evaluate('riceFixture.snapshot()');before_stored=p.evaluate('simpleTest.backup()');baseline=rows(p);before_slots=slot(p);picker=open_picker(p)
  if choice=='outer':select(p,picker,4);picker.get_by_role('button',name='Cancel',exact=True).tap()
  else:
   select(p,picker,1);picker.get_by_role('button',name='Save',exact=True).tap();d=p.get_by_role('dialog',name='Chicken Curry is already planned for Tuesday.',exact=True)
   if choice=='nested':d.get_by_role('radio',name='Use a different meal on Tuesday',exact=True).check();assert p.evaluate('riceFixture.snapshot()')==before;d.get_by_role('button',name='Cancel meal choice').tap();p.clock.run_for(450);picker.get_by_role('button',name='Cancel',exact=True).tap()
   else:
    d.get_by_role('radio',name='Use a different meal on Tuesday',exact=True).check()
    if choice=='storage':p.evaluate('riceFixture.fail()')
    d.get_by_role('button',name='Confirm meal choice').tap();alert=p.get_by_role('alertdialog');alert.wait_for();assert p.evaluate('riceFixture.snapshot()')==before;assert rows(p)==baseline and slot(p)==before_slots;after_stored=p.evaluate('simpleTest.backup()');assert all(after_stored.get(key)==before_stored.get(key) for key in ['mealRotationPlansV1','mealRotationDataV1']);alert.get_by_role('button',name='OK',exact=True).tap();assert picker.get_by_role('button',name='Save',exact=True).is_enabled()
    if choice=='storage':p.evaluate('restoreRiceWrites()');finish(p,picker,'replace');assert not picker.count()
    else:picker.get_by_role('button',name='Cancel',exact=True).tap()
  if choice!='storage':assert p.evaluate('riceFixture.snapshot()')==before;p.reload();assert rows(p)==baseline and slot(p)==before_slots
  assert not e,e;c.close()
 for disabled in ['noCandidates','reference']:
  c,p,e,pr=setup(b,name);p.evaluate('riceFixture.'+disabled+'()');p.reload();picker=open_picker(p);assert picker.get_by_role('button',name='Use next recipe',exact=True).is_disabled();select(p,picker,4);finish(p,picker);assert not picker.count();assert not next(meal for meal in p.evaluate('riceFixture.records()') if meal['id']==4)['rotation'];assert not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('riceFixture.otherGroup()');p.reload();baseline=rows(p);picker=open_picker(p);assert picker.get_by_role('button',name='Use next recipe',exact=True).is_enabled();select(p,picker,4);finish(p,picker);assert not picker.count();actual=rows(p);assert any(r['day']=='Monday' and r['id']==4 for r in actual);assert any(r['day']=='Monday' and r['id']==14 for r in actual);assert [r for r in actual if r['day']!='Monday']==[r for r in baseline if r['day']!='Monday'];p.reload();assert rows(p)==actual and not e,e;c.close()
 print('PASS',name,'actual empty-slot UI outer/nested cancel, unavailable replacement, atomic failed-write recovery and reference-only next disabled',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:selections(b,name);selections(b,name,'group');selections(b,name,'day');cancellation_and_failures(b,name)
  b.close()
