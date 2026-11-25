"""Meal Groups: each Regulars / Off menu row has a More menu with four single-purpose modes.
Select (checkboxes, Move or copy, no bulk delete), Reorder (handles), Take out of rotation (arrows), Delete (trash + existing dialog).
Run: python3 tests/group_more_menu_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.gp={open:()=>{showTop=false;masterCategoriesView=true;render()},names:()=>meals.filter(m=>m.cat==='Rice').map(m=>[m.name,recipeStatus(m)])};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('gp.open()'); p.wait_for_timeout(400)
    p.locator('.master-category-header').first.click(); p.wait_for_timeout(500)
    more = p.locator('.group-section-organize').first
    assert more.get_attribute('aria-label').startswith('More options'), more.get_attribute('aria-label')
    items = lambda: p.locator('.compact-meal-dialog button.meal-option-row').all_inner_texts()
    done = lambda: p.locator('.organize-mode-done, .recipe-bulk-actions button:has-text("Done")').first.click()
    more.click(); p.wait_for_timeout(300)
    assert items() == ['Move or copy to group', 'Reorder meals', 'Take out of rotation', 'Delete meals'], items()
    # select mode: checkboxes, Move or copy, no Delete
    p.get_by_role('button', name='Move or copy to group').click(); p.wait_for_timeout(400)
    assert p.locator('.recipe-bulk-check').count() >= 2 and p.locator('.organize-drag-handle,.organize-row-status,.organize-row-delete').count() == 0
    labels = p.locator('.recipe-bulk-actions button').all_inner_texts()
    assert [l.strip() for l in labels] == ['Move', 'Done'], labels
    done(); p.wait_for_timeout(300)
    # reorder: handles only, on the left of the name
    more.click(); p.get_by_role('button', name='Reorder meals').click(); p.wait_for_timeout(400)
    assert p.locator('.organize-drag-handle').count() >= 2 and p.locator('.recipe-bulk-check,.organize-row-status,.organize-row-delete').count() == 0
    box = p.locator('.organize-drag-handle').first.bounding_box(); info = p.locator('.master-category-meal .master-meal-info').first.bounding_box()
    assert box['x'] + box['width'] <= info['x'] + 2, (box, info)
    done(); p.wait_for_timeout(300)
    # move to Off menu: arrow moves one meal
    before = p.evaluate('gp.names()')
    more.click(); p.get_by_role('button', name='Take out of rotation').click(); p.wait_for_timeout(400)
    assert p.locator('.organize-row-status').count() >= 2 and p.locator('.recipe-bulk-check,.organize-drag-handle,.organize-row-delete').count() == 0
    p.locator('.organize-row-status').nth(1).click(); p.wait_for_timeout(600)
    after = p.evaluate('gp.names()')
    assert sum(1 for n in after if n[1] == 'up-next') == sum(1 for n in before if n[1] == 'up-next') + 1, (before, after)
    done(); p.wait_for_timeout(300)
    # rows without a left control keep their full-width names (Put in rotation mode from the Off menu row)
    sec = p.locator('.master-recipe-section[data-recipe-section="up-next"]')
    if sec.locator('.master-recipe-section-recipes').first.is_hidden():
        sec.locator('.master-category-group-label').click(); p.wait_for_timeout(400)
    sec.locator('.group-section-organize').click(); p.get_by_role('button', name='Put in rotation').click(); p.wait_for_timeout(500)
    widths = p.evaluate("[...document.querySelectorAll('.master-recipe-section[data-recipe-section=rotation] .master-category-meal')].map(r=>r.querySelector('.master-meal-info').getBoundingClientRect().width)")
    assert widths and min(widths) > 200, widths
    done(); p.wait_for_timeout(300)
    # delete: trash opens the existing delete dialog; cancel keeps the meal
    more.click(); p.get_by_role('button', name='Delete meals').click(); p.wait_for_timeout(400)
    assert p.locator('.organize-row-delete').count() >= 2 and p.locator('.recipe-bulk-check,.organize-drag-handle,.organize-row-status').count() == 0
    p.locator('.organize-row-delete').first.click(); p.wait_for_timeout(400)
    assert p.locator('.recipe-delete-dialog strong').first.text_content() == 'Delete this recipe?'
    p.get_by_role('button', name='Cancel deletion').click(); p.wait_for_timeout(300)
    assert len(p.evaluate('gp.names()')) == len(after)
    assert not errors, errors
    c.close()
    print('PASS', name, 'Meal Groups More menu: select / reorder / move / delete modes')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ('index.html', 'meal-rotation-test.html'):
        run(b, n)
    b.close()
