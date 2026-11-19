"""Use next recipe: a day whose group was removed no longer holds recipes back (stale skip records ignored).

Run: python3 tests/stale_skip_browser.py
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright
sys.path.insert(0, str(Path(__file__).parent))
import sides_batch127_browser as sb  # noqa: E402

sb.fixture.HOOK += '''window.stale={
 run:()=>{const plan=mealPlans.find(p=>p.id===activePlanId);const prior=getDisplayedWeekdayMealsForPlan({...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters});const e=prior.find(x=>!x.linkedTo&&!x.servingParentId&&!x.occasional&&x.cat);
  const free=automaticSlotCandidates(plan,e.day,e.cat,meals,prior).filter(m=>String(m.id)!==String(e.meal.id));const target=free[0];
  const ghost=orderedDays().find(d=>!(weekdayCategories[d]||[]).includes(e.cat));plan.cycleSlotChoices={...plan.cycleSlotChoices,[ghost+'::'+e.cat]:{mealId:'x',deferredMealIds:[String(target.id)]}};
  return {day:e.day,cat:e.cat,meal:e.meal.id,target:target.name}},
 skip:async(day,cat,id)=>{await skipScheduledMeal(day,cat,meals.find(m=>String(m.id)===String(id)));const plan=mealPlans.find(p=>p.id===activePlanId);return getDisplayedWeekdayMealsForPlan({...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}).find(x=>x.day===day&&x.cat===cat&&!x.linkedTo)?.meal.name}
};'''


def run(browser, name):
    c, p, errors, prefix = sb.open_page(browser, name)
    info = p.evaluate('stale.run()')
    got = p.evaluate('([d,c,m])=>stale.skip(d,c,m)', [info['day'], info['cat'], info['meal']])
    assert got == info['target'], (got, info)
    assert not errors, errors
    c.close()
    print('PASS', name, 'stale skip records from a removed group do not hold recipes back', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for n in ['index.html', 'meal-rotation-test.html']:
            run(b, n)
        b.close()
