"""Groceries: toolbar keeps Filter, the eye and +; Select all / Deselect all / Expand all / Collapse all live under More.
Run: python3 tests/grocery_more_menu_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.gm={open:()=>{showTop=true;allMealsActive=false;groceryTabActive=true;render()},checked:()=>{const e=[...getMasterGroceryItems()];return e.filter(([k,i])=>groceryItemChecked(k,i)).length+'/'+e.length}};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('gm.open()'); p.wait_for_timeout(500)
    icons = p.locator('.grocery-header-icons > button')
    labels = icons.evaluate_all('xs=>xs.map(x=>x.getAttribute("aria-label")||x.title)')
    assert not any(l and ('Select all' in l or 'Deselect all' in l or 'Expand all' in l or 'Collapse all' in l) for l in labels), labels
    assert labels[-1] == 'More grocery options' and len(labels) == 4, labels
    sb.shot(p, name, 'grocery-toolbar')
    more = p.get_by_role('button', name='More grocery options')
    more.click(); p.wait_for_timeout(300)
    rows = p.locator('.compact-meal-dialog button.meal-option-row')
    assert rows.all_inner_texts() == ['Select all', 'Deselect all', 'Expand all', 'Collapse all'], rows.all_inner_texts()
    assert rows.nth(1).is_disabled()  # nothing is checked yet
    sb.shot(p, name, 'grocery-menu')
    p.get_by_role('button', name='Select all', exact=True).click(); p.wait_for_timeout(500)
    a, b = p.evaluate('gm.checked()').split('/'); assert a == b and int(b) > 0, (a, b)
    more.click(); p.wait_for_timeout(300)
    assert rows.nth(0).is_disabled() and not rows.nth(1).is_disabled()  # everything checked now
    p.get_by_role('button', name='Deselect all', exact=True).click(); p.wait_for_timeout(500)
    assert p.evaluate('gm.checked()').startswith('0/')
    more.click(); p.get_by_role('button', name='Expand all', exact=True).click(); p.wait_for_timeout(400)
    more.click(); p.get_by_role('button', name='Collapse all', exact=True).click(); p.wait_for_timeout(400)
    assert not errors, errors
    c.close()
    print('PASS', name, 'Groceries More menu: select / deselect / expand / collapse')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ('index.html', 'meal-rotation-test.html'):
        run(b, n)
    b.close()
