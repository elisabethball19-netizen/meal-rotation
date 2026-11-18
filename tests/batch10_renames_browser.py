"""Batch 10: approved renames — In Rotation/Ideas -> Regulars/Off menu (labels only; saved status values
unchanged), Meals heading This Week's Meals / Next Week's Meals, no "rotating" wording on touched labels.

Run: python3 tests/batch10_renames_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch10={
 groups:()=>{showTop=false;groceryTabActive=false;allMealsActive=false;masterExpansionInitialized=true;masterExpandedCategories.clear();masterExpandedCategories.add('Rice');render()},
 home:w=>{showTop=true;groceryTabActive=false;allMealsActive=false;rotationWeekOffset=w;render()},
 editor:()=>openEditor(2),
 status:()=>meals.find(m=>m.id===2).recipeStatus||null,
 rotation:()=>meals.find(m=>m.id===2).rotation
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch10.home(0)')
    assert p.locator('.meal-plan-title').text_content() == 'This Week’s Meals'
    p.evaluate('batch10.home(1)')
    assert p.locator('.meal-plan-title').text_content() == 'Next Week’s Meals'
    p.evaluate('batch10.groups()')
    text = p.locator('#list').inner_text()
    assert 'Regulars' in text and 'In Rotation' not in text and 'Ideas' not in text, text[:500]
    sb.shot(p, name, 'batch10-groups')
    status_before, rot_before = p.evaluate('batch10.status()'), p.evaluate('batch10.rotation()')
    p.evaluate('batch10.editor()')
    ed = p.locator('#editor')
    assert ed.get_by_text('Regulars', exact=True).count() >= 1 and ed.get_by_text('Off menu', exact=True).count() >= 1, ed.inner_text()[:400]
    assert 'In Rotation' not in ed.inner_text() and 'Ideas' not in ed.inner_text()
    sb.shot(p, name, 'batch10-editor')
    assert p.evaluate('batch10.status()') == status_before and p.evaluate('batch10.rotation()') == rot_before
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 10: Regulars/Off menu labels, This/Next Week’s Meals heading, data unchanged', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
