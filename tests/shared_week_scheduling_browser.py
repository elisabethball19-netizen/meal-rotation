"""Whole-week allocation, recent-date promotion and scheduled-first display."""
import sys,tempfile,subprocess,random
from pathlib import Path
from playwright.sync_api import sync_playwright
from section_visibility_fixture import reveal_recipe
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose,context_key
ROOT=Path(__file__).resolve().parents[1]
f.EXTRA+='''window.sharedTest={
 allocate:inputs=>inputs.map(x=>[...allocateScheduledWeek(x.library,['G'],x.plans,x.days).values()].flat().map(e=>({day:e.day,id:e.meal.id}))),
 constrained:()=>{for(const m of meals)if(m.cat==='Weekend'){m.rotation=[1,2].includes(m.id);m.labels=m.id===1?['Pork']:['Beef'];delete m.lastCooked}persist();renderList()},
 dates:()=>{meals.find(m=>m.id===1).lastCooked='2026-10-20T12:00:00.000Z';meals.find(m=>m.id===2).lastCooked='2026-10-30T12:00:00.000Z';persist();renderList()},
 duplicate:()=>{const p=mealPlans.find(p=>p.id===activePlanId);weekdayMealOverrides['Sunday::Weekend']='1';p.cycleRetainedSlots['Sunday::Weekend']='1';p.cycleSlotChoices['Sunday::Weekend']={mealId:'1',parentId:''};saveWeekdayMealOverrides();persist();renderList()},
 assign:(day,groups)=>setDayCategories(day,groups),
 last:(id,date)=>{const m=meals.find(m=>m.id===id);if(date===null)delete m.lastCooked;else m.lastCooked=date;persist();renderList()},
 manualMode:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()},
 order:cat=>masterRecipeOrder(cat).map(m=>m.id),
 library:()=>meals,
 choices:()=>mealPlans,
 reset:()=>{weekdayCategories={};weekdayMealOverrides={};for(const p of mealPlans){p.weekdayCategories={};p.weekdayMealOverrides={};p.cycleRetainedSlots={};p.cycleSlotChoices={}}saveActiveMealPlan();persist();renderList()},
 filters:(day,cat,labels)=>{weekdayRecipeFilters[weekdaySlotKey(day,cat)]=labels;saveWeekdayRecipeFilters();setDayCategories(day,getDayCategories(day))},
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
def setup(b,name,w=360,mode='cross-group',tabs=True):
 c,p,e,prefix=f.setup(b,name,w,mode,tabs);return c,p,e,prefix
def pick(p,day,plan='original',cat='Weekend'):return next((r for r in f.rows(p) if r['planId']==plan and r['day']==day and r['cat']==cat),None)
def assign(p,day,groups=['Weekend']):p.evaluate('([day,groups])=>sharedTest.assign(day,groups)',[day,groups])
def move(p,id):
 p.evaluate('promotionTest.groups()');reveal_recipe(p,id).locator('.recipe-section-move').tap();assert not p.get_by_role('dialog').count()
def order(p):return p.evaluate("sharedTest.order('Weekend')")
def chooser(p):
 p.evaluate('promotionTest.groups()');expected=order(p);p.evaluate("promotionTest.chooser('Saturday','Weekend')");d=p.locator('.weekday-meal-picker');t=d.locator('[data-group=Weekend] .master-category-title')
 if t.get_attribute('aria-expanded')=='false':t.tap()
 assert d.locator('[data-group=Weekend] .weekday-meal-choice').evaluate_all('(es)=>es.map(e=>Number(e.dataset.mealId))')==expected;d.get_by_role('button',name='Cancel',exact=True).tap()
def check(c,p,e,prefix):
 assert not e,e;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()
def baseline(b):
 for name in ['index.html','meal-rotation-test.html']:
  c,p,e,pr=setup(b,name);p.evaluate('sharedTest.dates()');move(p,5);assert pick(p,'Saturday')['id']==5 and pick(p,'Sunday')['id']==2;move(p,6);assert pick(p,'Saturday')['id']==6 and not any(r['id']==5 for r in f.rows(p));check(c,p,e,pr)
  c,p,e,pr=setup(b,name,mode='multiple');p.evaluate('sharedTest.duplicate()');assert pick(p,'Saturday')['id']==pick(p,'Sunday')['id']==1;check(c,p,e,pr)
  c,p,e,pr=setup(b,name,mode='multiple');assign(p,'Thursday');assert pick(p,'Thursday')['id']==pick(p,'Saturday')['id']==1;check(c,p,e,pr)
  print('REPRODUCED',name,'first-day replacement, repeatedly displaced promotion, stale auto-pin duplicates, newly assigned day stealing an existing recipe',flush=True)
def promotion_rules(b,name,w,kind):
 mode=kind if kind in ['single','first-manual','all-manual','no-days','already-scheduled'] else 'cross-group'
 c,p,e,pr=setup(b,name,w,mode);p.evaluate('sharedTest.dates()');p.evaluate("promotionTest.start('Tuesday')")
 if kind=='same-date':p.evaluate('([id,date])=>sharedTest.last(id,date)',[2,'2026-10-20T20:00:00.000Z'])
 if kind in ['one-unknown','all-unknown','future']:
  p.evaluate('([id,date])=>sharedTest.last(id,date)',[1,None if kind!='future' else '2026-11-10T12:00:00.000Z'])
  if kind=='all-unknown':p.evaluate('([id,date])=>sharedTest.last(id,date)',[2,None])
 if kind=='Sunday':p.evaluate("promotionTest.start('Sunday')");p.evaluate('([id,date])=>sharedTest.last(id,date)',[2,'2026-10-20T20:00:00.000Z'])
 if kind=='other-tab':p.evaluate("promotionTest.plan('lunch')");p.evaluate("promotionTest.manual('Friday','Weekend',5)");p.evaluate("promotionTest.plan('original')")
 before=state(p);schedule=compose(p);old=f.sources(p);move(p,5);now=state(p)
 if kind in ['all-manual','no-days','already-scheduled','other-tab']:assert compose(p)==schedule
 else:
  day='Saturday' if kind in ['single','same-date','all-unknown'] else 'Sunday';assert pick(p,day)['id']==5,(kind,f.rows(p))
 assert not any(m.get('lastCooked')!=next(x for x in before['meals'] if x['id']==m['id']).get('lastCooked') for m in now['meals'])
 if kind not in ['all-manual','no-days']:assert sum(r['id']==5 for r in f.rows(p))==1
 for r in f.rows(p):
  if r['id']!=5 and any(x[0]==r['planId'] and x[1]==r['day'] and x[2]==r['cat'] and x[3]==r['id'] and x[4]==r['parent'] for x in schedule):
   key=context_key(r);assert now['sessions']['occurrences'].get(key)==before['sessions']['occurrences'].get(key)
 f.stable_sources(old,f.sources(p));chooser(p)
 if kind=='recent':
  move(p,6);assert pick(p,'Sunday')['id']==5 and pick(p,'Saturday')['id']==6 and pick(p,'Wednesday',cat='Mains')['id']==3
  f.stable_sources(old,f.sources(p));chooser(p)
 saved=compose(p);prior_order=order(p);p.reload();assert compose(p)==saved and order(p)==prior_order;chooser(p)
 check(c,p,e,pr);print('PASS',name,w,kind,'recent verified date replacement, never-cooked/manual protection, no extra copies, unchanged dates/progress/groceries, reload/chooser',flush=True)

def duplicate_rules(b,name,w,tabs):
 c,p,e,pr=setup(b,name,w,mode='multiple',tabs=tabs);p.evaluate('sharedTest.dates()');p.evaluate('sharedTest.reset()')
 assign(p,'Saturday');assert pick(p,'Saturday')['id']==3
 assign(p,'Sunday');assert pick(p,'Saturday')['id']==3 and pick(p,'Sunday')['id']==4
 old=compose(p);old_sources=f.sources(p);assign(p,'Thursday');assert pick(p,'Thursday')['id']==1 and all(r in compose(p) for r in old)
 assign(p,'Friday');assert pick(p,'Friday')['id']==2
 assert len({r['id'] for r in f.rows(p)})==4
 # Date and display changes do not silently reschedule established choices.
 old=compose(p);raw=p.evaluate("promotionTest.order('Weekend')");p.evaluate('([id,date])=>sharedTest.last(id,date)',[3,'2026-11-01T12:00:00.000Z']);p.evaluate('sharedTest.manualMode',True);p.evaluate('sharedTest.manualMode',False);assert compose(p)==old and p.evaluate("promotionTest.order('Weekend')")==raw
 p.evaluate("promotionTest.plan('lunch')");assign(p,'Tuesday');assert pick(p,'Tuesday','lunch')['id'] in [1,2,3,4];assert all(r in compose(p) for r in old)
 # Explicit manual duplicates remain two independent occurrences and keep source checks.
 p.evaluate("promotionTest.plan('original')");p.evaluate("promotionTest.manual('Friday','Weekend',3)");assert pick(p,'Saturday')['id']==pick(p,'Friday')['id']==3
 old=compose(p);assign(p,'Monday');assert all(r in compose(p) for r in old)
 f.stable_sources(old_sources,f.sources(p));saved=compose(p);p.reload();assert compose(p)==saved;chooser(p)
 p.evaluate('promotionTest.validate()');backup=p.evaluate('sharedTest.backup()');p.evaluate('sharedTest.restore',backup);p.reload();assert compose(p)==saved
 check(c,p,e,pr);print('PASS',name,w,'tabs',tabs,'2/3/4/5+ slots, never-cooked/oldest allocation, new earlier weekday stable, cross-tab shortage fallback, manual duplicates, date/mode/reload/backup stability',flush=True)

def stale_and_order(b,name,w):
 c,p,e,pr=setup(b,name,w,mode='multiple');p.evaluate('sharedTest.duplicate()');assert pick(p,'Saturday')['id']!=pick(p,'Sunday')['id'];check(c,p,e,pr)
 c,p,e,pr=setup(b,name,w);move(p,5);move(p,6);assert pick(p,'Saturday')['id']==6 and pick(p,'Sunday')['id']==2
 scheduled={r['id'] for r in f.rows(p) if any(m['id']==r['id'] and m['cat']=='Weekend' for m in state(p)['meals'])};shown=order(p);assert set(shown[:len(scheduled)])==scheduled and shown.index(5)>=len(scheduled),(shown,scheduled);assert shown[0]==3;chooser(p)
 before=compose(p);p.evaluate('promotionTest.full()');assert not any(choice.get('substitution') for plan in state(p)['plans'] for choice in plan.get('cycleSlotChoices',{}).values());p.evaluate('slotTest.back()');assert compose(p)==before;chooser(p)
 # The arrow ink moves only inside highlighted rows; hit targets and badges stay in place.
 p.evaluate('promotionTest.groups()');assert p.locator('#list .master-category-meal').evaluate_all("rows=>rows.every(row=>getComputedStyle(row.querySelector('.recipe-section-move svg')).transform===(row.classList.contains('featured-top-meal')?'matrix(1, 0, 0, 1, 5, 0)':'none'))")
 check(c,p,e,pr);print('PASS',name,w,'stale auto duplicates repaired; scheduled rows contiguous before unscheduled promotions; manual-first/weekday tiers; cycle expiry/Back; highlighted-only arrow inset',flush=True)

def constrained_filters(b,name):
 for manual in [False,True]:
  c,p,e,pr=setup(b,name);p.evaluate('sharedTest.reset()');p.evaluate('sharedTest.constrained()');assign(p,'Thursday');assert pick(p,'Thursday')['id']==1
  if manual:p.evaluate("promotionTest.manual('Thursday','Weekend',1)")
  p.evaluate("sharedTest.filters('Friday','Weekend',['Pork'])");assign(p,'Friday')
  assert pick(p,'Friday')['id']==1 and pick(p,'Thursday')['id']==(1 if manual else 2),(manual,f.rows(p))
  saved=compose(p);p.reload();assert compose(p)==saved;check(c,p,e,pr)
 print('PASS',name,'overlapping filters reallocate only when necessary; manual choices never moved; repeats only when protection prevents a distinct assignment',flush=True)

def allocation_graphs(b,name):
 rng=random.Random(19);inputs=[];expected=[]
 for case in range(300):
  count=rng.randint(1,5);days=['Tuesday','Wednesday','Thursday','Friday','Saturday'][:count];library=[{'id':i,'name':str(i),'cat':'G','rotation':True,'labels':[]} for i in range(1,rng.randint(2,5)+1)];possibles=[];fixed={};plans=[dict(id='a',weekdayCategories={},weekdayMealOverrides={},cycleSlotChoices={}),dict(id='b',weekdayCategories={},weekdayMealOverrides={},cycleSlotChoices={})]
  for i,day in enumerate(days):
   eligible=[m for m in library if rng.random()<.55] or [rng.choice(library)];label='slot'+str(i)
   for meal in eligible:meal['labels'].append(label)
   plan=plans[i%2];plan['weekdayCategories'][day]=['G'];plan.setdefault('weekdayRecipeFilters',{})[day+'::G']=[label];possibles.append([m['id'] for m in eligible])
   if rng.random()<.7:
    id=rng.choice(eligible)['id'];plan['weekdayMealOverrides'][day+'::G']=str(id);manual=rng.random()<.25;plan['cycleSlotChoices'][day+'::G']={'mealId':str(id),'substitution':manual}
    if manual:fixed[day]=id
  def maximum(i,used):
   if i==count:return len(used)
   return max(maximum(i+1,used|{id}) for id in ([fixed[days[i]]] if days[i] in fixed else possibles[i]))
  expected.append((maximum(0,set()),possibles,fixed));inputs.append(dict(library=library,plans=plans,days=days))
 c,p,e,pr=setup(b,name);actual=p.evaluate('sharedTest.allocate',inputs)
 for x,result,(maximum,possible,fixed) in zip(inputs,actual,expected):
  assert len(result)==len(x['days'])
  for entry in result:assert entry['id'] in possible[x['days'].index(entry['day'])] and (entry['day'] not in fixed or entry['id']==fixed[entry['day']])
  assert len({entry['id'] for entry in result})==maximum,(x,result,maximum)
 check(c,p,e,pr);print('PASS',name,'300 deterministic allocation graphs: maximum distinct eligible recipes across tabs, arbitrary overlapping filters and protected manual choices',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  if '--baseline' in sys.argv:
   with tempfile.TemporaryDirectory() as tmp:
    for name in ['index.html','meal-rotation-test.html']:Path(tmp,name).write_text(subprocess.check_output(['git','show','6354fa874089acbcbce32cee205846f902b5df61:'+name],cwd=ROOT,text=True))
    f.ROOT=Path(tmp);baseline(b)
  if '--baseline' not in sys.argv:
   for name in ['index.html','meal-rotation-test.html']:
    allocation_graphs(b,name)
    constrained_filters(b,name)
    for w in [320,360]:
     for kind in ['single','recent','first-manual','all-manual','no-days','already-scheduled','other-tab','one-unknown','all-unknown','same-date','Sunday','future']:promotion_rules(b,name,w,kind)
     for tabs in [True,False]:duplicate_rules(b,name,w,tabs)
     stale_and_order(b,name,w)
  b.close()
