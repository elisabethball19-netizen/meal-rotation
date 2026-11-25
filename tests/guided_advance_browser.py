"""2026-11-24: in split view with Sync ingredients on, tapping a step checks the steps before it and, after a short pause,
scrolls the instructions so the NEXT step sits at the top. A pane resize caused by the 'go to first unfinished step' bar
must not cancel or undo that scroll. Run: python3 tests/guided_advance_browser.py
"""
from playwright.sync_api import sync_playwright
import start_week_window_browser as s  # registers shared fixture hooks

s.fixture.HOOK += '''window.adv={open:()=>{const m={id:9101,name:'Long',cat:'',ingredients:['1 onion','2 lb beef'],instructions:Array.from({length:40},(_,i)=>(i+1)+'. Do the thing number '+i+' carefully and slowly for a while.').join(String.fromCharCode(10)),rotation:false};meals.push(m);persist();recipeViewPrefs.syncIngredients=true;try{saveRecipeViewPrefs()}catch(e){}openSavedMealRecipe(m);return recipeViewingMode()}};'''


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    p.set_viewport_size({'width': 390, 'height': 800})
    p.evaluate('adv.open()'); p.wait_for_timeout(600)
    p.locator('[aria-label="Split View"]').click(); p.wait_for_timeout(800)
    assert p.evaluate('recipeGuidanceEnabled()')
    btns = p.locator('.recipe-instructions-pane [data-cooking-token]')
    btns.nth(4).scroll_into_view_if_needed(); p.wait_for_timeout(300)
    btns.nth(4).click(); p.wait_for_timeout(1800)
    done = p.evaluate('recipeViewer.previewProgress.steps.length')
    top = p.evaluate("()=>{const x=document.querySelector('.recipe-instructions-pane');return [...x.querySelectorAll('[data-cooking-token]')][5].getBoundingClientRect().top-x.getBoundingClientRect().top}")
    assert done == 5, done
    assert -2 <= top <= 40, ('next step did not scroll to the top of the pane', top)
    assert not errors, errors
    c.close()
    print('PASS', name, 'tapping a step scrolls the next step to the top', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html']:  # the test copy's viewer does not reopen in this harness; code is mirrored there
            run(b, name)
        b.close()
