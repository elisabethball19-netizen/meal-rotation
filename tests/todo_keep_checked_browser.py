"""2026-11-24: a checked Make Ahead task stays checked when its meal is taken off this week's slot and put back on
the SAME date; a different date shows the task again; unchecking after the return is still honored (and survives reload).
Run: python3 tests/todo_keep_checked_browser.py
"""
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import start_week_window_browser as s  # registers follow126 + sw130 hooks

s.fixture.HOOK += '''window.keep={
 setup:()=>{meals.find(m=>m.id===2).makeAheadTasks=[{id:'soak',description:'Soak the beans',daysBefore:0}];persist();follow126.home()},
 swap:id=>{applyManualWeekdayMeal('Tuesday','Rice',meals.find(m=>m.id===id),null);follow126.home()},
 tasks:()=>scheduledMakeAheadTasks(false).filter(x=>String(x.entry.meal.id)==='2').map(x=>[x.scheduled,x.complete]),
 uncheck:()=>{const item=scheduledMakeAheadTasks(false).find(x=>String(x.entry.meal.id)==='2'),plan=item.plan;plan.makeAheadChecks={...(plan.makeAheadChecks||{}),[item.key]:false};saveActiveMealPlan(false)},
 otherDate:()=>{const item=scheduledMakeAheadTasks(false).find(x=>String(x.entry.meal.id)==='2'),parts=JSON.parse(item.key);parts[1]='2026-11-24';parts[2]='later';return makeAheadTaskComplete(item.plan,JSON.stringify(parts))}
};'''


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    p.context.new_cdp_session(p).send('Emulation.setTimezoneOverride', {'timezoneId': 'America/Los_Angeles'})
    p.clock.set_fixed_time(datetime(2026, 11, 17, 20, tzinfo=timezone.utc))
    p.evaluate('sw130.seed()')
    p.evaluate('keep.setup()')
    box = p.locator('#todaysTodo input[type=checkbox]').first
    box.check(); p.wait_for_timeout(600)
    assert p.evaluate('keep.tasks()') == [['2026-11-17', True]]
    # Take the meal off Tuesday, then put it back: still checked (no redundant task).
    p.evaluate('keep.swap(3)'); p.evaluate('keep.swap(2)')
    assert p.evaluate('keep.tasks()') == [['2026-11-17', True]], p.evaluate('keep.tasks()')
    # The same task for the same meal on a different date is NOT covered by the old check.
    assert p.evaluate('keep.otherDate()') is False
    # Unchecking after the return is honored and survives reload.
    p.evaluate('keep.uncheck()')  # same write as the To-Do checkbox (recipes.js toggle)
    assert p.evaluate('keep.tasks()') == [['2026-11-17', False]], p.evaluate('keep.tasks()')
    p.reload(); p.wait_for_function('window.keep')
    assert p.evaluate('keep.tasks()') == [['2026-11-17', False]]
    assert p.locator('#todaysTodo input[type=checkbox]').count() == 1, 'unchecked task shows again'
    assert not errors, errors
    c.close()
    print('PASS', name, 'to-do check kept after out-and-back on the same date; other date fresh; uncheck honored', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
