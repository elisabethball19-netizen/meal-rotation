"""Batch 3: recipe editor — source link row (site name + pencil, no link icon) in both editors,
viewer's Edit recipe opens with fields collapsed, app step picker replaces the native dropdown.

Run: python3 tests/batch3_recipe_editor_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch3={
 seed:()=>{const m=meals.find(m=>m.id===2);m.url='https://www.seriouseats.com/broth-bowls';m.originalRecipeUrl=m.url;delete m.recipeSourceHidden;m.ingredients=['1 tbsp olive oil','2 cups rice','1 tsp salt'];m.instructions=[{type:'step',text:'Warm the olive oil.'},{type:'step',text:'Add the rice and stir.'},{type:'step',text:'Season with salt.'}];m.ingredientStepLinks=[];persist()},
 noLink:()=>{const m=meals.find(m=>m.id===3);m.url='';m.originalRecipeUrl='';persist()},
 viewerEdit:()=>{openSavedMealRecipe(meals.find(m=>m.id===2));openViewedRecipeEditor()},
 editor:id=>{openEditor(id);let d=document.getElementById('recipeIngredientLinks');while(d){if(d.tagName==='DETAILS')d.open=true;d=d.parentElement}},
 renamePath:()=>appIconSvg.rename,
 closeViewer:()=>{if(recipeViewer)closeRecipeViewer()},
 closeEditor:()=>{editId=null;render()}
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch3.seed()')
    # Viewer -> Edit recipe: every edit section starts collapsed, even after one was left open.
    p.evaluate('batch3.viewerEdit()')
    d = p.get_by_role('dialog', name='Edit Recipe', exact=True)
    d.wait_for(state='visible')
    states = d.locator('details.viewer-editor-section').evaluate_all('(es)=>es.map(e=>e.open)')
    assert states and not any(states), states
    d.locator('details.viewer-editor-section summary').first.click()
    row = d.locator('.recipe-source-row')
    assert row.locator('.recipe-source-site').text_content() == 'seriouseats.com', row.inner_text()
    pencil = row.get_by_role('button', name='Edit recipe link', exact=True)
    assert pencil.inner_html().count('<path') == p.evaluate('batch3.renamePath()').count('<path') and 'Original recipe' not in row.inner_text()
    url = d.get_by_role('textbox', name='Recipe source link', exact=True)
    assert url.is_hidden()
    pencil.click()
    assert url.is_visible()
    sb.shot(p, name, 'batch3-viewer-editor')
    d.get_by_role('button', name='Cancel', exact=False).last.click() if d.get_by_role('button', name='Cancel', exact=False).count() else p.keyboard.press('Escape')
    p.wait_for_timeout(300)
    p.evaluate('batch3.closeViewer()')
    p.evaluate('batch3.viewerEdit()')
    d.wait_for(state='visible')
    assert not any(d.locator('details.viewer-editor-section').evaluate_all('(es)=>es.map(e=>e.open)')), 'collapsed on every opening'
    p.keyboard.press('Escape')
    p.wait_for_timeout(200)
    p.evaluate('batch3.closeViewer()')
    # Main editor: same source row; empty link shows a pencil to add one.
    p.evaluate('batch3.noLink()')
    p.evaluate('batch3.editor(3)')
    row = p.locator('#editor .recipe-source-row')
    assert row.locator('.recipe-source-empty').is_visible() and row.get_by_role('button', name='Add recipe link', exact=True).count() == 1
    p.evaluate('batch3.closeEditor()')
    p.wait_for_timeout(200)
    p.evaluate('batch3.editor(2)')
    assert p.locator('#editor .recipe-source-site').text_content() == 'seriouseats.com'
    # Step picker: no native select; list opens, choosing step 2 updates the picker and the checklist.
    links = p.locator('#recipeIngredientLinks')
    assert links.locator('select').count() == 0
    picker = links.get_by_role('button', name='Instruction step for ingredient links', exact=True)
    assert picker.inner_text().startswith('1.')
    picker.click()
    options = links.get_by_role('option')
    assert options.count() == 3
    sb.shot(p, name, 'batch3-step-picker')
    options.nth(1).click()
    assert links.get_by_role('option').count() == 0 and picker.inner_text().startswith('2.')
    checked = links.locator('.recipe-link-choices input:checked').evaluate_all('(es)=>es.map(e=>e.parentElement.textContent)')
    assert checked == ['2 cups rice'], checked
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 3: source row both editors, viewer edit collapsed, step picker', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
