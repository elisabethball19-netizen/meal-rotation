"""v435: 'Import recipe' row (link / photo / camera) on a new, empty recipe; the recipe link box offers to import on an
empty recipe; plain-text ingredient lists; the editor never slides sideways.
Run: python3 -m http.server 8765 (repo root), then python3 tests/new_recipe_import_browser.py"""
import asyncio, os, base64
from playwright.async_api import async_playwright

BASE = os.environ.get('BASE', 'http://localhost:8765')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
END = 'showAppMessage(builtinSidesMigrationNotice),0);})();'
URL = 'https://www.example.com/fried-rice/'
HTML = """<!doctype html><html><head><link rel="canonical" href="https://www.example.com/fried-rice/"></head><body>
<div class="wprm-recipe-container"><h2 class="wprm-recipe-name">Chicken Fried Rice</h2>
<span class="wprm-recipe-servings">4</span><span class="wprm-recipe-servings-unit">servings</span>
<ul><li class="wprm-recipe-ingredient">2 cups cooked rice</li><li class="wprm-recipe-ingredient">2 eggs</li></ul>
<div class="wprm-recipe-instructions-container"><ul><li>Scramble the eggs in a hot pan with a little oil.</li><li>Add the rice and stir fry for three minutes.</li></ul></div></div></body></html>"""
PHOTO_TEXT = "Lentil Soup\nServes 6\nIngredients\n1 cup red lentils\n1 onion, chopped\n4 cups stock\nInstructions\n1. Cook the onion in a little oil until soft.\n2. Add the lentils and stock and simmer for 25 minutes.\n"
PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==')

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
    async def ev(js, arg=None):
        if closure:
            return await pg.evaluate('([c,a])=>window.__t("("+c+")")(a)', [js, arg])
        return await pg.evaluate(js, arg)
    await pg.goto(f'{BASE}/{page_name}'); await pg.wait_for_timeout(1200)
    if await pg.locator('[aria-label="Dismiss startup prompt"]').count():
        await pg.locator('[aria-label="Dismiss startup prompt"]').click()
    # Stubs: the site answers directly with HTML; the photo reader returns fixed text.
    await ev("""([html,text])=>{window.fetch=async()=>new Response(html);
      ingredientPhotoIsBlank=async()=>false;recognizeIngredientPhoto=async()=>text}""", [HTML, PHOTO_TEXT])
    async def new_recipe(meal_id):
        if await ev("()=>editId!==null"):
            await pg.locator('#editor button[aria-label="Save"]:visible').first.click(); await pg.wait_for_timeout(700)
        await ev("""id=>{cats=['Sides','Mains'];meals.push({id,cat:'Mains',name:'',rotation:false,ingredients:[],instructions:[]});render();openEditor(id)}""", meal_id)
        await pg.wait_for_timeout(700)
    state = """()=>{const row=document.querySelector('#editor .meal-card-import');return {row:!!row&&!row.hidden,icons:row?[...row.querySelectorAll('button')].map(b=>b.innerHTML.includes('<svg')):[],
      name:document.getElementById('name').value,ing:document.getElementById('ingredients').value,steps:document.getElementById('recipeInstructions').value,servings:document.getElementById('servings').value,
      url:document.getElementById('url').value,recipeOpen:document.querySelector('#editor details[data-editor-section=recipe]').open}}"""

    # 1. Link import from the row
    await new_recipe(101)
    s = await ev(state)
    assert s['row'] and s['icons'] == [True, True, True], s
    await pg.locator('#editor .meal-card-import [aria-label="Import recipe from a website link"]').click(); await pg.wait_for_timeout(300)
    assert await pg.get_by_text('Import recipe from link').count() == 1
    await pg.locator('input[type=url]:visible').last.fill(URL); await pg.get_by_role('button', name='Import', exact=True).click(); await pg.wait_for_timeout(1200)
    s = await ev(state)
    assert s['name'] == 'Chicken Fried Rice' and s['ing'].split('\n') == ['2 cups cooked rice', '2 eggs'] and 'Scramble the eggs' in s['steps'], s
    assert s['servings'] == '4' and s['url'] == URL and s['recipeOpen'] and not s['row'], s
    await pg.screenshot(path=f'/tmp/v435_{page_name}_link.png')

    # 2. Photo import from the row (camera and gallery share the same path)
    await new_recipe(102)
    await pg.locator('#editor .meal-card-import input[type=file]').first.set_input_files(files=[{'name': 'r.png', 'mimeType': 'image/png', 'buffer': PNG}])
    await pg.wait_for_timeout(1200)
    s = await ev(state)
    assert s['name'] == 'Lentil Soup' and s['ing'].split('\n') == ['1 cup red lentils', '1 onion, chopped', '4 cups stock'], s
    assert 'simmer for 25 minutes' in s['steps'] and s['servings'] == '6' and not s['row'], s
    assert await pg.get_by_text('Recipes read from a photo can have mistakes').count() == 1
    await pg.locator('button:visible', has_text='OK').last.click(); await pg.wait_for_timeout(200)
    camera = await ev("()=>[...document.querySelectorAll('#editor .meal-card-import input[type=file]')].map(i=>i.getAttribute('capture'))")
    assert camera == [None, 'environment'], camera

    # 3. The recipe link box offers to import on an empty recipe
    await new_recipe(103)
    await ev("()=>{const u=document.getElementById('url');u.hidden=false;u.value='%s';u.dispatchEvent(new Event('input',{bubbles:true}));u.dispatchEvent(new Event('change',{bubbles:true}))}" % URL)
    await pg.wait_for_timeout(300)
    assert await pg.get_by_text('Import the recipe from this link?').count() == 1
    await pg.get_by_role('button', name='Import', exact=True).click(); await pg.wait_for_timeout(1200)
    s = await ev(state)
    assert s['name'] == 'Chicken Fried Rice' and s['ing'].startswith('2 cups cooked rice'), s

    # 4. A recipe with content: no row, no offer
    await pg.locator('#editor button[aria-label="Save"]:visible').first.click(); await pg.wait_for_timeout(700)
    await ev("()=>{meals.push({id:104,cat:'Mains',name:'Toast',rotation:true,ingredients:['2 slices bread'],instructions:[{type:'step',text:'Toast the bread.'}]});render();openEditor(104)}")
    await pg.wait_for_timeout(700)
    assert await ev("()=>!document.querySelector('#editor .meal-card-import')")
    await ev("()=>{const u=document.getElementById('url');u.value='%s';u.dispatchEvent(new Event('change',{bubbles:true}))}" % URL)
    await pg.wait_for_timeout(300)
    assert await pg.get_by_text('Import the recipe from this link?').count() == 0

    # 5. The editor cannot slide sideways
    r = await ev("()=>{const f=document.querySelector('#editor .meal-editor-fields');f.scrollLeft=9;return [f.scrollLeft,getComputedStyle(f).overflowX]}")
    assert r == [0, 'hidden'], r
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
