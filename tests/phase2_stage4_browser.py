"""Stage 4 onboarding, terminology, removal semantics and group safety. Synthetic data."""
import copy,json,re
from playwright.sync_api import sync_playwright,expect
import phase2_stage3_browser as s3
s2=s3.s2
stage=s3.stage
stage.f.HOOK += '''window.stage4Test={
 clearPlans:()=>{for(const p of mealPlans){p.weekdayCategories={};p.weekdayMealOverrides={};p.cycleSlotChoices={};p.cycleRetainedSlots={};delete p.weekSchedule;delete p.occasionalMeals;delete p.rotationCalendar;delete p.dependentSideState}weekdayCategories={};weekdayMealOverrides={};saveActiveMealPlan();persist();render()},
 empty:(groups=true)=>{meals=[];id=1;cats=groups?['Rice','Sides']:[];active=cats[0]||'';localStorage.setItem('mealRotationSelectedIngredientsV1','{}');stage4Test.clearPlans();openMasterCategories()},
 groups:()=>openMasterCategories(),setup:()=>openRotationSetup(),full:id=>openEditor(id),
 group:id=>openMasterCategoryEditMenu(id),del:id=>openCategoryDeleteDialog(id),swipe:id=>openMealSwipeMenu(meals.find(m=>m.id===id)),
 tweak:()=>{const m=meals.find(m=>m.id===1);assignRecipeTweaking(m,true,'Needs less salt.');persist();renderList()},
 destination:()=>{createMealGroup('Destination')},
 shared:(category='Sauces')=>{const original=meals.find(m=>m.id===1);original.linkGroup='stage4-family';meals.push({...JSON.parse(JSON.stringify(original)),id:id++,cat:category});persist();renderList()},
 explicitEmpty:()=>{weekdayCategories.Monday=[EMPTY_DAY_ASSIGNMENT];saveWeekdayCategories();renderList()},
 categories:()=>cats,
 legacy:()=>{meals[0].labels=['Legacy label'];recipeLabelCatalog=['Legacy label'];weekdayRecipeFilters={'Tuesday::Rice':'Legacy label'};mealPlans[0].weekdayRecipeFilters=weekdayRecipeFilters;saveRecipeLabelCatalog();saveWeekdayRecipeFilters();persist()},
 occasion:()=>{const plan=mealPlans.find(p=>p.id===activePlanId);plan.occasionalMeals={...(plan.occasionalMeals||{}),Sunday:'2'};persist();weekTest.check();renderList();openWeekdayMealChooser('Sunday',null,meals.find(m=>m.id===2),true)},
 labels:()=>({catalog:recipeLabelCatalog,filters:weekdayRecipeFilters,labels:meals.map(m=>({id:m.id,labels:m.labels||[]}))})
};'''
def setup(b,name,width=320):return s3.setup(b,name,width)
def records(p):return copy.deepcopy(stage.state(p)['meals'])
def storage(p):return p.evaluate('weekTest.storage()')
def clean(errors):assert not errors,errors

def empty_collection(b,name,width,groups):
 c,p,errors,prefix=setup(b,name,width);p.evaluate('stage4Test.empty',groups);before=storage(p);section=p.get_by_role('region',name='Meal Groups',exact=True);assert section.get_by_role('button',name='Import Recipes',exact=True).count()==1 and section.get_by_role('button',name='Add Recipe',exact=True).count()==1;assert not p.locator('.master-expansion-controls,.master-category-card,.master-order-reset').count()
 add=section.get_by_role('button',name='Add Recipe',exact=True);assert add.bounding_box()['height']>=44;add.focus();p.keyboard.press('Enter');d=p.get_by_role('dialog',name='Add Recipe',exact=True);d.get_by_role('button',name='Cancel',exact=True).click();assert storage(p)==before
 add.click();d=p.get_by_role('dialog',name='Add Recipe',exact=True)
 if not groups:d.get_by_role('textbox',name='New group name',exact=True).fill('My recipes')
 d.get_by_role('button',name='Continue',exact=True).click();assert p.locator('#editor .editor').is_visible() and p.locator('#rotation').is_checked();p.locator('#cancel').click();assert records(p)==[];p.get_by_role('button',name='Add Recipe',exact=True).click();p.get_by_role('dialog',name='Add Recipe',exact=True).get_by_role('button',name='Continue',exact=True).click();p.locator('#name').fill('First recipe');p.locator('#save').click();p.wait_for_function('!document.querySelector("#editor .editor")');assert len(records(p))==1 and records(p)[0]['rotation'];assert not p.locator('.empty-meal-groups').count();assert not p.get_by_role('button',name='Import Recipes',exact=True).count();assert p.get_by_role('button',name='Set Up Your Rotation',exact=True).count()==1
 saved=storage(p);p.reload();p.evaluate('stage4Test.groups()');assert records(p)[0]['name']=='First recipe';p.evaluate('weekTest.restore',saved);p.reload();assert records(p)[0]['name']=='First recipe'
 assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 clean(errors);c.close();print('PASS',name,width,'empty groups',groups,'clear actions, no empty clutter, keyboard/Cancel, creation defaults, reload/backup and isolation',flush=True)

def empty_import(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage4Test.empty',False);p.get_by_role('button',name='Import Recipes',exact=True).click();d=p.get_by_role('dialog',name='Import recipes',exact=True);assert d.get_by_role('button').first.evaluate('(e)=>e===document.activeElement');p.keyboard.press('Escape');assert not d.count() and records(p)==[]
 p.get_by_role('button',name='Import Recipes',exact=True).click();p.bring_to_front()
 with p.expect_file_chooser() as fc:p.get_by_role('dialog',name='Import recipes',exact=True).get_by_role('button',name=re.compile('Choose recipe export file')).click()
 fc.value.set_files({'name':'first.json','mimeType':'application/json','buffer':json.dumps({'@type':'Recipe','name':'Imported first recipe','recipeIngredient':['2 cups rice'],'recipeInstructions':'Simmer for 15 minutes.'}).encode()});d=p.get_by_role('dialog',name='Choose meal groups',exact=True);assert d.get_by_role('checkbox',name='Add imported recipes to rotation',exact=True).is_checked();d.get_by_role('button',name='Import recipes',exact=True).click();p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).click();assert records(p)[0]['rotation'] and records(p)[0]['groceryDefaultAll'];assert not p.get_by_role('button',name='Import Recipes',exact=True).count();clean(errors);c.close();print('PASS',name,'empty Import uses existing real file picker/parser, keyboard cancellation and Stage 3 defaults',flush=True)

def rotation_setup(b,name,width):
 c,p,errors,_=setup(b,name,width);p.evaluate('stage4Test.clearPlans();stage4Test.groups()');before=storage(p);definitions=records(p);prompt=p.get_by_role('button',name='Set Up Your Rotation',exact=True);prompt.focus();p.keyboard.press('Enter');d=p.get_by_role('dialog',name='Set Up Your Rotation',exact=True);d.get_by_role('combobox',name='Meal tab').select_option('lunch');d.get_by_role('button',name='Close setup',exact=True).click();assert storage(p)==before
 prompt.click();d=p.get_by_role('dialog',name='Set Up Your Rotation',exact=True);d.get_by_role('combobox',name='Meal tab').select_option('lunch');d.get_by_role('button',name='Monday',exact=True).click();picker=p.get_by_role('dialog',name="Choose Monday's meal groups",exact=True);picker.locator('input[data-group-choice][value=Sides]').check();picker.get_by_role('button',name='Close',exact=True).click();assert next(x for x in s2.plans(p) if x['id']=='lunch')['weekdayCategories']['Monday']==['Sides'];assert not next(x for x in s2.plans(p) if x['id']=='original')['weekdayCategories'];assert records(p)==definitions
 assert not p.get_by_role('button',name='Set Up Your Rotation',exact=True).count();assert p.get_by_role('button',name='Rotate Meals',exact=True).is_visible();assert not p.get_by_role('button',name='Cycle Meals',exact=True).count();assert p.get_by_role('button',name='Rotate Back',exact=True).is_visible();p.get_by_role('button',name='Rotate Meals',exact=True).click();assert p.get_by_role('dialog',name='Rotate out recipes',exact=True).is_visible();p.get_by_role('dialog',name='Rotate out recipes',exact=True).get_by_role('button',name='Close',exact=True).click()
 saved=storage(p);p.reload();assert not p.get_by_role('button',name='Set Up Your Rotation',exact=True).count();p.evaluate('weekTest.restore',saved);p.reload();assert next(x for x in s2.plans(p) if x['id']=='lunch')['weekdayCategories']['Monday']==['Sides'];assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');clean(errors);c.close();print('PASS',name,width,'temporary setup no writes on open/Cancel, explicit tab/day groups, normal Rotate Meals/Back and persistence',flush=True)

def configured_safety(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('weekTest.once();weekTest.check();stage4Test.legacy();stage4Test.groups()');before=storage(p);labels=p.evaluate('stage4Test.labels()');assert not p.get_by_role('button',name='Set Up Your Rotation',exact=True).count();p.evaluate('stage4Test.setup()');p.get_by_role('dialog',name='Set Up Your Rotation',exact=True).get_by_role('button',name='Close setup',exact=True).click();assert storage(p)==before and p.evaluate('stage4Test.labels()')==labels
 p.evaluate('stage4Test.clearPlans();stage4Test.explicitEmpty();stage4Test.groups()');assert not p.get_by_role('button',name='Set Up Your Rotation',exact=True).count();clean(errors);c.close();print('PASS',name,'configured/temporary plans and legacy labels preserved; explicit empty weekday counts as setup',flush=True)

def group_delete(b,name,width,duplicate=False):
 c,p,errors,_=setup(b,name,width);p.evaluate('stage4Test.destination()')
 if duplicate:p.evaluate('stage4Test.shared','Destination')
 p.evaluate('weekTest.check();stage4Test.groups()');old=records(p);checks={item['id']:(item['checked'],item['line']) for item in p.evaluate('weekTest.sources()')};p.evaluate('stage4Test.group','Rice');d=p.get_by_role('dialog',name='Edit meal group',exact=True);assert d.get_by_role('button',name='Delete group',exact=True).locator('svg').count()==1;d.get_by_role('button',name='Delete group',exact=True).click();d=p.get_by_role('dialog',name='Delete “Rice” group?',exact=True);assert d.get_by_role('button',name='Delete group, but keep recipes',exact=True).evaluate('(e)=>e===document.activeElement');expect(d).to_contain_text('Unrelated groups are not deleted');p.keyboard.press('Escape');assert records(p)==old
 p.evaluate('stage4Test.del','Rice');d=p.get_by_role('dialog',name='Delete “Rice” group?',exact=True);d.get_by_role('button',name='Delete group, but keep recipes',exact=True).click();d.get_by_role('combobox',name='Move recipes to group',exact=True).select_option('Destination');d.get_by_role('button',name='Confirm moving recipes and deleting group',exact=True).click();assert 'Rice' not in p.evaluate('stage4Test.categories()');after=records(p)
 # A move retains each source ID unless an existing shared identity in the
 # destination deliberately absorbs that membership. Every other field survives.
 expected=copy.deepcopy(old)
 if duplicate:
  # This fixture explicitly creates a second membership of recipe 1 at the
  # destination. Its existing ID survives; the now-redundant source ID does not.
  peer=next(item for item in old if item['cat']=='Destination')
  expected=[item for item in expected if item['id']!=1]
  next(item for item in expected if item['id']==peer['id'])['linkGroup']=''
 for item in expected:
  if item['cat']=='Rice':item['cat']='Destination'
 assert after==expected,('Exact IDs and all recipe fields',after,expected)
 remaining_checks={item['id']:(item['checked'],item['line']) for item in p.evaluate('weekTest.sources()')};assert checks.keys()&remaining_checks.keys();assert all(remaining_checks[key]==checks[key] for key in checks.keys()&remaining_checks.keys()),'Unaffected grocery occurrences keep checks and quantities'
 unrelated={key:value for key,value in checks.items() if json.loads(json.loads(key)[0])[:2]!=['original','Tuesday']};assert unrelated;assert all(remaining_checks.get(key)==value for key,value in unrelated.items()),'No unrelated contribution may disappear'
 p.locator('#undo').click();assert records(p)==old,'Undo must restore exact records and IDs'
 undo_checks={item['id']:(item['checked'],item['line']) for item in p.evaluate('weekTest.sources()')};assert undo_checks.keys()==checks.keys();assert all(undo_checks[key][0]==value[0] for key,value in checks.items()),'Undo preserves every checked occurrence'
 assert undo_checks==checks,'Undo restores every grocery quantity, including the merged day'
 p.evaluate('stage4Test.del','Rice');d=p.get_by_role('dialog',name='Delete “Rice” group?',exact=True);d.get_by_role('button',name='Delete group, but keep recipes',exact=True).click();d.get_by_role('combobox',name='Move recipes to group',exact=True).select_option('Destination');d.get_by_role('button',name='Confirm moving recipes and deleting group',exact=True).click();assert records(p)==expected
 assert not errors,errors;saved=storage(p);p.reload();assert records(p)==expected;p.evaluate('weekTest.restore',saved);p.reload();assert records(p)==expected;assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');clean(errors);c.close();print('PASS',name,width,'group deletion keeps exact IDs/fields, duplicate',duplicate,'Cancel, Undo, safe focus, trash, reload and backup',flush=True)

def polish(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage4Test.shared();stage4Test.tweak();stage4Test.groups()');before=records(p);p.evaluate('stage4Test.full',1);p.locator('#editor [data-editor-section=organization]>summary').click();button=p.get_by_role('button',name='Remove meal from Sauces',exact=True);assert button.locator('svg').inner_html().find('M4 7h16')>=0;assert button.bounding_box()['width']>=44 and button.bounding_box()['height']>=44;p.locator('#cancel').click();assert records(p)==before
 p.evaluate('stage3Test.open()');status=p.get_by_role('region',name='Needs Adjusting',exact=True);status.get_by_role('button',name='Remove Needs Adjusting',exact=True).click();d=p.get_by_role('dialog',name='Remove Needs Adjusting?',exact=True);expect(d).to_contain_text('Recipes will not be deleted');d.get_by_role('button',name='Cancel removal',exact=True).click();assert records(p)==before
 p.get_by_role('button',name='Close recipe',exact=True).click();p.evaluate('stage4Test.groups()');p.locator('.master-category-card[data-category=Rice] .master-category-title').click();ind=p.get_by_role('button',name='Needs Adjusting: Thai Garlic Pork',exact=True).first;assert ind.bounding_box()['width']>=44 and ind.bounding_box()['height']>=44;assert ind.locator('svg').bounding_box()['width']<=16
 p.evaluate('stage4Test.swipe',1);menu=p.locator('#mealSwipeMenu');assert menu.get_by_role('button',name='Remove from this group',exact=True).count()==1;expect(menu).to_contain_text('keeps it in its other groups');menu.get_by_role('button',name='Cancel',exact=True).click();assert records(p)==before;p.evaluate('stage4Test.swipe',1);p.locator('#mealSwipeMenu').get_by_role('button',name='Remove from this group',exact=True).click();remaining=records(p);assert {m['id'] for m in remaining}=={m['id'] for m in before}-{1};assert 'Rice' in p.evaluate('stage4Test.categories()');peer=next(m for m in remaining if m.get('name')=='Thai Garlic Pork');prior=next(m for m in before if m['id']==peer['id']);assert {k:v for k,v in peer.items() if k!='linkGroup'}=={k:v for k,v in prior.items() if k!='linkGroup'};clean(errors);c.close();print('PASS',name,'compact Needs Adjusting, 44px targets, scoped confirmations and membership trash/Cancel',flush=True)

def fresh_install(b,name):
 c=b.new_context(viewport={'width':320,'height':800},is_mobile=True,has_touch=True);p=c.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
 source=(stage.f.ROOT/name).read_text().replace('resumeRecipeViewer();})();','resumeRecipeViewer();'+stage.f.HOOK.replace('localStorage','testStorage' if prefix else 'localStorage')+'})();')
 if prefix:p.add_init_script("localStorage.setItem('mealRotationDataV1','WORKING SENTINEL')")
 p.route('http://stage4.test/**',lambda r:r.fulfill(content_type='text/html',body=source) if r.request.url.endswith(name) else r.fulfill(body=''));p.route('https://**/*',lambda r:r.fulfill(body=''));p.goto('http://stage4.test/'+name);assert [plan['name'] for plan in s2.plans(p)]==['Breakfast','Lunch','Dinner'];assert records(p)==[]
 p.get_by_role('button',name='Meal Groups',exact=True).click();assert p.get_by_role('button',name='Add Recipe',exact=True).is_visible() and p.get_by_role('button',name='Import Recipes',exact=True).is_visible();assert not p.locator('.master-category-card,.master-expansion-controls').count();p.reload();assert [plan['name'] for plan in s2.plans(p)]==['Breakfast','Lunch','Dinner'] and records(p)==[]
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 clean(errors);c.close();print('PASS',name,'genuine fresh install retains default tabs and clear empty onboarding through reload',flush=True)

def setup_failure(b,name):
 c,p,errors,prefix=setup(b,name);p.evaluate('stage4Test.clearPlans();stage4Test.groups()');definitions=records(p);original=p.evaluate('key=>localStorage.getItem(key)',prefix+'mealRotationPlansV1');p.get_by_role('button',name='Set Up Your Rotation',exact=True).click();p.get_by_role('dialog',name='Set Up Your Rotation',exact=True).get_by_role('button',name='Monday',exact=True).click();d=p.get_by_role('dialog',name="Choose Monday's meal groups",exact=True)
 p.evaluate('''()=>{window.stage4Set=Storage.prototype.setItem;Storage.prototype.setItem=function(k,v){if(String(k).endsWith('mealRotationPlansV1'))throw Error('synthetic setup failure');return stage4Set.call(this,k,v)}}''');d.locator('input[data-group-choice][value=Rice]').check();assert p.locator('#mealSaveWarning').is_visible();assert records(p)==definitions;assert p.evaluate('key=>localStorage.getItem(key)',prefix+'mealRotationPlansV1')==original;d.get_by_role('button',name='Close',exact=True).click()
 with p.expect_download() as download:p.locator('#mealSaveWarning').get_by_role('button',name='Export Data for Recovery',exact=True).click()
 assert 'mealRotationPlansV1' in open(download.value.path()).read();p.evaluate('()=>Storage.prototype.setItem=stage4Set');p.locator('#mealSaveWarning').get_by_role('button',name='Retry Save',exact=True).click();p.wait_for_function('!document.querySelector("#mealSaveWarning")');p.reload();assert next(plan for plan in s2.plans(p) if plan['id']=='original')['weekdayCategories']['Monday']==['Rice'] and records(p)==definitions;clean(errors);c.close();print('PASS',name,'setup reuses failed-save warning/export/Retry and preserves recipe definitions',flush=True)

def scheduled_removal(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage4Test.occasion()');before=records(p);assignments=copy.deepcopy(s2.plans(p));checks=s2.prior.progress(p);d=p.get_by_role('dialog',name="Choose Sunday's meal",exact=True);d.get_by_role('button',name='Remove scheduled meal',exact=True).click();confirm=p.get_by_role('dialog').filter(has_text='This removes only the scheduled meal from Sunday.');expect(confirm).to_contain_text('Saved recipes and permanent group assignments will not be deleted');confirm.get_by_role('button',name='No',exact=True).click();assert records(p)==before and s2.prior.progress(p)==checks
 d.get_by_role('button',name='Remove scheduled meal',exact=True).click();p.get_by_role('dialog').filter(has_text='This removes only the scheduled meal from Sunday.').get_by_role('button',name='Yes',exact=True).click();assert records(p)==before;assert all(plan['weekdayCategories']==next(old['weekdayCategories'] for old in assignments if old['id']==plan['id']) for plan in s2.plans(p));assert not any(row['day']=='Sunday' and row['id']==2 for row in stage.rows(p));assert all(value==checks[key] for key,value in s2.prior.progress(p).items());clean(errors);c.close();print('PASS',name,'scheduled-day removal confirmation distinguishes collection deletion; Cancel and saved recipes/checks/assignments preserved',flush=True)

def setup_with_one_time(b,name):
 c,p,errors,_=setup(b,name);p.evaluate('stage4Test.clearPlans();weekTest.once(null,"Sunday");weekTest.check();stage4Test.groups()');once=copy.deepcopy(stage.plan(p)['weekSchedule']['slots']);progress=s2.prior.progress(p);p.get_by_role('button',name='Set Up Your Rotation',exact=True).click();p.get_by_role('dialog',name='Set Up Your Rotation',exact=True).get_by_role('button',name='Monday',exact=True).click();d=p.get_by_role('dialog',name="Choose Monday's meal groups",exact=True);d.locator('input[data-group-choice][value=Rice]').check();d.get_by_role('button',name='Close',exact=True).click();assert stage.plan(p)['weekSchedule']['slots']==once;assert all(s2.prior.progress(p)[key]==value for key,value in progress.items());saved=storage(p);p.reload();p.evaluate('weekTest.restore',saved);p.reload();assert stage.plan(p)['weekSchedule']['slots']==once;assert all(s2.prior.progress(p)[key]==value for key,value in progress.items());clean(errors);c.close();print('PASS',name,'setup changes only the explicit weekday and preserves unrelated one-time identity/quantities/checks through backup/reload',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   for width in [280,320,360]:
    for groups in [False,True]:empty_collection(b,name,width,groups)
    rotation_setup(b,name,width);group_delete(b,name,width,width==360)
   empty_import(b,name);configured_safety(b,name);polish(b,name);fresh_install(b,name);setup_failure(b,name);scheduled_removal(b,name);setup_with_one_time(b,name)
  b.close()
