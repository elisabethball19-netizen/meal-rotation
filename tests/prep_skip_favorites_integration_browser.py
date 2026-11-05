"""Cross-feature occurrence, linked-priority, calendar, grocery and history checks."""
import copy,json,tempfile,subprocess
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import favorites_weighted_browser as fav
import make_ahead_reminders_browser as prep
from scheduled_linked_slots_browser import state,compose
f=fav.f
f.EXTRA+='''window.integratedTest={
 seed:()=>{prepTest.seed();for(const id of [1,3]){const m=meals.find(m=>m.id===id);m.makeAheadTasks=[{id:'thaw',description:'Thaw '+m.name,daysBefore:1}]}meals.find(m=>m.id===3).linkedMealIds=[21];meals.find(m=>m.id===1).favorite=true;meals.find(m=>m.id===1).needsTweaking=true;meals.find(m=>m.id===1).needsTweakingNote='Keep my adjusting note';saveActiveMealPlan();persist();renderList()},
 rows:()=>scheduledMakeAheadTasks().map(x=>({id:x.entry.meal.id,day:x.entry.day,due:x.due,complete:x.complete,key:x.key})),
 skip:(day='Saturday',cat='Weekend')=>{const item=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat===cat);return skipScheduledMeal(day,cat,item.meal)},
 undo:()=>restoreState(JSON.parse(history.pop())),
 cycleOne:()=>moveDisplayedMealsToBottom(new Set(['Saturday::Weekend'])),
 backOne:()=>rotateSelectedBack(['original||Saturday::Weekend']),
 cycleAll:()=>moveDisplayedMealsToBottom(null,true,false),
 score:()=>JSON.parse(JSON.stringify(mealPlans[0].favoriteRotationScores||{})),
 sameRecipeTwoDays:()=>{const m=meals.find(m=>m.id===2);applyManualWeekdayMeal('Saturday','Weekend',m);prepTest.seed()},
 viewer:id=>openSavedMealRecipe(meals.find(m=>m.id===id)),
 progress:()=>({sessions:cookingSessions,scales:occurrenceScales})
};'''
def run(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'linked-slot');p.clock.install(time=datetime(2026,11,3,8,tzinfo=timezone.utc));p.evaluate('integratedTest.seed()');p.evaluate('promotionTest.check()');before=copy.deepcopy(state(p));schedule=compose(p);sources=f.sources(p)
 p.evaluate('promotionTest.my()');p.get_by_role('button',name='Make ahead: Pernil',exact=True).tap();dialog=p.get_by_role('dialog',name='Make ahead: Pernil',exact=True);assert '1 day before' in dialog.inner_text() or '2026-11-06' in dialog.inner_text();dialog.get_by_role('checkbox').check();dialog.get_by_role('button',name='Close make ahead',exact=True).tap()
 assert next(x for x in p.evaluate('integratedTest.rows()') if x['id']==1)['complete']
 p.evaluate('integratedTest.skip()');after=state(p);now=compose(p);assert next(x for x in now if x[:3]==('original','Saturday','Weekend'))[3]==3
 assert next(x for x in now if x[:3]==('original','Saturday','Sides'))[3]==21,'New linked side must replace unprotected scheduled side'
 assert not any(x['id']==1 for x in p.evaluate('integratedTest.rows()'))
 assert next(x for x in p.evaluate('integratedTest.rows()') if x['id']==3)['due']=='2026-11-06'
 assert not next(x for x in p.evaluate('integratedTest.rows()') if x['id']==3)['complete']
 assert next(m for m in after['meals'] if m['id']==1)['favorite']
 assert sorted(before['meals'],key=lambda m:m['id'])==sorted(after['meals'],key=lambda m:m['id']);assert [m['id'] for m in before['meals'] if m['cat']=='Weekend']==[m['id'] for m in after['meals'] if m['cat']=='Weekend']
 for id,source in f.sources(p).items():assert source['checked']==(sources[id]['checked'] if id in sources else False)
 for r in schedule:
  if r[0]!='original' or r[1]!='Saturday':assert r in now
 p.evaluate('integratedTest.undo()');assert compose(p)==schedule and f.sources(p)==sources;assert next(x for x in p.evaluate('integratedTest.rows()') if x['id']==1)['complete']
 # A task check for Sunday's Spaghetti must not complete its deliberate Saturday duplicate.
 p.evaluate('integratedTest.sameRecipeTwoDays()');p.evaluate('prepTest.overview()');sun=p.locator('.all-meals-day').filter(has=p.get_by_role('heading',name='Saturday',exact=True));sun.get_by_role('checkbox',name="Marinate pork · for Sunday's Spaghetti",exact=True).check()
 checks=[x for x in p.evaluate('integratedTest.rows()') if x['id']==2];assert any(x['day']=='Sunday' and x['complete'] for x in checks) and all(not x['complete'] for x in checks if x['day']=='Saturday')
 saved=p.evaluate('favoriteTest.backup()');saved_state=copy.deepcopy(state(p));rows=p.evaluate('integratedTest.rows()');p.evaluate('b=>favoriteTest.restore(b)',saved);p.reload();assert state(p)==saved_state and p.evaluate('integratedTest.rows()')==rows
 assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'Skip swaps reminders/linked side, retains other days/tabs/checked quantities, Undo restores completion/scales, duplicate occurrence checks independent, full backup preserves all fields',flush=True);c.close()
def history(b,name):
 c,p,errors,_=f.setup(b,name,360,'single',False);p.evaluate('favoriteTest.seed()');p.evaluate('integratedTest.cycleOne()');first=copy.deepcopy(state(p));score=p.evaluate('integratedTest.score()');assert score
 p.evaluate('integratedTest.cycleOne()');p.evaluate('integratedTest.backOne()');assert p.evaluate('integratedTest.score()')==score
 # Later explicit personal recipe edits survive Cycle Back.
 p.evaluate('integratedTest.cycleOne()');p.evaluate('favoriteTest.flag(2)');p.evaluate("meals") if False else None
 p.evaluate('prepTest.back()');assert next(m for m in state(p)['meals'] if m['id']==2)['favorite']
 assert not errors,errors;print('PASS',name,'partial Cycle Back restores weighted credits; full Cycle Back preserves later favorite edit',flush=True);c.close()
def multi_slot(b,name):
 c,p,errors,_=f.setup(b,name,320,'cross-group');p.evaluate('favoriteTest.flag(1)');p.evaluate('favoriteTest.flag(2)');original=copy.deepcopy(state(p));schedule=compose(p)
 # Explicitly rotating Saturday must keep the out-of-group Wednesday override and Lunch.
 for _ in range(12):
  p.evaluate('integratedTest.cycleOne()');now=compose(p)
  assert all(x in now for x in schedule if x[0]!='original' or x[1]!='Saturday')
 # Whole-week cycling may expire manual selections, retaining the original group assignments.
 for _ in range(12):
  p.evaluate('integratedTest.cycleAll()');now=p.evaluate('favoriteTest.rows()');independent=[x['id'] for x in now if not x['parent']];assert len(independent)==len(set(independent)),now
 assert [x['weekdayCategories'] for x in state(p)['plans']]==[x['weekdayCategories'] for x in original['plans']]
 assert {m['id']:m.get('lastCooked') for m in state(p)['meals']}=={m['id']:m.get('lastCooked') for m in original['meals']}
 assert not errors,errors;print('PASS',name,'weighted multi-slot/cross-tab cycles avoid duplicates, unrelated manual override retained for individual cycles, group assignments and cooked dates unchanged',flush=True);c.close()
def no_favorites_parity(b,name):
 root=f.ROOT
 def series():
  c,p,errors,_=f.setup(b,name,320,'multiple');result=[]
  for _ in range(15):result.append(compose(p));p.evaluate('promotionTest.full()')
  assert not errors,errors;c.close();return result
 current=series()
 with tempfile.TemporaryDirectory() as d:
  path=Path(d);(path/name).write_bytes(subprocess.check_output(['git','show','8177685:'+name]));f.ROOT=path
  try:baseline=series()
  finally:f.ROOT=root
 assert current==baseline
 print('PASS',name,'15 no-favorites whole-week rotations identical to pre-weighting code',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   no_favorites_parity(b,name);history(b,name);multi_slot(b,name)
   for width in [320,360]:run(b,name,width)
  b.close()
