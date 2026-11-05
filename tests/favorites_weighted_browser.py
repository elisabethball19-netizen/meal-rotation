"""Favorites use the existing selector; deterministic credit state and isolated mobile UI."""
import copy,json
from collections import Counter
from playwright.sync_api import sync_playwright
import promotion_schedule_browser as f
from scheduled_linked_slots_browser import state,compose
f.EXTRA+='''window.favoriteTest={
 flag:id=>toggleRecipeFavorite(meals.find(m=>m.id===id)),
 seed:(count=4)=>{loadMealPlan('original',false);const plan=mealPlans[0];weekdayCategories={Saturday:['Weekend']};weekdayMealOverrides={'Saturday::Weekend':'1'};plan.weekdayCategories=weekdayCategories;plan.weekdayMealOverrides=weekdayMealOverrides;plan.cycleSlotChoices={'Saturday::Weekend':{mealId:'1',parentId:''}};plan.cycleRetainedSlots={'Saturday::Weekend':'1'};delete plan.favoriteRotationScores;mealPlans=[plan];for(const m of meals){delete m.favorite;if(m.cat==='Weekend')m.rotation=m.id<=count}meals.find(m=>m.id===1).favorite=true;persist();renderList()},
 cycles:n=>{const result=[];for(let i=0;i<n;i++){result.push(getDisplayedWeekdayMeals().find(x=>x.cat==='Weekend').meal.id);moveDisplayedMealsToBottom()}return result},
 skip:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.cat==='Weekend');return skipScheduledMeal(x.day,x.cat,x.meal)},
 rows:()=>slotTest.rows(),backup:()=>slotBackup.capture(),restore:b=>{slotBackup.restore(slotBackup.normalize({version:2,...JSON.parse(b.mealRotationDataV1),storage:b}));backupRestoreReloadPending=true},
 viewer:id=>openSavedMealRecipe(meals.find(m=>m.id===id)),weekly:()=>{allMealsActive=true;groceryTabActive=false;showTop=false;renderList()},
 link:()=>{meals.find(m=>m.id===2).linkedMealIds=[20];persist();renderList()},
 clear:()=>{for(const m of meals)delete m.favorite;persist();renderList()},
 baseline:()=>{const plan=mealPlans[0];return cats.every(cat=>JSON.stringify(automaticRecipeCandidates(cat,[],meals,plan).map(m=>m.id))===JSON.stringify(meals.filter(m=>m.rotation&&m.cat===cat).sort((a,b)=>{const x=recipeLastCookedTime(a),y=recipeLastCookedTime(b);return x===null?(y===null?0:-1):y===null?1:x-y}).map(m=>m.id)))}
};'''
def weighted(b,name):
 c,p,errors,_=f.setup(b,name,360,'single',False);p.evaluate('favoriteTest.seed()');before=copy.deepcopy(state(p));sequence=p.evaluate('favoriteTest.cycles(200)');counts=Counter(sequence)
 assert all(a!=b for a,b in zip(sequence,sequence[1:])),sequence
 assert abs(counts[1]-80)<=2 and all(abs(counts[i]-40)<=2 for i in [2,3,4]),counts
 assert {m['id']:m.get('lastCooked') for m in state(p)['meals']}=={m['id']:m.get('lastCooked') for m in before['meals']}
 backup=p.evaluate('favoriteTest.backup()');plans=copy.deepcopy(state(p)['plans']);p.reload();assert state(p)['plans']==plans and next(m for m in state(p)['meals'] if m['id']==1)['favorite']
 p.evaluate('favoriteTest.clear()');assert p.evaluate('favoriteTest.baseline()');p.evaluate('(b)=>favoriteTest.restore(b)',backup);p.reload();assert state(p)['plans']==plans and next(m for m in state(p)['meals'] if m['id']==1)['favorite']
 # A two-recipe pool must alternate; a one-recipe pool keeps the existing fallback.
 p.evaluate('favoriteTest.seed(2)');seq=p.evaluate('favoriteTest.cycles(20)');assert all(a!=b for a,b in zip(seq,seq[1:])) and set(seq)=={1,2}
 p.evaluate('favoriteTest.seed(1)');assert p.evaluate('favoriteTest.cycles(5)')==[1]*5
 p.evaluate('favoriteTest.seed()');seq=[]
 for _ in range(30):seq.append(p.evaluate("favoriteTest.rows().find(x=>x.cat==='Weekend').id"));p.evaluate('favoriteTest.skip()')
 count=Counter(seq);assert count[1]>=10 and all(count[i]>=4 for i in [2,3,4]) and all(a!=b for a,b in zip(seq,seq[1:])),count
 assert not errors,errors
 print('PASS',name,'200 normal cycles',dict(counts),'no repeats/starvation, 30 weighted skips',dict(count),'no cooking events, one/two-recipe fallbacks, reload/backup, no-favorite candidate parity',flush=True);c.close()
def ui(b,name,width):
 c,p,errors,prefix=f.setup(b,name,width,'multiple');before=copy.deepcopy(state(p));schedule=compose(p);sources=f.sources(p)
 p.evaluate('promotionTest.groups()');button=p.get_by_role('button',name='Add to favorites: Pernil',exact=True);button.tap();assert p.get_by_role('button',name='Remove from favorites: Pernil',exact=True).count()==1
 assert compose(p)==schedule and f.sources(p)==sources
 after=state(p);assert [{k:v for k,v in m.items() if k!='favorite'} for m in after['meals']]==before['meals']
 p.evaluate("promotionTest.chooser('Saturday','Weekend')");dialog=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True);dialog.get_by_role('button',name='Favorites only',exact=True).tap();assert dialog.locator('.weekday-meal-choice').count()==1 and 'Pernil' in dialog.locator('.weekday-meal-choice').inner_text();dialog.get_by_role('button',name='Cancel',exact=True).tap()
 p.evaluate('promotionTest.my()');p.get_by_role('button',name='Remove from favorites: Pernil',exact=True).tap();assert compose(p)==schedule
 p.evaluate('favoriteTest.viewer(1)');heart=p.locator('.recipe-title-actions').get_by_role('button',name='Add to favorites: Pernil',exact=True);heart.tap();assert p.get_by_role('button',name='Remove from favorites: Pernil',exact=True).count()>=1
 assert compose(p)==schedule and f.sources(p)==sources
 p.screenshot(path='/tmp/favorites-'+name+'-'+str(width)+'.png');p.get_by_role('button',name='Close recipe',exact=True).tap()
 p.evaluate('favoriteTest.weekly()');assert p.get_by_role('button',name='Remove from favorites: Pernil',exact=True).count()>=1
 p.reload();assert next(m for m in state(p)['meals'] if m['id']==1)['favorite'];assert not errors,errors
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 print('PASS',name,width,'hearts in Groups/Rotation/Viewer/Overview, favorite chooser filter, no schedule/grocery mutation, persistence and separate storage',flush=True);c.close()
def duplicate_choice(b,name,choice):
 c,p,errors,_=f.setup(b,name,320,'multiple');p.evaluate('favoriteTest.flag(2)');p.evaluate('favoriteTest.link()');p.evaluate('promotionTest.check()');original=compose(p);before=f.sources(p)
 p.evaluate("promotionTest.chooser('Saturday','Weekend')");d=p.get_by_role('dialog',name="Choose Saturday's meal",exact=True);d.locator('[data-meal-id="2"]').tap();d.get_by_role('button',name='Save',exact=True).tap();confirm=p.get_by_role('dialog',name='Spaghetti is already planned',exact=True)
 if choice=='cancel':
  confirm.get_by_role('button',name='Close',exact=True).tap();assert compose(p)==original and f.sources(p)==before;d.get_by_role('button',name='Cancel',exact=True).tap()
 else:
  confirm.get_by_role('button',name="Yes — Replace Sunday's meal" if choice=='yes' else 'No — Keep both meals',exact=True).tap();now=compose(p);assert next(x for x in now if x[:3]==('original','Saturday','Weekend'))[3]==2
  assert (next(x for x in now if x[:3]==('original','Sunday','Weekend'))[3]==2)==(choice=='no')
  for id,source in f.sources(p).items():
   if source['planId']=='original' and source['day']=='Saturday':
    if choice=='no':assert not source['checked']
    else:
     old=next(x for x in before.values() if x['planId']=='original' and x['day']=='Sunday' and x['mealId']==source['mealId'] and json.loads(x['id'])[1:]==json.loads(source['id'])[1:]);assert old['checked']==source['checked']
   elif source['planId']=='original' and source['day']=='Sunday' and choice=='yes':assert not source['checked']
   else:assert source['checked']==before[id]['checked']
  assert next(m for m in state(p)['meals'] if m['id']==2)['favorite']
 assert not errors,errors;print('PASS',name,'favorite linked recipe duplicate decision',choice,'preserves status and correct moved/duplicate/retained grocery states',flush=True);c.close()
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   weighted(b,name)
   for choice in ['yes','no','cancel']:duplicate_choice(b,name,choice)
   for width in [320,360]:ui(b,name,width)
  b.close()
