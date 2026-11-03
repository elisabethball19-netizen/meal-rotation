"""Display-only automatic order and reversible manual mode, in isolated mobile storage."""
import json
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.orderTest={
 configure:()=>{startWeekday='Tuesday';localStorage.setItem('mealRotationStartWeekdayV1',startWeekday);for(const [id,name,date] of [[30,'Zulu',null],[31,'Alpha',null],[32,'Cooked newer','2020-01-01T12:00:00.000Z'],[33,'Cooked older','2019-01-01T12:00:00.000Z'],[34,'Beta','invalid']])meals.push({...JSON.parse(JSON.stringify(meals[0])),id,name,lastCooked:date,linkedMealIds:[]});meals.find(m=>m.id===1).lastCooked='2030-01-01T12:00:00.000Z';persist();renderList()},
 raw:cat=>[...meals.filter(m=>m.cat===cat&&m.rotation),...meals.filter(m=>m.cat===cat&&!m.rotation)].map(m=>m.id),
 effective:cat=>masterRecipeOrder(cat).map(m=>m.id),
 dates:(id,date)=>{const m=meals.find(m=>m.id===id);if(date===null)delete m.lastCooked;else m.lastCooked=date;persist();renderList()},
 editDate:id=>editMealCookedDate(meals.find(m=>m.id===id)),
 demote:id=>{snapshot();meals.find(m=>m.id===id).rotation=false;persist();renderList()},
 remove:day=>{clearWeekdayOverride(day,'Mains');const p=mealPlans.find(p=>p.id===activePlanId);delete p.cycleSlotChoices[weekdaySlotKey(day,'Mains')];delete p.cycleRetainedSlots[weekdaySlotKey(day,'Mains')];saveWeekdayMealOverrides();persist();renderList()},
 mixed:()=>{showMealPlanTabs=false;const plan=mealPlans.find(p=>p.id===activePlanId);weekdayCategories={Tuesday:['Weekend'],Friday:['Weekend'],Sunday:['Weekend']};weekdayMealOverrides={'Tuesday::Weekend':'3','Friday::Weekend':'30','Sunday::Weekend':'3'};plan.cycleSlotChoices={'Tuesday::Weekend':{mealId:'3',retain:true},'Friday::Weekend':{mealId:'30',substitution:true},'Sunday::Weekend':{mealId:'3',substitution:true}};plan.cycleRetainedSlots={...weekdayMealOverrides};saveActiveMealPlan();persist();renderList()},
 manual:value=>{manualRecipeOrdering=value;saveManualRecipeOrdering();renderList()},
 restore:b=>{slotBackup.restore(slotBackup.normalize(b));backupRestoreReloadPending=true}
};'''

def ids(p):return f.group_rows(p).evaluate_all('(rows)=>rows.map(e=>Number(e.dataset.mealId))')
def groups(p):p.evaluate('promotionTest.groups()')
def chooser(p):
 p.evaluate("promotionTest.chooser('Saturday','Weekend')")
 d=p.locator('.weekday-meal-picker')
 toggle=d.locator('[data-group=Weekend] .master-category-title')
 if toggle.get_attribute('aria-expanded')=='false':toggle.tap()
 return d,d.locator('[data-group=Weekend] .weekday-meal-choice')
def compare(p):
 expected=ids(p);d,rows=chooser(p);assert rows.evaluate_all('(rows)=>rows.map(e=>Number(e.dataset.mealId))')==expected
 master=f.group_rows(p).evaluate_all('(rows)=>rows.map(e=>({id:e.dataset.mealId,days:e.querySelector(".master-meal-weekdays")?.textContent||"",color:getComputedStyle(e).backgroundColor}))')
 actual=rows.evaluate_all('(rows)=>rows.map(e=>({id:e.dataset.mealId,days:e.querySelector(".master-meal-weekdays")?.textContent||"",color:getComputedStyle(e).backgroundColor}))')
 for a,b in zip(actual,master):
  assert a['id']==b['id'] and a['days']==b['days']
  if a['days']:assert a['color']==b['color']
 d.get_by_role('button',name='Search recipes',exact=True).tap();d.get_by_role('searchbox').fill('cooked older');assert d.locator('.weekday-meal-choice').count()==1 and d.locator('.weekday-meal-choice').get_attribute('data-meal-id')=='33';d.get_by_role('searchbox').fill('');assert rows.evaluate_all('(es)=>es.map(e=>Number(e.dataset.mealId))')==expected
 d.get_by_role('button',name='Cancel',exact=True).tap()
def setting(p,value,save=True):
 p.get_by_role('button',name='Settings and backups',exact=True).tap()
 p.locator('details[data-settings-group=display]').evaluate('(e)=>e.open=true')
 check=p.get_by_role('checkbox',name='Enable manual recipe ordering',exact=True);check.set_checked(value)
 assert check.locator('..').bounding_box()['height']>=44
 p.get_by_role('button',name='Save settings' if save else 'Cancel settings',exact=True).tap()
 groups(p)
def setup(b,name,w,tabs=True):
 c,p,e,prefix=f.setup(b,name,w,'cross-group',tabs);p.evaluate('orderTest.configure()');groups(p);return c,p,e,prefix
def done(c,p,e,prefix):
 assert not e,e
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close()

def modes(b,name,w):
 c,p,e,prefix=setup(b,name,w);raw=p.evaluate("orderTest.raw('Weekend')");before=state(p);schedule=compose(p);sources=f.sources(p)
 automatic=[3,4,1,2,31,34,30,33,32,5,6];assert ids(p)==automatic,ids(p);assert f.group_rows(p).locator('.move').count()==0;compare(p)
 setting(p,True,False);assert ids(p)==automatic and p.evaluate("orderTest.raw('Weekend')")==raw
 setting(p,True);assert ids(p)==raw and f.group_rows(p).locator('.move').count()==2*9;compare(p)
 assert compose(p)==schedule and f.sources(p)==sources and state(p)['meals']==before['meals']
 for key in ['sessions','scales','prefs']:assert state(p)[key]==before[key]
 p.reload();groups(p);assert ids(p)==raw
 # Real arrows: tap to top, hold one position, and tap to bottom.
 row=p.locator('#list .master-category-meal[data-meal-id="32"]');row.locator('.move').first.tap();p.wait_for_timeout(50)
 saved=p.evaluate("orderTest.raw('Weekend')");assert saved[0]==32
 row=p.locator('#list .master-category-meal[data-meal-id="32"]');button=row.locator('.move').last;button.dispatch_event('pointerdown',{'pointerType':'touch'});p.wait_for_timeout(550);button.dispatch_event('pointerup',{'pointerType':'touch'});saved=p.evaluate("orderTest.raw('Weekend')");assert saved[1]==32
 p.locator('#list .master-category-meal[data-meal-id="30"] .move').last.tap();p.wait_for_timeout(50);saved=p.evaluate("orderTest.raw('Weekend')");assert saved[-3]==30
 stable=compose(p);old_sources=f.sources(p);old=state(p)
 setting(p,False);assert f.group_rows(p).locator('.move').count()==0;assert p.evaluate("orderTest.raw('Weekend')")==saved;compare(p)
 p.reload();groups(p);assert p.evaluate("orderTest.raw('Weekend')")==saved
 setting(p,True);assert ids(p)==saved;compare(p);assert compose(p)==stable and f.sources(p)==old_sources and state(p)['meals']==old['meals']
 p.evaluate('promotionTest.validate()');backup=p.evaluate('slotTest.storage()');assert backup['mealRotationManualRecipeOrderingV1']=='true'
 setting(p,False);p.evaluate('(storage)=>orderTest.restore({version:2,...JSON.parse(storage.mealRotationDataV1),storage})',backup);p.reload();groups(p);assert ids(p)==saved
 done(c,p,e,prefix);print('PASS',name,w,'default auto; settings Save/Cancel; tap/hold arrows; toggle/reload/backup restores exact manual order; chooser parity; schedules/groceries/progress/scales unchanged',flush=True)

def updates(b,name,w,tabs):
 c,p,e,prefix=setup(b,name,w,tabs);assert ids(p)==([3,4,1,2,31,34,30,33,32,5,6] if tabs else [3,1,2,31,34,4,30,33,32,5,6]),ids(p)
 # A real date editor save immediately reorders only unscheduled dated recipes.
 raw=p.evaluate("orderTest.raw('Weekend')");schedule=compose(p);p.evaluate('orderTest.editDate(32)');p.get_by_label('Choose last cooked date').fill('2018-01-01');p.get_by_role('button',name='Save',exact=True).tap();assert ids(p).index(32)<ids(p).index(33);assert p.evaluate("orderTest.raw('Weekend')")==raw and compose(p)==schedule
 p.evaluate('([id,date])=>orderTest.dates(id,date)',[33,None]);assert ids(p).index(33)<ids(p).index(30);compare(p)
 p.evaluate("promotionTest.manual('Sunday','Weekend',3)");groups(p);assert ids(p).count(3)==1;assert p.locator('#list .master-category-meal[data-meal-id="3"] .master-meal-weekdays').text_content()=='WED · SUN';compare(p)
 p.evaluate("promotionTest.manual('Saturday','Weekend',30)");groups(p);assert ids(p)[:2]==[3,30];compare(p)
 p.evaluate("promotionTest.start('Sunday')");groups(p);assert ids(p)[:2]==[3,30];compare(p)
 p.evaluate("orderTest.remove('Wednesday')");groups(p);assert ids(p)[:2]==[3,30]
 p.evaluate("promotionTest.manual('Sunday','Weekend',1)");groups(p);assert ids(p)[:2]==[1,30] and ids(p).index(3)>ids(p).index(31);compare(p)
 # Promoting and demoting retain Ideas order; automatic sorting never rearranges the queue.
 old_ideas=[id for id in ids(p) if id in [5,6]];assert old_ideas==[5,6]
 p.evaluate('promotionTest.promote(5)');groups(p);assert ids(p)[-1]==6;compare(p)
 old=compose(p);p.evaluate('promotionTest.full()');groups(p);compare(p)
 assert all(not x.get('substitution',False) for plan in state(p)['plans'] for x in plan.get('cycleSlotChoices',{}).values())
 p.evaluate('slotTest.back()');groups(p);assert compose(p)==old;compare(p)
 p.evaluate('orderTest.demote(33)');groups(p);assert ids(p)[-2:]==[6,33];compare(p)
 p.reload();groups(p);compare(p)
 if name.startswith('meal-') and w==320 and tabs:p.screenshot(path='/tmp/recipe-ordering-mobile.png')
 done(c,p,e,prefix);print('PASS',name,w,'tabs',tabs,'manual/scheduled/undated/oldest tiers; weekday labels/repeats; date edits; configured start; removal; promotion/demotion; override expiry/Cycle Back; reload',flush=True)

def mixed_days(b,name):
 c,p,e,prefix=setup(b,name,320,False);p.evaluate('orderTest.mixed()');groups(p);assert ids(p)[:2]==[3,30];compare(p)
 p.evaluate("promotionTest.start('Friday')");groups(p);assert ids(p)[:2]==[30,3];compare(p)
 p.evaluate('promotionTest.full()');groups(p)
 entries=[r for r in f.rows(p) if r['planId']=='original'];days=['Friday','Saturday','Sunday','Monday','Tuesday','Wednesday','Thursday'];expected=[]
 for r in sorted(entries,key=lambda r:days.index(r['day'])):
  if r['id'] not in expected and any(m['id']==r['id'] and m['rotation'] and m['cat']=='Weekend' for m in state(p)['meals']):expected.append(r['id'])
 assert ids(p)[:len(expected)]==expected;compare(p);done(c,p,e,prefix);print('PASS',name,'mixed manual/automatic repeated recipe uses earliest scheduled weekday; different configured start; priority expires after whole-week cycle',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   mixed_days(b,name)
   for width in [320,360]:
    modes(b,name,width)
    for tabs in [True,False]:updates(b,name,width,tabs)
  b.close()
