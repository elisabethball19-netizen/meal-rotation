"""Off menu -> Regulars opens 'Ingredients to include in your weekly shopping list' first (2026-11-19).

- Suggested switches for a recipe with no saved choices: meat/produce/one-offs on; staples off;
  condiments off only when used in 3+ other Regulars.
- Saved choices are never changed.
- X cancels the move; check saves choices and moves (Meal Groups arrow and recipe editor).

Run: python3 tests/regulars_ingredients_browser.py   (screenshots in /tmp/regulars)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/regulars')
OUT.mkdir(parents=True, exist_ok=True)

LINES = ['1 lb chicken thighs', '2 tbsp fish sauce', '1 tbsp oyster sauce', '1 tsp salt', '1/2 tsp black pepper',
         '2 tbsp olive oil', '3 cloves garlic, minced', '1 onion, diced', '1 cup jasmine rice', '1 tsp ground cumin',
         '2 tsp dried oregano', '1 bunch fresh cilantro', '1 can coconut milk', '1 red bell pepper, sliced',
         '1 tbsp brown sugar', '1 tbsp rice vinegar']
EXPECT_ON = ['1 lb chicken thighs', '1 tbsp oyster sauce', '3 cloves garlic, minced', '1 onion, diced', '1 cup jasmine rice',
             '1 bunch fresh cilantro', '1 can coconut milk', '1 red bell pepper, sliced']

sb.fixture.HOOK += '''window.reg={
 setup:(lines)=>{const rice=meals.filter(m=>m.cat==='Rice'&&m.rotation);const t=rice.find(m=>!getDisplayedWeekdayMeals().some(e=>String(e.meal.id)===String(m.id)));t.rotation=false;t.ingredients=[...lines];
  for(const m of rice.filter(m=>m!==t).slice(0,3))m.ingredients=[...(m.ingredients||[]),'1 tbsp fish sauce'];
  const sel=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');delete sel[String(t.id)];localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(sel));persist();return t.name},
 suggest:name=>suggestedGroceryLines(meals.find(m=>m.name===name)),
 status:name=>recipeStatus(meals.find(m=>m.name===name)),
 saved:name=>JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')[String(meals.find(m=>m.name===name).id)]||null,
 setSaved:(name,lines)=>{const sel=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');const m=meals.find(m=>m.name===name);m.rotation=false;persist();sel[String(m.id)]=lines;localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(sel))},
 groups:()=>{showTop=false;groceryTabActive=false;allMealsActive=false;masterExpansionInitialized=true;masterExpandedCategories.add('Rice');setGroupPageSectionOpen('weekly',true);setMasterRecipeSectionOpen('Rice','up-next',true);render()},
 edit:name=>{const m=meals.find(m=>m.name===name);openEditor(m.id)}
};'''


def chooser(p):
    return p.locator('[role=dialog][aria-label="Edit groceries"]')


def on_lines(p):
    return chooser(p).locator('input.grocery-include-switch').evaluate_all('xs=>xs.filter(x=>x.checked).map(x=>x.getAttribute("aria-label").replace(/^Include /,""))')


def arrow(p, recipe):
    a = p.get_by_role('button', name='Move %s to Regulars' % recipe)
    if not a.count() or not a.first.is_visible():
        p.get_by_role('button', name='Recipe actions for ' + recipe).first.click()
    return p.get_by_role('button', name='Move %s to Regulars' % recipe).first


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    recipe = p.evaluate('l=>reg.setup(l)', LINES)
    assert sorted(p.evaluate('n=>reg.suggest(n)', recipe)) == sorted(EXPECT_ON), p.evaluate('n=>reg.suggest(n)', recipe)

    # Meal Groups arrow: the meal moves first, then the selector opens (setting on by default).
    p.evaluate('reg.groups()')
    arrow(p, recipe).click()
    chooser(p).wait_for()
    assert p.evaluate('n=>reg.status(n)', recipe) == 'rotation', 'meal must already be in Regulars when the selector opens'
    assert chooser(p).locator('h3').text_content() == 'Ingredients to include in your weekly shopping list'
    assert sorted(on_lines(p)) == sorted(EXPECT_ON), on_lines(p)
    p.screenshot(path=str(OUT / (tag + '-popup.png')))
    chooser(p).get_by_role('button', name='Cancel').click()
    p.wait_for_timeout(200)
    assert p.evaluate('n=>reg.status(n)', recipe) == 'rotation' and p.evaluate('n=>reg.saved(n)', recipe) is None

    # Setting off: the meal just moves, no selector.
    p.evaluate("localStorage.setItem('mealRotationAutoIngredientSelectorV1','off')")
    p.evaluate('([n,l])=>reg.setSaved(n,l)', [recipe, EXPECT_ON])
    p.evaluate('reg.groups()')
    arrow(p, recipe).click()
    p.wait_for_timeout(700)
    assert p.evaluate('n=>reg.status(n)', recipe) == 'rotation' and chooser(p).count() == 0
    p.evaluate("localStorage.removeItem('mealRotationAutoIngredientSelectorV1')")

    # Saved choices are never changed: a recipe with saved choices opens with exactly those.
    p.evaluate('([n,l])=>reg.setSaved(n,l)', [recipe, ['2 tsp dried oregano']])
    p.evaluate('reg.groups()')
    arrow(p, recipe).click()
    chooser(p).wait_for()
    assert on_lines(p) == ['2 tsp dried oregano'], on_lines(p)
    chooser(p).get_by_role('button', name='Cancel').click()

    # Recipe editor: switching to Regulars and saving moves the meal, then opens the selector.
    p.evaluate('([n,l])=>reg.setSaved(n,l)', [recipe, ['2 tsp dried oregano']])
    p.evaluate('n=>reg.edit(n)', recipe)
    p.locator('#recipeStatus label', has_text='Regulars').click()
    p.locator('#save').click()
    chooser(p).wait_for()
    chooser(p).get_by_role('button', name='Save').click()
    p.wait_for_timeout(500)
    assert p.evaluate('n=>reg.status(n)', recipe) == 'rotation', 'editor save should finish the move'
    assert p.evaluate('n=>reg.saved(n)', recipe) == ['2 tsp dried oregano']
    assert not errors, errors
    c.close()
    print('PASS', name, 'Regulars move: moves first, selector after, setting off, saved choices kept, editor path', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
