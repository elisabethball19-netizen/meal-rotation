"""Batch 4: Meal Groups page — Weekly/Other/Unassigned sections, Unassigned checklist + Move/Delete bar,
section state kept (refresh) / reset after 5+ min in background, bulk toolbar Move + plain Done.

Run: python3 tests/batch4_groups_page_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.batch4={
 groups:()=>{showTop=false;groceryTabActive=false;allMealsActive=false;masterExpansionInitialized=true;masterExpandedCategories.clear();render()},
 unassign:n=>{const list=meals.filter(m=>m.cat&&!m.linkedMealIds?.length).slice(-n);list.forEach(m=>{m.cat='';m.rotation=false});persist();renderList({readOnly:true});return list.map(m=>String(m.id))},
 sections:()=>[...document.querySelectorAll('.master-group-section')].map(s=>[s.dataset.groupSection,s.querySelector('.master-group-section-toggle').getAttribute('aria-expanded'),[...s.querySelectorAll(':scope>.master-group-section-body>.master-category-card')].map(c=>c.dataset.category)]),
 weekly:()=>[...new Set(Object.values(weekdayCategories).flat())].filter(c=>cats.includes(c)),
 cats:()=>[...cats],
 cat:id=>meals.find(m=>String(m.id)===String(id))?.cat??null,
 exists:id=>meals.some(m=>String(m.id)===String(id)),
 background:(ms)=>{Object.defineProperty(document,'hidden',{configurable:true,get:()=>true});document.dispatchEvent(new Event('visibilitychange'));const v=JSON.parse(localStorage.getItem('mealRotationGroupPageSectionsV1'));v.hiddenAt-=ms;localStorage.setItem('mealRotationGroupPageSectionsV1',JSON.stringify(v));Object.defineProperty(document,'hidden',{configurable:true,get:()=>false});document.dispatchEvent(new Event('visibilitychange'))},
 organize:cat=>beginRecipeBulkGroup(cat),
 expand:cat=>{masterExpansionInitialized=true;masterExpandedCategories.add(cat);renderList({readOnly:true})},
 expanded:()=>[...masterExpandedCategories],
 undo:()=>restoreState(JSON.parse(history.pop()))
};'''


def sections(p):
    return {k: (o == 'true', cards) for k, o, cards in p.evaluate('batch4.sections()')}


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    ids = p.evaluate('batch4.unassign(2)')
    p.evaluate('batch4.groups()')
    s = sections(p)
    weekly = set(p.evaluate('batch4.weekly()'))
    assert set(s) >= {'weekly', 'unassigned'}, s
    assert s['weekly'][0] and not s['unassigned'][0] and ('other' not in s or not s['other'][0]), s
    assert weekly <= set(s['weekly'][1]), (weekly, s)
    if 'other' in s:
        assert not set(s['other'][1]) & set(s['weekly'][1])
    sb.shot(p, name, 'batch4-sections')
    # Open Unassigned: flat checklist, bar always shown, Move/Delete disabled until a pick.
    p.locator('.master-group-section[data-group-section="unassigned"] .master-group-section-toggle').click()
    rows = p.locator('.unassigned-row')
    assert rows.count() == 2 and p.locator('.unassigned-bulk-bar').is_visible()
    assert p.locator('.unassigned-move').is_disabled() and p.locator('.unassigned-delete').is_disabled()
    rows.nth(0).locator('input').check()
    assert p.locator('.unassigned-bulk-count').text_content() == '1 selected' and p.locator('.unassigned-move').is_enabled()
    sb.shot(p, name, 'batch4-unassigned')
    # Refresh keeps the section state.
    p.reload()
    p.wait_for_function('window.batch4')
    p.evaluate('batch4.groups()')
    assert sections(p)['unassigned'][0], 'refresh keeps sections'
    # 5+ minutes in background resets (Weekly open, others closed); under 5 does not.
    p.evaluate('batch4.background(60*1000)')
    assert sections(p)['unassigned'][0]
    p.evaluate('batch4.background(6*60*1000)')
    s = sections(p)
    assert s['weekly'][0] and not s['unassigned'][0] and not s.get('other', (False,))[0], (s, p.evaluate('batch4.expanded()'))
    # A group the app opens (e.g. returning from the editor) opens its section; closing the section closes it.
    other = s.get('other')
    if other:
        p.evaluate('batch4.expand(%r)' % other[1][0])
        assert sections(p)['other'][0]
        p.locator('.master-group-section[data-group-section="other"] .master-group-section-toggle').click()
        assert not sections(p)['other'][0] and other[1][0] not in p.evaluate('batch4.expanded()')
    # Move (group dialog) assigns the picked meal to a group.
    p.locator('.master-group-section[data-group-section="unassigned"] .master-group-section-toggle').click()
    p.locator('.unassigned-row').nth(0).locator('input').check()
    picked = p.locator('.unassigned-row').nth(0).get_attribute('data-meal-id')
    p.locator('.unassigned-move').click()
    dialog = p.get_by_role('dialog', name='Meal groups', exact=True)
    dialog.wait_for(state='visible')
    target = p.evaluate('batch4.cats()')[0]
    dialog.locator('label.recipe-bulk-choice', has_text=target).first.locator('input').check()
    sb.shot(p, name, 'batch4-move-dialog')
    dialog.get_by_role('button', name='Confirm meal groups', exact=True).click()
    p.wait_for_timeout(300)
    assert p.evaluate('batch4.cat(%s)' % picked) == target, p.evaluate('batch4.cat(%s)' % picked)
    assert p.locator('.unassigned-row').count() == 1
    # Bulk toolbar: Move with arrow, Done not emphasized.
    p.evaluate('batch4.organize(%r)' % target)
    bar = p.locator('#recipeBulkToolbar')
    bar.wait_for(state='visible')
    assert bar.get_by_role('button', name='Move', exact=True).count() == 1 and bar.get_by_role('button', name='Groups', exact=True).count() == 0
    w = p.evaluate("[...document.querySelectorAll('#recipeBulkToolbar .recipe-bulk-actions button')].map(b=>getComputedStyle(b).fontWeight)")
    assert len(set(w)) == 1, w
    sb.shot(p, name, 'batch4-bulk-bar')
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 4: sections + defaults, unassigned checklist/bar/Move, refresh keeps, 5-min background reset, bulk Move/Done', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
