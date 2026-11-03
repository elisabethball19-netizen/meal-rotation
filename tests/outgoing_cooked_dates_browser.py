"""Outgoing planning-week cooked dates; synthetic clocks, schedules and storage."""
import copy,json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
from playwright.sync_api import sync_playwright
from scheduled_linked_slots_browser import HOOK,meal,rows,state,compose
ROOT=Path(__file__).resolve().parents[1]
DAYS=['Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday','Monday']
OLD='2020-01-01T12:00:00.000Z'
EXTRA='''window.dateTest={
 createSchedule:()=>window.establishDatedFixtureSchedule(),
 localDates:()=>Object.fromEntries(meals.map(m=>[m.id,m.lastCooked?cookingLocalDate(new Date(m.lastCooked)):null])),
 calendarDate:day=>{const plan=mealPlans.find(p=>p.id===activePlanId),entry=getDisplayedWeekdayMealsForPlan(plan).find(x=>x.day===day&&x.cat==='Mains');return plan.rotationCalendar?.occurrences[rotationOccurrenceKey({...entry,planId:plan.id})]},
 recent:()=>{meals.find(m=>m.id===1).lastCooked='2026-11-03T12:00:00.000Z';persist()},
 dates:()=>Object.fromEntries(meals.map(m=>[m.id,m.lastCooked||null])),
 calendar:()=>mealPlans.map(p=>({id:p.id,calendar:p.rotationCalendar})),
 helper:days=>days.map(day=>{const d=cookedDateForWeekday(day);return d?cookingLocalDate(d):null}),
 all:(mark=true,all=false)=>moveDisplayedMealsToBottom(null,all,mark),
 cycle:(slots,mark=true)=>moveDisplayedMealsToBottom(new Set(slots),false,mark),
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 seed:()=>{for(const source of getGroceryContributions(true))groceryOccurrenceChecks.checks[source.id]=source.day==='Tuesday'||source.planId==='lunch';saveGroceryOccurrenceChecks()},
 otherWeek:()=>{const p=mealPlans.find(p=>p.id==='lunch'),key=rotationOccurrenceKey({planId:p.id,day:'Tuesday',mealId:'50'});p.rotationCalendar={version:2,weekStart:'2026-10-20',occurrences:{[key]:'2026-10-20'},assignedOn:{[key]:'2026-10-20'},assignedAt:{[key]:'2026-10-20T08:00:00.000Z'},slots:{'Tuesday::Lunch::slot':'2026-10-20'}};saveActiveMealPlan()},
 manual:()=>applyManualWeekdayMeal('Tuesday','Mains',meals.find(m=>m.id===9)),
 backup:()=>{const storage=slotBackup.capture();return {version:2,...JSON.parse(storage.mealRotationDataV1),storage}},
 dedup:()=>{const counts={};for(const m of meals.filter(m=>m.linkGroup==='shared-tiger')){let value=m.lastCooked;Object.defineProperty(m,'lastCooked',{enumerable:true,configurable:true,get:()=>value,set:next=>{counts[m.id]=(counts[m.id]||0)+1;value=next}})}const p=mealPlans.find(p=>p.id===activePlanId),item=getDisplayedWeekdayMealsForPlan(p).find(x=>x.day==='Tuesday'&&x.cat==='Mains');recordRotatedMealsCooked([{...item,planId:p.id},{...item,planId:p.id}],new Map([[p.id,p.rotationCalendar]]));return counts}
};'''
def setup(browser,name,width=360,zone='UTC',start='Tuesday',anchor=None,repeat=False):
 library=[meal(i,'Crying Tiger' if i==1 else 'Recipe '+str(i),'Mains',[100] if i==1 else []) for i in range(1,15)]
 library.extend([meal(30,'Shared Tiger copy','Copies'),meal(50,'Lunch recipe','Lunch'),meal(51,'Next lunch','Lunch'),meal(100,'Attached rice','Sides'),meal(101,'Other rice','Sides')])
 for m in library:m['lastCooked']=OLD;m['ingredientStepLinks']=[]
 for m in library:
  if m['id'] in [1,30]:m['linkGroup']='shared-tiger'
 assign={day:['Mains'] for day in DAYS};overrides={day+'::Mains':str(i+1) for i,day in enumerate(DAYS)}
 if repeat:overrides['Saturday::Mains']='1'
 plans=[dict(id='original',name='Dinner',weekdayCategories=assign,weekdayMealOverrides=overrides,cycleRetainedSlots=dict(overrides),cycleSlotChoices={k:{'mealId':v,'parentId':''} for k,v in overrides.items()},weekdayRecipeFilters={},pinnedCats=[]),dict(id='lunch',name='Lunch',weekdayCategories={'Tuesday':['Lunch']},weekdayMealOverrides={'Tuesday::Lunch':'50'},cycleRetainedSlots={'Tuesday::Lunch':'50'},cycleSlotChoices={'Tuesday::Lunch':{'mealId':'50','parentId':''}},weekdayRecipeFilters={},pinnedCats=[])]
 if anchor:plans[0]['rotationCalendar']={'weekStart':anchor,'occurrences':{}}
 prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
 seed={prefix+'mealRotationDataV1':json.dumps({'cats':['Mains','Copies','Lunch','Sides'],'active':'Mains','meals':library}),prefix+'mealRotationPlansV1':json.dumps({'plans':plans,'activeId':'original'}),prefix+'mealRotationStartWeekdayV1':start,prefix+'mealRotationShowPlanTabsV1':'true',prefix+'mealRotationSelectedIngredientsV1':json.dumps({str(m['id']):m['ingredients'] for m in library}),prefix+'mealRotationTutorialStageV1':'done',prefix+'mealRotationCustomSettingV9':'keep',prefix+'mealRotationRecipeViewPrefsV1':json.dumps({'mode':'split','ratio':.4,'keepScreenAwake':False})}
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
 src=(ROOT/name).read_text().replace('function validateBackupCore(d){','window.slotBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+(HOOK+EXTRA).replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,timezone_id=zone);p=ctx.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_default_timeout(8000)
 p.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
 p.route('http://dates.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(name) else r.fulfill(status=200,body=''));p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 p.goto('http://dates.test/'+name);p.evaluate('slotTest.seed()');p.evaluate('dateTest.seed()');return ctx,p,errors,prefix

def clock(p,day,zone='UTC'):p.clock.set_fixed_time(datetime.fromisoformat(day+'T08:00:00').replace(tzinfo=ZoneInfo(zone)))
def establish(p,day='2026-10-27',zone='UTC'):
 clock(p,day,zone);p.evaluate('dateTest.createSchedule()');p.evaluate('slotTest.seed()');p.evaluate('dateTest.seed()')
def local_dates(p):return p.evaluate('dateTest.localDates()')
def calendar_date(p,day):return p.evaluate('dateTest.calendarDate',day)

def week_cases(browser,name):
 cases=[('2026-11-03','Tuesday',None,['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'],'UTC'),('2026-11-04','Tuesday',None,['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'],'UTC'),('2027-01-05','Tuesday',None,['2026-12-29','2026-12-30','2026-12-31','2027-01-01','2027-01-02','2027-01-03','2027-01-04'],'UTC'),('2027-01-01','Friday',None,['2026-12-29','2026-12-30','2026-12-31','2026-12-25','2026-12-26','2026-12-27','2026-12-28'],'UTC'),('2024-03-05','Tuesday',None,['2024-02-27','2024-02-28','2024-02-29','2024-03-01','2024-03-02','2024-03-03','2024-03-04'],'UTC'),('2026-11-01','Tuesday','2026-10-27',['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01',None],'UTC'),('2026-11-05','Tuesday','2026-10-27',['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'],'UTC'),('2026-11-17','Tuesday','2026-10-27',['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'],'UTC'),('2026-11-03','Tuesday',None,['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'],'America/New_York'),('2026-03-10','Tuesday',None,['2026-03-03','2026-03-04','2026-03-05','2026-03-06','2026-03-07','2026-03-08','2026-03-09'],'America/New_York'),('2026-11-03','Tuesday',None,['2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-10-31','2026-11-01','2026-11-02'],'Pacific/Kiritimati')]
 for today,start,anchor,expected,zone in cases:
  results=[]
  for mark in [False,True]:
   ctx,p,errors,prefix=setup(browser,name,zone=zone,start=start,anchor=anchor);establish(p,anchor or expected[DAYS.index(start)],zone);clock(p,today,zone);before=state(p);original_dates=local_dates(p);saved=p.evaluate('slotTest.storage()');assert all(v==OLD for v in p.evaluate('dateTest.dates()').values())
   if today=='2026-11-03' and zone=='UTC' and mark:
    # Reproduce the report through the actual setting and menu.
    p.get_by_role('button',name='Cycle Meals',exact=True).tap();d=p.get_by_role('dialog',name='Rotate out recipes');d.get_by_role('checkbox',name='Mark rotated recipes as cooked',exact=True).check();d.get_by_role('button',name='Rotate out all recipes',exact=True).tap()
   else:p.evaluate('dateTest.all',mark)
   after=state(p);dates=local_dates(p)
   for i,want in enumerate(expected,1):assert dates[str(i)]==(want if mark and want else original_dates[str(i)]),(today,start,anchor,zone,mark,i,dates)
   assert dates['30']==(expected[0] if mark else original_dates['30'])
   assert dates['100']==(expected[0] if mark else original_dates['100']) and dates['50']==original_dates['50']
   if not mark:assert p.evaluate('dateTest.dates()')=={str(m['id']):OLD for m in before['meals']}
   assert all(value<=today for value in dates.values())
   assert saved['mealRotationSelectedIngredientsV1']==p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']
   assert before['prefs']==after['prefs']
   for m in after['meals']:m.pop('lastCooked',None)
   results.append({'state':after,'rows':compose(p),'sources':p.evaluate('dateTest.sources()')})
   if mark:
    p.evaluate('slotTest.back()');assert p.evaluate('dateTest.dates()')=={str(m['id']):OLD for m in before['meals']}
   if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
   assert not errors,errors;ctx.close()
  assert results[0]==results[1],(today,start,zone,'marking changed schedule/groceries/progress/settings')
  print('PASS',name,today,start,anchor or 'explicit schedule',zone,'outgoing dates, no future dates, mark-off preservation, links, identical rotation/grocery/progress results, Cycle Back',flush=True)

def partial_and_reload(browser,name,width):
 ctx,p,errors,prefix=setup(browser,name,width);establish(p);clock(p,'2026-11-03');p.evaluate('dateTest.cycle(["Tuesday::Mains","Wednesday::Mains"])')
 assert local_dates(p)['1']=='2026-10-27' and local_dates(p)['2']=='2026-10-28'
 assert calendar_date(p,'Tuesday')=='2026-11-03' and calendar_date(p,'Wednesday')=='2026-11-04' and calendar_date(p,'Monday')=='2026-11-02'
 saved=p.evaluate('dateTest.calendar()');backup=p.evaluate('dateTest.backup()');p.evaluate('(b)=>slotTest.restore(b)',backup);p.reload();assert p.evaluate('dateTest.calendar()')==saved
 clock(p,'2026-11-10');p.evaluate('slotTest.partial(["original||Tuesday::Mains"])');assert calendar_date(p,'Tuesday')=='2026-10-27' and calendar_date(p,'Wednesday')=='2026-11-04'
 p.evaluate('dateTest.cycle(["Tuesday::Mains","Wednesday::Mains"])');dates=local_dates(p);assert dates['1']=='2026-10-27' and dates['9']=='2026-11-04',dates
 assert calendar_date(p,'Monday')=='2026-11-02'
 # Retained old occurrences keep their real date after missed weeks and reloads.
 p.reload();clock(p,'2026-12-01');p.evaluate('dateTest.cycle(["Monday::Mains"])');assert local_dates(p)['7']=='2026-11-02'
 assert not errors,errors;ctx.close();print('PASS',name,width,'partial rotations, mixed outgoing weeks, full backup/reload, partial Cycle Back, missed weeks',flush=True)

def protections(browser,name,width):
 ctx,p,errors,_=setup(browser,name,width);establish(p);clock(p,'2026-11-03')
 p.evaluate('dateTest.recent()');p.reload();clock(p,'2026-11-03');assert local_dates(p)['1']=='2026-11-03'
 p.evaluate('dateTest.cycle(["Tuesday::Mains"])');assert local_dates(p)['1']=='2026-11-03' and local_dates(p)['30']=='2026-10-27'
 old=p.evaluate('dateTest.dates()');p.evaluate('dateTest.manual()');assert p.evaluate('dateTest.dates()')==old
 clock(p,'2026-11-10');p.evaluate('dateTest.cycle(["Tuesday::Mains"])');assert local_dates(p)['9']=='2026-11-03'
 assert not errors,errors;ctx.close()
 ctx,p,errors,_=setup(browser,name,width,anchor='2026-11-10');establish(p,'2026-11-03');p.evaluate('dateTest.all',False);p.evaluate('dateTest.all()');assert all(v==OLD for v in p.evaluate('dateTest.dates()').values());assert not errors,errors;ctx.close()
 ctx,p,errors,_=setup(browser,name,width,repeat=True);establish(p);clock(p,'2026-11-03');p.evaluate('dateTest.all()');assert local_dates(p)['1']==local_dates(p)['30']==local_dates(p)['100']=='2026-10-31';assert not errors,errors;ctx.close()
 ctx,p,errors,_=setup(browser,name,width);establish(p);clock(p,'2026-11-03');counts=p.evaluate('dateTest.dedup()');assert counts=={'1':1,'30':1},counts;assert local_dates(p)['1']==local_dates(p)['30']=='2026-10-27';assert not errors,errors;ctx.close()
 print('PASS',name,width,'later manual dates retained, individual changes do not mark cooked, future dates skipped, repeated/shared/linked recipes deduplicated',flush=True)

def all_tabs(browser,name):
 ctx,p,errors,_=setup(browser,name);establish(p);clock(p,'2026-11-03');p.evaluate('dateTest.otherWeek()');before=compose(p);p.evaluate('(args)=>dateTest.all(...args)',[True,True]);dates=local_dates(p)
 assert dates['1']=='2026-10-27' and dates['50']=='2026-10-20'
 p.evaluate('slotTest.back()');assert compose(p)==before and all(v==OLD for v in p.evaluate('dateTest.dates()').values())
 assert not errors,errors;ctx.close();print('PASS',name,'all-plan rotation respects independent stored outgoing weeks; Cycle Back restores dates and schedule',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   week_cases(b,name);all_tabs(b,name)
   for width in [320,360]:partial_and_reload(b,name,width);protections(b,name,width)
  b.close()
