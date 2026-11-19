"""Batch 12: multiple simultaneous recipe timers — start several from different steps, labelled rows, pause one,
finish one (completion popup + acknowledge removes only it), hide/show, list indicator, reload persistence,
legacy single-timer migration, limit of 6, deleting the recipe clears its timers.

Run: python3 tests/batch12_multiple_timers_browser.py
"""
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

T0 = datetime(2026, 11, 16, 20, tzinfo=timezone.utc)
sb.fixture.HOOK += '''const b12Store=()=>typeof testStorage!=='undefined'?testStorage:localStorage;window.batch12={
 setup:()=>{const m=meals.find(m=>m.id===2);m.instructions=[{type:'step',text:'Simmer the sauce for 10 minutes.'},{type:'step',text:'Rest the rice for 1 minute.'},{type:'step',text:'Bake for 20 minutes.'}];persist();recipeViewPrefs.mode='full';saveRecipeViewPrefs();openSavedMealRecipe(m)},
 rname:()=>meals.find(m=>m.id===2).name,
 timers:()=>cookingTimers.map(t=>[t.stepNumber,t.status]),
 stored:()=>JSON.parse(b12Store().getItem('mealRotationCookingTimersV1')||'null')?.timers?.length||0,
 legacy:()=>JSON.parse(b12Store().getItem('mealRotationCookingTimerV1')||'null')?.id||null,
 sync:()=>syncCookingTimer(),
 close:()=>{if(recipeViewer)closeRecipeViewer()},
 home:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;render()},
 onlyLegacy:()=>{const t=cookingTimers[0];b12Store().removeItem('mealRotationCookingTimersV1');b12Store().setItem('mealRotationCookingTimerV1',JSON.stringify(t));loadCookingTimers();return cookingTimers.length},
 fill:n=>{const base=cookingTimers[0];while(cookingTimers.length<n)cookingTimers.push({...base,id:'x'+cookingTimers.length,stepNumber:3,stepToken:'other'+cookingTimers.length});saveCookingTimer();syncCookingTimer();return cookingTimers.length},
 remove:id=>applyRecipeBulk([String(id)],{delete:true})
};'''


def step_timer(p, n):
    return p.locator('.recipe-viewer-steps li').nth(n - 1).locator('.recipe-step-timer')


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch12.setup()')
    p.wait_for_selector('.recipe-step-timer')
    step_timer(p, 1).click()
    strips = p.locator('#recipeViewer .recipe-viewer-bar .recipe-timer-strip')
    assert strips.count() == 1 and p.locator('#recipeViewer .recipe-timer-label').count() == 0
    step_timer(p, 2).click()
    # Part 3b: one row (soonest first: the 1-minute Step 2), the other behind a "+1 timer" chip.
    rname = p.evaluate('batch12.rname()')
    assert strips.count() == 1, strips.count()
    assert p.locator('#recipeViewer .recipe-timer-label').all_text_contents() == [rname + ' · 2']
    more = p.locator('#recipeViewer .recipe-timer-more')
    assert more.inner_text() == '+1' and more.get_attribute('aria-label') == '+1 timer'
    more.click()
    drop = p.locator('#recipeViewer .recipe-timer-dropdown')
    assert drop.is_visible() and drop.locator('.recipe-timer-label').all_text_contents() == [rname + ' · 1']
    assert p.get_by_role('button', name='Hide timer controls').count() == 0
    sb.shot(p, name, 'part3b-dropdown')
    assert p.evaluate('batch12.stored()') == 2 and p.evaluate('batch12.legacy()')
    sb.shot(p, name, 'batch12-two-timers')
    # Pause Step 1 only.
    p.get_by_role('button', name='Pause timer (' + rname + ' · 1)', exact=True).click()
    assert p.evaluate('batch12.timers()') == [[1, 'paused'], [2, 'running']]
    # Tapping a step that already has a timer doesn't add another.
    step_timer(p, 1).click()
    assert len(p.evaluate('batch12.timers()')) == 2
    # Step 2 (1 minute) finishes: popup names it; acknowledging removes only Step 2.
    p.clock.set_fixed_time(T0 + timedelta(seconds=70))
    p.evaluate('batch12.sync()')
    done = p.get_by_role('alertdialog')
    done.wait_for(state='visible')
    assert rname + ' · 2' in done.inner_text(), done.inner_text()
    sb.shot(p, name, 'batch12-finished')
    done.get_by_role('button', name='Acknowledge completed timer', exact=True).click()
    assert p.evaluate('batch12.timers()') == [[1, 'paused']]
    assert strips.count() == 1 and more.count() == 0
    # Reload keeps the timer.
    p.reload()
    p.wait_for_function('window.batch12')
    assert p.evaluate('batch12.timers()') == [[1, 'paused']]
    # List indicator shows timers for the recipe.
    p.evaluate('batch12.close()')
    p.evaluate('batch12.home()')
    step = p.evaluate('batch12.setup()')
    p.wait_for_selector('.recipe-step-timer')
    step_timer(p, 3).click()
    p.evaluate('batch12.close()')
    p.evaluate('batch12.home()')
    icon = p.locator('.recipe-list-timer').first
    assert 'timers (2)' in icon.get_attribute('aria-label'), icon.get_attribute('aria-label')
    icon.click()
    dlg = p.locator('#cookingTimerControlsDialog')
    dlg.wait_for(state='visible')
    assert dlg.locator('.recipe-timer-strip').count() == 2
    sb.shot(p, name, 'batch12-list-popup')
    p.keyboard.press('Escape')
    # Legacy single record migrates to a one-item list.
    assert p.evaluate('batch12.onlyLegacy()') == 1
    # Limit of 6.
    assert p.evaluate('batch12.fill(6)') == 6
    p.evaluate('batch12.setup()')
    p.wait_for_selector('.recipe-step-timer')
    step_timer(p, 2).click()
    msg = p.get_by_text('Up to 6 timers can run at once. Delete one to start another.')
    msg.wait_for(state='visible')
    sb.shot(p, name, 'batch12-limit')
    assert p.locator('#recipeViewer .recipe-viewer-bar > .recipe-timer-strip').count() == 1 and p.locator('.recipe-timer-more').get_attribute('aria-label') == '+5 timers'
    p.get_by_role('button', name='OK', exact=True).click()
    p.locator('.recipe-timer-more').click()
    assert p.locator('#recipeViewer .recipe-timer-dropdown .recipe-timer-strip').count() == 5  # Part 3b: chip opens the dropdown
    p.keyboard.press('Escape')
    p.wait_for_timeout(200)
    assert len(p.evaluate('batch12.timers()')) == 6
    # Deleting the recipe clears its timers.
    p.evaluate('batch12.close()')
    p.evaluate('batch12.remove(2)')
    p.wait_for_timeout(200)
    assert p.evaluate('batch12.timers()') == [] and p.evaluate('batch12.stored()') == 0 and not p.evaluate('batch12.legacy()')
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 12: multiple timers, labels, pause one, finish/acknowledge one, hide/show, reload, list popup, legacy migration, limit, delete recipe', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
