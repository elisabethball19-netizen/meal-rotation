"""Authorized Nov 16 phone corrections; disposable intercepted app storage only."""
import json
from datetime import datetime,timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
import meal_plan_active120_browser as prior
old=prior.old
base=old.base
base.HOOK+='''window.phone120={
 diagnostic:occurrenceDateDiagnostic,
 due:()=>{showMealPlanTabs=true;localStorage.setItem('mealRotationShowPlanTabsV1','true');rotationWeekOffset=0;allMealsActive=false;showTop=true;for(const m of meals)delete m.makeAheadTasks;const source=previewNextWeekPlans().find(s=>s.plan.id===activePlanId),entry=source.entries.find(e=>e.day==='Tuesday');meals.find(m=>m.id===entry.meal.id).makeAheadTasks=[{id:'phone-prep',description:'Defrost chicken',daysBefore:1}];makeAheadDisplayPrefs.showMakeAheadReminders=true;const plan=mealPlans.find(p=>p.id===activePlanId);plan.makeAheadChecks={};plan.makeAheadPending=[];saveActiveMealPlan(false);persist();renderList({readOnly:true});return scheduledMakeAheadTasks().filter(t=>t.task.id==='phone-prep').map(t=>({preview:t.preview,day:t.entry.day,due:t.due,scheduled:t.scheduled,key:t.key}))},
 tabs:value=>{showMealPlanTabs=value;localStorage.setItem('mealRotationShowPlanTabsV1',String(value));renderList({readOnly:true})},
 current:()=>{rotationWeekOffset=0;allMealsActive=false;showTop=true;renderList({readOnly:true})},
 overview:()=>{rotationWeekOffset=0;overviewWeekOffset=0;allMealsActive=true;showTop=true;renderList({readOnly:true})},
 preview:()=>{allMealsActive=false;rotationWeekOffset=1;renderList({readOnly:true})},
 clearSource:()=>{Object.assign(meals.find(m=>m.id===8),{url:'',rotation:true,recipeStatus:'rotation',rotationPromotionPriority:42})},
 statuses:()=>JSON.stringify(meals.map(m=>[m.id,m.rotation,m.recipeStatus,m.rotationPromotionPriority])),
 customContext:()=>{const before=startWeekday,overview=allMealsActive;const task=scheduledMakeAheadTasks().find(t=>t.preview&&t.entry.day==='Tuesday'&&t.task.id==='phone-prep');try{startWeekday='Wednesday';allMealsActive=false;if(!task)return null;const labels=[];for(const tabs of [false,true]){showMealPlanTabs=tabs;for(const offset of [0,1]){rotationWeekOffset=offset;labels.push(makeAheadTaskDescription(task))}}return labels}finally{startWeekday=before;allMealsActive=overview;showMealPlanTabs=true;rotationWeekOffset=0}},
 reference:()=>{saveMealGroupSettings('Reference','Reference',false);active='Reference';batch1.groups();openEditor(8)},
 rotation:()=>{active='Meals';batch1.groups();openEditor(74)},
 raw:()=>JSON.stringify(Array.from({length:localStorage.length},(_,i)=>{const k=localStorage.key(i);return [k,localStorage.getItem(k)]}).sort()),
 longEditor:()=>{const m=meals.find(m=>m.id===8);m.linkedMealIds=[74,75];active=m.cat;batch1.groups();openEditor(8)},
 organize:()=>beginRecipeBulkGroup('Meals'),
 groceries:()=>{showTop=true;groceryTabActive=true;allMealsActive=false;groceryPeriod='both';localStorage.setItem(GROCERY_PERIOD_KEY,'both');renderList({readOnly:true})}
};'''
OUT=Path('/workspace/work/screenshots120-phone');OUT.mkdir(exist_ok=True)
def shot(p,name,label):p.screenshot(path=str(OUT/(name+'-'+label+'.png')),full_page=False)
def run(b,name):
 c,p,errors,prefix=old.setup_followup(b,name)
 # Existing evidenced fixture is not the user's unknown data. Keep negative guards.
 p.evaluate('active120.sameDay();followup120.ambiguousFuture()');assert p.evaluate('active120.guards()')=={'early':False,'uncertain':False}
 checks=p.evaluate('active120.checks()');stable=p.evaluate('active120.stable()');raw=p.evaluate('phone120.raw()');report=p.evaluate('phone120.diagnostic()');assert p.evaluate('phone120.raw()')==raw
 assert any(r['day']=='Tuesday' and r['storedDate']=='2026-11-17' and r['repairEligible'] for r in report['rows'])
 assert not any(x in json.dumps(report) for x in ['Thai Garlic','ingredients','mealId','recipeId'])
 p.evaluate('followup120.repair()');assert p.evaluate('active120.checks()')==checks and p.evaluate('active120.stable()')==stable;assert p.evaluate('active120.prep()')[0]=={'scheduled':'2026-11-10','due':'2026-11-09','complete':True};assert ['Tuesday','2026-11-10'] in p.evaluate('active120.dates()');assert ['Saturday','2026-11-28'] in p.evaluate('active120.dates()')
 p.evaluate('active120.undo()');assert ['Tuesday','2026-11-17'] in p.evaluate('active120.dates()');p.evaluate('active120.redo()')
 # Actual diagnostic download through Backups; no recipe content or storage writes.
 p.locator('#settings').tap();p.locator('details[data-settings-group=backups] > summary').tap();raw=p.evaluate('phone120.raw()')
 with p.expect_download() as download:p.get_by_role('button',name='Export meal-date diagnostic',exact=True).tap()
 exported=json.loads(Path(download.value.path()).read_text());assert exported['kind']=='occurrence-date-diagnostic' and 'meals' not in exported and p.evaluate('phone120.raw()')==raw
 p.locator('#settings').tap()
 # Fixed Monday Nov16, generated Tuesday Nov17 meal, prep due Monday.
 p.clock.set_fixed_time(datetime(2026,11,16,12,tzinfo=timezone.utc));tasks=p.evaluate('phone120.due()');assert any(t['preview'] and t['day']=='Tuesday' and t['due']=='2026-11-16' for t in tasks),tasks
 row=p.locator('#todaysTodo .make-ahead-reminder').filter(has_text='Tuesday');assert row.count()==1
 assert row.inner_text()=='Defrost chicken for Tuesday’s dinner next week';shot(p,name,'due-monday')
 before=p.evaluate('active120.stable()');raw=p.evaluate('plan120.state()');row.get_by_role('button').tap();p.wait_for_timeout(800);assert p.evaluate('active120.offset()')==1
 assert p.locator('.preparation-meal-target').count()==1;shot(p,name,'scrolled-shadow');assert p.evaluate('active120.stable()')==before and p.evaluate('plan120.state()')==raw
 p.wait_for_timeout(2300);assert not p.locator('.preparation-meal-target').count()
 assert 'next week' not in p.locator('#todaysTodo').inner_text()
 p.evaluate('phone120.current();phone120.tabs(false)');assert p.locator('#todaysTodo').inner_text().find('Defrost chicken for Tuesday next week')>=0
 p.evaluate('phone120.preview()');assert 'Defrost chicken for Tuesday' in p.locator('#todaysTodo').inner_text() and 'next week' not in p.locator('#todaysTodo').inner_text()
 p.evaluate('phone120.current();phone120.tabs(true);phone120.overview()');assert p.locator('.make-ahead-task-link').filter(has_text='Tuesday').count()==1;shot(p,name,'overview-monday')
 p.evaluate('phone120.current()');p.locator('#todaysTodo .make-ahead-reminder').filter(has_text='Tuesday').locator('input').click();assert p.evaluate('active120.stable()')==before;p.evaluate('active120.undo();phone120.current()');assert p.locator('#todaysTodo').count()==1;p.evaluate('active120.redo();phone120.current()');assert not p.locator('#todaysTodo').count();p.reload();p.evaluate('phone120.current()');assert not p.locator('#todaysTodo').count()
 p.evaluate('phone120.overview()');assert p.locator('.make-ahead-reminder').filter(has_text='Tuesday').locator('input').is_checked()
 assert p.evaluate('phone120.customContext()')==['Defrost chicken for Tuesday next week','Defrost chicken for Tuesday','Defrost chicken for Tuesday’s dinner next week','Defrost chicken for Tuesday’s dinner']
 # Source labels, reference context retains status/memberships; cancel/save/history Back.
 p.evaluate('phone120.clearSource();phone120.reference()');assert not p.locator('#recipeStatus').is_visible();record=next(m for m in p.evaluate('batch1.records()') if m['id']==8);statuses=p.evaluate('phone120.statuses()')
 p.locator('#editor details[data-editor-section=recipe] > summary').tap();source=p.get_by_role('button',name='Add recipe link',exact=True);assert source.is_visible();source.tap();p.locator('#url').fill('https://example.org/recipe');p.locator('#url').dispatch_event('input');assert p.get_by_role('button',name='Edit recipe link',exact=True).is_visible();shot(p,name,'reference-editor')
 p.locator('#cancel').tap();assert next(m for m in p.evaluate('batch1.records()') if m['id']==8)==record
 p.evaluate('phone120.reference()');p.locator('#editor details[data-editor-section=recipe] > summary').tap();p.get_by_role('button',name='Add recipe link',exact=True).tap();p.locator('#url').fill('https://example.org/recipe');p.locator('#save').tap();saved=next(m for m in p.evaluate('batch1.records()') if m['id']==8);assert p.evaluate('phone120.statuses()')==statuses;assert saved['url']=='https://example.org/recipe' and saved['rotation']==record['rotation'] and saved['cat']==record['cat']
 p.evaluate('phone120.rotation()');assert p.locator('#recipeStatus').is_visible();p.locator('#cancel').tap();p.evaluate('phone120.reference()');p.go_back();p.wait_for_timeout(150);assert not p.locator('#editor .editor').count()
 # Reorder validates drafts first, Done and browser Back return directly to groups.
 p.evaluate("batch1.groupEdit('Meals')");p.get_by_role('switch',name='Use for weekly meals').uncheck();p.get_by_role('button',name='Reorder groups',exact=True).tap();assert p.get_by_role('dialog',name='Edit group',exact=True).is_visible() and not p.locator('body.group-reorder-active').count();p.get_by_role('button',name='Cancel group editing',exact=True).tap()
 p.evaluate("batch1.groupEdit('Reference')");p.get_by_role('textbox',name='Group name').fill('Long reference recipes and accompaniments');p.get_by_role('button',name='Reorder groups',exact=True).tap();p.wait_for_timeout(150);assert p.locator('body.group-reorder-active').count();shot(p,name,'reorder')
 p.get_by_role('button',name='Finish reordering groups',exact=True).tap();p.wait_for_timeout(150);assert not p.get_by_role('dialog',name='Edit group',exact=True).count() and not p.locator('body.group-reorder-active').count()
 p.evaluate("batch1.groupEdit('Long reference recipes and accompaniments')");p.get_by_role('button',name='Reorder groups',exact=True).tap();p.wait_for_timeout(100);p.go_back();p.wait_for_timeout(150);assert not p.locator('body.group-reorder-active').count() and not p.get_by_role('dialog',name='Edit group',exact=True).count()
 p.evaluate('phone120.longEditor()');p.wait_for_timeout(900);shot(p,name,'long-editor-headers');p.locator('#cancel').tap()
 p.evaluate('phone120.organize()');p.locator('#recipeBulkToolbar').wait_for(state='visible');p.wait_for_timeout(150);shot(p,name,'organizing');p.get_by_role('button',name='Done',exact=True).tap();assert not p.locator('#recipeBulkToolbar').count()
 # Existing rail behavior, arrow geometry and no visible caption; all-done/link pane.
 p.evaluate('active120.home();active120.long()')
 for mode in ['full','split']:
  for width,height in [(360,800),(740,360),(320,640)]:
   p.set_viewport_size({'width':width,'height':height});p.evaluate('document.body.dataset.mealTextSize='+json.dumps('extra' if width==320 else 'default'));p.evaluate('mode=>active120.viewer(mode)',mode);p.wait_for_timeout(200);p.evaluate('active120.scroll("end")');p.wait_for_timeout(100)
   jump=p.get_by_role('button',name='Go to first unfinished step',exact=True);assert jump.is_visible();box=jump.bounding_box();assert box['height']>=44 and box['y']>=0 and box['y']+box['height']<=height
   assert jump.inner_text()=='' and jump.evaluate('(e)=>getComputedStyle(e,"::after").content')=='none';shot(p,name,mode+'-'+str(width));jump.tap();p.wait_for_timeout(200)
   if mode=='split' and width==740:
    p.evaluate('active120.linked()');p.wait_for_timeout(200);p.evaluate('active120.scroll("end")');p.wait_for_timeout(100);p.get_by_role('button',name='Go to first unfinished step',exact=True).tap();p.wait_for_timeout(200);first=p.locator('.recipe-instructions-pane .cooking-item').first.bounding_box();pane=p.locator('.recipe-instructions-pane').bounding_box();assert pane['y']<=first['y']<pane['y']+pane['height'];shot(p,name,'linked-return')
   p.evaluate('active120.allDone()');p.wait_for_timeout(100);assert not p.locator('.recipe-current-step:visible').count();p.get_by_role('button',name='Close recipe',exact=True).tap()
 for width,height in [(320,640),(740,360)]:
  p.set_viewport_size({'width':width,'height':height});p.evaluate("document.body.dataset.mealTextSize='extra';phone120.groceries()");shot(p,name,'groceries-large-'+str(width));assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'date evidence/guards, Monday preview due/completion/reload, wording, shadow, editor/save/cancel/Back, reorder/Done/Back, viewer phones and grocery heading',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
