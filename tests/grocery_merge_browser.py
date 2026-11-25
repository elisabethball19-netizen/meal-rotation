"""2026-11-24: shopping-list lines for the same ingredient that differ only in prep wording stay separate but are listed
next to each other ('Cilantro' / 'Chopped cilantro'; '1 medium onion' / '2 large onions'); products that differ stay apart.
Run: python3 tests/grocery_merge_browser.py
"""
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import start_week_window_browser as s

s.fixture.HOOK += '''window.gm={names:()=>[["Cilantro","Chopped cilantro"],["1 medium onion","2 large onions"],["ground beef","beef"],["Dry Mexican cheese","Provolone cheese"],["1 cup orange juice, freshly squeezed if possible","2 cups orange juice"],["4 cloves garlic","3 cloves garlic, minced"]].map(([a,b])=>[groceryMergeName(a),groceryMergeName(b)]),
 lines:()=>{const plan=mealPlans[0];const ids=[...new Set(getDisplayedWeekdayMealsForPlan(plan).map(e=>e.meal.id))];return ids.length},
 run:()=>{meals.find(m=>m.id===2).ingredients=['Cilantro','1 medium onion','2 cups orange juice, freshly squeezed','ground beef'];
  meals.find(m=>m.id===3).ingredients=['Chopped cilantro','2 large onions','1 cup orange juice','beef'];persist();
  const plan=mealPlans[0];const entries=getDisplayedWeekdayMealsForPlan(plan);
  const items=[...groceryAdjacentOrder(getMasterGroceryItems(getGroceryContributions(false,'both'))).values()].map(i=>i.line);return {items,n:entries.length}}};'''


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    p.clock.set_fixed_time(datetime(2026, 11, 17, 20, tzinfo=timezone.utc))
    p.evaluate('sw130.seed()')
    n = p.evaluate('gm.names()')
    assert n[0][0] == n[0][1], n[0]            # cilantro
    assert n[1][0] == n[1][1], n[1]            # onion sizes
    assert n[2][0] != n[2][1], n[2]            # ground beef stays apart
    assert n[3][0] != n[3][1], n[3]            # different cheeses
    assert n[4][0] == n[4][1], n[4]            # orange juice, prep after the comma ignored
    assert n[5][0] == n[5][1], n[5]            # garlic cloves
    r = p.evaluate('gm.run()')
    items = r['items']
    assert 'Cilantro' in items and 'Chopped cilantro' in items, items
    assert abs(items.index('Cilantro') - items.index('Chopped cilantro')) == 1, items
    assert items.index('ground beef') != items.index('beef') and abs(items.index('ground beef') - items.index('beef')) != 0
    assert len(items) >= 8, items   # nothing merged away
    print(name, r)
    assert not errors, errors
    c.close()
    print('PASS', name, 'similar ingredients listed next to each other, none merged', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
