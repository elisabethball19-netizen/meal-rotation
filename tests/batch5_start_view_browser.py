"""Batch 5: first open on a new day starts on Meals; otherwise the last page (fresh launch, reload, resume).

Run: python3 tests/batch5_start_view_browser.py
"""
import sys
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch5={view:()=>appViewSnapshot().view,go:v=>{showTop=v!=='groups';groceryTabActive=v==='grocery';allMealsActive=v==='all';render()},edit:()=>openEditor(meals[0].id),editing:()=>editId!==null};'''

NOON_16 = datetime(2026, 11, 16, 20, tzinfo=timezone.utc)   # Mon 16 Nov, noon Pacific
EVENING_16 = datetime(2026, 11, 17, 6, tzinfo=timezone.utc)  # Mon 16 Nov, 10pm Pacific
MORNING_17 = datetime(2026, 11, 17, 15, tzinfo=timezone.utc)  # Tue 17 Nov, 7am Pacific


def view(p):
    return p.evaluate('batch5.view()')


def go(p, name):
    p.evaluate('v=>batch5.go(v)', name)
    assert view(p) == name, view(p)


def launch(p, url, when):
    """Fresh app launch: same tab, session storage cleared (as after the PWA is closed), normal navigation."""
    p.clock.set_fixed_time(when)
    p.evaluate("Object.keys(sessionStorage).filter(k=>k!=='seeded').forEach(k=>sessionStorage.removeItem(k))")
    p.goto(url)
    p.wait_for_function('window.batch5&&document.querySelector("#tabs")')
    return p


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    url = p.url
    assert view(p) == 'top'
    # Same day: a fresh launch (new tab, empty session storage) returns to the last page.
    go(p, 'grocery')
    q = launch(p, url, EVENING_16)
    assert view(q) == 'grocery', view(q)
    go(q, 'groups')
    q.reload()
    q.wait_for_function('window.batch5')
    assert view(q) == 'groups', 'reload keeps the page'
    # First open on a new day starts on Meals.
    q = launch(q, url, MORNING_17)
    assert view(q) == 'top', view(q)
    # After that, the same day returns to the last page again.
    go(q, 'grocery')
    q = launch(q, url, MORNING_17)
    assert view(q) == 'grocery'
    # Resuming from the background on a new day goes to Meals ...
    q.clock.set_fixed_time(datetime(2026, 11, 18, 15, tzinfo=timezone.utc))
    q.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    assert view(q) == 'top', view(q)
    # ... but never while something is open (an editor here); the page stays put.
    go(q, 'groups')
    q.evaluate('batch5.edit()')
    q.clock.set_fixed_time(datetime(2026, 11, 19, 15, tzinfo=timezone.utc))
    q.evaluate("document.dispatchEvent(new Event('visibilitychange'))")
    assert view(q) == 'groups' and q.evaluate('batch5.editing()'), view(q)
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 5: same-day last page (launch/reload), new-day Meals (launch/resume), busy guard', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
