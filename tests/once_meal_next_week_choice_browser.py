"""v448: a saved next-week choice for a one-time meal (Leftovers, id 'once-...', its old group deleted) is not reported as
'needs a replacement' and does not block Start next week. Uses her backup (argv[1], backup_17).
Run: python3 -m http.server 8765 (repo root), then python3 tests/once_meal_next_week_choice_browser.py <backup.json>"""
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
        r = await pg.evaluate("""()=>{const plan=mealPlans.find(p=>p.id===activePlanId);const once=Object.values(plan.pendingNextWeekV1?.choices||{}).some(c=>String(c.mealId).startsWith('once-'));
          rotationWeekOffset=1;renderList();const warn=[...document.querySelectorAll('.recipe-bulk-error')].map(x=>x.textContent);
          let err='';try{advanceMealPlanWeek(null,false,false,null,null,true)}catch(e){err=e.message}
          return {once,problem:sequenceProblem(plan),warn,err}}""")
        print(r)
        assert r['once'] and r['problem'] == '' and not any('needs a replacement' in w for w in r['warn']) and 'replacement' not in r['err'], r
        assert not errs, errs
        print('PASS')
asyncio.run(main())
