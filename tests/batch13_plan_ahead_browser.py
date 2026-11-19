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
 week:()=>{showMealPlanTabs=true;showTop=true;allMealsActive=true;groceryTabActive=false;overviewWeekOffset=0;render()},
 main:(week,date)=>{const plan=mealPlans.find(p=>p.id===activePlanId),src=week?previewMealPlanAdvance():{plan:{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters},entries:getDisplayedWeekdayMealsForPlan({...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters})};const e=src.entries.find(e=>!e.linkedTo&&!e.servingParentId&&!e.occasional&&cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},src.plan.rotationCalendar))===date);return e?[e.meal.name,e.cat,(src.entries.filter(x=>x.linkedTo&&String(x.linkedTo)===String(e.meal.id)||x.servingParentId).length)]:null},
 dates:()=>{const plan=mealPlans.find(p=>p.id===activePlanId),cur=getDisplayedWeekdayMealsForPlan({...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}).filter(e=>!e.linkedTo&&!e.servingParentId&&!e.occasional&&e.cat&&e.cat!=='@day').map(e=>cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},plan.rotationCalendar))),nx=previewMealPlanAdvance();return [cur,nx.entries.filter(e=>!e.linkedTo&&!e.servingParentId&&!e.occasional&&e.cat&&e.cat!=='@day').map(e=>cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},nx.plan.rotationCalendar)))]},
 rice:()=>meals.filter(m=>m.cat==='Rice').map(m=>m.name),
 plans:()=>plannedMealsFor().map(p=>[p.date,meals.find(m=>String(m.id)===p.mealId)?.name,p.shopEarly,p.applied]),
 dismissed:()=>plannedMealsFor().filter(p=>p.shopDismissed).map(p=>p.date),
 undo:()=>document.getElementById('undo').click(),
 seedShop:date=>{const list=plannedMealsFor();list.push({id:'shop-'+date,date,mealId:String(meals.find(m=>m.cat==='Rice').id),shopEarly:true,applied:null});writePlannedMeals(activePlanId,list);makeAheadDisplayPrefs.showMakeAheadReminders=true;saveMakeAheadDisplayPrefs();batch13.home()},
 dayMeal:date=>{const plan=mealPlans.find(p=>p.id===activePlanId),cur={...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters},e=getDisplayedWeekdayMealsForPlan(cur).find(e=>!e.linkedTo&&!e.servingParentId&&cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},cur.rotationCalendar))===date);return e?[e.meal.name,!!e.occasional]:null},
 emptyDates:()=>{const plan=mealPlans.find(p=>p.id===activePlanId),start=mealPlanWeekStart(plan);return orderedDays().filter(d=>!(weekdayCategories[d]||[]).filter(g=>cats.includes(g)).length).map(d=>cookingLocalDate(cookingDateInWeek(d,start)))},
 named:date=>{const plan=mealPlans.find(p=>p.id===activePlanId),cur={...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters},nx=previewMealPlanAdvance();return [[cur,getDisplayedWeekdayMealsForPlan(cur)],[nx.plan,nx.entries]].flatMap(([pl,es])=>es.filter(e=>!e.linkedTo&&!e.servingParentId&&cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},pl.rotationCalendar))===date).map(e=>e.meal.name))},
 dbg:d=>[JSON.stringify(plannedMealsFor().find(x=>x.date===d)),JSON.stringify(plannedDateSlot(activePlanId,d))],
 seedEarly:(date,from)=>{const list=plannedMealsFor().filter(p=>p.date!==date);list.push({id:'early-'+date,date,mealId:String(meals.find(m=>m.cat==='Rice').id),shopEarly:true,shopFrom:from,applied:null});writePlannedMeals(activePlanId,list);showTop=true;allMealsActive=false;groceryTabActive=true;render()},
 shopFrom:date=>plannedMealsFor().find(p=>p.date===date)?.shopFrom||null,
 replacedName:d=>{const it=plannedMealsFor().find(x=>x.date===d);return it&&it.replaced?meals.find(m=>String(m.id)===String(it.replaced))?.name||null:null},
 menu:date=>{const plan=mealPlans.find(p=>p.id===activePlanId),cur={...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters},e=getDisplayedWeekdayMealsForPlan(cur).find(e=>!e.linkedTo&&!e.servingParentId&&cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},cur.rotationCalendar))===date);openTopMealActionMenu(e.day,e.cat,e.meal)},
 seedCustom:(date,from)=>{const list=plannedMealsFor().filter(p=>p.date!==date);list.push({id:'cust-'+date,date,name:'Fish fry',ingredients:['2 lb cod','1 bag fries'],shopEarly:true,shopFrom:from,applied:null});writePlannedMeals(activePlanId,list);showTop=true;allMealsActive=false;groceryTabActive=true;render()},
 raw:()=>plannedMealsFor().map(p=>[p.date,p.mealId??null,p.name??null]),
 home:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=0;render()}
};'''


def plan(p, date, recipe, shop=False, save=True, popup=False):
    """Plan ahead v3: type the date (or use the calendar pop-up), search and pick, optional Shop early, one Save."""
    if not p.get_by_role('dialog', name='Plan ahead', exact=True).count():
        p.get_by_role('button', name='Plan ahead', exact=True).click()
    d = p.get_by_role('dialog', name='Plan ahead', exact=True)
    d.wait_for(state='visible')
    if popup:
        d.get_by_role('button', name='Open calendar', exact=True).click()
        pop = p.get_by_role('dialog', name='Choose date', exact=True)
        for _ in range(24):
            if pop.locator('.plan-ahead-day[data-date="%s"]' % date).count():
                break
            pop.get_by_role('button', name='Next month', exact=True).click()
        pop.locator('.plan-ahead-day[data-date="%s"]' % date).click()
        pop.get_by_role('button', name='Use this date', exact=True).click()
    else:
        f = d.get_by_role('textbox', name='Meal date', exact=True)
        f.fill(date)
        f.dispatch_event('change')
    d.get_by_role('searchbox', name='Search recipes to plan', exact=True).fill(recipe)
    d.locator('.plan-ahead-choice', has_text=recipe).first.click()
    if shop and d.locator('.plan-ahead-shop input').is_visible():
        d.locator('.plan-ahead-shop input').check()
    if save:
        d.get_by_role('button', name='Save planned meals', exact=True).click()
        p.wait_for_timeout(300)
    return d


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    cur, nxt = p.evaluate('batch13.dates()')
    d0, d1 = cur[0], nxt[0]
    rice = p.evaluate('batch13.rice()')
    before0, before1 = p.evaluate('([w,d])=>batch13.main(w,d)', [0, d0]), p.evaluate('([w,d])=>batch13.main(w,d)', [1, d1])
    pick0 = next(n for n in rice if n != before0[0])
    pick1 = next(n for n in rice if n != before1[0] and n != pick0)
    p.evaluate('batch13.home()')
    p.get_by_role('button', name='Plan ahead', exact=True).click()
    d = p.get_by_role('dialog', name='Plan ahead', exact=True)
    assert d.locator('.plan-ahead-results > *').count() == 0 and d.locator('.plan-ahead-calendar').count() == 0, 'search only, no big calendar'
    assert d.locator('.plan-ahead-shop-box').is_hidden(), 'Shop early waits for a saved recipe'
    sb.shot(p, name, 'batch13-groups')
    d.get_by_role('button', name='Cancel', exact=True).click()
    d = plan(p, d0, pick0, save=False)
    assert d.locator('.plan-ahead-chosen').inner_text().startswith(pick0)
    # Cancel discards.
    d.get_by_role('button', name='Cancel', exact=True).click()
    assert p.evaluate('batch13.plans()') == []
    plan(p, d0, pick0)
    plan(p, d1, pick1, shop=True, popup=True)
    d = plan(p, '2027-01-15', pick0, save=False)
    sb.shot(p, name, 'batch13-plan-ahead')
    d.get_by_role('button', name='Save planned meals', exact=True).click(); p.wait_for_timeout(300)
    d = plan(p, d0, pick1)  # same date twice is refused
    assert 'already planned' in d.locator('.recipe-bulk-error').text_content()
    assert d.locator('.plan-ahead-row').count() == 3
    d.get_by_role('button', name='Cancel', exact=True).click()
    p.wait_for_timeout(400)
    now0, now1 = p.evaluate('([w,d])=>batch13.main(w,d)', [0, d0]), p.evaluate('([w,d])=>batch13.main(w,d)', [1, d1])
    assert now0[0] == pick0 and now0[1] == before0[1], (now0, before0)
    assert now1[0] == pick1, (now1, before1)
    plans = p.evaluate('batch13.plans()')
    assert [x[0] for x in plans] == [d0, d1, '2027-01-15'] and plans[1][2] is False and plans[0][3] == d0 and plans[2][3] is None, plans
    sb.shot(p, name, 'batch13-week-after')
    # Reload keeps plans and the applied schedule.
    p.reload()
    p.wait_for_function('window.batch13')
    assert len(p.evaluate('batch13.plans()')) == 3 and p.evaluate('([w,d])=>batch13.main(w,d)', [0, d0])[0] == pick0
    # A day with no meal group gets the planned meal as its one-time meal.
    empty = p.evaluate('batch13.emptyDates()')
    if empty:
        p.evaluate('batch13.home()')
        pick2 = next(n for n in rice if n not in (pick0, pick1, before1[0]))
        plan(p, empty[0], pick2)
        p.wait_for_timeout(200)
        assert p.evaluate('d=>batch13.dayMeal(d)', empty[0]) == [pick2, True], p.evaluate('d=>batch13.dayMeal(d)', empty[0])
    # Shop early: from its "Groceries from" date, the planned meal's groceries join the list (no to-do reminder).
    p.evaluate("([d,f])=>batch13.seedEarly(d,f)", ['2026-12-10', '2026-11-30'])
    assert p.locator('.grocery-recipe-link', has_text='Thu, Dec 10').count() == 0, 'not yet: groceries-from date is later'
    p.evaluate("([d,f])=>batch13.seedEarly(d,f)", ['2026-12-10', '2026-11-16'])
    early = p.locator('.grocery-recipe-link', has_text='Thu, Dec 10')
    assert early.count() >= 1, p.locator('#list').inner_text()[:400]
    assert p.locator('.shop-early-reminder').count() == 0
    sb.shot(p, name, 'batch13-shop-early')
    row = p.locator('.master-grocery-item', has=early.first)
    row.locator('input[type=checkbox]').first.check(); p.wait_for_timeout(200)
    assert row.locator('input[type=checkbox]').first.is_checked()
    # Dialog: after picking, search hides; Shop early (only past next week) shows "Add groceries on", prefilled a week early.
    p.evaluate('batch13.home()')
    d = plan(p, '2026-12-17', rice[0], save=False)
    assert d.get_by_role('searchbox', name='Search recipes to plan', exact=True).is_hidden() and d.locator('.plan-ahead-choice').count() == 0
    assert d.locator('.plan-ahead-chosen').inner_text().startswith(rice[0]) and d.locator('.plan-ahead-summary').count() == 0
    d.locator('.plan-ahead-shop input').check()
    sf = d.get_by_role('textbox', name='Add groceries on', exact=True)
    assert sf.input_value() == 'Thu, Dec 10', sf.input_value()
    d.get_by_role('button', name='Choose grocery date', exact=True).click()
    pop = p.get_by_role('dialog', name='Add groceries on', exact=True)
    pop.locator('.plan-ahead-day[data-date="2026-12-12"]').click()
    pop.get_by_role('button', name='Use this date', exact=True).click()
    assert sf.input_value() == 'Sat, Dec 12'
    sb.shot(p, name, 'batch13-shop-choices')
    # "+ Plan another" queues it; a one-time meal with groceries goes in next.
    d.get_by_role('button', name='Plan another meal').click()
    assert d.get_by_role('textbox', name='Meal date', exact=True).input_value() == '' and d.locator('.plan-ahead-row[data-date="2026-12-17"]').count() == 1
    d.get_by_role('textbox', name='Meal date', exact=True).fill('2026-12-18'); d.get_by_role('textbox', name='Meal date', exact=True).dispatch_event('change')
    d.get_by_role('searchbox', name='Search recipes to plan', exact=True).fill('Fish fry')
    d.locator('.plan-ahead-custom').click()
    d.get_by_role('textbox', name='Groceries for this one-time meal', exact=True).fill('2 lb cod\n1 bag fries')
    d.locator('.plan-ahead-shop input').check()
    sb.shot(p, name, 'batch13-custom-groceries')
    d.get_by_role('button', name='Save planned meals', exact=True).click(); p.wait_for_timeout(300)
    assert p.evaluate("batch13.shopFrom('2026-12-17')") == '2026-12-12'
    assert p.evaluate("batch13.shopFrom('2026-12-18')") == '2026-12-11'
    p.evaluate("([d,f])=>batch13.seedCustom(d,f)", ['2026-12-18', '2026-11-16'])
    assert p.locator('.grocery-ingredient-name', has_text='cod').count() == 1, p.locator('#list').inner_text()[:300]
    p.evaluate('batch13.home()')
    # Planned rows: chevron opens Edit / Delete.
    p.get_by_role('button', name='Plan ahead', exact=True).click()
    d = p.get_by_role('dialog', name='Plan ahead', exact=True)
    d.locator('.plan-ahead-row[data-date="2026-12-18"] .plan-ahead-chevron').click()
    assert d.get_by_role('button', name='Edit plan for Fri, Dec 18').is_visible() and d.get_by_role('button', name='Delete plan for Fri, Dec 18').is_visible()
    d.get_by_role('button', name='Edit plan for Fri, Dec 18').click()
    assert d.locator('.plan-ahead-chosen').inner_text().startswith('Fish fry') and '2 lb cod' in d.get_by_role('textbox', name='Groceries for this one-time meal', exact=True).input_value()
    d.get_by_role('button', name='Cancel', exact=True).click(); p.wait_for_timeout(200)
    # Custom meal: typing a name that matches nothing offers "Add ... as a one-time meal".
    taken = {x[0] for x in p.evaluate('batch13.raw()')}
    free = [x for x in p.evaluate('batch13.emptyDates()') if x > '2026-11-16' and x not in taken]
    if free:
        cur = [cur[0], free[0]]
        p.evaluate('batch13.home()')
        p.get_by_role('button', name='Plan ahead', exact=True).click()
        d = p.get_by_role('dialog', name='Plan ahead', exact=True)
        d.get_by_role('textbox', name='Meal date', exact=True).fill(cur[1])
        d.get_by_role('textbox', name='Meal date', exact=True).dispatch_event('change')
        d.get_by_role('searchbox', name='Search recipes to plan', exact=True).fill('Pizza night')
        custom = d.locator('.plan-ahead-custom')
        assert custom.count() == 1 and 'one-time meal' in custom.inner_text()
        custom.click()
        sb.shot(p, name, 'batch13-custom')
        d.get_by_role('button', name='Save planned meals', exact=True).click()
        p.wait_for_timeout(400)
        assert [cur[1], None, 'Pizza night'] in p.evaluate('batch13.raw()'), p.evaluate('batch13.raw()')
        assert 'Pizza night' in p.evaluate('d=>batch13.named(d)', cur[1]), p.evaluate('d=>batch13.named(d)', cur[1])
    # Deleting an applied plan puts the day back to the meal it replaced (recipe and one-time meal).
    if free:
        p.evaluate('batch13.home()')
        p.get_by_role('button', name='Plan ahead', exact=True).click()
        d = p.get_by_role('dialog', name='Plan ahead', exact=True)
        d.locator('.plan-ahead-row[data-date="%s"] .plan-ahead-chevron' % cur[1]).click(); d.locator('button[aria-label^="Delete plan"]').first.click()
        d.get_by_role('button', name='Save planned meals', exact=True).click(); p.wait_for_timeout(400)
        assert 'Pizza night' not in p.evaluate('d=>batch13.named(d)', cur[1]), p.evaluate('d=>batch13.named(d)', cur[1])
    # A real Start next week keeps next week's planned meal in place.
    p.evaluate('batch13.home()')
    p.locator('.start-week-text').first.click()
    sw = p.get_by_role('dialog', name='Start next week', exact=True)
    sw.wait_for(state='visible')
    sw.locator('button.smallbtn', has_text='Start next week').click()
    p.wait_for_timeout(600)
    assert p.evaluate('([w,d])=>batch13.main(w,d)', [0, d1])[0] == pick1, p.evaluate('([w,d])=>batch13.main(w,d)', [0, d1])
    # Removing that applied plan puts the day back to the meal it replaced.
    p.evaluate('batch13.home()')
    p.get_by_role('button', name='Plan ahead', exact=True).click()
    d = p.get_by_role('dialog', name='Plan ahead', exact=True)
    replaced = p.evaluate('d=>batch13.replacedName(d)', d1)
    d.locator('.plan-ahead-row[data-date="%s"] .plan-ahead-chevron' % d1).click(); d.locator('button[aria-label^="Delete plan"]').first.click()
    d.get_by_role('button', name='Save planned meals', exact=True).click(); p.wait_for_timeout(400)
    if replaced:
        assert p.evaluate('d=>batch13.named(d)', d1)[0] == replaced, (p.evaluate('d=>batch13.named(d)', d1), replaced)
    # Deterministic check: plan a different recipe on that day, then remove the plan -> the day returns.
    was = p.evaluate('d=>batch13.named(d)', d1)[0]
    swap = next(n for n in rice if n != was)
    plan(p, d1, swap)
    assert p.evaluate('d=>batch13.named(d)', d1)[0] == swap
    # "Back to original" in the meal options does the same from the card, and removes the plan.
    p.evaluate('d=>batch13.menu(d)', d1)
    p.get_by_role('button', name='Back to original', exact=True).click(); p.wait_for_timeout(400)
    assert p.evaluate('d=>batch13.named(d)', d1)[0] == was and d1 not in [x[0] for x in p.evaluate('batch13.raw()')]
    plan(p, d1, swap)
    p.get_by_role('button', name='Plan ahead', exact=True).click()
    d = p.get_by_role('dialog', name='Plan ahead', exact=True)
    d.locator('.plan-ahead-row[data-date="%s"] .plan-ahead-chevron' % d1).click(); d.locator('button[aria-label^="Delete plan"]').first.click()
    d.get_by_role('button', name='Save planned meals', exact=True).click(); p.wait_for_timeout(400)
    assert p.evaluate('d=>batch13.named(d)', d1)[0] == was, (p.evaluate('d=>batch13.named(d)', d1), was)
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 13: plan ahead dialog, this/next week applied as main, far date waits, one per date, cancel, persist', flush=True)



def run_avoid(browser, name):
    """Rotation tries a recipe planned two weeks out last for next week's automatic slot."""
    c, p, errors, prefix = sb.open_page(browser, name)
    cur, nxt = p.evaluate('batch13.dates()')
    auto_next = p.evaluate('([w,d])=>batch13.main(w,d)', [1, nxt[0]])[0]
    from datetime import date, timedelta
    far = (date.fromisoformat(nxt[0]) + timedelta(days=7)).isoformat()
    p.evaluate('batch13.home()')
    plan(p, far, auto_next)
    p.wait_for_timeout(200)
    now_next = p.evaluate('([w,d])=>batch13.main(w,d)', [1, nxt[0]])[0]
    assert now_next != auto_next, (now_next, auto_next)
    assert not errors, errors
    c.close()
    print('PASS', name, 'batch 13: rotation defers a recipe planned for the following week', flush=True)

if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
            run_avoid(b, n)
        b.close()
