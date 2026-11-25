"""v433: Settings > Import recipes - 'Photo' label; Review recipe stays visible and tappable when the keyboard
leaves only a short viewport; the keyboard's Enter/Go key in the link box runs Review recipe.
Run: python3 -m http.server 8765 (repo root), then python3 tests/import_dialog_keyboard_browser.py"""
import asyncio, os
from playwright.async_api import async_playwright

BASE = os.environ.get('BASE', 'http://localhost:8765')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
END = 'showAppMessage(builtinSidesMigrationNotice),0);})();'

async def check(page_name, browser):
    pg = await browser.new_page(viewport={'width': 390, 'height': 844})
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    closure = page_name == 'meal-rotation-test.html'
    if closure:
        src = open(os.path.join(ROOT, page_name), encoding='utf-8').read()
        assert src.count(END) == 1
        src = src.replace(END, 'showAppMessage(builtinSidesMigrationNotice),0);window.__t=c=>eval(c);})();')
        await pg.route(f'**/{page_name}', lambda r: r.fulfill(status=200, content_type='text/html', body=src))
    ev = (lambda js: pg.evaluate('c=>window.__t("("+c+")")()', js)) if closure else (lambda js: pg.evaluate(js))
    await pg.goto(f'{BASE}/{page_name}'); await pg.wait_for_timeout(1200)
    if await pg.locator('[aria-label="Dismiss startup prompt"]').count():
        await pg.locator('[aria-label="Dismiss startup prompt"]').click()
    await ev("()=>{window.fetch=(u,o)=>new Promise((res,rej)=>{o?.signal?.addEventListener('abort',()=>rej(new DOMException('Aborted','AbortError')))})}")
    await ev("()=>openRecipeImportSourcePicker()"); await pg.wait_for_timeout(400)
    labels = await pg.evaluate("()=>[...document.querySelectorAll('.recipe-import-methods label')].map(l=>l.textContent.trim())")
    assert 'Photo' in labels and not any('camera' in l.lower() for l in labels), labels
    url = pg.locator('.recipe-import-popup input[type=url]')
    assert await url.get_attribute('enterkeyhint') == 'go'
    await url.click()
    await pg.set_viewport_size({'width': 390, 'height': 430}); await pg.wait_for_timeout(500)  # keyboard open
    vis = await pg.evaluate("""()=>{const b=[...document.querySelectorAll('.recipe-import-popup button')].find(x=>x.textContent.trim()==='Review recipe');const r=b.getBoundingClientRect();
      const top=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2);return {bottom:Math.round(r.bottom),h:innerHeight,hit:b.contains(top)}}""")
    assert vis['bottom'] <= vis['h'] and vis['hit'], vis
    await pg.screenshot(path=f'/tmp/v433_{page_name}_keyboard.png')
    # v434: on a shorter visible area (keyboard + autofill bar) the link box must not hide under the sticky row.
    for height in (360, 300):
        await pg.set_viewport_size({'width': 390, 'height': height}); await pg.wait_for_timeout(500)
        vis = await pg.evaluate("""()=>{const b=[...document.querySelectorAll('.recipe-import-popup button')].find(x=>x.textContent.trim()==='Review recipe');const u=document.querySelector('.recipe-import-popup input[type=url]');
          const rb=b.getBoundingClientRect(),ru=u.getBoundingClientRect(),hit=document.elementFromPoint(ru.left+20,ru.top+ru.height/2);
          return {fieldBottom:Math.round(ru.bottom),buttonTop:Math.round(rb.top),buttonBottom:Math.round(rb.bottom),h:innerHeight,fieldHit:hit===u}}""")
        assert vis['fieldBottom'] <= vis['buttonTop'] and vis['buttonBottom'] <= vis['h'] and vis['fieldHit'], (height, vis)
        await pg.screenshot(path=f'/tmp/v434_{page_name}_{height}.png')
    await url.fill('https://www.example.com/recipe/'); await url.press('Enter'); await pg.wait_for_timeout(400)
    assert await pg.get_by_text('Importing recipe from website…').count() == 1
    await pg.locator('[aria-label="Cancel ingredient import"]').click(); await pg.wait_for_timeout(300)
    assert not errors, errors
    await pg.close()
    print('PASS', page_name)

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for name in ('index.html', 'meal-rotation-test.html'):
            await check(name, b)
        await b.close()
asyncio.run(main())
