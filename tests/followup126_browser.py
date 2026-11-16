"""Only issue 126's authorized phone follow-up; disposable regular/test origins."""
import json
from pathlib import Path
from datetime import datetime, timezone
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as fixture
fixture.HOOK+='''window.follow126={
 seed:()=>{
 expandedPlanCards.clear();localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,'{}');saveManualGroceryItems([]);restoringRotationCalendars=true;cats=['Rice','Potatoes','Vegetables','Sides'];active='Rice';startWeekday='Tuesday';manualRecipeOrdering=false;
 const names=['Chicken Curry','Chili-Garlic Broth Bowls','Thai Garlic Pork','Thai Red Curry Chicken','Crying Tiger'],dates=['2026-11-10',null,'2026-10-15','2026-10-20','2026-10-27'];meals=names.map((name,i)=>({id:i+1,name,cat:'Rice',rotation:true,recipeStatus:'rotation',ingredients:['1 cup rice','1 lb chicken'],url:'',instructions:[{type:'step',text:'Cook the rice and chicken.'}],groceryDefaultAll:true,...(dates[i]?{lastCooked:dates[i]+'T12:00:00'}:{})}));
 meals.push({id:10,name:'Golden roast potatoes with rosemary and garlic for the whole family',cat:'Potatoes',rotation:true,recipeStatus:'rotation',ingredients:['1 lb potatoes'],groceryDefaultAll:true},{id:11,name:'Creamy mashed potatoes',cat:'Potatoes',rotation:true,recipeStatus:'rotation',ingredients:['2 lb potatoes'],groceryDefaultAll:true},{id:12,name:'Green vegetables',cat:'Vegetables',rotation:true,recipeStatus:'rotation',ingredients:['1 cup peas'],groceryDefaultAll:true,url:''});
 mealPlans=[{id:'original',name:'Dinner',mealPlanWeekStartV1:'2026-11-17',weekdayCategories:{Tuesday:['Rice']},weekdayMealOverrides:{'Tuesday::Rice':'3'},cycleSlotChoices:{'Tuesday::Rice':{mealId:'3',parentId:'',substitution:false}},weekdayRecipeFilters:{},pinnedCats:[]},{id:'hidden',name:'Lunch',mealPlanWeekStartV1:'2026-11-10',weekdayCategories:{Wednesday:['Vegetables']},weekdayMealOverrides:{'Wednesday::Vegetables':'12'},cycleSlotChoices:{'Wednesday::Vegetables':{mealId:'12',parentId:'',retain:true,substitution:true}},weekdayRecipeFilters:{},pinnedCats:[]}];activePlanId='original';weekdayCategories={Tuesday:['Rice']};weekdayMealOverrides={'Tuesday::Rice':'3'};weekdayRecipeFilters={};pinnedCats=[];showMealPlanTabs=false;occurrenceScales={version:1,occurrences:{}};cookingSessions={version:1,occurrences:{}};groceryOccurrenceChecks={version:1,checks:{},quantities:{}};checkedIngredients=new Set();
 for(const p of mealPlans){const entries=getDisplayedWeekdayMealsForPlan(p),calendar=rotationCalendarForPlan(p,entries),anchor=parseCookingLocalDate(p.mealPlanWeekStartV1);calendar.weekStart=p.mealPlanWeekStartV1;for(const e of entries){const key=rotationOccurrenceKey({...e,planId:p.id}),date=cookingLocalDate(cookingDateInWeek(e.day,anchor));calendar.occurrences[key]=date;calendar.assignedOn[key]=date;calendar.assignedAt[key]='2026-11-16T12:00:00.000Z';calendar.slots[rotationCalendarSlot(e)]=date}p.rotationCalendar=calendar}
 for(const m of meals)m.url??='';restoringRotationCalendars=false;saveActiveMealPlan(false);writeOccurrenceScales(occurrenceScales);writeCookingSessions(cookingSessions);saveGroceryOccurrenceChecks();persist();follow126.home();
 },
 state:()=>JSON.stringify({meals,mealPlans,weekdayCategories,weekdayMealOverrides,occurrenceScales,cookingSessions,groceryOccurrenceChecks}),
 home:(week=0)=>{showTop=true;allMealsActive=false;groceryTabActive=false;rotationWeekOffset=week;renderList({readOnly:true})},
 overview:(week=0,tabs=false)=>{showTop=true;allMealsActive=true;groceryTabActive=false;overviewWeekOffset=week;showMealPlanTabs=tabs;renderList({readOnly:true})},
 current:()=>getDisplayedWeekdayMealsForPlan(mealPlans[0]).map(e=>({id:e.meal.id,cat:e.cat,parent:e.linkedTo||'',side:e.servingParentId||'',date:cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},mealPlans[0].rotationCalendar))})),
 next:()=>{const s=previewMealPlanAdvance();return s.entries.map(e=>({id:e.meal.id,cat:e.cat,parent:e.linkedTo||'',date:cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},s.plan.rotationCalendar))}))},
 order:()=>masterRecipeOrder('Rice').map(m=>m.id),pool:()=>automaticRecipeCandidates('Rice',[],meals,mealPlans[0]).map(m=>m.id),
 picker:()=>{const e=getDisplayedWeekdayMeals()[0];openWeekdayMealChooser(e.day,e.cat,e.meal)},
 manual:()=>{weekdayMealOverrides['Tuesday::Rice']='3';mealPlans[0].weekdayMealOverrides={...weekdayMealOverrides};mealPlans[0].cycleSlotChoices['Tuesday::Rice']={mealId:'3',parentId:'',substitution:true,retain:true};follow126.home()},
 rules:()=>{const p=mealPlans[0],parent=getDisplayedWeekdayMealsForPlan(p)[0].meal;parent.serveWithEntriesV1=[{id:'fixed10',type:'fixed',recipeId:'10',always:true},{id:'rotate',type:'rotating',groupIds:[groupIdentity('Vegetables',true),groupIdentity('Potatoes',true)],always:true},{id:'simple',type:'simple',name:'Butter',ingredients:[{id:'butter',text:'1 tbsp butter'}],always:true}];parent.linkedMealIds=[10];parent.simpleSides=[{id:'simple',name:'Butter',ingredients:[{id:'butter',text:'1 tbsp butter'}]}];saveActiveMealPlan();persist();reconcileRotatedGroceryChecks(captureGroceryCheckStates(true),[]);follow126.home()},
 sides:()=>{const p=mealPlans[0],e=getDisplayedWeekdayMealsForPlan(p)[0];return servingSides(p,e,getDisplayedWeekdayMealsForPlan(p))},
 grocery:()=>{showTop=true;allMealsActive=false;groceryTabActive=true;groceryPeriod='both';localStorage.setItem(GROCERY_PERIOD_KEY,'both');renderList({readOnly:true})},
 scale:()=>{const e=getDisplayedWeekdayMealsForPlan(mealPlans[0])[0];openSavedMealRecipe(e.meal,cookingContext(activePlanId,e.day,e.cat,e.meal))},close:()=>closeRecipeViewer(),
 viewer:()=>recipeViewer?{id:recipeViewer.mealId,context:recipeViewer.context}:null,
 staleTask:()=>{follow126.home();const plan=mealPlans[0],entry=getDisplayedWeekdayMealsForPlan(plan)[0],date=n=>{const d=new Date();d.setDate(d.getDate()+n);return cookingLocalDate(d)};renderTodayTodo([{plan,entry,key:JSON.stringify([rotationOccurrenceKey({...entry,planId:plan.id}),date(1),'','future']),task:{id:'future',description:'Future task',daysBefore:0},due:date(-1),scheduled:date(1),complete:false}])},
 legacy:()=>{const p=mealPlans[0];weekdayCategories.Tuesday=['Rice','Potatoes'];p.weekdayCategories={...weekdayCategories};weekdayMealOverrides['Tuesday::Potatoes']='10';p.weekdayMealOverrides={...weekdayMealOverrides};p.cycleSlotChoices['Tuesday::Potatoes']={mealId:'10',parentId:'',substitution:true,retain:true};saveActiveMealPlan();persist();follow126.home()},
 advance:()=>advanceMealPlanWeek(),undo:()=>{const s=JSON.parse(history.pop());redoHistory.push(captureHistoryCounterpart(s));restoreState(s)},redo:()=>{const s=JSON.parse(redoHistory.pop());history.push(captureHistoryCounterpart(s));restoreState(s)},
 editor:()=>openEditor(getDisplayedWeekdayMealsForPlan(mealPlans[0])[0].meal.id,false,captureMealEditorOrigin()),settings:()=>{showTop=true;topSettingsOpen=true;renderMenu()},backup:()=>{const b=recipeBulkBackupAPI.capture();recipeBulkBackupAPI.validate(b);return b}
};'''
OUT=Path('/workspace/work/follow126/screenshots');OUT.mkdir(parents=True,exist_ok=True)
def shot(p,name,label):p.screenshot(path=str(OUT/(name+'-'+label+'.png')),full_page=False)
def run(browser,name):
 c,p,errors,prefix=fixture.setup(browser,name,navigation_timeout=30000)
 p.context.new_cdp_session(p).send('Emulation.setTimezoneOverride',{'timezoneId':'America/Los_Angeles'});p.clock.set_fixed_time(datetime(2026,11,16,20,tzinfo=timezone.utc));p.evaluate('follow126.seed()')
 assert p.evaluate('follow126.current()[0].id')==2,p.evaluate('follow126.current()')
 assert p.evaluate('follow126.next()[0].id')==3,p.evaluate('follow126.next()')
 assert p.evaluate('follow126.order()')==[2,3,4,5,1]
 p.evaluate('follow126.overview()');assert p.locator('.overview-dish[data-meal-id="2"]').count()==1;assert p.locator('.all-meals-day[data-date="2026-11-17"]').count()==1;assert not p.locator('.overview-dish[data-meal-id="12"]').count();shot(p,name,'overview-current')
 p.locator('.overview-dish[data-meal-id="2"] button').click();assert p.evaluate('follow126.viewer().context.mealId')=='2';p.evaluate('follow126.close()');p.wait_for_timeout(150)
 p.evaluate('follow126.overview(1)');assert p.locator('.overview-dish[data-meal-id="3"]').count()==1;p.evaluate('follow126.overview(0,true)');assert p.locator('.overview-dish[data-meal-id="12"]').count()==1
 p.evaluate('follow126.home();follow126.picker()');choices=p.locator('.weekday-meal-picker [data-group="Rice"] .weekday-meal-choice');assert choices.evaluate_all('(xs)=>xs.map(x=>Number(x.dataset.mealId))')==[2,3,4,5,1];assert not p.locator('.weekday-meal-picker').get_by_text('Choose a different meal',exact=True).count();assert not p.locator('.weekday-meal-quick-actions').count();p.get_by_role('button',name='Cancel',exact=True).click();p.wait_for_timeout(400)
 p.evaluate('follow126.manual()');assert p.evaluate('follow126.current()[0].id')==3
 p.evaluate('follow126.seed();follow126.staleTask()');assert not p.locator('#todaysTodo').count()
 # Scale presets/toggles are a coherent draft with visible real switch thumbs.
 p.evaluate('follow126.scale()');before=p.evaluate('follow126.state()');p.get_by_role('button',name='Scale Recipe',exact=True).click();p.get_by_role('button',name='2×',exact=True).click();p.get_by_role('switch',name='Remember',exact=True).check();assert p.evaluate('follow126.state()')==before;assert p.locator('#recipeScaleMenu .preference-switch-thumb').is_visible();shot(p,name,'scale-draft');p.get_by_role('button',name='Cancel recipe scale',exact=True).click();assert p.evaluate('follow126.state()')==before
 p.get_by_role('button',name='Scale Recipe',exact=True).click();assert not p.get_by_role('switch',name='Remember',exact=True).is_checked();p.get_by_role('button',name='2×',exact=True).click();p.get_by_role('button',name='Apply recipe scale',exact=True).click();p.evaluate('follow126.close()');p.wait_for_timeout(150)
 # One shared action layout and inline sides in both weeks; outer cancel is atomic.
 p.evaluate('follow126.seed();follow126.rules()');card=p.locator('.plan-meal-card[data-meal-id="2"]');assert p.locator('.plan-meal-card[data-meal-id="10"]').count()==0;assert card.get_by_text('Butter',exact=True).count()==1
 assert not card.locator('.shared-meal-actions').is_visible();card.locator('.meal-actions-toggle').click();assert card.locator('.shared-meal-actions').is_visible();assert card.locator('.shared-meal-action-grid button').count()==6;shot(p,name,'current-expanded');card.get_by_role('button',name='Add or edit sides',exact=True).click();assert card.get_by_text('Sides',exact=True).count();assert not p.get_by_role('dialog',name='Sides for Chili-Garlic Broth Bowls',exact=True).count();before=p.evaluate('follow126.state()')
 card.get_by_role('button',name='Add side',exact=True).click();p.get_by_role('button',name='Simple side',exact=True).click();card.get_by_role('textbox',name='Side name',exact=True).fill('Rice with a long descriptive label');assert card.get_by_role('switch',name='Always serve this side with Chili-Garlic Broth Bowls?',exact=True).is_visible();shot(p,name,'inline-simple');card.get_by_role('button',name='Cancel all side changes',exact=True).click();after=p.evaluate('follow126.state()');assert after==before,{k:[json.loads(before)[k],json.loads(after)[k]]for k in json.loads(before)if json.loads(before)[k]!=json.loads(after)[k]};p.wait_for_timeout(150)
 # Grouped grocery name and disclosure have separate meanings; contribution pencil is always visible.
 p.evaluate('follow126.grocery()');p.get_by_role('switch',name='Group by meal',exact=True).check();assert p.locator('.grocery-view-control .preference-switch-thumb').is_visible();assert not p.locator('.grocery-meal-section .grocery-expand').count();assert not p.locator('.grocery-meal-section .grocery-recipe-source').count();assert p.locator('.grocery-meal-section .grocery-contribution-edit').first.is_visible();shot(p,name,'groceries-grouped')
 head=p.locator('.grocery-meal-section').first;head.locator('.grocery-meal-heading .iconbtn').click();assert not head.locator('.master-grocery-item').first.is_visible();head.locator('.grocery-meal-title').click();assert p.locator('#recipeViewer').count();p.evaluate('follow126.close()');p.wait_for_timeout(150)
 assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'follow126 dates/Overview inclusion/context, Rice queue/picker/manual guard, due date, scale drafts/thumbs, shared cards/inline sides cancel, grouped groceries',flush=True)
if __name__=='__main__':
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
