"""Issue 127 Batch 1 only: meal card + sides auto-save, Add side, details, hearts, dates.

Disposable intercepted origins for index.html and the isolated meal-rotation-test.html.
Run: python3 tests/sides_batch127_browser.py  (screenshots go to OUT for inspection)
"""
import json
import os
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import followup126_browser as base  # registers the shared follow126 fixture hook

fixture = base.fixture
fixture.HOOK += '''window.batch127={
 times:()=>{const set=(id,v)=>Object.assign(meals.find(m=>m.id===id),v);set(2,{prep:15,cook:30,marinate:'2 hours'});set(10,{prep:10,cook:40,makeAheadTasks:[{id:'side-prep',description:'Parboil the potatoes',daysBefore:1}]});persist();follow126.home()},
 simpleOnly:()=>{const parent=meals.find(m=>m.id===2);parent.serveWithEntriesV1=[{id:'simple',type:'simple',name:'Butter',ingredients:[],always:true}];parent.linkedMealIds=[];parent.simpleSides=[{id:'simple',name:'Butter',ingredients:[]}];saveActiveMealPlan();persist();follow126.home()},
 sides:(week=0)=>{const s=week?previewMealPlanAdvance():{plan:mealPlans[0],entries:getDisplayedWeekdayMealsForPlan(mealPlans[0])},e=s.entries.find(x=>!x.linkedTo&&!x.servingParentId);return servingSides(s.plan,e,s.entries).map(x=>x.name||x.mealId)},
 undoDepth:()=>history.length,
 ing:()=>{const s=mealPlans[0],e=getDisplayedWeekdayMealsForPlan(s).find(x=>!x.linkedTo&&!x.servingParentId);return servingSides(s,e,getDisplayedWeekdayMealsForPlan(s)).filter(x=>x.type==='simple').flatMap(x=>(x.ingredients||[]).map(i=>i.text))},
 fav:id=>meals.find(m=>m.id===id).favorite===true,session:()=>!!servingSideSession,close:()=>closeServingSession(),
 home:week=>{expandedPlanCards.clear();follow126.home(week)},
 nextSide:()=>{const parent=meals.find(m=>m.id===3);parent.serveWithEntriesV1=[{id:'nb',type:'simple',name:'Pickles',ingredients:[],always:true}];parent.simpleSides=[{id:'nb',name:'Pickles',ingredients:[]}];saveActiveMealPlan();persist();batch127.home(1)},
 allSides:()=>{for(const m of meals.filter(m=>m.cat==='Rice'&&m.id!==2)){m.serveWithEntriesV1=[{id:'s'+m.id,type:'simple',name:'Butter',ingredients:[],always:true}];m.simpleSides=[{id:'s'+m.id,name:'Butter',ingredients:[]}]}for(const day of orderedDays())weekdayCategories[day]=['Rice'];mealPlans[0].weekdayCategories={...weekdayCategories};saveActiveMealPlan();persist();follow126.home()},
 tasks:()=>[...document.querySelectorAll('#todaysTodo .make-ahead-task-link')].map(x=>x.textContent)
};'''
OUT = Path(os.environ.get('BATCH127_OUT', '/tmp/batch127'))
OUT.mkdir(parents=True, exist_ok=True)


def shot(p, name, label):
    p.screenshot(path=str(OUT / ((name.split('.')[0]) + '-' + label + '.png')), full_page=False)


def open_page(browser, name, width=360, height=800):
    c, p, errors, prefix = fixture.setup(browser, name, width=width, navigation_timeout=30000)
    p.set_viewport_size({'width': width, 'height': height})
    p.context.new_cdp_session(p).send('Emulation.setTimezoneOverride', {'timezoneId': 'America/Los_Angeles'})
    p.clock.set_fixed_time(datetime(2026, 11, 16, 20, tzinfo=timezone.utc))
    p.evaluate('follow126.seed()')
    return c, p, errors, prefix


def card(p, meal_id=None):
    return p.locator('.plan-meal-card[data-meal-id="%s"]' % meal_id) if meal_id else p.locator('.plan-meal-card').first


def state(p):
    return p.evaluate('follow126.state()')


def date_offset(p, c):
    return c.evaluate('c=>c.querySelector(".plan-date strong").getBoundingClientRect().top-c.getBoundingClientRect().top')


def run(browser, name):
    c, p, errors, prefix = open_page(browser, name)
    p.evaluate('follow126.rules();batch127.times()')
    main = card(p, 2)

    # Collapsed: names only; time line for the main meal only, before the sides.
    line = main.locator('.plan-card-content > .plan-card-details .plan-time-line')
    assert line.count() == 1
    assert line.locator('.plan-time-part').all_text_contents() == ['15m prep · 45m total', '2h marinate'], line.locator('.plan-time-part').all_text_contents()
    order = main.evaluate('c=>[...c.querySelectorAll(".plan-card-details:not(.plan-side-details),.plan-linked-names")].map(x=>x.className)')
    assert order[0].startswith('plan-card-details') and 'plan-linked-names' in order[1], order
    assert not main.locator('.plan-side-details').first.is_visible()
    assert not main.locator('.plan-side-heart').first.is_visible()
    collapsed_offset = date_offset(p, main)
    shot(p, name, 'collapsed-with-sides')

    # Side prep to-dos exist while the card is collapsed.
    assert any('Parboil the potatoes' in t for t in p.evaluate('batch127.tasks()')), p.evaluate('batch127.tasks()')

    # Expanded: side details and a heart on recipe sides only; date column does not move.
    main.locator('.meal-actions-toggle').click()
    assert date_offset(p, main) == collapsed_offset
    assert line.is_visible() and line.locator('.plan-marinate-detail').evaluate('x=>getComputedStyle(x,"::before").content') == '" · "'
    assert line.evaluate('x=>x.getBoundingClientRect().height') < 22  # one line, tied to the main meal
    side_lines = main.locator('.plan-side-line')
    assert side_lines.count() == 2, side_lines.count()
    assert side_lines.first.locator('.plan-side-details').is_visible()
    assert '10m prep' in side_lines.first.locator('.plan-side-details').inner_text()
    assert side_lines.first.locator('.plan-cooked-detail').is_visible()
    assert side_lines.first.locator('.plan-side-heart').is_visible()
    assert main.locator('.plan-linked-names > span', has_text='Butter').count() == 1
    shot(p, name, 'expanded-side-details')

    # Favorite a recipe side from the card: recipe-wide favorite.
    side_lines.first.locator('.plan-side-heart').click()
    assert p.evaluate('batch127.fav(10)') is True
    main = card(p, 2)

    # Edit sides: no check/X row; remove a saved side auto-saves with a toast; toolbar Undo/Redo.
    main.get_by_role('button', name='Add or edit sides', exact=True).click()
    assert not p.get_by_role('button', name='Save all sides').count()
    assert not p.get_by_role('button', name='Cancel all side changes').count()
    # Header is a plain title; three sides start collapsed; one plus and the closing check at the bottom.
    assert main.locator('.inline-sides-header button').count() == 0
    assert main.locator('.inline-side-body').count() == 0
    assert main.get_by_role('button', name='Add side', exact=True).count() == 1
    assert main.get_by_role('button', name='Close sides', exact=True).is_visible()
    shot(p, name, 'sides-edit-mode')
    # Expanding a side shows exactly four icon-only actions; chevrons never close the editor.
    main.get_by_role('button', name='Side actions for Butter').click()
    icons = main.locator('.inline-side-body .serving-icon-row button')
    assert icons.count() == 4 and icons.evaluate_all('xs=>xs.map(x=>x.getAttribute("aria-label"))') == ['Edit side', 'Remove side', 'Edit groceries', 'Add side'], icons.evaluate_all('xs=>xs.map(x=>x.getAttribute("aria-label"))')
    assert all(t.strip() == '' for t in icons.all_inner_texts())
    assert main.get_by_role('button', name='Add side', exact=True).count() == 1
    assert main.locator('.inline-side-body .shared-meal-action-grid').count() == 0
    assert p.evaluate('batch127.session()')
    shot(p, name, 'side-icon-row')
    main.get_by_role('button', name='Side actions for Butter').click()
    assert main.locator('.inline-side-body').count() == 0 and p.evaluate('batch127.session()')
    depth = p.evaluate('batch127.undoDepth()')
    main.get_by_role('button', name='Side actions for Butter').click()
    main.get_by_role('button', name='Remove side', exact=True).click()
    assert p.evaluate('batch127.sides()') == ['10', '12'], p.evaluate('batch127.sides()')
    assert p.evaluate('batch127.undoDepth()') == depth + 1
    toast = p.locator('.serving-undo-toast')
    assert toast.is_visible() and 'Side removed' in toast.inner_text()
    shot(p, name, 'removed-toast')
    p.locator('#undo').click()
    assert p.evaluate('batch127.sides()') == ['10', '12', 'Butter']
    assert card(p, 2).locator('.inline-side-row[data-side-id="simple"]').count() == 1  # editor resynced
    p.locator('#redo').click()
    assert p.evaluate('batch127.sides()') == ['10', '12']
    p.locator('#undo').click()
    assert p.evaluate('batch127.sides()') == ['10', '12', 'Butter']
    # The toast's own Undo restores too.
    main = card(p, 2)
    main.get_by_role('button', name='Side actions for Butter').click()
    main.get_by_role('button', name='Remove side', exact=True).click()
    p.locator('.serving-undo-toast').get_by_role('button', name='Undo').click()
    assert p.evaluate('batch127.sides()') == ['10', '12', 'Butter']
    p.reload(); p.wait_for_function('window.batch127!==undefined'); p.evaluate('follow126.home()')
    assert p.evaluate('batch127.sides()') == ['10', '12', 'Butter']

    # Collapsing an editing card saves a pending simple-side name and closes editing.
    main = card(p, 2)
    main.locator('.meal-actions-toggle').click()
    main.get_by_role('button', name='Add or edit sides', exact=True).click()
    main.get_by_role('button', name='Side actions for Butter').click()
    main.get_by_role('button', name='Edit side', exact=True).click()
    main.get_by_role('textbox', name='Side name', exact=True).fill('Garlic butter')
    # A simple side's cart opens its ingredient list so it can still be shopped for.
    main.get_by_role('button', name='Edit groceries', exact=True).click()
    ingredients = main.get_by_role('textbox', name='Side ingredients', exact=True)
    assert ingredients.is_visible()
    ingredients.fill('2 cups white rice')
    summary = main.locator('.simple-side-ingredients > summary')
    assert summary.locator('svg').count() == 1 and summary.evaluate('s=>getComputedStyle(s).listStyleType') == 'none'
    assert main.get_by_role('textbox', name='Side name').evaluate('x=>parseFloat(getComputedStyle(x).borderTopLeftRadius)') >= 8
    edit_bg = main.locator('.sides-edit-mode').evaluate('x=>getComputedStyle(x).backgroundColor')
    assert edit_bg not in ('rgba(0, 0, 0, 0)', 'transparent'), edit_bg
    shot(p, name, 'simple-edit')
    main.locator('.meal-actions-toggle').click()
    assert not p.evaluate('batch127.session()')
    assert p.evaluate('batch127.sides()') == ['10', '12', 'Garlic butter']
    assert p.evaluate('batch127.ing()') == ['2 cups white rice'], p.evaluate('batch127.ing()')
    assert not card(p, 2).locator('.shared-meal-actions').is_visible()

    # The bottom check closes the editor (changes are already saved); the card stays expanded.
    main = card(p, 2)
    main.locator('.meal-actions-toggle').click()
    main.get_by_role('button', name='Add or edit sides', exact=True).click()
    main.get_by_role('button', name='Side actions for Garlic butter').click()
    assert p.evaluate('batch127.session()')
    main.get_by_role('button', name='Close sides', exact=True).click()
    assert not p.evaluate('batch127.session()')
    assert card(p, 2).locator('.shared-meal-action-grid').first.is_visible()

    # Add side: exact recipe match first, simple side second, other matches labeled with group.
    main = card(p, 2)
    main.get_by_role('button', name='Add or edit sides', exact=True).click()
    before = state(p)
    main.get_by_role('button', name='Add side', exact=True).click()
    dialog = p.get_by_role('dialog', name='Add side')
    search = dialog.get_by_role('searchbox', name='Search recipes or type a side')
    shot(p, name, 'add-side-browse')
    search.fill('creamy MASHED potatoes')
    rows = dialog.locator('.serving-add-row')
    assert rows.nth(0).get_attribute('data-meal-id') == '11', rows.all_inner_texts()
    assert 'as a simple side' in rows.nth(1).inner_text()
    assert rows.nth(0).get_attribute('aria-pressed') == 'true'
    shot(p, name, 'add-side-exact')
    search.fill('potatoes')
    rows = dialog.locator('.serving-add-row')
    assert 'Add “potatoes”' in rows.nth(0).inner_text()
    assert rows.nth(1).locator('.serving-add-group').inner_text() == 'Potatoes'
    # Unsaved draft cancel via X: nothing changes.
    dialog.get_by_role('button', name='Cancel', exact=True).click()
    assert state(p) == before
    # Simple side from typed text.
    main = card(p, 2)
    main.get_by_role('button', name='Add side', exact=True).click()
    dialog = p.get_by_role('dialog', name='Add side')
    dialog.get_by_role('searchbox').fill('Garlic green beans')
    shot(p, name, 'add-side-new-name')
    dialog.get_by_role('button', name='Add selected side').click()
    p.wait_for_timeout(200)
    assert p.evaluate('batch127.sides()')[-1] == 'Garlic green beans'
    assert not card(p, 2).locator('.inline-side-row').last.locator('.inline-side-heart').count()  # simple: no heart
    # Expanded recipe side row in the editor shows the heart.
    main = card(p, 2)
    main.get_by_role('button', name='Side actions for Golden roast potatoes with rosemary and garlic for the whole family').click()
    assert main.locator('.inline-side-row').first.locator('.inline-side-heart').is_visible()
    assert main.locator('.inline-side-row').first.locator('.plan-side-details').is_visible()
    main.get_by_role('button', name='Side actions for Golden roast potatoes with rosemary and garlic for the whole family').click()
    main.get_by_role('button', name='Close sides', exact=True).click()

    # Mix it up: group checklist, checked float to top, no "rotating" wording.
    main = card(p, 2)
    main.get_by_role('button', name='Add or edit sides', exact=True).click()
    main.get_by_role('button', name='Add side', exact=True).click()
    dialog = p.get_by_role('dialog', name='Add side')
    dialog.get_by_role('tab', name='Mix it up').click()
    choices = dialog.locator('.serving-group-choice')
    names = lambda: [x.split('\n')[0] for x in choices.all_inner_texts()]
    dialog.get_by_role('checkbox', name='Vegetables').check() if dialog.get_by_role('checkbox', name='Vegetables').count() else choices.filter(has_text='Vegetables').locator('input').check()
    assert names()[0] == 'Vegetables', names()
    assert 'rotating' not in dialog.inner_text().lower()
    shot(p, name, 'mix-it-up')
    dialog.get_by_role('button', name='Cancel', exact=True).click()
    p.wait_for_timeout(200)
    p.evaluate('batch127.close()')

    # Weekday dialog wording.
    p.evaluate('follow126.home()')
    card(p, 2).locator('.plan-date').click()
    assert p.get_by_role('dialog', name='Choose Tuesday’s meal groups').count() == 1
    p.get_by_role('button', name='Cancel meal groups').click(); p.wait_for_timeout(250)

    # No sides: Add or edit sides opens Add side directly; X returns to the expanded card.
    p.evaluate('follow126.seed()')
    main = card(p, 2)
    main.locator('.meal-actions-toggle').click()
    before = state(p)
    main.get_by_role('button', name='Add or edit sides', exact=True).click()
    assert p.get_by_role('dialog', name='Add side').is_visible()
    p.get_by_role('dialog', name='Add side').get_by_role('button', name='Cancel', exact=True).click()
    p.wait_for_timeout(250)
    assert state(p) == before and not p.evaluate('batch127.session()')
    assert card(p, 2).locator('.shared-meal-action-grid').first.is_visible()
    # Choosing a recipe from an empty card saves it and shows it auto-expanded (one side).
    card(p, 2).get_by_role('button', name='Add or edit sides', exact=True).click()
    dialog = p.get_by_role('dialog', name='Add side')
    dialog.get_by_role('searchbox').fill('Creamy mashed potatoes')
    dialog.get_by_role('button', name='Add selected side').click()
    p.wait_for_timeout(250)
    assert p.evaluate('batch127.sides()') == ['11']
    assert card(p, 2).locator('.inline-side-row .inline-side-body').count() == 1
    # One saved side reopens auto-expanded.
    p.evaluate('batch127.close()')
    card(p, 2).get_by_role('button', name='Add or edit sides', exact=True).click()
    assert card(p, 2).locator('.inline-side-row .inline-side-body').count() == 1
    p.evaluate('batch127.close()')

    # Date column: same offset collapsed/expanded, equal across cards, both weeks.
    for week in (0, 1):
        p.evaluate('batch127.home(%d)' % week)
        offsets = [date_offset(p, x) for x in p.locator('.plan-meal-card').all()]
        assert max(offsets) - min(offsets) < 0.5, (week, offsets)
        first = p.locator('.plan-meal-card').first
        first.locator('.meal-actions-toggle').click()
        assert abs(date_offset(p, p.locator('.plan-meal-card').first) - offsets[0]) < 0.5
        shot(p, name, 'dates-week%d' % week)

    # Next week: removal auto-saves to next week only and undoes.
    p.evaluate('batch127.nextSide()')
    current_before = p.evaluate('batch127.sides(0)')
    nxt = card(p, 3)
    nxt.locator('.meal-actions-toggle').click()
    nxt.get_by_role('button', name='Add or edit sides', exact=True).click()
    nxt.get_by_role('button', name='Remove side', exact=True).click()  # one side is auto-expanded
    assert p.evaluate('batch127.sides(1)') == []
    assert p.evaluate('batch127.sides(0)') == current_before
    p.locator('#undo').click()
    assert p.evaluate('batch127.sides(1)') == ['Pickles']
    p.evaluate('batch127.close()')

    assert not errors, errors
    if prefix:
        assert p.evaluate('localStorage.getItem("mealRotationDataV1")') == 'WORKING SENTINEL'
    c.close()
    print('PASS', name, 'batch127 auto-save/Undo/toast, collapse+side-close save, Add side search/exact/simple/cancel/mix, details+hearts, side to-dos, date alignment both weeks', flush=True)


def colors(browser, name):
    """Edit area must read lighter than every pastel weekday card."""
    c, p, errors, prefix = open_page(browser, name)
    p.evaluate('follow126.rules();batch127.allSides()')
    cards = p.locator('.plan-meal-card[data-meal-id]')
    seen = []
    for i in range(min(cards.count(), 7)):
        cd = p.locator('.plan-meal-card[data-meal-id]').nth(i)
        cd.locator('.meal-actions-toggle').click()
        cd.get_by_role('button', name='Add or edit sides', exact=True).click()
        cd = p.locator('.plan-meal-card.card-sides-editing')
        bg = cd.evaluate('c=>getComputedStyle(c).backgroundColor')
        seen.append(bg)
        cd.screenshot(path=str(OUT / ((name.split('.')[0]) + '-color-%d.png' % i)))
        p.evaluate('batch127.close()')
    assert len(set(seen)) >= 3, seen
    assert not errors, errors
    c.close()
    print('PASS', name, 'edit area on', len(seen), 'card colors', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
            colors(b, name)
        b.close()
