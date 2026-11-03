"""Immediate section moves, temporary promotion ranking and occurrence-safe demotion."""
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose,context_key
f.EXTRA+='''window.sectionTest={
 occasional:()=>applyManualWeekdayMeal('Monday',null,meals.find(m=>m.id===1),null,true),
 manual:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()},
 date:id=>{meals.find(m=>m.id===id).lastCooked='2030-01-01T12:00:00.000Z';persist()},
 configure:mode=>{if(mode==='only')for(const m of meals)if([2,3,4].includes(m.id))m.rotation=false;if(mode==='attached'){weekdayCategories.Saturday=['Weekend'];const p=mealPlans.find(p=>p.id===activePlanId);delete weekdayMealOverrides['Saturday::Sides'];delete p.cycleRetainedSlots['Saturday::Sides'];delete p.cycleSlotChoices['Saturday::Sides']}persist();saveActiveMealPlan();renderList()},
 back:()=>rotateAllBack(),partial:key=>rotateSelectedBack([key]),
 backup:()=>slotBackup.capture(),restore:storage=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage}));backupRestoreReloadPending=true}
};'''
def ids(p):return f.group_rows(p).evaluate_all('(es)=>es.map(e=>Number(e.dataset.mealId))')
def groups(p):p.evaluate('promotionTest.groups()')
def move(p,id):
 groups(p);p.locator('#list .master-category-meal[data-meal-id="'+str(id)+'"] .recipe-section-move').tap();assert not p.get_by_role('dialog').count() and not p.get_by_role('alertdialog').count()
def consistent(p):
 groups(p);expected=ids(p);p.evaluate("promotionTest.chooser('Saturday','Weekend')");d=p.locator('.weekday-meal-picker');toggle=d.locator('[data-group=Weekend] .master-category-title')
 if toggle.get_attribute('aria-expanded')=='false':toggle.tap()
 assert d.locator('[data-group=Weekend] .weekday-meal-choice').evaluate_all('(es)=>es.map(e=>Number(e.dataset.mealId))')==expected
 d.get_by_role('button',name='Cancel',exact=True).tap()
def check(c,p,e,prefix):
 assert not e,e;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert p.locator('#list .master-category-meal .check').count()==0
 assert p.locator('#list .recipe-section-move').evaluate_all('(es)=>es.every(e=>e.getBoundingClientRect().width>=44&&e.getBoundingClientRect().height>=44)')
 assert p.locator('#list .master-category-meal').evaluate_all('(rows)=>rows.every(e=>!e.querySelector(".master-meal-weekdays")||e.querySelector(".master-meal-weekdays").previousElementSibling.matches(".recipe-section-move"))')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()
def promotion(b,name,w,mode):
 c,p,e,prefix=f.setup(b,name,w,mode);p.evaluate('sectionTest.date(5)');before=state(p);schedule=compose(p);old=f.sources(p);move(p,5)
 expected_day='Sunday' if mode=='first-manual' else 'Saturday'
 if mode not in ['all-manual','no-days']:assert f.pick(p,expected_day)['id']==5
 else:assert compose(p)==schedule
 assert ids(p).index(5)==(2 if mode=='all-manual' else 1 if mode=='first-manual' else 0),(mode,ids(p))
 assert state(p)['meals'][next(i for i,m in enumerate(state(p)['meals']) if m['id']==5)]['lastCooked']=='2030-01-01T12:00:00.000Z'
 f.stable_sources(old,f.sources(p));consistent(p)
 marker=next(m for m in state(p)['meals'] if m['id']==5)['rotationPromotionPriority'];p.reload();groups(p);assert next(m for m in state(p)['meals'] if m['id']==5)['rotationPromotionPriority']==marker;consistent(p)
 automatic=ids(p);p.evaluate('sectionTest.manual(true)');assert ids(p)[0]==5 and f.group_rows(p).locator('.move').count()>0
 p.evaluate('sectionTest.manual(false)');assert ids(p)==automatic and f.group_rows(p).locator('.move').count()==0
 old=compose(p);p.evaluate('promotionTest.full()');groups(p);assert all('rotationPromotionPriority' not in m for m in state(p)['meals']);consistent(p)
 p.evaluate('sectionTest.back()');groups(p);assert compose(p)==old and next(m for m in state(p)['meals'] if m['id']==5)['rotationPromotionPriority']==marker;consistent(p)
 check(c,p,e,prefix);print('PASS',name,w,mode,'promotion, manual protection, future cooked-date ranking, reload, both modes, cycle expiry/Back',flush=True)

def demotion(b,name,w,mode):
 base='linked' if mode in ['linked','attached','protected-side'] else 'cross-group' if mode=='cross-group' else 'multiple'
 c,p,e,prefix=f.setup(b,name,w,base)
 if mode=='occasional':p.evaluate('sectionTest.occasional()')
 if mode=='repeat':p.evaluate("promotionTest.manual('Sunday','Weekend',1)");p.evaluate("promotionTest.plan('lunch')");p.evaluate("promotionTest.manual('Friday','Weekend',1)");p.evaluate("promotionTest.plan('original')")
 if mode in ['linked','attached','protected-side']:
  if mode=='attached':p.evaluate("sectionTest.configure('attached')")
  if mode=='protected-side':p.evaluate("promotionTest.manual('Saturday','Sides',20)")
  move(p,5)
 if mode=='only':p.evaluate("sectionTest.configure('only')")
 id=21 if mode in ['linked','attached'] else 3 if mode=='cross-group' else 5 if mode=='protected-side' else 1
 p.evaluate('slotTest.seed()');before=state(p);prior=f.rows(p);old=f.sources(p);date=next(m for m in before['meals'] if m['id']==id).get('lastCooked');move(p,id);now=state(p);current=f.rows(p)
 assert not any(r['id']==id for r in current),(mode,current)
 assert not next(m for m in now['meals'] if m['id']==id)['rotation'] and next(m for m in now['meals'] if m['id']==id).get('lastCooked')==date
 for r in prior:
  affected=r['id']==id or r['parent']==str(id)
  if not affected:
   assert r in current,(mode,r,current)
   k=context_key(r);assert before['sessions']['occurrences'][k]==now['sessions']['occurrences'][k] and before['scales']['occurrences'][k]==now['scales']['occurrences'][k]
 assert [p['weekdayCategories'] for p in before['plans']]==[p['weekdayCategories'] for p in now['plans']]
 for m in now['meals']:
  previous=next(x for x in before['meals'] if x['id']==m['id']);expected={**previous}
  if m['id']==id:expected['rotation']=False;expected.pop('rotationPromotionPriority',None)
  assert m==expected
 f.stable_sources(old,f.sources(p));consistent(p)
 if mode=='only':assert not any(r['cat']=='Weekend' for r in current)
 if mode=='cross-group':assert f.pick(p,'Wednesday','Mains')['id'] in [10,11,12]
 saved=compose(p);sources=f.sources(p);p.reload();groups(p);assert compose(p)==saved and f.sources(p)==sources
 backup=p.evaluate('sectionTest.backup()');p.evaluate('sectionTest.restore',backup);p.reload();groups(p);assert compose(p)==saved
 # Opposite arrow promotes immediately without changing recipe definitions/links.
 move(p,id);assert next(m for m in state(p)['meals'] if m['id']==id)['rotation'];consistent(p)
 if name.startswith('meal-') and w==320 and mode=='normal':p.screenshot(path='/tmp/section-move-mobile.png')
 check(c,p,e,prefix);print('PASS',name,w,mode,'demotion/replacements/empty slots, links and repeated tabs, unchanged unrelated progress/groceries/dates/definitions, reload/backup and reverse arrow',flush=True)
def multiple_priorities(b,name):
 c,p,e,prefix=f.setup(b,name,320,'cross-group');move(p,5);move(p,6);assert ids(p)[:3]==[3,6,5];old=state(p);schedule=compose(p)
 p.evaluate('slotTest.cycle(["Saturday::Weekend"])');groups(p);assert all('rotationPromotionPriority' not in m for m in state(p)['meals'])
 p.evaluate('sectionTest.partial("original||Saturday::Weekend")');groups(p);assert compose(p)==schedule and next(m for m in state(p)['meals'] if m['id']==6)['rotationPromotionPriority']==next(m for m in old['meals'] if m['id']==6)['rotationPromotionPriority'];consistent(p)
 saved=state(p);schedule=compose(p);move(p,6);p.get_by_role('button',name='Undo',exact=True).tap();groups(p);assert compose(p)==schedule and state(p)['meals']==saved['meals'];consistent(p)
 p.get_by_role('button',name='Redo',exact=True).tap();groups(p);assert not next(m for m in state(p)['meals'] if m['id']==6)['rotation'];consistent(p)
 check(c,p,e,prefix);print('PASS',name,'successive promotions below manual choices, partial-cycle priority expiry/Back, demotion Undo/Redo',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   multiple_priorities(b,name)
   for w in [320,360]:
    for mode in ['single','multiple','first-manual','all-manual','no-days']:promotion(b,name,w,mode)
    for mode in ['normal','repeat','occasional','cross-group','linked','attached','protected-side','only']:demotion(b,name,w,mode)
  b.close()
