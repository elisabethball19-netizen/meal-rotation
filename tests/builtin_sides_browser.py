"""Built-in Sides migration and occurrence-specific preference saves in disposable apps."""
import json,copy
from pathlib import Path
from playwright.sync_api import sync_playwright
import meal_dialog_corrections_browser as t
t.f.HOOK+='''window.sideBatch={seed:(mode='auto',prefs=[])=>{const side=builtinSidesGroup();for(const [id,name,rotation]of [[101,'Mashed potatoes',true],[102,'Garlic rice',true],[103,'Noodle idea',false]])meals.push({id,name,rotation,recipeStatus:rotation?'rotation':'up-next',upNextStar:!rotation,cat:side,ingredients:['1 cup '+name],makeAheadTasks:[{id:'prep-side',description:'Prepare side',daysBefore:1}],instructions:[]});weekdayCategories.Monday=['Meals',side,'Other'];weekdayMealOverrides['Monday::Other']='14';const plan=mealPlans[0];plan.cycleRetainedSlots['Monday::Other']='14';plan.cycleSlotChoices['Monday::Other']={mealId:'14',parentId:'',substitution:true,retain:true};for(const meal of meals)if(meal.id===6)meal.serveWith=prefs;saveActiveMealPlan();persist();render();if(mode!=='auto'){const e=recipePlanEntries(plan.id).find(e=>e.day==='Monday'&&e.cat===side);if(mode==='manual')applyManualWeekdayMeal(e.day,e.cat,e.meal);else{delete plan.cycleSlotChoices['Monday::'+side].sideSelection;delete plan.cycleSlotChoices['Monday::'+side].substitution;saveActiveMealPlan();persist()}}},rows:()=>dialogTest.rows(),plan:()=>mealPlans[0],record:id=>meals.find(m=>m.id===id),identity:()=>({name:builtinSidesGroup(),ids:readGroupIdentities()}),edit:()=>openEditor(6),prep:values=>preparePreferredSideChanges(meals.find(m=>m.id===6),values)};'''

t.f.HOOK+='''window.sideExtra={
 prefs:()=>sideBatch.record(6).serveWith||[],
 sideMenu:()=>{const entry=recipePlanEntries('original').find(e=>e.day==='Monday'&&isBuiltinSides(e.cat));openTopMealActionMenu(entry.day,entry.cat,entry.meal)},
 morePotatoes:()=>{meals.push({id:104,name:'Roast potatoes',cat:builtinSidesGroup(),rotation:true,recipeStatus:'rotation',upNextStar:false,ingredients:['2 potatoes'],instructions:[]});persist()},
 sideCycle:()=>moveDisplayedMealsToBottom(new Set(['Monday::'+builtinSidesGroup()]),false,false),
 seedExtras:()=>{saveManualGroceryItems([{id:'manual-fixture',text:'Buy milk',checked:true}]);localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify({'existing-shopping-edit':'Market onions'}));for(const item of scheduledMakeAheadTasks(false))if(item.entry.meal.id===14)item.plan.makeAheadChecks={...(item.plan.makeAheadChecks||{}),[item.key]:true};saveActiveMealPlan()},
 tasks:()=>scheduledMakeAheadTasks(false).map(item=>({id:item.entry.meal.id,key:item.key,due:item.due,complete:item.complete})),
 provenance:()=>{const cat=builtinSidesGroup(),entry=recipePlanEntries('original').find(e=>e.day==='Monday'&&e.cat===cat);return entry?builtinSideProvenance(mealPlans[0],entry.day,entry.cat,entry.meal.id):null},
 unassign:()=>{weekdayCategories.Monday=weekdayCategories.Monday.filter(cat=>!isBuiltinSides(cat));saveActiveMealPlan();persist();render()},
 conflict:()=>{meals.find(m=>m.id===14).serveWith=['Potatoes'];persist();render()},
 future:()=>{const plan=mealPlans[0];for(const entry of recipePlanEntries(plan.id).filter(e=>e.day==='Monday')){const key=rotationOccurrenceKey({...entry,planId:plan.id}),date='2026-11-09';plan.rotationCalendar.occurrences[key]=date;plan.rotationCalendar.slots[rotationCalendarSlot(entry)]=date}persist();render()},
 linked:()=>{meals.find(m=>m.id===6).linkedMealIds=[102];meals.find(m=>m.id===6).simpleSides=[{id:'simple-default',name:'Salad',ingredients:[]}];const entry=recipePlanEntries('original').find(e=>e.day==='Monday'&&e.meal.id===6);initializeSimpleSideOccurrence(mealPlans[0],entry);persist();render()},
 progress:()=>{localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(meal=>[String(meal.id),meal.ingredients||[]]))));const entries=recipePlanEntries('original');for(const entry of entries){const context=cookingContext('original',entry.day,entry.cat,entry.meal,entry.linkedTo);cookingSession(context,true).ingredients=[cookingItemTokens(entry.meal).ingredients[0].token]}writeCookingSessions(cookingSessions);simpleTest.scaleAt('original','Monday',101,2);for(const source of getGroceryContributions(true))groceryOccurrenceChecks.checks[source.id]=true;saveGroceryOccurrenceChecks()},
 snapshot:()=>JSON.stringify({meals,mealPlans,cookingSessions,occurrenceScales,groceryOccurrenceChecks}),
 rename:()=>renameCategoryDirect(builtinSidesGroup()),delete:()=>openCategoryDeleteDialog(builtinSidesGroup()),
 ambiguity:()=>{cats.push('sides');localStorage.removeItem(BUILTIN_SIDES_ROLE);persist()},
 backup:()=>recipeBulkBackupAPI.capture(),restore:value=>{recipeBulkBackupAPI.restore(value);backupRestoreReloadPending=true},
 groupOrder:()=>masterOrderedGroups(masterDisplayOrder()),move:()=>{const order=masterOrderedGroups(masterDisplayOrder());order.splice(order.indexOf(builtinSidesGroup()),1);order.unshift(builtinSidesGroup());writeMasterGroupOrder(order);render()},
 migrateAgain:()=>{initializeBuiltinSides();initializeBuiltinSides()},
 records:()=>({cats,meals,plans:mealPlans,identities:readGroupIdentities(),role:localStorage.getItem(BUILTIN_SIDES_ROLE)}),
 redoProgress:()=>{simpleTest.scaleAt('original','Monday',102,3);const entry=recipePlanEntries('original').find(e=>e.day==='Monday'&&e.meal.id===102),context=cookingContext('original',entry.day,entry.cat,entry.meal),session=cookingSession(context,true);session.ingredients=[cookingItemTokens(entry.meal).ingredients[0].token];writeCookingSessions(cookingSessions);const source=getGroceryContributions(true).find(source=>String(source.mealId)==='13');groceryOccurrenceChecks.checks[source.id]=false;if(groceryOccurrenceChecks.quantities)delete groceryOccurrenceChecks.quantities[source.id];saveGroceryOccurrenceChecks();return source.id},
 known:()=>{const plan=mealPlans[0],key='Monday::'+builtinSidesGroup();plan.cycleSlotChoices[key].substitution=false;plan.cycleSlotChoices[key].sideSelection='automatic';persist()}
};'''

def setup(b,name,mode='auto',prefs=None):
 c,p,e,pr=t.setup(b,name);p.evaluate('args=>sideBatch.seed(...args)',[mode,prefs or []]);return c,p,e,pr

def rows(p):return sorted(p.evaluate('sideBatch.rows()'),key=str)
def side(p):
 cat=p.evaluate('sideBatch.identity().name');return next((r for r in rows(p) if r['planId']=='original' and r['day']=='Monday' and r['cat']==cat),None)
def edit(p,add=None,remove=None):
 p.evaluate('sideBatch.edit()');p.clock.run_for(900);p.locator('[data-editor-section=serve]>summary').tap();area=p.locator('[data-editor-section=serve]')
 if remove:area.get_by_role('button',name='Remove Serve with '+remove,exact=True).tap()
 if add:area.get_by_role('button',name=add,exact=True).tap()
 return area

def save(p):p.locator('#save').tap()
def ack(p):p.get_by_role('alertdialog').get_by_role('button',name='OK',exact=True).tap();p.clock.run_for(450)

def automatic_cases(b,name):
 c,p,e,pr=setup(b,name,prefs=['Rice']);assert side(p)['id']==102;assert p.evaluate('sideExtra.provenance()')=='automatic';p.reload();assert side(p)['id']==102 and p.evaluate('sideExtra.provenance()')=='automatic';c.close()
 c,p,e,pr=setup(b,name);assert side(p)['id']==101;p.evaluate('sideExtra.progress()');before=rows(p);snap=p.evaluate('sideExtra.snapshot()');checks=p.evaluate('simpleTest.grocery()');edit(p,'Rice');save(p);assert not p.locator('#name').count(),p.get_by_role('alertdialog').all_text_contents();assert side(p)['id']==102;assert p.evaluate('sideExtra.prefs()')==['Rice'];after=rows(p);assert [r for r in after if r['cat']!='Sides']==[r for r in before if r['cat']!='Sides'];assert side(p)['date']=='2026-11-02';old={x['id']:x for x in checks};new=p.evaluate('simpleTest.grocery()');assert all(x['checked']==(old[x['id']]['checked'] if x['id'] in old else False) for x in new);p.locator('#undo').tap();assert rows(p)==before and p.evaluate('sideExtra.prefs()')==[];assert json.loads(p.evaluate('sideExtra.snapshot()'))['cookingSessions']==json.loads(snap)['cookingSessions'];p.locator('#redo').tap();assert rows(p)==after;edit(p);save(p);assert side(p)['id']==102;edit(p,remove='Rice');save(p);assert side(p)['id']==102;edit(p,'Potatoes');p.locator('#cancel').tap();assert side(p)['id']==102 and p.evaluate('sideExtra.prefs()')==[];p.reload();assert side(p)['id']==102;assert not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('sideExtra.unassign()');edit(p,'Rice');save(p);assert side(p) is None and not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('sideExtra.future()');before=rows(p);edit(p,'Rice');save(p);assert rows(p)==before and side(p)['id']==101;assert not e,e;c.close()
 print('PASS',name,'assigned matching/normal/unassigned, automatic update/retention/repeat save/clear, editor cancel, current-week isolation, checks/progress and Undo/Redo',flush=True)

def manual_cases(b,name):
 for mode in ['manual','unknown']:
  for accept in [False,True]:
   c,p,e,pr=setup(b,name,mode);p.reload();before=rows(p);edit(p,'Rice');save(p);d=p.get_by_role('dialog',name='Replace your selected side for Monday?',exact=True);assert 'Mashed potatoes' in d.inner_text();assert rows(p)==before and p.evaluate('sideExtra.prefs()')==[];d.get_by_role('button',name='Replace selected side' if accept else 'Keep selected side',exact=True).tap();p.clock.run_for(450);assert not p.locator('#name').count(),p.get_by_role('alertdialog').all_text_contents();assert p.evaluate('sideExtra.prefs()')==['Rice'];assert side(p)['id']==(102 if accept else 101);assert p.evaluate('sideExtra.provenance()')==('automatic' if accept else mode);p.reload();assert side(p)['id']==(102 if accept else 101);assert not e,e;c.close()
 print('PASS',name,'manual and legacy-unknown confirmation accept/X, preference save with X, no preconfirmation mutation and reload provenance',flush=True)

def conflict_cases(b,name):
 c,p,e,pr=setup(b,name);before=rows(p);edit(p,'Pasta');save(p);assert 'No matching side' in p.get_by_role('alertdialog').inner_text();ack(p);assert not p.locator('#name').count();assert rows(p)==before and p.evaluate('sideExtra.prefs()')==['Pasta'];assert 'No matching side in rotation.' in p.locator('#list').inner_text();assert not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('sideExtra.conflict()');before=rows(p);edit(p,'Rice');save(p);assert 'Conflicting side preferences' in p.get_by_role('alertdialog').inner_text();ack(p);assert rows(p)==before and p.evaluate('sideExtra.prefs()')==['Rice'];assert not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('sideExtra.linked()');before=rows(p);assert len([r for r in before if r['day']=='Monday' and r['id']==102])==1;edit(p,'Rice');save(p);assert len([r for r in rows(p) if r['day']=='Monday' and r['id']==102])==1;assert p.evaluate('sideBatch.record(6).simpleSides[0].name')=='Salad';assert not e,e;c.close()
 print('PASS',name,'no eligible match and multiple-parent conflict keep existing side with explanation; linked/simple sides retained without duplicates',flush=True)

def identity_cases(b,name):
 c,p,e,pr=setup(b,name);before=p.evaluate('sideExtra.records()');p.evaluate('sideExtra.migrateAgain()');assert p.evaluate('sideExtra.records()')==before;p.evaluate('sideExtra.move()');assert p.evaluate('sideExtra.groupOrder()[0]')=='Sides';identity=p.evaluate('sideBatch.identity().ids.Sides');p.evaluate('sideExtra.rename()');d=p.get_by_role('dialog').filter(has_text='Rename group');d.get_by_role('textbox').fill('Accompaniments');d.get_by_role('button',name='Save',exact=True).tap();p.clock.run_for(450);assert p.evaluate('sideBatch.identity().name')=='Accompaniments';assert p.evaluate('sideExtra.provenance()')=='automatic';edit(p,'Rice');save(p);assert side(p)['id']==102;p.evaluate('sideExtra.delete()');assert 'cannot delete' in p.get_by_role('alertdialog').inner_text();ack(p);backup=p.evaluate('sideExtra.backup()');assert json.loads(backup['mealRotationBuiltinSidesGroupV1'])==identity;p.evaluate('value=>sideExtra.restore(value)',backup);p.reload();assert p.evaluate('sideBatch.identity().name')=='Accompaniments' and side(p)['id']==102;assert p.evaluate('sideBatch.identity().ids.Accompaniments')==identity;assert not e,e;c.close()
 c,p,e,pr=setup(b,name);p.evaluate('sideExtra.ambiguity()');before=p.evaluate('sideExtra.records()');p.reload();p.clock.run_for(450);assert 'Multiple groups' in p.get_by_role('alertdialog').inner_text();after=p.evaluate('sideExtra.records()');assert after['cats']==before['cats'] and after['meals']==before['meals'];assert after['role'] is None;assert not e,e;c.close()
 print('PASS',name,'idempotent migration, identity-preserving rename/reorder, delete guard, backup round-trip and ambiguous names left untouched',flush=True)

def transaction_cases(b,name):
 c,p,e,pr=setup(b,name);p.evaluate('sideExtra.progress()');p.evaluate('sideExtra.seedExtras()')
 before=p.evaluate('sideExtra.backup()');cooked={m['id']:m.get('lastCooked') for m in p.evaluate('simpleTest.records()')};before_rows=rows(p);history=p.evaluate('dialogTest.history()');edit(p,'Rice');p.evaluate('simpleTest.fail()');save(p);assert 'could not be saved' in p.get_by_role('alertdialog').inner_text();assert rows(p)==before_rows and p.evaluate('sideExtra.prefs()')==[];stored=p.evaluate('sideExtra.backup()');assert all(stored[key]==before[key] for key in ['mealRotationPlansV1','mealRotationDataV1']);assert p.evaluate('dialogTest.history()')==history;ack(p);p.evaluate('restoreSimpleWrites()');save(p);assert side(p)['id']==102 and p.evaluate('dialogTest.history()')==history+1;after=p.evaluate('sideExtra.backup()');assert all(m.get('lastCooked')==cooked[m['id']] for m in p.evaluate('simpleTest.records()'));assert all(after[key]==before[key] for key in ['mealRotationManualGroceriesV1','mealRotationGroceryTextOverridesV1']);tasks=p.evaluate('sideExtra.tasks()');assert any(item['id']==102 for item in tasks) and not any(item['id']==101 for item in tasks);assert all(item['complete'] for item in tasks if item['id']==14);unchanged=p.evaluate('sideExtra.redoProgress()');progress=json.loads(p.evaluate('sideExtra.snapshot()'));p.locator('#undo').tap();assert side(p)['id']==101 and p.evaluate('sideExtra.prefs()')==[];assert not next(source for source in p.evaluate('simpleTest.grocery()') if source['id']==unchanged)['checked'];p.locator('#redo').tap();assert side(p)['id']==102;restored=json.loads(p.evaluate('sideExtra.snapshot()'));assert restored['cookingSessions']==progress['cookingSessions'] and restored['occurrenceScales']==progress['occurrenceScales'];assert not next(source for source in p.evaluate('simpleTest.grocery()') if source['id']==unchanged)['checked'];p.evaluate('ids=>simpleTest.check(ids)',[unchanged]);edit(p,remove='Rice');save(p);assert side(p)['id']==102 and p.evaluate('sideExtra.prefs()')==[];p.evaluate('sideExtra.redoProgress()');p.locator('#undo').tap();assert side(p)['id']==102 and p.evaluate('sideExtra.prefs()')==['Rice'];assert not next(source for source in p.evaluate('simpleTest.grocery()') if source['id']==unchanged)['checked'];p.locator('#redo').tap();assert p.evaluate('sideExtra.prefs()')==[];assert not next(source for source in p.evaluate('simpleTest.grocery()') if source['id']==unchanged)['checked'];p.reload();assert side(p)['id']==102 and not e,e;c.close();print('PASS',name,'atomic failed-save rollback/retry, one Undo entry, side tasks only, manual groceries/shopping edits and completed unaffected tasks retained',flush=True)

def automatic_provenance_cases(b,name):
 for action in ['next','cycle']:
  c,p,e,pr=setup(b,name);p.evaluate('sideExtra.morePotatoes()')
  if action=='next':p.evaluate('sideExtra.sideMenu()');p.get_by_role('button',name='Change meal',exact=True).tap();p.locator('.weekday-meal-picker').get_by_role('button',name='Use next recipe',exact=True).tap();p.clock.run_for(450)
  else:p.evaluate('sideExtra.sideCycle()')
  assert side(p)['id']==102 and p.evaluate('sideExtra.provenance()')=='automatic';p.reload();assert p.evaluate('sideExtra.provenance()')=='automatic';edit(p,'Potatoes');save(p);assert not p.get_by_role('dialog',name='Replace your selected side for Monday?',exact=True).count();assert side(p)['id']==104;assert not e,e;c.close()
 print('PASS',name,'Use next and side rotation preserve automatic provenance through reload and preference saves',flush=True)

def migration_cases(b,name):
 for existing in [False,True]:
  prefix='mealRotationTestSandboxV1:' if name.startswith('meal-') else ''
  c=b.new_context(viewport={'width':320,'height':700},is_mobile=True,has_touch=True,service_workers='block');p=c.new_page();errors=[];p.on('pageerror',lambda err:errors.append(str(err)))
  if existing:
   library=[dict(id=1,name='Main',cat='Mains',rotation=True,serveWith=['Rice'],ingredients=['1 onion'],custom={'keep':'parent'}),dict(id=2,name='Potato side',cat='Sides',rotation=True,ingredients=['2 potatoes'],custom={'keep':'side'}),dict(id=3,name='Rice idea',cat='Sides',rotation=False,ingredients=[]),dict(id=4,name='Greens',cat='Veggies',rotation=True,ingredients=['1 cup greens'])]
   plans={'plans':[dict(id='original',name='Dinner',weekdayCategories={'Monday':['Mains','Sides','Veggies']},weekdayMealOverrides={'Monday::Mains':'1','Monday::Sides':'2','Monday::Veggies':'4'},cycleRetainedSlots={'Monday::Sides':'2'},cycleSlotChoices={'Monday::Sides':{'mealId':'2','parentId':'','retain':True,'substitution':True}},pinnedCats=['Veggies'])],'activeId':'original'}
   seed={prefix+'mealRotationDataV1':json.dumps(dict(cats=['Mains','Sides','Veggies'],active='Mains',meals=library)),prefix+'mealRotationPlansV1':json.dumps(plans),prefix+'mealRotationGroupIdentitiesV1':json.dumps({'Sides':'existing-side-id','Mains':'main-id','Veggies':'veg-id'}),prefix+'mealRotationGroupDisplayOrderV1':json.dumps(['Veggies','Sides','Mains'])}
   p.add_init_script('if(!sessionStorage.seeded){for(const[k,v]of Object.entries('+json.dumps(seed)+'))localStorage.setItem(k,v);sessionStorage.seeded="yes"}')
  hook="window.migrationFixture={read:()=>({cats,meals,plans:mealPlans,name:builtinSidesGroup(),id:JSON.parse(localStorage.getItem(BUILTIN_SIDES_ROLE)||'null'),order:masterOrderedGroups(masterDisplayOrder())})};"
  def route(request):
   path=request.request.url.split('http://side-migration.test/',1)[-1].split('?')[0];file=t.f.ROOT/path
   if not file.is_file():request.fulfill(status=404,body='');return
   body=file.read_text() if file.suffix in ['.html','.js','.css','.webmanifest'] else ''
   if path=='ui.js':body+='\n'+hook
   if path=='meal-rotation-test.html':body=body.replace('mealPersistence.showRecovery({normalize:normalizeImportedBackup',hook.replace('localStorage','testStorage')+'\nmealPersistence.showRecovery({normalize:normalizeImportedBackup',1)
   request.fulfill(status=200,body=body,content_type='text/javascript' if file.suffix=='.js' else 'text/css' if file.suffix=='.css' else 'text/html')
  p.route('http://side-migration.test/**',route);p.route('https://**/*',lambda r:r.fulfill(status=200,body=''));p.goto('http://side-migration.test/'+name);p.wait_for_function('window.migrationFixture!==undefined');data=p.evaluate('migrationFixture.read()');assert data['cats'].count('Sides')==1 and data['name']=='Sides' and data['id'];identity=data['id']
  if existing:
   assert data['id']=='existing-side-id' and data['cats']==['Mains','Sides','Veggies'] and data['order']==['Veggies','Sides','Mains'];assert [(m['id'],m['name'],m['cat'],m['ingredients']) for m in data['meals']]==[(m['id'],m['name'],m['cat'],m['ingredients']) for m in library];assert data['plans'][0]['weekdayCategories']==plans['plans'][0]['weekdayCategories'] and data['plans'][0]['pinnedCats']==['Veggies'];assert data['meals'][1]['custom']=={'keep':'side'}
  else:assert not data['meals'] and all(not plan['weekdayCategories'] for plan in data['plans'])
  p.reload();again=p.evaluate('migrationFixture.read()');assert again['id']==identity and again['cats']==data['cats'];assert not errors,errors;c.close()
 print('PASS',name,'fresh empty/unassigned Sides and existing-group identity/memberships/order/assignments/settings migration, no duplication on reload',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:migration_cases(b,name);automatic_cases(b,name);manual_cases(b,name);conflict_cases(b,name);identity_cases(b,name);transaction_cases(b,name);automatic_provenance_cases(b,name)
  b.close()
