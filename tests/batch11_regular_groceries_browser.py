"""Batch 11 (revised): Repeat weekly is a plain switch in the Add/Edit grocery item dialog. A repeating item is
re-added fresh and unchecked on a real Start next week; turning the switch off or deleting the item stops it.

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
 templates:()=>regularGroceryItems().map(i=>[i.name,i.repeat]),
 edit:text=>openManualGroceryEditor(manualGroceryItems().find(i=>i.text===text),()=>render())
};'''


def add_item(p, text, repeat):
    p.get_by_role('button', name='Add grocery item', exact=True).click()
    d = p.get_by_role('dialog', name='Add grocery item', exact=True)
    d.wait_for(state='visible')
    d.get_by_role('textbox', name='Grocery item', exact=True).fill(text)
    if repeat:
        d.get_by_role('switch', name='Repeat weekly', exact=True).check()
    d.get_by_role('button', name='Save grocery item', exact=True).click()
    p.wait_for_timeout(150)


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    p.evaluate('batch11.groceries()')
    # No separate Regular items button any more.
    assert p.get_by_role('button', name='Regular items', exact=True).count() == 0
    add_item(p, '1 gal Milk', False)
    add_item(p, 'Eggs', True)
    assert p.evaluate('batch11.manual()') == [['1 gal Milk', False, False], ['Eggs', False, True]]
    assert p.evaluate('batch11.templates()') == [['Eggs', True]]
    p.get_by_role('button', name='Add grocery item', exact=True).click()
    d = p.get_by_role('dialog', name='Add grocery item', exact=True)
    assert d.get_by_role('switch', name='Repeat weekly', exact=True).is_visible()
    assert d.inner_text().count('Repeat weekly') == 1 and 'Regular' not in d.inner_text()
    sb.shot(p, name, 'batch11-repeat-switch')
    d.get_by_role('button', name='Cancel', exact=True).click()
    # Editing shows the switch on for Eggs; switching it off stops repeating but keeps this week's item.
    p.evaluate('batch11.edit("Eggs")')
    d = p.get_by_role('dialog', name='Edit grocery item', exact=True)
    sw = d.get_by_role('switch', name='Repeat weekly', exact=True)
    assert sw.is_checked()
    sw.uncheck()
    d.get_by_role('button', name='Save grocery item', exact=True).click()
    p.wait_for_timeout(150)
    assert p.evaluate('batch11.templates()') == [] and ['Eggs', False, False] in p.evaluate('batch11.manual()')
    p.evaluate('batch11.edit("Eggs")')
    d = p.get_by_role('dialog', name='Edit grocery item', exact=True)
    d.get_by_role('switch', name='Repeat weekly', exact=True).check()
    d.get_by_role('button', name='Save grocery item', exact=True).click()
    p.wait_for_timeout(150)
    assert p.evaluate('batch11.templates()') == [['Eggs', True]]
    # Buying Eggs, then a real Start next week: checked entries cleared, repeating Eggs added fresh and unchecked.
    p.locator('.manual-grocery-item', has_text='Eggs').locator('input').check()
    p.wait_for_timeout(150)
    p.evaluate('batch11.home()')
    p.locator('.start-week-text').first.click()
    sw_dialog = p.get_by_role('dialog', name='Start next week', exact=True)
    sw_dialog.wait_for(state='visible')
    sw_dialog.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(500)
    after = p.evaluate('batch11.manual()')
    assert ['Eggs', False, True] in after and not any(x[0] == 'Eggs' and x[1] for x in after), after
    # Deleting a repeating item stops it repeating.
    p.evaluate('batch11.groceries()')
    p.evaluate('batch11.edit("Eggs")')
    d = p.get_by_role('dialog', name='Edit grocery item', exact=True)
    d.get_by_role('button', name='Delete grocery item', exact=True).click()
    p.wait_for_timeout(150)
    assert p.evaluate('batch11.templates()') == [] and not any(x[0] == 'Eggs' for x in p.evaluate('batch11.manual()'))
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 11 revised: Repeat weekly switch in add/edit dialog, no Regular items button, repeats on Start next week, off/delete stops it', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
