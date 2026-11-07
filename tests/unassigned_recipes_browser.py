"""Mobile import, editing, backup, and bulk assignment for recipes without a group."""
import json
import os
from playwright.sync_api import expect, sync_playwright

import scheduled_linked_slots_browser as fixture


fixture.HOOK += """window.unassignedTest={
 import:items=>showRecipeImportSelection(recipeImportItems(items),'unassigned.json'),
 groups:()=>openMasterCategories(),
 validate:()=>validateBackupStorage(captureBackupStorage())
};"""


def run(browser, filename, width):
    context, page, errors, prefix = fixture.setup(browser, filename, width)
    before = fixture.compose(page)
    page.evaluate('unassignedTest.groups()')
    unassigned = page.locator('.master-category-card[data-category=""]')
    expect(unassigned).to_have_count(0)

    recipes = [
        {'name': 'White Bean Soup', 'recipeIngredient': ['1 cup beans']},
        {'name': 'Weekend Lentils', 'recipeCategory': 'Unchecked',
         'recipeIngredient': ['2 cups lentils']},
        {'name': 'Herbed Rice', 'recipeCategory': 'Rice',
         'recipeIngredient': ['3 cups rice']},
    ]
    page.evaluate('items=>unassignedTest.import(items)', recipes)
    dialog = page.get_by_role('dialog', name='Choose meal groups')
    dialog.get_by_role('checkbox', name='Rice').check()
    expect(dialog.get_by_text('2 recipes will go into Unassigned', exact=False)).to_be_visible()
    dialog.get_by_role('button', name='Import recipes', exact=True).tap()
    page.get_by_role('alertdialog').get_by_role('button', name='OK', exact=True).tap()

    expect(unassigned.get_by_role('button', name='Unassigned 2 meals')).to_be_visible()
    expect(unassigned.locator('.master-category-meal-name')).to_have_text(
        ['Weekend Lentils', 'White Bean Soup'])
    assert not unassigned.get_by_role('button', name='Move White Bean Soup to rotation').count()
    saved = page.evaluate('slotTest.storage()')
    collection = json.loads(saved['mealRotationDataV1'])
    imported = {m['name']: m for m in collection['meals'] if m['name'] in {r['name'] for r in recipes}}
    assert 'Misc' not in collection['cats'] and 'Unassigned' not in collection['cats']
    assert imported['White Bean Soup']['cat'] == '' and not imported['White Bean Soup']['rotation']
    assert imported['Weekend Lentils']['cat'] == '' and not imported['Weekend Lentils']['rotation']
    assert imported['Herbed Rice']['cat'] == 'Rice' and imported['Herbed Rice']['rotation']
    assert fixture.compose(page) == before
    page.evaluate('unassignedTest.validate()')
    page.evaluate('(backup)=>slotTest.restore(backup)', {**collection, 'version': 2, 'storage': saved})

    page.reload()
    page.evaluate('unassignedTest.groups()')
    unassigned.get_by_role('button', name='Unassigned 2 meals').tap()
    expect(unassigned.get_by_role('button', name='White Bean Soup', exact=True)).to_be_visible()
    unassigned.get_by_role('button', name='White Bean Soup', exact=True).tap()
    page.get_by_role('button', name='Edit', exact=True).tap()
    expect(page.locator('#rotation')).to_be_disabled()
    page.locator('#editor').get_by_role('button', name='Save', exact=True).tap()
    expect(page.locator('#editor .editor')).to_have_count(0)
    expect(unassigned.get_by_role('button', name='White Bean Soup', exact=True)).to_be_visible()

    recipe = unassigned.get_by_role('button', name='White Bean Soup', exact=True)
    recipe.scroll_into_view_if_needed()
    bounds = recipe.bounding_box()
    x, y = bounds['x'] + 4, bounds['y'] + bounds['height'] / 2
    touch = context.new_cdp_session(page)
    touch.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x, 'y': y}]})
    page.wait_for_timeout(600)
    touch.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []})
    page.get_by_role('button', name='Select all / Deselect all', exact=True).tap()
    page.get_by_role('button', name='Select all in Unassigned (2)', exact=True).tap()
    page.get_by_role('button', name='Move selected recipes', exact=True).tap()
    move = page.get_by_role('dialog', name='Move 2 recipes', exact=True)
    move.get_by_role('button', name='Meal group', exact=True).tap()
    picker = page.get_by_role('dialog', name='Meal group', exact=True)
    picker.get_by_role('radio', name='Sides', exact=True).check()
    picker.get_by_role('button', name='Confirm meal group', exact=True).tap()
    move.get_by_role('button', name='Apply to selected recipes', exact=True).tap()
    expect(move).to_have_count(0)
    expect(unassigned).to_have_count(0)
    for meal in fixture.state(page)['meals']:
        if meal['name'] in ['White Bean Soup', 'Weekend Lentils']:
            assert meal['cat'] == 'Sides' and not meal['rotation']
            assert meal['ingredients'] == imported[meal['name']]['ingredients']
    assert fixture.compose(page) == before

    page.reload()
    page.evaluate('unassignedTest.groups()')
    expect(unassigned).to_have_count(0)
    assert fixture.compose(page) == before

    sides = page.locator('.master-category-card[data-category="Sides"]')
    sides.get_by_role('button', name='Sides', exact=False).first.tap()
    ideas = sides.get_by_role('button', name='Sides: Ideas', exact=False)
    if ideas.get_attribute('aria-expanded') == 'false':
        ideas.tap()
    sides.get_by_role('button', name='White Bean Soup', exact=True).tap()
    page.get_by_role('button', name='Edit', exact=True).tap()
    if filename == 'index.html':
        page.get_by_role('button', name='Edit meal groups', exact=True).tap()
        picker = page.get_by_role('dialog', name='Select Meal Group')
        picker.get_by_role('checkbox', name='Sides', exact=True).uncheck()
        picker.get_by_role('button', name='Apply selected groups', exact=True).tap()
    else:
        page.locator('#categoryRows').get_by_role('button', name='Group', exact=True).tap()
        page.get_by_role('dialog', name='Select Meal Group').get_by_role(
            'radio', name='No group', exact=True).tap()
        expect(page.get_by_role('dialog', name='Select Meal Group')).to_have_count(0)
    page.locator('#editor').get_by_role('button', name='Save', exact=True).tap()
    expect(page.locator('#editor .editor')).to_have_count(0)
    expect(unassigned.get_by_role('button', name='Unassigned 1 meal', exact=True)).to_be_visible()
    soup = next(m for m in fixture.state(page)['meals'] if m['name'] == 'White Bean Soup')
    assert soup['cat'] == '' and soup['id'] == imported['White Bean Soup']['id']
    assert fixture.compose(page) == before

    if prefix:
        assert page.evaluate("localStorage.getItem('mealRotationDataV1')") == 'WORKING SENTINEL'
    assert not errors, errors
    print('PASS', filename, width, 'mixed import, backup restore, edit, bulk assignment and reload', flush=True)
    context.close()


if __name__ == '__main__':
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=os.environ.get('MEAL_TEST_CHROMIUM', '/usr/bin/chromium'),
            args=['--no-sandbox'],
        )
        for filename in ['index.html', 'meal-rotation-test.html']:
            for width in [320, 360]:
                run(browser, filename, width)
        browser.close()
