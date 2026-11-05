"""Manual duplicate decisions, occurrence-specific groceries, linked meals and history."""
import json
from playwright.sync_api import sync_playwright
import rotation_no_duplicates_browser as fixture
from scheduled_linked_slots_browser import rows,state,compose,definitions,context_key
fixture.HOOK+='''window.duplicateTest={
 prepare:mode=>{
  const plan=mealPlans.find(p=>p.id===activePlanId);weekdayCategories.Tuesday=weekdayCategories.Saturday;delete weekdayCategories.Saturday;
  for(const obj of [weekdayMealOverrides,plan.cycleRetainedSlots]){obj['Tuesday::Weekend']=obj['Saturday::Weekend'];delete obj['Saturday::Weekend']}
  if(mode==='multi'){weekdayCategories.Friday=['Weekend'];weekdayMealOverrides['Friday::Weekend']='2';plan.cycleRetainedSlots['Friday::Weekend']='2';for(const day of ['Sunday','Friday']){const key=day+'::Weekend';plan.cycleSlotChoices={...(plan.cycleSlotChoices||{}),[key]:{mealId:'2',parentId:'',substitution:true}}}}
  if(mode==='other-plan'){delete weekdayCategories.Sunday;delete weekdayMealOverrides['Sunday::Weekend'];delete plan.cycleRetainedSlots['Sunday::Weekend']}
  if(mode==='linked'||mode==='linked-only'){
   cats.push('Extras');meals.push({id:6,name:'Linked garnish',cat:'Extras',rotation:true,ingredients:['1 cup rice'],instructions:'Stir.'},{id:7,name:'New garnish',cat:'Extras',rotation:true,ingredients:['2 cups rice'],instructions:'Mix.'});
   meals.find(m=>m.id===2).linkedMealIds=[6];meals.find(m=>m.id===3).linkedMealIds=[7];
   if(mode==='linked-only'){meals.find(m=>m.id===2).cat='Extras';meals.find(m=>m.id===3).linkedMealIds=[2];weekdayMealOverrides['Sunday::Weekend']='3';plan.cycleRetainedSlots['Sunday::Weekend']='3'}
  }
  if(mode==='filtered'){weekdayRecipeFilters['Sunday::Weekend']=['Eligible'];for(const m of meals)m.labels=[2,4].includes(m.id)?['Eligible']:[]}
  for(const m of meals)m.ingredients=['1 cup rice','1 cup rice','Salt to taste','1/2 cup beans'];
  const selected=Object.fromEntries(meals.map(m=>[m.id,m.ingredients]));localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selected));
  saveWeekdayCategories();saveWeekdayMealOverrides();saveWeekdayRecipeFilters();persist();renderList();
  for(const s of getGroceryContributions(true)){checkedIngredients.add(s.baseKey);groceryOccurrenceChecks.checks[s.id]=!(s.day==='Sunday'&&JSON.parse(s.id)[2]===1)}saveGroceryOccurrenceChecks();localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));
 },
 open:()=>{const x=getDisplayedWeekdayMeals().find(x=>x.day==='Tuesday'&&x.cat==='Weekend');openWeekdayMealChooser('Tuesday','Weekend',x.meal)},
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 groceries:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,quantity:item.quantity,checked:groceryItemChecked(key,item),sources:item.contributions})),
 history:()=>readPreviousRotation(),setHistory:()=>localStorage.setItem(ROTATION_BACK_KEY,JSON.stringify({...JSON.parse(captureState()),marker:'existing history'})),
 undo:()=>{if(history.length)restoreState(JSON.parse(history.pop()))}
};'''
def sources(p):return {s['id']:s for s in p.evaluate('duplicateTest.sources()')}
def recipe(p,day,cat='Weekend',plan='original'):return next(r for r in rows(p) if r['day']==day and r['cat']==cat and r['planId']==plan)
def pick(p,id=2):
 p.evaluate('duplicateTest.open()');d=p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True)
 d.get_by_role('button',name='Search recipes',exact=True).tap();d.get_by_role('searchbox').fill('Lentils' if id==2 else 'Saturday stew')
 d.locator(f'[data-meal-id="{id}"]').tap();d.get_by_role('button',name='Save',exact=True).tap();return d

def run(browser,filename,width,mode,choice):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,'standard');p.evaluate('duplicateTest.prepare',mode);p.evaluate('slotTest.seed()');p.evaluate('duplicateTest.setHistory()');p.set_default_timeout(8000)
 before=state(p);before_rows=compose(p);before_sources=sources(p);saved=p.evaluate('slotTest.storage()');history=p.evaluate('duplicateTest.history()')
 d=pick(p,1 if choice=='same' else 2)
 if choice in ['same','automatic']:
  assert not p.get_by_role('dialog',name='Lentils is already planned',exact=True).count()
  assert recipe(p,'Tuesday')['id']==(1 if choice=='same' else 2)
  if choice=='same':assert p.evaluate('slotTest.storage()')==saved
 else:
  confirm=p.get_by_role('dialog',name='Lentils is already planned',exact=True);assert confirm.is_visible()
  assert compose(p)==before_rows and p.evaluate('slotTest.storage()')==saved
  yes=confirm.get_by_role('button',name="Yes — Replace Sunday's meal",exact=True)
  if mode=='multi':
   assert confirm.get_by_role('button',name='Yes — Replace selected meal',exact=True).is_disabled()
   opts=confirm.get_by_role('combobox');assert set(opts.locator('option').all_text_contents())=={'Choose an occurrence','Sunday · Weekend','Friday · Weekend'}
   opts.select_option(label='Sunday · Weekend')
  assert confirm.get_by_text("Lentils is scheduled for Sunday. Would you like to replace Sunday's meal?",exact=True).is_visible()
  box=confirm.bounding_box();assert box['x']>=15 and box['x']+box['width']<=width-15 and confirm.evaluate('(e)=>e.scrollWidth<=e.clientWidth')
  if filename.startswith('meal-') and width==360:p.screenshot(path='/tmp/manual-duplicate-'+mode+'-'+choice+'.png')
  if choice=='cancel':
   confirm.get_by_role('button',name='Close',exact=True).tap();assert compose(p)==before_rows and p.evaluate('slotTest.storage()')==saved
   d.get_by_role('searchbox').fill('');assert d.locator('[data-meal-id="1"]').get_attribute('aria-pressed')=='true';d.get_by_role('button',name='Cancel',exact=True).tap()
  else:
   (yes if choice=='yes' else confirm.get_by_role('button',name='No — Keep both meals',exact=True)).tap()
   assert recipe(p,'Tuesday')['id']==2
   assert recipe(p,'Sunday')['id']!=2 if choice=='yes' else recipe(p,'Sunday')['id']==2
   # Legacy filter data is preserved but inactive; it must not constrain scheduling.
   if choice=='yes' and mode=='filtered':assert recipe(p,'Sunday')['id']==1
   # The queue-preservation policy leaves the displaced first recipe available.
   # The untouched Phase 1 baseline also selects 1; the former 3 assertion was stale.
   if choice=='yes' and mode in ['standard','linked']:assert recipe(p,'Sunday')['id']==1
   after=sources(p)
   for id,source in after.items():
    if source['planId']!='original' or source['day'] not in ['Tuesday','Sunday']:
     assert id in before_sources and source['checked']==before_sources[id]['checked'] and source['line']==before_sources[id]['line'],('retained',source)
    elif source['day']=='Tuesday':
     if choice=='no':assert source['checked'] is False,('new inherited check',source)
     else:
      old=next(s for s in before_sources.values() if s['planId']=='original' and s['day']=='Sunday' and s['mealId']==source['mealId'] and json.loads(s['id'])[1:]==json.loads(source['id'])[1:])
      assert source['checked']==old['checked'],('move lost check',old,source)
    elif choice=='no':assert source['checked']==before_sources[id]['checked'],('original changed',source)
    else:assert source['checked'] is False,('replacement checked',source)
   assert len(after)==4*len(rows(p))
   assert len([s for s in after.values() if s['planId']=='original' and s['day']=='Tuesday' and s['mealId']==2])==4
   # Duplicate ingredient lines and mixed states use quantity splitting without losing totals.
   gs=p.evaluate('duplicateTest.groceries()');rice=[g for g in gs if g['quantity'] and g['quantity']['name']=='rice']
   assert len(rice)==2 and {g['checked'] for g in rice}=={True,False}
   assert abs(sum(g['quantity']['lo'] for g in rice)-sum(s['quantity']['lo'] for s in after.values() if s['quantity'] and s['quantity']['name']=='rice'))<1e-8
   if mode=='linked':
    assert recipe(p,'Tuesday','Extras')['id']==6
    if choice=='yes':assert not any(r['day']=='Sunday' and r['cat']=='Extras' and r['planId']=='original' for r in rows(p))
    else:assert recipe(p,'Sunday','Extras')['id']==6
   after_state=state(p)
   assert [x['weekdayCategories'] for x in before['plans']]==[x['weekdayCategories'] for x in after_state['plans']]
   assert before['prefs']==after_state['prefs']
   assert sorted(before['meals'],key=lambda m:m['id'])==sorted(after_state['meals'],key=lambda m:m['id'])
   for r in rows(p):
    if r['planId']=='lunch' or r['day']=='Friday':
     key=context_key(r);assert before['sessions']['occurrences'][key]==after_state['sessions']['occurrences'][key] and before['scales']['occurrences'][key]==after_state['scales']['occurrences'][key]
   if choice=='no':
    old_sunday=recipe(p,'Sunday');key=context_key(old_sunday)
    assert before['sessions']['occurrences'][key]==after_state['sessions']['occurrences'][key] and before['scales']['occurrences'][key]==after_state['scales']['occurrences'][key]
    assert p.evaluate('duplicateTest.history()')==history
    schedule=compose(p);checks={k:s['checked'] for k,s in after.items()};p.reload();assert compose(p)==schedule and {k:s['checked'] for k,s in sources(p).items()}==checks
   else:
    p.evaluate('slotTest.back()');assert compose(p)==before_rows
    restored=sources(p);assert {k:s['checked'] for k,s in restored.items()}=={k:s['checked'] for k,s in before_sources.items()}
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors
 print('PASS',filename,width,mode,choice,'prompt/cancel, occurrence groceries/shared quantities, links, retained progress/settings/assignments/history',flush=True);ctx.close()
def choose_friday(browser,filename,width):
 ctx,p,errors,prefix=fixture.setup(browser,filename,width,'standard');p.evaluate('duplicateTest.prepare','multi');p.evaluate('slotTest.seed()');original=compose(p);old=sources(p)
 pick(p);d=p.get_by_role('dialog',name='Lentils is already planned',exact=True);d.get_by_role('combobox').select_option(label='Friday · Weekend');d.get_by_role('button',name="Yes — Replace Friday's meal",exact=True).tap()
 assert recipe(p,'Sunday')['id']==2 and recipe(p,'Friday')['id']!=2 and recipe(p,'Tuesday')['id']==2
 for id,s in sources(p).items():
  if s['planId']=='original' and s['day']=='Sunday':assert s['checked']==old[id]['checked']
  if s['planId']=='original' and s['day']=='Tuesday':assert s['checked'] is True
  if s['planId']=='original' and s['day']=='Friday':assert s['checked'] is False
 p.evaluate('slotTest.back()');assert compose(p)==original and not errors,errors
 print('PASS',filename,width,'explicit Friday choice leaves Sunday intact; moved checks, unchecked replacement and Cycle Back',flush=True);ctx.close()

def undo_and_partial(browser,filename):
 for action in ['undo','partial']:
  ctx,p,errors,_=fixture.setup(browser,filename,360,'standard');p.evaluate('duplicateTest.prepare','linked');p.evaluate('slotTest.seed()');before=compose(p);old=sources(p)
  pick(p);p.get_by_role('dialog',name='Lentils is already planned',exact=True).get_by_role('button',name="Yes — Replace Sunday's meal",exact=True).tap();moved=sources(p)
  if action=='undo':
   p.evaluate('duplicateTest.undo()');assert compose(p)==before
   assert {k:s['checked'] for k,s in sources(p).items()}=={k:s['checked'] for k,s in old.items()}
  else:
   p.evaluate('slotTest.partial(["original||Sunday::Weekend"])');assert recipe(p,'Sunday')['id']==2 and recipe(p,'Tuesday')['id']==2
   for id,s in sources(p).items():
    if s['planId']=='original' and s['day']=='Tuesday':assert s['checked']==moved[id]['checked']
    if s['planId']=='original' and s['day']=='Sunday':assert s['checked']==old[id]['checked']
  assert not errors,errors;ctx.close();print('PASS',filename,360,action,'restores intended slots and grocery source checks',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for mode in ['standard','linked','multi']:
     for choice in ['yes','no','cancel']:run(b,filename,width,mode,choice)
    run(b,filename,width,'filtered','yes')
    run(b,filename,width,'standard','same')
    for mode in ['other-plan','linked-only']:run(b,filename,width,mode,'automatic')
    choose_friday(b,filename,width)
   undo_and_partial(b,filename)
  b.close()

