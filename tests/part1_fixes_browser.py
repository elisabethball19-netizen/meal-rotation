"""Fix part 1: Edit groceries Cancel prompts, favorite heart stays on the name line, curry-powder step match,
"for today" To-Do wording, plain Serve with row in the recipe editor.

Run: python3 tests/part1_fixes_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402
import batch2_groceries_browser as b2  # noqa: E402
import recipe_sync_matching_browser  # noqa: E402,F401  (adds the sync6 hooks)

sb.fixture.HOOK += '''window.p1={
 heart:()=>{const m=meals.find(x=>x.cat);m.name='Thai Chicken Thukpa With Extra Long Name Here';m.favorite=true;m.needsTweaking=true;persist();showTop=false;allMealsActive=true;groceryTabActive=false;masterExpansionInitialized=true;masterExpandedCategories.clear();masterExpandedCategories.add(m.cat);for(const k of ['weekly','other','unassigned'])setGroupPageSectionOpen(k,true);render()},
 desc:offset=>{const d=new Date();d.setDate(d.getDate()+offset);return makeAheadTaskDescription({plan:{name:'Dinner'},entry:{day:'Monday',cat:''},scheduled:cookingLocalDate(d),task:{description:'Defrost chicken'},preview:false},true)},
 editor:()=>{const m=meals.find(x=>x.cat);showTop=false;allMealsActive=false;groceryTabActive=false;openEditor(m.id,false)}
};'''


def cancel_prompts(p, ids, change):
    p.evaluate('id=>batch2.chooser(id)', ids[0])
    dlg = p.get_by_role('dialog', name='Edit groceries', exact=True)
    dlg.wait_for(state='visible')
    change(dlg, p)
    dlg.get_by_role('button', name='Cancel', exact=True).click()
    p.wait_for_timeout(300)
    prompt = p.get_by_text('Save changes before closing?')
    shown = prompt.count() > 0
    if shown:
        p.get_by_role('button', name='No', exact=True).click()
        p.wait_for_timeout(200)
    return shown


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    ids = p.evaluate('l=>batch2.seed(l)', b2.LINES)
    # No change: no prompt.
    assert cancel_prompts(p, ids, lambda d, p: None) is False, 'no prompt without changes'
    # Toggling an ingredient switch off then Cancel prompts.
    assert cancel_prompts(p, ids, lambda d, p: d.get_by_role('switch').first.click()) is True, 'switch change should prompt'
    # Shopping-name edit then Cancel prompts.
    def rename(d, p):
        d.get_by_role('button', name='Edit shopping name for Kosher salt, to taste', exact=True).click()
        ed = p.get_by_role('dialog', name='Edit ingredient', exact=True)
        ed.get_by_role('textbox', name='Ingredient', exact=True).fill('Sea salt')
        ed.get_by_role('button', name='Save ingredient', exact=True).click()
    assert cancel_prompts(p, ids, rename) is True, 'shopping rename should prompt'
    # Favorite heart stays on the same line as a long name.
    p.evaluate('p1.heart()')
    p.wait_for_timeout(300)
    pos = p.evaluate("""()=>{const h=document.querySelector('.expanded-name-heart'),n=h.parentElement.firstElementChild,a=h.getBoundingClientRect(),b=n.getBoundingClientRect();return [a.top,a.bottom,b.top,b.bottom,a.left,b.right]}""")
    assert pos[0] < pos[3] - 4 and pos[1] > pos[2] + 4 and pos[4] >= pos[5] - 2, pos
    # Curry powder with leading descriptors matches the shorter step wording.
    p.evaluate('([i,s])=>sync6.fixture(i,s)', [['3 tsp mild yellow curry powder, divided', '1 tbsp olive oil'], ['Season with salt.', 'Stir in remaining 1 1/2 tsp curry powder and olive oil.']])
    m = p.evaluate('sync6.matches()')
    assert any('curry powder' in x for x in m[1]), m
    # To-Do wording for today / tomorrow / other days.
    assert p.evaluate('p1.desc(0)').endswith('for today’s dinner') or p.evaluate('p1.desc(0)').endswith('for today'), p.evaluate('p1.desc(0)')
    assert 'for tomorrow' in p.evaluate('p1.desc(1)') and 'for today' not in p.evaluate('p1.desc(1)')
    assert 'for Monday' in p.evaluate('p1.desc(3)') and 'today' not in p.evaluate('p1.desc(3)')
    # Recipe editor: Serve with is a label plus add button only (no Sides label, no chevron).
    p.evaluate('showMealPlanTabs=true;p1.editor()')
    p.wait_for_timeout(500)
    serve = p.locator('.meal-editor-serve')
    assert serve.count() == 1 and serve.get_by_role('button', name='Add side', exact=True).is_visible()
    assert serve.locator('.settings-chevron').count() == 0 and 'Sides' not in serve.inner_text(), serve.inner_text()
    sb.shot(p, name, 'part1-editor-serve')
    assert not errors, errors
    c.close()
    print('PASS', name, 'part 1: cancel prompt, heart line, curry match, for today, Serve with row', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
