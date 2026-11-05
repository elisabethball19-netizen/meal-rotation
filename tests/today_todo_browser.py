"""Local-date Today checklist, cross-plan occurrence checks and global visibility."""
import copy
from datetime import datetime
from playwright.sync_api import sync_playwright
import make_ahead_reminders_browser as t
from scheduled_linked_slots_browser import state,compose
f=t.f
f.EXTRA+='''window.todayTest={
 seed:()=>{prepTest.seed();meals.find(m=>m.id===4).makeAheadTasks=[{id:'thaw',description:'Thaw soup',daysBefore:6}];meals.find(m=>m.id===10).makeAheadTasks=[{id:'eggs',description:'Prepare eggs',daysBefore:1}];meals.find(m=>m.id===20).makeAheadTasks=[{id:'side',description:'Prepare rice',daysBefore:0}];meals.find(m=>m.id===1).linkedMealIds=[20];
 const breakfast=JSON.parse(JSON.stringify(mealPlans[0]));breakfast.id='breakfast';breakfast.name='Second Breakfast';breakfast.weekdayCategories={Sunday:['Mains']};breakfast.weekdayMealOverrides={'Sunday::Mains':'10'};breakfast.cycleRetainedSlots={'Sunday::Mains':'10'};breakfast.cycleSlotChoices={'Sunday::Mains':{mealId:'10',parentId:'',substitution:true,retain:true}};breakfast.makeAheadChecks={};mealPlans.push(breakfast);
 for(const plan of mealPlans){const start=parseCookingLocalDate(plan.id==='lunch'?'2026-11-10':'2026-11-03'),entries=getDisplayedWeekdayMealsForPlan(plan),calendar={version:2,weekStart:cookingLocalDate(start),occurrences:{},assignedOn:{},assignedAt:{},slots:{}};for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:plan.id}),date=cookingLocalDate(cookingDateInWeek(entry.day,start));calendar.occurrences[key]=date;calendar.assignedOn[key]='2026-11-03';calendar.assignedAt[key]='2026-11-03T08:00:00.000Z';calendar.slots[rotationCalendarSlot(entry)]=date}plan.rotationCalendar=calendar}persist();saveActiveMealPlan();promotionTest.my();syncMakeAheadLocalDay()},
 prefs:()=>makeAheadDisplayPrefs,hidden:value=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>value});document.dispatchEvent(new Event('visibilitychange'))},
 tabs:value=>{showMealPlanTabs=value;localStorage.setItem('mealRotationShowPlanTabsV1',String(value));render()},
 raw:()=>slotBackup.capture(),restore:b=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(b.mealRotationDataV1),storage:b}));backupRestoreReloadPending=true},
 empty:()=>{for(const meal of meals)delete meal.makeAheadTasks;persist();renderList()},
 undo:()=>restoreState(JSON.parse(history.pop())),remove:id=>applyRecipeBulk([String(id)],{delete:true}),skip:()=>{const entry=getDisplayedWeekdayMeals().find(x=>x.meal.id===2);return skipScheduledMeal(entry.day,entry.cat,entry.meal)},remember:()=>{window.todoMealNode=document.querySelector('#list>.weekday-heading')},sameNode:()=>todoMealNode===document.querySelector('#list>.weekday-heading')
};'''
class Zone:
 def __init__(self,b,tz):self.b=b;self.tz=tz
 def new_context(self,**kwargs):return self.b.new_context(**kwargs,timezone_id=self.tz)
def setup(b,name,width=320,iso='2026-11-07T20:00:00+00:00',tz='America/Los_Angeles'):
 c,p,e,prefix=f.setup(Zone(b,tz),name,width,'linked-slot');p.clock.install(time=datetime.fromisoformat(iso));p.evaluate('todayTest.seed()');return c,p,e,prefix
def todo(p):return p.locator('#todaysTodo')
def labels(p):return todo(p).locator('.make-ahead-reminder').all_text_contents()
def setting(p,enabled,save=True):
 p.get_by_role('button',name='Settings and backups',exact=True).tap();group=p.locator('#settingsPanel [data-settings-group="display"]')
 if group.get_attribute('open') is None:group.locator(':scope > summary').tap()
 check=group.get_by_role('checkbox',name='Show Make Ahead Reminders',exact=True);check.set_checked(enabled);p.locator('#settingsPanel').get_by_role('button',name='Save settings' if save else 'Cancel settings',exact=True).tap()
def checklist(b,name,width,tabs):
 c,p,e,prefix=setup(b,name,width);p.evaluate('v=>todayTest.tabs(v)',tabs);assert len(labels(p))==4,labels(p)
 text=todo(p).inner_text();assert all(x in text for x in ['Marinate pork','Thaw soup','Prepare eggs','Prepare rice','Dinner','Lunch','Second Breakfast']);assert all(x not in text for x in ['Prepare dough','Chop herbs','Order ingredients']);assert not p.locator('#list button[aria-label^="Make ahead:"]').count()
 geometry=p.evaluate('({header:document.querySelector(".rotation-heading-actions").getBoundingClientRect().bottom,todo:document.querySelector("#todaysTodo").getBoundingClientRect(),card:document.querySelector(".weekday-heading").getBoundingClientRect().top})');assert geometry['todo']['top']>=geometry['header'] and geometry['card']>=geometry['todo']['bottom'];assert p.get_by_role('button',name='Show completed tasks',exact=True).is_visible()
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p);target="Marinate pork · for Sunday's Spaghetti · Dinner";todo(p).get_by_role('checkbox',name=target,exact=True).tap();assert len(labels(p))==3
 p.evaluate('prepTest.overview()');weekly=p.get_by_role('checkbox',name="Marinate pork · for Sunday's Spaghetti",exact=True);assert weekly.is_checked();weekly.uncheck();p.evaluate('promotionTest.my()');assert len(labels(p))==4
 while todo(p).get_by_role('checkbox').count():todo(p).get_by_role('checkbox').first.tap()
 assert 'All done!' in todo(p).inner_text();p.get_by_role('button',name='Show completed tasks',exact=True).tap();assert todo(p).locator('.make-ahead-complete').count()==4
 todo(p).get_by_role('checkbox',name=target,exact=True).tap();assert todo(p).locator('.make-ahead-reminder').first.inner_text().startswith('Marinate pork');assert todo(p).locator('.make-ahead-complete').count()==3;p.get_by_role('button',name='Hide completed tasks',exact=True).tap();assert len(labels(p))==1
 assert state(p)['meals']==before['meals'] and compose(p)==schedule and f.sources(p)==groceries and state(p)['sessions']==before['sessions'] and state(p)['scales']==before['scales']
 p.reload();assert len(labels(p))==1 and not p.evaluate('todayTest.prefs().showCompletedToday');backup=p.evaluate('todayTest.raw()');expected=copy.deepcopy(state(p));p.get_by_role('button',name='Show completed tasks',exact=True).tap();assert len(labels(p))==4
 setting(p,False);assert not todo(p).count();p.evaluate('prepTest.overview()');assert not p.locator('.make-ahead-reminder').count();assert state(p)['meals']==expected['meals']
 # Reminders remain editable even while planning displays are globally disabled.
 p.evaluate('promotionTest.editor(2)');p.wait_for_timeout(850);p.locator('[data-editor-section="notes"]>summary').tap();p.locator('#recipeMakeAhead>summary').tap();assert p.get_by_role('textbox',name='Preparation task',exact=True).count()==4;p.locator('#cancel').tap();setting(p,True);assert p.locator('.make-ahead-complete').count()==3
 setting(p,False,False);assert p.evaluate('todayTest.prefs().showMakeAheadReminders') and p.locator('.make-ahead-reminder').count()>0
 p.evaluate('b=>todayTest.restore(b)',backup);p.reload();assert state(p)==expected and len(labels(p))==1
 # Older complete backups without this preference retain tasks/checks and use enabled defaults.
 del backup['mealRotationMakeAheadDisplayV1'];p.evaluate('b=>todayTest.restore(b)',backup);p.reload();assert p.evaluate('todayTest.prefs()')=={'showMakeAheadReminders':True,'showCompletedToday':False};assert len(labels(p))==1
 p.screenshot(path='/tmp/today-todo-'+name+'-'+str(width)+'-'+str(tabs)+'.png');p.evaluate('todayTest.empty()');assert not todo(p).count() and not e,e
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'tabs',tabs,'only local-today/all-plan tasks, no duplicates/icons, shared completion/uncheck, ordering/eye/All done/reload, global Save/Cancel and old/new backups, disabled editing, unchanged schedules/groceries/progress',flush=True);c.close()
def dates(b,name):
 for tz,iso,expected in [('America/Los_Angeles','2026-11-07T03:30:00+00:00','Prepare dough'),('Pacific/Auckland','2026-11-06T12:30:00+00:00','Marinate pork')]:
  c,p,e,_=setup(b,name,360,iso,tz);assert expected in todo(p).inner_text();assert ('Marinate pork' in todo(p).inner_text())==(expected=='Marinate pork');assert not e,e;c.close()
 c,p,e,_=setup(b,name,320,'2026-11-07T07:59:59.500000+00:00');assert labels(p)==["Prepare dough · for Sunday's Spaghetti · Dinner"];before=copy.deepcopy(state(p));p.evaluate('todayTest.remember()');p.clock.fast_forward(1000);assert len(labels(p))==4 and p.evaluate('todayTest.sameNode()');assert state(p)==before
 p.evaluate('todayTest.hidden(true)');p.clock.fast_forward(24*60*60*1000);p.evaluate('todayTest.hidden(false)');assert labels(p)==["Chop herbs · for Sunday's Spaghetti · Dinner"];assert p.evaluate('todayTest.sameNode()') and state(p)==before
 p.evaluate('todayTest.remember()');p.clock.fast_forward(24*60*60*1000+3600000);assert not todo(p).count() and p.evaluate('todayTest.sameNode()') and not e,e;c.close()
 print('PASS',name,'local dates differ from UTC in both directions; live midnight and hidden/foreground rollover update only Todo, without replacing meal-card DOM or modifying data',flush=True)
def schedule_updates(b,name):
 for action in ['skip','cycle','remove']:
  c,p,e,_=setup(b,name);target="Marinate pork · for Sunday's Spaghetti · Dinner";todo(p).get_by_role('checkbox',name=target,exact=True).tap();key=next(x['key'] for x in p.evaluate('prepTest.rows()') if x['description']=='Marinate pork');before=copy.deepcopy(state(p));p.get_by_role('button',name='Show completed tasks',exact=True).tap()
  p.evaluate('todayTest.skip()' if action=='skip' else 'prepTest.cycle()' if action=='cycle' else 'todayTest.remove(2)');assert 'Marinate pork' not in todo(p).inner_text();assert all(x['key']!=key for x in p.evaluate('prepTest.rows()'));assert all(x in todo(p).inner_text() for x in ['Prepare eggs','Thaw soup'])
  for m in state(p)['meals']:assert m.get('lastCooked')==next(old for old in before['meals'] if old['id']==m['id']).get('lastCooked')
  p.evaluate('prepTest.back()' if action=='cycle' else 'todayTest.undo()');assert next(x for x in p.evaluate('prepTest.rows()') if x['key']==key)['complete'];assert todo(p).get_by_role('checkbox',name=target,exact=True).is_checked() and not e,e;c.close()
 print('PASS',name,'skip, cycle, deletion and Undo/Cycle Back update Today and preserve independent plans, saved completions and last-cooked fields',flush=True)
def dst_and_editor_midnight(b,name):
 c,p,e,_=setup(b,name,320,'2026-11-01T06:59:59.500000+00:00');assert not todo(p).count();p.clock.fast_forward(1000);assert 'Order ingredients' in todo(p).inner_text();p.clock.fast_forward(24*60*60*1000);assert 'Order ingredients' in todo(p).inner_text();p.clock.fast_forward(3600000+1000);assert not todo(p).count() and not e,e;c.close()
 c,p,e,_=setup(b,name,320,'2026-11-07T07:59:58+00:00');p.evaluate('promotionTest.editor(2)');p.wait_for_timeout(850);p.locator('[data-editor-section="notes"]>summary').tap();p.locator('#toggleRecipeNotes').tap();p.locator('#recipeNotes').fill('Keep this midnight draft');p.clock.fast_forward(3000);assert p.locator('#recipeNotes').input_value()=='Keep this midnight draft' and p.locator('[data-editor-section="notes"]').get_attribute('open') is not None;p.locator('#cancel').tap();assert len(labels(p))==4 and not e,e;c.close()
 print('PASS',name,'25-hour DST day refreshes at local midnight; midnight during meal editing retains draft and section state, then returning shows new-day tasks',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   dates(b,name);schedule_updates(b,name);dst_and_editor_midnight(b,name)
   for width in [320,360]:
    for tabs in [False,True]:checklist(b,name,width,tabs)
  b.close()
