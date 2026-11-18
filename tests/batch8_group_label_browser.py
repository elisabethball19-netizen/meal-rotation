"""Batch 8: main card group label lists all of the weekday's main groups, active first ("Rice · Soup").

Run: python3 tests/batch8_group_label_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch8={
 two:()=>{if(!cats.includes('Soup'))cats.push('Soup');const day=getDisplayedWeekdayMeals().find(e=>e.meal.cat==='Rice'&&!e.linkedTo).day;weekdayCategories[day]=['Soup','Rice'];mealPlans.find(p=>p.id===activePlanId).weekdayCategories={...weekdayCategories};saveActiveMealPlan();persist();follow126.home();return day},
 label:day=>[...document.querySelectorAll('.plan-meal-card')].map(c=>c.querySelector('.plan-card-group')?.textContent).filter(Boolean)
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    before = p.evaluate('batch8.label()')
    assert all(' · ' not in x for x in before), before
    p.evaluate('batch8.two()')
    labels = p.evaluate('batch8.label()')
    assert 'Rice · Soup' in labels, labels
    sb.shot(p, name, 'batch8-group-label')
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 8: weekday group label lists all main groups, active first', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
