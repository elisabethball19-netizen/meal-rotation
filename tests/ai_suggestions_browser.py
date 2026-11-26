"""v438: Ask AI recipe ideas - refill request, paste into the queue, one idea at a time, Save / Pin / Try this week /
Not for us, pace + pause, and the dot on the Ask AI tab.
Run: python3 -m http.server 8765 (repo root), then python3 tests/ai_suggestions_browser.py"""
import asyncio, os
from playwright.async_api import async_playwright

BASE = os.environ.get('BASE', 'http://localhost:8765')
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
END = 'showAppMessage(builtinSidesMigrationNotice),0);})();'

def recipe(title, why, ing):
    return (f"Title: {title}\nWhy: {why}\nPrep time: 15 minutes\nCook time: 25 minutes\nServings: 4\nIngredients\n"
            + "\n".join(f"{x} [1]" for x in ing) + "\nInstructions\n1. Cook everything together until done.\n2. Serve hot.\n\n")
ANSWER = (recipe('Lemon Chicken Orzo', 'Bright and quick, like your Thai Garlic Pork.', ['1 lb chicken thighs', '1 cup orzo'])
          + recipe('Beef and Broccoli', 'Savory and saucy, on the table in 30 minutes.', ['1 lb flank steak', '2 cups broccoli'])
          + recipe('Shrimp Tacos', 'A lighter twist on taco night.', ['1 lb shrimp', '8 tortillas']))

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
    await ev("""()=>{localStorage.setItem(AI_FEATURES_KEY,'on');localStorage.removeItem(AI_SUGGEST_KEY);setAiPending(null);
      window.__opened=[];window.open=u=>{window.__opened.push(String(u));return null};
      cats=['Sides','Mains','Soup'];meals=[{id:1,cat:'Mains',name:'Thai Garlic Pork',rotation:true,ingredients:['1 lb pork'],instructions:[{type:'step',text:'Cook.'}]}];id=2;
      showTop=true;allMealsActive=false;groceryTabActive=false;aiTabActive=true;editId=null;render()}""")
    await pg.wait_for_timeout(500)
    card = pg.locator('.ai-suggest-card')
    assert await card.count() == 1 and 'Get recipe ideas' in await card.inner_text()

    # Refill: request copied/opened, pending 'suggest'
    await pg.locator('.ai-suggest-refill').click(); await pg.wait_for_timeout(500)
    r = await ev("()=>({job:aiPending()?.job,req:buildAiJobRequest('suggest',{count:10})})")
    assert r['job'] == 'suggest' and 'Suggest 10 new dinner recipes' in r['req'] and '"Why: "' in r['req'], r
    assert 'Waiting for your recipe ideas' in await card.inner_text()

    # Paste the answer -> queue of 3, first one shown
    await pg.locator('.ai-paste-card textarea').fill(ANSWER)
    await pg.locator('.ai-paste-card button', has_text='Review recipe').click(); await pg.wait_for_timeout(600)
    st = await ev("()=>{const s=aiSuggestState();return {queue:s.queue.map(x=>x.name),current:s.current?.name,why:s.current?.aiWhy,seen:s.seen,pending:aiPending()}}")
    assert st['current'] == 'Lemon Chicken Orzo' and st['queue'] == ['Beef and Broccoli', 'Shrimp Tacos'] and st['why'].startswith('Bright and quick') and st['seen'] and st['pending'] is None, st
    text = await card.inner_text()
    assert 'Lemon Chicken Orzo' in text and '15m prep' in text and 'serves 4' in text and '2 more waiting' in text, text
    await pg.locator('.ai-suggest-see').click(); await pg.wait_for_timeout(200)
    assert '1 lb chicken thighs' in await card.inner_text()
    await pg.screenshot(path=f'/tmp/v438_{page_name}_card.png', full_page=False)

    # Save -> AI recipes; next idea waits for its date; Show one now
    await pg.locator('.ai-suggest-save').click(); await pg.wait_for_timeout(400)
    assert await ev("()=>meals.some(m=>m.name==='Lemon Chicken Orzo'&&m.aiRecipe&&m.cat===''&&m.ingredients.length===2)")
    assert 'Next idea' in await card.inner_text()
    await pg.locator('.ai-suggest-now').click(); await pg.wait_for_timeout(300)
    assert 'Beef and Broccoli' in await card.inner_text()

    # Not for us -> remembered and sent with the next refill
    await pg.locator('.ai-suggest-no').click(); await pg.wait_for_timeout(300)
    assert await ev("()=>aiSuggestState().rejected.includes('Beef and Broccoli')&&buildAiJobRequest('suggest').includes('Beef and Broccoli')")

    # Time passes -> the next idea arrives by itself and the Ask AI tab shows a dot (on another page)
    await ev("()=>{const s=aiSuggestState();s.shownAt=Date.now()-8*864e5;saveAiSuggestState(s);aiTabActive=false;render()}")
    await pg.wait_for_timeout(300)
    assert await pg.locator('#mealBottomNav [data-destination="ai"] .ai-suggest-dot').count() == 1
    await pg.locator('#mealBottomNav [data-destination="ai"]').click(); await pg.wait_for_timeout(500)
    assert 'Shrimp Tacos' in await card.inner_text()
    await pg.wait_for_timeout(200)
    assert await pg.locator('#mealBottomNav .ai-suggest-dot').count() == 0
    assert 'Refill recipe ideas' in await card.inner_text()  # running low

    # Try this week -> saved and the Schedule dialog opens
    await pg.locator('.ai-suggest-try').click(); await pg.wait_for_timeout(500)
    assert await pg.get_by_text('Schedule Shrimp Tacos').count() == 1
    assert await ev("()=>meals.some(m=>m.name==='Shrimp Tacos'&&m.aiRecipe)")
    await pg.locator('[aria-label="Cancel scheduling"]').click(); await pg.wait_for_timeout(300)

    # Pace + pause persist
    await ev("()=>{const s=aiSuggestState();s.queue.push({name:'Pea Soup',ingredients:['1 cup peas'],instructions:[{type:'step',text:'Simmer.'}]});saveAiSuggestState(s);renderList({readOnly:true})}")
    await pg.wait_for_timeout(300)
    await pg.locator('.ai-suggest-pace').select_option('2weeks'); await pg.wait_for_timeout(200)
    await ev("()=>{const s=aiSuggestState();s.paused=true;saveAiSuggestState(s);renderList({readOnly:true})}"); await pg.wait_for_timeout(200)
    st = await ev("()=>({pace:aiSuggestState().pace,paused:aiSuggestState().paused})")
    assert st == {'pace': '2weeks', 'paused': True}, st
    assert 'paused' in (await card.inner_text()).lower()

    # Pin -> saved to AI recipes and the group chooser opens
    await ev("()=>{const s=aiSuggestState();s.paused=false;saveAiSuggestState(s);aiSuggestShowNext(s);renderList({readOnly:true})}"); await pg.wait_for_timeout(300)
    await pg.locator('.ai-suggest-pin').click(); await pg.wait_for_timeout(500)
    assert await pg.get_by_text('Meal groups', exact=True).count() >= 1
    assert await ev("()=>meals.some(m=>m.name==='Pea Soup'&&m.aiRecipe)")
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
