"""Opt-in disposable interaction profile. No production instrumentation or private data."""
import argparse,json,subprocess
from pathlib import Path
from datetime import datetime,timezone
from playwright.sync_api import sync_playwright
import batch1_ideas_browser as f
ROOT=Path(__file__).resolve().parents[1]
HOOK=r'''
window.appPerf={seed:()=>{
 const side=builtinSidesGroup();cats=['Meals',side,'Veggies'];active='Meals';for(const cat of cats)groupIdentity(cat,true);
 meals=Array.from({length:180},(_,i)=>{const cat=i<100?'Meals':i<140?side:'Veggies';return {id:i+1,name:(cat===side?(i%2?'Rice pilaf ':'Potato mash '):cat+' recipe ')+(i+1),cat,rotation:i<60||i>=100&&i<130||i>=140&&i<170,upNextStar:false,ingredients:Array.from({length:12},(_,j)=>'1 cup '+(j<2?'pantry '+j:'recipe '+(i+1)+' ingredient '+j)),instructions:[{type:'step',text:'Cook ingredients.'}],notes:'Fixture notes '+i,makeAheadTasks:[{id:'prep',description:'Prepare ingredients',daysBefore:0}],...(cat==='Meals'&&i%3===0?{serveWith:['Rice']}:{}),...(cat==='Meals'&&i%5===0?{simpleSides:[{id:'simple-'+i,name:'Salad',ingredients:[{id:'simple-ing-'+i,text:'1 cup lettuce'}]}]}:{})}});
 for(let i=0;i<20;i++){meals[i].linkGroup='shared-'+i;meals.push({...JSON.parse(JSON.stringify(meals[i])),id:1000+i,cat:'Veggies'})}id=1100;
 meals[0].linkedMealIds=[102];
 mealPlans=['original','lunch','breakfast'].map((id,index)=>({id,name:['Dinner','Lunch','Breakfast'][index],weekdayCategories:Object.fromEntries(weekdays.map(day=>[day,[...cats]])),weekdayMealOverrides:Object.fromEntries(weekdays.flatMap((day,i)=>[[day+'::Meals',String(1+index*7+i)],[day+'::Veggies',String(141+index*7+i)]])),weekdayRecipeFilters:{},pinnedCats:[],cycleSlotChoices:{},cycleRetainedSlots:{}}));
 for(const p of mealPlans)for(const [key,mealId]of Object.entries(p.weekdayMealOverrides)){p.cycleRetainedSlots[key]=mealId;p.cycleSlotChoices[key]={mealId,parentId:'',retain:true,substitution:true}}
 activePlanId='original';weekdayCategories=JSON.parse(JSON.stringify(mealPlans[0].weekdayCategories));weekdayMealOverrides={...mealPlans[0].weekdayMealOverrides};weekdayRecipeFilters={};showMealPlanTabs=true;makeAheadDisplayPrefs.showMakeAheadReminders=true;makeAheadDisplayPrefs.showCompletedToday=true;
 cookingSessions={version:1,occurrences:{}};occurrenceScales={version:1,occurrences:{}};groceryOccurrenceChecks={version:1,checks:{},quantities:{}};checkedIngredients=new Set();
 localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(Object.fromEntries(meals.map(m=>[m.id,m.ingredients]))));localStorage.setItem('mealRotationShowPlanTabsV1','true');saveManualGroceryItems([{id:'manual-keep',text:'Manual milk',checked:true}]);localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify({'keep-edit':'Market onions'}));
 saveActiveMealPlan();persist();for(const p of mealPlans){const entries=scheduledCalendarEntries(p),cal=rotationCalendarForPlan(p,entries),start=cookingPlanningWeekStart();for(const entry of entries){const key=rotationOccurrenceKey({...entry,planId:p.id}),date=cookingLocalDate(cookingDateInWeek(entry.day,start));cal.occurrences[key]=date;cal.assignedOn[key]=cookingLocalDate(start);cal.assignedAt[key]=start.toISOString();cal.slots[rotationCalendarSlot(entry)]=date}p.rotationCalendar=cal}
 groceryPeriod='both';localStorage.setItem(GROCERY_PERIOD_KEY,'both');saveActiveMealPlan();persist();showTop=true;groceryTabActive=false;allMealsActive=false;render();
},metrics:()=>({records:meals.length,logicalRecipes:new Set(meals.map(sharedRecipeIdentity)).size,ingredients:meals.reduce((n,m)=>n+m.ingredients.length,0),plans:mealPlans.length,currentOccurrences:mealPlans.reduce((n,p)=>n+recipePlanEntries(p.id).length,0),nextOccurrences:previewNextWeekPlans().reduce((n,s)=>n+s.entries.length,0),grocerySources:getGroceryContributions(true,'both').length,storageBytes:Object.values(captureBackupStorage()).reduce((n,v)=>n+v.length,0)}),
 prepare:kind=>{
  document.querySelectorAll('.compact-meal-dialog').forEach(e=>e.remove());
  if(kind==='pin'){setMasterCategoriesView(true);showTop=false;groceryTabActive=false;allMealsActive=false;active='Meals';masterExpansionInitialized=true;masterExpandedCategories.clear();masterExpandedCategories.add('Meals');setMasterRecipeSectionOpen('Meals','up-next',true);render();return ['[data-up-next-star="90"].recipe-up-next-star','onclick']}
  showTop=true;groceryTabActive=kind==='grocery'||kind==='selectAll';allMealsActive=false;rotationWeekOffset=0;render();
  if(kind==='grocery')return ['.master-grocery-item input[type=checkbox]','onchange'];
  if(kind==='selectAll')return ['[aria-label="Select all groceries"]','onclick'];
  if(kind==='task')return ['#todaysTodo [data-make-ahead-key] input[type=checkbox]','onchange'];
  if(kind==='view')return ['#summary','onclick'];
  if(kind==='dialog'){const button=document.createElement('button');button.id='perfDialog';button.onclick=()=>{const entry=recipePlanEntries(activePlanId).find(e=>e.day==='Tuesday'&&e.cat==='Meals');openTopMealActionMenu(entry.day,entry.cat,entry.meal)};document.body.append(button);return ['#perfDialog','onclick']}
  if(kind==='recipe'){openEditor(2);document.getElementById('name').value+=' x';return ['#save','onclick']}
  if(kind==='side'){const entry=recipePlanEntries(activePlanId).find(e=>e.day==='Tuesday'&&e.cat==='Meals');openOccurrenceServeWith(activePlanId,entry);document.querySelector('.occurrence-side-editor [aria-label="Side name"]').value='Perf garnish';document.querySelector('.occurrence-side-editor [aria-label="Side name"]').dispatchEvent(new Event('input'));return ['.occurrence-side-editor [aria-label="Save sides"]','onclick']}
 },install:(counters=true)=>{
  const stats={};window.perfStats=stats;if(!counters)return;let stack=[];
  const wrap=(name,fn)=>function(...args){let stat=stats[name]||(stats[name]={calls:0,ms:0,self:0}),frame={child:0};stat.calls++;const start=performance.now();stack.push(frame);try{return fn.apply(this,args)}finally{const ms=performance.now()-start;stack.pop();stat.ms+=ms;stat.self+=ms-frame.child;if(stack.length)stack.at(-1).child+=ms}};
  renderList=wrap('renderList',renderList);persist=wrap('persist',persist);saveActiveMealPlan=wrap('savePlan',saveActiveMealPlan);reconcileRotationCalendars=wrap('calendars',reconcileRotationCalendars);stabilizeAutomaticWeekSlots=wrap('stabilize',stabilizeAutomaticWeekSlots);getDisplayedWeekdayMealsForPlan=wrap('schedule',getDisplayedWeekdayMealsForPlan);allocateScheduledWeek=wrap('allocate',allocateScheduledWeek);reconcileAllCookingData=wrap('cooking',reconcileAllCookingData);getGroceryContributions=wrap('groceries',getGroceryContributions);previewNextWeekPlans=wrap('preview',previewNextWeekPlans);captureGroceryCheckStates=wrap('captureChecks',captureGroceryCheckStates);readGroupIdentities=wrap('groupIDs',readGroupIdentities);automaticRecipeCandidates=wrap('candidates',automaticRecipeCandidates);serveWithMatches=wrap('typeMatch',serveWithMatches);
  const get=Storage.prototype.getItem,set=Storage.prototype.setItem;Storage.prototype.getItem=function(k){stats.reads=(stats.reads||0)+1;return get.call(this,k)};Storage.prototype.setItem=function(k,v){stats.writes=(stats.writes||0)+1;stats.writeBytes=(stats.writeBytes||0)+String(v).length;return set.call(this,k,v)};
  
 },measure:async([selector,event])=>{
  window.perfStats||={};for(const key of Object.keys(perfStats))delete perfStats[key];const button=document.querySelector(selector);if(!button)throw Error('Missing '+selector);const t0=performance.now();let mutated=null;const observer=new MutationObserver(()=>{mutated??=performance.now()-t0});observer.observe(document.body,{subtree:true,childList:true,attributes:true,characterData:true});
  if(event==='onchange')button.checked=!button.checked;
  const result=button[event]({target:button,currentTarget:button,preventDefault(){},stopPropagation(){}}),sync=performance.now()-t0;await result;const finish=performance.now()-t0,counts=JSON.parse(JSON.stringify(perfStats));await new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));const paint=performance.now()-t0;observer.disconnect();return {sync,finish,paint,dom:mutated,counts};
 },stable:()=>JSON.stringify({meals,mealPlans,cookingSessions,occurrenceScales,manual:manualGroceryItems(),text:groceryTextOverrides()}),
};'''
f.HOOK+=HOOK

def setup(browser,name,ref=None,throttle=1,counters=True):
 c,p,e,pr=f.setup(browser,name,390);p.set_default_timeout(120000)
 if ref:
  cache={}
  def route(request):
   path=request.request.url.split('http://batch1.test/',1)[-1].split('?')[0]
   if path not in cache:
    try:cache[path]='' if Path(path).suffix not in ['.js','.html','.css','.webmanifest'] else subprocess.check_output(['git','show',ref+':'+path],cwd=ROOT,text=True,stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:cache[path]=''
   body=cache[path]
   if path=='ui.js':body+='\n'+f.HOOK
   if path=='meal-rotation-test.html':body=body.replace('mealPersistence.showRecovery({normalize:normalizeImportedBackup',f.HOOK.replace('localStorage','testStorage')+'\nmealPersistence.showRecovery({normalize:normalizeImportedBackup',1)
   request.fulfill(status=200,body=body,content_type='text/javascript' if path.endswith('.js') else 'text/css' if path.endswith('.css') else 'text/html')
  p.route('http://batch1.test/**',route);p.reload();p.wait_for_function('window.appPerf!==undefined')
 p.clock.set_fixed_time(datetime(2026,11,10,12,tzinfo=timezone.utc));p.evaluate('appPerf.seed()');metrics=p.evaluate('appPerf.metrics()');cdp=c.new_cdp_session(p);cdp.send('Emulation.setCPUThrottlingRate',{'rate':throttle});p.evaluate('appPerf.install',counters);return c,p,e,pr,metrics

if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--ref');parser.add_argument('--kinds',default='pin,grocery,task,view,dialog,recipe,side,selectAll');parser.add_argument('--timing-only',action='store_true');parser.add_argument('--trials',type=int,default=3);parser.add_argument('--cpu',type=int,default=4);parser.add_argument('--app',default='index.html');parser.add_argument('--output',required=True);args=parser.parse_args();out=[]
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox']);c,p,e,pr,metrics=setup(b,args.app,args.ref,args.cpu,not args.timing_only);print(json.dumps({'metrics':metrics,'cpu':args.cpu}),flush=True)
  for kind in args.kinds.split(','):
   for i in range(args.trials):
    selector=p.evaluate('appPerf.prepare',kind);result=p.evaluate('appPerf.measure',selector);out.append({'kind':kind,'trial':i,**result});print(json.dumps(out[-1]),flush=True)
  assert not e,e;c.close();b.close()
 Path(args.output).write_text(json.dumps({'ref':args.ref,'metrics':metrics,'cpu':args.cpu,'results':out},indent=2))
