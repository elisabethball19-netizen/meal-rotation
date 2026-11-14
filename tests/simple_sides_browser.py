"""Simple side defaults, occurrence transactions and existing grocery/scaling paths."""
import json,copy
from playwright.sync_api import sync_playwright
import rotation_task_corrections_browser as t
f=t.f
f.HOOK+='''window.simpleTest={
 seed:()=>{correctionTest.seed();const p=mealPlans[1];p.weekdayCategories.Friday=['Other','Meals'];p.weekdayMealOverrides['Friday::Meals']='1';p.cycleRetainedSlots['Friday::Meals']='1';p.cycleSlotChoices['Friday::Meals']={mealId:'1',parentId:'',substitution:true,retain:true};saveActiveMealPlan();persist();render()},
 menu:()=>{const entry=recipePlanEntries('original').find(e=>e.day==='Tuesday'&&e.cat==='Meals'&&!e.occasional);openTopMealActionMenu(entry.day,entry.cat,entry.meal)},
 open:(planId='original',day='Tuesday',mealId=1)=>{const entry=recipePlanEntries(planId).find(e=>e.day===day&&String(e.meal.id)===String(mealId));if(!entry)throw Error('Missing fixture occurrence');openOccurrenceServeWith(planId,entry)},
 records:()=>JSON.parse(JSON.stringify(meals)),plans:()=>JSON.parse(JSON.stringify(mealPlans)),
 sides:(planId='original',day='Tuesday',mealId=1)=>{const plan=mealPlans.find(p=>p.id===planId),entry=recipePlanEntries(planId).find(e=>e.day===day&&String(e.meal.id)===String(mealId));return entry?simpleSidesForEntry(plan,entry):null},
 grocery:(period='rotation')=>getGroceryContributions(true,period).map(s=>({...s,checked:grocerySourceChecked(s)})),
 futureLunch:()=>{const plan=mealPlans[1],entry=recipePlanEntries(plan.id).find(e=>e.day==='Friday'&&e.meal.id===1),key=rotationOccurrenceKey({...entry,planId:plan.id}),date=parseCookingLocalDate(plan.rotationCalendar.occurrences[key]);date.setDate(date.getDate()+7);plan.rotationCalendar.occurrences[key]=cookingLocalDate(date);plan.rotationCalendar.slots[rotationCalendarSlot(entry)]=cookingLocalDate(date);persist()},
 scaleAt:(planId,day,mealId,value)=>{const entry=recipePlanEntries(planId).find(e=>e.day===day&&String(e.meal.id)===String(mealId)),context=cookingContext(planId,day,entry.cat,entry.meal,entry.linkedTo);openRecipeViewer(entry.meal,context);setViewedRecipeScale(value);closeRecipeViewer();renderList()},
 removeParent:()=>applyRecipeBulk(['1'],{delete:true}),
 preview:()=>{showTop=true;groceryTabActive=false;allMealsActive=false;rotationWeekOffset=1;render()},
 shoppingEdit:()=>{const line=[...getMasterGroceryItems().values()].find(line=>line.contributions.some(source=>source.simpleSideName==='Peas'&&source.original==='1 cup peas'));openGroceryTextEditor(line,()=>{})},
 shoppingText:()=>[...getMasterGroceryItems().values()].filter(line=>line.contributions.some(source=>source.simpleSideName==='Peas'&&source.original==='1 cup peas')).map(groceryDisplayText),
 scale:value=>{const entry=recipePlanEntries('original').find(e=>e.day==='Tuesday'&&e.cat==='Meals'&&!e.occasional),context=cookingContext('original',entry.day,entry.cat,entry.meal,entry.linkedTo);openRecipeViewer(entry.meal,context);setViewedRecipeScale(value);closeRecipeViewer();renderList()},
 check:ids=>{for(const source of getGroceryContributions(true))if(ids.includes(source.id)){groceryOccurrenceChecks.checks[source.id]=true;if(source.quantity)(groceryOccurrenceChecks.quantities??={})[source.id]={...source.quantity}}saveGroceryOccurrenceChecks()},
 manual:()=>{const meal=meals.find(m=>m.id===1);applyManualWeekdayMeal('Thursday','Meals',meal)},
 defaults:()=>{for(const meal of meals)if(meal.rotation)assignSharedRecipeFields(meal,{simpleSides:[{id:'default-'+meal.id,name:'Default '+meal.id,ingredients:[{id:'ingredient-'+meal.id,text:'1 cup peas'}]}]});persist()},
 cycle:()=>moveDisplayedMealsToBottom(new Set([weekdaySlotKey('Tuesday','Meals')]),false,false),
 back:()=>rotateAllBack(),
 undo:()=>document.getElementById('undo').click(),
 redo:()=>document.getElementById('redo').click(),
 backup:()=>recipeBulkBackupAPI.capture(),restore:storage=>{recipeBulkBackupAPI.restore(storage);backupRestoreReloadPending=true},
 legacy:()=>{for(const meal of meals)delete meal.simpleSides;for(const plan of mealPlans)delete plan.simpleSideOccurrences;persist();render()},
 setLegacy:()=>{meals.find(m=>m.id===1).serveWith=['Rice','Vegetables'];persist()},
 fail:()=>{const original=Storage.prototype.setItem;let thrown=false;Storage.prototype.setItem=function(key,value){if(key.endsWith('mealRotationDataV1')&&!thrown){thrown=true;throw Error('injected side write failure')}return original.call(this,key,value)};window.restoreSimpleWrites=()=>{Storage.prototype.setItem=original}},
 pinLayout:()=>{meals.find(m=>m.id===3).name='Roasted vegetables with chickpeas and lemon tahini dressing';meals.find(m=>m.id===3).prep='10';meals.find(m=>m.id===3).lastCooked='2020-01-01T12:00:00Z';timeDisplayPrefs.category.cooking=true;showLastCooked=true;renderList()},
 my:()=>{allMealsActive=false;groceryTabActive=false;showTop=true;renderList()},
 overview:()=>{allMealsActive=true;showTop=true;renderList()},
 snapshot:()=>JSON.stringify({meals,mealPlans,checks:groceryOccurrenceChecks,sessions:cookingSessions,scales:occurrenceScales}),
 upcoming:()=>previewNextWeekPlans().flatMap(s=>s.entries.map(e=>({planId:s.plan.id,day:e.day,id:e.meal.id,sides:simpleSidesForEntry(s.plan,e)})))
};'''
def setup(b,name):
 c,p,e,prefix=t.setup(b,name);p.evaluate('simpleTest.seed()');return c,p,e,prefix

def outer(p,day='Tuesday'):return p.get_by_role('dialog',name='Serve with for '+day,exact=True)
def add(p,name,ingredients='',choice='This time only',where=None):
 if where is None:where=outer(p)
 where.get_by_role('button',name='Add simple side',exact=True).tap();d=p.get_by_role('dialog',name='Add simple side',exact=True);d.get_by_role('textbox',name='Side name',exact=True).fill(name);d.get_by_role('textbox',name='Side ingredients (optional)',exact=True).fill(ingredients);d.get_by_role('button',name='Confirm side',exact=True).tap()
 if choice:
  prompt=p.get_by_role('dialog',name='Always serve '+name.strip()+' with Active?',exact=True);prompt.get_by_role('button',name=choice,exact=True).tap()
 return d

def save(p):outer(p).get_by_role('button',name='Save Serve with',exact=True).tap()
def sides(p,plan='original',day='Tuesday',meal=1):return p.evaluate('([plan,day,meal])=>simpleTest.sides(plan,day,meal)',[plan,day,meal])
def sources(p,period='rotation'):return p.evaluate('period=>simpleTest.grocery(period)',period)
def side_sources(p,period='rotation'):return [s for s in sources(p,period) if s.get('simpleSideId')]
def record(p,id=1):return next(m for m in p.evaluate('simpleTest.records()') if m['id']==id)

def occurrence_flows(b,name):
 c,p,e,prefix=setup(b,name);p.evaluate('simpleTest.setLegacy()');legacy=copy.deepcopy(record(p)['serveWith']);before=p.evaluate('simpleTest.snapshot()');p.evaluate('simpleTest.menu()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Serve with',exact=True).tap();d=outer(p)
 d.get_by_role('button',name='Add simple side',exact=True).tap();editor=p.get_by_role('dialog',name='Add simple side',exact=True);editor.get_by_role('button',name='Confirm side',exact=True).tap();assert 'Enter a side name' in editor.inner_text();editor.get_by_role('textbox',name='Side name',exact=True).fill('  Salad  ');editor.get_by_role('textbox',name='Side ingredients (optional)',exact=True).fill('1 cup lettuce');editor.get_by_role('button',name='Confirm side',exact=True).tap();prompt=p.get_by_role('dialog',name='Always serve Salad with Active?',exact=True);prompt.get_by_role('button',name='Back to side editor',exact=True).tap();assert editor.get_by_role('textbox',name='Side name',exact=True).input_value()=='  Salad  ' and editor.get_by_role('textbox',name='Side ingredients (optional)',exact=True).input_value()=='1 cup lettuce';editor.get_by_role('button',name='Confirm side',exact=True).tap();p.get_by_role('button',name='Always',exact=True).tap();assert p.evaluate('simpleTest.snapshot()')==before;d.get_by_role('button',name='Cancel Serve with',exact=True).last.tap();assert p.evaluate('simpleTest.snapshot()')==before
 p.evaluate('simpleTest.open()');add(p,'Bread',choice='This time only');save(p);assert [s['name'] for s in sides(p)]==['Bread'] and not side_sources(p);assert not record(p).get('simpleSides');assert not sides(p,'lunch','Friday')
 p.evaluate('simpleTest.open()');add(p,'  Salad  ','1 cup lettuce\n2 carrots',choice='Always');save(p);assert [s['name'] for s in sides(p)]==['Bread','Salad'];assert record(p)['simpleSides'][0]['name']=='Salad';assert not sides(p,'lunch','Friday');assert record(p)['serveWith']==legacy and record(p)['linkedMealIds']==[8]
 defaults=copy.deepcopy(record(p)['simpleSides']);p.evaluate('simpleTest.open()');add(p,'Salad','3 carrots',choice='Always');save(p);assert len(record(p)['simpleSides'])==1 and record(p)['simpleSides'][0]['id']==defaults[0]['id'];assert len(sides(p))==2
 p.reload();assert len(sides(p))==2 and not sides(p,'lunch','Friday');assert record(p)['serveWith']==legacy
 assert p.locator('#list .simple-side-names').first.inner_text()=='Bread · Salad';assert p.locator('#list .top-inline-linked').filter(has_text='Linked side').count();assert not p.locator('.simple-side-names button').count()
 p.evaluate('simpleTest.open()');d=outer(p);d.get_by_role('button',name='Edit simple side Salad',exact=True).tap();edit=p.get_by_role('dialog',name='Edit simple side',exact=True);edit.get_by_role('textbox',name='Side name',exact=True).fill('Long crisp seasonal vegetable salad with lemon dressing');edit.get_by_role('button',name='Confirm side',exact=True).tap();save(p);assert record(p)['simpleSides'][0]['name']=='Salad';assert not sides(p,'lunch','Friday');assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert p.locator('#list .simple-side-names').evaluate_all('(nodes)=>nodes.every(node=>{const range=document.createRange();range.selectNodeContents(node);return [...range.getClientRects()].every(rect=>rect.right<=innerWidth-58)})');p.screenshot(path='/tmp/simple-side-names-'+name+'.png')
 p.evaluate('simpleTest.overview()');assert p.locator('.simple-side-names').filter(has_text='Long crisp seasonal').count();p.evaluate('simpleTest.my()');p.evaluate('simpleTest.menu()');p.get_by_role('dialog',name='Meal options for Tuesday',exact=True).get_by_role('button',name='Serve with',exact=True).tap();d=outer(p)
 for side in list(sides(p)):d.get_by_role('button',name='Remove simple side '+side['name'],exact=True).tap()
 save(p);p.reload();assert sides(p)==[] and record(p)['simpleSides'] and not side_sources(p)
 assert not e,e
 if prefix:assert p.evaluate("localStorage.getItem('mealRotationDataV1')")=='WORKING SENTINEL'
 c.close();print('PASS',name,'blank validation, scope X/draft, outer cancel, named-only, Always/This time, duplicate defaults, occurrence edits/remove-all/reload, legacy and linked sides',flush=True)

def groceries_scaling(b,name):
 c,p,e,prefix=setup(b,name);base=sources(p);p.evaluate('ids=>simpleTest.check(ids)',[s['id'] for s in base]);p.evaluate('simpleTest.open()');add(p,'Peas','1 cup peas\n2 carrots');save(p);initial=side_sources(p);assert len(initial)==2 and all(not s['checked'] for s in initial);assert all(s['checked'] for s in sources(p) if not s.get('simpleSideId'))
 p.evaluate('simpleTest.defaults()');defaults=copy.deepcopy(record(p)['simpleSides']);p.evaluate('simpleTest.scale(2)');assert record(p)['simpleSides']==defaults;scaled=side_sources(p);assert any(s['quantity']['lo']==2 and s['original']=='1 cup peas' for s in scaled),scaled;assert all(s['multiplier']==2 and not s.get('ingredientToken') for s in scaled);assert all('Active — Peas'==s['mealName'] for s in scaled)
 p.evaluate('ids=>simpleTest.check(ids)',[s['id'] for s in scaled]);p.evaluate('simpleTest.shoppingEdit()');shopping=p.get_by_role('dialog',name='Edit grocery item',exact=True);shopping.get_by_role('textbox',name='Grocery item',exact=True).fill('Frozen peas for shopping');shopping.get_by_role('button',name='Save grocery item',exact=True).tap();p.evaluate('simpleTest.open()');outer(p).get_by_role('button',name='Edit simple side Peas',exact=True).tap();edit=p.get_by_role('dialog',name='Edit simple side',exact=True);edit.get_by_role('textbox',name='Side ingredients (optional)',exact=True).fill('1 cup peas\n3 carrots\nSalt');edit.get_by_role('button',name='Confirm side',exact=True).tap();save(p);current=side_sources(p);peas=next(s for s in current if 'peas' in s['original']);assert peas['checked'] and peas['id']==next(s for s in scaled if 'peas' in s['original'])['id'];assert all(not s['checked'] for s in current if 'peas' not in s['original']);assert p.evaluate('simpleTest.shoppingText()')==['Frozen peas for shopping']
 assert len(side_sources(p,'current'))==3 and not any(s['simpleSideName']=='Peas' for s in side_sources(p,'next'));expected=copy.deepcopy(current);p.reload();assert side_sources(p)==expected
 backup=p.evaluate('simpleTest.backup()');p.evaluate('simpleTest.open()');outer(p).get_by_role('button',name='Remove simple side Peas',exact=True).tap();save(p);assert not side_sources(p);p.evaluate('simpleTest.undo()');assert side_sources(p)==expected;p.evaluate('simpleTest.redo()');assert not side_sources(p)
 p.evaluate('storage=>simpleTest.restore(storage)',backup);p.reload();assert side_sources(p)==expected
 p.evaluate('simpleTest.cycle()');assert not any(s['simpleSideId']==expected[0]['simpleSideId'] for s in side_sources(p));p.evaluate('simpleTest.undo()');restored=side_sources(p);assert [(s['id'],s['original'],s['checked'],s['scheduledDate']) for s in restored]==[(s['id'],s['original'],s['checked'],s['scheduledDate']) for s in expected]
 assert not e,e;c.close();print('PASS',name,'stable sources, scaled ingredients, no step target, unaffected/new checks, period filtering, reload/backup, remove and rotation Undo/Redo',flush=True)

def recipe_defaults(b,name):
 c,p,e,prefix=setup(b,name);p.evaluate('batch1.editor(2)');p.wait_for_timeout(850);p.locator('[data-editor-section=serve]>summary').tap();area=p.locator('[data-editor-section=serve]');add(p,'Rice','1 cup rice',choice=None,where=area);p.locator('#cancel').tap();assert not record(p,2).get('simpleSides')
 p.evaluate('batch1.editor(2)');p.wait_for_timeout(850);p.locator('[data-editor-section=serve]>summary').tap();add(p,'Rice','1 cup rice',choice=None,where=p.locator('[data-editor-section=serve]'));p.locator('#save').tap();assert record(p,2)['simpleSides']==record(p,12)['simpleSides'];assert not sides(p)
 p.evaluate('simpleTest.defaults()');assert not sides(p) and not sides(p,'lunch','Friday');p.evaluate('simpleTest.cycle()');incoming=next(r for r in p.evaluate('correctionTest.rows()') if r['planId']=='original' and r['day']=='Tuesday' and r['cat']=='Meals');assert sides(p,day='Tuesday',meal=incoming['id'])==record(p,incoming['id']).get('simpleSides',[])
 p.evaluate('simpleTest.undo()');assert not sides(p);p.evaluate('simpleTest.manual()');assert sides(p,day='Thursday')==record(p)['simpleSides'] and not sides(p)
 assert p.evaluate('simpleTest.upcoming()');future_sources=side_sources(p,'next');assert future_sources and all(s['preview'] for s in future_sources);assert not e,e;c.close();print('PASS',name,'recipe-editor final Save/Cancel, shared memberships, defaults only on new manual/rotation/preview occurrences',flush=True)

def editing_and_compatibility(b,name):
 c,p,e,prefix=setup(b,name);count=len(p.evaluate('simpleTest.records()'));old=p.evaluate('simpleTest.backup()');p.evaluate('simpleTest.open()');add(p,'Pending sauce','1 tbsp oil',choice='Always');outer(p).get_by_role('button',name='Remove simple side Pending sauce',exact=True).tap();save(p);assert not record(p).get('simpleSides') and not sides(p)
 p.evaluate('simpleTest.open()');add(p,'Salad','1 cup lettuce',choice='Always');save(p);snapshot=copy.deepcopy(sides(p));sources_before=side_sources(p);p.evaluate('ids=>simpleTest.check(ids)',[s['id'] for s in sources_before]);defaults=copy.deepcopy(record(p)['simpleSides']);p.evaluate('batch1.editor(1)');p.wait_for_timeout(850);p.locator('[data-editor-section=serve]>summary').tap();p.get_by_role('button',name='Edit simple side Salad',exact=True).tap();edit=p.get_by_role('dialog',name='Edit simple side',exact=True);edit.get_by_role('textbox',name='Side name',exact=True).fill('Default slaw');edit.get_by_role('textbox',name='Side ingredients (optional)',exact=True).fill('2 cups cabbage');edit.get_by_role('button',name='Confirm side',exact=True).tap();p.locator('#save').tap();assert record(p)['simpleSides'][0]['name']=='Default slaw' and sides(p)==snapshot and not sides(p,'lunch','Friday');assert all(s['checked'] for s in side_sources(p))
 p.evaluate('simpleTest.manual()');assert sides(p,day='Thursday')[0]['name']=='Default slaw';p.reload();assert sides(p)==snapshot and sides(p,day='Thursday')[0]['name']=='Default slaw';assert len(p.evaluate('simpleTest.records()'))==count
 p.evaluate('simpleTest.open()');add(p,'Sauce','1 tbsp oil',choice='Always');before=p.evaluate('simpleTest.snapshot()');p.evaluate('simpleTest.fail()');save(p);assert 'could not be saved' in outer(p).inner_text().lower();assert p.evaluate('simpleTest.snapshot()')==before;p.evaluate('restoreSimpleWrites()');save(p);assert not outer(p).count() and any(side['name']=='Sauce' for side in sides(p))
 p.evaluate('storage=>simpleTest.restore(storage)',old);p.reload();assert not any('simpleSides' in meal for meal in p.evaluate('simpleTest.records()'));assert not any('simpleSideOccurrences' in plan for plan in p.evaluate('simpleTest.plans()'));assert not side_sources(p);assert not e,e;c.close();print('PASS',name,'pending Always removal, default edits preserve existing occurrences/checks, no recipe records, failed-write rollback/retry and old backup without sides',flush=True)

def pin_layout(b,name):
 c,p,e,prefix=f.setup(b,name,320);p.evaluate('simpleTest.pinLayout()');rows=p.locator('.master-category-meal[data-up-next-star]');heights=rows.evaluate_all('(xs)=>xs.map(e=>e.getBoundingClientRect().height)');baseline=p.add_style_tag(content='.master-category-meal[data-up-next-star]:not(.meal-card-edit-mode)>.recipe-up-next-star{align-self:start!important;place-items:start center!important;padding:4px 0 0!important}');assert rows.evaluate_all('(xs)=>xs.map(e=>e.getBoundingClientRect().height)')==heights;baseline.evaluate('(e)=>e.remove()');assert rows.evaluate_all('(xs)=>xs.every(row=>{const icon=row.querySelector(".recipe-up-next-star svg").getBoundingClientRect(),text=row.querySelector(".master-meal-info").getBoundingClientRect();return Math.abs((icon.top+icon.bottom-text.top-text.bottom)/2)<2})');p.screenshot(path='/tmp/simple-side-pin-centering-'+name+'.png');f.touch_drag(p,c,f.row(p,2),f.row(p,3));assert f.get(p,'order()')[:2]==['3','2'];assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not e,e;c.close();print('PASS',name,'pin/text block centers, unchanged row heights with wrapping/metadata and touch dragging',flush=True)

def lifecycle_and_weeks(b,name):
 c,p,e,prefix=setup(b,name);p.evaluate('simpleTest.open()');add(p,'Tuesday peas','1 cup peas');save(p);original=side_sources(p);p.evaluate('ids=>simpleTest.check(ids)',[s['id'] for s in original]);p.evaluate('simpleTest.cycle()');assert not any(s['simpleSideName']=='Tuesday peas' for s in side_sources(p));p.evaluate('simpleTest.back()');restored=side_sources(p);assert [(s['id'],s['checked']) for s in restored]==[(s['id'],True) for s in original]
 p.evaluate('simpleTest.removeParent()');assert not any(s['mealId']==1 for s in side_sources(p));p.evaluate('simpleTest.undo()');assert [(s['id'],s['checked']) for s in side_sources(p)]==[(s['id'],s['checked']) for s in restored];p.evaluate('simpleTest.redo()');assert not side_sources(p);p.evaluate('simpleTest.undo()')
 p.evaluate('simpleTest.futureLunch()');p.evaluate('simpleTest.defaults()');assert not sides(p,'lunch','Friday');assert not any(s['mealId']==1 and s['planId']=='lunch' and s['day']=='Friday' for s in side_sources(p,'next'));p.evaluate('simpleTest.open("lunch","Friday",1)');add(p,'Friday beans','1 cup beans',where=outer(p,'Friday'));outer(p,'Friday').get_by_role('button',name='Save Serve with',exact=True).tap();p.evaluate('simpleTest.scaleAt("lunch","Friday",1,2)');next_sources=side_sources(p,'next');assert any(s['simpleSideName']=='Friday beans' and s['multiplier']==2 for s in next_sources);assert not any(s['simpleSideName']=='Tuesday peas' for s in next_sources);both=side_sources(p,'both');assert len({s['id'] for s in both})==len(both);assert any(s['simpleSideName']=='Tuesday peas' and s['multiplier']==1 for s in both)
 p.evaluate('simpleTest.preview()');button=p.locator('.all-meals-day .mealname').first;t.hold(p,button);d=p.get_by_role('dialog',name='Next week meal options',exact=True);assert d.count() and not d.get_by_role('button',name='Serve with',exact=True).count();d.get_by_role('button',name='Close',exact=True).tap();assert not e,e;c.close();print('PASS',name,'Cycle Back, parent removal Undo/Redo, actual future side scale/week isolation, both-week deduplication and read-only generated preview',flush=True)

if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   occurrence_flows(b,name);groceries_scaling(b,name);recipe_defaults(b,name);editing_and_compatibility(b,name);pin_layout(b,name);lifecycle_and_weeks(b,name)
  b.close()
