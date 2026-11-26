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
        nxt="()=>previewMealPlanAdvance().entries.filter(x=>!x.linkedTo).map(x=>[x.day.slice(0,3),x.cat,x.meal?.name])"
        print('NEXT',await pg.evaluate(nxt))
        await pg.evaluate("()=>{const e=previewMealPlanAdvance().entries.find(x=>x.day==='Friday'&&!x.linkedTo);applyRecipeBulk([String(e.meal.id)],{},{mealSelection:{planId:activePlanId,week:1,day:'Friday',category:e.cat,mealId:String(e.meal.id),empty:true}})}"); await pg.wait_for_timeout(500)
        print('CLEARED',await pg.evaluate(nxt))
        await pg.evaluate("()=>{rotationWeekOffset=1;renderList();openWeekdayMealChooser('Friday','Tacos',null,false,{})}"); await pg.wait_for_timeout(500)
        print('BTNS',await pg.evaluate("()=>[...document.querySelectorAll('.weekday-next-recipe-row button')].map(b=>b.textContent)"))
        await pg.evaluate("()=>[...document.querySelectorAll('.weekday-next-recipe-row button')].find(b=>b.textContent==='Use next recipe').click()"); await pg.wait_for_timeout(800)
        print('AFTER',await pg.evaluate(nxt))
        print('errs',errs)
asyncio.run(main())
