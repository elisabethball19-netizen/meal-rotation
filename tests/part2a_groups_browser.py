"""Part 2a: Weekly groups = groups used for weekly meals (toggle on), Other groups = toggle off, one open section at a time,
no expand/collapse-all icons, weekday picker lists only weekly-meal groups.

Run: python3 tests/part2a_groups_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.p2a={
 setup:()=>{const used=new Set([weekdayCategories,...mealPlans.map(p=>p.weekdayCategories)].flatMap(m=>Object.values(m||{}).flatMap(v=>Array.isArray(v)?v:[v]))),off=cats.find(c=>c&&!used.has(c));const v=JSON.parse(localStorage.getItem(GROUP_ROTATION_KEY)||'{}');v[groupIdentity(off,true)]=false;localStorage.setItem(GROUP_ROTATION_KEY,JSON.stringify(v));for(const k of ['weekly','other','unassigned'])setGroupPageSectionOpen(k,k==='weekly');masterExpansionInitialized=true;masterExpandedCategories.clear();showTop=false;allMealsActive=true;groceryTabActive=false;render();return off},
 sections:()=>[...document.querySelectorAll('.master-group-section')].map(s=>[s.dataset.groupSection,[...s.querySelectorAll('.master-category-card,.master-category')].length,s.querySelector('.master-group-section-body').hidden]),
 picker:()=>{showTop=true;allMealsActive=false;render();openRecurringDayEditor('Monday')},
 unassign:()=>{meals.slice(0,3).forEach(m=>{m.cat=''});persist();for(const k of ['weekly','other','unassigned'])setGroupPageSectionOpen(k,k==='unassigned');showTop=false;allMealsActive=true;render();return meals.filter(m=>m.cat==='').length},
 weeklyOpen:()=>{for(const k of ['weekly','other','unassigned'])setGroupPageSectionOpen(k,k==='weekly');showTop=false;allMealsActive=true;render()},
 edit:cat=>openMasterCategoryEditMenu(cat),
 names:key=>[...document.querySelectorAll('.master-group-section[data-group-section="'+key+'"] .master-category-heading,.master-group-section[data-group-section="'+key+'"] h3')].map(x=>x.textContent)
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    off = p.evaluate('p2a.setup()')
    p.wait_for_timeout(400)
    assert p.get_by_role('button', name='Expand all groups', exact=True).count() == 0
    assert p.get_by_role('button', name='Collapse all groups', exact=True).count() == 0
    sec = lambda k: p.locator('.master-group-section[data-group-section="%s"]' % k)
    tog = lambda k: sec(k).locator('.master-group-section-toggle').click() or p.wait_for_timeout(300)
    weekly = sec('weekly').inner_text()
    assert off not in weekly, (off, weekly[:200])
    tog('other')  # accordion: opening Other closes Weekly
    assert off in sec('other').inner_text()
    assert [k for k, n, h in p.evaluate('p2a.sections()') if not h] == ['other'], p.evaluate('p2a.sections()')
    tog('weekly')
    assert [k for k, n, h in p.evaluate('p2a.sections()') if not h] == ['weekly'], p.evaluate('p2a.sections()')
    # Weekday picker lists only groups used for weekly meals.
    p.evaluate('p2a.picker()')
    p.wait_for_timeout(400)
    labels = p.locator('.recurring-group-row input').evaluate_all('xs=>xs.map(x=>x.getAttribute("aria-label"))')
    assert labels and off not in labels, (off, labels)
    sb.shot(p, name, 'part2a-groups')
    p.locator('.recipe-bulk-dialog button[aria-label^="Cancel"]').first.click()
    p.evaluate('c=>p2a.edit(c)', off)
    p.wait_for_timeout(300)
    gap = p.evaluate("""()=>{const l=document.querySelector('.recipe-bulk-dialog .settings-display-option'),sw=l.querySelector('.preference-switch-control').getBoundingClientRect(),r=document.createRange();r.selectNodeContents(l.lastChild);return r.getBoundingClientRect().left-sw.right}""")
    assert 4 <= gap <= 8, gap
    p.locator('.recipe-bulk-dialog button[aria-label^="Cancel"]').first.click()
    p.wait_for_timeout(300)
    p.evaluate('p2a.weeklyOpen()')
    p.wait_for_timeout(300)
    days = p.locator('.master-category-days').all_inner_texts()
    assert days and all(d.strip(' ·') for d in days), days
    colors = p.locator('.master-category-card').evaluate_all('xs=>xs.map(x=>x.style.getPropertyValue("--group-color")).filter(Boolean)')
    assert len(colors) >= 3 and len(set(colors)) >= 2, colors
    sb.shot(p, name, 'part2c-group-colors')
    n = p.evaluate('p2a.unassign()')
    p.wait_for_timeout(400)
    bar = p.locator('.unassigned-bulk-bar')
    assert bar.count() == 1 and bar.evaluate('e=>getComputedStyle(e).position') == 'sticky'
    bar.get_by_role('button', name='Select all', exact=True).click()
    assert bar.locator('.unassigned-bulk-count').inner_text() == '%d selected' % n, bar.inner_text()
    assert p.locator('.unassigned-check input:checked').count() == n
    bar.get_by_role('button', name='Deselect all', exact=True).click()
    assert bar.locator('.unassigned-bulk-count').inner_text() == '0 selected'
    assert p.locator('.unassigned-check input:checked').count() == 0
    sb.shot(p, name, 'part2b-unassigned-bar')
    assert not errors, errors
    c.close()
    print('PASS', name, 'part 2a: sections by weekly toggle, accordion, no expand-all, weekday picker', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
