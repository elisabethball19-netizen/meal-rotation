const UP_NEXT_ORDER_KEY='mealRotationUpNextOrderV1',GROUP_ROTATION_KEY='mealRotationGroupRotationV1';
const timePreferencesStorageKey='mealRotationTimeVisibilityV1';
const previousMarinateVisibility=localStorage.getItem('mealRotationShowMarinateV1')==='true';
let timeDisplayPrefs={top:{cooking:false,marinate:previousMarinateVisibility},category:{cooking:false,marinate:previousMarinateVisibility},all:{cooking:false,marinate:false}};
function setTimeDisplayPrefs(next){
  for(const view of ['top','category','all'])for(const field of ['cooking','marinate']){
    if(next&&next[view]&&typeof next[view][field]==='boolean')timeDisplayPrefs[view][field]=next[view][field];
  }
}
try{setTimeDisplayPrefs(JSON.parse(localStorage.getItem(timePreferencesStorageKey)||'null'))}catch(e){}
function saveTimeDisplayPrefs(){try{localStorage.setItem(timePreferencesStorageKey,JSON.stringify(timeDisplayPrefs))}catch(e){}}
const cookedDateVisibilityKey='mealRotationShowLastCookedV1';
let showLastCooked=localStorage.getItem(cookedDateVisibilityKey)!=='false';
const manualRecipeOrderingKey='mealRotationManualRecipeOrderingV1';
let manualRecipeOrdering=localStorage.getItem(manualRecipeOrderingKey)==='true';
function saveManualRecipeOrdering(){try{localStorage.setItem(manualRecipeOrderingKey,String(manualRecipeOrdering))}catch(e){}}
function saveLastCookedVisibility(){try{localStorage.setItem(cookedDateVisibilityKey,String(showLastCooked))}catch(e){}}
const mealChooserSortKey='mealRotationChooserCookedSortV1';
const mealChooserUndatedKey='mealRotationChooserIncludeUndatedV1';
let mealChooserSort=['oldest','newest','original'].includes(localStorage.getItem(mealChooserSortKey))?localStorage.getItem(mealChooserSortKey):'oldest';
let mealChooserIncludeUndated=localStorage.getItem(mealChooserUndatedKey)!=='false';

let groceryUndo=null;let topCounts={};try{const ts=JSON.parse(localStorage.getItem('mealRotationTopCountsV1')||'{}');if(ts&&typeof ts==='object')topCounts=ts}catch(e){}function getTopCount(c){return Number.isFinite(Number(topCounts[c]))?Math.max(0,Math.min(10,Number(topCounts[c]))):1}function saveTopCounts(){try{localStorage.setItem('mealRotationTopCountsV1',JSON.stringify(topCounts))}catch(e){}}const weekdays=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'];let weekdayCategories={};try{const wc=JSON.parse(localStorage.getItem('mealRotationWeekdayCategoriesV1')||'{}');if(wc&&typeof wc==='object')weekdayCategories=wc}catch(e){}// Optional recipe labels and per-plan weekday group filters.
const weekdayRecipeFiltersKey='mealRotationWeekdayRecipeFiltersV1';
let weekdayRecipeFilters={};try{weekdayRecipeFilters=JSON.parse(localStorage.getItem(weekdayRecipeFiltersKey)||'{}')||{}}catch(e){}
function saveWeekdayRecipeFilters(){try{localStorage.setItem(weekdayRecipeFiltersKey,JSON.stringify(weekdayRecipeFilters))}catch(e){}saveActiveMealPlan()}
const recipeLabelCatalogKey='mealRotationRecipeLabelCatalogV1';
let recipeLabelCatalog=[];try{const saved=JSON.parse(localStorage.getItem(recipeLabelCatalogKey)||'[]');if(Array.isArray(saved))recipeLabelCatalog=saved.filter(x=>typeof x==='string'&&x.trim()).map(x=>x.trim())}catch(e){}
function labelKey(x){return String(x).trim().replace(/\s+/g,' ').toLocaleLowerCase()}
function allRecipeLabels(){const result=new Map();for(const name of [...recipeLabelCatalog,...meals.flatMap(m=>Array.isArray(m.labels)?m.labels:[])]){const value=String(name).trim().replace(/\s+/g,' ');if(value&&!result.has(labelKey(value)))result.set(labelKey(value),value)}return [...result.values()].sort((a,b)=>a.localeCompare(b))}
function saveRecipeLabelCatalog(){localStorage.setItem(recipeLabelCatalogKey,JSON.stringify(recipeLabelCatalog))}

function recipeLabels(meal){return Array.isArray(meal.labels)?meal.labels.map(x=>String(x).trim()).filter(Boolean):[]}
// Legacy label fields remain restorable, but no longer constrain rotation.
function recipeMatchesFilters(){return true}
// Optional stable identities leave the existing name-based group memberships intact.
const GROUP_IDENTITIES_KEY='mealRotationGroupIdentitiesV1';
function readGroupIdentities(){const raw=localStorage.getItem(GROUP_IDENTITIES_KEY);if(!raw)return Object.create(null);const value=JSON.parse(raw);if(!value||Array.isArray(value)||typeof value!=='object'||Object.values(value).some(id=>typeof id!=='string'||!id))throw Error('Saved group identities could not be read. Restore a backup before changing side preferences.');return Object.assign(Object.create(null),value)}
function groupIdentity(name,create=false){const ids=readGroupIdentities();if(!Object.hasOwn(ids,name)&&create){ids[name]='group-'+(crypto.randomUUID?.()||Date.now()+'-'+Math.random().toString(36).slice(2));localStorage.setItem(GROUP_IDENTITIES_KEY,JSON.stringify(ids))}return Object.hasOwn(ids,name)?ids[name]:null}
function groupNameForIdentity(id){const ids=readGroupIdentities();return cats.find(cat=>Object.hasOwn(ids,cat)&&ids[cat]===id)||null}
function renameGroupIdentity(oldName,newName){const ids=readGroupIdentities();if(Object.hasOwn(ids,oldName)){ids[newName]=ids[oldName];delete ids[oldName];localStorage.setItem(GROUP_IDENTITIES_KEY,JSON.stringify(ids))}const next=JSON.parse(JSON.stringify(occurrenceScales));let changed=false;for(const entry of Object.values(next.occurrences))if(entry.context.cat===oldName){entry.context.cat=newName;changed=true}if(changed)writeOccurrenceScales(next)}
function removeGroupIdentity(name){const ids=readGroupIdentities();if(Object.hasOwn(ids,name)){delete ids[name];localStorage.setItem(GROUP_IDENTITIES_KEY,JSON.stringify(ids))}}
function renameDependentGroupState(oldName,newName){
 const id=groupIdentity(newName),relevant=mealPlans.some(p=>Object.values(p.sideGroupPairs||{}).some(pairs=>Object.hasOwn(pairs,id)||Object.values(pairs).includes(id)));if(!id||!relevant)return;
 for(const plan of mealPlans){for(const day of weekdays)for(const field of ['cycleRetainedSlots','cycleSlotChoices']){const map=plan[field],old=weekdaySlotKey(day,oldName);if(map&&Object.hasOwn(map,old)){map[weekdaySlotKey(day,newName)]=map[old];delete map[old]}}
  for(const key of Object.keys(plan.favoriteRotationScores||{})){let parts;try{parts=JSON.parse(key)}catch(e){continue}if(Array.isArray(parts)&&parts[0]===oldName){parts[0]=newName;plan.favoriteRotationScores[JSON.stringify(parts)]=plan.favoriteRotationScores[key];delete plan.favoriteRotationScores[key]}}
 }
}

function pairedMainGroup(plan,day,side){const sideId=groupIdentity(side),parent=sideId&&groupNameForIdentity(plan.sideGroupPairs?.[day]?.[sideId]);const raw=plan.weekdayCategories?.[day],groups=Array.isArray(raw)?raw:[raw];return parent&&parent!==side&&groups.includes(side)&&groups.includes(parent)?parent:null}
// Offline title vocabulary. Each row is bidirectional; custom terms match whole phrases.
const SERVE_WITH_SYNONYMS=[
 ['potato','potatoes','mash','mashed','spud','spuds'],
 ['rice','pilaf','risotto'],
 ['pasta','noodle','noodles','spaghetti','macaroni','penne','linguine','fettuccine'],
 ['vegetable','vegetables','veggie','veggies','broccoli','carrot','carrots','green beans','cauliflower'],
 ['bread','roll','rolls','biscuit','biscuits','toast','garlic bread']
];
function serveWithWords(value){return String(value||'').normalize('NFKC').toLowerCase().replace(/[’']/g,'').replace(/[^\p{L}\p{N}]+/gu,' ').trim().split(/\s+/).filter(Boolean).map(word=>word.length>4&&word.endsWith('ies')?word.slice(0,-3)+'y':word.length>4&&/(oes|ches|shes|xes|zes)$/.test(word)?word.slice(0,-2):word.length>3&&word.endsWith('s')&&!/(ss|us|is)$/.test(word)?word.slice(0,-1):word).join(' ')}
function normalizeServeWith(value){return [...new Map((Array.isArray(value)?value:[]).filter(v=>typeof v==='string').map(v=>v.trim()).filter(v=>serveWithWords(v)).map(v=>[serveWithWords(v),v])).values()]}
function serveWithMatches(title,preferences){const text=' '+serveWithWords(title)+' ';return normalizeServeWith(preferences).some(value=>{const term=serveWithWords(value),exact=text.includes(' '+term+' ');if(exact)return true;return SERVE_WITH_SYNONYMS.some(words=>words.some(word=>serveWithWords(word)===term)&&words.some(word=>text.includes(' '+serveWithWords(word)+' ')))})}
function sideServeWith(plan,day,side,entries){const parent=pairedMainGroup(plan,day,side),main=parent&&entries?.find(item=>item.day===day&&item.cat===parent)?.meal;return normalizeServeWith(main?.serveWith)}
function automaticSlotCandidates(plan,day,cat,library=meals,entries=null){return dependentSideCandidates(plan,day,cat,library,entries||getDisplayedWeekdayMealsForPlan(plan))}
function hasDependentSideSlots(){return mealPlans.some(plan=>Object.values(plan.sideGroupPairs||{}).some(pairs=>Object.keys(pairs||{}).length))}
function dependentSideKey(day,cat){const id=groupIdentity(cat);return id?JSON.stringify([day,id]):null}
function sharedRecipeIdentity(meal){return meal?.linkGroup?'shared:'+meal.linkGroup:'recipe:'+String(meal?.id)}
function dependentSideAutomatic(plan,entry,entries){return !!entry?.dependentSide&&!manualWeekdayMealChoice(plan,entry.day,entry.cat,entry.meal.id)&&entry.linkedTo==null&&!entries.some(parent=>parent.day===entry.day&&parent!==entry&&(parent.meal.linkedMealIds||[]).some(id=>String(id)===String(entry.meal.id)))}
function rememberDependentSideState(plan,entries,replace=false){
 for(const day of weekdays){const raw=plan.weekdayCategories?.[day];for(const cat of Array.isArray(raw)?raw:[raw]){if(!cat)continue;const parent=pairedMainGroup(plan,day,cat);if(!parent)continue;const key=dependentSideKey(day,cat);if(!replace&&plan.dependentSideState?.[key])continue;const main=entries.find(item=>item.day===day&&item.cat===parent),side=entries.find(item=>item.day===day&&item.cat===cat);plan.dependentSideState={...(plan.dependentSideState||{}),[key]:{mainId:main?String(main.meal.id):'',mealId:side?String(side.meal.id):'',automatic:dependentSideAutomatic(plan,side,entries)&&plan.cycleSlotChoices?.[weekdaySlotKey(day,parent)]?.preserveSideQueue!==true}}}}
}
function dependentSideCandidates(plan,day,cat,library,entries){
 const parent=pairedMainGroup(plan,day,cat);if(!parent)return automaticRecipeCandidates(cat,[],library,plan);
 if(!entries.some(item=>item.day===day&&item.cat===parent))return [];
 const preferences=sideServeWith(plan,day,cat,entries),pool=automaticRecipeCandidates(cat,[],library,plan);
 return preferences.length?pool.filter(meal=>serveWithMatches(meal.name,preferences)):pool;
}
// Only the selected source membership advances; other side-group queues stay intact.
function advanceDependentSource(plan,meal){
 if(!meal?.rotation)return;advanceFavoriteRotation(plan,meal.cat,meal);
 const slots=[];meals.forEach((record,index)=>{if(record.cat===meal.cat&&record.rotation)slots.push(index)});const records=slots.map(index=>meals[index]);const ordered=records.filter(record=>String(record.id)!==String(meal.id)).concat(records.filter(record=>String(record.id)===String(meal.id)));slots.forEach((index,i)=>meals[index]=ordered[i]);
}
let coordinatingDependentSides=false;
function coordinateDependentSides(restore=false){
 if(coordinatingDependentSides||restoringRotationCalendars||groceryCheckStorageInvalid)return false;coordinatingDependentSides=true;let changed=false;
 try{
  for(const plan of mealPlans){
   if(!plan.sideGroupPairs)continue;if(plan.id===activePlanId)plan.weekdayMealOverrides={...weekdayMealOverrides};
   let entries=getDisplayedWeekdayMealsForPlan(plan,null,null,null,true);rememberDependentSideState(plan,entries);
   for(const day of weekdays){const raw=plan.weekdayCategories?.[day];for(const cat of Array.isArray(raw)?raw:[raw]){
    if(!cat)continue;const parent=pairedMainGroup(plan,day,cat);if(!parent)continue;const stateKey=dependentSideKey(day,cat),old=plan.dependentSideState[stateKey],main=entries.find(item=>item.day===day&&item.cat===parent),mainId=main?String(main.meal.id):'';
    if(!restore&&old.mainId!==mainId){
     const outgoing=meals.find(meal=>String(meal.id)===String(old.mealId));if(old.automatic&&outgoing&&plan.cycleSlotChoices?.[weekdaySlotKey(day,parent)]?.preserveSideQueue!==true)advanceDependentSource(plan,outgoing);
     const key=weekdaySlotKey(day,cat),prior=plan.cycleSlotChoices?.[key]||{};plan.weekdayMealOverrides={...(plan.weekdayMealOverrides||{})};plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{})};delete plan.weekdayMealOverrides[key];delete plan.cycleRetainedSlots[key];if((Array.isArray(raw)?raw:[raw])[0]===cat)delete plan.weekdayMealOverrides[day];
     plan.cycleSlotChoices={...(plan.cycleSlotChoices||{}),[key]:{parentId:'',blockedParents:[],avoidMealId:outgoing?String(outgoing.id):String(prior.avoidMealId||''),previousGroupId:outgoing?groupIdentity(outgoing.cat):prior.previousGroupId}};
     if(plan.id===activePlanId)weekdayMealOverrides={...plan.weekdayMealOverrides};entries=getDisplayedWeekdayMealsForPlan(plan,null,null,null,true);const selected=entries.find(item=>item.day===day&&item.cat===cat);
     if(selected){plan.weekdayMealOverrides[key]=String(selected.meal.id);plan.cycleRetainedSlots[key]=String(selected.meal.id);plan.cycleSlotChoices[key]={...plan.cycleSlotChoices[key],mealId:String(selected.meal.id),parentId:String(selected.linkedTo??'')};resolveRotatedMealSlots(plan,[selected],entries.filter(item=>item.day!==day||item.cat!==cat))}
     else plan.cycleSlotChoices[key]={...plan.cycleSlotChoices[key],empty:true,sideUnavailable:true};
     if(plan.id===activePlanId)weekdayMealOverrides={...plan.weekdayMealOverrides};changed=true;
    }
   }}
   entries=getDisplayedWeekdayMealsForPlan(plan,null,null,null,true);rememberDependentSideState(plan,entries,true);
  }
  return changed;
 }finally{coordinatingDependentSides=false}
}
function linkedRecipePlacement(plan,day,parent,target,entries,library=meals){
 if(rotationGroupScheduled(plan,day,target.cat))return target.cat;
 const raw=plan.weekdayCategories?.[day],groups=(Array.isArray(raw)?raw:[raw]).filter(Boolean),identity=sharedRecipeIdentity(target);
 const matches=groups.filter(cat=>pairedMainGroup(plan,day,cat)===parent.cat&&(library.some(peer=>peer.cat===cat&&sharedRecipeIdentity(peer)===identity)||serveWithMatches(target.name,sideServeWith(plan,day,cat,entries))||String(plan.dependentSideState?.[dependentSideKey(day,cat)]?.mealId||'')===String(target.id)));
 return matches.length===1?matches[0]:target.cat;
}
function setSideGroupPair(plan,day,side,parent){
 if(groceryCheckStorageInvalid)throw Error('Saved grocery selections could not be read. No group role was changed.');if(pairedMainGroup(plan,day,side)===(parent||null))return;
 applyRecipeBulk([],{}, {render:false,dependentRole:{planId:plan.id,day,side,parent}});bulkRecipeRender();
}
function applyDependentRoleMutation(change,transaction){
 const {day,side,parent}=change,plan=mealPlans.find(plan=>plan.id===change.planId);if(!plan)throw Error('The meal plan no longer exists.');const groups=(Array.isArray(plan.weekdayCategories?.[day])?plan.weekdayCategories[day]:[plan.weekdayCategories?.[day]]).filter(cat=>cats.includes(cat));
 if(!groups.includes(side)||parent&&(!groups.includes(parent)||parent===side))throw Error('Choose another assigned main group.');
 const sideId=groupIdentity(side,true),parentId=parent?groupIdentity(parent,true):null,activeIds=new Set(groups.map(cat=>groupIdentity(cat)).filter(Boolean)),pairs=Object.fromEntries(Object.entries(plan.sideGroupPairs?.[day]||{}).filter(([side,main])=>activeIds.has(side)&&activeIds.has(main)));if(parentId)pairs[sideId]=parentId;else delete pairs[sideId];
 if(parentId&&(pairs[parentId]||Object.values(pairs).some(id=>id===sideId)))throw Error('A side group cannot also be a main group on this day.');
 const entries=transaction.schedules.get(plan.id)||[],oldSide=entries.find(item=>item.day===day&&item.cat===side),automatic=dependentSideAutomatic(plan,oldSide,entries);plan.sideGroupPairs={...(plan.sideGroupPairs||{}),[day]:pairs};const key=dependentSideKey(day,side);
 if(parentId)plan.dependentSideState={...(plan.dependentSideState||{}),[key]:{mainId:'__role_changed__',mealId:oldSide?String(oldSide.meal.id):'',automatic}};
 else{delete plan.dependentSideState?.[key];if(oldSide&&oldSide.meal.cat!==side){const choice=plan.cycleSlotChoices?.[weekdaySlotKey(day,side)];if(choice){choice.substitution=true;choice.retain=true}}}
 transaction.allowedDays.push({planId:plan.id,day});
}
function buildSidePairControls(holder,day){
 holder.replaceChildren();const assigned=getDayCategories(day);if(assigned.length<2)return;const plan=mealPlans.find(p=>p.id===activePlanId);
 for(const side of assigned){const row=document.createElement('div');row.style.cssText='display:flex;align-items:center;gap:8px;margin-top:5px;font-size:13px';const name=document.createElement('span');name.textContent=side;name.style.cssText='flex:1;min-width:0;overflow-wrap:anywhere';const button=document.createElement('button');button.type='button';button.className='smallbtn';const parent=pairedMainGroup(plan,day,side);button.textContent=parent?'Dependent side · '+parent:'Independent';button.style.cssText='max-width:65%;min-height:44px;white-space:normal;overflow-wrap:anywhere;text-align:left';button.setAttribute('aria-label','Side for '+side);button.onclick=()=>chooseBulkValue('Side for '+side,parent||'',()=>[['','Independent'],...assigned.filter(cat=>cat!==side).map(cat=>[cat,'Dependent side for '+cat])],value=>{try{setSideGroupPair(plan,day,side,value);buildSidePairControls(holder,day)}catch(e){showAppMessage(e.message)}},false,()=>[...holder.querySelectorAll('button')].find(el=>el.getAttribute('aria-label')==='Side for '+side));row.append(name,button);holder.append(row)}
}
function chooseServeWith(value,onSave){
 const dialog=recipeBulkDialog('Serve with'),list=document.createElement('div');list.className='recipe-bulk-choice-list';const draft=new Set(normalizeServeWith(value));
 function render(){list.replaceChildren();for(const name of normalizeServeWith(['Rice','Potatoes','Pasta','Vegetables','Bread',...draft])){const label=document.createElement('label');label.className='recipe-bulk-choice';const input=document.createElement('input');input.type='checkbox';input.className='check';input.checked=[...draft].some(v=>serveWithWords(v)===serveWithWords(name));input.onchange=()=>{for(const v of draft)if(serveWithWords(v)===serveWithWords(name))draft.delete(v);if(input.checked)draft.add(name)};label.append(input,document.createTextNode(name));list.append(label)}}
 const custom=document.createElement('input');custom.type='text';custom.placeholder='Custom keyword';custom.setAttribute('aria-label','Custom Serve with keyword');const add=document.createElement('button');add.type='button';add.className='smallbtn';add.textContent='+';add.setAttribute('aria-label','Add Serve with keyword');function addCustom(){const name=custom.value.trim();if(!serveWithWords(name))return;draft.add(name);custom.value='';render()}add.onclick=addCustom;custom.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();addCustom()}};const row=document.createElement('div');row.style.cssText='display:flex;gap:8px;align-items:center';custom.style.minWidth='0';row.append(custom,add);
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Save Serve with');setIconButton(cancel,'cancel','Cancel Serve with');save.onclick=()=>{if(custom.value.trim())addCustom();onSave(normalizeServeWith([...draft]));dialog.close()};cancel.onclick=dialog.close;actions.append(save,cancel);render();dialog.panel.append(list,row,actions);cancel.focus({preventScroll:true});
}

const EMPTY_DAY_ASSIGNMENT="__meal_rotation_empty_day__";
function isEmptyDay(day,assignments=weekdayCategories){
 const value=assignments[day];return (Array.isArray(value)?value:[value]).includes(EMPTY_DAY_ASSIGNMENT);
}
function getDayCategories(day){
  const raw=weekdayCategories[day];
  return [...new Set((Array.isArray(raw)?raw:[raw]).filter(c=>typeof c==='string'&&cats.includes(c)))];
}
function saveWeekdayCategories(){
  try{localStorage.setItem('mealRotationWeekdayCategoriesV1',JSON.stringify(weekdayCategories))}catch(e){}
  if(typeof mealPlans!=='undefined')saveActiveMealPlan();
}
function weekdaySlotKey(day,cat){return day+'::'+cat}
function boundOccasionalGroup(plan,day){
 const id=plan.occasionalMeals?.[day];if(id==null)return null;
 const prefix=day+'::';return Object.entries(plan.cycleSlotChoices||{}).find(([key,choice])=>key.startsWith(prefix)&&key!==prefix+'@day'&&choice.occasional===true&&String(choice.mealId)===String(id))?.[0].slice(prefix.length)||null;
}
function unassignedWeekGroupSlots(plan,day,assigned,entries=getDisplayedWeekdayMealsForPlan(plan)){
 const linkedMasks=new Set();
 for(const parent of entries)if(parent.day===day&&(assigned.includes(parent.cat)||parent.cat==='@day'||parent.occasional))for(const id of parent.meal.linkedMealIds||[]){const side=meals.find(meal=>String(meal.id)===String(id));if(side){linkedMasks.add(side.cat);linkedMasks.add(linkedRecipePlacement(plan,day,parent,side,entries))}}
 const orphaned=[];for(const [key,item]of Object.entries(weekSchedule(plan).slots)){const prefix=day+'::';if(key.startsWith(prefix)){const cat=key.slice(prefix.length);if(cat!=='@day'&&!assigned.includes(cat)&&(item.kind==='once'||!linkedMasks.has(cat)))orphaned.push(cat)}}
 const owner=boundOccasionalGroup(plan,day);if(owner&&owner!=='@day'&&!assigned.includes(owner))orphaned.push(owner);
 return {orphaned,linkedMasks};
}
function setDayCategories(day,values){
  const previous=getDayCategories(day);
  const next=values.includes(EMPTY_DAY_ASSIGNMENT)?[EMPTY_DAY_ASSIGNMENT]:[...new Set(values.filter(c=>cats.includes(c)&&groupUsesRotation(c)))];
  const plan=mealPlans.find(plan=>plan.id===activePlanId),occasional=meals.find(meal=>String(meal.id)===String(plan?.occasionalMeals?.[day]));
  const occasionalOwner=boundOccasionalGroup(plan,day),removeOccasional=occasionalOwner&&!next.includes(occasionalOwner);
  const groceryBefore=captureGroceryCheckStates(),schedules=new Map(mealPlans.map(p=>[p.id,getDisplayedWeekdayMealsForPlan(p.id===activePlanId?{...p,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:p)]));
  snapshot();preserveOtherMealPlanChoices(null,null,schedules);if(removeOccasional)delete plan.occasionalMeals[day];
  const {orphaned,linkedMasks}=unassignedWeekGroupSlots(plan,day,next,schedules.get(plan.id)||[]),removed=new Set([...previous.filter(cat=>!next.includes(cat)),...orphaned,...(removeOccasional?[occasionalOwner]:[])]);
  // Delete only unassigned group state; day-only meals and deliberate linked
  // side masks remain valid even without an independent group assignment.
  for(const cat of new Set([...previous,...next,...removed]))if(previous.includes(cat)!==next.includes(cat)||removed.has(cat)){
   const key=weekdaySlotKey(day,cat);delete weekdayMealOverrides[key];delete plan.cycleRetainedSlots?.[key];delete plan.cycleSlotChoices?.[key];
   if(removed.has(cat)){if(weekSchedule(plan).slots[temporarySlotKey(day,cat)]?.kind!=='empty'||!linkedMasks.has(cat))clearTemporarySlot(plan,day,cat);const sideKey=dependentSideKey(day,cat);if(sideKey)delete plan.dependentSideState?.[sideKey]}
  }
  weekdayCategories[day]=next;
  for(const c of previous)if(!next.includes(c)){delete weekdayMealOverrides[weekdaySlotKey(day,c)];}saveWeekdayRecipeFilters();
  delete weekdayMealOverrides[day];
  if(occasional&&!removeOccasional&&(occasionalOwner||!previous.length)&&next.some(cat=>cats.includes(cat))&&(next.includes(occasional.cat)||!(occasional.linkedMealIds||[]).some(id=>meals.some(meal=>String(meal.id)===String(id)&&next.includes(meal.cat))))){
   const cat=occasionalOwner&&next.includes(occasionalOwner)?occasionalOwner:next.includes(occasional.cat)?occasional.cat:next.find(cat=>cats.includes(cat)),key=weekdaySlotKey(day,cat);
   weekdayMealOverrides[key]=String(occasional.id);plan.cycleRetainedSlots={...(plan.cycleRetainedSlots||{}),[key]:String(occasional.id)};
   plan.cycleSlotChoices={...(plan.cycleSlotChoices||{}),[key]:{mealId:String(occasional.id),parentId:'',retain:true,substitution:true,occasional:true,blockedParents:[]}};
  }
  saveWeekdayCategories();saveWeekdayMealOverrides();
  if(groceryBefore){
   reconcileRotatedGroceryChecks(groceryBefore,[]);
   // Settings Cancel may restore the pre-assignment slots; keep their exact checks too.
   preserveGroceryCheckStates(groceryBefore);
   for(const source of getGroceryContributions(true))if(!groceryBefore.has(source.id)){
    const token=JSON.parse(source.id),previous=[...groceryBefore.values()].find(item=>item.source.planId===source.planId&&item.source.day===source.day&&String(item.source.mealId)===String(source.mealId)&&JSON.stringify(JSON.parse(item.source.id).slice(1))===JSON.stringify(token.slice(1)));
    if(previous){groceryOccurrenceChecks.checks[source.id]=previous.checked;if(previous.amount)(groceryOccurrenceChecks.quantities??={})[source.id]={...previous.amount}}
   }
   saveGroceryOccurrenceChecks();
  }
  renderTabs();renderList();
}
let startWeekday=localStorage.getItem('mealRotationStartWeekdayV1')||'Monday';let pinnedCats=[];try{pinnedCats=JSON.parse(localStorage.getItem('mealRotationPinnedCategoriesV1')||'[]')}catch(e){}let expandedCats=[];try{expandedCats=JSON.parse(localStorage.getItem('mealRotationExpandedCategoriesV1')||'[]')}catch(e){}
let autoPinTopCategories=true;
let applyPinsToAllTabs=localStorage.getItem('mealRotationApplyPinsAllTabsV1')==='true';
// Master Categories opening behavior. These two checkbox options are exclusive.
let masterOpenMode=localStorage.getItem('mealRotationMasterOpenModeV1')||'all';
if(!['all','current','across','none'].includes(masterOpenMode))masterOpenMode='all';
let masterPinsOverride=localStorage.getItem('mealRotationMasterPinsOverrideV1')!=='false';
function saveMasterOpeningPrefs(){localStorage.setItem('mealRotationMasterOpenModeV1',masterOpenMode);localStorage.setItem('mealRotationMasterPinsOverrideV1',String(masterPinsOverride))}

let groceryTabOpen=false,groceryTabActive=false,allMealsActive=false;
const masterGroceryPlanExclusionsKey='mealRotationMasterGroceryExcludedPlansV1';
let masterGroceryExcludedPlanIds=new Set();
try{const stored=JSON.parse(localStorage.getItem(masterGroceryPlanExclusionsKey)||'[]');if(Array.isArray(stored))masterGroceryExcludedPlanIds=new Set(stored.map(String))}catch(e){}
const masterGroceryMealExclusionsKey='mealRotationMasterGroceryExcludedMealsV1';
let masterGroceryExcludedMealKeys=new Set();
try{const stored=JSON.parse(localStorage.getItem(masterGroceryMealExclusionsKey)||'[]');if(Array.isArray(stored))masterGroceryExcludedMealKeys=new Set(stored.map(String))}catch(e){}
function saveMasterGroceryMealExclusions(){try{localStorage.setItem(masterGroceryMealExclusionsKey,JSON.stringify([...masterGroceryExcludedMealKeys]))}catch(e){}}
function groceryMealKey(plan,meal){return String(plan.id)+'::'+String(meal.id)}
function saveMasterGroceryPlanExclusions(){try{localStorage.setItem(masterGroceryPlanExclusionsKey,JSON.stringify([...masterGroceryExcludedPlanIds]))}catch(e){}}

let lastTopPinnedCategories=new Set();
// Manually pinned categories always remain available. Automatic pinning
// follows the ACTIVE meal-plan tab and its own saved checkbox.
function effectivePinnedCategories(){
 // Automatic shortcuts represent groups with meals actually displayed in
 // the active plan's weekly rotation, not merely scheduled empty groups.
 const plan=mealPlans.find(p=>p.id===activePlanId);
 const assigned=plan?getDisplayedWeekdayMealsForPlan(plan).filter(entry=>!entry.linkedTo).map(entry=>entry.cat):[];
 const manual=applyPinsToAllTabs?
  mealPlans.flatMap(p=>Array.isArray(p.pinnedCats)?p.pinnedCats:[]):pinnedCats;
 return new Set([...manual,...assigned].filter(c=>cats.includes(c)));
}const catColors=['#e9f1fc','#e9f4ed','#fff1df','#f3eafa','#e9f4f3','#fff0ef','#f1f1e5','#eef0fa'];let categoryColors={};try{const savedColors=JSON.parse(localStorage.getItem('mealRotationCategoryColorsV1')||'{}');if(savedColors&&typeof savedColors==='object'&&!Array.isArray(savedColors))categoryColors=Object.fromEntries(Object.entries(savedColors).filter(([name,color])=>typeof name==='string'&&/^#[0-9a-fA-F]{6}$/.test(color)))}catch(e){}
function saveCategoryColors(){try{localStorage.setItem('mealRotationCategoryColorsV1',JSON.stringify(categoryColors))}catch(e){}}
const defaultColorForCat=c=>c==='Weekend'?catColors[Math.max(0,cats.indexOf('Misc'))%catColors.length]:c==='Misc'?'#eee7df':catColors[Math.max(0,cats.indexOf(c))%catColors.length];
// Color is attached to the weekday, not to the category assigned to it.
// Existing category colors are used once to preserve familiar colors during migration.
const weekdayColorDefaults={Tuesday:'#D1DEC0',Wednesday:'#F6DEAA',Thursday:'#E0CDE4',Friday:'#EDC2B3',Saturday:'#C9E5DC',Sunday:'#E9C5CC',Monday:'#D1DCEA'};
// Shortcut colors retain a little more definition than the larger meal cards.
const weekdayShortcutColors={Tuesday:'#C5D6AE',Wednesday:'#F3D493',Thursday:'#D7BFDC',Friday:'#E9B19E',Saturday:'#B8DCD0',Sunday:'#E2B3BD',Monday:'#C2D1E4'};
let weekdayColors={};
try{const stored=JSON.parse(localStorage.getItem('mealRotationWeekdayColorsV1')||'{}');if(stored&&typeof stored==='object'&&!Array.isArray(stored))weekdayColors=Object.fromEntries(Object.entries(stored).filter(([d,color])=>weekdays.includes(d)&&/^#[0-9a-fA-F]{6}$/.test(color)))}catch(e){}
function saveWeekdayColors(){weekdayColors={...weekdayColorDefaults};try{localStorage.setItem('mealRotationWeekdayColorsV1',JSON.stringify(weekdayColors))}catch(e){}}
function deriveWeekdayColors(legacy=categoryColors){return Object.fromEntries(weekdays.map(day=>{const cat=getDayCategories(day)[0];return [day,cat?(legacy[cat]||defaultColorForCat(cat)):weekdayColorDefaults[day]]}))}
const colorForDay=day=>weekdayColorDefaults[day]||'#ffffff';
// A category assigned to several weekdays displays every assigned day's color.
// This is derived from the active plan, so no saved category data is changed.
const colorForCat=c=>{
 const colors=[...new Set(orderedDays().filter(d=>getDayCategories(d).includes(c)).map(d=>weekdayShortcutColors[d]||colorForDay(d)))];
 if(!colors.length)return '#ffffff';
 if(colors.length===1)return colors[0];
 const stops=colors.flatMap((color,i)=>[`${color} ${100*i/colors.length}%`,`${color} ${100*(i+1)/colors.length}%`]);
 return `linear-gradient(90deg, ${stops.join(', ')})`;
};
function applyCategoryBackground(element,category){
 const color=colorForCat(category);
 element.style.background=color;
}

function orderedDays(){const n=weekdays.indexOf(startWeekday);return weekdays.slice(n<0?0:n).concat(weekdays.slice(0,n<0?0:n))}function clearOverridesForCat(c){
  for(const day of weekdays){
    if(manualWeekdayMealChoice({...mealPlans.find(p=>p.id===activePlanId),weekdayCategories,weekdayMealOverrides},day,c))continue;
    delete weekdayMealOverrides[weekdaySlotKey(day,c)];
    if(getDayCategories(day)[0]===c)delete weekdayMealOverrides[day];
  }
  saveWeekdayMealOverrides();
}
// Manual choices survive unrelated queue changes; explicit cycling expires them.
// Older explicit
// overrides without a cycle pin remain protected without migrating saved data.
function manualWeekdayMealChoice(plan,day,cat,mealId=null){
 const key=weekdaySlotKey(day,cat),raw=plan?.weekdayCategories?.[day],groups=Array.isArray(raw)?raw:[raw];
 const chosen=plan?.weekdayMealOverrides?.[key]??(groups[0]===cat?plan?.weekdayMealOverrides?.[day]:undefined);
 if(chosen==null||(mealId!=null&&String(chosen)!==String(mealId)))return false;
 const choice=plan.cycleSlotChoices?.[key];
 if(choice&&String(choice.mealId)===String(chosen))return choice.substitution===true;
 return !choice&&String(plan.cycleRetainedSlots?.[key]??'')!==String(chosen);
}
function getWeekdayOverride(day,cat){
  return weekdayMealOverrides[weekdaySlotKey(day,cat)]??
    (getDayCategories(day)[0]===cat?weekdayMealOverrides[day]:undefined);
}
function setWeekdayOverride(day,cat,mealId){
  weekdayMealOverrides[weekdaySlotKey(day,cat)]=String(mealId);
  if(getDayCategories(day)[0]===cat)delete weekdayMealOverrides[day];
}
function clearWeekdayOverride(day,cat){
  delete weekdayMealOverrides[weekdaySlotKey(day,cat)];
  if(getDayCategories(day)[0]===cat)delete weekdayMealOverrides[day];
}
let weekdayMealOverrides={};try{const wo=JSON.parse(localStorage.getItem('mealRotationWeekdayMealOverridesV1')||'{}');if(wo&&typeof wo==='object')weekdayMealOverrides=wo}catch(e){}function saveWeekdayMealOverrides(){try{localStorage.setItem('mealRotationWeekdayMealOverridesV1',JSON.stringify(weekdayMealOverrides))}catch(e){}if(typeof mealPlans!=='undefined')saveActiveMealPlan()}
migrateSavedIngredientFractions();
let meals=[];let hasValidSavedData=false;try{const saved=localStorage.getItem('mealRotationDataV1');if(saved){const d=JSON.parse(saved);if(Array.isArray(d.cats)&&Array.isArray(d.meals)){cats=d.cats;meals=d.meals.map(m=>normalizeRecipeStatus({...m,ingredients:Array.isArray(m.ingredients)?m.ingredients:[]}));for(const meal of meals)if(meal.linkGroup)meal.upNextStar=meals.some(peer=>peer.linkGroup===meal.linkGroup&&peer.upNextStar===true);id=Math.max(0,...meals.map(m=>Number(m.id)||0))+1;active=cats.includes(d.active)?d.active:(cats[0]||'Chicken');hasValidSavedData=true}}}catch(e){}
// New installations begin with three editable example groups and no recipes.
weekdayColors={...weekdayColorDefaults};saveWeekdayColors();
// Keep Top Recipes as the default landing page, but restore the current view
// when this browser tab refreshes. A fresh navigation still opens Top Recipes.
// Meal-plan tabs: keep this plan's weekday selection and individual meal overrides separate.

// Saved globally, independently of recipes and meal-plan tabs.
const mealTextSizeKey='mealRotationTextSizeV1';
let mealTextSize=localStorage.getItem(mealTextSizeKey)||'normal';
if(!['normal','large','extra'].includes(mealTextSize))mealTextSize='normal';
function applyMealTextSize(){document.body.dataset.mealTextSize=mealTextSize;}
applyMealTextSize();
const mealPlansKey='mealRotationPlansV1';
// Only brand-new installations receive the three starter plans. Existing saved
// installations retain their own plan names, order, and visibility preference.
const isFirstMealPlanSetup=!hasValidSavedData && localStorage.getItem('mealRotationPlansV1')===null;
const starterDinner={id:'original',name:isFirstMealPlanSetup?'Dinner':'Meal Plan',weekdayCategories:JSON.parse(JSON.stringify(weekdayCategories)),weekdayMealOverrides:{...weekdayMealOverrides},weekdayRecipeFilters:JSON.parse(JSON.stringify(weekdayRecipeFilters)),autoPinTopCategories};
let mealPlans=isFirstMealPlanSetup?[
 {id:'starter-breakfast',name:'Breakfast',weekdayCategories:{},weekdayMealOverrides:{},weekdayRecipeFilters:{},autoPinTopCategories:false,pinnedCats:[]},
 {id:'starter-lunch',name:'Lunch',weekdayCategories:{},weekdayMealOverrides:{},weekdayRecipeFilters:{},autoPinTopCategories:false,pinnedCats:[]},
 starterDinner
]:[starterDinner];
let activePlanId='original';
const savedTabVisibility=localStorage.getItem('mealRotationShowPlanTabsV1');
let showMealPlanTabs=savedTabVisibility===null?isFirstMealPlanSetup:savedTabVisibility==='true';
try{
 const stored=JSON.parse(localStorage.getItem(mealPlansKey)||'null');
 if(stored&&Array.isArray(stored.plans)&&stored.plans.length){
  const valid=stored.plans.filter(p=>p&&typeof p.id==='string'&&typeof p.name==='string'&&p.weekdayCategories&&typeof p.weekdayCategories==='object');
  if(valid.length){mealPlans=valid;
   mealPlans.forEach(p=>{if(typeof p.autoPinTopCategories!=='boolean')p.autoPinTopCategories=p.id==='original'?autoPinTopCategories:true});
   activePlanId=valid.some(p=>p.id===stored.activeId)?stored.activeId:valid[0].id;
   const selected=mealPlans.find(p=>p.id===activePlanId);
   autoPinTopCategories=true;
   weekdayCategories=JSON.parse(JSON.stringify(selected.weekdayCategories));
   weekdayMealOverrides={...(selected.weekdayMealOverrides||{})};
  }
 }
}catch(e){}
// Keep manual pins independent per tab, while retaining the user's existing pins.
mealPlans.forEach(plan=>{
 if(!Array.isArray(plan.pinnedCats))plan.pinnedCats=plan.id===activePlanId?[...pinnedCats]:[];
});
pinnedCats=[...(mealPlans.find(p=>p.id===activePlanId)?.pinnedCats||[])];
if(isFirstMealPlanSetup){try{localStorage.setItem('mealRotationPlansV1',JSON.stringify({plans:mealPlans,activeId:activePlanId}));localStorage.setItem('mealRotationShowPlanTabsV1',String(showMealPlanTabs))}catch(e){}}
function saveActiveMealPlan(){
 const plan=mealPlans.find(p=>p.id===activePlanId);
 if(plan){plan.weekdayCategories=JSON.parse(JSON.stringify(weekdayCategories));plan.weekdayMealOverrides={...weekdayMealOverrides};plan.autoPinTopCategories=autoPinTopCategories;plan.pinnedCats=[...pinnedCats];plan.weekdayRecipeFilters=JSON.parse(JSON.stringify(weekdayRecipeFilters));}
 reconcileRotationCalendars();
 try{localStorage.setItem(mealPlansKey,JSON.stringify({plans:mealPlans,activeId:activePlanId}))}catch(e){}
}
function loadMealPlan(planId,renderView=true){
 const plan=mealPlans.find(p=>p.id===planId);if(!plan)return;
 saveActiveMealPlan();activePlanId=planId;
 weekdayCategories=JSON.parse(JSON.stringify(plan.weekdayCategories||{}));
 weekdayMealOverrides={...(plan.weekdayMealOverrides||{})};weekdayRecipeFilters=JSON.parse(JSON.stringify(plan.weekdayRecipeFilters||{}));try{localStorage.setItem(weekdayRecipeFiltersKey,JSON.stringify(weekdayRecipeFilters))}catch(e){}
 autoPinTopCategories=true;pinnedCats=[...(plan.pinnedCats||[])];
 groceryTabActive=false;allMealsActive=false;saveActiveMealPlan();
 try{localStorage.setItem('mealRotationWeekdayCategoriesV1',JSON.stringify(weekdayCategories));localStorage.setItem('mealRotationWeekdayMealOverridesV1',JSON.stringify(weekdayMealOverrides))}catch(e){}
 topIngredientExpanded.clear();topIngredientManualHiddenOverride.clear();
 showTop=true;editId=null;menuCat=null;if(renderView)render();
}
function nextMealPlanId(){return 'plan-'+Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,8)}
// Stage 2 entry points reuse the existing plan and manual-slot formats.
function stage2FormField(parent,label,control){const wrap=document.createElement('label');wrap.className='recipe-bulk-field';const text=document.createElement('span');text.textContent=label;control.setAttribute('aria-label',label);if(control.type==='checkbox'){wrap.style.cssText='flex-direction:row;align-items:center;min-height:44px;gap:10px';control.style.cssText='width:20px;height:20px;min-height:20px;flex:none;margin:0';wrap.append(control,text)}else{if(control.tagName==='TEXTAREA')control.style.cssText='width:100%;box-sizing:border-box;padding:8px;border:1px solid #cfd5dd;border-radius:7px;font:inherit;resize:vertical';wrap.append(text,control)}parent.append(wrap);return control}
function stage2Select(items){const select=document.createElement('select');for(const [value,label]of items){const option=document.createElement('option');option.value=value;option.textContent=label;select.append(option)}return select}
function openAddMealTabDialog(){
 if(editId!==null){showAppMessage('Save or cancel the open recipe first.');return}
 const d=recipeBulkDialog('Add Meal Tab'),field=document.createElement('input');field.type='text';field.placeholder='Tab name';
 const suggestions=document.createElement('div');suggestions.style.cssText='display:flex;gap:8px;flex-wrap:wrap';
 for(const name of ['Breakfast','Lunch','Dinner'])if(!mealPlans.some(plan=>plan.name.trim().toLowerCase()===name.toLowerCase())){const button=document.createElement('button');button.type='button';button.className='smallbtn';button.textContent=name;button.style.minHeight='44px';button.onclick=()=>{field.value=name;field.focus()};suggestions.append(button)}
 d.panel.append(suggestions);stage2FormField(d.panel,'Tab name',field);field.previousElementSibling.remove();const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');d.panel.append(error);
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Add tab');setIconButton(cancel,'cancel','Cancel');cancel.onclick=d.close;
 save.onclick=()=>{const name=field.value.trim();if(!name){error.textContent='Enter a tab name.';field.focus();return}if(mealPlans.some(plan=>plan.name.trim().toLowerCase()===name.toLowerCase())){error.textContent='A meal tab with that name already exists.';return}d.close();navigateAfterSettings(()=>createMealPlan(name))};
 field.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();save.click()}};actions.append(save,cancel);d.panel.append(actions);field.focus();
}
function validateScheduleTarget(target){
 const plan=mealPlans.find(plan=>plan.id===target.planId);if(!plan||!weekdays.includes(target.day))throw Error('The selected meal tab or weekday is no longer available.');
 const raw=plan.weekdayCategories?.[target.day],groups=(Array.isArray(raw)?raw:[raw]).filter(cat=>cats.includes(cat));
 if(groups.length&&!target.occasional&&!groups.includes(target.category))throw Error('Choose one of this weekday’s assigned meal slots.');return plan;
}
function withSchedulingPlan(planId,action){
 saveActiveMealPlan();const previousId=activePlanId,target=mealPlans.find(plan=>plan.id===planId);if(!target)throw Error('The selected meal tab is no longer available.');
 function select(plan){activePlanId=plan.id;weekdayCategories=JSON.parse(JSON.stringify(plan.weekdayCategories||{}));weekdayMealOverrides={...plan.weekdayMealOverrides};weekdayRecipeFilters=JSON.parse(JSON.stringify(plan.weekdayRecipeFilters||{}));pinnedCats=[...(plan.pinnedCats||[])];autoPinTopCategories=plan.autoPinTopCategories}
 select(target);try{return action(target)}finally{saveActiveMealPlan();const previous=mealPlans.find(plan=>plan.id===previousId);if(previous)select(previous);saveActiveMealPlan()}
}
function scheduleMealFromGroups(mealId,target){
 if(editId!==null||mealPersistence.paused||groceryCheckStorageInvalid){throw Error('Save or recover the open changes before scheduling a meal.')}
 const plan=validateScheduleTarget(target),meal=meals.find(meal=>String(meal.id)===String(mealId));if(!meal)throw Error('This recipe is no longer available.');
 // The allocator emits a recipe once per day. Reject an unrepresentable second
 // slot before taking an Undo snapshot or changing any schedule or groceries.
 const displayed=getDisplayedWeekdayMealsForPlan(plan.id===activePlanId?{...plan,weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters}:plan);
 const duplicate=displayed.find(entry=>entry.day===target.day&&String(entry.meal.id)===String(meal.id)&&!(target.occasional?entry.occasional&&entry.linkedTo==null:entry.cat===target.category||target.startGroup&&entry.occasional&&entry.linkedTo==null));
 if(duplicate)throw Error('This recipe is already scheduled in another group ('+duplicate.cat+') on '+target.day+'. A recipe can only appear once per weekday in each meal tab. Choose another group or day, or cancel to select another recipe.');
 saveActiveMealPlan();const before=JSON.parse(captureState());
 withSchedulingPlan(target.planId,()=>applyManualWeekdayMeal(target.day,target.category,meal,null,!!target.occasional,{quiet:true,schedulingOnly:true,beforeState:before,startGroup:target.startGroup,automatic:target.startGroup&&meal.rotation}));
 snapshot(JSON.stringify(before));finishScheduleChangeUndo(before);renderList();return true;
}
function openScheduleMealDialog(meal){
 if(editId!==null){showAppMessage('Save or cancel the open recipe first.');return}
 const d=recipeBulkDialog('Schedule Meal'),name=document.createElement('p');name.textContent=meal.name||'Untitled meal';d.panel.append(name);
 const plan=stage2FormField(d.panel,'Meal tab',stage2Select(mealPlans.map(plan=>[plan.id,plan.name]))),day=stage2FormField(d.panel,'Weekday',stage2Select(orderedDays().map(day=>[day,day]))),slot=stage2FormField(d.panel,'Meal slot',document.createElement('select'));plan.value=activePlanId;
 const note=document.createElement('p');note.style.fontSize='14px';note.textContent='Schedule this recipe here. Its recipe groups and other planned days stay the same.';d.panel.append(note);
 function update(){const target=mealPlans.find(p=>p.id===plan.value),raw=target?.weekdayCategories?.[day.value],groups=(Array.isArray(raw)?raw:[raw]).filter(cat=>cats.includes(cat));slot.replaceChildren(...stage2Select(groups.length?groups.map(cat=>[cat,cat]):[['','This day only — no assigned groups']]).children)}
 plan.onchange=day.onchange=update;update();const error=document.createElement('p');error.className='recipe-bulk-error';error.setAttribute('role','status');d.panel.append(error);
 const actions=document.createElement('div');actions.className='meal-unified-actions';const save=document.createElement('button'),cancel=document.createElement('button');save.type=cancel.type='button';setIconButton(save,'save','Schedule meal');setIconButton(cancel,'cancel','Cancel');cancel.onclick=d.close;
 save.onclick=()=>{try{scheduleMealFromGroups(meal.id,{planId:plan.value,day:day.value,category:slot.value||null,occasional:!slot.value});d.close()}catch(e){error.textContent=e.message}};actions.append(save,cancel);d.panel.append(actions);plan.focus();
}
function prepareRecipeCreation(){
 if(document.querySelector('#editor .editor,[data-scheduled-recipe-draft],[data-viewer-recipe-draft],[data-recovery-draft="one-time-meal"]')||recipeViewer?.linkEdit){showAppMessage('Save or cancel the open recipe first.');return false}
 if(editId!==null||newRecipeDraftId!==null){editId=null;newRecipeDraftId=null;editorCategoryBaseline=null;editorDraftCategories=null;stopMealEditorPositioning()}
 return true;
}
let scheduledMealEditor=null;
function openCreateScheduledRecipe(target,selectionContext=null,current=null){
 if(!prepareRecipeCreation())return false;
 const origin=captureMealEditorOrigin(),group=cats.includes(current?.mealGroup)?current.mealGroup:cats.includes(target.category)?target.category:cats[0]||'';
 const draft={...(current?JSON.parse(JSON.stringify(current)):{}),id:id++,cat:group,name:current?.name||'',rotation:false,prep:current?.prep||'',cook:current?.cook||'',total:current?.total||'',url:current?.url||'',ingredients:current?.ingredients||[],_scheduledEditorDraft:true};
 delete draft.temporaryMeal;meals.push(draft);newRecipeDraftId=draft.id;
 scheduledMealEditor={target:{...target},selectionContext,current,oneTime:!!current,draftId:draft.id,origin,dialog:null};
 openEditor(draft.id,true,origin);stopMealEditorPositioning();
 const d=recipeBulkDialog(current?'Edit one-time meal':'Create New Meal');scheduledMealEditor.dialog=d;d.overlay.style.zIndex='10002';
 const root=$('editor');root.inert=false;d.panel.append(root);d.panel.style.overflowY='auto';
 const close=()=>finishScheduledMealEditor(false);d.overlay.onclick=e=>{if(e.target===d.overlay)close()};const keys=d.overlay.onkeydown;d.overlay.onkeydown=e=>{if(e.key==='Escape'){e.preventDefault();close()}else keys(e)};
 decorateScheduledMealEditor();
 for(const cat of current?.mealGroups||[]){if(cat===group||!cats.includes(cat))continue;const add=$('categoryRows').querySelector('[aria-label="Add group membership"]');if(!add)break;add.click();const selects=$('categoryRows').querySelectorAll('select');const select=selects[selects.length-1];if(select){select.value=cat;select.dispatchEvent(new Event('change',{bubbles:true}))}}
 fitOneTimeMealViewport(d.overlay,d.panel);if(!current&&$('name').revealCardField)$('name').revealCardField();else $('name').focus({preventScroll:true});return true;
}
function decorateScheduledMealEditor(){
 const ctx=scheduledMealEditor;if(!ctx||editId!==ctx.draftId)return;
 let check=$('scheduledOneTime');if(!check){check=document.createElement('input');check.type='checkbox';check.id='scheduledOneTime';check.checked=ctx.oneTime;const label=document.createElement('label');label.className='meal-checkbox-option';label.append(check,document.createTextNode('One-time meal'));const card=document.querySelector('#editor .meal-card-edit-mode');if(card)card.after(label);else $('name').after(label)}
 check.onchange=()=>{ctx.oneTime=check.checked;if(ctx.dialog)ctx.dialog.panel.querySelector('strong').textContent=ctx.current&&ctx.oneTime?'Edit one-time meal':ctx.oneTime?'Add One-Time Meal':'Create New Meal'};
 const groupLabel=$('categoryRows')?.previousElementSibling;if(groupLabel?.tagName==='LABEL')groupLabel.textContent='Meal Group';
 $('cancel').onclick=()=>finishScheduledMealEditor(false);
 $('delete').onclick=()=>{if(ctx.current){const target=ctx.target;finishScheduledMealEditor(false);withSchedulingPlan(target.planId,()=>resumeWeekSlot(target.day,target.category))}else finishScheduledMealEditor(false)};
}
function finishScheduledMealEditor(saved){
 const ctx=scheduledMealEditor;if(!ctx)return;
 if(!saved)rollbackEditorCategories();scheduledMealEditor=null;newRecipeDraftId=null;editId=null;editorCategoryBaseline=null;editorDraftCategories=null;
 const root=$('editor');root.innerHTML='';document.body.insertBefore(root,$('list'));ctx.dialog?.close();restoreMealEditorScroll();
 if(saved)ctx.selectionContext?.complete?.();else ctx.selectionContext?.cancel?.();
}
function saveScheduledMealEditor(next,memberships,rotation){
 const ctx=scheduledMealEditor;if(!ctx)return false;validateScheduleTarget(ctx.target);
 const recipe={...next,rotation,cat:memberships.find(item=>String(item.id)===String(ctx.draftId))?.cat||next.cat};delete recipe.id;delete recipe._scheduledEditorDraft;delete recipe.temporaryMeal;
 const draftIndex=meals.findIndex(meal=>meal.id===ctx.draftId),draft=meals[draftIndex];meals.splice(draftIndex,1);
 try{
  if(ctx.oneTime){const details={...recipe,mealGroup:recipe.cat,mealGroups:memberships.map(item=>item.cat).filter(Boolean)};let saved=false;withSchedulingPlan(ctx.target.planId,()=>{saved=saveOneTimeMeal(ctx.target.day,ctx.target.category,recipe.name,recipe.ingredients,ctx.current?.id,details)});if(!saved){meals.splice(draftIndex,0,draft);return false}}
  else applyRecipeBulk([],{}, {render:false,createScheduledRecipe:{owner:'recipe:'+ctx.draftId,target:ctx.target,recipe,groups:memberships.map(item=>item.cat).filter(Boolean),includeGroceries:true}});
  finishScheduledMealEditor(true);return true;
 }catch(error){meals.splice(Math.min(draftIndex,meals.length),0,draft);throw error}
}
function addScheduledRecipeDraft(draft,transaction){
 validateScheduleTarget(draft.target);const recipe=draft.recipe;if(!recipe||!String(recipe.name||'').trim()||!Array.isArray(recipe.ingredients)||recipe.ingredients.some(line=>typeof line!=='string')||typeof recipe.rotation!=='boolean')throw Error('Invalid recipe draft.');
 if(!cats.length&&recipe.cat==='Misc')cats.push('Misc');if(!cats.includes(recipe.cat))throw Error('Choose an existing recipe group.');
 const created={...recipe,groceryDefaultAll:true,keepAsIdea:!recipe.rotation,id:id++,name:recipe.name.trim(),prep:recipe.prep??'',cook:recipe.cook??'',total:recipe.total??'',linkedMealIds:recipe.linkedMealIds||[]};meals.push(created);transaction.createdRecipeId=created.id;
 const selections=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');selections[String(created.id)]=draft.includeGroceries?[...created.ingredients]:[];
 const groups=[...new Set(draft.groups||[recipe.cat])].filter(cat=>cat!==recipe.cat);if(groups.length){created.linkGroup='linked-'+created.id+'-'+Date.now();for(const cat of groups){if(!cats.includes(cat))throw Error('Choose an existing meal group.');const copy={...JSON.parse(JSON.stringify(created)),id:id++,cat};meals.push(copy);selections[String(copy.id)]=draft.includeGroceries?[...copy.ingredients]:[]}}
 localStorage.setItem('mealRotationSelectedIngredientsV1',JSON.stringify(selections));
}

function createMealPlan(name){
 const clean=String(name||'').trim();if(!clean)return;
 saveActiveMealPlan();snapshot();showMealPlanTabs=true;localStorage.setItem('mealRotationShowPlanTabsV1','true');const created={id:nextMealPlanId(),name:clean,weekdayCategories:{},weekdayMealOverrides:{},weekdayRecipeFilters:{},autoPinTopCategories:true,pinnedCats:[]};
 mealPlans.push(created);loadMealPlan(created.id);
}
function restoreMealPlansFromBackup(data){
 if(!data||!Array.isArray(data.plans)||!data.plans.length)return;
 const valid=data.plans.filter(p=>p&&typeof p.id==='string'&&typeof p.name==='string'&&p.weekdayCategories&&typeof p.weekdayCategories==='object');
 if(!valid.length)return;
 mealPlans=JSON.parse(JSON.stringify(valid));mealPlans.forEach(p=>{if(typeof p.autoPinTopCategories!=='boolean')p.autoPinTopCategories=false});activePlanId=valid.some(p=>p.id===data.activeId)?data.activeId:valid[0].id;
 const plan=mealPlans.find(p=>p.id===activePlanId);
 weekdayCategories=JSON.parse(JSON.stringify(plan.weekdayCategories));
 weekdayMealOverrides={...(plan.weekdayMealOverrides||{})};autoPinTopCategories=true;pinnedCats=[...(plan.pinnedCats||[])];saveActiveMealPlan();
}
// Meal Groups display order is independent of category/weekday/schedule ordering.
const MASTER_GROUP_ORDER_KEY='mealRotationGroupDisplayOrderV1';
let masterGroupOrder=null,masterGroupDragCleanup=null;
const validMasterGroupOrder=value=>Array.isArray(value)&&value.every(x=>typeof x==='string'&&x.trim())&&new Set(value).size===value.length;
try{const raw=localStorage.getItem(MASTER_GROUP_ORDER_KEY);if(raw!==null){const value=JSON.parse(raw);if(validMasterGroupOrder(value))masterGroupOrder=value}}catch(e){/* Keep unknown legacy storage intact until an explicit reorder/reset. */}
function masterOrderedGroups(automatic){return masterGroupOrder===null?automatic:[...masterGroupOrder.filter(c=>cats.includes(c)),...cats.filter(c=>!masterGroupOrder.includes(c))]}
function writeMasterGroupOrder(next,recordHistory=true){
 try{if(next===null)localStorage.removeItem(MASTER_GROUP_ORDER_KEY);else localStorage.setItem(MASTER_GROUP_ORDER_KEY,JSON.stringify(next))}catch(e){showAppMessage('Group order could not be saved. Your previous order and meal data are unchanged.');return false}
 if(recordHistory)snapshot();masterGroupOrder=next===null?null:[...next];return true;
}
function restoreMasterGroupOrder(next){const value=validMasterGroupOrder(next)?next:null;return JSON.stringify(value)===JSON.stringify(masterGroupOrder)||writeMasterGroupOrder(value,false)}
function renameMasterGroupOrder(old,next){return masterGroupOrder===null||!masterGroupOrder.includes(old)||writeMasterGroupOrder(masterGroupOrder.map(c=>c===old?next:c),false)}
function removeMasterGroupOrder(category){return masterGroupOrder===null||!masterGroupOrder.includes(category)||writeMasterGroupOrder(masterGroupOrder.filter(c=>c!==category),false)}
function weekdayOrderedGroups(){return [...new Set(orderedDays().flatMap(day=>masterDisplayCategories(day)))].filter(group=>cats.includes(group))}
function weekdayGroupOrderNeedsReset(){const assigned=weekdayOrderedGroups(),set=new Set(assigned);return JSON.stringify(masterOrderedGroups(masterDisplayOrder()).filter(group=>set.has(group)))!==JSON.stringify(assigned)}
function resetWeekdayGroupOrder(){const assigned=weekdayOrderedGroups(),set=new Set(assigned);return writeMasterGroupOrder([...assigned,...masterOrderedGroups(masterDisplayOrder()).filter(group=>!set.has(group))])}
function currentMasterGroupOrder(){const shown=[...document.querySelectorAll('#list .master-category-card')].map(card=>card.dataset.category).filter(category=>cats.includes(category));return shown.length===cats.length?shown:masterOrderedGroups(masterDisplayOrder())}
function installMasterGroupDragging(wrap,reset){
 const events=new AbortController(),signal=events.signal;let gesture=null,suppressClick=false;
 const on=(target,event,handler,options={})=>target.addEventListener(event,handler,{...options,signal});
 const cards=()=>[...wrap.querySelectorAll(':scope>.master-category-card')].filter(card=>cats.includes(card.dataset.category));
 const eligible=target=>{
  const card=target.closest('.master-category-card');if(!card||!cats.includes(card.dataset.category)||target.closest('.master-category-meal,.editor,[contenteditable="true"]'))return null;
  const control=target.closest('button,a,input,select,textarea,summary,[role="button"]');
  if(control&&(!control.classList.contains('master-category-title')||target.closest('svg')))return null;
  return card;
 };
 const arrange=drag=>{
  drag.order.forEach((category,index)=>{const card=drag.nodes.find(card=>card.dataset.category===category);if(card)card.style.order=index+1});
 };
 const end=(cancel=false)=>{
  const drag=gesture;if(!drag)return;gesture=null;clearTimeout(drag.timer);cancelAnimationFrame(drag.frame);
  if(drag.phase==='drag'){
   const changed=JSON.stringify(drag.order)!==JSON.stringify(drag.before);
   const accepted=!cancel&&(!changed||writeMasterGroupOrder(drag.order));
   const final=accepted?drag.order:drag.before,top=drag.card.getBoundingClientRect().top;
   for(const category of final){const card=drag.nodes.find(card=>card.dataset.category===category);if(card){card.style.removeProperty('order');card.style.removeProperty('--group-closed-height');wrap.append(card)}}
   wrap.classList.remove('master-group-drag-active');drag.card.classList.remove('master-group-dragging');drag.ghost?.remove();
   reset.hidden=!weekdayGroupOrderNeedsReset();
   if(accepted&&changed){window.scrollBy({top:drag.card.getBoundingClientRect().top-top,behavior:'instant'})}else window.scrollTo({top:drag.originalScroll,behavior:'instant'});
   drag.focus?.isConnected&&drag.focus.focus({preventScroll:true});
  }
  if(drag.phase!=='pending')suppressClick=true;
  if(drag.source==='pointer'&&wrap.hasPointerCapture(drag.id))wrap.releasePointerCapture(drag.id);
 };
 masterGroupDragCleanup=()=>{end(true);events.abort()};
 const frame=now=>{
  const drag=gesture;if(drag?.phase!=='drag')return;
  const elapsed=Math.min(40,drag.last?now-drag.last:16.7)/16.7;drag.last=now;
  const edge=65,velocity=!drag.moved?0:drag.y<edge?-Math.min(14,(edge-drag.y)/3):drag.y>innerHeight-edge?Math.min(14,(drag.y-innerHeight+edge)/3):0;
  if(velocity){window.scrollBy(0,velocity*elapsed);drag.direction=Math.sign(velocity);drag.correction=0}
  drag.ghost.style.top=Math.max(4,Math.min(innerHeight-drag.height-4,drag.y-drag.offset))+'px';
  const index=drag.order.indexOf(drag.category),next=drag.order[index+(drag.direction>0?1:-1)];
  if(drag.direction&&next){const node=drag.nodes.find(card=>card.dataset.category===next),box=node.getBoundingClientRect(),y=drag.y-drag.correction;
   if(drag.direction>0?y>box.top+box.height/2:y<box.top+box.height/2){drag.order.splice(index,1);drag.order.splice(index+(drag.direction>0?1:-1),0,drag.category);arrange(drag)}
  }
  drag.frame=requestAnimationFrame(frame);
 };
 const activate=drag=>{
  if(gesture!==drag||drag.phase!=='pending'||!wrap.isConnected)return;
  clearTimeout(drag.timer);if(Math.abs(scrollY-drag.originalScroll)>3){drag.phase='scroll';return}
  drag.phase='drag';suppressClick=true;drag.before=cards().map(card=>card.dataset.category);drag.order=[...drag.before];drag.nodes=cards();drag.focus=document.activeElement;
  const box=drag.card.getBoundingClientRect(),header=drag.card.querySelector('.master-category-header'),head=header.getBoundingClientRect();
  drag.height=head.height+2;drag.offset=Math.max(8,Math.min(drag.height/2,drag.startY-head.top));
  for(const card of drag.nodes)card.style.setProperty('--group-closed-height',card.querySelector('.master-category-header').offsetHeight+2+'px');
  // Clip bodies without detaching the held target or changing expansion state.
  wrap.classList.add('master-group-drag-active');drag.card.classList.add('master-group-dragging');
  window.scrollBy({top:drag.card.getBoundingClientRect().top-(drag.startY-drag.offset),behavior:'instant'});
  drag.correction=drag.startY-(drag.card.getBoundingClientRect().top+drag.height/2);
  drag.ghost=document.createElement('div');drag.ghost.className='master-category-card master-group-drag-ghost';drag.ghost.setAttribute('aria-hidden','true');drag.ghost.inert=true;drag.ghost.append(header.cloneNode(true));
  for(const node of drag.ghost.querySelectorAll('[id]'))node.removeAttribute('id');
  drag.ghost.style.cssText='position:fixed;left:'+box.left+'px;top:'+(drag.startY-drag.offset)+'px;width:'+box.width+'px;height:'+drag.height+'px;pointer-events:none;z-index:10010';document.body.append(drag.ghost);
  if(drag.source==='pointer')wrap.setPointerCapture(drag.id);drag.frame=requestAnimationFrame(frame);
 };
 const begin=(target,x,y,source,id)=>{
  suppressClick=false;const card=eligible(target);if(!card||editId!==null||document.querySelector('[role="dialog"]'))return;
  const drag={card,category:card.dataset.category,source,id,startX:x,startY:y,y,previousY:y,originalScroll:scrollY,phase:'pending'};gesture=drag;drag.timer=setTimeout(()=>activate(drag),550);
 };
 const move=(x,y,event)=>{
  const drag=gesture;if(!drag)return;
  if(drag.phase==='pending'&&(Math.hypot(x-drag.startX,y-drag.startY)>8||event.cancelable===false)){clearTimeout(drag.timer);drag.phase='scroll'}
  if(drag.phase!=='drag')return; // The browser owns ordinary vertical swipes.
  if(event.cancelable===false){end(true);return}
  event.preventDefault();event.stopPropagation();if(!drag.moved&&Math.hypot(x-drag.startX,y-drag.startY)<8)return;drag.moved=true;const delta=y-drag.previousY;if(delta)drag.direction=Math.sign(delta);drag.previousY=y;drag.y=y;
 };
 on(wrap,'touchstart',e=>{suppressClick=false;if(e.touches.length!==1||gesture){end(true);return}const t=e.changedTouches[0];begin(e.target,t.clientX,t.clientY,'touch',t.identifier)},{passive:false});
 on(document,'touchmove',e=>{const drag=gesture;if(drag?.source!=='touch')return;const t=[...e.changedTouches].find(t=>t.identifier===drag.id);if(t)move(t.clientX,t.clientY,e)},{capture:true,passive:false});
 on(document,'touchend',e=>{const drag=gesture;if(drag?.source!=='touch'||![...e.changedTouches].some(t=>t.identifier===drag.id))return;if(drag.phase==='drag'){if(e.cancelable)e.preventDefault();e.stopPropagation()}end()},{capture:true,passive:false});
 on(document,'touchcancel',()=>{if(gesture?.source==='touch')end(true)},{capture:true});
 on(wrap,'pointerdown',e=>{suppressClick=false;if(e.pointerType==='touch'||e.button!==0)return;if(gesture){end(true);return}begin(e.target,e.clientX,e.clientY,'pointer',e.pointerId)});
 on(document,'pointermove',e=>{if(gesture?.source==='pointer'&&gesture.id===e.pointerId)move(e.clientX,e.clientY,e)},{capture:true,passive:false});
 on(document,'pointerup',e=>{const drag=gesture;if(drag?.source!=='pointer'||drag.id!==e.pointerId)return;if(drag.phase==='drag'){e.preventDefault();e.stopPropagation()}end()},{capture:true});
 on(document,'pointercancel',e=>{if(gesture?.source==='pointer'&&gesture.id===e.pointerId)end(true)},{capture:true});
 on(wrap,'lostpointercapture',e=>{if(e.target===wrap&&gesture?.source==='pointer'&&gesture.id===e.pointerId)end(true)});
 on(wrap,'click',e=>{if(suppressClick){suppressClick=false;e.preventDefault();e.stopImmediatePropagation()}},{capture:true});
 on(wrap,'contextmenu',e=>{if(gesture?.phase==='pending'){e.preventDefault();activate(gesture)}});
 on(document,'keydown',e=>{suppressClick=false;if(e.key==='Escape'&&gesture){e.preventDefault();e.stopPropagation();end(true)}},{capture:true});
 on(window,'blur',()=>end(true));on(window,'resize',()=>end(true));on(document,'visibilitychange',()=>{if(document.hidden)end(true)});
}

const MASTER_CATEGORIES_VALUE='__all_categories__';
let masterCategoriesView=false;try{masterCategoriesView=sessionStorage.getItem('mealRotationMasterCategoriesV1')==='true'}catch(e){}
// UI-only section visibility, independent for each group and included in backups.
const masterSectionExpansionKey='mealRotationGroupSectionExpansionV1',masterSectionExpansion=new Map();
try{const saved=JSON.parse(localStorage.getItem(masterSectionExpansionKey)||'null');if(saved?.version===1&&saved.groups&&typeof saved.groups==='object'&&!Array.isArray(saved.groups))for(const [category,sections]of Object.entries(saved.groups)){
 if(sections&&typeof sections==='object'&&!Array.isArray(sections)){const known={};for(const key of ['rotation','ideas','up-next','back-burner'])if(typeof sections[key]==='boolean')known[key]=sections[key];masterSectionExpansion.set(category,known)}
}}catch(e){}
function masterRecipeSectionOpen(category,rotation){const key=rotation===true?'rotation':rotation===false?'up-next':rotation;return masterSectionExpansion.get(category)?.[key]??(key!=='back-burner')}
function saveMasterSectionExpansion(){try{localStorage.setItem(masterSectionExpansionKey,JSON.stringify({version:1,groups:Object.fromEntries(masterSectionExpansion)}))}catch(e){/* Keep navigation preferences in memory if storage is unavailable. */}}
function setMasterRecipeSectionOpen(category,rotation,open){
 if(masterRecipeSectionOpen(category,rotation)===open)return false;
 masterSectionExpansion.set(category,{...masterSectionExpansion.get(category),[rotation===true?'rotation':rotation===false?'up-next':rotation]:open});saveMasterSectionExpansion();return true;
}
function copyMasterSectionExpansion(oldName,newName){if(masterSectionExpansion.has(oldName)){masterSectionExpansion.set(newName,{...masterSectionExpansion.get(oldName)});saveMasterSectionExpansion()}}
const masterExpandedCategories=new Set();let masterExpansionInitialized=false;
function initializeMasterCategoryExpansion(extraCategory){
 masterExpansionInitialized=true;
 masterExpandedCategories.clear();
 // Menu navigation starts collapsed; a category button opens only its category.
 if(extraCategory&&cats.includes(extraCategory))masterExpandedCategories.add(extraCategory);
}

function buildGroupedMealPicker(container,search,entries,searchMode,pinSelected=false,scrollExpandedToTop=false,resetOnSelect=false,compactPinned=false,leftChevrons=false,behavior={}){
 // Entries: {meal, checked, onChange}. Keep selections when groups collapse or searches change.
 const groups=new Map();entries.forEach(entry=>{const cat=entry.meal.cat||behavior.unassignedLabel||'Ungrouped';if(!groups.has(cat))groups.set(cat,[]);groups.get(cat).push(entry)});
 const sections=[];let searching=false,searchExpansion=[];
 const selectedArea=document.createElement('div');
 if(pinSelected){selectedArea.style.cssText='border-bottom:1px solid #ddd;margin-bottom:8px';container.append(selectedArea)}
 const selectedRows=[];
 function refreshPinned(){
  if(!pinSelected)return;
  selectedArea.replaceChildren();selectedRows.length=0;
  const selected=entries.filter(e=>e.checked).sort((a,b)=>a.meal.name.localeCompare(b.meal.name));
  for(const entry of selected){
   const row=document.createElement('label');row.style.cssText=compactPinned?'display:flex;align-items:center;gap:8px;padding:3px 4px;line-height:1.25;min-height:32px;cursor:pointer':'display:flex;align-items:center;gap:10px;padding:10px 4px';
   const cb=document.createElement('input');cb.type='checkbox';cb.checked=true;cb.style.cssText='width:20px;height:20px;flex-shrink:0';
   cb.onchange=()=>{entry.checked=false;if(entry.checkbox)entry.checkbox.checked=false;entry.onChange(false);search.dispatchEvent(new Event('input'));if(resetOnSelect)sections.forEach(s=>s.setExpanded(false));container.scrollTop=0};
   const label=document.createElement('span');label.textContent=entry.meal.name;label.style.flex='1';
   const group=document.createElement('small');group.textContent=entry.meal.cat||'Ungrouped';group.style.cssText='color:#777;font-size:12px';
   if(leftChevrons)row.className='meal-editor-linked-row';row.append(cb,label,group);selectedArea.append(row);selectedRows.push(row);
  }
  selectedArea.style.display=selected.length?'block':'none';
 }
 [...groups.keys()].sort((a,b)=>Number(groups.get(b).some(x=>x.checked))-Number(groups.get(a).some(x=>x.checked))||a.localeCompare(b)).forEach(cat=>{
  const section=document.createElement('div');section.style.cssText='border-bottom:1px solid #ddd';
  const header=document.createElement('button');header.type='button';header.style.cssText='display:flex;align-items:center;justify-content:space-between;width:100%;padding:12px 6px;text-align:left;background:transparent;border:0;color:inherit;font-weight:600;cursor:pointer';
  const name=document.createElement('span');name.textContent=cat;const arrow=document.createElement('span');if(leftChevrons){arrow.className='meal-editor-group-chevron';arrow.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg>'}else arrow.textContent='▸';if(leftChevrons){header.append(arrow,name);header.classList.add('meal-editor-group-heading');name.style.flex='1'}else header.append(name,arrow);
  const body=document.createElement('div');body.style.cssText=leftChevrons?'display:none;padding:0 0 4px':'display:none;padding:0 4px 6px 14px';
  groups.get(cat).sort((a,b)=>Number(!!b.checked)-Number(!!a.checked)||a.meal.name.localeCompare(b.meal.name)).forEach(entry=>{
   const row=document.createElement('label');row.style.cssText='display:flex;align-items:center;gap:10px;padding:9px 3px;cursor:pointer';
   const cb=document.createElement('input');cb.type='checkbox';cb.checked=!!entry.checked;cb.style.cssText='width:20px;height:20px;flex-shrink:0';cb.onchange=()=>{entry.checked=cb.checked;entry.onChange(cb.checked);search.dispatchEvent(new Event('input'));if(resetOnSelect){sections.forEach(s=>s.setExpanded(false));container.scrollTop=0;const outer=container.closest('[data-label-manager-list]');if(outer)outer.scrollTop=0;}else if(cb.checked&&pinSelected)container.scrollTop=0};
   const text=document.createElement('span');text.textContent=entry.meal.name;if(leftChevrons)row.className='meal-editor-linked-row';row.append(cb,text);body.append(row);entry.row=row;entry.checkbox=cb;
  });
  let expanded=!behavior.startCollapsed&&!pinSelected&&groups.get(cat).some(x=>x.checked);const setExpanded=value=>{expanded=value;body.style.display=value?'block':'none';if(leftChevrons){arrow.classList.toggle('expanded',value);header.setAttribute('aria-expanded',String(value))}else arrow.textContent=value?'▾':'▸'};
  header.onclick=()=>{const opening=!expanded;setExpanded(opening);if(opening&&scrollExpandedToTop){requestAnimationFrame(()=>{const offset=header.getBoundingClientRect().top-container.getBoundingClientRect().top;container.scrollTop+=offset})}};setExpanded(expanded);section.append(header,body);container.append(section);sections.push({section,entries:groups.get(cat),setExpanded,getExpanded:()=>expanded});
 });
 const empty=behavior.emptyText?document.createElement('p'):null;if(empty){empty.className='muted';empty.textContent=behavior.emptyText;container.append(empty)}
 container.collapseMealGroups=()=>sections.forEach(group=>group.setExpanded(false));
 search.oninput=()=>{
  const query=search.value.trim().toLocaleLowerCase();
  if(behavior.restoreExpansion){if(query&&!searching)searchExpansion=sections.map(group=>[group,group.getExpanded()]);if(!query&&searching)for(const [group,expanded]of searchExpansion)group.setExpanded(expanded);searching=!!query}
  const words=query.split(/\s+/).filter(Boolean);
  refreshPinned();
  sections.forEach(group=>{
   let visible=0;group.entries.forEach(entry=>{const title=entry.meal.name.toLocaleLowerCase();const match=(!pinSelected||!entry.checked)&&(!query||(searchMode&&!searchMode.checked?words.every(word=>title.includes(word)):title.includes(query)));entry.row.style.display=match?'flex':'none';if(match)visible++});
   group.section.style.display=visible?'block':'none';if(query&&visible)group.setExpanded(true);if(!query&&!behavior.restoreExpansion)group.setExpanded(resetOnSelect?false:group.entries.some(entry=>entry.checkbox.checked));
  });
  if(empty)empty.hidden=sections.some(group=>group.section.style.display!=='none');
 };
 search.dispatchEvent(new Event('input'));
}
function chooseExistingMealsForNewGroup(category,existingGroup=false){
 return new Promise(resolve=>{
  const unique=new Map();
  meals.forEach(m=>{if(!m.name||m.cat===category)return;const key=m.linkGroup||'meal-'+m.id;if(!unique.has(key))unique.set(key,m)});
  if(!unique.size){if(existingGroup)showAppMessage('No other meals available.');resolve('cancel');return}
  const overlay=document.createElement('div');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:14000;display:flex;align-items:center;justify-content:center;padding:16px';
  const dialog=document.createElement('div');dialog.setAttribute('role','dialog');dialog.setAttribute('aria-modal','true');dialog.style.cssText='background:#fff;color:#222;border-radius:14px;width:100%;max-width:460px;max-height:85vh;display:flex;flex-direction:column;padding:18px;gap:12px';
  dialog.classList.add('add-meals-picker');const title=document.createElement('strong');title.textContent='Add meals to '+category;
  const search=document.createElement('input');search.type='search';search.placeholder='Search meals';search.setAttribute('aria-label','Search meals');search.style.cssText='width:100%;padding:10px;border:1px solid #bbb;border-radius:8px';
  const list=document.createElement('div');list.style.cssText='overflow:auto;min-height:60px;flex:1';
  const selections=[...unique.values()].map(m=>({meal:m,checked:false,onChange(value){this.checked=value}}));
  buildGroupedMealPicker(list,search,selections,undefined,false,false,false,false,true);
  const modeRow=document.createElement('div');modeRow.style.cssText='display:flex;flex-wrap:wrap;gap:14px;padding:7px 2px;border-top:1px solid #ddd';
  const modeName='group-meal-mode-'+Date.now();
  for(const [value,label] of [['copy','Copy (keep in original group)'],['move','Move (remove from original group)']]){
   const option=document.createElement('label');option.style.cssText='display:flex;align-items:center;gap:6px;cursor:pointer;font-size:14px';
   const radio=document.createElement('input');radio.type='radio';radio.name=modeName;radio.value=value;radio.checked=value==='copy';option.append(radio,document.createTextNode(label));modeRow.append(option);
  }
  const actions=document.createElement('div');actions.className='meal-unified-actions';actions.style.cssText='flex-shrink:0;padding-top:12px;border-top:1px solid #ddd;background:#fff;color:#242424';
  const iconButton=(label,paths)=>{const btn=document.createElement('button');btn.type='button';btn.className='iconbtn';btn.title=label;btn.setAttribute('aria-label',label);btn.style.cssText='width:52px;height:48px';btn.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'+paths+'</svg>';return btn};
  const remove=iconButton('Delete new group','<path d="M3 6h18M8 6V4h8v2m3 0-1 15H6L5 6m5 4v7m4-7v7"/>');
  const skip=iconButton('Cancel','<path d="M18 6 6 18M6 6l12 12"/>');
  const add=iconButton('Add selected meals','<path d="M5 12l4 4L19 6"/>');
  const close=result=>{overlay.remove();resolve(result)};
  skip.onclick=()=>close('cancel');
  remove.onclick=()=>close('delete');
  add.onclick=()=>{
   const chosen=selections.filter(x=>x.checked).map(x=>x.meal);
   const mode=modeRow.querySelector('input[name="'+modeName+'"]:checked').value;
   if(chosen.length){
    snapshot();
    chosen.forEach(m=>{
     const group=m.linkGroup?meals.filter(x=>x.linkGroup===m.linkGroup):[m];
     if(group.some(x=>x.cat===category))return;
     if(mode==='move'){
      const oldCat=m.cat;
      m.cat=category;
      if(typeof clearOverridesForCat==='function')clearOverridesForCat(oldCat);
     }else{
      const link=m.linkGroup||'linked-'+m.id+'-'+Date.now();
      group.forEach(x=>x.linkGroup=link);
      const copy={...m,id:id++,cat:category,linkGroup:link,ingredients:Array.isArray(m.ingredients)?[...m.ingredients]:[]};
      meals.push(copy);
     }
    });
    persist();
   }
   close('added');
  };
  actions.append(add,skip);if(!existingGroup)actions.append(remove);dialog.append(title,search,list,modeRow,actions);overlay.append(dialog);document.body.append(overlay);
 });
}
function showRelatedMeals(meal){
 const sameRecipe=x=>String(x.id)===String(meal.id)||(meal.linkGroup&&x.linkGroup===meal.linkGroup);
 const outgoing=new Set((Array.isArray(meal.linkedMealIds)?meal.linkedMealIds:[]).map(String));
 const related=meals.filter(other=>!sameRecipe(other)&&(outgoing.has(String(other.id))||meals.some(source=>sameRecipe(source)&&Array.isArray(source.linkedMealIds)&&source.linkedMealIds.some(id=>String(id)===String(other.id)))||(Array.isArray(other.linkedMealIds)&&other.linkedMealIds.some(id=>meals.some(source=>sameRecipe(source)&&String(source.id)===String(id))))));
 const unique=[...new Map(related.map(other=>[other.linkGroup||String(other.id),other])).values()];
 if(!unique.length)return;
 const shade=document.createElement('div');shade.className='shared-groups-shade';
 const panel=document.createElement('div');panel.className='shared-groups-panel';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Meals linked to '+(meal.name||'this recipe'));
 const heading=document.createElement('h3');heading.textContent='Meals linked to '+(meal.name||'this recipe');panel.append(heading);
 unique.forEach(target=>{const button=document.createElement('button');button.type='button';button.className='shared-groups-choice';button.textContent=(target.name||'Untitled meal')+' — '+target.cat;button.onclick=()=>{shade.remove();openMasterCategories(target.cat);requestAnimationFrame(()=>{const card=[...document.querySelectorAll('.master-category-card')].find(x=>x.dataset.category===target.cat);const row=card&&[...card.querySelectorAll('[data-meal-id]')].find(x=>x.dataset.mealId===String(target.id));if(row)row.scrollIntoView({block:'center',behavior:'smooth'})})};panel.append(button)});
 const close=document.createElement('button');close.type='button';close.className='shared-groups-close';setIconButton(close,'cancel','Close');close.setAttribute('aria-label','Close');close.onclick=()=>shade.remove();panel.append(close);shade.onclick=e=>{if(e.target===shade)shade.remove()};shade.append(panel);document.body.append(shade);close.focus();
}
function showSharedRecipeGroups(meal){
 const copies=meal.linkGroup?meals.filter(x=>x.linkGroup===meal.linkGroup):[meal];
 const categories=[...new Set(copies.map(x=>x.cat).filter(Boolean))];
 const shade=document.createElement('div');shade.className='shared-groups-shade';shade.setAttribute('role','presentation');
 const panel=document.createElement('div');panel.className='shared-groups-panel';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');panel.setAttribute('aria-label','Groups containing '+(meal.name||'this recipe'));
 const title=document.createElement('h3');title.textContent='Groups containing '+(meal.name||'this recipe');panel.append(title);
 categories.forEach(cat=>{const button=document.createElement('button');button.type='button';button.className='shared-groups-choice';button.textContent=cat+(cat===meal.cat?' (current)':'');button.onclick=()=>{shade.remove();openMasterCategories(cat);requestAnimationFrame(()=>{const card=[...document.querySelectorAll('.master-category-card')].find(x=>x.dataset.category===cat);const target=card&&[...card.querySelectorAll('[data-meal-id]')].find(x=>copies.some(m=>m.cat===cat&&String(m.id)===x.dataset.mealId));if(target)target.scrollIntoView({block:'center',behavior:'smooth'})})};panel.append(button)});
 const close=document.createElement('button');close.type='button';close.className='shared-groups-close';setIconButton(close,'cancel','Close');close.setAttribute('aria-label','Close');close.onclick=()=>shade.remove();panel.append(close);
 shade.onclick=e=>{if(e.target===shade)shade.remove()};shade.append(panel);document.body.append(shade);close.focus();
}
function openMasterCategories(focusCategory){
 setMasterCategoriesView(true);showTop=false;groceryTabActive=false;allMealsActive=false;
 if(focusCategory)initializeMasterCategoryExpansion(focusCategory);
 else initializeMasterCategoryExpansion();
 editId=null;menuCat=null;render();
 if(!focusCategory)requestAnimationFrame(()=>window.scrollTo({top:0,behavior:'instant'}));
 if(focusCategory&&cats.includes(focusCategory)){
  requestAnimationFrame(()=>{
   const card=[...document.querySelectorAll('.master-category-card')].find(el=>el.dataset.category===focusCategory);
   if(card)card.scrollIntoView({behavior:'smooth',block:'start'});
  });
 }
}

function setMasterCategoriesView(value){masterCategoriesView=!!value;try{sessionStorage.setItem('mealRotationMasterCategoriesV1',String(masterCategoriesView))}catch(e){}}
// Individual category pages have been replaced by the Master Categories page.
masterCategoriesView=true;
// Default to all expanded until the first user transition initializes the chosen mode.

const currentViewKey='mealRotationCurrentViewV1';
let isPageReload=false;
try{
  const nav=performance.getEntriesByType('navigation')[0];
  isPageReload=nav?nav.type==='reload':performance.navigation?.type===1;
}catch(e){}
// Start on My Rotation when there are no recipes, including after a test reset.
if(isPageReload&&meals.length){
  try{
    const previousView=sessionStorage.getItem(currentViewKey);
    if(previousView==='category')showTop=false;
    else if(previousView==='top'||previousView==='all'||previousView==='grocery')showTop=true;
    if(previousView==='all'){allMealsActive=true;groceryTabActive=false;}
    else if(previousView==='grocery'){groceryTabActive=true;allMealsActive=false;}
    else {allMealsActive=false;groceryTabActive=false;}
  }catch(e){}
}
function rememberCurrentView(){
  try{sessionStorage.setItem(currentViewKey,!showTop?'category':allMealsActive?'all':groceryTabActive?'grocery':'top')}catch(e){}
}
// Rendered-page identity is also used to close Settings on navigation.
let lastRenderedPageKey=null;
const $=x=>document.getElementById(x);let backupRestoreReloadPending=false;window.addEventListener('mealRotationBeforeStorageReset',()=>{backupRestoreReloadPending=true});function persist(){if(backupRestoreReloadPending||mealPersistence.paused)return;saveUpNextOrder();if(hasDependentSideSlots()&&!coordinatingDependentSides&&!restoringRotationCalendars){const before=captureGroceryCheckStates();if(coordinateDependentSides())reconcileRotatedGroceryChecks(before,[]);saveActiveMealPlan()}reconcileRotationCalendars();reconcileAllCookingData();try{localStorage.setItem('mealRotationDataV1',JSON.stringify({cats,active,meals:meals.filter(meal=>!meal._scheduledEditorDraft)}))}catch(e){}}window.addEventListener('pagehide',persist);document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='hidden')persist()});const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));function captureState(){return JSON.stringify({upNextOrder:normalizedUpNextOrder(),groupIdentities:localStorage.getItem(GROUP_IDENTITIES_KEY),lastRotationBefore:localStorage.getItem('mealRotationLastRotationBeforeV1'),cats,active,meals:meals.filter(meal=>!meal._scheduledEditorDraft),masterGroupOrder,groceryOccurrenceChecks,checkedIngredients:[...checkedIngredients],weekdayCategories,weekdayMealOverrides,weekdayRecipeFilters,pinnedCats,expandedCats,startWeekday,topCounts,categoryColors,weekdayColors,autoPinTopCategories,applyPinsToAllTabs,masterOpenMode,masterPinsOverride,mealPlans,activePlanId,showMealPlanTabs})}
function snapshot(state=captureState()){dismissOnboardingHint();if(history[history.length-1]!==state){history.push(state);if(history.length>100)history.shift()}redoHistory=[];groceryUndo=null}
// Change Meal snapshots describe scheduling, never a replacement recipe library.
function captureScheduleUndoChecks(){return Object.fromEntries([...captureGroceryCheckStates()].map(([id,item])=>[id,item.checked]))}
function captureHistoryCounterpart(target){
 const current=JSON.parse(captureState());
 if(target.manualGroceriesUndo)current.manualGroceriesUndo=manualGroceryItems();
 if(target.recipePhotoUndo)current.recipePhotoUndo={refs:recipePhotoReferences(Object.keys(target.recipePhotoUndo.refs))};
 if(target.scheduleChangeUndo)current.scheduleChangeUndo={...target.scheduleChangeUndo,checks:captureScheduleUndoChecks()};
 if(target.groupUndoIngredientSelections){const selected=JSON.parse(localStorage.getItem('mealRotationSelectedIngredientsV1')||'{}');current.groupUndoIngredientSelections=Object.fromEntries(Object.keys(target.groupUndoIngredientSelections).map(key=>[key,Object.hasOwn(selected,key)?selected[key]:null]));current.skippedCookingState=JSON.parse(JSON.stringify({keys:target.skippedCookingState?.keys||[],sessions:cookingSessions.occurrences,scales:occurrenceScales.occurrences}))}
 if(target.groupUndoGrocery)current.groupUndoGrocery=groupGrocerySnapshot(target.groupUndoGrocery,captureGroceryCheckStates());
 return JSON.stringify(current);
}
// Group history owns only grocery occurrences changed by that group operation.
function groupGrocerySnapshot(meta,states){
 const occurrences=new Set(meta.occurrences),ids=new Set(meta.sourceIds),owned=id=>ids.has(id)||occurrences.has(JSON.parse(id)[0]);
 const entries=[...states].filter(([id])=>owned(id));
 return {...meta,sourceIds:[...new Set([...ids,...entries.map(([id])=>id),...Object.keys(groceryOccurrenceChecks.checks).filter(owned)])],checks:Object.fromEntries(entries.map(([id,item])=>[id,item.checked])),sources:Object.fromEntries(entries.map(([id,item])=>[id,item.source]))};
}
function captureGroupGroceryUndo(prior,saved){
 const next=captureGroceryCheckStates(),occurrences=new Set(),oldChecks=saved.groceryOccurrenceChecks.checks;
 for(const id of new Set([...prior.keys(),...next.keys()])){const old=prior.get(id),now=next.get(id);if(!old||!now||old.checked!==now.checked||JSON.stringify(old.source)!==JSON.stringify(now.source))occurrences.add((old||now).source.occurrence)}
 // Include changed inactive ledger entries without claiming unchanged legacy
 // materialization on an unrelated active occurrence.
 for(const id of new Set([...Object.keys(oldChecks),...Object.keys(groceryOccurrenceChecks.checks)]))if(!prior.has(id)&&!next.has(id)&&oldChecks[id]!==groceryOccurrenceChecks.checks[id])occurrences.add(JSON.parse(id)[0]);
 const ids=[...new Set([...prior.keys(),...next.keys(),...Object.keys(oldChecks),...Object.keys(groceryOccurrenceChecks.checks)])].filter(id=>occurrences.has(JSON.parse(id)[0]));
 const legacyKeys=new Set();for(const states of [prior,next])for(const [id,item]of states)if(occurrences.has(item.source.occurrence))for(const key of [item.source.baseKey,...item.source.checkKeys])legacyKeys.add(key);
 const oldLegacy=new Set(saved.checkedIngredients);for(const key of new Set([...oldLegacy,...checkedIngredients]))if(oldLegacy.has(key)!==checkedIngredients.has(key))legacyKeys.add(key);
 return groupGrocerySnapshot({occurrences:[...occurrences],sourceIds:ids,legacyKeys:[...legacyKeys]},prior);
}
function restoreGroupGroceryUndo(saved){
 const meta=saved.groupUndoGrocery,states=captureGroceryCheckStates(),occurrences=new Set(meta.occurrences),ids=new Set(meta.sourceIds),owned=id=>ids.has(id)||occurrences.has(JSON.parse(id)[0]),legacy=new Set(checkedIngredients),oldLegacy=new Set(saved.checkedIngredients),shared=new Set();
 for(const [id,item]of states)if(!owned(id))for(const key of [item.source.baseKey,...item.source.checkKeys])shared.add(key);
 for(const key of meta.legacyKeys)if(!shared.has(key)){if(oldLegacy.has(key))legacy.add(key);else legacy.delete(key)}
 const ledger={...groceryOccurrenceChecks,checks:{...groceryOccurrenceChecks.checks},quantities:{...groceryOccurrenceChecks.quantities}},empty={checks:{}};
 for(const [id,item]of states)if(!owned(id)&&typeof ledger.checks[id]!=='boolean'&&grocerySourceChecked(item.source,empty,legacy)!==item.checked)ledger.checks[id]=item.checked;
 for(const id of new Set([...ids,...Object.keys(ledger.checks).filter(owned)])){
  if(Object.hasOwn(saved.groceryOccurrenceChecks.checks,id))ledger.checks[id]=saved.groceryOccurrenceChecks.checks[id];
  else if(Object.hasOwn(meta.checks,id)&&grocerySourceChecked(meta.sources[id],empty,legacy)!==meta.checks[id])ledger.checks[id]=meta.checks[id];
  else delete ledger.checks[id];
  const amount=saved.groceryOccurrenceChecks.quantities?.[id];if(amount)ledger.quantities[id]={...amount};else delete ledger.quantities[id];
 }
 return {...saved,checkedIngredients:[...legacy],groceryOccurrenceChecks:ledger};
}
function restoreScheduleUndoState(saved){
 const current=JSON.parse(captureState()),meta=saved.scheduleChangeUndo;
 const fields=['weekdayCategories','weekdayMealOverrides','weekdayRecipeFilters','cycleSlotChoices','cycleRetainedSlots','weekSchedule','rotationCalendar','favoriteRotationScores','dependentSideState','occasionalMeals'];
 current.mealPlans=current.mealPlans.map(plan=>{const old=saved.mealPlans.find(p=>p.id===plan.id);if(!old)return plan;for(const key of fields){if(Object.hasOwn(old,key))plan[key]=JSON.parse(JSON.stringify(old[key]));else delete plan[key]}return plan});
 for(const key of ['weekdayCategories','weekdayMealOverrides','weekdayRecipeFilters','activePlanId','lastRotationBefore'])current[key]=saved[key];
 if(meta.restoreOrder){const records=new Map(meals.map(m=>[String(m.id),m]));current.meals=saved.meals.map(m=>records.get(String(m.id))).filter(Boolean).concat(meals.filter(m=>!saved.meals.some(old=>String(old.id)===String(m.id))))}
 // Keep later shopping progress on retained occurrences; recover only sources
 // that entered/left the schedule during this particular change.
 current.groceryOccurrenceChecks={version:1,checks:{...groceryOccurrenceChecks.checks},quantities:{...groceryOccurrenceChecks.quantities}};
 for(const id of meta.sourceIds){if(Object.hasOwn(meta.checks,id))current.groceryOccurrenceChecks.checks[id]=meta.checks[id];else delete current.groceryOccurrenceChecks.checks[id];const amount=saved.groceryOccurrenceChecks?.quantities?.[id];if(amount)current.groceryOccurrenceChecks.quantities[id]={...amount};else delete current.groceryOccurrenceChecks.quantities[id]}
 if(saved.skippedCookingState)current.skippedCookingState=saved.skippedCookingState;
 return current;
}
function finishScheduleChangeUndo(before){
 if(!before.scheduleChangeUndo)return;
 const after=captureScheduleUndoChecks(),prior=before.scheduleChangeUndo.checks;
 before.scheduleChangeUndo.sourceIds=[...new Set([...before.scheduleChangeUndo.sourceIds,...Object.keys(prior).filter(id=>!Object.hasOwn(after,id)),...Object.keys(after).filter(id=>!Object.hasOwn(prior,id))])];
 if(before.skippedCookingState){const saved=before.skippedCookingState;for(const [old,now]of [[saved.sessions,cookingSessions.occurrences],[saved.scales,occurrenceScales.occurrences]])for(const key of Object.keys(old))if(!now[key])saved.keys.push(key);saved.keys=[...new Set(saved.keys)]}
 history[history.length-1]=JSON.stringify(before);
}


function showRecipePhotoRestoreNotice(){let notice='';try{const key=recipePhotoStorage.test?'mealRotationTestPhotoNotice':'mealRotationPhotoNotice';notice=sessionStorage.getItem(key)||'';sessionStorage.removeItem(key)}catch(e){}if(notice)setTimeout(()=>showAppMessage(notice),0)}

function time(v){v=Number(v);if(!Number.isFinite(v)||v<0)return '—';if(v<60)return v+'m';let h=Math.floor(v/60),m=v%60;return h+'h'+(m?' '+m+'m':'')}
// Times remain stored in minutes, so existing recipes and backups stay compatible.
// For NEW bare-number entries: 0–9, 12 and 24 mean hours; other two- and
// three-digit values mean minutes. Explicit units always override this shortcut.
function inferBareTimeMinutes(text){
  if(!/^\d+$/.test(text))return NaN;
  const amount=Number(text);
  return (text.length===1||amount===12||amount===24)?amount*60:amount;
}
function parseDurationInput(raw){
  const value=String(raw??'').trim().toLowerCase();
  if(!value)return null;
  if(/^\d+$/.test(value))return inferBareTimeMinutes(value);
  // A bare decimal is a fractional number of HOURS (1.5 = 90 minutes),
  // not a range separator. Only a dash or "to" denotes a range.
  if(/^\d+\.\d+$/.test(value))return Math.round(Number(value)*60);
  const colon=value.match(/^(\d+):(\d{1,2})$/);
  if(colon&&Number(colon[2])<60)return Number(colon[1])*60+Number(colon[2]);
  const pattern=/(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?|m)\b/g;
  let total=0,last=0,matched=false,unitType=new Set(),hit;
  while((hit=pattern.exec(value))!==null){
    if(value.slice(last,hit.index).trim())return NaN;
    const u=hit[2],kind=/^h/.test(u)?'hour':'minute';
    if(unitType.has(kind))return NaN;
    unitType.add(kind);total+=Number(hit[1])*(kind==='hour'?60:1);
    matched=true;last=pattern.lastIndex;
  }
  if(!matched||value.slice(last).trim()||!Number.isFinite(total))return NaN;
  return Math.round(total);
}
// Values already saved in the recipe are minutes, not fresh text entries.
// Do not run new bare-number shortcuts on those existing saved minute values.
function prettyTimeInput(raw){
  if(raw===null||raw===undefined||String(raw).trim()==='')return '';
  const text=String(raw).trim();
  const value=/^\d+(?:\.\d+)?$/.test(text)?Number(text):parseDurationInput(text);
  return Number.isFinite(value)?time(value):text;
}
// A marinade duration can be a single time or a dash/"to" range.
// A dot is always a decimal fraction of hours (1.5 = 90 min), never a range.
// Explicit units continue to take priority (1.5 min = 1.5 minutes).
function parseMarinateInput(raw){
  const text=String(raw??'').trim();if(!text)return null;
  const parts=text.split(/\s*(?:[-–—]|\bto\b)\s*/i);
  if(parts.length>2||parts.some(x=>!x.trim()))return NaN;
  let [first,second]=parts;
  const bare=/^\d+$/;
  if(second!==undefined){
    // A bare one-digit start followed by a bare two-digit end denotes
    // hours at BOTH ends, e.g. 2-20 means 2–20 hours.
    if(bare.test(first.trim())&&bare.test(second.trim())&&
       first.trim().length===1&&second.trim().length===2){
      first+=' hrs';second+=' hrs';
    }else if(bare.test(first.trim())){
      // Keep supporting 2-5 hours and 30-60 minutes when just the
      // second endpoint specifies the unit.
      const unit=second.trim().match(/^\d+(?:\.\d+)?\s*(hours?|hrs?|h|minutes?|mins?|m)\s*$/i);
      if(unit)first+=' '+unit[1];
    }
  }
  const low=parseDurationInput(first);
  if(low===null||!Number.isFinite(low))return NaN;
  if(second===undefined)return {low,high:null};
  const high=parseDurationInput(second);
  if(high===null||!Number.isFinite(high)||high<low)return NaN;
  return {low,high};
}
function displayMarinateTime(raw){
  const parsed=parseMarinateInput(raw);
  if(!parsed||typeof parsed!=='object')return '';
  return parsed.high===null?time(parsed.low):time(parsed.low)+'–'+time(parsed.high);
}
function mealTimeDescription(meal,omitEmpty=false){
  const parts=[];
  const visibility=timeDisplayPrefs[showTop?(allMealsActive?'all':'top'):'category'];
  if(visibility.cooking){
    let prep=meal.prep===''||meal.prep==null?'—':time(meal.prep);
    let total=meal.total!==undefined&&meal.total!==''?time(meal.total):((meal.prep===''&&meal.cook==='')?'—':time((Number(meal.prep)||0)+(Number(meal.cook)||0)));
    if(omitEmpty){
      const recorded=value=>['string','number'].includes(typeof value)&&String(value).trim()!==''&&time(value)!=='—';
      if(!recorded(meal.prep))prep='—';
      if(!recorded(meal.total)){const known=[meal.prep,meal.cook].filter(recorded);total=known.length?time(known.reduce((sum,value)=>sum+Number(value),0)):'—'}
    }
    if(!omitEmpty||prep!=='—')parts.push(prep+' prep');
    if(!omitEmpty||total!=='—')parts.push(total+' total');
  }
  if(visibility.marinate&&String(meal.marinate??'').trim()){
    const value=displayMarinateTime(meal.marinate);
    if(value)parts.push(value+' marinate');
  }
  return parts.join(' · ');
}
function setTimeSegments(el,summary){el.replaceChildren();summary.split(' · ').forEach((part,i)=>{if(i){const separator=document.createElement('span');separator.textContent=' · ';separator.className='time-separator';el.append(separator)}const segment=document.createElement('span');segment.className='time-segment';segment.textContent=part;el.append(segment)})}
function appendMealTimes(body,meal,omitEmpty=false){
  const summary=mealTimeDescription(meal,omitEmpty);
  if(!summary)return;
  const el=document.createElement('div');el.className='times';setTimeSegments(el,summary);body.append(el);
}let topPanel=null;let renderTopSettingsPanel=null;let topIngredientExpanded=new Set();let topIngredientManualHiddenOverride=new Set();
// Contextual onboarding. The saved stage is independent of recipes and settings.
const tutorialKey='mealRotationTutorialStageV1';
let tutorialStage=localStorage.getItem(tutorialKey);
if(tutorialStage===null){tutorialStage='done';localStorage.setItem(tutorialKey,tutorialStage)}
function setTutorialStage(stage){tutorialStage=stage;localStorage.setItem(tutorialKey,stage);showTutorialHint()}
function showTutorialHint(){
 document.querySelectorAll('.meal-tutorial-hint').forEach(el=>el.remove());
 if(!['1','2','3'].includes(tutorialStage))return;
 const target=tutorialStage==='1'?document.querySelector('.unified-nav-fab[data-destination="groups"]'):
  tutorialStage==='2'?document.querySelector('.master-category-card button[aria-label^="Add meal to "]'):
  document.querySelector('.unified-nav-fab[data-destination="top"]');
 const relevant=tutorialStage==='1'?showTop&&!allMealsActive&&!groceryTabActive:
  tutorialStage==='2'?!showTop:tutorialStage==='3'?true:false;
 if(!relevant||!target)return;
 const hint=document.createElement('div');hint.className='meal-tutorial-hint';hint.setAttribute('role','status');
 hint.style.cssText='position:fixed;z-index:10005;width:min(260px,calc(100vw - 110px));background:#fffdf3;border:1px solid #d6c48e;border-radius:11px;padding:11px 12px;box-shadow:0 4px 18px #0003;color:#303030;font:14px/1.4 system-ui,sans-serif';
 const message=document.createElement('div');
 message.textContent=tutorialStage==='1'?'Tap the Menu button to open your meal groups.':tutorialStage==='2'?'Tap the + beside a group to add a recipe.':'Your recipe is saved! Tap Home, then tap a weekday to choose its meal group.';
 const arrow=document.createElement('span');arrow.textContent='→';arrow.style.cssText='font-size:22px;display:block;text-align:right;margin-top:2px';
 const skip=document.createElement('button');skip.type='button';skip.textContent='Skip tutorial';skip.style.cssText='background:transparent;border:0;padding:4px 0;color:#555;text-decoration:underline;font:12px system-ui;cursor:pointer';skip.onclick=()=>setTutorialStage('done');
 hint.append(message,arrow,skip);document.body.append(hint);
 const r=target.getBoundingClientRect();const w=hint.offsetWidth,h=hint.offsetHeight;
 let left=Math.max(8,r.left-w-12),top=Math.max(8,Math.min(window.innerHeight-h-8,r.top-h/2));
 if(tutorialStage==='2'){left=Math.max(8,Math.min(window.innerWidth-w-8,r.left-w-10));top=Math.max(8,Math.min(window.innerHeight-h-8,r.top-18))}
 hint.style.left=left+'px';hint.style.top=top+'px';
}
function startMealTutorial(){setTutorialStage('1');showTop=true;groceryTabActive=false;allMealsActive=false;render();window.scrollTo(0,0)}
function openHelpModal(){
 const top=showTop;
 const overlay=document.createElement('div');overlay.setAttribute('role','dialog');overlay.setAttribute('aria-modal','true');overlay.style.cssText='position:fixed;inset:0;background:#0008;z-index:10020;display:flex;align-items:center;justify-content:center;padding:16px';
 const box=document.createElement('div');box.style.cssText='background:var(--panel,#fff);color:var(--text,#222);border-radius:14px;width:100%;max-width:520px;max-height:82vh;display:flex;flex-direction:column;box-shadow:0 8px 30px #0004;overflow:hidden';
 const header=document.createElement('div');header.style.cssText='padding:18px 20px 10px;flex:0 0 auto;border-bottom:1px solid var(--border,#ddd);display:flex;align-items:center;justify-content:space-between;gap:12px;background:var(--panel,#fff)';
 const title=document.createElement('h2');title.textContent=top?'My Rotation help':'Meal Groups help';title.style.cssText='margin:0';
 const close=document.createElement('button');close.type='button';setIconButton(close,'cancel','Close');close.style.flex='0 0 44px';close.onclick=()=>overlay.remove();header.append(title,close);
 const content=document.createElement('div');content.style.cssText='padding:10px 20px 20px;overflow-y:auto;overscroll-behavior:contain';
 const intro=document.createElement('p');intro.textContent=top?'My Rotation displays the meals assigned to weekdays in the selected Breakfast, Lunch, or Dinner tab.':'Meal Groups contains your recipes, organized into In Rotation and Ideas. Expand a group to manage its meals.';content.append(intro);
 const items=top?[
  ['Meal-plan tabs','Choose a tab to see its own weekday assignments. Long-press a tab to rename, reorder, or delete it.'],
  ['Tap a displayed meal','Open its meal actions, including recipe options, editing, grocery list, and last-cooked date where available.'],
  ['Long-press a displayed meal','Open the weekday meal-change and grocery-list options.'],
  ['Rotate out arrow','Tap to rotate out all displayed recipes or select specific recipes. Long-pressing this arrow does nothing.'],
  ['Rotate across tabs','Use the all-tabs rotation control to rotate recipes across your meal-plan tabs.'],
  ['Weekday group headings','Tap a group name in a weekday card to open that group in Meal Groups.'],
  ['Navigation buttons','Use the floating buttons to switch between My Rotation, Meal Groups, Weekly Overview, and Grocery List.'],
  ['Weekly Overview','See weekday meals across tabs and expand their ingredient lists. Tap a meal to return to it in My Rotation.'],
  ['Grocery List','Review ingredients from the tabs you include; select, deselect, or hide checked groceries.'],
  ['Settings and backups','Configure display and weekday options, export or restore backups. Review changes before saving or discarding.']
 ]:[
  ['Open a group','Tap its heading or chevron to expand or collapse it. Use the top controls to expand or collapse all groups.'],
  ['Edit a group','Tap its pencil to rename or delete it. Long-press a group name or blank card area and drag to save a custom display order. Reset to Weekday Order restores automatic ordering without changing assignments.'],
  ['Add a meal','Tap + to add a meal to the selected group.'],
  ['Edit a meal','Choose Edit meal from its meal actions. The editor opens beneath the selected meal.'],
  ['Move a rotating meal','Tap its up or down arrow to move it to the top or bottom of the group; hold to move one position.'],
  ['Recipe status','Choose In Rotation or Ideas in the recipe status control.'],
  ['Linked meals','Linked recipes can appear in more than one group; linked changes may affect their other appearances.'],
  ['Last cooked','Shows the latest recorded cooking date when enabled.'],
  ['Navigation','Use the floating buttons to open My Rotation, Weekly Overview, or Grocery List. The Menu button returns here with groups collapsed.']
 ];
 items.forEach(([gesture,desc])=>{const h=document.createElement('strong');h.textContent=gesture;h.style.display='block';h.style.marginTop='12px';const d=document.createElement('div');d.textContent=desc;d.style.color='var(--muted,#666)';d.style.fontSize='14px';content.append(h,d)});
 const tutorialButton=document.createElement('button');tutorialButton.type='button';tutorialButton.className='smallbtn';tutorialButton.textContent='Start Tutorial';tutorialButton.style.marginTop='16px';tutorialButton.onclick=()=>{overlay.remove();startMealTutorial()};content.prepend(tutorialButton);
 box.append(header,content);overlay.append(box);overlay.addEventListener('click',e=>{if(e.target===overlay)overlay.remove()});document.body.append(overlay)
 }function appDialog(message,initial,kind='confirm',options=[],description=''){return new Promise(resolve=>{const shade=document.createElement('div');shade.style.cssText='position:fixed;inset:0;z-index:20000;background:#0008;display:flex;align-items:center;justify-content:center;padding:18px';const panel=document.createElement('div');panel.style.cssText='background:#fff;color:#242424;border-radius:16px;padding:22px;width:100%;max-width:480px;box-shadow:0 12px 36px #0003';panel.setAttribute('role','dialog');panel.setAttribute('aria-modal','true');const heading=document.createElement('div');heading.textContent=message;heading.style.cssText='font-size:19px;font-weight:600;margin-bottom:18px';panel.append(heading);if(description){shade.style.zIndex='36000';shade.setAttribute('role','dialog');shade.setAttribute('aria-modal','true');shade.setAttribute('aria-label',message);panel.setAttribute('role','presentation');panel.removeAttribute('aria-modal');panel.style.maxHeight='85dvh';panel.style.overflowY='auto';const detail=document.createElement('p');detail.textContent=description;detail.style.cssText='font-size:16px;line-height:1.45;margin:0 0 18px';panel.append(detail)}let field=null;if(kind==='prompt'){field=document.createElement('input');field.type='text';field.value=initial||'';field.style.cssText='width:100%;border:1px solid #ccc;border-radius:9px;padding:12px;margin-bottom:20px;background:#fff;color:#242424';panel.append(field)}const actions=document.createElement('div');actions.style.cssText='display:flex;gap:12px;justify-content:center';function btn(label,result){const b=document.createElement('button');b.type='button';b.textContent=label;b.className='smallbtn';b.style.cssText='min-width:100px;padding:11px 20px';b.onclick=()=>{const value=result&&field?field.value:result;shade.remove();resolve(value)};actions.append(b)}if(kind==='yesnocancel'){
  actions.className='meal-unified-actions';
  function iconChoice(type,label,result){const b=document.createElement('button');b.type='button';setIconButton(b,type,label);b.onclick=()=>{shade.remove();resolve(result)};actions.append(b)}
  iconChoice('save','Yes',true);iconChoice('delete','No',false);iconChoice('cancel','Cancel',null);
}else if(kind==='prompt'){
  actions.className='meal-unified-actions';
  function promptIcon(type,label,result){const b=document.createElement('button');b.type='button';setIconButton(b,type,label);b.onclick=()=>{const value=result?field.value:null;shade.remove();resolve(value)};actions.append(b)}
  promptIcon('save','Save',true);promptIcon('cancel','Cancel',false);
}else if(kind==='yesno'||kind==='tracking-remove'){
  actions.className='meal-unified-actions';
  function iconChoice(type,label,result){const b=document.createElement('button');b.type='button';setIconButton(b,type,label);b.onclick=()=>{shade.remove();resolve(result)};actions.append(b)}
  iconChoice('save',kind==='tracking-remove'?'Confirm removal':'Yes',true);iconChoice('cancel',kind==='tracking-remove'?'Cancel removal':'No',null);
}else if(kind==='options'){
  // Return the selected option verbatim to callers such as Recipe Labels.
  for(const option of options)btn(option,option==='Cancel'?null:option);
}else if(kind==='alert'){
  btn('Cancel',null);
}else{
  btn(kind==='prompt'?'Save':kind==='yesno'?'Yes':'Delete',true);
  btn(kind==='yesno'?'No':'Cancel',null);
}
panel.append(actions);shade.append(panel);document.body.append(shade);
if(description){actions.lastElementChild.focus({preventScroll:true});shade.addEventListener('click',e=>{if(e.target===shade)actions.lastElementChild.click()});shade.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();actions.lastElementChild.click()}if(e.key==='Tab'){const controls=[...actions.querySelectorAll('button')],first=controls[0],last=controls.at(-1);if(e.shiftKey&&document.activeElement===first){e.preventDefault();last.focus()}else if(!e.shiftKey&&document.activeElement===last){e.preventDefault();first.focus()}}})}
// Keep the entire prompt, including Save and Cancel, above Android's keyboard.
let promptFrame=0;
function fitPrompt(){if(!shade.isConnected)return;cancelAnimationFrame(promptFrame);promptFrame=requestAnimationFrame(()=>{if(!shade.isConnected)return;const vv=window.visualViewport;const top=vv?vv.offsetTop:0;const height=vv?vv.height:window.innerHeight;const bottom=top+height;shade.style.top=top+'px';shade.style.bottom='auto';shade.style.height=height+'px';shade.style.alignItems='center';shade.style.overflowY='auto';panel.style.maxHeight=Math.max(160,height-24)+'px';panel.style.overflowY='auto';});}
if(kind==='prompt'){window.visualViewport?.addEventListener('resize',fitPrompt);window.visualViewport?.addEventListener('scroll',fitPrompt);fitPrompt();}
if(field){field.focus({preventScroll:true});field.select();setTimeout(fitPrompt,120);field.onkeydown=e=>{if(e.key==='Enter'){e.preventDefault();actions.firstChild.click()}}}})}
const appIconSvg={settings:'<path d="M12 3.5v2M12 18.5v2M3.5 12h2M18.5 12h2M6 6l1.4 1.4M16.6 16.6 18 18M18 6l-1.4 1.4M7.4 16.6 6 18"/><circle cx="12" cy="12" r="6.5"/><circle cx="12" cy="12" r="2"/>','chevrons-down':'<path d="m6 4 6 6 6-6M6 12l6 6 6-6"/>','chevrons-up':'<path d="m6 20 6-6 6 6M6 12l6-6 6 6"/>',left:'<path d="M15 18l-6-6 6-6"/>',right:'<path d="m9 18 6-6-6-6"/>',save:'<path d="M5 12l5 5L20 7"/>',cancel:'<path d="M5 5l14 14M19 5L5 19"/>',delete:'<path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6"/>',rename:'<path d="M4 20h16M6 16l10-10 3 3-10 10-4 1z"/>',add:'<path d="M12 5v14M5 12h14"/>',move:'<path d="M5 12h14m-6-6 6 6-6 6"/>'};function setIconButton(b,type,label){b.textContent='';b.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">'+appIconSvg[type]+'</svg>';b.title=label;b.setAttribute('aria-label',label);b.style.cssText='border:0;background:transparent;color:#444;display:grid;place-items:center;min-width:42px;min-height:42px;padding:6px'}
  function normalizeSearchText(value){
    return String(value||'').normalize('NFKD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase().trim().replace(/\s+/g,' ');
  }
  function searchWords(value){return normalizeSearchText(value).match(/[\p{L}\p{N}]+/gu)||[]}
  function singularSearchWord(word){
    if(word.length>4&&word.endsWith('ies'))return word.slice(0,-3)+'y';
    if(word.length>4&&word.endsWith('oes'))return word.slice(0,-2);
    if(word.length>4&&/(ches|shes|sses|xes|zes)$/.test(word))return word.slice(0,-2);
    if(word.length>3&&word.endsWith('s')&&!/(ss|us|is)$/.test(word))return word.slice(0,-1);
    return word;
  }
function mealMatchesSearch(m,query){
 const q=normalizeSearchText(query),queryWords=searchWords(q);
      const mealName=normalizeSearchText(m.name);
      const mealWords=searchWords(mealName);
      const wordMatches=(word,candidate)=>candidate.includes(word)||singularSearchWord(candidate)===singularSearchWord(word);
      return queryWords.length>0&&queryWords.every(word=>mealWords.some(candidate=>wordMatches(word,candidate)));
}
function openMealSearch(saved=null){
  const navigationOrigin=captureMealEditorOrigin();
  const shade=document.createElement('div');
  shade.style.cssText='position:fixed;inset:0;z-index:13020;background:#0008;display:flex;align-items:center;justify-content:center;padding:16px';
  const panel=document.createElement('div');
  panel.setAttribute('role','dialog');
  panel.setAttribute('aria-modal','true');
  panel.setAttribute('aria-label','Search meals');
  panel.style.cssText='width:100%;max-width:520px;max-height:85%;min-height:240px;background:#fff;color:#242424;border-radius:14px;box-shadow:0 10px 30px #0004;padding:18px;display:flex;flex-direction:column;gap:12px;overflow:hidden';
  const header=document.createElement('div');
  header.style.cssText='display:flex;align-items:center;justify-content:space-between;gap:10px';
  const title=document.createElement('strong');
  title.textContent='Search meals';
  title.style.cssText='font-size:19px';
  const closeButton=document.createElement('button');
  closeButton.type='button';
  setIconButton(closeButton,'cancel','Close');
  const input=document.createElement('input');
  input.type='search';
  input.placeholder='Enter a meal name';
  input.setAttribute('aria-label','Search meal names');
  input.autocomplete='off';
  input.value=saved?.query||'';
  input.style.cssText='width:100%;min-height:46px;padding:9px 12px;border:1px solid #ccc;border-radius:9px;background:#fff;color:#242424;font-size:16px';
  const selectedGroups=new Set((Array.isArray(saved?.groups)?saved.groups:[]).filter(group=>cats.includes(group)));
  const groupFilter=document.createElement('fieldset');
  groupFilter.style.cssText='margin:0;padding:8px;border:1px solid #ccc;border-radius:9px;max-height:150px;overflow-y:auto;flex-shrink:0';
  const legend=document.createElement('legend');legend.textContent='Filter meal groups';groupFilter.append(legend);
  const clearGroups=document.createElement('button');clearGroups.type='button';clearGroups.className='iconbtn';setIconButton(clearGroups,'save','Deselect all meal groups');clearGroups.innerHTML='<svg viewBox="0 0 24 24" width="25" height="25" fill="none" stroke="currentColor" stroke-width="1.9"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 12h10"/></svg>';clearGroups.style.cssText='width:30px;height:30px;min-width:30px;min-height:30px;padding:4px;margin-left:auto';
  clearGroups.onclick=()=>{selectedGroups.clear();groupFilter.querySelectorAll('input').forEach(check=>check.checked=false);updateResults()};
  legend.style.cssText='display:flex;align-items:center;gap:8px;width:100%';legend.append(clearGroups);
  for(const group of cats){
    const label=document.createElement('label');label.style.cssText='display:flex;align-items:center;gap:8px;min-height:44px;font-size:15px;cursor:pointer';
    const check=document.createElement('input');check.type='checkbox';check.className='check';check.checked=selectedGroups.has(group);
    check.onchange=()=>{if(check.checked)selectedGroups.add(group);else selectedGroups.delete(group);updateResults()};
    label.append(check,document.createTextNode(group));groupFilter.append(label);
  }
  const searchRow=document.createElement('div');searchRow.style.cssText='display:flex;align-items:center;gap:8px';input.style.minWidth='0';
  const filterButton=document.createElement('button');filterButton.type='button';filterButton.className='iconbtn search-filter-toggle';filterButton.setAttribute('aria-label','Meal group filters');filterButton.setAttribute('aria-expanded','false');
  filterButton.innerHTML='<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 4h18l-7 8v7l-4 2v-9z"/></svg>';
  groupFilter.hidden=true;filterButton.onclick=()=>{groupFilter.hidden=!groupFilter.hidden;filterButton.setAttribute('aria-expanded',String(!groupFilter.hidden))};searchRow.append(input,filterButton);
  const results=document.createElement('div');
  results.setAttribute('aria-live','polite');
  results.style.cssText='overflow-y:auto;min-height:100px;flex:1;overscroll-behavior:contain';
  const selectedRecipes=new Set(recipeBulkMode?[...recipeBulkIds]:[]);let selectedSourceGroup=recipeBulkMode?recipeBulkSourceGroup:null;const bulk=document.createElement('button');bulk.type='button';bulk.className='smallbtn';bulk.hidden=true;bulk.setAttribute('aria-label','Bulk actions for selected recipes');
  const updateSelection=()=>{bulk.hidden=!selectedRecipes.size;bulk.textContent='Bulk actions ('+selectedRecipes.size+')'};updateSelection();
  bulk.onclick=()=>{if(!selectedRecipes.size)return;closeSearch();setMasterCategoriesView(true);showTop=false;groceryTabActive=false;allMealsActive=false;recipeBulkMode=true;recipeBulkIds=new Set(selectedRecipes);recipeBulkSourceGroup=selectedSourceGroup;recipeBulkFilter={query:input.value,groups:[...selectedGroups]};render()};
  function fitSearch(){
    const vv=window.visualViewport;
    if(!vv)return;
    shade.style.top=vv.offsetTop+'px';
    shade.style.bottom='auto';
    shade.style.height=vv.height+'px';
    panel.style.maxHeight=Math.max(200,vv.height-32)+'px';
  }
  function closeSearch(){
    shade.remove();
    document.removeEventListener('keydown',onKeyDown);
    window.visualViewport?.removeEventListener('resize',fitSearch);
    window.visualViewport?.removeEventListener('scroll',fitSearch);
  }
  function chooseMeal(mealId){
    input.blur();closeSearch();
    const meal=meals.find(m=>String(m.id)===String(mealId));
    if(meal){const search={query:input.value,groups:[...selectedGroups],scroll:results.scrollTop};openTopMealActionMenu(null,meal.cat,meal,false,null,{...navigationOrigin,resumeDialog:()=>openMealSearch(search)})}
  }
  function updateResults(){
    clearGroups.hidden=!selectedGroups.size;
    filterButton.classList.toggle('active',selectedGroups.size>0);filterButton.title=selectedGroups.size?'Meal group filters ('+selectedGroups.size+' active)':'Meal group filters';
    results.replaceChildren();
    const q=normalizeSearchText(input.value);
    if(!q&&!selectedGroups.size)return;
    const matches=meals.filter(m=>(!selectedGroups.size||selectedGroups.has(m.cat))&&(!q||mealMatchesSearch(m,q)));
    if(!matches.length){
      const empty=document.createElement('p');
      empty.textContent='No matching meals.';
      empty.style.cssText='font-size:14px;color:#666;margin:8px 0';
      results.append(empty);
      return;
    }
    matches.forEach(meal=>{
      const button=document.createElement('button');
      button.type='button';
      button.style.cssText='display:block;width:100%;padding:12px 8px;text-align:left;border:0;border-bottom:1px solid #e3e3e3;background:#fff;color:inherit';
      const name=document.createElement('span');
      name.textContent=meal.name||'Untitled meal';
      name.style.cssText='display:block;font-size:17px';
      const meta=document.createElement('span');
      meta.textContent=(meal.cat||'Unassigned')+(' · '+recipeStatusLabel(recipeStatus(meal)));
      meta.style.cssText='display:block;font-size:13px;color:#666;margin-top:4px';
      button.append(name,meta);
      button.dataset.mealId=String(meal.id);
      button.onclick=()=>chooseMeal(meal.id);
      const row=document.createElement('div');row.style.cssText='display:flex;align-items:center;gap:8px';
      const check=document.createElement('input');check.type='checkbox';check.className='check';check.setAttribute('aria-label','Select '+(meal.name||'Untitled meal'));check.checked=selectedRecipes.has(String(meal.id));check.disabled=selectedSourceGroup!==null&&meal.cat!==selectedSourceGroup;check.title=check.disabled?'Select recipes from '+(selectedSourceGroup||'Unassigned'):'';check.onchange=()=>{if(selectedSourceGroup!==null&&meal.cat!==selectedSourceGroup){check.checked=false;return}if(check.checked){if(!selectedRecipes.size)selectedSourceGroup=meal.cat;selectedRecipes.add(String(meal.id))}else selectedRecipes.delete(String(meal.id));if(!selectedRecipes.size)selectedSourceGroup=null;updateSelection();updateResults()};const target=document.createElement('label');target.className='recipe-search-select';target.append(check);row.append(target,button);results.append(row);
    });
  }
  function onKeyDown(event){if(event.key==='Escape'){event.preventDefault();closeSearch()}}
  closeButton.onclick=closeSearch;
  shade.onclick=event=>{if(event.target===shade)closeSearch()};
  input.oninput=updateResults;
  input.onkeydown=event=>{
    if(event.key==='Enter'){
      const first=results.querySelector('button');
      if(first){event.preventDefault();first.click()}
    }
  };
  header.append(title,closeButton);
  panel.append(header,searchRow,groupFilter,results,bulk);
  shade.append(panel);
  document.body.append(shade);
  document.addEventListener('keydown',onKeyDown);
  window.visualViewport?.addEventListener('resize',fitSearch);
  window.visualViewport?.addEventListener('scroll',fitSearch);
  updateResults();
  results.scrollTop=saved?.scroll||0;
  fitSearch();
  requestAnimationFrame(()=>{if(shade.isConnected){input.focus({preventScroll:true});fitSearch()}});
}

function readUpNextOrder(){const value=JSON.parse(localStorage.getItem(UP_NEXT_ORDER_KEY)||'[]');return Array.isArray(value)?[...new Set(value.filter(id=>typeof id==='string'))]:[]}
function normalizedUpNextOrder(){
 const eligible=meals.filter(m=>recipeStatus(m)==='up-next'),ids=new Set(eligible.map(m=>String(m.id)));
 const order=readUpNextOrder().filter(id=>ids.has(id));
 // Former Back Burner/Ideas displayed alphabetically; append them in that same relative order.
 const missing=eligible.filter(m=>!order.includes(String(m.id))).sort((a,b)=>String(a.name||'').localeCompare(String(b.name||''),undefined,{sensitivity:'base'}));
 for(const meal of missing){
  const peer=meal.linkGroup&&meals.find(other=>other!==meal&&other.linkGroup===meal.linkGroup&&order.includes(String(other.id)));
  if(peer)order.splice(order.indexOf(String(peer.id))+1,0,String(meal.id));else order.push(String(meal.id));
 }
 const starred=id=>meals.find(m=>String(m.id)===id)?.upNextStar===true;
 return [...order.filter(starred),...order.filter(id=>!starred(id))];
}
function saveUpNextOrder(){const order=normalizedUpNextOrder();if(JSON.stringify(order)!==localStorage.getItem(UP_NEXT_ORDER_KEY))localStorage.setItem(UP_NEXT_ORDER_KEY,JSON.stringify(order));return order}
function upNextRank(meal,order){const peers=meal.linkGroup?meals.filter(m=>m.linkGroup===meal.linkGroup):[meal];return Math.min(...peers.map(m=>order.indexOf(String(m.id))).filter(i=>i>=0),Infinity)}
function setRecipeStatus(meal,status){
 const peers=meal.linkGroup?meals.filter(m=>m.linkGroup===meal.linkGroup):[meal];
 for(const record of peers){record.rotation=status==='rotation';record.recipeStatus=status;if(typeof record.upNextStar!=='boolean')record.upNextStar=false;if(!record.rotation)delete record.rotationPromotionPriority}
}
function groupUsesRotation(category){const values=JSON.parse(localStorage.getItem(GROUP_ROTATION_KEY)||'{}');const key=groupIdentity(category);return !key||values[key]!==false}
