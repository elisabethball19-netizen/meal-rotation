const MANUAL_GROCERIES_KEY='mealRotationManualGroceriesV1',GROCERY_PERIOD_KEY='mealRotationGroceryPeriodV1';
function readGroceryPeriod(){
 const raw=localStorage.getItem(GROCERY_PERIOD_KEY);if(raw===null)return 'current';let value=raw;try{value=JSON.parse(raw)}catch(_){}
 if(value&&typeof value==='object'&&typeof value.thisWeek==='boolean'&&typeof value.nextWeek==='boolean')return value.thisWeek?(value.nextWeek?'both':'current'):(value.nextWeek?'next':'none');
 return ({current:'current','this week':'current',next:'next','next week':'next',both:'both','both weeks':'both',none:'none'})[String(value).toLowerCase().trim()]||'current';
}
let groceryPeriod=readGroceryPeriod();
function manualGroceryItems(){const items=JSON.parse(localStorage.getItem(MANUAL_GROCERIES_KEY)||'[]');validateManualGroceryItems(items);return items}
function saveManualGroceryItems(items){validateManualGroceryItems(items);localStorage.setItem(MANUAL_GROCERIES_KEY,JSON.stringify(items))}
function setAllManualGroceries(checked){saveManualGroceryItems(manualGroceryItems().map(item=>({...item,checked})))}
function openManualGroceryEditor(item=null,refresh=()=>renderList()){
 const d=recipeBulkDialog(item?'Edit grocery item':'Add grocery item'),field=document.createElement('input');field.type='text';field.className='manual-grocery-field';field.setAttribute('aria-label','Grocery item');field.placeholder='e.g. 2 cartons oat milk';field.value=item?.text||'';
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');const actions=document.createElement('div');actions.className='meal-unified-actions';
 function action(kind,label,change){const button=document.createElement('button');button.type='button';setIconButton(button,kind,label);button.onclick=()=>{try{if(change()===false)return;d.close();refresh()}catch(e){error.textContent='Could not save grocery item: '+e.message}};actions.append(button);return button}
 const save=action('save','Save grocery item',()=>{const text=field.value.trim();if(!text)return false;const current=manualGroceryItems();if(item&&!current.some(record=>record.id===item.id))throw Error('This item was removed.');saveManualGroceryItems(item?current.map(record=>record.id===item.id?{...record,text}:record):[...current,{id:crypto.randomUUID?.()||'manual-'+Date.now()+'-'+Math.random().toString(36).slice(2),text,checked:false}])});
 if(item)action('delete','Delete grocery item',()=>saveManualGroceryItems(manualGroceryItems().filter(record=>record.id!==item.id)));
 action('cancel','Cancel',()=>{});actions.lastElementChild.onclick=d.close;
 field.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();save.click()}};d.panel.append(field,error,actions);fitOneTimeMealViewport(d.overlay,d.panel);field.focus({preventScroll:true});
}
function appendManualGroceries(rows,refresh){
 const items=manualGroceryItems().filter(item=>localStorage.getItem('mealRotationHideCheckedGroceriesV1')!=='true'||!item.checked);if(!items.length)return;
 const section=document.createElement('section');section.className='manual-groceries';const heading=document.createElement('h3');heading.textContent='Additional items';section.append(heading);
 for(const item of items){
  const row=document.createElement('label');row.className='master-grocery-item manual-grocery-item';row.dataset.manualId=item.id;
  const check=document.createElement('input');check.type='checkbox';check.checked=item.checked;check.setAttribute('aria-label',item.text);check.onchange=()=>{try{saveManualGroceryItems(manualGroceryItems().map(record=>record.id===item.id?{...record,checked:check.checked}:record));refresh()}catch(e){check.checked=item.checked;showAppMessage(e.message)}};
  row.addEventListener('pointerdown',()=>{held=false},true);row.addEventListener('keydown',()=>{held=false},true);
  const text=document.createElement('span');text.className='grocery-item-details manual-grocery-text';text.textContent=item.text;let timer=null,start=null,held=false;
  text.addEventListener('pointerdown',event=>{if(event.button!==0)return;held=false;start={x:event.clientX,y:event.clientY};clearTimeout(timer);timer=setTimeout(()=>{held=true;openManualGroceryEditor(item,refresh)},550)});
  text.addEventListener('pointermove',event=>{if(start&&Math.hypot(event.clientX-start.x,event.clientY-start.y)>10){clearTimeout(timer);start=null}});for(const event of ['pointerup','pointercancel','pointerleave'])text.addEventListener(event,()=>{clearTimeout(timer);start=null});
  text.addEventListener('contextmenu',event=>event.preventDefault());row.addEventListener('click',event=>{if(held){event.preventDefault();event.stopImmediatePropagation();held=false}},true);
  row.append(check,text);section.append(row);
 }rows.append(section);
}
const GROCERY_TEXT_OVERRIDES_KEY='mealRotationGroceryTextOverridesV1';
function groceryTextOverrides(){const records=JSON.parse(localStorage.getItem(GROCERY_TEXT_OVERRIDES_KEY)||'{}');validateGroceryTextOverrides(records);return records}
function groceryTextKey(line){return JSON.stringify([...new Set((line.contributions||[]).map(source=>source.id))].sort())}
function groceryDisplayText(line){const ids=JSON.parse(groceryTextKey(line));for(const [key,text]of Object.entries(groceryTextOverrides()).reverse()){let sources;try{sources=JSON.parse(key)}catch(_){continue}if(ids.length&&Array.isArray(sources)&&ids.every(id=>sources.includes(id)))return text}return line.line}
function openGroceryTextEditor(line,refresh){
 const d=recipeBulkDialog('Edit grocery item'),field=document.createElement('input');field.type='text';field.className='manual-grocery-field';field.setAttribute('aria-label','Grocery item');field.value=groceryDisplayText(line);
 const note=document.createElement('p');note.className='muted';note.textContent='Your recipe will not change.';
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save grocery item');setIconButton(cancel,'cancel','Cancel');
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');
 save.onclick=()=>{const text=field.value.trim();if(!text){error.textContent='Enter a grocery item.';field.focus();return}try{const records=groceryTextOverrides();delete records[groceryTextKey(line)];records[groceryTextKey(line)]=text;localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify(records));d.close();refresh()}catch(e){error.textContent=e.message}};
 cancel.onclick=d.close;field.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();save.click()}};actions.append(save,cancel);d.panel.append(field,note,error,actions);fitOneTimeMealViewport(d.overlay,d.panel);field.focus({preventScroll:true});
}
function bindGroceryTextPress(name,line,refresh){
 let timer=null,start=null,held=false;name.style.touchAction='pan-y';name.style.userSelect='none';
 name.addEventListener('pointerdown',e=>{if(e.button!==0)return;held=false;start={x:e.clientX,y:e.clientY,scroll:scrollY};timer=setTimeout(()=>{if(start&&Math.abs(scrollY-start.scroll)<3)held=true},550)});
 name.addEventListener('pointermove',e=>{if(start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>8){clearTimeout(timer);start=null;held=false}});
 name.addEventListener('pointerup',e=>{clearTimeout(timer);if(start&&held){e.preventDefault();e.stopPropagation();openGroceryTextEditor(line,refresh)}start=null});
 for(const type of ['pointercancel','pointerleave'])name.addEventListener(type,()=>{clearTimeout(timer);start=null;held=false});
 name.addEventListener('click',e=>{if(held){held=false;e.preventDefault();e.stopImmediatePropagation()}},true);name.oncontextmenu=e=>e.preventDefault();
}
function groceryPeriodSchedules(period=groceryPeriod){
 if(period==='none')return [];
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
  groceryPeriod=readGroceryPeriod();
  const panel=document.createElement('section');panel.className='meal-plan-grocery';panel.setAttribute('aria-label','Master grocery list');
  const heading=document.createElement('h2');heading.textContent='Grocery List';
  const groceryHeader=document.createElement('div');groceryHeader.className='grocery-compact-header';groceryHeader.append(heading);const addManual=document.createElement('button');addManual.type='button';addManual.className='iconbtn grocery-add-manual';setIconButton(addManual,'add','Add grocery item');addManual.onclick=()=>openManualGroceryEditor(null,updateRows);panel.append(groceryHeader);
  const filters=document.createElement('div');filters.className='master-grocery-plan-filters';
  const periods=document.createElement('div');periods.className='grocery-week-options';periods.setAttribute('role','group');periods.setAttribute('aria-label','Grocery period');const weekChecks={};
  for(const [value,text]of [['current','This week'],['next','Next week']]){const label=document.createElement('label'),check=document.createElement('input'),name=document.createElement('span');check.type='checkbox';check.checked=groceryPeriod===value||groceryPeriod==='both';name.textContent=text;weekChecks[value]=check;
   check.onchange=()=>{const previous=groceryPeriod,next=weekChecks.current.checked?(weekChecks.next.checked?'both':'current'):(weekChecks.next.checked?'next':'none');try{localStorage.setItem(GROCERY_PERIOD_KEY,next);groceryPeriod=next;updateRows()}catch(e){weekChecks.current.checked=previous==='current'||previous==='both';weekChecks.next.checked=previous==='next'||previous==='both';showAppMessage(e.message)}};label.append(check,name);periods.append(label);
  }filters.append(periods);
  const rows=document.createElement('div');rows.className='master-grocery-list';
  function updateRows(){
   rows.replaceChildren();
   const groceries=getMasterGroceryItems();
   if(!groceries.size){
    const msg=document.createElement('p');msg.className='muted';
    msg.textContent=groceryPeriod==='none'?'Select a week to show recipe groceries.':mealPlans.every(plan=>masterGroceryExcludedPlanIds.has(String(plan.id)))?'Select a meal plan to show groceries.':'No selected recipe groceries.';
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
    name.textContent=groceryDisplayText(line);bindGroceryTextPress(name,line,updateRows);
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
    name.setAttribute('aria-label',groceryDisplayText(line)+'. Tap to show associated recipes');
    name.onclick=()=>{
     source.hidden=!source.hidden;
     name.setAttribute('aria-expanded',String(!source.hidden));
     name.setAttribute('aria-label',groceryDisplayText(line)+(source.hidden?'. Tap to show associated recipes':'. Tap to hide associated recipes'));
    };
    details.append(name,source);
    const target=document.createElement('label');target.className='grocery-checkbox-target';target.append(check);row.append(target,details);rows.append(row);
   });
   appendManualGroceries(rows,updateRows);
  }
  const chooseMeals=document.createElement('button');chooseMeals.type='button';chooseMeals.className='iconbtn grocery-choose-meals';
  chooseMeals.title='Choose meals';chooseMeals.setAttribute('aria-label','Choose meals');chooseMeals.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h18l-7 8v7l-4 2v-9z"/></svg>';
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
  const toolbar=list.querySelector(':scope > .top-controls');
  const icons=document.createElement('div');icons.className='grocery-header-icons';icons.append(chooseMeals);if(toolbar){icons.append(...toolbar.children);toolbar.remove()}icons.append(addManual);groceryHeader.append(icons);panel.append(filters);
  panel.append(rows);list.append(panel);updateRows();
 }
 function toggleMasterGroceryTab(){
  if(!showTop){showTop=true;setMasterCategoriesView(false);}
  groceryTabActive=!groceryTabActive;groceryTabOpen=groceryTabActive;if(groceryTabActive)allMealsActive=false;
  editId=null;renderList();
 }