"""Part 2e: calm read-only Weekly Overview; Week tab hidden when meal tabs are off; Plan ahead on the Meals title.

Run: python3 tests/part2e_overview_browser.py
"""
import sys
from datetime import datetime, timezone
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.p2e={
 tabs:on=>{showMealPlanTabs=on;showTop=true;groceryTabActive=false;allMealsActive=true;overviewWeekOffset=0;render()},
 view:()=>allMealsActive?'all':'top'
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.clock.set_fixed_time(datetime(2026, 11, 19, 20, tzinfo=timezone.utc))
    p.evaluate('p2e.tabs(true)')
    p.wait_for_timeout(400)
    assert p.locator('#mealBottomNav [data-destination="all"]').count() == 1
    days = p.locator('.all-meals-day')
    assert days.count() >= 7
    bg = days.first.evaluate('e=>getComputedStyle(e).backgroundColor')
    assert bg == 'rgb(255, 255, 255)', bg
    assert p.locator('.all-meals-day .make-ahead-reminder, .all-meals-day input[type=checkbox]').count() == 0
    assert p.locator('.all-meals-day:has-text("No meal planned")').count() == 0
    assert p.locator('.all-meals-day.overview-today').count() == 1 and p.locator('.all-meals-day.overview-past').count() >= 1
    assert p.locator('.all-meals-day .plan-ahead-open').count() == 0
    sb.shot(p, name, 'part2e-overview')
    # Meal tabs off: no Week tab; landing on Week sends you to Meals; Plan ahead sits on the Meals title.
    p.evaluate('p2e.tabs(false)')
    p.wait_for_timeout(400)
    assert p.locator('#mealBottomNav [data-destination="all"]').count() == 0
    assert p.evaluate('p2e.view()') == 'top'
    assert p.locator('.meal-plan-title .plan-ahead-open').count() == 1
    sb.shot(p, name, 'part2e-meals-title')
    assert not errors, errors
    c.close()
    print('PASS', name, 'part 2e: calm overview, Week tab follows meal tabs, Plan ahead on Meals title', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
