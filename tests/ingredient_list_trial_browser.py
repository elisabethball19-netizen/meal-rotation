"""Ingredient-list trial (2026-11-24): recipe-view setting 'When a step has no ingredients' (Stay put / Show a note /
Preview what's next) in split view with Sync Ingredients on. Disposable origins for index.html and the test copy.
Run: python3 tests/ingredient_list_trial_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

SPICES = ['paprika', 'cumin', 'oregano', 'thyme', 'basil', 'sage', 'dill', 'cinnamon', 'nutmeg', 'ginger',
          'turmeric', 'coriander', 'fennel', 'mustard', 'allspice', 'cardamom', 'tarragon', 'marjoram']
ING = ['1 lb chicken'] + ['1 tsp ' + s for s in SPICES] + ['1 cup rice', '2 cups broth']
STEPS = ['Rub the chicken with ' + ', '.join(SPICES) + '.',
         'Preheat the oven to 400 degrees.',
         'Add the rice and broth and bake.']
sb.fixture.HOOK += '''window.trial={
 fixture:(ing,steps)=>{const m=meals.find(m=>m.id===2);m.ingredients=ing;m.instructions=steps.map(text=>({type:'step',text}));m.ingredientStepLinks=[];persist()},
 open:(mode)=>{recipeViewPrefs.mode='split';recipeViewPrefs.syncIngredients=true;if(mode)recipeViewPrefs.emptyStepMode=mode;else delete recipeViewPrefs.emptyStepMode;saveRecipeViewPrefs();openSavedMealRecipe(meals.find(m=>m.id===2))},
 pin:i=>{const steps=[...recipeViewer.content.querySelectorAll('.recipe-instructions-pane [data-cooking-token]')];recipeViewer.syncGeometryHold=false;recipeViewer.syncToInstruction(steps[i].dataset.cookingToken)},
 lit:()=>[...document.querySelectorAll('.recipe-viewer-ingredients .recipe-sync-relevant')].map(x=>x.textContent.trim()),
 note:()=>{const n=document.querySelector('.recipe-ingredients-pane .recipe-sync-step-note');return n&&!n.hidden?n.textContent:null},
 scroll:()=>document.querySelector('.recipe-ingredients-pane').scrollTop,
 visible:text=>{const pane=document.querySelector('.recipe-ingredients-pane').getBoundingClientRect(),b=[...document.querySelectorAll('.recipe-viewer-ingredients [data-cooking-token]')].find(x=>x.textContent.includes(text)).getBoundingClientRect();return b.top>=pane.top&&b.bottom<=pane.bottom},
 tap:text=>[...document.querySelectorAll('.recipe-viewer-ingredients [data-cooking-token]')].find(x=>x.textContent.includes(text)).click(),
 mode:()=>recipeViewPrefs.emptyStepMode||'stay',
 radiosDisabled:()=>document.querySelector('.recipe-empty-step-options').disabled,
 noSync:()=>{recipeViewPrefs.syncIngredients=false;saveRecipeViewPrefs();openSavedMealRecipe(meals.find(m=>m.id===2))},
 reset:()=>{document.querySelector('.recipe-ingredients-pane').scrollTop=0}
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.emulate_media(reduced_motion='reduce')
    p.evaluate('([i,s])=>trial.fixture(i,s)', [ING, STEPS])

    # Default = Stay put (current behavior): no note, no highlight, list does not move.
    p.evaluate('trial.open()')
    p.wait_for_selector('.recipe-ingredients-pane .recipe-viewer-ingredients')
    p.wait_for_timeout(800)  # let the viewer's first sync pass settle
    assert p.evaluate('trial.mode()') == 'stay'
    p.evaluate('trial.pin(0)'); p.wait_for_timeout(250)
    assert len(p.evaluate('trial.lit()')) >= 10
    p.evaluate('trial.reset()'); p.evaluate('trial.pin(1)'); p.wait_for_timeout(250)
    assert p.evaluate('trial.lit()') == [] and p.evaluate('trial.note()') is None and p.evaluate('trial.scroll()') == 0

    # Show a note, chosen through the settings radios.
    p.get_by_role('button', name='Recipe settings', exact=True).click()
    assert not p.evaluate('trial.radiosDisabled()')
    p.get_by_role('radio', name='Show a note', exact=True).check()
    p.get_by_role('button', name='Close settings', exact=True).click()
    assert p.evaluate('trial.mode()') == 'note'
    p.evaluate('trial.pin(1)'); p.wait_for_timeout(250)
    assert p.evaluate('trial.note()') == 'No ingredients for this step', p.evaluate('trial.note()')
    assert p.evaluate('trial.lit()') == []
    p.evaluate('trial.pin(2)'); p.wait_for_timeout(250)
    assert p.evaluate('trial.note()') is None and set(p.evaluate('trial.lit()')) == {'1 cup rice', '2 cups broth'}, p.evaluate('trial.lit()')

    # Preview what's next: scrolls to step 3's ingredients, unhighlighted, with a 'Next: step 3' cue.
    p.keyboard.press('Escape')
    p.evaluate("trial.open('next')")
    p.wait_for_selector('.recipe-ingredients-pane .recipe-viewer-ingredients')
    p.wait_for_timeout(800)  # let the viewer's first sync pass settle
    p.evaluate('trial.reset()'); p.evaluate('trial.pin(1)'); p.wait_for_timeout(300)
    assert p.evaluate('trial.note()') == 'Next: step 3', p.evaluate('trial.note()')
    assert p.evaluate('trial.lit()') == []
    assert p.evaluate('trial.scroll()') > 0 and p.evaluate("trial.visible('rice')"), p.evaluate('trial.scroll()')
    # Once those later ingredients are done, the list stays put.
    p.evaluate("trial.tap('rice')"); p.evaluate("trial.tap('broth')"); p.wait_for_timeout(1500)
    p.evaluate('trial.pin(0)'); p.wait_for_timeout(300)
    before = p.evaluate('trial.scroll()')
    p.evaluate('trial.pin(1)'); p.wait_for_timeout(300)
    assert p.evaluate('trial.note()') is None and p.evaluate('trial.scroll()') == before, (before, p.evaluate('trial.scroll()'))

    # Saved choice survives reload; radios are disabled (note hidden) when Sync Ingredients is off.
    p.reload(); p.wait_for_function('window.trial')
    assert p.evaluate('trial.mode()') == 'next'
    p.evaluate('trial.noSync()')
    p.wait_for_selector('.recipe-empty-step-options', state='attached')
    assert p.evaluate('trial.radiosDisabled()') and p.evaluate('trial.note()') is None

    assert not errors, errors
    c.close()
    print('PASS', name, 'ingredient-list trial: stay (default), note, next (scroll + cue, unhighlighted, done -> stay), saved, disabled without sync', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
