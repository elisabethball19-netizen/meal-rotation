"""Expanded week card: heart, Needs adjusting and Scale sit under More until used once, then stay visible.
Run: python3 tests/card_more_menu_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.cm={home:()=>{showMealPlanTabs=true;showTop=true;allMealsActive=false;groceryTabActive=false;render()}};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate("localStorage.removeItem('mealRotationCardControlsUsedV1')")
    p.evaluate('cm.home()'); p.wait_for_timeout(300)
    p.locator('#list .plan-card-disclosure, #list [aria-label^="Meal actions for"]').first.click(); p.wait_for_timeout(400)
    card = p.locator('#list .week-meal-card, #list .plan-card').first
    labels = lambda: p.locator('.shared-meal-action-grid:visible button').all_inner_texts()
    assert 'Scale' not in labels() and 'More' in ' '.join(labels()), labels()
    assert p.locator('.expanded-name-heart:visible').count() == 0 and p.locator('.expanded-name-needs:visible').count() == 0
    sb.shot(p, name, 'more-closed')
    p.get_by_role('button', name='More', exact=True).first.click(); p.wait_for_timeout(300)
    opts = p.locator('.compact-meal-dialog button.meal-option-row').all_inner_texts()
    assert opts == ['Add to favorites', 'Needs adjusting', 'Scale'], opts
    sb.shot(p, name, 'more-open')
    p.get_by_role('button', name='Add to favorites').click(); p.wait_for_timeout(500)
    assert p.locator('.expanded-name-heart:visible').count() == 1
    assert p.evaluate("JSON.parse(localStorage.getItem('mealRotationCardControlsUsedV1')).favorite") == 1
    assert not errors, errors
    c.close()
    print('PASS', name, 'More menu holds heart / Needs adjusting / Scale until used')


with sync_playwright() as pw:
    b = pw.chromium.launch()
    for n in ('index.html', 'meal-rotation-test.html'):
        run(b, n)
    b.close()
