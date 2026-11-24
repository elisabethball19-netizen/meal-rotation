"""Issue 130: Start next week due-window guard + one press rolls all meal tabs.

Frozen clock (America/Los_Angeles), Tuesday-start weeks; the seeded plan week is Tue 2026-11-17 .. Mon 2026-11-23,
so the due window opens Sun 2026-11-22. Disposable origins for index.html and meal-rotation-test.html.
Run: python3 tests/start_week_window_browser.py
"""
import json
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import followup126_browser as base  # registers the shared follow126 fixture hook

fixture = base.fixture
fixture.HOOK += '''window.sw130={
 seed:(tabs=false,three=false)=>{follow126.seed();
  const set=(p,week)=>{p.mealPlanWeekStartV1=week;const entries=getDisplayedWeekdayMealsForPlan(p),calendar=rotationCalendarForPlan(p,entries),anchor=parseCookingLocalDate(week);calendar.weekStart=week;calendar.occurrences={};calendar.assignedOn={};calendar.slots={};for(const e of entries){const key=rotationOccurrenceKey({...e,planId:p.id}),date=cookingLocalDate(cookingDateInWeek(e.day,anchor));calendar.occurrences[key]=date;calendar.assignedOn[key]=date;calendar.assignedAt[key]='2026-11-16T12:00:00.000Z';calendar.slots[rotationCalendarSlot(e)]=date}p.rotationCalendar=calendar};
  restoringRotationCalendars=true;
  if(three)mealPlans.push({id:'third',name:'Sides tab',mealPlanWeekStartV1:'2026-11-17',weekdayCategories:{Thursday:['Potatoes']},weekdayMealOverrides:{'Thursday::Potatoes':'10'},cycleSlotChoices:{'Thursday::Potatoes':{mealId:'10',parentId:'',substitution:false}},weekdayRecipeFilters:{},pinnedCats:[]});
  for(const p of mealPlans)set(p,'2026-11-17');
  restoringRotationCalendars=false;showMealPlanTabs=tabs;saveActiveMealPlan(false);persist();follow126.home()},
 weeks:()=>Object.fromEntries(mealPlans.map(p=>[p.id,p.mealPlanWeekStartV1])),
 slot:(plan,key)=>{const p=mealPlans.find(x=>x.id===plan),e=getDisplayedWeekdayMealsForPlan(p.id===activePlanId?{...p,weekdayCategories,weekdayMealOverrides}:p).find(e=>weekdaySlotKey(e.day,e.cat)===key&&!e.linkedTo);return e?String(e.meal.id):null},
 pinTue:on=>{const p=mealPlans[0],e=getDisplayedWeekdayMealsForPlan(p).find(e=>e.day==='Tuesday'&&!e.linkedTo);setSlotPin(p,e,on);saveActiveMealPlan(false);return String(e.meal.id)},
 nextTue:()=>{const s=previewMealPlanAdvance();const e=s.entries.find(e=>e.day==='Tuesday'&&!e.linkedTo);return e?String(e.meal.id):null},
 stale:()=>{const p=mealPlans[0];p.mealPlanWeekStartV1='2026-11-24';const e=getDisplayedWeekdayMealsForPlan(p).find(e=>e.day==='Tuesday'&&!e.linkedTo),key=rotationOccurrenceKey({...e,planId:p.id});p.rotationCalendar.occurrences[key]='2026-11-17';p.rotationCalendar.assignedOn[key]='2026-11-10';p.rotationCalendar=rotationCalendarForPlan(p,getDisplayedWeekdayMealsForPlan(p));return p.rotationCalendar.occurrences[key]},
 wed:()=>{const p=mealPlans[0];p.mealPlanWeekStartV1='2026-11-24';startWeekday='Wednesday';const e=getDisplayedWeekdayMealsForPlan(p).find(e=>e.day==='Tuesday'&&!e.linkedTo),key=rotationOccurrenceKey({...e,planId:p.id});p.rotationCalendar.occurrences[key]='2026-11-24';p.rotationCalendar.assignedOn[key]='2026-11-17';p.rotationCalendar=rotationCalendarForPlan(p,getDisplayedWeekdayMealsForPlan(p));const out=[cookingLocalDate(mealPlanWeekStart(p)),p.rotationCalendar.occurrences[key]];startWeekday='Tuesday';return out},
 wedSwitch:()=>{const p=mealPlans[0];p.mealPlanWeekStartV1='2026-11-24';const e=getDisplayedWeekdayMealsForPlan(p).find(e=>e.day==='Tuesday'&&!e.linkedTo),key=rotationOccurrenceKey({...e,planId:p.id});const go=day=>{const old=new Map(mealPlans.map(x=>[x.id,mealPlanWeekStart(x)]));startWeekday=day;realignPlanWeeks(old);return mealPlans[0].rotationCalendar.occurrences[key]};p.rotationCalendar.occurrences[key]='2026-11-24';p.rotationCalendar.assignedOn[key]='2026-11-17';const out=[go('Wednesday'),go('Tuesday'),go('Wednesday'),go('Tuesday')];return out},
 pend:()=>{restoringRotationCalendars=true;weekdayCategories.Wednesday=['Rice'];weekdayMealOverrides['Wednesday::Rice']='4';const pl=mealPlans[0];pl.weekdayCategories={...weekdayCategories};pl.weekdayMealOverrides={...weekdayMealOverrides};pl.cycleSlotChoices['Wednesday::Rice']={mealId:'4',parentId:'',substitution:true,retain:true};pl.mealPlanWeekStartV1='2026-11-24';for(const id of [2,3,4])meals.find(m=>m.id===id).makeAheadTasks=[{id:'b'+id,description:'Begin the bread',daysBefore:1}];const entries=getDisplayedWeekdayMealsForPlan(pl),cal=rotationCalendarForPlan(pl,entries),a=parseCookingLocalDate('2026-11-24');cal.weekStart='2026-11-24';for(const e of entries){const k=rotationOccurrenceKey({...e,planId:pl.id}),d=cookingLocalDate(cookingDateInWeek(e.day,a));cal.occurrences[k]=d;cal.assignedOn[k]='2026-11-17';cal.assignedAt[k]='2026-11-16T12:00:00.000Z';cal.slots[rotationCalendarSlot(e)]=d}pl.rotationCalendar=cal;restoringRotationCalendars=false;saveActiveMealPlan(false);retainDueMakeAheadTasks();persist();follow126.home();const before=document.querySelector('#todaysTodo')?.innerText;saveActiveMealPlan();const old=new Map(mealPlans.map(x=>[x.id,mealPlanWeekStart(x)]));startWeekday='Wednesday';realignPlanWeeks(old);renderList({readOnly:true});return [before,document.querySelector('#todaysTodo')?.innerText||'',mealPlans[0].makeAheadPending.map(x=>x.scheduled)]},
 depth:()=>history.length,open:()=>openStartNextWeek(),rotate:()=>openRotateOptions(false),offset:()=>rotationWeekOffset,load:id=>{loadMealPlan(id,false);follow126.home()},
 third:week=>{mealPlans.find(p=>p.id==='third').mealPlanWeekStartV1=week;saveActiveMealPlan(false)},
 plans:()=>JSON.stringify(mealPlans.map(p=>({id:p.id,week:p.mealPlanWeekStartV1,o:p.weekdayMealOverrides,c:p.weekdayCategories})))
};'''


def at(p, y, m, d):
    """Freeze the clock at local noon (America/Los_Angeles) on the given date and re-render."""
    p.clock.set_fixed_time(datetime(y, m, d, 20, tzinfo=timezone.utc))
    p.evaluate('follow126.home()')


def blocked(p):
    started = p.locator('.rotation-week-controls .start-week-started')
    return started.count() == 1 and started.inner_text().strip() == 'Next week started' and \
        p.locator('.rotation-week-controls button.start-week-text').count() == 0


def press(p, uncheck=()):
    p.locator('.rotation-week-controls button.start-week-text').click()
    d = p.get_by_role('dialog', name='Start next week', exact=True)
    d.wait_for(state='visible')
    for text in uncheck:
        d.locator('label.start-week-choice', has_text=text).locator('input[type=checkbox]').uncheck()
    d.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(500)


def run(browser, name):
    c, p, errors, prefix = fixture.setup(browser, name, navigation_timeout=30000)
    p.context.new_cdp_session(p).send('Emulation.setTimezoneOverride', {'timezoneId': 'America/Los_Angeles'})
    p.clock.set_fixed_time(datetime(2026, 11, 19, 20, tzinfo=timezone.utc))
    p.evaluate('sw130.seed()')

    # 1) Mid-week (Thu): quiet, non-interactive label; direct calls cannot stack a week either.
    at(p, 2026, 11, 19)
    assert blocked(p), p.locator('.rotation-week-controls').inner_html()
    assert p.locator('.start-week-started').evaluate('e=>getComputedStyle(e).pointerEvents') == 'none'
    p.evaluate('sw130.open()')
    assert not p.get_by_role('dialog', name='Start next week', exact=True).count()
    p.evaluate('sw130.rotate()')
    d = p.get_by_role('dialog', name='Start next week', exact=True)
    d.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(300)
    assert p.evaluate('sw130.weeks()')['original'] == '2026-11-17'
    # 6) This week / Next week radios still preview while blocked (read-only).
    before = p.evaluate('sw130.plans()')
    p.locator('.rotation-week-controls input[value="1"]').check()
    p.wait_for_timeout(200)
    assert p.evaluate('sw130.offset()') == 1 and p.locator('.plan-meal-card').count() >= 1
    assert p.evaluate('sw130.plans()') == before
    p.locator('.rotation-week-controls input[value="0"]').check()

    # 2) Day -2 (Sun): allowed; one press moves to the real upcoming week, then the label returns.
    at(p, 2026, 11, 22)
    assert not blocked(p)
    depth = p.evaluate('sw130.depth()')
    press(p)
    assert p.evaluate('sw130.weeks()')['original'] == '2026-11-24', p.evaluate('sw130.weeks()')
    assert p.evaluate('sw130.depth()') == depth + 1
    assert blocked(p)
    p.evaluate('sw130.rotate()')
    p.get_by_role('dialog', name='Start next week', exact=True).locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(300)
    assert p.evaluate('sw130.weeks()')['original'] == '2026-11-24', 'second roll must not stack'
    # Still inactive on Tue/Thu of that new week; reopens two days before it ends (Sun 11-29).
    at(p, 2026, 11, 26)
    assert blocked(p)
    at(p, 2026, 11, 29)
    assert not blocked(p)

    # 2b) Day -1 (Mon): allowed.
    p.evaluate('sw130.seed()')
    at(p, 2026, 11, 23)
    assert not blocked(p)

    # 3) After the boundary and behind: allowed, repeat until caught up, then blocked.
    p.evaluate('sw130.seed()')
    at(p, 2026, 12, 13)  # Sunday; real week Tue 12-08 .. Mon 12-14
    press(p)
    assert p.evaluate('sw130.weeks()')['original'] == '2026-12-08', p.evaluate('sw130.weeks()')
    assert not blocked(p), 'still in the due window of the caught-up week'
    press(p)
    assert p.evaluate('sw130.weeks()')['original'] == '2026-12-15'
    assert blocked(p)

    # 4) Single-tab mode unchanged: only the active plan rolls.
    p.evaluate('sw130.seed(false,true)')
    at(p, 2026, 11, 22)
    press(p)
    w = p.evaluate('sw130.weeks()')
    assert w == {'original': '2026-11-24', 'hidden': '2026-11-17', 'third': '2026-11-17'}, w

    # 5) Three tabs: ONE press rolls all tabs; checklist grouped by tab; unchecked meals carry forward.
    p.evaluate('sw130.seed(true,true)')
    at(p, 2026, 11, 22)
    assert not blocked(p)
    before = p.evaluate('sw130.plans()')
    depth = p.evaluate('sw130.depth()')
    p.locator('.rotation-week-controls button.start-week-text').click()
    d = p.get_by_role('dialog', name='Start next week', exact=True)
    d.wait_for(state='visible')
    headings = d.locator('.start-week-checklist h4').all_inner_texts()
    assert headings == ['Dinner', 'Lunch', 'Sides tab'], headings
    carried = p.evaluate('sw130.slot("third","Thursday::Potatoes")')
    d.locator('label.start-week-choice', has_text='Golden roast potatoes').locator('input[type=checkbox]').uncheck()
    d.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(600)
    w = p.evaluate('sw130.weeks()')
    assert w == {'original': '2026-11-24', 'hidden': '2026-11-24', 'third': '2026-11-24'}, w
    assert p.evaluate('sw130.slot("third","Thursday::Potatoes")') == carried
    assert p.evaluate('sw130.depth()') == depth + 1, 'one undo step for the whole roll'
    assert blocked(p)
    # Switching tabs shows the same started state (no per-tab early roll).
    p.evaluate('sw130.load("hidden")')
    assert blocked(p)
    p.evaluate('sw130.load("original")')

    # Undo restores every tab in one step.
    p.locator('#undo').click()
    p.wait_for_timeout(400)
    assert p.evaluate('sw130.plans()') == before, (json.loads(p.evaluate('sw130.plans()')), json.loads(before))
    p.evaluate('follow126.home()')
    assert not blocked(p)

    # A tab already in the upcoming week is left alone by the all-tabs roll.
    p.evaluate('sw130.seed(true,true);sw130.third("2026-11-24")')
    at(p, 2026, 11, 22)
    press(p)
    w = p.evaluate('sw130.weeks()')
    assert w == {'original': '2026-11-24', 'hidden': '2026-11-24', 'third': '2026-11-24'}, w

    # A) A pinned slot is carried in the Next week preview (matches the Start next week dialog).
    p.evaluate('sw130.seed()')
    cur = p.evaluate('sw130.pinTue(false)')
    assert p.evaluate('sw130.nextTue()') != cur, 'unpinned slot rotates'
    p.evaluate('sw130.pinTue(true)')
    assert p.evaluate('sw130.nextTue()') == cur, 'pinned slot must show the same meal next week'
    # B) A stored date before the displayed week (left by a start-weekday change) is recomputed into the week.
    p.evaluate('sw130.seed()')
    assert p.evaluate('sw130.stale()') == '2026-11-24'

    # C) Changing the start weekday to Wednesday: the week starts Wed 11-25, so Tuesday falls on Dec 1 (after Monday).
    p.evaluate('sw130.seed()')
    assert p.evaluate('sw130.wed()') == ['2026-11-25', '2026-12-01']

    # D) Switching the start weekday re-dates the week both ways (Tue 11-24 <-> Tue 12-01).
    p.evaluate('sw130.seed()')
    assert p.evaluate('sw130.wedSwitch()') == ['2026-12-01', '2026-11-24', '2026-12-01', '2026-11-24']

    # E) A saved (pending) reminder follows its meal when the start weekday changes: no stale "today's dinner".
    p.evaluate('sw130.seed()')
    p.clock.set_fixed_time(datetime(2026, 11, 24, 20, tzinfo=timezone.utc))
    before, after, pend = p.evaluate('sw130.pend()')
    assert 'today' in before and 'tomorrow' in before, before
    assert 'today' not in after and 'tomorrow' in after, after
    assert sorted(pend) == ['2026-11-25', '2026-12-01'], pend

    assert not errors, errors
    if prefix:
        assert p.evaluate('localStorage.getItem("mealRotationDataV1")') == 'WORKING SENTINEL'
    c.close()
    print('PASS', name, 'issue130 window (mid-week blocked, day -2/-1 allowed, catch-up, no stacking), '
          'all-tabs single roll + carry-forward + one-step Undo, single-tab parity, radio preview', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
