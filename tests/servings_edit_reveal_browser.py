"""v430: serving size (editor chip, recipe view line with Scale, backups, imports) and
Edit from the recipe view opening ingredients as text + steps, scrolled to Ingredients.
Run: python3 -m http.server 8765 (repo root), then python3 tests/servings_edit_reveal_browser.py
Optional BASE env var (default http://localhost:8765). Checks index.html and meal-rotation-test.html."""
import asyncio, os
from playwright.async_api import async_playwright

BASE = os.environ.get('BASE', 'http://localhost:8765')
SEED = """()=>{const groups=['Quick Pasta','Sheet Pan','Tacos','Soup'];const row=(i,cat,name,ing,steps)=>({id:i,cat,name,rotation:true,ingredients:ing,instructions:steps.map(text=>({type:'step',text}))});
 cats=['Sides',...groups];meals=[row(1,'Quick Pasta','Tomato pasta',['200 g pasta','1 can tomatoes'],['Boil pasta.','Add tomatoes.']),
  row(2,'Quick Pasta','Pea pasta',['200 g pasta','1 cup peas'],['Boil pasta.','Add peas.']),
  row(3,'Sheet Pan','Sheet-pan chicken',['2 chicken thighs','2 potatoes, diced','1 tbsp olive oil','1 tsp paprika'],['Toss everything with oil and paprika.','Roast for 35 minutes.']),
  row(4,'Tacos','Bean tacos',['1 can black beans','6 tortillas'],['Warm beans.','Fill tortillas.']),
  row(5,'Soup','Lentil soup',['1 can lentils','2 cups stock'],['Simmer 20 minutes.'])];id=6;render()}"""
HTML = """<html><head><script type="application/ld+json">{"@context":"https://schema.org","@type":"Recipe","name":"Yield soup",
"recipeYield":["6","6 servings"],"recipeIngredient":["1 onion","2 cups stock"],"recipeInstructions":[{"@type":"HowToStep","text":"Simmer everything."}]}</script></head><body></body></html>"""

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
END = 'showAppMessage(builtinSidesMigrationNotice),0);})();'

async def check(page_name, browser):
    pg = await browser.new_page(viewport={'width': 390, 'height': 844})
    closure = page_name == 'meal-rotation-test.html'
    if closure:  # the test page keeps the app inside one closure; expose a direct-eval hook (as the other tests do)
        src = open(os.path.join(ROOT, page_name), encoding='utf-8').read()
        assert src.count(END) == 1
        src = src.replace(END, 'showAppMessage(builtinSidesMigrationNotice),0);window.__t=c=>eval(c);})();')
        await pg.route(f'**/{page_name}', lambda r: r.fulfill(status=200, content_type='text/html', body=src))
    async def ev(js):
        return await (pg.evaluate('c=>window.__t(c)', '(' + js + ')()') if closure else pg.evaluate(js))
    errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)))
    await pg.goto(f'{BASE}/{page_name}'); await pg.wait_for_timeout(1200)
    if await pg.locator('[aria-label="Dismiss startup prompt"]').count():
        await pg.locator('[aria-label="Dismiss startup prompt"]').click()
    await ev(SEED); await pg.wait_for_timeout(300)

    # Import parsing
    r = await ev(f"""()=>({{
      cases:[recipeImportServings('4'),recipeImportServings('4 servings'),recipeImportServings('Serves 4-6'),recipeImportServings('Makes 12 cookies'),
             recipeImportServings(['', '8 people']),recipeImportServings(5),recipeImportServings('')],
      ld:extractCompleteRecipe({HTML!r},'https://example.com/soup')?.servings,
      fill:(()=>{{const t={{name:'x'}};fillMissingRecipeContent(t,{{servings:3}});const u={{name:'y',servings:2}};fillMissingRecipeContent(u,{{servings:5}});return [t.servings,u.servings]}})()
    }})""")
    assert r['cases'] == [4, 4, 4, '', 8, 5, ''], r
    assert r['ld'] == 6, r
    assert r['fill'] == [3, 2], r

    # Backup validation
    v = await ev("""()=>{const ok=m=>{try{validateBackupCore({version:2,cats:['A'],active:'A',meals:[m]});return true}catch(e){return e.message}};
      return [ok({id:1,cat:'A',name:'a',servings:4}),ok({id:1,cat:'A',name:'a',servings:'4'}),ok({id:1,cat:'A',name:'a',servings:0}),ok({id:1,cat:'A',name:'a'})]}""")
    assert v[0] is True and v[1] == 'Invalid servings' and v[2] == 'Invalid servings' and v[3] is True, v

    # Editor opened normally (Groups page path): sections stay closed, serves chip present
    await ev("()=>openEditor(meals[2].id)"); await pg.wait_for_timeout(600)
    st = await ev("""()=>({recipe:document.querySelector('#editor details[data-editor-section=recipe]').open,
      chip:[...document.querySelectorAll('#editor .meal-card-time-field .meal-card-field-button')].map(b=>b.textContent)})""")
    assert st['recipe'] is False, st
    assert st['chip'][-1] == '— serves', st
    await pg.screenshot(path=f'/tmp/v430_{page_name}_chips.png')
    # Invalid then valid entry
    await pg.locator('[aria-label="Edit servings"]').click()
    await pg.locator('#servings').fill('abc')
    await pg.locator('#editor button[aria-label="Save"]:visible').first.click(); await pg.wait_for_timeout(500)
    msg = await ev("()=>document.body.innerText.includes('whole number, such as 4')")
    assert msg, 'no invalid servings message'
    assert await ev("()=>meals[2].servings===undefined")
    await ev("()=>document.querySelector('[role=dialog] button, [aria-modal=true] button')?.click()"); await pg.wait_for_timeout(300)
    await pg.locator('#servings').fill('4')
    assert await ev("()=>editorHasPendingChanges()")
    await pg.locator('#editor button[aria-label="Save"]:visible').first.click(); await pg.wait_for_timeout(600)
    assert await ev("()=>meals[2].servings===4"), await ev("()=>meals[2].servings")

    # Recipe view: Serves 4, follows Scale
    await ev("()=>{editId=null;render();openRecipeViewer(meals[2])}"); await pg.wait_for_timeout(700)
    assert await pg.locator('#recipeViewer .recipe-servings').inner_text() == 'Serves 4'
    await pg.screenshot(path=f'/tmp/v430_{page_name}_view.png')
    await ev("()=>{recipeViewer.previewScale=2;renderRecipeViewer()}"); await pg.wait_for_timeout(300)
    assert await pg.locator('#recipeViewer .recipe-servings').inner_text() == 'Serves 8'
    await ev("()=>{recipeViewer.previewScale=1.5;renderRecipeViewer()}"); await pg.wait_for_timeout(300)
    assert await pg.locator('#recipeViewer .recipe-servings').inner_text() == 'Serves 6'
    await ev("()=>{recipeViewer.previewScale=1;renderRecipeViewer()}"); await pg.wait_for_timeout(300)

    # Edit from the recipe view: Recipe open, ingredients as text, steps open, ingredients at top
    await pg.locator('[aria-label="Edit Recipe"]:visible').first.click(); await pg.wait_for_timeout(900)
    st = await ev("""()=>{const ing=document.getElementById('editorIngredientsSection'),r=ing.getBoundingClientRect();
      return {recipe:document.querySelector('#editor details[data-editor-section=recipe]').open,ing:ing.open,
        steps:document.getElementById('editorInstructionsSection').open,
        text:getComputedStyle(document.getElementById('ingredients')).display!=='none'&&document.getElementById('ingredients').offsetParent!==null,
        chips:!document.getElementById('ingredientStepView').hidden,
        stepsText:document.getElementById('recipeInstructions').offsetParent!==null,
        top:Math.round(r.top-ing.closest('.meal-editor-fields').getBoundingClientRect().top),pageTop:Math.round(document.querySelector('#editor .editor').getBoundingClientRect().top)}}""")
    await pg.screenshot(path=f'/tmp/v430_{page_name}_edit.png')
    assert st['recipe'] and st['ing'] and st['steps'], st
    assert st['text'] and not st['chips'] and st['stepsText'], st
    assert 0 <= st['top'] < 40 and st['pageTop'] < 260, st  # Ingredients at the top of the editor box; editor near the page top

    # Clearing the number removes the field
    await pg.locator('[aria-label="Edit servings"]').click(); await pg.locator('#servings').fill('')
    await pg.locator('#editor button[aria-label="Save"]:visible').first.click(); await pg.wait_for_timeout(600)
    assert await ev("()=>!('servings' in meals[2])")
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
