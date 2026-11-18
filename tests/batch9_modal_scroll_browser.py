"""Batch 9: shared modal scroll lock — swipes inside a dialog never move the page behind it (also at list
ends); list scrolling inside works; page position unchanged after closing; page scrolls normally without a modal.

Run: python3 tests/batch9_modal_scroll_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch9={
 open:()=>{const m=meals.find(m=>m.id===2);m.ingredients=Array.from({length:40},(_,i)=>(i+1)+' cup item '+i);persist();openTopIngredientChooser(m)},
 tall:()=>{const s=document.createElement('div');s.id='b9spacer';s.style.height='3000px';document.getElementById('list').append(s)},
 close:()=>document.querySelector('[aria-label="Edit groceries"] button[aria-label="Cancel"]').click()
};'''


def swipe(p, cdp, x, y0, y1):
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y0}]})
    steps = 8
    for i in range(1, steps + 1):
        cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x, 'y': y0 + (y1 - y0) * i / steps}]})
    cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    p.wait_for_timeout(400)


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    cdp = p.context.new_cdp_session(p)
    p.evaluate('batch9.tall()')
    p.evaluate('window.scrollTo(0,300)')
    p.wait_for_timeout(100)
    # Sanity: without a modal, a swipe scrolls the page.
    swipe(p, cdp, 180, 600, 400)
    free = p.evaluate('scrollY')
    assert free > 300, free
    p.evaluate('window.scrollTo(0,300)')
    p.wait_for_timeout(100)
    p.evaluate('batch9.open()')
    dlg = p.get_by_role('dialog', name='Edit groceries', exact=True)
    dlg.wait_for(state='visible')
    lst = dlg.locator('.grocery-include-row').first.locator('xpath=..')
    box = lst.bounding_box()
    cx, mid = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
    # At the list top, pulling down must not move the page.
    swipe(p, cdp, cx, mid - 60, mid + 60)
    assert p.evaluate('scrollY') == 300, p.evaluate('scrollY')
    # Pushing up scrolls the list, not the page.
    swipe(p, cdp, cx, mid + 60, mid - 60)
    top = lst.evaluate('e=>e.scrollTop')
    assert top > 0 and p.evaluate('scrollY') == 300, (top, p.evaluate('scrollY'))
    # Scroll the list to its end, then keep pushing: still no page movement.
    lst.evaluate('e=>e.scrollTop=e.scrollHeight')
    swipe(p, cdp, cx, mid + 60, mid - 60)
    assert p.evaluate('scrollY') == 300
    # Swiping on the dimmed backdrop does nothing to the page.
    swipe(p, cdp, 180, 40, 10) if p.evaluate("document.elementFromPoint(180,20)?.closest('[aria-modal]')") else None
    swipe(p, cdp, 20, 780, 700)
    assert p.evaluate('scrollY') == 300
    p.evaluate('batch9.close()')
    p.wait_for_timeout(200)
    assert p.evaluate('scrollY') == 300, 'page position unchanged after close'
    swipe(p, cdp, 180, 600, 400)
    assert p.evaluate('scrollY') > 300, 'lock released after close'
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 9: modal scroll lock (list ends, backdrop), list scroll works, released on close', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
