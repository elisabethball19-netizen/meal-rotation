"""v421: New group dialog carries the 'Use for weekly meals' switch; Groceries icon row clusters + and More on the right.
Run: python3 tests/new_group_weekly_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.ng={groups:()=>{showTop=false;masterCategoriesView=true;render()},groc:()=>{showTop=true;allMealsActive=false;groceryTabActive=true;render()},weekly:n=>groupUsesRotation(n)};'''


def add(p, name, weekly):
    p.locator('.master-add-group').click()
    p.wait_for_timeout(300)
    box = p.locator('[role=dialog]').last
    assert box.get_by_text('Use for weekly meals').count() == 1
    sw = box.locator('input.preference-switch')
    assert sw.is_checked()  # on by default, like every group before
    box.locator('input[type=text]').fill(name)
    if not weekly:
        box.get_by_text('Use for weekly meals').click(); p.wait_for_timeout(100)
        assert not sw.is_checked()
    sb.shot(p, 'x', 'new-group-' + name)
    box.get_by_role('button', name='Save').click(); p.wait_for_timeout(800)
    p.locator('[role=dialog]').last.get_by_role('button', name='Cancel', exact=True).click(); p.wait_for_timeout(600)


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('ng.groups()'); p.wait_for_timeout(400)
    add(p, 'ZZWeekly', True); add(p, 'ZZOther', False)
    assert p.evaluate("ng.weekly('ZZWeekly')") is True and p.evaluate("ng.weekly('ZZOther')") is False
    p.evaluate('ng.groc()'); p.wait_for_timeout(500)
    icons = p.locator('.grocery-header-icons > button').evaluate_all('xs=>xs.map(x=>Math.round(x.getBoundingClientRect().left))')
    assert icons[0] < 60 and icons[1] < 120 and icons[-1] > 280 and icons[2] > 230, icons
    sb.shot(p, name, 'grocery-v421')
    assert not errors, errors
    c.close()
    print('PASS', name, 'new group weekly switch; grocery icons clustered')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ('index.html', 'meal-rotation-test.html'):
        run(b, n)
    b.close()
