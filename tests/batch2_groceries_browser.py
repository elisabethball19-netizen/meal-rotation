"""Batch 2 (grocery list part): shopping names drop non-shopping phrases, non-ingredient lines skipped
(grocery list + Edit groceries), user-edited names win, pencil on the item's own line, recipe lines
are checkbox + name only, multi-recipe pencil edits each recipe's amount.

Run: python3 tests/batch2_groceries_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

LINES = ['3 tbsp olive oil, divided', 'Kosher salt, to taste', '1 can (13.5 oz) full-fat coconut milk', '4 cloves garlic, minced',
         'SERVE WITH', 'Serve with steamed rice', 'Fresh cilantro, for garnish', '1 cup frozen peas', '2 cups shredded cabbage (see notes)']
sb.fixture.HOOK += '''const b2Store=()=>typeof testStorage!=='undefined'?testStorage:localStorage;window.batch2={
 text:l=>groceryShoppingText(l),skip:l=>groceryNonIngredientLine(l),
 seed:lines=>{const s=JSON.parse(b2Store().getItem('mealRotationSelectedIngredientsV1')||'{}');for(const m of meals){m.ingredients=['1 tbsp olive oil','1 onion'];s[String(m.id)]=[...m.ingredients]}
  b2Store().setItem('mealRotationSelectedIngredientsV1',JSON.stringify(s));b2Store().setItem('mealRotationGroceryPeriodV1','both');
  const ids=[...new Set(getGroceryContributions(false,'both').map(x=>String(x.mealId)))];const first=meals.find(m=>String(m.id)===ids[0]);first.ingredients=[...lines];s[ids[0]]=[...lines];
  b2Store().setItem('mealRotationSelectedIngredientsV1',JSON.stringify(s));persist();showTop=true;allMealsActive=false;groceryTabActive=true;render();return ids},
 items:()=>[...document.querySelectorAll('.master-grocery-item .grocery-ingredient-name')].map(n=>n.firstChild.textContent),
 chooser:id=>openTopIngredientChooser(meals.find(m=>String(m.id)===String(id))),
 recipe:id=>[...meals.find(m=>String(m.id)===String(id)).ingredients]
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    t = lambda s: p.evaluate('l=>batch2.text(l)', s)
    assert t('3 tbsp olive oil, divided') == '3 tbsp olive oil'
    assert t('Kosher salt, to taste') == 'Kosher salt'
    assert t('1 can (13.5 oz) full-fat coconut milk') == '1 can full-fat coconut milk'
    assert t('4 cloves garlic, minced') == '4 cloves garlic, minced'
    assert t('Fresh cilantro, for garnish') == 'Fresh cilantro'
    assert t('2 cups shredded cabbage (see notes)') == '2 cups shredded cabbage'
    assert t('1 tbsp butter, plus more for serving') == '1 tbsp butter'
    assert t('1 cup frozen peas') == '1 cup frozen peas'
    for line, skip in [('SERVE WITH', True), ('Serve with steamed rice', True), ('MSG', False), ('1 tsp MSG', False), ('SAUCE:', True), ('Kosher salt', False)]:
        assert p.evaluate('l=>batch2.skip(l)', line) is skip, line
    ids = p.evaluate('l=>batch2.seed(l)', LINES)
    assert len(ids) >= 2, ids
    items = p.evaluate('batch2.items()')
    joined = ' | '.join(items)
    assert 'Kosher salt' in items and '4 cloves garlic, minced' in items and '1 cup frozen peas' in items, items
    assert 'SERVE' not in joined.upper() and 'divided' not in joined and '(' not in joined and 'garnish' not in joined, items
    # Pencil sits on each item's own line; recipe lines show only checkbox + recipe name.
    rows = p.locator('.master-grocery-item')
    assert rows.count() == p.locator('.master-grocery-item>.grocery-item-edit').count()
    assert p.locator('.grocery-contribution .grocery-contribution-edit').count() == 0
    oil = rows.filter(has=p.locator('.grocery-ingredient-name', has_text='olive oil')).first
    oil.locator('.grocery-expand').click()
    lines = oil.locator('.grocery-contribution')
    assert lines.count() >= 2 and lines.first.locator('input[type=checkbox]').count() == 1
    sb.shot(p, name, 'batch2-grocery-list')
    # Multi-recipe pencil: one field per recipe with its own amount; saving edits only that recipe's wording.
    oil.locator('.grocery-item-edit').click()
    d = p.get_by_role('dialog', name='Edit grocery item', exact=True)
    fields = d.locator('.grocery-contribution-field input')
    assert fields.count() == lines.count()
    values = fields.evaluate_all('(es)=>es.map(e=>e.value)')
    assert '3 tbsp olive oil' in values and '1 tbsp olive oil' in values, values
    sb.shot(p, name, 'batch2-multi-editor')
    fields.nth(values.index('3 tbsp olive oil')).fill('3 tbsp extra virgin olive oil')
    d.get_by_role('button', name='Save grocery item', exact=True).click()
    items = p.evaluate('batch2.items()')
    assert any('extra virgin olive oil' in x for x in items) and any(x.endswith(' olive oil') and 'virgin' not in x for x in items), items
    # A user-edited name is never cleaned or replaced.
    assert '3 tbsp extra virgin olive oil' in items
    # Edit groceries (include editor) hides serve-with lines.
    p.evaluate('id=>batch2.chooser(id)', ids[0])
    dlg = p.get_by_role('dialog', name='Edit groceries', exact=True)
    dlg.wait_for(state='visible')
    text = dlg.inner_text()
    assert 'SERVE WITH' not in text and 'Serve with steamed rice' not in text and 'Kosher salt, to taste' in text, text[:400]
    # Cancel with no changes closes without a save prompt (hidden serve-with lines don't count as changes).
    dlg.get_by_role('button', name='Cancel', exact=True).click()
    p.wait_for_timeout(250)
    assert p.get_by_role('dialog', name='Edit groceries', exact=True).count() == 0, 'no save prompt without changes'
    p.evaluate('id=>batch2.chooser(id)', ids[0])
    dlg.wait_for(state='visible')
    # Include editor: toggles, intro sentence, no import controls or bulk trash, footer Deselect/Select/Save/Cancel.
    assert 'Choose which ingredients to add to your shopping list' in text  # heading replaces the intro sentence (2026-11-19)
    switches = dlg.get_by_role('switch')
    assert switches.count() == len([l for l in LINES if not p.evaluate('l=>batch2.skip(l)', l)]) and dlg.locator('input[type=checkbox]:not([role=switch])').count() == 0
    assert dlg.get_by_role('button', name='Import ingredients from photo').count() == 0 and dlg.get_by_role('button', name='Take photo of ingredients').count() == 0
    labels = dlg.locator('button[aria-label]').evaluate_all('(es)=>es.map(e=>e.getAttribute("aria-label"))')
    footer = [x for x in labels if x in ('Deselect all', 'Select all', 'Save', 'Cancel', 'Delete selected')]
    assert footer == ['Deselect all', 'Select all', 'Save', 'Cancel'], labels
    dlg.get_by_role('button', name='Deselect all', exact=True).click()
    assert not any(switches.evaluate_all('(es)=>es.map(e=>e.checked)'))
    dlg.get_by_role('button', name='Select all', exact=True).click()
    assert all(switches.evaluate_all('(es)=>es.map(e=>e.checked)'))
    sb.shot(p, name, 'batch2-include-editor')
    # Pencil renames only the shopping wording (staged until Save); trash turns the ingredient off; recipe unchanged.
    recipe_before = p.evaluate('id=>batch2.recipe(id)', ids[0])
    dlg.get_by_role('button', name='Edit shopping name for Kosher salt, to taste', exact=True).click()
    ed = p.get_by_role('dialog', name='Edit ingredient', exact=True)
    ed.get_by_role('textbox', name='Ingredient', exact=True).fill('Diamond Crystal kosher salt')
    ed.get_by_role('button', name='Save ingredient', exact=True).click()
    assert 'Diamond Crystal kosher salt' in dlg.inner_text() and 'Shopping list:' not in dlg.inner_text()  # row shows the new name, no subline
    dlg.get_by_role('button', name='Edit shopping name for Fresh cilantro, for garnish', exact=True).click()
    ed.get_by_role('button', name='Delete ingredient', exact=True).click()
    # Trash removes the row from the selector; 'Show removed' brings it back (switched off).
    assert dlg.get_by_role('switch', name='Include Fresh cilantro, for garnish', exact=True).count() == 0
    dlg.get_by_role('button', name='Show removed (1)', exact=True).click()
    assert not dlg.get_by_role('switch', name='Include Fresh cilantro, for garnish', exact=True).is_checked()
    sb.shot(p, name, 'batch2-include-rename')
    dlg.get_by_role('button', name='Save', exact=True).click()
    p.wait_for_timeout(300)
    items = p.evaluate('batch2.items()')
    assert 'Diamond Crystal kosher salt' in items and 'Kosher salt' not in items and 'Fresh cilantro' not in items, items
    assert p.evaluate('id=>batch2.recipe(id)', ids[0]) == recipe_before, 'recipe unchanged'
    p.locator('#undo').click()
    p.wait_for_timeout(300)
    items = p.evaluate('batch2.items()')
    assert 'Kosher salt' in items and 'Fresh cilantro' in items and 'Diamond Crystal kosher salt' not in items, items
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 2: shopping names, skipped lines, user names win, item pencil, recipe lines, multi-recipe editor, include editor', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
