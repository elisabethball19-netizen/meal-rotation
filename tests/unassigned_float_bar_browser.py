"""v446: AI recipes / Unassigned keep checkboxes and pencils; select all / none sit at the top with no box; Move / Delete
float at the bottom (pill, like a group's select mode) only while something is selected.
Run: python3 -m http.server 8765 (repo root), then python3 tests/unassigned_float_bar_browser.py"""
import asyncio, os
from playwright.async_api import async_playwright
BASE = os.environ.get('BASE', 'http://localhost:8765')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
END = 'showAppMessage(builtinSidesMigrationNotice),0);})();'

async def check(page_name, browser):
    pg = await browser.new_page(viewport={'width': 412, 'height': 892})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    closure = page_name == 'meal-rotation-test.html'
    if closure:
        src = open(os.path.join(ROOT, page_name), encoding='utf-8').read()
        src = src.replace(END, 'showAppMessage(builtinSidesMigrationNotice),0);window.__t=c=>eval(c);})();')
        await pg.route(f'**/{page_name}', lambda r: r.fulfill(status=200, content_type='text/html', body=src))
    ev = (lambda js: pg.evaluate('c=>window.__t("("+c+")")()', js)) if closure else (lambda js: pg.evaluate(js))
    await pg.goto(f'{BASE}/{page_name}'); await pg.wait_for_timeout(1200)
    if await pg.locator('[aria-label="Dismiss startup prompt"]').count():
        await pg.locator('[aria-label="Dismiss startup prompt"]').click()
    await ev("""()=>{const host=document.createElement('div');host.id='uhost';document.body.prepend(host);
      renderUnassignedChecklist(host,Array.from({length:30},(_,i)=>({id:900+i,cat:'',name:'Meal '+i})),new Set())}""")
    await pg.wait_for_timeout(200)
    r = await pg.evaluate("""()=>{const h=document.getElementById('uhost');return {tickFirst:h.firstElementChild.className,tickInBar:!!h.querySelector('.unassigned-bulk-bar .unassigned-bulk-tick'),barLast:h.lastElementChild.classList.contains('unassigned-float'),hidden:h.querySelector('.unassigned-float').hidden,pencils:h.querySelectorAll('.unassigned-edit').length,checks:h.querySelectorAll('.unassigned-row input.check').length}}""")
    assert r == {'tickFirst': 'unassigned-bulk-tick', 'tickInBar': False, 'barLast': True, 'hidden': True, 'pencils': 30, 'checks': 30}, r
    await pg.locator('#uhost .unassigned-row input.check').nth(2).check(); await pg.wait_for_timeout(100)
    r = await pg.evaluate("""()=>{const b=document.querySelector('#uhost .unassigned-float'),s=getComputedStyle(b),m=b.querySelector('.unassigned-move');return {hidden:b.hidden,text:b.querySelector('.unassigned-bulk-count').textContent,pos:s.position,radius:s.borderTopLeftRadius,dir:getComputedStyle(m).flexDirection,moveOn:!m.disabled,del:!!b.querySelector('.unassigned-delete')}}""")
    assert r['hidden'] is False and r['text'] == '1 selected' and r['pos'] == 'sticky' and r['radius'] == '999px' and r['dir'] == 'row' and r['moveOn'] and r['del'], r
    await pg.locator('#uhost .unassigned-tick-all').first.click(); await pg.wait_for_timeout(100)
    assert await pg.locator('#uhost .unassigned-bulk-count').inner_text() == '30 selected'
    await pg.locator('#uhost .unassigned-tick-all').nth(1).click(); await pg.wait_for_timeout(100)
    assert await pg.evaluate("()=>document.querySelector('#uhost .unassigned-float').hidden")
    assert not errors, errors
    await pg.close(); print('PASS', page_name)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name in ('index.html', 'meal-rotation-test.html'):
            await check(name, b)
        await b.close()
asyncio.run(main())
