"""Batch 6: split-view step/ingredient sync — better matching + "For this step" box.

Fixture mirrors the real phone example (Mild Chili-Garlic Chicken Broth Bowls step 5).
Run: python3 tests/recipe_sync_matching_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

ING = ['3 tbsp olive oil, divided', '1 lb boneless skinless chicken thighs', '1 1/2 tsp curry powder, divided',
       '3/4 tsp garlic powder, divided', '4 cloves garlic, minced', '1 cup dairy-free, soy-free chicken stock',
       '1 can (13.5 oz) full-fat coconut milk', '1 tsp salt', '2 cups cooked rice']
STEPS = ['Toss the chicken with 1 1/2 tbsp olive oil, 1 1/2 tsp curry powder and 3/4 tsp garlic powder; set aside.',
         'Warm the remaining 1 1/2 tbsp olive oil in a pan. Add minced garlic, remaining curry powder and remaining garlic powder, then pan juices, chicken stock and coconut milk.',
         'Serve over rice with a pinch of salt.']
sb.fixture.HOOK += '''window.sync6={
 fixture:(ing,steps)=>{const m=meals.find(m=>m.id===2);m.ingredients=ing;m.instructions=steps.map(text=>({type:'step',text}));m.ingredientStepLinks=[];return m.id},
 matches:()=>{const m=meals.find(m=>m.id===2),items=recipeAssociationItems(m),r=recipeIngredientMatches(m),t=new Map(items.ingredients.map(i=>[i.token,i.text]));return items.steps.map(s=>(r.get(s.token)||[]).map(x=>t.get(x)))},
 manual:()=>{const m=meals.find(m=>m.id===2),items=recipeAssociationItems(m);m.ingredientStepLinks=[{step:items.steps[1].token,ingredients:[items.ingredients[7].token]}]},
 open:()=>{recipeViewPrefs.mode='split';recipeViewPrefs.syncIngredients=true;saveRecipeViewPrefs();openSavedMealRecipe(meals.find(m=>m.id===2))},
 pin:i=>{const steps=[...recipeViewer.content.querySelectorAll('.recipe-instructions-pane [data-cooking-token]')];recipeViewer.syncGeometryHold=false;recipeViewer.syncToInstruction(steps[i].dataset.cookingToken)},
 box:()=>[...document.querySelectorAll('.recipe-step-box .cooking-item')].map(x=>x.textContent),
 full:()=>[...document.querySelectorAll('.recipe-viewer-ingredients [data-cooking-token]')].map(x=>x.textContent),
 lit:()=>[...document.querySelectorAll('.recipe-viewer-ingredients .recipe-sync-relevant')].map(x=>x.textContent)
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('([i,s])=>sync6.fixture(i,s)', [ING, STEPS])
    steps = p.evaluate('sync6.matches()')
    joined = ' | '.join(steps[1])
    for needle in ['olive oil', 'minced', 'curry powder', 'garlic powder', 'chicken stock', 'coconut milk']:
        assert needle in joined, (needle, steps[1])
    for bad in ['rice', 'salt', 'thighs']:
        assert bad not in joined, (bad, steps[1])
    assert any('thighs' in x for x in steps[0]) and not any('stock' in x for x in steps[0]), steps[0]
    assert any('salt' in x for x in steps[2]) and any('rice' in x for x in steps[2]), steps[2]
    # Box: shows the current step's ingredients together; full list keeps order and highlights.
    p.evaluate('sync6.open()')
    p.wait_for_selector('.recipe-ingredients-pane .recipe-viewer-ingredients')
    order = p.evaluate('sync6.full()')
    p.evaluate('sync6.pin(1)')
    p.wait_for_function('document.querySelectorAll(".recipe-step-box .cooking-item").length>=6')
    box, lit = p.evaluate('sync6.box()'), p.evaluate('sync6.lit()')
    assert sorted(box) == sorted(lit) and any('coconut milk' in x for x in box), (box, lit)
    assert p.evaluate('sync6.full()') == order, 'full list must not reorder'
    assert p.evaluate("document.querySelector('.recipe-step-box').nextElementSibling.classList.contains('recipe-viewer-ingredients')")
    sb.shot(p, name, 'batch6-step-box')
    assert p.evaluate("(()=>{const b=document.querySelector('.recipe-step-box').getBoundingClientRect(),q=document.querySelector('.recipe-ingredients-pane').getBoundingClientRect();return b.top>=q.top-1})()"), 'box scrolled into view'
    # Tapping in the box is the same state as tapping the full-list item.
    full_btn = p.locator('.recipe-viewer-ingredients [data-cooking-token]', has_text='coconut milk')
    before = full_btn.get_attribute('class') + str(full_btn.get_attribute('aria-pressed'))
    p.locator('.recipe-step-box .cooking-item', has_text='coconut milk').click()
    p.wait_for_timeout(300)
    full_btn = p.locator('.recipe-viewer-ingredients [data-cooking-token]', has_text='coconut milk')
    after = full_btn.get_attribute('class') + str(full_btn.get_attribute('aria-pressed'))
    assert before != after, (before, after)
    # Manual links always win.
    p.evaluate('sync6.manual()')
    manual = p.evaluate('sync6.matches()')[1]
    assert manual == ['1 tsp salt'] if len(manual) == 1 else False, manual
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 6: matching, step box, same tick state, manual links win', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
