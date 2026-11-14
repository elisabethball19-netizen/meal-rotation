let groceryPeriod='current';
function groceryPeriodSchedules(period=groceryPeriod){
 const current=mealPlans.map(plan=>({plan,entries:getDisplayedWeekdayMealsForPlan(plan),preview:false}));if(period==='rotation')return current;
 const start=cookingPlanningWeekStart(),next=new Date(start);next.setDate(next.getDate()+7);const end=new Date(next);end.setDate(end.getDate()+7);
 const within=(source,from,to)=>({...source,entries:source.entries.filter(entry=>{const date=scheduledOccurrenceDate({...entry,planId:source.plan.id},source.plan.rotationCalendar);return date>=from&&date<to})});
 const upcoming=period==='next'||period==='both'?previewNextWeekPlans().map(source=>within(source,next,end)):[];
 return (period==='next'?[]:current).concat(upcoming);
}
function getGroceryContributions(allPlans=false,period='rotation'){
 if(period==='rotation')saveActiveMealPlan();let selected={};try{selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')}catch(e){}
 const result=[],observed=new Set(),legacyOwners=new Map();
 for(const {plan,entries,preview}of groceryPeriodSchedules(period)){
  if(!allPlans&&!(showMealPlanTabs&&mealPlans.length>1)&&plan.id!==activePlanId)continue;
  if(!allPlans&&showMealPlanTabs&&mealPlans.length>1&&masterGroceryExcludedPlanIds.has(String(plan.id)))continue;
  const groupRank=entry=>{const raw=plan.weekdayCategories?.[entry.day],groups=Array.isArray(raw)?raw:[raw],index=groups.indexOf(entry.cat);return index<0?groups.length:index};
  for(const entry of [...entries].sort((a,b)=>weekdays.indexOf(a.day)-weekdays.indexOf(b.day)||groupRank(a)-groupRank(b))){const occurrence=groceryOccurrenceIdentity(plan,entry),legacy=JSON.stringify(JSON.parse(occurrence).slice(0,4));if(!legacyOwners.has(legacy))legacyOwners.set(legacy,occurrence)}
  for(const entry of entries){
   const {meal,day,linkedTo}=entry;if(!allPlans&&masterGroceryExcludedMealKeys.has(groceryMealKey(plan,meal)))continue;
   const context=cookingContext(plan.id,day,entry.cat,meal,linkedTo),occurrence=groceryOccurrenceIdentity(plan,entry),scheduledDate=cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar)),dated=JSON.stringify([...JSON.parse(occurrence),scheduledDate]);if(observed.has(dated))continue;observed.add(dated);
   const legacyOccurrence=JSON.stringify(JSON.parse(occurrence).slice(0,4));if(!legacyOwners.has(legacyOccurrence))legacyOwners.set(legacyOccurrence,occurrence);const legacyOwner=!preview&&legacyOwners.get(legacyOccurrence)===occurrence;
   const linkedParent=linkedTo??entries.find(parent=>parent.day===day&&parent.cat!==entry.cat&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(meal.id)))?.meal.id;
   const selectedKeys=new Set(grocerySelectionsForMeal(meal,selected).map(ingredientKey)),actualPlan=mealPlans.find(item=>item.id===plan.id),sameDate=actualPlan&&cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},actualPlan.rotationCalendar))===scheduledDate,multiplier=!preview||sameDate?occurrenceMultiplier(context):1,counts=new Map();
   for(const raw of Array.isArray(meal.ingredients)?meal.ingredients:[]){
    const original=String(raw??'').trim(),oldKey=ingredientKey(original);if(!oldKey||!selectedKeys.has(oldKey)||syncIngredientHeading(original))continue;
    const normalized=ingredientKey(compactIngredientFractions(original)),index=counts.get(normalized)||0;counts.set(normalized,index+1);
    const line=scaleRecipeIngredient(original,multiplier),quantity=groceryQuantityParts(line),baseKey=quantity?.key||'unmeasured:'+oldKey;
    result.push({id:JSON.stringify([dated,normalized,index]),occurrence,scheduledDate,preview:!!preview,legacyId:JSON.stringify([occurrence,normalized,index]),legacyIds:[JSON.stringify([occurrence,normalized,index]),JSON.stringify([legacyOccurrence,normalized,index])],legacyOwner,parentId:linkedParent==null?null:String(linkedParent),planId:plan.id,day,cat:entry.cat,mealId:meal.id,mealName:meal.name,original,line,quantity,baseKey,checkKeys:[...new Set([oldKey,original.toLowerCase().replace(/\s+/g,' ').trim()])]});
   }
  }
 }
 return result;
}
function getMasterGroceryItems(){
 const sources=getGroceryContributions(false,groceryPeriod).flatMap(source=>{
  const amount=groceryCheckedAmount(source),q=source.quantity;
  // Ranges stay whole unless both bounds can be split without inventing a range.
  if(!q||!amount||amount.lo<=0||amount.hi<=0||grocerySourceChecked(source)||q.hi-amount.hi<q.lo-amount.lo)return [source];
  return [{...source,quantity:{...q,lo:amount.lo,hi:amount.hi},segmentChecked:true},{...source,quantity:{...q,lo:q.lo-amount.lo,hi:q.hi-amount.hi},segmentChecked:false}];
 }),states=new Map(),groceries=new Map();
 for(const source of sources){if(!states.has(source.baseKey))states.set(source.baseKey,new Set());states.get(source.baseKey).add(grocerySourceChecked(source))}
 for(const source of sources){
  const {line,quantity,baseKey}=source,checked=grocerySourceChecked(source);
  // Reuse the existing quantity/check-group rows, splitting only mixed states.
  const key=states.get(baseKey).size>1?baseKey+'|'+(checked?'checked':'unchecked'):baseKey;
  if(!groceries.has(key))groceries.set(key,{line,recipes:[],checkKeys:[],checkGroups:[],quantity:quantity?{...quantity,lo:0,hi:0}:null,baseKey,contributions:[]});
  const item=groceries.get(key);item.contributions.push(source);
  if(!item.recipes.includes(source.mealName))item.recipes.push(source.mealName);
  if(!item.checkGroups.some(group=>group[0]===source.checkKeys[0]))item.checkGroups.push(source.checkKeys);
  for(const checkKey of source.checkKeys)if(!item.checkKeys.includes(checkKey))item.checkKeys.push(checkKey);
  if(quantity){item.quantity.lo+=quantity.lo;item.quantity.hi+=quantity.hi;const q=item.quantity;const amount=formatRecipeQuantity(q.lo)+(Math.abs(q.hi-q.lo)>1e-8?'–'+formatRecipeQuantity(q.hi):'');const unit=q.unit==='cup'?(q.hi===1?'cup':'cups'):q.unit==='clove'?(q.hi===1?'clove':'cloves'):q.unit==='piece'?(q.hi===1?'piece':'pieces'):q.unit==='sprig'?(q.hi===1?'sprig':'sprigs'):q.unit;item.line=amount+' '+(unit?unit+' ':'')+q.name}
 }
 return groceries;
}
 function addMasterGroceryFloatingButton(){
  if(!(showMealPlanTabs&&mealPlans.length>1))return;
  const button=document.createElement('button');button.type='button';
  button.className='smallbtn add-meal-floating master-grocery-fab'+(groceryTabActive?' active':'');
  button.title=groceryTabActive?'Close master grocery list':'Open master grocery list';
  button.setAttribute('aria-label',button.title);
  button.setAttribute('aria-pressed',String(groceryTabActive));
  button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="9" cy="20" r="1"/><circle cx="19" cy="20" r="1"/><path d="M2 3h2l2.5 12h12L22 7H5"/></svg>';
  button.onclick=()=>navigateAfterSettings(toggleMasterGroceryTab);
  document.body.append(button);
 }
 function addAllMealsFloatingButton(){
  if(!(showMealPlanTabs&&mealPlans.length>1))return;
  const button=document.createElement('button');button.type='button';
  button.className='smallbtn add-meal-floating all-meals-fab'+(allMealsActive?' active':'');
  button.title=allMealsActive?'Close Weekly Overview overview':'Show Weekly Overview across plans';
  button.setAttribute('aria-label',button.title);
  button.setAttribute('aria-pressed',String(allMealsActive));
  // A calendar-grid icon visually distinct from the shopping cart.
  button.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18M8 14h3M14 14h3M8 18h3M14 18h3"/></svg>';
  button.onclick=()=>navigateAfterSettings(()=>{if(!showTop){showTop=true;setMasterCategoriesView(false)}allMealsActive=!allMealsActive;if(allMealsActive)groceryTabActive=false;editId=null;renderList()});
  document.body.append(button);
 }
 function addFloatingViewButtons(){
  // Show all four destinations, highlighting the active view.
  const current=!showTop?'groups':groceryTabActive?'grocery':allMealsActive?'all':'top';
  const destinations=[
   ['top','Home','<path d="M3 10.2 12 3l9 7.2V21h-6.5v-7h-5v7H3z"/>',()=>{showTop=true;groceryTabActive=false;allMealsActive=false;render()}],
   ['groups','Meal Groups','<path d="M4 6h16M4 12h16M4 18h16"/>',()=>openMasterCategories()],
   ['all','Weekly Overview','<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4M17 3v4M3 10h18M8 14h3M14 14h3M8 18h3M14 18h3"/>',()=>{showTop=true;groceryTabActive=false;allMealsActive=true;render()}],
   ['grocery','Grocery List','<circle cx="9" cy="20" r="1"/><circle cx="19" cy="20" r="1"/><path d="M2 3h2l2.5 12h12L22 7H5"/>',()=>{showTop=true;allMealsActive=false;groceryTabActive=true;render()}]
  ];
  const visibleDestinations=destinations.filter(([key])=>key!=='all'||(showMealPlanTabs&&mealPlans.length>1));
  visibleDestinations.forEach(([key,title,art,action],index)=>{
   const b=document.createElement('button');b.type='button';b.className='smallbtn add-meal-floating unified-nav-fab';
   b.title=title;b.setAttribute('aria-label',title);b.dataset.destination=key;
   if(key===current){b.classList.add('current-view');b.setAttribute('aria-current','page');}
   const visibleCount=visibleDestinations.length;
   b.style.bottom='calc('+(14+(visibleCount-1-index)*51)+'px + env(safe-area-inset-bottom,0px))';
   b.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true">'+art+'</svg>';
   b.onclick=()=>navigateAfterSettings(()=>{if(key==='groups'&&tutorialStage==='1')setTutorialStage('2');action();window.scrollTo(0,0);requestAnimationFrame(()=>{window.scrollTo(0,0);document.documentElement.scrollTop=0;document.body.scrollTop=0})});document.body.append(b);
  });
 }
 function renderMasterGroceryTab(list){
  const panel=document.createElement('section');panel.className='meal-plan-grocery';panel.setAttribute('aria-label','Master grocery list');
  const heading=document.createElement('h2');heading.textContent='Grocery List';
  const groceryHeader=document.createElement('div');groceryHeader.className='grocery-compact-header';groceryHeader.append(heading);panel.append(groceryHeader);
  const filters=document.createElement('div');filters.className='master-grocery-plan-filters';
  const periods=document.createElement('div');periods.className='week-selector';periods.setAttribute('role','group');periods.setAttribute('aria-label','Grocery period');
  for(const [value,label]of [['current','This week'],['next','Next week'],['both','Both weeks']]){const button=document.createElement('button');button.type='button';button.textContent=label;button.setAttribute('aria-pressed',String(groceryPeriod===value));button.onclick=()=>{groceryPeriod=value;for(const other of periods.querySelectorAll('button'))other.setAttribute('aria-pressed',String(other===button));updateRows()};periods.append(button)}filters.append(periods);
  const rows=document.createElement('div');rows.className='master-grocery-list';
  function updateRows(){
   rows.replaceChildren();
   const groceries=getMasterGroceryItems();
   if(!groceries.size){
    const msg=document.createElement('p');msg.className='muted';
    msg.textContent=mealPlans.every(plan=>masterGroceryExcludedPlanIds.has(String(plan.id)))?'Select a meal plan to show groceries.':'No selected groceries.';
    rows.append(msg);
   }
   groceries.forEach((line,key)=>{
    if(localStorage.getItem('mealRotationHideCheckedGroceriesV1')==='true'&&groceryItemChecked(key,line))return;
    const row=document.createElement('div');row.className='master-grocery-item';
    const check=document.createElement('input');check.type='checkbox';check.checked=groceryItemChecked(key,line);
    check.onchange=()=>{
     setGroceryItemChecked(key,line,check.checked);
     try{localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]))}catch(e){}
     // Refresh the grocery rows after each selection so the hide-selected
     // preference is applied immediately, without leaving a stale checked row.
     updateRows();
    };
    const details=document.createElement('span');details.className='grocery-item-details';
    const name=document.createElement('button');name.type='button';name.className='grocery-ingredient-name';
    name.textContent=line.line;
    const source=document.createElement('span');source.className='grocery-recipe-source';
    const associations=new Map();for(const contribution of line.contributions||[]){const key=JSON.stringify([contribution.planId,contribution.day,String(contribution.mealId),contribution.occurrence]);if(!associations.has(key))associations.set(key,contribution)}
    if(!associations.size)source.textContent='No associated recipes';
    for(const contribution of associations.values()){
     if(source.childNodes.length)source.append(document.createTextNode(' · '));const link=document.createElement('button');link.type='button';link.className='grocery-recipe-link';link.dataset.mealId=String(contribution.mealId);link.dataset.planId=contribution.planId;link.dataset.day=contribution.day;link.style.cssText='border:0;background:transparent;color:inherit;text-decoration:underline;padding:5px 2px;min-height:44px;text-align:left;font:inherit';link.textContent=contribution.mealName+' ('+mealPlans.find(p=>p.id===contribution.planId)?.name+', '+contribution.day+', '+contribution.cat+')';
     link.textContent+=' · '+contribution.scheduledDate;
     link.onclick=()=>{const plan=mealPlans.find(p=>p.id===contribution.planId),entry=plan&&getDisplayedWeekdayMealsForPlan(plan).find(entry=>entry.day===contribution.day&&String(entry.meal.id)===String(contribution.mealId)&&groceryOccurrenceIdentity(plan,entry)===contribution.occurrence&&cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar))===contribution.scheduledDate),meal=entry?.meal||meals.find(meal=>String(meal.id)===String(contribution.mealId));if(!meal||meal.temporaryMeal){showAppMessage('This one-time meal has no saved recipe.');return}openSavedMealRecipe(meal,entry?cookingContext(plan.id,entry.day,entry.cat,meal,entry.linkedTo):null);revealGroceryRecipeIngredient(meal,contribution.original)};source.append(link);
    }
    source.hidden=true;
    name.setAttribute('aria-expanded','false');
    name.setAttribute('aria-label',line.line+'. Tap to show associated recipes');
    name.onclick=()=>{
     source.hidden=!source.hidden;
     name.setAttribute('aria-expanded',String(!source.hidden));
     name.setAttribute('aria-label',line.line+(source.hidden?'. Tap to show associated recipes':'. Tap to hide associated recipes'));
    };
    details.append(name,source);
    row.append(check,details);rows.append(row);
   });
  }
  const chooseMeals=document.createElement('button');chooseMeals.type='button';chooseMeals.className='smallbtn grocery-choose-meals';
  chooseMeals.textContent='Choose Meals';chooseMeals.title='Choose which meals contribute ingredients to this grocery list';
  chooseMeals.onclick=()=>{
   saveActiveMealPlan();
   const overlay=document.createElement('div');overlay.className='grocery-meal-dialog-overlay';
   overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10020;display:flex;align-items:center;justify-content:center;padding:16px';
   const box=document.createElement('div');box.setAttribute('role','dialog');box.setAttribute('aria-modal','true');box.setAttribute('aria-label','Choose Meals');
   box.style.cssText='background:#fff;color:#222;border-radius:14px;padding:18px;max-width:520px;width:100%;max-height:82vh;display:flex;flex-direction:column;box-shadow:0 8px 30px #0004';
   const title=document.createElement('h3');title.textContent='Choose Meals';title.style.margin='0 0 6px';box.append(title);
   const hint=document.createElement('p');hint.textContent='Choose which meals to include in your grocery list. Your meal rotation will not change.';hint.style.cssText='font-size:14px;color:#666;margin:0 0 12px';box.append(hint);
   const body=document.createElement('div');body.style.cssText='overflow-y:auto;min-height:0;flex:1';
   const schedules=groceryPeriodSchedules();
   const excludedPlans=new Set(masterGroceryExcludedPlanIds),excludedMeals=new Set(masterGroceryExcludedMealKeys);
   for(const plan of (showMealPlanTabs&&mealPlans.length>1?mealPlans:mealPlans.filter(p=>p.id===activePlanId))){
    const section=document.createElement('section');section.style.cssText='border-top:1px solid #ddd;padding:12px 0';
    const header=document.createElement('label');header.style.cssText='display:flex;align-items:center;gap:10px;font-weight:700;margin-bottom:8px';
    const planCheck=document.createElement('input');planCheck.type='checkbox';planCheck.checked=!excludedPlans.has(String(plan.id));planCheck.style.cssText='width:20px;height:20px';
    header.append(planCheck,document.createTextNode(plan.name));if(showMealPlanTabs&&mealPlans.length>1)section.append(header);
    const entries=new Map();for(const source of schedules.filter(source=>source.plan.id===plan.id))for(const entry of source.entries){entries.set(String(entry.meal.id),entry.meal)}
    const mealChecks=[];
    for(const meal of entries.values()){
     const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:10px;padding:7px 2px 7px 22px';
     const cb=document.createElement('input');cb.type='checkbox';cb.style.cssText='width:20px;height:20px;flex:0 0 20px';
     const key=groceryMealKey(plan,meal);cb.checked=!excludedMeals.has(key);cb.disabled=(showMealPlanTabs&&mealPlans.length>1)&&!planCheck.checked;
     cb.onchange=()=>{if(cb.checked)excludedMeals.delete(key);else excludedMeals.add(key)};
     mealChecks.push(cb);label.append(cb,document.createTextNode(meal.name));section.append(label);
    }
    if(!entries.size){const empty=document.createElement('p');empty.textContent='No meals in rotation';empty.className='muted';empty.style.margin='6px 0 6px 22px';section.append(empty)}
    planCheck.onchange=()=>{if(planCheck.checked)excludedPlans.delete(String(plan.id));else excludedPlans.add(String(plan.id));mealChecks.forEach(cb=>cb.disabled=!planCheck.checked)};
    body.append(section);
   }
   box.append(body);
   const footer=document.createElement('div');footer.style.cssText='display:flex;align-items:center;justify-content:center;gap:18px;padding-top:12px';
   const save=document.createElement('button');save.type='button';setIconButton(save,'save','Save meal selections');
   save.onclick=()=>{masterGroceryExcludedPlanIds=excludedPlans;masterGroceryExcludedMealKeys=excludedMeals;saveMasterGroceryPlanExclusions();saveMasterGroceryMealExclusions();overlay.remove();updateRows()};
   const cancel=document.createElement('button');cancel.type='button';setIconButton(cancel,'cancel','Cancel');cancel.onclick=()=>overlay.remove();
   footer.append(save,cancel);box.append(footer);overlay.append(box);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});document.body.append(overlay);
  };
  filters.append(chooseMeals);
  const toolbar=list.querySelector(':scope > .top-controls');
  if(toolbar){filters.append(toolbar);toolbar.classList.add('grocery-inline-actions');}
  groceryHeader.append(filters);
  panel.append(rows);list.append(panel);updateRows();
 }
 function toggleMasterGroceryTab(){
  if(!showTop){showTop=true;setMasterCategoriesView(false);}
  groceryTabActive=!groceryTabActive;groceryTabOpen=groceryTabActive;if(groceryTabActive)allMealsActive=false;
  editId=null;renderList();
 }