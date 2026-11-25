"""2026-11-25: Meal Groups list = groups with a weekday in weekday order, then the rest in saved manual order
(no more 'groups scheduled this week first', so Reset group order and the list agree).
Run: python3 tests/group_manual_order_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.mo={open:()=>{showTop=false;masterCategoriesView=true;render()},cats:()=>cats.slice(),set:o=>writeMasterGroupOrder(o),reset:()=>resetWeekdayGroupOrder(),weekly:()=>weekdayOrderedGroups(),shown:()=>[...document.querySelectorAll('#list .master-category-card')].map(c=>c.dataset.category)};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('mo.open()'); p.wait_for_timeout(400)
    cats = p.evaluate('mo.cats()')
    want = list(reversed(cats))
    p.evaluate('o=>mo.set(o)', want); p.evaluate('mo.open()'); p.wait_for_timeout(400)
    shown = p.evaluate('mo.shown()'); weekly = p.evaluate('mo.weekly()')
    assert shown[:len(weekly)] == weekly and len(shown) >= 3, (shown, weekly)  # weekday groups lead in weekday order
    rest = [x for x in shown if x not in weekly]; assert rest == [x for x in want if x in rest], (rest, want)
    p.evaluate('mo.reset()'); p.evaluate('mo.open()'); p.wait_for_timeout(400)
    shown = p.evaluate('mo.shown()'); weekly = p.evaluate('mo.weekly()')
    assert shown[:len(weekly)] == weekly, (shown[:len(weekly)], weekly)
    assert not errors, errors
    c.close()
    print('PASS', name, 'manual group order is shown as saved; reset puts weekday groups first')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ('index.html', 'meal-rotation-test.html'):
        run(b, n)
    b.close()
