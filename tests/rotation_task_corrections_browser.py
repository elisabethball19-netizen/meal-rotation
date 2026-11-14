"""Skipped-slot gestures, exact task navigation, and tab settings in disposable apps."""
from datetime import datetime
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as f
f.HOOK+='''window.correctionTest={
 seed:()=>{
  for(const meal of meals){meal.makeAheadTasks=[{id:'prep-'+meal.id,description:'Defrost chicken roast',daysBefore:2}];if([2,3,6,13].includes(meal.id)){meal.rotation=true;meal.recipeStatus='rotation'}}
  const plan=mealPlans[0];plan.weekdayCategories={Tuesday:['Meals','Other'],Thursday:['Meals']};plan.weekdayMealOverrides={'Tuesday::Meals':'1','Tuesday::Other':'14','Thursday::Meals':'3'};plan.occasionalMeals={Tuesday:'5'};
  mealPlans[1].weekdayCategories={Friday:['Other']};mealPlans[1].weekdayMealOverrides={'Friday::Other':'13'};
  for(const p of mealPlans){p.cycleRetainedSlots={...p.weekdayMealOverrides};p.cycleSlotChoices=Object.fromEntries(Object.entries(p.weekdayMealOverrides).map(([key,mealId])=>[key,{mealId,parentId:'',retain:true,substitution:true}]));delete p.rotationCalendar;delete p.weekSchedule}
  activePlanId=plan.id;weekdayCategories=JSON.parse(JSON.stringify(plan.weekdayCategories));weekdayMealOverrides={...plan.weekdayMealOverrides};weekdayRecipeFilters={};showMealPlanTabs=true;showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;saveActiveMealPlan();
  const start=cookingPlanningWeekStart();for(const p of mealPlans){const entries=scheduledCalendarEntries(p),calendar={version:2,weekStart:cookingLocalDate(start),occurrences:{},assignedOn:{},assignedAt:{},slots:{}};for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:p.id}),date=cookingLocalDate(cookingDateInWeek(entry.day,start));calendar.occurrences[key]=date;calendar.assignedOn[key]=cookingLocalDate(start);calendar.assignedAt[key]=start.toISOString();calendar.slots[rotationCalendarSlot(entry)]=date}p.rotationCalendar=calendar}
  localStorage.setItem('mealRotationShowPlanTabsV1','true');persist();render();
 },
 snapshot:()=>JSON.stringify({meals,plans:mealPlans,sessions:cookingSessions,scales:occurrenceScales,checks:groceryOccurrenceChecks,groceries:getGroceryContributions(true).map(s=>[s.id,grocerySourceChecked(s)])}),
 checkGroceries:()=>{for(const source of getGroceryContributions(true))groceryOccurrenceChecks.checks[source.id]=true;saveGroceryOccurrenceChecks()},
 associated:()=>JSON.stringify({tasks:scheduledMakeAheadTasks(false).map(x=>[x.plan.id,x.key,x.due,x.scheduled,x.complete]).sort((a,b)=>JSON.stringify(a).localeCompare(JSON.stringify(b))),groceries:getGroceryContributions(true).map(x=>[x.id,grocerySourceChecked(x)]),sessions:cookingSessions,scales:occurrenceScales}),
 rows:()=>mealPlans.flatMap(plan=>recipePlanEntries(plan.id).map(e=>({planId:plan.id,day:e.day,cat:e.cat,id:e.meal.id,linked:e.linkedTo,date:cookingLocalDate(scheduledOccurrenceDate({...e,planId:plan.id},plan.rotationCalendar))}))),
 empty:()=>leaveWeekEmpty('Tuesday','Meals'),
 futureEmpty:()=>{const p=mealPlans[0],start=cookingPlanningWeekStart();start.setDate(start.getDate()+7);for(const e of scheduledCalendarEntries(p).filter(e=>e.day==='Tuesday'&&e.cat==='Meals')){const key=rotationOccurrenceKey({...e,planId:p.id});p.rotationCalendar.occurrences[key]=cookingLocalDate(cookingDateInWeek(e.day,start));p.rotationCalendar.slots[rotationCalendarSlot(e)]=p.rotationCalendar.occurrences[key]}persist();leaveWeekEmpty('Tuesday','Meals');rotationWeekOffset=1;render()},
 week:value=>{rotationWeekOffset=value;render()},
 showTask:({plan='original',id=1,future=false,linked=false}={})=>{document.getElementById('taskProbe')?.remove();const items=scheduledMakeAheadTasks(),start=cookingPlanningWeekStart();start.setDate(start.getDate()+7);const item=items.find(x=>x.plan.id===plan&&String(x.entry.meal.id)===String(id)&&(x.scheduled>=cookingLocalDate(start))===future&&(!linked||x.entry.linkedTo!=null));if(!item)throw Error('Task fixture missing '+JSON.stringify({plan,id,future,items:items.map(x=>[x.plan.id,x.entry.meal.id,x.entry.day,x.scheduled])}));window.correctionItem=item;const probe=document.createElement('section');probe.id='taskProbe';probe.append(makeAheadReminderRow(item,true));document.body.prepend(probe);return {key:item.key,text:probe.textContent,day:item.entry.day,scheduled:item.scheduled,due:item.due,occurrence:rotationOccurrenceKey({...item.entry,planId:item.plan.id})}},
 futureTask:()=>{const start=cookingPlanningWeekStart();start.setDate(start.getDate()+7);return scheduledMakeAheadTasks().filter(x=>x.scheduled>=cookingLocalDate(start)).map(x=>({plan:x.plan.id,id:x.entry.meal.id,future:true}))},
 state:()=>({plan:activePlanId,offset:rotationWeekOffset,view:appViewSnapshot()}),
 describe:()=>makeAheadTaskDescription({task:{description:'  Defrost chicken!  '},plan:{name:'Dinner'},entry:{day:'Sunday',meal:{name:'Hidden title'}},scheduled:cookingLocalDate(new Date())}),
 one:()=>{mealPlans=mealPlans.slice(0,1);saveActiveMealPlan();render()},
 checks:()=>mealPlans.map(p=>p.makeAheadChecks||{}),
 stale:()=>{const item=mealPlans[0].weekSchedule.slots['Tuesday::Meals'],date=parseCookingLocalDate(item.scheduledDate);date.setDate(date.getDate()+7);item.scheduledDate=cookingLocalDate(date)},
 skip:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Tuesday'&&x.cat==='Meals'&&!x.occasional);return skipScheduledMeal(x.day,x.cat,x.meal)}
};'''
def setup(b,name):
 c,p,e,prefix=f.setup(b,name,320);p.clock.install(time=datetime.fromisoformat('2026-11-02T12:00:00-08:00'));p.evaluate('correctionTest.seed()');return c,p,e,prefix

def hold(p,loc):
 loc.scroll_into_view_if_needed();box=loc.bounding_box();x=box['x']+min(box['width']/2,70);y=box['y']+box['height']/2
 p.mouse.move(x,y);p.mouse.down();p.clock.run_for(600);p.mouse.up()

def touch_hold(c,p,loc):
 loc.scroll_into_view_if_needed();box=loc.bounding_box();point={'x':box['x']+min(60,box['width']/2),'y':box['y']+box['height']/2,'id':1};cdp=c.new_cdp_session(p)
 cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});p.clock.run_for(600);cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});cdp.detach()

def blank(p):return p.locator('.empty-weekday-meal[data-schedule-day=Tuesday][data-category=Meals]')
def close_empty(p):p.get_by_role('dialog',name='Empty meal options',exact=True).get_by_role('button',name='Close',exact=True).tap()
def empty_cases(b,name):
 c,p,e,prefix=setup(b,name)
 original=p.evaluate('correctionTest.rows()');recipes=f.get(p,'records()');p.evaluate('correctionTest.skip()');p.evaluate('correctionTest.empty()');before=p.evaluate('correctionTest.snapshot()');assert blank(p).count()==1
 hold(p,blank(p).locator('.mealname'));assert p.get_by_role('dialog',name='Empty meal options',exact=True).is_visible();close_empty(p);assert p.evaluate('correctionTest.snapshot()')==before
 hold(p,blank(p).locator('.mealname'));p.get_by_role('button',name='Select Meal',exact=True).tap();p.get_by_role('button',name='Cancel',exact=True).tap();assert p.evaluate('correctionTest.snapshot()')==before
 hold(p,blank(p).locator('.mealname'));p.get_by_role('button',name='Resume planned meal',exact=True).tap();assert not blank(p).count()
 after=p.evaluate('correctionTest.rows()');assert [x for x in after if not(x['planId']=='original' and x['day']=='Tuesday' and (x['cat']=='Meals' or x.get('linked')==1))]==[x for x in original if not(x['planId']=='original' and x['day']=='Tuesday' and (x['cat']=='Meals' or x.get('linked')==1))],(original,after)
 assert f.get(p,'records()')==recipes
 p.evaluate('correctionTest.empty()');touch_hold(c,p,blank(p).locator('.mealname'));close_empty(p);before=p.evaluate('correctionTest.snapshot()');hold(p,blank(p));p.get_by_role('button',name='Select Meal',exact=True).tap();picker=p.locator('.weekday-meal-picker');picker.get_by_role('button',name='Default missing',exact=False).first.tap();p.evaluate('correctionTest.stale()');before=p.evaluate('correctionTest.snapshot()');picker.get_by_role('button',name='Save',exact=True).tap();assert p.evaluate('correctionTest.snapshot()')==before
 p.evaluate('correctionTest.empty()');hold(p,blank(p));p.get_by_role('button',name='Select Meal',exact=True).tap();picker=p.locator('.weekday-meal-picker');picker.get_by_role('button',name='Default missing',exact=False).first.tap();picker.get_by_role('button',name='Save',exact=True).tap();assert not blank(p).count();assert any(x['day']=='Tuesday' and x['id']==6 for x in p.evaluate('correctionTest.rows()'))
 # Future-dated saved slot, not a second copy of this week's slot.
 p.evaluate('correctionTest.seed()');p.evaluate('correctionTest.futureEmpty()');p.reload();p.evaluate('correctionTest.week(1)');before=p.evaluate('correctionTest.snapshot()');assert blank(p).count()==1;hold(p,blank(p));close_empty(p);assert p.evaluate('correctionTest.snapshot()')==before
 hold(p,blank(p));p.get_by_role('button',name='Resume planned meal',exact=True).tap();assert not blank(p).count();assert p.evaluate('correctionTest.state().offset')==1
 p.evaluate('correctionTest.seed()');p.evaluate('correctionTest.futureEmpty()');before=p.evaluate('correctionTest.rows()');hold(p,blank(p));p.get_by_role('button',name='Select Meal',exact=True).tap();picker=p.locator('.weekday-meal-picker');picker.get_by_role('button',name='Default missing',exact=False).first.tap();picker.get_by_role('button',name='Save',exact=True).tap();rows=p.evaluate('correctionTest.rows()');assert any(x['id']==6 and x['date']=='2026-11-10' for x in rows);assert [x for x in rows if x['day']!='Tuesday' or x['planId']!='original']==[x for x in before if x['day']!='Tuesday' or x['planId']!='original']
 # Hiding and restoring an unchanged recipe keeps its dated tasks, checks and groceries.
 p.evaluate('correctionTest.seed()');p.evaluate('correctionTest.showTask({id:1})');p.locator('#taskProbe input').tap();p.evaluate('correctionTest.checkGroceries()');associated=p.evaluate('correctionTest.associated()');p.evaluate('correctionTest.empty()');hold(p,blank(p));p.get_by_role('button',name='Resume planned meal',exact=True).tap();assert p.evaluate('correctionTest.associated()')==associated
 # An unassigned dash does not get restore actions from a different group.
 p.evaluate('correctionTest.seed()');empty=p.locator('.empty-weekday-meal[data-schedule-day=Monday]');hold(p,empty);assert not p.get_by_role('dialog',name='Empty meal options',exact=True).count()
 # Ordinary touch scrolling neither edits nor opens options.
 p.evaluate('correctionTest.empty()');blank(p).scroll_into_view_if_needed();p.evaluate("const spacer=document.createElement('div');spacer.style.height='1600px';document.getElementById('list').append(spacer)");box=blank(p).bounding_box();point={'x':box['x']+40,'y':box['y']+20,'id':1};cdp=c.new_cdp_session(p);before=p.evaluate('correctionTest.snapshot()');cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]})
 for delta in [15,40,80]:cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**point,'y':point['y']-delta}]})
 cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});p.wait_for_timeout(150);assert not p.get_by_role('dialog',name='Empty meal options',exact=True).count() and p.evaluate('correctionTest.snapshot()')==before;cdp.detach()
 assert not e,e;c.close();print('PASS',name,'skip/empty long press, restore/replace/cancel, saved future slot, unrelated slots/recipes and unassigned empties',flush=True)

def task_cases(b,name):
 c,p,e,prefix=setup(b,name)
 assert p.evaluate('correctionTest.describe()')=='  Defrost chicken!   for Sunday’s dinner'
 item=p.evaluate('correctionTest.showTask({plan:"lunch",id:13})');assert item['day']=='Friday' and item['due']<item['scheduled'];assert item['text']=='Defrost chicken roast for Friday’s lunch'
 before=p.evaluate('correctionTest.snapshot()');p.locator('#taskProbe .make-ahead-task-link').tap();p.wait_for_timeout(100);assert p.evaluate('correctionTest.state().plan')=='lunch';assert p.evaluate('correctionTest.snapshot()')==before
 assert p.locator('.preparation-meal-target').get_attribute('data-rotation-occurrence')==item['occurrence']
 item=p.evaluate('correctionTest.showTask({plan:"original",id:5})');before=p.evaluate('correctionTest.snapshot()');p.locator('#taskProbe .make-ahead-task-link').tap();p.wait_for_timeout(100);assert p.locator('.preparation-meal-target').get_attribute('data-rotation-occurrence')==item['occurrence'];assert p.evaluate('correctionTest.snapshot()')==before
 # Linked recipe has its own exact anchor, rather than its parent.
 p.evaluate('correctionTest.showTask({id:8,linked:true})');p.locator('#taskProbe .make-ahead-task-link').tap();p.wait_for_timeout(100);assert p.locator('.preparation-meal-target').inner_text()=='Linked side'
 p.evaluate('correctionTest.showTask({id:1})');state=p.evaluate('correctionTest.state()');before=p.evaluate('correctionTest.checks()');p.locator('#taskProbe input').tap();assert p.evaluate('correctionTest.state()')==state;assert p.evaluate('correctionTest.checks()')!=before
 p.evaluate('correctionTest.showTask({id:1})');before=p.evaluate('correctionTest.snapshot()');hold(p,p.locator('#taskProbe .make-ahead-task-link'));assert p.get_by_role('dialog',name='Edit preparation task',exact=True).count();p.get_by_role('dialog',name='Edit preparation task',exact=True).get_by_role('button',name='Cancel preparation edit',exact=True).tap();assert p.evaluate('correctionTest.snapshot()')==before and p.evaluate('correctionTest.state()')==state
 future=p.evaluate('correctionTest.futureTask()')[0];item=p.evaluate('arg=>correctionTest.showTask(arg)',future);before=p.evaluate('correctionTest.snapshot()');p.locator('#taskProbe .make-ahead-task-link').tap();p.wait_for_timeout(100);assert p.evaluate('correctionTest.state().offset')==1;assert p.locator('.preparation-meal-target').get_attribute('data-rotation-occurrence')==item['occurrence'];assert p.evaluate('correctionTest.snapshot()')==before
 p.evaluate('correctionTest.week(0)');p.evaluate('correctionTest.showTask({id:1})');p.evaluate('correctionTest.empty()');before=p.evaluate('correctionTest.snapshot()');state=p.evaluate('correctionTest.state()');p.locator('#taskProbe .make-ahead-task-link').tap();assert p.get_by_role('alertdialog').count();assert p.evaluate('correctionTest.snapshot()')==before and p.evaluate('correctionTest.state()')==state;p.get_by_role('button',name='OK',exact=True).tap()
 assert not e,e;c.close();print('PASS',name,'exact task text, planned day, tab/current/next/linked/multiple-slot navigation, checkbox only, held edit and missing occurrence',flush=True)

def settings_cases(b,name):
 c,p,e,prefix=setup(b,name);p.evaluate('correctionTest.one()');plans=p.evaluate('batch1.plans()');assert p.locator('.meal-plan-tab').count()==1 and p.locator('.meal-plan-add').count()==1
 assert not p.get_by_role('button',name='Add Meal Tab',exact=True).count()
 p.locator('#settings').tap();p.locator('[data-settings-group=display]>summary').tap();p.get_by_role('checkbox',name='Show meal tabs',exact=True).uncheck();assert not p.locator('.meal-plan-add').count();p.get_by_role('button',name='Cancel settings',exact=True).tap();assert p.locator('.meal-plan-add').count()==1
 p.locator('#settings').tap();p.locator('[data-settings-group=display]>summary').tap();p.get_by_role('checkbox',name='Show meal tabs',exact=True).uncheck();p.get_by_role('button',name='Save settings',exact=True).tap();p.reload();assert not p.locator('.meal-plan-add').count();assert p.evaluate('batch1.plans()')==plans
 p.locator('#settings').tap();p.locator('[data-settings-group=display]>summary').tap();p.get_by_role('checkbox',name='Show meal tabs',exact=True).check();p.get_by_role('button',name='Save settings',exact=True).tap();assert p.locator('.meal-plan-tab').count()==1;p.locator('.meal-plan-add').tap();p.get_by_role('dialog',name='Add Meal Tab',exact=True).get_by_role('button',name='Cancel',exact=True).tap();p.reload();assert p.locator('.meal-plan-add').count()==1 and p.evaluate('batch1.plans()')==plans
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');p.screenshot(path='/tmp/rotation-task-settings-'+name+'.png')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not e,e;c.close();print('PASS',name,'one-plan tabs/plus, Show meal tabs Save/Cancel, hidden/shown reload and preserved plan',flush=True)

def gesture_layout_cases(b,name):
 c,p,e,prefix=setup(b,name)
 main=p.locator('#list .meal[data-meal-id="1"] .mealname').first;main.tap();assert p.locator('#recipeViewer').count();p.get_by_role('button',name='Close recipe',exact=True).tap();before=p.evaluate('correctionTest.snapshot()');touch_hold(c,p,main);assert p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).count();p.get_by_role('button',name='Close meal options',exact=True).tap();assert p.evaluate('correctionTest.snapshot()')==before
 p.evaluate('correctionTest.showTask({id:1})');state=p.evaluate('correctionTest.state()');before=p.evaluate('correctionTest.snapshot()');touch_hold(c,p,p.locator('#taskProbe .make-ahead-task-link'));assert p.get_by_role('dialog',name='Edit preparation task',exact=True).count();p.get_by_role('button',name='Cancel preparation edit',exact=True).tap();assert p.evaluate('correctionTest.state()')==state and p.evaluate('correctionTest.snapshot()')==before;checks=p.evaluate('correctionTest.checks()');p.locator('#taskProbe input').tap();assert p.evaluate('correctionTest.checks()')!=checks and p.evaluate('correctionTest.state()')==state;p.locator('#taskProbe').evaluate('(e)=>e.remove()')
 for width,height in [(320,800),(360,420)]:
  p.set_viewport_size({'width':width,'height':height});p.evaluate('correctionTest.week(0)');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert p.locator('#todaysTodo .make-ahead-task-link').evaluate_all('(xs)=>xs.every(x=>{const b=x.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth})');p.screenshot(path='/tmp/rotation-task-text-'+name+'-'+str(width)+'.png')
 assert not e,e;c.close();print('PASS',name,'populated tap/touch-hold, task touch editing without navigation, 320px and reduced-height task layouts',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   empty_cases(b,name);task_cases(b,name);settings_cases(b,name);gesture_layout_cases(b,name)
  b.close()
