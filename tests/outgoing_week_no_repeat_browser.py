"""v447: a recipe on this week in ANY slot (e.g. a Weekend recipe put by hand on a Rice day) is not auto-picked for next
week while other recipes are waiting. Uses her backup (argv[1], e.g. backup_17: Spaghetti sauce ala Moi on Tue/Rice).
Run: python3 -m http.server 8765 (repo root), then python3 tests/outgoing_week_no_repeat_browser.py <backup.json>"""
import asyncio, json, sys
from playwright.async_api import async_playwright
BK = json.load(open(sys.argv[1]))
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(); pg = await b.new_page(); errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto('http://localhost:8765/README.md')
        await pg.evaluate("s=>{window.localStorage.clear();for(const [k,v] of Object.entries(s))window.localStorage.setItem(k,v)}", BK['storage'])
        await pg.goto('http://localhost:8765/index.html'); await pg.wait_for_timeout(2000)
        r = await pg.evaluate("""()=>{const plan=mealPlans.find(p=>p.id===activePlanId),now=new Set(getDisplayedWeekdayMealsForPlan(plan).filter(e=>e.meal&&!e.meal.temporaryMeal).map(e=>String(e.meal.id)));
          const next=previewMealPlanAdvance().entries.filter(e=>!e.linkedTo&&e.meal&&!e.meal.temporaryMeal);return {repeats:next.filter(e=>now.has(String(e.meal.id))).map(e=>e.day+':'+e.meal.name),next:next.map(e=>e.day.slice(0,3)+':'+e.meal.name)}}""")
        print(r['next'])
        assert not r['repeats'], r
        assert not errs, errs
        print('PASS')
asyncio.run(main())
