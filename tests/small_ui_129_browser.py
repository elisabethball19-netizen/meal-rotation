"""Issue 129: compact Meal Groups rows, fixed '!' slot, 'Groups' tab label, centered Ask AI choices,
Regulars-open / Off-menu-closed when a group is opened. Disposable regular/test origins.

Run: python3 tests/small_ui_129_browser.py  (screenshots go to /tmp/small129)
"""
import os
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402
import batch4_groups_page_browser  # noqa: E402,F401  (registers batch4 hooks)

sb.fixture.HOOK += '''window.small129={
 flag:()=>{const rice=meals.filter(m=>m.cat==='Rice');rice[0].needsTweaking=true;rice[2].needsTweaking=true;rice[2].name='Thai Red Curry Chicken With Extra Long Name Here';rice[1].lastCooked='2026-11-10';persist();renderList({readOnly:true})},
 render:()=>renderList({readOnly:true}),
 tabs:on=>{showMealPlanTabs=on;render()},
 aiMenu:()=>openAiRecipeMenu(meals[0]),
 sections:cat=>[masterRecipeSectionOpen(cat,'rotation'),masterRecipeSectionOpen(cat,'up-next')],
 setSections:(cat,a,b)=>{setMasterRecipeSectionOpen(cat,'rotation',a);setMasterRecipeSectionOpen(cat,'up-next',b)},
 collapseAll:()=>{masterExpansionInitialized=true;masterExpandedCategories.clear();renderList({readOnly:true})}
};'''
OUT = Path(os.environ.get('SMALL129_OUT', '/tmp/small129'))
OUT.mkdir(parents=True, exist_ok=True)
RICE = '.master-category-card[data-category="Rice"]'


def rect(p, selector, nth=0):
    return p.locator(selector).nth(nth).evaluate('e=>{const r=e.getBoundingClientRect();return {l:r.left,r:r.right,t:r.top,b:r.bottom,w:r.width,h:r.height}}')


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name, width=411, height=900)
    tag = name.split('.')[0]
    p.evaluate('batch4.groups()')
    p.evaluate('small129.flag()')
    # 5. Opening a group shows Regulars open and Off menu closed, even if saved state said otherwise.
    p.evaluate('small129.collapseAll()')
    p.evaluate("small129.setSections('Rice',false,true)")
    p.locator(RICE + ' button[aria-expanded]').first.click()
    p.wait_for_timeout(300)
    assert p.evaluate("small129.sections('Rice')") == [True, False], p.evaluate("small129.sections('Rice')")
    # A manual toggle during the visit stays.
    p.locator(RICE + ' .master-recipe-section[data-recipe-section="up-next"] button').first.click()
    p.wait_for_timeout(200)
    assert p.evaluate("small129.sections('Rice')")[1] is True
    p.evaluate('small129.render()')
    assert p.evaluate("small129.sections('Rice')")[1] is True
    p.evaluate("small129.setSections('Rice',true,false)")
    p.evaluate('small129.render()')
    p.wait_for_timeout(200)
    sb.shot(p, name, 'small129-groups')
    p.screenshot(path=str(OUT / (tag + '-groups.png')))
    # 1. Compact rows: a single-line row is clearly shorter than the old 78px.
    rows = p.locator(RICE + ' .master-recipe-section[data-recipe-section="rotation"] .master-category-meal')
    heights = [rows.nth(i).evaluate('e=>e.getBoundingClientRect().height') for i in range(rows.count())]
    assert min(heights) <= 70, heights
    for i in range(rows.count()):
        name_box = rows.nth(i).locator('.master-category-meal-name').first.evaluate('e=>e.getBoundingClientRect().bottom')
        cooked = rows.nth(i).locator('.group-last-cooked').first.evaluate('e=>e.getBoundingClientRect().top')
        assert cooked - name_box < 16, (i, cooked - name_box)
    # 3. '!' is in one slot: same x on every flagged row, left of the day label / chevron, clear of the name.
    flags = p.locator(RICE + ' .group-row-flag')
    assert flags.count() == 2, flags.count()
    boxes = [flags.nth(i).evaluate('e=>{const r=e.getBoundingClientRect();return [r.left,r.right,r.height]}') for i in range(2)]
    assert abs(boxes[0][0] - boxes[1][0]) < 0.6 and all(b[2] >= 43 for b in boxes), boxes
    for i in range(2):
        row = flags.nth(i).locator('xpath=ancestor::*[contains(@class,"master-category-meal")][1]')
        chevron = row.locator('.group-recipe-toggle').evaluate('e=>e.getBoundingClientRect().left')
        assert chevron - 36 <= boxes[i][1] <= chevron - 20, (boxes[i], chevron)
        day = row.locator('.master-meal-weekdays')
        if day.count():
            text_left = day.first.evaluate('e=>{const r=document.createRange();r.selectNodeContents(e);return r.getBoundingClientRect().left}')
            assert boxes[i][1] - 8 <= text_left - 3, ('icon clear of day label', boxes[i], text_left)
        names = row.locator('.master-category-meal-name')
        for j in range(names.count()):
            assert names.nth(j).evaluate('e=>e.getBoundingClientRect().right') <= boxes[i][0] + 1
    # Same slot on a row with no flag keeps the day label / chevron untouched (no '!' there).
    assert rows.count() - 2 == p.locator(RICE + ' .master-category-meal:not(:has(.group-row-flag))').count()
    # 4. Bottom bar label.
    p.evaluate('small129.tabs(true)')
    labels = p.evaluate("[...document.querySelectorAll('#mealBottomNav button')].map(b=>[b.querySelector('span').textContent,b.getAttribute('aria-label'),b.querySelector('span').getBoundingClientRect().height])")
    assert [l[0] for l in labels] == ['Meals', 'Week', 'Groups', 'Groceries', 'Ask AI'], labels
    assert labels[2][1] == 'Meal Groups' and all(l[2] < 17 for l in labels), labels
    p.evaluate("document.body.style.zoom='1.3'")
    assert all(l[2] < 24 for l in p.evaluate("[...document.querySelectorAll('#mealBottomNav button span')].map(s=>[0,0,s.getBoundingClientRect().height])")), 'label wraps at large size'
    p.evaluate("document.body.style.zoom=''")
    p.evaluate('small129.tabs(false)')
    labels = p.evaluate("[...document.querySelectorAll('#mealBottomNav button span')].map(s=>s.textContent)")
    assert labels == ['Meals', 'Meal Groups', 'Groceries', 'Ask AI'], labels
    # 2. Ask AI choices are centered both ways.
    p.evaluate('small129.aiMenu()')
    p.wait_for_selector('.ai-choice')
    for i in range(p.locator('.ai-choice').count()):
        btn = p.locator('.ai-choice').nth(i)
        css = btn.evaluate('e=>{const s=getComputedStyle(e);return [s.textAlign,s.justifyContent,s.alignItems]}')
        assert css == ['center', 'center', 'center'], css
        off = btn.evaluate('''e=>{const r=document.createRange();r.selectNodeContents(e);const t=r.getBoundingClientRect(),b=e.getBoundingClientRect();return [Math.abs((t.top+t.bottom)/2-(b.top+b.bottom)/2),Math.abs((t.left+t.right)/2-(b.left+b.right)/2)]}''')
        assert off[0] < 3 and off[1] < 3, off
    p.screenshot(path=str(OUT / (tag + '-ai-menu.png')))
    assert not errors, errors
    print('ok', name)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(**({'executable_path': '/usr/bin/chromium', 'args': ['--no-sandbox']} if os.path.exists('/usr/bin/chromium') else {}))
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
