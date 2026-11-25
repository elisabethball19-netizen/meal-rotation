"""2026-11-24: opening a recipe from a grocery item scrolls BOTH panes in split view. With a manual ingredient-step link the
linked step is used; with no link the first step the automatic matching says uses the ingredient is used.
Run: python3 tests/nav_fallback_browser.py
"""
from playwright.sync_api import sync_playwright
import start_week_window_browser as s

s.fixture.HOOK += '''window.nav={open:(linked)=>{const steps=Array.from({length:40},(_,i)=>(i+1)+'. Stir the pot number '+i+' slowly and carefully for a while until done.');steps[24]='25. Add the saffron threads and stir well until the broth turns golden.';const m={id:9201+(linked?1:0),name:'Nav',cat:'',ingredients:['2 cups rice','1 pinch saffron threads','3 cups water'],instructions:steps.join(String.fromCharCode(10)),rotation:false};meals.push(m);const it=cookingItemTokens(m);
 if(linked)m.ingredientStepLinks=[{step:it.steps.filter(x=>x.token)[30].token,ingredients:[it.ingredients[1].token]}];persist();recipeViewPrefs.mode='split';try{saveRecipeViewPrefs()}catch(e){}
 const target=groceryRecipeNavigation(m,{mealId:String(m.id),ingredientToken:it.ingredients[1].token,id:'x',planId:'p',day:'Monday',scheduledDate:'2026-11-30'});window.tg=target;window.stepIndex=it.steps.filter(x=>x.token).findIndex(x=>x.token===target?.stepToken);openSavedMealRecipe(m,null,null,target);return {step:window.stepIndex}},
 pos:()=>{const v=recipeViewer;const sp=v.content.querySelector('.recipe-instructions-pane');const n=[...sp.querySelectorAll('[data-cooking-token]')].find(e=>e.dataset.cookingToken===tg.stepToken);return Math.round(n.getBoundingClientRect().top-sp.getBoundingClientRect().top)}};'''


def run(browser, name):
    for linked, expect in ((False, 24), (True, 30)):
        c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
        p.set_viewport_size({'width': 390, 'height': 800})
        r = p.evaluate(f'nav.open({str(linked).lower()})'); p.wait_for_timeout(1200)
        top = p.evaluate('nav.pos()')
        assert r['step'] == expect, (linked, r)
        assert 0 <= top <= 30, (linked, 'step not at top of pane', top)
        assert not errors, errors
        c.close()
    print('PASS', name, 'grocery recipe link scrolls the step: automatic match and manual link', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        run(b, 'index.html')
        b.close()
