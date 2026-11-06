"""Deferred turns across consecutive days, including hidden skip replacements.

The current Skip action chooses an alternative; Leave Empty This Week hides it.
Exercise both paths instead of assuming those two UI actions are equivalent.
All recipes and storage are disposable fixtures.
"""
import copy
import argparse
from pathlib import Path
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import compose, state

f.EXTRA += '''window.emptySkipTest={
 seed:({favorite=false,days=['Saturday','Sunday'],ids=[2,3]})=>{
  const names=['Pernil','Korean Slow-Cooker Beef Bowls','Mississippi-Style Pot Roast','Spaghetti','Tortilla Soup','Apple Braised Pork','French Dip'];
  meals=names.map((name,i)=>({id:i+1,name,url:'',cat:'Weekend',rotation:true,ingredients:[(i+1)+' cups rice',(i+1)+' cups rice','Salt to taste'],instructions:'Cook.',lastCooked:'2020-01-'+String(i+1).padStart(2,'0')+'T12:00:00.000Z',labels:[]}));
  meals.push(...[100,101,102].map(id=>({id,name:'Other '+id,url:'',cat:'Mains',rotation:true,ingredients:['1 cup flour'],instructions:'Mix.',lastCooked:'2020-01-01T12:00:00.000Z'})));
  if(favorite){meals.find(m=>m.id===3).favorite=true;meals.find(m=>m.id===7).favorite=true}
  cats=['Weekend','Mains'];id=103;const assignments=Object.fromEntries(days.map(day=>[day,['Weekend']])),overrides=Object.fromEntries(days.map((day,i)=>[weekdaySlotKey(day,'Weekend'),String(ids[i])]));
  assignments.Wednesday=['Mains'];overrides['Wednesday::Mains']='100';
  mealPlans=[{id:'original',name:'Dinner',weekdayCategories:assignments,weekdayMealOverrides:overrides,cycleRetainedSlots:{...overrides},cycleSlotChoices:Object.fromEntries(Object.entries(overrides).map(([key,mealId])=>[key,{mealId,parentId:''}])),weekdayRecipeFilters:{},pinnedCats:[]},{id:'lunch',name:'Lunch',weekdayCategories:{Tuesday:['Mains']},weekdayMealOverrides:{'Tuesday::Mains':'101'},cycleRetainedSlots:{'Tuesday::Mains':'101'},cycleSlotChoices:{'Tuesday::Mains':{mealId:'101',parentId:''}},weekdayRecipeFilters:{},pinnedCats:[]}];
  activePlanId='original';weekdayCategories=mealPlans[0].weekdayCategories;weekdayMealOverrides={...mealPlans[0].weekdayMealOverrides};weekdayRecipeFilters=mealPlans[0].weekdayRecipeFilters;
  localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));
  persist();promotionTest.my();slotTest.seed();for(const value of Object.values(occurrenceScales.occurrences))value.multiplier=1;writeOccurrenceScales(occurrenceScales);promotionTest.check();
 },
 menu:day=>{const x=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat==='Weekend');openTopMealActionMenu(day,x.cat,x.meal)},
 skip:day=>{const x=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat==='Weekend');return skipScheduledMeal(day,x.cat,x.meal)},
 empty:day=>leaveWeekEmpty(day,'Weekend'),
 whole:day=>leaveWeekEmpty(day,null,true),
 cycle:({days=null,mark=false}={})=>moveDisplayedMealsToBottom(days?new Set(days.map(day=>weekdaySlotKey(day,'Weekend'))):null,false,mark),
 choices:()=>mealPlans[0].cycleSlotChoices,
 queue:()=>meals.filter(m=>m.cat==='Weekend').map(m=>m.id),
 favorites:()=>mealPlans[0].favoriteRotationScores||{},
 legacy:()=>{delete mealPlans[0].cycleSlotChoices['Sunday::Weekend'].deferredMealIds;persist()},
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))}
};'''


def picks(p):
    return {x[1]: x[3] for x in compose(p) if x[0] == 'original' and x[2] == 'Weekend'}


def meal_menu(p, day, action):
    p.evaluate('emptySkipTest.menu', day)
    p.get_by_role('dialog', name='Meal options for '+day, exact=True).get_by_role('button', name=action, exact=True).tap()


def exact(browser, name, width, mode, favorite=False, mark=False):
    c,p,errors,prefix=f.setup(browser,name,width)
    p.evaluate('emptySkipTest.seed', {'favorite':favorite})
    assert p.evaluate('emptySkipTest.queue()') == list(range(1,8))
    assert picks(p)=={'Saturday':2,'Sunday':3}
    recipes=copy.deepcopy(state(p)['meals']);selected=p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']
    p.evaluate("promotionTest.manual('Saturday','Weekend',1)")
    if mode!='empty':meal_menu(p,'Sunday','Skip This Meal')
    if mode=='legacy':p.evaluate('emptySkipTest.legacy()')
    if mode!='skip':meal_menu(p,'Sunday','Leave Empty This Week')
    assert picks(p)==({'Saturday':1,'Sunday':4} if mode=='skip' else {'Saturday':1})
    assert state(p)['meals']==recipes
    assert not p.evaluate('emptySkipTest.favorites()'), 'Schedule edits consumed Favorites credits'
    adjusted=compose(p);groceries=f.sources(p);queue=p.evaluate('emptySkipTest.queue()');prior_choices=p.evaluate('emptySkipTest.choices()')
    p.reload();assert compose(p)==adjusted and f.sources(p)==groceries
    p.evaluate('emptySkipTest.cycle',{'mark':mark})
    assert picks(p)=={'Saturday':2,'Sunday':3},(mode,favorite,mark,picks(p))
    assert all(not choice.get('skipReplacement') and not choice.get('deferredMealIds') for key,choice in p.evaluate('emptySkipTest.choices()').items() if key in ['Saturday::Weekend','Sunday::Weekend'])
    # Neither unconsumed original gains a cooked date. Incoming groceries reset;
    # the unrelated tab's existing check states and selections remain exact.
    after=state(p)
    for meal in after['meals']:
        if meal['id'] in [2,3]:assert meal==next(m for m in recipes if m['id']==meal['id']),(meal,next(m for m in recipes if m['id']==meal['id']))
    for key,source in f.sources(p).items():
        if source['planId']=='lunch':assert source==groceries[key]
        if source['planId']=='original' and source['day'] in ['Saturday','Sunday']:assert not source['checked']
    assert p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']==selected
    resolved=compose(p);checks=f.sources(p);p.reload();assert compose(p)==resolved and f.sources(p)==checks
    p.evaluate('slotTest.back()');assert compose(p)==adjusted,(compose(p),adjusted);assert f.sources(p)==groceries,({k:v for k,v in f.sources(p).items() if groceries.get(k)!=v},{k:v for k,v in groceries.items() if f.sources(p).get(k)!=v})
    restored_queue=p.evaluate('emptySkipTest.queue()')
    if mode!='skip':assert restored_queue==queue
    else:assert restored_queue.index(2)<restored_queue.index(3)
    if mode!='skip':assert p.evaluate('emptySkipTest.choices()')['Sunday::Weekend']==prior_choices['Sunday::Weekend'],'Rotate Back lost the hidden choice/deferrals'
    assert not p.evaluate('emptySkipTest.favorites()')
    p.reload();assert compose(p)==adjusted and f.sources(p)==groceries
    p.evaluate('emptySkipTest.cycle',{'mark':mark});assert picks(p)=={'Saturday':2,'Sunday':3}
    if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
    assert not errors,errors;c.close()
    print('PASS',name,width,mode,'favorite',favorite,'mark',mark,'ordered originals, reload/Rotate Back, queues/credits/dates/groceries/storage',flush=True)


def multiple(browser,name,mode):
    c,p,errors,_=f.setup(browser,name,360)
    p.evaluate('emptySkipTest.seed',{'days':['Friday','Saturday','Sunday'],'ids':[2,3,4]})
    before=copy.deepcopy(state(p)['meals'])
    p.evaluate("promotionTest.manual('Friday','Weekend',1)")
    if mode=='manual':
        p.evaluate("promotionTest.manual('Friday','Weekend',7)")
        p.evaluate("promotionTest.manual('Saturday','Weekend',5)")
        p.evaluate('emptySkipTest.skip','Sunday');p.evaluate('emptySkipTest.empty','Sunday')
    else:
        p.evaluate('emptySkipTest.skip','Saturday');p.evaluate('emptySkipTest.skip','Saturday')
        p.evaluate('emptySkipTest.empty','Saturday')
        p.evaluate('emptySkipTest.skip','Sunday');p.evaluate('emptySkipTest.whole','Sunday')
    assert state(p)['meals']==before
    old=compose(p);checks=f.sources(p);p.reload();assert compose(p)==old
    p.evaluate('emptySkipTest.cycle()')
    assert picks(p)=={'Friday':2,'Saturday':3,'Sunday':4},picks(p)
    assert len(set(picks(p).values()))==3
    p.evaluate('slotTest.back()');assert compose(p)==old and f.sources(p)==checks
    assert not errors,errors;c.close();print('PASS',name,'three consecutive days, repeated',mode,'edits/skips and whole-day empty, distinct FIFO turns and Rotate Back',flush=True)


def partial_and_unavailable(browser,name):
    c,p,errors,_=f.setup(browser,name,360);p.evaluate('emptySkipTest.seed',{})
    p.evaluate("promotionTest.manual('Saturday','Weekend',1)");p.evaluate('emptySkipTest.skip','Sunday');p.evaluate('emptySkipTest.empty','Sunday')
    adjusted=compose(p);p.evaluate('emptySkipTest.cycle',{'days':['Saturday']});assert picks(p)=={'Saturday':2}
    assert p.evaluate('emptySkipTest.choices()')["Sunday::Weekend"]['deferredMealIds']==['3']
    p.evaluate('emptySkipTest.cycle',{'days':['Sunday']});assert picks(p)=={'Saturday':2,'Sunday':3}
    p.evaluate('slotTest.back()');assert picks(p)=={'Saturday':2}
    assert not errors;c.close()
    # A removed/Idea deferred recipe must not be resurrected or block selection.
    c,p,errors,_=f.setup(browser,name,360);p.evaluate('emptySkipTest.seed',{})
    p.evaluate("promotionTest.manual('Saturday','Weekend',1)");p.evaluate('emptySkipTest.skip','Sunday');p.evaluate('emptySkipTest.empty','Sunday')
    p.evaluate("slotTest.state().meals.find(m=>m.id===3).rotation=false")
    p.evaluate('emptySkipTest.cycle()');assert 3 not in picks(p).values() and len(set(picks(p).values()))==2
    assert not errors;c.close();print('PASS',name,'partial rotation retains unselected deferrals; unavailable deferred recipes stay out',flush=True)


def eligibility_and_reservations(browser,name):
    for mode in ['filtered','reserved']:
        c,p,errors,_=f.setup(browser,name,360);p.evaluate('emptySkipTest.seed',{})
        p.evaluate("promotionTest.manual('Saturday','Weekend',1)");p.evaluate('emptySkipTest.skip','Sunday');p.evaluate('emptySkipTest.empty','Sunday')
        if mode=='filtered':
            p.evaluate("slotTest.state().meals.find(m=>m.id===3).labels=['Allowed'];slotTest.state().plans[0].weekdayRecipeFilters['Sunday::Weekend']=['Allowed']")
        else:
            p.evaluate("""const plan=slotTest.state().plans[1];plan.weekdayCategories={Tuesday:['Weekend']};plan.weekdayMealOverrides={'Tuesday::Weekend':'3'};plan.cycleRetainedSlots={'Tuesday::Weekend':'3'};plan.cycleSlotChoices={'Tuesday::Weekend':{mealId:'3',parentId:'',substitution:true,retain:true}}""")
        p.evaluate('emptySkipTest.cycle()')
        assert picks(p)['Saturday']==2
        if mode=='filtered':assert picks(p)['Sunday']==3
        else:
            assert 3 not in picks(p).values()
            ids=[x[3] for x in compose(p) if x[2]=='Weekend'];assert len(ids)==len(set(ids)),compose(p)
        assert not errors,errors;c.close()
    # No deferred edit: an ordinary empty Sunday retains its existing slot;
    # the earlier Saturday takes the next unused recipe in normal queue order.
    c,p,errors,_=f.setup(browser,name,360);p.evaluate('emptySkipTest.seed',{'ids':[1,3]})
    p.evaluate('emptySkipTest.empty','Sunday');p.evaluate('emptySkipTest.cycle()')
    assert picks(p)=={'Saturday':2,'Sunday':3},picks(p)
    assert not errors;c.close()
    print('PASS',name,'deferred choices respect slot filters and cross-tab manual reservations without automatic duplicates',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir',type=Path,help='Optional directory containing a clean baseline copy of both HTML files')
    args=parser.parse_args()
    if args.source_dir:f.ROOT=args.source_dir
    with sync_playwright() as pw:
        b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for name in ['index.html','meal-rotation-test.html']:
            for width in [320,360]:
                for mode in ['skip-empty','skip','empty']:
                    exact(b,name,width,mode)
            exact(b,name,360,'skip-empty',favorite=True,mark=True)
            exact(b,name,360,'legacy')
            for mode in ['manual','skip']:multiple(b,name,mode)
            partial_and_unavailable(b,name)
            eligibility_and_reservations(b,name)
        b.close()
