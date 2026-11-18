"""Batch 13 (Plan Ahead, part 1): Week calendar button opens Plan ahead; plan a meal for this week, next week and a
far date; this/next-week plans replace that day's main through the normal choose-meal path (sides unchanged), far
plans wait; one meal per date; Cancel discards; Save is undoable; plans persist across reload.

Run: python3 tests/batch13_plan_ahead_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''const b13Store=()=>typeof testStorage!=='undefined'?testStorage:localStorage;window.batch13={
 week:()=>{showTop=true;allMealsActive=true;groceryTabActive=false;overviewWeekOffset=0;render()},
 main:(week,date)=>{const plan=mealPlans.find(p=>p.id===activePlanId),src=week?previewMealPlanAdvance():{plan:{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters},entries:getDisplayedWeekdayMealsForPlan({...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters})};const e=src.entries.find(e=>!e.linkedTo&&!e.servingParentId&&!e.occasional&&cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},src.plan.rotationCalendar))===date);return e?[e.meal.name,e.cat,(src.entries.filter(x=>x.linkedTo&&String(x.linkedTo)===String(e.meal.id)||x.servingParentId).length)]:null},
 dates:()=>{const plan=mealPlans.find(p=>p.id===activePlanId),cur=getDisplayedWeekdayMealsForPlan({...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}).filter(e=>!e.linkedTo&&!e.servingParentId&&!e.occasional&&e.cat&&e.cat!=='@day').map(e=>cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},plan.rotationCalendar))),nx=previewMealPlanAdvance();return [cur,nx.entries.filter(e=>!e.linkedTo&&!e.servingParentId&&!e.occasional&&e.cat&&e.cat!=='@day').map(e=>cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},nx.plan.rotationCalendar)))]},
 rice:()=>meals.filter(m=>m.cat==='Rice').map(m=>m.name),
 plans:()=>plannedMealsFor().map(p=>[p.date,meals.find(m=>String(m.id)===p.mealId)?.name,p.shopEarly,p.applied]),
 dismissed:()=>plannedMealsFor().filter(p=>p.shopDismissed).map(p=>p.date),
 undo:()=>document.getElementById('undo').click(),
 seedShop:date=>{const list=plannedMealsFor();list.push({id:'shop-'+date,date,mealId:String(meals.find(m=>m.cat==='Rice').id),shopEarly:true,applied:null});writePlannedMeals(activePlanId,list);makeAheadDisplayPrefs.showMakeAheadReminders=true;saveMakeAheadDisplayPrefs();batch13.home()},
 dayMeal:date=>{const plan=mealPlans.find(p=>p.id===activePlanId),cur={...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters},e=getDisplayedWeekdayMealsForPlan(cur).find(e=>!e.linkedTo&&!e.servingParentId&&cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},cur.rotationCalendar))===date);return e?[e.meal.name,!!e.occasional]:null},
 emptyDates:()=>{const plan=mealPlans.find(p=>p.id===activePlanId),start=mealPlanWeekStart(plan);return orderedDays().filter(d=>!(weekdayCategories[d]||[]).filter(g=>cats.includes(g)).length).map(d=>cookingLocalDate(cookingDateInWeek(d,start)))},
 home:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;render()}
};'''


def plan(d, date, recipe, shop=False):
    d.get_by_role('textbox', name='Planned date').fill(date) if d.get_by_role('textbox', name='Planned date').count() else d.locator('input[type=date]').fill(date)
    d.get_by_role('searchbox', name='Search recipes to plan', exact=True).fill(recipe)
    d.locator('.plan-ahead-choice', has_text=recipe).first.click()
    if shop:
        d.get_by_role('switch', name='Shop early', exact=True).check()
    d.locator('.plan-ahead-add').click()


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    cur, nxt = p.evaluate('batch13.dates()')
    d0, d1 = cur[0], nxt[0]
    rice = p.evaluate('batch13.rice()')
    before0, before1 = p.evaluate('([w,d])=>batch13.main(w,d)', [0, d0]), p.evaluate('([w,d])=>batch13.main(w,d)', [1, d1])
    pick0 = next(n for n in rice if n != before0[0])
    pick1 = next(n for n in rice if n != before1[0] and n != pick0)
    p.evaluate('batch13.week()')
    p.get_by_role('button', name='Plan ahead', exact=True).click()
    d = p.get_by_role('dialog', name='Plan ahead', exact=True)
    d.wait_for(state='visible')
    plan(d, d0, pick0)
    # Cancel discards.
    d.get_by_role('button', name='Cancel', exact=True).click()
    assert p.evaluate('batch13.plans()') == []
    p.get_by_role('button', name='Plan ahead', exact=True).click()
    d.wait_for(state='visible')
    plan(d, d0, pick0)
    plan(d, d1, pick1, shop=True)
    plan(d, '2027-01-15', pick0)
    plan(d, d0, pick1)  # same date twice is refused
    assert 'already planned' in d.locator('.recipe-bulk-error').text_content()
    assert d.locator('.plan-ahead-row').count() == 3
    sb.shot(p, name, 'batch13-plan-ahead')
    d.get_by_role('button', name='Save planned meals', exact=True).click()
    p.wait_for_timeout(400)
    now0, now1 = p.evaluate('([w,d])=>batch13.main(w,d)', [0, d0]), p.evaluate('([w,d])=>batch13.main(w,d)', [1, d1])
    assert now0[0] == pick0 and now0[1] == before0[1], (now0, before0)
    assert now1[0] == pick1, (now1, before1)
    plans = p.evaluate('batch13.plans()')
    assert [x[0] for x in plans] == [d0, d1, '2027-01-15'] and plans[1][2] is True and plans[0][3] == d0 and plans[2][3] is None, plans
    sb.shot(p, name, 'batch13-week-after')
    # Reload keeps plans and the applied schedule.
    p.reload()
    p.wait_for_function('window.batch13')
    assert len(p.evaluate('batch13.plans()')) == 3 and p.evaluate('([w,d])=>batch13.main(w,d)', [0, d0])[0] == pick0
    # A day with no meal group gets the planned meal as its one-time meal.
    empty = p.evaluate('batch13.emptyDates()')
    if empty:
        p.evaluate('batch13.week()')
        p.get_by_role('button', name='Plan ahead', exact=True).click()
        d.wait_for(state='visible')
        pick2 = next(n for n in rice if n not in (pick0, pick1, before1[0]))
        plan(d, empty[0], pick2)
        d.get_by_role('button', name='Save planned meals', exact=True).click()
        p.wait_for_timeout(400)
        assert p.evaluate('d=>batch13.dayMeal(d)', empty[0]) == [pick2, True], p.evaluate('d=>batch13.dayMeal(d)', empty[0])
    # Shop early: a reminder in Today's To-Do within a week of the date (not earlier); checking dismisses only.
    p.evaluate("batch13.seedShop('2026-11-27')")
    assert p.locator('.shop-early-reminder').count() == 0, 'more than a week away'
    p.evaluate("batch13.seedShop('2026-11-21')")
    rem = p.locator('.shop-early-reminder')
    assert rem.count() == 1 and 'Shop early for' in rem.inner_text(), p.locator('#list').inner_text()[:300]
    sb.shot(p, name, 'batch13-shop-early')
    rem.locator('input').check()
    p.wait_for_timeout(2500)
    assert p.locator('.shop-early-reminder').count() == 0, (p.evaluate('batch13.dismissed()'), errors, p.locator('#todaysTodo').inner_text())
    assert [x for x in p.evaluate('batch13.plans()') if x[0] == '2026-11-21']
    # A real Start next week keeps next week's planned meal in place.
    p.evaluate('batch13.home()')
    p.locator('.start-week-text').first.click()
    sw = p.get_by_role('dialog', name='Start next week', exact=True)
    sw.wait_for(state='visible')
    sw.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(600)
    assert p.evaluate('([w,d])=>batch13.main(w,d)', [0, d1])[0] == pick1, p.evaluate('([w,d])=>batch13.main(w,d)', [0, d1])
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 13: plan ahead dialog, this/next week applied as main, far date waits, one per date, cancel, persist', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
