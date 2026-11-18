"""Batch 11: Regular grocery items — reusable templates (optional amount, This week, Repeat weekly), saved as a
draft (Save/Cancel), Undo, purchase keeps the template, Repeat weekly adds a fresh unchecked entry on a real
Start next week (and Undo of that), deleting a template leaves this week's entry as a plain item.

Run: python3 tests/batch11_regular_groceries_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch11={
 groceries:()=>{showTop=true;allMealsActive=false;groceryTabActive=true;render()},
 home:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;render()},
 manual:()=>manualGroceryItems().map(i=>[i.text,i.checked,!!i.regularId]),
 templates:()=>regularGroceryItems().map(i=>[i.name,i.amount,i.repeat]),
 undo:()=>{document.getElementById('undo').click()}
};'''


def open_editor(p):
    p.get_by_role('button', name='Regular items', exact=True).click()
    d = p.get_by_role('dialog', name='Regular items', exact=True)
    d.wait_for(state='visible')
    return d


def add(d, amount, name):
    d.get_by_role('textbox', name='New regular item amount (optional)', exact=True).fill(amount)
    d.get_by_role('textbox', name='New regular item', exact=True).fill(name)
    d.get_by_role('button', name='Add', exact=True).click()


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch11.groceries()')
    d = open_editor(p)
    add(d, '1 gal', 'Milk')
    add(d, '', 'Eggs')
    d.get_by_role('switch', name='This week for Eggs', exact=True).uncheck()
    d.get_by_role('switch', name='Repeat weekly for Eggs', exact=True).check()
    sb.shot(p, name, 'batch11-regular-editor')
    # Cancel discards the draft.
    d.get_by_role('button', name='Cancel', exact=True).click()
    assert p.evaluate('batch11.templates()') == [] and p.evaluate('batch11.manual()') == []
    d = open_editor(p)
    add(d, '1 gal', 'Milk')
    add(d, '', 'Eggs')
    d.get_by_role('switch', name='This week for Eggs', exact=True).uncheck()
    d.get_by_role('switch', name='Repeat weekly for Eggs', exact=True).check()
    d.get_by_role('button', name='Save regular items', exact=True).click()
    assert p.evaluate('batch11.templates()') == [['Milk', '1 gal', False], ['Eggs', '', True]]
    assert p.evaluate('batch11.manual()') == [['1 gal Milk', False, True]]
    assert p.locator('.manual-grocery-item', has_text='1 gal Milk').count() == 1
    tops = p.evaluate("[...document.querySelectorAll('.grocery-header-icons>button')].map(b=>Math.round(b.getBoundingClientRect().top))")
    assert len(set(tops)) == 1, tops
    sb.shot(p, name, 'batch11-grocery-list')
    # Undo removes both the templates and this week's entry.
    p.evaluate('batch11.undo()')
    p.wait_for_timeout(200)
    assert p.evaluate('batch11.templates()') == [] and p.evaluate('batch11.manual()') == []
    p.evaluate('batch11.groceries()')
    d = open_editor(p)
    add(d, '1 gal', 'Milk')
    add(d, '', 'Eggs')
    d.get_by_role('switch', name='This week for Eggs', exact=True).uncheck()
    d.get_by_role('switch', name='Repeat weekly for Eggs', exact=True).check()
    d.get_by_role('button', name='Save regular items', exact=True).click()
    # Buying the Milk entry keeps the template.
    p.locator('.manual-grocery-item', has_text='1 gal Milk').locator('input').check()
    p.wait_for_timeout(150)
    assert p.evaluate('batch11.manual()') == [['1 gal Milk', True, True]] and len(p.evaluate('batch11.templates()')) == 2
    # Real Start next week: checked Milk entry cleared (existing rule), Eggs (Repeat weekly) added fresh and unchecked.
    p.evaluate('batch11.home()')
    p.locator('.start-week-text').first.click()
    sw = p.get_by_role('dialog', name='Start next week', exact=True)
    sw.wait_for(state='visible')
    sw.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(500)
    after = p.evaluate('batch11.manual()')
    assert after == [['Eggs', False, True]], after
    assert len(p.evaluate('batch11.templates()')) == 2
    p.evaluate('batch11.undo()')
    p.wait_for_timeout(300)
    assert p.evaluate('batch11.manual()') == [['1 gal Milk', True, True]], p.evaluate('batch11.manual()')
    # Deleting a template keeps this week's entry as a plain item.
    p.evaluate('batch11.groceries()')
    d = open_editor(p)
    d.get_by_role('button', name='Remove Milk', exact=True).click()
    d.get_by_role('button', name='Save regular items', exact=True).click()
    assert p.evaluate('batch11.manual()') == [['1 gal Milk', True, False]] and p.evaluate('batch11.templates()') == [['Eggs', '', True]]
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 11: regular items draft/save/cancel, Undo, purchase keeps template, Repeat weekly on Start next week (+Undo), delete keeps entry', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
