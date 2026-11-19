"""Part 3a: step chips in the recipe editor - automatic step chips, dividers between steps, picker with
expandable step text, split amounts into per-step lines (grocery list still one item), reset to automatic,
Link Steps section gone.

Run: python3 tests/part3a_step_chips_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402
import recipe_sync_matching_browser as rs  # noqa: E402  (adds the sync6 hooks)

ING = ['3 tbsp olive oil, divided', '1 lb boneless skinless chicken thighs', '3 tsp curry powder, divided',
       '4 cloves garlic, minced', '1 cup chicken stock', 'Cilantro, to serve']
STEPS = ['Toss the chicken with 1 1/2 tbsp olive oil and 2 tsp curry powder; set aside.',
         'Warm the remaining olive oil. Add minced garlic and the chicken stock.',
         'Stir in the remaining curry powder and simmer.']


sb.fixture.HOOK += '''window.p3a={groceries:()=>{const plan=mealPlans.find(p=>p.id===activePlanId),m=meals.find(m=>m.id===2);showTop=true;allMealsActive=false;groceryTabActive=true;render()}};'''


def chip(p, text):
    return p.locator('.step-chip-row', has=p.locator('.step-chip-text', has_text=text)).locator('.step-chip')


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('([i,s])=>sync6.fixture(i,s)', [ING, STEPS])
    p.evaluate('sync6.pick()')
    p.evaluate('sync6.editor()')
    p.locator('#editorIngredientsSection > summary').click(position={'x': 12, 'y': 12})
    p.wait_for_timeout(400)
    assert p.locator('#ingredientStepView').is_visible()
    assert not p.locator('#ingredients').is_visible(), 'text box hidden in step view'
    assert p.locator('#recipeIngredientLinks').is_hidden() and p.get_by_role('button', name='Sort by steps').count() == 0
    rows = p.locator('.step-chip-row .step-chip-text').all_inner_texts()
    assert rows[-1] == 'Cilantro, to serve' and chip(p, 'Cilantro').inner_text() == '+ Step', rows
    assert chip(p, 'curry powder').inner_text() == 'Steps 1, 3'
    assert chip(p, 'chicken stock').inner_text() == 'Step 2'
    assert p.locator('.step-chip-divider').count() >= 2
    assert p.locator('.step-chip-heading').count() == 0, 'no Step N headings'
    sb.shot(p, name, 'part3a-chips')
    # Picker: step text expands in place; split amounts prefill from the steps (2 tsp + remaining 1 tsp).
    chip(p, 'curry powder').click()
    pick = p.locator('.step-chip-picker')
    assert pick.is_visible() and pick.locator('input[type=checkbox]:checked').count() == 2
    more = pick.get_by_role('button', name='Show full step 1')
    more.click()
    assert p.locator('.step-chip-option-text.expanded').count() == 1
    amounts = pick.locator('.step-chip-amount')
    assert amounts.count() == 2, amounts.count()
    vals = amounts.evaluate_all('xs=>xs.map(x=>x.value)')
    assert vals == ['2 tsp', '1 tsp'], vals
    amounts.nth(0).fill('2½ tsp')
    assert 'Adds up to' in pick.locator('.step-chip-note').inner_text()
    amounts.nth(0).fill('2 tsp')
    sb.shot(p, name, 'part3a-picker')
    pick.get_by_role('button', name='Save steps').click()
    p.wait_for_timeout(200)
    lines = p.evaluate("document.querySelector('#ingredients').value").split('\n')
    assert '2 tsp curry powder' in lines and '1 tsp curry powder, remaining' in lines and '3 tsp curry powder, divided' not in lines, lines
    assert chip(p, '2 tsp curry powder').inner_text() == 'Step 1' and chip(p, 'curry powder, remaining').inner_text() == 'Step 3'
    # Give cilantro a step, then reset it to automatic.
    chip(p, 'Cilantro').click()
    p.locator('.step-chip-picker input[type=checkbox]').nth(2).check()
    p.locator('.step-chip-picker').get_by_role('button', name='Save steps').click()
    assert chip(p, 'Cilantro').inner_text() == 'Step 3'
    chip(p, 'Cilantro').click()
    p.locator('.step-chip-picker').get_by_role('button', name='Reset to automatic').click()
    assert chip(p, 'Cilantro').inner_text() == '+ Step'
    # Text mode toggle shows the plain text box.
    p.get_by_role('button', name='Edit ingredients as text').click()
    p.wait_for_timeout(200)
    assert p.locator('#ingredients').is_visible() and p.locator('#ingredientStepView').is_hidden()
    p.get_by_role('button', name='Show ingredients by step').click()
    assert p.locator('#ingredientStepView').is_visible()
    # Save: lines + links stored; viewer matches per step; grocery list keeps one curry item.
    p.locator('#editor').get_by_role('button', name='Save', exact=True).click()
    p.wait_for_timeout(300)
    rec = p.evaluate('sync6.record()')
    assert '2 tsp curry powder' in rec['ingredients'] and '1 tsp curry powder, remaining' in rec['ingredients'], rec['ingredients']
    m = p.evaluate('sync6.matches()')
    assert '2 tsp curry powder' in m[0] and not any('curry' in x for x in m[1]) and '1 tsp curry powder, remaining' in m[2], m
    picks = p.evaluate('sync6.picks()')
    assert '2 tsp curry powder' in picks and '1 tsp curry powder, remaining' in picks, picks
    if p.evaluate("typeof getMasterGroceryItems==='function'"):
        curry = p.evaluate("[...getMasterGroceryItems(getGroceryContributions(true,'rotation')).values()].filter(i=>/curry/.test(i.line)).map(i=>i.line)")
        assert len(curry) == 1 and curry[0].startswith('3'), curry
    p.evaluate('p3a.groceries()'); p.wait_for_timeout(400)
    rows = p.locator('.grocery-ingredient-name', has_text='curry')
    assert rows.count() == 1, rows.all_inner_texts()
    assert '(' not in rows.first.inner_text(), rows.first.inner_text()
    assert rows.first.locator('xpath=ancestor::*[1]').locator('.grocery-recipe-link').count() == 1
    sb.shot(p, name, 'part3a-grocery')
    assert not errors, errors
    c.close()
    print('PASS', name, 'part 3a: step chips, picker, split amounts, reset, text toggle, save, one grocery item', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
