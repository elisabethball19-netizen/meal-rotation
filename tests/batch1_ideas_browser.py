"""Batch 1 focused fixtures; disposable touch-browser contexts, both existing apps."""
import json, copy
from pathlib import Path
from playwright.sync_api import sync_playwright
from scheduled_date_fixture import DATED_SCHEDULE_HOOK
ROOT=Path(__file__).resolve().parents[1]
HOOK='''window.batch1={
 star:(id,value)=>applyRecipeBulk([String(id)],{upNextStar:value},{upNextFirst:String(id)}),front:id=>placeUpNextFirst(meals.find(m=>m.id===id)),longList:()=>{for(let n=100;n<140;n++)meals.push({id:n,name:'Long '+n,cat:'Meals',rotation:false,recipeStatus:'up-next',upNextStar:false,ingredients:[]});persist();renderList()},importRecords:items=>showRecipeImportSelection(recipeImportItems(items),"legacy-status-fixture.json"),records:()=>JSON.parse(JSON.stringify(meals)),plans:()=>JSON.parse(JSON.stringify(mealPlans)),
 groups:()=>{showTop=false;allMealsActive=false;groceryTabActive=false;masterExpansionInitialized=true;masterExpandedCategories.clear();cats.forEach(c=>masterExpandedCategories.add(c));render()},
 status:(id,status)=>applyRecipeBulk([String(id)],{status}),bulk:(ids,patch,options={})=>applyRecipeBulk(ids.map(String),patch,options),
 order:()=>normalizedUpNextOrder(),list:cat=>masterRecipeOrder(cat).map(m=>m.id),
 move:(id,dir,ids)=>moveUpNextRecipe(meals.find(m=>m.id===id),dir,ids.map(id=>meals.find(m=>m.id===id))),
 pool:cat=>automaticRecipeCandidates(cat).map(m=>m.id),
 snapshot:()=>recipeBulkBackupAPI.capture(),restore:b=>{recipeBulkBackupAPI.restore(normalizeImportedBackup(b));backupRestoreReloadPending=true},
 schedule:()=>mealPlans.flatMap(p=>getDisplayedWeekdayMealsForPlan(p.id===activePlanId?{...p,weekdayCategories,weekdayMealOverrides}:p).map(e=>[p.id,e.day,e.cat,e.meal.id,String(e.linkedTo??'')])),
 manual:id=>applyManualWeekdayMeal('Thursday','Meals',meals.find(m=>m.id===id)),
 select:ids=>{endRecipeBulk();showTop=false;recipeBulkMode=true;recipeBulkSourceGroup=meals.find(m=>m.id===ids[0]).cat;recipeBulkIds=new Set(ids.map(String));updateRecipeBulkUI();openRecipeBulkEditor(false)},
 editor:openEditor,groupEdit:openMasterCategoryEditMenu,enabled:groupUsesRotation,assignments:groupRotationAssignments,
 unassign:cat=>{saveActiveMealPlan();for(const p of mealPlans)for(const day of weekdays){const raw=p.weekdayCategories[day];p.weekdayCategories[day]=(Array.isArray(raw)?raw:[raw]).filter(c=>c&&c!==cat)}weekdayCategories=JSON.parse(JSON.stringify(mealPlans.find(p=>p.id===activePlanId).weekdayCategories));saveWeekdayCategories();persist();render()},
 seedProgress:()=>{for(const p of mealPlans){const calendar=rotationCalendarForPlan(p,getDisplayedWeekdayMealsForPlan(p)),start=cookingPlanningWeekStart();calendar.weekStart=cookingLocalDate(start);for(const e of getDisplayedWeekdayMealsForPlan(p)){const key=rotationOccurrenceKey({...e,planId:p.id});calendar.occurrences[key]=cookingLocalDate(cookingDateInWeek(e.day,start));calendar.assignedOn[key]=cookingLocalDate(start);calendar.assignedAt[key]=start.toISOString();}for(const key of Object.keys(calendar.slots||{}))calendar.slots[key]=cookingLocalDate(cookingDateInWeek(key.split('::')[0],start));p.rotationCalendar=calendar}for(const p of mealPlans)for(const e of getDisplayedWeekdayMealsForPlan(p)){const context=cookingContext(p.id,e.day,e.cat,e.meal,e.linkedTo),key=cookingOccurrenceKey(context),tokens=cookingItemTokens(e.meal);cookingSessions.occurrences[key]={id:'session-'+key,context,ingredients:tokens.ingredients.slice(0,1).map(x=>x.token),steps:[],autoIngredients:[],ingredientOverrides:{}};occurrenceScales.occurrences[key]={context,multiplier:2}}writeCookingSessions(cookingSessions);writeOccurrenceScales(occurrenceScales);persist()},
 associated:()=>JSON.stringify({cookingSessions,occurrenceScales,checks:mealPlans.map(p=>p.makeAheadChecks),calendars:mealPlans.map(p=>p.rotationCalendar),groceries:[...getGroceryContributions(true)].map(s=>[s.id,grocerySourceChecked(s)])}),
 cycle:()=>moveDisplayedMealsToBottom(),cancelBulk:endRecipeBulk,persist,undo:()=>restoreState(JSON.parse(history.pop()))
};'''
HOOK+=DATED_SCHEDULE_HOOK
def recipe(id,name,cat,rotation=False,**kw):
 return dict(id=id,name=name,cat=cat,rotation=rotation,ingredients=['1 cup rice'],instructions=[{'type':'step','text':'Cook rice.'}],url='https://example.test/'+str(id),custom={'preserve':id},**kw)
def setup(browser,name,width=360):
 prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
 records=[recipe(1,'Active','Meals',True,favorite=True,linkedMealIds=[8],makeAheadTasks=[{'id':'prep','description':'Prep rice','daysBefore':1}]),recipe(2,'Zulu soon','Meals',favorite=True,recipeStatus='up-next',linkGroup='shared'),recipe(3,'Alpha soon','Meals',recipeStatus='up-next'),recipe(4,'Legacy idea','Meals',recipeStatus='back-burner'),recipe(5,'Scheduled idea','Meals'),recipe(6,'Default missing','Meals'),recipe(8,'Linked side','Reference'),recipe(12,'Zulu soon','Other',recipeStatus='up-next',linkGroup='shared'),recipe(13,'Other soon','Other',recipeStatus='up-next'),recipe(14,'Other active','Other',True)]
 records[5].pop('rotation')
 dinner=dict(id='original',name='Dinner',weekdayCategories={'Monday':['Meals']},weekdayMealOverrides={'Monday::Meals':'1'},cycleRetainedSlots={'Monday::Meals':'1'},cycleSlotChoices={'Monday::Meals':{'mealId':'1','parentId':'','retain':True}},occasionalMeals={'Friday':'5'},weekdayRecipeFilters={},pinnedCats=[])
 lunch=dict(id='lunch',name='Lunch',weekdayCategories={'Tuesday':['Other']},weekdayMealOverrides={},weekdayRecipeFilters={},pinnedCats=[])
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Meals','Other','Reference'],active='Meals',meals=records)),prefix+'mealRotationPlansV1':json.dumps(dict(plans=[dinner,lunch],activeId='original')),prefix+'mealRotationShowPlanTabsV1':'false',prefix+'mealRotationTutorialStageV1':'done',prefix+'mealRotationRecipeViewPrefsV1':json.dumps({'keepScreenAwake':False})}
 seed[prefix+'mealRotationUpNextOrderV1']=json.dumps(['2','12','3','13'])
 seed['unrelated-sentinel']='keep'
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
 context=browser.new_context(viewport={'width':width,'height':800},is_mobile=True,has_touch=True,service_workers='block');p=context.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_default_timeout(5000)
 p.add_init_script('if(!sessionStorage.seeded){for(const [k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seeded="yes"}')
 def route(request):
  path=request.request.url.split('http://batch1.test/',1)[-1].split('?')[0];f=ROOT/path
  if not f.is_file():request.fulfill(status=404,body='');return
  body=f.read_text() if f.suffix in ['.html','.js','.css','.webmanifest'] else ''
  if path=='ui.js':body+='\n'+HOOK
  if path=='meal-rotation-test.html':body=body.replace('mealPersistence.showRecovery({normalize:normalizeImportedBackup',HOOK.replace('localStorage','testStorage')+'\nmealPersistence.showRecovery({normalize:normalizeImportedBackup',1)
  request.fulfill(status=200,body=body,content_type='text/javascript' if f.suffix=='.js' else 'text/css' if f.suffix=='.css' else 'text/html')
 p.route('http://batch1.test/**',route);p.route('https://**/*',lambda r:r.fulfill(status=200,body=''))
 p.goto('http://batch1.test/'+name);p.wait_for_function('window.batch1!==undefined');assert not errors,errors
 p.evaluate('batch1.groups()');return context,p,errors,prefix

def get(p,expr):return p.evaluate('batch1.'+expr)
def pick(p,dialog,button,label):
 dialog.get_by_role('button',name=button,exact=True).tap()
 picker=p.get_by_role('dialog',name=button,exact=True)
 picker.get_by_role('radio',name=label,exact=True).check()
 # Existing single-choice dialog confirms pending selection with the check icon.
 picker.get_by_role('button',name='Confirm '+button.lower(),exact=True).tap()

def record(p,id):return next(m for m in get(p,'records()') if m['id']==id)
def row(p,id,cat='Meals'):return p.locator('[data-category="'+cat+'"] .master-category-meal[data-meal-id="'+str(id)+'"]')
def up_list(p,cat='Meals'):return p.locator('[data-category="'+cat+'"] [data-recipe-section="up-next"] .master-category-meal').evaluate_all('(xs)=>xs.map(x=>Number(x.dataset.mealId))')
def status_editor(p,id,label,save=True):
 get(p,'editor('+str(id)+')');p.locator('#recipeStatus').tap();d=p.get_by_role('dialog',name='Recipe status',exact=True)
 assert d.get_by_role('radio').count()==2 and not d.get_by_text('Back Burner',exact=True).count()
 d.get_by_role('radio',name=label,exact=True).check();d.get_by_role('button',name='Confirm recipe status',exact=True).tap();p.locator('#save' if save else '#cancel').tap()

def migration_and_actions(browser,name):
 c,p,errors,prefix=setup(browser,name)
 assert p.locator('[data-category="Meals"] [data-recipe-section]').evaluate_all('(xs)=>xs.map(x=>x.dataset.recipeSection)')==['rotation','up-next']
 assert get(p,'order()')[:4]==['2','12','3','13']
 assert up_list(p)==[2,3,6,4,5]
 assert record(p,2)['upNextStar'] and not record(p,4)['upNextStar'] and not record(p,6)['upNextStar']
 assert not row(p,2).locator('[data-recipe-favorite]').count() and row(p,1).locator('[data-recipe-favorite]').count()==1
 assert not p.locator('.shared-meal-link-button').count() and not p.locator('[title="Shared across groups"]').count()
 assert not p.locator('[aria-label*=" in Ideas"]').count()
 # Star taps share across copies, place first within their portion, and preserve Favorite values.
 row(p,2).get_by_role('button',name='Unstar Zulu soon',exact=True).tap()
 assert not record(p,2)['upNextStar'] and not record(p,12)['upNextStar'] and record(p,2)['favorite']
 assert get(p,'order()')==['3','13','2','12','6','4','8','5'];assert not p.locator('[role="dialog"],#recipeBulkToolbar').count()
 p.reload();assert not record(p,2)['upNextStar'] and get(p,'order()')==['3','13','2','12','6','4','8','5']
 get(p,'groups()');row(p,4).get_by_role('button',name='Star Legacy idea',exact=True).tap();assert get(p,'order()')[:3]==['4','3','13']
 row(p,4).get_by_role('button',name='Unstar Legacy idea',exact=True).tap();assert get(p,'order()')[2:5]==['4','2','12']
 p.evaluate('establishDatedFixtureSchedule()');get(p,'seedProgress()');schedule=get(p,'schedule()');associated=get(p,'associated()')
 row(p,1).get_by_role('button',name='Move Active to Ideas',exact=True).tap()
 assert get(p,'order()')[0]=='1' and record(p,1)['upNextStar'] and record(p,1)['favorite']
 assert get(p,'schedule()')==schedule and get(p,'associated()')==associated
 assert get(p,"pool('Meals')")==[]
 row(p,1).get_by_role('button',name='Move Active to In Rotation',exact=True).tap();assert get(p,'schedule()')==schedule and get(p,'associated()')==associated
 # Shared promotion goes first in each In Rotation list, without replacing scheduled recipes.
 row(p,2).get_by_role('button',name='Move Zulu soon to In Rotation',exact=True).tap()
 assert record(p,2)['rotation'] and record(p,12)['rotation'] and record(p,2)['favorite']
 assert p.locator('[data-category="Meals"] [data-recipe-section="rotation"] .master-category-meal').first.get_attribute('data-meal-id')=='2'
 assert get(p,'schedule()')==schedule and get(p,'associated()')==associated
 row(p,2).get_by_role('button',name='Move Zulu soon to Ideas',exact=True).tap();assert set(get(p,'order()')[:2])=={'2','12'} and record(p,12)['upNextStar'],(get(p,'order()'),record(p,2),record(p,12),p.locator('[role=dialog]').all_text_contents())
 assert get(p,'schedule()')==schedule and get(p,'associated()')==associated
 get(p,'manual(4)');assert not record(p,4)['rotation'] and not record(p,4)['upNextStar']
 statuses={m['id']:(m.get('rotation'),m.get('upNextStar'),m.get('favorite'))for m in get(p,'records()')};get(p,'cycle()');assert statuses=={m['id']:(m.get('rotation'),m.get('upNextStar'),m.get('favorite'))for m in get(p,'records()')}
 # Backups preserve an explicit unstar across restoration and repeated loading.
 get(p,'persist()');snapshot=get(p,'snapshot()');core=json.loads(snapshot['mealRotationDataV1']);backup=dict(version=2,**core,storage=snapshot)
 get(p,'star(4,true)');p.evaluate('b=>batch1.restore(b)',backup);p.reload();assert not record(p,4)['upNextStar'];p.reload();assert not record(p,4)['upNextStar']
 assert p.evaluate('localStorage.getItem("unrelated-sentinel")')=='keep'
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;c.close();print('PASS',name,'two-section migration/order, stars versus Favorites, reload/restore, direct shared arrows/promotion, exact scheduled associated data, manual scheduling/cycling and storage isolation',flush=True)

def editors_and_groups(browser,name):
 c,p,errors,prefix=setup(browser,name)
 status_editor(p,3,'In Rotation',False);assert not record(p,3)['rotation']
 status_editor(p,3,'In Rotation',True);assert record(p,3)['rotation'] and record(p,3)['upNextStar']
 get(p,'groups()');get(p,'select([1,2,4])');d=p.get_by_role('dialog',name='Edit recipes',exact=True);before=get(p,'snapshot()')
 pick(p,d,'Rotation status','Ideas');assert get(p,'snapshot()')==before
 pick(p,d,'Rotation status','Keep existing');assert d.get_by_role('button',name='Apply to selected recipes',exact=True).is_disabled()
 d.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert get(p,'snapshot()')==before
 get(p,'select([1,2,4])');d=p.get_by_role('dialog',name='Edit recipes',exact=True);pick(p,d,'Rotation status','Ideas');d.get_by_role('button',name='Apply to selected recipes',exact=True).tap();assert all(not record(p,id)['rotation'] for id in [1,2,4,12])
 get(p,"status(1,'rotation')");before={m['id']:(m.get('rotation'),m['upNextStar'])for m in get(p,'records()')}
 get(p,'bulk([1,2,4],{}, {bulkGroups:{sourceGroup:"Meals",add:true,remove:false,groups:["Reference"],newGroups:[]}})');assert all(before[m['id']]==(m.get('rotation'),m['upNextStar']) for m in get(p,'records()') if m['id'] in before)
 get(p,"groupEdit('Other')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);assert d.locator('.meal-unified-actions button').evaluate_all('(xs)=>xs.every(x=>{const b=x.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth})');check=d.get_by_role('checkbox',name='Use for meal rotation',exact=True)
 assert check.evaluate('(x)=>getComputedStyle(x).width')=='18px';check.uncheck();d.get_by_role('button',name='Save group changes',exact=True).tap();assert 'Remove this group’s weekday assignments before turning off meal rotation.' in d.inner_text() and 'Tuesday · Lunch' in d.inner_text();d.get_by_role('button',name='Cancel group editing',exact=True).tap();assert get(p,"enabled('Other')")
 get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();d.get_by_role('button',name='Cancel group editing',exact=True).tap();assert get(p,"enabled('Reference')")
 get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();schedule=get(p,'schedule()');d.get_by_role('button',name='Save group changes',exact=True).tap();assert not get(p,"enabled('Reference')") and get(p,'schedule()')==schedule
 get(p,'groups()');assert p.locator('[data-category="Reference"] [data-recipe-section]').evaluate_all('(xs)=>xs.map(x=>x.dataset.recipeSection)')==['all'];assert not p.locator('[data-category="Reference"] .recipe-up-next-star').count()
 # Add meals keeps Copy/Move, search, checkbox selection and confirmation/cancel with outline chevrons.
 get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);add=d.get_by_role('button',name='Add meals',exact=True)
 assert add.bounding_box()['width']<d.bounding_box()['width']*.7;assert not add.locator('svg').count();add.tap();picker=p.locator('.add-meals-picker');assert 'Add meals to Reference' in picker.inner_text() and 'Add meals by:' not in picker.inner_text()
 assert not any(x in picker.inner_text() for x in ['▸','▾']);assert picker.locator('.meal-editor-group-chevron svg').count()>0
 assert picker.get_by_role('radio',name='Copy (keep in original group)',exact=True).is_checked();picker.get_by_role('radio',name='Move (remove from original group)',exact=True).check();picker.get_by_role('button',name='Cancel',exact=True).tap()
 # Confirm both existing Add meals modes with representative non-scheduled recipes.
 get(p,"groupEdit('Reference')");p.get_by_role('dialog',name='Edit meal group',exact=True).get_by_role('button',name='Add meals',exact=True).tap();picker=p.locator('.add-meals-picker');picker.get_by_role('searchbox',name='Search meals',exact=True).fill('Alpha soon');picker.get_by_role('checkbox',name='Alpha soon',exact=True).check();picker.get_by_role('button',name='Add selected meals',exact=True).tap()
 assert record(p,3)['cat']=='Meals' and any(m['cat']=='Reference' and m.get('linkGroup')==record(p,3).get('linkGroup') for m in get(p,'records()'))
 original=record(p,6).copy();scheduled=get(p,'schedule()');get(p,"groupEdit('Reference')");p.get_by_role('dialog',name='Edit meal group',exact=True).get_by_role('button',name='Add meals',exact=True).tap();picker=p.locator('.add-meals-picker');picker.get_by_role('searchbox',name='Search meals',exact=True).fill('Default missing');picker.get_by_role('checkbox',name='Default missing',exact=True).check();picker.get_by_role('radio',name='Move (remove from original group)',exact=True).check();picker.get_by_role('button',name='Add selected meals',exact=True).tap();assert record(p,6)=={**original,'cat':'Reference'} and get(p,'schedule()')==scheduled
 get(p,"unassign('Other')");get(p,"groupEdit('Other')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();d.get_by_role('button',name='Save group changes',exact=True).tap();assert get(p,"pool('Other')")==[] and 1 in get(p,"pool('Meals')")
 get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).check();d.get_by_role('button',name='Save group changes',exact=True).tap();assert get(p,"enabled('Reference')")
 assert not errors,errors;c.close();c,p,errors,prefix=setup(browser,name,320);get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);assert d.locator('.meal-unified-actions button').evaluate_all('(xs)=>xs.every(x=>{const b=x.getBoundingClientRect();return b.left>=0&&b.right<=innerWidth})');assert not errors,errors;c.close();print('PASS',name,'individual/bulk confirmation and Cancel/Keep existing, membership preservation, reference lists/safeguards, group editor controls and Add meals chevrons/Copy/Move/Cancel',flush=True)

def touch_drag(p,c,source,target=None,cancel=False,edge=False):
 source.locator('.master-category-meal-name').first.evaluate('(x)=>x.scrollIntoView({block:"center"})');p.wait_for_timeout(80);box=source.locator('.master-category-meal-name').first.bounding_box();start={'x':box['x']+15,'y':box['y']+box['height']/2,'id':1};client=c.new_cdp_session(p)
 client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[start]});p.wait_for_timeout(650)
 assert not p.locator('.master-group-drag-ghost,#recipeBulkToolbar').count()
 targetbox=target.bounding_box() if target else None;y=p.viewport_size['height']-15 if edge else targetbox['y']+targetbox['height']*.85
 client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**start,'y':start['y']+12}]});p.wait_for_timeout(80)
 client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**start,'y':y}]});p.wait_for_timeout(260)
 assert p.locator('.master-group-drag-ghost').count()==1
 scroll=p.evaluate('scrollY');p.wait_for_timeout(250)
 if edge:assert p.evaluate('scrollY')>scroll
 client.send('Input.dispatchTouchEvent',{'type':'touchCancel' if cancel else 'touchEnd','touchPoints':[]});p.wait_for_timeout(100)
 assert not p.locator('.master-group-drag-ghost,[role="dialog"],#recipeBulkToolbar').count()

def dragging(browser,name):
 c,p,errors,prefix=setup(browser,name);before=get(p,'order()');touch_drag(p,c,row(p,2),row(p,3));assert get(p,'order()')[:4]==['3','2','12','13'];assert record(p,2)['upNextStar'] and record(p,12)['upNextStar']
 before=get(p,'order()');touch_drag(p,c,row(p,6),row(p,4),True);assert get(p,'order()')==before
 touch_drag(p,c,row(p,6),row(p,4));assert up_list(p).index(4)<up_list(p).index(6);assert not record(p,6)['upNextStar']
 p.reload();get(p,'groups()');assert up_list(p).index(4)<up_list(p).index(6)
 # Overlapping membership + hidden filtered row: only the moved recipe changes relative placement.
 get(p,'bulk([13],{}, {bulkGroups:{sourceGroup:"Other",add:true,remove:false,groups:["Meals"],newGroups:[]}})');copyid=next(m['id'] for m in get(p,'records()') if m.get('linkGroup')==record(p,13).get('linkGroup') and m['cat']=='Meals')
 get(p,'star(2,true)');row(p,3).evaluate('(x)=>x.hidden=true');before=get(p,'order()');hidden=[id for id in before if id not in ['2','12']]
 touch_drag(p,c,row(p,2),row(p,copyid));assert [id for id in get(p,'order()') if id not in ['2','12']]==hidden
 assert get(p,"list('Other')").index(13)<get(p,"list('Other')").index(12)
 get(p,'persist()');snapshot=get(p,'snapshot()');backup=dict(version=2,**json.loads(snapshot['mealRotationDataV1']),storage=snapshot);order=get(p,'order()');p.evaluate('b=>batch1.restore(b)',backup);p.reload();assert get(p,'order()')==order
 # A quick swipe remains ordinary scrolling, and a stationary hold selects only on release.
 get(p,'groups()');source=row(p,2);source.locator('.master-category-meal-name').first.evaluate('(x)=>x.scrollIntoView({block:"center"})');box=source.bounding_box();point={'x':box['x']+70,'y':box['y']+20,'id':1};client=c.new_cdp_session(p)
 client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**point,'y':point['y']+50}]});client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert get(p,'order()')==order and not p.locator('#recipeBulkToolbar').count()
 get(p,'longList()');before=get(p,'order()');touch_drag(p,c,row(p,100),cancel=True,edge=True);assert get(p,'order()')==before
 # Stationary long-press keeps existing bulk selection, while the normal tap retains meal options.
 source=row(p,2).locator('.master-category-meal-name').first;source.evaluate('(x)=>x.scrollIntoView({block:"center"})');box=source.bounding_box();point={'x':box['x']+15,'y':box['y']+10,'id':1};client=c.new_cdp_session(p)
 client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});p.wait_for_timeout(650);assert not p.locator('#recipeBulkToolbar').count();client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert p.locator('#recipeBulkToolbar').count()==1
 get(p,'cancelBulk()');row(p,2).locator('.master-category-meal-name').first.tap();assert p.locator('.compact-meal-dialog,[role="dialog"]').count()
 assert not errors,errors;c.close();print('PASS',name,'CDP touch hold-and-drag in both portions, overlapping/filtered shared order, cancellation, edge scroll, ordinary scroll, reload/backup and no accidental actions',flush=True)

def imports_and_failure(browser,name):
 c,p,errors,prefix=setup(browser,name)
 items=[dict(name='Imported '+label,cat='Meals',ingredients=['rice'],instructions='Cook rice.',**fields) for label,fields in [('idea',{'rotation':False}),('back',{'recipeStatus':'back-burner'}),('soon',{'recipeStatus':'up-next','rotation':False}),('unstarred',{'recipeStatus':'up-next','upNextStar':False,'rotation':False}),('active',{'rotation':True}),('default',{})]]
 p.evaluate('items=>batch1.importRecords(items)',items);picker=p.locator('#recipeImportDialog');picker.get_by_role('button',name='Select all',exact=True).tap();picker.get_by_role('button',name='Import recipes',exact=True).tap()
 actual={m['name']:m for m in get(p,'records()') if m['name'].startswith('Imported ')}
 assert not actual['Imported idea']['upNextStar'] and not actual['Imported back']['upNextStar'] and actual['Imported soon']['upNextStar'] and not actual['Imported unstarred']['upNextStar'];assert actual['Imported active']['rotation'] and actual['Imported default']['rotation']
 get(p,'persist()');p.reload();assert not next(m for m in get(p,'records()') if m['name']=='Imported unstarred')['upNextStar']
 snapshot=get(p,'snapshot()');legacy=json.loads(snapshot['mealRotationDataV1']);legacy['meals']=copy.deepcopy(legacy['meals'])
 for meal in legacy['meals']:
  meal.pop('upNextStar',None)
  if meal['id'] in [4,5,6,8]:meal['recipeStatus']='back-burner' if meal['id']==4 else 'Ideas'
 oldbackup=dict(version=2,**legacy,storage=snapshot);p.evaluate('b=>batch1.restore(b)',oldbackup);p.reload()
 assert record(p,2)['upNextStar'] and not record(p,4)['upNextStar'] and not record(p,5)['upNextStar'];get(p,'star(2,false)');p.reload();assert not record(p,2)['upNextStar']
 get(p,'star(2,true)');before=get(p,'records()');order=get(p,'order()')
 p.evaluate("""()=>{const native=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key.endsWith('mealRotationUpNextOrderV1'))throw Error('injected order write failure');return native.call(this,key,value)};window.restoreBatch1Writes=()=>{Storage.prototype.setItem=native}}""")
 try:get(p,'star(2,false)');raise AssertionError('write failure accepted')
 except Exception as error:assert 'injected order write failure' in str(error)
 assert get(p,'records()')==before and get(p,'order()')==order;p.evaluate('restoreBatch1Writes()')
 assert not errors,errors;c.close();print('PASS',name,'legacy/current imports, preserved import defaults, explicit unstar restoration and atomic star/order failure rollback',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   migration_and_actions(browser,name);editors_and_groups(browser,name);dragging(browser,name);imports_and_failure(browser,name)
  browser.close()
