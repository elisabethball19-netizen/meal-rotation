"""Balanced day groups + picker browse lists (2026-11-19).

- Groups on one day get turns in proportion to their distinct Regulars, spread out, with a 1-in-4 minimum.
- A recipe shared by two of the day's groups counts once.
- Start next week (real UI) follows the balanced turns; credits survive reload/validation; Undo restores them.
- Choose meal browse list shows only Weekly groups and their Regulars; search finds Off menu recipes;
  Add side browse list shows only side groups.

Run: python3 tests/balanced_rotation_browser.py   (screenshots in /tmp/balanced)
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

OUT = Path('/tmp/balanced')
OUT.mkdir(parents=True, exist_ok=True)

sb.fixture.HOOK += '''window.bal={
 setSeq:(groups)=>{const plan=mealPlans.find(p=>p.id===activePlanId);plan.alternatingGroupsV1={Tuesday:{day:'Tuesday',groups:groups.map(g=>groupIdentity(g,true)),position:0}};weekdayCategories.Tuesday=[groups[0]];plan.weekdayCategories={...plan.weekdayCategories,Tuesday:[groups[0]]};saveActiveMealPlan();persist();renderList()},
 simulate:(groups,n)=>{const plan={id:'sim'},seq={day:'Tuesday',groups:groups.map(g=>groupIdentity(g,true)),position:0},out=[];for(let i=0;i<n;i++){const t=nextSequenceTurn(plan,seq);seq.position=t.index;seq.credits=t.credits;out.push(sequenceGroup(seq.groups[t.index]))}return out},
 shares:(groups)=>sequenceGroupShares({id:'sim'},{day:'Tuesday',groups:groups.map(g=>groupIdentity(g,true)),position:0}).map(g=>[g.cat,Math.round(g.share*1000)/1000]),
 share:()=>{const r=meals.find(m=>m.cat==='Rice');r.linkGroup='shared-test';meals.push({...JSON.parse(JSON.stringify(r)),id:9901,cat:'Potatoes',linkGroup:'shared-test'});persist()},
 tuesday:()=>weekdayCategories.Tuesday[0],
 credits:()=>JSON.parse(JSON.stringify(mealPlans.find(p=>p.id===activePlanId).alternatingGroupsV1.Tuesday)),
 offMenu:()=>{const m=meals.find(m=>m.cat==='Rice'&&m.rotation&&!getDisplayedWeekdayMeals().some(e=>String(e.meal.id)===String(m.id)));m.rotation=false;persist();return m.name},
 open:()=>{const e=getDisplayedWeekdayMeals().find(x=>!x.linkedTo&&!x.servingParentId);openWeekdayMealChooser(e.day,e.cat,e.meal)},
 offIds:ids=>ids.some(id=>meals.find(m=>String(m.id)===id)?.rotation===false),
 fixedSide:()=>{const parent=meals.find(m=>m.id===3),veg=meals.find(m=>m.cat==='Vegetables');parent.serveWithEntriesV1=[{id:'fx',type:'fixed',recipeId:String(veg.id),always:true}];persist()},
 cats:()=>[...cats],
 sideGroups:()=>sidePickerGroups(),
 openSide:()=>{const e=getDisplayedWeekdayMeals().find(x=>!x.linkedTo&&!x.servingParentId);openAddSideDialog(e.meal,e.day,[],()=>{})},
 otherGroup:()=>{const values=JSON.parse(localStorage.getItem(GROUP_ROTATION_KEY)||'{}');values[groupIdentity('Vegetables',true)]=false;localStorage.setItem(GROUP_ROTATION_KEY,JSON.stringify(values));renderList()}
};'''


def is_spread(seq, small):
    return all(not (a == small and b == small) for a, b in zip(seq, seq[1:]))


def start_next_week(p):
    p.locator('.start-week-text').first.click()
    p.get_by_role('button', name='Start next week →').last.click()
    p.wait_for_timeout(300)


def run(browser, name):
    c, p, errors, _ = sb.open_page(browser, name)
    # Proportional turns: 5 rice + 2 potatoes -> 5 and 2 per 7, never two potatoes in a row.
    seq = p.evaluate('bal.simulate(["Rice","Potatoes"],14)')
    assert seq.count('Rice') == 10 and seq.count('Potatoes') == 4, seq
    assert is_spread(seq, 'Potatoes'), seq
    # Minimum share: 5 rice + 1 vegetable -> vegetable gets 1 in 4.
    assert p.evaluate('bal.shares(["Rice","Vegetables"])') == [['Rice', 0.75], ['Vegetables', 0.25]]
    seq = p.evaluate('bal.simulate(["Rice","Vegetables"],8)')
    assert seq.count('Vegetables') == 2, seq
    # Shared recipe counts once (split): Rice 4.5, Potatoes 2.5.
    p.evaluate('bal.share()')
    assert p.evaluate('bal.shares(["Rice","Potatoes"])') == [['Rice', 0.643], ['Potatoes', 0.357]]
    c.close()

    # Real Start next week flow, reload validation, Undo.
    c, p, errors, _ = sb.open_page(browser, name)
    p.evaluate('bal.setSeq(["Rice","Potatoes"])')
    got = []
    for _ in range(7):
        start_next_week(p)
        got.append(p.evaluate('bal.tuesday()'))
    assert got.count('Rice') == 5 and got.count('Potatoes') == 2 and is_spread(got, 'Potatoes'), got
    saved = p.evaluate('bal.credits()')
    assert 'credits' in saved, saved
    p.reload()
    p.wait_for_timeout(500)
    assert p.evaluate('bal.credits()') == saved, 'credits lost on reload'
    assert not p.locator('text=Saved data is unavailable').count()
    before = p.evaluate('bal.credits()')
    start_next_week(p)
    assert p.evaluate('bal.credits()') != before
    p.get_by_role('button', name='Undo', exact=True).first.click()
    p.wait_for_timeout(300)
    assert p.evaluate('bal.credits()') == before, 'Undo did not restore turns'
    c.close()

    # Choose meal browse list: Weekly groups + Regulars only; search still finds Off menu.
    c, p, errors, _ = sb.open_page(browser, name)
    off = p.evaluate('bal.offMenu()')
    p.evaluate('bal.otherGroup()')
    p.evaluate('bal.open()')
    picker = p.locator('.weekday-meal-picker')
    groups = picker.locator('.master-category-card').evaluate_all('els=>els.map(e=>e.dataset.group)')
    assert 'Vegetables' not in groups and 'Rice' in groups, groups
    names = picker.locator('.weekday-meal-choice').evaluate_all('els=>els.map(e=>e.dataset.mealId)')
    assert not p.evaluate('ids=>bal.offIds(ids)', names), 'Off menu shown'
    p.screenshot(path=str(OUT / (name.split('.')[0] + '-choose-meal.png')))
    picker.get_by_role('button', name='Search recipes').click()
    picker.locator('input[type=search]').fill(off)
    assert picker.locator('.weekday-meal-choice', has_text=off).count() >= 1, 'search should find Off menu'
    p.screenshot(path=str(OUT / (name.split('.')[0] + '-choose-search.png')))
    picker.get_by_role('button', name='Cancel').click()
    # Add side browse list: only groups used for sides.
    assert p.evaluate('bal.sideGroups()') == p.evaluate('bal.cats()'), 'no side groups yet -> all groups'
    p.evaluate('bal.fixedSide()')
    side_groups = p.evaluate('bal.sideGroups()')
    assert side_groups == ['Vegetables'], side_groups
    p.evaluate('bal.openSide()')
    shown = p.locator('.serving-add-dialog .master-category-card').evaluate_all('els=>els.map(e=>e.dataset.group)')
    assert shown and set(shown) <= set(side_groups), (shown, side_groups)
    p.screenshot(path=str(OUT / (name.split('.')[0] + '-add-side.png')))
    assert not errors, errors
    c.close()
    print('side groups', side_groups, 'shown', shown)
    print('PASS', name, 'balanced day groups, Start next week/Undo/reload, picker browse filtering', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
