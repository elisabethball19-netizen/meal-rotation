"""Search meals -> "Show in Meal Groups" (2026-11-19).

Covers a Weekly-group recipe, an Off menu recipe (its list opens), an Unassigned recipe, a recipe shared across
two groups (goes to the Weekly copy) and that tapping the name still opens the recipe.

Run: python3 tests/search_locate_browser.py   (screenshots in /tmp/locate)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/locate')
OUT.mkdir(parents=True, exist_ok=True)

sb.fixture.HOOK += '''window.loc={
 setup:()=>{const rice=meals.filter(m=>m.cat==='Rice');const off=rice.find(m=>!getDisplayedWeekdayMeals().some(e=>String(e.meal.id)===String(m.id)));off.rotation=false;
  meals.push({id:9801,name:'Lonely Unassigned Stew',cat:'',ingredients:['1 onion'],rotation:false},{id:9802,name:'Another Loose Recipe',cat:'',ingredients:[],rotation:false});
  const veg=meals.find(m=>m.cat==='Vegetables');veg.linkGroup='share-test';meals.push({...JSON.parse(JSON.stringify(veg)),id:9803,cat:'Potatoes',linkGroup:'share-test'});
  const values=JSON.parse(localStorage.getItem(GROUP_ROTATION_KEY)||'{}');values[groupIdentity('Vegetables',true)]=false;localStorage.setItem(GROUP_ROTATION_KEY,JSON.stringify(values));
  persist();showTop=false;groceryTabActive=false;allMealsActive=false;render();
  return {regular:rice.find(m=>m.rotation&&m!==off).name,off:off.name,shared:veg.name,vegId:String(veg.id)}},
 search:()=>openMealSearch(),
 found:id=>{const rows=[...document.querySelectorAll('#list [data-meal-id]')].filter(el=>el.dataset.mealId===String(id)&&el.getClientRects().length);const row=rows[0];if(!row)return null;const r=row.getBoundingClientRect();return {cat:row.closest('.master-category-card')?.dataset.category??'',flash:row.classList.contains('search-locate-flash'),inView:r.top>=0&&r.bottom<=innerHeight,groups:!showTop}},
 id:name=>String(meals.find(m=>m.name===name&&(name!=='x')).id),
 viewer:()=>!!recipeViewer
};'''


def locate(p, query, nth=0):
    p.evaluate('loc.search()')
    dlg = p.locator('[role=dialog][aria-label="Search meals"]')
    dlg.get_by_label('Search meal names').fill(query)
    dlg.locator('.recipe-search-locate').nth(nth).click()
    p.wait_for_timeout(900)


def run(browser, name):
    tag = name.split('.')[0]
    c, p, errors, _ = sb.open_page(browser, name)
    info = p.evaluate('loc.setup()')
    p.evaluate('follow126.home()')  # start from the Meals page: locate must switch to Meal Groups
    # Weekly-group Regulars recipe.
    locate(p, info['regular'])
    got = p.evaluate('id=>loc.found(id)', p.evaluate('n=>loc.id(n)', info['regular']))
    assert got and got['cat'] == 'Rice' and got['flash'] and got['inView'] and got['groups'], got
    p.screenshot(path=str(OUT / (tag + '-regular.png')))
    # Off menu recipe: its list opens.
    locate(p, info['off'])
    got = p.evaluate('id=>loc.found(id)', p.evaluate('n=>loc.id(n)', info['off']))
    assert got and got['cat'] == 'Rice' and got['flash'] and got['inView'], got
    p.screenshot(path=str(OUT / (tag + '-offmenu.png')))
    # Unassigned recipe (flat Unassigned list).
    locate(p, 'Lonely Unassigned')
    got = p.evaluate('id=>loc.found(id)', '9801')
    assert got and got['cat'] == '' and got['flash'] and got['inView'], got
    # Shared recipe: the non-weekly (Vegetables) copy's button goes to the Weekly copy (Potatoes).
    p.evaluate('loc.search()')
    dlg = p.locator('[role=dialog][aria-label="Search meals"]')
    dlg.get_by_label('Search meal names').fill(info['shared'])
    rows = dlg.locator('button[data-meal-id]').evaluate_all('xs=>xs.map(x=>x.dataset.mealId)')
    assert set(rows) == {info['vegId'], '9803'}, rows
    dlg.locator('.recipe-search-locate').nth(rows.index(info['vegId'])).click()
    p.wait_for_timeout(900)
    got = p.evaluate('id=>loc.found(id)', '9803')
    assert got and got['cat'] == 'Potatoes' and got['flash'] and got['inView'], got
    # Tapping the name still opens the recipe.
    p.evaluate('loc.search()')
    dlg.get_by_label('Search meal names').fill(info['regular'])
    dlg.locator('button[data-meal-id]').first.click()
    p.wait_for_timeout(600)
    assert p.evaluate('loc.viewer()'), 'name tap should open the recipe'
    assert not errors, errors
    c.close()
    print('PASS', name, 'search locate: weekly, Off menu, Unassigned, shared copy, name tap opens recipe', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
