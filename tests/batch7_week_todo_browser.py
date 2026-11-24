"""Batch 7 (approved Week / To-Do polish): no dated task list below Week's day cards, Week task text
does not open the meal, divider only on days with tasks, To-Do collapse remembered across reload,
final task completion fades the To-Do out (no "all caught up" text).

Run: python3 tests/batch7_week_todo_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch7={
 setup:()=>{follow126.rules();batch127.times();Object.assign(meals.find(m=>m.id===2),{makeAheadTasks:[...(meals.find(m=>m.id===2).makeAheadTasks||[]).filter(t=>t.id!=='w7'),{id:'w7',description:'Soak the beans',daysBefore:0}]});persist();makeAheadDisplayPrefs.showMakeAheadReminders=true;makeAheadDisplayPrefs.showCompletedToday=false;saveMakeAheadDisplayPrefs();showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;render()},
 week:()=>{showMealPlanTabs=true;showTop=true;allMealsActive=true;groceryTabActive=false;overviewWeekOffset=0;render()},
 view:()=>appViewSnapshot().view,
 home:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;render()},
 viewer:()=>!!recipeViewer,
 size:v=>{mealTextSize=v;document.body.dataset.mealTextSize=v;applyMealTextSize()},
 dish:()=>parseFloat(getComputedStyle(document.querySelector('.days-card .days-meals .mealname')).fontSize)
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch7.setup()')
    todo = p.locator('#todaysTodo')
    assert todo.count() == 1 and todo.locator('.make-ahead-reminder').count() >= 1
    # Week page.
    p.evaluate('batch7.week()')
    assert p.locator('.make-ahead-outside').count() == 0
    # Days page: dishes are plain weight.
    sizes = p.evaluate("[...document.querySelectorAll('.days-card .days-meals .mealname')].map(e=>getComputedStyle(e).fontWeight)")
    assert sizes and set(sizes) == {'400'}, sizes
    normal = p.evaluate('batch7.dish()')
    p.evaluate("batch7.size('extra')")
    assert p.evaluate('batch7.dish()') > normal + 2, 'Week dishes follow Text Size'
    p.evaluate("batch7.size('normal')")
    sb.shot(p, name, 'batch7-week')
    # To-Do collapse is remembered across reload.
    p.evaluate('batch7.home()')
    p.locator('#todaysTodo .todo-collapse-toggle').click()
    assert p.locator('#todoTaskItems').is_hidden()
    p.reload()
    p.wait_for_function('window.batch7')
    p.evaluate('batch7.setup()')
    assert p.locator('#todoTaskItems').is_hidden(), 'collapse remembered'
    p.locator('#todaysTodo .todo-collapse-toggle').click()
    assert p.locator('#todoTaskItems').is_visible()
    # Complete every open task: the last one stays checked briefly, then the section fades away.
    rows = p.locator('#todaysTodo .make-ahead-reminder:not(.make-ahead-complete) input')
    while rows.count() > 1:
        rows.first.check()
        p.wait_for_timeout(100)
    rows.first.check()
    p.wait_for_timeout(150)
    assert todo.count() == 1 and todo.locator('input:checked').count() >= 1, 'checked state shown briefly'
    p.wait_for_timeout(1400)
    assert p.locator('#todaysTodo').count() == 0
    assert 'caught up' not in p.locator('#list').inner_text().lower()
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 7: Week no outside list/divider/no navigation, To-Do collapse persisted, final-task fade', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
