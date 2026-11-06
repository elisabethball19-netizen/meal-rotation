"""Stage 2 UI, scheduling and guarded-creation regressions. Disposable data only."""
import copy
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
import phase2_stage1_corrections_browser as prior
stage=prior.stage

stage.f.HOOK += '''window.stage2Test={
 groups:id=>{openMasterCategories();const meal=meals.find(m=>m.id===id);openTopMealActionMenu(null,meal.cat,meal)},
 plans:()=>mealPlans,
 active:()=>activePlanId,
 tabMenu:id=>{activeTabMenuId=id;showTop=true;groceryTabActive=false;allMealsActive=false;renderList()},
 hideTabs:()=>{showMealPlanTabs=false;localStorage.setItem('mealRotationShowPlanTabsV1','false');render()},
 addHidden:()=>openAddMealTabDialog(),
 direct:(id,target)=>scheduleMealFromGroups(id,target),
 create:target=>openCreateScheduledRecipe(target),
 paired:()=>{meals.find(m=>m.id===1).linkedMealIds=[];meals.find(m=>m.id===3).linkedMealIds=[];meals.find(m=>m.id===3).serveWith=['Another Side'];const p=mealPlans.find(p=>p.id===activePlanId);weekdayMealOverrides['Tuesday::Sides']='11';p.cycleSlotChoices['Tuesday::Sides']={mealId:'11',parentId:''};p.cycleRetainedSlots['Tuesday::Sides']='11';p.dependentSideState={};weekTest.pair();persist();renderList()},
 single:()=>{mealPlans=mealPlans.filter(p=>p.id==='original');saveActiveMealPlan();renderList()},
 extraIngredients:()=>{meals.find(m=>m.id===3).linkedMealIds=[12];meals.find(m=>m.id===3).favorite=true;persist();renderList()}
};'''

def setup(browser,name,width=360,**kw):
 c,p,errors,prefix=stage.setup(browser,name,width,**kw);p.set_default_timeout(8000);return c,p,errors,prefix
def plans(p):return p.evaluate('stage2Test.plans()')
def sources(p):return prior.sources(p)
def clean(errors):assert not errors,errors

def tab_creation(browser,name,width):
 c,p,errors,prefix=setup(browser,name,width);before=stage.definitions(p);original=copy.deepcopy(plans(p))
 p.evaluate('weekTest.my()');p.get_by_role('button',name='Add meal tab',exact=True).click();d=p.get_by_role('dialog',name='Add Meal Tab',exact=True);d.get_by_role('textbox',name='Meal tab name',exact=True).fill('Cancelled');d.get_by_role('button',name='Cancel',exact=True).click();assert plans(p)==original
 for label in ['Breakfast','Lunch']:
  p.get_by_role('button',name='Add meal tab',exact=True).click();d=p.get_by_role('dialog',name='Add Meal Tab',exact=True);d.get_by_role('button',name=label,exact=True).click();d.get_by_role('button',name='Add tab',exact=True).click()
  assert plans(p)[-1]['name']==label and not plans(p)[-1]['weekdayCategories']
 assert stage.definitions(p)==before and plans(p)[0]['weekdayCategories']==original[0]['weekdayCategories']
 p.reload();assert [x['name'] for x in plans(p)]==['Dinner','Breakfast','Lunch']
 p.get_by_role('button',name='Add meal tab',exact=True).click();d=p.get_by_role('dialog',name='Add Meal Tab',exact=True);d.get_by_role('textbox',name='Meal tab name').fill('Snacks');d.get_by_role('button',name='Add tab',exact=True).click()
 snack=plans(p)[-1]['id'];p.evaluate('stage2Test.tabMenu',snack);p.locator('.meal-plan-menu').get_by_role('button',name='Move tab left',exact=True).click();assert plans(p)[-2]['id']==snack
 p.locator('.meal-plan-menu').get_by_role('button',name='Rename',exact=True).click();prompt=p.get_by_role('dialog').filter(has_text='Rename meal plan');prompt.get_by_role('textbox').fill('Evening snacks');prompt.get_by_role('button',name='Save',exact=True).click();assert next(x for x in plans(p) if x['id']==snack)['name']=='Evening snacks'
 p.evaluate('stage2Test.tabMenu',snack);p.locator('.meal-plan-menu').get_by_role('button',name='Delete',exact=True).click();p.get_by_role('dialog').filter(has_text='Recipes will be kept').get_by_role('button',name='Yes',exact=True).click();assert all(x['id']!=snack for x in plans(p)) and stage.definitions(p)==before
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();assert [x['name'] for x in plans(p)]==['Dinner','Breakfast','Lunch']
 # Hidden-tab installations still have an explicit Add action in Settings.
 p.evaluate('stage2Test.hideTabs()');assert not p.get_by_role('button',name='Add meal tab',exact=True).count();p.get_by_role('button',name='Settings and backups',exact=True).click();p.locator('details[data-settings-group=display]').evaluate('(e)=>e.open=true');p.get_by_role('button',name='Add Meal Tab',exact=True).click()
 d=p.get_by_role('dialog',name='Add Meal Tab',exact=True);d.get_by_role('textbox',name='Meal tab name').fill('Tea');d.get_by_role('button',name='Add tab',exact=True).click();assert plans(p)[-1]['name']=='Tea';assert p.get_by_role('tab',name='Tea',exact=True).is_visible()
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 p.evaluate('stage2Test.tabMenu("original")');p.locator('.meal-plan-menu').get_by_role('button',name='Delete',exact=True).click();p.get_by_role('dialog').filter(has_text='Recipes will be kept').get_by_role('button',name='Yes',exact=True).click();p.reload();assert all(x['name']!='Dinner' for x in plans(p))
 p.get_by_role('button',name='Add meal tab',exact=True).click();d=p.get_by_role('dialog',name='Add Meal Tab',exact=True);d.get_by_role('button',name='Dinner',exact=True).click();d.get_by_role('button',name='Add tab',exact=True).click();assert plans(p)[-1]['name']=='Dinner' and not plans(p)[-1]['weekdayCategories']
 clean(errors);c.close();print('PASS',name,width,'add deleted/default/custom tabs, Cancel, rename/reorder/delete, hidden settings entry, reload/backup and isolation',flush=True)

def direct_schedule(browser,name,width):
 c,p,errors,_=setup(browser,name,width,multi=True);p.evaluate('stage2Test.extraIngredients()');before=stage.definitions(p);old=stage.rows(p);assign={x['id']:copy.deepcopy(x['weekdayCategories']) for x in plans(p)};selections=p.evaluate('correctionTest.edits()');old_active=p.evaluate('stage2Test.active()')
 p.evaluate('stage2Test.groups(3)');p.get_by_role('dialog',name='Meal options',exact=True).get_by_role('button',name='Schedule Meal',exact=True).click();d=p.get_by_role('dialog',name='Schedule Meal',exact=True)
 d.get_by_role('combobox',name='Meal tab').select_option('lunch');d.get_by_role('combobox',name='Weekday').select_option('Thursday');d.get_by_role('button',name='Schedule meal',exact=True).click()
 assert any(e['planId']=='lunch' and e['day']=='Thursday' and e['id']==3 for e in stage.rows(p));assert stage.definitions(p)==before
 assert p.evaluate('stage2Test.active()')==old_active and {x['id']:x['weekdayCategories'] for x in plans(p)}==assign
 assert all(e in stage.rows(p) for e in old if e['planId']!='lunch' or e['day']!='Thursday')
 assert any(s['planId']=='lunch' and s['day']=='Thursday' and s['mealId']==3 for s in sources(p).values())
 assert p.evaluate('correctionTest.edits()')==selections
 p.locator('#undo').click();assert stage.rows(p)==old and stage.definitions(p)==before
 p.evaluate('target=>stage2Test.direct(3,target)',{'planId':'lunch','day':'Sunday','category':None,'occasional':True});assert any(e['planId']=='lunch' and e['day']=='Sunday' and e['id']==3 for e in stage.rows(p))
 assert not next(x for x in plans(p) if x['id']=='lunch')['weekdayCategories'].get('Sunday')
 p.reload();backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();assert stage.definitions(p)==before;assert any(e['planId']=='lunch' and e['day']=='Sunday' and e['id']==3 for e in stage.rows(p))
 clean(errors);c.close();print('PASS',name,width,'Meal Groups scheduling to other tab/assigned or unconfigured day, groups/queues/selection preserved, Undo and backup',flush=True)

def create_dialog(p,target):
 p.evaluate('stage2Test.create',target);return p.get_by_role('dialog',name='Create New Recipe',exact=True)
def fill_recipe(d,name='New lentil supper',rotation=False,groceries=True):
 d.get_by_role('textbox',name='Recipe name',exact=True).fill(name);d.get_by_role('combobox',name='Recipe group',exact=True).select_option('Soup' if d.get_by_role('combobox',name='Recipe group').locator('option[value="Soup"]').count() else 'Sauces');d.get_by_role('textbox',name='Ingredients',exact=True).fill('2 cups rice\n3 apples');d.get_by_role('textbox',name='Instructions',exact=True).fill('Simmer for 15 minutes.');d.get_by_role('textbox',name='Recipe notes',exact=True).fill('Keep my recipe notes');d.get_by_role('textbox',name='Recipe source link',exact=True).fill('https://recipes.test/lentils')
 d.get_by_role('checkbox',name='Add to rotation',exact=True).set_checked(rotation);d.get_by_role('checkbox',name='Include these ingredients in groceries',exact=True).set_checked(groceries)

def create_recipe(browser,name,width):
 c,p,errors,_=setup(browser,name,width,multi=True);target={'planId':'original','day':'Tuesday','category':'Rice','occasional':False};p.evaluate('weekTest.once();weekTest.check();weekTest.my()');before=stage.definitions(p);old=stage.rows(p);checks=prior.progress(p)
 p.evaluate('weekTest.chooser()');p.get_by_role('dialog',name="Choose Tuesday's meal",exact=True).get_by_role('button',name='Create New Recipe',exact=True).click();d=p.get_by_role('dialog',name='Create New Recipe',exact=True);fill_recipe(d);d.get_by_role('button',name='Cancel',exact=True).click();assert stage.rows(p)==old and stage.definitions(p)==before and prior.progress(p)==checks
 d=create_dialog(p,target);fill_recipe(d);d.get_by_role('button',name='Save recipe and schedule',exact=True).click();assert not d.count()
 created=next(m for m in stage.state(p)['meals'] if m['name']=='New lentil supper');assert created['cat']=='Sauces' and created['rotation'] is False and created['ingredients']==['2 cups rice','3 apples'] and created['notes']=='Keep my recipe notes'
 assert any(e['planId']=='original' and e['day']=='Tuesday' and e['id']==created['id'] for e in stage.rows(p))
 assert len([s for s in sources(p).values() if s['mealId']==created['id']])==2
 p.locator('#undo').click();assert stage.rows(p)==old and prior.progress(p)==checks;assert any(m['id']==created['id'] for m in stage.state(p)['meals']),'Scheduling Undo keeps the saved reusable recipe'
 p.reload();assert any(m['id']==created['id'] for m in stage.state(p)['meals'])
 target={'planId':'original','day':'Sunday','category':None,'occasional':True};d=create_dialog(p,target);fill_recipe(d,'Sunday reusable idea',groceries=False);d.get_by_role('button',name='Save recipe and schedule',exact=True).click();record=next(m for m in stage.state(p)['meals'] if m['name']=='Sunday reusable idea');assert any(e['day']=='Sunday' and e['id']==record['id'] for e in stage.rows(p));assert not stage.plan(p)['weekdayCategories'].get('Sunday');assert not any(s['mealId']==record['id'] for s in sources(p).values())
 backup=p.evaluate('weekTest.storage()');p.evaluate('weekTest.restore',backup);p.reload();assert any(e['day']=='Sunday' and e['id']==record['id'] for e in stage.rows(p));clean(errors);c.close();print('PASS',name,width,'Create New Recipe real entry, Cancel unchanged, reusable saved recipe plus schedule, explicit groceries, Ideas, Undo, unconfigured day and backup',flush=True)

def dependencies_and_transitions(browser,name):
 c,p,errors,_=setup(browser,name);p.evaluate('stage2Test.paired();weekTest.check()');definitions=stage.definitions(p);scores=copy.deepcopy(stage.plan(p).get('favoriteRotationScores'))
 p.evaluate('target=>stage2Test.direct(3,target)',{'planId':'original','day':'Tuesday','category':'Rice','occasional':False})
 assert stage.definitions(p)==definitions and stage.plan(p).get('favoriteRotationScores')==scores
 assert any(e['id']==13 and e['cat']=='Sides' for e in stage.rows(p)),stage.rows(p)
 p.reload();p.evaluate('weekTest.rotate(["Tuesday::Rice"])');assert stage.definitions(p)==definitions and stage.plan(p).get('favoriteRotationScores')==scores
 p.evaluate('weekTest.back()');assert stage.definitions(p)==definitions;assert any(e['id']==3 and e['cat']=='Rice' for e in stage.rows(p));clean(errors);c.close()
 for kind in ['once','empty']:
  c,p,errors,_=setup(browser,name,multi=True);p.evaluate('weekTest.check();weekTest.'+('once()' if kind=='once' else 'empty()'));old=copy.deepcopy(stage.plan(p)['weekSchedule']);before=prior.progress(p)
  p.evaluate('target=>stage2Test.direct(3,target)',{'planId':'original','day':'Tuesday','category':'Rice','occasional':False});p.locator('#undo').click();assert stage.plan(p)['weekSchedule']==old and prior.progress(p)==before
  if kind=='empty':p.evaluate('weekTest.resume()');assert all(s['checked'] for s in sources(p).values() if s['mealId'] in [1,20])
  clean(errors);c.close()
 print('PASS',name,'paired side scheduling/expiry preserves queues and Favorites; direct scheduling Undo retains one-time/empty shopping progress',flush=True)

def creation_failures(browser,name):
 c,p,errors,prefix=setup(browser,name,multi=True);p.evaluate('weekTest.empty();weekTest.my()');target={'planId':'original','day':'Tuesday','category':'Rice','occasional':False};before=stage.rows(p);definitions=stage.definitions(p);native=p.evaluate('prefix=>Object.fromEntries(Object.entries(localStorage).filter(([key])=>key.startsWith(prefix+"mealRotation")&&(!prefix?!key.startsWith("mealRotationTestSandboxV1:"):true)))',prefix)
 d=create_dialog(p,target);fill_recipe(d,'Draft before failure')
 p.evaluate('''()=>{window.stage2NativeSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationDataV1'))throw Error('synthetic quota');return stage2NativeSet.call(this,k,v)}}''')
 d.get_by_role('button',name='Save recipe and schedule',exact=True).click();expect(d.get_by_role('status')).to_contain_text('draft is still open');assert stage.definitions(p)==definitions and stage.rows(p)==before
 assert p.locator('#mealSaveWarning').is_visible();assert p.evaluate('prefix=>Object.fromEntries(Object.entries(localStorage).filter(([key])=>key.startsWith(prefix+"mealRotation")&&!key.endsWith("mealRotationRecoveryJournalV1")&&(!prefix?!key.startsWith("mealRotationTestSandboxV1:"):true)))',prefix)==native
 d.get_by_role('textbox',name='Recipe name',exact=True).fill('Latest edited retry draft')
 with p.expect_download() as download:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 assert 'Latest edited retry draft' in Path(download.value.path()).read_text()
 p.evaluate('()=>{Storage.prototype.setItem=stage2NativeSet}');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('!document.querySelector("[data-scheduled-recipe-draft]")')
 assert not p.locator('#mealSaveWarning').count();created=next(m for m in stage.state(p)['meals'] if m['name']=='Latest edited retry draft');assert any(e['id']==created['id'] and e['cat']=='Rice' for e in stage.rows(p));p.reload();assert any(m['id']==created['id'] for m in stage.state(p)['meals']);clean(errors);c.close()
 c,p,errors,_=setup(browser,name);before=stage.definitions(p);old=stage.rows(p);d=create_dialog(p,target);fill_recipe(d)
 p.evaluate('''()=>{window.stage2NativeSet=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationDataV1'))throw Error('synthetic quota');return stage2NativeSet.call(this,k,v)}}''');d.get_by_role('button',name='Save recipe and schedule',exact=True).click();p.evaluate('()=>{Storage.prototype.setItem=stage2NativeSet}');d.get_by_role('button',name='Cancel',exact=True).click();assert stage.definitions(p)==before and stage.rows(p)==old and not p.locator('#mealSaveWarning').count();clean(errors);c.close()
 print('PASS',name,'atomic creation failure rolls back schedule/library, exports latest draft, retries latest edits, persists after reload, and cancels cleanly',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [320,360]:tab_creation(browser,name,width);direct_schedule(browser,name,width);create_recipe(browser,name,width)
   dependencies_and_transitions(browser,name);creation_failures(browser,name)
  browser.close()
