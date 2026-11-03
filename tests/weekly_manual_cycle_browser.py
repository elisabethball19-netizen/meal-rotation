"""Explicit weekly cycling expires assigned-slot manual overrides, not cooking dates."""
import copy,json
from playwright.sync_api import sync_playwright
import outgoing_cooked_dates_browser as fixture
from scheduled_linked_slots_browser import meal,rows,state,compose,context_key
fixture.EXTRA+='''window.weeklyTest={
 prepare:()=>{
  cats.push('Weekend','Salads');meals.push({id:200,name:'Lentils',cat:'Weekend',rotation:true,ingredients:['1 cup rice','1 cup rice','Salt to taste'],instructions:'Cook for 20 minutes.',linkedMealIds:[202],lastCooked:'2020-01-01T12:00:00.000Z'},{id:201,name:'Unused Weekend recipe',cat:'Weekend',rotation:true,ingredients:['1 cup rice'],instructions:'Cook.',lastCooked:'2020-01-01T12:00:00.000Z'},{id:202,name:'Linked salad',cat:'Salads',rotation:true,ingredients:['2 cups rice'],instructions:'Mix.',lastCooked:'2020-01-01T12:00:00.000Z'});
  const chosen=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');for(const m of meals)chosen[m.id]=m.ingredients;localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(chosen));
  applyManualWeekdayMeal('Tuesday','Mains',meals.find(m=>m.id===1));applyManualWeekdayMeal('Wednesday','Mains',meals.find(m=>m.id===200));
  const lunch=mealPlans.find(p=>p.id==='lunch');lunch.cycleSlotChoices['Tuesday::Lunch']={mealId:'50',parentId:'',substitution:true,retain:true};
  saveActiveMealPlan();persist();renderList();
 },
 check:()=>{for(const source of getGroceryContributions(true))groceryOccurrenceChecks.checks[source.id]=source.day!=='Wednesday'||JSON.parse(source.id)[2]===0;saveGroceryOccurrenceChecks()},
 open:()=>openRotateOptions(),all:all=>openRotateOptions(all),
 overview:()=>{showTop=true;allMealsActive=true;groceryTabActive=false;renderList()},
 groups:()=>{masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));showTop=false;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(true);renderList()},
 my:()=>{setMasterCategoriesView(false);showTop=true;allMealsActive=false;groceryTabActive=false;renderList()},
 weekend:()=>meals.filter(m=>m.cat==='Weekend').map(m=>m.id),
 ideas:()=>{meals.find(m=>m.id===200).rotation=false;persist();renderList()},
 counts:()=>{const counts={};for(const m of meals){let value=m.lastCooked;Object.defineProperty(m,'lastCooked',{enumerable:true,configurable:true,get:()=>value,set:next=>{counts[m.id]=(counts[m.id]||0)+1;value=next}})}window.weeklyDateWrites=counts},writes:()=>weeklyDateWrites
};'''

def sources(p):return {s['id']:s for s in p.evaluate('dateTest.sources()')}
def pick(p,day,plan='original'):return next(r for r in rows(p) if r['planId']==plan and r['day']==day and r['cat']==('Mains' if plan=='original' else 'Lunch'))
def setup(browser,name,width,anchor=None):
 ctx,p,errors,prefix=fixture.setup(browser,name,width,anchor=anchor);fixture.establish(p,anchor or '2026-10-27');p.evaluate('weeklyTest.prepare()');p.evaluate('slotTest.seed()');p.evaluate('weeklyTest.check()');fixture.clock(p,'2026-11-03');return ctx,p,errors,prefix

def apply(p,mode,mark,all_tabs=False):
 p.evaluate('weeklyTest.all',all_tabs);dialog=p.get_by_role('dialog',name='Rotate out recipes');dialog.get_by_role('checkbox',name='Mark rotated recipes as cooked',exact=True).set_checked(mark)
 if mode=='all':dialog.get_by_role('button',name='Rotate out all recipes',exact=True).tap()
 else:
  dialog.get_by_role('button',name='Select recipes to rotate out',exact=True).tap();d=p.get_by_role('heading',name='Select meals to rotate out').locator('..')
  assert d.get_by_role('checkbox').evaluate_all('(es)=>es.every(e=>e.checked)'), 'Manual choices must be included by default in explicit cycling'
  d.get_by_role('button',name='Deselect all',exact=True).tap()
  if mode=='selected-all':d.get_by_role('button',name='Select all',exact=True).tap()
  else:
   for day,title in [('Tuesday','Crying Tiger'),('Wednesday','Lentils')]:
    if mode==day or mode=='both':d.get_by_role('checkbox',name=(('Dinner · ' if all_tabs else '')+day+' · Mains — '+title),exact=True).check()
  d.get_by_role('button',name='Move selected',exact=True).tap()

def run(browser,name,width,mode,mark=True,all_tabs=False):
 ctx,p,errors,prefix=setup(browser,name,width);before=state(p);schedule=compose(p);old=sources(p);selected=p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1'];p.evaluate('weeklyTest.counts()')
 apply(p,mode,mark,all_tabs);after=state(p);dates=fixture.local_dates(p)
 tiger=mode in ['all','selected-all','both','Tuesday'];lentils=mode in ['all','selected-all','both','Wednesday']
 assert (pick(p,'Tuesday')['id']!=1)==tiger,(mode,rows(p))
 assert pick(p,'Wednesday')['id']==(8 if mode in ['all','selected-all','both'] else 2) if lentils else pick(p,'Wednesday')['id']==200,(mode,rows(p))
 assert dates['1']==dates['30']==dates['100']==('2026-10-27' if mark and tiger else '2020-01-01'),dates
 assert dates['200']==dates['202']==('2026-10-28' if mark and lentils else '2020-01-01'),dates
 assert all(dates[str(id)]=='2020-01-01' for id in [2,*range(8,15),51,101,201]), 'Recipes not in the outgoing schedule must not be marked cooked'
 assert dates['50']==('2026-10-27' if mark and all_tabs else '2020-01-01')
 if not all_tabs:assert pick(p,'Tuesday','lunch')['id']==50
 assert p.evaluate('weeklyTest.weekend()')==[200,201], 'Cross-group substitution must not move the source group queue'
 assert [plan['weekdayCategories'] for plan in after['plans']]==[plan['weekdayCategories'] for plan in before['plans']]
 assert selected==p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']
 for source in sources(p).values():assert source['checked']==(old[source['id']]['checked'] if source['id'] in old and (source['planId']!='original' and not all_tabs or source['planId']=='original' and mode not in ['all','selected-all'] and source['day'] not in (['Tuesday','Wednesday'] if mode=='both' else [mode])) else False),(mode,source)
 for r in rows(p):
  outgoing=(r['planId']=='lunch' and all_tabs) or (r['planId']=='original' and (mode in ['all','selected-all'] or r['day'] in (['Tuesday','Wednesday'] if mode=='both' else [mode])))
  if not outgoing:
   key=context_key(r);assert after['sessions']['occurrences'][key]==before['sessions']['occurrences'][key] and after['scales']['occurrences'][key]==before['scales']['occurrences'][key]
 assert all(count==1 for count in p.evaluate('weeklyTest.writes()').values())
 if not mark:assert not p.evaluate('weeklyTest.writes()')
 # Only scheduling flags/order and authorized outgoing cooked dates may change.
 for meal_after in after['meals']:
  prior=copy.deepcopy(next(m for m in before['meals'] if m['id']==meal_after['id']));prior['lastCooked']=meal_after['lastCooked'];assert meal_after==prior
 if lentils:
  assert not after['plans'][0]['cycleSlotChoices']['Wednesday::Mains'].get('substitution')
  p.evaluate('weeklyTest.groups()');assert 'WED' not in p.locator('.master-category-meal[data-meal-id="200"]').inner_text();new=pick(p,'Wednesday')['id'];assert 'WED' in p.locator(f'.master-category-meal[data-meal-id="{new}"]').inner_text()
  p.evaluate('weeklyTest.overview()');assert 'Lentils' not in p.locator('#list').inner_text();p.evaluate('weeklyTest.my()');assert 'Lentils' not in p.locator('#list').inner_text()
 current=compose(p);checks=sources(p);p.reload();assert compose(p)==current and sources(p)==checks
 p.evaluate('slotTest.back()');assert compose(p)==schedule and p.evaluate('dateTest.dates()')=={str(m['id']):m['lastCooked'] for m in before['meals']}
 assert {key:s['checked'] for key,s in sources(p).items()}=={key:s['checked'] for key,s in old.items()}
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',name,width,mode,'mark',mark,'all-tabs',all_tabs,'manual expiry, outgoing dates, no incoming marks, links, source queues/assignments, groceries, views, progress, reload/Cycle Back',flush=True)

def tracked_weeks_and_ideas(browser,name):
 ctx,p,errors,_=setup(browser,name,360,anchor='2026-10-20');apply(p,'both',True);dates=fixture.local_dates(p)
 assert dates['1']==dates['30']==dates['100']=='2026-10-20' and dates['200']==dates['202']=='2026-10-21'
 assert fixture.calendar_date(p,'Tuesday')=='2026-11-03' and fixture.calendar_date(p,'Wednesday')=='2026-11-04'
 assert dates['2']==dates['8']=='2020-01-01'
 p.reload();fixture.clock(p,'2026-11-10');p.evaluate('dateTest.cycle(["Tuesday::Mains","Wednesday::Mains"])');dates=fixture.local_dates(p)
 assert dates['2']=='2026-11-03' and dates['8']=='2026-11-04' and dates['9']=='2020-01-01'
 assert dates['1']=='2026-10-20' and dates['200']=='2026-10-21' and not errors,errors;ctx.close()
 ctx,p,errors,_=setup(browser,name,360);p.evaluate('weeklyTest.ideas()');apply(p,'Wednesday',True)
 assert pick(p,'Wednesday')['id']==2 and fixture.local_dates(p)['200']=='2026-10-28'
 assert next(m for m in state(p)['meals'] if m['id']==200)['rotation'] is False and not errors,errors;ctx.close()
 print('PASS',name,'tracked missed week, subsequent incoming/outgoing boundary, cross-group Idea selection and source status preservation',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for mode in ['all','selected-all','Tuesday','Wednesday','both']:run(browser,name,width,mode)
    run(browser,name,width,'all',False);run(browser,name,width,'all',True,True)
   tracked_weeks_and_ideas(browser,name)
  browser.close()
