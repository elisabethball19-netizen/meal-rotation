# Occurrence UI/lifecycle checks now live in meal_dialog_corrections_browser.py.
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



def recipe_defaults(b,name):
 c,p,e,prefix=setup(b,name);p.evaluate('batch1.editor(2)');p.wait_for_timeout(850);p.locator('[data-editor-section=serve]>summary').tap();area=p.locator('[data-editor-section=serve]');add(p,'Rice','1 cup rice',choice=None,where=area);p.locator('#cancel').tap();assert not record(p,2).get('simpleSides')
 p.evaluate('batch1.editor(2)');p.wait_for_timeout(850);p.locator('[data-editor-section=serve]>summary').tap();add(p,'Rice','1 cup rice',choice=None,where=p.locator('[data-editor-section=serve]'));p.locator('#save').tap();assert record(p,2)['simpleSides']==record(p,12)['simpleSides'];assert not sides(p)
 p.evaluate('simpleTest.defaults()');assert not sides(p) and not sides(p,'lunch','Friday');p.evaluate('simpleTest.cycle()');incoming=next(r for r in p.evaluate('correctionTest.rows()') if r['planId']=='original' and r['day']=='Tuesday' and r['cat']=='Meals');assert sides(p,day='Tuesday',meal=incoming['id'])==record(p,incoming['id']).get('simpleSides',[])
 p.evaluate('simpleTest.undo()');assert not sides(p);p.evaluate('simpleTest.manual()');assert sides(p,day='Thursday')==record(p)['simpleSides'] and not sides(p)
 assert p.evaluate('simpleTest.upcoming()');future_sources=side_sources(p,'next');assert future_sources and all(s['preview'] for s in future_sources);assert not e,e;c.close();print('PASS',name,'recipe-editor final Save/Cancel, shared memberships, defaults only on new manual/rotation/preview occurrences',flush=True)


def pin_layout(b,name):
 c,p,e,prefix=f.setup(b,name,320);p.evaluate('simpleTest.pinLayout()');rows=p.locator('.master-category-meal[data-up-next-star]');heights=rows.evaluate_all('(xs)=>xs.map(e=>e.getBoundingClientRect().height)');baseline=p.add_style_tag(content='.master-category-meal[data-up-next-star]:not(.meal-card-edit-mode)>.recipe-up-next-star{align-self:start!important;place-items:start center!important;padding:4px 0 0!important}');assert rows.evaluate_all('(xs)=>xs.map(e=>e.getBoundingClientRect().height)')==heights;baseline.evaluate('(e)=>e.remove()');assert rows.evaluate_all('(xs)=>xs.every(row=>{const icon=row.querySelector(".recipe-up-next-star svg").getBoundingClientRect(),text=row.querySelector(".master-meal-info").getBoundingClientRect();return Math.abs((icon.top+icon.bottom-text.top-text.bottom)/2)<2})');p.screenshot(path='/tmp/simple-side-pin-centering-'+name+'.png');f.touch_drag(p,c,f.row(p,2),f.row(p,3));assert f.get(p,'order()')[:2]==['3','2'];assert p.evaluate('document.documentElement.scrollWidth<=innerWidth');assert not e,e;c.close();print('PASS',name,'pin/text block centers, unchanged row heights with wrapping/metadata and touch dragging',flush=True)


if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:
   recipe_defaults(b,name);pin_layout(b,name)
  b.close()
