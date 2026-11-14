"""Batch 1 focused fixtures; disposable touch-browser contexts, both existing apps."""
import json, copy
from pathlib import Path
from playwright.sync_api import sync_playwright
from scheduled_date_fixture import DATED_SCHEDULE_HOOK
ROOT=Path(__file__).resolve().parents[1]
HOOK='''window.batch1={
 importRecords:items=>showRecipeImportSelection(recipeImportItems(items),"legacy-status-fixture.json"),records:()=>JSON.parse(JSON.stringify(meals)),plans:()=>JSON.parse(JSON.stringify(mealPlans)),
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
def setup(browser,name):
 prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
 records=[recipe(1,'Active','Meals',True,linkedMealIds=[8],makeAheadTasks=[{'id':'prep','description':'Prep rice','daysBefore':1}]),recipe(2,'Zulu soon','Meals',recipeStatus='up-next',linkGroup='shared'),recipe(3,'Alpha soon','Meals',recipeStatus='up-next'),recipe(4,'Legacy idea','Meals'),recipe(5,'Scheduled idea','Meals'),recipe(6,'Default missing','Meals'),recipe(8,'Linked side','Reference'),recipe(12,'Zulu soon','Other',recipeStatus='up-next',linkGroup='shared'),recipe(13,'Other soon','Other',recipeStatus='up-next'),recipe(14,'Other active','Other',True)]
 records[5].pop('rotation')
 dinner=dict(id='original',name='Dinner',weekdayCategories={'Monday':['Meals']},weekdayMealOverrides={'Monday::Meals':'1'},cycleRetainedSlots={'Monday::Meals':'1'},cycleSlotChoices={'Monday::Meals':{'mealId':'1','parentId':'','retain':True}},occasionalMeals={'Friday':'5'},weekdayRecipeFilters={},pinnedCats=[])
 lunch=dict(id='lunch',name='Lunch',weekdayCategories={'Tuesday':['Other']},weekdayMealOverrides={},weekdayRecipeFilters={},pinnedCats=[])
 seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Meals','Other','Reference'],active='Meals',meals=records)),prefix+'mealRotationPlansV1':json.dumps(dict(plans=[dinner,lunch],activeId='original')),prefix+'mealRotationShowPlanTabsV1':'false',prefix+'mealRotationTutorialStageV1':'done',prefix+'mealRotationRecipeViewPrefsV1':json.dumps({'keepScreenAwake':False})}
 seed['unrelated-sentinel']='keep'
 if prefix:seed['mealRotationDataV1']='WORKING SENTINEL'
 context=browser.new_context(viewport={'width':360,'height':800},is_mobile=True,has_touch=True,service_workers='block');p=context.new_page();errors=[];p.on('pageerror',lambda e:errors.append(str(e)));p.set_default_timeout(5000)
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

def run(browser,name):
 c,p,errors,prefix=setup(browser,name)
 assert get(p,"pool('Meals')")==[1]
 assert next(m for m in get(p,'records()') if m['id']==8)['rotation'] is False
 assert get(p,'records()')[5].get('rotation') is None
 assert p.locator('[data-category="Meals"] [data-recipe-section]').evaluate_all('(xs)=>xs.map(x=>x.dataset.recipeSection)')==['rotation','up-next','back-burner']
 assert p.locator('[data-category="Meals"] [data-recipe-section="back-burner"] .master-recipe-section-recipes').is_hidden()
 p.evaluate('establishDatedFixtureSchedule()');get(p,'seedProgress()');schedule=get(p,'schedule()');associated=get(p,'associated()')
 # A scheduled automatic recipe can change status without replacing or losing its occurrence.
 get(p,"status(1,'up-next')");assert get(p,'schedule()')==schedule;assert get(p,'associated()')==associated
 assert get(p,"pool('Meals')")==[]
 get(p,"status(1,'back-burner')");assert get(p,'schedule()')==schedule and get(p,'associated()')==associated
 # Returning to rotation is an explicit metadata edit, without queue changes.
 get(p,"status(1,'rotation')");assert get(p,'schedule()')==schedule
 assert get(p,'order()')==['2','12','3','13']
 # Move shared peer past a visible subset; hidden IDs keep their relative order.
 get(p,'move(2,1,[2,3])');assert get(p,'order()')==['3','2','12','13'];assert get(p,"list('Other')").index(12)<get(p,"list('Other')").index(13)
 get(p,'move(13,-1,[12,13])');assert get(p,'order()')==['3','13','2','12'];assert get(p,"list('Meals')").index(3)<get(p,"list('Meals')").index(2)
 get(p,"status(2,'back-burner')");assert get(p,'order()')==['3','13'];get(p,"status(2,'up-next')");assert get(p,'order()')==['3','13','2','12']
 p.reload();assert get(p,'order()')==['3','13','2','12'];assert get(p,'schedule()')==schedule
 # Manual scheduling is allowed and leaves the chosen status intact.
 get(p,'manual(4)');assert next(m for m in get(p,'records()') if m['id']==4)['rotation'] is False
 assert ['original','Thursday','Meals',4,''] in get(p,'schedule()')
 # Pending individual status dialog + editor Cancel/Save.
 get(p,'editor(3)');button=p.locator('#recipeStatus');assert button.inner_text()=='Up Next';button.tap()
 d=p.get_by_role('dialog',name='Recipe status',exact=True);d.get_by_role('radio',name='Back Burner',exact=True).check()
 d.get_by_role('button',name='Confirm recipe status',exact=True).tap();p.locator('#cancel').tap();assert next(m for m in get(p,'records()') if m['id']==3)['recipeStatus']=='up-next'
 # Mixed bulk Keep existing with final cancellation must not write statuses.
 get(p,'select([1,3,4])');before=get(p,'snapshot()');d=p.get_by_role('dialog',name='Edit recipes',exact=True)
 pick(p,d,'Rotation status','Back Burner');assert get(p,'snapshot()')==before
 pick(p,d,'Rotation status','Keep existing');assert d.get_by_role('button',name='Apply to selected recipes',exact=True).is_disabled();assert get(p,'snapshot()')==before
 d.get_by_role('button',name='Cancel bulk edit',exact=True).tap();assert get(p,'snapshot()')==before
 # Reference-only group settings remain pending, block hidden-plan weekday assignments.
 get(p,"groupEdit('Other')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();d.get_by_role('button',name='Save group changes',exact=True).tap();assert 'Remove this group’s weekday assignments before turning off meal rotation.' in d.inner_text();assert 'Tuesday · Lunch' in d.inner_text();d.get_by_role('button',name='Cancel group editing',exact=True).tap();assert get(p,"enabled('Other')")
 get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();d.get_by_role('button',name='Cancel group editing',exact=True).tap();assert get(p,"enabled('Reference')")
 saved_schedule=get(p,'schedule()');get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();d.get_by_role('button',name='Save group changes',exact=True).tap();assert not get(p,"enabled('Reference')");assert get(p,'schedule()')==saved_schedule
 get(p,'groups()');assert p.locator('[data-category="Reference"] [data-recipe-section]').evaluate_all('(xs)=>xs.map(x=>x.dataset.recipeSection)')==['all']
 # Backup contains shared order and group option; old backups still restore legacy false values.
 snapshot=get(p,'snapshot()');core=json.loads(snapshot['mealRotationDataV1']);backup=dict(version=2,**core,storage=snapshot)
 get(p,"status(3,'rotation')");p.evaluate('b=>batch1.restore(b)',backup);p.reload();assert get(p,'order()')==['3','13','2','12'];assert not get(p,"enabled('Reference')");assert get(p,'schedule()')==saved_schedule
 get(p,"groupEdit('Reference')");d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).check();d.get_by_role('button',name='Save group changes',exact=True).tap();assert get(p,"enabled('Reference')")
 legacy=copy.deepcopy(backup);legacy['storage'].pop('mealRotationUpNextOrderV1',None);legacy['storage'].pop('mealRotationGroupRotationV1',None)
 for m in legacy['meals']:m.pop('recipeStatus',None)
 legacy['meals'][3]['recipeStatus']='Ideas'
 p.evaluate('b=>batch1.restore(b)',legacy);p.reload();assert get(p,'order()')==[];assert get(p,"pool('Meals')")==[1];assert next(m for m in get(p,'records()') if m['id']==4)['recipeStatus']=='back-burner';p.reload();assert get(p,'order()')==[]
 assert p.evaluate('localStorage.getItem("unrelated-sentinel")')=='keep'
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 assert not errors,errors;c.close();print('PASS',name,'Batch 1 migration, scheduling preservation, shared order, pending editors, reference groups, backups, reload, isolation and runtime',flush=True)
def ui_and_rotation(browser,name):
 c,p,errors,prefix=setup(browser,name)
 p.evaluate('establishDatedFixtureSchedule()');get(p,'seedProgress()')
 # Short touch uses existing meal options, and explicit move arrows do not start selection mode.
 name_button=p.locator('[data-category="Meals"] [data-meal-id="2"] .master-category-meal-name').first
 name_button.tap();assert p.locator('.compact-meal-dialog').count() or p.get_by_role('dialog').count()
 p.keyboard.press('Escape')
 # Use the normal rendering after dismissing the options overlay.
 p.evaluate('document.querySelectorAll(".meal-dialog-overlay,.compact-meal-overlay").forEach(x=>x.remove())')
 # A separate disposable context avoids relying on unrelated popup dismissal selectors.
 c.close();c,p,errors,prefix=setup(browser,name)
 row=p.locator('[data-category="Meals"] [data-meal-id="2"]')
 row.get_by_role('button',name='Move Zulu soon down in Up Next',exact=True).tap()
 assert get(p,'order()')==['3','2','12','13'];assert not p.locator('.recipe-bulk-check').count()
 get(p,'undo()');assert get(p,'order()')==['2','12','3','13']
 # A vertical touch swipe stays a scroll gesture and does not reorder or select recipes.
 row=p.locator('[data-category="Meals"] [data-meal-id="2"]');row.scroll_into_view_if_needed();box=row.locator('.master-category-meal-name').first.bounding_box();client=c.new_cdp_session(p)
 point={'x':box['x']+20,'y':box['y']+10,'id':1};client.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[point]});client.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{**point,'y':point['y']+55}]});client.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});assert get(p,'order()')==['2','12','3','13'] and not p.locator('.recipe-bulk-check').count()

 # Individual editor Save applies the final status, and is repeat-load safe.
 get(p,'editor(3)');p.locator('#recipeStatus').tap();d=p.get_by_role('dialog',name='Recipe status',exact=True)
 d.get_by_role('radio',name='Back Burner',exact=True).check();d.get_by_role('button',name='Confirm recipe status',exact=True).tap()
 assert next(m for m in get(p,'records()') if m['id']==3)['recipeStatus']=='up-next'
 p.locator('#save').tap();assert next(m for m in get(p,'records()') if m['id']==3)['recipeStatus']=='back-burner'
 p.reload();assert next(m for m in get(p,'records()') if m['id']==3)['recipeStatus']=='back-burner'
 # Mixed bulk updates apply only at the existing final confirmation.
 get(p,'groups()');get(p,'select([1,2,4])');d=p.get_by_role('dialog',name='Edit recipes',exact=True)
 before=get(p,'records()');pick(p,d,'Rotation status','Up Next');assert get(p,'records()')==before
 d.get_by_role('button',name='Apply to selected recipes',exact=True).tap()
 assert all(m['recipeStatus']=='up-next' for m in get(p,'records()') if m['id'] in [1,2,4,12])
 # Keep existing preserves mixed statuses while adding memberships, including Up Next position.
 get(p,"status(1,'rotation')");get(p,"status(4,'back-burner')")
 statuses={m['id']:m.get('recipeStatus') for m in get(p,'records()')};order=get(p,'order()')
 get(p,'bulk([1,2,4],{}, {bulkGroups:{sourceGroup:"Meals",add:true,remove:false,groups:["Reference"],newGroups:[]}})')
 assert all(m.get('recipeStatus')==statuses[m['id']] for m in get(p,'records()') if m['id'] in statuses)
 assert [id for id in get(p,'order()') if id in order]==order
 # Source-group restriction is still enforced by the transaction validator.
 before=get(p,'snapshot()')
 try:
  get(p,'bulk([1,13],{status:"rotation"},{bulkGroups:{sourceGroup:"Meals",add:true,remove:false,groups:["Reference"],newGroups:[]}})')
  raise AssertionError('mixed source groups accepted')
 except Exception as error:assert 'Choose valid meal groups' in str(error)
 assert get(p,'snapshot()')==before
 # Reference-only membership does not disable the same recipe in another enabled group.
 get(p,"unassign('Other')");get(p,"status(2,'rotation')");get(p,"groupEdit('Other')")
 d=p.get_by_role('dialog',name='Edit meal group',exact=True);d.get_by_role('checkbox',name='Use for meal rotation',exact=True).uncheck();d.get_by_role('button',name='Save group changes',exact=True).tap()
 assert get(p,"pool('Other')")==[] and 2 in get(p,"pool('Meals')")
 # All non-rotation statuses stay unchanged when scheduled recipes rotate out.
 before={m['id']:(m.get('rotation'),m.get('recipeStatus')) for m in get(p,'records()')}
 get(p,'cycle()');after={m['id']:(m.get('rotation'),m.get('recipeStatus')) for m in get(p,'records()')};assert before==after
 assert all(m['rotation'] for m in get(p,'records()') if m['id'] in get(p,"pool('Meals')"))
 assert not errors,errors;c.close();print('PASS',name,'touch arrows/options, order Undo, editor Save, mixed bulk confirmation/Keep existing/source restriction, membership ordering, multi-group eligibility and cycling statuses',flush=True)

def failed_save(browser,name):
 c,p,errors,prefix=setup(browser,name)
 before=p.evaluate('prefix=>Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith(prefix+"mealRotation")&&!k.endsWith("mealRotationRecoveryJournalV1")).map(k=>[k.slice(prefix.length),localStorage.getItem(k)]))',prefix);records=get(p,'records()');order=get(p,'order()')
 p.evaluate("""()=>{const native=Storage.prototype.setItem;Storage.prototype.setItem=function(key,value){if(key.endsWith('mealRotationUpNextOrderV1'))throw Error('Batch 1 injected order write failure');return native.call(this,key,value)};window.restoreBatch1Writes=()=>{Storage.prototype.setItem=native}}""")
 try:
  get(p,"status(2,'back-burner')");raise AssertionError('write failure accepted')
 except Exception as error:assert 'Batch 1 injected order write failure' in str(error)
 assert get(p,'records()')==records and get(p,'order()')==order
 # The existing persistence controller can retain a pending proposal; underlying saved values remain exact.
 p.evaluate('restoreBatch1Writes()');after=p.evaluate('prefix=>Object.fromEntries(Object.keys(localStorage).filter(k=>k.startsWith(prefix+"mealRotation")&&!k.endsWith("mealRotationRecoveryJournalV1")).map(k=>[k.slice(prefix.length),localStorage.getItem(k)]))',prefix)
 for key,value in before.items():assert after.get(key)==value,(key,after.get(key),value)
 assert not errors,errors;c.close();print('PASS',name,'injected Up Next storage failure rolls back recipe status and shared ordering without changing saved data',flush=True)

def imports(browser,name):
 c,p,errors,prefix=setup(browser,name)
 items=[dict(name='Imported '+label,cat='Meals',ingredients=['1 cup rice'],instructions='Cook rice.',**fields) for label,fields in [('idea',{'rotation':False}),('named idea',{'status':'Ideas'}),('soon',{'recipeStatus':'up-next','rotation':False}),('active',{'rotation':True}),('default',{})]]
 p.evaluate('items=>batch1.importRecords(items)',items)
 p.locator('#recipeImportDialog').get_by_role('button',name='Select all',exact=True).tap()
 p.locator('#recipeImportDialog').get_by_role('button',name='Import recipes',exact=True).tap()
 actual={m['name']:m for m in get(p,'records()') if m['name'].startswith('Imported ')}
 assert actual['Imported idea']['recipeStatus']==actual['Imported named idea']['recipeStatus']=='back-burner'
 assert actual['Imported soon']['recipeStatus']=='up-next' and actual['Imported soon']['rotation'] is False
 assert actual['Imported active']['rotation'] and actual['Imported default']['rotation']
 assert not errors,errors;c.close();print('PASS',name,'legacy false/Ideas recipe imports become Back Burner, saved Up Next/In Rotation survive and unstated import defaults remain intact',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   run(browser,name);ui_and_rotation(browser,name);failed_save(browser,name);imports(browser,name)
  browser.close()
