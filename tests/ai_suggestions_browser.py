"""v438-v443: Ask AI recipe ideas - refill request, paste into the queue, one idea at a time. v443: no schedule (the next
idea comes in once the current one is used), recipe shown straight away, choices are radio buttons with check / X,
'Last idea · Get more', 'No ideas waiting', no dot on the Ask AI tab.
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
    head = pg.locator('[data-ai-card="idea"] .ai-job-card-head')
    async def open_idea():
        if not await pg.locator('[data-ai-card="idea"].open').count():
            await head.click(); await pg.wait_for_timeout(300)
    async def choose(value):
        await open_idea()
        await pg.locator(f'.ai-suggest-option input[value="{value}"]').check(); await pg.wait_for_timeout(100)
        await pg.locator('.ai-suggest-ok').click(); await pg.wait_for_timeout(500)
    await open_idea()
    card = pg.locator('.ai-suggest-card')
    assert await card.count() == 1 and 'No ideas waiting' in await card.inner_text()

    # Refill: request copied/opened, pending 'suggest'
    await pg.locator('.ai-suggest-refill', has_text='Get 10 more ideas').click(); await pg.wait_for_timeout(500)
    r = await ev("()=>({job:aiPending()?.job,req:buildAiJobRequest('suggest',{count:10})})")
    assert r['job'] == 'suggest' and 'Suggest 10 new dinner recipes' in r['req'] and '"Why: "' in r['req'], r
    assert 'Waiting for new ideas' in await card.inner_text()

    # Paste the answer -> queue of 3, first one shown with its recipe straight away; no count, no pace
    await pg.locator('.ai-paste-card textarea').fill(ANSWER)
    await pg.locator('.ai-paste-card button', has_text='Review recipe').click(); await pg.wait_for_timeout(600)
    st = await ev("()=>{const s=aiSuggestState();return {queue:s.queue.map(x=>x.name),current:s.current?.name,why:s.current?.aiWhy,pending:aiPending()}}")
    assert st['current'] == 'Lemon Chicken Orzo' and st['queue'] == ['Beef and Broccoli', 'Shrimp Tacos'] and st['why'].startswith('Bright and quick') and st['pending'] is None, st
    await open_idea()
    text = await card.inner_text()
    assert 'Lemon Chicken Orzo' in text and '15m prep' in text and 'serves 4' in text and '1 lb chicken thighs' not in text, text
    await pg.locator('.ai-suggest-see').click(); await pg.wait_for_timeout(200)
    text = await card.inner_text()
    assert '1 lb chicken thighs' in text and 'Hide recipe' in text, text
    assert 'waiting' not in text and 'Every week' not in text and 'Last idea' not in text, text
    assert await pg.locator('.ai-suggest-option').count() == 5
    assert await pg.locator('.ai-suggest-ok').is_disabled()
    assert await pg.locator('[data-ai-card="idea"] .ai-job-card-summary').count() == 0  # v444: no name beside the open header
    assert await pg.locator('.ai-suggest-confirm.meal-unified-actions').count() == 1
    await pg.screenshot(path=f'/tmp/v443_{page_name}_card.png', full_page=True)
    # X closes the card and changes nothing
    await pg.locator('.ai-suggest-cancel').click(); await pg.wait_for_timeout(300)
    assert await pg.locator('[data-ai-card="idea"].open').count() == 0
    assert await ev("()=>aiSuggestState().current?.name") == 'Lemon Chicken Orzo'
    assert await pg.locator('[data-ai-card="idea"] .ai-job-card-summary').inner_text() == 'Lemon Chicken Orzo'

    # Save -> AI recipes; the next idea is there right away (no date)
    await choose('save')
    assert await ev("()=>meals.some(m=>m.name==='Lemon Chicken Orzo'&&m.aiRecipe&&m.cat===''&&m.ingredients.length===2)")
    assert await ev("()=>aiSuggestState().current?.name") == 'Beef and Broccoli'

    # Show me later -> to the back; the next one shows
    await choose('later')
    st = await ev("()=>{const s=aiSuggestState();return {current:s.current?.name,queue:s.queue.map(x=>x.name)}}")
    assert st == {'current': 'Shrimp Tacos', 'queue': ['Beef and Broccoli']}, st

    # Not for us -> remembered and sent with the next refill; Beef comes back in
    await choose('no')
    assert await ev("()=>aiSuggestState().rejected.includes('Shrimp Tacos')&&buildAiJobRequest('suggest').includes('Shrimp Tacos')")
    await open_idea()
    text = await card.inner_text()
    assert 'Beef and Broccoli' in text and 'Last idea' in text and 'Get more' in text, text

    # No dot on the Ask AI tab, even with an unseen idea
    await ev("()=>{const s=aiSuggestState();s.seen=false;saveAiSuggestState(s);aiTabActive=false;render()}"); await pg.wait_for_timeout(300)
    assert await pg.locator('#mealBottomNav .ai-suggest-dot').count() == 0
    await pg.locator('#mealBottomNav [data-destination="ai"]').click(); await pg.wait_for_timeout(500)

    # Try this week -> saved and the Schedule dialog opens
    await choose('try')
    assert await pg.get_by_text('Schedule Beef and Broccoli').count() == 1
    assert await ev("()=>meals.some(m=>m.name==='Beef and Broccoli'&&m.aiRecipe)")
    await pg.locator('[aria-label="Cancel scheduling"]').click(); await pg.wait_for_timeout(300)
    await open_idea()
    assert 'No ideas waiting' in await card.inner_text()

    # Pin -> saved to AI recipes and the group chooser opens
    await ev("()=>{const s=aiSuggestState();s.queue.push({name:'Pea Soup',ingredients:['1 cup peas'],instructions:[{type:'step',text:'Simmer.'}]});saveAiSuggestState(s);renderList({readOnly:true})}"); await pg.wait_for_timeout(300)
    await choose('pin')
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
