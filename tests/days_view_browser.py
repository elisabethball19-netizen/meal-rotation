"""Days page (v379): rolling Today + Tomorrow + next five days across meal tabs, prep due that day, checkable.

Run: python3 tests/days_view_browser.py   (screenshots in /tmp/days)
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/days')
OUT.mkdir(parents=True, exist_ok=True)

sb.fixture.HOOK += '''window.days={
 setup:()=>{
  const p=mealPlans[1];p.mealPlanWeekStartV1='2026-11-17';
  const entries=getDisplayedWeekdayMealsForPlan(p),calendar=rotationCalendarForPlan(p,entries),anchor=parseCookingLocalDate(p.mealPlanWeekStartV1);calendar.weekStart=p.mealPlanWeekStartV1;
  for(const e of entries){const key=rotationOccurrenceKey({...e,planId:p.id}),date=cookingLocalDate(cookingDateInWeek(e.day,anchor));calendar.occurrences[key]=date;calendar.assignedOn[key]=date;calendar.assignedAt[key]='2026-11-16T12:00:00.000Z';calendar.slots[rotationCalendarSlot(e)]=date}p.rotationCalendar=calendar;
  const m=meals.find(x=>x.id===2);m.makeAheadTasks=[{id:'defrost1',description:'Defrost chuck roast',daysBefore:1}];
  makeAheadDisplayPrefs.showMakeAheadReminders=true;persist();saveActiveMealPlan();
 },
 open:()=>{showTop=true;groceryTabActive=false;aiTabActive=false;allMealsActive=true;showMealPlanTabs=true;rotationWeekOffset=1;render()},
 showDone:on=>{makeAheadDisplayPrefs.showCompletedToday=on;render()},
 checks:()=>mealPlans.flatMap(p=>Object.entries(p.makeAheadChecks||{}).filter(([k,v])=>v).map(([k])=>k)).length
};'''


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    p.evaluate('days.setup()')
    p.evaluate('days.open()')
    assert p.locator('.days-view h2').text_content() == 'Days'
    assert p.locator('#mealBottomNav button[data-destination=all] span').text_content() == 'Days'
    cards = p.locator('.days-card')
    assert cards.count() == 7, cards.count()
    dates = [cards.nth(i).get_attribute('data-date') for i in range(7)]
    assert dates == ['2026-11-16', '2026-11-17', '2026-11-18', '2026-11-19', '2026-11-20', '2026-11-21', '2026-11-22'], dates
    assert p.locator('.days-card.days-open .days-name').all_text_contents() == ['Today', 'Tomorrow']
    assert p.locator('details.days-card').count() == 5 and p.locator('details.days-card[open]').count() == 0
    assert p.locator('.days-view').get_by_text('Weekly Overview').count() == 0

    # Tomorrow (Tue 17): Dinner has the Rice meal, Lunch is a dash; each open card lists every tab.
    tomorrow = cards.nth(1)
    rows = tomorrow.locator('.days-row')
    assert rows.count() == 2 and rows.nth(0).locator('.days-tab').text_content() == 'Dinner' and rows.nth(1).locator('.days-tab').text_content() == 'Lunch'
    assert rows.nth(0).locator('.mealname').count() == 1 and rows.nth(1).locator('.days-none').text_content() == '—'
    # Prep is listed on the day it is due (Today), worded with the meal it is for.
    prep = cards.nth(0).locator('.days-prep .make-ahead-reminder')
    assert prep.count() == 1, prep.count()
    assert 'Defrost chuck roast for tomorrow' in prep.text_content(), prep.text_content()
    assert tomorrow.locator('.days-prep').count() == 0, 'not repeated on the meal day'
    p.locator('.days-card').first.scroll_into_view_if_needed()
    p.screenshot(path=str(OUT / f'{tag}-today.png'))

    # Checking it saves the shared completion and the page redraws (collapsed state kept).
    cards.nth(3).locator('summary').click()
    assert cards.nth(3).get_attribute('open') is not None
    prep.locator('input[type=checkbox]').click()
    p.wait_for_timeout(150)
    assert p.locator('.days-card').nth(0).locator('.days-prep input[type=checkbox]').first.is_checked(), 'check shows before the row leaves'
    p.wait_for_timeout(500)
    assert p.evaluate('days.checks()') == 1
    assert p.locator('.days-card').nth(0).locator('.days-prep').count() == 0, 'completed prep hides (show-completed off)'
    assert p.locator('.days-card').nth(3).get_attribute('open') is not None, 'expanded day stays open after redraw'
    p.screenshot(path=str(OUT / f'{tag}-open.png'))
    # Centering: checkbox and text share a vertical center when shown.
    p.evaluate('days.showDone(true)')
    box = p.locator('.days-card').nth(0).locator('.days-prep input[type=checkbox]')
    txt = p.locator('.days-card').nth(0).locator('.days-prep .make-ahead-reminder')
    cb, tb = box.bounding_box(), txt.bounding_box()
    assert abs((cb['y'] + cb['height'] / 2) - (tb['y'] + tb['height'] / 2)) <= 3, (cb, tb)
    assert box.is_checked()
    p.evaluate('days.showDone(false)')
    row = p.locator('.days-card').nth(1).locator('.days-row').nth(1)
    assert row.bounding_box()['height'] < 46, row.bounding_box()
    mn = p.locator('.days-card').nth(1).locator('.days-mealname').first.bounding_box()
    assert mn['height'] < 34, mn
    p.locator('.days-card').nth(3).locator('summary').click()
    assert p.locator('.days-card').nth(3).get_attribute('open') is None

    # Rolling: from Fri Nov 20 the window runs into the next week (Tue Nov 24 comes from the preview).
    p.clock.set_fixed_time(datetime(2026, 11, 20, 20, tzinfo=timezone.utc))
    p.evaluate('days.open()')
    cards = p.locator('.days-card')
    dates = [cards.nth(i).get_attribute('data-date') for i in range(7)]
    assert dates == ['2026-11-20', '2026-11-21', '2026-11-22', '2026-11-23', '2026-11-24', '2026-11-25', '2026-11-26'], dates
    nov24 = cards.nth(4)
    assert nov24.locator('.days-chip').text_content().startswith('Tue') and nov24.locator('.days-chip b').text_content() == '24'
    assert nov24.locator('.days-row .mealname').count() >= 1, 'next-week preview meal shows in the rolling window'
    assert 'Nothing planned' not in nov24.locator('.days-summary').text_content()
    p.screenshot(path=str(OUT / f'{tag}-rolling.png'))
    assert not errors, errors
    c.close()
    print(name, 'ok')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ['index.html', 'meal-rotation-test.html']:
        run(b, n)
    b.close()
