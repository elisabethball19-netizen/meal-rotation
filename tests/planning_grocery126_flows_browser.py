"""Final 126 phone flows: atomic prompts, dated handoff and backup round trip."""
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import planning_grocery126_edges_browser as base
fixture=base.fixture
fixture.HOOK+='''window.flow126={
 groupSchedule:()=>openScheduleMealDialog(meals.find(m=>m.id===103)),
 currentPlan:()=>{const p=JSON.parse(JSON.stringify(mealPlans[0]));delete p.pendingNextWeekV1;return JSON.stringify(p)},
 picker:()=>{const e=getDisplayedWeekdayMeals()[0];openWeekdayMealChooser(e.day,e.cat,e.meal)},
 start:()=>openRotateOptions(),
 nextGrocery:()=>{groceryPeriod='next';localStorage.setItem(GROCERY_PERIOD_KEY,'next');batch122.grocery()},
 selectedNext:()=>{const s=getGroceryContributions(false,'next').find(s=>s.mealId===103);setGroceryItemChecked(s.baseKey,{contributions:[s]},true);saveGroceryOccurrenceChecks();return s.id},
 restored:b=>{recipeBulkBackupAPI.restore(b);backupRestoreReloadPending=true},
 temporaryViewer:()=>openSavedMealRecipe(meals.find(m=>m.id===103),null),temporaryScale:()=>setViewedRecipeScale(1.5,{linked:true}),temporaryLinked:()=>[...recipeViewer.tabCache.values()].filter(t=>t.mealId==='104').every(t=>t.previewScale===1.5),
 noLinkViewer:()=>openSavedMealRecipe(meals.find(m=>m.id===102),null),
 prep:()=>{makeAheadDisplayPrefs.automaticDefrost=true;makeAheadDisplayPrefs.showMakeAheadReminders=true;return scheduledMakeAheadTasks().filter(t=>t.entry.meal.id===103).map(t=>({preview:t.preview,key:t.key,text:t.task.description,due:t.due}))},
 unknown:()=>{for(const c of Object.values(mealPlans[0].pendingNextWeekV1.choices))delete c.provenance;saveActiveMealPlan()},
 invalid:()=>{const p=mealPlans[0];p.alternatingGroupsV1.monday.groups[1]='missing';saveActiveMealPlan()},
 };'''

def check(browser,name):
 c,p,errors,prefix=fixture.setup(browser,name,navigation_timeout=30000)
 p.context.new_cdp_session(p).send('Emulation.setTimezoneOverride',{'timezoneId':'America/Los_Angeles'})
 p.evaluate('batch122.seed();batch126.add()');current=p.evaluate('flow126.currentPlan()');p.evaluate('batch126.select(103)');assert p.evaluate('flow126.currentPlan()')==current
 # Group scheduling uses the same protected future-choice prompt and cancellation.
 p.evaluate('batch126.show();flow126.groupSchedule()');groupDialog=p.get_by_role('dialog',name='Schedule Lemon rice and chicken with a very long name for a family dinner',exact=True);groupDialog.get_by_role('checkbox',name='Monday',exact=True).check();before=p.evaluate('batch126.state()');groupDialog.get_by_role('button',name='Schedule selected days',exact=True).click();prompt=p.locator('.recipe-bulk-dialog').last;assert 'Monday next week' in prompt.inner_text();prompt.get_by_role('button',name='Cancel meal choice',exact=True).click();assert p.evaluate('batch126.state()')==before;groupDialog.get_by_role('button',name='Cancel scheduling',exact=True).click()
 # Explicit manual/unknown future choice prompt appears on Save only; cancellation unchanged.
 p.evaluate('batch126.show();flow126.picker()');picker=p.locator('.weekday-meal-picker');picker.locator('[data-meal-id="103"]').first.click();state=p.evaluate('batch126.state()');picker.get_by_role('button',name='Save',exact=True).click()
 prompt=p.get_by_role('dialog',name='Meal already scheduled',exact=True)
 if not prompt.count():prompt=p.locator('.recipe-bulk-dialog').last
 assert 'Monday next week' in prompt.inner_text();p.screenshot(path='/workspace/work/screenshots/'+name+'-duplicate126.png');prompt.get_by_role('button',name='Cancel meal choice',exact=True).click();assert p.evaluate('batch126.state()')==state
 picker.get_by_role('button',name='Cancel',exact=True).click();p.wait_for_timeout(400)
 p.evaluate('flow126.unknown();batch126.show();flow126.picker()');picker=p.locator('.weekday-meal-picker');picker.locator('[data-meal-id="103"]').first.click();picker.get_by_role('button',name='Save',exact=True).click();prompt=p.locator('.recipe-bulk-dialog').last
 prompt.get_by_role('radio',name='Keep Lemon rice and chicken with a very long name for a family dinner on Monday next week too',exact=True).check();prompt.get_by_role('button',name='Confirm meal choice',exact=True).click();p.wait_for_timeout(400);assert not picker.count();assert p.evaluate('batch126.plans()[0].weekdayMealOverrides["Monday::Meals"]')=='103'
 # Pending occurrence scale/grocery checks/prep survive projection becoming active.
 p.evaluate('batch122.seed();batch126.add();batch126.select(103);batch126.scale(103,2,{},true);batch126.close()');p.wait_for_timeout(200)
 sourceid=p.evaluate('flow126.selectedNext()');before=p.evaluate('flow126.prep()');assert any('2 lb chicken' in t['text'] for t in before)
 p.evaluate('batch126.advance()');sources=p.evaluate('edge126.sources("current")');assert any(s['id']==sourceid and s['checked'] and s['multiplier']==2 for s in sources),sources
 assert any('2 lb chicken' in t['text'] for t in p.evaluate('flow126.prep()'))
 # Complete version-2 storage round trip and legacy missing-scale defaults.
 b=p.evaluate('edge126.backup()');p.evaluate('b=>flow126.restored(b)',b);p.reload();assert p.evaluate('batch126.scales()')
 assert any(s['id']==sourceid and s['checked'] for s in p.evaluate('edge126.sources("current")'))
 # Legacy backup without scaling remains loadable, defaults safely to 1x.
 legacy=p.evaluate('edge126.backup()');legacy.pop('mealRotationOccurrenceScalesV1',None);p.evaluate('b=>flow126.restored(b)',legacy);p.reload();assert p.evaluate('Object.keys(batch126.scales().defaults||{}).length')==0
 # Temporary viewer linked scale writes no schedule or defaults; no-linked popup hides toggle.
 p.evaluate('flow126.temporaryViewer()');state=p.evaluate('batch126.state()');p.evaluate('flow126.temporaryScale()');assert p.evaluate('batch126.state()')==state
 assert p.evaluate('flow126.temporaryLinked()')
 p.evaluate('batch126.close()');p.wait_for_timeout(150);p.evaluate('flow126.noLinkViewer()');p.get_by_role('button',name='Scale Recipe',exact=True).click();assert not p.get_by_role('switch',name='Scale linked recipes too').count()
 p.get_by_role('spinbutton',name='Custom multiplier',exact=True).fill('1.5');p.set_viewport_size({'width':360,'height':420});p.get_by_role('button',name='Apply multiplier',exact=True).scroll_into_view_if_needed();p.screenshot(path='/workspace/work/screenshots/'+name+'-scale-no-links-keyboard126.png');p.get_by_role('button',name='Apply multiplier',exact=True).click();p.evaluate('batch126.close()');p.set_viewport_size({'width':360,'height':800});p.wait_for_timeout(150)
 # Explicit carry conflicts require approval; cancel leaves pending and current untouched.
 p.evaluate('batch122.seed();batch126.add();batch126.select(103);batch126.show();flow126.start()')
 d=p.get_by_role('dialog',name='Start next week',exact=True);d.locator('.start-week-choice input').first.uncheck();state=p.evaluate('batch126.state()');d.get_by_role('button',name='Start next week →',exact=True).click();prompt=p.locator('.recipe-bulk-dialog').last
 assert 'Monday next week' in prompt.inner_text();prompt.get_by_role('button',name='Keep selected side',exact=True).click();assert p.evaluate('batch126.state()')==state
 d.get_by_role('button',name='Close Start next week',exact=True).click();p.wait_for_timeout(200)
 # Invalid sequence visibly blocks advance; no mutation.
 p.evaluate('batch122.seed();batch126.sequence();flow126.invalid();batch126.show()');state=p.evaluate('batch126.state()');p.evaluate('flow126.start()');d=p.get_by_role('dialog',name='Start next week',exact=True);d.get_by_role('button',name='Start next week →',exact=True).click();assert 'needs a replacement' in p.locator('body').inner_text();assert p.evaluate('batch126.state()')==state
 # Date-boundary Today filtering uses real local date; future-only/completed don't keep card alive.
 for utc in ['2026-11-16T07:59:00Z','2026-11-16T08:01:00Z','2026-11-17T07:59:00Z','2026-11-17T08:01:00Z']:
  p.clock.set_fixed_time(datetime.fromisoformat(utc.replace('Z','+00:00')));p.evaluate('edge126.onlyFuture()');assert not p.locator('#todaysTodo').count()
 assert not errors,errors
 c.close();print('PASS',name,'126 exact current-plan preservation, protected prompt cancel/keep, next grocery/scale/prep transfer, storage roundtrip, carry conflict cancel, invalid group, boundary due filter',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:check(b,name)
  b.close()
