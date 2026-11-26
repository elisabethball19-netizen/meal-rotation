"""v440: Ask AI jobs open in place (one at a time, typed text kept), New recipe idea first under New ideas,
and the AI flow started from a recipe page returns to the recipe view (close the card, Back, Out of an ingredient sent).
Run: python3 -m http.server 8765 (repo root), then python3 tests/ask_ai_cards_browser.py"""
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
    await ev("""()=>{localStorage.setItem(AI_FEATURES_KEY,'on');localStorage.removeItem(AI_SUGGEST_KEY);setAiPending(null);window.open=()=>null;
      cats=['Sides','Mains'];meals=[{id:1,cat:'Mains',name:'Chili Garlic Bowls',rotation:true,ingredients:['1 lb chicken','2 tbsp chili crisp'],instructions:[{type:'step',text:'Cook.'}]}];id=2;
      showTop=true;allMealsActive=false;groceryTabActive=false;aiTabActive=true;editId=null;render()}""")
    await pg.wait_for_timeout(500)
    order = await pg.evaluate("()=>[...document.querySelectorAll('[data-ai-card]')].map(c=>c.dataset.aiCard)")
    assert order == ['idea', 'fridge', 'write', 'convert', 'like', 'out'], order
    # A job opens in place (no pop-up); another closes it; typed text survives a redraw
    await pg.locator('[data-ai-card="write"] .ai-job-card-head').click(); await pg.wait_for_timeout(300)
    assert await pg.locator('[data-ai-card="write"] .ai-job-card-body textarea').count() == 1
    assert await pg.locator('.recipe-import-popup').count() == 0
    await pg.locator('[data-ai-card="write"] textarea').fill('crispy pork, quick weeknight')
    await ev("()=>renderList({readOnly:true})"); await pg.wait_for_timeout(200)
    assert await pg.locator('[data-ai-card="write"] textarea').input_value() == 'crispy pork, quick weeknight'
    await pg.locator('[data-ai-card="fridge"] .ai-job-card-head').click(); await pg.wait_for_timeout(300)
    opened = await pg.evaluate("()=>[...document.querySelectorAll('.ai-job-card.open')].map(c=>c.dataset.aiCard)")
    assert opened == ['fridge'], opened
    # Send from a card: request copied, card closes, waiting-answer card appears at the top
    await pg.locator('[data-ai-card="fridge"] textarea').fill('chicken, rice')
    await pg.locator('[data-ai-card="fridge"] button', has_text='Copy request').click(); await pg.wait_for_timeout(400)
    assert await ev("()=>aiPending()?.job==='fridge'")
    assert await pg.locator('.ai-job-card.open').count() == 0
    await ev("()=>{setAiPending(null);renderList({readOnly:true})}")

    # From a recipe page: card opens with the recipe chosen; closing the card returns to the recipe view
    async def from_recipe(job):
        await ev("()=>{aiTabActive=false;render();openRecipeViewer(meals[0])}"); await pg.wait_for_timeout(500)
        await ev("()=>openAiCardFromRecipe('%s',meals[0])" % job); await pg.wait_for_timeout(500)
        st = await ev("()=>({ai:aiTabActive,viewer:!!recipeViewer,open:document.querySelector('.ai-job-card.open')?.dataset.aiCard,summary:document.querySelector('.ai-job-card.open .ai-job-card-summary')?.textContent})")
        assert st == {'ai': True, 'viewer': False, 'open': job, 'summary': 'Chili Garlic Bowls'}, st
    await from_recipe('convert')
    await pg.locator('[data-ai-card="convert"] .ai-job-card-head').click(); await pg.wait_for_timeout(600)
    assert await ev("()=>!!recipeViewer&&recipeViewer.mealId==='1'&&!aiTabActive"), 'closing the card should return to the recipe'
    await ev("()=>{finishRecipeViewerClose(false)}"); await pg.wait_for_timeout(300)
    # Back returns to the recipe view
    await from_recipe('like')
    await pg.go_back(); await pg.wait_for_timeout(700)
    assert await ev("()=>!!recipeViewer&&recipeViewer.mealId==='1'"), 'Back should return to the recipe'
    await ev("()=>{finishRecipeViewerClose(false)}"); await pg.wait_for_timeout(300)
    # Out of an ingredient: sending returns to the recipe right away (you are cooking)
    await from_recipe('out')
    await pg.locator('[data-ai-card="out"] .ai-ingredient-chip').first.click()
    await pg.locator('[data-ai-card="out"] button', has_text='Copy request').click(); await pg.wait_for_timeout(700)
    assert await ev("()=>!!recipeViewer&&recipeViewer.mealId==='1'"), 'sending Out of an ingredient should return to the recipe'
    await ev("()=>{finishRecipeViewerClose(false)}"); await pg.wait_for_timeout(300)
    # Change this recipe from the recipe page: paste the answer, Update, save -> back on the (updated) recipe view
    await from_recipe('convert')
    await pg.locator('[data-ai-card="convert"] button', has_text='Copy request').click(); await pg.wait_for_timeout(500)
    ans = "Changed: milder.\n\nTitle: Chili Garlic Bowls\nPrep time: 10 minutes\nCook time: 20 minutes\nServings: 4\nIngredients\n1 lb chicken [1]\n1 tbsp chili crisp [1]\nInstructions\n1. Cook the chicken with the chili crisp.\n"
    await pg.locator('.ai-paste-card textarea').fill(ans); await pg.locator('.ai-paste-card button', has_text='Review recipe').click(); await pg.wait_for_timeout(800)
    await pg.locator('[role=dialog] button:visible').filter(has_text='Update').first.click(); await pg.wait_for_timeout(2500)
    assert await ev("()=>editId!==null"), 'the review editor should be open'
    await pg.locator('#editor button[aria-label="Save"]:visible').first.click(); await pg.wait_for_timeout(1200)
    r = await ev("()=>({viewer:recipeViewer?.mealId||null,ing:meals.find(m=>m.id===1).ingredients})")
    assert r['viewer'] == '1' and '1 tbsp chili crisp' in r['ing'], r
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
