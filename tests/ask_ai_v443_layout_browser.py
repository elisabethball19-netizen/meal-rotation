"""v443: Ask AI - an opened card moves up so its typing box stays above the keyboard (keyboard simulated by shrinking the
viewport), opening Family tastes closes an open card (and the reverse), cards sit closer together.
Run: python3 -m http.server 8765 (repo root), then python3 tests/ask_ai_v443_layout_browser.py"""
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
    await ev("""()=>{localStorage.setItem(AI_FEATURES_KEY,'on');localStorage.removeItem(AI_SUGGEST_KEY);setAiPending(null);window.open=()=>null;
      meals=[{id:1,cat:'Mains',name:'Chili Garlic Bowls',rotation:true,ingredients:['1 lb chicken'],instructions:[{type:'step',text:'Cook.'}]}];id=2;
      showTop=true;allMealsActive=false;groceryTabActive=false;aiTabActive=true;editId=null;render()}""")
    await pg.wait_for_timeout(500)
    gaps = await pg.evaluate("()=>{const c=[...document.querySelectorAll('.ai-section:first-of-type .ai-job-card')].map(x=>x.getBoundingClientRect());return c.slice(1).map((r,i)=>Math.round(r.top-c[i].bottom))}")
    assert all(g <= 8 for g in gaps), gaps
    # Write a recipe: opens, its box is focused; the keyboard opens (viewport shrinks) -> box still visible
    await pg.locator('[data-ai-card="write"] .ai-job-card-head').click(); await pg.wait_for_timeout(200)
    await pg.set_viewport_size({'width': 412, 'height': 430}); await pg.wait_for_timeout(600)
    r = await pg.evaluate("()=>{const t=document.querySelector('[data-ai-card=\"write\"] textarea').getBoundingClientRect(),c=document.querySelector('[data-ai-card=\"write\"]').getBoundingClientRect();return {top:Math.round(c.top),tb:Math.round(t.bottom),h:innerHeight,focus:document.activeElement?.tagName}}")
    assert r['focus'] == 'TEXTAREA' and r['top'] >= 0 and r['tb'] <= r['h'], r
    await pg.set_viewport_size({'width': 412, 'height': 892}); await pg.wait_for_timeout(300)
    # Out of an ingredient (last card) too
    await pg.locator('[data-ai-card="out"] .ai-job-card-head').click(); await pg.wait_for_timeout(200)
    await pg.set_viewport_size({'width': 412, 'height': 430}); await pg.wait_for_timeout(600)
    r = await pg.evaluate("()=>{const f=document.activeElement.getBoundingClientRect();return {tag:document.activeElement.tagName,top:Math.round(f.top),bottom:Math.round(f.bottom),h:innerHeight}}")
    assert r['tag'] in ('INPUT', 'TEXTAREA') and r['top'] >= 0 and r['bottom'] <= r['h'], r
    await pg.set_viewport_size({'width': 412, 'height': 892}); await pg.wait_for_timeout(300)
    # Family tastes closes the open card; opening a card closes Family tastes
    await pg.locator('.ai-tastes-toggle').click(); await pg.wait_for_timeout(300)
    assert await pg.locator('.ai-job-card.open').count() == 0
    assert await pg.locator('.ai-tastes-body').count() == 1
    await pg.locator('[data-ai-card="fridge"] .ai-job-card-head').click(); await pg.wait_for_timeout(300)
    assert await pg.locator('.ai-tastes-body').count() == 0 and await pg.locator('.ai-job-card.open').count() == 1
    assert not errors, errors
    await pg.close(); print('PASS', page_name)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name in ('index.html', 'meal-rotation-test.html'):
            await check(name, b)
        await b.close()
asyncio.run(main())
