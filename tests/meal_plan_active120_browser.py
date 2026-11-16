"""Latest #120 active batch: disposable mixed-date, card, To-Do and viewer flows."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright
import meal_plan_batch120_browser as old
base=old.base
base.HOOK+='''window.active120={
 sameDay:()=>{followup120.badDates();const plan=mealPlans.find(p=>p.id===activePlanId);for(const entry of getDisplayedWeekdayMeals().filter(e=>e.day==='Tuesday')){const key=rotationOccurrenceKey({...entry,planId:plan.id});plan.rotationCalendar.assignedOn[key]='2026-11-10';plan.rotationCalendar.assignedAt[key]='2026-11-10T15:00:00.000Z'}saveActiveMealPlan(false);meals.find(m=>m.id===74).makeAheadTasks=[{id:'tuesday-prep',description:'Prepare Tuesday',daysBefore:1}];const task=scheduledMakeAheadTasks(false).find(t=>t.task.id==='tuesday-prep');plan.makeAheadChecks={...(plan.makeAheadChecks||{}),[task.key]:true};saveActiveMealPlan(false);followup120.seedChecks();},
 guards:()=>{const p=mealPlans.find(p=>p.id===activePlanId),entry=getDisplayedWeekdayMeals().find(e=>e.day==='Tuesday'),key=rotationOccurrenceKey({...entry,planId:p.id}),calendar=p.rotationCalendar,choices=p.cycleSlotChoices;try{p.rotationCalendar=JSON.parse(JSON.stringify(calendar));p.rotationCalendar.assignedOn[key]='2026-11-09';const early=legacyLocalDateRepairs().some(f=>f.key===key);p.rotationCalendar=JSON.parse(JSON.stringify(calendar));p.cycleSlotChoices=JSON.parse(JSON.stringify(choices));p.cycleSlotChoices[weekdaySlotKey(entry.day,entry.cat)].skipReplacement=false;const uncertain=legacyLocalDateRepairs().some(f=>f.key===key);return {early,uncertain}}finally{p.rotationCalendar=calendar;p.cycleSlotChoices=choices}},
 prep:()=>scheduledMakeAheadTasks(false).filter(t=>t.task.id==='tuesday-prep').map(t=>({scheduled:t.scheduled,due:t.due,complete:t.complete})),checks:()=>getGroceryContributions(true).map(s=>[stableGrocerySource(s),grocerySourceChecked(s),groceryCheckedAmount(s),s.multiplier]),
 headers:()=>{showMealPlanTabs=true;rotationWeekOffset=0;active120.home();scrollTo(0,0)},overview:()=>{showTop=true;showMealPlanTabs=true;allMealsActive=true;groceryTabActive=false;renderList({readOnly:true});scrollTo(0,0)},
 stable:()=>JSON.stringify({recipes:meals,scales:occurrenceScales,sessions:cookingSessions,historyDates:meals.map(m=>m.lastCooked)}),
 dates:()=>getDisplayedWeekdayMeals().map(e=>[e.day,cookingLocalDate(scheduledOccurrenceDate({...e,planId:activePlanId},mealPlans.find(p=>p.id===activePlanId).rotationCalendar))]),
 undo:()=>{const v=JSON.parse(history.pop());redoHistory.push(captureHistoryCounterpart(v));restoreState(v)},redo:()=>{const v=JSON.parse(redoHistory.pop());history.push(captureHistoryCounterpart(v));restoreState(v)},
 previewTask:()=>{const first=previewNextWeekPlans().find(s=>s.plan.id===activePlanId).entries.find(e=>e.day==='Tuesday');meals.find(m=>m.id===first.meal.id).makeAheadTasks=[{id:'preview-target',description:'Preview preparation',daysBefore:1}];const item=scheduledMakeAheadTasks().find(t=>t.preview&&t.plan.id===activePlanId&&t.task.id==='preview-target'&&t.entry.day==='Tuesday');navigateToPreparationMeal(item);return {day:item.entry.day,id:String(item.entry.meal.id)}},offset:()=>rotationWeekOffset,linked:()=>openLinkedRecipeTab(meals.find(m=>m.id===8)),prefs:()=>({...recipeViewPrefs}),off:()=>{localStorage.setItem(RECIPE_VIEW_PREFS_KEY,JSON.stringify({syncIngredients:false,autoCompleteIngredients:false}))},
 long:()=>{const m=meals.find(m=>m.id===72);m.ingredients=Array.from({length:25},(_,i)=>'1 cup ingredient '+i);m.instructions=Array.from({length:30},(_,i)=>({type:'step',text:'Step '+(i+1)+' carefully mix and cook the ingredients until tender, then continue with the recipe.'}));m.linkedMealIds=[8];const side=meals.find(m=>m.id===8);side.instructions=Array.from({length:20},(_,i)=>({type:'step',text:'Linked step '+i+' continue cooking.'}));persist()},
 viewer:(mode='full',id=72)=>{for(const session of Object.values(cookingSessions.occurrences))if(session.context.mealId===String(id))session.steps=[];recipeViewPrefs.mode=mode;openSavedMealRecipe(meals.find(m=>m.id===id))},
 scroll:(where)=>{const v=recipeViewer,split=recipeViewingMode()==='split',pane=v.content.querySelector('.recipe-instructions-pane'),node=split?pane:v.cover;node.scrollTop=where==='end'?node.scrollHeight:where==='ingredients'?300:0},
 allDone:()=>{const v=recipeViewer,m=meals.find(m=>String(m.id)===v.mealId),s=v.context?cookingSession(v.context,true):v.previewProgress;s.steps=cookingItemTokens(m).steps.filter(s=>s.token).map(s=>s.token);renderRecipeViewer()},
 debug:()=>{const m=meals.find(m=>String(m.id)===recipeViewer.mealId);return {id:m.id,steps:cookingItemTokens(m).steps.slice(0,2),session:recipeViewer.context?cookingSession(recipeViewer.context):recipeViewer.previewProgress,dom:[...recipeViewer.content.querySelectorAll('.recipe-instructions-pane [data-cooking-token]')].slice(0,2).map(x=>x.dataset.cookingToken)}},viewerState:()=>({id:recipeViewer.mealId,progress:JSON.stringify(recipeViewer.previewProgress),context:recipeViewer.context}),
 task:()=>{followup120.tasks('some');return scheduledMakeAheadTasks().find(t=>t.entry.day==='Sunday'&&t.task.id==='today')},
 taskNav:()=>navigateToPreparationMeal(scheduledMakeAheadTasks().find(t=>t.entry.day==='Sunday'&&t.task.id==='today')),
 preview:()=>{rotationWeekOffset=1;renderList({readOnly:true})},home:()=>{rotationWeekOffset=0;plan120.home()}
};'''
OUT=Path('/workspace/work/screenshots120-active');OUT.mkdir(exist_ok=True)
def shot(p,name,label):p.screenshot(path=str(OUT/(name+'-'+label+'.png')))
def run(b,name):
 c,p,errors,prefix=old.setup_followup(b,name);assert p.evaluate('active120.prefs().syncIngredients')and p.evaluate('active120.prefs().autoCompleteIngredients')
 p.evaluate('active120.sameDay();followup120.ambiguousFuture()');assert p.evaluate('active120.guards()')=={'early':False,'uncertain':False};checks=p.evaluate('active120.checks()');stable=p.evaluate('active120.stable()');before=p.evaluate('active120.dates()');assert ['Tuesday','2026-11-17']in before;assert p.evaluate('active120.prep()')[0]=={'scheduled':'2026-11-17','due':'2026-11-16','complete':True}
 p.evaluate('followup120.repair()');assert ['Tuesday','2026-11-10']in p.evaluate('active120.dates()') and ['Wednesday','2026-11-11']in p.evaluate('active120.dates()') and ['Saturday','2026-11-28']in p.evaluate('active120.dates()');assert p.evaluate('active120.stable()')==stable;assert p.evaluate('active120.checks()')==checks;assert p.evaluate('active120.prep()')[0]=={'scheduled':'2026-11-10','due':'2026-11-09','complete':True}
 p.evaluate('active120.undo()');assert ['Tuesday','2026-11-17']in p.evaluate('active120.dates()');p.evaluate('active120.redo()');assert ['Tuesday','2026-11-10']in p.evaluate('active120.dates()');p.reload();p.evaluate('active120.home()');assert ['Tuesday','2026-11-10']in p.evaluate('active120.dates()')
 # Exactly one stable occurrence open, no sibling swaps on favorite or cancel.
 old.expanded_card(p,'Saturday');old.expanded_card(p,'Sunday');assert p.locator('.plan-card-expanded').count()==1 and old.card(p,'Sunday').locator('.expanded-meal-actions').is_visible()
 shot(p,name,'expanded');p.evaluate('active120.home()');assert old.card(p,'Sunday').locator('.expanded-meal-actions').is_visible()
 old.expanded_card(p,'Wednesday');assert p.locator('.plan-card-expanded').count()==1
 p.evaluate('active120.headers()');shot(p,name,'headers');shot(p,name,'cards');p.locator('.week-selector input[value="1"]').tap();assert p.locator('.week-selector label').evaluate_all('(xs)=>xs.every(x=>getComputedStyle(x).outlineStyle==="none")')
 p.locator('.week-selector input[value="0"]').focus();p.keyboard.press('Tab');shot(p,name,'keyboard-header');p.evaluate('active120.overview()');p.locator('.week-selector input[value="1"]').tap();shot(p,name,'overview-header');assert p.locator('.week-selector label').evaluate_all('(xs)=>xs.every(x=>getComputedStyle(x).outlineStyle==="none")');p.evaluate('active120.home()')
 # Text navigates actual source occurrence; completion only changes checks.
 item=p.evaluate('active120.task()');assert item
 assert p.locator('#todaysTodo').count()==1 and not p.locator('#todaysTodo .make-ahead-due').count()
 before=p.evaluate('active120.stable()');check=p.locator('#todaysTodo .make-ahead-reminder input').first;check.click();assert p.evaluate('active120.stable()')==before;p.evaluate('active120.undo()');p.locator('#todaysTodo .make-ahead-task-link').filter(has_text='Defrost Sunday meal').click();p.wait_for_timeout(150);assert old.card(p,'Sunday').get_attribute('class').find('preparation-meal-target')>=0;shot(p,name,'todo-target');p.wait_for_timeout(1100);assert not p.locator('.preparation-meal-target').count()
 # Preview render still does not mutate core scheduling or groceries.
 raw=p.evaluate('plan120.state()');p.evaluate('active120.preview()');shot(p,name,'preview');p.evaluate('active120.home()');assert p.evaluate('plan120.state()')==raw
 target=p.evaluate('active120.previewTask()');p.wait_for_timeout(100);assert p.evaluate('active120.offset()')==1;assert old.card(p,'Tuesday').get_attribute('data-meal-id')==target['id'];shot(p,name,'preview-task-target');p.evaluate('active120.home();active120.long()')
 for mode in ['full','split']:
  for width,height in [(360,800),(740,360)]:
   p.set_viewport_size({'width':width,'height':height});p.evaluate('mode=>active120.viewer(mode)',mode);p.wait_for_timeout(200);p.evaluate('active120.scroll("end")');p.wait_for_timeout(100)
   shot(p,name,mode+'-'+str(width)+'-debug');jump=p.get_by_role('button',name='Return to unfinished step',exact=True);assert jump.is_visible(),p.evaluate('active120.debug()');box=jump.bounding_box();assert box['y']>=0 and box['y']+box['height']<=height,(mode,box)
   shot(p,name,mode+'-'+str(width)+'-jump');jump.click();p.wait_for_timeout(400)
   if mode=='full':
    p.evaluate('active120.scroll("ingredients")');p.wait_for_timeout(100);assert p.locator('.recipe-current-step:visible').count()==1;shot(p,name,'ingredients-jump-'+str(width))
   if mode=='split' and width==740:
    p.evaluate('active120.linked()');p.wait_for_timeout(200);assert p.evaluate('active120.viewerState().id')=='8';p.evaluate('active120.scroll("end")');p.wait_for_timeout(100);p.get_by_role('button',name='Return to unfinished step',exact=True).click();p.wait_for_timeout(400);first=p.locator('.recipe-instructions-pane .cooking-item').first.bounding_box();pane=p.locator('.recipe-instructions-pane').bounding_box();assert first['y']>=pane['y'] and first['y']<pane['y']+pane['height'],(first,pane,p.evaluate('active120.debug()'));shot(p,name,'linked-step-target')
   p.evaluate('active120.allDone()');p.wait_for_timeout(100);assert not p.locator('.recipe-current-step:visible').count();p.get_by_role('button',name='Close recipe',exact=True).click();p.wait_for_timeout(100)
 # An explicit OFF survives even a legacy preferences object without mode/ratio.
 p.evaluate('active120.off()');p.reload();assert not p.evaluate('active120.prefs().syncIngredients')and not p.evaluate('active120.prefs().autoCompleteIngredients');p.evaluate("active120.viewer('full');active120.linked()");assert not p.evaluate('active120.prefs().syncIngredients')and not p.evaluate('active120.prefs().autoCompleteIngredients');p.get_by_role('button',name='Close recipe',exact=True).click();p.wait_for_timeout(100)
 for width,height in [(320,640),(740,360)]:
  p.set_viewport_size({'width':width,'height':height});p.evaluate("document.body.dataset.mealTextSize='extra';active120.home()");shot(p,name,'layout-'+str(width));assert p.evaluate('document.documentElement.scrollWidth<=innerWidth')
 assert not errors,errors
 if prefix:assert p.evaluate('localStorage.getItem("mealRotationDataV1")')=='WORKING SENTINEL'
 c.close();print('PASS',name,'same-day date repair/Undo, one card, To-Do, headers, contextual jump, explicit OFF and mobile layouts')
if __name__=='__main__':
 with sync_playwright()as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  for name in ['index.html','meal-rotation-test.html']:run(b,name)
  b.close()
