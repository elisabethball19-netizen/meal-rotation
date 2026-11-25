"""2026-11-24: cooking progress is kept PER recipe version. Check steps/ingredients on the changed version, switch to the
original and back: the same checks return; the original shows none of them. Run: python3 tests/version_switch_progress_browser.py
"""
from playwright.sync_api import sync_playwright
import start_week_window_browser as s  # registers shared fixture hooks

s.fixture.HOOK += '''window.vsp={run:()=>{
 const m={id:9001,name:'Birria',cat:'',ingredients:['2 lb chuck roast','1 onion'],instructions:'1. Sear the chuck roast.\\n2. Add the onion.',rotation:false};meals.push(m);
 m.aiAltVersion={kind:'original',flagsV1:true,ingredients:['3 lb beef','2 bay leaves'],instructions:'1. Brown beef.\\n2. Add bay leaves.',savedAt:new Date().toISOString()};persist();
 const ctx=cookingContext('p1','Mon','c',m,'');cookingSession(ctx,true);const t=cookingItemTokens(m);const next=JSON.parse(JSON.stringify(cookingSessions));const e=next.occurrences[cookingOccurrenceKey(ctx)];e.steps=[t.steps.find(x=>x.token).token];e.ingredients=[t.ingredients[0].token];writeCookingSessions(next);
 const snap=()=>JSON.stringify(Object.values(cookingSessions.occurrences).filter(x=>x.context.mealId==='9001').map(x=>[x.steps,x.ingredients]));
 const before=snap();switchRecipeVersion(m);const mid=snap();switchRecipeVersion(m);const after=snap();
 return {before,mid,after}}};'''


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    r = p.evaluate('vsp.run()')
    assert r['before'] != '[]' and r['mid'] == '[]' and r['after'] == r['before'], r
    assert not errors, errors
    c.close()
    print('PASS', name, 'progress kept per version across switch and back', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
