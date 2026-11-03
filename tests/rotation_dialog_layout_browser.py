"""Cycle Meals dialog layout with isolated synthetic data and mobile touch input."""
from pathlib import Path
from playwright.sync_api import sync_playwright
from scheduled_linked_slots_browser import setup

def rect(loc):
    return loc.bounding_box()

def run(browser, filename, width, height, long_list=False):
    ctx, page, errors, prefix = setup(browser, filename, width, linked=True, duplicate=True, multi=True)
    page.set_viewport_size({'width': width, 'height': height})
    if long_list:
        page.evaluate('''() => {
            const s=slotTest.state();
            s.meals.forEach(m=>m.name+=' with a long descriptive recipe title for mobile layout');
            for(let i=0;i<12;i++)s.plans.push({...structuredClone(s.plans[1]),id:'layout-'+i,name:'Extra plan '+i});
        }''')
    # Save Active Plan runs when opening the all-plans chooser. Capture after that
    # intentional pre-existing operation, before testing selection-only changes.
    page.evaluate('slotTest.open(true)')
    before = page.evaluate('slotTest.storage()')
    title = page.get_by_role('heading', name='Select meals to rotate out', exact=True)
    dialog = title.locator('..')
    select = dialog.get_by_role('button', name='Select all', exact=True)
    deselect = dialog.get_by_role('button', name='Deselect all', exact=True)
    ok = dialog.get_by_role('button', name='Move selected', exact=True)
    cancel = dialog.get_by_role('button', name='Cancel', exact=True)
    checks = dialog.get_by_role('checkbox')
    assert checks.count() >= 6
    assert dialog.get_by_role('button').count() == 4
    t, s, d, o, c, box = map(rect, [title, select, deselect, ok, cancel, dialog])
    assert t['x'] + t['width'] <= s['x'] - 7
    assert abs(s['y'] - d['y']) < 1
    assert s['y'] < o['y'] and d['x'] > s['x']
    assert abs(o['y'] - c['y']) < 1 and o['x'] < c['x']
    assert abs(o['x'] - (box['x']+18)) < 1
    assert abs(c['x']+c['width']-(box['x']+box['width']-18)) < 1
    assert 11 <= box['y']+box['height']-(c['y']+c['height']) <= 13
    assert box['x'] >= 15 and box['x']+box['width'] <= width-15
    assert box['y'] >= 0 and box['y']+box['height'] <= height
    for r in [s,d,o,c]: assert r['width'] >= 44 and r['height'] >= 44
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    assert title.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
    if width <= 360: assert t['height'] > 30, 'Heading should wrap at narrow widths'
    assert checks.evaluate_all('(es)=>es.every(e=>e.checked)')
    deselect.tap(); assert checks.evaluate_all('(es)=>es.every(e=>!e.checked)')
    select.tap(); assert checks.evaluate_all('(es)=>es.every(e=>e.checked)')
    checks.first.tap(); assert not checks.first.is_checked()
    assert checks.evaluate_all('(es)=>es.slice(1).every(e=>e.checked)')
    assert page.evaluate('slotTest.storage()') == before
    assert ok.locator('..').get_by_role('button').count() == 2
    scroll = checks.first.locator('../..')
    if long_list:
        assert scroll.evaluate('(e)=>e.scrollHeight>e.clientHeight+100')
        r=rect(scroll); x=r['x']+r['width']*.7; y=r['y']+r['height']*.8
        session=ctx.new_cdp_session(page)
        session.send('Input.dispatchTouchEvent', {'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
        for n in range(1,9):
            session.send('Input.dispatchTouchEvent', {'type':'touchMove','touchPoints':[{'x':x,'y':y-r['height']*.6*n/8}]})
            page.wait_for_timeout(20)
        session.send('Input.dispatchTouchEvent', {'type':'touchEnd','touchPoints':[]})
        page.wait_for_timeout(250)
        assert scroll.evaluate('(e)=>e.scrollTop') > 0, 'Native touch swipe must scroll meal list'
        assert abs(rect(select)['y']-s['y']) < 1 and abs(rect(ok)['y']-o['y']) < 1
        checks.last.scroll_into_view_if_needed(); checks.last.tap()
        assert not checks.last.is_checked()
        assert rect(checks.last)['y']+rect(checks.last)['height'] < rect(ok)['y']
    else:
        assert scroll.evaluate('(e)=>e.scrollHeight<=e.clientHeight+1')
    if filename=='index.html' and width in [280,360]:
        page.screenshot(path=f'/tmp/rotation-dialog-{width}-{height}.png')
    cancel.tap(); assert not title.count()
    assert page.evaluate('slotTest.storage()') == before
    page.evaluate('slotTest.open(true)')
    dialog=page.get_by_role('heading',name='Select meals to rotate out').locator('..')
    dialog.get_by_role('button',name='Deselect all',exact=True).tap()
    dialog.get_by_role('button',name='Move selected',exact=True).tap()
    assert not page.get_by_role('heading',name='Select meals to rotate out').count()
    assert page.evaluate('slotTest.storage()') == before
    if prefix:
        assert page.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
    assert not errors, errors
    print(f'PASS {filename} {width}x{height}: heading/actions, 44px targets, compact footer, selection/cancel/no-selection, '+('native touch scrolling' if long_list else 'content-sized list')+', no storage changes or JS errors', flush=True)
    ctx.close()

if __name__=='__main__':
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
        for filename in ['index.html','meal-rotation-test.html']:
            for width,height,long_list in [(280,800,False),(320,800,False),(360,800,False),(390,851,True),(740,360,True)]:
                run(browser,filename,width,height,long_list)
        browser.close()
