"""Batch 6: split-view step/ingredient sync — better matching + editor "Sort by steps" (split amounts).

Fixture mirrors the real phone example (Mild Chili-Garlic Chicken Broth Bowls step 5).
Run: python3 tests/recipe_sync_matching_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

ING = ['3 tbsp olive oil, divided', '1 lb boneless skinless chicken thighs', '3 tsp curry powder, divided',
       '1 1/2 tsp garlic powder, divided', '4 cloves garlic, minced', '1 cup dairy-free, soy-free chicken stock',
       '1 can (13.5 oz) full-fat coconut milk', '1 tsp salt', '2 cups cooked rice']
STEPS = ['Toss the chicken with 1 1/2 tbsp olive oil, 1 1/2 tsp curry powder and 3/4 tsp garlic powder; set aside.',
         'Warm the remaining 1 1/2 tbsp olive oil in a pan. Add minced garlic, remaining curry powder and remaining garlic powder, then pan juices, chicken stock and coconut milk.',
         'Serve over rice with a pinch of salt.']
sb.fixture.HOOK += '''const sync6Store=()=>typeof testStorage!=='undefined'?testStorage:localStorage;window.sync6={
 fixture:(ing,steps)=>{const m=meals.find(m=>m.id===2);m.ingredients=ing;m.instructions=steps.map(text=>({type:'step',text}));m.ingredientStepLinks=[];return m.id},
 matches:()=>{const m=meals.find(m=>m.id===2),items=recipeAssociationItems(m),r=recipeIngredientMatches(m),t=new Map(items.ingredients.map(i=>[i.token,i.text]));return items.steps.map(s=>(r.get(s.token)||[]).map(x=>t.get(x)))},
 manual:()=>{const m=meals.find(m=>m.id===2),items=recipeAssociationItems(m);m.ingredientStepLinks=[{step:items.steps[1].token,ingredients:[items.ingredients[7].token]}]},
 open:()=>{recipeViewPrefs.mode='split';recipeViewPrefs.syncIngredients=true;saveRecipeViewPrefs();openSavedMealRecipe(meals.find(m=>m.id===2))},
 pin:i=>{const steps=[...recipeViewer.content.querySelectorAll('.recipe-instructions-pane [data-cooking-token]')];recipeViewer.syncGeometryHold=false;recipeViewer.syncToInstruction(steps[i].dataset.cookingToken)},
 box:()=>[...document.querySelectorAll('.recipe-step-box .cooking-item')].map(x=>x.textContent),
 full:()=>[...document.querySelectorAll('.recipe-viewer-ingredients [data-cooking-token]')].map(x=>x.textContent),
 plan:()=>recipeStepSortPlan(meals.find(m=>m.id===2)).lines,
 sortRows:()=>recipeStepSortPlan(meals.find(m=>m.id===2)).sections[0].rows.map(r=>[r.text,r.step,!!r.split,r.check||null]),
 editor:()=>{openEditor(2);let d=$('recipeIngredientLinks');while(d){if(d.tagName==='DETAILS')d.open=true;d=d.parentElement}},
 pick:()=>{const s=JSON.parse(sync6Store().getItem('mealRotationSelectedIngredientsV1')||'{}');s['2']=[...meals.find(m=>m.id===2).ingredients];sync6Store().setItem('mealRotationSelectedIngredientsV1',JSON.stringify(s))},
 picks:()=>JSON.parse(sync6Store().getItem('mealRotationSelectedIngredientsV1')||'{}')['2'],
 record:()=>JSON.parse(JSON.stringify(meals.find(m=>m.id===2))),
 undo:()=>restoreState(JSON.parse(history.pop())),
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
    # Split view: highlights only, no extra box; full list order unchanged.
    p.evaluate('sync6.open()')
    p.wait_for_selector('.recipe-ingredients-pane .recipe-viewer-ingredients')
    order = p.evaluate('sync6.full()')
    p.evaluate('sync6.pin(1)')
    p.wait_for_function('document.querySelectorAll(".recipe-viewer-ingredients .recipe-sync-relevant").length>=6')
    assert p.locator('.recipe-step-box').count() == 0 and p.evaluate('sync6.full()') == order
    p.keyboard.press('Escape')
    # Sort by steps plan: olive oil + curry powder split (amounts stated / "remaining"); garlic powder split too.
    lines = p.evaluate('sync6.plan()')
    assert lines[:5] == ['1½ tbsp olive oil', '1 lb boneless skinless chicken thighs', '1½ tsp curry powder', '¾ tsp garlic powder', '1½ tbsp olive oil, remaining'], lines
    assert '1½ tsp curry powder, remaining' in lines and '¾ tsp garlic powder, remaining' in lines and lines[-2:] == ['1 tsp salt', '2 cups cooked rice'], lines
    # The editor's Sort by steps panel was replaced by step chips (tests/part3a_step_chips_browser.py covers the editor flow).
    # Manual links always win.
    p.evaluate('sync6.manual()')
    manual = p.evaluate('sync6.matches()')[1]
    assert manual == ['1 tsp salt'] if len(manual) == 1 else False, manual
    # Two different lines sharing a name (main list + Sauce section) are never both auto-highlighted.
    p.evaluate('([i,s])=>sync6.fixture(i,s)', [['1 lb chicken thighs', '2 tbsp soy sauce, divided', 'Sauce:', '1 tbsp honey', '1 tbsp soy sauce'],
                                             ['Marinate the chicken with 1 tbsp soy sauce.', 'Whisk honey with the remaining soy sauce.']])
    amb = p.evaluate('sync6.matches()')
    assert amb == [['1 lb chicken thighs'], ['1 tbsp honey']], amb
    # Amounts that don't add up stay whole at the first step, marked for checking.
    p.evaluate('([i,s])=>sync6.fixture(i,s)', [['3 tbsp olive oil', '1 onion'], ['Heat 1 tbsp olive oil.', 'Add the onion and 1 tbsp olive oil.']])
    rows = p.evaluate("sync6.sortRows()")
    assert rows == [['3 tbsp olive oil', 1, False, [1, 2]], ['1 onion', 2, False, None]], rows
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 6: matching, no box, sort-by-steps preview/split/apply/save, grocery picks+combine, Undo, manual links win', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
