"""v442 checks on a copy of real data: (1) Clear meal on a pinned day only clears this week and the pin brings it back
on Start next week; (2) 'Use next recipe' fills an empty day in the Next week view. Needs a backup JSON path as argv[1]."""
import asyncio,json,sys
from playwright.async_api import async_playwright
BK=json.load(open(sys.argv[1]))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(); pg=await b.new_page(); errs=[]
        pg.on('pageerror',lambda e:errs.append(str(e)))
        await pg.goto('http://localhost:8765/README.md'); await pg.evaluate("s=>{window.localStorage.clear();for(const [k,v] of Object.entries(s))window.localStorage.setItem(k,v)}",BK['storage'])
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2000)
        info="""()=>{const plan=mealPlans.find(p=>p.id===activePlanId);const e=getDisplayedWeekdayMealsForPlan(plan).filter(x=>x.day==='Saturday');return {now:e.map(x=>[x.cat,x.meal?.name,!!x.occasional,slotPinned(plan,x)]),pins:plan.pinnedMealsV1,next:previewMealPlanAdvance().entries.filter(x=>x.day==='Saturday').map(x=>[x.cat,x.meal?.name])}}"""
        print('BEFORE',await pg.evaluate(info))
        await pg.evaluate("""()=>{const plan=mealPlans.find(p=>p.id===activePlanId);const e=recipePlanEntries(plan.id).find(x=>x.day==='Saturday'&&x.meal);skipMealOccurrence(plan.id,e,simpleSideOccurrenceKey(plan,e));renderList()}""")
        await pg.wait_for_timeout(500)
        print('AFTER CLEAR',await pg.evaluate(info))
        await pg.evaluate("()=>{window.startNextWeekAllowed=()=>true;openRotateOptions()}"); await pg.wait_for_timeout(500)
        print('ROW',await pg.evaluate("()=>[document.querySelectorAll('dialog[open]').length,...[...document.querySelectorAll('.start-week-choice')].map(l=>[l.textContent,l.querySelector('input').checked,l.querySelector('input').disabled])]"))
        await pg.evaluate("()=>[...document.querySelectorAll('button')].find(b=>b.textContent.startsWith('Start next week'))?.click()"); await pg.wait_for_timeout(1500)
        print('AFTER START NEXT WEEK',await pg.evaluate("""()=>{const plan=mealPlans.find(p=>p.id===activePlanId);const e=getDisplayedWeekdayMealsForPlan(plan).filter(x=>x.day==='Saturday');return {now:e.map(x=>[x.cat,x.meal?.name,slotPinned(plan,x)]),pins:plan.pinnedMealsV1}}"""))
        print('errs',errs)
        await b.close()
asyncio.run(main())
