"""Explicit tasks, real calendar boundaries, per-occurrence completion and editor drafts."""
import copy
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
from editor_sections_fixture import open_editor_section
f.EXTRA+='''window.prepTest={
 seed:()=>{const meal=meals.find(m=>m.id===2);meal.makeAheadTasks=[{id:'marinate',description:'Marinate pork',daysBefore:1},{id:'dough',description:'Prepare dough',daysBefore:2},{id:'same',description:'Chop herbs',daysBefore:0},{id:'early',description:'Order ingredients',daysBefore:7}];meal.marinate='120';startWeekday='Tuesday';localStorage.setItem('mealRotationStartWeekdayV1',startWeekday);for(const plan of mealPlans){const entries=getDisplayedWeekdayMealsForPlan(plan),calendar={version:2,weekStart:'2026-11-03',occurrences:{},assignedOn:{},assignedAt:{},slots:{}};for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:plan.id}),date=cookingLocalDate(cookingDateInWeek(entry.day,new Date(2026,10,3)));calendar.occurrences[key]=date;calendar.assignedOn[key]='2026-11-03';calendar.assignedAt[key]='2026-11-03T08:00:00.000Z';calendar.slots[rotationCalendarSlot(entry)]=date}plan.rotationCalendar=calendar}persist();saveActiveMealPlan();},
 overview:()=>{showTop=true;allMealsActive=true;groceryTabActive=false;render()},
 rows:()=>scheduledMakeAheadTasks().map(x=>({description:x.task.description,due:x.due,key:x.key,complete:x.complete,day:x.entry.day,id:x.entry.meal.id})),
 back:rotateAllBack,cycle:()=>moveDisplayedMealsToBottom(null,false,false),
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
f.EXTRA+="""prepTest.boundary=(start,day)=>{prepTest.seed();startWeekday=day;for(const plan of mealPlans){const entries=getDisplayedWeekdayMealsForPlan(plan),calendar={version:2,weekStart:start,occurrences:{},assignedOn:{},assignedAt:{},slots:{}};for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:plan.id}),date=cookingLocalDate(cookingDateInWeek(entry.day,parseCookingLocalDate(start)));calendar.occurrences[key]=date;calendar.assignedOn[key]=start;calendar.assignedAt[key]=start+'T08:00:00.000Z';calendar.slots[rotationCalendarSlot(entry)]=date}plan.rotationCalendar=calendar}persist();saveActiveMealPlan()};"""
def boundaries(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple')
 for start,day,expected in [('2026-12-29','Tuesday','2027-01-02'),('2026-12-27','Sunday','2026-12-26'),('2027-01-04','Monday','2027-01-09')]:
  p.evaluate('([s,d])=>prepTest.boundary(s,d)',[start,day]);p.evaluate('prepTest.overview()');row=next(x for x in p.evaluate('prepTest.rows()') if x['description']=='Marinate pork');assert row['due']==expected,(start,day,row)
  if expected<start:assert p.locator('.make-ahead-outside').get_by_role('checkbox',name="Marinate pork · for Sunday's Spaghetti",exact=True).count()==1
 assert not errors,errors;print('PASS',name,'Tuesday/Sunday/Monday start, month/year boundary and pre-week reminders',flush=True);c.close()
def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');p.clock.install(time=datetime(2026,11,3,8,tzinfo=timezone.utc));p.evaluate('prepTest.seed()');p.evaluate('promotionTest.check()');p.evaluate('prepTest.overview()')
 rows=p.evaluate('prepTest.rows()');by={r['description']:r for r in rows}
 assert by['Marinate pork']['due']=='2026-11-07' and by['Prepare dough']['due']=='2026-11-06' and by['Chop herbs']['due']=='2026-11-08' and by['Order ingredients']['due']=='2026-11-01'
 cards=p.locator('.all-meals-day');sat=cards.filter(has=p.get_by_role('heading',name='Saturday',exact=True));sun=cards.filter(has=p.get_by_role('heading',name='Sunday',exact=True))
 assert sat.get_by_role('checkbox',name="Marinate pork · for Sunday's Spaghetti",exact=True).count()==1
 assert not sun.get_by_role('checkbox',name="Order ingredients · for Sunday's Spaghetti",exact=True).count()
 assert p.locator('.make-ahead-outside').get_by_text('2026-11-01 · Dinner',exact=True).count()==1
 before=copy.deepcopy(state(p));schedule=compose(p);groceries=f.sources(p)
 sat.get_by_role('checkbox').check();assert p.locator('.make-ahead-complete').count()==1 and state(p)['meals']==before['meals'] and compose(p)==schedule and f.sources(p)==groceries
 backup=p.evaluate('prepTest.backup()');p.reload();p.evaluate('prepTest.overview()');assert p.locator('.make-ahead-complete').count()==1
 old_key=next(x['key'] for x in p.evaluate('prepTest.rows()') if x['complete'])
 p.evaluate('prepTest.cycle()');p.evaluate('prepTest.overview()');assert not any(x['id']==2 for x in p.evaluate('prepTest.rows()'))
 p.evaluate('prepTest.back()');p.evaluate('prepTest.overview()');assert next(x for x in p.evaluate('prepTest.rows()') if x['key']==old_key)['complete']
 p.evaluate('prepTest.cycle()')
 for _ in range(6):
  p.evaluate('prepTest.cycle()')
  current=[x for x in p.evaluate('prepTest.rows()') if x['id']==2]
  if current:
   assert all(not x['complete'] and x['key']!=old_key for x in current);break
 else:raise AssertionError('Recipe did not return for future-occurrence completion test')
 p.evaluate('storage=>prepTest.restore(storage)',backup);p.reload();p.evaluate('prepTest.overview()');assert p.locator('.make-ahead-complete').count()==1
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'date offsets/multiple tasks/before-week placement, per-occurrence checks/reload/backup/Cycle Back/new rotations; unchanged recipe/grocery data on completion',flush=True);c.close()
def editor(b,name):
 c,p,errors,_=f.setup(b,name,360,'multiple');p.evaluate('prepTest.seed()');before=copy.deepcopy(state(p));p.evaluate('promotionTest.editor(2)');p.wait_for_timeout(850);open_editor_section(p,'notes')
 box=p.locator('#recipeMakeAhead');box.locator('summary').tap();assert box.get_by_role('textbox',name='Preparation task',exact=True).count()==4
 box.get_by_role('button',name='Add preparation task',exact=True).last.tap();box.get_by_role('textbox',name='Preparation task',exact=True).last.fill('Thaw chicken')
 box.locator('.make-ahead-task-editor').last.get_by_role('button',name='Days',exact=True).click();box.get_by_role('spinbutton',name='Preparation lead time',exact=True).last.fill('3')
 p.locator('#save').tap();after=state(p);m=next(m for m in after['meals'] if m['id']==2);assert m['makeAheadTasks'][-1]['daysBefore']==3 and m['marinate']=='120'
 p.evaluate('promotionTest.editor(2)');p.wait_for_timeout(850);open_editor_section(p,'notes');p.locator('#recipeMakeAhead').evaluate('(e)=>e.open=true');p.get_by_role('textbox',name='Preparation task',exact=True).last.fill('Discard change');p.locator('#cancel').tap();assert state(p)['meals']==after['meals']
 assert not errors,errors
 print('PASS',name,'existing editor task add/custom timing/save/cancel and marinate preservation',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   boundaries(b,name);editor(b,name)
   for width in [320,360]:run(b,name,width)
  b.close()

