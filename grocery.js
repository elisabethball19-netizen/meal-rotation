const MANUAL_GROCERIES_KEY='mealRotationManualGroceriesV1',GROCERY_PERIOD_KEY='mealRotationGroceryPeriodV1';
function readGroceryPeriod(){
 const raw=localStorage.getItem(GROCERY_PERIOD_KEY);if(raw===null)return 'current';let value=raw;try{value=JSON.parse(raw)}catch(_){}
 if(value&&typeof value==='object'&&typeof value.thisWeek==='boolean'&&typeof value.nextWeek==='boolean')return value.thisWeek?(value.nextWeek?'both':'current'):(value.nextWeek?'next':'none');
 return ({current:'current','this week':'current',next:'next','next week':'next',both:'both','both weeks':'both',none:'none'})[String(value).toLowerCase().trim()]||'current';
}
let groceryPeriod=readGroceryPeriod();
const collapsedGroceryMeals=new Set();
function manualGroceryItems(){const items=JSON.parse(localStorage.getItem(MANUAL_GROCERIES_KEY)||'[]');validateManualGroceryItems(items);return items}
function saveManualGroceryItems(items){validateManualGroceryItems(items);localStorage.setItem(MANUAL_GROCERIES_KEY,JSON.stringify(items))}
function setAllManualGroceries(checked){saveManualGroceryItems(manualGroceryItems().map(item=>({...item,checked})))}
function openManualGroceryEditor(item=null,refresh=()=>renderList()){
 const d=recipeBulkDialog(item?'Edit grocery item':'Add grocery item'),field=document.createElement('input');field.type='text';field.className='manual-grocery-field';field.setAttribute('aria-label','Grocery item');field.placeholder='e.g. 2 cartons oat milk';field.value=item?.text||'';
 const repeatLabel=document.createElement('label');repeatLabel.className='settings-display-option manual-grocery-repeat';const repeatSwitch=document.createElement('input');repeatSwitch.type='checkbox';repeatSwitch.className='preference-switch';repeatSwitch.setAttribute('role','switch');repeatSwitch.setAttribute('aria-label','Repeat weekly');
 const existingTemplate=item?.regularId?regularGroceryItems().find(template=>template.id===item.regularId):null;repeatSwitch.checked=!!existingTemplate?.repeat;repeatLabel.append(repeatSwitch,document.createTextNode('Repeat weekly'));decoratePreferenceSwitches(repeatLabel);
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');const actions=document.createElement('div');actions.className='meal-unified-actions';
 function action(kind,label,change){const button=document.createElement('button');button.type='button';setIconButton(button,kind,label);button.onclick=()=>{try{if(change()===false)return;d.close();refresh()}catch(e){error.textContent='Could not save grocery item: '+e.message}};actions.append(button);return button}
 const save=action('save','Save grocery item',()=>{const text=field.value.trim();if(!text)return false;const current=manualGroceryItems();if(item&&!current.some(record=>record.id===item.id))throw Error('This item was removed.');
  // Repeat weekly keeps one small template; the item is re-added unchecked on each Start next week.
  let templates=regularGroceryItems().filter(template=>template.id!==item?.regularId),regularId;
  if(repeatSwitch.checked){regularId=existingTemplate?.id||newGroceryId('regular');templates=[...templates,{id:regularId,name:text,amount:'',repeat:true}]}
  localStorage.setItem(REGULAR_GROCERIES_KEY,JSON.stringify(templates));
  const withRepeat=record=>{const {regularId:_old,...rest}=record;return regularId?{...rest,text,regularId}:{...rest,text}};
  saveManualGroceryItems(item?current.map(record=>record.id===item.id?withRepeat(record):record):[...current,withRepeat({id:crypto.randomUUID?.()||'manual-'+Date.now()+'-'+Math.random().toString(36).slice(2),checked:false})])});
 if(item)action('delete','Delete grocery item',()=>{if(item.regularId)localStorage.setItem(REGULAR_GROCERIES_KEY,JSON.stringify(regularGroceryItems().filter(template=>template.id!==item.regularId)));saveManualGroceryItems(manualGroceryItems().filter(record=>record.id!==item.id))});
 action('cancel','Cancel',()=>{});actions.lastElementChild.onclick=d.close;
 field.onkeydown=event=>{if(event.key==='Enter'){event.preventDefault();save.click()}};d.panel.append(field,repeatLabel,error,actions);fitOneTimeMealViewport(d.overlay,d.panel);field.focus({preventScroll:true});
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
// Regular items: reusable grocery templates (name, optional amount, Repeat weekly). Templates never change
// recipes. "This week" adds an unchecked Additional item linked by regularId; Repeat weekly adds a fresh unchecked
// entry on each successful Start next week (no calendar-only resets). Buying/removing an entry keeps the template.
const REGULAR_GROCERIES_KEY='mealRotationRegularGroceriesV1';
function regularGroceryItems(){try{const v=JSON.parse(localStorage.getItem(REGULAR_GROCERIES_KEY)||'[]');return Array.isArray(v)?v.filter(x=>x&&typeof x.id==='string'&&x.id&&typeof x.name==='string'&&x.name.trim()).map(x=>({id:x.id,name:x.name.trim(),amount:typeof x.amount==='string'?x.amount.trim():'',repeat:x.repeat===true})):[]}catch(e){return []}}
function regularGroceryText(item){return (item.amount?item.amount+' ':'')+item.name}
function newGroceryId(prefix){return crypto.randomUUID?.()||prefix+'-'+Date.now()+'-'+Math.random().toString(36).slice(2)}
function refreshRepeatingRegularItems(){
 const repeating=regularGroceryItems().filter(item=>item.repeat);if(!repeating.length)return;const ids=new Set(repeating.map(item=>item.id));
 saveManualGroceryItems([...manualGroceryItems().filter(entry=>!ids.has(entry.regularId)),...repeating.map(item=>({id:newGroceryId('manual'),text:regularGroceryText(item),checked:false,regularId:item.id}))]);
}
const GROCERY_TEXT_OVERRIDES_KEY='mealRotationGroceryTextOverridesV1';
function groceryTextOverrides(){const records=JSON.parse(localStorage.getItem(GROCERY_TEXT_OVERRIDES_KEY)||'{}');validateGroceryTextOverrides(records);return records}
function groceryTextKey(line){return JSON.stringify([...new Set((line.contributions||[]).map(source=>source.id))].sort())}
function groceryTextSourceIdentity(id){try{const token=JSON.parse(id),dated=JSON.parse(token[0]);if(dated.length===6)dated.pop();return JSON.stringify([dated,token[1],token[2]])}catch(e){return id}}
function groceryTextSourceMatches(a,b){if(a===b)return true;try{const x=JSON.parse(JSON.parse(a)[0]),y=JSON.parse(JSON.parse(b)[0]);if(x.length===6&&y.length===6)return false}catch(_){}return groceryTextSourceIdentity(a)===groceryTextSourceIdentity(b)}
function groceryDisplayText(line){return line.line}
// Shopping names typed for ingredients that are switched off (no shopping line yet); they apply as soon as the ingredient is included.
const PENDING_SHOPPING_NAMES_KEY='mealRotationPendingShoppingNamesV1';
function pendingShoppingNames(){try{const value=JSON.parse(localStorage.getItem(PENDING_SHOPPING_NAMES_KEY)||'{}');return value&&typeof value==='object'&&!Array.isArray(value)?value:{}}catch(e){return {}}}
function savePendingShoppingNames(value){try{localStorage.setItem(PENDING_SHOPPING_NAMES_KEY,JSON.stringify(value))}catch(e){}}
// Ingredient rows removed from a recipe's shopping selector (recipe text is untouched); key = mealId|ingredient token.
const HIDDEN_SHOPPING_LINES_KEY='mealRotationHiddenShoppingLinesV1';
function hiddenShoppingLines(){try{const value=JSON.parse(localStorage.getItem(HIDDEN_SHOPPING_LINES_KEY)||'{}');return value&&typeof value==='object'&&!Array.isArray(value)?value:{}}catch(e){return {}}}
function saveHiddenShoppingLines(value){try{localStorage.setItem(HIDDEN_SHOPPING_LINES_KEY,JSON.stringify(value))}catch(e){}}
function pendingShoppingNameKey(meal,line){const token=cookingItemTokens(meal).ingredients.find(i=>i.text===line)?.token;return token?String(meal.id)+'|'+token:''}
function groceryContributionText(source,overrides=groceryTextOverrides()){
 for(const [key,record]of Object.entries(overrides).reverse()){
  let ids;try{ids=JSON.parse(key)}catch(_){continue}
  if(!Array.isArray(ids)||!ids.some(id=>groceryTextSourceMatches(id,source.id)))continue;
  // Old multi-source wording has no per-source quantity provenance. Keep it intact.
  if(typeof record==='string'){
   if(ids.length>1)return source.line;
   const q=parseRecipeQuantity(record),original=parseRecipeQuantity(source.original);
   return ids.length===1&&q&&original&&q.lo===original.lo&&q.hi===original.hi?scaleRecipeIngredient(record,source.multiplier):record;
  }
  return scaleRecipeIngredient(record.text,source.multiplier/record.multiplier);
 }
 {const pending=pendingShoppingNames()[String(source.mealId)+'|'+source.ingredientToken];if(pending&&typeof pending.text==='string'&&pending.text.trim())return scaleRecipeIngredient(pending.text,(source.multiplier||1)/(pending.multiplier||1))}
 return groceryShoppingText(source.line);
}
// Split recipe lines ("2 tsp curry" + "1 tsp curry, remaining") from one meal occurrence count as one source.
function groceryOccurrenceGroups(line){const groups=new Map();for(const c of line.contributions||[]){const k=[c.mealId,c.planId,c.day].join('|');if(!groups.has(k))groups.set(k,[]);groups.get(k).push(c)}return [...groups.values()]}
function openGroceryTextEditor(line,refresh){
 if(groceryOccurrenceGroups(line).length>1){openGroceryContributionEditor(line,refresh);return}
 const d=recipeBulkDialog('Edit grocery item'),field=document.createElement('input');field.type='text';field.className='manual-grocery-field';field.setAttribute('aria-label','Grocery item');field.value=line.line;
 const note=document.createElement('p');note.className='muted';note.textContent='Changes apply only to your grocery list. Quantities still update when you scale the recipe.';
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save grocery item');setIconButton(cancel,'cancel','Cancel');
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');
 save.onclick=()=>{const text=field.value.trim();if(!text){error.textContent='Enter a grocery item.';field.focus();return}try{const records=groceryTextOverrides();delete records[groceryTextKey(line)];const entered=groceryQuantityParts(text),total=groceryQuantityParts(line.line);
 for(const source of line.contributions||[]){const original=groceryQuantityParts(groceryContributionText(source));let wording=text;
 if(entered&&total&&original&&total.lo>0){const ratio=entered.lo/total.lo,amount=formatRecipeQuantity(original.lo*ratio)+(original.hi!==original.lo?'–'+formatRecipeQuantity(original.hi*ratio):'');wording=amount+' '+(entered.unit?entered.unit+' ':'')+entered.name}
 records[JSON.stringify([source.id])]={text:wording,multiplier:source.multiplier||1};}const before=captureState();localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify(records));snapshot(before);d.close();refresh()}catch(e){error.textContent=e.message}};
 cancel.onclick=d.close;field.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();save.click()}};actions.append(save,cancel);d.panel.append(field,note,error,actions);fitOneTimeMealViewport(d.overlay,d.panel);field.focus({preventScroll:true});
}
// Batch 2: a multi-recipe item lists each recipe's own amount; each saves as that recipe's shopping wording only.
function openGroceryContributionEditor(line,refresh){
 const d=recipeBulkDialog('Edit grocery item'),fields=[];
 const note=document.createElement('p');note.className='muted';note.textContent='Changes apply only to your grocery list. Quantities still update when you scale the recipe.';
 const list=document.createElement('div');list.className='grocery-contribution-fields';
 for(const source of line.contributions){const label=document.createElement('label');label.className='grocery-contribution-field';const name=document.createElement('span');name.className='grocery-contribution-recipe';name.textContent=source.mealName;const field=document.createElement('input');field.type='text';field.className='manual-grocery-field';field.setAttribute('aria-label','Grocery item for '+source.mealName);field.value=groceryContributionText(source);label.append(name,field);list.append(label);fields.push([source,field])}
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save grocery item');setIconButton(cancel,'cancel','Cancel');
 const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');
 save.onclick=()=>{const empty=fields.find(([,field])=>!field.value.trim());if(empty){error.textContent='Enter a grocery item.';empty[1].focus();return}try{const records=groceryTextOverrides();delete records[groceryTextKey(line)];
  for(const [source,field]of fields){const text=field.value.trim();if(text===groceryContributionText(source))continue;records[JSON.stringify([source.id])]={text,multiplier:source.multiplier||1}}
  const before=captureState();localStorage.setItem(GROCERY_TEXT_OVERRIDES_KEY,JSON.stringify(records));snapshot(before);d.close();refresh()}catch(e){error.textContent=e.message}};
 cancel.onclick=d.close;actions.append(save,cancel);d.panel.append(list,note,error,actions);fitOneTimeMealViewport(d.overlay,d.panel);fields[0]?.[1].focus({preventScroll:true});
}
function bindGroceryTextPress(name,line,refresh){
 let timer=null,start=null,held=false;name.style.touchAction='pan-y';name.style.userSelect='none';
 name.addEventListener('pointerdown',e=>{if(e.button!==0)return;held=false;start={x:e.clientX,y:e.clientY,scroll:scrollY};timer=setTimeout(()=>{if(start&&Math.abs(scrollY-start.scroll)<3)held=true},550)});
 name.addEventListener('pointermove',e=>{if(start&&Math.hypot(e.clientX-start.x,e.clientY-start.y)>8){clearTimeout(timer);start=null;held=false}});
 name.addEventListener('pointerup',e=>{clearTimeout(timer);if(start&&held){e.preventDefault();e.stopPropagation();openGroceryTextEditor(line,refresh)}start=null});
 for(const type of ['pointercancel','pointerleave'])name.addEventListener(type,()=>{clearTimeout(timer);start=null;held=false});
 name.addEventListener('click',e=>{if(held){held=false;e.preventDefault();e.stopImmediatePropagation()}},true);name.oncontextmenu=e=>e.preventDefault();
}
// A checkbox operation changes checks, not schedules. Never retain this snapshot across events.
let groceryCheckSchedules=null;
function withGroceryCheckSchedules(action){
 if(groceryCheckSchedules)return action();groceryCheckSchedules=new Map();try{return action()}finally{groceryCheckSchedules=null}
}
function groceryPeriodSchedules(period=groceryPeriod){
 if(period==='none')return [];
 const cacheable=period==='both'||period==='next';if(cacheable&&groceryCheckSchedules?.has(period))return groceryCheckSchedules.get(period);
 const current=mealPlans.map(saved=>{const plan=saved.id===activePlanId?{...saved,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:saved;return {plan,entries:getDisplayedWeekdayMealsForPlan(plan),preview:false}});if(period==='rotation')return current;
 const upcoming=period==='next'||period==='both'?previewNextWeekPlans():[];
 const result=(period==='next'?[]:current).concat(upcoming);if(cacheable&&groceryCheckSchedules)groceryCheckSchedules.set(period,result);return result;
}
function getGroceryContributions(allPlans=false,period='rotation'){
 let selected={};try{selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}')}catch(e){}
 const result=[],observed=new Set(),legacyOwners=new Map(),ingredientTokens=new Map();
 for(const {plan,entries,preview,retainedKeys}of groceryPeriodSchedules(period)){
  if(!allPlans&&!(showMealPlanTabs&&mealPlans.length>1)&&plan.id!==activePlanId)continue;
  if(!allPlans&&showMealPlanTabs&&mealPlans.length>1&&masterGroceryExcludedPlanIds.has(String(plan.id)))continue;
  const groupRank=entry=>{const raw=plan.weekdayCategories?.[entry.day],groups=Array.isArray(raw)?raw:[raw],index=groups.indexOf(entry.cat);return index<0?groups.length:index};
  for(const entry of [...entries].sort((a,b)=>weekdays.indexOf(a.day)-weekdays.indexOf(b.day)||groupRank(a)-groupRank(b))){const occurrence=groceryOccurrenceIdentity(plan,entry),legacy=JSON.stringify(JSON.parse(occurrence).slice(0,4));if(!legacyOwners.has(legacy))legacyOwners.set(legacy,occurrence)}
  for(const entry of entries){
   const {meal,day,linkedTo}=entry;if(!allPlans&&masterGroceryExcludedMealKeys.has(groceryMealKey(plan,meal)))continue;
   const context=preview?pendingContext(plan,entry):cookingContext(plan.id,day,entry.cat,meal,linkedTo),occurrence=groceryOccurrenceIdentity(plan,entry),scheduledDate=cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar)),dated=JSON.stringify([...JSON.parse(occurrence),scheduledDate]);if(observed.has(dated))continue;observed.add(dated);
   const legacyOccurrence=JSON.stringify(JSON.parse(occurrence).slice(0,4));if(!legacyOwners.has(legacyOccurrence))legacyOwners.set(legacyOccurrence,occurrence);const legacyOwner=!preview&&legacyOwners.get(legacyOccurrence)===occurrence;
   const linkedParent=linkedTo??entries.find(parent=>parent.day===day&&parent.cat!==entry.cat&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(meal.id)))?.meal.id;
   const selectedKeys=new Set(grocerySelectionsForMeal(meal,selected).map(ingredientKey)),actualPlan=mealPlans.find(item=>item.id===plan.id),sameDate=actualPlan&&cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},actualPlan.rotationCalendar))===scheduledDate,multiplier=preview?projectedOccurrenceMultiplier(plan,entry,retainedKeys):occurrenceMultiplier(context),counts=new Map();
   if(!ingredientTokens.has(meal))ingredientTokens.set(meal,cookingItemTokens(meal).ingredients);
   for(const [ingredientIndex,raw]of (Array.isArray(meal.ingredients)?meal.ingredients:[]).entries()){
    const original=String(raw??'').trim(),oldKey=ingredientKey(original);if(!oldKey||!selectedKeys.has(oldKey)||syncIngredientHeading(original)||groceryNonIngredientLine(original))continue;
    const normalized=ingredientKey(compactIngredientFractions(original)),index=counts.get(normalized)||0;counts.set(normalized,index+1);
    const line=scaleRecipeIngredient(original,multiplier),quantity=groceryQuantityParts(line),baseKey=quantity?.key||'unmeasured:'+oldKey;
    result.push({id:JSON.stringify([dated,normalized,index]),occurrence,scheduledDate,preview:!!preview,legacyId:JSON.stringify([occurrence,normalized,index]),legacyIds:[JSON.stringify([occurrence,normalized,index]),JSON.stringify([legacyOccurrence,normalized,index])],legacyOwner,parentId:linkedParent==null?null:String(linkedParent),planId:plan.id,day,cat:entry.cat,mealId:meal.id,mealName:meal.name,original,ingredientToken:ingredientTokens.get(meal)[ingredientIndex]?.token,multiplier,line,quantity,baseKey,checkKeys:[...new Set([oldKey,original.toLowerCase().replace(/\s+/g,' ').trim()])]});
   }
   for(const side of simpleSidesForEntry(plan,entry))for(const ingredient of side.ingredients){
    const original=ingredient.text,line=scaleRecipeIngredient(original,multiplier),quantity=groceryQuantityParts(line),baseKey=quantity?.key||'unmeasured:'+ingredientKey(original),token='simple-side:'+JSON.stringify([side.id,ingredient.id]);
    result.push({id:JSON.stringify([dated,token,0]),occurrence,scheduledDate,preview:!!preview,legacyOwner:false,legacyIds:[],parentId:linkedParent==null?null:String(linkedParent),planId:plan.id,day,cat:entry.cat,mealId:meal.id,mealName:(meal.name||'Meal')+' — '+side.name,simpleSideId:side.id,simpleSideName:side.name,multiplier,original,line,quantity,baseKey,checkKeys:[ingredientKey(original)]});
   }
  }
 }
 // Plan ahead "Shop early": from its chosen date, a planned meal's groceries join the list until its week is covered.
 if(typeof plannedMealsFor==='function'){const today=cookingLocalDate(new Date()),covered=new Set(result.map(s=>s.scheduledDate));
  const seenPlans=new Set();for(const {plan:shown}of groceryPeriodSchedules(period)){const plan=mealPlans.find(p=>p.id===shown.id)||shown;if(seenPlans.has(plan.id))continue;seenPlans.add(plan.id);if(!allPlans&&!(showMealPlanTabs&&mealPlans.length>1)&&plan.id!==activePlanId)continue;
   const start=mealPlanWeekStart(plan),weeks=period==='rotation'?1:period==='next'?2:2,from=cookingLocalDate(period==='next'?new Date(start.getFullYear(),start.getMonth(),start.getDate()+7):start),to=cookingLocalDate(new Date(start.getFullYear(),start.getMonth(),start.getDate()+7*weeks-1));
   for(const item of plannedMealsFor(plan.id)){
    if(!item.shopEarly||(item.mealId==null&&!item.ingredients?.length)||item.date<today||(item.date>=from&&item.date<=to)||covered.has(item.date))continue;
    const shopFrom=item.shopFrom||cookingLocalDate(new Date(parseCookingLocalDate(item.date).getTime()-7*864e5));if(today<shopFrom)continue;
    // A one-time (typed) plan carries its own grocery lines.
    const meal=item.mealId==null?{id:'planned:'+item.id,name:item.name,ingredients:item.ingredients,temporaryMeal:true}:meals.find(m=>String(m.id)===String(item.mealId));if(!meal)continue;
    const keys=new Set((item.mealId==null?meal.ingredients:grocerySelectionsForMeal(meal,selected)).map(ingredientKey)),tokens=cookingItemTokens(meal).ingredients,counts=new Map(),occurrence=JSON.stringify(['planned',String(plan.id),item.date,String(meal.id)]),when=parseCookingLocalDate(item.date);
    for(const [ingredientIndex,raw]of (Array.isArray(meal.ingredients)?meal.ingredients:[]).entries()){
     const original=String(raw??'').trim(),oldKey=ingredientKey(original);if(!oldKey||!keys.has(oldKey)||syncIngredientHeading(original)||groceryNonIngredientLine(original))continue;
     const normalized=ingredientKey(compactIngredientFractions(original)),index=counts.get(normalized)||0;counts.set(normalized,index+1);
     const quantity=groceryQuantityParts(original);
     result.push({id:JSON.stringify([occurrence,normalized,index]),occurrence,scheduledDate:item.date,preview:true,plannedEarly:true,legacyOwner:false,legacyIds:[],parentId:null,planId:plan.id,day:weekdays[(when.getDay()+6)%7],cat:'',mealId:meal.id,mealName:meal.name+' · '+when.toLocaleDateString(undefined,{weekday:'short',month:'short',day:'numeric'}),original,ingredientToken:tokens[ingredientIndex]?.token,multiplier:1,line:original,quantity,baseKey:quantity?.key||'unmeasured:'+oldKey,checkKeys:[...new Set([oldKey,original.toLowerCase().replace(/\s+/g,' ').trim()])]});
    }
   }
  }
 }
 return result;
}
function openGroceryRecipeSource(source){
 const meal=meals.find(meal=>String(meal.id)===String(source.mealId));if(!meal||meal.temporaryMeal){showAppMessage('This one-time meal has no saved recipe.');return}
 const plan=mealPlans.find(plan=>String(plan.id)===String(source.planId));
 const matches=(plan,entry)=>entry.day===source.day&&String(entry.meal.id)===String(source.mealId)&&groceryOccurrenceIdentity(plan,entry)===source.occurrence&&cookingLocalDate(scheduledOccurrenceDate({...entry,planId:plan.id},plan.rotationCalendar))===source.scheduledDate;
 const current=plan?recipePlanEntries(plan.id).filter(entry=>matches(plan,entry)):[];
 let context=current.length===1?cookingContext(plan.id,current[0].day,current[0].cat,meal,current[0].linkedTo):null;
 // Future sources own their dated pending occurrence, never this week's progress.
 const future=!context&&source.preview&&groceryPeriodSchedules('next').find(item=>String(item.plan.id)===String(source.planId)&&item.entries.some(entry=>matches(item.plan,entry)));if(future){const entry=future.entries.find(entry=>matches(future.plan,entry));context=pendingContext(future.plan,entry)}
 const target=context||future?groceryRecipeNavigation(meal,source):null;
 openSavedMealRecipe(meal,context,null,target);
}
function getMasterGroceryItems(sources=getGroceryContributions(false,groceryPeriod)){
 const groceries=new Map(),overrides=groceryTextOverrides();
 for(const source of sources){
  const line=groceryContributionText(source,overrides),quantity=groceryQuantityParts(line),baseKey=source.baseKey;
  // Combining follows shopping wording; checks retain their canonical source quantities.
  const key=quantity?.key||'unmeasured:'+ingredientKey(line);
  if(!groceries.has(key))groceries.set(key,{line,recipes:[],checkKeys:[],checkGroups:[],quantity:quantity?{...quantity,lo:0,hi:0}:null,baseKey,contributions:[]});
  const item=groceries.get(key);item.contributions.push(source);
  if(!item.recipes.includes(source.mealName))item.recipes.push(source.mealName);
  if(!item.checkGroups.some(group=>group[0]===source.checkKeys[0]))item.checkGroups.push(source.checkKeys);
  for(const checkKey of source.checkKeys)if(!item.checkKeys.includes(checkKey))item.checkKeys.push(checkKey);
  if(quantity){item.quantity.lo+=quantity.lo;item.quantity.hi+=quantity.hi;const q=item.quantity;const amount=formatRecipeQuantity(q.lo)+(Math.abs(q.hi-q.lo)>1e-8?'–'+formatRecipeQuantity(q.hi):'');const unit=q.unit==='cup'?(q.hi===1?'cup':'cups'):q.unit==='clove'?(q.hi===1?'clove':'cloves'):q.unit==='piece'?(q.hi===1?'piece':'pieces'):q.unit==='sprig'?(q.hi===1?'sprig':'sprigs'):q.unit;item.line=amount+' '+(unit?unit+' ':'')+q.name}
 }
 for(const item of groceries.values()){
  const ids=item.contributions.map(source=>source.id);
  for(const [key,record]of Object.entries(overrides).reverse()){
   let saved;try{saved=JSON.parse(key)}catch(_){continue}
   if(!Array.isArray(saved))continue;
   const matches=ids.some(id=>saved.some(old=>groceryTextSourceMatches(old,id)));
   if(matches&&typeof record!=='string')break;
   if(typeof record==='string'&&saved.length>1&&ids.every(id=>saved.some(old=>groceryTextSourceMatches(old,id)))){item.line=record;break}
  }
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
  button.onclick=()=>navigateAfterSettings(()=>{if(!showTop){showTop=true;setMasterCategoriesView(false)}allMealsActive=!allMealsActive;if(allMealsActive)groceryTabActive=false,aiTabActive=false;editId=null;renderList()});
  document.body.append(button);
 }
 function addFloatingViewButtons(){
  // Show all four destinations, highlighting the active view.
  const current=!showTop?'groups':groceryTabActive?'grocery':allMealsActive?'all':aiTabActive?'ai':'top';
  const destinations=[
   ['top','Meals','<path d="M3 10.2 12 3l9 7.2V21h-6.5v-7h-5v7H3z"/>',()=>{showTop=true;groceryTabActive=false,aiTabActive=false;allMealsActive=false;render()}],
   ['groups','Meal Groups','<path d="M4 6h16M4 12h16M4 18h16"/>',()=>openMasterCategories()],
   ['all','Week',weekCalendarArtwork,()=>{showTop=true;groceryTabActive=false,aiTabActive=false;allMealsActive=true;render()}],
   ['grocery','Groceries','<circle cx="9" cy="20" r="1"/><circle cx="19" cy="20" r="1"/><path d="M2 3h2l2.5 12h12L22 7H5"/>',()=>{showTop=true;allMealsActive=false;groceryTabActive=true,aiTabActive=false;render()}],
   ['ai','Ask AI',appIconSvg.sparkle,()=>{showTop=true;allMealsActive=false;groceryTabActive=false;aiTabActive=true;editId=null;render()}]
  ];
  document.getElementById('mealBottomNav')?.remove();const nav=document.createElement('nav');nav.id='mealBottomNav';nav.setAttribute('aria-label','Main navigation');document.body.append(nav);
  const order=['top','all','groups','grocery','ai'];const visibleDestinations=destinations.filter(d=>d[0]!=='all'||showMealPlanTabs).sort((a,b)=>order.indexOf(a[0])-order.indexOf(b[0]));
  visibleDestinations.forEach(([key,title,art,action])=>{
   const b=document.createElement('button');b.type='button';b.className='smallbtn unified-nav-fab';
   b.title=title;b.setAttribute('aria-label',title);b.dataset.destination=key;
   if(key===current){b.classList.add('current-view');b.setAttribute('aria-current','page');}
   b.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true">'+art+'</svg>';const label=document.createElement('span');label.textContent=key==='groups'&&visibleDestinations.length>=5?'Groups':title;b.append(label);
   b.onclick=()=>navigateAfterSettings(()=>{if(key==='groups'&&tutorialStage==='1')setTutorialStage('2');action();window.scrollTo(0,0);requestAnimationFrame(()=>{window.scrollTo(0,0);document.documentElement.scrollTop=0;document.body.scrollTop=0})});nav.append(b);
  });
 }
 const expandedGrocerySources=new Set();
 function renderMasterGroceryTab(list){
  groceryPeriod=readGroceryPeriod();
  const panel=document.createElement('section');panel.className='meal-plan-grocery';panel.setAttribute('aria-label','Master grocery list');
  const heading=document.createElement('h2');heading.textContent='Groceries';
  const groceryHeader=document.createElement('div');groceryHeader.className='grocery-compact-header';groceryHeader.append(heading);const addManual=document.createElement('button');addManual.type='button';addManual.className='iconbtn grocery-add-manual';setIconButton(addManual,'add','Add grocery item');addManual.onclick=()=>openManualGroceryEditor(null,updateRows);panel.append(groceryHeader);
  const weekSummary=document.createElement('span');weekSummary.className='grocery-week-summary';panel.append(weekSummary);
  const viewLabel=document.createElement('label');viewLabel.className='grocery-view-control';const view=document.createElement('input');view.type='checkbox';view.setAttribute('role','switch');view.className='preference-switch';view.setAttribute('aria-label','Group by meal');view.checked=localStorage.getItem('mealRotationGroceryViewV1')==='meal';view.onchange=()=>{localStorage.setItem('mealRotationGroceryViewV1',view.checked?'meal':'combined');updateRows()};viewLabel.append(view,document.createTextNode('Group by meal'));groceryHeader.append(viewLabel);
  const rows=document.createElement('div');rows.className='master-grocery-list';
  const expanded=expandedGrocerySources;
  function changeCheck(item,value){withGroceryCheckSchedules(()=>{snapshot();setGroceryItemChecked(item.baseKey,item,value);localStorage.setItem('mealRotationCheckedIngredientsV1',JSON.stringify([...checkedIngredients]));updateRows()})}
  function updateRows(){
   rows.replaceChildren();weekSummary.textContent={current:'This week',next:'Next week',both:'Both weeks',none:'No weeks selected'}[groceryPeriod];
   const groceries=getMasterGroceryItems();
   if(!groceries.size){
    const msg=document.createElement('p');msg.className='muted';
    msg.textContent=groceryPeriod==='none'?'Select a week to show recipe groceries.':mealPlans.every(plan=>masterGroceryExcludedPlanIds.has(String(plan.id)))?'Select a meal plan to show groceries.':'No selected recipe groceries.';
    rows.append(msg);
   }
   const grouped=localStorage.getItem('mealRotationGroceryViewV1')==='meal',sections=new Map();
   const displayed=grouped?[...getGroceryContributions(false,groceryPeriod).reduce((map,s)=>{const key=JSON.stringify([s.occurrence,s.scheduledDate]);if(!map.has(key))map.set(key,[]);map.get(key).push(s);return map},new Map()).entries()].flatMap(([occurrence,sources])=>[...getMasterGroceryItems(sources)].map(([key,line])=>[key,{...line,section:occurrence}])):[...groceries];
   displayed.sort((a,b)=>Number(groceryItemChecked(b[0],b[1]))-Number(groceryItemChecked(a[0],a[1]))).forEach(([key,line])=>{
    if(localStorage.getItem('mealRotationHideCheckedGroceriesV1')==='true'&&groceryItemChecked(key,line))return;
    let container=rows;if(grouped){if(!sections.has(line.section)){const section=document.createElement('section');section.className='grocery-meal-section';const header=document.createElement('div');header.className='grocery-meal-heading';const title=document.createElement('button'),toggle=document.createElement('button'),body=document.createElement('div'),contribution=line.contributions[0];title.type=toggle.type='button';title.className='grocery-meal-title';title.textContent=contribution.mealName;title.onclick=()=>openGroceryRecipeSource(contribution);toggle.className='iconbtn';toggle.setAttribute('aria-label','Ingredients for '+contribution.mealName);const disclosure=()=>{const closed=collapsedGroceryMeals.has(line.section);body.hidden=closed;setIconButton(toggle,closed?'down':'up','Ingredients for '+contribution.mealName);toggle.setAttribute('aria-expanded',String(!closed))};toggle.onclick=()=>{if(collapsedGroceryMeals.has(line.section))collapsedGroceryMeals.delete(line.section);else collapsedGroceryMeals.add(line.section);disclosure()};disclosure();header.append(title,toggle);section.append(header,body);sections.set(line.section,body);rows.append(section)}container=sections.get(line.section)}
    const row=document.createElement('div');row.className='master-grocery-item';
    const check=document.createElement('input');check.type='checkbox';check.checked=groceryItemChecked(key,line);
    check.indeterminate=!check.checked&&line.contributions.some(source=>grocerySourceChecked(source)||groceryCheckedAmount(source)?.lo>0);
    check.setAttribute('aria-label',line.line);check.onchange=()=>changeCheck(line,check.checked);
    const details=document.createElement('span');details.className='grocery-item-details';
    const name=document.createElement('button');name.type='button';name.className='grocery-ingredient-name';
    name.textContent=line.line;
    if(grouped){const text=document.createElement('span');text.textContent=line.line;details.append(text);const pencil=document.createElement('button');pencil.type='button';pencil.className='iconbtn grocery-contribution-edit';setIconButton(pencil,'rename','Edit shopping wording for '+line.line);pencil.onclick=()=>openGroceryTextEditor(line,updateRows);const target=document.createElement('label');target.className='grocery-checkbox-target';target.append(check);row.append(target,details,pencil);container.append(row);return}
    const source=document.createElement('span');source.className='grocery-recipe-source';
    const occurrences=groceryOccurrenceGroups(line);
    for(const parts of occurrences){const contribution=parts[0];
     const detail=document.createElement('span');detail.className='grocery-contribution';
     if(occurrences.length>1){const cb=document.createElement('input');cb.type='checkbox';cb.checked=parts.every(x=>grocerySourceChecked(x));cb.indeterminate=!cb.checked&&parts.some(x=>grocerySourceChecked(x)||groceryCheckedAmount(x)?.lo>0);cb.setAttribute('aria-label','Check '+contribution.mealName);cb.onchange=()=>changeCheck({contributions:parts,baseKey:contribution.baseKey,checkKeys:parts.flatMap(x=>x.checkKeys||[])},cb.checked);detail.append(cb)}
     const link=document.createElement('button');link.type='button';link.className='grocery-recipe-link';link.dataset.mealId=String(contribution.mealId);link.dataset.planId=contribution.planId;link.dataset.day=contribution.day;link.dataset.grocerySourceId=contribution.id;link.textContent=contribution.mealName+(typeof scaleBadgeText==='function'&&scaleBadgeText(contribution.multiplier)?' '+scaleBadgeText(contribution.multiplier):'');
     link.onclick=()=>openGroceryRecipeSource(contribution);detail.append(link);source.append(detail);
    }
    const expandedKey=groceryTextKey(line);source.hidden=!expanded.has(expandedKey);
    const chevron=document.createElement('button');chevron.type='button';chevron.className='iconbtn grocery-expand';chevron.setAttribute('aria-label','Show contributions for '+line.line);
    function disclosure(){name.setAttribute('aria-expanded',String(!source.hidden));chevron.setAttribute('aria-expanded',String(!source.hidden));chevron.innerHTML='<svg viewBox="0 0 24 24"><path d="'+(source.hidden?'m6 9 6 6 6-6':'m6 15 6-6 6 6')+'"/></svg>'}
    name.onclick=chevron.onclick=()=>{source.hidden=!source.hidden;if(source.hidden)expanded.delete(expandedKey);else expanded.add(expandedKey);disclosure()};disclosure();
    if(occurrences.length>1){const count=document.createElement('span');count.className='muted grocery-source-count';count.textContent=' ('+occurrences.length+')';name.append(count)}
    details.append(name,source);
    const pencil=document.createElement('button');pencil.type='button';pencil.className='iconbtn grocery-contribution-edit grocery-item-edit';setIconButton(pencil,'rename','Edit shopping wording for '+line.line);pencil.onclick=()=>openGroceryTextEditor(line,updateRows);
    const target=document.createElement('label');target.className='grocery-checkbox-target';target.append(check);const shop=typeof shoppingLinkNode==='function'?shoppingLinkNode(line.line):null;row.replaceChildren(...[target,details,shop,pencil,chevron].filter(Boolean));container.append(row);
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
   const title=document.createElement('h3');title.textContent='Meals to include in your weekly shopping list';title.style.margin='0 0 6px';box.append(title);
   const hint=document.createElement('p');hint.textContent='';hint.hidden=true;hint.style.cssText='font-size:14px;color:#666;margin:0 0 12px';box.append(hint);
   const body=document.createElement('div');body.style.cssText='overflow-y:auto;min-height:0;flex:1';
   const excludedPlans=new Set(masterGroceryExcludedPlanIds),excludedMeals=new Set(masterGroceryExcludedMealKeys);
   const weeks=document.createElement('fieldset');weeks.className='grocery-filter-weeks';const legend=document.createElement('legend');legend.textContent='Weeks';weeks.append(legend);const weekChecks={};
   for(const [value,text]of [['current','This week'],['next','Next week']]){const label=document.createElement('label'),check=document.createElement('input');check.type='checkbox';check.checked=groceryPeriod===value||groceryPeriod==='both';weekChecks[value]=check;label.append(check,document.createTextNode(text));weeks.append(label);check.onchange=()=>{const previous=groceryPeriod,next=weekChecks.current.checked?(weekChecks.next.checked?'both':'current'):(weekChecks.next.checked?'next':'none');try{localStorage.setItem(GROCERY_PERIOD_KEY,next);groceryPeriod=next;updateRows();renderMealChoices()}catch(error){weekChecks.current.checked=previous==='current'||previous==='both';weekChecks.next.checked=previous==='next'||previous==='both';showAppMessage(error.message)}}}
   const mealsHeading=document.createElement('h4');mealsHeading.textContent='Meals';box.append(weeks,mealsHeading);
   function renderMealChoices(){body.replaceChildren();const schedules=groceryPeriodSchedules();
   for(const plan of (showMealPlanTabs&&mealPlans.length>1?mealPlans:mealPlans.filter(p=>p.id===activePlanId))){
    const section=document.createElement('section');section.style.cssText='border-top:1px solid #ddd;padding:12px 0';
    const header=document.createElement('label');header.style.cssText='display:flex;align-items:center;gap:10px;font-weight:700;margin-bottom:8px';
    const planCheck=document.createElement('input');planCheck.type='checkbox';planCheck.checked=!excludedPlans.has(String(plan.id));planCheck.style.cssText='width:20px;height:20px';
    header.append(planCheck,document.createTextNode(plan.name));if(showMealPlanTabs&&mealPlans.length>1)section.append(header);
    const entries=new Map();for(const source of schedules.filter(source=>source.plan.id===plan.id))for(const entry of source.entries){entries.set(String(entry.meal.id),entry.meal)}
    const mealChecks=[];
    for(const meal of entries.values()){
     const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:10px;padding:7px 0;align-items:flex-start';
     const cb=document.createElement('input');cb.type='checkbox';cb.style.cssText='width:20px;height:20px;flex:0 0 20px';
     const key=groceryMealKey(plan,meal);cb.checked=!excludedMeals.has(key);cb.disabled=(showMealPlanTabs&&mealPlans.length>1)&&!planCheck.checked;
     cb.onchange=()=>{if(cb.checked)excludedMeals.delete(key);else excludedMeals.add(key)};
     mealChecks.push(cb);label.append(cb,document.createTextNode(meal.name));section.append(label);
    }
    if(!entries.size){const empty=document.createElement('p');empty.textContent='No regular meals';empty.className='muted';empty.style.margin='6px 0 6px 22px';section.append(empty)}
    planCheck.onchange=()=>{if(planCheck.checked)excludedPlans.delete(String(plan.id));else excludedPlans.add(String(plan.id));mealChecks.forEach(cb=>cb.disabled=!planCheck.checked)};
    body.append(section);
   }
   }renderMealChoices();
   box.append(body);
   const footer=document.createElement('div');footer.style.cssText='display:flex;align-items:center;justify-content:center;gap:18px;padding-top:12px';
   const save=document.createElement('button');save.type='button';setIconButton(save,'save','Save meal selections');
   save.onclick=()=>{masterGroceryExcludedPlanIds=excludedPlans;masterGroceryExcludedMealKeys=excludedMeals;saveMasterGroceryPlanExclusions();saveMasterGroceryMealExclusions();overlay.remove();updateRows()};
   const cancel=document.createElement('button');cancel.type='button';setIconButton(cancel,'cancel','Cancel');cancel.onclick=()=>overlay.remove();
   footer.append(save,cancel);box.append(footer);overlay.append(box);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});document.body.append(overlay);
  };
  const toolbar=list.querySelector(':scope > .top-controls');
  const icons=document.createElement('div');icons.className='grocery-header-icons';icons.append(chooseMeals);if(toolbar){icons.append(...toolbar.children);toolbar.remove()}icons.append(addManual);for(const [expand,label]of [[true,'Expand all groceries'],[false,'Collapse all groceries']]){const button=document.createElement('button');button.type='button';button.className='iconbtn';setIconButton(button,expand?'chevrons-down':'chevrons-up',label);button.onclick=()=>{if(view.checked){for(const source of getGroceryContributions(false,groceryPeriod)){const key=JSON.stringify([source.occurrence,source.scheduledDate]);if(expand)collapsedGroceryMeals.delete(key);else collapsedGroceryMeals.add(key)}}else for(const line of getMasterGroceryItems().values()){const key=groceryTextKey(line);if(expand)expandedGrocerySources.add(key);else expandedGrocerySources.delete(key)}updateRows()};icons.append(button)}panel.append(icons);
  panel.append(rows);list.append(panel);decoratePreferenceSwitches(panel);updateRows();
 }
 function toggleMasterGroceryTab(){
  if(!showTop){showTop=true;setMasterCategoriesView(false);}
  groceryTabActive=!groceryTabActive,aiTabActive=false;groceryTabOpen=groceryTabActive;if(groceryTabActive)allMealsActive=false;
  editId=null;renderList();
 }
function updateMealNavigationKeyboard(){
 const target=document.activeElement,editing=target?.matches('textarea,input:not([type=checkbox]):not([type=radio]):not([type=button]),[contenteditable=true]');
 document.body.classList.toggle('meal-keyboard-open',!!editing||!!(window.visualViewport&&window.visualViewport.height<window.innerHeight*.75));
}
document.addEventListener('focusin',updateMealNavigationKeyboard);document.addEventListener('focusout',()=>requestAnimationFrame(updateMealNavigationKeyboard));window.visualViewport?.addEventListener('resize',updateMealNavigationKeyboard);
