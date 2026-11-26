"""v451: in the One-Time Meal editor the 'Always serve this side with …?' switch is hidden while One-time meal is ticked
(shown again when unticked), and the switch names the meal as it is typed (it used to read 'with ?').
Run: python3 -m http.server 8765 (repo root), then python3 tests/one_time_side_switch_browser.py"""
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
    await ev("()=>{openOneTimeMealEditor('Thursday','@day')}"); await pg.wait_for_timeout(600)
    await pg.locator('#editor #name').fill('Test')
    await pg.locator('#scheduledOneTime').check(); await pg.wait_for_timeout(200)
    # add a side so the switch exists
    await ev("()=>{if(!meals.length){meals.push({id:777,cat:'',name:'Knorr Spinach Dip',ingredients:[],instructions:[]})}const side=meals.find(m=>m.name!=='Test');openAddSideDialog=(p,d,ex,cb)=>cb({id:'s1',type:'fixed',mealId:String(side.id),always:true});document.getElementById('serveWith').addServingSide?.()}"); await pg.wait_for_timeout(400)
    n = await pg.locator('#editor .side-always-toggle').count()
    assert n == 1, n
    visible = await pg.evaluate("()=>[...document.querySelectorAll('#editor .side-always-toggle')].map(x=>getComputedStyle(x).display)")
    assert all(v == 'none' for v in visible), visible
    assert await pg.evaluate("()=>getComputedStyle(document.querySelector('#editor .meal-group-editor-heading')).display") == 'none'  # v452
    await pg.evaluate("()=>{const c=document.getElementById('scheduledOneTime');c.click()}"); await pg.wait_for_timeout(200)
    visible = await pg.evaluate("()=>[...document.querySelectorAll('#editor .side-always-toggle')].map(x=>[getComputedStyle(x).display,x.textContent])")
    print(visible)
    assert all(v[0] != 'none' and 'with Test?' in v[1] for v in visible), visible
    assert await pg.evaluate("()=>getComputedStyle(document.querySelector('#editor .meal-group-editor-heading')).display") != 'none'
    assert not errors, errors
    await pg.close(); print('PASS', page_name, n)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name in ('index.html', 'meal-rotation-test.html'):
            await check(name, b)
        await b.close()
asyncio.run(main())
