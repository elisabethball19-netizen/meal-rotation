"""2026-11-24: cooking progress is kept PER recipe version. Check steps/ingredients on the changed version, switch to the
original and back: the same checks return; the original shows none of them. Run: python3 tests/version_switch_progress_browser.py
"""
from playwright.sync_api import sync_playwright
import start_week_window_browser as s  # registers shared fixture hooks

s.fixture.HOOK += '''window.vsp={run:()=>{
 const m={id:9001,name:'Birria',cat:'',ingredients:['2 lb chuck roast','1 onion'],instructions:'1. Sear the chuck roast.\\n2. Add the onion.',rotation:false,linkGroup:'lg1'};meals.push(m);const m2={...m,id:9002,cat:'Other'};delete m2.aiAltVersion;meals.push(m2);
 m.aiAltVersion={kind:'original',flagsV1:true,ingredients:['3 lb beef','2 bay leaves'],instructions:'1. Brown beef.\\n2. Add bay leaves.',savedAt:new Date().toISOString()};persist();
 const ctx=cookingContext('p1','Mon','c',m2,'');cookingSession(ctx,true);const t=cookingItemTokens(m);const next=JSON.parse(JSON.stringify(cookingSessions));const e=next.occurrences[cookingOccurrenceKey(ctx)];e.steps=[t.steps.find(x=>x.token).token];e.ingredients=[t.ingredients[0].token];writeCookingSessions(next);
 const snap=()=>JSON.stringify(Object.values(cookingSessions.occurrences).filter(x=>['9001','9002'].includes(x.context.mealId)).map(x=>[x.steps,x.ingredients]));
 const before=snap();switchRecipeVersion(m);const mid=snap();switchRecipeVersion(m);const after=snap();
 return {before,mid,after}},
 viewer:()=>{const m=meals.find(x=>x.id===9001);openSavedMealRecipe(m);const v=recipeViewer;const t=cookingItemTokens(m);v.previewProgress={ingredients:[t.ingredients[0].token],steps:[t.steps.find(x=>x.token).token]};const a=JSON.stringify(v.previewProgress);switchRecipeVersion(m);const mid=JSON.stringify(recipeViewer.previewProgress);switchRecipeVersion(m);return {a,mid,b:JSON.stringify(recipeViewer.previewProgress),ctx:!!v.context}},
 ui:()=>{const m=meals.find(x=>x.id===9001);m.aiAltVersion={kind:'original',flagsV1:true,ingredients:['3 lb beef','2 bay leaves'],instructions:'1. Brown beef.\\n2. Add bay leaves.',savedAt:new Date().toISOString()};m.ingredients=['2 lb chuck roast','1 onion'];m.instructions='1. Sear the chuck roast.\\n2. Add the onion.';persist();openSavedMealRecipe(m);const v=recipeViewer;const t=cookingItemTokens(m);v.previewProgress={ingredients:[t.ingredients[0].token],steps:[t.steps.find(x=>x.token).token]};renderRecipeViewer();return {a:JSON.stringify(v.previewProgress),ctx:!!v.context,vm:v.mealId}}};'''


def run(browser, name):
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    r = p.evaluate('vsp.run()')
    assert r['before'] != '[]' and r['mid'] == '[]' and r['after'] == r['before'], r
    v = p.evaluate('vsp.viewer()')
    assert not v['ctx'] and v['a'] == v['b'] and v['mid'] != v['a'], v
    c.close()
    if name != 'index.html':
        print('PASS', name, 'direct switch only (viewer UI path checked on index.html)', flush=True); return
    c, p, errors, prefix = s.fixture.setup(browser, name, navigation_timeout=30000)
    p.evaluate('vsp.run()')
    u = p.evaluate('vsp.ui()')
    p.locator('.recipe-version-link').click(); p.wait_for_timeout(300)
    p.locator('.ai-choice').first.click(); p.wait_for_timeout(500); p.wait_for_function('recipeViewer&&recipeViewer.activeTab')
    mid = p.evaluate('JSON.stringify(recipeViewer.previewProgress)')
    p.locator('.recipe-version-link').click(); p.wait_for_timeout(300)
    p.locator('.ai-choice').first.click(); p.wait_for_timeout(500); p.wait_for_function('recipeViewer&&recipeViewer.activeTab')
    b = p.evaluate('JSON.stringify(recipeViewer.previewProgress)')
    assert b == u['a'], (u, mid, b)
    assert not errors, errors
    c.close()
    print('PASS', name, 'progress kept per version across switch and back', flush=True)


if __name__ == '__main__':
    with sync_playwright() as pw:
        b = pw.chromium.launch(executable_path='/usr/bin/chromium', args=['--no-sandbox'])
        for name in ['index.html', 'meal-rotation-test.html']:
            run(b, name)
        b.close()
