"""Promotion and protected manual slots, with synthetic data in isolated storage."""
import copy,json
from pathlib import Path
from playwright.sync_api import sync_playwright
from scheduled_linked_slots_browser import HOOK,meal,rows,state,compose,context_key,definitions
ROOT=Path(__file__).resolve().parents[1]
EXTRA='''window.promotionTest={
 groups:()=>{masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));showTop=false;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(true);renderList()},
 my:()=>{showTop=true;allMealsActive=false;groceryTabActive=false;setMasterCategoriesView(false);renderList()},
 order:cat=>meals.filter(m=>m.cat===cat&&m.rotation).map(m=>m.id),
 sources:()=>getGroceryContributions(true).map(s=>({...s,checked:grocerySourceChecked(s)})),
 check:()=>{for(const s of getGroceryContributions(true)){checkedIngredients.add(s.baseKey);groceryOccurrenceChecks.checks[s.id]=JSON.parse(s.id)[2]!==1}saveGroceryOccurrenceChecks();localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))},
 full:()=>moveDisplayedMealsToBottom(),plan:id=>loadMealPlan(id),start:day=>{startWeekday=day;localStorage.setItem('mealRotationStartWeekdayV1',day);renderList()},
 manual:(day,cat,id,from=null)=>applyManualWeekdayMeal(day,cat,meals.find(m=>m.id===id),from?getDisplayedWeekdayMeals().find(x=>x.day===from&&String(x.meal.id)===String(id)):null),
 chooser:(day,cat)=>{const current=getDisplayedWeekdayMeals().find(x=>x.day===day&&x.cat===cat);openWeekdayMealChooser(day,cat,current?.meal)},
 promote:id=>promoteMealToRotation(meals.find(m=>m.id===id)),swipe:id=>openMealSwipeMenu(meals.find(m=>m.id===id)),editor:id=>openEditor(id),
 move:(id,dir,single)=>moveMasterCategoryMeal(meals.find(m=>m.id===id),dir,single),
 groceries:()=>[...getMasterGroceryItems()].map(([key,item])=>({key,line:item.line,quantity:item.quantity,checked:groceryItemChecked(key,item)})),
 validate:()=>{const storage=slotBackup.capture();slotBackup.normalize({version:2,...JSON.parse(storage.mealRotationDataV1),storage})}
};'''
def setup(browser,filename,width,mode='multiple',tabs=True):
 lib=[meal(1,'Pernil','Weekend'),meal(2,'Spaghetti','Weekend'),meal(3,'Lentils','Weekend'),meal(4,'Soup','Weekend'),meal(5,'Mississippi Pot Roast','Weekend'),meal(6,'New Roast','Weekend'),meal(10,'Wednesday main','Mains'),meal(11,'Next main','Mains'),meal(12,'Third main','Mains'),meal(20,'Current side','Sides'),meal(21,'Linked replacement side','Sides'),meal(22,'Next side','Sides')]
 for m in lib:m['ingredients']=['1 cup rice','1 cup rice','Salt to taste'];m['ingredientStepLinks']=[]
 lib[4]['rotation']=False;lib[5]['rotation']=False
 assigns={'Saturday':['Weekend'],'Sunday':['Weekend'],'Wednesday':['Mains']}
 overrides={'Saturday::Weekend':'1','Sunday::Weekend':'2','Wednesday::Mains':'10'}
 choices={k:{'mealId':v,'parentId':'','blockedParents':[]} for k,v in overrides.items()}
 if mode=='single':assigns.pop('Sunday');overrides.pop('Sunday::Weekend');choices.pop('Sunday::Weekend')
 if mode in ['first-manual','all-manual','legacy-manual']:
  overrides['Saturday::Weekend']='3';choices['Saturday::Weekend']={'mealId':'3','parentId':'','substitution':True,'retain':True,'blockedParents':[]}
 if mode=='all-manual':choices['Sunday::Weekend'].update(substitution=True,retain=True)
 if mode in ['cross-group','already-scheduled','linked-protected']:
  overrides['Wednesday::Mains']='5' if mode=='already-scheduled' else '3';choices['Wednesday::Mains']={'mealId':overrides['Wednesday::Mains'],'parentId':'','substitution':True,'retain':True,'blockedParents':[]}
 if mode in ['linked','linked-protected','linked-slot']:
  assigns['Saturday']=['Weekend','Sides'];overrides['Saturday::Sides']='20';choices['Saturday::Sides']={'mealId':'20','parentId':'','blockedParents':[]}
  lib[4]['linkedMealIds']=[21]
  if mode=='linked-protected':choices['Saturday::Sides'].update(substitution=True,retain=True)
  if mode=='linked-slot':lib[0]['linkedMealIds']=[20];lib[4]['cat']='Sides';lib[4]['linkedMealIds']=[]
 if mode=='filtered':
  for m in lib:m['labels']=['Pork'] if m['id']==1 else []
  assigns['Saturday']=['Weekend'];filters={'Saturday::Weekend':['Pork']}
 else:filters={}
 pins=dict(overrides)
 if mode=='legacy-manual':pins.pop('Saturday::Weekend');choices.pop('Saturday::Weekend')
 if mode=='no-days':assigns={'Wednesday':['Mains']};overrides={'Wednesday::Mains':'10'};pins=dict(overrides);choices={}
 dinner=dict(id='original',name='Dinner',weekdayCategories=assigns,weekdayMealOverrides=overrides,cycleRetainedSlots=pins,cycleSlotChoices=choices,weekdayRecipeFilters=filters,pinnedCats=[])
 lunch=dict(id='lunch',name='Lunch',weekdayCategories={'Friday':['Weekend']},weekdayMealOverrides={'Friday::Weekend':'4'},cycleRetainedSlots={'Friday::Weekend':'4'},cycleSlotChoices={'Friday::Weekend':{'mealId':'4','parentId':''}},weekdayRecipeFilters={},pinnedCats=[])
 prefix='mealRotationTestSandboxV1:' if filename.startswith('meal-') else ''
 seed={prefix+'mealRotationDataV1':json.dumps({'cats':['Weekend','Mains','Sides'],'active':'Weekend','meals':lib}),prefix+'mealRotationPlansV1':json.dumps({'plans':[dinner,lunch],'activeId':'original'}),prefix+'mealRotationShowPlanTabsV1':str(tabs).lower(),prefix+'mealRotationSelectedIngredientsV1':json.dumps({str(m['id']):m['ingredients'] for m in lib}),prefix+'mealRotationTutorialStageV1':'done',prefix+'mealRotationRecipeViewPrefsV1':json.dumps({'mode':'split','ratio':.4,'keepScreenAwake':False}),prefix+'mealRotationCustomSettingV9':'keep'}
 seed[prefix+'mealRotationWeekdayRecipeFiltersV1']=json.dumps(filters)
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
 src=(ROOT/filename).read_text().replace('function validateBackupCore(d){','window.slotBackup={capture:captureBackupStorage,restore:restoreBackupStorage,normalize:normalizeImportedBackup};function validateBackupCore(d){').replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+(HOOK+EXTRA).replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 ctx=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,accept_downloads=True);p=ctx.new_page();p.set_default_timeout(8000);errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
 p.add_init_script('if(!sessionStorage.seed){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seed="1"}')
 p.route('http://promotion.test/**',lambda r:r.fulfill(status=200,content_type='text/html',body=src) if r.request.url.endswith(filename) else r.fulfill(status=200,body=''));p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 p.goto('http://promotion.test/'+filename);p.evaluate('slotTest.seed()');p.evaluate('promotionTest.check()');return ctx,p,errors,prefix

def sources(p):return {s['id']:s for s in p.evaluate('promotionTest.sources()')}
def pick(p,day,cat='Weekend',plan='original'):return next((r for r in rows(p) if r['planId']==plan and r['day']==day and r['cat']==cat),None)
def group_rows(p,cat='Weekend'):return p.locator('#list .master-category-card[data-category="'+cat+'"] .master-category-meal')
def promote_ui(p,id=5):
 p.evaluate('promotionTest.groups()');p.get_by_role('checkbox',name='Move '+('Mississippi Pot Roast' if id==5 else 'New Roast')+' to rotation',exact=True).tap()
def stable_sources(old,new):
 for id,source in new.items():assert source['checked']==(old[id]['checked'] if id in old else False),(id,source,old.get(id))
def run(browser,filename,width,mode,tabs=True):
 ctx,p,errors,prefix=setup(browser,filename,width,mode,tabs);before=state(p);schedule=compose(p);old=sources(p);saved=p.evaluate('slotTest.storage()');p.evaluate('promotionTest.groups()')
 original_order=p.evaluate("promotionTest.order('Weekend')")
 promote_ui(p);now=state(p);new=sources(p)
 day='Sunday' if mode in ['first-manual','legacy-manual','filtered'] else 'Saturday'
 if mode in ['all-manual','no-days','already-scheduled','linked-slot']:assert compose(p)==schedule,(mode,rows(p),schedule)
 else:assert pick(p,day)['id']==5,(mode,rows(p))
 for r in rows(p):
  if r['planId']!='original' or r['day']!=day or mode in ['all-manual','no-days','already-scheduled','linked-slot']:
   assert any(x==r for x in [dict(planId=x[0],day=x[1],cat=x[2],id=x[3],parent=x[4],slot=r['slot']) for x in schedule]),(mode,r,schedule)
 assert p.get_by_role('dialog').count()==0
 assert p.evaluate("promotionTest.order('Weekend')")==([5]+original_order if mode!='linked-slot' else original_order)
 for m in now['meals']:
  expected=copy.deepcopy(next(x for x in before['meals'] if x['id']==m['id']))
  if m['id']==5:expected['rotation']=True
  assert m==expected,(mode,m,expected)
 for r in rows(p):
  if any(x[0]==r['planId'] and x[1]==r['day'] and x[3]==r['id'] and x[4]==r['parent'] for x in schedule):
   key=context_key(r);assert before['sessions']['occurrences'][key]==now['sessions']['occurrences'][key] and before['scales']['occurrences'][key]==now['scales']['occurrences'][key]
 assert before['prefs']==now['prefs']
 assert [x['weekdayCategories'] for x in before['plans']]==[x['weekdayCategories'] for x in now['plans']]
 assert saved['mealRotationSelectedIngredientsV1']==p.evaluate('slotTest.storage()')['mealRotationSelectedIngredientsV1']
 stable_sources(old,new)
 if mode=='linked':assert pick(p,'Saturday','Sides')['id']==21
 if mode=='linked-protected':assert pick(p,'Saturday','Sides')['id']==20
 if mode=='cross-group':
  ids=group_rows(p).evaluate_all('(es)=>es.map(e=>Number(e.dataset.mealId))');assert ids==([3,4,5,2,1,6] if tabs else [3,5,2,1,4,6]),ids
  lentils=p.locator('#list .master-category-meal[data-meal-id="3"]')
  assert 'WED' in lentils.inner_text() and lentils.evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgb(246, 222, 170)'
  assert p.locator('#list .master-category-meal[data-meal-id="1"]').evaluate('(e)=>getComputedStyle(e).backgroundColor')=='rgba(0, 0, 0, 0)'
  raw=p.evaluate("promotionTest.order('Weekend')");p.evaluate('promotionTest.move(3,-1,true)');assert p.evaluate("promotionTest.order('Weekend')")!=raw and pick(p,'Wednesday','Mains')['id']==3
  p.evaluate('promotionTest.groups()');ids=group_rows(p).evaluate_all('(es)=>es.map(e=>Number(e.dataset.mealId))');assert len(ids)==len(set(ids))
  if filename.startswith('meal-') and width==360:p.screenshot(path='/tmp/promotion-scheduled-first.png')
 after=compose(p);checks={k:s['checked'] for k,s in sources(p).items()};p.reload();assert compose(p)==after and {k:s['checked'] for k,s in sources(p).items()}==checks
 p.evaluate("promotionTest.plan('lunch')");assert pick(p,'Friday',plan='lunch')['id']==4;p.evaluate("promotionTest.plan('original')");assert compose(p)==after
 p.evaluate('promotionTest.validate()')
 if mode in ['multiple','first-manual','all-manual','cross-group','legacy-manual','linked-protected']:
  protected=[r for r in rows(p) if r['planId']=='original' and ((mode in ['first-manual','legacy-manual','all-manual'] and r['day']=='Saturday') or mode=='all-manual' and r['day']=='Sunday' or mode in ['cross-group','linked-protected'] and r['day']=='Wednesday' or mode=='linked-protected' and r['cat']=='Sides')]
  before_cycle=compose(p);old=sources(p);p.evaluate('promotionTest.full()')
  for r in protected:assert not state(p)['plans'][0]['cycleSlotChoices'][r['day']+'::'+r['cat']].get('substitution'),(mode,'manual override survived explicit weekly cycle',r)
  stable_sources(old,sources(p));p.evaluate('slotTest.back()');assert compose(p)==before_cycle
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 assert not errors,errors;ctx.close();print('PASS',filename,width,mode,'tabs',tabs,'promotion/slot protection/display/groceries/cycle/reload',flush=True)

def manual_moves(browser,filename,width):
 ctx,p,errors,prefix=setup(browser,filename,width,'cross-group');old=sources(p);p.evaluate("promotionTest.manual('Saturday','Weekend',3,'Wednesday')")
 moved=sources(p)
 for s in moved.values():
  if s['planId']=='original' and s['day']=='Saturday' and s['mealId']==3:
   prior=next(x for x in old.values() if x['planId']=='original' and x['day']=='Wednesday' and x['mealId']==3 and json.loads(x['id'])[1:]==json.loads(s['id'])[1:]);assert s['checked']==prior['checked']
 assert pick(p,'Wednesday','Mains')['id']!=3
 p.evaluate("promotionTest.manual('Sunday','Weekend',3)");dup=sources(p)
 assert pick(p,'Saturday')['id']==pick(p,'Sunday')['id']==3
 for s in dup.values():
  if s['planId']=='original' and s['day']=='Sunday':assert s['checked'] is False
  elif s['id'] in moved:assert s['checked']==moved[s['id']]['checked']
 p.evaluate('slotTest.cycle(["Wednesday::Mains"])');assert pick(p,'Saturday')['id']==pick(p,'Sunday')['id']==3
 promote_ui(p);assert pick(p,'Saturday')['id']==pick(p,'Sunday')['id']==3
 p.evaluate('promotionTest.my()');p.evaluate('slotTest.open()');d=p.get_by_role('heading',name='Select meals to rotate out').locator('..');cb=d.get_by_role('checkbox',name='Saturday · Weekend — Lentils',exact=True);assert cb.is_checked();d.get_by_role('button',name='Deselect all',exact=True).tap();cb.check();d.get_by_role('button',name='Move selected',exact=True).tap()
 assert pick(p,'Saturday')['id']!=3 and pick(p,'Sunday')['id']==3
 assert not errors,errors;ctx.close();print('PASS',filename,width,'manual move and intentional duplicate: checks/quantities retained, unrelated-cycle protection, explicit selection changes only selected override',flush=True)

def paths(browser,filename,width):
 for path in ['swipe','editor']:
  ctx,p,errors,_=setup(browser,filename,width)
  if path=='swipe':p.evaluate('promotionTest.swipe(5)');p.get_by_role('button',name='Move to rotation',exact=True).tap()
  else:
   p.evaluate('promotionTest.editor(5)');p.locator('#rotation').check();p.locator('#save').tap()
  assert pick(p,'Saturday')['id']==5 and pick(p,'Sunday')['id']==2
  assert p.evaluate("promotionTest.order('Weekend')")[0]==5
  assert not errors,errors;ctx.close();print('PASS',filename,width,path,'promotion shares scheduling logic',flush=True)

def plan_and_week_order(browser,filename):
 for mode in ['lunch','Sunday','legacy-again']:
  ctx,p,errors,_=setup(browser,filename,360,'legacy-manual' if mode=='legacy-again' else 'multiple')
  if mode=='lunch':p.evaluate("promotionTest.plan('lunch')")
  elif mode=='Sunday':p.evaluate("promotionTest.start('Sunday')")
  before=compose(p);old=sources(p);promote_ui(p)
  if mode=='lunch':assert pick(p,'Friday',plan='lunch')['id']==5 and pick(p,'Saturday')['id']==1 and pick(p,'Sunday')['id']==2
  elif mode=='Sunday':assert pick(p,'Sunday')['id']==5 and pick(p,'Saturday')['id']==1
  else:
   p.evaluate('promotionTest.full()');p.evaluate('slotTest.back()');promote_ui(p,6);assert pick(p,'Saturday')['id']==3 and pick(p,'Sunday')['id']==6
   p.evaluate('promotionTest.move(1,-1,true)');assert pick(p,'Saturday')['id']==3
  stable_sources(old,sources(p));assert not errors,errors;ctx.close();print('PASS',filename,mode,'active-plan isolation, displayed week order and repeated legacy protection',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for filename in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:
    for mode in ['single','multiple','first-manual','all-manual','legacy-manual','cross-group','already-scheduled','no-days','filtered','linked','linked-protected','linked-slot']:run(b,filename,width,mode)
    run(b,filename,width,'cross-group',False);manual_moves(b,filename,width);paths(b,filename,width)
   plan_and_week_order(b,filename)
  b.close()
