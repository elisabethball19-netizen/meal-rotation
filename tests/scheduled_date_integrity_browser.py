"""Actual scheduled dates, explicit cycle times, cooked events and history integrity."""
import copy,json
from datetime import datetime
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
import outgoing_cooked_dates_browser as f
from scheduled_linked_slots_browser import rows,state,compose
f.EXTRA+='''window.integrityTest={
 create:()=>dateTest.createSchedule(),
 history:()=>readPreviousRotation(),rawHistory:()=>localStorage.getItem(ROTATION_BACK_KEY),
 newPlan:()=>{createMealPlan('New plan');weekdayCategories={Tuesday:['Mains']};saveWeekdayCategories();persist()},
 legacyRestore:()=>{const state=JSON.parse(captureState());state.mealPlans.forEach(p=>{p.id='restored-'+p.id;delete p.rotationCalendar});state.activePlanId='restored-'+state.activePlanId;restoreState(state)},
 noDates:()=>{for(const m of meals)delete m.lastCooked;persist()},
 manual:()=>applyManualWeekdayMeal('Wednesday','Mains',meals.find(m=>m.id===9)),
 manualDate:(id,value)=>{meals.find(m=>m.id===id).lastCooked=value;persist()},
 known:()=>mealPlans.map(p=>({id:p.id,calendar:p.rotationCalendar})),
 date:day=>dateFor(day),
 tabs:value=>{showMealPlanTabs=value;persist();renderList()},plan:id=>loadMealPlan(id),
 staleBucket:()=>{mealPlans.find(p=>p.id===activePlanId).rotationCalendar.weekStart='2026-10-13';meals.find(m=>m.id===2).name='Thai Red Curry Chicken';meals.find(m=>m.id===14).name='Thai Red Curry Chicken';persist()},
 preference:(current,legacy)=>{if(current===null)localStorage.removeItem(ROTATE_MARK_COOKED_KEY);else localStorage.setItem(ROTATE_MARK_COOKED_KEY,current);localStorage.setItem('mealRotationMarkRotatedAsCookedV1',legacy);openRotateOptions()},
 legacyHistory:()=>{const before=JSON.parse(captureState());delete before.lastRotationBefore;for(const p of before.mealPlans)p.rotationCalendar={weekStart:'2026-10-13',occurrences:{}};localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify(before))}
};function dateFor(day){const p=mealPlans.find(p=>p.id===activePlanId),x=getDisplayedWeekdayMealsForPlan(p).find(x=>x.day===day&&x.cat==='Mains');return p.rotationCalendar.occurrences[rotationOccurrenceKey({...x,planId:p.id})]}'''

def create(browser,name,day='2026-10-27',width=360,start='Tuesday',zone='UTC',repeat=False,legacy=False):
 ctx,p,errors,prefix=f.setup(browser,name,width,zone=zone,start=start,repeat=repeat)
 f.clock(p,day,zone)
 if not legacy:p.evaluate('integrityTest.create()')
 return ctx,p,errors,prefix

def cycle(p,days=None,mark=True):
 if days is None:p.evaluate('dateTest.all',mark)
 else:p.evaluate('([days,mark])=>dateTest.cycle(days.map(day=>day+"::Mains"),mark)',[days,mark])
def dates(p):return f.local_dates(p)
def planned(p,day):return p.evaluate('integrityTest.date',day)
def notice(p):
 if p.get_by_role('alertdialog').count():p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).tap()
def check(ctx,p,errors,prefix):
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors;ctx.close()

def date_rules(browser,name,width):
 for kind in ['following','same-day','future','end-week','off','manual','repeat']:
  ctx,p,errors,prefix=create(browser,name,width=width,repeat=kind=='repeat');p.evaluate('integrityTest.noDates()')
  assert planned(p,'Tuesday')=='2026-10-27' and planned(p,'Wednesday')=='2026-10-28'
  before=state(p);old=compose(p)
  if kind=='following':f.clock(p,'2026-11-03');cycle(p,['Tuesday']);assert dates(p)['1']==dates(p)['30']==dates(p)['100']=='2026-10-27' and planned(p,'Tuesday')=='2026-11-03'
  elif kind=='same-day':cycle(p,['Tuesday']);assert dates(p)['1']=='2026-10-27' and planned(p,'Tuesday')=='2026-10-27'
  elif kind=='future':cycle(p,['Wednesday']);assert dates(p)['2'] is None and planned(p,'Wednesday')=='2026-10-28'
  elif kind=='end-week':f.clock(p,'2026-11-02');cycle(p);assert [dates(p)[str(i)] for i in range(1,8)]==['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'];assert planned(p,'Tuesday')=='2026-11-03'
  elif kind=='off':f.clock(p,'2026-11-03');cycle(p,mark=False);assert all(value is None for value in p.evaluate('dateTest.dates()').values())
  elif kind=='manual':p.evaluate('integrityTest.manual()');old=compose(p);before=state(p);assert planned(p,'Wednesday')=='2026-10-28';f.clock(p,'2026-10-28');cycle(p,['Wednesday']);assert dates(p)['9']=='2026-10-28' and dates(p)['2'] is None
  else:f.clock(p,'2026-11-03');cycle(p);assert dates(p)['1']==dates(p)['30']==dates(p)['100']=='2026-10-31'
  if kind!='off':assert not p.get_by_role('alertdialog').count()
  record=p.evaluate('integrityTest.history()');assert record['cycledAt'].startswith('2026-') and 'lastRotationBefore' not in record
  # No recipe that was absent from the outgoing schedule is automatically cooked.
  old_ids={x[3] for x in old}|{30}
  for id,value in dates(p).items():
   if int(id) not in old_ids:assert value is None,(kind,id,value)
  p.evaluate('slotTest.back()');assert compose(p)==old and p.evaluate('dateTest.dates()')=={str(m['id']):None for m in before['meals']}
  check(ctx,p,errors,prefix);print('PASS',name,width,kind,'actual scheduled date, eligibility, no incoming marks, Cycle Back',flush=True)

def history_rules(browser,name,width):
 ctx,p,errors,prefix=create(browser,name,width=width);p.evaluate('integrityTest.noDates()');f.clock(p,'2026-11-03');original=compose(p);cycle(p,['Tuesday']);first=compose(p);first_dates=p.evaluate('dateTest.dates()');first_history=p.evaluate('integrityTest.rawHistory()')
 cycle(p,['Wednesday']);second=compose(p);second_dates=p.evaluate('dateTest.dates()');second_history=p.evaluate('integrityTest.rawHistory()')
 p.get_by_role('button',name='Undo',exact=True).tap();assert compose(p)==first and p.evaluate('dateTest.dates()')==first_dates and p.evaluate('integrityTest.rawHistory()')==first_history
 p.get_by_role('button',name='Redo',exact=True).tap();assert compose(p)==second and p.evaluate('dateTest.dates()')==second_dates and p.evaluate('integrityTest.rawHistory()')==second_history
 p.evaluate('slotTest.back()');assert compose(p)==first and p.evaluate('dateTest.dates()')==first_dates
 p.get_by_role('button',name='Undo',exact=True).tap();assert compose(p)==second and p.evaluate('integrityTest.rawHistory()')==second_history
 p.get_by_role('button',name='Redo',exact=True).tap();assert compose(p)==first
 # Manual cooked-date edits after a rotation are not erased by Cycle Back.
 cycle(p,['Thursday']);p.evaluate('([id,value])=>integrityTest.manualDate(id,value)',[3,'2026-11-03T12:00:00.000Z']);p.evaluate('slotTest.back()');assert dates(p)['3']=='2026-11-03'
 backup=p.evaluate('dateTest.backup()');cal=p.evaluate('integrityTest.known()');p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload();assert p.evaluate('integrityTest.known()')==cal
 check(ctx,p,errors,prefix);print('PASS',name,width,'Undo/Redo restore matching history, no duplicate events, later manual dates, backup/reload',flush=True)
 ctx,p,errors,prefix=create(browser,name,width=width,repeat=True);p.evaluate('integrityTest.noDates()');f.clock(p,'2026-11-03');cycle(p);assert dates(p)['1']=='2026-10-31'
 p.evaluate('slotTest.partial(["original||Saturday::Mains"])');assert dates(p)['1']==dates(p)['30']=='2026-10-27'
 check(ctx,p,errors,prefix);print('PASS',name,width,'partial Cycle Back recalculates shared-recipe dates from remaining legitimate events',flush=True)

def legacy_and_boundaries(browser,name):
 ctx,p,errors,prefix=create(browser,name,legacy=True);p.evaluate('integrityTest.noDates()');f.clock(p,'2026-11-03');cycle(p,['Tuesday']);assert dates(p)['1'] is None
 assert 'no verified calendar date' in p.get_by_role('alertdialog').inner_text();notice(p);assert planned(p,'Tuesday')=='2026-11-03'
 outgoing=next(r['id'] for r in rows(p) if r['planId']=='original' and r['day']=='Tuesday' and r['cat']=='Mains');cycle(p,['Tuesday']);assert dates(p)[str(outgoing)]=='2026-11-03' and planned(p,'Tuesday')=='2026-11-03'
 p.evaluate('integrityTest.legacyHistory()');old=p.evaluate('dateTest.dates()');p.evaluate('slotTest.back()');assert p.evaluate('dateTest.dates()')==old
 check(ctx,p,errors,prefix);print('PASS',name,'legacy unknown dates reported, no week subtraction or historical rewrite, later same-day cycle records correctly',flush=True)
 cases=[('2026-12-29','2027-01-05','Tuesday','2026-12-29','UTC'),('2026-12-27','2027-01-03','Sunday','2026-12-29','UTC'),('2024-02-27','2024-03-05','Tuesday','2024-02-27','UTC'),('2026-03-03','2026-03-10','Tuesday','2026-03-03','America/New_York'),('2026-10-27','2026-11-03','Tuesday','2026-10-27','America/New_York'),('2026-10-27','2026-11-03','Tuesday','2026-10-27','Pacific/Kiritimati')]
 for start,end,weekday,want,zone in cases:
  ctx,p,errors,prefix=create(browser,name,start,start=weekday,zone=zone);p.evaluate('integrityTest.noDates()');f.clock(p,end,zone);cycle(p,['Tuesday']);assert dates(p)['1']==want,(start,end,weekday,zone,dates(p));check(ctx,p,errors,prefix)
 print('PASS',name,'month/year/leap day, different week starts, DST, UTC+14',flush=True)
 ctx,p,errors,prefix=create(browser,name);known=p.evaluate('integrityTest.known()');p.evaluate('integrityTest.tabs',False);p.evaluate("integrityTest.plan('lunch')");p.evaluate('integrityTest.tabs',True);p.evaluate("integrityTest.plan('original')");assert p.evaluate('integrityTest.known()')==known
 check(ctx,p,errors,prefix);print('PASS',name,'tab visibility and navigation preserve scheduled dates',flush=True)

def saved_values(browser,name):
 ctx,p,errors,prefix=create(browser,name);p.evaluate('integrityTest.newPlan()');assert planned(p,'Tuesday')=='2026-10-27';p.evaluate('integrityTest.legacyRestore()');assert all(value is None for plan in p.evaluate('integrityTest.known()') for value in plan['calendar']['occurrences'].values());check(ctx,p,errors,prefix)
 print('PASS',name,'new empty plan dates actual assignments; legacy restored plan IDs never invent historical dates',flush=True)
 ctx,p,errors,prefix=create(browser,name);p.evaluate('integrityTest.noDates()');p.evaluate('integrityTest.staleBucket()');f.clock(p,'2026-11-03');cycle(p,['Wednesday']);assert dates(p)['2']=='2026-10-28' and dates(p)['14'] is None
 p.evaluate('([id,value])=>integrityTest.manualDate(id,value)',[1,'2026-11-03T12:00:00.000Z']);cycle(p,['Tuesday']);assert dates(p)['1']=='2026-11-03'
 for current,want in [('false',False),(None,True)]:
  p.evaluate('([current,legacy])=>integrityTest.preference(current,legacy)',[current,'true']);dialog=p.get_by_role('dialog',name='Rotate out recipes');assert dialog.get_by_role('checkbox').is_checked()==want;dialog.get_by_role('button',name='Close',exact=True).tap()
 check(ctx,p,errors,prefix);print('PASS',name,'actual occurrence date wins over stale week bucket, recipe IDs stay distinct, newer manual dates and explicit marking preference preserved; legacy preference fallback',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:date_rules(b,name,width);history_rules(b,name,width)
   legacy_and_boundaries(b,name);saved_values(b,name)
  b.close()
