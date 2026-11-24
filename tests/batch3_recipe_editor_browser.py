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
 closeEditor:()=>{editId=null;render()},
 state:()=>[editId,recipeViewer?recipeViewer.mealId:null]
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch3.seed()')
    # Viewer -> Edit recipe (2026-11-23): opens the full editor (sections collapsed); Cancel reopens the recipe.
    p.evaluate('batch3.viewerEdit()')
    p.wait_for_timeout(500)
    assert p.evaluate('batch3.state()') == [2, None], p.evaluate('batch3.state()')
    states = p.locator('#editor details.meal-editor-section').evaluate_all('(es)=>es.filter(e=>!e.classList.contains("meal-editor-serve")).map(e=>e.open)')
    assert states and not any(states), states
    assert p.locator('#editor .recipe-source-site').text_content() == 'seriouseats.com'
    sb.shot(p, name, 'batch3-viewer-editor')
    p.locator('#editor #cancel').click()
    p.wait_for_timeout(500)
    assert p.evaluate('batch3.state()') == [None, '2'], p.evaluate('batch3.state()')
    p.evaluate('batch3.closeViewer()')
    p.wait_for_timeout(200)
    # Main editor: same source row; empty link shows a pencil to add one.
    p.evaluate('batch3.noLink()')
    p.evaluate('batch3.editor(3)')
    row = p.locator('#editor .recipe-source-row')
    assert row.locator('.recipe-source-empty').is_visible() and row.get_by_role('button', name='Add recipe link', exact=True).count() == 1
    p.evaluate('batch3.closeEditor()')
    p.wait_for_timeout(200)
    p.evaluate('batch3.editor(2)')
    assert p.locator('#editor .recipe-source-site').text_content() == 'seriouseats.com'
    # The Link Steps step picker was replaced by step chips on each ingredient (see part3a_step_chips_browser.py).
    assert p.locator('#recipeIngredientLinks').is_hidden()
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 3: source row, viewer pencil opens full editor and returns, step picker', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
