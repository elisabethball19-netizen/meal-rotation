"""Focused correctness checks for measured interaction paths; disposable 200-record fixture."""
import json
from playwright.sync_api import sync_playwright
import interaction_performance_browser as f
f.f.HOOK+=r'''
window.perfCheck={
 showTasks:()=>{makeAheadDisplayPrefs.showCompletedToday=true},
 sharedIdea:()=>{for(const meal of meals)if([20,1019].includes(meal.id)){meal.rotation=false;meal.recipeStatus='up-next';meal.upNextStar=false}persist()},
 taskChecked:({key,plan})=>makeAheadTaskComplete(mealPlans.find(p=>p.id===plan),key),
 recordName:()=>meals.find(m=>m.id===2).name,
 pins:()=>meals.filter(m=>[20,1019].includes(m.id)).map(m=>m.upNextStar),
 order:()=>normalizedUpNextOrder(),
 history:()=>history.length,
 backup:()=>captureBackupStorage(),
 semantics:()=>({current:mealPlans.map(plan=>({id:plan.id,entries:recipePlanEntries(plan.id).map(entry=>({day:entry.day,cat:entry.cat,id:entry.meal.id,parent:entry.linkedTo||'',date:cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar)),sides:simpleSidesForEntry(plan,entry).map(side=>({name:side.name,ingredients:side.ingredients.map(i=>i.text)}))}))})),next:previewNextWeekPlans().map(({plan,entries})=>({id:plan.id,entries:entries.map(entry=>({day:entry.day,cat:entry.cat,id:entry.meal.id,parent:entry.linkedTo||'',date:cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar)),sides:simpleSidesForEntry(plan,entry).map(side=>side.name)}))}))}),
 fail:key=>{const set=Storage.prototype.setItem;let once=false;Storage.prototype.setItem=function(k,v){if(k.endsWith(key)&&!once){once=true;throw Error('injected interaction write failure')}return set.call(this,k,v)};window.restorePerfWrites=()=>{Storage.prototype.setItem=set}},
 readOnly:()=>{const set=Storage.prototype.setItem,writes=[];Storage.prototype.setItem=function(k,v){writes.push(k);return set.call(this,k,v)};try{getGroceryContributions(true);getGroceryContributions(true,'both');return writes}finally{Storage.prototype.setItem=set}},
 rapidPins:n=>{for(let i=0;i<n;i++)document.querySelector('.recipe-up-next-star[data-up-next-star="20"]').click()},
 grocery:()=>[...document.querySelectorAll('.master-grocery-item')].find(row=>row.querySelector('.grocery-ingredient-name')?.textContent.includes('pantry 0'))?.querySelector('input'),
 rapidGroceries:n=>{for(let i=0;i<n;i++)perfCheck.grocery().click();return perfCheck.grocery().checked},
 task:()=>{const row=document.querySelector('#todaysTodo [data-make-ahead-key]');return row?{key:row.dataset.makeAheadKey,plan:row.dataset.planId,checked:row.querySelector('input').checked}:null},
 rapidTasks:({key,n})=>{for(let i=0;i<n;i++){const row=[...document.querySelectorAll('[data-make-ahead-key]')].find(row=>row.dataset.makeAheadKey===key);row.querySelector('input').click()}return mealPlans.some(plan=>plan.makeAheadChecks?.[key]===true)},
 checks:()=>({manual:manualGroceryItems(),text:groceryTextOverrides()}),
};'''

def pin_checks(b,name):
 c,p,e,pr,metrics=f.setup(b,name,counters=False);p.evaluate('perfCheck.sharedIdea()');p.evaluate('appPerf.prepare','pin');before=json.loads(p.evaluate('appPerf.stable()'));schedule=p.evaluate('perfCheck.semantics()');order=p.evaluate('perfCheck.order()');history=p.evaluate('perfCheck.history()');p.evaluate('perfCheck.rapidPins(9)');assert p.evaluate('perfCheck.pins()')==[True,True];after=json.loads(p.evaluate('appPerf.stable()'));assert all(after[key]==before[key] for key in ['mealPlans','cookingSessions','occurrenceScales','manual','text']);assert [id for id in p.evaluate('perfCheck.order()') if id not in ['20','1019']]==[id for id in order if id not in ['20','1019']];assert p.evaluate('perfCheck.history()')==history+9;p.locator('#undo').click();assert p.evaluate('perfCheck.pins()')==[False,False];p.locator('#redo').click();assert p.evaluate('perfCheck.pins()')==[True,True];p.reload();p.evaluate('appPerf.prepare','pin');assert p.evaluate('perfCheck.pins()')==[True,True] and p.evaluate('perfCheck.semantics()')==schedule
 saved=p.evaluate('perfCheck.backup()');p.evaluate("perfCheck.fail('mealRotationDataV1')");p.locator('.recipe-up-next-star[data-up-next-star="20"]').click();p.get_by_role('alertdialog').wait_for();assert p.evaluate('perfCheck.pins()')==[True,True];failed=p.evaluate('perfCheck.backup()');assert all(failed[key]==saved[key] for key in ['mealRotationDataV1','mealRotationPlansV1','mealRotationUpNextOrderV1']);p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();p.evaluate('restorePerfWrites()');p.locator('.recipe-up-next-star[data-up-next-star="20"]').click();assert p.evaluate('perfCheck.pins()')==[False,False];p.reload();assert p.evaluate('perfCheck.pins()')==[False,False];assert not e,e
 if pr:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close();print('PASS',name,'rapid/shared pin flags/order, unchanged schedules/sides/progress, Undo/Redo, failed transaction/retry and reload',flush=True)

def grocery_task_checks(b,name):
 c,p,e,pr,metrics=f.setup(b,name,counters=False);schedule=p.evaluate('perfCheck.semantics()');extras=p.evaluate('perfCheck.checks()');assert p.evaluate('perfCheck.readOnly()')==[];p.evaluate('appPerf.prepare','grocery');assert p.evaluate('perfCheck.rapidGroceries(7)') is True;p.reload();p.evaluate('appPerf.prepare','grocery');assert p.evaluate('perfCheck.grocery().checked') is True
 p.evaluate("perfCheck.fail('mealRotationGroceryOccurrenceChecksV1')");p.evaluate('perfCheck.rapidGroceries(3)');assert p.locator('#mealSaveWarning').count();assert p.evaluate('perfCheck.grocery().checked') is False;p.evaluate('restorePerfWrites()');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('!document.getElementById("mealSaveWarning")');p.reload();p.evaluate('appPerf.prepare','grocery');assert p.evaluate('perfCheck.grocery().checked') is False
 bulk=[]
 for _ in range(3):
  for label in ['Select all groceries','Deselect all groceries']:
   result=p.evaluate('label=>{const start=performance.now();document.querySelector("[aria-label=\\""+label+"\\"]").click();return performance.now()-start}',label);bulk.append([label,result]);assert p.evaluate('perfCheck.grocery().checked')==(label.startswith('Select'))
 p.locator('#undo').click();p.locator('#redo').click();assert p.evaluate('perfCheck.checks()')=={**extras,'manual':[{**item,'checked':False} for item in extras['manual']]};assert p.evaluate('perfCheck.semantics()')==schedule;extras=p.evaluate('perfCheck.checks()')
 p.evaluate('perfCheck.showTasks()');p.evaluate('appPerf.prepare','task');task=p.evaluate('perfCheck.task()');assert task;p.evaluate('perfCheck.rapidTasks',{'key':task['key'],'n':5});assert p.evaluate('perfCheck.taskChecked',task) is True;p.locator('#undo').click();p.locator('#redo').click();p.reload();p.evaluate('appPerf.prepare','task');assert p.evaluate('perfCheck.taskChecked',task) is True;assert p.evaluate('perfCheck.semantics()')==schedule;assert p.evaluate('perfCheck.checks()')==extras and not e,e;c.close();print('PASS',name,'read-only grocery queries, rapid grocery/task changes, write failure/retry, bulk select/deselect',bulk,'Undo/Redo and reload; schedules/sides/manual/text unchanged',flush=True)

def dialog_save_checks(b,name):
 c,p,e,pr,metrics=f.setup(b,name,counters=False);before=p.evaluate('perfCheck.semantics()');p.evaluate('appPerf.prepare','dialog');p.locator('#perfDialog').click();d=p.get_by_role('dialog',name='Meal options for Tuesday',exact=True);d.get_by_role('button',name='Close meal options',exact=True).click();p.wait_for_function('!document.querySelector(".meal-action-shield")');assert p.evaluate('perfCheck.semantics()')==before
 p.evaluate('appPerf.prepare','side');p.locator('.occurrence-side-editor [aria-label="Close sides"]').click();assert p.evaluate('perfCheck.semantics()')==before
 target=p.evaluate('appPerf.prepare','recipe');p.evaluate('appPerf.measure',target);assert not p.locator('#name').count();saved_name=p.evaluate('perfCheck.recordName()');p.reload();assert p.evaluate('perfCheck.recordName()')==saved_name and p.evaluate('perfCheck.semantics()')==before
 target=p.evaluate('appPerf.prepare','side');p.evaluate('appPerf.measure',target);assert not p.locator('.occurrence-side-editor').count();p.locator('#undo').click();assert p.evaluate('perfCheck.semantics()')==before;p.locator('#redo').click();saved=p.evaluate('perfCheck.semantics()');p.reload();assert p.evaluate('perfCheck.semantics()')==saved and not e,e;c.close();print('PASS',name,'meal popup/X and side cancellation, small recipe/side saves, reload, side Undo/Redo and occurrence isolation',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:pin_checks(b,name);grocery_task_checks(b,name);dialog_save_checks(b,name)
  b.close()
