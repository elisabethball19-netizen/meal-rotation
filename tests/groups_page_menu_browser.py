"""Meal Groups title-bar More menu: Two columns / One column, Reorder groups, Reset group order (only with a custom order).
Run: python3 tests/groups_page_menu_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.gp={open:()=>{showTop=false;masterCategoriesView=true;render()},order:()=>currentMasterGroupOrder(),stub:()=>{window.__needs=weekdayGroupOrderNeedsReset;weekdayGroupOrderNeedsReset=()=>true},unstub:()=>{weekdayGroupOrderNeedsReset=window.__needs}};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate("localStorage.removeItem('mealRotationGroupsLayoutV1')")
    p.evaluate('gp.open()'); p.wait_for_timeout(400)
    more = p.locator('.master-layout-toggle')
    assert more.get_attribute('aria-label') == 'More options for Meal Groups'
    assert p.locator('.master-order-reset').count() == 0
    assert p.locator('#search').count() == 0  # Search moved into the menu
    items = lambda: p.locator('.compact-meal-dialog button.meal-option-row').all_inner_texts()
    more.click(); p.wait_for_timeout(300)
    assert items() == ['Search meals', 'Two columns', 'Reorder groups'], items()
    sb.shot(p, name, 'groups-menu')
    p.get_by_role('button', name='Two columns').click(); p.wait_for_timeout(400)
    assert p.locator('.master-categories').get_attribute('data-groups-layout') == 'two'
    more.click(); p.wait_for_timeout(300)
    assert items()[1] == 'One column'
    p.get_by_role('button', name='One column').click(); p.wait_for_timeout(400)
    assert p.locator('.master-categories').get_attribute('data-groups-layout') == 'compact'
    # reorder groups opens the existing reorder mode (finish / cancel controls, drag handles on every group)
    more.click(); p.get_by_role('button', name='Reorder groups').click(); p.wait_for_timeout(500)
    assert p.locator('.master-categories h2, .master-categories-heading h2').first.text_content() == 'Reorder groups'
    assert p.locator('.master-category-card .organize-drag-handle').count() >= 3
    p.get_by_role('button', name='Cancel reordering groups').click(); p.wait_for_timeout(500)
    # Reset group order is listed only while a custom order is active (stubbed: the fixture has one weekday group)
    p.evaluate('gp.stub()'); more.click(); p.wait_for_timeout(300)
    assert items() == ['Search meals', 'Two columns', 'Reorder groups', 'Reset group order'], items()
    p.get_by_role('button', name='Reset group order').click(); p.wait_for_timeout(400)
    p.evaluate('gp.unstub()')
    assert not errors, errors
    c.close()
    print('PASS', name, 'Meal Groups title-bar More menu: layout, reorder groups, reset group order')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ('index.html', 'meal-rotation-test.html'):
        run(b, n)
    b.close()
